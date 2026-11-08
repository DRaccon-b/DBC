# Karte 18 – The Fog-Bound City v1.0

136 × 112 Kacheln à 16 px (2176 × 1792), Vorlage `assets/vorlagen/karte18_vorlage.png`.
Eine Hafenstadt im Nebel im Handheld-Stil (Pflaster und Gras wie Karte 01). Anspielungen nur über Farben und
Motive, nichts originalgetreu nachgebaut.

## Inhalt der Karte
- **Straßen und Plätze:** Asphalt mit Zebrastreifen, Gehwege und Plätze aus Platten im GBA-Stil, Mittelstreifen
  und Beete mit Gras von Karte 01, Bordsteine.
- **Gebäude:** Häuserzeilen bündig ohne Abstand (Läden, Wohnhäuser), größere Lagerhallen, die Messehalle am
  Platz, Containerlager.
- **Hochbahn:** quer über die Karte, Pfeiler im festen Raster, Zug als Objekt; im Westen verschwindet sie im Nebel.
- **Hafen:** Kaimauer mit Brüstung, Mole, Hafenobjekte im Wasser (eingetaucht, mit Schaumring), Fähre.
- **Meer:** terrassiert wie auf Karte 01 (mehrere Tiefenstufen, Boden sichtbar), Brandung und Schaum.
- **Grünflächen:** Bäume von Karte 01, dazu goldene und rot-orange Herbstbäume, Blumen, Büschel, Unkraut mit
  weichem Übergang zum Pflaster.
- **Nebel und Wolken** an den Kartenrändern, zwei Teleporter.

## Animation (4 Bilder, 250 ms – Regel: höchstens 4 Animationsbilder)
Meer und Brandung, Schaumringe an den Hafenobjekten, schaukelnde Fähre, Laternen und Lichtkegel, Feuer, Ampeln,
Fahnen (nur der Stoff), Automaten, Leuchtreklamen.

## Dateien
- `The_Fog_Bound_City_v1.0.png` – Standbild (2176 × 1792), `The_Fog_Bound_City_v1.0_discord.gif` – Animation für
  Discord.
- `kollision/` – Kollisionsraster (`kollision.json`, `.txt`, `ebene2_kollision.png`, `kollision_overlay.png`):
  begehbar sind Straßen, Gehwege, Plätze, Grünflächen und Mole; blockiert sind Gebäude, Sockel, Wasser und Nebel.
  Alle begehbaren Felder bilden eine zusammenhängende Fläche.

Erzeugt mit `tools/karte18_layout.py`, `karte18_kacheln.py`, `karte18_gebaeude.py`, `karte18_objekte.py`,
`karte18_bauen.py`, `kollision.py karte18`, `karte18_animation.py`, `tileset_export.py karte18`.
