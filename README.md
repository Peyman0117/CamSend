# CamSend 1.0

CamSend überträgt Dateien direkt zwischen einem Windows-PC und einem Smartphone oder Tablet im selben lokalen Netzwerk. Das Mobilgerät benötigt keine App: Es verbindet sich über einen QR-Code und einen normalen Webbrowser.

## Funktionen

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

## Voraussetzungen

- Windows 10 oder Windows 11
- Python 3.10 oder neuer
- PC und Mobilgerät befinden sich im selben privaten WLAN oder LAN
- Der Browser des Mobilgeräts darf lokale Netzwerkadressen öffnen

## Installation und Start

Repository herunterladen oder klonen und anschließend im Projektordner ausführen:

```powershell
python -m pip install -r requirements.txt
python windows_app.py
```

Alternativ kann unter Windows `Start-CamSend.bat` gestartet werden.

Beim ersten Start kann die Windows-Firewall nach einer Freigabe fragen. Der Netzwerkzugriff sollte ausschließlich für private Netzwerke erlaubt werden.

## Verwendung

1. CamSend auf dem Windows-PC starten.
2. Den QR-Code mit der Kamera des Mobilgeräts scannen. Falls die Kamera nicht funktioniert, den Verbindungslink kopieren und auf dem Mobilgerät öffnen.
3. Im Windows-Fenster auswählen, welches Gerät senden soll.
4. Dateien oder einen Zielordner auswählen.
5. Die Übertragung auf dem empfangenden Gerät bestätigen und den Fortschritt verfolgen.
6. Für eine weitere Übertragung **Neuer Transfer** wählen oder mit **Richtung wechseln** die Senderichtung ändern.
7. Mit **Beenden** die Sitzung auf beiden Geräten schließen.

CamSend unterstützt in Version 1.0 eine gleichzeitig verbundene Browser-Sitzung. Die Verbindung bleibt aktiv, solange die CamSend-Seite auf dem Mobilgerät geöffnet und erreichbar ist. Über **Neues Gerät verbinden** wird ein neuer QR-Code mit einem neuen Sitzungstoken erzeugt.

## Dateiverarbeitung

- Vom Mobilgerät empfangene Dateien werden im unter Windows gewählten Zielordner gespeichert.
- Von Windows gesendete Dateien werden vorübergehend in den lokalen Ordner `transfers/` kopiert.
- Bereits vorhandene Dateinamen werden nicht überschrieben, sondern automatisch ergänzt.
- Die maximale Größe einer einzelnen HTTP-Anfrage beträgt derzeit 2 GB.
- Inhalte aus `transfers/` werden durch `.gitignore` nicht veröffentlicht.

## Sicherheit und Datenschutz

CamSend überträgt Dateien ausschließlich über das lokale Netzwerk und verwendet keine Cloud. Version 1.0 nutzt lokales HTTP mit einem zufälligen Sitzungstoken, aber noch keine TLS- oder Ende-zu-Ende-Verschlüsselung. Deshalb sollte CamSend nur in einem vertrauenswürdigen privaten Netzwerk verwendet werden, nicht in öffentlichen oder gemeinsam genutzten WLANs.

Der QR-Code beziehungsweise Verbindungslink enthält die lokale Adresse und das Sitzungstoken. Er sollte nur mit dem gewünschten Gerät geteilt werden. Beim Start einer neuen Verbindung wird das vorherige Token ungültig.

Weitere technische Einzelheiten stehen in [PROTOCOL.md](PROTOCOL.md).

## Fehlerbehebung

### Der QR-Code meldet „ungültig“ oder „abgelaufen“

Im Windows-Fenster **Neues Gerät verbinden** wählen und den neu erzeugten QR-Code scannen. Ein alter Link funktioniert nach dem Erstellen einer neuen Verbindung nicht mehr.

### Das Mobilgerät erreicht den PC nicht

- Prüfen, ob beide Geräte im selben Netzwerk sind.
- Ein Gast-WLAN kann die direkte Kommunikation zwischen Geräten blockieren.
- In der Windows-Firewall den Zugriff für private Netzwerke erlauben.
- VPNs oder Mobilfunk testweise deaktivieren.
- Den kopierten Link direkt im Browser des Mobilgeräts öffnen.

### Die Verbindung endet beim Wechseln der App

Mobile Browser können Webseiten im Hintergrund anhalten. Die CamSend-Seite während der Übertragung geöffnet lassen.

## Projektstruktur

- `windows_app.py` – Windows-Oberfläche und Ablaufsteuerung
- `app.py` – lokaler Webserver und Übertragungslogik
- `templates/` – Browseroberfläche
- `static/` – Gestaltung der Browseroberfläche
- `PROTOCOL.md` – Beschreibung des lokalen Protokolls
- `requirements.txt` – Python-Abhängigkeiten

## Entwicklungsstand

Dies ist Version 1.0. Eine installierbare EXE beziehungsweise ein Windows-Setup ist als separater Release-Schritt vorgesehen und gehört noch nicht zu diesem Quellcode-Stand.
