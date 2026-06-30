import os
import subprocess
import sys
import psutil
import time
import threading
from dataclasses import asdict
from typing import Callable, Dict, Literal, Optional

from pydantic import TypeAdapter
from requests import Response

from app.config.config import RUNNING_APPS_PATH, TEMP_DATA_PATH
from app.models import AppModel, ReleaseInfo
from app.models.manifest_model import ManifestModel
from app.models.ws_message import WSMessage
from app.repositories import AppDb
from app.repositories.filesystem_repo import (
    override_json_file,
    read_json_file,
    install_zip_file,
    install_tar_file,
)
from app.repositories.installed_apps_repo import InstalledApps
from app.services.releases_service import AppReleases
import warnings
from app.config import APPS_PATH

# from app.services.github_service import get_manifest
from app.services.http_service import get_http_response


def get_app_manifest(app_id: str, version: str) -> ManifestModel | None:

    db = AppDb()
    app_item = db.get_db_item(app_id)
    if not app_item:
        print(f"Couldn't find app with id {app_id} in Database")
        return None
    url = f"https://raw.githubusercontent.com/{app_item.owner}/{app_item.repo}/{version}/manifest.json"
    try:
        response: Response = get_http_response(url)
        response_data = response.json()
        return ManifestModel.model_validate(response_data)
    except Exception as e:
        print(
            f"Error: failed to get manifest for app with id {app_id} and version {version}. Message: {e}"
        )
    # manifest_data = get_manifest(app_item.owner,app_item.repo)
    # try:
    #    return ManifestModel.convert_data_to_manifest_model(manifest_data)
    # except Exception as e:
    #     print(f"Error: failed to get manifest for app with id {app_id} and version {version}. Message: {e}")
    return None


def get_app_status(
    installed_version: str | None, latest_version: str
) -> Literal["not installed", "update available", "up to date"]:
    if not installed_version:
        return "not installed"
    try:
        installed_tuple = parse_version(installed_version)
        latest_tuple = parse_version(latest_version)
    except ValueError:
        return "not installed"
    if installed_tuple < latest_tuple:
        return "update available"
    return "up to date"


def parse_version(version: str) -> tuple[int, ...]:
    """Parse 'V1.10.1' or 'v1.0.0' into (1, 10, 1) or (1, 0, 0)."""
    import re

    match = re.search(r"(\d[\d.]*)", version)
    if not match:
        raise ValueError(f"Invalid version string: {version}")
    return tuple(int(part) for part in match.group(1).split("."))


