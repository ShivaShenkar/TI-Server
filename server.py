from app.controllers import (
    FetchController,
    FetchByIdController,
    InstallController,
    RunController,
    RunStatusController,
    ShutdownCancelController,
    ShutdownController,
    ShutdownScheduleController,
    UninstallController,
    UpdateController,
)
from flask import Flask, jsonify, wrappers
from flask_restful import Api
from flask_cors import CORS

app = Flask(__name__)
api = Api(app)
CORS(app)

api.add_resource(FetchController, "/api/fetch-data")
api.add_resource(FetchByIdController, "/api/fetch-data/<string:app_id>")
api.add_resource(InstallController, "/api/install-app/<string:app_id>/<string:version>")
api.add_resource(RunController, "/api/run-app/<string:app_id>")
api.add_resource(RunStatusController, "/api/run-status/<string:app_id>")
api.add_resource(UninstallController, "/api/uninstall-app/<string:app_id>")
api.add_resource(UpdateController, "/api/update-app/<string:app_id>/<string:version>")
api.add_resource(ShutdownController, "/api/shutdown")
api.add_resource(ShutdownScheduleController, "/api/shutdown/schedule")
api.add_resource(ShutdownCancelController, "/api/shutdown/cancel")


@app.route("/", methods=["GET"])  # type: ignore
def hello() -> wrappers.Response:
    return jsonify(message="Hello, Flask!")


if __name__ == "__main__":
    # use_reloader=False so /api/shutdown can exit the process (reloader respawns the child)
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)
