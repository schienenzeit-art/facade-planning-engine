from datetime import datetime

from pydantic import BaseModel, Field

from facade_planner.domain.entities.panel_format import PanelFormat


class SupplierCatalog(BaseModel):
    id: str
    supplier_name: str
    formats: list[PanelFormat] = Field(default_factory=list)
    rules_raw: list[dict] = Field(default_factory=list)
    imported_at: datetime = Field(default_factory=datetime.now)
    source_path: str = ""

    @property
    def active_formats(self) -> list[PanelFormat]:
        return [f for f in self.formats if f.is_active]

    def get_format(self, format_code: str) -> PanelFormat | None:
        return next((f for f in self.formats if f.format_code == format_code), None)
