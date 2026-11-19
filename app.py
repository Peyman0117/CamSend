from __future__ import annotations

import io
import ipaddress
import mimetypes
import os
import queue
import re
import secrets
import socket
import sys
import time
import threading
import unicodedata
from pathlib import Path
from urllib.parse import quote, unquote

import qrcode
from flask import Flask, Response, abort, make_response, render_template, request, send_from_directory, stream_with_context
from werkzeug.utils import secure_filename as ascii_secure_filename

from camsend_version import VERSION


SOURCE_DIR = Path(__file__).resolve().parent
RESOURCE_DIR = Path(getattr(sys, "_MEIPASS", SOURCE_DIR))
IS_FROZEN = bool(getattr(sys, "frozen", False))

if IS_FROZEN:
    local_app_data = os.environ.get("LOCALAPPDATA")
    DATA_DIR = Path(local_app_data) / "CamSend" if local_app_data else Path.home() / "AppData" / "Local" / "CamSend"
else:
    DATA_DIR = SOURCE_DIR

TRANSFER_DIR = DATA_DIR / "transfers"
TRANSFER_DIR.mkdir(parents=True, exist_ok=True)
BRAND_PATH = RESOURCE_DIR / "static" / "brand" / "camsend-logo.png"

PORT = int(os.environ.get("CAMSEND_PORT", os.environ.get("DATATRANSFER_PORT", "8765")))
SESSION_TTL_SECONDS = 15 * 60
HEARTBEAT_TIMEOUT_SECONDS = 20
MAX_FILE_BYTES = 2 * 1024 * 1024 * 1024
DEVICE_COOKIE = "camsend_device"
MAX_TEXT_CHARS = 10_000
MAX_TEXT_MESSAGES = 50
# JSON requests (texts, local hand-off) are tiny; refusing large bodies early keeps a
# paired browser from making the server buffer up to MAX_FILE_BYTES in memory.
MAX_JSON_BYTES = 64 * 1024
INSTANCE_KEY_PATH = DATA_DIR / "instance.key"

app = Flask(
    __name__,
    template_folder=str(RESOURCE_DIR / "templates"),
    static_folder=str(RESOURCE_DIR / "static"),
)
app.config["MAX_CONTENT_LENGTH"] = MAX_FILE_BYTES

MOBILE_TEXT = {
    "de": {"connected": "Smartphone verbunden", "transfer": "Dateien übertragen", "select": "Fotos oder Dateien auswählen", "send": "Senden", "download": "Laden", "show": "Anzeigen", "pc": "Auswahl am PC", "choose_pc": "Wähle auf Windows, ob du Dateien empfangen oder senden möchtest.", "auto": "Der passende Bereich öffnet sich automatisch.", "history": "Übertragungen dieser Sitzung", "waiting": "Warten auf Datei", "transferring": "Datei wird gesendet", "done": "Fertig", "end": "Beenden", "new_transfer": "Neuer Transfer", "switch": "Richtung wechseln"},
    "en": {"connected": "Phone connected", "transfer": "Transfer files", "select": "Select photos or files", "send": "Send", "download": "Download", "show": "Show", "pc": "Choose on your PC", "choose_pc": "Choose on Windows whether to receive or send files.", "auto": "The matching area opens automatically.", "history": "Transfers in this session", "waiting": "Waiting for file", "transferring": "File is being sent", "done": "Done", "end": "End", "new_transfer": "New transfer", "switch": "Switch direction"},
    "tr": {"connected": "Telefon bağlandı", "transfer": "Dosya aktarımı", "select": "Fotoğraf veya dosya seç", "send": "Gönder", "download": "İndir", "show": "Göster", "pc": "Bilgisayarda seçim", "choose_pc": "Windows'ta dosya alma veya gönderme seçeneğini seçin.", "auto": "Uygun bölüm otomatik olarak açılır.", "history": "Bu oturumdaki aktarımlar", "waiting": "Dosya bekleniyor", "transferring": "Dosya gönderiliyor", "done": "Tamamlandı", "end": "Bitir", "new_transfer": "Yeni aktarım", "switch": "Yönü değiştir"},
    "az": {"connected": "Telefon qoşuldu", "transfer": "Faylları köçür", "select": "Foto və ya fayl seç", "send": "Göndər", "download": "Endir", "show": "Göstər", "pc": "Kompüterdə seçim", "choose_pc": "Windows-da fayl qəbul etməyi və ya göndərməyi seçin.", "auto": "Uyğun bölmə avtomatik açılacaq.", "history": "Bu sessiyadakı köçürmələr", "waiting": "Fayl gözlənilir", "transferring": "Fayl göndərilir", "done": "Hazırdır", "end": "Bitir", "new_transfer": "Yeni köçürmə", "switch": "İstiqaməti dəyiş"},
    "ru": {"connected": "Телефон подключён", "transfer": "Передача файлов", "select": "Выберите фото или файлы", "send": "Отправить", "download": "Скачать", "show": "Показать", "pc": "Выбор на компьютере", "choose_pc": "Выберите в Windows: принять или отправить файлы.", "auto": "Нужный раздел откроется автоматически.", "history": "Передачи в этой сессии", "waiting": "Ожидание файла", "transferring": "Файл отправляется", "done": "Готово", "end": "Завершить", "new_transfer": "Новая передача", "switch": "Сменить направление"},
}

