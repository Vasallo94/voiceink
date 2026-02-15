"""Tests for the recorder module."""

import struct

from recorder import AudioRecorder


class TestGetRms:
    def test_silence_returns_zero(self):
        recorder = AudioRecorder()
        silent = struct.pack("512h", *([0] * 512))
        assert recorder._get_rms(silent) == 0.0
        recorder.cleanup()

    def test_loud_signal(self):
        recorder = AudioRecorder()
        loud = struct.pack("512h", *([10000] * 512))
        assert recorder._get_rms(loud) == 10000.0
        recorder.cleanup()

    def test_mixed_signal(self):
        recorder = AudioRecorder()
        # Mix of values
        values = [1000, -1000] * 256
        mixed = struct.pack("512h", *values)
        rms = recorder._get_rms(mixed)
        assert 999 < rms < 1001  # Should be ~1000
        recorder.cleanup()

    def test_empty_chunk(self):
        recorder = AudioRecorder()
        assert recorder._get_rms(b"") == 0.0
        recorder.cleanup()


class TestRecorderInit:
    def test_default_values(self):
        r = AudioRecorder()
        assert r.rate == 16000
        assert r.channels == 1
        assert r.is_recording is False
        assert r._lock is not None
        r.cleanup()

    def test_custom_values(self):
        r = AudioRecorder(
            filename="/tmp/test.wav",
            silence_threshold=500,
            silence_timeout=10,
        )
        assert r.filename == "/tmp/test.wav"
        assert r.silence_threshold == 500
        assert r.silence_timeout == 10
        r.cleanup()

    def test_stop_without_recording(self):
        r = AudioRecorder()
        result = r.stop()  # Should not crash
        assert result == r.filename
        r.cleanup()
