"""Tests for the sounds module."""

import os
from unittest.mock import patch

from sounds import (
    SOUND_ERROR,
    SOUND_START,
    SOUND_STOP,
    play,
    play_error,
    play_start,
    play_stop,
)


class TestSoundPaths:
    def test_start_sound_exists(self):
        assert os.path.exists(SOUND_START)

    def test_stop_sound_exists(self):
        assert os.path.exists(SOUND_STOP)

    def test_error_sound_exists(self):
        assert os.path.exists(SOUND_ERROR)


class TestPlay:
    @patch("sounds.subprocess.Popen")
    def test_play_calls_afplay(self, mock_popen):
        play(SOUND_START)
        mock_popen.assert_called_once()
        args = mock_popen.call_args[0][0]
        assert args[0] == "afplay"
        assert args[1] == SOUND_START

    @patch("sounds.subprocess.Popen", side_effect=FileNotFoundError)
    def test_play_handles_missing_afplay(self, mock_popen):
        # Should not raise
        play(SOUND_START)

    @patch("sounds.subprocess.Popen")
    def test_play_start_uses_correct_sound(self, mock_popen):
        play_start()
        args = mock_popen.call_args[0][0]
        assert args[1] == SOUND_START

    @patch("sounds.subprocess.Popen")
    def test_play_stop_uses_correct_sound(self, mock_popen):
        play_stop()
        args = mock_popen.call_args[0][0]
        assert args[1] == SOUND_STOP

    @patch("sounds.subprocess.Popen")
    def test_play_error_uses_correct_sound(self, mock_popen):
        play_error()
        args = mock_popen.call_args[0][0]
        assert args[1] == SOUND_ERROR
