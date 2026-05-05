from typing import Dict, Tuple
from flask_restful import Resource

from app.services.app_service import Apps


class RunController(Resource):  # type: ignore[misc]
    def get(self, app_id: str) -> Tuple[Dict[str, object], int]:
        status, code = Apps().run_app(app_id)

        if status:
            message = "App started successfully"
        else:
            if code == 400:
                message = "App not found"
            elif code == 404:
                message = "App is not installed or executable path is invalid"
            elif code == 409:
                message = "App is already running"
            else:
                message = "Could not run app"

        return {"success": status, "message": message}, code


class RunStatusController(Resource):  # type: ignore[misc]
    def get(self, app_id: str) -> Tuple[Dict[str, object], int]:
        running, code = Apps().is_app_running(app_id)
        if code == 400:
            return {"success": False, "message": "App not found", "running": False}, code

        message = "App is running" if running else "App is not running"
        return {"success": True, "message": message, "running": running}, code
