# Karte 28 – Tower Forest (A02) v1.0

100 × 85 Kacheln à 16 px (1600 × 1360), Vorlage `assets/vorlagen/karte28_vorlage.png`. Spielt in einem dunklen Wald.

## Inhalt der Karte
- **Dunkler Wald ringsum**: Gras-, Weg- und Erdkacheln von Karte 01 (GBA-Stil), dunkler und kühler gefärbt;
  dunkle Waldbäume (umgefärbt aus Karte 01, `tools/karte28_baeume.py`).
- **Schlamm-Arena** links als Erhöhung: nasse Walderde mit Rissen und Erdflecken, Grasrand mit sichtbarer
  Plateaukante im Norden und an den Seiten, Steinfront mit zwei Steintreppen im Süden. Wurzeln, Totholz,
  Findlinge, Stämme, Pilze, Pfützen, Spinnweben in den oberen Ecken.
- **Spinnen-Arena** rechts auf dem Steinplatz: unregelmäßige Ringmauer am 16er-Raster (2 Kacheln dick, Fronten,
  Torlücke unten), Spinnweben hängen an Mauerkrone und Fronten; dunkle Kristallbrocken, umgestürzter Turm am Weg.
- **12 schwarze Obelisken** (Türme) nach der Vorlage, ohne Leuchten.
- **Wiesen** mit Feldwegen, einzelnen Bäumen mit Begleitern (Regel 5d), kleinen Nadelbäumen, Lagerfeuer mit
  Sitzstämmen, Wegweiser, Laterne, Pilzen und Büscheln.
- **Ausgänge** (Teleporter) oben rechts und unten in der Mitte.

## Animation (4 Bilder, 250 ms)
Bäume, Gräser und Blumen im Wind, Lagerfeuer, Laterne, Teleporter. Steine, Mauern, Obelisken und Kristalle sind
unbewegt.

## Dateien
- `Tower_Forest_v1.0.png` – Standbild, `Tower_Forest_v1.0_discord.gif` – Animation für Discord (2×).
- `kollision/` – Kollisionsraster (`kollision.json`, `.txt`, `ebene2_kollision.png`, `kollision_overlay.png`):
  blockiert sind Wald, Mauer der Spinnen-Arena, Arena-Front und Plateaukanten sowie die Füße der Objekte;
  die zwei Treppen führen in die Schlamm-Arena.

Erzeugt mit `tools/karte28_layout.py`, `karte28_bauen.py`, `karte28_baeume.py`, `karte28_objekte.py`,
`karte28_animation.py`, `kollision.py karte28`, `tileset_export.py karte28`. Neue Objekte: PixelLab
Objekt-Creator (`k28_*`).
