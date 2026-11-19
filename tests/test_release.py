from __future__ import annotations

import io
import re
import socket
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import app
import windows_app
from camsend_version import VERSION


class CamSendReleaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.original_transfer_dir = app.TRANSFER_DIR
        app.TRANSFER_DIR = Path(self.temp_directory.name) / "transfers"
        app.TRANSFER_DIR.mkdir()
        app.new_session()
        self.token = app.session_token
        self.client = app.app.test_client()

    def tearDown(self) -> None:
        app.TRANSFER_DIR = self.original_transfer_dir
        app.new_session()
        self.temp_directory.cleanup()

    def connect(self, address: str = "192.168.10.20", client=None):
        # Each test client has its own cookie jar, i.e. it acts as a separate browser.
        return (client or self.client).get(
            f"/connect/{self.token}",
            environ_overrides={"REMOTE_ADDR": address},
        )

    def test_release_version_and_request_limit(self) -> None:
        self.assertEqual(VERSION, "1.0.0")
        self.assertEqual(app.MAX_FILE_BYTES, 2 * 1024 * 1024 * 1024)
        self.assertEqual(app.app.config["MAX_CONTENT_LENGTH"], app.MAX_FILE_BYTES)

    def test_unused_token_expires_but_paired_session_remains(self) -> None:
        created = app.session_created
        with patch("app.time.time", return_value=created + app.SESSION_TTL_SECONDS + 1):
            self.assertFalse(app.session_is_valid(self.token))
            self.assertEqual(self.connect().status_code, 403)

        app.new_session()
        self.token = app.session_token
        self.assertEqual(self.connect().status_code, 200)
        created = app.session_created
        with patch("app.time.time", return_value=created + app.SESSION_TTL_SECONDS + 1):
            self.assertTrue(app.session_is_valid(self.token))

    def test_new_session_invalidates_previous_token(self) -> None:
        previous = self.token
        app.new_session()
        self.assertNotEqual(previous, app.session_token)
        self.assertEqual(self.client.get(f"/connect/{previous}").status_code, 403)

    def test_only_one_active_browser_address_is_allowed(self) -> None:
        self.assertEqual(self.connect("192.168.10.20").status_code, 200)
        second = self.connect("192.168.10.21", client=app.app.test_client())
        self.assertEqual(second.status_code, 409)

    def test_paired_session_cannot_be_taken_over_by_another_device(self) -> None:
        self.assertEqual(self.connect("192.168.10.20").status_code, 200)
        intruder = app.app.test_client()
        environ = {"REMOTE_ADDR": "192.168.10.66"}
        # Knowing the token is not enough for any session endpoint.
        self.assertEqual(intruder.post(f"/api/heartbeat/{self.token}", environ_overrides=environ).status_code, 403)
        self.assertEqual(intruder.get(f"/api/session/{self.token}", environ_overrides=environ).status_code, 403)
        self.assertEqual(intruder.post(f"/api/switch/{self.token}", environ_overrides=environ).status_code, 403)
        upload = intruder.post(
            f"/upload-file/{self.token}", data=b"x", headers={"X-Filename": "x.txt"}, environ_overrides=environ
        )
        self.assertEqual(upload.status_code, 403)
        self.assertFalse((app.TRANSFER_DIR / "x.txt").exists())
        self.assertEqual(intruder.post(f"/api/end/{self.token}", environ_overrides=environ).status_code, 403)
        self.assertFalse(app.session_state["ended"])
        # Not even after the paired phone has been silent past the heartbeat timeout.
        with patch("app.time.time", return_value=app.session_state["last_seen"] + app.HEARTBEAT_TIMEOUT_SECONDS + 1):
            self.assertEqual(self.connect("192.168.10.66", client=intruder).status_code, 409)
        self.assertEqual(app.session_state["device_ip"], "192.168.10.20")
        self.assertEqual(self.client.post(f"/api/heartbeat/{self.token}").status_code, 200)

    def test_second_browser_on_same_address_replaces_the_first(self) -> None:
        self.assertEqual(self.connect("192.168.10.20").status_code, 200)
        other_browser = app.app.test_client()
        self.assertEqual(self.connect("192.168.10.20", client=other_browser).status_code, 200)
        self.assertEqual(other_browser.post(f"/api/heartbeat/{self.token}").status_code, 200)
        self.assertEqual(self.client.post(f"/api/heartbeat/{self.token}").status_code, 403)

    def test_garbage_token_is_rejected_without_server_error(self) -> None:
        self.assertEqual(self.client.get("/connect/%C3%A4").status_code, 403)
        self.assertEqual(self.client.post("/api/heartbeat/%C3%A4").status_code, 403)

    def test_qr_code_and_desktop_page_are_local_only(self) -> None:
        lan = {"REMOTE_ADDR": "192.168.10.66"}
        self.assertEqual(self.client.get("/", environ_overrides=lan).status_code, 404)
        self.assertEqual(self.client.get("/qr.png", environ_overrides=lan).status_code, 404)
        self.assertEqual(self.client.get("/", environ_overrides={"REMOTE_ADDR": "127.0.0.1"}).status_code, 200)
        with patch("app.local_ip", return_value="192.168.10.5"):
            local_qr = self.client.get("/qr.png", environ_overrides={"REMOTE_ADDR": "127.0.0.1"})
        self.assertEqual(local_qr.status_code, 200)
        self.assertEqual(local_qr.mimetype, "image/png")

    def test_phone_page_renders_in_both_directions(self) -> None:
        for mode in ("receive", "send"):
            app.session_state["mode"] = mode
            response = self.connect()
            self.assertEqual(response.status_code, 200, mode)
            self.assertIn(b'id="end-session"', response.data)
        app.session_state["mode"] = "receive"
        self.assertIn(b'type="file"', self.connect().data)

    def test_end_blocks_further_transfers(self) -> None:
        self.assertEqual(self.connect().status_code, 200)
        self.assertEqual(self.client.post(f"/api/end/{self.token}").status_code, 200)
        response = self.client.post(
            f"/upload-file/{self.token}",
            data=b"blocked",
            headers={"X-Filename": "blocked.txt"},
        )
        self.assertEqual(response.status_code, 410)

    def test_session_api_exposes_only_browser_fields(self) -> None:
        self.assertEqual(self.connect().status_code, 200)
        response = self.client.get(f"/api/session/{self.token}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            set(response.json),
            {"connected", "mode", "ended", "language", "offered_files", "history", "transfer"},
        )
        self.assertFalse({"receive_dir", "device_ip", "device", "device_key", "paired"} & set(response.json))

    def test_upload_stream_sanitizes_and_deduplicates_names(self) -> None:
        self.assertEqual(self.connect().status_code, 200)
        first = self.client.post(
            f"/upload-file/{self.token}",
            data=b"first",
            headers={"X-Filename": "my photo?.jpg"},
        )
        second = self.client.post(
            f"/upload-file/{self.token}",
            data=b"second",
            headers={"X-Filename": "my photo?.jpg"},
        )
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(first.json["name"], "my_photo.jpg")
        self.assertEqual(second.json["name"], "my_photo-1.jpg")
        self.assertEqual((app.TRANSFER_DIR / "my_photo.jpg").read_bytes(), b"first")
        self.assertEqual((app.TRANSFER_DIR / "my_photo-1.jpg").read_bytes(), b"second")

        international = self.client.post(
            f"/upload-file/{self.token}",
            data=b"unicode",
            headers={"X-Filename": "Привет мир.pdf"},
        )
        self.assertEqual(international.status_code, 200)
        self.assertEqual(international.json["name"], "Привет_мир.pdf")
        self.assertEqual((app.TRANSFER_DIR / "Привет_мир.pdf").read_bytes(), b"unicode")

    def test_interrupted_upload_removes_partial_file_and_history(self) -> None:
        self.assertEqual(self.connect().status_code, 200)
        with self.client.application.test_request_context(
            f"/upload-file/{self.token}",
            method="POST",
            headers={
                "X-Filename": "partial video.mp4",
                "Content-Length": "20",
                "Cookie": f"{app.DEVICE_COOKIE}={app.session_state['device_key']}",
            },
            input_stream=io.BytesIO(b"partial content"),
        ):
            with patch.object(app.request.stream, "read", side_effect=[b"partial", OSError("disconnected")]):
                with self.assertRaises(OSError):
                    app.upload_file(self.token)

        self.assertFalse((app.TRANSFER_DIR / "partial_video.mp4").exists())
        self.assertEqual(app.session_state["history"], [])
        self.assertFalse(app.session_state["transfer"]["active"])

    def test_download_stream_requires_session_and_completes_history(self) -> None:
        self.assertEqual(self.connect().status_code, 200)
        content = b"local transfer" * 1024
        path = app.TRANSFER_DIR / "sample.pdf"
        path.write_bytes(content)
        app.session_state["offered_files"] = [path.name]

        invalid = self.client.get(f"/download-file/not-the-token/{path.name}")
        self.assertEqual(invalid.status_code, 403)
        response = self.client.get(f"/download-file/{self.token}/{path.name}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, content)
        response.close()
        self.assertNotIn(path.name, app.session_state["offered_files"])
        self.assertEqual(app.session_state["history"][-1]["status"], "done")

    def test_offered_files_download_under_their_original_names(self) -> None:
        self.assertEqual(self.connect().status_code, 200)
        names = ["Bericht März 2026.pdf", "a%20b.txt", "double__underscore.txt", "100 % sicher.txt"]
        for name in names:
            (app.TRANSFER_DIR / name).write_bytes(name.encode("utf-8"))
        (app.TRANSFER_DIR / "not offered.txt").write_bytes(b"secret")
        app.session_state["offered_files"] = list(names)
        app.session_state["mode"] = "send"

        page = self.connect().data.decode("utf-8")
        for name in names:
            href = re.search(r'data-name="%s" href="([^"]+)"' % re.escape(name.replace("&", "&amp;")), page)
            self.assertIsNotNone(href, name)
            response = self.client.get(href.group(1).replace("&amp;", "&"))
            self.assertEqual(response.status_code, 200, name)
            self.assertEqual(response.data, name.encode("utf-8"))
            response.close()

        for path in ["not%20offered.txt", "../app.py", "..%5capp.py", "C:not%20offered.txt"]:
            self.assertEqual(self.client.get(f"/download-file/{self.token}/{path}").status_code, 404, path)

    def test_cancelled_download_remains_available_for_retry(self) -> None:
        self.assertEqual(self.connect().status_code, 200)
        path = app.TRANSFER_DIR / "large-video.mp4"
        path.write_bytes(b"a" * (2 * 1024 * 1024 + 1))
        app.session_state["offered_files"] = [path.name]

        response = self.client.get(f"/download-file/{self.token}/{path.name}", buffered=False)
        next(response.response)
        response.close()

        self.assertIn(path.name, app.session_state["offered_files"])
        self.assertEqual(app.session_state["history"][-1]["status"], "waiting")
        self.assertEqual(app.session_state["history"][-1]["done"], 0)

    def test_local_address_detection_never_falls_back_to_loopback(self) -> None:
        address_info = (socket.AF_INET, socket.SOCK_DGRAM, 17, "", ("192.168.50.4", 0))
        route_socket = MagicMock()
        route_socket.connect.side_effect = OSError("no default route")
        with patch("app.socket.getaddrinfo", return_value=[address_info]), patch(
            "app.socket.socket", return_value=route_socket
        ):
            self.assertEqual(app.local_ip(), "192.168.50.4")

        route_socket = MagicMock()
        route_socket.connect.side_effect = OSError("no route")
        with patch("app.socket.getaddrinfo", side_effect=socket.gaierror()), patch(
            "app.socket.socket", return_value=route_socket
        ):
            with self.assertRaises(RuntimeError):
                app.local_ip()

    def test_brand_asset_and_route_are_available(self) -> None:
        self.assertTrue(app.BRAND_PATH.is_file())
        response = self.client.get("/brand/logo.png")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "image/png")
        response.close()

    def test_all_interface_translation_keys_exist(self) -> None:
        mobile_keys: set[str] = set()
        for path in app.RESOURCE_DIR.joinpath("templates").glob("*.html"):
            mobile_keys.update(
                re.findall(r"\{\{\s*t\.([A-Za-z_][A-Za-z0-9_]*)", path.read_text(encoding="utf-8"))
            )
        for language, texts in app.MOBILE_TEXT.items():
            self.assertFalse(mobile_keys - texts.keys(), (language, mobile_keys - texts.keys()))

        windows_source = Path(windows_app.__file__).read_text(encoding="utf-8")
        windows_keys = set(re.findall(r"self\.tr\([\"']([^\"']+)", windows_source))
        for language, texts in windows_app.WORDS.items():
            self.assertFalse(windows_keys - texts.keys(), (language, windows_keys - texts.keys()))

    def test_cancelled_windows_actions_preserve_state(self) -> None:
        window = windows_app.CamSendWindow.__new__(windows_app.CamSendWindow)
        window.language = "de"
        window.show_progress = Mock()
        window.send = Mock(return_value=False)
        app.session_state["mode"] = "send"
        app.session_state["transfer"] = {
            "active": False,
            "name": "completed.zip",
            "done": 10,
            "total": 10,
            "direction": "send",
        }
        previous_transfer = dict(app.session_state["transfer"])
        self.assertFalse(window.new_transfer())
        self.assertEqual(app.session_state["transfer"], previous_transfer)

        window.receive = Mock(return_value=False)
        window.current_mode = "send"
        self.assertFalse(window.switch_direction())
        self.assertEqual(app.session_state["mode"], "send")
        self.assertEqual(app.session_state["transfer"], previous_transfer)


if __name__ == "__main__":
    unittest.main()
