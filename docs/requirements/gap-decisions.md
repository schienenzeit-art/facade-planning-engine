# GAP & Risk Decision Register
## Facade Planning Engine — MVP

**Version:** 1.1  
**Status:** Review Complete  
**Datum:** 2026-06-08  
**Reviewer:** Senior Software Architect / Co-Projektleiter  

> Dieses Dokument ist die autorisierte Entscheidungsgrundlage für BRS, SRS und Architektur.  
> Alle Entscheidungen hier überschreiben frühere Arbeitsstände.

---

## Bewertungsmethode

Für jeden Punkt: **Entscheidung übernommen / modifiziert / ersetzt** + Begründung + Auswirkungen auf SRS / Domäne / Architektur.

---

## GAP-001: PDF-Unterstützung

### Entscheidung des Projektteams
Fokus auf Vektordaten. Unterstützte Generatoren: AutoCAD, Revit, ArchiCAD. Raster/Scan/Illustrator explizit ausgeschlossen.

### Architekt-Bewertung: **Modifiziert — wichtige technische Ergänzungen**

Die grundsätzliche Entscheidung ist **korrekt und notwendig**. Jedoch fehlen drei kritische technische Punkte:

**1. Der eigentliche Risikofaktor sind nicht PDF-Versionen, sondern Koordinatensystemunterschiede der Generatoren:**

| Generator | Koordinatenursprung | Y-Achse | Layer-Struktur |
|-----------|-------------------|---------|----------------|
| AutoCAD PDF | Seitenunterseite links | Aufwärts | Exakt nach AutoCAD-Layern |
| Revit PDF | Projektursprung variiert | Aufwärts | Nach Kategorie/Ansicht |
| ArchiCAD PDF | Seitenunterseite links | Aufwärts | Nach ArchiCAD-Layern |

→ Ein **PDFNormalizer-Layer** in der Infrastruktur muss Koordinatensysteme vereinheitlichen, bevor Geometrien in Domänenobjekte übertragen werden. Dies ist architektonisch eigenständig zu planen.

**2. "Vektorbasiert" ist keine zuverlässige Selbstauskunft:**
Ein PDF kann Vektordaten für den Planrahmen/Schriftfeld und Rasterdaten für den eigentlichen Plan enthalten. Das System muss die Geometrie-Schichten pro Seite analysieren, nicht das PDF als Ganzes klassifizieren.

**3. Illustrator-Ausschluss ist korrekt — aber aus anderem Grund:**
Illustrator-PDFs sind technisch Vektordaten, aber ihre Geometry-Encoding unterscheidet sich fundamental von CAD-Exportpfaden. Wichtiger: Sie enthalten keine Layer-Struktur im CAD-Sinne. Der Ausschluss ist richtig, muss aber mit klarem Fehlertext kommuniziert werden.

### Auswirkungen

**SRS:** FR-001 erhält Sub-Anforderungen für Generatoren-Validierung und Fehlermeldungen.  
**Architektur:** Neue Komponente `PDFNormalizer` im Infrastructure-Layer (zwischen Raw-Parsing und GeometryMapper).  
**ADR-002:** Wird aktualisiert mit Generator-spezifischen Normalisierungsanforderungen.

### Finalisierte Entscheidung GAP-001

```
Das System verarbeitet ausschliesslich vektorbasierte PDF-Dateien aus 
technischen CAD-Werkzeugen. Unterstützte Generatoren (MVP):
  - AutoCAD 2018+ PDF-Export
  - Revit 2019+ PDF-Export  
  - ArchiCAD 25+ PDF-Export

Explizit nicht unterstützt (MVP):
  - Scan-PDFs (Rasterbild)
  - Bild-PDFs (JPEG/PNG in PDF)
  - Illustrator-PDFs (kreative Vektordaten)
  - Unbekannte oder nicht getestete Generatoren

Fehlermeldung bei unbekanntem Generator:
  "PDF-Quelle nicht erkannt oder nicht unterstützt. 
   Bitte aus AutoCAD, Revit oder ArchiCAD exportieren."

Architektonische Massnahme:
  PDFNormalizer normalisiert Koordinatensysteme je Generator.
```

---

## GAP-002: Skalierung

### Entscheidung des Projektteams
Zwei-Punkte-Kalibrierung: Nutzer wählt zwei Punkte, gibt reale Distanz ein.

### Architekt-Bewertung: **Übernommen — mit CLI-Workflow-Präzisierung**

**Die Entscheidung ist fachlich und technisch die robusteste Lösung für ein CLI-Tool.**

Begründung: OCR-basierte Maßstabserkennung ist bei technischen Zeichnungen fehleranfällig (verschiedene Schriften, Maßlinien, Skalierungen in Schriftfeld). Die manuelle Zwei-Punkte-Kalibrierung ist in der Praxis von professionellen CAD-Werkzeugen (AutoCAD SCALE, MicroStation) bewährt.

**Kritischer Ergänzungsbedarf: CLI-Workflow ist bisher nicht spezifiziert.**

