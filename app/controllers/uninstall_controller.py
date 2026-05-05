from typing import Dict, Tuple
from flask_restful import Resource

from app.services.app_service import Apps


# HTTP entry for uninstall: delegates to the service and turns result codes into status + JSON.
class UninstallController(Resource):  # type: ignore[misc]
    def _run_uninstall(self, app_id: str) -> Tuple[Dict[str, object], int]:
        status, code = Apps().uninstall_app(app_id)
        # Map business outcome to HTTP (body is always JSON for the client).
        if status:
            message = "App uninstalled successfully"
        else:
            message = "App not found" if code == 400 else "App is not installed" if code == 404 else "Could not remove app files"
            
        return {"success": status, "message": message}, code


    def get(self, app_id: str) -> Tuple[Dict[str, object], int]:
        return self._run_uninstall(app_id)

    def delete(self, app_id: str) -> Tuple[Dict[str, object], int]:
        return self._run_uninstall(app_id)
