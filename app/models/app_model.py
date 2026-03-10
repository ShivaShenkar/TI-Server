from dataclasses import dataclass
from typing import List, Literal, Optional
import json

@dataclass
class AppModel:
    name: str
    description: str
    versions: List[str]
    status =  Literal["not installed", "update available", "up to date"]
    supportedOS: List[str]
    installedVersion: Optional[str] = None
    iconPath: Optional[str] = None

    @classmethod
    def json(cls):
        return json.dumps(
            {
                "name":cls.name,
                "description":cls.description,
                "versions":cls.versions,
                "status":cls.status,
                "supportedOS":cls.supportedOS,
                "installedVersion":cls.installedVersion,
                "iconPath":cls.iconPath
            }
        )
