"""Tests for the hotkey handler module."""

from hotkey_handler import HotkeyHandler


class TestDoubleControlDetection:
    def test_triggers_on_second_press_within_window(self):
        handler = HotkeyHandler(callback=lambda: None, double_press_window=0.35)

        assert handler._handle_control_keydown(1.0) is False
        assert handler._handle_control_keydown(1.2) is True

    def test_does_not_trigger_outside_window(self):
        handler = HotkeyHandler(callback=lambda: None, double_press_window=0.35)

        assert handler._handle_control_keydown(1.0) is False
        assert handler._handle_control_keydown(1.5) is False

    def test_resets_after_trigger(self):
        handler = HotkeyHandler(callback=lambda: None, double_press_window=0.35)

        assert handler._handle_control_keydown(1.0) is False
        assert handler._handle_control_keydown(1.1) is True
        assert handler._handle_control_keydown(2.0) is False


class TestModifierFilter:
    def test_accepts_only_control(self):
        ctrl = 1 << 18
        cmd = 1 << 20
        shift = 1 << 17
        alt = 1 << 19

        assert HotkeyHandler._has_only_control_modifier(ctrl, ctrl, cmd, shift, alt)
        assert not HotkeyHandler._has_only_control_modifier(ctrl | cmd, ctrl, cmd, shift, alt)
        assert not HotkeyHandler._has_only_control_modifier(ctrl | shift, ctrl, cmd, shift, alt)
        assert not HotkeyHandler._has_only_control_modifier(ctrl | alt, ctrl, cmd, shift, alt)
