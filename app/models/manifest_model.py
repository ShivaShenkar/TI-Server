from dataclasses import dataclass
from typing import Optional, Dict,Any

@dataclass
class ManifestModel:
    name: str
    description: str
    version: str
    #key is OS
    #value is path for exe file of matching OS
    supportedOS: Dict[str, str]
    iconPath: Optional[str] = None

    @staticmethod
    def convert_data_to_manifest_model(data:Any) ->"ManifestModel":
        if isinstance(data,"ManifestModel"):
            return data
        if not isinstance(data, dict):
            raise ValueError("Invalid data format: expected item to be a dictionary")

        if not "name" in data or not "description" in data or not "version" in data or not "supportedOS" in data :
            raise ValueError(f"Invalid data format: missing required fields for ManifestModel conversion in argument: {data}")
                             
        if not isinstance(data["name"], str) or not isinstance(data["description"], str) or not isinstance(data["version"], str) or not isinstance(data["supportedOS"], dict):
            raise ValueError(f"Invalid data format: invalid field types in instance: {data}")
        
        if len(data["supportedOS"].keys())==0:
            raise ValueError(f"Invalid data format: app doesn't have supported OS")
        
        iconPath = None
        if "iconPath" in data:
            if isinstance(data["iconPath"],str):
                iconPath = data["iconPath"]

        return ManifestModel(name=data["name"],description=data["description"],version=data["version"],supportedOS=data["supportedOS"],iconPath=iconPath)
    


