from flask_restful import Resource
import json


from app.services.app_service import Apps


class FetchController(Resource):  # type: ignore[misc]
    def get(self) -> tuple[dict[str,dict[str, object]],int]:
        apps = Apps()
        code = apps.fetch_landing_page()
        if code != 200:
            return {}, code
        return {id: app.json() for (id, app) in apps._apps.items()}, 200
