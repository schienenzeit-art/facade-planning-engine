from pathlib import Path

from facade_planner.domain.entities.supplier_catalog import SupplierCatalog
from facade_planner.domain.exceptions import EntityNotFoundError


class FileSupplierCatalogRepository:
    """JSON-backed persistence for SupplierCatalog (one file per catalog)."""

    def __init__(self, catalogs_dir: Path) -> None:
        self._dir = catalogs_dir

    def save(self, catalog: SupplierCatalog) -> None:
        self._dir.mkdir(parents=True, exist_ok=True)
        (self._dir / f"{catalog.id}.json").write_text(
            catalog.model_dump_json(indent=2), encoding="utf-8"
        )

    def load(self, catalog_id: str) -> SupplierCatalog:
        path = self._dir / f"{catalog_id}.json"
        if not path.exists():
            raise EntityNotFoundError("SupplierCatalog", catalog_id)
        return SupplierCatalog.model_validate_json(path.read_text(encoding="utf-8"))

    def list_all(self) -> list[SupplierCatalog]:
        if not self._dir.exists():
            return []
        result: list[SupplierCatalog] = []
        for f in sorted(self._dir.glob("*.json")):
            try:
                result.append(SupplierCatalog.model_validate_json(f.read_text(encoding="utf-8")))
            except Exception:
                continue
        return result

    def exists(self, catalog_id: str) -> bool:
        return (self._dir / f"{catalog_id}.json").exists()

    def delete(self, catalog_id: str) -> None:
        path = self._dir / f"{catalog_id}.json"
        if not path.exists():
            raise EntityNotFoundError("SupplierCatalog", catalog_id)
        path.unlink()
