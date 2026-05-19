from typing import Tuple
from flask_restful import Resource
import json

from app.services.app_service import Apps


class FetchByIdController(Resource):  # type: ignore[misc]
    def get(self, app_id: str) -> Tuple[dict[str, object], int]:
        apps = Apps()

        if not apps.check_app_in_db(app_id):
            return {"success": False, "message": "App not found"}, 404

        app_model = apps.get_app_by_id(app_id)
        return json.loads(app_model.json()), 200
