# CamSend 1.1.0

## New

- **Share texts and links** in both directions between Windows and the phone, with Copy and Open buttons
- **Explorer right-click menu:** "Send with CamSend" offers files directly; a running CamSend window takes them over
- The installer can add the right-click entry; portable builds toggle it in the language menu

## Fixes

- Phone page in receive mode no longer fails with HTTP 500
- Files with spaces or `%` in their names can be downloaded
- The session token is no longer exposed to other devices on the network; a paired session is bound to the pairing browser

> CamSend uses local HTTP and should only be used on trusted private networks.
