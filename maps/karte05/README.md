# Karte 05 – Freezeland

110 × 85 Kacheln à 16 px, Vorlage `assets/vorlagen/karte05_vorlage.png`.

```
python3 tools/karte05_layout.py     # Raster aus der Vorlage -> layout.json
python3 tools/karte05_kacheln.py    # Bodenkacheln (Karte-01-Sand/Gras umgefaerbt)
python3 tools/karte05_objekte.py    # Objekte, alle am 16x16-Raster
python3 tools/karte05_bauen.py      # terrain.png
python3 tools/karte05_animation.py  # animation/ (webp, Discord-GIF, Detail-GIFs)
```

- Höhen: Nordplateau mit Eisklippen (Fronten 4 Kacheln, Seitenwände), Schneefeld, Eismeer rechts.
- Eissee mit offenen Eislöchern, Gletscherspalten mit zwei Holzbrücken, Steg auf dem See, drei Treppen.
- Bausteine aus Karte 04 (Wände, Treppen, Schatten, Einbettung, Animation), Kacheln aus Karte 01 umgefärbt.
- Objekte: PixelLab (`assets/objekte/karte05/`), jedes mittig in einer Kachel (`kachel: [x, y]` in platzierung.json).
- Animation: Schneefall, Wasser, Tannen im Wind (Waldrand ruhig), Lagerfeuer, Laternen, Kristalle, Fahne, Teleporter.
