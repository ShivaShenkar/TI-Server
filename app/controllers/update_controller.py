from typing import Dict, Tuple

from app.services.app_service import Apps
from flask_restful import Resource


class UpdateController(Resource):  # type: ignore[misc]
    # Updates share the installer; only the response message differs.
    def get(self, app_id: str, version: str) -> Tuple[Dict[str, object], int]:
        status, code = Apps().install_app_version(app_id, version)
        if status:
            message = "App updated successfully"
        else:
            message = (
                "App not found"
                if code == 400
                else "App is not installed" if code == 404 else "Could not update app"
            )

        return {"success": status, "message": message}, code
