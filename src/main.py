import os
import threading
import time

import pyperclip
import rumps
from pynput import keyboard

from recorder import AudioRecorder
from transcriber import GeminiTranscriber

# Icons (Unicode placeholders for simplicity, can be replaced with files)
ICON_IDLE = "⚫"
ICON_REC = "🔴"
ICON_PROCESS = "🟡"

class Voice2ClipApp(rumps.App):
    def __init__(self):
        super(Voice2ClipApp, self).__init__("V2C", title=None, icon=None)
        self.title = ICON_IDLE
        
        # Initialize components
        self.recorder = AudioRecorder(
            filename=os.path.expanduser("~/.voice2clip_recording.wav"),
            silence_threshold=800, # Adjusted threshold
            silence_timeout=3     # Stop after 3 seconds of silence
        )
        try:
            self.transcriber = GeminiTranscriber()
        except ValueError:
            rumps.alert("Error: GOOGLE_API_KEY not found. Please configure it in .env")
            self.transcriber = None

        self.is_processing = False
        
        # Global Hotkey Listener
        # We want Cmd+Shift+D (which is mapped to the mouse gesture)
        self.hotkey_listener = keyboard.GlobalHotKeys({
            '<cmd>+<shift>+d': self.on_hotkey
        })
        self.hotkey_listener.start()
        
        # Menu Items
        self.menu = [
            rumps.MenuItem("Start/Stop Recording (⌘+Shift+D)", callback=self.toggle_recording),
            rumps.separator,
            rumps.MenuItem("Preferences", callback=self.prefs),
            rumps.MenuItem("Quit", callback=self.quit_app)
        ]

    def on_hotkey(self):
        """Global hotkey handler."""
        # This runs in a separate thread from pynput, so we need to be careful with UI updates
        # rumps handles UI updates on main thread usually, but setting .title is often safe.
        # However, it's better to verify.
        # Trigger the toggle via a method that is safe.
        print("Global Hotkey Pressed")
        rumps.timer(0.1)(self.toggle_recording_wrapper)

    def toggle_recording_wrapper(self, _):
        """Wrapper for timer to call toggle_recording on main thread."""
        self.toggle_recording(None)

    def toggle_recording(self, sender=None):
        """Toggle between recording and stopping."""
        if self.is_processing:
            print("Processing... ignoring input")
            return

        if not self.recorder.is_recording:
            # START RECORDING
            print("Start triggered")
            self.title = ICON_REC
            if sender: sender.title = "Stop Recording"
            
            self.recorder.start(stop_callback=self.stop_and_process_callback)
            
            rumps.notification(
                title="Voice2Clip",
                subtitle="Listening...",
                message="Speak now. Silence or Shortcut to stop.",
            )
            
        else:
            # STOP RECORDING MANUALLY
            print("Stop triggered manually")
            self.stop_and_process()

    def stop_and_process_callback(self):
        """Called from recorder thread when silence is detected."""
        # rumps methods must be thread-safe or queued. 
        # Ideally, we trigger processing.
        # Since this call comes from a background thread, proceed carefully.
        self.stop_and_process()

    def stop_and_process(self):
        """Stops recording, transcribes, and updates UI."""
        file_path = self.recorder.stop()
        
        # UI Update to Processing
        self.title = ICON_PROCESS
        
        # Run transcription in a separate thread to keep UI responsive
        threading.Thread(target=self._process_audio, args=(file_path,)).start()

    def _process_audio(self, file_path):
        """Background worker for transcription."""
        self.is_processing = True
        
        if not self.transcriber:
             self.end_processing("API Key Missing")
             return

        result = self.transcriber.transcribe(file_path)
        
        # Result to clipboard
        pyperclip.copy(result)
        
        self.end_processing(result)

    def end_processing(self, partial_result):
        """Cleanup after processing."""
        self.is_processing = False
        self.title = ICON_IDLE
        
        print(f"Transcription complete: {partial_result[:50]}...")

        rumps.notification(
            title="Voice2Clip",
            subtitle="Copied to Clipboard!",
            message=partial_result[:100], # Preview
            sound=True
        )

    def quit_app(self, _):
        self.hotkey_listener.stop()
        rumps.quit_application()

    def prefs(self, _):
        rumps.alert("Preferences placeholder")

if __name__ == "__main__":
    Voice2ClipApp().run()
