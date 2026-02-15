import logging
import os
import sys
import threading
import time

import history
import pyperclip
import rumps
import sounds
from hotkey_handler import HotkeyHandler

# from pynput import keyboard # Using custom handler now
from recorder import AudioRecorder
from transcriber import GeminiTranscriber

# Configure logging
log_file = os.path.expanduser("~/.voice2clip.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller."""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    # Check if the path exists in base_path
    path = os.path.join(base_path, relative_path)
    if os.path.exists(path):
        return path
        
    # Fallback for macOS .app bundle: Contents/Resources/
    if getattr(sys, 'frozen', False):
        # Look in ../Resources
        # sys.executable is inside Contents/MacOS
        resources_path = os.path.join(os.path.dirname(sys.executable), "..", "Resources", relative_path)
        if os.path.exists(resources_path):
            return os.path.abspath(resources_path)
            
    return path

# Menu bar icons
# Menu bar icons (Template images for auto dark mode)
ICON_IDLE = resource_path("src/icons/icon_idle_Template.png")
ICON_REC = resource_path("src/icons/icon_rec_Template.png")
ICON_PROCESS = resource_path("src/icons/icon_process_Template.png")
ICON_SUCCESS = resource_path("src/icons/icon_success_Template.png")


class Voice2ClipApp(rumps.App):
    def __init__(self):
        super().__init__("V2C", title=None, icon=ICON_IDLE, quit_button=None, template=True)
        # self.icon is set via super().__init__, no need to set self.title for icon

        # Initialize components
        self.recorder = AudioRecorder(
            filename=os.path.expanduser("~/.voice2clip_recording.wav"),
            silence_threshold=800,
            silence_timeout=3,
        )
        try:
            self.transcriber = GeminiTranscriber()
        except ValueError as e:
            rumps.alert(f"Error: {e}")
            self.transcriber = None

        self.is_processing = False
        self._recording_start_time: float = 0

        # Global Hotkey Listener (Cmd+Shift+R) with EVENT SUPPRESSION
        self.hotkey_handler = HotkeyHandler(callback=self.on_hotkey)
        self.hotkey_handler.start()
        logger.info("Voice2Clip started. Hotkey: Cmd+Shift+R (Suppressed)")

        # Menu Items
        self.menu = [
            rumps.MenuItem(
                "Start/Stop Recording (⌘+⇧+R)", callback=self.toggle_recording
            ),
            rumps.separator,
            rumps.MenuItem("Recent Transcriptions", callback=None),
            rumps.separator,
            rumps.MenuItem("Quit", callback=self.quit_app),
        ]
        self._refresh_history_menu()

    @rumps.timer(2.0)
    def update_history_timer(self, _):
        """Poll for history updates on main thread to fix UI bug."""
        # Check if we need to revert success icon
        if self.icon == ICON_SUCCESS:
            self.icon = ICON_IDLE
        
        # Always refresh history to catch new entries
        self._refresh_history_menu()

    def _refresh_history_menu(self):
        """Update the Recent Transcriptions submenu."""
        if not hasattr(self, 'menu'):
            return
            
        menu_item = self.menu.get("Recent Transcriptions")
        # Check if menu_item is valid and has the underlying _menu object (initialized)
        if menu_item is None or not hasattr(menu_item, '_menu') or menu_item._menu is None:
            return

        # Optimization: Don't rebuild if nothing changed (optional, but good practice)
        # For now, just rebuild safely
        menu_item.clear()
        
        recent = history.get_recent(10)
        if not recent:
            menu_item.add(rumps.MenuItem("(empty)", callback=None))
            return

        for entry in reversed(recent):
            text = entry["text"]
            preview = text[:60] + "…" if len(text) > 60 else text
            ts = entry["timestamp"][:16].replace("T", " ")
            label = f"[{ts}] {preview}"

            def copy_handler(sender, _text=text):
                pyperclip.copy(_text)
                sounds.play_success() # Add sound feedback here too
                try:
                    rumps.notification(
                        title="Voice2Clip",
                        subtitle="Copied from history!",
                        message=_text[:100],
                    )
                except Exception:
                    pass

            menu_item.add(rumps.MenuItem(label, callback=copy_handler))

    def on_hotkey(self):
        """Global hotkey handler (called from HotkeyHandler thread)."""
        logger.debug("Global Hotkey Pressed")
        # Bridge to main thread for UI updates
        rumps.timer(0.1)(self._toggle_from_hotkey)

    def _toggle_from_hotkey(self, _):
        """Wrapper to call toggle_recording on main thread."""
        self.toggle_recording(None)

    def toggle_recording(self, sender=None):
        """Toggle between recording and stopping."""
        if self.is_processing:
            logger.debug("Processing in progress, ignoring input")
            return

        if not self.recorder.is_recording:
            self._start_recording(sender)
        else:
            logger.info("Manual stop triggered")
            self._stop_and_process()

    def _start_recording(self, sender=None):
        """Start a new recording session."""
        logger.info("Recording started")
        self.icon = ICON_REC
        self._recording_start_time = time.time()
        if sender:
            sender.title = "Stop Recording"

        sounds.play_start()
        self.recorder.start(stop_callback=self._on_silence_detected)

        try:
            rumps.notification(
                title="Voice2Clip",
                subtitle="Listening...",
                message="Speak now. Silence or Shortcut to stop.",
            )
        except Exception:
            pass

    def _on_silence_detected(self):
        """Called from recorder thread when silence is detected."""
        self._stop_and_process()

    def _stop_and_process(self):
        """Stops recording, transcribes, and updates UI."""
        # Race condition protection: ensure we only stop once
        if self.is_processing:
            return
            
        self.is_processing = True
        logger.debug("Stopping and starting processing flow...")
        
        duration = time.time() - self._recording_start_time
        file_path = self.recorder.stop()
        self.icon = ICON_PROCESS
        sounds.play_stop()

        # Run transcription in background to keep UI responsive
        threading.Thread(
            target=self._process_audio, args=(file_path, duration), daemon=True
        ).start()

    def _process_audio(self, file_path: str, duration: float):
        """Background worker for transcription."""
        self.is_processing = True

        if not self.transcriber:
            sounds.play_error()
            self._finish_processing("API Key Missing", duration)
            return

        result = self.transcriber.transcribe(file_path)

        # Filter out bad responses
        ignore_phrases = ["no hay audio", "no audio", "sin audio", "silencio detectado"]
        is_bad_response = any(phrase in result.lower() for phrase in ignore_phrases)

        if result.startswith("Error") or is_bad_response:
            logger.warning("Transcription ignored: %s", result)
            sounds.play_error()
            # Optionally show a discrete notification, but DON'T copy to clipboard
            try:
                rumps.notification("Voice2Clip", "Ignored", result[:50])
            except Exception:
                pass
        else:
            # Save to history only on success
            history.save_entry(result, duration_secs=duration)
            pyperclip.copy(result)
            self._finish_processing(result, duration)
        
        self.is_processing = False
        self.icon = ICON_IDLE

    def _finish_processing(self, result: str, duration: float):
        """Cleanup after processing."""
        self.is_processing = False
        self.icon = ICON_IDLE
        self._refresh_history_menu()

        preview = result[:50] + "..." if len(result) > 50 else result
        preview = result[:50] + "..." if len(result) > 50 else result
        logger.info("Result (%.1fs): %s", duration, preview)

        # SUCCESS SOUND (Ready to paste)
        sounds.play_success()
        # SUCCESS ICON (Will be reverted by timer)
        self.icon = ICON_SUCCESS

        try:
            rumps.notification(
                title="Voice2Clip",
                subtitle="Copied to Clipboard!",
                message=result[:100],
                sound=True,
            )
        except Exception as e:
            logger.debug("Notification not available: %s", e)

    def quit_app(self, _):
        """Clean shutdown."""
        logger.info("Shutting down...")
        self.hotkey_handler.stop()
        self.recorder.cleanup()
        rumps.quit_application()


if __name__ == "__main__":
    Voice2ClipApp().run()
