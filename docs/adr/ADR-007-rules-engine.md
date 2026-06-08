# ADR-007: Rules Engine — Architektur des Regelwerks

**Status:** Accepted  
**Datum:** 2026-06-08  
**Entscheider:** Softwarearchitektur  
**Auslöser:** RISK-004 — Regelwerk wächst unkontrolliert ohne Architekturentscheidung  

---

## Kontext

Das Domänenmodell kennt bereits Business Rules (GR-001 bis GR-005). Mit den in den GAP- und Risk-Reviews identifizierten Erweiterungen (GR-006 bis GR-010, lieferantenspezifische Regeln, Bewegungsfugen) wächst das Regelwerk auf 15+ Regeln. Ohne eine strukturierte Architektur entstehen folgende Probleme:

1. Regeln sind über multiple Services verstreut — nicht wartbar
2. Regeln können nicht konfiguriert oder deaktiviert werden
3. Lieferantenspezifische Regeln haben keinen definierten Importpfad
4. Neue Regeln erfordern Code-Änderungen in vielen Stellen

**Für ein System das im Fassadenbau eingesetzt wird, ist das Regelwerk selbst ein Kernprodukt.** Es ist nicht Boilerplate — es ist fachliches Know-how, das akkumuliert und gepflegt werden muss.

---

## Entscheidung

Eine eigenständige **Rules-Engine-Teildomäne** wird als Teil der Kerndomäne implementiert.

### Architektur

```
domain/
└── rules/
    ├── __init__.py
    ├── rule_definition.py   ← Value Object: Definition einer Regel
    ├── rule_catalog.py      ← Entity: Projektspezifischer Regelkatalog
    ├── rule_violation.py    ← Value Object: Ergebnis einer Regelprüfung
    ├── rule_engine.py       ← Domain Service: Evaluiert Regeln
    └── builtin_rules.py     ← Standard-Regelimplementierungen (GR-001...GR-010)
```

### RuleDefinition (Value Object)

```python
@dataclass(frozen=True)
class RuleDefinition:
    id: RuleId               # z.B. "GR-001", "SWISSPEARL-002"
    name: str
    description: str
    severity: RuleSeverity   # ERROR | WARNING | INFO
    category: RuleCategory   # GEOMETRIC | FORMAT | JOINT | TECHNICAL | SUPPLIER
    parameters: dict         # Konfigurierbare Parameter
    is_builtin: bool         # True = im System eingebaut; False = importiert
```

### RuleCatalog (Entity, Aggregatroot der Rules-Teildomäne)

```python
@dataclass
class RuleCatalog:
    id: UUID
    project_id: UUID
    rules: List[RuleDefinition]    # Geordnete Liste (Priorität = Reihenfolge)
    
    def add_rule(self, rule: RuleDefinition) -> None: ...
    def deactivate_rule(self, rule_id: RuleId) -> None: ...
    def configure_rule(self, rule_id: RuleId, parameters: dict) -> None: ...
    def get_active_rules(self, category: RuleCategory = None) -> List[RuleDefinition]: ...
```

### RuleEngine (Domain Service)

```python
class RuleEngine:
    def evaluate_panelization(
        self,
        result: PanelizationResult,
        catalog: RuleCatalog
    ) -> List[RuleViolation]: ...
    
    def evaluate_panel(
        self,
        panel: Panel,
        surface: FacadeSurface,
        catalog: RuleCatalog
    ) -> List[RuleViolation]: ...
    
    def evaluate_surface(
        self,
        surface: FacadeSurface,
        catalog: RuleCatalog
    ) -> List[RuleViolation]: ...
```

### RuleViolation (Value Object)

```python
@dataclass(frozen=True)
class RuleViolation:
    rule_id: RuleId
    rule_name: str
    severity: RuleSeverity
    message: str
    context: dict            # {"panel_id": "PA-001", "surface_id": "FA-001"}
    suggestion: str          # Konkrete Handlungsempfehlung für den Nutzer
```

