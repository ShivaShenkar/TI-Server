from pydantic import BaseModel


class ReleaseURLs(BaseModel):
    # version: str
    zipball_url: str
    tarball_url: str
