# Karte 01

Fertige Karte: `terrain.png` (1760×1920 px, 110×120 Kacheln à 16×16).
Ohne Objekte: `terrain_basis.png`. Kachelzuordnung: `tilemap.json`.

## Neu bauen

```bash
python3 tools/basis_kacheln.py      # Grundkacheln Gras/Sand/Wasser/Meer (je 5 Varianten)
python3 tools/karte_bauen.py        # Boden + Klippen  (schreibt tilemap.json mit Klassen)
python3 tools/objekte_setzen.py     # Wald, Deko, Sonderobjekte -> platzierung.json
python3 tools/karte_bauen.py        # fertige Karte mit Objekten
```

## Aufbau

| Ebene | Quelle | Datei |
|---|---|---|
| Grundkacheln | handgezeichnet (Skript) | `tools/basis_kacheln.py` → `assets/basis/` |
| Übergänge Gras/Sand/Wasser/Meer | PixelLab Pro-Tilesets, Grundkacheln als exakte Referenz | `assets/tilesets/pixellab/` |
| Klippen (3–4 Kacheln hoch) und Wasserfall | handgezeichnet (Skript) | `tools/klippen.py` |
| Bäume, Deko, Brücken, Treppen, Zelt … | PixelLab-Objekt-Manager | `assets/objekte/karte01/{baeume,deko,gross}/` |

- Geländetypen je Kachel: `terrain_grid.json` (aus dem Original abgeleitet).
- Klippenverlauf, Wandhöhe `h`, Treppen, Brücken, Steg: `hoehenplan.json`.
- Welche Objekt-Kandidaten wo verwendet werden: `AUSWAHL` und `FEST` in `tools/objekte_setzen.py`
  (Nummern siehe `uebersicht.png` der jeweiligen Gruppe).
- Neue Objektgruppen: `tools/pixellab_objekte.py` (braucht `PIXELLAB_API_KEY`).

## Stilregeln (Handheld-Monster-RPG-Look, 16 px)

- Bodenkacheln ohne Outlines, kontrastarme Textur, Hue-Shifting (Schatten → blaugrün, Licht → gelblich).
- Übergänge ohne Linie: dunklerer Rand + Saum.
- Objekte mit farbiger dunkler Kontur (nie Schwarz), Licht von oben links, runde gebündelte Formen,
  weicher Bodenschatten.
