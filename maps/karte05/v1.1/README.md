# Karte 05 (Freezeland) – v1.1

Neue Fassung nach den Regeln in `CLAUDE.md`. v1.0 liegt in `maps/karte05/v1.0/` (Bild, GIF, Platzierung, Layout).

## Änderungen
- **Regel 1/1b – Raster:** jedes Objekt im kleinsten Kachelblock, waagerecht zentriert, Fuß bündig auf der Kachelkante.
- **Regel 6 – Wege:** natürliche Bögen statt eckiger Wege; Treppen, Teleporter, Klippen und Kartenrand bleiben fest.
- **Regel 2 – Treppen:** unter jeder Treppe ein Wegstück in voller Breite; Treppenzugang frei von Objekten (3× geprüft).
- **Regel 8 – Bäume:** Überlappung nur an den äußeren Spalten (Waldrand: bis zwei Spalten), Sockel nie auf derselben Kachel;
  Waldrand danach neu gepackt (am Kartenrand dürfen Kronen über den Rand ragen), Lücken mit kleinen Tannen gefüllt.
- **Regel 5 – Einzelbäume:** Begleitung aus den Schnee-Sets (Frostgras, Farn, Schneeglöckchen …) bzw. zweite kleine Tanne;
  Bäume ohne Platz für Begleitung entfernt.
- **Einbettung:** Felsen bekommen Frostgras/Schneeblumen an den Sockelecken.
- **Wehen nur am Stoff:** Die Dorffahne weht nur noch am Banner, Mast und Querstange bleiben ruhig.
- **Regel 7 / Kontrolle:** Schatten nur auf der eigenen Ebene (nie über Klippe/Wasser/Spalte); keine ungewollten Überlappungen.

## Neu bauen
```bash
python3 tools/karte05_v11.py wege && python3 tools/karte05_bauen.py
python3 tools/karte05_objekte.py && python3 tools/karte05_v11.py objekte
python3 tools/karte05_bauen.py && python3 tools/karte05_animation.py
```
