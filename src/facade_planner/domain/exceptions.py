class FacadePlannerError(Exception):
    """Base exception for all domain errors."""


class UserInputError(FacadePlannerError):
    """Invalid input from user (wrong format, missing file, bad value)."""


class ProjectNotInitializedError(FacadePlannerError):
    """No .facadeplanner/ project found in current directory."""

    def __init__(self) -> None:
        super().__init__(
            "Kein Projekt gefunden. Bitte zuerst 'facade project create <name>' ausführen."
        )


class ProjectAlreadyExistsError(FacadePlannerError):
    """A project already exists in this directory."""

    def __init__(self, path: str) -> None:
        super().__init__(f"Projekt existiert bereits in: {path}")


class EntityNotFoundError(FacadePlannerError):
    """Requested entity does not exist."""

    def __init__(self, entity_type: str, entity_id: str) -> None:
        super().__init__(f"{entity_type} nicht gefunden: {entity_id}")


class DomainRuleError(FacadePlannerError):
    """A domain invariant was violated."""


class CalibrationError(UserInputError):
    """Scale calibration failed."""


class PanelizationError(FacadePlannerError):
    """Panelization failed for a surface."""

    def __init__(self, error_type: str, surface_id: str, message: str) -> None:
        self.error_type = error_type
        self.surface_id = surface_id
        super().__init__(f"[{error_type}] Surface {surface_id}: {message}")
