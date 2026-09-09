from typing import Dict, Tuple

from app.services.app_service import Apps
from flask_restful import Resource


class InstallController(Resource):  # type: ignore[misc]
    # Install the requested release and translate its result into a client message.
    def get(self, app_id: str, version: str) -> Tuple[Dict[str, object], int]:
        success, code = Apps().install_app_version(app_id, version)

        if success:
            message = "App installed successfully"
        else:
            message = (
                "App not found"
                if (code == 400 or code == 404)
                else "Could not install app"
            )

        return {"success": success, "message": message}, code
