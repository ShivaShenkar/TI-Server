from typing import Dict, Tuple

from app.services.app_service import Apps
from flask_restful import Resource


class UninstallController(Resource):  # type: ignore[misc]
    # Build the shared response for both uninstall HTTP methods.
    def _run_uninstall(self, app_id: str) -> Tuple[Dict[str, object], int]:
        success, code = Apps().uninstall_app(app_id)
        if success:
            message = "App uninstalled successfully"
        else:
            message = (
                "App not found"
                if code == 400
                else "App is not installed"
                if code == 404
                else "Could not remove app files"
            )

        return {"success": success, "message": message}, code


    def get(self, app_id: str) -> Tuple[Dict[str, object], int]:
        return self._run_uninstall(app_id)

    def delete(self, app_id: str) -> Tuple[Dict[str, object], int]:
        return self._run_uninstall(app_id)