Im CLI-Kontext ohne grafische Darstellung muss der Nutzer Koordinaten textbasiert angeben. Empfohlener Workflow:

```bash
# Schritt 1: Plan importieren → extrahierte Geometrien als SVG/ASCII-Preview ausgeben
facade plan import plan.pdf

# Schritt 2: Skalierung definieren via bekannte Referenzstrecke
# Option A: Koordinaten direkt (wenn Nutzer Koordinaten aus dem Plan kennt)
facade plan scale <plan-id> --p1 0,0 --p2 1500,0 --real-mm 1500

# Option B: Referenzdistanz + Pixel-/Einheitengrösse (wenn nur Massstab bekannt)
facade plan scale <plan-id> --scale 1:100

# Option C: Interaktiver Modus (gibt ASCII-Koordinatengitter aus)
facade plan scale <plan-id> --interactive
```

**Validierungsregeln für Skalierung:**
- Referenzpunkte müssen sich unterscheiden (p1 ≠ p2)
- Reale Distanz muss > 0 sein
- Kalibrierter Massstab wird im Audit-Log gespeichert
- Neu-Kalibrierung invalidiert alle abhängigen Geometrie-Berechnungen (→ Warnung)

**Neue Anforderung (aus Schweizer Praxis):**
PDFs aus AutoCAD enthalten häufig einen Massstabsbalken im Schriftfeld. Für v1.1 (nicht MVP): automatische Erkennung des Massstabsbalkens als optionale Kalibrierungshilfe.

### Finalisierte Entscheidung GAP-002

```
Primäre Skalierungsmethode: Zwei-Punkte-Kalibrierung (MVP)
  - Nutzer definiert zwei Referenzpunkte via Koordinaten
  - Nutzer gibt bekannte reale Distanz in mm ein
  - System berechnet Skalierungsfaktor
  
Sekundäre Methode: Direkteingabe Massstab (z.B. 1:100)
  - Nur wenn Massstab aus dem Plan bekannt ist
  
Nicht im MVP: Automatische OCR-Massstabserkennung
Nicht im MVP: Massstabsbalken-Erkennung

Alle Kalibrierungsdaten werden im Audit-Log erfasst.
```

---

## GAP-003: Öffnungen (Fenster, Türen, Aussparungen)

### Entscheidung des Projektteams
Öffnungen sind Kernbestandteil. Panels dürfen Öffnungen nicht ignorieren oder überschneiden.

### Architekt-Bewertung: **Erweitert — kritische fachliche Regeln fehlen**

Die Entscheidung ist korrekt. Es fehlen jedoch vier in der Schweizer Fassadenpraxis essentielle Regeln:

**Fehlende Regel 1: Mindestrandabstand Panel zu Öffnungsrand**

In der Praxis (SIA 331, Hersteller-Verlegeanleitungen) darf ein Panel nicht bündig an eine Öffnung heranreichen. Es gibt einen technischen Mindestrand (typisch 30–100 mm je nach System):

```
Neue Business Rule (GR-006):
Der Abstand zwischen Panelkante und Öffnungsrand muss ≥ min_opening_clearance_mm sein.
Default: 0mm (neutral/nicht erzwungen im MVP), konfigurierbar.
```

**Fehlende Regel 2: Mindestpanelgrösse bei Öffnungsschnitt**

Ein Panel das durch eine Öffnung auf eine Restbreite von z.B. 50mm reduziert wird, ist in der Realität nicht herstellbar:

```
Neue Business Rule (GR-007):
Ein durch eine Öffnung zugeschnittenes Panel muss nach Zuschnitt 
≥ min_panel_width_mm und ≥ min_panel_height_mm einhalten.
Unterschreitet es diese Grenze → Panel wird entfernt (Öffnungsrand ist Panelgrenze).
```

**Fehlende Regel 3: Öffnungsrandbehandlung**

Was passiert am Öffnungsrand? Es gibt zwei Strategien:
- **TRIM:** Panel wird auf die Öffnungsgrenze zugeschnitten (Restpanel)
- **DROP:** Panel fällt weg wenn es von einer Öffnung geschnitten wird

Empfehlung MVP: TRIM als Standard, DROP als Konfigurationsoption.

**Fehlende Überlegung: Laibungsverkleidung (explizit für v1.1)**

In der Schweizer Fassadenpraxis sind Fenster-/Türlaibungen oft verkleidet. Diese sind geometrisch eigenständige Flächen. Dies ist kein MVP-Scope, muss aber als Extension Point im Domänenmodell vorgesehen sein (Opening kann eine Tiefe haben: `reveal_depth_mm`).

### Finalisierte Entscheidung GAP-003

```
Öffnungen werden als Aussparungen in FacadeSurface modelliert.
Panels dürfen Öffnungen nicht überlappen.

Neue Business Rules:
  GR-006: Mindestrandabstand Panel zu Öffnung (konfigurierbar, default 0mm)
  GR-007: Minimalmaß für Panels nach Öffnungsschnitt (sonst: Panel entfernt)

Öffnungsrandstrategie: TRIM (Standard), DROP (konfigurierbar)

Extension Point (v1.1): reveal_depth_mm für Laibungsverkleidungen
```

