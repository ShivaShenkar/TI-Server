from typing import List, Literal, Optional, Dict
from pydantic import BaseModel

"""
Model for rendering all needed data to client.
"""


class AppModel(BaseModel):
    id: str
    name: str
    description: str
    latestVersion: str
    versions: List[str]
    status: Literal["not installed", "update available", "up to date"]
    supportedOS: Dict[Literal["windows", "linux", "macos"], str]
    installedVersion: Optional[str] = None
    iconUrl: Optional[str] = None
