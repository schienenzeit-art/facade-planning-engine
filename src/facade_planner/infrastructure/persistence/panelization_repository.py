"""JSON-backed persistence for PanelizationJob and PanelizationResult."""
from __future__ import annotations

from pathlib import Path

from facade_planner.domain.entities.panelization_job import PanelizationJob
from facade_planner.domain.entities.panelization_result import PanelizationResult
from facade_planner.domain.exceptions import EntityNotFoundError


class FilePanelizationRepository:
    """Stores jobs and results as JSON files under <jobs_dir>/.

    Layout:
        {job_id}.json          — PanelizationJob
        {job_id}_result.json   — PanelizationResult
    """

    def __init__(self, jobs_dir: Path) -> None:
        self._dir = jobs_dir

    def save_job(self, job: PanelizationJob) -> None:
        self._dir.mkdir(parents=True, exist_ok=True)
        (self._dir / f"{job.id}.json").write_text(
            job.model_dump_json(indent=2), encoding="utf-8"
        )

    def save_result(self, result: PanelizationResult) -> None:
        self._dir.mkdir(parents=True, exist_ok=True)
        (self._dir / f"{result.job_id}_result.json").write_text(
            result.model_dump_json(indent=2), encoding="utf-8"
        )

    def load_job(self, job_id: str) -> PanelizationJob:
        path = self._dir / f"{job_id}.json"
        if not path.exists():
            raise EntityNotFoundError("PanelizationJob", job_id)
        return PanelizationJob.model_validate_json(path.read_text(encoding="utf-8"))

    def load_result(self, job_id: str) -> PanelizationResult:
        path = self._dir / f"{job_id}_result.json"
        if not path.exists():
            raise EntityNotFoundError("PanelizationResult", job_id)
        return PanelizationResult.model_validate_json(path.read_text(encoding="utf-8"))

    def list_jobs(self) -> list[PanelizationJob]:
        if not self._dir.exists():
            return []
        jobs: list[PanelizationJob] = []
        for f in sorted(self._dir.glob("*.json")):
            if f.stem.endswith("_result"):
                continue
            try:
                jobs.append(PanelizationJob.model_validate_json(f.read_text(encoding="utf-8")))
            except Exception:
                continue
        return jobs

    def exists_job(self, job_id: str) -> bool:
        return (self._dir / f"{job_id}.json").exists()

    def exists_result(self, job_id: str) -> bool:
        return (self._dir / f"{job_id}_result.json").exists()