MOBILE_TEXT["de"].update(session_ended="Sitzung beendet", session_ended_hint="Du kannst dieses Browserfenster jetzt schließen.")
MOBILE_TEXT["en"].update(session_ended="Session ended", session_ended_hint="You can close this browser window now.")
MOBILE_TEXT["tr"].update(session_ended="Oturum sona erdi", session_ended_hint="Bu tarayıcı penceresini şimdi kapatabilirsiniz.")
MOBILE_TEXT["az"].update(session_ended="Sessiya bitdi", session_ended_hint="İndi bu brauzer pəncərəsini bağlaya bilərsiniz.")
MOBILE_TEXT["ru"].update(session_ended="Сеанс завершён", session_ended_hint="Теперь это окно браузера можно закрыть.")

MOBILE_EXTRA = {
    "de": {
        "direct_transfer": "Direkte Übertragung", "phone_intro": "Wähle deine Dateien aus. CamSend überträgt sie direkt über dein lokales WLAN.",
        "upload_complete": "Upload abgeschlossen", "label_send": "Senden", "multi_select": "Mehrfachauswahl möglich",
        "label_receive": "Empfangen", "no_files": "Warte auf Dateien von Windows.", "activity": "Aktivität",
        "local_connection": "Direkte Verbindung im lokalen WLAN", "transfer_complete": "Übertragung abgeschlossen", "transfer_failed": "Übertragung unterbrochen. Bitte erneut versuchen.",
        "download_complete": "Download abgeschlossen", "connection_established": "Verbindung hergestellt",
        "ready": "Bereit", "local_secure": "Lokale Verbindung", "connect_title": "Smartphone verbinden",
        "connect_intro": "Öffne die Kamera deines Smartphones und scanne den QR-Code. Beide Geräte müssen im selben WLAN sein.",
        "step_camera": "Kamera öffnen", "step_camera_hint": "Keine zusätzliche App erforderlich",
        "step_scan": "Code scannen", "step_scan_hint": "Die Verbindung öffnet sich automatisch",
        "step_transfer": "Dateien übertragen", "step_transfer_hint": "Direkt zwischen deinen Geräten",
        "privacy_title": "Deine Dateien bleiben lokal.", "privacy_hint": "Die Übertragung läuft direkt über dein WLAN.",
        "unknown_type": "Unbekannter Dateityp", "error_invalid": "Diese Verbindung ist abgelaufen oder ungültig.",
        "error_ended": "Diese Sitzung wurde beendet.", "error_in_use": "Mit diesem QR-Code ist bereits ein anderes Smartphone verbunden.",
        "error_mode": "Unbekannter Übertragungsmodus", "error_filename": "Dateiname fehlt", "error_too_large": "Die Datei ist größer als 2 GB.",
        "error_network": "Keine geeignete lokale Netzwerkadresse gefunden. Verbinde den PC mit einem WLAN oder LAN.",
        "file_label": "DATEI", "qr_alt": "QR-Code zur Verbindung", "error_heading": "Fehler",
    },
    "en": {
        "direct_transfer": "Direct transfer", "phone_intro": "Choose your files. CamSend transfers them directly over your local Wi-Fi.",
        "upload_complete": "Upload complete", "label_send": "Send", "multi_select": "Multiple selection available",
        "label_receive": "Receive", "no_files": "Waiting for files from Windows.", "activity": "Activity",
        "local_connection": "Direct connection over local Wi-Fi", "transfer_complete": "Transfer complete", "transfer_failed": "Transfer interrupted. Please try again.",
        "download_complete": "Download complete", "connection_established": "Connection established",
        "ready": "Ready", "local_secure": "Local connection", "connect_title": "Connect phone",
        "connect_intro": "Open your phone camera and scan the QR code. Both devices must use the same Wi-Fi.",
        "step_camera": "Open camera", "step_camera_hint": "No additional app required",
        "step_scan": "Scan code", "step_scan_hint": "The connection opens automatically",
        "step_transfer": "Transfer files", "step_transfer_hint": "Directly between your devices",
        "privacy_title": "Your files stay local.", "privacy_hint": "The transfer runs directly over your Wi-Fi.",
        "unknown_type": "Unknown file type", "error_invalid": "This connection has expired or is invalid.",
        "error_ended": "This session has ended.", "error_in_use": "Another phone is already connected with this QR code.",
        "error_mode": "Unknown transfer mode", "error_filename": "File name is missing", "error_too_large": "The file is larger than 2 GB.",
        "error_network": "No suitable local network address was found. Connect the PC to Wi-Fi or LAN.",
        "file_label": "FILE", "qr_alt": "QR code for connection", "error_heading": "Error",
    },
    "tr": {
        "direct_transfer": "Doğrudan aktarım", "phone_intro": "Dosyalarınızı seçin. CamSend onları yerel Wi-Fi ağınız üzerinden doğrudan aktarır.",
        "upload_complete": "Yükleme tamamlandı", "label_send": "Gönder", "multi_select": "Birden fazla dosya seçilebilir",
        "label_receive": "Al", "no_files": "Windows'tan dosya bekleniyor.", "activity": "Etkinlik",
        "local_connection": "Yerel Wi-Fi üzerinden doğrudan bağlantı", "transfer_complete": "Aktarım tamamlandı", "transfer_failed": "Aktarım kesildi. Lütfen tekrar deneyin.",
        "download_complete": "İndirme tamamlandı", "connection_established": "Bağlantı kuruldu",
        "ready": "Hazır", "local_secure": "Yerel bağlantı", "connect_title": "Telefonu bağla",
        "connect_intro": "Telefon kameranızı açın ve QR kodunu tarayın. İki cihaz aynı Wi-Fi ağında olmalıdır.",
        "step_camera": "Kamerayı aç", "step_camera_hint": "Ek uygulama gerekmez",
        "step_scan": "Kodu tara", "step_scan_hint": "Bağlantı otomatik olarak açılır",
        "step_transfer": "Dosyaları aktar", "step_transfer_hint": "Doğrudan cihazlarınız arasında",
        "privacy_title": "Dosyalarınız yerelde kalır.", "privacy_hint": "Aktarım doğrudan Wi-Fi ağınız üzerinden gerçekleşir.",
        "unknown_type": "Bilinmeyen dosya türü", "error_invalid": "Bu bağlantının süresi dolmuş veya bağlantı geçersiz.",
        "error_ended": "Bu oturum sona erdi.", "error_in_use": "Bu QR koduyla başka bir telefon zaten bağlı.",
        "error_mode": "Bilinmeyen aktarım modu", "error_filename": "Dosya adı eksik", "error_too_large": "Dosya 2 GB'tan büyük.",
        "error_network": "Uygun bir yerel ağ adresi bulunamadı. Bilgisayarı Wi-Fi veya LAN'a bağlayın.",
        "file_label": "DOSYA", "qr_alt": "Bağlantı için QR kodu", "error_heading": "Hata",
    },
    "az": {
        "direct_transfer": "Birbaşa köçürmə", "phone_intro": "Fayllarınızı seçin. CamSend onları yerli Wi-Fi şəbəkəniz üzərindən birbaşa köçürür.",
        "upload_complete": "Yükləmə tamamlandı", "label_send": "Göndər", "multi_select": "Bir neçə fayl seçmək mümkündür",
        "label_receive": "Qəbul et", "no_files": "Windows-dan fayllar gözlənilir.", "activity": "Fəaliyyət",
        "local_connection": "Yerli Wi-Fi üzərindən birbaşa bağlantı", "transfer_complete": "Köçürmə tamamlandı", "transfer_failed": "Köçürmə dayandırıldı. Yenidən cəhd edin.",
        "download_complete": "Endirmə tamamlandı", "connection_established": "Bağlantı quruldu",
        "ready": "Hazır", "local_secure": "Yerli bağlantı", "connect_title": "Telefonu qoş",
        "connect_intro": "Telefon kamerasını açın və QR kodu skan edin. Hər iki cihaz eyni Wi-Fi şəbəkəsində olmalıdır.",
        "step_camera": "Kameranı aç", "step_camera_hint": "Əlavə tətbiq tələb olunmur",
        "step_scan": "Kodu skan et", "step_scan_hint": "Bağlantı avtomatik açılır",
        "step_transfer": "Faylları köçür", "step_transfer_hint": "Birbaşa cihazlarınız arasında",
        "privacy_title": "Fayllarınız lokal qalır.", "privacy_hint": "Köçürmə birbaşa Wi-Fi şəbəkəniz üzərindən gedir.",
        "unknown_type": "Naməlum fayl növü", "error_invalid": "Bu bağlantının vaxtı bitib və ya etibarsızdır.",
        "error_ended": "Bu sessiya bitib.", "error_in_use": "Bu QR kodla artıq başqa telefon qoşulub.",
        "error_mode": "Naməlum köçürmə rejimi", "error_filename": "Fayl adı yoxdur", "error_too_large": "Fayl 2 GB-dan böyükdür.",
        "error_network": "Uyğun yerli şəbəkə ünvanı tapılmadı. Kompüteri Wi-Fi və ya LAN-a qoşun.",
        "file_label": "FAYL", "qr_alt": "Bağlantı üçün QR kod", "error_heading": "Xəta",
    },
    "ru": {
        "direct_transfer": "Прямая передача", "phone_intro": "Выберите файлы. CamSend передаст их напрямую через вашу локальную сеть Wi-Fi.",
        "upload_complete": "Загрузка завершена", "label_send": "Отправить", "multi_select": "Можно выбрать несколько файлов",
        "label_receive": "Получить", "no_files": "Ожидание файлов из Windows.", "activity": "Активность",
        "local_connection": "Прямое подключение по локальной сети Wi-Fi", "transfer_complete": "Передача завершена", "transfer_failed": "Передача прервана. Повторите попытку.",
        "download_complete": "Скачивание завершено", "connection_established": "Соединение установлено",
        "ready": "Готово", "local_secure": "Локальное подключение", "connect_title": "Подключить телефон",
        "connect_intro": "Откройте камеру телефона и отсканируйте QR-код. Оба устройства должны быть в одной сети Wi-Fi.",
        "step_camera": "Открыть камеру", "step_camera_hint": "Дополнительное приложение не требуется",
        "step_scan": "Сканировать код", "step_scan_hint": "Соединение откроется автоматически",
        "step_transfer": "Передать файлы", "step_transfer_hint": "Напрямую между вашими устройствами",
        "privacy_title": "Ваши файлы остаются локальными.", "privacy_hint": "Передача выполняется напрямую через вашу сеть Wi-Fi.",
        "unknown_type": "Неизвестный тип файла", "error_invalid": "Срок действия подключения истёк или оно недействительно.",
        "error_ended": "Этот сеанс завершён.", "error_in_use": "По этому QR-коду уже подключён другой телефон.",
        "error_mode": "Неизвестный режим передачи", "error_filename": "Отсутствует имя файла", "error_too_large": "Размер файла превышает 2 ГБ.",
        "error_network": "Подходящий локальный сетевой адрес не найден. Подключите компьютер к Wi-Fi или LAN.",
        "file_label": "ФАЙЛ", "qr_alt": "QR-код для подключения", "error_heading": "Ошибка",
    },
}
for language_code, extra_text in MOBILE_EXTRA.items():
    MOBILE_TEXT[language_code].update(extra_text)

