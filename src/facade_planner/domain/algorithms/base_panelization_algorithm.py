"""Abstract base class for all panelization algorithms (Strategy Pattern)."""
from __future__ import annotations

from abc import ABC, abstractmethod

from facade_planner.domain.entities.facade_surface import FacadeSurface
from facade_planner.domain.entities.panel import Panel
from facade_planner.domain.entities.panel_format import PanelFormat
from facade_planner.domain.entities.panelization_job import PanelizationConfig


class BasePanelizationAlgorithm(ABC):
    """Strategy interface for panel layout algorithms.

    Concrete implementations receive a surface plus available formats and
    produce a flat list of placed Panel objects (raises PanelizationError on
    unrecoverable failures).
    """

    @classmethod
    @abstractmethod
    def name(cls) -> str:
        """Short, stable identifier used for persistence (e.g. 'grid-v1')."""

    @abstractmethod
    def panelize(
        self,
        surface: FacadeSurface,
        formats: list[PanelFormat],
        config: PanelizationConfig,
    ) -> list[Panel]:
        """Place panels on *surface* and return the resulting Panel list.

        Raises:
            PanelizationError: when the surface cannot be panelized
                (PE-001 / PE-002 / PE-003 / PE-004).
        """
