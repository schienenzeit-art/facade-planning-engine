# Domänenmodell
## Facade Planning Engine — MVP

**Version:** 1.0  
**Status:** Draft  
**Datum:** 2026-06-08  

---

**Version:** 1.1 (aktualisiert nach GAP/Risk-Review)

## 1. Domänenübersicht

Die Facade Planning Engine operiert im Fachbereich **Fassadenbau / Metallbau**. Die Kerndomäne ist die **technische Planungsdomäne**: Sie übersetzt geometrische Pläne in eine technisch umsetzbare Panelaufteilung auf Basis realer Lieferantenformate.

### Bounded Contexts (Domänenabgrenzungen)

```
┌──────────────────────────────────────────────────────────────────────┐
│                      FACADE PLANNING ENGINE                          │
│                                                                      │
│  ┌──────────────────┐   ┌────────────────────┐   ┌───────────────┐ │
│  │  PLAN IMPORT     │   │  FACADE PLANNING   │   │  EXPORT       │ │
│  │  CONTEXT         │──▶│  CONTEXT (KERN)    │──▶│  CONTEXT      │ │
│  │                  │   │                    │   │               │ │
│  │ - PDF laden      │   │ - Zonen (neu)      │   │ - DXF Output  │ │
│  │ - Normalisieren  │   │ - Flächen          │   │ - Reports     │ │
│  │ - Geometrie      │   │ - Panels           │   │ - Audit-JSON  │ │
│  │   extrahieren    │   │ - Rules Engine(neu)│   │               │ │
│  │ - Skalieren      │   │ - Panelisierung    │   │               │ │
│  └──────────────────┘   └────────────────────┘   └───────────────┘ │
│                                   ▲                                  │
│                          ┌────────┴────────┐                        │
│                          │  SUPPLIER       │                        │
│                          │  CONTEXT        │                        │
│                          │                 │                        │
│                          │ - Lieferanten   │                        │
│                          │ - Plattenformate│                        │
│                          │ - Lieferanten-  │                        │
│                          │   Regeln (neu)  │                        │
│                          └─────────────────┘                        │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 2. Kernentitäten (Ubiquitous Language)

> **Wichtig:** Diese Begriffe bilden die fachliche Sprache des Systems. Sie werden im Code, in Tests und in der Dokumentation einheitlich verwendet.

### 2.1 FacadePlan (Fassadenplan)

**Definition:** Ein importierter Plan, der eine oder mehrere Fassadenansichten enthält. Entspricht typischerweise einer PDF-Datei.

| Attribut | Typ | Beschreibung | Pflicht |
|----------|-----|-------------|---------|
| `id` | UUID | Eindeutige System-ID | Ja |
| `source_file` | FilePath | Pfad zur Originaldatei | Ja |
| `file_type` | Enum(PDF, DXF) | Importformat | Ja |
| `scale` | Scale | Maßstab (z.B. 1:100) | Ja |
| `created_at` | DateTime | Importzeitpunkt | Ja |
| `pages` | List[PlanPage] | Enthaltene Seiten/Ansichten | Ja |

**Verantwortlichkeiten:**
- Repräsentiert das physische Eingabedokument
- Hält den Maßstab, der auf alle Geometrien angewendet wird
- Aggregatroot des Import-Contexts

---

### 2.2 PlanPage (Planseite / Ansicht)

**Definition:** Eine einzelne Seite oder Ansicht eines Fassadenplans. Enthält die rohen geometrischen Primitive.

| Attribut | Typ | Beschreibung | Pflicht |
|----------|-----|-------------|---------|
| `id` | UUID | Eindeutige ID | Ja |
| `plan_id` | UUID | Verweis auf FacadePlan | Ja |
| `page_number` | int | Seitennummer (1-basiert) | Ja |
| `raw_geometries` | List[RawGeometry] | Extrahierte Rohgeometrien | Ja |
| `width_mm` | float | Seitenbreite in mm (skaliert) | Ja |
| `height_mm` | float | Seitenhöhe in mm (skaliert) | Ja |

---

### 2.3 FacadeSurface (Fassadenfläche)

**Definition:** Eine identifizierte, technisch planbare Fassadenfläche. Entspricht einer zusammenhängenden, rechteckigen oder polygonalen Fassadenansicht mit potenziellen Öffnungen.

**Dies ist die zentrale Entität der Kerndomäne.**

| Attribut | Typ | Beschreibung | Pflicht |
|----------|-----|-------------|---------|
| `id` | FacadeSurfaceId | Eindeutige fachliche ID (z.B. "FA-001") | Ja |
| `plan_page_id` | UUID | Verweis auf Herkunftsseite | Ja |
| `boundary` | Polygon | Aussenkontur der Fläche in mm | Ja |
| `openings` | List[Opening] | Fenster, Türen, Aussparungen | Nein |
| `orientation` | Enum(NORTH, SOUTH, EAST, WEST, UNKNOWN) | Himmelsrichtung (optional) | Nein |
| `net_area_mm2` | float | Nettofläche (abzgl. Öffnungen) in mm² | Berechnet |
| `gross_area_mm2` | float | Bruttofläche ohne Abzüge | Berechnet |
| `status` | Enum(DETECTED, CONFIRMED, REJECTED) | Bestätigungsstatus durch Nutzer | Ja |

**Verantwortlichkeiten:**
- Repräsentiert die zu beplankende Fläche
- Hält Öffnungen, die bei der Panelisierung ausgespart werden
- Aggregatroot des Planning-Contexts
- Kennt ihre eigene Geometrie, kennt aber keine Panels direkt (vermeidet zyklische Abhängigkeit)

---

### 2.4 Opening (Öffnung)

**Definition:** Eine Aussparung innerhalb einer Fassadenfläche (Fenster, Tür, Lüftungsöffnung, sonstige Aussparung).

| Attribut | Typ | Beschreibung | Pflicht |
|----------|-----|-------------|---------|
| `id` | UUID | Eindeutige ID | Ja |
| `surface_id` | FacadeSurfaceId | Verweis auf Fassadenfläche | Ja |
| `boundary` | Polygon | Kontur der Öffnung in mm | Ja |
| `opening_type` | Enum(WINDOW, DOOR, VENT, OTHER) | Art der Öffnung | Nein |

---

### 2.5 SupplierCatalog (Lieferantenkatalog)

**Definition:** Ein importierter Katalog eines Lieferanten mit verfügbaren Plattenformaten.

| Attribut | Typ | Beschreibung | Pflicht |
|----------|-----|-------------|---------|
| `id` | UUID | Eindeutige ID | Ja |
| `supplier_name` | str | Name des Lieferanten | Ja |
| `catalog_version` | str | Version / Datum des Katalogs | Nein |
| `formats` | List[PanelFormat] | Verfügbare Plattenformate | Ja |
| `imported_at` | DateTime | Import-Zeitpunkt | Ja |

---

### 2.6 PanelFormat (Plattenformat)

**Definition:** Ein verfügbares Rohplattenformat eines Lieferanten. Definiert die maximalen Abmessungen, aus denen Panels gefertigt werden können.

**Dies ist ein Value Object** — zwei PanelFormats mit denselben Abmessungen und demselben Lieferanten sind identisch.

| Attribut | Typ | Beschreibung | Pflicht |
|----------|-----|-------------|---------|
| `catalog_id` | UUID | Verweis auf SupplierCatalog | Ja |
| `format_code` | str | Lieferanten-interne Bezeichnung | Ja |
| `width_mm` | float | Breite in mm | Ja |
| `height_mm` | float | Höhe in mm | Ja |
| `material` | str | Material (z.B. "Aluminium 3mm") | Nein |
| `surface_finish` | str | Oberfläche (z.B. "RAL 9010 pulverbeschichtet") | Nein |

**Business Rule Enforcement:**
- width_mm > 0, height_mm > 0 (GR-002)
- Maße in mm (GR-003)

---

### 2.7 PanelizationJob (Panelisierungsauftrag)

**Definition:** Ein Auftrag zur Panelisierung einer oder mehrerer Fassadenflächen. Hält den Kontext einer vollständigen Panelisierungsoperation.

| Attribut | Typ | Beschreibung | Pflicht |
|----------|-----|-------------|---------|
| `id` | UUID | Eindeutige ID | Ja |
| `surface_ids` | List[FacadeSurfaceId] | Zu panelisierende Flächen | Ja |
| `catalog_ids` | List[UUID] | Zu verwendende Lieferantenkataloge | Ja |
| `config` | PanelizationConfig | Konfiguration | Ja |
| `status` | Enum(PENDING, RUNNING, COMPLETED, FAILED) | Status | Ja |
| `result` | PanelizationResult | Ergebnis (wenn abgeschlossen) | Nein |
| `audit_log` | List[AuditEntry] | Entscheidungsprotokoll | Ja |

---

### 2.8 PanelizationConfig (Konfiguration)

**Definition:** Value Object — enthält alle Parameter für eine Panelisierungsoperation.

| Attribut | Typ | Beschreibung | Default |
|----------|-----|-------------|---------|
| `joint_width_mm` | float | Fugenbreite in mm | 0.0 |
| `panel_orientation` | Enum(HORIZONTAL, VERTICAL, AUTO) | Panelausrichtung | AUTO |
| `min_panel_width_mm` | float | Mindestbreite Randpanel | 0.0 |
| `min_panel_height_mm` | float | Mindesthöhe Randpanel | 0.0 |
| `prefer_full_panels` | bool | Vollplatten bevorzugen | True |

---

### 2.9 Panel

**Definition:** Ein einzelnes Panel als Ergebnis der Panelisierung. Repräsentiert eine physisch herstellbare Fassadenplatte.

| Attribut | Typ | Beschreibung | Pflicht |
|----------|-----|-------------|---------|
| `id` | PanelId | Eindeutige fachliche ID (z.B. "PA-001-042") | Ja |
| `surface_id` | FacadeSurfaceId | Zugehörige Fassadenfläche | Ja |
| `format` | PanelFormat | Verwendetes Lieferantenformat | Ja |
| `position` | Point2D | Position (x, y) der linken oberen Ecke in mm | Ja |
| `actual_width_mm` | float | Tatsächliche Breite (≤ format.width_mm) | Ja |
| `actual_height_mm` | float | Tatsächliche Höhe (≤ format.height_mm) | Ja |
| `is_cut` | bool | Handelt es sich um ein zugeschnittenes Panel? | Ja |
| `cut_reason` | Enum(EDGE, OPENING, BOUNDARY) | Warum zugeschnitten? | Wenn is_cut |

---

### 2.10 PanelizationResult (Panelisierungsergebnis)

**Definition:** Das vollständige Ergebnis einer Panelisierungsoperation.

| Attribut | Typ | Beschreibung |
|----------|-----|-------------|
| `job_id` | UUID | Verweis auf PanelizationJob |
| `panels` | List[Panel] | Alle erzeugten Panels |
| `total_panels` | int | Anzahl Panels gesamt |
| `full_panels` | int | Anzahl Vollplatten |
| `cut_panels` | int | Anzahl Zuschnitte |
| `violations` | List[RuleViolation] | Regelverletzungen (ersetzt PlanningWarning) |
| `errors` | List[PanelizationError] | Flächen die nicht panelisiert werden konnten |
| `completed_at` | DateTime | Abschlusszeitpunkt |

---

### 2.11 FacadeZone (Fassadenzone) — NEU

**Definition:** Ein frei definierbarer Planungsbereich, der eine oder mehrere Fassadenflächen gruppiert. Eine Zone kann ein Geschoss, eine Himmelsrichtung, eine Gebäudeachse oder ein beliebiger Planungsbereich sein.

> **Design-Entscheidung (GAP-008):** FacadeZone ist ein organisatorisches Konstrukt ohne eigene Geometrie. Dies vermeidet Komplexität bei überlappenden Zonen und hält das Modell flexibel.

| Attribut | Typ | Beschreibung | Pflicht |
|----------|-----|-------------|---------|
| `id` | FacadeZoneId | Eindeutige fachliche ID (z.B. "FZ-001") | Ja |
| `name` | str | Frei definierbar ("Nordfassade", "EG", "Achse A–C") | Ja |
| `description` | str | Optionale Beschreibung | Nein |
| `surface_ids` | List[FacadeSurfaceId] | Zugeordnete Fassadenflächen | Ja (mind. 1) |
| `panelization_override` | Optional[PanelizationConfig] | Zone-spezifische Konfigurationsüberschreibung | Nein |

**Invarianten:**
- Eine FacadeSurface gehört zu maximal einer FacadeZone (MVP: flache Hierarchie)
- FacadeZone ohne zugeordnete Surfaces ist erlaubt (leer, in Planung)

---

### 2.12 JointConfig (Fugenkonfiguration) — NEU

**Definition:** Value Object — vollständige Konfiguration aller Fugen und Bewegungsfugen für eine Panelisierungsoperation. Ersetzt den einzelnen `joint_width_mm`-Parameter.

> **Design-Entscheidung (GAP-006):** Fugen sind keine optionalen Parameter sondern ein technisches Regelwerk. Horizontale und vertikale Fugen können sich unterscheiden. Bewegungsfugen sind eigenständig konfigurierbar.

| Attribut | Typ | Beschreibung | Default |
|----------|-----|-------------|---------|
| `horizontal_joint_mm` | float | Horizontale Fuge (Querrichtung) | 10.0 |
| `vertical_joint_mm` | float | Vertikale Fuge (Hochrichtung) | 10.0 |
| `expansion_joint_interval_mm` | float | Abstand zwischen Bewegungsfugen | 6000.0 |
| `expansion_joint_width_mm` | float | Breite der Bewegungsfuge | 15.0 |

**Business Rules:**
- `horizontal_joint_mm ≥ 0` (GR-009: Warnung wenn < 8mm)
- `vertical_joint_mm ≥ 0` (GR-009: Warnung wenn < 8mm)
- `expansion_joint_interval_mm > 0` wenn Bewegungsfugen aktiv (GR-008)

---

### 2.13 RuleDefinition (Regeldefinition) — NEU

**Definition:** Value Object — die Definition einer einzelnen Planungsregel. Regeln sind konfigurierbar, aktivierbar/deaktivierbar und können aus Lieferantenkatalogen importiert werden.

| Attribut | Typ | Beschreibung | Pflicht |
|----------|-----|-------------|---------|
| `id` | RuleId | Eindeutige ID (z.B. "GR-001", "SWISSPEARL-002") | Ja |
| `name` | str | Kurzbeschreibung | Ja |
| `description` | str | Vollständige Beschreibung | Nein |
| `severity` | Enum(ERROR, WARNING, INFO) | Schwere der Verletzung | Ja |
| `category` | Enum(GEOMETRIC, FORMAT, JOINT, TECHNICAL, SUPPLIER) | Regelkategorie | Ja |
| `parameters` | dict | Konfigurierbare Parameter der Regel | Ja (kann leer) |
| `is_builtin` | bool | Eingebaut (True) oder importiert (False) | Ja |
| `is_active` | bool | Regel ist aktiv | Ja (default: True) |

---

### 2.14 RuleCatalog (Regelkatalog) — NEU

**Definition:** Entity — enthält alle für ein Projekt aktiven Regeln. Aggregatroot der Rules-Teildomäne. Regeln werden priorisiert (Reihenfolge bestimmt Evaluierungsreihenfolge).

| Attribut | Typ | Beschreibung | Pflicht |
|----------|-----|-------------|---------|
| `id` | UUID | Eindeutige ID | Ja |
| `project_id` | UUID | Zugehöriges Projekt | Ja |
| `rules` | List[RuleDefinition] | Geordnete Regelliste | Ja |

---

### 2.15 RuleViolation (Regelverletzung) — NEU

**Definition:** Value Object — Ergebnis einer Regelprüfung. Ersetzt den bisherigen `PlanningWarning`-Typ.

| Attribut | Typ | Beschreibung |
|----------|-----|-------------|
| `rule_id` | RuleId | Verletzte Regel |
| `rule_name` | str | Regelbezeichnung (denormalisiert für Lesbarkeit) |
| `severity` | Severity | ERROR / WARNING / INFO |
| `message` | str | Beschreibung der Verletzung |
| `context` | dict | Kontext (panel_id, surface_id, position) |
| `suggestion` | str | Konkreter Handlungsvorschlag für den Nutzer |

---

### 2.16 PanelizationError (Panelisierungsfehler) — NEU

**Definition:** Value Object — beschreibt warum eine Fassadenfläche nicht panelisiert werden konnte.

> **Design-Entscheidung (RISK-002):** Fehler sind spezifisch typisiert, nicht generisch. Jeder Fehlertyp hat eine eigene Ursache und Lösungsempfehlung.

| Attribut | Typ | Beschreibung |
|----------|-----|-------------|
| `surface_id` | FacadeSurfaceId | Betroffene Fläche |
| `error_type` | Enum(PE-001, PE-002, PE-003, PE-004) | Fehlertyp |
| `message` | str | Menschenlesbare Fehlerbeschreibung |
| `suggestion` | str | Konkreter Lösungsvorschlag |

**Fehlertypen:**
| Typ | Ursache |
|-----|---------|
| PE-001: NO_FORMAT_FITS | Kein Format passt auf die Fläche |
| PE-002: EDGE_PANEL_TOO_SMALL | Randpanel unterschreitet Mindestmaß |
| PE-003: ALL_PANELS_BLOCKED | Alle Panels durch Öffnungen eliminiert |
| PE-004: SURFACE_TOO_SMALL | Fläche kleiner als kleinstes Format |

---

## 3. Value Objects

Value Objects haben keine eigene Identität — sie sind durch ihre Werte definiert.

| Value Object | Felder | Beschreibung |
|-------------|--------|-------------|
| `Scale` | numerator: int, denominator: int | Maßstab (z.B. 1:100) |
| `Point2D` | x: float, y: float | 2D-Koordinate in mm |
| `Polygon` | points: List[Point2D] | Polygon als Punktliste |
| `BoundingBox` | min_x, min_y, max_x, max_y: float | Achsenparalleles Rechteck |
| `PanelId` | value: str | Validierter Panel-Bezeichner (PA-NNN-NNN) |
| `FacadeSurfaceId` | value: str | Validierter Flächen-Bezeichner (FA-NNN) |
| `FacadeZoneId` | value: str | Validierter Zonen-Bezeichner (FZ-NNN) — NEU |
| `RuleId` | value: str | Regelbezeichner (z.B. "GR-001", "SWISSPEARL-001") — NEU |
| `JointConfig` | horizontal_joint_mm, vertical_joint_mm, expansion_joint_interval_mm, expansion_joint_width_mm | Fugenkonfiguration (ersetzt joint_width_mm) — NEU |
| `ScaleCalibration` | method, reference_points, real_distance_mm, factor | Kalibrierungsdaten für Audit-Trail — NEU |

---

## 4. Domain Services

Domain Services enthalten fachliche Logik, die nicht einer einzelnen Entität zugeordnet werden kann.

### 4.1 GeometryExtractionService
**Kontext:** Import Context  
**Verantwortlichkeit:** Extrahiert geometrische Primitive aus einem FacadePlan und erzeugt RawGeometry-Objekte. Wendet den Maßstab an.

### 4.2 SurfaceDetectionService
**Kontext:** Planning Context  
**Verantwortlichkeit:** Analysiert RawGeometries und identifiziert FacadeSurfaces (geschlossene Polygone, Öffnungen).

### 4.3 PanelizationService
**Kontext:** Planning Context (Kern)  
**Verantwortlichkeit:** Führt die eigentliche Panelisierung durch. Bekommt eine FacadeSurface, einen PanelFormat-Katalog und eine PanelizationConfig und erzeugt eine Liste von Panels.

### 4.4 FormatSelectionService
**Kontext:** Planning Context  
**Verantwortlichkeit:** Wählt aus den verfügbaren PanelFormats das optimale für eine gegebene Position/Fläche aus. Kapselt die Auswahllogik (z.B. Vollplatte bevorzugen, kleinster Zuschnitt).

### 4.5 RuleEngine — NEU (ersetzt ValidationService)
**Kontext:** Planning Context (Rules-Teildomäne)  
**Verantwortlichkeit:** Evaluiert einen RuleCatalog gegen PanelizationResult, Panels oder FacadeSurfaces und erzeugt RuleViolations. Unterscheidet ERROR (blockiert), WARNING (Hinweis) und INFO.

> Der bisherige `ValidationService` wird von der `RuleEngine` abgelöst. Die RuleEngine ist konfigurierbar und lieferantenspezifisch erweiterbar (→ ADR-007).

### 4.6 ExportService
**Kontext:** Export Context  
**Verantwortlichkeit:** Serialisiert PanelizationResult in DXF-Format.

---

## 5. Beziehungsdiagramm

```
FacadePlan
│
├── 1..* PlanPage
│         │
│         └── 1..* RawGeometry (extrahiert, temporär)
│
├── (ergibt) ──▶ FacadeSurface [FacadeSurfaceId]
│                     │
│                     ├── 1..* Opening
│                     │
│                     └── (zugehörig zu) ──▶ FacadeZone [FacadeZoneId]  ← NEU
│                                                 │
│                                                 └── Optional[PanelizationConfig]

