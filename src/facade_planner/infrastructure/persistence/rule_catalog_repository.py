import uuid
from pathlib import Path

from facade_planner.domain.exceptions import EntityNotFoundError
from facade_planner.domain.rules.rule_catalog import RuleCatalog


class FileRuleCatalogRepository:
    """JSON-backed persistence for RuleCatalog (one catalog per project)."""

    _FILENAME = "rule_catalog.json"

    def __init__(self, data_path: Path) -> None:
        self._path = data_path / self._FILENAME

    def load_or_create(self, project_id: str) -> RuleCatalog:
        if self._path.exists():
            catalog = RuleCatalog.model_validate_json(
                self._path.read_text(encoding="utf-8")
            )
        else:
            catalog = RuleCatalog(id=str(uuid.uuid4()), project_id=project_id)
        catalog.initialize_builtin_rules()
        self._save(catalog)
        return catalog

    def load(self) -> RuleCatalog:
        if not self._path.exists():
            raise EntityNotFoundError("RuleCatalog", self._FILENAME)
        return RuleCatalog.model_validate_json(self._path.read_text(encoding="utf-8"))

    def save(self, catalog: RuleCatalog) -> None:
        self._save(catalog)

    def _save(self, catalog: RuleCatalog) -> None:
        self._path.write_text(catalog.model_dump_json(indent=2), encoding="utf-8")