class Apps:
    _instance = None
    # key is app id, value is AppModel
    _apps: Dict[str, AppModel]
    _db: AppDb
    _installed_apps: InstalledApps
    # latest apps manifest
    _manifests: Dict[str, ManifestModel]
    _releases: Dict[str, AppReleases]
    _processes_lock: threading.RLock
    _broadcast_callback: Optional[Callable[[Dict[str, str]], None]]

    _running_processes: Dict[str, int]

    def __new__(cls) -> "Apps":
        if not cls._instance:
            cls._instance = super().__new__(cls)

            # app fetching related props
            cls._apps = {}
            cls._db = AppDb()
            cls._releases = {}
            cls._manifests = {}
            cls._installed_apps = InstalledApps()

            # app launching/stopping related props
            cls._running_processes = {}
            cls._processes_lock = threading.RLock()
            cls._broadcast_callback = None
            print("Apps instance created!")
        return cls._instance

    ###################### APP FETCHING ######################

    def fetch_apps_releases(self) -> None:

        db_dict = self._db.get_db()

        # remove apps that are not in db anymore (and their releases)
        for id in db_dict.keys():
            if id not in self._releases.keys():
                self._releases[id] = AppReleases(id)

            self._releases[id].load_releases()
            if not self._releases[id].get_releases():
                warnings.warn(
                    f"Warning: couldn't fetch releases of app with id {id}, App skipped.."
                )
                self.remove_app_from_memory(id)
                continue

    def fetch_apps_manifest(self) -> None:
        device_os = self._get_os()
        db_dict = self._db.get_db()

        for id in db_dict.keys():
            print(f"Loading manifest of app with id: {id}")
            latest_app_manifest = None
            try:
                latest_app_manifest = get_app_manifest(
                    id, self._releases[id].get_latest()[0]
                )
                if not latest_app_manifest:
                    raise ValueError()
                self._manifests[id] = latest_app_manifest
            except:
                warnings.warn(
                    f"Warning: Couldn't fetch manifest from latest version of app with id {id}, App skipped.."
                )
                self.remove_app_from_memory(id)
                continue
            # filter by OS
            if not device_os or device_os not in latest_app_manifest.supportedOS:
                print(f"App with id {id} does not support user's OS")
                self.remove_app_from_memory(id)
                continue
            print("Manifest Loaded Successfully!")

    # def write_data_to_temp() ->None:

    def initial_fetch(self) -> None:
        print("Initial fetch triggered, loading data from remote...")
        self._db.update_db()
        self.fetch_apps_releases()
        self.fetch_apps_manifest()

        for id in self._manifests.keys():
            installedVersion = self._installed_apps.get_installed_version(id)
            latestVersion = self._releases[id].get_latest_version()
            icon_path = self._manifests[id].iconPath
            db_item = self._db.get_db_item(id)
            latest_branch = self._releases[id].get_latest()[1].branch
            icon_url = (
                None
                if not icon_path or not db_item
                else f"https://raw.githubusercontent.com/{db_item.owner}/{db_item.repo}/refs/heads/{latest_branch}/{icon_path}"
            )
            self._apps[id] = AppModel(
                id=id,
                name=self._manifests[id].name,
                description=self._manifests[id].description,
                latestVersion=latestVersion,
                versions=self._releases[id].get_versions_list(),
                installedVersion=installedVersion,
                supportedOS=self._manifests[id].supportedOS,
                status=get_app_status(installedVersion, latestVersion),
                iconUrl=icon_url,
            )

        self.store_apps_in_temp()

    def fetch_from_temp_file(self) -> None:
        print("Reading apps from temp file,")
        self.read_temp_file()
        if not self._apps:
            print(
                "Reading from temp file failed or file is empty. Making initial fetch."
            )
            self.initial_fetch()

    def store_apps_in_temp(self) -> None:
        print("Storing Apps data in a temp file...")
        res = False
        for i in range(5):
            res = override_json_file(
                TEMP_DATA_PATH, {id: app.model_dump() for id, app in self._apps.items()}
            )
            if res:
                break
            else:
                print(f"Storing failed, trying again (Attempt {i+1}/5)")
        if not res:
            print("Storing to temp file failed")
        else:
            print("Stored successfully!")

    def read_temp_file(self) -> None:
        data = read_json_file(TEMP_DATA_PATH)
        apps_adapter = TypeAdapter(Dict[str, AppModel])
        manifests_adapter = TypeAdapter(Dict[str, ManifestModel])
        try:
            self._apps = apps_adapter.validate_python(data)
            self._manifests = manifests_adapter.validate_python(data)
            # db and temp file both fetched at the same time
            # so I can rely on the db file
            self._db.read_local_db()
            for id, db_item in self._db.get_db().items():
                app_versions = data[id]["versions"]
                app_releases_dict: Dict[str, ReleaseInfo] = {
                    version: ReleaseInfo(
                        zipball_url=f"https://api.github.com/repos/{db_item.owner}/{db_item.repo}/zipball/{version}",
                        tarball_url=f"https://api.github.com/repos/{db_item.owner}/{db_item.repo}/tarball/{version}",
                        # branch name is not necessary here (only needed for getting iconUrl)
                        branch="main",
                    )
                    for version in app_versions
                }
                self._releases[id] = AppReleases(id=id, releases=app_releases_dict)

        except Exception as e:
            warnings.warn(f"Error: could not read apps data from temp file: {e}")
            self._apps = {}

    def delete_temp_file(self) -> None:
        print("Deleting Apps data from the temp file...")
        res = False
        for i in range(5):  # type: ignore
            res = override_json_file(TEMP_DATA_PATH, {})
            if res:
                break
        if not res:
            print("Storing to temp file failed")
        else:
            print("Temp data deleted successfully!")

    # def fetch_landing_page(self) -> int:
    #     print("Fetching data for landing page...")

    #     device_os = self._get_os()
    #     if not device_os:
    #         print('Can\'t fetch apps for loading pages, Couldn\'t resolve OS type')
    #         return 510
    #     self._db.update_db()
    #     db_dict = self._db.get_db()

    #     for id in self._releases.keys():
    #         if id not in db_dict.keys():
    #             warnings.warn(
    #                 f"Warning: App with id {id} is in releases cache but not in db, removing app"
    #             )
    #             self._apps.pop(id, None)
    #             self._releases.pop(id, None)
    #     # getting app versions
    #     print('Loading latest releases for all apps..')
    #     for id in db_dict.keys():
    #         if id not in self._releases.keys():
    #             self._releases[id] = AppReleases(id)
    #         self._releases[id].load_latest()
    #         if not self._releases[id].get_latest():
    #             warnings.warn(
    #                 f"Warning: couldn't fetch latest release of app with id {id}, App skipped.."
    #             )
    #             self._apps.pop(id, None)
    #             continue
    #         print(f'Loading manifest of app with id: {id}')
    #         latest_app_manifest = get_app_manifest(id, self._releases[id].get_latest()[0])
    #         if not latest_app_manifest:
    #             warnings.warn(
    #                 f"Warning: Couldn't fetch manifest from latest version of app with id {id}, App skipped.."
    #             )
    #             self._apps.pop(id, None)
    #             continue

    #         if device_os not in latest_app_manifest.supportedOS:
    #             print(f'App with id {id} does not support user\'s OS')
    #             self._apps.pop(id, None)
    #             continue

    #         self._apps[id] = AppModel(
    #             id=id,
    #             name=latest_app_manifest.name,
    #             description=latest_app_manifest.description,
    #             latestVersion=self._releases[id].get_latest()[0],
    #             versions=None,
    #             supportedOS=latest_app_manifest.supportedOS,
    #             status=get_app_status(
    #                 self._installed_apps.get_installed_version(id),
    #                 self._releases[id].get_latest()[0],
    #             ),
    #             installedVersion=self._installed_apps.get_installed_version(id),
    #             iconUrl=latest_app_manifest.iconPath,
    #         )
    #     print("Finished fetching data for landing page")
    #     return 200

    # def fetch_app_details(self, app_id: str) -> int:
    #     self._db.update_db()
    #     if not self._db.get_db_item(app_id):
    #         print(f"Couldn't find app with id {app_id} in Database")
    #         self._apps.pop(app_id, None)
    #         self._releases.pop(app_id, None)
    #         return 404
    #     if app_id not in self._releases.keys():
    #         self._releases[app_id] = AppReleases(app_id)
    #     self._releases[app_id].load_releases()
    #     if not self._releases[app_id]._releases:
    #         print(f"Couldn't fetch releases of app with id {app_id}")
    #         return 404
    #     version_list = list(self._releases[app_id]._releases.keys())
    #     latest_version =version_list[0]
    #     latest_app_manifest = get_app_manifest(
    #         app_id, latest_version
    #     )
    #     if not latest_app_manifest:
    #         print(f"Couldn't fetch manifest from latest version of app with id {app_id}")
    #         return 404

    #     installed_version = self._installed_apps.get_installed_version(app_id)
    #     self._apps[app_id] = AppModel(
    #         id=app_id,
    #         name=latest_app_manifest.name,
    #         description=latest_app_manifest.description,
    #         versions=version_list,
    #         latestVersion=latest_version,
    #         status=get_app_status(
    #             self._installed_apps.get_installed_version(app_id),
    #             latest_version,
    #         ),
    #         installedVersion=installed_version,
    #         iconUrl=latest_app_manifest.iconPath,
    #     )
    #     return 200

    ###################### UTILITY FUNCTIONS ######################

    def get_apps(self) -> Dict[str, AppModel]:
        return self._apps

    def get_app_by_id(self, app_id: str) -> AppModel:
        return self._apps[app_id]

    def check_app_in_db(self, app_id: str) -> bool:
        if self._db.get_db_item(app_id) is not None:
            return True
        if len(self._db.get_db()) == 0:
            self._db.update_db()
        return self._db.get_db_item(app_id) is not None

    def _get_os(self) -> str | None:
        if sys.platform == "win32":
            return "windows"
        if sys.platform == "darwin":
            return "macos"
        if sys.platform == "linux":
            return "linux"
        return None

    ###################### APP UNINSTALL|INSTALL OPERATIONS ######################

    def uninstall_app(self, app_id: str) -> tuple[bool, int]:
        """Remove a downloaded app from disk. Returns (success, reason_code)."""
        from app.repositories.filesystem_repo import remove_installed_app_directory

        print(f"Uninstalling app with id {app_id} ...")

        # Uninstall = delete the app folder under Connectivity-Toolbox/apps, then refresh installed-app cache.
        if (
            app_id not in self._apps.keys()
            or self._apps[app_id].status == "not installed"
        ):
            print(f"Couldn't find installed app with id {app_id}")
            return False, 400

        status, code = remove_installed_app_directory(app_id)

        if status:
            self._installed_apps.delete_app_by_id(app_id)
            print(
                f"App with id {app_id} uninstalled successfully! Updating temp-data file..."
            )
            self._apps[app_id].status = "not installed"
            self._apps[app_id].installedVersion = None
            self.store_apps_in_temp()
        else:
            print(f"Failed to uninstall app with id {app_id}. Reason code: {code}")
        return status, code

    def install_app_version(self, app_id: str, version: str) -> tuple[bool, int]:
        """Install a specific app release tag from GitHub. Returns (success, reason_code)."""

        print(f"Installing app with id {app_id} with version {version}...")
        # self.uninstall_app(app_id)

        # if not self._db.get_db_item(app_id):
        #     print(f"Couldn't find app with id {app_id} in Database")
        #     return False, 400

        # if not self._releases[app_id].get_releases():
        #     print(f"Couldn't find any releases for app with id {app_id}")
        #     return False, 404

        # if version not in self._releases[app_id].get_versions_list():
        #     print(
        #         f"Couldn't find version {version} of app with id {app_id} in releases cache"
        #     )
        #     return False, 404

        if app_id not in self._apps.keys():
            print(f"App with id: {app_id} is not found")
            return False, 400
        if version not in self._apps[app_id].versions:
            print(f"Can not find version: {version} for app with id:{app_id}")
            return False, 400

        if sys.platform == "win32":
            status, code = install_zip_file(
                app_id, self._releases[app_id].get_releases()[version].zipball_url
            )
        else:
            status, code = install_tar_file(
                app_id, self._releases[app_id]._releases[version].tarball_url
            )
        if status:
            self._installed_apps.set_installed_version(app_id, version)
            print(
                f"Version {version} for app with id {app_id} installed successfully! Updating temp-data file..."
            )
            self._apps[app_id].status = get_app_status(
                installed_version=version,
                latest_version=self._apps[app_id].latestVersion,
            )
            self._apps[app_id].installedVersion = version
            self.store_apps_in_temp()
        return status, code

    ###################### APP LAUNCHING\CLOSING OPERATIONS ######################

    def remove_app_from_memory(self, id: str) -> None:
        self._apps.pop(id, None)
        self._releases.pop(id, None)
        self._manifests.pop(id, None)

    @classmethod
    def set_broadcast_callback(cls, callback: Callable[[Dict[str, str]], None]) -> None:
        cls._broadcast_callback = callback

    def monitor_running_apps(self) -> None:
        while True:
            try:
                time.sleep(0.5)
                stopped: list[str] = []
                with self._processes_lock:
                    for app_id, pid in list(self._running_processes.items()):
                        if not psutil.pid_exists(pid):
                            stopped.append(app_id)
                            del self._running_processes[app_id]

                for app_id in stopped:
                    print("Monitoring function found a stopped app, sending to client.")
                    if self._broadcast_callback:
                        msg = asdict(WSMessage(type="app-stopped", appId=app_id))
                        self._broadcast_callback(msg)
            except Exception as e:
                print(f"Error in monitor loop: {e}")

    def _get_app_executable_path(self, app_id: str) -> str | None:
        from app.repositories.filesystem_repo import get_manifest_file

        try:
            installed_manifest = get_manifest_file(app_id)
        except Exception as e:
            warnings.warn(
                f"Warning: failed to read manifest for installed app with id {app_id}. Message: {e}"
            )
            return None

        device_os = self._get_os()
        if not device_os:
            warnings.warn(f"Warning: App with id {app_id} doesn't have supported OS")
            return None
        relative_exe_path = installed_manifest.get("supportedOS", {}).get(device_os)
        if not isinstance(relative_exe_path, str) or len(relative_exe_path) == 0:
            warnings.warn(
                f"Warning: App with id {app_id} is missing executable path for OS {device_os}"
            )
            return None

        full_exe_path = os.path.abspath(
            os.path.join(APPS_PATH, app_id, relative_exe_path)
        )
        expected_app_root = os.path.abspath(os.path.join(APPS_PATH, app_id))
        # path traversal security check
        if not full_exe_path.startswith(expected_app_root):
            warnings.warn(
                f"Warning: App with id {app_id} has a malicious executable path"
            )
            return None
        # file exists check
        if not os.path.isfile(full_exe_path):
            warnings.warn(
                f"Warning: App with id {app_id} has a missing executable file"
            )
            return None
        return full_exe_path

    def stop_app(self, app_id: str) -> tuple[bool, int]:
        print(f"Stopping app with id {app_id} ...")

        with self._processes_lock:
            pid = self._running_processes.get(app_id)
            if not pid:
                print(f"Couldn't find running app with id {app_id}")
                if self._broadcast_callback:
                    msg = asdict(WSMessage(type="app-stopped", appId=app_id))
                    self._broadcast_callback(msg)
                return False, 400

        try:
            process = psutil.Process(pid)
            process.terminate()
            try:
                process.wait(timeout=5)
            except Exception:
                process.kill()
                process.wait()
        except Exception as e:
            print(f"Error: failed to stop app {app_id}. Message: {e}")
            return False, 500

        print(f"App with id {app_id} stopped successfully!")
        return True, 200

    def run_app(self, app_id: str) -> tuple[bool, int]:
        print(f"Running app with id {app_id} ...")

        if not self._installed_apps.get_installed_version(app_id):
            print(f"Couldn't find installed app with id {app_id}")
            return False, 400

        exe_path = self._get_app_executable_path(app_id)
        if not exe_path:
            print(f"Couldn't find exe path for app with id {app_id}")
            return False, 404

        with self._processes_lock:
            if app_id in self._running_processes:
                return False, 409
            process = subprocess.Popen(
                [exe_path],
                cwd=os.path.dirname(exe_path),
                shell=False,
                creationflags=(
                    subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0
                ),
            )
            self._running_processes[app_id] = process.pid

        if self._broadcast_callback:
            msg = asdict(WSMessage("app-running", app_id))
            self._broadcast_callback(msg)

        return True, 200

    def is_app_running(self, app_id: str) -> tuple[bool, int]:
        if not self.check_app_in_db(
            app_id
        ) and not self._installed_apps.get_installed_version(app_id):
            return False, 400
        with self._processes_lock:
            pid = self._running_processes.get(app_id)
        if pid is not None and psutil.pid_exists(pid):
            return True, 200
        return False, 200

    def store_running_apps(self) -> None:
        print("Writing records of currently running apps in json file")
        print("Current dict: ", self._running_processes)
        with self._processes_lock:
            snapshot = dict(self._running_processes)
        res = False
        for i in range(5):
            res = override_json_file(RUNNING_APPS_PATH, snapshot)
            if res:
                break
            else:
                print(f"Storing failed, trying again (Attempt {i+1}/5)")
        if not res:
            print("Storing to running_apps file failed")
        else:
            print("Stored successfully!")

    def read_running_apps_file(self) -> None:
        print("Reading the running-apps.json file...")
        data = read_json_file(RUNNING_APPS_PATH)
        try:
            pids = TypeAdapter(Dict[str, int]).validate_python(data)
            for app_id, pid in pids.items():
                if psutil.pid_exists(pid):
                    print(
                        f"  App {app_id} (PID {pid}) is still running from previous session"
                    )
                    with self._processes_lock:
                        self._running_processes[app_id] = pid
            print(f"Read {len(pids)} app(s) from file (tracked from fresh start)")
        except Exception as e:
            warnings.warn(f"Error: could not read running apps from file: {e}")
