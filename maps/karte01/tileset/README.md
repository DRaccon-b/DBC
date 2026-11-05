# Karte 01 – Tileset

16 × 16 px, Karte 110 × 120 Kacheln.

| Datei | Inhalt |
|---|---|
| `bausteine.png` / `.json` | 100 Grundkacheln: Gras, Sand, Wasser, Meer (je 5 Varianten) und die Wang-Übergänge |
| `boden_tiles.png` | 6451 Kacheln der Boden-Ebene (unter dem Spieler), 64 je Zeile |
| `ueberlagerung_tiles.png` | 2716 Kacheln der Überlagerung (über dem Spieler), 64 je Zeile |
| `kollision_tiles.png` | 3 Kacheln: grün begehbar, rot gesperrt, blau verdeckt |
| `karte01.tmx` | Tiled-Karte: Boden → Spieler (Objektebene) → Überlagerung, dazu Kollision (ausgeblendet) |
| `karte01_raster.json` | dieselben Raster als Listen (0 = leer, sonst Index + 1) |
| `objekte/` | 63 Objekt-Sprites einzeln |

Boden und Überlagerung sind ein exakter Export der fertigen Karte: Atlas + Raster ergeben Pixel für Pixel
`ebenen/ebene1_boden.png` und `ebenen/ebene3_ueberlagerung.png`. Weil Schatten, Kiesel, Gras, Wasserdetails
und Felsen gemalt sind, sind viele Kacheln Unikate. Animationen (Wasser, Wind, Laternen) sind nicht enthalten,
dafür gibt es `animation/`.
