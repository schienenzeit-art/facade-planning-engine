from pydantic import BaseModel, Field


class FacadeZone(BaseModel):
    id: str
    name: str
    description: str = ""
    surface_ids: list[str] = Field(default_factory=list)

    def assign_surface(self, surface_id: str) -> None:
        if surface_id not in self.surface_ids:
            self.surface_ids.append(surface_id)

    def remove_surface(self, surface_id: str) -> None:
        self.surface_ids = [s for s in self.surface_ids if s != surface_id]
