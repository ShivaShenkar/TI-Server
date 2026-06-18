from dataclasses import dataclass
from typing import Literal


@dataclass
class WSMessage:
    type: Literal['launch','app-running' ,'app-stopped','stop']
    appId: str