from pydantic import BaseModel, Field, model_validator


class JointConfig(BaseModel):
    """Joint configuration for panelization. All values in mm."""

    model_config = {"frozen": True}

    horizontal_joint_mm: float = Field(default=10.0, ge=0)
    vertical_joint_mm: float = Field(default=10.0, ge=0)
    expansion_joint_interval_mm: float = Field(
        default=6000.0,
        ge=0,
        description="Distance between expansion joints (Bewegungsfugen). 0 = disabled.",
    )
    expansion_joint_width_mm: float = Field(default=20.0, ge=0)

    @model_validator(mode="after")
    def warn_narrow_joints(self) -> "JointConfig":
        # Minimum per SIA 331 / Swisspearl recommendation is 8mm.
        # Validation happens in RuleEngine (GR-009); this VO accepts any value >= 0.
        return self
