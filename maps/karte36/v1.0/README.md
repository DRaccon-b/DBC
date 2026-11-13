# Shinjuku Backstreets (A03 Nr. 3) v1.0

104 x 88 Kacheln zu 16 px (1664 x 1408 px).

## Inhalt
Shinjuku-Seitenstrassen: Wohn- und Buerobloecke, Ladenzeile mit Cafe, Mart, Buchladen, Drogerie und Ramen, Gruenstreifen mit Baeumen, Zebrastreifen, Autos, Baumguertel am Rand.

Alle Bodenkanten liegen am 16er-Raster mit 45-Grad-Schraegen; Objekte stehen am Raster, hohe Objekte blockieren nur
am Sockel. Kontrolliert nach allen Regeln (CLAUDE.md) inkl. Agenten-Gesamtpruefung.

## Animation
- `Shinjuku_Backstreets_v1.0_discord_16.gif` - 16 Bilder, 110 ms (fluessige Fassung)
- `Shinjuku_Backstreets_v1.0_discord.gif` - 4 Bilder (Takt der Tilesets)
Bewegt sich nur, was sich wirklich bewegt (Wasser, Feuer, Licht, Pflanzen im Wind, Stoff, Maschinen); Steine,
Stangen und Mauern bleiben ruhig.

## Dateien
- `Shinjuku_Backstreets_v1.0.png` - Standbild
- `kollision/` - `kollision.json`, `kollision.txt` (1 begehbar, 2 gesperrt, 3 begehbar + verdeckt),
  `ebene2_kollision.png`, `kollision_overlay.png`
- `tileset/` - Boden- und Objekt-Tilesets am 16x16-Raster, animierte Teile am exakt selben Platz, Tiled-Karte (`.tmx`)

Erzeugt mit `tools/karte36_*.py`, `tools/kollision.py`, `tools/tileset_export.py`, `tools/paket_a02.py`.
