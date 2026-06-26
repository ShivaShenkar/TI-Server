from pydantic import BaseModel


class DbItem(BaseModel):
    owner: str
    repo: str
