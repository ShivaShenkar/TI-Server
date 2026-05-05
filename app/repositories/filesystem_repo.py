import sys
import os
import json
import shutil
import zipfile
import tempfile
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


def remove_installed_app_directory(app_id: str) -> tuple[bool, int]:
    """Delete the install folder for app_id under APPS_PATH. Returns False if missing or unsafe."""
    print(f"Removing installed app directory {app_id}...")
    from app.config import APPS_PATH
    

    if app_id=="." or app_id=="..":
        return False, 400

    target = os.path.join(APPS_PATH, app_id)
    if not os.path.isdir(target):
        print(f"App {app_id} is not installed")
        return True, 200
    try:
        shutil.rmtree(target)        
    except OSError as e:
        print(f"Error removing installed app directory {target}: {e}")
        return False, 500
    print(f"App {app_id} removed successfully!")
    return True, 200

def install_tar_file(app_id:str,tar_url:str)->tuple[bool,int]:
    print(f"Installing tar file for app {app_id} from {tar_url} ...")
    from app.config import APPS_PATH
    import requests
    import tarfile

    target_path = os.abspath(os.path.join(APPS_PATH, app_id))
    os.makedirs(target_path, exist_ok=True)
    try:
        with requests.get(tar_url,stream=True) as r:
            r.raise_for_status()
            with tarfile.open(fileobj=r.raw, mode="r|*") as tar:
                for member in tar:
                    if member.name.count("/") > 0:
                        member.name = member.name.split("/", 1)[1]  # strip top folder
                        #checks for path traversal security issue.
                        member_path = os.path.abspath(os.path.join(target_path, member.name))
                        if not member_path.startswith(target_path):
                            raise OSError(f"Error: {member.name} contains unsafe path")
                        tar.extract(member, path=target_path)

    except Exception as e:
        print(f"Error extracting tar file from {tar_url}: {e}")
        return False,500
    print(f"tar file installed successfully!")
    return True,200


def install_zip_file(app_id:str,zip_url:str)->tuple[bool,int]:
    print(f"Installing zip file for app {app_id} from {zip_url} ...")
    from app.config import APPS_PATH
    import requests
    import zipfile

    target_path = os.path.abspath(os.path.join(APPS_PATH, app_id))
    zip_path = os.path.join(target_path, "app.zip")
    os.makedirs(target_path, exist_ok=True)
    try:
        with requests.get(zip_url, stream=True) as r:
            r.raise_for_status()
            with open(zip_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            for member in zip_ref.infolist():
                name_parts = member.filename.split("/", 1)
                if len(name_parts) > 1:
                    member.filename = name_parts[1]  # strip top folder

                    #checks for path traversal security issue.
                    member_path = os.path.abspath(os.path.join(target_path, member.filename))
                    if not member_path.startswith(target_path):
                        raise OSError(f"Error: {member.filename} contains unsafe path")

                    zip_ref.extract(member, target_path)
        os.remove(zip_path)
    except Exception as e:
        print(f"Error extracting zip file from {zip_url}: {e}")
        return False,500
    print(f"Zip file installed successfully!")
    return True,200 


