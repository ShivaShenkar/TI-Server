import os
import shutil
from app.repositories.filesystem_repo import get_ct_apps_folder
import sys


# Use writable AppData storage when packaged, or the project db folder in development.
def _get_db_path(filename: str) -> str:
    if getattr(sys, "frozen", False):
        base = os.path.join(os.environ["APPDATA"], "TI-Connectivity-Toolbox", "db")
    else:
        base = os.path.join(os.path.dirname(__file__), "..", "..", "db")
    os.makedirs(base, exist_ok=True)

    # On first run in frozen mode, copy the bundled apps.json seed to AppData
    if getattr(sys, "frozen", False) and filename == "apps.json":
        target = os.path.join(base, filename)
        if not os.path.exists(target):
            bundled = os.path.join(sys._MEIPASS, "db", filename)  #type: ignore
            if os.path.exists(bundled):
                shutil.copy2(bundled, target)
                print(f"Copied bundled {filename} to {target}")

    return os.path.join(base, filename)


# Resolve local storage paths during module initialization.
DB_PATH = _get_db_path("apps.json")
TEMP_DATA_PATH = _get_db_path("temp-data.json")
RUNNING_APPS_PATH = _get_db_path("running-apps.json")
APPS_PATH = get_ct_apps_folder()
# Select the remote catalog branch used by refresh requests.
BRANCH_NAME = "ws-update"
REMOTE_DB_URL = f"https://raw.githubusercontent.com/TI-Connectivity-Toolbox-Org/TI-Server/refs/heads/{BRANCH_NAME}/db/apps.json"
REMOTE_APP_GITHUB_URL = ""
GITHUB_INSTALLATION_ID = "141340719"
GITHUB_APP_ID = "4095025"