MOBILE_TEXT_SHARING = {
    "de": {
        "text_label": "Text & Links", "text_title": "Mit dem PC teilen",
        "text_placeholder": "Text oder Link eingeben …", "text_send": "Senden",
        "text_copy": "Kopieren", "text_copied": "Kopiert", "text_copy_failed": "Bitte Text markieren und kopieren.",
        "text_empty": "Noch keine Texte oder Links.", "text_from_pc": "Vom PC", "text_from_phone": "Von diesem Smartphone",
        "text_too_long": "Der Text ist zu lang (max. 10.000 Zeichen).", "text_failed": "Senden fehlgeschlagen. Bitte erneut versuchen.",
    },
    "en": {
        "text_label": "Text & links", "text_title": "Share with the PC",
        "text_placeholder": "Enter text or a link …", "text_send": "Send",
        "text_copy": "Copy", "text_copied": "Copied", "text_copy_failed": "Please select the text and copy it.",
        "text_empty": "No texts or links yet.", "text_from_pc": "From the PC", "text_from_phone": "From this phone",
        "text_too_long": "The text is too long (max. 10,000 characters).", "text_failed": "Sending failed. Please try again.",
    },
    "tr": {
        "text_label": "Metin ve bağlantılar", "text_title": "Bilgisayarla paylaş",
        "text_placeholder": "Metin veya bağlantı girin …", "text_send": "Gönder",
        "text_copy": "Kopyala", "text_copied": "Kopyalandı", "text_copy_failed": "Lütfen metni seçip kopyalayın.",
        "text_empty": "Henüz metin veya bağlantı yok.", "text_from_pc": "Bilgisayardan", "text_from_phone": "Bu telefondan",
        "text_too_long": "Metin çok uzun (en fazla 10.000 karakter).", "text_failed": "Gönderilemedi. Lütfen tekrar deneyin.",
    },
    "az": {
        "text_label": "Mətn və linklər", "text_title": "Kompüterlə paylaş",
        "text_placeholder": "Mətn və ya link daxil edin …", "text_send": "Göndər",
        "text_copy": "Kopyala", "text_copied": "Kopyalandı", "text_copy_failed": "Zəhmət olmasa mətni seçib kopyalayın.",
        "text_empty": "Hələ mətn və ya link yoxdur.", "text_from_pc": "Kompüterdən", "text_from_phone": "Bu telefondan",
        "text_too_long": "Mətn çox uzundur (maks. 10.000 simvol).", "text_failed": "Göndərmək alınmadı. Yenidən cəhd edin.",
    },
    "ru": {
        "text_label": "Текст и ссылки", "text_title": "Обмен с компьютером",
        "text_placeholder": "Введите текст или ссылку …", "text_send": "Отправить",
        "text_copy": "Копировать", "text_copied": "Скопировано", "text_copy_failed": "Выделите текст и скопируйте его.",
        "text_empty": "Пока нет текстов или ссылок.", "text_from_pc": "С компьютера", "text_from_phone": "С этого телефона",
        "text_too_long": "Текст слишком длинный (макс. 10 000 символов).", "text_failed": "Не удалось отправить. Повторите попытку.",
    },
}
for language_code, sharing_text in MOBILE_TEXT_SHARING.items():
    MOBILE_TEXT[language_code].update(sharing_text)

