# Karte 14 – Spiral Mountain: Summit v1.0

80 × 70 Kacheln à 16 px (1280 × 1120), Vorlage `assets/vorlagen/karte14_vorlage.png`.
Der Gipfel des Spiral Mountain – letzte Karte der Spiral-Mountain-Reihe. Anspielungen auf die Herren des Gipfels
(Gaukler, Ritter, dunkle Dame, Endgegner hinter dem Portal) nur über Motive und Farben, keine Figur nachgebaut.

## Inhalt der Karte
- **Rand:** dieselbe Bergwand wie Dark Ocean, Puppet Woods und Machine City; schwarze Wolken vom Kartenrand
  angeschnitten, funkelnde Sterne (Punkte, Kreuze, Funkelsterne in Weiß, Violett, Gold, Hellblau).
- **Gauklerschloss:** frontal mit Harlekin-Rauten und roten Kegeldächern, Burgmauern und Ecktürme exakt
  spiegelsymmetrisch zur Achse.
- **Boss-Feld:** Achteck eine Etage höher, liegt als Ebene vor der Burg; roter Teppich, Harlekin-Schachbrettsaum
  und -ring, goldene Kartenzeichen, große Spirale in der Mitte, Narrenthron, vier Feuerschalen, zwei Kandelaber,
  Ziegelfront mit Goldband und Pfeilern, Treppe.
- **Schachbrettweg:** 5 Kacheln breit auf der Achse, Statuen (Gaukler, Ritter, Flügeldamen) und Banner paarweise
  gespiegelt, gestufter Treppenplatz mit Feuerschalen, Truhe, Zylinder, Teleporter unten.
- **Eingang zum Endgegner:** unregelmäßige Portal-Ebene mit Apsis und Treppe, Leere-Portal, Siegel mit
  Licht-Rissen, schwarze Kristallsplitter, Obelisken mit blinzelndem Auge, Schattenklauen, Datenwürfel, Ketten,
  Eierschalen, Steinkreis.
- **Gipfel:** Felsnasen (eine Etage höher), dunkler Schotter, Kristallboden mit Kristallen, Spielkarten-Monolithe,
  stehende Spielkarten, Schwerter im Fels, Masken, Kleinkram.

## Animation (16 Bilder, 170 ms)
Spirale (dreht, pulsiert), Siegel, Portalwirbel (dreht), Teleporter, Feuerschalen (violette Flammen), Kandelaber,
Kristalle und Leere-Elemente (glimmen), Obelisk-Augen (blinzeln), Banner (nur das Tuch), Wolken (treiben),
Sterne (funkeln), Gras.

## Dateien
- `Spiral_Mountain_Summit_v1.0.png` – Standbild, `Spiral_Mountain_Summit_v1.0_discord.gif` – Animation für Discord.
- `kollision/` – Kollisionsraster (`kollision.json`, `.txt`, `ebene2_kollision.png`, `kollision_overlay.png`).

Erzeugt mit `tools/karte14_layout.py`, `karte14_kacheln.py`, `karte14_bauen.py`, `karte14_objekte.py`,
`regeln_v11.py karte14`, `karte14_animation.py`, `kollision.py karte14`, `tileset_export.py karte14`.
