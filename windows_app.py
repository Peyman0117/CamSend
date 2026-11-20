from __future__ import annotations

import json
import os
import locale
import math
import mimetypes
import queue
import re
import shutil
import sys
import threading
import time
import tkinter as tk
import urllib.request
import webbrowser
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from tkinter import filedialog, messagebox
from tkinter import font as tkfont
from urllib.parse import urlparse

import qrcode
from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageTk
from werkzeug.serving import make_server

import app as transfer
import shell_integration
from camsend_version import VERSION


BG = "#eaf2fa"
PANEL = "#ffffff"
TEXT = "#0a213d"
MUTED = "#667a91"
BLUE = "#146bff"
BLUE_DARK = "#0752d4"
SOFT = "#f5f9fd"
BORDER = "#dbe6f1"
GREEN = "#0a9b70"

WORDS = {
    "de": {
        "connect": "Smartphone verbinden", "scan": "Kamera öffnen und QR-Code scannen\nBeide Geräte müssen im selben WLAN sein",
        "waiting": "Warte auf Smartphone …", "connected": "Smartphone verbunden", "question": "Was möchtest du machen?",
        "receive": "Vom Smartphone empfangen", "send": "An das Smartphone senden", "other": "＋ Anderes Handy verbinden",
        "destination": "Zielordner für empfangene Dateien wählen", "select": "Eine oder mehrere Dateien auswählen",
        "receiving": "Empfangen vom Smartphone", "sending": "Senden an Smartphone", "location": "Speicherort",
        "ready": "Datei(en) bereit", "await": "Warte auf Übertragung …", "done": "fertig",
        "ended": "Verbindung beendet", "ended_text": "Die Browserseite wurde geschlossen oder das Smartphone ist nicht mehr erreichbar.",
        "new": "＋ Neues Handy verbinden",
        "history": "Übertragungen dieser Sitzung", "status_waiting": "Warten auf Datei", "status_transferring": "Datei wird gesendet", "status_done": "Fertig", "show": "Anzeigen", "more": "Weitere Dateien senden", "end": "Beenden",
        "start": "Bereit für eine Verbindung", "start_text": "Verbinde ein Smartphone ohne App direkt über das lokale WLAN.", "new_connection": "Neue Verbindung",
        "status_accept": "Warte auf Annahme am Smartphone",
        "new_transfer": "＋ Neuer Transfer",
        "copy_link": "Link kopieren", "copied": "Link wurde kopiert",
        "switch": "Richtung wechseln",
        "unknown_file": "Datei", "server_error": "Server konnte nicht gestartet werden",
        "network_error": "Keine geeignete lokale Netzwerkadresse gefunden. Verbinde den PC mit einem WLAN oder LAN und versuche es erneut.",
        "retry": "Erneut versuchen",
    },
    "en": {
        "connect": "Connect phone", "scan": "Open Camera and scan the QR code\nBoth devices must use the same Wi-Fi",
        "waiting": "Waiting for phone …", "connected": "Phone connected", "question": "What would you like to do?",
        "receive": "Receive from phone", "send": "Send to phone", "other": "＋ Connect another phone",
        "destination": "Choose a folder for received files", "select": "Select one or more files",
        "receiving": "Receiving from phone", "sending": "Sending to phone", "location": "Save location",
        "ready": "file(s) ready", "await": "Waiting for transfer …", "done": "done",
        "ended": "Connection ended", "ended_text": "The browser page was closed or the phone is no longer reachable.",
        "new": "＋ Connect a new phone",
        "history": "Transfers in this session", "status_waiting": "Waiting for file", "status_transferring": "File is being sent", "status_done": "Done", "show": "Show", "more": "Send more files", "end": "End",
        "start": "Ready to connect", "start_text": "Connect a phone without an app over your local Wi-Fi.", "new_connection": "New connection",
        "status_accept": "Waiting for acceptance on the phone",
        "new_transfer": "＋ New transfer",
        "copy_link": "Copy link", "copied": "Link copied",
        "switch": "Switch direction",
        "unknown_file": "File", "server_error": "The server could not be started",
        "network_error": "No suitable local network address was found. Connect the PC to Wi-Fi or LAN and try again.",
        "retry": "Try again",
    },
    "tr": {
        "connect": "Telefonu bağla", "scan": "Kamerayı açın ve QR kodunu tarayın\nİki cihaz aynı Wi-Fi ağında olmalı",
        "waiting": "Telefon bekleniyor …", "connected": "Telefon bağlandı", "question": "Ne yapmak istersiniz?",
        "receive": "Telefondan al", "send": "Telefona gönder", "other": "＋ Başka telefon bağla",
        "destination": "Alınan dosyalar için klasör seçin", "select": "Bir veya daha fazla dosya seçin",
        "receiving": "Telefondan alınıyor", "sending": "Telefona gönderiliyor", "location": "Kayıt konumu",
        "ready": "dosya hazır", "await": "Aktarım bekleniyor …", "done": "tamamlandı",
        "ended": "Bağlantı sona erdi", "ended_text": "Tarayıcı kapatıldı veya telefona artık ulaşılamıyor.", "new": "＋ Yeni telefon bağla",
        "history": "Bu oturumdaki aktarımlar", "status_waiting": "Dosya bekleniyor", "status_transferring": "Dosya gönderiliyor", "status_done": "Tamamlandı", "show": "Göster", "more": "Daha fazla dosya gönder", "end": "Bitir",
        "start": "Bağlantıya hazır", "start_text": "Telefonu uygulama olmadan yerel Wi-Fi üzerinden bağlayın.", "new_connection": "Yeni bağlantı",
        "status_accept": "Telefonda kabul bekleniyor",
        "new_transfer": "＋ Yeni aktarım",
        "copy_link": "Bağlantıyı kopyala", "copied": "Bağlantı kopyalandı",
        "switch": "Yönü değiştir",
        "unknown_file": "Dosya", "server_error": "Sunucu başlatılamadı",
        "network_error": "Uygun bir yerel ağ adresi bulunamadı. Bilgisayarı Wi-Fi veya LAN'a bağlayıp yeniden deneyin.",
        "retry": "Yeniden dene",
    },
    "az": {
        "connect": "Telefonu qoş", "scan": "Kameranı açın və QR kodu skan edin\nHər iki cihaz eyni Wi-Fi şəbəkəsində olmalıdır",
        "waiting": "Telefon gözlənilir …", "connected": "Telefon qoşuldu", "question": "Nə etmək istəyirsiniz?",
        "receive": "Telefondan qəbul et", "send": "Telefona göndər", "other": "＋ Başqa telefon qoş",
        "destination": "Qəbul edilən fayllar üçün qovluq seçin", "select": "Bir və ya bir neçə fayl seçin",
        "receiving": "Telefondan qəbul edilir", "sending": "Telefona göndərilir", "location": "Saxlama yeri",
        "ready": "fayl hazırdır", "await": "Köçürmə gözlənilir …", "done": "tamamlandı",
        "ended": "Bağlantı bitdi", "ended_text": "Brauzer bağlandı və ya telefon artıq əlçatan deyil.", "new": "＋ Yeni telefon qoş",
        "history": "Bu sessiyadakı köçürmələr", "status_waiting": "Fayl gözlənilir", "status_transferring": "Fayl göndərilir", "status_done": "Hazırdır", "show": "Göstər", "more": "Daha çox fayl göndər", "end": "Bitir",
        "start": "Qoşulmağa hazırdır", "start_text": "Telefonu tətbiqsiz yerli Wi-Fi üzərindən qoşun.", "new_connection": "Yeni bağlantı",
        "status_accept": "Telefonda qəbul gözlənilir",
        "new_transfer": "＋ Yeni köçürmə",
        "copy_link": "Linki kopyala", "copied": "Link kopyalandı",
        "switch": "İstiqaməti dəyiş",
        "unknown_file": "Fayl", "server_error": "Serveri başlatmaq mümkün olmadı",
        "network_error": "Uyğun yerli şəbəkə ünvanı tapılmadı. Kompüteri Wi-Fi və ya LAN-a qoşub yenidən cəhd edin.",
        "retry": "Yenidən cəhd et",
    },
    "ru": {
        "connect": "Подключить телефон", "scan": "Откройте камеру и отсканируйте QR-код\nОба устройства должны быть в одной сети Wi-Fi",
        "waiting": "Ожидание телефона …", "connected": "Телефон подключён", "question": "Что вы хотите сделать?",
        "receive": "Получить с телефона", "send": "Отправить на телефон", "other": "＋ Подключить другой телефон",
        "destination": "Выберите папку для полученных файлов", "select": "Выберите один или несколько файлов",
        "receiving": "Получение с телефона", "sending": "Отправка на телефон", "location": "Папка сохранения",
        "ready": "файл(ов) готово", "await": "Ожидание передачи …", "done": "готово",
        "ended": "Соединение завершено", "ended_text": "Браузер закрыт или телефон больше недоступен.", "new": "＋ Подключить новый телефон",
        "history": "Передачи в этой сессии", "status_waiting": "Ожидание файла", "status_transferring": "Файл отправляется", "status_done": "Готово", "show": "Показать", "more": "Отправить ещё файлы", "end": "Завершить",
        "start": "Готово к подключению", "start_text": "Подключите телефон без приложения через локальную сеть Wi-Fi.", "new_connection": "Новое подключение",
        "status_accept": "Ожидание подтверждения на телефоне",
        "new_transfer": "＋ Новая передача",
        "copy_link": "Копировать ссылку", "copied": "Ссылка скопирована",
        "switch": "Сменить направление",
        "unknown_file": "Файл", "server_error": "Не удалось запустить сервер",
        "network_error": "Подходящий локальный сетевой адрес не найден. Подключите компьютер к Wi-Fi или LAN и повторите попытку.",
        "retry": "Повторить",
    },
}

