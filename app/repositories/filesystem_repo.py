import sys
import os
import json
import shutil
from typing import Dict, Any, cast
from app.models.db_item import DbItem


def get_main_drive() -> str:
    """Return the main/system drive for the current OS."""
    if sys.platform == "win32":
        return os.environ.get("SystemDrive", "C:") + "\\"
    # macOS (darwin) and Linux use root as the main filesystem
    return "/"


def is_path_file(path: str) -> bool:
    return os.path.exists(path) and os.path.isfile(path)


def delete_file(path: str) -> bool:
    if not os.path.exists(path) or not os.path.isfile(path):
        return True
    try:
        os.remove(path)
        return True
    except OSError as e:
        print(f"Error occurred while deleting {path}: {e}")
        return False


def get_ct_folder() -> str:
    drive = get_main_drive()
    path = os.path.join(drive, "Connectivity-Toolbox")
    if is_path_file(path):
        res = delete_file(path)
        if not res:
            raise Exception("Error: can't get CT folder")
    os.makedirs(path, exist_ok=True)
    return path


def get_ct_apps_folder() -> str:
    path = os.path.join(get_ct_folder(), "apps")
    if is_path_file(path):
        res = delete_file(path)
        if not res:
            raise Exception("Error: can't get CT apps folder")
    os.makedirs(path, exist_ok=True)
    return path


def override_db_file(db: Dict[str, DbItem]) -> bool:
    from app.config import DB_PATH

    try:
        with open(DB_PATH, "w", encoding="utf-8") as f:
            json.dump(
                {
                    id: {"owner": db[id].owner, "repo": db[id].repo}
                    for id in list(db.keys())
                },
                f,
                indent=4,
                ensure_ascii=False,
            )
    except OSError:
        return False
    return True


def get_db_file() -> Any:
    from app.config import DB_PATH

    try:
        with open(DB_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error reading {DB_PATH}: {e}")
    return {}


def get_manifest_file(app_id: str) -> Dict[str, Any]:
    from app.config import APPS_PATH

    app_folder_path = os.path.join(APPS_PATH, app_id)
    if not os.path.isdir(app_folder_path):
        raise OSError(f"Error: no directory for {app_id} in {APPS_PATH}")

    # check manifest file
    app_manifest_path = os.path.join(app_folder_path, "manifest.json")
    if not os.path.isfile(app_manifest_path):
        raise OSError(f"Error: manifest file not found for app with id {app_id}")

    with open(app_manifest_path, "r", encoding="utf-8") as f:
        manifest_data: Any = json.load(f)
    manifest_data_dict = cast(Dict[str, Any], manifest_data)

    return manifest_data_dict


def remove_installed_app_directory(app_id: str) -> bool:
    """Delete the install folder for app_id under APPS_PATH. Returns False if missing or unsafe."""
    from app.config import APPS_PATH

    # Reject traversal in app_id; ensure resolved path stays inside APPS_PATH before deleting.
    if not app_id or "/" in app_id or "\\" in app_id or app_id in (".", ".."):
        return False
    target = os.path.abspath(os.path.join(APPS_PATH, app_id))
    apps_root = os.path.abspath(APPS_PATH)
    try:
        if os.path.commonpath([target, apps_root]) != apps_root:
            return False
    except ValueError:
        return False
    if not os.path.isdir(target):
        return False
    try:
        shutil.rmtree(target)
    except OSError as e:
        print(f"Error removing installed app directory {target}: {e}")
        return False
    return True
