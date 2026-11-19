"""Explorer context-menu entry "Send with CamSend" for the current Windows user.

The entry is a classic shell verb under HKCU\\Software\\Classes\\*\\shell, so it
needs no administrator rights and works for portable builds as well. On Windows 11
classic verbs appear under "Show more options" (Shift+F10); the compact menu only
lists apps that ship a packaged IExplorerCommand handler.
"""

from __future__ import annotations

import sys

try:
    import winreg
except ImportError:  # Non-Windows: the feature is simply unavailable.
    winreg = None

VERB_KEY = r"Software\Classes\*\shell\CamSend"
COMMAND_KEY = VERB_KEY + r"\command"


def is_supported() -> bool:
    # Only a frozen CamSend.exe has a stable command line Explorer can call;
    # a development checkout would register a python.exe path instead.
    return winreg is not None and bool(getattr(sys, "frozen", False))


def command_for(executable: str) -> str:
    # Explorer starts one process per selected file with %1; the new process hands
    # the file over to a running CamSend instance (see windows_app.main).
    return f'"{executable}" --send "%1"'


def registered_command() -> str | None:
    if winreg is None:
        return None
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, COMMAND_KEY) as key:
            value, _kind = winreg.QueryValueEx(key, "")
            return value
    except OSError:
        return None


def is_registered() -> bool:
    return registered_command() is not None


def register(executable: str, label: str) -> None:
    if winreg is None:
        raise OSError("Windows registry is not available")
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, VERB_KEY) as key:
        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, label)
        winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, f'"{executable}",0')
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, COMMAND_KEY) as key:
        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, command_for(executable))


def unregister() -> None:
    if winreg is None:
        return
    for key_path in (COMMAND_KEY, VERB_KEY):
        try:
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key_path)
        except FileNotFoundError:
            pass


def refresh(executable: str, label: str) -> None:
    """Keep an existing registration pointing at this executable.

    A portable folder may have been moved since the user enabled the entry; only
    an entry the user already enabled is updated, nothing is created here.
    """
    current = registered_command()
    if current is not None and current != command_for(executable):
        register(executable, label)
