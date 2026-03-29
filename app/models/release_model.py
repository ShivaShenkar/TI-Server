from dataclasses import dataclass
from typing import Dict


@dataclass
class ReleaseModel:
    version: str
    zipball_url: str
    tarball_url: str

    def json(self) -> Dict[str, str]:
        return {
            "version": self.version,
            "zipball_url": self.zipball_url,
            "tarball_url": self.tarball_url,
        }
