from typing import Dict, Tuple
from flask_restful import Resource
from app.models.ws_message import WSMessage
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


class RunStatusPollController(Resource):  # type: ignore[misc]
    def get(self, app_id: str) -> Tuple[WSMessage,int]:
        running, code = Apps().is_app_running(app_id)
        if code == 400:
            return WSMessage('app-stopped',app_id), code

        message = 'app-running' if running else 'app-stopped'
        return  WSMessage(message,app_id), code
    