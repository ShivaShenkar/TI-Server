
from server import app


@app.route("/fetch-data", methods=["GET"])
def hello():
    