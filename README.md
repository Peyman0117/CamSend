# CamSend 1.0.0

[Deutsch](#deutsch) · [English](#english)

<a id="deutsch"></a>

## Deutsch

CamSend überträgt Dateien direkt zwischen einem Windows-PC und einem Smartphone oder Tablet im selben lokalen Netzwerk. Das Mobilgerät benötigt keine App: Es verbindet sich über einen QR-Code und einen normalen Webbrowser.

### Funktionen

- Dateien in beide Richtungen übertragen
- Eine oder mehrere Dateien pro Transfer auswählen
- Zielordner für empfangene Dateien unter Windows frei wählen
- Verbindung per QR-Code oder kopierbarem Link herstellen
- Übertragungsfortschritt und Sitzungsverlauf auf beiden Geräten anzeigen
- Übertragungsrichtung innerhalb derselben Verbindung wechseln
- Dateitypen durch passende Symbole darstellen
- Oberfläche automatisch an die Systemsprache anpassen
- Deutsch, Englisch, Türkisch, Aserbaidschanisch und Russisch
- Funktioniert mit iPhone, iPad, Android und anderen Geräten mit modernem Browser
- Keine Cloud, kein Benutzerkonto und kein Internetzugang erforderlich

### Voraussetzungen

- Windows 10 oder Windows 11
- Python 3.10 oder neuer
- PC und Mobilgerät befinden sich im selben privaten WLAN oder LAN
- Der Browser des Mobilgeräts darf lokale Netzwerkadressen öffnen

### Installation und Start

Repository herunterladen oder klonen und anschließend im Projektordner ausführen:

```powershell
python -m pip install -r requirements.txt
python windows_app.py
```

Alternativ kann unter Windows `Start-CamSend.bat` gestartet werden.

Beim ersten Start kann die Windows-Firewall nach einer Freigabe fragen. Der Netzwerkzugriff sollte ausschließlich für private Netzwerke erlaubt werden.

### Verwendung

1. CamSend auf dem Windows-PC starten.
2. Den QR-Code mit der Kamera des Mobilgeräts scannen. Falls die Kamera nicht funktioniert, den Verbindungslink kopieren und auf dem Mobilgerät öffnen.
3. Im Windows-Fenster auswählen, welches Gerät senden soll.
4. Dateien oder einen Zielordner auswählen.
5. Die Übertragung auf dem empfangenden Gerät bestätigen und den Fortschritt verfolgen.
6. Für eine weitere Übertragung **Neuer Transfer** wählen oder mit **Richtung wechseln** die Senderichtung ändern.
7. Mit **Beenden** die Sitzung auf beiden Geräten schließen.

CamSend unterstützt in Version 1.0.0 eine gleichzeitig verbundene Browser-Sitzung. Ein noch nicht verwendeter QR-Code läuft nach 15 Minuten ab. Nach dem ersten erfolgreichen Pairing bleibt die Sitzung bestehen, bis sie beendet oder über **Neues Gerät verbinden** durch einen neuen QR-Code und ein neues Sitzungstoken ersetzt wird. Die Verbindungsanzeige bleibt aktiv, solange die CamSend-Seite auf dem Mobilgerät geöffnet und erreichbar ist.

### Dateiverarbeitung

- Vom Mobilgerät empfangene Dateien werden im unter Windows gewählten Zielordner gespeichert.
- Von Windows gesendete Dateien werden vorübergehend in den lokalen Ordner `transfers/` kopiert.
- Bereits vorhandene Dateinamen werden nicht überschrieben, sondern automatisch ergänzt.
- Die maximale Größe einer einzelnen HTTP-Anfrage beträgt derzeit 2 GB.
- Inhalte aus `transfers/` werden durch `.gitignore` nicht veröffentlicht.

### Sicherheit und Datenschutz

CamSend überträgt Dateien ausschließlich über das lokale Netzwerk und verwendet keine Cloud. Version 1.0.0 nutzt lokales HTTP mit einem zufälligen Sitzungstoken, aber noch keine TLS- oder Ende-zu-Ende-Verschlüsselung. Deshalb sollte CamSend nur in einem vertrauenswürdigen privaten Netzwerk verwendet werden, nicht in öffentlichen oder gemeinsam genutzten WLANs.

Der QR-Code beziehungsweise Verbindungslink enthält die lokale Adresse und das Sitzungstoken. Er sollte nur mit dem gewünschten Gerät geteilt werden. Beim Start einer neuen Verbindung wird das vorherige Token ungültig.

CamSend ermittelt die lokale Netzwerkadresse direkt aus den aktiven Windows-Netzwerkverbindungen und benötigt dafür keinen externen IP-Dienst.

Weitere technische Einzelheiten stehen in [PROTOCOL.md](PROTOCOL.md).

### Fehlerbehebung

#### Der QR-Code meldet „ungültig“ oder „abgelaufen“

Im Windows-Fenster **Neues Gerät verbinden** wählen und den neu erzeugten QR-Code scannen. Ein alter Link funktioniert nach dem Erstellen einer neuen Verbindung nicht mehr.

#### Das Mobilgerät erreicht den PC nicht

- Prüfen, ob beide Geräte im selben Netzwerk sind.
- Ein Gast-WLAN kann die direkte Kommunikation zwischen Geräten blockieren.
- In der Windows-Firewall den Zugriff für private Netzwerke erlauben.
- VPNs oder Mobilfunk testweise deaktivieren.
- Den kopierten Link direkt im Browser des Mobilgeräts öffnen.

#### Die Verbindung endet beim Wechseln der App

Mobile Browser können Webseiten im Hintergrund anhalten. Die CamSend-Seite während der Übertragung geöffnet lassen.

### Projektstruktur

- `windows_app.py` – Windows-Oberfläche und Ablaufsteuerung
- `app.py` – lokaler Webserver und Übertragungslogik
- `templates/` – Browseroberfläche
- `static/` – Gestaltung und öffentliche Markenassets der Browseroberfläche
- `PROTOCOL.md` – Beschreibung des lokalen Protokolls
- `requirements.txt` – Python-Abhängigkeiten

### Entwicklungsstand

Dies ist Version 1.0.0. Eine installierbare EXE beziehungsweise ein Windows-Setup ist als separater Release-Schritt vorgesehen und gehört noch nicht zu diesem Quellcode-Stand.

---

<a id="english"></a>

## English

CamSend transfers files directly between a Windows PC and a smartphone or tablet on the same local network. No mobile app is required: the mobile device connects through a QR code and a standard web browser.

### Features

- Transfer files in either direction
- Select one or multiple files per transfer
- Choose any destination folder for files received on Windows
- Connect through a QR code or a copyable link
- Display transfer progress and session history on both devices
- Switch the transfer direction without creating a new connection
- Represent common file types with matching icons
- Automatically adapt the interface to the system language
- German, English, Turkish, Azerbaijani, and Russian
- Works with iPhone, iPad, Android, and other devices with a modern browser
- No cloud, user account, or internet connection required

### Requirements

- Windows 10 or Windows 11
- Python 3.10 or newer
- The PC and mobile device are connected to the same private Wi-Fi or LAN
- The mobile browser is allowed to open local network addresses

### Installation and startup

Download or clone the repository, then run the following commands inside the project directory:

```powershell
python -m pip install -r requirements.txt
python windows_app.py
```

On Windows, you can alternatively launch `Start-CamSend.bat`.

Windows Firewall may request permission during the first launch. Allow network access for private networks only.

### Usage

1. Start CamSend on the Windows PC.
2. Scan the QR code with the mobile device camera. If the camera is unavailable, copy the connection link and open it on the mobile device.
3. In the Windows window, choose which device should send files.
4. Select the files or a destination folder.
5. Accept the transfer on the receiving device and follow its progress.
6. Select **New transfer** to transfer more files or **Switch direction** to change the sender.
7. Select **End** to close the session on both devices.

CamSend 1.0.0 supports one connected browser session at a time. An unused QR code expires after 15 minutes. After the first successful pairing, the session remains valid until it is ended or replaced through **Connect new device**, which creates a new QR code and session token. The connection indicator stays active while the CamSend page remains open and reachable on the mobile device.

### File handling

- Files received from the mobile device are saved in the destination folder selected on Windows.
- Files sent from Windows are temporarily copied to the local `transfers/` directory.
- Existing filenames are never overwritten; CamSend automatically adds a suffix.
- The current maximum size of a single HTTP request is 2 GB.
- `.gitignore` prevents the contents of `transfers/` from being published.

### Security and privacy

CamSend transfers files only through the local network and does not use cloud storage. Version 1.0.0 uses local HTTP with a random session token, but it does not yet provide TLS or end-to-end encryption. CamSend should therefore be used only on a trusted private network, not on public or shared Wi-Fi.

The QR code or connection link contains the local address and session token. Share it only with the intended device. Starting a new connection invalidates the previous token.

CamSend determines the local network address directly from the active Windows network connections and does not require an external IP service.

For additional technical details, see [PROTOCOL.md](PROTOCOL.md).

### Troubleshooting

#### The QR code is reported as invalid or expired

Select **Connect new device** in the Windows window and scan the newly generated QR code. An old link stops working after a new connection is created.

#### The mobile device cannot reach the PC

- Confirm that both devices are on the same network.
- Guest Wi-Fi networks may block direct communication between devices.
- Allow CamSend through Windows Firewall for private networks.
- Temporarily disable VPNs or mobile data.
- Open the copied connection link directly in the mobile browser.

#### The connection ends after switching apps

Mobile browsers may suspend pages in the background. Keep the CamSend page open during a transfer.

### Project structure

- `windows_app.py` – Windows interface and workflow control
- `app.py` – local web server and transfer logic
- `templates/` – browser interface
- `static/` – browser interface styling and public brand assets
- `PROTOCOL.md` – local protocol description
- `requirements.txt` – Python dependencies

### Development status

This is version 1.0.0. A packaged EXE or Windows installer is planned as a separate release step and is not part of this source release yet.
