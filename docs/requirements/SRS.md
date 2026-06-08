# Software Requirements Specification (SRS)
## Facade Planning Engine — MVP

**Version:** 1.1  
**Status:** Updated nach GAP/Risk-Review  
**Datum:** 2026-06-08  
**Autor:** Softwarearchitektur-Review  
**Änderungen v1.1:** FR-001 (Generator-Validierung), FR-002 (CLI-Workflow), FR-004 (Öffnungsregeln), FR-006 (JointConfig), neues FR-010 (FacadeZone), FR-011 (Rules Engine), NFR-P-001/002 (geometriebasiert)  

---

## 1. Einleitung

### 1.1 Zweck
Dieses Dokument definiert die Software Requirements Specification (SRS) für die Facade Planning Engine MVP. Es richtet sich an Entwickler, Architekten und technische Stakeholder.

### 1.2 Projektumfang (Scope)
Die Facade Planning Engine automatisiert die technische Fassadenplanung: PDF-Pläne werden importiert, Geometrien extrahiert, Fassadenflächen erkannt und automatisch panelisiert. Das Ergebnis wird als DXF exportiert.

**Explizit ausgeschlossen (Out of Scope für MVP):**
- Statikberechnungen
- Kostenberechnung / Kostenauswertung
- Ausschreibungsdokumente
- BIM-Integration (IFC, Revit)
- Produktionsdaten / Fertigungsdaten
- Grafische Benutzeroberfläche (GUI)
- Netzwerk- oder Cloud-Dienste
- Mehrbenutzer-Betrieb

---

## 2. Kritische Analyse der Anforderungen

> **Architekt-Hinweis:** Folgende offene Fragen müssen vor Sprint 1 geklärt werden.

### 2.1 Fehlende Anforderungen (Gaps)

| ID | Offene Frage | Risiko | Empfehlung |
|----|-------------|--------|------------|
| GAP-001 | Welche PDF-Versionen werden unterstützt? (1.4–2.0?) | Hoch — PDF-Generatoren erzeugen sehr unterschiedliche interne Strukturen | Auf vektorbasierte PDFs einschränken; Rasterbild-PDFs als v2.0 Feature |
| GAP-002 | Wie wird der Maßstab aus PDFs erkannt? OCR der Bemaßung? Maßstabsbalken? | Hoch — Fehlerhafte Skalierung macht alle Maße unbrauchbar | Manuelle Skalierung als primären Weg definieren; automatische Erkennung als optional |
| GAP-003 | Wie werden Öffnungen (Fenster, Türen) in Fassadenflächen behandelt? | Hoch — Panelisierung um Öffnungen herum ist algorithmisch komplex | Explizite Anforderung: Öffnungen müssen als Aussparungen in der Panelisierung berücksichtigt werden |
| GAP-004 | Welche DXF-Versionen / AutoCAD-Kompatibilität ist erforderlich? (R2010, R2018, R2022?) | Mittel — DXF ist kein einheitlicher Standard | Zielversion explizit festlegen (Empfehlung: AC1027 = AutoCAD 2013+) |
| GAP-005 | Wie wird eine Fassadenfläche von anderen Bauteilen unterschieden? (Dach, Boden?) | Hoch — Ohne klare Erkennungsregeln ist das System nicht zuverlässig | Erkennungsregeln explizit dokumentieren (Layer-Namen, Farben, manuelle Auswahl) |
| GAP-006 | Gibt es Fugenmaße / Mindestabstände zwischen Panels? | Mittel — Fugen sind Teil der technischen Planung | Als konfigurierbarer Parameter definieren (default: 0mm, typisch 8–20mm) |
| GAP-007 | Welche Panelausrichtung ist erlaubt? (Hochformat, Querformat, beides?) | Mittel — Beeinflusst den Panelisierungs-Algorithmus direkt | Als konfigurierbare Regel pro Projekt |
| GAP-008 | Wie werden mehrgeschossige Gebäude behandelt? (eine Fläche pro Ebene?) | Mittel — Koordinatensystem und Zonierung unklar | Klärung: sind Stockwerke separate Fassadenflächen oder eine Gesamtfläche? |
| GAP-009 | Was ist das maximale Dateiformat für PDFs? (Seitenzahl, Dateigrösse?) | Niedrig — Performance-Erwartungen fehlen | Performance-NFR definieren |
| GAP-010 | Wie sieht die "Nachvollziehbarkeit" konkret aus? Log-Datei? PDF-Bericht? JSON? | Mittel — Ohne klares Format ist das Feature nicht testbar | Format der Audit-Dokumentation festlegen |

