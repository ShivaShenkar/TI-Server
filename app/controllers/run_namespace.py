from typing import Dict
from flask_socketio import Namespace

from app.services.app_service import Apps


# Socket.IO commands and responses for app process tracking.
class RunNamespace(Namespace):
    def on_connect(self):
        print("Client is connected!")

    def on_disconnect(self):
        print("Client disconnected.")

    # Dispatch client_message by type; launch and stop also require appId.
    def on_client_message(self, data: Dict[str, str]):
        apps = Apps()
        match data["type"]:  # type: ignore
            case "launch":
                apps.run_app(data["appId"])
            case "stop":
                apps.stop_app(data["appId"])
            # A status request returns the full set of tracked app IDs.
            case "status":
                self.send_response({"type": "running-apps", "appIds": list(apps._running_processes)})  # type: ignore

    # Send status events through the same namespace used by the Angular client.
    def send_response(self, response: Dict[str, str]):
        self.emit("server_response", data=response)  # type: ignore
