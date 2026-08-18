# CamSend Protocol v1.0

Der QR-Code enthält nur eine lokale HTTP-Adresse mit einem zufälligen Sitzungstoken:

`http://<windows-ip>:8765/connect/<token>`

## Ablauf

1. Windows erzeugt beim Start ein kryptografisch zufälliges Token.
2. Das Mobilgerät liest die URL per Kamera und öffnet sie im Browser.
3. Der Server akzeptiert das Token, solange Windows diese Sitzung anzeigt. Beim Verbinden
   eines anderen Handys wird es sofort durch ein neues Token ersetzt.
4. Upload: `multipart/form-data` an `POST /upload/<token>`.
5. Download: `GET /download/<token>/<dateiname>`.
6. Dateinamen werden bereinigt; vorhandene Dateien werden nicht überschrieben.

## Sicherheitsgrenzen des Prototyps

Die Übertragung bleibt im lokalen WLAN, ist in v1.0 aber noch nicht TLS-verschlüsselt.
Das WLAN sollte daher vertrauenswürdig sein. Eine Produktionsversion sollte Geräte-Pairing,
HTTPS mit Zertifikats-Pinning, Widerruf, Chunking und Integritätsprüfungen per SHA-256 ergänzen.