# Files handed over by a second CamSend process (Explorer "Send with CamSend").
# The HTTP handler only enqueues; the Tk main thread drains the queue in poll(),
# because Tk must not be touched from the server thread.
local_offer_queue: "queue.Queue[list[str]]" = queue.Queue()
local_handoff_key: str | None = None

session_token = secrets.token_urlsafe(24)
session_created = time.time()
session_lock = threading.Lock()
session_state = {
    "connected": False, "last_seen": 0.0, "mode": None, "device": None,
    "device_ip": None, "device_key": None, "paired": False,
    "receive_dir": str(TRANSFER_DIR),
    "language": "de",
    "ended": False, "offered_files": [], "history": [], "messages": [],
    "transfer": {"active": False, "name": "", "done": 0, "total": 0, "direction": ""},
}


def new_session() -> str:
    """Invalidate the old QR link and create a fresh pairing session."""
    global session_token, session_created, session_state
    with session_lock:
        session_token = secrets.token_urlsafe(24)
        session_created = time.time()
        session_state = {
            "connected": False, "last_seen": 0.0, "mode": None, "device": None,
            "device_ip": None, "device_key": None, "paired": False,
            "receive_dir": str(TRANSFER_DIR),
            "language": "de",
            "ended": False, "offered_files": [], "history": [], "messages": [],
            "transfer": {"active": False, "name": "", "done": 0, "total": 0, "direction": ""},
        }
    return session_token


