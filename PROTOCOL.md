# CamSend Protocol v1.0.0

[Deutsch](#deutsch) · [English](#english)

<a id="deutsch"></a>

## Deutsch

CamSend verwendet einen lokalen HTTP-Server auf dem Windows-PC. Der QR-Code enthält eine lokale Adresse mit einem kryptografisch zufälligen Sitzungstoken:

```text
http://<windows-ip>:8765/connect/<token>
```

### Sitzungsablauf

1. Windows erzeugt beim Start einer Verbindung ein kryptografisch zufälliges Token.
   Die lokale IPv4-Adresse wird aus den aktiven Netzwerkverbindungen ermittelt; ein externer IP-Dienst ist nicht erforderlich.
2. Das Mobilgerät liest die URL per Kamera oder öffnet den kopierten Link im Browser.
3. Ein unbenutztes Token läuft 15 Minuten nach seiner Erzeugung ab. Nach dem ersten erfolgreichen Pairing bleibt es bis zum Sitzungsende oder einem Tokenwechsel gültig.
4. Der Server bindet die aktive Sitzung an das verbundene Mobilgerät. Version 1.0.0 erlaubt nur eine gleichzeitig aktive Browserverbindung.
5. Regelmäßige Heartbeat-Anfragen halten die Verbindungsanzeige aktiv und melden einen Sitzungsabbruch an den Browser.
6. **Neuer Transfer** behält Token und Übertragungsrichtung bei. **Richtung wechseln** behält das Token bei und tauscht Sender und Empfänger.
7. **Neues Gerät verbinden** erzeugt ein neues Token und macht den vorherigen Link ungültig.
8. **Beenden** markiert die Sitzung als beendet und blockiert weitere Übertragungen mit diesem Token.

### Relevante Endpunkte

- `GET /connect/<token>` – Browseroberfläche öffnen
- `POST /api/heartbeat/<token>` – Verbindung aktiv halten
- `GET /api/session/<token>` – Sitzungsstatus und Übertragungsverlauf abrufen
- `POST /api/mode/<token>/<mode>` – Übertragungsrichtung festlegen
- `POST /api/next/<token>` – nächsten Transfer in derselben Richtung vorbereiten
- `POST /api/switch/<token>` – Übertragungsrichtung wechseln
- `POST /api/end/<token>` – Sitzung beenden
- `POST /upload-file/<token>` – Datei als HTTP-Anfragetext hochladen; der bereinigte Dateiname steht in `X-Filename`
- `GET /download-file/<token>/<filename>` – Datei als Stream herunterladen

### Dateiverarbeitung

- Dateinamen werden vor der Verwendung bereinigt.
- Vorhandene Dateien werden nicht überschrieben; CamSend ergänzt den Namen automatisch.
- Uploads und Downloads werden in Blöcken von 1 MiB verarbeitet, damit der Fortschritt angezeigt werden kann.
- Die maximale Größe einer HTTP-Anfrage beträgt 2 GB.

### Sicherheitsgrenzen von Version 1.0.0

Die Übertragung bleibt im lokalen Netzwerk, ist aber noch nicht durch TLS oder Ende-zu-Ende-Verschlüsselung geschützt. Das Sitzungstoken verhindert keinen aktiven Angriff innerhalb eines kompromittierten Netzwerks. CamSend sollte deshalb nur in einem vertrauenswürdigen privaten Netzwerk eingesetzt werden.

Eine spätere Version kann authentifizierte Dateiverschlüsselung, Gerätebestätigung, sichere Schlüsselableitung, Widerruf und Integritätsprüfungen ergänzen.

---

<a id="english"></a>

## English

CamSend runs a local HTTP server on the Windows PC. The QR code contains a local address with a cryptographically random session token:

```text
http://<windows-ip>:8765/connect/<token>
```

### Session flow

1. Windows generates a cryptographically random token when a connection is started.
   The local IPv4 address is determined from the active network connections; no external IP service is required.
2. The mobile device reads the URL with its camera or opens the copied link in a browser.
3. An unused token expires 15 minutes after it is generated. After the first successful pairing, it remains valid until the session ends or the token is replaced.
4. The server associates the active session with the connected mobile device. Version 1.0.0 permits only one active browser connection at a time.
5. Regular heartbeat requests keep the connection indicator active and notify the browser when the session ends.
6. **New transfer** keeps the token and transfer direction. **Switch direction** keeps the token and swaps sender and receiver.
7. **Connect new device** generates a new token and invalidates the previous link.
8. **End** marks the session as ended and blocks further transfers with that token.

### Relevant endpoints

- `GET /connect/<token>` – open the browser interface
- `POST /api/heartbeat/<token>` – keep the connection active
- `GET /api/session/<token>` – retrieve session state and transfer history
- `POST /api/mode/<token>/<mode>` – select the transfer direction
- `POST /api/next/<token>` – prepare another transfer in the same direction
- `POST /api/switch/<token>` – switch the transfer direction
- `POST /api/end/<token>` – end the session
- `POST /upload-file/<token>` – upload a file as the HTTP request body; the sanitized filename is supplied in `X-Filename`
- `GET /download-file/<token>/<filename>` – download a file as a stream

### File handling

- Filenames are sanitized before use.
- Existing files are not overwritten; CamSend automatically adds a suffix to the name.
- Uploads and downloads are processed in 1 MiB chunks so progress can be displayed.
- The maximum HTTP request size is 2 GB.

### Security boundaries of version 1.0.0

Transfers stay on the local network, but they are not yet protected by TLS or end-to-end encryption. The session token does not prevent an active attack inside a compromised network. CamSend should therefore be used only on a trusted private network.

A future version may add authenticated file encryption, device verification, secure key derivation, revocation, and integrity checks.
