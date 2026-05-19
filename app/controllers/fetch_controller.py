from flask_restful import Resource
import json


from app.services.app_service import Apps


class FetchController(Resource):  # type: ignore[misc]
    def get(self) -> tuple[dict[str,dict[str, object]],int]:
        apps = Apps()
        apps.fetch_landing_page()
        return {id: app.json() for (id, app) in apps._apps.items()}, 200
