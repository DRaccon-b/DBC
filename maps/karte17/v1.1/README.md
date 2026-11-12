# Our War Game (A01 Nr. 2) v1.1

76 x 36 Kacheln zu 16 px (1216 x 576 px).

## Inhalt
Zwei schwebende Raeume im Netz, verbunden ueber die Leere; Aufstellfelder, Marker und Teleporter im Stil von Karte 16.

Alle Bodenkanten liegen am 16er-Raster mit 45-Grad-Schraegen; Objekte stehen am Raster, hohe Objekte blockieren nur
am Sockel. Kontrolliert nach allen Regeln (CLAUDE.md) inkl. Agenten-Gesamtpruefung.

## Animation
- `Our_War_Game_v1.1_discord_16.gif` - 16 Bilder, 110 ms (fluessige Fassung)
- `Our_War_Game_v1.1_discord.gif` - 4 Bilder (Takt der Tilesets)
Bewegt sich nur, was sich wirklich bewegt (Wasser, Feuer, Licht, Pflanzen im Wind, Stoff, Maschinen); Steine,
Stangen und Mauern bleiben ruhig.

## Dateien
- `Our_War_Game_v1.1.png` - Standbild
- `kollision/` - `kollision.json`, `kollision.txt` (1 begehbar, 2 gesperrt, 3 begehbar + verdeckt),
  `ebene2_kollision.png`, `kollision_overlay.png`
- `tileset/` - Boden- und Objekt-Tilesets am 16x16-Raster, animierte Teile am exakt selben Platz, Tiled-Karte (`.tmx`)

Erzeugt mit `tools/karte17_*.py`, `tools/kollision.py`, `tools/tileset_export.py`, `tools/paket_a02.py`.
