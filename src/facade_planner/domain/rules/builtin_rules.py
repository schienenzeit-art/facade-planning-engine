"""Builtin planning rules GR-001 to GR-010.

Rules are pure data (RuleDefinition). Evaluation logic lives in RuleEngine.
"""
from facade_planner.domain.enums import RuleCategory, RuleSeverity
from facade_planner.domain.rules.rule_definition import RuleDefinition

BUILTIN_RULES: list[RuleDefinition] = [
    # ── GEOMETRIC ──────────────────────────────────────────────────────────────
    RuleDefinition(
        id="GR-001",
        name="Panel-Format-Referenz",
        description="Jedes Panel muss eine gültige Format-Referenz haben.",
        severity=RuleSeverity.ERROR,
        category=RuleCategory.FORMAT,
        is_builtin=True,
        suggestion="Vergewissere dich, dass ein Lieferantenkatalog importiert wurde.",
    ),
    RuleDefinition(
        id="GR-002",
        name="Panel-Übermass",
        description="Panel-Masse dürfen die Rohplattengroesse des Formats nicht überschreiten.",
        severity=RuleSeverity.ERROR,
        category=RuleCategory.FORMAT,
        is_builtin=True,
        suggestion="Wähle ein grösseres Format oder verkleinere die Fassadenfläche.",
    ),
    RuleDefinition(
        id="GR-003",
        name="Panel-Mindestmasse",
        description="Panel-Breite und -Höhe müssen grösser als 0mm sein.",
        severity=RuleSeverity.ERROR,
        category=RuleCategory.GEOMETRIC,
        is_builtin=True,
        suggestion="Prüfe die Panelisierungs-Konfiguration und die Flächengeometrie.",
    ),
    RuleDefinition(
        id="GR-004",
        name="Eindeutige Flächen-IDs",
        description="Jede FacadeSurface-ID darf im Ergebnis nur einmal vorkommen.",
        severity=RuleSeverity.ERROR,
        category=RuleCategory.GEOMETRIC,
        is_builtin=True,
        suggestion="Interner Fehler: Bitte melde dieses Problem.",
    ),
    RuleDefinition(
        id="GR-005",
        name="Eindeutige Panel-IDs",
        description="Jede Panel-ID darf im Ergebnis nur einmal vorkommen.",
        severity=RuleSeverity.ERROR,
        category=RuleCategory.GEOMETRIC,
        is_builtin=True,
        suggestion="Interner Fehler: Bitte melde dieses Problem.",
    ),
    # ── TECHNICAL ──────────────────────────────────────────────────────────────
    RuleDefinition(
        id="GR-006",
        name="Mindestrandabstand Öffnung",
        description="Mindestabstand zwischen Panel-Kante und Öffnungsrand.",
        severity=RuleSeverity.WARNING,
        category=RuleCategory.TECHNICAL,
        parameters={"min_opening_clearance_mm": 0},
        is_builtin=True,
        suggestion="Erhöhe den Abstand oder passe die Panelisierungs-Konfiguration an.",
    ),
    RuleDefinition(
        id="GR-007",
        name="Mindestpanelgrösse nach Schnitt",
        description="Restpanel nach Öffnungsschnitt darf die Mindestgrösse nicht unterschreiten.",
        severity=RuleSeverity.INFO,
        category=RuleCategory.TECHNICAL,
        parameters={"min_cut_panel_width_mm": 50},
        is_builtin=True,
        suggestion="Panel wird entfernt. Prüfe die Öffnungsgeometrie oder erhöhe min_panel_width_mm.",
    ),
    # ── JOINT ──────────────────────────────────────────────────────────────────
    RuleDefinition(
        id="GR-008",
        name="Bewegungsfugen-Intervall",
        description="Bewegungsfugen (Expansion Joints) müssen in konfigurierbarem Abstand gesetzt werden.",
        severity=RuleSeverity.WARNING,
        category=RuleCategory.JOINT,
        parameters={"expansion_joint_interval_mm": 6000},
        is_builtin=True,
        suggestion=(
            "Gemaess SIA 331 / Swisspearl-Empfehlung: Bewegungsfugen alle 6000mm. "
            "Konfiguriere expansion_joint_interval_mm in PanelizationConfig."
        ),
    ),
    RuleDefinition(
        id="GR-009",
        name="Mindestfugengrösse",
        description="Horizontale und vertikale Fugen müssen mindestens 8mm breit sein (Swisspearl).",
        severity=RuleSeverity.WARNING,
        category=RuleCategory.JOINT,
        parameters={"min_joint_width_mm": 8},
        is_builtin=True,
        suggestion=(
            "Erhöhe horizontal_joint_mm / vertical_joint_mm auf mindestens 8mm "
            "gemäss Swisspearl-Verarbeitungsrichtlinien."
        ),
    ),
    RuleDefinition(
        id="GR-010",
        name="Keine Panel-Überlappungen",
        description="Keine zwei Panels dürfen sich überlappen.",
        severity=RuleSeverity.ERROR,
        category=RuleCategory.GEOMETRIC,
        is_builtin=True,
        suggestion="Interner Fehler im Panelisierungs-Algorithmus. Bitte melde dieses Problem.",
    ),
]

BUILTIN_RULE_IDS: set[str] = {r.id for r in BUILTIN_RULES}