---

## GAP-004: DXF-Version

### Entscheidung des Projektteams
DXF AC1027 (AutoCAD 2013+).

### Architekt-Bewertung: **Vollständig übernommen — technische Detailspezifikation ergänzt**

AC1027 ist die richtige Wahl. Drei technische Ergänzungen für die Implementierung:

**DXF-Entity-Wahl:**
- Panels → `LWPOLYLINE` (leichtgewichtig, effizient, alle modernen CAD-Tools unterstützen es)
- Panel-Labels → `MTEXT` (statt TEXT, da Unicode-sicher)
- Flächen-Umrisse → `LWPOLYLINE` mit anderem Layer
- Öffnungen → `LWPOLYLINE` mit eigenem Layer (z.B. `FACADE_FA-001_OPENINGS`)

**UNITS-Einstellung:**
DXF muss explizit `UNITS = 4` (Millimeter) setzen. Ohne diese Einstellung interpretiert AutoCAD die Koordinaten als Einheitenlos — kritischer Fehler.

**Layer-Namenskonvention:**
```
FACADE_<SurfaceId>_BOUNDARY    ← Fassadenumriss
FACADE_<SurfaceId>_PANELS      ← Alle Panels
FACADE_<SurfaceId>_OPENINGS    ← Öffnungen
FACADE_<SurfaceId>_LABELS      ← Panel-IDs als Text
FACADE_OVERVIEW                ← Gesamtübersicht
```

### Finalisierte Entscheidung GAP-004

```
DXF-Version: AC1027 (AutoCAD 2013+)
Entities: LWPOLYLINE (Geometrie), MTEXT (Labels)
Units: INSUNITS = 4 (Millimeter) — zwingend
Layer-Naming: FACADE_<SurfaceId>_<TYPE>
AutoCAD LT: vollständig kompatibel
```

---

## GAP-005: Fassadenflächenerkennung

### Entscheidung des Projektteams
Keine vollständige Automatik im MVP. Nutzer kann Flächen/Layer auswählen und Zonen definieren.

### Architekt-Bewertung: **Übernommen — mit kritischer Workflow-Ergänzung und FacadeZone-Integration**

**Korrekte Entscheidung für MVP.** Vollautomatische Klassifikation ("was ist Fassade, was ist Dach?") ist KI/ML-Territorium und kein MVP-Scope.

**Kritische Workflow-Ergänzung für CLI:**
Der Nutzer muss die verfügbaren Layer des PDFs einsehen können, bevor er eine Auswahl trifft:

```bash
# Workflow:
facade plan layers --plan <id>
# Output: Tabelle aller Layer mit Farbe, Anzahl Geometrien, Beispielobjekte

facade surface detect --plan <id> --layer "A-FASSADE" --layer "A-FASSADE-OEFFNUNG"
# Oder: alle Flächen vorschlagen, User bestätigt/verwirft einzeln

facade surface list --plan <id>   # Liste detektierter Flächen
facade surface confirm FA-001
facade surface reject FA-002 --reason "Dachfläche, kein Fassadenelement"
```

**Ergänzung: FacadeZone (aus GAP-008) bereits hier einführen:**
Flächen werden direkt einer Zone zugeordnet beim Bestätigen:
```bash
facade surface confirm FA-001 --zone "Nordfassade EG"
```

**Risiko: PDFs ohne Layer-Struktur**
AutoCAD-PDFs exportieren typischerweise Layer. Revit-PDFs können layerlos sein (alle Geometrie auf einem Layer). Wenn keine Layer vorhanden: alle geschlossenen Polygone werden angeboten, Nutzer wählt manuell.

### Finalisierte Entscheidung GAP-005

```
MVP: Semi-automatische Flächenerkennung
  - System erkennt geschlossene Polygone als Kandidaten
  - Nutzer kann nach Layer filtern (CLI: Layer-Liste anzeigen)
  - Nutzer bestätigt/verwirft Flächen
  - Flächen werden beim Bestätigen einer FacadeZone zugeordnet

Fallback (layerlose PDFs): Alle geschlossenen Polygone als Kandidaten anbieten
```

---

## GAP-006: Fugen

### Entscheidung des Projektteams
Default-Fuge 10mm, projektbezogen konfigurierbar. Hintergrund Swisspearl/ALUCOBOND.

### Architekt-Bewertung: **Erweitert — Fugen müssen Teil des Regelwerks werden, nicht nur ein Parameter**

Die Entscheidung ist fachlich richtig, aber **architektonisch zu schwach modelliert**. Fugen sind in der Schweizer Fassadenpraxis ein technisches Regelwerk, nicht nur ein einfacher Konfigurationswert.

**Kritische Erweiterungen:**

**1. Unterscheidung horizontale/vertikale Fuge:**
Viele Systeme haben unterschiedliche horizontale und vertikale Fugenmaße:
- Swisspearl: horizontal 8mm, vertikal 8mm (symmetrisch)
- ALUCOBOND: abhängig von Systemhöhe und thermischer Ausdehnung
- Anodisiertes Aluminium: typisch 10-12mm wegen Oxidschicht-Bewegung

