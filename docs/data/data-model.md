# Datenmodell
## Facade Planning Engine — MVP

**Version:** 1.0  
**Status:** Draft  
**Datum:** 2026-06-08  

---

## 1. UML-Klassendiagramm (Textform)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          IMPORT CONTEXT                                         │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌──────────────────────┐         ┌──────────────────────┐                     │
│  │    FacadePlan        │         │      PlanPage        │                     │
│  ├──────────────────────┤  1..*   ├──────────────────────┤                     │
│  │ +id: UUID            │────────▶│ +id: UUID            │                     │
│  │ +source_file: Path   │         │ +plan_id: UUID       │                     │
│  │ +file_type: FileType │         │ +page_number: int    │                     │
│  │ +scale: Scale        │         │ +width_mm: float     │                     │
│  │ +created_at: datetime│         │ +height_mm: float    │                     │
│  └──────────────────────┘         └──────────────────────┘                     │
│                                            │ 0..*                               │
│                                            ▼                                    │
│                                  ┌──────────────────────┐                     │
│                                  │    RawGeometry       │                     │
│                                  ├──────────────────────┤                     │
│                                  │ +id: UUID            │                     │
│                                  │ +page_id: UUID       │                     │
│                                  │ +geometry_type: Enum │                     │
│                                  │ +points: List[Point] │                     │
│                                  │ +layer: str          │                     │
│                                  │ +color: str          │                     │
│                                  │ +is_closed: bool     │                     │
│                                  └──────────────────────┘                     │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                          PLANNING CONTEXT (KERN)                                │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌────────────────────────────┐       ┌─────────────────────────┐             │
│  │     FacadeSurface          │       │        Opening          │             │
│  ├────────────────────────────┤ 0..*  ├─────────────────────────┤             │
│  │ +id: FacadeSurfaceId       │──────▶│ +id: UUID               │             │
│  │ +plan_page_id: UUID        │       │ +surface_id: SurfaceId  │             │
│  │ +boundary: Polygon         │       │ +boundary: Polygon      │             │
│  │ +orientation: Orientation  │       │ +opening_type: Enum     │             │
│  │ +status: SurfaceStatus     │       └─────────────────────────┘             │
│  │ +gross_area_mm2: float     │                                                 │
│  │ +net_area_mm2: float       │                                                 │
│  └────────────────────────────┘                                                 │
│                 │                                                               │
│                 │ (Ergebnis von PanelizationJob)                                │
│                 ▼                                                               │
│  ┌────────────────────────────┐       ┌─────────────────────────┐             │
│  │     PanelizationJob        │       │   PanelizationConfig    │             │
│  ├────────────────────────────┤  1    ├─────────────────────────┤             │
│  │ +id: UUID                  │──────▶│ +joint_width_mm: float  │             │
│  │ +surface_ids: List[...]    │       │ +orientation: Enum      │             │
│  │ +catalog_ids: List[UUID]   │       │ +min_panel_width_mm:fl. │             │
│  │ +status: JobStatus         │       │ +min_panel_height_mm:fl.│             │
│  │ +created_at: datetime      │       │ +prefer_full_panels:bool│             │
│  └────────────────────────────┘       └─────────────────────────┘             │
│                 │                                                               │
│                 │ 0..1                                                          │
│                 ▼                                                               │
│  ┌────────────────────────────┐       ┌─────────────────────────┐             │
│  │   PanelizationResult       │       │    PlanningWarning      │             │
│  ├────────────────────────────┤  0..* ├─────────────────────────┤             │
│  │ +job_id: UUID              │──────▶│ +code: str              │             │
│  │ +total_panels: int         │       │ +message: str           │             │
│  │ +full_panels: int          │       │ +severity: Enum         │             │
│  │ +cut_panels: int           │       │ +panel_id: PanelId?     │             │
│  │ +completed_at: datetime    │       └─────────────────────────┘             │
│  └────────────────────────────┘                                                 │
│                 │                                                               │
│                 │ 0..*                                                          │
│                 ▼                                                               │
│  ┌────────────────────────────┐       ┌─────────────────────────┐             │
│  │          Panel             │       │      PanelFormat        │             │
│  ├────────────────────────────┤  1    ├─────────────────────────┤             │
│  │ +id: PanelId               │──────▶│ +catalog_id: UUID       │             │
│  │ +surface_id: SurfaceId     │       │ +format_code: str       │             │
│  │ +position: Point2D         │       │ +width_mm: float        │             │
│  │ +actual_width_mm: float    │       │ +height_mm: float       │             │
│  │ +actual_height_mm: float   │       │ +material: str          │             │
│  │ +is_cut: bool              │       │ +surface_finish: str    │             │
│  │ +cut_reason: CutReason?    │       └─────────────────────────┘             │
│  └────────────────────────────┘                 │                              │
│                                                 │ N:1                          │
│                                                 ▼                              │
│                                    ┌─────────────────────────┐                │
│                                    │    SupplierCatalog      │                │
│                                    ├─────────────────────────┤                │
│                                    │ +id: UUID               │                │
│                                    │ +supplier_name: str     │                │
│                                    │ +catalog_version: str   │                │
│                                    │ +imported_at: datetime  │                │
│                                    └─────────────────────────┘                │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                          VALUE OBJECTS                                          │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐   │
│  │    Scale     │  │   Point2D    │  │   Polygon    │  │   BoundingBox   │   │
│  ├──────────────┤  ├──────────────┤  ├──────────────┤  ├─────────────────┤   │
│  │+numerator:int│  │+x: float     │  │+points:      │  │+min_x: float    │   │
│  │+denominator: │  │+y: float     │  │ List[Point2D]│  │+min_y: float    │   │
│  │  int         │  │              │  │              │  │+max_x: float    │   │
│  │              │  │+distance()   │  │+area()       │  │+max_y: float    │   │
│  │+factor():    │  │+translate()  │  │+bounding_box │  │+width()         │   │
│  │  float       │  │              │  │+contains()   │  │+height()        │   │
│  └──────────────┘  └──────────────┘  │+is_closed()  │  │+intersects()    │   │
│                                       └──────────────┘  └─────────────────┘   │
│                                                                                 │
│  ┌──────────────────┐  ┌──────────────────┐                                   │
│  │  FacadeSurfaceId │  │     PanelId      │                                   │
│  ├──────────────────┤  ├──────────────────┤                                   │
│  │+value: str       │  │+value: str       │                                   │
│  │                  │  │                  │                                   │
│  │Format: FA-NNN    │  │Format:PA-NNN-NNN │                                   │
│  └──────────────────┘  └──────────────────┘                                   │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Enumerationen

