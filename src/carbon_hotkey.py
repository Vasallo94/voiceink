import ctypes
from ctypes import util
from dataclasses import dataclass

OSStatus = ctypes.c_int32
UInt32 = ctypes.c_uint32
EventTargetRef = ctypes.c_void_p
EventHandlerRef = ctypes.c_void_p
EventHotKeyRef = ctypes.c_void_p
EventRef = ctypes.c_void_p
EventHandlerCallRef = ctypes.c_void_p


class EventHotKeyID(ctypes.Structure):
    _fields_ = [("signature", UInt32), ("id", UInt32)]


class EventTypeSpec(ctypes.Structure):
    _fields_ = [("eventClass", UInt32), ("eventKind", UInt32)]


def _fourcc(value: str) -> int:
    return int.from_bytes(value.encode("mac_roman"), "big")


kEventClassKeyboard = _fourcc("keyb")
kEventHotKeyPressed = 5
kEventParamDirectObject = _fourcc("----")
typeEventHotKeyID = _fourcc("hkid")

cmdKey = 1 << 8
optionKey = 1 << 11
controlKey = 1 << 12
shiftKey = 1 << 9

MODIFIER_MAP = {
    "cmd": cmdKey,
    "command": cmdKey,
    "option": optionKey,
    "alt": optionKey,
    "control": controlKey,
    "ctrl": controlKey,
    "shift": shiftKey,
}

KEYCODE_MAP = {
    "v": 9,
    "space": 49,
    "r": 15,
    "s": 1,
}


@dataclass(slots=True)
class CarbonHotkeyConfig:
    keycode: int
    modifiers: int
    label: str


class CarbonHotkeyManager:
    def __init__(self, callback, config: CarbonHotkeyConfig):
        self.callback = callback
        self.config = config

        carbon_path = util.find_library("Carbon")
        if not carbon_path:
            raise RuntimeError("Carbon framework not available")
        self.carbon = ctypes.CDLL(carbon_path)

        self._handler_proc = None
        self._handler_ref = EventHandlerRef()
        self._hotkey_ref = EventHotKeyRef()
        self._started = False

        self._configure_signatures()

    @staticmethod
    def default_config() -> CarbonHotkeyConfig:
        modifiers = controlKey | shiftKey
        keycode = KEYCODE_MAP["s"]
        return CarbonHotkeyConfig(keycode=keycode, modifiers=modifiers, label="Ctrl+Shift+S")

    @staticmethod
    def parse_combo(value: str | None) -> CarbonHotkeyConfig:
        if not value:
            return CarbonHotkeyManager.default_config()

        parts = [part.strip().lower() for part in value.split("+") if part.strip()]
        if len(parts) < 2:
            return CarbonHotkeyManager.default_config()

        key_name = parts[-1]
        keycode = KEYCODE_MAP.get(key_name)
        if keycode is None:
            return CarbonHotkeyManager.default_config()

        modifiers = 0
        for name in parts[:-1]:
            modifiers |= MODIFIER_MAP.get(name, 0)

        if modifiers == 0:
            return CarbonHotkeyManager.default_config()

        label = "+".join(part.capitalize() for part in parts)
        return CarbonHotkeyConfig(keycode=keycode, modifiers=modifiers, label=label)

    def _configure_signatures(self) -> None:
        self.carbon.GetApplicationEventTarget.restype = EventTargetRef

        self.carbon.InstallEventHandler.argtypes = [
            EventTargetRef,
            ctypes.c_void_p,
            UInt32,
            ctypes.POINTER(EventTypeSpec),
            ctypes.c_void_p,
            ctypes.POINTER(EventHandlerRef),
        ]
        self.carbon.InstallEventHandler.restype = OSStatus

        self.carbon.RemoveEventHandler.argtypes = [EventHandlerRef]
        self.carbon.RemoveEventHandler.restype = OSStatus

        self.carbon.RegisterEventHotKey.argtypes = [
            UInt32,
            UInt32,
            EventHotKeyID,
            EventTargetRef,
            UInt32,
            ctypes.POINTER(EventHotKeyRef),
        ]
        self.carbon.RegisterEventHotKey.restype = OSStatus

        self.carbon.UnregisterEventHotKey.argtypes = [EventHotKeyRef]
        self.carbon.UnregisterEventHotKey.restype = OSStatus

        self.carbon.GetEventParameter.argtypes = [
            EventRef,
            UInt32,
            UInt32,
            ctypes.c_void_p,
            UInt32,
            ctypes.c_void_p,
            ctypes.c_void_p,
        ]
        self.carbon.GetEventParameter.restype = OSStatus

    def start(self) -> bool:
        if self._started:
            return True

        @ctypes.CFUNCTYPE(OSStatus, EventHandlerCallRef, EventRef, ctypes.c_void_p)
        def on_event(_next, event, _user_data):
            hotkey_id = EventHotKeyID()
            status = self.carbon.GetEventParameter(
                event,
                kEventParamDirectObject,
                typeEventHotKeyID,
                None,
                ctypes.sizeof(EventHotKeyID),
                None,
                ctypes.byref(hotkey_id),
            )
            if status == 0:
                try:
                    self.callback()
                except Exception:
                    return 0
            return 0

        self._handler_proc = on_event
        spec = EventTypeSpec(kEventClassKeyboard, kEventHotKeyPressed)
        target = self.carbon.GetApplicationEventTarget()

        status = self.carbon.InstallEventHandler(
            target,
            self._handler_proc,
            1,
            ctypes.byref(spec),
            None,
            ctypes.byref(self._handler_ref),
        )
        if status != 0:
            return False

        hotkey_id = EventHotKeyID(_fourcc("V2CP"), 1)
        status = self.carbon.RegisterEventHotKey(
            self.config.keycode,
            self.config.modifiers,
            hotkey_id,
            target,
            0,
            ctypes.byref(self._hotkey_ref),
        )
        if status != 0:
            self.stop()
            return False

        self._started = True
        return True

    def stop(self) -> None:
        if self._hotkey_ref:
            self.carbon.UnregisterEventHotKey(self._hotkey_ref)
            self._hotkey_ref = EventHotKeyRef()

        if self._handler_ref:
            self.carbon.RemoveEventHandler(self._handler_ref)
            self._handler_ref = EventHandlerRef()

        self._handler_proc = None
        self._started = False
