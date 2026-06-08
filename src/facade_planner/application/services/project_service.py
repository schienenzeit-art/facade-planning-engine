from pathlib import Path

from facade_planner.domain.entities.project import Project
from facade_planner.domain.exceptions import ProjectNotInitializedError
from facade_planner.infrastructure.persistence.project_repository import FileProjectRepository


class ProjectService:
    def __init__(self, cwd: Path | None = None) -> None:
        self._repo = FileProjectRepository(cwd or Path.cwd())

    def create_project(self, name: str) -> Project:
        return self._repo.create(name)

    def require_initialized(self) -> Project:
        """Call at the start of every CLI command that needs a project."""
        return self._repo.load()

    def is_initialized(self) -> bool:
        return self._repo.exists()