```
Neu: JointConfig statt einfachem joint_width_mm
  - horizontal_joint_mm: float (Querrichtung)
  - vertical_joint_mm: float (Hochrichtung)
  - default: beide = 10mm
```

**2. Bewegungsfugen (Dilatationsfugen) — PFLICHT:**

Dies ist die wichtigste fehlende Anforderung in der gesamten bisherigen Dokumentation.

Bei Fassadenpaneelen aus Metall/Verbundmaterialien entstehen durch thermische Ausdehnung Bewegungen. Bei zu langen Panelreihen ohne Unterbrechung entstehen Schäden.

Typische Regel (SIA 331 / Herstellervorgaben):
- Vertikale Bewegungsfugen: alle 6–8 Meter (abhängig von Material)
- Horizontale Bewegungsfugen: alle 3–4 Stockwerke (ca. 9–12m)
- Breite: mindestens 15–20mm (Swisspearl: 15mm)

```
Neue Business Rule (GR-008):
Vertikale Dilatationsfuge alle expansion_joint_interval_mm (default: 6000mm).
Horizontale Dilatationsfuge alle h_expansion_joint_interval_mm (default: 9000mm).
Fugenbreite: expansion_joint_width_mm (default: 15mm).
```

→ Diese Regel muss zwingend im Rules-Engine-Katalog erscheinen.

**3. Fuge ist OBLIGATORISCH, nicht optional:**

Der bisherige Default von "0mm" (aus dem ursprünglichen SRS) ist fachlich **falsch**. Es gibt keine reale Fassade ohne Fugen. Empfehlung: Minimum-Fuge = 8mm; System warnt wenn Fuge < 8mm gesetzt wird.

### Finalisierte Entscheidung GAP-006

```
Fuge ist obligatorischer Bestandteil der Panelisierung.
Minimum-Fuge: 8mm (Warnung wenn unterschritten).
Default: horizontal 10mm, vertikal 10mm.

Neue JointConfig (Value Object):
  horizontal_joint_mm: float = 10.0
  vertical_joint_mm: float = 10.0
  expansion_joint_interval_mm: float = 6000.0  # Bewegungsfuge
  expansion_joint_width_mm: float = 15.0

Neue Business Rules:
  GR-008: Bewegungsfugen alle expansion_joint_interval_mm
  GR-009: Fugengrösse ≥ 8mm (Warnung wenn unterschritten)

Teil des Rules-Engine-Katalogs (→ RISK-004).
```

---

## GAP-007: Panelausrichtung

### Entscheidung des Projektteams
Hochformat / Querformat / Automatisch. AUTO = spätere Optimierung.

### Architekt-Bewertung: **Übernommen mit einer Präzisierung**

Korrekte Entscheidung. Eine wichtige Ergänzung:

**AUTO-Semantik für MVP muss definiert sein:**
Wenn AUTO gewählt wird, braucht das System eine fallback-Strategie (nicht "nichts tun"). Empfehlung:
- AUTO MVP: Wählt die Ausrichtung die mehr Vollplatten ergibt (schnell berechenbar)
- AUTO v1.1: Vollständige Optimierung (Materialminimierung)

**Zusätzliche Überlegung: Per-Zone-Konfiguration**
In der Praxis können verschiedene Fassadenabschnitte unterschiedliche Ausrichtungen haben (z.B. Erdgeschoss: Hochformat, Obergeschoss: Querformat). FacadeZone sollte eine eigene Ausrichtungskonfiguration tragen können.

### Finalisierte Entscheidung GAP-007

```
Panelausrichtung: HORIZONTAL | VERTICAL | AUTO
AUTO-MVP: Ausrichtung mit mehr Vollplatten wird gewählt
Per-FacadeZone konfigurierbar (v1.1)
Konfiguration in PanelizationConfig (pro Job) und optional per FacadeZone
```

---

## GAP-008: Mehrgeschossigkeit — FacadeZone

### Entscheidung des Projektteams
Neue Entität FacadeZone: flexible Gruppierung (Zone = gesamte Fassade, Gebäudeteil, Achse, Geschoss, beliebiger Bereich). Keine Fixierung auf "Geschoss".

### Architekt-Bewertung: **Vollständig übernommen — hervorragende Abstraktion — Domänenmodell-Update nötig**

**Das ist die stärkste fachliche Entscheidung in diesem Review-Dokument.** Die Entscheidung gegen eine hard-codierte "Geschoss"-Entität ist architektonisch richtig: Sie hält das Domänenmodell offen für verschiedene Planungsparadigmen (nach Himmelsrichtung, nach Materialzone, nach Verkleidungsart).

**Integration ins Domänenmodell:**

```
FacadeZone
├── id: FacadeZoneId (FZ-001)
├── name: str ("Nordfassade", "EG", "Achse A-C")
├── description: str
├── surfaces: List[FacadeSurfaceId] (enthaltene Flächen)
└── panelization_config: Optional[PanelizationConfig] (Zone-spezifisch überschreiben)

Beziehung:
FacadeZone (1) ──── (0..*) FacadeSurface
```

