from pydantic import BaseModel


# Archive URLs and the release target used when constructing icon URLs.
class ReleaseInfo(BaseModel):
    # version: str
    zipball_url: str
    tarball_url: str
    branch: str