PanelizationJob
│
├── ref ──▶ FacadeSurface (1..*)
├── ref ──▶ SupplierCatalog (1..*)
├── ref ──▶ RuleCatalog (1)           ← NEU
├── PanelizationConfig (mit JointConfig)
└── PanelizationResult
          │
          ├── Panel (0..*) ──▶ PanelFormat ──▶ SupplierCatalog
          ├── RuleViolation (0..*) ──▶ RuleDefinition  ← NEU
          └── PanelizationError (0..*) [PE-001..PE-004] ← NEU

RuleCatalog [projekt-weit]  ← NEU
│
└── 1..* RuleDefinition
            ├── Builtin: GR-001..GR-010
            └── Supplier: SWISSPEARL-001, ALUCOBOND-001, ...
```

---

## 6. Aggregate-Grenzen

| Aggregat | Root | Enthält | Invarianten |
|---------|------|---------|------------|
| PlanImport | FacadePlan | PlanPage, RawGeometry | Mindestens 1 Seite; Scale definiert |
| FacadeDefinition | FacadeSurface | Opening | ID eindeutig; Boundary valid; Öffnungen innerhalb Boundary |
| FacadeOrganization | FacadeZone | List[FacadeSurfaceId] | ID eindeutig; mind. 0 Surfaces; 1 Surface → max. 1 Zone — **NEU** |
| SupplierData | SupplierCatalog | PanelFormat, List[RuleDefinition] | Mind. 1 Format; Maße > 0; optionale Lieferantenregeln — **NEU: Regeln** |
| ProjectRules | RuleCatalog | List[RuleDefinition] | RuleId eindeutig; Basisregeln GR-001..GR-010 immer aktiv — **NEU** |
| PanelizationWork | PanelizationJob | PanelizationResult, Panel, RuleViolation, PanelizationError, AuditEntry | Panels innerhalb Surface; Keine Überlappungen; JointConfig valid |

---

## 7. Ubiquitous Language — Glossar

| Begriff (DE) | Begriff (EN, Code) | Definition |
|-------------|-------------------|-----------|
| Fassadenfläche | FacadeSurface | Planbare Fassadeneinheit mit Umriss und Öffnungen |
| Fassadenzone | FacadeZone | Organisatorische Gruppierung von Flächen (Geschoss, Achse, Himmelsrichtung) — **NEU** |
| Panel | Panel | Einzelne herstellbare Fassadenplatte |
| Rohplatte | PanelFormat | Vom Lieferanten verfügbares Maximalformat |
| Lieferant | Supplier | Hersteller/Lieferant von Fassadenpaneelen |
| Maßstab | Scale | Verhältnis Plan zu Realität |
| Öffnung | Opening | Fenster, Tür oder sonstige Aussparung in Fassade |
| Laibung | Reveal | Tiefe einer Öffnung (v1.1: reveal_depth_mm) |
| Fuge | Joint | Abstand/Übergang zwischen Panels |
| Bewegungsfuge | ExpansionJoint | Dilatationsfuge für thermische Ausdehnung, alle ~6m — **NEU** |
| Regelverletzung | RuleViolation | Ergebnis einer fehlgeschlagenen Regelprüfung — **NEU** |
| Regelkatalog | RuleCatalog | Projektspezifische Sammlung aktiver Planungsregeln — **NEU** |
| Panelisierung | Panelization | Prozess der automatischen Aufteilung in Panels |
| Panelaufteilung | PanelLayout | Ergebnis der Panelisierung |
| Zuschnitt | CutPanel | Nicht-vollständige Platte, zugeschnitten |
| Vollplatte | FullPanel | Platte in Originalgrösse des Formats |
| Zwei-Punkte-Kalibrierung | TwoPointCalibration | Massstabsdefinition via zwei Referenzpunkte und bekannter Realdistanz — **NEU** |
