# ADR-006: DXF-Zielversion AC1027 (AutoCAD 2013+)

**Status:** Accepted  
**Datum:** 2026-06-08  
**Entscheider:** Softwarearchitektur  

---

## Kontext

DXF ist kein einheitlicher Standard — es gibt zahlreiche Versionen (AC1006 = R10 bis AC1032 = R2018). Die gewählte Zielversion beeinflusst:
- Kompatibilität mit AutoCAD-Versionen der Nutzer
- Unterstützte DXF-Features (Layer, Text, Annotationen)
- ezdxf API-Nutzung

## Entscheidung

**DXF-Zielversion: AC1027 (AutoCAD R2013)**

**Begründung:**
- AC1027 bietet alle benötigten Features (Layer, LWPOLYLINE, MTEXT)
- Kompatibel mit AutoCAD 2013+ und allen neueren Versionen
- Von BricsCAD, LibreCAD und anderen CAD-Systemen unterstützt
- ezdxf unterstützt AC1027 vollständig
- Vermeidet Probleme mit sehr alten Versionen (AC1014/AC1015)

## Konsequenzen

- ezdxf `doc = ezdxf.new('R2013')` als Standard
- Alle Panels als `LWPOLYLINE` (leichtgewichtig, effizient)
- Panel-Labels als `MTEXT` für Unicode-Unterstützung
- Layer-Namen nach Schema: `FACADE_<SurfaceId>`

## Risiken

- Nutzer mit AutoCAD 2010 oder älter können Dateien nicht öffnen (sehr unwahrscheinlich)
- Mitigation: Version im CLI-Output dokumentieren