def phone_url() -> str:
    return f"http://{local_ip()}:{PORT}/connect/{session_token}"


def local_ip() -> str:
    candidates: list[str] = []

    def add_candidate(address: str) -> None:
        try:
            parsed = ipaddress.ip_address(address)
        except ValueError:
            return
        if not isinstance(parsed, ipaddress.IPv4Address):
            return
        if parsed.is_loopback or parsed.is_link_local or parsed.is_multicast or parsed.is_unspecified:
            return
        if address not in candidates:
            candidates.append(address)

    try:
        for result in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET, socket.SOCK_DGRAM):
            add_candidate(result[4][0])
    except OSError:
        pass

    # UDP connect only asks the local routing table which interface it would use;
    # it sends no packet. TEST-NET is reserved for documentation and is not an
    # external availability dependency.
    route_address = None
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("192.0.2.1", 9))
        route_address = sock.getsockname()[0]
        add_candidate(route_address)
    except OSError:
        pass
    finally:
        sock.close()

    if route_address in candidates:
        return route_address
    if candidates:
        return candidates[0]
    raise RuntimeError("No usable local IPv4 address was found")


def session_is_valid(token: str) -> bool:
    with session_lock:
        # Compare bytes: compare_digest raises TypeError for non-ASCII str input,
        # which turned a garbage token in the URL into a 500 instead of a 403.
        if not secrets.compare_digest(token.encode("utf-8"), session_token.encode("utf-8")):
            return False
        # An unused QR code expires after 15 minutes. Once a device has paired,
        # the session stays valid until Windows creates a new one or either side
        # explicitly ends it.
        return session_state["paired"] or time.time() - session_created <= SESSION_TTL_SECONDS


def tr(key: str) -> str:
    language = session_state.get("language", "en")
    return MOBILE_TEXT.get(language, MOBILE_TEXT["en"])[key]


def request_has_device_key() -> bool:
    """True if the request carries the cookie issued to the paired browser.

    Caller must hold session_lock.
    """
    expected = session_state["device_key"]
    supplied = request.cookies.get(DEVICE_COOKIE, "")
    return bool(expected) and secrets.compare_digest(supplied.encode("utf-8"), expected.encode("utf-8"))


def is_loopback_request() -> bool:
    try:
        return ipaddress.ip_address(request.remote_addr or "").is_loopback
    except ValueError:
        return False


def require_session(token: str, allow_ended: bool = False) -> None:
    if not session_is_valid(token):
        abort(403, tr("error_invalid"))
    # The token alone is not enough after pairing: it travels in the QR code and in
    # plain-HTTP URLs. Every API call must also come from the browser that paired.
    with session_lock:
        paired_device = request_has_device_key()
    if not paired_device:
        abort(403, tr("error_invalid"))
    if session_state["ended"] and not allow_ended:
        abort(410, tr("error_ended"))


def touch_session() -> None:
    session_state["connected"] = True
    session_state["last_seen"] = time.time()


