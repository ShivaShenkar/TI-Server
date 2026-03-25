from app.controllers import FetchController
from flask import Flask, jsonify
from flask_restful import Api

app = Flask(__name__)
api = Api(app)

api.add_resource(FetchController, "/api/fetch-data")


@app.route("/", methods=["GET"])
def hello():
    return jsonify(message="Hello, Flask!")


if __name__ == "main":
    app.run(host="0.0.0.0", port=5000, debug=True)
