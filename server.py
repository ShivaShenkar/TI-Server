from app.models.ws_message import WSMessage
from app.services.app_service import Apps

from app.controllers import (
    FetchController,
    FetchByIdController,
    InstallController,
    StopController,
    RunController,
    RunStatusPollController,
    ShutdownCancelController,
    ShutdownController,
    ShutdownScheduleController,
    UninstallController,
    UpdateController,
)
from flask import Flask, jsonify, wrappers
from flask_restful import Api
from flask_cors import CORS
from dataclasses import asdict
from flask_sock import Sock, ConnectionClosed
import json
import threading

app = Flask(__name__)
api = Api(app)
CORS(app)

sock = Sock(app)
_ws_clients: set = set()
_ws_clients_lock = threading.Lock()


@sock.route('/ws')
def events(ws):
    with _ws_clients_lock:
        _ws_clients.add(ws)
        print("established a WebSocket connection!")
    try:
        while True:
            data = ws.receive()
            try:
                payload = json.loads(data)
                msg_type = payload.get("type")
                app_id = payload.get("appId")
                if not msg_type or not isinstance(app_id, str):
                    continue

                if msg_type == "launch":
                    _, code = Apps().run_app(app_id)
                    running = code in (200, 409)
                    reply = json.dumps(asdict(
                        WSMessage('app-running' if running else 'app-stopped', app_id)
                    ))
                    ws.send(reply)

                elif msg_type == "stop":
                    _, code = Apps().stop_app(app_id)
                    reply = json.dumps(asdict(WSMessage('app-stopped', app_id)))
                    ws.send(reply)

            except (json.JSONDecodeError, KeyError, ValueError):
                pass
    except ConnectionClosed:
        pass
    finally:
        with _ws_clients_lock:
            _ws_clients.discard(ws)
            print("A WebSocket connection with client was closed")


def _broadcast(message_str: str) -> None:
    with _ws_clients_lock:
        dead = set()
        for ws in _ws_clients:
            try:
                ws.send(message_str)
            except ConnectionClosed:
                dead.add(ws)
        _ws_clients -= dead

api.add_resource(FetchController, "/api/fetch-data") # type: ignore
api.add_resource(FetchByIdController, "/api/fetch-data/<string:app_id>") # type: ignore
api.add_resource(InstallController, "/api/install-app/<string:app_id>/<string:version>") # type: ignore
api.add_resource(RunController, "/api/run-app/<string:app_id>") # type: ignore
api.add_resource(RunStatusPollController, "/api/run-status/<string:app_id>")    # type: ignore
api.add_resource(UninstallController, "/api/uninstall-app/<string:app_id>") # type: ignore
api.add_resource(UpdateController, "/api/update-app/<string:app_id>/<string:version>")  # type: ignore
api.add_resource(StopController, "/api/stop-app/<string:app_id>")    # type: ignore
api.add_resource(ShutdownController, "/api/shutdown")   # type: ignore
api.add_resource(ShutdownScheduleController, "/api/shutdown/schedule")  # type: ignore
api.add_resource(ShutdownCancelController, "/api/shutdown/cancel")  # type: ignore


@app.route("/", methods=["GET"])  # type: ignore
def hello() -> wrappers.Response:
    return jsonify(message="Hello, Flask!")


if __name__ == "__main__":
    Apps.set_broadcast_callback(_broadcast)
    Apps().start_monitor()
    # use_reloader=False so /api/shutdown can exit the process (reloader respawns the child)
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)
