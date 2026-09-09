from pydantic import BaseModel


# GitHub repository coordinates for an app catalog entry.
class DbItem(BaseModel):
    owner: str
    repo: str
