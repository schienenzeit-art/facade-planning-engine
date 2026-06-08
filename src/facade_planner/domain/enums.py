from enum import Enum


class PDFSource(str, Enum):
    AUTOCAD = "AUTOCAD"
    REVIT = "REVIT"
    ARCHICAD = "ARCHICAD"
    GENERIC = "GENERIC"


class SurfaceStatus(str, Enum):
    DETECTED = "DETECTED"
    CONFIRMED = "CONFIRMED"
    REJECTED = "REJECTED"


class OpeningType(str, Enum):
    WINDOW = "WINDOW"
    DOOR = "DOOR"
    VENT = "VENT"
    OTHER = "OTHER"


class PanelizationStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class PanelizationErrorType(str, Enum):
    """Typed panelization errors per surface."""
    PE_001_NO_FORMAT_FITS = "PE-001"
    PE_002_EDGE_PANEL_TOO_SMALL = "PE-002"
    PE_003_ALL_PANELS_BLOCKED = "PE-003"
    PE_004_SURFACE_TOO_SMALL = "PE-004"


class OpeningStrategy(str, Enum):
    TRIM = "TRIM"
    DROP = "DROP"


class PanelOrientation(str, Enum):
    HORIZONTAL = "HORIZONTAL"
    VERTICAL = "VERTICAL"
    AUTO = "AUTO"


class RuleSeverity(str, Enum):
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


class RuleCategory(str, Enum):
    GEOMETRIC = "GEOMETRIC"
    FORMAT = "FORMAT"
    JOINT = "JOINT"
    TECHNICAL = "TECHNICAL"


class SelectionReason(str, Enum):
    FULL_PANEL_FIT = "FULL_PANEL_FIT"
    SMALLEST_FIT = "SMALLEST_FIT"
    ONLY_FIT = "ONLY_FIT"
    NONE_FIT = "NONE_FIT"


class CutReason(str, Enum):
    OPENING = "OPENING"
    SURFACE_EDGE = "SURFACE_EDGE"
    EXPANSION_JOINT = "EXPANSION_JOINT"


class ScaleMethod(str, Enum):
    TWO_POINT = "TWO_POINT"
    DIRECT = "DIRECT"
