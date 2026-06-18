from dataclasses import dataclass
from typing import List, Literal, Optional

"""
Model for rendering all needed data to client.
"""
@dataclass
class AppModel:
    id: str
    name: str
    description: str
    # versions: List[str]
    latestVersion:str
    versions: List[str] | None
    status: Literal["not installed", "update available", "up to date"]
    # supportedOS: List[str]
    installedVersion: Optional[str] = None
    iconUrl: Optional[str] = None

    def json(self) -> dict[str, object]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "latestVersion":self.latestVersion,
            "versions": self.versions,
            "status": self.status,
            # "supportedOS": self.supportedOS,
            "installedVersion": self.installedVersion,
            "iconUrl": self.iconUrl,
        }