### 2.2 Widersprüche / Risiken in bestehenden Anforderungen

| ID | Widerspruch / Risiko | Empfehlung |
|----|---------------------|------------|
| RISK-001 | BR-001 nennt "PDF oder CAD", aber die gesamte Architektur scheint auf PDF ausgerichtet — CAD-Import (DXF/DWG) hat fundamental andere Verarbeitungslogik | CAD-Import als v1.1 Feature planen, nicht MVP |
| RISK-002 | GR-001 sagt "jedes Panel muss auf verfügbarem Lieferantenformat basieren" — was passiert wenn keine Kombination passt? Fehler? Teilaufteilung? | Fehlerverhalten explizit definieren |
| RISK-003 | PDF-Geometrieextraktion ist nicht deterministisch — verschiedene PDF-Generatoren (AutoCAD, Revit, Illustrator) erzeugen sehr unterschiedliche interne Strukturen | Akzeptanzkriterium: Testdaten aus definierten Quellen |
| RISK-004 | "Regelbasierte Planung" (BR-007) ist zu vage — welche Regeln? | Regelkatalog als separates Dokument erstellen |

---

## 3. Stakeholder

| Rolle | Beschreibung | Interesse |
|-------|-------------|-----------|
| Fassadenplaner | Hauptnutzer — erstellt Panelisierungspläne | Zeitersparnis, korrekte Maße, DXF-Output |
| Projektleiter Fassadenbau | Auftraggeber intern | Reproduzierbarkeit, Auditierbarkeit |
| CAD-Techniker | Nachbearbeitung der DXF-Exporte | Kompatibilität mit AutoCAD/BricsCAD |
| Entwicklungsteam | Implementierung und Wartung | Klare Anforderungen, testbare Akzeptanzkriterien |

---

## 4. Funktionale Anforderungen (FR)

### 4.1 FR-001: PDF-Import

**Priorität:** MUST  
**Basiert auf:** BR-001  
**Aktualisiert:** v1.1 — Generator-Validierung und Normalisierung ergänzt (GAP-001, RISK-003)

| Sub-Req | Beschreibung | Akzeptanzkriterium |
|---------|-------------|-------------------|
| FR-001.1 | Das System importiert vektorbasierte PDFs aus AutoCAD 2018+, Revit 2019+, ArchiCAD 25+ | PDFs aus unterstützten Generatoren werden ohne Fehler geladen |
| FR-001.2 | Das System identifiziert den PDF-Generator automatisch (PDFSourceDetector) | Generator wird im Audit-Log erfasst; Warnung bei unbekanntem Generator |
| FR-001.3 | Das System meldet einen klaren Fehler bei rasterbildbasierten PDFs | Fehlermeldung: "Datei enthält keine Vektordaten. Bitte aus AutoCAD/Revit/ArchiCAD exportieren." |
| FR-001.4 | Das System meldet einen Hinweis bei unbekanntem PDF-Generator | Warnung: "Generator nicht erkannt — Qualität nicht garantiert." Verarbeitung läuft weiter. |
| FR-001.5 | Das System unterstützt mehrseitige PDFs (eine Seite = eine Ansicht) | Seiten werden einzeln verarbeitbar aufgelistet |
| FR-001.6 | PDFs ohne Layer-Struktur werden als "layerlos" behandelt | Alle Geometrien auf einem Layer; Nutzer erhält Hinweis |
| FR-001.7 | Koordinatensystem wird je Generator normalisiert (PDFNormalizer) | Koordinaten nach Normalisierung ±1mm korrekt vs. Referenzmaß |

### 4.2 FR-002: Skalierung

**Priorität:** MUST  
**Basiert auf:** BR-002  
**Aktualisiert:** v1.1 — Zwei-Punkte-Kalibrierung als primärer Workflow (GAP-002)

