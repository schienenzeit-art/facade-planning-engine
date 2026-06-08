# MVP Definition
## Facade Planning Engine v1.0

**Version:** 1.0  
**Datum:** 2026-06-08  
**Status:** Finalisiert nach GAP/Risk-Review  

> Diese Definition ist verbindlich. Änderungen erfordern explizite Entscheidung des Projektleiters und Aktualisierung dieser Datei.

---

## MVP ist exakt dies

### Input-Fähigkeiten

| Feature | Detail |
|---------|--------|
| PDF-Import | Vektorbasierte PDFs aus AutoCAD 2018+, Revit 2019+, ArchiCAD 25+ |
| Generator-Erkennung | Automatisch aus PDF-Metadaten; WARNING bei unbekanntem Generator |
| Mehrseitige PDFs | Jede Seite als separate Ansicht verarbeitbar |
| Layer-Listing | Alle verfügbaren Layer aus dem PDF werden aufgelistet |
| Katalog-Import JSON | `{"supplier": "...", "formats": [{...}], "rules": [...]}` |
| Katalog-Import CSV | Tabulatorische Formate mit width_mm, height_mm, format_code |
| Lieferantenregeln | Regeln aus Katalog werden automatisch in RuleCatalog übernommen |

### Verarbeitungs-Fähigkeiten

| Feature | Detail |
|---------|--------|
| Skalierung: Zwei-Punkte | `--p1 x,y --p2 x,y --real-mm DIST` |
| Skalierung: Direkteingabe | `--scale 1:100` |
| Geometrieextraktion | Linien, Polylines, geschlossene Polygone mit Layer-Attributen |
| Koordinatennormalisierung | Generator-spezifisch (AutoCAD, Revit, ArchiCAD, Generic) |
| Flächenerkennung | Geschlossene Polygone als Kandidaten; Toleranz konfigurierbar |
| Öffnungserkennung | Polygone innerhalb von Flächen als Holes erkannt |
| Öffnungstypen | WINDOW, DOOR, VENT, OTHER — manuell oder heuristisch zuweisbar |
| Fassadenzonen | Freie Gruppierung: `facade zone create "Nordfassade"` |
| Flächenbestätigung | DETECTED → CONFIRMED (explizit) oder REJECTED |
| Panelisierung: Grid-Algorithmus | Regelmässiges Grid, Vollplatten bevorzugt |
| Panelisierung: Fugen | Horizontale + vertikale Fugen separat konfigurierbar |
| Panelisierung: Bewegungsfugen | Alle expansion_joint_interval_mm (default: 6000mm) |
| Panelisierung: Öffnungen | TRIM (default) oder DROP — kein Panel überdeckt Öffnung |
| Panelisierung: Mindestmaße | min_panel_width_mm + min_panel_height_mm für Randpanele |
| Format-Auswahl | Grösstes passendes Format; Vollplatte vor Zuschnitt bevorzugt |
| Zonenbasierte Panelisierung | `facade panelize run --zone FZ-001` mit optionalem Config-Override |
| Rules Engine | Builtin GR-001..GR-010 + Lieferantenregeln |
| Fehlerbehandlung | PE-001..PE-004: Fail-Per-Surface; Job läuft weiter |

### Output-Fähigkeiten

| Feature | Detail |
|---------|--------|
| DXF-Export | AC1027 (AutoCAD 2013+), INSUNITS=mm |
| DXF-Layer | FACADE_<SurfaceId>_PANELS, _BOUNDARY, _OPENINGS, _LABELS |
| DXF-Entities | LWPOLYLINE für Geometrie, MTEXT für Labels |
| Audit-JSON | Vollständig: config_snapshot, scale_calibration, format_selection_log |
| Prozessreport | Textformat: Statistik, Warnungen, Fehlerliste |

### CLI-Befehle (vollständig)

```
facade project create <name>
facade project info

facade plan import <file> [--scale 1:100]
facade plan scale <id> [--p1 x,y --p2 x,y --real-mm dist | --scale 1:100]
facade plan layers <id>
facade plan list
facade plan show <id>

facade surface detect --plan <id> [--layer <name>]
facade surface confirm <id> [--zone <zone-id>]
facade surface reject <id> [--reason <text>]
facade surface list [--plan <id>]
facade surface show <id>

facade zone create <name> [--description <text>]
facade zone list
facade zone assign <zone-id> <surface-id>

facade catalog import <file>
facade catalog list
facade catalog show <id>

facade rules list
facade rules disable <rule-id> [--reason <text>]
facade rules configure <rule-id> [--param key=value ...]

facade panelize run [--surface <id>...] [--zone <id>...] --catalog <id>...
    [--joint-h FLOAT] [--joint-v FLOAT] [--expansion-interval FLOAT]
    [--orientation horizontal|vertical|auto]
    [--min-width FLOAT] [--min-height FLOAT]
    [--opening-strategy trim|drop]
facade panelize list
facade panelize show <id>

facade export dxf <job-id> [--output <path>]
facade export report <job-id> [--output <path>]
```

