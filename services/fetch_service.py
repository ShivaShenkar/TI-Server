import json
import requests
from flask import jsonify
from services.files_service import *


system_drive = get_main_drive()

def update_data():
    response = requests.get('https://raw.githubusercontent.com/ShivaShenkar/TI-Server/refs/heads/main/db/apps.json')
    if response.status_code == 200:
        data = response.json()

        #update apps.json according to fetched data from github
    override_apps(data)

def fetch_data():
        update_data()
        db_path = os.path.join(os.path.dirname(__file__), "..", "db", "apps.json")
        data=[]
        with open(db_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        installed_apps = get_installed_apps()
          
        for app in data:
            app.pop("github_url", None)
            app["status"] = "uninstalled"
            app["installedVersion"] = None
            for installed_app in installed_apps:
                if app.id==installed_app.id:
                    app.installedVersion = installed_app.installedVersion
                    if(version_tuple(app.version)>version_tuple(installed_app.installedversion)):
                        app.status = "update available"
                    else:
                        app.status = "installed"
        
        
        return data


def version_tuple(s):
    return tuple(int(x) for x in s.split("."))