**Wichtige Design-Entscheidung: FacadeZone ist ein Organisationskonstrukt, keine Geometrie.**
Sie trägt keine eigene Boundary. Sie gruppiert Flächen. Dies verhindert Komplexität bei überlappenden Zonen oder Flächen die zu mehreren Zonen gehören könnten.

**Bewusste MVP-Einschränkung: Flache Hierarchie.**
Keine Zone-in-Zone-Hierarchie im MVP. Eine Fläche gehört zu maximal einer Zone.

### Finalisierte Entscheidung GAP-008

```
Neue Entität: FacadeZone
  - id: FacadeZoneId (FZ-NNN)
  - name: frei definierbar (kein fest codiertes "Geschoss")
  - surfaces: Referenzen auf FacadeSurface
  - config: Optional[PanelizationConfig] für Zone-spezifische Überschreibung

Beziehungsregel: FacadeSurface kann zu 0..1 FacadeZone gehören.
MVP: flache Hierarchie (keine Zone-Hierarchie).
```

---

## GAP-009: Performance-Definition

### Entscheidung des Projektteams
Performance nicht über Dateigrösse (MB), sondern über Geometriekomplexität definieren.

### Architekt-Bewertung: **Vollständig übernommen — konkrete Grenzwerte ergänzt**

**Korrekte und professionelle Entscheidung.** MB ist kein sinnvolles Mass für Verarbeitungsperformance — ein 5MB-PDF kann 10 oder 10.000 Geometrieobjekte enthalten.

**Konkrete Projektgrössenklassen (basierend auf Schweizer Fassadenbaupraxis):**

| Klasse | Geometrieobjekte | Typisches Szenario | Panels erwartet |
|--------|-----------------|-------------------|----------------|
| Klein | < 2.000 | Einfamilienhaus, kleine Gewerbefassade | < 100 |
| Mittel | 2.000–20.000 | Mehrfamilienhaus, Bürogebäude | 100–500 |
| Gross | 20.000–100.000 | Hochhaus, grosses Gewerbeprojekt | 500–2.000 |
| Komplex | > 100.000 | Spezialfall (v1.1+) | > 2.000 |

**Revidierte NFRs (ersetzen NFR-P-001/002/003):**

```
NFR-P-001 (neu): PDF-Import + Geometrieextraktion
  - Klein (<2.000 Obj.): < 5 Sekunden
  - Mittel (2.000–20.000): < 20 Sekunden
  - Gross (20.000–100.000): < 60 Sekunden; Fortschrittsanzeige in CLI

NFR-P-002 (neu): Panelisierung
  - < 500 Panels: < 5 Sekunden
  - 500–2.000 Panels: < 20 Sekunden
  - > 2.000 Panels: < 60 Sekunden; Fortschrittsanzeige

NFR-P-003 (neu): DXF-Export
  - < 500 Panels: < 3 Sekunden
  - 500–2.000 Panels: < 10 Sekunden
```

### Finalisierte Entscheidung GAP-009

```
Performance-Metriken basieren auf Geometrieanzahl (Input) und Panelanzahl (Output).
Performance-Klassen: Klein / Mittel / Gross (wie oben).
Ab "Mittel": CLI-Fortschrittsanzeige (Progress Bar).
Maximale getestete Projektgrösse MVP: 100.000 Geometrieobjekte / 2.000 Panels.
```

---

## GAP-010: Nachvollziehbarkeit — Audit-Format

### Entscheidung des Projektteams
Audit-JSON mit: surface, supplier, format, joint, panels.

### Architekt-Bewertung: **Erweitert — vorgeschlagenes Format ist zu minimal für Reproduzierbarkeit**

Die Richtung (JSON) ist korrekt. Das Beispiel-JSON enthält jedoch zu wenig Information, um eine Panelisierung wirklich reproduzieren zu können.

**Vollständiges Audit-Dokument-Schema:**

```json
{
  "schema_version": "1.0",
  "audit_type": "PanelizationAudit",
  "job_id": "JOB-042",
  "timestamp": "2026-06-08T14:30:00Z",
  "engine_version": "1.0.0",
  
  "input_snapshot": {
    "surfaces": [
      {"id": "FA-001", "gross_area_mm2": 18000000, "openings_count": 3}
    ],
    "catalogs": [
      {"id": "CAT-001", "supplier": "Swisspearl", "formats_count": 5}
    ]
  },
  
  "config_snapshot": {
    "horizontal_joint_mm": 10,
    "vertical_joint_mm": 10,
    "expansion_joint_interval_mm": 6000,
    "orientation": "HORIZONTAL",
    "min_panel_width_mm": 100,
    "min_panel_height_mm": 100
  },
  
  "results_per_surface": [
    {
      "surface_id": "FA-001",
      "total_panels": 87,
      "full_panels": 72,
      "cut_panels": 15,
      "primary_format": {"supplier": "Swisspearl", "code": "1250x3050", "width_mm": 1250, "height_mm": 3050},
      "coverage_percent": 94.3,
      "warnings": []
    }
  ],
  
  "format_selection_log": [
    {
      "panel_id": "PA-001-001",
      "position": {"x": 0, "y": 0},
      "selected_format": "Swisspearl/1250x3050",
      "reason": "FULL_PANEL_FIT",
      "alternatives_considered": 3
    }
  ],
  
  "scale_calibration": {
    "method": "TWO_POINT",
    "reference_points": [[0, 0], [1500, 0]],
    "real_distance_mm": 1500,
    "calculated_factor": 1.0
  },
  
  "warnings": [],
  "errors": []
}
```

