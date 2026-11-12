# Revenge (A01 Nr. 3) v1.1

76 x 38 Kacheln zu 16 px (1216 x 608 px).

## Inhalt
Zwei Raeume: links mit drei Druckplatten (spiegelsymmetrisch), rechts ein Hafen mit Wasserbecken und Pollern; Ausgang ueber goldene Pfeile.

Alle Bodenkanten liegen am 16er-Raster mit 45-Grad-Schraegen; Objekte stehen am Raster, hohe Objekte blockieren nur
am Sockel. Kontrolliert nach allen Regeln (CLAUDE.md) inkl. Agenten-Gesamtpruefung.

## Animation
- `Revenge_v1.1_discord_16.gif` - 16 Bilder, 110 ms (fluessige Fassung)
- `Revenge_v1.1_discord.gif` - 4 Bilder (Takt der Tilesets)
Bewegt sich nur, was sich wirklich bewegt (Wasser, Feuer, Licht, Pflanzen im Wind, Stoff, Maschinen); Steine,
Stangen und Mauern bleiben ruhig.

## Dateien
- `Revenge_v1.1.png` - Standbild
- `kollision/` - `kollision.json`, `kollision.txt` (1 begehbar, 2 gesperrt, 3 begehbar + verdeckt),
  `ebene2_kollision.png`, `kollision_overlay.png`
- `tileset/` - Boden- und Objekt-Tilesets am 16x16-Raster, animierte Teile am exakt selben Platz, Tiled-Karte (`.tmx`)

Erzeugt mit `tools/karte19_*.py`, `tools/kollision.py`, `tools/tileset_export.py`, `tools/paket_a02.py`.
