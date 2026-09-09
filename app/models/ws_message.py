from dataclasses import dataclass
from typing import Literal


# Single-app socket payload; services convert it to a dictionary with asdict.
@dataclass
class WSMessage:
    type: Literal["launch", "app-running", "app-stopped", "stop"]
    appId: str
