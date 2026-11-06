# Karte 05 (Freezeland) – v1.1

Neue Fassung nach den Regeln in `CLAUDE.md`. v1.0 liegt in `maps/karte05/v1.0/` (Bild, GIF, Platzierung, Layout).

## Änderungen
- **Regel 1/1b – Raster:** jedes Objekt im kleinsten Kachelblock, waagerecht zentriert, Fuß bündig auf der Kachelkante.
- **Regel 6 – Wege:** natürliche Bögen statt eckiger Wege; Treppen, Teleporter, Klippen und Kartenrand bleiben fest.
- **Regel 2 – Treppen:** unter jeder Treppe ein Wegstück in voller Breite; Treppenzugang frei von Objekten (3× geprüft).
- **Bäume:** unverändert dicht wie in v1.0 (Baum-Änderungen nach Regel 8 auf Wunsch verworfen).
- **Regel 5 – Einzelbäume:** Begleitung aus den Schnee-Sets (Frostgras, Farn, Schneeglöckchen …) bzw. zweite kleine Tanne;
  Bäume ohne Platz für Begleitung entfernt.
- **Einbettung:** Felsen bekommen Frostgras/Schneeblumen an den Sockelecken.
- **Wehen nur am Stoff:** Die Dorffahne weht nur noch am Banner, Mast und Querstange bleiben ruhig.
- **Regel 7 / Kontrolle:** Schatten nur auf der eigenen Ebene (nie über Klippe/Wasser/Spalte); keine ungewollten Überlappungen.

## Neue Objekte (PixelLab, Stil Karte 05)
- **Kaputte Server** (3×): vereiste Serverschränke mit Kabeln, je mit Eisblume/Frostgras vor dem Sockel.
- **Teich, Bach und Wasserfall:** Teich auf dem Mittelplateau, Bach zur Kante, Wasserfall (Stil Karte 01, animiert)
  an der Stelle der früheren mittleren Treppe, unten weiter als Bach mit Holzbrücke über den Weg in den
  zugefrorenen See. Die mittlere Treppe und der gefrorene Wasserfall-Objekt sind entfernt.
- **Senkrechte Kanten:** Plateaus haben seitlich keine sichtbare Seitenwand mehr, nur eine schmale Abgrenzung
  (Kontur + leichter Schatten); die Höhenregel bleibt (man kommt seitlich nicht hoch).
- **Mehr Deko oben:** kleine Tannen, verschneite Büsche, Eiskristalle, Eisblumen, Beeren, halb eingeschneite Felsen.
- **Oben mehr Variation:** zwei Server, große Eiszapfen/Eiskristalle, große Tannen (mit Pflanzen vor dem Sockel).
- **Eishöhle:** ursprüngliche Höhle mit gesäuberten, felsartigen Kanten; links/rechts je eine Tanne als Übergang.
- **Links oben:** mehr Schneetannen und kahle Frostbäume dieser Karte, Deko unregelmäßig statt in Reihen.
- **Verdeckung:** Objekte auf dem unteren Boden werden vom seitlich daneben liegenden Plateau abgeschnitten.
- **Schatten liegender Objekte:** Äste, Knochen usw. werfen den Schatten über ihre ganze Form (leicht nach rechts
  unten versetzt) statt nur vom untersten Punkt aus.
- **Waldrand oben:** Tannen entlang des oberen Kartenrands (wie links/rechts/unten).
- **Eisblumen** (zwei Sorten) verstreut und als Begleitblumen vor Sockeln.
- **Verschneite Beerensträucher** (Beeren, Stechpalme) verstreut.
- **Halb eingeschneite Felsen** (klein) und **Findlinge** (groß, 3×) – mit Einbettung an den Sockelecken.

## Neu bauen
```bash
python3 tools/karte05_v11.py wege && python3 tools/karte05_bauen.py
python3 tools/karte05_objekte.py && python3 tools/karte05_v11.py objekte
python3 tools/karte05_bauen.py && python3 tools/karte05_animation.py
```
