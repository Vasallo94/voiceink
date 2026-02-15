"""Tests for the history module."""

import json
import os
import tempfile
import time

import pytest
from history import get_file_version, get_recent, load_history, save_entry


@pytest.fixture
def history_file():
    """Create a temporary history file."""
    path = tempfile.mktemp(suffix=".json")
    yield path
    if os.path.exists(path):
        os.unlink(path)


class TestLoadHistory:
    def test_returns_empty_for_missing_file(self, tmp_path):
        assert load_history(str(tmp_path / "nope.json")) == []

    def test_returns_empty_for_corrupt_json(self, history_file):
        with open(history_file, "w") as f:
            f.write("{not valid json")
        assert load_history(history_file) == []

    def test_loads_existing_entries(self, history_file):
        data = [{"text": "hello", "timestamp": "2026-01-01T00:00:00", "duration_secs": 1.0}]
        with open(history_file, "w") as f:
            json.dump(data, f)
        result = load_history(history_file)
        assert len(result) == 1
        assert result[0]["text"] == "hello"


class TestSaveEntry:
    def test_creates_file_if_missing(self, history_file):
        save_entry("test text", 2.5, history_file)
        assert os.path.exists(history_file)
        data = json.loads(open(history_file).read())
        assert len(data) == 1
        assert data[0]["text"] == "test text"
        assert data[0]["duration_secs"] == 2.5

    def test_appends_to_existing(self, history_file):
        save_entry("first", 1.0, history_file)
        save_entry("second", 2.0, history_file)
        data = json.loads(open(history_file).read())
        assert len(data) == 2
        assert data[0]["text"] == "first"
        assert data[1]["text"] == "second"

    def test_caps_at_max_entries(self, history_file):
        for i in range(55):
            save_entry(f"entry {i}", 0.5, history_file)
        data = json.loads(open(history_file).read())
        assert len(data) == 50
        assert data[0]["text"] == "entry 5"  # oldest kept

    def test_includes_timestamp(self, history_file):
        save_entry("hello", 1.0, history_file)
        data = json.loads(open(history_file).read())
        assert "timestamp" in data[0]
        assert "T" in data[0]["timestamp"]  # ISO format


class TestGetRecent:
    def test_returns_last_n(self, history_file):
        for i in range(5):
            save_entry(f"entry {i}", 0.5, history_file)
        recent = get_recent(3, history_file)
        assert len(recent) == 3
        assert recent[0]["text"] == "entry 2"

    def test_returns_all_if_less_than_n(self, history_file):
        save_entry("only one", 1.0, history_file)
        recent = get_recent(10, history_file)
        assert len(recent) == 1

    def test_returns_empty_for_missing_file(self, tmp_path):
        recent = get_recent(5, str(tmp_path / "nope.json"))
        assert recent == []


class TestHistoryVersion:
    def test_returns_zero_for_missing_file(self, tmp_path):
        version = get_file_version(str(tmp_path / "missing.json"))
        assert version == (0, 0)

    def test_changes_after_write(self, history_file):
        before = get_file_version(history_file)
        save_entry("test", 1.0, history_file)
        time.sleep(0.001)
        save_entry("test2", 1.0, history_file)
        after = get_file_version(history_file)
        assert before != after
