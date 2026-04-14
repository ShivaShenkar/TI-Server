from typing import Tuple

from flask import Response, jsonify
from flask_restful import Resource

from app.services.app_service import uninstall_app


# HTTP entry for uninstall: delegates to the service and turns result codes into status + JSON.
class UninstallController(Resource):  # type: ignore[misc]
    def delete(self, app_id: str) -> Tuple[Response, int] | Response:
        ok, code = uninstall_app(app_id)
        # Map business outcome to HTTP (body is always JSON for the client).
        if ok:
            return jsonify(success=True, message="App uninstalled"), 200
        if code == "invalid_id":
            return jsonify(success=False, error="Invalid app id"), 400
        if code == "not_installed":
            return jsonify(success=False, error="App is not installed"), 404
        return jsonify(success=False, error="Could not remove app files"), 500