WORDS_1_1 = {
    "de": {
        "text_button": "Text oder Link senden", "text_title": "Text & Links",
        "text_intro": "Texte und Links direkt zwischen PC und Smartphone austauschen. Strg+Enter sendet.",
        "text_send": "An Smartphone senden", "text_copy": "Kopieren", "text_open": "Öffnen",
        "text_copied": "In die Zwischenablage kopiert", "text_empty": "Noch keine Texte oder Links.",
        "text_from_phone": "Vom Smartphone", "text_from_pc": "Von diesem PC", "text_sent": "Gesendet",
        "text_too_long": "Der Text ist zu lang (max. 10.000 Zeichen).",
        "shell_menu": "Im Explorer-Rechtsklick anzeigen", "shell_send": "Mit CamSend senden",
        "shell_error": "Der Explorer-Eintrag konnte nicht geändert werden",
        "offer_error": "Die Datei konnte nicht vorbereitet werden",
    },
    "en": {
        "text_button": "Send text or link", "text_title": "Text & links",
        "text_intro": "Exchange texts and links directly between PC and phone. Ctrl+Enter sends.",
        "text_send": "Send to phone", "text_copy": "Copy", "text_open": "Open",
        "text_copied": "Copied to the clipboard", "text_empty": "No texts or links yet.",
        "text_from_phone": "From the phone", "text_from_pc": "From this PC", "text_sent": "Sent",
        "text_too_long": "The text is too long (max. 10,000 characters).",
        "shell_menu": "Show in Explorer right-click menu", "shell_send": "Send with CamSend",
        "shell_error": "The Explorer entry could not be changed",
        "offer_error": "The file could not be prepared",
    },
    "tr": {
        "text_button": "Metin veya bağlantı gönder", "text_title": "Metin ve bağlantılar",
        "text_intro": "Metin ve bağlantıları bilgisayar ile telefon arasında doğrudan paylaşın. Ctrl+Enter gönderir.",
        "text_send": "Telefona gönder", "text_copy": "Kopyala", "text_open": "Aç",
        "text_copied": "Panoya kopyalandı", "text_empty": "Henüz metin veya bağlantı yok.",
        "text_from_phone": "Telefondan", "text_from_pc": "Bu bilgisayardan", "text_sent": "Gönderildi",
        "text_too_long": "Metin çok uzun (en fazla 10.000 karakter).",
        "shell_menu": "Gezgin sağ tık menüsünde göster", "shell_send": "CamSend ile gönder",
        "shell_error": "Gezgin girdisi değiştirilemedi",
        "offer_error": "Dosya hazırlanamadı",
    },
    "az": {
        "text_button": "Mətn və ya link göndər", "text_title": "Mətn və linklər",
        "text_intro": "Mətn və linkləri kompüter ilə telefon arasında birbaşa paylaşın. Ctrl+Enter göndərir.",
        "text_send": "Telefona göndər", "text_copy": "Kopyala", "text_open": "Aç",
        "text_copied": "Mübadilə buferinə kopyalandı", "text_empty": "Hələ mətn və ya link yoxdur.",
        "text_from_phone": "Telefondan", "text_from_pc": "Bu kompüterdən", "text_sent": "Göndərildi",
        "text_too_long": "Mətn çox uzundur (maks. 10.000 simvol).",
        "shell_menu": "Explorer sağ klik menyusunda göstər", "shell_send": "CamSend ilə göndər",
        "shell_error": "Explorer girişini dəyişmək mümkün olmadı",
        "offer_error": "Faylı hazırlamaq mümkün olmadı",
    },
    "ru": {
        "text_button": "Отправить текст или ссылку", "text_title": "Текст и ссылки",
        "text_intro": "Обменивайтесь текстом и ссылками напрямую между компьютером и телефоном. Ctrl+Enter отправляет.",
        "text_send": "Отправить на телефон", "text_copy": "Копировать", "text_open": "Открыть",
        "text_copied": "Скопировано в буфер обмена", "text_empty": "Пока нет текстов или ссылок.",
        "text_from_phone": "С телефона", "text_from_pc": "С этого компьютера", "text_sent": "Отправлено",
        "text_too_long": "Текст слишком длинный (макс. 10 000 символов).",
        "shell_menu": "Показывать в контекстном меню Проводника", "shell_send": "Отправить через CamSend",
        "shell_error": "Не удалось изменить пункт меню Проводника",
        "offer_error": "Не удалось подготовить файл",
    },
}
for _language, _words in WORDS_1_1.items():
    WORDS[_language].update(_words)

