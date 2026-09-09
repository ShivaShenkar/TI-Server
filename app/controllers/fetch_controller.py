from app.services.app_service import Apps
from flask_restful import Resource


class FetchController(Resource):  # type: ignore[misc]
    # Read cached app data, fetching remotely if the cache is empty or invalid.
    def get(self) -> tuple[dict[str, dict[str, object]], int]:
        apps = Apps()
        apps.fetch_from_temp_file()
        return {id: app.model_dump() for (id, app) in apps.get_apps().items()}, 200