---

## Supplier-spezifische Regeln

Lieferanten können eigene technische Regeln als Teil ihres Katalogs liefern. Diese werden beim Katalog-Import in den projektspezifischen `RuleCatalog` übernommen:

```json
{
  "supplier": "Swisspearl",
  "rules": [
    {
      "id": "SWISSPEARL-001",
      "name": "Max. Plattengrösse",
      "description": "Kein Panel darf grösser als das grösste Swisspearl-Format sein",
      "severity": "ERROR",
      "category": "SUPPLIER",
      "parameters": {"max_width_mm": 1250, "max_height_mm": 3050}
    },
    {
      "id": "SWISSPEARL-002",
      "name": "Mindestfuge",
      "description": "Horizontale und vertikale Mindestfuge 8mm",
      "severity": "WARNING",
      "parameters": {"min_joint_mm": 8}
    }
  ]
}
```

---

## Eingebaute Basisregeln (Builtin Rules)

| Regel-ID | Kategorie | Severity | Beschreibung |
|----------|-----------|----------|-------------|
| GR-001 | FORMAT | ERROR | Panel muss Formatreferenz haben |
| GR-002 | FORMAT | ERROR | Panel ≤ Rohplattengrösse |
| GR-003 | GEOMETRIC | ERROR | Maße müssen in mm sein (> 0) |
| GR-004 | GEOMETRIC | ERROR | Flächen-IDs eindeutig |
| GR-005 | GEOMETRIC | ERROR | Panel-IDs eindeutig |
| GR-006 | TECHNICAL | WARNING | Mindestrandabstand Panel zu Öffnung |
| GR-007 | TECHNICAL | ERROR | Mindestpanelgrösse nach Öffnungsschnitt |
| GR-008 | JOINT | WARNING | Bewegungsfugen-Intervall einhalten |
| GR-009 | JOINT | WARNING | Fugengrösse ≥ 8mm |
| GR-010 | GEOMETRIC | INFO | Keine Panelüberlappungen |

---

## Verhalten bei Regelverletzungen

| Severity | Verhalten | Beispiel |
|----------|-----------|---------|
| ERROR | Panelisierung der betroffenen Fläche schlägt fehl | Panel grösser als Rohplatte |
| WARNING | Panelisierung läuft weiter, Warnung wird ausgegeben | Fuge < 8mm |
| INFO | Nur Logging, kein visueller Hinweis nötig | Statistik-Hinweis |

---

## Alternativen betrachtet

| Alternative | Warum verworfen |
|-------------|----------------|
| Regeln direkt im PanelizationService | Nicht wartbar, nicht konfigurierbar, nicht testbar isoliert |
| Externe Regel-Engine (Drittbibliothek) | Overkill; externe Abhängigkeit für domänenspezifische Logik unerwünscht |
| Nur Konfigurationsparameter (keine echte Engine) | Nicht erweiterbar auf Supplier-Regeln und komplexe Geometrie-Regeln |

---

## Konsequenzen

**Positiv:**
- Regelwerk ist ein eigenständiges, testbares und dokumentierbares Domänenobjekt
- Lieferantenspezifische Regeln haben einen sauberen Importpfad
- Regeln können pro Projekt konfiguriert werden (aktivieren/deaktivieren/Parameter)
- Neue Regeln werden hinzugefügt ohne bestehende Services zu ändern
- Fachliches Know-how (Bewegungsfugen, Mindestmasse) ist explizit und versionierbar

**Negativ:**
- Mehr Domänenobjekte zu implementieren und zu testen
- `ValidationService` (aus bisheriger Architektur) wird durch `RuleEngine` ersetzt/integriert

## Sprint-Auswirkung

Die Rules-Engine-Grundstruktur muss in **Sprint 2** implementiert sein (vor der Panelisierung). Die builtin Regeln können inkrementell hinzukommen. Supplier-Regeln-Import kommt in **Sprint 1** (beim Katalog-Import).
