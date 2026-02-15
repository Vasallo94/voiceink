"""Tests for Voice2Clip app state transitions."""

import threading

from app_controller import AppController, AppState


def make_app_stub():
    app = AppController.__new__(AppController)
    app._state = AppState.IDLE
    app._state_lock = threading.Lock()
    return app


class TestAppState:
    def test_transition_success(self):
        app = make_app_stub()

        assert app._transition_state(AppState.IDLE, AppState.RECORDING)
        assert app._get_state() == AppState.RECORDING

    def test_transition_fails_on_unexpected_state(self):
        app = make_app_stub()

        assert not app._transition_state(AppState.RECORDING, AppState.PROCESSING)
        assert app._get_state() == AppState.IDLE

    def test_set_state_overrides_current(self):
        app = make_app_stub()

        app._set_state(AppState.PROCESSING)
        assert app._get_state() == AppState.PROCESSING
