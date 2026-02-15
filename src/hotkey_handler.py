import logging
import os
import time

import Quartz
from pynput import keyboard

from carbon_hotkey import CarbonHotkeyManager

logger = logging.getLogger(__name__)


class HotkeyHandler:
    def __init__(self, callback, double_press_window: float = 0.35):
        self.callback = callback
        self.listener = None
        self.carbon_hotkey: CarbonHotkeyManager | None = None
        self.double_press_window = double_press_window
        self._last_control_down = 0.0
        self._last_trust_state: bool | None = None
        self.active_hotkey_label = "Ctrl x2"

        combo = os.getenv("VOICE2CLIP_CARBON_HOTKEY", "ctrl+shift+s")
        self._carbon_config = CarbonHotkeyManager.parse_combo(combo)

    def start(self, quiet: bool = False):
        """Starts the low-level keyboard listener."""
        if self.listener or self.carbon_hotkey:
            return True

        self.carbon_hotkey = CarbonHotkeyManager(self.callback, self._carbon_config)
        if self.carbon_hotkey.start():
            self.active_hotkey_label = self._carbon_config.label
            logger.info("HotkeyHandler started with Carbon: %s", self.active_hotkey_label)
            return True
        self.carbon_hotkey = None

        trusted = self.is_accessibility_trusted()
        if not trusted:
            if not quiet or self._last_trust_state is not False:
                logger.error("Carbon hotkey failed and Accessibility permission is NOT granted.")
            self._last_trust_state = False
            return False

        self.listener = keyboard.Listener(darwin_intercept=self._intercept)
        self.listener.start()
        logger.info(
            "HotkeyHandler started: double Control within %.0fms",
            self.double_press_window * 1000,
        )
        self.active_hotkey_label = "Ctrl x2"
        self._last_trust_state = True
        return True

    def request_accessibility_permission(self) -> bool:
        """Request Accessibility trust prompt from macOS (if available)."""
        try:
            if hasattr(Quartz, "AXIsProcessTrustedWithOptions") and hasattr(
                Quartz, "kAXTrustedCheckOptionPrompt"
            ):
                options = {Quartz.kAXTrustedCheckOptionPrompt: True}
                return bool(Quartz.AXIsProcessTrustedWithOptions(options))
        except Exception:
            logger.debug("Could not request Accessibility permission prompt", exc_info=True)
        return self.is_accessibility_trusted()

    def ensure_started(self) -> bool:
        """Start listener only when trusted; safe to call repeatedly."""
        if self.listener or self.carbon_hotkey:
            return True
        return self.start(quiet=True)

    def is_using_carbon(self) -> bool:
        return self.carbon_hotkey is not None

    def is_operational(self) -> bool:
        return self.listener is not None or self.carbon_hotkey is not None

    @staticmethod
    def is_accessibility_trusted() -> bool:
        try:
            return bool(Quartz.AXIsProcessTrusted())
        except Exception:
            return False

    def stop(self):
        """Stops the listener."""
        if self.listener:
            self.listener.stop()
            self.listener = None
        if self.carbon_hotkey:
            self.carbon_hotkey.stop()
            self.carbon_hotkey = None

    def _intercept(self, event_type, event):
        """
        Low-level interceptor for macOS Quartz events.
        Return None to suppress the event.
        Return event to pass it through.
        """
        kCGEventKeyDown = Quartz.kCGEventKeyDown
        kCGKeyboardEventKeycode = Quartz.kCGKeyboardEventKeycode
        kCGKeyboardEventAutorepeat = Quartz.kCGKeyboardEventAutorepeat

        kCGEventFlagMaskCommand = Quartz.kCGEventFlagMaskCommand
        kCGEventFlagMaskShift = Quartz.kCGEventFlagMaskShift
        kCGEventFlagMaskAlternate = Quartz.kCGEventFlagMaskAlternate
        kCGEventFlagMaskControl = Quartz.kCGEventFlagMaskControl

        left_control_keycode = 59
        right_control_keycode = 62

        if event_type == kCGEventKeyDown:
            code = Quartz.CGEventGetIntegerValueField(event, kCGKeyboardEventKeycode)
            is_autorepeat = (
                Quartz.CGEventGetIntegerValueField(event, kCGKeyboardEventAutorepeat) == 1
            )
            if is_autorepeat:
                return event

            if code in (left_control_keycode, right_control_keycode):
                flags = Quartz.CGEventGetFlags(event)
                if self._has_only_control_modifier(
                    flags,
                    kCGEventFlagMaskControl,
                    kCGEventFlagMaskCommand,
                    kCGEventFlagMaskShift,
                    kCGEventFlagMaskAlternate,
                ) and self._handle_control_keydown(time.monotonic()):
                    logger.info("Detected double Control press")
                    try:
                        self.callback()
                    except Exception as e:
                        logger.error("Error in hotkey callback: %s", e)
                    return None

        return event

    def _handle_control_keydown(self, timestamp: float) -> bool:
        if self._last_control_down == 0:
            self._last_control_down = timestamp
            return False

        elapsed = timestamp - self._last_control_down
        self._last_control_down = timestamp

        if elapsed <= self.double_press_window:
            self._last_control_down = 0.0
            return True

        return False

    @staticmethod
    def _has_only_control_modifier(flags, control_mask, command_mask, shift_mask, alt_mask):
        is_ctrl = (flags & control_mask) != 0
        is_cmd = (flags & command_mask) != 0
        is_shift = (flags & shift_mask) != 0
        is_alt = (flags & alt_mask) != 0
        return is_ctrl and not is_cmd and not is_shift and not is_alt
