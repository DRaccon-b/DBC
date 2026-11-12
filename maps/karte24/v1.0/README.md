# The Kaisers Canyon (A02 Nr. 4) v1.0

100 x 85 Kacheln zu 16 px (1600 x 1360 px).

## Inhalt
Roter Canyon: Schrein-Arena mit Bannern, Mine mit Loren und Oelpumpe, Seilbahn mit wippenden Gondeln, Lager und Bergstation.

Alle Bodenkanten liegen am 16er-Raster mit 45-Grad-Schraegen; Objekte stehen am Raster, hohe Objekte blockieren nur
am Sockel. Kontrolliert nach allen Regeln (CLAUDE.md) inkl. Agenten-Gesamtpruefung.

## Animation
- `The_Kaisers_Canyon_v1.0_discord_16.gif` - 16 Bilder, 110 ms (fluessige Fassung)
- `The_Kaisers_Canyon_v1.0_discord.gif` - 4 Bilder (Takt der Tilesets)
Bewegt sich nur, was sich wirklich bewegt (Wasser, Feuer, Licht, Pflanzen im Wind, Stoff, Maschinen); Steine,
Stangen und Mauern bleiben ruhig.

## Dateien
- `The_Kaisers_Canyon_v1.0.png` - Standbild
- `kollision/` - `kollision.json`, `kollision.txt` (1 begehbar, 2 gesperrt, 3 begehbar + verdeckt),
  `ebene2_kollision.png`, `kollision_overlay.png`
- `tileset/` - Boden- und Objekt-Tilesets am 16x16-Raster, animierte Teile am exakt selben Platz, Tiled-Karte (`.tmx`)

Erzeugt mit `tools/karte24_*.py`, `tools/kollision.py`, `tools/tileset_export.py`, `tools/paket_a02.py`.
