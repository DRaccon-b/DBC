# Karte 11 – Spiral Mountain: Dark Ocean v1.0

80 × 70 Kacheln à 16 px (1280 × 1120), Vorlage `assets/vorlagen/karte11_vorlage.png`.
Links schwarzes, verseuchtes Land, rechts das Meer der Finsternis – erste Karte der Spiral-Mountain-Reihe.

## Inhalt der Karte
- **Rand:** Bergwand ringsum (dieselbe wie Puppet Woods, Machine City und Summit), Teleporter oben und links.
- **Land:** schwarze Asche, ölige Tümpel, zwei lila Plateaus mit Treppen und toten Bäumen, Felsblock, Ruinen-Platz
  mit Feuerschalen, Walskelett, gestrandetes Wrack, Anker, Mastbruch, Treibholz, Kristalle, Knochen.
- **Meer:** türkises Flachwasser mit Seetangfeldern, Korallen, Anemone, Kristall; Tiefsee in fünf Stufen bis zum
  Kartenrand im öligen Schwarz-Violett, Felsnadeln (kleiner, je tiefer das Wasser), versunkenes Wrack.
- **Bannkreis-Plattform:** Achteck, dessen Mauer bis zum Meeresgrund reicht, Bannkreis mit Spirale, Runensäulen
  und Feuerschalen spiegelgleich; Steinbrücke mit Bögen und Pfeilern bis zum Grund, Brückenkopf mit Laternen.

## Animation (16 Bilder, 170 ms)
Flachwasser (Lichtnetz), Tiefsee (Wellenkämme), Schaum am Ufer, Seetang im Wind, Tümpel (Ölhaut), Feuerschalen,
Geisterlaternen, Runensäulen und Kristalle (Glimmen), Bannkreis (Spirale dreht sich), Teleporter.

## Dateien
- `Spiral_Mountain_Dark_Ocean_v1.0.png` – Standbild, `Spiral_Mountain_Dark_Ocean_v1.0_discord.gif` – Animation.
- `kollision/` – Kollisionsraster (`kollision.json`, `.txt`, `ebene2_kollision.png`, `kollision_overlay.png`).

Erzeugt mit `tools/karte11_layout.py`, `karte11_kacheln.py`, `karte11_bauen.py`, `karte11_objekte.py`,
`regeln_v11.py karte11`, `karte11_animation.py`, `kollision.py karte11`, `tileset_export.py karte11`.
