from flask_restful import Resource

from app.services.app_service import Apps



class FetchController(Resource):
    def get(self):
        apps = Apps()
        appsDict = apps.get_apps()
        return [app.json() for app in appsDict.values()]
        
