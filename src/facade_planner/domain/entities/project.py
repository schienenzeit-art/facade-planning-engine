from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field


class Project(BaseModel):
    id: str
    name: str
    path: str
    created_at: datetime = Field(default_factory=datetime.now)

    @property
    def root_path(self) -> Path:
        return Path(self.path)

    @property
    def data_path(self) -> Path:
        return self.root_path / ".facadeplanner"
