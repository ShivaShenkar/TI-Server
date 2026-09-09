# from typing import Dict, Tuple

# from app.services.app_service import Apps
# from flask_restful import Resource


# class StopController(Resource):  # type: ignore[misc]
#     def get(self, app_id: str) -> Tuple[Dict[str, object], int]:
#         status, code = Apps().stop_app(app_id)

#         if status:
#             message = "App stopped successfully"
#         else:
#             message = (
#                 "App is not running"
#                 if code == 400
#                 else "Could not stop app"
#             )

#         return {"success": status, "message": message}, code
