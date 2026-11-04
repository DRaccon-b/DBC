# Karte 04 – Gear Savanna

110 × 85 Kacheln à 16 px (1760 × 1280 px … 1360 px), Vorlage: `assets/vorlagen/karte04_vorlage.png`.

```
python3 tools/karte04_layout.py     # Raster aus der Vorlage -> layout.json
python3 tools/karte04_kacheln.py    # Bodenkacheln (Karte-01-Gras/Sand umgefaerbt)
python3 tools/karte04_objekte.py    # Objekte platzieren
python3 tools/karte04_bauen.py      # terrain.png
python3 tools/karte04_animation.py  # animation/ (webp, Discord-GIF, Detail-GIFs)
```

- Hoehenstufen: 0 Canyon + Teerbecken, 1 Savanne, 2 Plateaus. Waende pixelgenau aus den Hoehenmasken
  (Fels aus `klippen.wand` von Karte 01, umgefaerbt: Sandstein / Erde / Schiefer), Lippe mit Grasueberhang,
  Schatten nach rechts unten (Licht oben links), Treppen an drei Plateaus, Rampen an den Canyon-Uebergaengen.
- Fluss fliesst nach Sueden, Stromschnellen an zwei Furten, Holzbruecke auf der Hauptstrasse.
- Objekte: PixelLab-Objekt-Manager (`assets/objekte/karte04/<gruppe>`), Bodenfuss wie Karte 03.
- Animation: Fluss, Stromschnellen, Teiche, Wind (Akazien, Graeser), Lagerfeuer, Laterne, Teleporter,
  Monument-Juwel, glitzernde Kristalle.
