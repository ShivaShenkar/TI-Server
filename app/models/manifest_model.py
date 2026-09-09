from typing import Optional, Dict, List, Literal
from pydantic import BaseModel, Field, AliasChoices


# Metadata read from release manifests or reconstructed from cached app data.
class ManifestModel(BaseModel):
    name: str
    description: str
    # Accept both manifest version and cached client latestVersion fields.
    version: str = Field(validation_alias=AliasChoices("version", "latestVersion"))
    # key is OS, value is path for exe file of matching OS
    supportedOS: Dict[Literal["windows", "linux", "macos"], str]
    iconPath: Optional[str] = None

    def get_supported_os(self) -> List[str]:
        return list(self.supportedOS.keys())
