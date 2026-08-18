# Building CamSend 1.0.0 for Windows

[Deutsch](#deutsch) · [English](#english)

<a id="deutsch"></a>

## Deutsch

Der Release-Build erzeugt bewusst einen PyInstaller-Ordner statt einer einzelnen One-File-EXE. Der Start ist dadurch schneller und Templates, CSS sowie Bildressourcen bleiben zuverlässig verfügbar. Für normale Nutzer wird der gesamte Ordner durch einen einzigen Setup-Assistenten installiert.

### Voraussetzungen

- Windows 10 oder Windows 11 (64 Bit)
- Python 3.10 oder neuer (64 Bit; für den offiziellen Build wird Python 3.12 verwendet)
- PowerShell 5.1 oder neuer
- Inno Setup 6.7.3 mit `ISCC.exe` für den Setup-Build

PyInstaller und alle Python-Abhängigkeiten werden in `.venv-build/` installiert. Diese isolierte Umgebung gehört nicht zum Repository. Die exakten Build-Versionen stehen in `requirements-build.lock`; `requirements-build.txt` beschreibt die direkt benötigten Werkzeuge.

### Vollständigen Release bauen

```powershell
powershell -ExecutionPolicy Bypass -File .\packaging\build-release.ps1
```

Das Skript:

1. liest die Version aus `camsend_version.py`,
2. installiert die festgelegten Build-Abhängigkeiten,
3. führt die automatisierten Release-Tests aus,
4. erzeugt das Windows-Icon aus dem öffentlichen CamSend-Logo,
5. baut den PyInstaller-Ordner,
6. erzeugt das Portable-ZIP,
7. kompiliert den Inno-Setup-Installer und
8. schreibt SHA-256-Prüfsummen.

Ergebnisse:

```text
dist/CamSend/CamSend.exe
release/CamSend-Portable-1.0.0.zip
release/CamSend-Setup-1.0.0.exe
release/SHA256SUMS.txt
```

Nur den portablen Build erzeugen:

```powershell
powershell -ExecutionPolicy Bypass -File .\packaging\build-release.ps1 -SkipInstaller
```

Bereits installierte Build-Abhängigkeiten wiederverwenden:

```powershell
powershell -ExecutionPolicy Bypass -File .\packaging\build-release.ps1 -SkipDependencyInstall
```

### Wichtige Release-Hinweise

- Die erzeugten Binärdateien sind ohne separates Code-Signing-Zertifikat nicht digital signiert. Windows SmartScreen kann deshalb warnen.
- Der Installer erzeugt keine Autostart-Einträge und keine Firewall-Regel für öffentliche Netzwerke.
- Ein stabiler Release darf erst nach den realen Gerätetests aus `docs/RELEASE_CHECKLIST.md` veröffentlicht werden.
- Der MPL-2.0-Quellcode ist unter `https://github.com/Peyman0117/CamSend` verfügbar.

---

<a id="english"></a>

## English

The release build intentionally uses a PyInstaller one-folder bundle instead of a single one-file executable. This improves startup time and keeps templates, CSS, and image assets reliable. Normal users still receive a single setup executable that installs the complete bundle.

### Requirements

- 64-bit Windows 10 or Windows 11
- 64-bit Python 3.10 or newer (the official build uses Python 3.12)
- PowerShell 5.1 or newer
- Inno Setup 6.7.3 with `ISCC.exe` for the installer build

PyInstaller and all Python dependencies are installed into `.venv-build/`. This isolated environment is not part of the repository. Exact build versions are recorded in `requirements-build.lock`; `requirements-build.txt` lists the directly required tools.

### Build the complete release

```powershell
powershell -ExecutionPolicy Bypass -File .\packaging\build-release.ps1
```

The script:

1. reads the version from `camsend_version.py`,
2. installs the pinned build dependencies,
3. runs the automated release tests,
4. creates the Windows icon from the public CamSend logo,
5. builds the PyInstaller folder,
6. creates the portable ZIP,
7. compiles the Inno Setup installer, and
8. writes SHA-256 checksums.

Outputs:

```text
dist/CamSend/CamSend.exe
release/CamSend-Portable-1.0.0.zip
release/CamSend-Setup-1.0.0.exe
release/SHA256SUMS.txt
```

Build only the portable package:

```powershell
powershell -ExecutionPolicy Bypass -File .\packaging\build-release.ps1 -SkipInstaller
```

Reuse previously installed build dependencies:

```powershell
powershell -ExecutionPolicy Bypass -File .\packaging\build-release.ps1 -SkipDependencyInstall
```

### Important release notes

- The generated binaries are not digitally signed unless a separate code-signing certificate is configured. Windows SmartScreen may therefore display a warning.
- The installer creates neither an autostart entry nor a firewall rule for public networks.
- Do not publish a stable release until the real-device checks in `docs/RELEASE_CHECKLIST.md` have passed.
- The MPL-2.0 source code is available at `https://github.com/Peyman0117/CamSend`.
