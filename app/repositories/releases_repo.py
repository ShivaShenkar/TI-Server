from typing import Dict, Any


def convert_to_releases_model(data: Any) -> Dict[str, Dict[str, str]]:
    import warnings

    res: Dict[str, Dict[str, str]] = {}
    if not isinstance(data, list):
        raise ValueError(
            f"Invalid response format: expected a list of releases. Data: {data}"
        )

    for item in data:
        try:
            if not isinstance(item, dict):
                raise ValueError("Invalid release data format: expected a dictionary")
            if (
                "tag_name" not in item
                or "tarball_url" not in item
                or "zipball_url" not in item
            ):
                raise ValueError(
                    "Invalid release data format: missing required fields"
                )
            if (
                not isinstance(item["tag_name"], str)
                or not isinstance(item["tarball_url"], str)
                or not isinstance(item["zipball_url"], str)
            ):
                raise ValueError(
                    "Invalid release data format: expected fields to be string"
                )
        except Exception as e:
            warnings.warn(
                f"Warning: couldn't fetch a release in item: {item}, skipping. Message: {e}"
            )
        else:
            res[item["tag_name"]] = {
                "zipball_url": item["zipball_url"],
                "tarball_url": item["tarball_url"],
            }

    return res


class AppReleases:
    # new instance is created for each app_id
    # it's like singleton but for each id
    _instances: Dict[str, "AppReleases"] = {}
    _id: str

    # key: app version\tag_name
    # value: a dictionary with keys of "zipball_url" and "tarball_url"
    # with matching values
    _releases: Dict[str, Dict[str, str]]

    def __new__(cls, app_id: str) ->"AppReleases":
        if app_id not in cls._instances:
            cls._instances[app_id] = super().__new__(cls)
            cls._instances[app_id]._id = app_id
            cls._instances[app_id]._releases = {}
            print(f"Created new AppReleases instance for app with id: {app_id}!")
            cls._instances[app_id].load_releases()
        return cls._instances[app_id]

    def load_releases(self):
        print(f"Loading releases of app with id {self._id}")
        from app.services.http_service import get_http_response
        from app.repositories import AppDb

        db = AppDb()
        app_item = db.get_db_item(self._id)

        if not app_item:
            print(f"Couldn't find app with id {self._id} in Database")
            return

        releases_url = (
            f"https://api.github.com/repos/{app_item.owner}/{app_item.repo}/releases"
        )
        try:
            response = get_http_response(releases_url)
            response_data = response.json()
            self._releases = convert_to_releases_model(response_data)
        except Exception as e:
            print(
                f"Error: Failed to load releases of app with id {self._id}. Message: {e} "
            )
        else:
            print(f"Loaded releases of app with id {self._id} Successfully!")

    def get_versions_list(self):
        return list(self._releases.keys())

    def get_latest_version(self) -> str:
        return self.get_versions_list()[0]

    def get_latest_release(self) -> Dict[str, Dict[str, str]]:
        latest_version = self.get_latest_version()
        return {latest_version: self._releases[latest_version]}
