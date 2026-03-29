from app.controllers import FetchController
from flask import Flask, jsonify, wrappers
from flask_restful import Api
from flask_cors import CORS

app = Flask(__name__)
api = Api(app)
CORS(app)

api.add_resource(FetchController, "/api/fetch-data")


@app.route("/", methods=["GET"])  # type: ignore
def hello() -> wrappers.Response:
    return jsonify(message="Hello, Flask!")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
