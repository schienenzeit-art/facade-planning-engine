from abc import ABC, abstractmethod
from pathlib import Path

from facade_planner.domain.entities.facade_plan import FacadePlan


class ImportPort(ABC):
    @abstractmethod
    def import_plan(self, path: Path, name: str) -> FacadePlan: ...
