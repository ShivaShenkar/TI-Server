from dataclasses import dataclass
from typing import Optional, Dict, Any, List, cast


@dataclass
class ManifestModel:
    name: str
    description: str
    version: str
    # key is OS
    # value is path for exe file of matching OS
    supportedOS: Dict[str, str]
    iconPath: Optional[str] = None

    def get_supported_os(self) -> List[str]:
        return list(self.supportedOS.keys())

    @staticmethod
    def convert_data_to_manifest_model(data: Any) -> "ManifestModel":
        if isinstance(data, ManifestModel):
            return data
        if not isinstance(data, dict):
            raise ValueError("Invalid data format: expected item to be a dictionary")

        if (
            "name" not in data
            or "description" not in data
            or "version" not in data
            or "supportedOS" not in data
        ):
            raise ValueError(
                f"Invalid data format: missing required fields for ManifestModel conversion in argument: {data}"
            )

        if (
            not isinstance(data["name"], str)
            or not isinstance(data["description"], str)
            or not isinstance(data["version"], str)
            or not isinstance(data["supportedOS"], dict)
        ):
            raise ValueError(
                f"Invalid data format: invalid field types in instance: {data}"
            )
        supportedOS = cast(Dict[str, str], data["supportedOS"])
        supportedOS = {
            osKey:pathValue 
                       for osKey,pathValue in supportedOS.items() 
                       if osKey in ["windows","linux","macos"]
            }

        if len(supportedOS) == 0:
            raise ValueError("Invalid data format: app doesn't have supported OS")

        iconPath = None
        if "iconPath" in data:
            if isinstance(data["iconPath"], str):
                iconPath = data["iconPath"]

        return ManifestModel(
            name=data["name"],
            description=data["description"],
            version=data["version"],
            supportedOS=supportedOS,
            iconPath=iconPath,
        )
