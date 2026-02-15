import logging
import math
import struct
import threading
import time
import wave
from typing import Callable, Optional

import pyaudio

logger = logging.getLogger(__name__)


class AudioRecorder:
    def __init__(
        self,
        filename: str = "temp_recording.wav",
        silence_threshold: int = 1000,
        silence_timeout: int = 5,
    ):
        """
        Initialize the AudioRecorder.

        Args:
            filename: Path to save the WAV file.
            silence_threshold: Amplitude threshold to consider as silence.
            silence_timeout: Seconds of silence before auto-stopping.
        """
        self.filename = filename
        self.silence_threshold = silence_threshold
        self.silence_timeout = silence_timeout

        self.chunk = 1024
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 16000  # 16kHz is good for speech

        self.p = pyaudio.PyAudio()
        self.stream: Optional[pyaudio.Stream] = None
        self.frames: list[bytes] = []
        self.is_recording = False
        self._lock = threading.Lock()
        self._recording_thread: Optional[threading.Thread] = None
        self._stop_callback: Optional[Callable[[], None]] = None
        self._level_callback: Optional[Callable[[float], None]] = None

    def start(
        self,
        stop_callback: Optional[Callable[[], None]] = None,
        level_callback: Optional[Callable[[float], None]] = None,
    ) -> None:
        """Start recording asynchronously."""
        with self._lock:
            if self.is_recording:
                logger.warning("Already recording, ignoring start request")
                return

            self.frames = []
            self.is_recording = True
            self._stop_callback = stop_callback
            self._level_callback = level_callback

            self.stream = self.p.open(
                format=self.format,
                channels=self.channels,
                rate=self.rate,
                input=True,
                frames_per_buffer=self.chunk,
            )

        # Start the recording loop in a background thread
        self._recording_thread = threading.Thread(target=self._record_loop, daemon=True)
        self._recording_thread.start()

    def _record_loop(self) -> None:
        """Internal loop to read audio frames and check for silence."""
        logger.info("Listening...")
        silence_start_time = None

        try:
            while self.is_recording and self.stream:
                try:
                    data = self.stream.read(self.chunk, exception_on_overflow=False)
                    self.frames.append(data)

                    # Silence Detection
                    rms = self._get_rms(data)
                    if self._level_callback:
                        try:
                            self._level_callback(rms)
                        except Exception as e:
                            logger.debug("Error in level_callback: %s", e)
                    if rms < self.silence_threshold:
                        if silence_start_time is None:
                            silence_start_time = time.time()
                        elif time.time() - silence_start_time > self.silence_timeout:
                            logger.info("Silence detected for %ds. Stopping.", self.silence_timeout)
                            # We don't call self.stop() here anymore,
                            # we just break and let the finally block handle it
                            break
                    else:
                        silence_start_time = None

                except IOError as e:
                    logger.error("Error recording: %s", e)
                    break
        finally:
            with self._lock:
                self.is_recording = False
                self._level_callback = None
                if self.stream:
                    try:
                        self.stream.stop_stream()
                        self.stream.close()
                    except Exception as e:
                        logger.error(f"Error closing stream in _record_loop: {e}")
                    self.stream = None

            # Ensure callback happens outside the lock if possible,
            # but inside the end of thread
            if self._stop_callback:
                try:
                    self._stop_callback()
                except Exception as e:
                    logger.error(f"Error in stop_callback: {e}")

    def stop(self) -> str:
        """Stop recording and save the file. Returns the filename."""
        with self._lock:
            if self.is_recording:
                logger.info("Stopping recording...")
                self.is_recording = False

        # Wait for the thread to finish (it might have stopped itself via silence)
        if self._recording_thread and self._recording_thread.is_alive():
            if self._recording_thread != threading.current_thread():
                self._recording_thread.join(timeout=1.0)

        self._save_file()
        return self.filename

    def _save_file(self) -> None:
        """Saves recorded frames to a WAV file."""
        with self._lock:
            if not self.frames:
                logger.warning("No frames to save.")
                return

            logger.info("Saving %d frames to %s", len(self.frames), self.filename)
            try:
                with wave.open(self.filename, "wb") as wf:
                    wf.setnchannels(self.channels)
                    wf.setsampwidth(self.p.get_sample_size(self.format))
                    wf.setframerate(self.rate)
                    wf.writeframes(b"".join(self.frames))

                # Clear frames after successful save to prevent double-saving or reuse
                self.frames = []
                logger.info("Saved to %s", self.filename)
            except Exception as e:
                logger.error("Error saving file: %s", e)

    def _get_rms(self, chunk: bytes) -> float:
        """Calculate Root Mean Square (RMS) amplitude of audio chunk."""
        count = len(chunk) // 2
        if count == 0:
            return 0.0
        shorts = struct.unpack(f"{count}h", chunk)
        sum_squares = sum(s * s for s in shorts)
        return math.sqrt(sum_squares / count)

    def cleanup(self) -> None:
        """Terminate PyAudio and release resources."""
        if self.is_recording:
            self.stop()
        self.p.terminate()
        logger.info("PyAudio terminated")
