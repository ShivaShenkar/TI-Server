from typing import Dict
from flask_socketio import Namespace

from app.services.app_service import Apps


class RunNamespace(Namespace):
    def on_connect(self):
        print("Client is connected!")

    def on_disconnect(self):
        print("Client disconnected.")

    def on_client_message(self, data: Dict[str, str]):
        apps = Apps()
        match data["type"]:  # type: ignore
            case "launch":
                apps.run_app(data["appId"])
            case "stop":
                apps.stop_app(data["appId"])
            case "app-stopped" | "app-running":
                print("Im The GOATTTTTTTTT!!!!")

    def send_response(self, response: Dict[str, str]):
        self.emit("server_response", data=response)  # type: ignore
