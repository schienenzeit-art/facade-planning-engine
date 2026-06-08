from abc import ABC, abstractmethod
from pathlib import Path

from facade_planner.domain.entities.panelization_result import PanelizationResult


class ExportPort(ABC):
    @abstractmethod
    def export(self, result: PanelizationResult, output_path: Path) -> None: ...
