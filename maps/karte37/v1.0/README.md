# Hypnos Rooftop (A03 Nr. 4) v1.0

48 x 36 Kacheln zu 16 px (768 x 576 px).

## Inhalt
Dach des Hypnos-Hochhauses ueber Shinjuku: helle Ziegelwege und tiefer liegende Dachflaeche mit Lueftungsgittern, Faesser, Tanks, Laternen; am Rand der Blick hinunter auf die Stadt von Shinjuku Digital Fog.

Alle Bodenkanten liegen am 16er-Raster mit 45-Grad-Schraegen; Objekte stehen am Raster, hohe Objekte blockieren nur
am Sockel. Kontrolliert nach allen Regeln (CLAUDE.md) inkl. Agenten-Gesamtpruefung.

## Animation
- `Hypnos_Rooftop_v1.0_discord_16.gif` - 16 Bilder, 110 ms (fluessige Fassung)
- `Hypnos_Rooftop_v1.0_discord.gif` - 4 Bilder (Takt der Tilesets)
Bewegt sich nur, was sich wirklich bewegt (Wasser, Feuer, Licht, Pflanzen im Wind, Stoff, Maschinen); Steine,
Stangen und Mauern bleiben ruhig.

## Dateien
- `Hypnos_Rooftop_v1.0.png` - Standbild
- `kollision/` - `kollision.json`, `kollision.txt` (1 begehbar, 2 gesperrt, 3 begehbar + verdeckt),
  `ebene2_kollision.png`, `kollision_overlay.png`
- `tileset/` - Boden- und Objekt-Tilesets am 16x16-Raster, animierte Teile am exakt selben Platz, Tiled-Karte (`.tmx`)

Erzeugt mit `tools/karte37_*.py`, `tools/kollision.py`, `tools/tileset_export.py`, `tools/paket_a02.py`.
