import os
from typing import Dict, Self
from app.repositories.filesystem_repo import get_manifest_file
import warnings


# Cache installed versions from manifests found on this computer.
class InstalledApps:
    _instance = None
    # key: app_id, value: version
    _installed_versions: Dict[str, str] = {}

    # Scan installations once when the shared repository is first created.
    def __new__(cls) -> Self:
        if not cls._instance:
            cls._instance = super().__new__(cls)
            print("InstalledApps instance created!")
            cls._instance.load_apps_from_computer()

        return cls._instance

    # Read one installed manifest; invalid metadata leaves the cache unchanged.
    def load_app_from_computer_by_id(self, app_id: str) -> None:
        print(
            f"Updating metadata of installed app with id: {app_id} in InstalledApps instance.."
        )

        try:
            manifest_data = get_manifest_file(app_id)
            if not manifest_data:
                raise Exception(
                    f"Error: manifest data is empty for app with id {app_id}"
                )
            if not isinstance(manifest_data, dict):
                raise Exception(
                    f"Error: manifest data format is wrong for app with id {app_id}"
                )
            if "version" not in manifest_data.keys():
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

    # Inspect each entry in the app installation directory.
    def load_apps_from_computer(self) -> None:
        print("Fetching metadata of installed apps in computer...")
        from app.config import APPS_PATH

        for id_folder in os.listdir(APPS_PATH):
            self.load_app_from_computer_by_id(id_folder)

        print("Finished fetching metadata of installed apps.")

    # A missing cache entry means no installed version is known.
    def get_installed_version(self, app_id: str) -> str | None:
        if app_id in self._installed_versions:
            return self._installed_versions[app_id]
        print(f"Couldn't find metadata of installed app with id: {app_id}")
        return None

    # Update the version cache after a successful installation.
    def set_installed_version(self, app_id: str, version: str) -> None:
        self._installed_versions[app_id] = version

    # Forget the cached version after successful removal.
    def delete_app_by_id(self, app_id: str) -> None:
        self._installed_versions.pop(app_id, None)
