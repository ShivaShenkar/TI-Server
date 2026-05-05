from dataclasses import dataclass
from typing import Dict, List, Literal, Optional
import json

"""
Model for rendering all needed data to client.
"""
@dataclass
class AppModel:
    id: str
    name: str
    description: str
    # versions: List[str]
    
    # key is version, value is list of supported OSes
    versions:Dict[str,List[str]]
    status: Literal["not installed", "update available", "up to date"]
    # supportedOS: List[str]
    installedVersion: Optional[str] = None
    iconPath: Optional[str] = None

    def json(self) -> str:
        return json.dumps(
            {
                "id": self.id,
                "name": self.name,
                "description": self.description,
                "versions": self.versions,
                "status": self.status,
                # "supportedOS": self.supportedOS,
                "installedVersion": self.installedVersion,
                "iconPath": self.iconPath,
            }
        )
