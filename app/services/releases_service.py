from typing import Dict, Tuple

from app.models import ReleaseInfo

# from app.services.github_service import get_latest_release, get_app_releases
from app.services.http_service import get_http_response
from app.repositories import AppDb


def check_valid_release_format(item: dict) -> bool:  # type:ignore
    if "tag_name" not in item or "tarball_url" not in item or "zipball_url" not in item:
        raise ValueError("Invalid release data format: missing required fields")
    if (
        not isinstance(item["tag_name"], str)
        or not isinstance(item["tarball_url"], str)
        or not isinstance(item["zipball_url"], str)
    ):
        raise ValueError("Invalid release data format: expected fields to be string")



#instance storing releases of a single app
class AppReleases:
    _id: str
    # key is version, value is the version's urls and branch
    _releases: Dict[str, ReleaseInfo]

    # Accept restored release data or start with an empty mapping.
    def __init__(self, id: str, releases: Dict[str, ReleaseInfo] = {}) -> None:
        self._id = id
        self._releases = releases

    # Rebuild the release mapping in GitHub response order.
    def load_releases(self) -> None:
        print(f"Loading releases of app with id {self._id}")
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
            for release in response_data:
                #    print(release)
                self._releases[release["tag_name"]] = ReleaseInfo(
                    zipball_url=release["zipball_url"],
                    tarball_url=release["tarball_url"],
                    branch=release["target_commitish"],
                )

        except Exception as e:
            print(
                f"Error: Failed to load releases of app with id {self._id}. Message: {e} "
            )
        else:
            print(f"Loaded releases of app with id {self._id} Successfully!")


    # Preserve release order for the client version selector.
    def get_versions_list(self) -> list[str]:
        return list(self._releases.keys())

    # Treat the first stored release as latest; the mapping must not be empty.
    def get_latest_version(self) -> str:
        return self.get_versions_list()[0]

    # Return the first release tag together with its download metadata.
    def get_latest(self) -> Tuple[str, ReleaseInfo]:
        return next(iter(self._releases.items()))

    # Expose release metadata used to select installation archives.
    def get_releases(self) -> Dict[str, ReleaseInfo]:
        return self._releases

    def get_release_by_tag(self, tag: str) -> ReleaseInfo | None:
        if tag in self._releases.keys():
            return self._releases[tag]
        return None

    def get_zip_url(self, tag_name: str) -> str:
        release = self.get_release_by_tag(tag_name)
        return release.zipball_url if release else ""

    def get_tar_url(self, tag_name: str) -> str:
        release = self.get_release_by_tag(tag_name)
        return release.tarball_url if release else ""
