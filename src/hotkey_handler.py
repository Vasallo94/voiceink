import logging

import Quartz
from pynput import keyboard

logger = logging.getLogger(__name__)

class HotkeyHandler:
    def __init__(self, callback):
        self.callback = callback
        self.listener = None
        
    def start(self):
        """Starts the low-level keyboard listener."""
        self.listener = keyboard.Listener(darwin_intercept=self._intercept)
        self.listener.start()
        logger.info("HotkeyHandler started with suppression enabled.")

    def stop(self):
        """Stops the listener."""
        if self.listener:
            self.listener.stop()
            self.listener = None

    def _intercept(self, event_type, event):
        """
        Low-level interceptor for macOS Quartz events.
        Return None to suppress the event.
        Return event to pass it through.
        """
        # Constants
        kCGEventKeyDown = Quartz.kCGEventKeyDown
        kCGKeyboardEventKeycode = Quartz.kCGKeyboardEventKeycode
        
        # Modifier flags
        kCGEventFlagMaskCommand = Quartz.kCGEventFlagMaskCommand
        kCGEventFlagMaskShift = Quartz.kCGEventFlagMaskShift
        kCGEventFlagMaskAlternate = Quartz.kCGEventFlagMaskAlternate
        kCGEventFlagMaskControl = Quartz.kCGEventFlagMaskControl
        
        # Target Key: 'r' -> Code 15
        TARGET_KEYCODE = 15 
        
        if event_type == kCGEventKeyDown:
            # Check keycode
            code = Quartz.CGEventGetIntegerValueField(event, kCGKeyboardEventKeycode)
            
            if code == TARGET_KEYCODE:
                # Check modifiers
                flags = Quartz.CGEventGetFlags(event)
                
                is_cmd = (flags & kCGEventFlagMaskCommand) != 0
                is_shift = (flags & kCGEventFlagMaskShift) != 0
                is_alt = (flags & kCGEventFlagMaskAlternate) != 0
                is_ctrl = (flags & kCGEventFlagMaskControl) != 0
                
                # Match: Cmd + Shift + R
                # We want EXACT match or AT LEAST match?
                # Browser reload is Cmd+Shift+R. 
                # If user presses Cmd+Shift+Alt+R, browser won't likely reload.
                # So we target specifically Cmd+Shift+R (ignoring others? No, if Alt is pressed it's a different shortcut)
                
                # STRICT MATCHING: CMD + SHIFT + R (and NO Alt, NO Ctrl)
                if is_cmd and is_shift and not is_alt and not is_ctrl:
                    logger.info("Intercepted Cmd+Shift+R! Suppressing event.")
                    # Trigger callback
                    # Note: Callback must handle threading if necessary
                    try:
                        self.callback()
                    except Exception as e:
                        logger.error(f"Error in hotkey callback: {e}")
                        
                    return None # SUPPRESS EVENT
                    
        return event # PASS EVENT
