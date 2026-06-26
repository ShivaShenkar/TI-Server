# from typing import Tuple

# from app.services.app_service import Apps
# from flask_restful import Resource


# class FetchByIdController(Resource):  # type: ignore[misc]
#     def get(self, app_id: str) -> Tuple[dict[str, object], int]:
#         apps = Apps()
#         code = apps.fetch_app_details(app_id)
#         if code != 200:
#             return {"error": f"error fetching app details for ID {app_id}"}, code

#         return apps.get_app_by_id(app_id).model_dump(), 200
