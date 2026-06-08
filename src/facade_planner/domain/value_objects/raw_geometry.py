from pydantic import BaseModel, Field, computed_field


Coordinate = tuple[float, float]


class RawGeometry(BaseModel):
    """A single vector path extracted from a PDF page."""

    model_config = {"frozen": True}

    coordinates: list[Coordinate] = Field(min_length=2)
    layer: str = ""
    color: tuple[int, int, int] | None = None
    line_type: str = "SOLID"
    is_closed: bool = False

    @computed_field  # type: ignore[misc]
    @property
    def point_count(self) -> int:
        return len(self.coordinates)
