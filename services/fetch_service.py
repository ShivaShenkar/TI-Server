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
        all_apps_data=[]
        with open(db_path, "r", encoding="utf-8") as f:
            all_apps_data = json.load(f)
        

        for app in all_apps_data:
            app.versions=[]
            releases_url = f"https://api.github.com/repos/{app.owner}/{app.repo}/releases"
            releases_response = requests.get(releases_url)

            if releases_response.status_code == 200: 
                releases = releases_response.json()
                for release in releases:
                    app.versions.append(release.tag_name)


                latest_release = app.versions[0]
                manifest_url = f"https://raw.githubusercontent.com/{app.owner}/{app.repo}/{latest_release}/manifest.json"
                manifest_response = requests.get(manifest_url)
                if(manifest_response.status_code == 200):
                    manifest_data = manifest_response.json()
                    app.name = manifest_data.name
                    app.description = manifest_data.description
                    app.iconUrl = manifest_data.iconUrl
                    app.exeUrl = manifest_data.exeUrl
                






        installed_apps = get_installed_apps()



            if response.status_code == 200:
                releases = response.json()
                for release in releases:
                    app.versions.append(release.tag_name)

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

