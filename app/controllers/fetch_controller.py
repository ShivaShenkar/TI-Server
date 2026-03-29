from flask_restful import Resource

from app.services.app_service import Apps


class FetchController(Resource):  # type: ignore[misc]
    def get(self) -> list[str]:
        apps = Apps()
        apps_dict = apps.get_apps()
        return [app.json() for app in apps_dict.values()]