| Sub-Req | Beschreibung | Akzeptanzkriterium |
|---------|-------------|-------------------|
| FR-002.1 | Primär: Zwei-Punkte-Kalibrierung — Nutzer gibt zwei Koordinaten und reale Distanz in mm an | System berechnet Skalierungsfaktor; Maße korrekt skaliert |
| FR-002.2 | Sekundär: Direkteingabe Maßstab (z.B. `--scale 1:100`) | Alle extrahierten Maße werden korrekt skaliert |
| FR-002.3 | Validierung: Referenzpunkte müssen verschieden sein; reale Distanz > 0 | Fehlermeldung bei ungültigen Eingaben |
| FR-002.4 | Das System gibt eine Warnung wenn kein Maßstab definiert wurde | Warnung erscheint vor Extraktion; Prozess kann mit expliziter Bestätigung fortgesetzt werden |
| FR-002.5 | Alle Maße werden intern in Millimetern gespeichert (GR-003) | Ausgabewerte entsprechen mm-Einheit |
| FR-002.6 | Kalibrierungsdaten werden im Audit-JSON gespeichert (ScaleCalibration) | Kalibrierungsmethode, Referenzpunkte und Faktor im Audit nachvollziehbar |
| FR-002.7 | Neu-Kalibrierung eines bereits verarbeiteten Plans erzeugt eine Warnung | Warnung: "Bereits detektierte Flächen und Panels werden durch Neu-Kalibrierung ungültig." |

### 4.3 FR-003: Geometrieextraktion

**Priorität:** MUST  
**Basiert auf:** BR-003

| Sub-Req | Beschreibung | Akzeptanzkriterium |
|---------|-------------|-------------------|
| FR-003.1 | Das System extrahiert Linien und Polygone aus dem PDF | Extrahierte Geometrien sind als Liste aufrufbar |
| FR-003.2 | Das System filtert Linien nach Layer/Farbe (konfigurierbar) | Extraktion auf definierten Layer einschränkbar |
| FR-003.3 | Geometrien werden mit Positionskoordinaten (x, y) in mm gespeichert | Koordinaten sind korrekt skaliert |
| FR-003.4 | Das System protokolliert die Anzahl extrahierter Elemente | Log-Eintrag mit Statistik |

### 4.4 FR-004: Fassadenflächenerkennung

**Priorität:** MUST  
**Basiert auf:** BR-004  
**Aktualisiert:** v1.1 — Layer-Workflow, FacadeZone-Zuordnung, Öffnungsregeln (GAP-003, GAP-005, GAP-008)

| Sub-Req | Beschreibung | Akzeptanzkriterien |
|---------|-------------|-------------------|
| FR-004.1 | Das System listet alle verfügbaren Layer des PDFs mit Geometrie-Statistik | Layer-Liste mit Name, Anzahl Geometrien ausgegeben |
| FR-004.2 | Geschlossene Polygone des gewählten Layers werden als Flächen-Kandidaten erkannt | Alle geschlossenen Polygone auf gewähltem Layer identifiziert |
| FR-004.3 | Der Nutzer kann Fassadenflächen manuell bestätigen oder verwerfen (CLI) | `facade surface confirm/reject` funktioniert; Status persistiert |
| FR-004.4 | Jede Fassadenfläche erhält eine eindeutige ID (GR-004, Format FA-NNN) | IDs systemweit eindeutig |
| FR-004.5 | Öffnungen (Fenster, Türen, Lüftung, Revision) werden als Aussparungen modelliert | Öffnungen als Holes gespeichert; Typ zuweisbar |
| FR-004.6 | Flächeninhalt (brutto + netto) und Bounding Box werden berechnet | Ausgabe in mm² und mm; netto = brutto minus Öffnungsflächen |
| FR-004.7 | Fassadenflächen können beim Bestätigen einer FacadeZone zugeordnet werden | `facade surface confirm FA-001 --zone "Nordfassade"` funktioniert |
| FR-004.8 | Panels dürfen Öffnungen nicht überdecken (GR-003 Geometrie) | Automatische Validierung nach Panelisierung |
| FR-004.9 | Öffnungsrand-Strategie (TRIM/DROP) ist konfigurierbar | Default: TRIM; `--opening-strategy drop` verfügbar |

### 4.5 FR-005: Lieferantenformate

**Priorität:** MUST  
**Basiert auf:** BR-005

