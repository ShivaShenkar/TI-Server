from types import FrameType

from app.services.app_service import Apps
from app.controllers import (
    FetchController,
    # FetchByIdController,
    InitialFetchController,
    InstallController,
    # StopController,
    # RunController,
    # RunStatusPollController,
    ShutdownCancelController,
    ShutdownController,
    ShutdownScheduleController,
    UninstallController,
    UpdateController,
    RunNamespace,
)

# from gevent import monkey
# monkey.patch_all()
from flask import Flask, send_from_directory  # type: ignore
from flask_restful import Api
from flask_cors import CORS
from flask_socketio import SocketIO
import threading
import signal
import os
import webbrowser


UI_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui")


app = Flask(__name__)
api = Api(app)
CORS(app)
# sio = SocketIO(app, cors_allowed_origins="*")
sio = SocketIO(app, cors_allowed_origins="*", async_mode="gevent")
run_namespace = RunNamespace("/app-running-status")
sio.on_namespace(run_namespace)  # type: ignore


# Serve index.html at root
@app.route("/")
def serve_index():
    return send_from_directory(UI_DIR, "index.html")


# Serve static UI files + SPA fallback
@app.route("/<path:path>")
def serve_ui(path: str):
    file_path = os.path.join(UI_DIR, path)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return send_from_directory(UI_DIR, path)
    # SPA fallback: any unmatched path serves index.html
    return send_from_directory(UI_DIR, "index.html")


# api.add_resource(FetchByIdController, "/api/fetch-data/<string:app_id>") # type: ignore
# api.add_resource(RunController, "/api/run-app/<string:app_id>")  # type: ignore
# api.add_resource(RunStatusPollController, "/api/run-status/<string:app_id>")  # type: ignore
# api.add_resource(StopController, "/api/stop-app/<string:app_id>")  # type: ignore

api.add_resource(FetchController, "/api/fetch-data")  # type: ignore
api.add_resource(InitialFetchController, "/api/initial-fetch")  # type: ignore
api.add_resource(InstallController, "/api/install-app/<string:app_id>/<string:version>")  # type: ignore
api.add_resource(UninstallController, "/api/uninstall-app/<string:app_id>")  # type: ignore
api.add_resource(UpdateController, "/api/update-app/<string:app_id>/<string:version>")  # type: ignore
api.add_resource(ShutdownController, "/api/shutdown")  # type: ignore
api.add_resource(ShutdownScheduleController, "/api/shutdown/schedule")  # type: ignore
api.add_resource(ShutdownCancelController, "/api/shutdown/cancel")  # type: ignore


def close_server(sigNum: int, frame: FrameType | None):
    apps = Apps()
    apps.store_running_apps()
    # apps.delete_temp_file()
    os._exit(0)


if __name__ == "__main__":
    apps = Apps()
    apps.set_broadcast_callback(run_namespace.send_response)
    thread = threading.Thread(target=apps.monitor_running_apps, daemon=True)
    thread.start()
    apps.read_running_apps_file()
    apps.fetch_from_temp_file()

    signal.signal(signal.SIGINT, close_server)
    signal.signal(signal.SIGTERM, close_server)
    if hasattr(signal, "SIGHUP"):
        signal.signal(signal.SIGHUP, close_server)  # type: ignore

    threading.Timer(
        1.5,
        lambda: (
            print("Opening Web Browser..."),
            webbrowser.open("http://127.0.0.1:5000/"),
        ),
    ).start()
    sio.run(app, host="127.0.0.1", port=5000, debug=True, use_reloader=False)  # type: ignore
