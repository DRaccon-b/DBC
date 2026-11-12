# Sunset Bay (A02 Nr. 5) v1.0

120 x 80 Kacheln zu 16 px (1920 x 1280 px).

## Inhalt
Strand mit Huetten, Palmen und Stegen, Plateau mit Leuchtturm, terrassiertes Meer mit Schaum am 45-Grad-Raster und das Kaiser-Flaggschiff.

Alle Bodenkanten liegen am 16er-Raster mit 45-Grad-Schraegen; Objekte stehen am Raster, hohe Objekte blockieren nur
am Sockel. Kontrolliert nach allen Regeln (CLAUDE.md) inkl. Agenten-Gesamtpruefung.

## Animation
- `Sunset_Bay_v1.0_discord_16.gif` - 16 Bilder, 110 ms (fluessige Fassung)
- `Sunset_Bay_v1.0_discord.gif` - 4 Bilder (Takt der Tilesets)
Bewegt sich nur, was sich wirklich bewegt (Wasser, Feuer, Licht, Pflanzen im Wind, Stoff, Maschinen); Steine,
Stangen und Mauern bleiben ruhig.

## Dateien
- `Sunset_Bay_v1.0.png` - Standbild
- `kollision/` - `kollision.json`, `kollision.txt` (1 begehbar, 2 gesperrt, 3 begehbar + verdeckt),
  `ebene2_kollision.png`, `kollision_overlay.png`
- `tileset/` - Boden- und Objekt-Tilesets am 16x16-Raster, animierte Teile am exakt selben Platz, Tiled-Karte (`.tmx`)

Erzeugt mit `tools/karte25_*.py`, `tools/kollision.py`, `tools/tileset_export.py`, `tools/paket_a02.py`.
