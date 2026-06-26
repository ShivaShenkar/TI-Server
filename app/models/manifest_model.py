from typing import Optional, Dict, List, Literal
from pydantic import BaseModel, Field, AliasChoices


class ManifestModel(BaseModel):
    name: str
    description: str
    version: str = Field(validation_alias=AliasChoices("version", "latestVersion"))
    # key is OS, value is path for exe file of matching OS
    supportedOS: Dict[Literal["windows", "linux", "macos"], str]
    iconPath: Optional[str] = None

    def get_supported_os(self) -> List[str]:
        return list(self.supportedOS.keys())
