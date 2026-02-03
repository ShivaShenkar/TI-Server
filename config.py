from flask import Blueprint, jsonify
from services.fetch_service import fetch_data

api_bp = Blueprint("api_bp", __name__)

@api_bp.route("/fetch-data", methods=["GET"])
def fetch():
    return fetch_data()
