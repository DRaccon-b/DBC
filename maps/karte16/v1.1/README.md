# The Network (A01 Nr. 1) v1.1

64 x 40 Kacheln zu 16 px (1024 x 640 px).

## Inhalt
Ankunft im Netz: schmaler Steg zur runden Plattform mit Firewall-Tor und Computer "Dungeon Records"; Leere mit blauen Datenstraengen und schwebenden Fragmenten.

Alle Bodenkanten liegen am 16er-Raster mit 45-Grad-Schraegen; Objekte stehen am Raster, hohe Objekte blockieren nur
am Sockel. Kontrolliert nach allen Regeln (CLAUDE.md) inkl. Agenten-Gesamtpruefung.

## Animation
- `The_Network_v1.1_discord_16.gif` - 16 Bilder, 110 ms (fluessige Fassung)
- `The_Network_v1.1_discord.gif` - 4 Bilder (Takt der Tilesets)
Bewegt sich nur, was sich wirklich bewegt (Wasser, Feuer, Licht, Pflanzen im Wind, Stoff, Maschinen); Steine,
Stangen und Mauern bleiben ruhig.

## Dateien
- `The_Network_v1.1.png` - Standbild
- `kollision/` - `kollision.json`, `kollision.txt` (1 begehbar, 2 gesperrt, 3 begehbar + verdeckt),
  `ebene2_kollision.png`, `kollision_overlay.png`
- `tileset/` - Boden- und Objekt-Tilesets am 16x16-Raster, animierte Teile am exakt selben Platz, Tiled-Karte (`.tmx`)

Erzeugt mit `tools/karte16_*.py`, `tools/kollision.py`, `tools/tileset_export.py`, `tools/paket_a02.py`.
