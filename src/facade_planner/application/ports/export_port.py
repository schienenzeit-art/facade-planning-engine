from abc import ABC, abstractmethod
from pathlib import Path

from facade_planner.domain.entities.facade_surface import FacadeSurface
from facade_planner.domain.entities.panelization_result import PanelizationResult


class ExportPort(ABC):
    @abstractmethod
    def export(
        self,
        result: PanelizationResult,
        surfaces: list[FacadeSurface],
        output_path: Path,
    ) -> None: ...
