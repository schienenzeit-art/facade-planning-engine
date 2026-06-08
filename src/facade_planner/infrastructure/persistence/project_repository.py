import json
import uuid
from pathlib import Path

from facade_planner.domain.entities.project import Project
from facade_planner.domain.exceptions import ProjectAlreadyExistsError, ProjectNotInitializedError

_PROJECT_FILE = "project.json"
_SUBDIRS = ("plans", "surfaces", "jobs", "exports", "catalogs")


class FileProjectRepository:
    def __init__(self, root_path: Path) -> None:
        self._root = root_path
        self._data_path = root_path / ".facadeplanner"

    def exists(self) -> bool:
        return (self._data_path / _PROJECT_FILE).exists()

    def create(self, name: str) -> Project:
        if self.exists():
            raise ProjectAlreadyExistsError(str(self._data_path))
        self._data_path.mkdir(exist_ok=True)
        for sub in _SUBDIRS:
            (self._data_path / sub).mkdir(exist_ok=True)
        project = Project(id=str(uuid.uuid4()), name=name, path=str(self._root))
        (self._data_path / _PROJECT_FILE).write_text(
            project.model_dump_json(indent=2), encoding="utf-8"
        )
        return project

    def load(self) -> Project:
        project_file = self._data_path / _PROJECT_FILE
        if not project_file.exists():
            raise ProjectNotInitializedError()
        return Project.model_validate_json(project_file.read_text(encoding="utf-8"))
