# CamSend Local 1.0.0 release checklist

A stable GitHub release must not be published until the two mandatory real-device combinations have passed:

- [ ] Windows 11 + iPhone Safari
- [ ] Windows 11 + Android Chrome

## Automated checks

- [x] `python -m unittest discover -s tests -v`
- [x] Python source compilation succeeds
- [x] PyInstaller build succeeds
- [x] Packaged `CamSend.exe` starts with its bundled Python runtime
- [x] Packaged templates, CSS, logo, and QR endpoint load
- [x] Installer builds and uninstalls cleanly in an isolated test directory
- [x] SHA-256 checksums are generated

## Windows coverage

- [ ] Windows 10, current supported build
- [ ] Windows 11, current supported build
- [ ] Start menu shortcut works
- [ ] Optional desktop shortcut works
- [ ] Uninstaller removes the application
- [ ] No autostart entry is created
- [ ] Firewall access is allowed for private networks only

## Smartphone and browser coverage

- [ ] iPhone Safari
- [ ] iPad Safari
- [ ] Android Chrome
- [ ] Responsive layout in portrait orientation
- [ ] Responsive layout in landscape orientation
- [ ] No mobile application is requested

## Network coverage

- [ ] Home Wi-Fi with internet access
- [ ] Wi-Fi without internet access
- [ ] PC connected by LAN and phone connected to the same router by Wi-Fi
- [ ] Guest Wi-Fi with client isolation produces an understandable connection failure
- [ ] VPN active: selected address and connection behavior are documented
- [ ] Missing local IPv4 address produces the localized retry screen

## Transfer coverage

- [ ] Small JPG
- [ ] PDF
- [ ] MP3
- [ ] Video
- [ ] Multiple files
- [ ] Large file
- [ ] Filename containing spaces
- [ ] Filename containing non-ASCII characters
- [ ] Duplicate filenames are renamed instead of overwritten
- [ ] Cancel Windows file dialog without resetting the current state
- [ ] Close the smartphone page during a transfer
- [ ] Let an unused QR token expire
- [ ] Connect a new device and verify that the old token stops working
- [ ] Switch direction repeatedly
- [ ] End the session from Windows
- [ ] End the session from the smartphone

## Release publication

- [ ] Review `packaging/release-notes.md`
- [ ] Confirm `main` and `v1.0.0` point to the approved commit
- [ ] Upload `CamSend-Setup-1.0.0.exe`
- [ ] Upload `CamSend-Portable-1.0.0.zip`
- [ ] Upload `SHA256SUMS.txt`
- [ ] Include the local-HTTP security warning in the release notes
