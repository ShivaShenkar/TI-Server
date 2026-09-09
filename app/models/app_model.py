from typing import List, Literal, Optional, Dict
from pydantic import BaseModel

"""
Model for rendering all needed data to client.
"""


# Client-facing app metadata combined with local installation status.
class AppModel(BaseModel):
    id: str
    name: str
    description: str
    latestVersion: str
    versions: List[str]
    status: Literal["not installed", "update available", "up to date"]
    # Each OS maps to its executable path relative to the installed app folder.
    supportedOS: Dict[Literal["windows", "linux", "macos"], str]
    # Optional fields allow not installed apps and apps without icons.
    installedVersion: Optional[str] = None
    iconUrl: Optional[str] = None
