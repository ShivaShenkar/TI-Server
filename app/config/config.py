import os
from app.repositories.filesystem_repo import get_ct_apps_folder

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "db", "apps.json")
TEMP_DATA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "db", "temp-data.json"
)
APPS_PATH = get_ct_apps_folder()
BRANCH_NAME = "ws-update"
REMOTE_DB_URL = f"https://raw.githubusercontent.com/TI-Connectivity-Toolbox-Org/TI-Server/refs/heads/{BRANCH_NAME}/db/apps.json"
REMOTE_APP_GITHUB_URL = ""
GITHUB_INSTALLATION_ID = "141340719"
GITHUB_APP_ID = "4095025"
