import json
from pathlib import Path

from facade_planner.domain.entities.facade_plan import FacadePlan
from facade_planner.domain.exceptions import EntityNotFoundError


class FileFacadePlanRepository:
    """JSON-backed FacadePlan persistence (one file per plan in .facadeplanner/plans/)."""

    def __init__(self, plans_dir: Path) -> None:
        self._dir = plans_dir

    def save(self, plan: FacadePlan) -> None:
        self._dir.mkdir(parents=True, exist_ok=True)
        (self._dir / f"{plan.id}.json").write_text(
            plan.model_dump_json(indent=2), encoding="utf-8"
        )

    def load(self, plan_id: str) -> FacadePlan:
        path = self._dir / f"{plan_id}.json"
        if not path.exists():
            raise EntityNotFoundError("FacadePlan", plan_id)
        return FacadePlan.model_validate_json(path.read_text(encoding="utf-8"))

    def list_all(self) -> list[FacadePlan]:
        if not self._dir.exists():
            return []
        plans: list[FacadePlan] = []
        for f in sorted(self._dir.glob("*.json")):
            try:
                plans.append(FacadePlan.model_validate_json(f.read_text(encoding="utf-8")))
            except Exception:
                continue
        return plans

    def delete(self, plan_id: str) -> None:
        path = self._dir / f"{plan_id}.json"
        if not path.exists():
            raise EntityNotFoundError("FacadePlan", plan_id)
        path.unlink()
