# Karte 20 – Startdorf (A02) v1.0

60 × 48 Kacheln à 16 px (960 × 768), Vorlage `assets/vorlagen/karte20_vorlage.png`.
Startkarte von Gebiet A02, im Stil von Karte 06 (Primary Village).

## Inhalt der Karte
- **Wald ringsum** (Bäume von Karte 01); oben rechts ragen die Waldbäume über die Plateaukante.
- **Fluss**: kommt oben aus dem Wald, läuft nach Süden und links aus der Karte (vertiefter Wasserstil wie der Teich
  von Karte 06); an den zwei Holzbrücken genau so breit wie die Brücken.
- **Fernseher** mit Steintreppe – exakt derselbe wie auf Karte 06 (Portalbild dreht sich).
- **Vier Strohdachhäuser** mit Kaminrauch.
- **Dorfplatz** aus Kopfstein: Brunnen auf dem Rasen in der Mitte, Laternen, Bänke und Marktstände paarweise
  symmetrisch, Fässer, Säcke, Anschlagbrett, rosa Kirschbäume.
- **Beetgarten** (geschlossener Zaun): Möhren, Kohl und Weizen gleichmäßig in den Beeten, Vogelscheuche.
- **Feld** unten links (geschlossener Zaun) mit Vogelscheuchen und Heuballen.
- **Windmühle** mit drehenden Gitterflügeln, Heuballen, Schubkarre, Holzstapel.
- **Plateau** oben rechts mit Felsfront, Steintreppe, Bänken und Wegweiser.
- **Ausgänge** mit Teleportern unten in der Mitte und rechts.

## Animation (4 Bilder, 250 ms – Regel: höchstens 4 Animationsbilder)
Windmühlenflügel (22,5° je Bild, Schatten dreht mit), Kaminrauch, Fluss, Fernseher-Portal, Laternen, Teleporter,
Kirschbäume, Weizen und Gräser im Wind.

## Dateien
- `Startdorf_v1.0.png` – Standbild (960 × 768), `Startdorf_v1.0_discord.gif` – Animation für Discord (2×, 1920 × 1536).
- `kollision/` – Kollisionsraster (`kollision.json`, `.txt`, `ebene2_kollision.png`, `kollision_overlay.png`):
  Dorf und Plateau (über die Treppe) sind eine zusammenhängende begehbare Fläche, Brücken begehbar; blockiert sind
  Wald, Fluss, Felsfront, Zäune und die Füße der Objekte.

Erzeugt mit `tools/karte20_layout.py`, `karte20_bauen.py`, `karte20_objekte.py`, `karte20_animation.py`,
`kollision.py karte20`, `tileset_export.py karte20`. Neue Objekte: PixelLab Objekt-Creator (`k20_*`).