| Sub-Req | Beschreibung | Akzeptanzkriterien |
|---------|-------------|-------------------|
| FR-005.1 | Lieferantenformatlisten werden als JSON/CSV importiert | Datei wird validiert und geladen |
| FR-005.2 | Plattenformate werden mit Breite × Höhe in mm gespeichert | Werte abrufbar |
| FR-005.3 | Mehrere Lieferanten können im selben Projekt verwaltet werden | Lieferanten sind identifizierbar und filterbar |
| FR-005.4 | Das System validiert, dass Plattenmaße > 0 sind | Fehlermeldung bei ungültigen Maßen |
| FR-005.5 | Verfügbare Formate können aufgelistet werden (CLI) | Tabellarische Ausgabe |

### 4.6 FR-006: Panelisierung

**Priorität:** MUST  
**Basiert auf:** BR-006  
**Aktualisiert:** v1.1 — JointConfig, Öffnungsregeln, Fehlerstrategie (GAP-003, GAP-006, GAP-007, RISK-002)

| Sub-Req | Beschreibung | Akzeptanzkriterien |
|---------|-------------|-------------------|
| FR-006.1 | Das System teilt eine Fassadenfläche automatisch in Panels auf | Panelliste für jede Fläche wird erzeugt |
| FR-006.2 | Jedes Panel basiert auf einem verfügbaren Lieferantenformat (GR-001) | Kein Panel ohne Lieferantenformat-Referenz |
| FR-006.3 | Panelgröße überschreitet nicht die Rohplattengröße (GR-002) | Validierung schlägt fehl wenn Panel > Rohplatte |
| FR-006.4 | Jedes Panel erhält eine eindeutige ID (GR-005) | IDs systemweit eindeutig |
| FR-006.5 | Panels haben definierte Positionen (x, y, Breite, Höhe) in mm | Koordinaten korrekt |
| FR-006.6 | Öffnungen werden aus der Panelisierung ausgeschnitten | Kein Panel überdeckt eine Öffnungsfläche |
| FR-006.7 | Horizontale und vertikale Fugen separat konfigurierbar (JointConfig) | Default: je 10mm; beide Richtungen unabhängig einstellbar |
| FR-006.8 | Mindest-Fuge 8mm — Warnung wenn unterschritten (GR-009) | CLI-Ausgabe zeigt Warnung; Panelisierung läuft weiter |
| FR-006.9 | Bewegungsfugen werden im Grid berücksichtigt (GR-008) | Alle 6000mm (konfigurierbar) wird eine breitere Bewegungsfuge eingefügt |
| FR-006.10 | Panelausrichtung konfigurierbar: HORIZONTAL, VERTICAL, AUTO | AUTO wählt Ausrichtung mit mehr Vollplatten |
| FR-006.11 | Kann keine Fläche panelisiert werden → Fehler PE-001..PE-004 (RISK-002) | Fehler markiert Fläche als PANELIZATION_FAILED; Rest des Jobs läuft weiter |
| FR-006.12 | Mindest-Panelgrösse nach Öffnungsschnitt konfigurierbar (GR-007) | Zu kleine Panels nach Zuschnitt werden entfernt |

### 4.7 FR-007: Regelbasierte Planung

**Priorität:** SHOULD  
**Basiert auf:** BR-007

| Sub-Req | Beschreibung | Akzeptanzkriterien |
|---------|-------------|-------------------|
| FR-007.1 | Technische Regeln (Mindestmaß, Maximalmaß je Panel) sind konfigurierbar | Regeln werden bei Panelisierung geprüft |
| FR-007.2 | Randpanele können auf ein Mindestmaß begrenzt werden | Kein Randpanel kleiner als definiertes Minimum |
| FR-007.3 | Regelverletzungen werden als Warnungen protokolliert | Log-Einträge mit Regelreferenz |

### 4.8 FR-008: DXF-Export

**Priorität:** MUST  
**Basiert auf:** BR-008

