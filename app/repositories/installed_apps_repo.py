
from app.config import APPS_PATH
from app.models import ManifestModel
import os
from typing import Dict


class InstalledApps:
    _instance = None
    _installed_apps: Dict[str,ManifestModel] = {}

    def __new__(cls):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            print("InstalledApps instance created!")
            cls._instance.update()

        return cls._instance
    
    def update(self):
        print("Fetching metadata of installed apps in computer...")
        from app.repositories.filesystem_repo import get_manifest_file

        for id_folder in os.listdir(APPS_PATH):
            try:
                manifest_data = get_manifest_file(id_folder)
                manifest_model = ManifestModel.convert_data_to_manifest_model(manifest_data)
                self._installed_apps[id_folder] = manifest_model
            except Exception as e:
                print(f"Error fetching metadata of installed app with id: {id_folder}. Error: {e}")
                continue         
    

    def get_installed_apps(self):
        return self._installed_apps
    

    def get_installed_app(self,app_id:str) ->ManifestModel|None:
        if app_id in self._installed_apps:
            return self._installed_apps[app_id]
        print(f"Couldn't find metadata of installed app with id: {app_id}")
        return None




