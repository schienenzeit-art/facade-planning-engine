# ADR-005: Panelisierungs-Algorithmus — Strategy-Pattern

**Status:** Accepted  
**Datum:** 2026-06-08  
**Entscheider:** Softwarearchitektur  

---

## Kontext

Die Panelisierung ist die Kernintelligenz des Systems. Es gibt grundlegend verschiedene Ansätze zur Aufteilung einer Fassadenfläche in Panels:

1. **Grid-basiert:** Regelmässiges Raster, Panels an Rasterteilungen
2. **Optimierend:** Minimierung von Verschnitt / Maximierung von Vollplatten
3. **Regelbasiert mit Constraints:** Bestimmte Fugen-, Start- oder Ausrichtungsregeln
4. **Hybride Ansätze:** Grid mit lokaler Optimierung

Im MVP brauchen wir zunächst den einfachsten funktionierenden Algorithmus. In v1.1/v2.0 können komplexere Algorithmen hinzukommen.

## Entscheidung

Der Panelisierungs-Algorithmus wird hinter einer **abstrakten Basisklasse (Strategy-Pattern)** implementiert:

```python
class BasePanelizationAlgorithm(ABC):
    @abstractmethod
    def execute(
        self,
        surface: FacadeSurface,
        formats: List[PanelFormat],
        config: PanelizationConfig
    ) -> List[Panel]:
        ...
```

**MVP-Implementierung:** `GridPanelizationAlgorithm`
- Teilt Fassadenfläche in reguläres Grid (Zeilen × Spalten)
- Wählt grösstes verfügbares Format als Grid-Basis
- Schneidet Öffnungen aus
- Erzeugt Randpanel-Zuschnitte

Der konkrete Algorithmus wird dem PanelizationService injiziert — der Service kennt nur die Abstraktion.

## Alternativen betrachtet

| Alternative | Warum verworfen |
|-------------|----------------|
| Direktimplementierung im Service | Nicht austauschbar; v1.1-Erweiterungen erfordern Refactoring |
| Sofort optimierender Algorithmus | Zu komplex für MVP; Anforderungen an Optimierungsziele unklar |
| Plugin-System (extern ladbar) | Overkill für MVP; zu frühe Abstraktion |

## Konsequenzen

**Positiv:**
- Algorithmus ist unabhängig vom Service testbar
- Neuer Algorithmus in v1.1 ohne Änderung am Service
- Klare Schnittstelle: Input/Output klar definiert

**Negativ:**
- Abstraktion muss stabil bleiben — Breaking Changes an der Signatur betreffen alle Algorithmen
- Leicht mehr Code als eine direkte Implementierung

## MVP-Algorithmus: GridPanelizationAlgorithm — Verhalten

```
Gegeben: FacadeSurface (6000×3000mm), PanelFormat (1200×600mm), Joint: 10mm

1. Berechne Grid-Dimensionen:
   - Spalten = ceil(6000 / (1200 + 10)) = 5 Spalten
   - Zeilen  = ceil(3000 / (600 + 10))  = 5 Zeilen

2. Erzeuge Panels (Zeile × Spalte):
   - Vollplatten: 1200×600mm wo möglich
   - Randpanele: Reste (z.B. letztes Panel = 6000 - 4*(1200+10) - 10 = 1150mm)

3. Für jedes Panel: Prüfe Öffnungsüberlappung
   - Kein Overlap → Panel normal
   - Overlap → Panel entfernen (Öffnung)
   - Teilüberlap → (MVP: entfernen; v1.1: aufteilen)

4. Validiere Invarianten
```

## Offene Fragen für v1.1

- Sollen teilweise überlappende Panels (Öffnung im Panel) aufgeteilt werden?
- Soll der Algorithmus den Startpunkt des Grids konfigurierbar machen? (z.B. Mitte, Ecke)
- Ist eine Materialoptimierung (Minimierung Verschnitt) gewünscht?

## Risiken

- **RISK:** Grid-Algorithmus für nicht-rechteckige Fassadenflächen komplex → MVP beschränkt sich auf rechteckige Flächen
- **Mitigation:** Explizit in Dokumentation und Fehlerbehandlung: "Nicht-rechteckige Flächen werden in v1.1 unterstützt"