```
FileType          PLANNING_STATUS      SURFACE_STATUS
─────────         ───────────────      ──────────────
PDF               PENDING              DETECTED
DXF               RUNNING              CONFIRMED
                  COMPLETED            REJECTED
                  FAILED

ORIENTATION       PANEL_ORIENTATION    CUT_REASON
───────────       ─────────────────    ──────────
NORTH             HORIZONTAL           EDGE
SOUTH             VERTICAL             OPENING
EAST              AUTO                 BOUNDARY
WEST
UNKNOWN

GEOMETRY_TYPE     OPENING_TYPE         WARNING_SEVERITY
─────────────     ────────────         ────────────────
LINE              WINDOW               INFO
POLYLINE          DOOR                 WARNING
POLYGON           VENT                 ERROR
ARC               OTHER
CIRCLE
```

---

## 3. Persistenzstrategie (MVP)

Im MVP wird **dateibasierte Persistenz** verwendet (keine Datenbank). Grund: einfaches Deployment, Offline-Betrieb, keine Infrastrukturabhängigkeit.

### 3.1 Projektdatei-Struktur

```
<project_name>/
  project.json              ← Projektmetadaten, Skalierung
  plans/
    <plan_id>.json          ← FacadePlan + PlanPages
    <plan_id>_geometries.json  ← RawGeometries (kann gross werden)
  surfaces/
    <surface_id>.json       ← FacadeSurface + Openings
  suppliers/
    <catalog_id>.json       ← SupplierCatalog + PanelFormats
  jobs/
    <job_id>.json           ← PanelizationJob + Config + Result
    <job_id>_panels.json    ← Panels (kann gross werden, getrennt)
    <job_id>_audit.jsonl    ← Audit Log (append-only, JSON Lines)
  exports/
    <timestamp>_<job_id>.dxf   ← DXF-Exporte
    <timestamp>_<job_id>_report.txt  ← Prozessberichte
```

