# ADR-004: Shapely für 2D-Geometrieoperationen

**Status:** Accepted  
**Datum:** 2026-06-08  
**Entscheider:** Softwarearchitektur  

---

## Kontext

Die Kerndomäne erfordert robuste 2D-Geometrieoperationen:
- Polygon-Erkennung und -Validierung
- Point-in-Polygon-Tests
- Polygon-Subtraktion (Öffnungen aus Fassadenflächen ausschneiden)
- Überlappungsprüfung
- Flächen- und Distanzberechnungen

Diese Operationen korrekt und stabil zu implementieren ist nicht trivial (Edge Cases, numerische Präzision, Toleranzen).

## Entscheidung

**Shapely** wird als Geometriebibliothek für alle 2D-Operationen in der Domäne verwendet.

**Begründung:**
- Industriestandard für 2D-Geometrie in Python (basiert auf GEOS-Bibliothek)
- Robust gegen numerische Edge Cases
- Umfangreiche und getestete Operationen (Union, Difference, Intersection, Contains)
- Gute Performance (GEOS ist C-implementiert)
- Open Source (BSD-Lizenz)
- Shapely 2.0+ hat stabiles API

## Alternativen betrachtet

| Alternative | Warum verworfen |
|-------------|----------------|
| Eigene Implementierung | Zu fehleranfällig; numerische Geometrie ist ein bekanntes schwieriges Problem |
| PyGEOS | In Shapely 2.0 integriert — kein eigenständiges Paket mehr nötig |
| SymPy | Symbolische Mathematik, nicht für Performance-kritische Geometrie |
| Clipper2 (Python-Binding) | Gut für Polygon-Clipping, aber geringere Python-Community |

## Konsequenzen

**Positiv:**
- Robuste und korrekte Geometrieoperationen out-of-the-box
- Edge Cases (fast-berührende Polygone, degenerierte Formen) bereits behandelt
- Gute Testabdeckung der Bibliothek selbst

**Negativ:**
- Shapely führt eigene Geometrietypen ein (Polygon, LineString etc.) die von Domänen-Value-Objects getrennt sein müssen
- C-Abhängigkeit (GEOS) muss auf allen Zielplattformen verfügbar sein (normalerweise als Binary-Wheel vorhanden)

## Architekturhinweis

Shapely-Typen werden **nur im `geometry_service.py`** verwendet. Domänen-Value-Objects (`Polygon`, `Point2D`) sind eigene Python-Datenklassen, die bei Bedarf in Shapely-Typen konvertiert werden. Dies verhindert die Kopplung der Domäne an Shapely-spezifische APIs.

```python
# Konvertierung nur im Service, nicht in Entitäten:
class GeometryService:
    def area(self, polygon: Polygon) -> float:
        shapely_polygon = _to_shapely(polygon)  # Private Hilfsfunktion
        return shapely_polygon.area
```

## Risiken

- **RISK:** Shapely-API-Änderungen zwischen Major-Versionen
- **Mitigation:** Shapely-Version in pyproject.toml pinnen (`shapely>=2.0,<3.0`)
