from typing import Dict, Tuple
from flask_restful import Resource

from app.services.app_service import Apps


# HTTP entry for update: remove current install and install requested version.
class UpdateController(Resource):  # type: ignore[misc]
    def get(self, app_id: str, version: str) -> Tuple[Dict[str, object], int]:
        status, code = Apps().install_app_version(app_id, version)
        if status:
            message = "App updated successfully"
        else:
            message = "App not found" if code == 400 else "App is not installed" if code == 404 else "Could not update app"
            
        return {"success": status, "message": message}, code
    
 

