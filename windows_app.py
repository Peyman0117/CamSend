from __future__ import annotations

import os
import locale
import math
import mimetypes
import shutil
import threading
import tkinter as tk
from functools import lru_cache
from pathlib import Path
from tkinter import filedialog, messagebox

import qrcode
from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageTk
from werkzeug.serving import make_server

import app as transfer


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

LANGUAGE_NAMES = {"de": "Deutsch", "en": "English", "tr": "Türkçe", "az": "Azərbaycan", "ru": "Русский"}


class CamSendWindow:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("CamSend")
        root.geometry("480x690")
        root.resizable(False, False)
        root.configure(bg=BG)
        self.logo_photo, self.icon_photo = self._load_brand_images()
        self.language_icon_photo = self._load_language_icon()
        if self.icon_photo:
            root.iconphoto(True, self.icon_photo)
        self.server = make_server("0.0.0.0", transfer.PORT, transfer.app, threaded=True)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.qr_photo = None
        self.connection_url = None
        system_language = (locale.getlocale()[0] or "en").lower()
        prefix = system_language.split("_")[0].split("-")[0]
        self.language = prefix if prefix in WORDS else "en"
        transfer.session_state["language"] = self.language
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
                 anchor="w", justify="left", font=("Segoe UI", 24, "bold")).pack(fill="x", pady=(0, 6))
        if subtext:
            tk.Label(self.body, text=subtext, bg=PANEL, fg=MUTED, wraplength=385,
                     anchor="w", justify="left", font=("Segoe UI", 10)).pack(fill="x")

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
        self.language_menu = menu
        x = anchor.winfo_rootx() + anchor.winfo_width() - 168
        y = anchor.winfo_rooty() + anchor.winfo_height() + 7
        menu.tk_popup(max(anchor.winfo_rootx(), x), y)

    def change_language(self, selected):
        self.language = next(code for code, name in LANGUAGE_NAMES.items() if name == selected)
        with transfer.session_lock:
            transfer.session_state["language"] = self.language
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
        self.show_progress(self.tr("sending"), f"{len(selected)} {self.tr('ready')}")
        return True

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
        tk.Button(actions, text=self.tr("end"), command=self.end_session, bg="#edf3f8", fg="#385069",
                  activebackground="#e2ebf3", activeforeground="#385069", relief="flat", bd=0,
                  padx=10, pady=10, font=("Segoe UI", 9, "bold")).pack(side="left", expand=True, fill="x", padx=(4 if mode == "send" else 0, 0))

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

    def show_disconnected(self):
        self.view = "disconnected"
        self.clear()
        self.title(self.tr("ended"), self.tr("ended_text"))
        tk.Label(self.body, text="○", bg="#fff4e8", fg="#dc781b", width=4, height=2,
                 font=("Segoe UI", 34)).pack(pady=(50, 25))
        self.button(self.tr("new"), lambda: self.show_qr(True)).pack(fill="x", pady=10)

    def poll(self):
        now = __import__("time").time()
        with transfer.session_lock:
            state = dict(transfer.session_state)
            state["transfer"] = dict(transfer.session_state["transfer"])
        connected = state["connected"] and now - state["last_seen"] < transfer.HEARTBEAT_TIMEOUT_SECONDS
        if state.get("ended") and self.view not in {"start", "qr"}:
            self.show_start()
        elif connected and self.view == "qr":
            self.was_connected = True
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
        self.server.shutdown()
        self.root.destroy()


def main():
    root = tk.Tk()
    try:
        CamSendWindow(root)
    except OSError as error:
        system_language = (locale.getlocale()[0] or "en").lower().split("_")[0].split("-")[0]
        language = system_language if system_language in WORDS else "en"
        messagebox.showerror("CamSend", f"{WORDS[language]['server_error']}:\n{error}")
        root.destroy()
        return
    root.mainloop()


if __name__ == "__main__":
    main()
