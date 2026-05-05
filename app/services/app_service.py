from typing import Dict, Literal
from app.models import AppModel
from app.models.manifest_model import ManifestModel
from app.repositories.installed_apps_repo import InstalledApps
from app.repositories import AppDb
from app.services.releases_service import AppReleases


def get_app_manifest(app_id: str, version: str) -> ManifestModel | None:
    from app.repositories import AppDb
    from app.services.http_service import get_http_response

    db = AppDb()
    app_item = db.get_db_item(app_id)
    if not app_item:
        print(f"Couldn't find app with id {app_id} in Database")
        return None
    url = f"https://raw.githubusercontent.com/{app_item.owner}/{app_item.repo}/{version}/manifest.json"
    try:
        response = get_http_response(url)
        response_data = response.json()
        return ManifestModel.convert_data_to_manifest_model(response_data)
    except Exception as e:
        print(
            f"Error: failed to get manifest for app with id {app_id} and version {version}. Message: {e}"
        )
    return None


def get_app_status(
    installed_app: ManifestModel | None, latest_app: ManifestModel
) -> Literal["not installed", "update available", "up to date"]:
    if not installed_app:
        return "not installed"
    if installed_app.version != latest_app.version:
        return "update available"
    return "up to date"


class Apps:

    _instance = None
    _apps: Dict[str, AppModel]
    _db: AppDb
    _installed_apps: InstalledApps
    _releases: Dict[str, AppReleases]

    def __new__(cls) -> "Apps":
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._apps = {}
            cls._db = AppDb()
            cls._releases = {}
            cls._installed_apps = InstalledApps()
            print("Apps instance created!")
        cls._instance.load_apps()
        return cls._instance

    def load_apps(self) -> None:
        print("Loading details of all apps ...")
        import sys
        import warnings

        db_dict = self._db.get_db()
        for id in db_dict.keys():
            # getting app versions
            self._releases[id] = AppReleases(id)
            latest_version = self._releases[id].get_latest_version()

            # getting app name,description,supportedOS,iconPath
            app_manifest = get_app_manifest(id, latest_version)

            # if couldn't fetch manifest, app wouldn't be sent to client
            if not app_manifest:
                warnings.warn(
                    f"Warning: Couldn't fetch manifest from latest version of app with id {id}, App skipped"
                )
                continue

            # filtering out apps that don't support the user's OS
            # if sys.platform not in app_manifest.supportedOS.keys():
            #     warnings.warn(
            #         f"Warning: App with id {id} is not supported for OS: {sys.platform}, App skipped"
            #     )
            #     continue

            # getting app status and installedVersion
            installed_app = self._installed_apps.get_installed_app(id)
            status = get_app_status(
                installed_app=installed_app, latest_app=app_manifest
            )
            installed_version = None
            if installed_app:
                installed_version = installed_app.version

            self._apps[id] = AppModel(
                id=id,
                name=app_manifest.name,
                description=app_manifest.description,
                versions=self._releases[id].get_versions_list(),
                status=status,
                supportedOS=app_manifest.get_supported_os(),
                installedVersion=installed_version,
                iconPath=app_manifest.iconPath,
            )
        print("Finished loading details for all apps")

    def update(self) -> None:
        print("Updating details of all apps...")
        self._db.update_db()
        self._installed_apps.update()
        db_dict = self._db.get_db()
        for id in db_dict.keys():
            # checking if new apps added to db
            if id not in self._releases.keys():
                self._releases[id] = AppReleases(id)
            else:
                self._releases[id].load_releases()

        self.load_apps()
        print("Update of all apps details complete")

    def get_apps(self) -> Dict[str, AppModel]:
        return self._apps

    def get_app_by_id(self, app_id: str) -> AppModel:
        return self._apps[app_id]


    def uninstall_app(self, app_id: str) -> tuple[bool, int]:
        """Remove a downloaded app from disk. Returns (success, reason_code)."""
        from app.config import APPS_PATH
        from app.repositories.filesystem_repo import remove_installed_app_directory

        # Uninstall = delete the app folder under Connectivity-Toolbox/apps, then refresh installed-app cache.
        if not self._db.get_db_item(app_id):
            return False, 400

        status, code = remove_installed_app_directory(app_id)

        if status:
            self.update()
        return status,code
        


    def install_app_version(self, app_id: str, version: str) -> tuple[bool, int]:
        import sys
        """Install a specific app release tag from GitHub. Returns (success, reason_code)."""
        print(f"Installing app with id {app_id} with version {version}...")

        self.uninstall_app(app_id)
        from app.config import APPS_PATH
        from app.repositories.filesystem_repo import install_zip_file, install_tar_file
        
        if not self._db.get_db_item(app_id):
            return False, 400

        releases:AppReleases = self._releases[app_id]
        release:ReleaseModel|None = releases.get_release_by_tag(version)

        if not release:
            return False, 404
        if sys.platform == "win32":
            status, code = install_zip_file(app_id,release.zipball_url)
        
        else:
            status, code = install_tar_file(app_id,release.tarball_url)
        if status:
            self.update()
        return status, code

    # def update_app(app_id: str, version: str) -> tuple[bool, str]:
    #     """Replace current installed app with requested version. Returns (success, reason_code)."""
    #     ok, code = uninstall_app(app_id)
    #     if not ok:
    #         return False, code

    #     ok, code = install_app_version(app_id, version)
    #     if not ok:
    #         return False, code
    #     return True, "ok"