### 3.2 Serialisierungsformat

Alle JSON-Dateien verwenden **UTF-8** und folgendes Schema:

```json
{
  "schema_version": "1.0",
  "entity_type": "FacadeSurface",
  "created_at": "2026-06-08T10:30:00Z",
  "data": { ... }
}
```

### 3.3 Erweiterbarkeit zur Datenbank

Das Repository-Pattern isoliert die Persistenzlogik vollständig. Ein späterer Wechsel zu SQLite oder PostgreSQL erfordert nur neue Repository-Implementierungen, keine Änderungen an der Domänenlogik.

---

## 4. Aggregate-Grenzen und Konsistenzregeln

### Aggregat: PlanImport

**Root:** FacadePlan  
**Invarianten:**
- `scale.numerator > 0` und `scale.denominator > 0`
- `pages` ist nicht leer nach Import
- `source_file` existiert zur Import-Zeit

**Transaktionsgrenze:** Laden eines Plans ist atomar — entweder vollständig geladen oder nicht.

---

### Aggregat: FacadeDefinition

**Root:** FacadeSurface  
**Invarianten:**
- `boundary` ist ein geschlossenes Polygon
- Alle `openings` liegen vollständig innerhalb `boundary`
- `id` ist systemweit eindeutig (Format FA-NNN)
- `net_area_mm2 = gross_area_mm2 - sum(opening.area)`

**Transaktionsgrenze:** Änderungen an Surface und Openings sind zusammen konsistent.

---

### Aggregat: PanelizationWork

**Root:** PanelizationJob  
**Invarianten:**
- Im Status COMPLETED: `result` ist nicht null
- Alle Panels liegen innerhalb der zugehörigen FacadeSurface
- Keine zwei Panels überlappen sich (geometrische Invariante)
- Panel.actual_width ≤ Panel.format.width (GR-002)
- Panel.actual_height ≤ Panel.format.height (GR-002)
- Jedes Panel hat eine gültige PanelFormat-Referenz (GR-001)

**Transaktionsgrenze:** Panelisierungsergebnis wird vollständig oder gar nicht gespeichert.

---

## 5. Domain Services — Signaturen

```
GeometryExtractionService
  extract(plan: FacadePlan, page: PlanPage) -> List[RawGeometry]

SurfaceDetectionService
  detect(geometries: List[RawGeometry], scale: Scale) -> List[FacadeSurface]

PanelizationService
  panelize(
    surface: FacadeSurface,
    formats: List[PanelFormat],
    config: PanelizationConfig
  ) -> PanelizationResult

FormatSelectionService
  select_format(
    required_width_mm: float,
    required_height_mm: float,
    available_formats: List[PanelFormat]
  ) -> Optional[PanelFormat]

ValidationService
  validate_surface(surface: FacadeSurface) -> List[PlanningWarning]
  validate_result(result: PanelizationResult) -> List[PlanningWarning]

ExportService
  export_dxf(result: PanelizationResult, path: Path) -> None
  export_report(result: PanelizationResult, path: Path) -> None
```

---

## 6. Datenmigration und Versionierung

- Alle Dateien enthalten `schema_version`
- Migrations-Scripts werden in `src/migrations/` verwaltet
- Bei inkompatiblen Schemaänderungen: neues `schema_version`, Migrationsskript bereitstellen
- MVP: Schema 1.0 ist stabil bis v1.0 Release