**Audit-Log vs. Audit-Report:**

Zwei separate Ausgaben:
- **Audit-JSON** (maschinenlesbar): für Reproduzierbarkeit, Debugging, zukünftige Automatisierung
- **Summary-Report.txt** (menschenlesbar): für Projektdokumentation, Lieferantenkommunikation

### Finalisierte Entscheidung GAP-010

```
Audit-Ausgabe: zwei Formate
  1. <job-id>_audit.json — vollständiges JSON (maschinenlesbar, versioniert)
  2. <job-id>_report.txt — Zusammenfassung (menschenlesbar)

Audit-JSON enthält zwingend:
  - job_id, timestamp, engine_version
  - input_snapshot (Flächen, Kataloge)
  - config_snapshot (alle Parameter)
  - results_per_surface (Statistik)
  - format_selection_log (Entscheidung pro Panel — optional, konfigurierbar)
  - scale_calibration (Kalibrierungsparameter)
  - warnings + errors
```

---

## RISK-001: CAD-Import (DXF/DWG)

### Entscheidung des Projektteams
MVP: nur PDF. Später: DXF, dann DWG.

### Architekt-Bewertung: **Vollständig übernommen — wichtige technische Vorwarnungen**

**Die Priorisierung ist korrekt.** Drei Punkte für die Roadmap-Planung:

**1. DXF-Import ist einfacher als PDF-Import (wenn er kommt):**
DXF ist ein strukturiertes Format (Entities mit expliziten Typ- und Koordinatenangaben). Keine Koordinatensystem-Normalisierung notwendig. DXF-Import in v1.1 wird deutlich schneller implementiert als der PDF-Import.

**2. DWG ist proprietär — frühzeitig kommunizieren:**
DWG (.dwg) ist Autodesks proprietäres Format. Python-Bibliotheken für DWG sind entweder via ODA File Converter (Open Design Alliance) oder über `ezdxf` (liest DWG als DXF). Lizenzfrage für kommerzielle Nutzung muss rechtzeitig geklärt werden. Empfehlung: DWG erst v2.0.

**3. Architektur ist bereits korrekt vorbereitet:**
Das `PlanImportPort`-Interface ermöglicht einen DXF-Adapter ohne Domänenänderung. Dieser Punkt ist architektonisch bereits gelöst.

### Finalisierte Entscheidung RISK-001

```
MVP: PDF-Import (AutoCAD, Revit, ArchiCAD)
v1.1: DXF-Import (via separatem DXFImportAdapter, implementiert PlanImportPort)
v2.0: DWG-Import (Lizenzklärung erforderlich: ODA File Converter)

Kein Handlungsbedarf im MVP — Architektur ist bereits vorbereitet.
```

---

## RISK-002: Keine gültige Panelisierung

### Entscheidung des Projektteams
Fläche wird als Fehler markiert wenn keine gültige Panelisierung möglich.

### Architekt-Bewertung: **Erweitert — mehrere Fehler-Modi und Fehlerbehandlungsstrategie fehlen**

**Die Grundentscheidung ist korrekt.** Es gibt jedoch nicht einen Fehlerfall, sondern mindestens vier:

```
PANELIZATION_ERROR Typen:

PE-001: NO_FORMAT_FITS
  Keines der verfügbaren Formate passt auf die Fläche 
  (z.B. Fläche 200mm breit, kleinstes Format 300mm).
  → Neue Formate hinzufügen oder Fläche aufteilen

PE-002: EDGE_PANEL_TOO_SMALL
  Randpanel unterschreitet min_panel_width_mm oder min_panel_height_mm.
  → Mindestmasse reduzieren oder Startpunkt anpassen

PE-003: ALL_PANELS_BLOCKED_BY_OPENING
  Alle generierten Panels werden durch Öffnungen eliminiert.
  → Öffnungsgeometrie prüfen oder Fläche teilen

PE-004: SURFACE_TOO_SMALL
  Fläche ist kleiner als das kleinste verfügbare Format.
  → Manuell bearbeiten
```

**Empfohlene Fehler-Strategie: Fail-Per-Surface, nicht Fail-Per-Job**

Der Job läuft weiter. Flächen mit Fehler werden als `PANELIZATION_FAILED` markiert. Der Nutzer erhält einen strukturierten Fehlerbericht, der auch Partial-Ergebnisse enthält.

**Neue Business Rule:**

