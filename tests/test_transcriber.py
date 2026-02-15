"""Tests for the transcriber module."""

import os
from unittest.mock import MagicMock, patch

import pytest
from transcriber import TRANSCRIPTION_PROMPT, GeminiTranscriber


class TestTranscriptionPrompt:
    def test_includes_language_detection(self):
        assert "Respeta el idioma del audio" in TRANSCRIPTION_PROMPT

    def test_includes_spanish_fillers(self):
        assert "eh" in TRANSCRIPTION_PROMPT
        assert "o sea" in TRANSCRIPTION_PROMPT

    def test_includes_english_fillers(self):
        assert "meta-lenguaje" in TRANSCRIPTION_PROMPT
        assert "Si NO pide estructura explícita" in TRANSCRIPTION_PROMPT

    def test_no_meta_commentary(self):
        assert "NUNCA respondas al usuario" in TRANSCRIPTION_PROMPT


class TestGeminiTranscriber:
    def test_init_raises_without_key(self):
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="GOOGLE_API_KEY"):
                GeminiTranscriber(api_key=None)

    @patch("transcriber.genai.Client")
    def test_init_with_explicit_key(self, mock_client):
        t = GeminiTranscriber(api_key="test-key-123")
        assert t.api_key == "test-key-123"
        assert t.model_name == "gemini-2.5-flash"

    @patch("transcriber.genai.Client")
    def test_transcribe_missing_file(self, mock_client):
        t = GeminiTranscriber(api_key="test-key")
        result = t.transcribe("/nonexistent/audio.wav")
        assert "Error" in result

    @patch("transcriber.genai.Client")
    def test_transcribe_success(self, mock_client, tmp_path):
        # Create a fake audio file
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"fake audio data")

        # Mock response
        mock_response = MagicMock()
        mock_response.text = "  Transcribed text here  "
        mock_client.return_value.models.generate_content.return_value = mock_response

        t = GeminiTranscriber(api_key="test-key")
        result = t.transcribe(str(audio_file))
        assert result == "Transcribed text here"  # stripped

    @patch("transcriber.genai.Client")
    def test_transcribe_api_error(self, mock_client, tmp_path):
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"fake audio")

        mock_client.return_value.models.generate_content.side_effect = Exception("API down")

        t = GeminiTranscriber(api_key="test-key")
        result = t.transcribe(str(audio_file))
        assert "Error" in result
        assert "API down" in result