def file_details():
    items = sorted(
        (item for item in TRANSFER_DIR.iterdir() if item.is_file()),
        key=lambda item: item.stat().st_mtime,
        reverse=True,
    )
    return [
        {
            "name": item.name,
            "size": item.stat().st_size,
            "size_text": format_bytes(item.stat().st_size),
            "type": mimetypes.guess_type(item.name)[0] or tr("unknown_type"),
        }
        for item in items
    ]


def session_file_details():
    with session_lock:
        offered = set(session_state["offered_files"])
    return [item for item in file_details() if item["name"] in offered]


def add_history(name: str, total: int, direction: str, status: str = "waiting") -> dict:
    item = {
        "id": secrets.token_hex(8), "name": name,
        "type": mimetypes.guess_type(name)[0] or "application/octet-stream",
        "size": total, "size_text": format_bytes(total), "direction": direction,
        "status": status, "done": 0, "total": total,
    }
    session_state["history"].append(item)
    return item


def update_history(item_id: str, **values) -> None:
    for item in session_state["history"]:
        if item["id"] == item_id:
            item.update(values)
            break


def prepare_text(value) -> tuple[str | None, str | None]:
    """Normalise a shared text. Returns (text, None) or (None, error_key)."""
    if not isinstance(value, str):
        return None, "text_failed"
    text = value.replace("\r\n", "\n").replace("\r", "\n")
    if not text.strip():
        return None, "text_empty"
    if len(text) > MAX_TEXT_CHARS:
        return None, "text_too_long"
    return text, None


def add_message(sender: str, text: str) -> dict:
    """Store a text/link message. Caller must hold session_lock."""
    item = {"id": secrets.token_hex(8), "from": sender, "text": text, "time": time.time()}
    messages = session_state["messages"]
    messages.append(item)
    # Keep memory bounded for long sessions; older messages simply scroll away.
    del messages[:-MAX_TEXT_MESSAGES]
    return item


def enable_local_handoff() -> None:
    """Accept files from a second CamSend process started via Explorer.

    The key file lives in the user's profile, so only processes of this Windows
    user can read it. The key (sent as a custom header) also stops web pages in the
    PC's browser from posting to the loopback endpoint (CSRF): they cannot read the
    file and a custom header forces a CORS preflight the server never answers.
    """
    global local_handoff_key
    local_handoff_key = secrets.token_urlsafe(32)
    INSTANCE_KEY_PATH.parent.mkdir(parents=True, exist_ok=True)
    INSTANCE_KEY_PATH.write_text(f"{PORT}\n{local_handoff_key}\n", encoding="utf-8")


def disable_local_handoff() -> None:
    global local_handoff_key
    try:
        # Only remove the file if it is still ours; a newer instance may own it.
        if local_handoff_key and INSTANCE_KEY_PATH.read_text(encoding="utf-8").split()[1:2] == [local_handoff_key]:
            INSTANCE_KEY_PATH.unlink()
    except (OSError, IndexError):
        pass
    local_handoff_key = None


def format_bytes(size: int) -> str:
    value = float(size)
    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024 or unit == "GB":
            return f"{value:.0f} {unit}" if unit == "B" else f"{value:.1f} {unit}"
        value /= 1024


def sanitize_filename(value: str) -> str:
    """Return a Windows-safe filename while preserving international text."""
    decoded = unicodedata.normalize("NFC", unquote(value or ""))
    name = decoded.replace("\\", "/").rsplit("/", 1)[-1]
    name = "".join(
        "" if character in '<>:"/\\|?*' or ord(character) < 32 else character
        for character in name
    )
    name = re.sub(r"\s+", "_", name)
    name = re.sub(r"_+", "_", name).strip(" .")
    if name in {"", ".", ".."}:
        return ""

    suffix = Path(name).suffix
    stem = name[:-len(suffix)] if suffix else name
    reserved = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}
    if stem.upper() in reserved:
        stem = f"_{stem}"
    maximum_stem = max(1, 240 - len(suffix))
    return f"{stem[:maximum_stem].rstrip(' .')}{suffix}"


@app.get("/")
def index():
    # The desktop page embeds the QR code, i.e. the live session token. The server
    # listens on 0.0.0.0, so without this check any device on the Wi-Fi could read it.
    if not is_loopback_request():
        abort(404)
    language = session_state.get("language", "en")
    return render_template("index.html", language=language, t=MOBILE_TEXT[language])


@app.get("/brand/logo.png")
def brand_logo():
    return send_from_directory(BRAND_PATH.parent, BRAND_PATH.name, max_age=3600)


@app.get("/qr.png")
def qr_code():
    if not is_loopback_request():
        abort(404)
    try:
        url = phone_url()
    except RuntimeError:
        abort(503, tr("error_network"))
    image = qrcode.make(url)
    output = io.BytesIO()
    image.save(output, format="PNG")
    output.seek(0)
    return app.response_class(output.getvalue(), mimetype="image/png")