LANGUAGE_NAMES = {"de": "Deutsch", "en": "English", "tr": "Türkçe", "az": "Azərbaycan", "ru": "Русский"}
URL_PATTERN = re.compile(r"https?://[^\s<>\"']+", re.IGNORECASE)
HEADING_MAX_WIDTH = 385  # usable width inside the fixed 480 px window
HANDOFF_TIMEOUT_SECONDS = 2.0
HANDOFF_RETRY_SECONDS = 6.0


def system_language() -> str:
    prefix = (locale.getlocale()[0] or "en").lower().split("_")[0].split("-")[0]
    return prefix if prefix in WORDS else "en"


def first_url(text: str) -> str | None:
    match = URL_PATTERN.search(text)
    if not match:
        return None
    url = match.group(0).rstrip(".,;:!?)]}")
    return url if urlparse(url).scheme in {"http", "https"} else None


def hand_off_to_running_instance(paths: list[str]) -> bool:
    """Pass files to an already running CamSend; True if it accepted them."""
    try:
        port_text, key = transfer.INSTANCE_KEY_PATH.read_text(encoding="utf-8").split()[:2]
        request = urllib.request.Request(
            f"http://127.0.0.1:{int(port_text)}/local/offer",
            data=json.dumps({"paths": paths}).encode("utf-8"),
            headers={"Content-Type": "application/json", "X-CamSend-Key": key},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=HANDOFF_TIMEOUT_SECONDS) as response:
            return response.status == 200
    except (OSError, ValueError):
        # No instance, a stale key file from a crashed run, or a foreign server on
        # the port: start a normal window instead.
        return False


