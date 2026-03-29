import os
from app.repositories.filesystem_repo import get_ct_apps_folder

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "db", "apps.json")
APPS_PATH = get_ct_apps_folder()
REMOTE_DB_URL = "https://raw.githubusercontent.com/ShivaShenkar/TI-Server/refs/heads/main/db/apps.json"