| Sub-Req | Beschreibung | Akzeptanzkriterien |
|---------|-------------|-------------------|
| FR-008.1 | Das System exportiert Panelisierung als DXF-Datei | DXF-Datei wird erzeugt und ist in AutoCAD öffenbar |
| FR-008.2 | Jede Fassadenfläche wird auf eigenem DXF-Layer abgebildet | Layer pro Fläche vorhanden |
| FR-008.3 | Panel-IDs werden als Textobjekte in DXF eingebettet | ID-Texte sichtbar im DXF |
| FR-008.4 | Maßstab und Einheit (mm) sind im DXF korrekt gesetzt | AutoCAD zeigt mm-Werte korrekt |
| FR-008.5 | DXF-Kompatibilität: AC1027 (AutoCAD 2013+) | Datei öffnet ohne Fehler in AutoCAD 2013 oder neuer |

### 4.9 FR-009: Nachvollziehbarkeit

**Priorität:** SHOULD  
**Basiert auf:** BR-009

| Sub-Req | Beschreibung | Akzeptanzkriterien |
|---------|-------------|-------------------|
| FR-009.1 | Jede Verarbeitungsoperation wird in einem strukturierten Log protokolliert | Log-Datei (JSON) enthält Timestamps und Operationen |
| FR-009.2 | Panelisierungsentscheidungen werden dokumentiert (welches Format wurde warum gewählt) | Pro Panel: gewähltes Format + Auswahlgrund |
| FR-009.3 | Ein Prozess-Report wird als Textdatei exportiert | Report enthält: Input-File, Skalierung, Flächenanzahl, Panel-Statistik |

### 4.10 FR-010: Fassadenzonen (FacadeZone) — NEU

**Priorität:** SHOULD  
**Basiert auf:** GAP-008  
**Hintergrund:** Flexible Organisationsstruktur ohne fest codierte Geschoss-Entität. Ermöglicht Gruppierung nach Himmelsrichtung, Gebäudeachse, Geschoss oder beliebigem Bereich.

| Sub-Req | Beschreibung | Akzeptanzkriterium |
|---------|-------------|-------------------|
| FR-010.1 | Zonen können frei benannt und erstellt werden | `facade zone create "Nordfassade"` funktioniert; ID FZ-NNN vergeben |
| FR-010.2 | Fassadenflächen können einer Zone zugeordnet werden | `facade surface confirm FA-001 --zone FZ-001` funktioniert |
| FR-010.3 | Eine Fläche gehört zu max. einer Zone (MVP: flache Hierarchie) | Fehler wenn Fläche mehrfach zugeordnet wird |
| FR-010.4 | Panelisierung kann zonenweise gestartet werden | `facade panelize run --zone FZ-001 --catalog CAT-001` funktioniert |
| FR-010.5 | Zonen können eigene Konfigurationsüberschreibungen tragen | `--orientation vertical` für Zone überschreibt Projekt-Default |

---

### 4.11 FR-011: Rules Engine — NEU

**Priorität:** MUST (Grundstruktur), SHOULD (erweiterte Regeln)  
**Basiert auf:** RISK-004, GAP-006  
**Hintergrund:** Strukturiertes Regelwerk statt verstreuter Validierungscode. Lieferantenregeln sind importierbar.

| Sub-Req | Beschreibung | Akzeptanzkriterium |
|---------|-------------|-------------------|
| FR-011.1 | Builtin-Regeln GR-001 bis GR-010 sind immer aktiv | Alle Business Rules werden automatisch geprüft |
| FR-011.2 | Regeln können pro Projekt deaktiviert werden (ausser GR-001/002) | `facade rules disable GR-009 --reason "Sonderbewilligung"` |
| FR-011.3 | Regelparameter können konfiguriert werden | `facade rules configure GR-008 --expansion-interval 8000` |
| FR-011.4 | Lieferantenspezifische Regeln werden mit Katalog importiert | Swisspearl-Regeln nach Katalog-Import verfügbar |
| FR-011.5 | Regelverletzungen sind typisiert (ERROR/WARNING/INFO) mit Handlungsempfehlung | Ausgabe enthält Regelname, Schwere und Vorschlag |
| FR-011.6 | ERROR-Verletzungen blockieren Panelisierung der betroffenen Fläche | Fläche erhält Status PANELIZATION_FAILED bei ERROR |
| FR-011.7 | Alle Regelverletzungen erscheinen im Audit-JSON | Vollständige Regel-Trace in Audit-Datei |

---

## 5. Nicht-Funktionale Anforderungen (NFR)

### 5.1 Performance