class CamSendWindow:
    def __init__(self, root: tk.Tk, initial_paths: list[str] | None = None):
        self.root = root
        root.title(f"CamSend {VERSION}")
        root.geometry("480x690")
        root.resizable(False, False)
        root.configure(bg=BG)
        self.logo_photo, self.icon_photo = self._load_brand_images()
        self.language_icon_photo = self._load_language_icon()
        if self.icon_photo:
            root.iconphoto(True, self.icon_photo)
        self.server = make_server("0.0.0.0", transfer.PORT, transfer.app, threaded=True)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        # Written only after the port is bound, so a second process never hands
        # files to an instance whose server is not listening yet.
        transfer.enable_local_handoff()
        self.qr_photo = None
        self.connection_url = None
        self.text_window = None
        self.text_signature = None
        self.seen_message_ids: set[str] = set()
        self.language = system_language()
        transfer.session_state["language"] = self.language
        if shell_integration.is_supported():
            try:
                shell_integration.refresh(sys.executable, self.tr("shell_send"))
            except OSError:
                pass  # Best effort only; the menu toggle reports errors when used.
        self.view = ""
        self.was_connected = False
        self.history_signature = None
        self.animation_active = False
        self.animation_phase = 0.0
        self.current_progress = 0.0
        self.display_progress = 0.0
        self.transfer_art_photo = None
        self.body = tk.Frame(root, bg=PANEL, padx=30, pady=24,
                             highlightbackground=BORDER, highlightthickness=1)
        self.body.pack(fill="both", expand=True, padx=16, pady=16)
        self.show_qr(False)
        if initial_paths:
            self.handle_shell_files(initial_paths)
        self.poll()
        root.protocol("WM_DELETE_WINDOW", self.close)

    def _load_brand_images(self):
        logo_path = transfer.BRAND_PATH
        if not logo_path.exists():
            return None, None
        source = Image.open(logo_path).convert("RGB")
        difference = ImageChops.difference(source, Image.new("RGB", source.size, "white")).convert("L")
        bounds = difference.point(lambda value: 255 if value > 14 else 0).getbbox()
        brand = source.crop(bounds) if bounds else source
        wordmark = brand.copy()
        wordmark.thumbnail((168, 48), Image.Resampling.LANCZOS)
        icon_width = min(brand.width, int(brand.height * 1.18))
        icon = brand.crop((0, 0, icon_width, brand.height))
        icon.thumbnail((64, 64), Image.Resampling.LANCZOS)
        return ImageTk.PhotoImage(wordmark), ImageTk.PhotoImage(icon)

    @staticmethod
    def _load_language_icon():
        scale = 4
        image = Image.new("RGBA", (30 * scale, 22 * scale), (255, 255, 255, 0))
        draw = ImageDraw.Draw(image)
        globe = (2 * scale, 2 * scale, 20 * scale, 20 * scale)
        stroke = 2 * scale
        draw.ellipse(globe, outline=BLUE, width=stroke)
        draw.ellipse((7 * scale, 2 * scale, 15 * scale, 20 * scale), outline=BLUE, width=stroke)
        draw.line((3 * scale, 8 * scale, 19 * scale, 8 * scale), fill=BLUE, width=stroke)
        draw.line((3 * scale, 14 * scale, 19 * scale, 14 * scale), fill=BLUE, width=stroke)
        draw.line((24 * scale, 9 * scale, 27 * scale, 12 * scale, 30 * scale, 9 * scale),
                  fill=MUTED, width=stroke, joint="curve")
        image = image.resize((30, 22), Image.Resampling.LANCZOS)
        return ImageTk.PhotoImage(image)

    @staticmethod
    @lru_cache(maxsize=16)
    def _art_font(size, bold=False):
        filename = "segoeuib.ttf" if bold else "segoeui.ttf"
        try:
            return ImageFont.truetype(filename, size)
        except OSError:
            return ImageFont.load_default()

    def clear(self):
        for child in self.body.winfo_children():
            child.destroy()

    def title(self, heading, subtext=""):
        header = tk.Frame(self.body, bg=PANEL)
        header.pack(fill="x", pady=(0, 18))
        if self.logo_photo:
            tk.Label(header, image=self.logo_photo, bg=PANEL).pack(side="left")
        else:
            tk.Label(header, text="CamSend", bg=PANEL, fg=BLUE,
                     font=("Segoe UI", 17, "bold")).pack(side="left")
        language_button = tk.Button(
            header,
            image=self.language_icon_photo,
            command=lambda: self.show_language_menu(language_button),
            bg=SOFT,
            activebackground="#e7f0fa",
            relief="flat",
            bd=0,
            highlightthickness=0,
            padx=9,
            pady=7,
            cursor="hand2",
        )
        language_button.pack(side="right")
        tk.Label(self.body, text=heading, bg=PANEL, fg=TEXT,
                 anchor="w", justify="left", font=self._heading_font(heading)).pack(fill="x", pady=(0, 6))
        if subtext:
            tk.Label(self.body, text=subtext, bg=PANEL, fg=MUTED, wraplength=385,
                     anchor="w", justify="left", font=("Segoe UI", 10)).pack(fill="x")

    @staticmethod
    def _heading_font(heading, max_width=HEADING_MAX_WIDTH):
        # The window has a fixed width; long headings such as "Empfangen vom
        # Smartphone" were clipped at 24 pt. Shrinking keeps the layout height
        # unchanged, which wrapping would not (the progress view has no spare room).
        size = 24
        while size > 16 and tkfont.Font(family="Segoe UI", size=size, weight="bold").measure(heading) > max_width:
            size -= 1
        return ("Segoe UI", size, "bold")

    def tr(self, key):
        return WORDS[self.language][key]

    def show_language_menu(self, anchor):
        menu = tk.Menu(
            self.root,
            tearoff=False,
            bg="#ffffff",
            fg=TEXT,
            activebackground="#eaf2ff",
            activeforeground=BLUE_DARK,
            selectcolor=BLUE,
            relief="flat",
            bd=0,
            activeborderwidth=0,
            font=("Segoe UI", 10),
        )
        for code, name in LANGUAGE_NAMES.items():
            marker = "✓  " if code == self.language else "     "
            menu.add_command(label=marker + name, command=lambda value=name: self.change_language(value))
        if shell_integration.is_supported():
            menu.add_separator()
            marker = "✓  " if shell_integration.is_registered() else "     "
            menu.add_command(label=marker + self.tr("shell_menu"), command=self.toggle_shell_entry)
        self.language_menu = menu
        x = anchor.winfo_rootx() + anchor.winfo_width() - 168
        y = anchor.winfo_rooty() + anchor.winfo_height() + 7
        menu.tk_popup(max(anchor.winfo_rootx(), x), y)

    def toggle_shell_entry(self):
        try:
            if shell_integration.is_registered():
                shell_integration.unregister()
            else:
                shell_integration.register(sys.executable, self.tr("shell_send"))
        except OSError as error:
            messagebox.showerror("CamSend", f"{self.tr('shell_error')}:\n{error}", parent=self.root)

    def change_language(self, selected):
        self.language = next(code for code, name in LANGUAGE_NAMES.items() if name == selected)
        with transfer.session_lock:
            transfer.session_state["language"] = self.language
        if shell_integration.is_supported() and shell_integration.is_registered():
            try:
                shell_integration.register(sys.executable, self.tr("shell_send"))
            except OSError:
                pass  # Keeps the old label; the entry itself still works.
        if self.text_window is not None and self.text_window.winfo_exists():
            self.text_window.destroy()
            self.text_window = None
            self.open_texts()
        if self.view == "qr": self.show_qr(False)
        elif self.view == "connected": self.show_connected()
        elif self.view == "disconnected": self.show_disconnected()
        elif self.view == "start": self.show_start()
        elif self.view == "progress":
            mode = transfer.session_state.get("mode")
            heading = self.tr("receiving") if mode == "receive" else self.tr("sending")
            self.show_progress(heading, "")

    def button(self, text, command, secondary=False):
        return tk.Button(self.body, text=text, command=command,
                         bg="#edf3f8" if secondary else BLUE,
                         activebackground="#e2ebf3" if secondary else BLUE_DARK,
                         fg="#385069" if secondary else "#ffffff",
                         activeforeground="#385069" if secondary else "#ffffff",
                         relief="flat", bd=0, highlightthickness=0,
                         padx=15, pady=12, font=("Segoe UI", 10, "bold"), cursor="hand2")

    def show_qr(self, fresh=True):
        if fresh:
            transfer.new_session()
            with transfer.session_lock:
                transfer.session_state["language"] = self.language
        self.view = "qr"
        self.was_connected = False
        self.clear()
        self.title(self.tr("connect"), self.tr("scan"))
        try:
            self.connection_url = transfer.phone_url()
        except RuntimeError:
            self.connection_url = None
            tk.Label(self.body, text="!", bg="#fff2f0", fg="#c53b2c", width=4, height=2,
                     font=("Segoe UI", 34, "bold")).pack(pady=(42, 22))
            tk.Label(self.body, text=self.tr("network_error"), bg=PANEL, fg=MUTED,
                     wraplength=365, justify="center", font=("Segoe UI", 10)).pack(pady=(0, 20))
            self.button(self.tr("retry"), lambda: self.show_qr(False)).pack(fill="x", padx=62)
            return
        image = qrcode.make(self.connection_url).convert("RGB").resize((260, 260), Image.Resampling.NEAREST)
        self.qr_photo = ImageTk.PhotoImage(image)
        qr_frame = tk.Frame(self.body, bg="#ffffff", padx=10, pady=10,
                            highlightbackground=BORDER, highlightthickness=1)
        qr_frame.pack(pady=(19, 14))
        tk.Label(qr_frame, image=self.qr_photo, bg="white").pack()
        self.qr_status = tk.Label(self.body, text="●  " + self.tr("waiting"), bg=PANEL, fg=GREEN,
                                  font=("Segoe UI", 9, "bold"))
        self.qr_status.pack(pady=(0, 12))
        self.button(self.tr("copy_link"), self.copy_link, True).pack(fill="x", padx=62)

    def copy_link(self):
        if not self.connection_url:
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(self.connection_url)
        self.root.update()
        self.qr_status.configure(text="✓  " + self.tr("copied"))

    def show_connected(self):
        self.view = "connected"
        self.clear()
        self.title(self.tr("connected"), self.tr("question"))
        tk.Label(self.body, text="✓", bg="#e9faf3", fg=GREEN, width=4, height=2,
                 font=("Segoe UI", 34, "bold")).pack(pady=(32, 22))
        self.button(self.tr("receive"), self.receive).pack(fill="x", pady=7)
        self.button(self.tr("send"), self.send).pack(fill="x", pady=7)
        self.button(self.tr("text_button"), self.open_texts, True).pack(fill="x", pady=7)
        self.button(self.tr("other"), lambda: self.show_qr(True), True).pack(fill="x", pady=(24, 7))

    def receive(self):
        destination = filedialog.askdirectory(parent=self.root, title=self.tr("destination"))
        if not destination:
            return False
        with transfer.session_lock:
            transfer.session_state["receive_dir"] = destination
            transfer.session_state["mode"] = "receive"
        self.show_progress(self.tr("receiving"), f"{self.tr('location')}: {destination}")
        return True

    def send(self):
        selected = filedialog.askopenfilenames(parent=self.root, title=self.tr("select"))
        if not selected:
            return False
        count = self.offer_files(selected)
        self.show_progress(self.tr("sending"), f"{count} {self.tr('ready')}")
        return True

    def offer_files(self, selected) -> int:
        """Copy files into the transfer folder and offer them to the phone."""
        prepared = []
        for source_name in selected:
            source = Path(source_name)
            target = transfer.TRANSFER_DIR / source.name
            counter = 1
            while target.exists() and target.resolve() != source.resolve():
                target = transfer.TRANSFER_DIR / f"{source.stem}-{counter}{source.suffix}"
                counter += 1
            if target.resolve() != source.resolve():
                shutil.copy2(source, target)
            prepared.append(target)
        with transfer.session_lock:
            transfer.session_state["mode"] = "send"
            for target in prepared:
                if target.name not in transfer.session_state["offered_files"]:
                    transfer.session_state["offered_files"].append(target.name)
                    transfer.add_history(target.name, target.stat().st_size, "send", "waiting")
        return len(prepared)

    def bring_to_front(self):
        self.root.deiconify()
        self.root.lift()
        # Windows only lets a process steal focus in limited cases; a short topmost
        # toggle reliably raises the window after an Explorer hand-off.
        self.root.attributes("-topmost", True)
        self.root.after(300, lambda: self.root.attributes("-topmost", False))
        self.root.focus_force()

    def handle_shell_files(self, paths):
        """Offer files from Explorer's "Send with CamSend" entry."""
        files = [path for path in paths if Path(path).is_file()]
        if not files:
            return
        self.bring_to_front()
        if self.view in {"start", "disconnected"}:
            self.show_qr(True)
        try:
            count = self.offer_files(files)
        except OSError as error:
            messagebox.showerror("CamSend", f"{self.tr('offer_error')}:\n{error}", parent=self.root)
            return
        if self.view in {"connected", "progress"}:
            self.show_progress(self.tr("sending"), f"{count} {self.tr('ready')}")
        # In the QR view the files wait in send mode; poll() opens the send view as
        # soon as a phone connects, and the phone page opens directly in that mode.

    def show_progress(self, heading, subtext):
        self.view = "progress"
        self.history_signature = None
        self.current_progress = 0.0
        self.display_progress = 0.0
        self.clear()
        self.title(heading, subtext)
        self.percent = tk.StringVar(value="0 %")
        mode = transfer.session_state.get("mode")
        self.current_mode = mode
        initial_status = self.tr("status_accept") if mode == "send" else self.tr("status_waiting")
        self.filename = tk.StringVar(value=initial_status)
        tk.Label(self.body, textvariable=self.filename, bg=PANEL, fg=TEXT,
                 wraplength=350, font=("Segoe UI", 10, "bold")).pack(pady=(12, 5))
        self.transfer_canvas = tk.Canvas(self.body, width=350, height=155, bg=PANEL,
                                         highlightthickness=0)
        self.transfer_canvas.pack()
        self.draw_transfer_scene()
        self.percent_label = tk.Label(self.body, textvariable=self.percent, bg=PANEL, fg=BLUE,
                                      font=("Segoe UI", 15, "bold"))
        self.percent_label.pack(pady=3)
        self.percent.set("")
        tk.Label(self.body, text=self.tr("history"), bg=PANEL, fg=MUTED,
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(8, 3))
        history_shell = tk.Frame(
            self.body, bg=SOFT, height=116,
            highlightbackground=BORDER, highlightthickness=1,
        )
        history_shell.pack(fill="x")
        history_shell.pack_propagate(False)
        self.history_canvas = tk.Canvas(
            history_shell, bg=SOFT, bd=0, highlightthickness=0,
            yscrollincrement=24,
        )
        history_scrollbar = tk.Scrollbar(
            history_shell, orient="vertical", command=self.history_canvas.yview,
            width=10, relief="flat", bd=0, highlightthickness=0,
            troughcolor=SOFT, bg="#c5d5e5", activebackground=BLUE,
        )
        self.history_canvas.configure(yscrollcommand=history_scrollbar.set)
        history_scrollbar.pack(side="right", fill="y")
        self.history_canvas.pack(side="left", fill="both", expand=True)
        self.history_frame = tk.Frame(self.history_canvas, bg=SOFT)
        self.history_window = self.history_canvas.create_window(
            (0, 0), window=self.history_frame, anchor="nw",
        )
        self.history_frame.bind(
            "<Configure>",
            lambda _event: self.history_canvas.configure(scrollregion=self.history_canvas.bbox("all")),
        )
        self.history_canvas.bind(
            "<Configure>",
            lambda event: self.history_canvas.itemconfigure(self.history_window, width=event.width),
        )
        self.history_canvas.bind("<MouseWheel>", self.scroll_history)
        actions = tk.Frame(self.body, bg=PANEL)
        actions.pack(fill="x", pady=(10, 0))
        if mode == "send":
            tk.Button(actions, text=self.tr("switch"), command=self.switch_direction,
                      bg=BLUE, activebackground=BLUE_DARK, fg="#ffffff", activeforeground="#ffffff",
                      relief="flat", bd=0, padx=10, pady=10,
                      font=("Segoe UI", 9, "bold")).pack(side="left", expand=True, fill="x", padx=(0, 4))
        tk.Button(actions, text=self.tr("text_title"), command=self.open_texts, bg="#edf3f8", fg="#385069",
                  activebackground="#e2ebf3", activeforeground="#385069", relief="flat", bd=0,
                  padx=10, pady=10, font=("Segoe UI", 9, "bold")).pack(side="left", expand=True, fill="x", padx=4 if mode == "send" else (0, 4))
        tk.Button(actions, text=self.tr("end"), command=self.end_session, bg="#edf3f8", fg="#385069",
                  activebackground="#e2ebf3", activeforeground="#385069", relief="flat", bd=0,
                  padx=10, pady=10, font=("Segoe UI", 9, "bold")).pack(side="left", expand=True, fill="x", padx=(4, 0))

    def draw_transfer_scene(self):
        if not hasattr(self, "transfer_canvas") or not self.transfer_canvas.winfo_exists():
            return
        canvas = self.transfer_canvas
        canvas.delete("all")
        canvas.configure(cursor="")
        canvas.unbind("<Button-1>")

        # Tk's native Canvas has no proper anti-aliasing. Render at 4x and
        # downsample once so arcs, dots and diagonal document edges stay smooth.
        scale = 4
        image = Image.new("RGB", (350 * scale, 155 * scale), PANEL)
        draw = ImageDraw.Draw(image)

        def box(values):
            return tuple(int(value * scale) for value in values)

        center_x, center_y, radius = 175, 62, 51
        bounds = box((center_x - radius, center_y - radius, center_x + radius, center_y + radius))
        draw.ellipse(bounds, outline="#dfe9f3", width=3 * scale)
        visual_progress = getattr(self, "display_progress", self.current_progress)
        degrees = max(0.0, min(360.0, visual_progress * 3.6))
        if degrees:
            draw.arc(bounds, start=-90, end=-90 + degrees, fill="#d8e8ff", width=9 * scale)
            draw.arc(bounds, start=-90, end=-90 + degrees, fill=BLUE, width=5 * scale)
        dot_angle = math.radians(-90 + degrees)
        dot_x = center_x + radius * math.cos(dot_angle)
        dot_y = center_y + radius * math.sin(dot_angle)
        if degrees:
            draw.ellipse(box((dot_x - 6, dot_y - 6, dot_x + 6, dot_y + 6)),
                         fill=BLUE, outline="#dcecff", width=2 * scale)
        draw.ellipse(box((center_x - 39, center_y - 39, center_x + 39, center_y + 39)),
                     fill=SOFT, outline=BORDER, width=scale)

        name = transfer.session_state.get("transfer", {}).get("name", "")
        if not name:
            history = transfer.session_state.get("history", [])
            name = history[-1]["name"] if history else "file"
        extension = Path(name).suffix.lower().lstrip(".")
        groups = {
            "IMG": ({"png", "jpg", "jpeg", "gif", "webp", "heic", "svg", "bmp", "tiff", "raw"}, "#ad75ff"),
            "MUSIC": ({"mp3", "wav", "aac", "m4a", "flac", "ogg", "wma"}, "#ff70b8"),
            "VIDEO": ({"mp4", "mov", "mkv", "avi", "webm", "m4v", "wmv"}, "#ff795f"),
            "PDF": ({"pdf"}, "#ff5d67"),
            "ZIP": ({"zip", "rar", "7z", "tar", "gz", "bz2"}, "#e5ae42"),
            "DOC": ({"doc", "docx", "odt", "rtf"}, "#4b91ff"),
            "SHEET": ({"xls", "xlsx", "ods", "csv"}, "#4bc487"),
            "SLIDE": ({"ppt", "pptx", "odp"}, "#ff8a4b"),
            "TEXT": ({"txt", "md", "log"}, "#8ea4ba"),
            "CODE": ({"py", "js", "ts", "html", "css", "json", "xml", "java", "c", "cpp", "cs", "go", "rs"}, "#55c9cf"),
        }
        label, color = (extension.upper()[:5] or "FILE"), "#8ea4ba"
        for group_label, (extensions, group_color) in groups.items():
            if extension in extensions:
                label, color = group_label, group_color
                break
        # Document shape with a folded corner; unlike OS icons this remains clear
        # on every Windows language and DPI setting.
        document = [(157, 35), (185, 35), (193, 43), (193, 81), (157, 81)]
        draw.polygon([(x * scale, y * scale) for x, y in document], fill=color)
        draw.line([(x * scale, y * scale) for x, y in document + [document[0]]],
                  fill="#d9efff", width=scale, joint="curve")
        fold = [(185, 35), (185, 44), (193, 44)]
        draw.polygon([(x * scale, y * scale) for x, y in fold], fill=SOFT)
        draw.line([(x * scale, y * scale) for x, y in fold], fill="#d9efff", width=scale)
        draw.text((175 * scale, 61 * scale), label, fill="#ffffff",
                  font=self._art_font(6 * scale, True), anchor="mm")
        draw.text((175 * scale, 132 * scale), label, fill=MUTED,
                  font=self._art_font(8 * scale, True), anchor="mm")

        image = image.resize((350, 155), Image.Resampling.LANCZOS)
        self.transfer_art_photo = ImageTk.PhotoImage(image)
        canvas.create_image(0, 0, image=self.transfer_art_photo, anchor="nw")

    def draw_new_transfer(self):
        canvas = self.transfer_canvas
        canvas.delete("all")
        scale = 4
        image = Image.new("RGB", (350 * scale, 155 * scale), PANEL)
        draw = ImageDraw.Draw(image)
        draw.ellipse((124 * scale, 8 * scale, 226 * scale, 110 * scale),
                     fill="#eaf2ff", outline=BLUE, width=3 * scale)
        draw.text((175 * scale, 46 * scale), "+", fill=BLUE,
                  font=self._art_font(33 * scale, True), anchor="mm")
        draw.text((175 * scale, 81 * scale), self.tr("new_transfer").replace("＋ ", ""),
                  fill=BLUE_DARK, font=self._art_font(9 * scale, True), anchor="mm")
        image = image.resize((350, 155), Image.Resampling.LANCZOS)
        self.transfer_art_photo = ImageTk.PhotoImage(image)
        canvas.create_image(0, 0, image=self.transfer_art_photo, anchor="nw")
        canvas.bind("<Button-1>", lambda _event: self.new_transfer())
        canvas.configure(cursor="hand2")

    def new_transfer(self):
        if transfer.session_state.get("mode") == "send":
            # Keep the completed state and the plus button intact while the
            # native file dialog is open. Cancel must be a true no-op.
            if not self.send():
                return False
            with transfer.session_lock:
                transfer.session_state["transfer"] = {
                    "active": False, "name": "", "done": 0, "total": 0, "direction": ""
                }
            self.current_progress = 0
            self.display_progress = 0
            self.percent.set("")
            self.filename.set(self.tr("status_accept"))
            self.draw_transfer_scene()
            return True
        with transfer.session_lock:
            transfer.session_state["transfer"] = {
                "active": False, "name": "", "done": 0, "total": 0, "direction": ""
            }
        self.show_progress(self.tr("receiving"), "")
        return True

    def switch_direction(self):
        with transfer.session_lock:
            old_mode = transfer.session_state.get("mode")
            old_transfer = dict(transfer.session_state["transfer"])
            new_mode = "receive" if old_mode == "send" else "send"
            transfer.session_state["mode"] = new_mode
            transfer.session_state["transfer"] = {
                "active": False, "name": "", "done": 0, "total": 0, "direction": ""
            }
        changed = self.receive() if new_mode == "receive" else self.send()
        if not changed:
            with transfer.session_lock:
                transfer.session_state["mode"] = old_mode
                transfer.session_state["transfer"] = old_transfer
            self.current_mode = old_mode
        return changed

    def animate_transfer(self):
        if not self.animation_active:
            return
        difference = self.current_progress - self.display_progress
        if abs(difference) > 0.05:
            self.display_progress += difference * 0.24
            if abs(self.current_progress - self.display_progress) < 0.08:
                self.display_progress = self.current_progress
            self.draw_transfer_scene()
        self.root.after(34, self.animate_transfer)

    def show_received(self):
        destination = transfer.session_state.get("receive_dir")
        if destination and Path(destination).is_dir():
            os.startfile(destination)

    def end_session(self):
        with transfer.session_lock:
            transfer.session_state["ended"] = True
            transfer.session_state["connected"] = False
        self.show_start()

    def show_start(self):
        self.view = "start"
        self.was_connected = False
        self.clear()
        self.title(self.tr("start"), self.tr("start_text"))
        tk.Label(self.body, text="↗", bg="#eaf2ff", fg=BLUE, width=4, height=2,
                 font=("Segoe UI", 34, "bold")).pack(pady=(62, 34))
        self.button(self.tr("new_connection"), lambda: self.show_qr(True)).pack(fill="x", pady=10)

    def render_history(self, history):
        signature = tuple((i["id"], i["status"], i["done"]) for i in history)
        if signature == self.history_signature:
            return
        self.history_signature = signature
        for child in self.history_frame.winfo_children():
            child.destroy()
        statuses = {"waiting": self.tr("status_waiting"), "transferring": self.tr("status_transferring"), "done": self.tr("status_done")}
        for item in history:
            row = tk.Frame(self.history_frame, bg=SOFT, padx=10, pady=6)
            row.pack(fill="x")
            name_label = tk.Label(row, text=item["name"], bg=SOFT, fg=TEXT, anchor="w",
                                  font=("Segoe UI", 9, "bold"))
            name_label.pack(fill="x")
            color = GREEN if item["status"] == "done" else BLUE
            status_label = tk.Label(
                row, text=f"{statuses.get(item['status'], item['status'])} · {item['size_text']}",
                bg=SOFT, fg=color, anchor="w", font=("Segoe UI", 8),
            )
            status_label.pack(fill="x")
            for widget in (row, name_label, status_label):
                widget.bind("<MouseWheel>", self.scroll_history)
        self.history_frame.update_idletasks()
        self.history_canvas.configure(scrollregion=self.history_canvas.bbox("all"))
        self.history_canvas.yview_moveto(1.0)

    def scroll_history(self, event):
        if event.delta:
            self.history_canvas.yview_scroll(-1 if event.delta > 0 else 1, "units")
        return "break"

    def open_texts(self):
        if self.text_window is not None and self.text_window.winfo_exists():
            self.text_window.deiconify()
            self.text_window.lift()
            self.text_input.focus_set()
            return
        window = tk.Toplevel(self.root)
        self.text_window = window
        self.text_signature = None
        window.title(f"CamSend – {self.tr('text_title')}")
        window.geometry("440x560")
        window.minsize(380, 460)
        window.configure(bg=BG)
        if self.icon_photo:
            window.iconphoto(False, self.icon_photo)
        body = tk.Frame(window, bg=PANEL, padx=20, pady=18, highlightbackground=BORDER, highlightthickness=1)
        body.pack(fill="both", expand=True, padx=12, pady=12)
        tk.Label(body, text=self.tr("text_title"), bg=PANEL, fg=TEXT, anchor="w",
                 font=("Segoe UI", 18, "bold")).pack(fill="x")
        tk.Label(body, text=self.tr("text_intro"), bg=PANEL, fg=MUTED, anchor="w", justify="left",
                 wraplength=370, font=("Segoe UI", 9)).pack(fill="x", pady=(2, 10))

        shell = tk.Frame(body, bg=SOFT, highlightbackground=BORDER, highlightthickness=1)
        shell.pack(fill="both", expand=True)
        self.text_canvas = tk.Canvas(shell, bg=SOFT, bd=0, highlightthickness=0, yscrollincrement=24)
        scrollbar = tk.Scrollbar(shell, orient="vertical", command=self.text_canvas.yview, width=10,
                                 relief="flat", bd=0, highlightthickness=0, troughcolor=SOFT)
        self.text_canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.text_canvas.pack(side="left", fill="both", expand=True)
        self.text_list = tk.Frame(self.text_canvas, bg=SOFT)
        text_list_window = self.text_canvas.create_window((0, 0), window=self.text_list, anchor="nw")
        self.text_list.bind("<Configure>", lambda _event: self.text_canvas.configure(
            scrollregion=self.text_canvas.bbox("all")))
        self.text_canvas.bind("<Configure>", lambda event: self.text_canvas.itemconfigure(
            text_list_window, width=event.width))
        self.text_canvas.bind("<MouseWheel>", self.scroll_texts)

        self.text_input = tk.Text(body, height=4, wrap="word", bg=SOFT, fg=TEXT, relief="flat", bd=0,
                                  highlightbackground=BORDER, highlightcolor=BLUE, highlightthickness=1,
                                  padx=10, pady=8, font=("Segoe UI", 10), undo=True)
        self.text_input.pack(fill="x", pady=(12, 8))
        self.text_input.bind("<Control-Return>", lambda _event: (self.send_text(), "break")[1])
        tk.Button(body, text=self.tr("text_send"), command=self.send_text, bg=BLUE, activebackground=BLUE_DARK,
                  fg="#ffffff", activeforeground="#ffffff", relief="flat", bd=0, padx=12, pady=10,
                  font=("Segoe UI", 10, "bold"), cursor="hand2").pack(fill="x")
        self.text_status = tk.Label(body, text="", bg=PANEL, fg=MUTED, anchor="w", font=("Segoe UI", 9))
        self.text_status.pack(fill="x", pady=(6, 0))
        window.protocol("WM_DELETE_WINDOW", self.close_texts)
        self.render_texts()
        self.text_input.focus_set()

    def close_texts(self):
        if self.text_window is not None and self.text_window.winfo_exists():
            self.text_window.destroy()
        self.text_window = None

    def scroll_texts(self, event):
        if event.delta:
            self.text_canvas.yview_scroll(-1 if event.delta > 0 else 1, "units")
        return "break"

    def send_text(self):
        text, error = transfer.prepare_text(self.text_input.get("1.0", "end-1c"))
        if error == "text_too_long":
            self.text_status.configure(text=self.tr("text_too_long"), fg="#c53b2c")
            return
        if error:
            return  # Empty input: nothing to send, no error needed.
        with transfer.session_lock:
            item = transfer.add_message("pc", text)
        self.seen_message_ids.add(item["id"])
        self.text_input.delete("1.0", "end")
        self.text_status.configure(text="✓  " + self.tr("text_sent"), fg=GREEN)
        self.render_texts()

    def copy_text(self, text):
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.root.update()
        if self.text_window is not None and self.text_window.winfo_exists():
            self.text_status.configure(text="✓  " + self.tr("text_copied"), fg=GREEN)

    def render_texts(self):
        if self.text_window is None or not self.text_window.winfo_exists():
            return
        with transfer.session_lock:
            messages = [dict(item) for item in transfer.session_state["messages"]]
        signature = tuple(item["id"] for item in messages)
        if signature == self.text_signature:
            return
        self.text_signature = signature
        for child in self.text_list.winfo_children():
            child.destroy()
        if not messages:
            tk.Label(self.text_list, text=self.tr("text_empty"), bg=SOFT, fg=MUTED,
                     font=("Segoe UI", 9)).pack(pady=18)
        for item in messages:
            from_phone = item["from"] == "phone"
            row = tk.Frame(self.text_list, bg="#ffffff" if from_phone else "#eaf2ff", padx=10, pady=8,
                           highlightbackground=BORDER, highlightthickness=1)
            row.pack(fill="x", padx=8, pady=(8, 0))
            sender = self.tr("text_from_phone") if from_phone else self.tr("text_from_pc")
            stamp = datetime.fromtimestamp(item["time"]).strftime("%H:%M")
            header = tk.Label(row, text=f"{sender} · {stamp}", bg=row["bg"], fg=MUTED, anchor="w",
                              font=("Segoe UI", 8, "bold"))
            header.pack(fill="x")
            body = tk.Label(row, text=item["text"], bg=row["bg"], fg=TEXT, anchor="w", justify="left",
                            wraplength=330, font=("Segoe UI", 10))
            body.pack(fill="x", pady=(2, 6))
            buttons = tk.Frame(row, bg=row["bg"])
            buttons.pack(fill="x")
            tk.Button(buttons, text=self.tr("text_copy"), command=lambda value=item["text"]: self.copy_text(value),
                      bg="#edf3f8", fg="#385069", activebackground="#e2ebf3", relief="flat", bd=0,
                      padx=10, pady=4, font=("Segoe UI", 8, "bold"), cursor="hand2").pack(side="left")
            url = first_url(item["text"])
            if url:
                # first_url() only returns http(s) URLs, so this never launches
                # file:, javascript: or other handlers from text the phone sent.
                tk.Button(buttons, text=self.tr("text_open"), command=lambda value=url: webbrowser.open(value),
                          bg=BLUE, fg="#ffffff", activebackground=BLUE_DARK, activeforeground="#ffffff",
                          relief="flat", bd=0, padx=10, pady=4, font=("Segoe UI", 8, "bold"),
                          cursor="hand2").pack(side="left", padx=(6, 0))
            for widget in (row, header, body, buttons):
                widget.bind("<MouseWheel>", self.scroll_texts)
        tk.Frame(self.text_list, bg=SOFT, height=8).pack()
        self.text_list.update_idletasks()
        self.text_canvas.configure(scrollregion=self.text_canvas.bbox("all"))
        self.text_canvas.yview_moveto(1.0)

    def check_texts(self, messages):
        """Open the text window when the phone sent something new."""
        incoming = [item for item in messages if item["from"] == "phone" and item["id"] not in self.seen_message_ids]
        self.seen_message_ids.update(item["id"] for item in messages)
        if incoming:
            self.open_texts()
            self.text_window.lift()
        self.render_texts()

    def drain_shell_files(self):
        while True:
            try:
                paths = transfer.local_offer_queue.get_nowait()
            except queue.Empty:
                return
            self.handle_shell_files(paths)

    def show_disconnected(self):
        self.view = "disconnected"
        self.clear()
        self.title(self.tr("ended"), self.tr("ended_text"))
        tk.Label(self.body, text="○", bg="#fff4e8", fg="#dc781b", width=4, height=2,
                 font=("Segoe UI", 34)).pack(pady=(50, 25))
        self.button(self.tr("new"), lambda: self.show_qr(True)).pack(fill="x", pady=10)

    def poll(self):
        self.drain_shell_files()
        now = time.time()
        with transfer.session_lock:
            state = dict(transfer.session_state)
            state["transfer"] = dict(transfer.session_state["transfer"])
            state["offered_files"] = list(transfer.session_state["offered_files"])
            state["messages"] = [dict(item) for item in transfer.session_state["messages"]]
        self.check_texts(state["messages"])
        connected = state["connected"] and now - state["last_seen"] < transfer.HEARTBEAT_TIMEOUT_SECONDS
        if state.get("ended") and self.view not in {"start", "qr"}:
            self.show_start()
        elif connected and self.view == "qr":
            self.was_connected = True
            if state.get("mode") == "send" and state["offered_files"]:
                # Files from Explorer were queued before the phone connected.
                self.show_progress(self.tr("sending"), f"{len(state['offered_files'])} {self.tr('ready')}")
            else:
                self.show_connected()
        elif self.was_connected and not connected and self.view not in {"qr", "disconnected"}:
            self.show_disconnected()
        if self.view == "progress":
            if state.get("mode") != self.current_mode:
                old_mode = self.current_mode
                self.current_mode = state.get("mode")
                changed = self.send() if self.current_mode == "send" else self.receive()
                if not changed:
                    with transfer.session_lock:
                        transfer.session_state["mode"] = old_mode
                    self.current_mode = old_mode
                self.root.after(500, self.poll)
                return
            progress = state["transfer"]
            total = progress.get("total", 0)
            done = progress.get("done", 0)
            value = min(100, done / total * 100) if total else 0
            self.current_progress = value
            if progress.get("active"):
                if not self.animation_active:
                    self.animation_active = True
                    self.animate_transfer()
                self.percent.set(f"{value:.0f} %")
                self.filename.set(self.tr("status_transferring") + (f" – {progress['name']}" if progress.get("name") else ""))
            elif not done:
                self.animation_active = False
                self.current_progress = 0
                self.display_progress = 0
                self.draw_transfer_scene()
                self.percent.set("")
                mode = state.get("mode")
                self.filename.set(self.tr("status_accept") if mode == "send" else self.tr("status_waiting"))
            else:
                self.animation_active = False
                self.current_progress = 100
                self.display_progress = 100
                if state.get("mode") == "send" and not state.get("offered_files"):
                    self.draw_new_transfer()
                    self.percent.set("")
                elif state.get("mode") == "send":
                    self.current_progress = 0
                    self.display_progress = 0
                    self.draw_transfer_scene()
                    self.percent.set("")
                else:
                    self.draw_transfer_scene()
                    self.percent.set("100 %")
            if progress.get("name"):
                file_type = mimetypes.guess_type(progress["name"])[0] or self.tr("unknown_file")
                size = transfer.format_bytes(total) if total else ""
                suffix = f"\n{file_type} · {size}" if size else f"\n{file_type}"
                finished = f" – {self.tr('done')}" if not progress["active"] and done else ""
                if not progress.get("active"):
                    self.filename.set(progress["name"] + finished + suffix)
            if state.get("mode") == "send" and done and state.get("offered_files"):
                self.filename.set(self.tr("status_accept"))
            self.render_history(state.get("history", []))
        self.root.after(500, self.poll)

    def close(self):
        transfer.disable_local_handoff()
        self.server.shutdown()
        self.root.destroy()


