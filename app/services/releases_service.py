from typing import Dict, Any, cast, List,Tuple
from app.models import ReleaseURLs


def check_valid_release_fromat(item:dict) -> bool:
    if (
        "tag_name" not in item
        or "tarball_url" not in item
        or "zipball_url" not in item
    ):
        raise ValueError("Invalid release data format: missing required fields")
    if (
        not isinstance(item["tag_name"], str)
        or not isinstance(item["tarball_url"], str)
        or not isinstance(item["zipball_url"], str)
    ):
        raise ValueError(
            "Invalid release data format: expected fields to be string"
        )

def convert_to_releases_model(data: Any) -> Dict[str, ReleaseURLs]|Tuple[str,ReleaseURLs]:
    import warnings


    #if data is a list of all releses
    if isinstance(data, list):
        res: Dict[str, ReleaseURLs] = {}
        for item in data:
            try:
                if not isinstance(item, dict):
                    raise ValueError("Invalid release data format: expected a dictionary")
                
                check_valid_release_fromat(item)
                
            except Exception as e:
                warnings.warn(
                    f"Warning: couldn't fetch a release in item: {item}, skipping. Message: {e}"
                )
            else:
                res[item["tag_name"]] = ReleaseURLs(
                    # version=item["tag_name"],
                    zipball_url=item["zipball_url"],
                    tarball_url=item["tarball_url"],
                )
        return res
    #if data is a dictionary of latest release
    if isinstance(data, dict):
        check_valid_release_fromat(data)
        return (data["tag_name"],ReleaseURLs(
                    zipball_url=data["zipball_url"],
                    tarball_url=data["tarball_url"],
                ))
            
    

    raise ValueError("Invalid release data format: expected a list of releases or a single release dictionary")
    


class AppReleases:
    _id: str
    _releases: Dict[str, ReleaseURLs]
    _latest: Tuple[str,ReleaseURLs] | None

    def __init__(self, id: str) -> None:
        self._id = id
        self._releases = {}
        self._latest = None

    
    def load_latest(self)->None:

        from app.services.http_service import get_http_response
        from app.repositories import AppDb

        self._latest = None
        db = AppDb()
        app_item = db.get_db_item(self._id)
        if not app_item:
            print(f"Couldn't find app with id {self._id} in Database")
            return
        
        releases_url = (
            f"https://api.github.com/repos/{app_item.owner}/{app_item.repo}/releases/latest"
        )
        try:
            response = get_http_response(releases_url)
            response_data = response.json()
            latest_release = convert_to_releases_model(response_data)
            self._latest = latest_release
            
        except Exception as e:
            print(
                f"Error: Failed to load latest release of app with id {self._id}. Message: {e} "
            )
        else:
            print(f"Loaded latest release of app with id {self._id} Successfully!")


    def load_releases(self) -> None:
        print(f"Loading releases of app with id {self._id}")
        from app.services.http_service import get_http_response
        from app.repositories import AppDb

        self._releases = {}

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

  
    def get_versions_list(self) -> list[str]:
        return list(self._releases.keys())

    def get_latest_version(self) -> str:
        return self.get_versions_list()[0]

    def get_latest_release(self) -> ReleaseURLs:
        latest_version = self.get_latest_version()
        return self._releases[latest_version]

    def get_release_by_tag(self, tag: str) -> ReleaseURLs | None:
        if tag in self._releases.keys():
            return self._releases[tag]
        return None


    def get_zip_url(self, tag_name: str) -> str:
        release = self.get_release_by_tag(tag_name)
        return release.zipball_url if release else ""
    
    def get_tar_url(self, tag_name: str) -> str:
        release = self.get_release_by_tag(tag_name)
        return release.tarball_url if release else ""