**Aktualisiert v1.1:** Performance basiert auf Geometrieanzahl und Panelanzahl, nicht auf Dateigrösse in MB (GAP-009). Dateigrösse ist kein geeignetes Komplexitätsmass.

**Projektgrössen-Klassen (Schweizer Fassadenbaupraxis):**
| Klasse | Geometrieobjekte | Typisches Szenario |
|--------|-----------------|-------------------|
| Klein | < 2.000 | Einfamilienhaus, kleine Gewerbefassade |
| Mittel | 2.000–20.000 | Mehrfamilienhaus, Bürogebäude |
| Gross | 20.000–100.000 | Hochhaus, grosses Gewerbeprojekt |

| ID | Anforderung | Messgrösse | Priorität |
|----|------------|------------|-----------|
| NFR-P-001 | PDF-Import Klein (<2.000 Obj.) < 5 Sek.; Mittel (<20.000) < 20 Sek.; Gross (<100.000) < 60 Sek. mit Fortschrittsanzeige | Zeit von CLI-Aufruf bis Extraktionsabschluss | MUST |
| NFR-P-002 | Panelisierung: <500 Panels < 5 Sek.; 500–2.000 Panels < 20 Sek. | Zeit für vollständige Panelisierung inkl. Rules Engine | SHOULD |
| NFR-P-003 | DXF-Export: <500 Panels < 3 Sek.; 500–2.000 Panels < 10 Sek. | Zeit für Export-Operation | SHOULD |
| NFR-P-004 | CLI zeigt Fortschrittsanzeige bei Operationen > 5 Sekunden | Fortschrittsbalken oder %-Anzeige sichtbar | SHOULD |

### 5.2 Zuverlässigkeit / Korrektheit

| ID | Anforderung | Messgrösse | Priorität |
|----|------------|------------|-----------|
| NFR-R-001 | Maßabweichung bei Geometrieextraktion ≤ 1mm bei bekanntem Eingabemaßstab | Vergleich mit manuell vermessenen Testplänen | MUST |
| NFR-R-002 | Keine Panels dürfen sich überlappen (außer bei Fugen = 0) | Automatische Überlappungsprüfung im Test | MUST |
| NFR-R-003 | Alle Panels müssen vollständig innerhalb der Fassadenfläche liegen | Geometrische Validierung | MUST |

### 5.3 Wartbarkeit

| ID | Anforderung | Messgrösse | Priorität |
|----|------------|------------|-----------|
| NFR-M-001 | Testabdeckung ≥ 80% für Domänen-Logik (Panelisierung, Geometrie) | Coverage-Report | MUST |
| NFR-M-002 | Modularer Aufbau: PDF-Parser austauschbar ohne Änderung der Domänenlogik | Interface-Konformität in Tests | MUST |
| NFR-M-003 | Alle Abhängigkeiten in pyproject.toml / requirements definiert | Reproduzierbares Setup | MUST |
| NFR-M-004 | Code-Qualität: PEP 8 konform, keine Cyclomatic Complexity > 10 | CI-Prüfung mit flake8/ruff | SHOULD |

### 5.4 Erweiterbarkeit

| ID | Anforderung | Messgrösse | Priorität |
|----|------------|------------|-----------|
| NFR-E-001 | Neuer Eingabeformat-Adapter (z.B. DXF-Import) ist hinzufügbar ohne Änderung der Kernlogik | Definiertes Input-Interface | MUST |
| NFR-E-002 | Neuer Export-Adapter ist hinzufügbar ohne Änderung der Domänenlogik | Definiertes Output-Interface | MUST |
| NFR-E-003 | Panelisierungs-Algorithmus ist austauschbar | Strategy-Pattern im Algorithmus | SHOULD |

### 5.5 Bedienbarkeit (CLI)

| ID | Anforderung | Messgrösse | Priorität |
|----|------------|------------|-----------|
| NFR-U-001 | Alle Funktionen über CLI erreichbar | Vollständige CLI-Abdeckung | MUST |
| NFR-U-002 | Fehlermeldungen sind für Fassadenplaner verständlich (nicht nur Stack Traces) | Review durch Nicht-Entwickler | SHOULD |
| NFR-U-003 | `--help` für jeden CLI-Befehl verfügbar | Dokumentiert in CLI | MUST |
| NFR-U-004 | Exit-Codes sind standardkonform (0=Erfolg, 1+=Fehler) | Automatisch testbar | MUST |

