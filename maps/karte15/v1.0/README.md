# Karte 15 – Apocalymon's Realm v1.0

40 × 40 Kacheln à 16 px (640 × 640), Vorlage `assets/vorlagen/karte15_vorlage.png`.
Das Reich hinter dem Portal des Summit: eine runde Steininsel schwebt in der Leere. Anspielungen nur über Farben
und Motive (Leere, Daten, verlorene Welten) – nichts nachgebaut.

## Inhalt der Karte
- **Insel:** Steinziegel mit vereinzelten violetten Kristallsplittern, dunkler Randring mit magenta glimmender
  Kante, alle Ränder gestuft am 16×16-Raster (wie die Vorlage). Im Boden zwei helle Ringe mit Zeichen, feine
  Strahlen und violett leuchtende Risse; Boss-Spawn in der Mitte (Kachel 20/19), ohne Objekte.
- **Felsbauch:** unter der Südkante hängt der Fels als Kegel (Mitte tief, Seiten schmal), zackige Felszapfen,
  verliert sich in der Leere, violette Leuchtadern.
- **Steg:** auf der Achse nach Süden, Bordsteine, Teleporter am unteren Rand.
- **Leere:** Sternenraum mit Nebel, funkelnden Sternen und flackernden Datenstrichen.
- **Verlorene Welten:** 12 schwebende Brocken der bisherigen Karten – Wiese (01), Industrie (02), Wüste (03),
  Gear Savanna (04), Freezeland (05), Overdell (08), Vamdemon's Keep (09), Toy Town (10), Dark Ocean (11),
  Puppet Woods (12), Machine City (13), Summit (14).

## Animation (4 Bilder, 250 ms – Regel: höchstens 4 Animationsbilder)
Sterne (funkeln), Datenstriche (flackern), Inselkante (glimmt), Leuchtadern im Felsbauch, Bodenrisse (pulsieren),
Teleporter, schwebende Brocken (1 px auf und ab).

## Dateien
- `Apocalymons_Realm_v1.0.png` – Standbild (640 × 640), `Apocalymons_Realm_v1.0_discord.gif` – Animation für
  Discord (2× vergrößert, 1280 × 1280).
- `kollision/` – Kollisionsraster (`kollision.json`, `.txt`, `ebene2_kollision.png`, `kollision_overlay.png`):
  begehbar sind Insel und Steg, blockiert sind Leere, Felsbauch und die schwebenden Brocken.

Erzeugt mit `tools/karte15_layout.py`, `karte15_kacheln.py`, `karte15_bauen.py`, `karte15_objekte.py`,
`karte15_animation.py`, `kollision.py karte15`, `tileset_export.py karte15`.
