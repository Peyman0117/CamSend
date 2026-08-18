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

    def connect(self, address: str = "192.168.10.20"):
        return self.client.get(
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
        second = self.connect("192.168.10.21")
        self.assertEqual(second.status_code, 409)

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
        self.assertFalse({"receive_dir", "device_ip", "device", "paired"} & set(response.json))

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
            headers={"X-Filename": "partial video.mp4", "Content-Length": "20"},
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
