from dataclasses import dataclass
from typing import Any


@dataclass
class DbItem:
    owner: str
    repo: str

    @staticmethod
    def convert_to_DbItem(instance:Any) ->"DbItem":
        if isinstance(instance,DbItem):
            return instance
        
        if not isinstance(instance, dict):
            raise ValueError("Invalid data format: expected item to be a dictionary")

        if not "owner"  in instance or not "repo" in instance:
            raise ValueError(f"Invalid data format: missing required fields for DbItem conversion in instance: {instance}")
                             
        if not isinstance(instance["owner"], str) or not isinstance(instance["repo"], str):
            raise ValueError(f"Invalid data format: invalid field types in instance: {instance}")
        
        return DbItem(owner=instance["owner"], repo=instance["repo"])
    


    