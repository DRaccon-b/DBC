# Karte 19 – Revenge v1.0

76 × 38 Kacheln à 16 px (1216 × 608), Vorlage `assets/vorlagen/karte19_vorlage.png` (zwei Räume je 28 × 24 Kacheln).
Drittes Gebiet des Keramon-Dungeons, im Stil von Karte 16/17: zwei schwebende Plattformen in der Leere des Netzes.
Anspielungen nur über Farben und Motive, nichts nachgebaut.

## Inhalt der Karte
- **Linker Raum (Network-Stil):** Plattenboden der Vorlage, dunkler Randring mit cyan glimmender Kante, Metallfront
  mit hängenden Lichtfäden, Aufstellfeld (6 × 5 Eckklammern), drei kleine Bodenplatten, Ankunftspfeile (cyan) und
  goldene Weiter-Pfeile – die Pfeile im Stil des Aufstellfelds direkt auf dem Boden.
- **Rechter Raum (Hafen):** Kaimauer aus Granit ringsum, oben das Hafenbecken mit Netz-Wasser (cyan über den
  Pflasterplatten, leuchtendes Datenraster, Bitreihen auf der Oberfläche) und einer zweiten, tieferen Ebene in der
  Mitte; nasse Nordmauer. Links und rechts fehlt die Mauer auf Wasserhöhe: das Wasser läuft über die Kante und zerfällt
  als Datenstrom in die Leere. Kaikante aus hellem Stein, graues Pflaster, vier Poller mit Tau (symmetrisch),
  Ringmarke, Aufstellfeld, Ankunftspfeile.
- **Leere:** Netzraster, blauer Nebel, Datenstränge, schwebende Datenfragmente.

## Animation (4 Bilder, 250 ms – Regel: höchstens 4 Animationsbilder)
Datenpakete auf den Strängen, Fragmente schweben (1 px), Kanten glimmen, Pfeilmarken und Aufstellfelder leuchten,
Netz-Wasser (Raster pulsiert, Bitreihen treiben), Datenstrom-Überlauf rauscht nach unten, Lichtfäden.

## Dateien
- `Revenge_v1.0.png` – Standbild (1216 × 608), `Revenge_v1.0_discord.gif` – Animation für Discord (2×, 2432 × 1216).
- `kollision/` – Kollisionsraster (`kollision.json`, `.txt`, `ebene2_kollision.png`, `kollision_overlay.png`):
  begehbar sind beide Räume (je eine zusammenhängende Fläche, verbunden über die goldenen Pfeile); blockiert sind die
  Leere, das Hafenbecken, die obere Kaimauer und die Füße der Poller.

Erzeugt mit `tools/karte19_layout.py`, `karte19_bauen.py`, `karte19_objekte.py`, `karte19_animation.py`,
`kollision.py karte19`, `tileset_export.py karte19`.
