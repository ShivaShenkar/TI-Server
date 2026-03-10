from typing import Generator

from flask import Blueprint, Response

from app.services.app_service import (
    fetch_detailed_apps,
    stream_install_app,
    stream_uninstall_app,
)

api_bp: Blueprint = Blueprint("api_bp", __name__, url_prefix="/api")


@api_bp.get("/fetch-data")
def fetch_data() -> Response:
    """
    Fetch detailed application data.
    """
    return fetch_detailed_apps()


@api_bp.get("/install-app/<string:app_id>/<string:version>")
def install_app_route(app_id: str, version: str) -> Response:
    """
    Stream installation progress via Server-Sent Events (SSE).
    """
    event_stream: Generator[str, None, None] = stream_install_app(
        app_id=app_id,
        version=version,
    )

    return Response(event_stream, mimetype="text/event-stream")


@api_bp.get("/uninstall-app/<string:app_id>")
def uninstall_app_route(app_id: str) -> Response:
    """
    Stream uninstallation progress via SSE.
    """
    event_stream: Generator[str, None, None] = stream_uninstall_app(
        app_id=app_id,
    )

    return Response(event_stream, mimetype="text/event-stream")
