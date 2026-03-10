from flask_restful import Resource
from app.repositories.apps_db_repo import update_app_data
from app.services.app_service import filter_apps_by_os, get_all_apps_details

class FetchController(Resource):
    def get(self):
        update_app_data()
        apps = get_all_apps_details()
        filter_apps_by_os(apps)
        return [app.json for app in apps]
 