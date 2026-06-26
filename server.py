from app.services.app_service import Apps
from app.controllers import (
    FetchController,
    # FetchByIdController,
    InitialFetchController,
    InstallController,
    StopController,
    RunController,
    RunStatusPollController,
    ShutdownCancelController,
    ShutdownController,
    ShutdownScheduleController,
    UninstallController,
    UpdateController,
    RunNamespace,
)
from flask import Flask, wrappers, jsonify  # type: ignore
from flask_restful import Api
from flask_cors import CORS
from flask_socketio import SocketIO
import threading


app = Flask(__name__)
api = Api(app)
CORS(app)
sio = SocketIO(app, cors_allowed_origins="*", async_mode="gevent")
run_namespace = RunNamespace("/app-running-status")
sio.on_namespace(run_namespace)  # type: ignore

# sio.register_namespace(RunningNamespace('/app-running-status')) #type: ignore
# class RunningNamespace(Namespace):
#     def on_connect(self):
#         print("Client joined the /app-running-status Namespace")
#     def on


api.add_resource(FetchController, "/api/fetch-data")  # type: ignore
# api.add_resource(FetchByIdController, "/api/fetch-data/<string:app_id>") # type: ignore
api.add_resource(InitialFetchController, "/api/initial-fetch")  # type: ignore
api.add_resource(InstallController, "/api/install-app/<string:app_id>/<string:version>")  # type: ignore
api.add_resource(RunController, "/api/run-app/<string:app_id>")  # type: ignore
api.add_resource(RunStatusPollController, "/api/run-status/<string:app_id>")  # type: ignore
api.add_resource(UninstallController, "/api/uninstall-app/<string:app_id>")  # type: ignore
api.add_resource(UpdateController, "/api/update-app/<string:app_id>/<string:version>")  # type: ignore
api.add_resource(StopController, "/api/stop-app/<string:app_id>")  # type: ignore
api.add_resource(ShutdownController, "/api/shutdown")  # type: ignore
api.add_resource(ShutdownScheduleController, "/api/shutdown/schedule")  # type: ignore
api.add_resource(ShutdownCancelController, "/api/shutdown/cancel")  # type: ignore


@app.route("/", methods=["GET"])
def hello() -> wrappers.Response:
    return jsonify(message="Hello, Flask!")  # type: ignore


if __name__ == "__main__":
    apps = Apps()
    apps.set_broadcast_callback(run_namespace.send_response)
    thread = threading.Thread(target=apps.monitor_running_apps, daemon=True)
    thread.start()
    # use_reloader=False so /
    # app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)
    sio.run(app, host="127.0.0.1", port=5000, debug=True)  # type: ignore
