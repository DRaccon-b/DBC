# Karte 17 – Our War Game! v1.0

76 × 36 Kacheln à 16 px (1216 × 576), Vorlage `assets/vorlagen/karte17_vorlage.png` (zwei Räume je 28 × 22 Kacheln).
Zweite Karte des Keramon-Dungeons, im Stil von Karte 16 (The Network): zwei schwebende Plattformen in der Leere
des Netzes. Anspielungen nur über Farben und Motive, nichts nachgebaut.

## Inhalt der Karte
- **Zwei Räume** als schwebende Plattformen (je 28 × 22 Kacheln, Ecken gestuft), Bodenplatten der Vorlage, dunkler
  Randring mit cyan glimmender Kante, schmale Metallfront mit hängenden Lichtfäden.
- **Aufstellfeld** in beiden Räumen unten links: 6 × 5 Kacheln mit Eckklammern (wie in der Vorlage).
- **Ankunft:** je 2 cyan Pfeilmarken unten links (Eckklammern + Doppelpfeil direkt auf dem Boden, wie das Aufstellfeld).
- **Linker Raum:** Ringmarke in der Mitte, 2 × 2 goldene Pfeilmarken am rechten Rand (Weg in den zweiten Raum).
- **Leere:** Netzraster, blauer Nebel, blaue Datenstränge mit laufenden Datenpaketen, schwebende Datenfragmente
  (links, rechts und zwischen den Räumen).

## Animation (4 Bilder, 250 ms – Regel: höchstens 4 Animationsbilder)
Datenpakete auf den Strängen, Fragmente schweben (1 px), Kanten glimmen, Pfeilkacheln (cyan und gold) leuchten
nacheinander, Aufstellfelder und Ringmarke glimmen, Lichtfäden unter den Plattformen.

## Dateien
- `Our_War_Game_v1.0.png` – Standbild (1216 × 576), `Our_War_Game_v1.0_discord.gif` – Animation für Discord
  (2× vergrößert, 2432 × 1152).
- `kollision/` – Kollisionsraster (`kollision.json`, `.txt`, `ebene2_kollision.png`, `kollision_overlay.png`):
  begehbar sind beide Räume (je eine zusammenhängende Fläche, verbunden über die goldenen Pfeile), blockiert ist
  die Leere.

Erzeugt mit `tools/karte17_layout.py`, `karte17_bauen.py`, `karte17_animation.py`, `kollision.py karte17`,
`tileset_export.py karte17`.
