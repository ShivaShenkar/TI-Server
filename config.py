from flask import Blueprint, jsonify, Response

from server.services.app_data_service import (
    get_detailed_apps_data,
    get_app_from_db,
    get_app_releases,
)
from server.services.files_service import install_app

api_bp = Blueprint("api_bp", __name__)


@api_bp.route("/fetch-data", methods=["GET"])
def fetch():
    return get_detailed_apps_data()


@api_bp.route("/install-app/<string:id>/<string:version>", methods=["GET"])
def install_app_route(id, version):
    app = get_app_from_db(id)
    if not app:
        return jsonify({"error": f"App with id:{id} not found"}), 404

    app_releases = get_app_releases(id)
    if not app_releases:
        return jsonify({"error": f"Could not found release for {id}"}), 404

    for release in app_releases:
        if release["tag_name"] == version:
            zip_url = release["zipball_url"]
            break
    else:
        return (
            jsonify({"error": f"Version {version} not found for app with id: {id}"}),
            404,
        )

    def generate():
        try:
            for progress_data in install_app(id, zip_url):
                yield f"data: {jsonify(progress_data).get_json() if hasattr(jsonify(progress_data), 'get_json') else progress_data}\n\n"
        except Exception as e:
            yield f"data: {{'error': '{str(e)}'}}\n\n"

    return Response(generate(), mimetype="text/event-stream")


@api_bp.route("/uninstall-app/<string:id>", methods=["GET"])
def uninstall_app(id):
    def generate():
        # Your event stream logic here
        yield "data: Uninstallation started\n\n"

    return Response(generate(), mimetype="text/event-stream")
