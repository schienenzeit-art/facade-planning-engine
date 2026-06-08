# ADR-003: Dateibasierte Persistenz (kein RDBMS im MVP)

**Status:** Accepted  
**Datum:** 2026-06-08  
**Entscheider:** Softwarearchitektur  

---

## Kontext

Die Facade Planning Engine ist im MVP ein lokales CLI-Tool. Es gibt keine Anforderung an Mehrbenutzer-Betrieb, Netzwerkzugriff oder zentrale Datenverwaltung. Die Persistenz muss einfach, offline-fähig und ohne Installation von Datenbankservern funktionieren.

## Entscheidung

Im MVP wird **ausschliesslich dateibasierte Persistenz** verwendet:
- Alle Domänenobjekte werden als **JSON-Dateien** serialisiert (via Pydantic)
- Projektdaten liegen in einem **Projektverzeichnis** auf dem Dateisystem
- Kein externer Datenbankserver erforderlich

## Alternativen betrachtet

| Alternative | Warum verworfen |
|-------------|----------------|
| SQLite | Sinnvoll, aber Overhead für MVP; erschwerter Debugging-Zugang ohne DB-Tool |
| PostgreSQL | Infrastrukturabhängigkeit, nicht offline-fähig, Overkill für MVP |
| SQLite (mit SQLAlchemy) | Gute Erweiterungsoption, aber unnötige Komplexität in MVP |
| TinyDB | Zusätzliche Abhängigkeit, bietet keinen Vorteil über plain JSON |

## Konsequenzen

**Positiv:**
- Kein Infrastruktur-Setup für Nutzer
- Projektdateien sind lesbar (JSON) und versionierbar (Git)
- Einfaches Debugging (Dateien direkt einsehbar)
- Offline-Betrieb

**Negativ:**
- Keine komplexen Queries (Joins, Aggregationen)
- Keine ACID-Transaktionen
- Performance-Probleme bei sehr vielen Projekten (unwahrscheinlich in MVP)
- Kein Mehrbenutzer-Zugriff

## Erweiterungspfad

Das **Repository-Pattern** kapselt die gesamte Persistenzlogik. Für v2.0 (falls Netzwerk/Multi-User benötigt wird) wird nur eine neue Repository-Implementierung benötigt, ohne Änderung an Domäne oder Use Cases.

```python
# Port-Interface bleibt stabil:
class FacadeSurfaceRepository(ABC):
    def save(self, surface: FacadeSurface) -> None: ...
    def load(self, id: FacadeSurfaceId) -> FacadeSurface: ...
    def list_all(self) -> List[FacadeSurface]: ...

# MVP: FileSystemFacadeSurfaceRepository
# v2.0: SQLiteFacadeSurfaceRepository oder PostgresFacadeSurfaceRepository
```

## Risiken

- **RISK:** Grosse Geometrie-Dateien (viele Panels) können Ladezeiten erhöhen
- **Mitigation:** Panels und Geometrien werden in separaten Dateien gespeichert (lazy loading möglich)
- **RISK:** Gleichzeitiger Zugriff auf Projektdateien nicht sicher
- **Mitigation:** Explizite Dokumentation: MVP ist Einzelnutzer-Tool; kein Concurrent-Access
