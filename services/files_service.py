import os
import sys
import json
import pathlib


def override_apps(data):
    db_path = os.path.join(os.path.dirname(__file__), "..", "db", "apps.json")
    with open(db_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)



def get_main_drive() ->str:
    """Return the main/system drive for the current OS."""
    if sys.platform == "win32":
        return os.environ.get("SystemDrive", "C:") + "\\"
    # macOS (darwin) and Linux use root as the main filesystem
    return "/"

def create_ct_folder(drive):
    path = os.path.join(drive, "Connectivity-Toolbox", "apps")
    os.makedirs(path, exist_ok=True)


def get_installed_apps() -> list: 
    #Reaching the Directory of work (usually C:\\Connectivity-Toolbox\\apps)
    drive = get_main_drive()
    create_ct_folder(drive)
    apps_path = os.path.join(drive, "Connectivity-Toolbox", "apps")

    resArr=[]

    #Looking at the installed apps inside the client's computer
    for idFolder in os.listdir(apps_path):
        if os.path.isdir(folder_path):
            manifest_path = os.path.join(apps_path, idFolder, "manifest.json")
            if os.path.isfile(manifest_path):
                with open(manifest_path, "r", encoding="utf-8") as f:
                    manifest_data = json.load(f)
                    resArr.append({"id":idFolder,"installedVersion":manifest_data.version})

        


    return resArr



