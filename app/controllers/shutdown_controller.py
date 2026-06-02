import os
import threading
from typing import Dict, Tuple

from flask_restful import Resource

_shutdown_lock = threading.RLock()
_pending_shutdown_timer: threading.Timer | None = None
_shutdown_delay_seconds = 8.0


def _shutdown_now() -> None:
    os._exit(0)


def _cancel_pending_shutdown() -> None:
    global _pending_shutdown_timer
    with _shutdown_lock:
        if _pending_shutdown_timer is not None:
            _pending_shutdown_timer.cancel()
            _pending_shutdown_timer = None


def _schedule_delayed_shutdown() -> None:
    global _pending_shutdown_timer
    with _shutdown_lock:
        if _pending_shutdown_timer is not None:
            _pending_shutdown_timer.cancel()
        _pending_shutdown_timer = threading.Timer(_shutdown_delay_seconds, _shutdown_now)
        _pending_shutdown_timer.start()


class ShutdownController(Resource):  # type: ignore[misc]
    """Stops only the Flask backend. Apps launched via Run keep running."""

    def _shutdown(self) -> Tuple[Dict[str, object], int]:
        threading.Timer(0.5, lambda: os._exit(0)).start()
        return {"success": True, "message": "Server shutting down"}, 200

    def get(self) -> Tuple[Dict[str, object], int]:
        return self._shutdown()

    def post(self) -> Tuple[Dict[str, object], int]:
        return self._shutdown()


class ShutdownScheduleController(Resource):  # type: ignore[misc]
    def post(self) -> Tuple[Dict[str, object], int]:
        _schedule_delayed_shutdown()
        return {"success": True, "message": "Shutdown scheduled"}, 200


class ShutdownCancelController(Resource):  # type: ignore[misc]
    def post(self) -> Tuple[Dict[str, object], int]:
        _cancel_pending_shutdown()
        return {"success": True, "message": "Shutdown canceled"}, 200