@app.get("/connect/<token>")
def connect(token: str):
    # /connect is the pairing step, so it only checks the token here; the device
    # check below decides who may pair.
    if not session_is_valid(token):
        abort(403, tr("error_invalid"))
    with session_lock:
        known_device = request_has_device_key()
        if session_state["ended"]:
            if not known_device:
                abort(403, tr("error_invalid"))
            language = session_state["language"]
            return render_template("ended.html", language=language, t=MOBILE_TEXT[language]), 410
        # Once paired, the session belongs to that browser (cookie). A second browser
        # on the same address (e.g. QR opened in an in-app browser, then in Chrome)
        # may re-pair; any other device is refused for the rest of the session, even
        # if the phone went quiet. Windows offers "Connect another phone" for that.
        if session_state["paired"] and not known_device and session_state["device_ip"] != request.remote_addr:
            abort(409, tr("error_in_use"))
        if not known_device:
            # A new key also locks out a previously paired browser on the same address.
            session_state["device_key"] = secrets.token_urlsafe(24)
        device_key = session_state["device_key"]
        touch_session()
        session_state["device_ip"] = request.remote_addr
        session_state["device"] = request.headers.get("User-Agent", "Smartphone")[:160]
        session_state["paired"] = True
        mode = session_state["mode"]
        language = session_state["language"]
    if mode is None:
        page = render_template("waiting.html", token=token, language=language, t=MOBILE_TEXT[language])
    else:
        page = render_template("phone.html", token=token, files=session_file_details(), mode=mode, language=language, t=MOBILE_TEXT[language])
    response = make_response(page)
    # Lax (not Strict): the cookie must still be sent when the phone reopens the
    # link from the camera app, which is a cross-site top-level navigation.
    response.set_cookie(DEVICE_COOKIE, device_key, httponly=True, samesite="Lax", path="/")
    return response


@app.post("/api/heartbeat/<token>")
def heartbeat(token: str):
    require_session(token, allow_ended=True)
    with session_lock:
        if session_state["ended"]:
            return {"ok": False, "ended": True}, 410
        touch_session()
    return {"ok": True}


@app.get("/api/session/<token>")
def session_status(token: str):
    require_session(token, allow_ended=True)
    with session_lock:
        active = session_state["connected"] and time.time() - session_state["last_seen"] < HEARTBEAT_TIMEOUT_SECONDS
        if not active:
            session_state["connected"] = False
        return {
            "connected": active,
            "mode": session_state["mode"],
            "ended": session_state["ended"],
            "language": session_state["language"],
            "offered_files": list(session_state["offered_files"]),
            "history": [dict(item) for item in session_state["history"]],
            "transfer": dict(session_state["transfer"]),
        }


@app.post("/api/mode/<token>/<mode>")
def select_mode(token: str, mode: str):
    require_session(token)
    if mode not in {"receive", "send"}:
        abort(400, tr("error_mode"))
    with session_lock:
        session_state["mode"] = mode
    return {"ok": True, "mode": mode}


@app.post("/api/end/<token>")
def end_session(token: str):
    require_session(token)
    with session_lock:
        session_state["ended"] = True
        session_state["connected"] = False
    return {"ok": True}


@app.post("/api/next/<token>")
def next_transfer(token: str):
    require_session(token)
    with session_lock:
        session_state["transfer"] = {"active": False, "name": "", "done": 0, "total": 0, "direction": ""}
    return {"ok": True}


@app.post("/api/switch/<token>")
def switch_direction(token: str):
    require_session(token)
    with session_lock:
        session_state["mode"] = "send" if session_state["mode"] == "receive" else "receive"
        session_state["transfer"] = {"active": False, "name": "", "done": 0, "total": 0, "direction": ""}
    return {"ok": True, "mode": session_state["mode"]}


@app.post("/upload-file/<token>")
def upload_file(token: str):
    require_session(token)
    name = sanitize_filename(request.headers.get("X-Filename", ""))
    if not name:
        abort(400, tr("error_filename"))
    with session_lock:
        receive_dir = Path(session_state.get("receive_dir", str(TRANSFER_DIR)))
    receive_dir.mkdir(parents=True, exist_ok=True)
    target = receive_dir / name
    stem, suffix = target.stem, target.suffix
    counter = 1
    while target.exists():
        target = receive_dir / f"{stem}-{counter}{suffix}"
        counter += 1
    total = request.content_length or 0
    with session_lock:
        history_item = add_history(target.name, total, "receive", "transferring")
        session_state["transfer"] = {"active": True, "name": target.name, "done": 0, "total": total, "direction": "receive"}
    done = 0
    try:
        with target.open("wb") as output:
            while chunk := request.stream.read(1024 * 1024):
                output.write(chunk)
                done += len(chunk)
                with session_lock:
                    session_state["transfer"]["done"] = done
                    update_history(history_item["id"], done=done)
    except Exception:
        try:
            target.unlink(missing_ok=True)
        finally:
            with session_lock:
                session_state["transfer"] = {"active": False, "name": "", "done": 0, "total": 0, "direction": ""}
                session_state["history"] = [item for item in session_state["history"] if item["id"] != history_item["id"]]
        raise
    with session_lock:
        session_state["transfer"]["active"] = False
        update_history(history_item["id"], done=done, status="done")
    return {"ok": True, "name": target.name}