---

## Explizit NICHT im MVP

### Keine GUI / keine visuellen Werkzeuge

| Ausgeschlossen | Begründung |
|----------------|-----------|
| Grafische Benutzeroberfläche | CLI-first — GUI ist v2.0 |
| Interaktive PDF-Ansicht (Punkte klicken für Kalibrierung) | Erfordert GUI-Framework; aufwändig |
| DXF-Vorschau / Viewer | Externe CAD-Software übernimmt diese Rolle |
| Web-Interface / Browser-App | Separate Infrastruktur; nicht im Scope |

### Keine erweiterten Algorithmen

| Ausgeschlossen | Begründung |
|----------------|-----------|
| Materialoptimierungs-Algorithmus (Verschnitt minimieren) | Komplex; Optimierungsziele noch unklar |
| Nicht-rechteckige Fassadenflächen | Grid-Algorithmus nur für Rechtecke; v1.1 |
| Gebogene / geschwungene Fassaden | Fundamentale Algorithmusänderung erforderlich |
| Panelisierung mit mehreren verschiedenen Formaten (Mix) | MVP: ein dominantes Format pro Zone; v1.1 |
| Automatische Massstabserkennung (OCR) | Unzuverlässig; v1.1 |

### Keine CAD-Inputs ausser PDF

| Ausgeschlossen | Begründung |
|----------------|-----------|
| DXF-Import | v1.1 — Architektur vorbereitet (Port vorhanden) |
| DWG-Import | v2.0 — Lizenzfrage (ODA File Converter) ungeklärt |
| IFC-Import | v3.0 — BIM-Integration, vollständig anders |
| SVG-Import | Nicht relevant für Fassadenplanung |

### Keine ingenieur-technischen Berechnungen

| Ausgeschlossen | Begründung |
|----------------|-----------|
| Statik / Tragwerksplanung | Eigenständige Fachdisziplin |
| Befestigungspunkte / Anker-Berechnung | Erfordert Unterkonstruktion-Modell |
| Unterkonstruktions-Generierung | v2.0 |
| Thermische Ausdehnung berechnen (Swisspearl-Formel) | Lieferantenregel als Warnung; Berechnung v2.0 |
| Windlast / Erdbebensicherheit | Statik — Out of Scope |

### Keine Betriebssystem-Integration

| Ausgeschlossen | Begründung |
|----------------|-----------|
| Mehrbenutzer-Betrieb / Netzwerk | Lokales CLI-Tool |
| Datenbank-Backend | Dateibasiert bleibt bis v2.0 |
| Cloud-Speicher / Sync | Keine Infrastruktur im Scope |
| Ausschreibungsdokumente | Separate Domäne |
| Kostenberechnung | Keine Preislogik |
| BIM-Integration (IFC, Revit-Link) | v3.0 |
| Produktionsdaten / CNC-Export | v2.0+ |

---

## Was ist "Phase 2" (Post-MVP)

### v1.1 (direkt nach MVP-Stabilisierung)

| Feature | Hintergrund |
|---------|------------|
| DXF/DWG-Import | Architektur vorbereitet; wichtiger Wunsch der Nutzer |
| Nicht-rechteckige Fassadenflächen | Häufig in der Praxis (L-Form, Giebel) |
| Automatische Maßstabserkennung (Maßstabsbalken-OCR) | Komfort-Feature |
| Gemischte Panelformate pro Zone | Mehr Flexibilität in der Planung |
| Per-Zone Panelausrichtung | Kleine Erweiterung; hoher Nutzwert |

### v2.0 (Mittelfristig)

| Feature | Hintergrund |
|---------|------------|
| Materialoptimierung (Verschnitt-Minimierung) | Wirtschaftlichkeit |
| Unterkonstruktions-Generierung | Logische Erweiterung nach Panelisierung |
| Befestigungspunkte (Anker-Muster) | Systemspezifisch (Swisspearl, Alucobond) |
| Thermische Ausdehnung (Formelberechnung) | Genauere Fugenplanung |
| SQLite-Backend (statt JSON-Dateien) | Performance + Multi-Projekt-Verwaltung |

### v3.0 (Langfristig)

| Feature | Hintergrund |
|---------|------------|
| BIM-Integration (IFC-Import) | Grosses Marktpotenzial |
| GUI (Electron oder Web) | Breiterer Nutzerkreis |
| Produktionsdaten / CNC-Export | Fertigung direkt aus Planung |
| Ausschreibungsdokumente | Vollständiger Planungsworkflow |
| Kosten-/Mengenermittlung | Angebotsplanung |
