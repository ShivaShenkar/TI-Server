import json

from github import Github, GithubException
from typing import Tuple, Dict
import time
from app.models import ReleaseURLs
from typing import Any


g = Github()


def print_rate_limit():
    global g
    rate_limit = g.rate_limiting
    print(f"Current Rate Limit: {rate_limit[0]}/{rate_limit[1]}")
    if rate_limit[0] == 0:
        reset_time = time.strftime(
            "%H:%M:%S", time.localtime(g.rate_limiting_resettime)
        )
        print(f"Rate limit exhausted. Resets at {reset_time}")
        return


def get_latest_release(owner: str, repo: str) -> Tuple[str, ReleaseURLs] | None:
    try:
        global g
        print_rate_limit()
        g_repo = g.get_repo(f"{owner}/{repo}")
        latest = g_repo.get_latest_release()
        return (latest.tag_name, ReleaseURLs(zipball_url=latest.zipball_url, tarball_url=latest.tarball_url))  # type: ignore
    except GithubException as e:
        print(f"Error: {e}")
    return


def get_app_releases(owner: str, repo: str) -> Dict[str, ReleaseURLs] | None:
    try:
        global g
        print_rate_limit()
        g_repo = g.get_repo(f"{owner}/{repo}")
        releases = g_repo.get_releases()
        return {r.tag_name: ReleaseURLs(zipball_url=r.zipball_url, tarball_url=r.tarball_url) for r in releases}  # type: ignore
    except GithubException as e:
        print(f"Error: {e}")
    return


def get_manifest(owner: str, repo: str) -> Any | None:
    try:
        global g
        print_rate_limit()
        g_repo = g.get_repo(f"{owner}/{repo}")
        latest_release = get_latest_release(owner, repo)
        if not latest_release:
            raise Exception(f"Can't fetch latest_release of app {owner}/{repo}")
        manifest_content = g_repo.get_contents("manifest.json", ref=latest_release[0])
        return json.loads(manifest_content.decoded_content)  # type: ignore
    except Exception as e:
        print(f"Error: {e}")
