import pyaudio
import wave
import time
import struct
import math
import asyncio
import os
from typing import Optional, Callable

class AudioRecorder:
    def __init__(self, filename: str = "temp_recording.wav", silence_threshold: int = 1000, silence_timeout: int = 5):
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
        self.rate = 16000 # 16kHz is good for speech
        
        self.p = pyaudio.PyAudio()
        self.stream: Optional[pyaudio.Stream] = None
        self.frames: list[bytes] = []
        self.is_recording = False
        self._loop = None
        self._stop_callback: Optional[Callable[[], None]] = None

    def start(self, stop_callback: Optional[Callable[[], None]] = None) -> None:
        """Start recording asynchronously."""
        self.frames = []
        self.is_recording = True
        self._stop_callback = stop_callback
        
        self.stream = self.p.open(
            format=self.format,
            channels=self.channels,
            rate=self.rate,
            input=True,
            frames_per_buffer=self.chunk
        )
        
        # Start the recording loop in a background thread to avoid blocking GUI
        import threading
        self._recording_thread = threading.Thread(target=self._record_loop)
        self._recording_thread.start()

    def _record_loop(self) -> None:
        """Internal loop to read audio frames and check for silence."""
        print("Listening...")
        silence_start_time = None
        
        while self.is_recording and self.stream:
            try:
                data = self.stream.read(self.chunk, exception_on_overflow=False)
                self.frames.append(data)
                
                # Silence Detection
                rms = self._get_rms(data)
                if rms < self.silence_threshold:
                    if silence_start_time is None:
                        silence_start_time = time.time()
                    elif time.time() - silence_start_time > self.silence_timeout:
                        print(f"Silence detected for {self.silence_timeout}s. Stopping.")
                        self.stop()
                        if self._stop_callback:
                            self._stop_callback() # Notify app to update UI
                        break
                else:
                    silence_start_time = None
                    
            except IOError as e:
                print(f"Error recording: {e}")
                break

    def stop(self) -> str:
        """Stop recording and save the file. Returns the filename."""
        if not self.is_recording:
            return self.filename
            
        print("Stopping recording...")
        self.is_recording = False
        
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None

        self._save_file()
        return self.filename

    def _save_file(self) -> None:
        """Save recorded frames to a WAV file."""
        if not self.frames:
            return
            
        wf = wave.open(self.filename, 'wb')
        wf.setnchannels(self.channels)
        wf.setsampwidth(self.p.get_sample_size(self.format))
        wf.setframerate(self.rate)
        wf.writeframes(b''.join(self.frames))
        wf.close()
        print(f"Saved to {self.filename}")

    def _get_rms(self, chunk: bytes) -> float:
        """Calculate Root Mean Square (RMS) amplitude of audio chunk."""
        count = len(chunk) / 2
        format_str = "%dh" % (count)
        shorts = struct.unpack(format_str, chunk)
        sum_squares = 0.0
        for sample in shorts:
            n = sample * 1.0 # normalize
            sum_squares += n * n
        
        try:
            return math.sqrt(sum_squares / count)
        except ZeroDivisionError:
            return 0.0

    def cleanup(self) -> None:
        """Terminate PyAudio."""
        self.p.terminate()
