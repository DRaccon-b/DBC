# Tower Forest (A02 Nr. 8) v1.1

100 x 85 Kacheln zu 16 px (1600 x 1360 px).

## Inhalt
Dunkler Wald mit Schlamm-Arena, Spinnen-Arena, schwarzen Obelisken, Wiesen mit Lagerfeuer und geschwungenen Feldwegen.

Alle Bodenkanten liegen am 16er-Raster mit 45-Grad-Schraegen; Objekte stehen am Raster, hohe Objekte blockieren nur
am Sockel. Kontrolliert nach allen Regeln (CLAUDE.md) inkl. Agenten-Gesamtpruefung.

## Animation
- `Tower_Forest_v1.1_discord_16.gif` - 16 Bilder, 110 ms (fluessige Fassung)
- `Tower_Forest_v1.1_discord.gif` - 4 Bilder (Takt der Tilesets)
Bewegt sich nur, was sich wirklich bewegt (Wasser, Feuer, Licht, Pflanzen im Wind, Stoff, Maschinen); Steine,
Stangen und Mauern bleiben ruhig.

## Dateien
- `Tower_Forest_v1.1.png` - Standbild
- `kollision/` - `kollision.json`, `kollision.txt` (1 begehbar, 2 gesperrt, 3 begehbar + verdeckt),
  `ebene2_kollision.png`, `kollision_overlay.png`
- `tileset/` - Boden- und Objekt-Tilesets am 16x16-Raster, animierte Teile am exakt selben Platz, Tiled-Karte (`.tmx`)

Erzeugt mit `tools/karte28_*.py`, `tools/kollision.py`, `tools/tileset_export.py`, `tools/paket_a02.py`.
