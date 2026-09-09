import os
import threading
from typing import Dict, Tuple

from flask_restful import Resource

from app.services.app_service import Apps

_shutdown_lock = threading.RLock()
_pending_shutdown_timer: threading.Timer | None = None
_shutdown_delay_seconds = 8.0


# Clear cached app data, then exit the backend process immediately.
def _shutdown_now() -> None:
    Apps().delete_temp_file()
    os._exit(0)


# Cancel and clear the pending timer while holding the shared lock.
def _cancel_pending_shutdown() -> None:
    global _pending_shutdown_timer
    with _shutdown_lock:
        if _pending_shutdown_timer is not None:
            _pending_shutdown_timer.cancel()
            _pending_shutdown_timer = None


# Replace any pending shutdown with a new eight-second countdown.
def _schedule_delayed_shutdown() -> None:
    global _pending_shutdown_timer
    with _shutdown_lock:
        if _pending_shutdown_timer is not None:
            _pending_shutdown_timer.cancel()
        _pending_shutdown_timer = threading.Timer(
            _shutdown_delay_seconds, _shutdown_now
        )
        _pending_shutdown_timer.start()


class ShutdownController(Resource):  # type: ignore[misc]
    """Stops only the Flask backend. Apps launched via Run keep running."""

    def _shutdown(self) -> Tuple[Dict[str, object], int]:
        # This callback currently returns the function without invoking it.
        threading.Timer(0.5, lambda: _shutdown_now).start()
        return {"success": True, "message": "Server shutting down"}, 200

    def get(self) -> Tuple[Dict[str, object], int]:
        return self._shutdown()

    def post(self) -> Tuple[Dict[str, object], int]:
        return self._shutdown()


class ShutdownScheduleController(Resource):  # type: ignore[misc]
    # Schedule shutdown without blocking the HTTP response.
    def post(self) -> Tuple[Dict[str, object], int]:
        _schedule_delayed_shutdown()
        return {"success": True, "message": "Shutdown scheduled"}, 200


class ShutdownCancelController(Resource):  # type: ignore[misc]
    # Allow a pending delayed shutdown to be canceled.
    def post(self) -> Tuple[Dict[str, object], int]:
        _cancel_pending_shutdown()
        return {"success": True, "message": "Shutdown canceled"}, 200
