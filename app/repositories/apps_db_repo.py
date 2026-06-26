from pydantic import TypeAdapter

from app.models import DbItem
from typing import Dict, Self
from app.repositories.filesystem_repo import override_json_file, read_json_file


class AppDb:
    _instance = None
    _db: Dict[str, DbItem]

    def __new__(cls) -> Self:
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance._db = {}
            print("AppDb instance created!")
            # cls._instance.read_local_db()

        return cls._instance

    def update_db(self) -> None:

        print("Updating db from remote...")
        new_db = self.fetch_db_from_remote()

        if new_db is not None:
            self._db = new_db
            print("Database updated successfully!")
            self.save_db_locally()
        else:
            print("Failed to update db from remote. Keeping the old db.")

    def fetch_db_from_remote(self) -> Dict[str, DbItem] | None:

        try:
            from app.config import REMOTE_DB_URL
            from app.services import get_http_response

            response = get_http_response(REMOTE_DB_URL)
            apps_data = response.json()
            dict_adapter = TypeAdapter(Dict[str, DbItem])
            new_db = dict_adapter.validate_python(apps_data)

            # if no valid items in dict then db wouldn't be changed
            if len(new_db.keys()) == 0:
                raise ValueError("Invalid data format: Response has 0 valid data types")
            return new_db

        except Exception as e:
            print(f"Failed to update db from github. Error: {e}")
            return

    def save_db_locally(self) -> None:

        print("Saving updated db locally...")
        from app.config import DB_PATH

        override_success = override_json_file(DB_PATH, {id: item.model_dump() for id, item in self.get_db().items()})  # type: ignore
        # override_success = override_db_file(self._db)
        if override_success:
            print("Database was successfully saved locally!")
        else:
            print("Error: Couldn't save db locally")

    def read_local_db(self) -> None:
        print("Parsing local db into AppDb instance..")

        try:
            from app.config import DB_PATH

            data = read_json_file(DB_PATH)
            dict_adapter = TypeAdapter(Dict[str, DbItem])
            self._db = dict_adapter.validate_python(data)
        except Exception as e:
            print(f"Error: Couldn't parse local db. Message: {e}")
        else:
            print("Parsed local db successfully!")

    def get_db(self) -> Dict[str, DbItem]:
        return self._db

    def get_db_item(self, app_id: str) -> DbItem | None:
        if app_id in self._db:
            return self._db[app_id]
        print(f"Couldn't find DbItem with id: {app_id} in AppDb")
        return None
