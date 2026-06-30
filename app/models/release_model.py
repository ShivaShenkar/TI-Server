from pydantic import BaseModel


class ReleaseInfo(BaseModel):
    # version: str
    zipball_url: str
    tarball_url: str
    branch: str
