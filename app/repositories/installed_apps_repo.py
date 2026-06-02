import os
from typing import Dict, Self


class InstalledApps:
    _instance = None
    # key: app_id, value: version
    _installed_versions: Dict[str, str] = {}

    def __new__(cls) -> Self:
        if not cls._instance:
            cls._instance = super().__new__(cls)
            print("InstalledApps instance created!")
            cls._instance.load_apps_from_computer()

        return cls._instance
    
    def load_apps_from_computer_by_id(self, app_id: str) -> None:
        print(f"Updating metadata of installed app with id: {app_id} in InstalledApps instance..")
        from app.config import APPS_PATH
        from app.repositories.filesystem_repo import get_manifest_file
        import warnings

        try:
            manifest_data = get_manifest_file(app_id)
            if not manifest_data:
                raise Exception(f"Error: manifest data is empty for app with id {app_id}")
            if "version" not in manifest_data:
                raise Exception(
                    f"Error: version field is missing in manifest for app with id {app_id}"
                )
            self._installed_versions[app_id] = manifest_data["version"]
        except Exception as e:
            warnings.warn(
                f"Warning: Failed to fetch metadata of installed app with id: {app_id}. Message: {e}"
            )
            return

        print(
            f"Finished updating metadata of installed app with id: {app_id} in InstalledApps instance."
        )

    def load_apps_from_computer(self) -> None:
        print("Fetching metadata of installed apps in computer...")
        from app.config import APPS_PATH
        for id_folder in os.listdir(APPS_PATH):
            self.load_apps_from_computer_by_id(id_folder)

        print("Finished fetching metadata of installed apps.")


    def get_installed_version(self, app_id: str) -> str | None:
        if app_id in self._installed_versions:
            return self._installed_versions[app_id]
        print(f"Couldn't find metadata of installed app with id: {app_id}")
        return None
    
    def set_installed_version(self, app_id: str, version: str) -> None:
        self._installed_versions[app_id] = version

    def delete_app_by_id(self, app_id: str) -> None:
        self._installed_versions.pop(app_id, None)
