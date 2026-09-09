from app.services.app_service import Apps
from flask_restful import Resource


class InitialFetchController(Resource):
    # Refresh remote metadata and return app records keyed by ID.
    def get(self) -> tuple[dict[str, dict[str, object]], int]:
        apps = Apps()
        apps.initial_fetch()
        return {id: app.model_dump() for (id, app) in apps.get_apps().items()}, 200
