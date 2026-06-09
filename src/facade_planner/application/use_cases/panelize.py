"""PanelizeUseCase — entry point for running a panelization job."""
from __future__ import annotations

import uuid
from datetime import datetime
from pathlib import Path

from facade_planner.domain.algorithms.grid_panelization_algorithm import (
    GridPanelizationAlgorithm,
)
from facade_planner.domain.entities.panelization_job import (
    PanelizationConfig,
    PanelizationJob,
    PanelizationStatus,
)
from facade_planner.domain.entities.panelization_result import PanelizationResult
from facade_planner.domain.enums import SurfaceStatus
from facade_planner.domain.exceptions import DomainRuleError, EntityNotFoundError
from facade_planner.domain.services.panelization_service import PanelizationService
from facade_planner.infrastructure.persistence.facade_surface_repository import (
    FileFacadeSurfaceRepository,
)
from facade_planner.infrastructure.persistence.panelization_repository import (
    FilePanelizationRepository,
)
from facade_planner.infrastructure.persistence.rule_catalog_repository import (
    FileRuleCatalogRepository,
)
from facade_planner.infrastructure.persistence.supplier_catalog_repository import (
    FileSupplierCatalogRepository,
)


class PanelizeUseCase:
    """Loads surfaces + formats, runs GridPanelizationAlgorithm, saves job + result.

    Raises:
        DomainRuleError: if no catalogs/surfaces found or prerequisites not met.
        EntityNotFoundError: if a specific surface_id or catalog_id does not exist.
    """

    def __init__(self, data_dir: Path) -> None:
        self._data_dir = data_dir
        self._surface_repo = FileFacadeSurfaceRepository(data_dir / "surfaces")
        self._catalog_repo = FileSupplierCatalogRepository(data_dir / "catalogs")
        self._job_repo = FilePanelizationRepository(data_dir / "jobs")
        self._rule_repo = FileRuleCatalogRepository(data_dir)

    def execute(
        self,
        project_id: str,
        catalog_ids: list[str],
        surface_ids: list[str] | None = None,
        config: PanelizationConfig | None = None,
    ) -> tuple[PanelizationJob, PanelizationResult]:
        cfg = config or PanelizationConfig()

        # Load surfaces
        if surface_ids:
            surfaces = [self._surface_repo.load(sid) for sid in surface_ids]
        else:
            surfaces = [
                s
                for s in self._surface_repo.list_all()
                if s.status == SurfaceStatus.CONFIRMED
            ]

        if not surfaces:
            raise DomainRuleError(
                "Keine bestaetigten Flaechen gefunden. "
                "Bitte zuerst 'facade surface confirm <id>' ausfuehren."
            )

        # Load formats from catalogs
        formats = _load_formats(self._catalog_repo, catalog_ids)
        if not formats:
            raise DomainRuleError(
                "Keine aktiven Formate in den angegebenen Katalogen gefunden. "
                "Bitte zuerst einen Katalog importieren: facade catalog import <name>"
            )

        # Load or create rule catalog
        rule_catalog = self._rule_repo.load_or_create(project_id)

        # Build and run job
        job = PanelizationJob(
            id=f"JOB-{uuid.uuid4().hex[:8].upper()}",
            surface_ids=[s.id for s in surfaces],
            catalog_ids=catalog_ids,
            config=cfg,
            status=PanelizationStatus.RUNNING,
        )
        self._job_repo.save_job(job)

        algo = GridPanelizationAlgorithm()
        svc = PanelizationService(algo, rule_catalog)
        result = svc.panelize(job, surfaces, formats)

        # Finalize job status
        job = job.model_copy(
            update={
                "status": (
                    PanelizationStatus.FAILED
                    if result.failed_surface_ids and not result.panels
                    else PanelizationStatus.COMPLETED
                ),
                "completed_at": datetime.now(),
            }
        )
        self._job_repo.save_job(job)
        self._job_repo.save_result(result)

        return job, result


def _load_formats(
    catalog_repo: FileSupplierCatalogRepository,
    catalog_ids: list[str],
) -> list:
    """Load active PanelFormats from the given catalogs.

    If catalog_ids is empty, load from all available catalogs.
    """
    if catalog_ids:
        catalogs = [catalog_repo.load(cid) for cid in catalog_ids]
    else:
        catalogs = catalog_repo.list_all()

    formats = []
    seen: set[str] = set()
    for cat in catalogs:
        for fmt in cat.active_formats:
            if fmt.format_code not in seen:
                formats.append(fmt)
                seen.add(fmt.format_code)
    return formats
