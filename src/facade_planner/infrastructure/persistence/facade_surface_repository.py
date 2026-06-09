"""JSON-backed FacadeSurface repository (one file per surface)."""
from __future__ import annotations

from pathlib import Path

from facade_planner.domain.entities.facade_surface import FacadeSurface
from facade_planner.domain.exceptions import EntityNotFoundError


class FileFacadeSurfaceRepository:
    """Stores FacadeSurface objects as individual JSON files.

    Layout: <surfaces_dir>/<surface_id>.json
    """

    def __init__(self, surfaces_dir: Path) -> None:
        self._dir = surfaces_dir

    def save(self, surface: FacadeSurface) -> None:
        self._dir.mkdir(parents=True, exist_ok=True)
        (self._dir / f"{surface.id}.json").write_text(
            surface.model_dump_json(indent=2), encoding="utf-8"
        )

    def load(self, surface_id: str) -> FacadeSurface:
        path = self._dir / f"{surface_id}.json"
        if not path.exists():
            raise EntityNotFoundError("FacadeSurface", surface_id)
        return FacadeSurface.model_validate_json(path.read_text(encoding="utf-8"))

    def list_all(self) -> list[FacadeSurface]:
        if not self._dir.exists():
            return []
        result: list[FacadeSurface] = []
        for f in sorted(self._dir.glob("*.json")):
            try:
                result.append(FacadeSurface.model_validate_json(f.read_text(encoding="utf-8")))
            except Exception:
                continue
        return result

    def list_by_plan(self, plan_id: str) -> list[FacadeSurface]:
        return [s for s in self.list_all() if s.plan_id == plan_id]

    def exists(self, surface_id: str) -> bool:
        return (self._dir / f"{surface_id}.json").exists()

    def delete(self, surface_id: str) -> None:
        path = self._dir / f"{surface_id}.json"
        if not path.exists():
            raise EntityNotFoundError("FacadeSurface", surface_id)
        path.unlink()