def main(argv: list[str] | None = None):
    args = sys.argv[1:] if argv is None else argv
    language = system_language()
    # Used by the installer (runs as the signed-in user) and its uninstaller.
    if args[:1] == ["--register-shell"]:
        if shell_integration.is_supported():
            shell_integration.register(sys.executable, WORDS[language]["shell_send"])
        return
    if args[:1] == ["--unregister-shell"]:
        shell_integration.unregister()
        return

    initial_paths: list[str] = []
    if args[:1] == ["--send"]:
        initial_paths = [str(Path(value)) for value in args[1:] if Path(value).is_file()]
        if initial_paths and hand_off_to_running_instance(initial_paths):
            return

    root = tk.Tk()
    try:
        CamSendWindow(root, initial_paths)
    except OSError as error:
        if initial_paths:
            # Explorer starts one process per selected file. Several may race for the
            # port; the losers hand their file to the winner once it is listening.
            root.withdraw()
            deadline = time.monotonic() + HANDOFF_RETRY_SECONDS
            while time.monotonic() < deadline:
                if hand_off_to_running_instance(initial_paths):
                    root.destroy()
                    return
                time.sleep(0.25)
        messagebox.showerror("CamSend", f"{WORDS[language]['server_error']}:\n{error}")
        root.destroy()
        return
    root.mainloop()


if __name__ == "__main__":
    main()
