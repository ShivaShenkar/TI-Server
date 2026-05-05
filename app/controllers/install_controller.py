from typing import Dict, Tuple
from flask_restful import Resource

from app.services.app_service import Apps

# HTTP entry for install: delegates to service and maps result codes to HTTP + JSON.
class InstallController(Resource):  # type: ignore[misc]
    def get(self, app_id: str, version: str) -> Tuple[Dict[str, object], int]:
        status, code = Apps().install_app_version(app_id, version)

        if status:
            message = "App installed successfully"
        else:
            message = "App not found" if (code == 400 or code == 404) else "Could not install app"
            
        return {"success": status, "message": message}, code

