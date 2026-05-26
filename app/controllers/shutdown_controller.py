import os
import threading
from typing import Dict, Tuple

from flask_restful import Resource


class ShutdownController(Resource):  # type: ignore[misc]
    """Stops only the Flask backend. Apps launched via Run keep running."""

    def _shutdown(self) -> Tuple[Dict[str, object], int]:
        threading.Timer(0.5, lambda: os._exit(0)).start()
        return {"success": True, "message": "Server shutting down"}, 200

    def get(self) -> Tuple[Dict[str, object], int]:
        return self._shutdown()

    def post(self) -> Tuple[Dict[str, object], int]:
        return self._shutdown()
