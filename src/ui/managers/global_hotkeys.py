# src/ui/managers/global_hotkeys.py
"""System-wide hotkeys via Win32 RegisterHotKey.

No game injection involved: Windows posts WM_HOTKEY messages to this
process even while the game window has focus, which is what makes the
overlay controllable in-game without touching the game process (EAC-safe).
"""

import sys
import ctypes

if sys.platform == "win32":
    import ctypes.wintypes

from PySide6.QtCore import QAbstractNativeEventFilter
from PySide6.QtWidgets import QApplication

WM_HOTKEY = 0x0312
MOD_NOREPEAT = 0x4000

VK_F8 = 0x77
VK_F9 = 0x78


class GlobalHotkeys(QAbstractNativeEventFilter):
    """Registers global hotkeys and dispatches them to Python callbacks.

    Windows-only; on other platforms register() is a no-op so callers
    don't need to guard every call site.
    """

    def __init__(self):
        super().__init__()
        self._callbacks = {}
        self._next_id = 1
        self._supported = sys.platform == "win32"
        if self._supported:
            QApplication.instance().installNativeEventFilter(self)

    def register(self, virtual_key: int, callback) -> bool:
        """Registers a hotkey. Returns False when the key is taken by
        another application or the platform is unsupported."""
        if not self._supported:
            return False
        hotkey_id = self._next_id
        ok = ctypes.windll.user32.RegisterHotKey(None, hotkey_id, MOD_NOREPEAT, virtual_key)
        if not ok:
            print(f"GlobalHotkeys: could not register virtual key 0x{virtual_key:X} (already in use?)")
            return False
        self._callbacks[hotkey_id] = callback
        self._next_id += 1
        return True

    def unregister_all(self):
        if not self._supported:
            return
        for hotkey_id in self._callbacks:
            ctypes.windll.user32.UnregisterHotKey(None, hotkey_id)
        self._callbacks.clear()

    def nativeEventFilter(self, event_type, message):
        if event_type == b"windows_generic_MSG":
            msg = ctypes.wintypes.MSG.from_address(int(message))
            if msg.message == WM_HOTKEY:
                callback = self._callbacks.get(msg.wParam)
                if callback:
                    callback()
        return False, 0
