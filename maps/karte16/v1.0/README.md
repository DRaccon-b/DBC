# Karte 16 – The Network v1.0

64 × 40 Kacheln à 16 px (1024 × 640), Vorlage `assets/vorlagen/karte16_vorlage.png` (echtes 16er-Raster).
Ein Raum im digitalen Netz: Eine runde Plattform schwebt in der Leere, oben das Firewall-Tor. Anspielungen nur
über Farben und Motive, nichts nachgebaut.

## Inhalt der Karte
- **Ankunft:** unten auf 4 cyan Pfeilmarken (Teleporter; Eckklammern + Doppelpfeil direkt auf dem Boden, wie auf Karte 17/19), kleines Ankunftsfeld.
- **Pfad:** schmaler Pfad (2 Kacheln) mit cyan Leitlinien nach Norden zur Plattform.
- **Plattform:** kreisrund am 16er-Raster gestuft, Bodenplatten der Vorlage, dunkler Randring mit cyan glimmender
  Kante, zwei Leuchtringe im Boden; unter der Südkante eine schmale Metallfront mit hängenden Lichtfäden.
- **Firewall-Tor:** oben auf der Plattform, exakt auf der Achse von Pfad und Pfeilfeld.
- **Computer „Dungeon Records“:** links auf halber Höhe der Plattform, mittig auf den Leuchtringen.
- **Leere:** feines Netzraster, blauer Nebel, links und rechts blaue Datenstränge (Datenpakete laufen nach unten)
  und schwebende Datenfragmente (losgerissene Bodenplatten, Datenwürfel).

## Animation (4 Bilder, 250 ms – Regel: höchstens 4 Animationsbilder)
Datenpakete auf den Strängen, Fragmente schweben (1 px), Kanten und Leuchtringe glimmen, Pfeilmarken leuchten
nacheinander, Lichtfäden unter der Plattform, Tor (roter Bildschirm pulsiert, das Fadenkreuz dreht sich, Lichtimpuls auf den Leiterbahnen),
Computer (Balken flackern, gelbe Punkte blinken). Rahmen, Gehäuse und Boden bleiben ruhig.

## Dateien
- `The_Network_v1.0.png` – Standbild (1024 × 640), `The_Network_v1.0_discord.gif` – Animation für Discord
  (2× vergrößert, 2048 × 1280).
- `kollision/` – Kollisionsraster (`kollision.json`, `.txt`, `ebene2_kollision.png`, `kollision_overlay.png`):
  begehbar sind Ankunftsfeld, Pfad und Plattform (eine zusammenhängende Fläche); blockiert sind die Leere sowie die
  Füße von Tor und Computer.

Erzeugt mit `tools/karte16_layout.py`, `karte16_bauen.py`, `karte16_objekte.py`, `karte16_animation.py`,
`kollision.py karte16`, `tileset_export.py karte16`.
