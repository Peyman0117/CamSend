# PyInstaller specification for the CamSend Windows one-folder bundle.

from pathlib import Path


project_root = Path(SPEC).resolve().parent.parent
build_root = project_root / "build"

analysis = Analysis(
    [str(project_root / "windows_app.py")],
    pathex=[str(project_root)],
    binaries=[],
    datas=[
        (str(project_root / "templates"), "templates"),
        (str(project_root / "static"), "static"),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

python_archive = PYZ(analysis.pure)

executable = EXE(
    python_archive,
    analysis.scripts,
    [],
    exclude_binaries=True,
    name="CamSend",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    icon=str(build_root / "camsend.ico"),
    version=str(build_root / "version_info.txt"),
    contents_directory="_internal",
)

bundle = COLLECT(
    executable,
    analysis.binaries,
    analysis.datas,
    strip=False,
    upx=False,
    name="CamSend",
)