@app.get("/download-file/<token>/<path:name>")
def download_file(token: str, name: str):
    require_session(token)
    # Werkzeug has already URL-decoded the path segment. Windows offers files under
    # their real names (spaces, "%", "__" ...), so the name must match the offered
    # list exactly; re-sanitizing or decoding it again would break those downloads.
    # The exact membership check is the access control: only names Windows put
    # into the list (plain file names inside TRANSFER_DIR) can ever be served.
    safe_name = name
    if not safe_name or Path(safe_name).name != safe_name or "\\" in safe_name:
        abort(404)
    with session_lock:
        if safe_name not in session_state["offered_files"]:
            abort(404)
    path = TRANSFER_DIR / safe_name
    if not path.is_file():
        abort(404)
    total = path.stat().st_size
    with session_lock:
        history_item = next((item for item in session_state["history"] if item["name"] == safe_name and item["direction"] == "send"), None)
        if history_item is None:
            history_item = add_history(safe_name, total, "send")
        update_history(history_item["id"], status="transferring")
        session_state["transfer"] = {"active": True, "name": safe_name, "done": 0, "total": total, "direction": "send"}

    @stream_with_context
    def chunks():
        done = 0
        completed = total == 0
        try:
            with path.open("rb") as source:
                while chunk := source.read(1024 * 1024):
                    done += len(chunk)
                    completed = done >= total
                    with session_lock:
                        session_state["transfer"]["done"] = done
                        update_history(history_item["id"], done=done)
                    yield chunk
        finally:
            with session_lock:
                session_state["transfer"]["active"] = False
                if completed:
                    update_history(history_item["id"], done=done, status="done")
                    if safe_name in session_state["offered_files"]:
                        session_state["offered_files"].remove(safe_name)
                else:
                    session_state["transfer"]["done"] = 0
                    update_history(history_item["id"], done=0, status="waiting")

    fallback_name = ascii_secure_filename(safe_name) or "download"
    encoded_name = quote(safe_name, safe="")
    return Response(chunks(), headers={
        "Content-Length": str(total),
        "Content-Disposition": f'attachment; filename="{fallback_name}"; filename*=UTF-8\'\'{encoded_name}',
        "Content-Type": mimetypes.guess_type(safe_name)[0] or "application/octet-stream",
    })


@app.get("/api/texts/<token>")
def list_texts(token: str):
    require_session(token)
    with session_lock:
        return {"messages": [dict(item) for item in session_state["messages"]]}


@app.post("/api/texts/<token>")
def send_text(token: str):
    require_session(token)
    if (request.content_length or 0) > MAX_JSON_BYTES:
        return {"ok": False, "error": "text_too_long"}, 413
    payload = request.get_json(silent=True) or {}
    text, error = prepare_text(payload.get("text"))
    if error:
        return {"ok": False, "error": error}, 400
    with session_lock:
        item = add_message("phone", text)
        touch_session()
    return {"ok": True, "message": dict(item)}


@app.post("/local/offer")
def local_offer():
    # Only another CamSend process of this Windows user may hand over files; see
    # enable_local_handoff() for why both checks are needed.
    if not is_loopback_request() or not local_handoff_key:
        abort(404)
    supplied = request.headers.get("X-CamSend-Key", "")
    if not secrets.compare_digest(supplied.encode("utf-8"), local_handoff_key.encode("utf-8")):
        abort(403)
    if (request.content_length or 0) > MAX_JSON_BYTES:
        abort(413)
    payload = request.get_json(silent=True) or {}
    paths = payload.get("paths")
    if not isinstance(paths, list):
        abort(400)
    files = [str(Path(value)) for value in paths if isinstance(value, str) and Path(value).is_file()]
    if files:
        local_offer_queue.put(files)
    return {"ok": True, "accepted": len(files)}


@app.errorhandler(400)
@app.errorhandler(403)
@app.errorhandler(409)
@app.errorhandler(410)
@app.errorhandler(413)
@app.errorhandler(503)
def localized_error(error):
    language = session_state.get("language", "en")
    message = tr("error_too_large") if error.code == 413 else str(error.description)
    return render_template(
        "error.html", language=language, t=MOBILE_TEXT[language], message=message
    ), error.code


if __name__ == "__main__":
    print(f"CamSend läuft: http://localhost:{PORT}")
    try:
        print(f"Smartphone-Adresse: {phone_url()}")
    except RuntimeError:
        print("Smartphone-Adresse nicht verfügbar: PC mit WLAN oder LAN verbinden.")
    app.run(host="0.0.0.0", port=PORT, debug=False)