```
GR-010: PANELIZATION_FAILURE_HANDLING
Wenn keine gültige Panelisierung erzeugt werden kann:
  1. Fläche erhält Status PANELIZATION_FAILED
  2. Fehlertyp (PE-001 bis PE-004) wird im Audit-Log erfasst
  3. Restliche Flächen des Jobs werden normal verarbeitet
  4. CLI-Ausgabe enthält Fehlerliste am Ende

Optional (v1.1): --force Flag ignoriert Fehler und produziert Best-Effort-Ergebnis
```

### Finalisierte Entscheidung RISK-002

```
Fehler-Typen: PE-001 bis PE-004 (spezifisch, nicht generisch)
Strategie: Fail-Per-Surface (Job läuft weiter)
Neue Entität: PanelizationError { surface_id, error_type, message, suggestion }
Audit-Log: Alle Fehler werden dokumentiert
CLI: Fehlerliste am Ende der Ausgabe, Exit-Code ≠ 0 wenn Fehler vorhanden
```

---

## RISK-003: Unterschiedliche PDF-Strukturen

### Entscheidung des Projektteams
MVP: nur AutoCAD, Revit, ArchiCAD. Weitere nicht unterstützt.

### Architekt-Bewertung: **Erweitert — architektonische Massnahme ist notwendig, nicht nur eine Liste**

**Die Einschränkung ist korrekt, reicht aber als Mitigation alleine nicht aus.**

**Konkretes Problem:** Die drei unterstützten Generatoren erzeugen trotzdem unterschiedliche interne Strukturen:

| Problem | AutoCAD | Revit | ArchiCAD |
|---------|---------|-------|----------|
| Koordinatenursprung | Seitenunterseite links | Projektmittelpunkt | Seitenunterseite links |
| Y-Achse | Standard aufwärts | Standard aufwärts | Standard aufwärts |
| Layer-Struktur | Vollständig | Eingeschränkt | Vollständig |
| Schriftfeld-Geometrie | Separater Layer | Gemischt | Separater Layer |
| Bemaßungslinien | Eigener Layer (A-ANNO-DIMS) | Gemischt | Eigener Layer |

**Architektonische Massnahme: `PDFSourceDetector` + `PDFNormalizer`**

```
Infrastructure Layer:

PDFSourceDetector
  detect_generator(raw_pdf) → PDFGenerator enum
    → Analysiert PDF-Metadaten (Producer-Feld) 
    → Fallback: strukturelle Heuristiken

PDFNormalizer (Strategy-Pattern)
  normalize(raw_geometries, generator: PDFGenerator) → List[NormalizedGeometry]
  
  Implementierungen:
    AutoCADPDFNormalizer     ← koordinatentransformation, layer-filter
    RevitPDFNormalizer       ← koordinatentransformation, kategorie-mapping
    ArchiCADPDFNormalizer    ← koordinatentransformation, layer-filter
    GenericPDFNormalizer     ← best-effort für unbekannte Generatoren (warnt)
```

**Testanforderung:** Für jeden Generator müssen Referenz-PDFs in `fixtures/pdf/` vorhanden sein (je Generator mind. 1 Testdatei).

### Finalisierte Entscheidung RISK-003

```
Architektonische Massnahme: PDFSourceDetector + PDFNormalizer (Strategy)
Je Generator eine Normalizer-Implementierung.
Testdaten: mind. 1 PDF pro unterstütztem Generator in fixtures/.
Bekanntes Risiko: Revit ohne Layer → explizite Dokumentation + CLI-Hinweis.
Unbekannte Generatoren: GenericPDFNormalizer mit WARNING-Log.
```

---

## RISK-004: Regelwerk wächst unkontrolliert

### Entscheidung des Projektteams
Eigenständiger Rules Catalog mit Regeln für Fugen, Mindestmaße, Rotation, Öffnungen, Lieferantenlimits, Bewegungsfugen.

### Architekt-Bewertung: **Erheblich erweitert — KRITISCHSTES architektonisches Risiko — eigene ADR erforderlich**

**Dies ist der wichtigste Punkt dieses gesamten Reviews.**

Ein unkontrolliertes Regelwerk wird das System mittelfristig unwartbar machen. Folgende Entwicklung ist ohne Architekturentscheidung absehbar:

```
Sprint 2: 3 Regeln (Mindestmaß, Fuge, GR-001/002)
Sprint 3: +3 Regeln (Bewegungsfuge, Öffnungsrand)
v1.1: +5 Regeln (Lieferanten-spezifisch, thermische Ausdehnung)
v2.0: +10 Regeln (Unterkonstruktion, Befestigung)
→ 20+ Regeln ohne Struktur = unlösbare Wartungsprobleme
```

**Empfohlene Architektur: Strukturiertes Rules Engine Design**

