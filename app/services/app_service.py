import json
import os
import subprocess
import sys
import time
import threading
from dataclasses import asdict
from typing import Callable, Dict, List, Literal, Optional

from app.models import AppModel
from app.models.manifest_model import ManifestModel
from app.models.release_model import ReleaseURLs
from app.models.ws_message import WSMessage
from app.repositories import AppDb
from app.repositories.installed_apps_repo import InstalledApps
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
    installed_version: str | None, latest_version: str
) -> Literal["not installed", "update available", "up to date"]:
    if not installed_version:
        return "not installed"
    if installed_version != latest_version:
        return "update available"
    return "up to date"


class Apps:
    _instance = None
    # key is app id, value is AppModel
    _apps: Dict[str, AppModel]
    _db: AppDb
    _installed_apps: InstalledApps
    _releases: Dict[str, AppReleases]
    _processes_lock: threading.RLock
    _broadcast_callback: Optional[Callable[[str], None]]

    _running_processes: Dict[str, subprocess.Popen[str]]

    

    def __new__(cls) -> "Apps":
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._apps = {}
            cls._db = AppDb()
            cls._releases = {}
            cls._installed_apps = InstalledApps()
            cls._running_processes = {}
            cls._processes_lock = threading.RLock()
            cls._broadcast_callback = None
            print("Apps instance created!")
        return cls._instance
    
    ###################### APP FETCHING ###################### 

    def fetch_landing_page(self) -> int:
        print("Fetching data for landing page...")
        import warnings

        device_os = self._get_os()
        if not device_os:
            print('Can\'t fetch apps for loading pages, Couldn\'t resolve OS type')
            return 510
        self._db.update_db()
        db_dict = self._db.get_db()


        for id in self._releases.keys():
            if id not in db_dict.keys():
                warnings.warn(
                    f"Warning: App with id {id} is in releases cache but not in db, removing app"
                )
                self._apps.pop(id, None)
                self._releases.pop(id, None)
        # getting app versions
        print('Loading latest releases for all apps..')
        for id in db_dict.keys():
            
            if id not in self._releases.keys():
                self._releases[id] = AppReleases(id)
            self._releases[id].load_latest()
            if not self._releases[id]._latest:
                warnings.warn(
                    f"Warning: couldn't fetch latest release of app with id {id}, App skipped.."
                )
                self._apps.pop(id, None)
                continue
            print(f'Loading manifest of app with id: {id}')
            latest_app_manifest = get_app_manifest(id, self._releases[id]._latest[0])
            if not latest_app_manifest:
                warnings.warn(
                    f"Warning: Couldn't fetch manifest from latest version of app with id {id}, App skipped.."
                )
                self._apps.pop(id, None)
                continue
            
            if device_os not in latest_app_manifest.supportedOS:
                print(f'App with id {id} does not support user\'s OS')
                self._apps.pop(id, None)
                continue

            self._apps[id] = AppModel(
                id=id,
                name=latest_app_manifest.name,
                description=latest_app_manifest.description,
                latestVersion=self._releases[id]._latest[0],
                versions=None,
                status=get_app_status(
                    self._installed_apps.get_installed_version(id),
                    self._releases[id]._latest[0],
                ),
                installedVersion=self._installed_apps.get_installed_version(id),
                iconUrl=latest_app_manifest.iconPath,
            )
        print("Finished fetching data for landing page")
        return 200

    def fetch_app_details(self, app_id: str) -> int:
        self._db.update_db()
        if not self._db.get_db_item(app_id):
            print(f"Couldn't find app with id {app_id} in Database")
            self._apps.pop(app_id, None)
            self._releases.pop(app_id, None)
            return 404
        if app_id not in self._releases.keys():
            self._releases[app_id] = AppReleases(app_id)
        self._releases[app_id].load_releases()
        if not self._releases[app_id]._releases:
            print(f"Couldn't fetch releases of app with id {app_id}")
            return 404
        version_list = list(self._releases[app_id]._releases.keys())
        latest_version =version_list[0]
        latest_app_manifest = get_app_manifest(
            app_id, latest_version
        )
        if not latest_app_manifest:
            print(f"Couldn't fetch manifest from latest version of app with id {app_id}")
            return 404

        installed_version = self._installed_apps.get_installed_version(app_id)
        self._apps[app_id] = AppModel(
            id=app_id,
            name=latest_app_manifest.name,
            description=latest_app_manifest.description,
            versions=version_list,
            latestVersion=latest_version,
            status=get_app_status(
                self._installed_apps.get_installed_version(app_id),
                latest_version,
            ),
            installedVersion=installed_version,
            iconUrl=latest_app_manifest.iconPath,
        )
        return 200
    
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
        if not self._installed_apps.get_installed_version(app_id):
            print(f"Couldn't find installed app with id {app_id}")
            return False, 400

        status, code = remove_installed_app_directory(app_id)

        if status:
            self._installed_apps.delete_app_by_id(app_id)
            print(f"App with id {app_id} uninstalled successfully!")
        else:
            print(f"Failed to uninstall app with id {app_id}. Reason code: {code}")
        return status, code

    def install_app_version(self, app_id: str, version: str) -> tuple[bool, int]:
        from app.repositories.filesystem_repo import install_zip_file, install_tar_file

        """Install a specific app release tag from GitHub. Returns (success, reason_code)."""
        
        print(f"Installing app with id {app_id} with version {version}...")
        self.fetch_app_details(app_id)
        # self.uninstall_app(app_id)

        if not self._db.get_db_item(app_id):
            print(f"Couldn't find app with id {app_id} in Database")
            return False, 400

        if not self._releases[app_id]._releases:
            print(f"Couldn't find any releases for app with id {app_id}")
            return False, 404

        if version not in self._releases[app_id]._releases.keys():
            print(
                f"Couldn't find version {version} of app with id {app_id} in releases cache"
            )
            return False, 404

        if sys.platform == "win32":
            status, code = install_zip_file(
                app_id, self._releases[app_id]._releases[version].zipball_url
            )
        else:
            status, code = install_tar_file(
                app_id, self._releases[app_id]._releases[version].tarball_url
            )
        if status:
            self._installed_apps.set_installed_version(app_id, version)
        return status, code

    ###################### APP LAUNCHING\CLOSING OPERATIONS ###################### 

    @classmethod
    def set_broadcast_callback(cls, callback: Callable[[str], None]) -> None:
        cls._broadcast_callback = callback

    def start_monitor(self) -> None:
        thread = threading.Thread(target=self._monitor_running_processes, daemon=True)
        thread.start()

    def _monitor_running_processes(self) -> None:
        while True:
            time.sleep(0.5)
            stopped: list[str] = []
            with self._processes_lock:
                for app_id, process in list(self._running_processes.items()):
                    if process.poll() is not None:
                        stopped.append(app_id)
                for app_id in stopped:
                    self._running_processes.pop(app_id, None)
            for app_id in stopped:
                if self._broadcast_callback:
                    msg = json.dumps(asdict(WSMessage('app-stopped', app_id)))
                    self._broadcast_callback(msg)

    def _get_app_executable_path(self, app_id: str) -> str | None:
        from app.config import APPS_PATH
        from app.repositories.filesystem_repo import get_manifest_file
        import warnings

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

        print(relative_exe_path)
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
            process = self._running_processes.get(app_id)
            if not process:
                print(f"Couldn't find running app with id {app_id}")
                return False, 400

            success = True
            try:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
            except OSError as e:
                print(f"Error: failed to stop app {app_id}. Message: {e}")
                success = False

            self._running_processes.pop(app_id, None)

        if self._broadcast_callback:
            msg = json.dumps(asdict(WSMessage('app-stopped', app_id)))
            self._broadcast_callback(msg)

        if success:
            print(f"App with id {app_id} stopped successfully!")
            return True, 200

        print(f"App with id {app_id} was removed from tracking after stop failure.")
        return False, 500

    def run_app(self, app_id: str) -> tuple[bool, int]:
        print(f"Running app with id {app_id} ...")

        if not self._installed_apps.get_installed_version(app_id):
            print(f"Couldn't find installed app with id {app_id}")
            return False, 400

        with self._processes_lock:
            if app_id in self._running_processes:
                return False, 409

        exe_path = self._get_app_executable_path(app_id)
        if not exe_path:
            return False, 404

        try:
            process = subprocess.Popen(
                [exe_path],
                cwd=os.path.dirname(exe_path),
                shell=False,
            )
        except OSError as e:
            print(f"Error: failed to run app {app_id}. Message: {e}")
            return False, 500

        with self._processes_lock:
            self._running_processes[app_id] = process

        if self._broadcast_callback:
            msg = json.dumps(asdict(WSMessage('app-running', app_id)))
            self._broadcast_callback(msg)

        return True, 200

    def is_app_running(self, app_id: str) -> tuple[bool, int]:
        if not self.check_app_in_db(app_id) and not self._installed_apps.get_installed_version(
            app_id
        ):
            return False, 400
        with self._processes_lock:
            return app_id in self._running_processes, 200
    
    
    
    
