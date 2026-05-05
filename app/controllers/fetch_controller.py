from flask_restful import Resource
import json

from app.services.app_service import Apps


class FetchController(Resource):  # type: ignore[misc]
    def get(self) -> list[dict[str, object]]:
        apps = Apps()
        apps_dict = apps.get_apps()
        return [json.loads(app.json()) for app in apps_dict.values()]
