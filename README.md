# CamSend

**Transfer files between Windows and any phone over your local Wi-Fi.**

**No mobile app. No account. No cloud. No internet required.**

[Download CamSend for Windows](https://github.com/Peyman0117/CamSend/releases) · [Deutsch](#deutsch) · [English](#english)

> CamSend 1.0.0 uses local HTTP. Use it only on trusted private Wi-Fi or LAN networks.

<a id="deutsch"></a>

## Deutsch

CamSend Local 1.0.0 überträgt Dateien direkt zwischen einem Windows-PC und einem Smartphone oder Tablet im selben lokalen Netzwerk. Auf dem Mobilgerät muss nichts installiert werden: QR-Code scannen, Browser öffnen und Dateien senden oder empfangen.

### Funktionen

- Dateien in beide Richtungen übertragen
- Eine oder mehrere Dateien pro Transfer auswählen
- Zielordner für empfangene Dateien unter Windows frei wählen
- Verbindung per QR-Code oder kopierbarem Link herstellen
- Fortschritt, Dateityp, Dateigröße, Status und Sitzungsverlauf auf beiden Geräten anzeigen
- Übertragungsrichtung innerhalb derselben Verbindung wechseln
- Funktioniert mit iPhone, iPad, Android und anderen modernen Mobilbrowsern
- Deutsch, Englisch, Türkisch, Aserbaidschanisch und Russisch
- Keine Cloud, kein Konto und keine verpflichtende Internetverbindung

### Download und Installation

Die geprüften Windows-Pakete werden unter [GitHub Releases](https://github.com/Peyman0117/CamSend/releases) bereitgestellt:

- `CamSend-Setup-1.0.0.exe` – empfohlener Installer mit Startmenü-Eintrag, optionaler Desktop-Verknüpfung und Deinstallation
- `CamSend-Portable-1.0.0.zip` – portabler Ordner mit `CamSend.exe`

Für diese Pakete ist keine Python-Installation erforderlich. Vor der Veröffentlichung als stabiler Release müssen die realen Gerätetests aus [docs/RELEASE_CHECKLIST.md](docs/RELEASE_CHECKLIST.md) abgeschlossen sein.

Die Binärdateien sind ohne separates Code-Signing-Zertifikat nicht digital signiert. Windows SmartScreen kann deshalb eine Warnung anzeigen.

### Verwendung

1. CamSend auf dem Windows-PC starten.
2. Falls die Windows-Firewall fragt, den Zugriff ausschließlich für **private Netzwerke** erlauben.
3. Den QR-Code mit der Kamera des Mobilgeräts scannen. Alternativ den Verbindungslink kopieren und auf dem Mobilgerät öffnen.
4. Unter Windows auswählen, welches Gerät senden soll.
5. Dateien oder einen Zielordner auswählen.
6. Die Übertragung auf dem empfangenden Gerät bestätigen und den Fortschritt verfolgen.
7. **Neuer Transfer**, **Richtung wechseln** oder **Beenden** wählen.

Ein noch nicht verwendeter QR-Code läuft nach 15 Minuten ab. Nach dem ersten erfolgreichen Pairing bleibt die Sitzung bestehen, bis sie beendet oder über **Neues Gerät verbinden** durch einen neuen QR-Code ersetzt wird. Version 1.0.0 erlaubt eine aktive Smartphone-Browser-Sitzung gleichzeitig.

### Dateiverarbeitung

- Vom Mobilgerät empfangene Dateien werden im ausgewählten Windows-Zielordner gespeichert.
- Dateien, die Windows anbietet, werden für die Sitzung lokal zwischengespeichert.
- Eine installierte oder portable Build-Version verwendet `%LOCALAPPDATA%\CamSend\transfers` für ihre Arbeitsdateien.
- Im Python-Entwicklungsmodus wird der Projektordner `transfers/` verwendet.
- Vorhandene Dateien werden nicht überschrieben; CamSend ergänzt Dateinamen automatisch, beispielsweise `foto-1.jpg`.
- Uploads und Downloads werden gestreamt und in Blöcken verarbeitet.
- Die maximale Größe einer einzelnen HTTP-Anfrage beträgt 2 GB.

### Sicherheit und Datenschutz

CamSend überträgt Dateien ausschließlich über das lokale Netzwerk und verwendet keine Cloud. Version 1.0.0 nutzt lokales HTTP mit einem kryptografisch zufälligen Sitzungstoken, besitzt aber noch keine TLS- oder Ende-zu-Ende-Verschlüsselung.

- Nur in einem vertrauenswürdigen privaten WLAN oder LAN verwenden.
- Nicht für öffentliche oder gemeinsam genutzte WLAN-Netze empfohlen.
- Das Sitzungstoken ist eine Zugangskontrolle, aber kein Ersatz für Transportverschlüsselung.
- Der QR-Code beziehungsweise Verbindungslink sollte nur mit dem gewünschten Gerät geteilt werden.
- CamSend benötigt keinen externen IP-Dienst und keinen Internetzugang.
- `camsend.app` ist eine offizielle Markenadresse, aber keine technische Abhängigkeit der lokalen Anwendung.

Weitere technische Einzelheiten stehen in [PROTOCOL.md](PROTOCOL.md).

### Fehlerbehebung

#### QR-Code ist ungültig oder abgelaufen

Unter Windows **Neues Gerät verbinden** wählen und den neuen QR-Code scannen. Ein alter Link wird durch ein neues Token sofort ungültig.

#### Das Mobilgerät erreicht den PC nicht

- Sicherstellen, dass beide Geräte im selben WLAN/LAN sind.
- Gast-WLANs können direkte Gerätekommunikation durch Client-Isolation blockieren.
- Windows-Firewall-Zugriff ausschließlich für private Netzwerke erlauben.
- VPN testweise deaktivieren, falls es die falsche Netzwerkroute auswählt.
- Den kopierten Link direkt im Mobilbrowser öffnen.

#### Keine lokale Netzwerkadresse gefunden

Den PC mit WLAN oder LAN verbinden und in CamSend **Erneut versuchen** wählen. CamSend erzeugt bewusst keinen Smartphone-Link mit `127.0.0.1`.

#### Verbindung endet beim App-Wechsel

Mobile Browser können Hintergrundseiten pausieren. Die CamSend-Seite während einer laufenden Übertragung geöffnet lassen.

### Entwicklung aus dem Quellcode

Voraussetzungen: Windows 10/11 und Python 3.10 oder neuer.

```powershell
python -m pip install -r requirements.txt
python windows_app.py
```

Alternativ `Start-CamSend.bat` starten. Der reproduzierbare Windows-Build ist in [BUILDING.md](BUILDING.md) beschrieben.

### Screenshots

Release-Screenshots werden nach der abschließenden Prüfung auf Windows 11, iPhone Safari und Android Chrome ergänzt.

### Projektstruktur

- `windows_app.py` – Windows-Oberfläche und Ablaufsteuerung
- `app.py` – lokaler Webserver, Session- und Übertragungslogik
- `camsend_version.py` – zentrale Versionsnummer
- `templates/` – Smartphone-Browseroberfläche
- `static/` – CSS und öffentliche Markenassets
- `tests/` – automatisierte Release-Regressionstests
- `packaging/` – PyInstaller-, Icon-, Installer- und Release-Dateien
- `PROTOCOL.md` – zweisprachige Beschreibung des lokalen Protokolls
- `BUILDING.md` – reproduzierbarer Windows-Build

### Lizenz

Der Softwarequellcode steht unter der [Mozilla Public License 2.0](LICENSE). Name, Logo und Marke CamSend werden dadurch nicht automatisch zur Nutzung für fremde oder abgeleitete Produkte freigegeben. Einzelheiten stehen in [TRADEMARKS.md](TRADEMARKS.md).

---

<a id="english"></a>

## English

CamSend Local 1.0.0 transfers files directly between a Windows PC and a smartphone or tablet on the same local network. Nothing needs to be installed on the mobile device: scan the QR code, open the browser, and send or receive files.

### Features

- Transfer files in either direction
- Select one or multiple files per transfer
- Choose any Windows destination folder for received files
- Connect through a QR code or copyable link
- Show progress, file type, file size, status, and session history on both devices
- Switch direction without creating a new connection
- Works with iPhone, iPad, Android, and other modern mobile browsers
- German, English, Turkish, Azerbaijani, and Russian
- No cloud, account, or mandatory internet connection

### Download and installation

Validated Windows packages are published under [GitHub Releases](https://github.com/Peyman0117/CamSend/releases):

- `CamSend-Setup-1.0.0.exe` – recommended installer with Start menu shortcut, optional desktop shortcut, and clean uninstallation
- `CamSend-Portable-1.0.0.zip` – portable folder containing `CamSend.exe`

These packages do not require Python. The real-device checks in [docs/RELEASE_CHECKLIST.md](docs/RELEASE_CHECKLIST.md) must pass before a stable release is published.

The binaries are not digitally signed unless a separate code-signing certificate is configured. Windows SmartScreen may therefore display a warning.

### Usage

1. Start CamSend on the Windows PC.
2. If Windows Firewall asks, allow access for **private networks only**.
3. Scan the QR code with the mobile device camera. Alternatively, copy the connection link and open it on the mobile device.
4. On Windows, choose which device should send files.
5. Select files or a destination folder.
6. Accept the transfer on the receiving device and follow its progress.
7. Select **New transfer**, **Switch direction**, or **End**.

An unused QR code expires after 15 minutes. After the first successful pairing, the session remains valid until it is ended or replaced through **Connect new device**. Version 1.0.0 permits one active smartphone browser session at a time.

### File handling

- Files received from the mobile device are saved in the selected Windows destination folder.
- Files offered by Windows are cached locally for the session.
- Installed and portable builds use `%LOCALAPPDATA%\CamSend\transfers` for working files.
- Python development mode uses the project-local `transfers/` directory.
- Existing files are not overwritten; CamSend adds a suffix such as `photo-1.jpg`.
- Uploads and downloads are streamed and processed in chunks.
- The maximum size of a single HTTP request is 2 GB.

### Security and privacy

CamSend transfers files only over the local network and does not use cloud storage. Version 1.0.0 uses local HTTP with a cryptographically random session token, but it does not yet provide TLS or end-to-end encryption.

- Use CamSend only on a trusted private Wi-Fi or LAN.
- Public or shared Wi-Fi networks are not recommended.
- The session token provides access control but does not replace transport encryption.
- Share the QR code or connection link only with the intended device.
- CamSend requires neither an external IP service nor internet access.
- `camsend.app` is an official brand address, not a technical dependency of the local application.

For technical details, see [PROTOCOL.md](PROTOCOL.md).

### Troubleshooting

#### The QR code is invalid or expired

Select **Connect new device** on Windows and scan the new QR code. Creating a new token immediately invalidates the old link.

#### The mobile device cannot reach the PC

- Confirm that both devices are on the same Wi-Fi/LAN.
- Guest Wi-Fi may block direct device communication through client isolation.
- Allow Windows Firewall access for private networks only.
- Temporarily disable a VPN if it selects the wrong network route.
- Open the copied link directly in the mobile browser.

#### No local network address was found

Connect the PC to Wi-Fi or LAN and select **Try again**. CamSend intentionally does not create a smartphone link using `127.0.0.1`.

#### The connection ends after switching apps

Mobile browsers may suspend background pages. Keep the CamSend page open during an active transfer.

### Development from source

Requirements: Windows 10/11 and Python 3.10 or newer.

```powershell
python -m pip install -r requirements.txt
python windows_app.py
```

You can alternatively launch `Start-CamSend.bat`. See [BUILDING.md](BUILDING.md) for the reproducible Windows build.

### Screenshots

Release screenshots will be added after final validation on Windows 11, iPhone Safari, and Android Chrome.

### Project structure

- `windows_app.py` – Windows interface and workflow control
- `app.py` – local server, session, and transfer logic
- `camsend_version.py` – central version number
- `templates/` – smartphone browser interface
- `static/` – CSS and public brand assets
- `tests/` – automated release regression tests
- `packaging/` – PyInstaller, icon, installer, and release files
- `PROTOCOL.md` – bilingual local protocol description
- `BUILDING.md` – reproducible Windows build instructions

### License

The software source code is available under the [Mozilla Public License 2.0](LICENSE). The license does not automatically grant permission to use the CamSend name, logo, or brand for unrelated or derivative products. See [TRADEMARKS.md](TRADEMARKS.md) for details.
