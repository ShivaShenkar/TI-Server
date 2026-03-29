from app.models import DbItem
from typing import Dict, Any, Self, cast


class AppDb:
    _instance = None
    _db: Dict[str, DbItem]

    def __new__(cls) -> Self:
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance._db = {}
            print("AppDb instance created!")
            cls._instance.read_local_db()
            cls._instance.update_db()

        return cls._instance

    def update_db(self) -> None:
        from app.services.http_service import get_http_response
        from app.config import REMOTE_DB_URL

        print("Updating db from remote...")
        new_db: Dict[str, DbItem] = {}
        try:

            response = get_http_response(REMOTE_DB_URL)
            apps_data = response.json()
            new_db = self.convert_dict_to_db(apps_data)

            # if no valid items in dict then db wouldn't be changed
            if len(new_db.keys()) == 0:
                raise ValueError("Invalid data format: Response has 0 valid data types")
        except Exception as e:
            print(f"Failed to update db from github. Error: {e}")
            return

        else:
            self._db = new_db
            print("Database updated successfully!")
            self.save_db_locally()

    def get_db(self) -> Dict[str, DbItem]:
        return self._db

    def get_db_item(self, app_id: str) -> DbItem | None:
        if app_id in self._db:
            return self._db[app_id]
        print(f"Couldn't find DbItem with id: {app_id} in AppDb")
        return None

    def save_db_locally(self) -> None:
        from app.repositories.filesystem_repo import override_db_file

        print("Saving updated db locally...")
        override_success = override_db_file(self._db)
        if override_success:
            print("Database was successfully saved locally")
        else:
            print("Error: Couldn't save db locally")

    def read_local_db(self) -> None:
        print("Parsing local db into AppDb instance..")
        from app.repositories.filesystem_repo import get_db_file

        try:
            self._db = AppDb.convert_dict_to_db(get_db_file())
        except Exception as e:
            print(f"Error: Couldn't parse local db. Message: {e}")
        else:
            print("Parsed local db successfully!")

    # converting valid values in dict to DbItems
    # invalid items won't be returned
    @staticmethod
    def convert_dict_to_db(instance: Any) -> Dict[str, DbItem]:
        import warnings

        # checking if response is a valid dictionary
        if not isinstance(instance, dict):
            raise ValueError("Invalid data format: expected a dictionary of db items")

        res: Dict[str, DbItem] = {}
        instance_dict = cast(Dict[Any, Any], instance)
        for key, value in instance_dict.items():
            try:
                if not isinstance(key, str):
                    raise ValueError(
                        "Invalid data format: expected app id to be a string"
                    )

                new_item = DbItem.convert_to_DbItem(value)
                res[key] = new_item

            except Exception as e:
                warnings.warn(
                    f"Warning: failed to fetch data from app with id {id}, error:{e}"
                )

        # if no valid items in dict then db wouldn't be changed
        return res
