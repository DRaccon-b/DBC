# Karte 29 – The Sea of Darkness (A02) v1.0

90 × 80 Kacheln à 16 px (1440 × 1280), Vorlage `assets/vorlagen/karte29_vorlage.png`. Alles am 16×16-Raster.

## Inhalt der Karte
- **Meer im Stil von Karte 01** (terrassiert), schwarzgrau: flaches Wasser mit sichtbarem Sandgrund, zwei tiefere
  Stufen mit Stufenwänden, Unterwasserfelsen, Algen, Schaumkante und Brandung; Stufen genau am Raster.
- **Strand** graublau mit hellen Sandflecken und Pfützen, **10 Felsblöcke** mit Schieferfront (3 im Meer).
- **Spawnplatz** oben links: rundlicher Pflasterplatz mit dem Portal von Holy Peaks (schwarz-grau-weiß) und vier Laternen (symmetrisch).
- **Leuchtturm** oben rechts, lange dunkle Steinbrücke hinunter zum **Tempel**: Tempeltor auf der Brückenachse,
  Statue eines Meeresgottes, drei Säulenpaare spiegelsymmetrisch, Säulenstümpfe, Treppe im Süden direkt ins Wasser.
- **Strand-Objekte:** großes Schiffswrack, Ruderboote, Bootswrack, Anker, Felsbrocken, Muscheln, Treibholz, Gräten, Seetang.
- **Portale:** Portal wie Karte 07 (Spawn), dunkler Riss über dem Meer neben dem Leuchtturm, Wasserstrudel unten rechts.

## Animation (4 Bilder, 250 ms)
Meer (Lichtstriche, Schaum, Brandung, Algen), Leuchtturmlicht, Laternen, Riss, Kristallportal und Strudel, Seetang.
Steine, Felsen, Säulen, Statue und Brücken sind unbewegt.

## Dateien
- `The_Sea_of_Darkness_v1.0.png` – Standbild, `The_Sea_of_Darkness_v1.0_discord.gif` – Animation für Discord (2×).
- `kollision/` – Kollisionsraster: blockiert sind Meer, Felsfronten, Tempelfront und Objektfüße; Treppe und Brücken begehbar.

Erzeugt mit `tools/karte29_layout.py`, `karte29_bauen.py`, `karte29_objekte.py`, `karte29_animation.py`,
`kollision.py karte29`, `tileset_export.py karte29`. Neue Objekte: PixelLab Objekt-Creator (`k29_*`),
wiederverwendet aus Karte 11 und 25.
