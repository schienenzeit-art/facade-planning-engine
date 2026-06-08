from abc import ABC, abstractmethod

from facade_planner.domain.entities.facade_plan import FacadePlan
from facade_planner.domain.entities.facade_surface import FacadeSurface
from facade_planner.domain.entities.facade_zone import FacadeZone
from facade_planner.domain.entities.panelization_job import PanelizationJob
from facade_planner.domain.entities.panelization_result import PanelizationResult
from facade_planner.domain.entities.project import Project
from facade_planner.domain.entities.supplier_catalog import SupplierCatalog


class ProjectRepository(ABC):
    @abstractmethod
    def create(self, project: Project) -> None: ...

    @abstractmethod
    def load(self) -> Project: ...

    @abstractmethod
    def exists(self) -> bool: ...


class FacadePlanRepository(ABC):
    @abstractmethod
    def save(self, plan: FacadePlan) -> None: ...

    @abstractmethod
    def load(self, plan_id: str) -> FacadePlan: ...

    @abstractmethod
    def list_all(self) -> list[FacadePlan]: ...


class FacadeSurfaceRepository(ABC):
    @abstractmethod
    def save(self, surface: FacadeSurface) -> None: ...

    @abstractmethod
    def load(self, surface_id: str) -> FacadeSurface: ...

    @abstractmethod
    def list_all(self) -> list[FacadeSurface]: ...


class FacadeZoneRepository(ABC):
    @abstractmethod
    def save(self, zone: FacadeZone) -> None: ...

    @abstractmethod
    def load(self, zone_id: str) -> FacadeZone: ...

    @abstractmethod
    def list_all(self) -> list[FacadeZone]: ...


class SupplierCatalogRepository(ABC):
    @abstractmethod
    def save(self, catalog: SupplierCatalog) -> None: ...

    @abstractmethod
    def load(self, catalog_id: str) -> SupplierCatalog: ...

    @abstractmethod
    def list_all(self) -> list[SupplierCatalog]: ...


class PanelizationJobRepository(ABC):
    @abstractmethod
    def save_job(self, job: PanelizationJob) -> None: ...

    @abstractmethod
    def load_job(self, job_id: str) -> PanelizationJob: ...

    @abstractmethod
    def save_result(self, result: PanelizationResult) -> None: ...

    @abstractmethod
    def load_result(self, job_id: str) -> PanelizationResult: ...

    @abstractmethod
    def list_jobs(self) -> list[PanelizationJob]: ...