```
DOMAIN — Rules-Teildomäne:

RuleDefinition (Value Object)
  - id: RuleId (z.B. "GR-001", "GR-008", "SWISSPEARL-001")
  - name: str
  - description: str
  - severity: Enum(ERROR, WARNING, INFO)
  - category: Enum(GEOMETRIC, FORMAT, JOINT, TECHNICAL, SUPPLIER)
  - parameters: Dict[str, Any]  ← konfigurierbare Parameter
  - is_active: bool

RuleCatalog (Entity)
  - id: UUID
  - rules: List[RuleDefinition]  ← geordnet, prioritätsbewusst
  - project_id: UUID

RuleViolation (Value Object)
  - rule_id: RuleId
  - severity: Severity
  - message: str
  - context: Dict  ← welches Panel, welche Fläche

RuleEngine (Domain Service)
  evaluate(
    target: Panel | PanelizationResult | FacadeSurface,
    catalog: RuleCatalog
  ) -> List[RuleViolation]
```

**Regelkategorien und Basisregeln:**

```
GEOMETRIC:
  GR-001: Panel hat Formatreferenz
  GR-002: Panel ≤ Rohplattengrösse
  GR-003: Maße in mm
  GR-004: Flächen-IDs eindeutig
  GR-005: Panel-IDs eindeutig

FORMAT:
  GR-006: Mindestrandabstand zu Öffnungen
  GR-007: Mindestpanelgrösse nach Öffnungsschnitt

JOINT:
  GR-008: Bewegungsfugen-Intervall
  GR-009: Fugengrösse ≥ Minimum

TECHNICAL (MVP-Basis):
  GR-010: Fehlerbehandlung Panelisierungsfehler

SUPPLIER (lieferantenspezifisch, kommen mit Katalog):
  z.B. "SWISSPEARL-001": max. Plattengrösse 1250x3050mm
```

**Supplier-spezifische Regeln — wichtige Design-Entscheidung:**

Lieferanten können eigene technische Regeln haben (z.B. Swisspearl hat spezifische Verlegeanleitungen, ALUCOBOND hat Dehnungsformeln). Diese Regeln sollen **mit dem Lieferantenkatalog importierbar** sein:

```json
// In supplier_catalog.json:
{
  "supplier": "Swisspearl",
  "formats": [...],
  "rules": [
    {
      "id": "SWISSPEARL-001",
      "description": "Max. Panel 1250x3050mm (Format-Maximum)",
      "severity": "ERROR",
      "category": "SUPPLIER",
      "parameters": {"max_width_mm": 1250, "max_height_mm": 3050}
    },
    {
      "id": "SWISSPEARL-002", 
      "description": "Mindestfuge horizontal 8mm",
      "severity": "WARNING",
      "parameters": {"min_horizontal_joint_mm": 8}
    }
  ]
}
```

### Finalisierte Entscheidung RISK-004

```
Rules Engine: eigenständige Teildomäne mit:
  - RuleDefinition (konfigurierbar, aktivierbar/deaktivierbar)
  - RuleCatalog (geordnet, per Projekt)
  - RuleEngine (Domain Service, evaluiert Ergebnisse)
  - RuleViolation (mit Severity und Kontext)

Regel-Kategorien: GEOMETRIC, FORMAT, JOINT, TECHNICAL, SUPPLIER
Supplier-spezifische Regeln: importierbar mit Lieferantenkatalog
Konfiguration per Projekt: Regeln aktivieren/deaktivieren/Parameter anpassen

→ Neue ADR-007 für Rules Engine wird erstellt.
→ Domänenmodell wird entsprechend aktualisiert.
```

---

## Zusammenfassung der Änderungen an SRS, Domäne und Architektur

### Neue Business Rules
| ID | Regel | Quelle |
|----|-------|--------|
| GR-006 | Mindestrandabstand Panel zu Öffnung | GAP-003 |
| GR-007 | Mindestpanelgrösse nach Öffnungsschnitt | GAP-003 |
| GR-008 | Bewegungsfugen-Intervall | GAP-006 |
| GR-009 | Fugengrösse ≥ 8mm (Warnung) | GAP-006 |
| GR-010 | Panelisierungsfehler-Behandlung | RISK-002 |

### Neue Entitäten im Domänenmodell
| Entität | Grund |
|---------|-------|
| `FacadeZone` | GAP-008: Flexible Gruppierung statt fest codierter Geschoss-Entität |
| `RuleDefinition` | RISK-004: Rules Engine Teildomäne |
| `RuleCatalog` | RISK-004 |
| `RuleViolation` | RISK-004 (ersetzt/erweitert PlanningWarning) |
| `PanelizationError` | RISK-002: Spezifische Fehlerfälle |
| `JointConfig` | GAP-006: Erweitert PanelizationConfig |

### Neue Architekturkomponenten
| Komponente | Schicht | Grund |
|------------|---------|-------|
| `PDFSourceDetector` | Infrastructure | RISK-003 |
| `PDFNormalizer` (Strategy) | Infrastructure | RISK-003, GAP-001 |
| `RuleEngine` | Domain Services | RISK-004 |

### Neue ADRs
| ADR | Thema |
|-----|-------|
| ADR-007 | Rules Engine Architektur |

### Aktualisierte ADRs
| ADR | Änderung |
|-----|---------|
| ADR-002 | Generator-spezifische Normalisierung ergänzt |