### 5.6 Portabilität

| ID | Anforderung | Messgrösse | Priorität |
|----|------------|------------|-----------|
| NFR-PO-001 | Läuft auf Windows 10+, macOS 12+, Ubuntu 22.04+ | Getestet auf allen Plattformen | MUST |
| NFR-PO-002 | Python 3.11+ | Keine älteren Syntax-Features | MUST |

---

## 6. Business Rules — vollständige Liste v1.1

| ID | Regel | Kategorie | Severity |
|----|-------|-----------|---------|
| GR-001 | Jedes Panel muss auf einem verfügbaren Lieferantenformat basieren | FORMAT | ERROR |
| GR-002 | Panelgrössen dürfen die Rohplattengrösse nicht überschreiten | FORMAT | ERROR |
| GR-003 | Alle Maße werden in Millimetern gespeichert | GEOMETRIC | ERROR |
| GR-004 | Jede Fassadenfläche besitzt eine eindeutige ID | GEOMETRIC | ERROR |
| GR-005 | Jedes Panel besitzt eine eindeutige ID | GEOMETRIC | ERROR |
| GR-006 | Mindestrandabstand Panel zu Öffnungsrand (konfigurierbar, default 0mm) | TECHNICAL | WARNING |
| GR-007 | Panels nach Öffnungsschnitt müssen Mindestmaß einhalten | TECHNICAL | ERROR |
| GR-008 | Vertikale Bewegungsfugen alle expansion_joint_interval_mm (default 6000mm) | JOINT | WARNING |
| GR-009 | Fugengrösse muss ≥ 8mm sein | JOINT | WARNING |
| GR-010 | Fläche mit nicht lösbarem Panelisierungsfehler wird als FAILED markiert | TECHNICAL | ERROR |

---

## 7. Priorisierungsmatrix (MoSCoW)

| Anforderung | Kategorie | Sprint |
|-------------|-----------|--------|
| FR-001 PDF-Import (inkl. Generator-Normalisierung) | MUST | Sprint 1 |
| FR-002 Skalierung (Zwei-Punkte-Kalibrierung) | MUST | Sprint 1 |
| FR-003 Geometrieextraktion | MUST | Sprint 1 |
| FR-004 Fassadenflächenerkennung (Layer-Workflow) | MUST | Sprint 2 |
| FR-005 Lieferantenformate (inkl. Lieferantenregeln) | MUST | Sprint 1 |
| FR-006 Panelisierung (inkl. JointConfig, Bewegungsfugen) | MUST | Sprint 2 |
| FR-007 Regelbasierte Planung | SHOULD | Sprint 3 |
| FR-008 DXF-Export | MUST | Sprint 3 |
| FR-009 Nachvollziehbarkeit (Audit-JSON + Report) | SHOULD | Sprint 3 |
| FR-010 FacadeZone | SHOULD | Sprint 2 |
| FR-011 Rules Engine (Grundstruktur + Builtin-Regeln) | MUST | Sprint 2 |
| PDFNormalizer + PDFSourceDetector | MUST | Sprint 1 |
| CAD-Import (DXF) | COULD | v1.1 |
| Automatische Maßstabserkennung (Massstabsbalken) | COULD | v1.1 |
| Per-Zone Panelausrichtung | COULD | v1.1 |
| Optimierungsalgorithmus (Materialminimierung) | COULD | v2.0 |
| Unterkonstruktionsgenerierung | WON'T (MVP) | v2.0 |
| Befestigungspunkte | WON'T (MVP) | v2.0 |
| BIM-Integration | WON'T (MVP) | v3.0 |

---

## 7. Constraints

| ID | Constraint | Quelle |
|----|-----------|--------|
| CON-001 | Python als Hauptsprache | Projektvorgabe |
| CON-002 | CLI-first, keine GUI im MVP | Projektvorgabe |
| CON-003 | Keine Netzwerk-Abhängigkeiten im MVP (offline-fähig) | Implizit (kein Cloud-Requirement) |
| CON-004 | Open-Source-Bibliotheken bevorzugt | Best Practice |
| CON-005 | Alle Maße in Millimetern (GR-003) | Business Rule |
