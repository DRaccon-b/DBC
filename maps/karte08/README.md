# Karte 08 – Overdell

100 × 90 Kacheln à 16 px, Vorlage `assets/vorlagen/karte08_vorlage.png`.

```
python3 tools/karte08_layout.py      # Raster + Hoehenstufen aus der Vorlage -> layout.json
python3 tools/karte08_kacheln.py     # Bodenkacheln (Karte-01-Gras/Sand duester umgefaerbt)
python3 tools/karte08_bauen.py       # Gelaende (pixelhoehe.npy fuer die Objektpruefung)
python3 tools/karte08_objekte.py && python3 tools/regeln_v11.py karte08 && python3 tools/karte08_bauen.py
python3 tools/karte08_animation.py   # animation/ (webp, Discord-GIF, Detail-GIFs)
```

- Ringsum schwarzer Fels (Ebene 7) mit Geroell und Felsbrocken, schwarze Felsnasen und ein Felsloch links.
- Terrassenberg in der Mitte: 4 Terrassen + Schlossplateau, Treppen abwechselnd links/rechts (Ebenen 2–6).
- Dunkles gotisches Schloss oben mittig (Devimons Sitz), Gargoyles, Banner, Saeulen, Geisterlaternen.
- Friedhof links (tote Baeume) und unten: Mausoleum, Gruften, Grabreihen, Lagerplatz mit Bannern unten links,
  Sumpf (vertieft, zwei Tiefenstufen) mit verwitterter Holzbruecke, rechter Friedhof auf dem Berg.
- Objekte: PixelLab (`assets/objekte/karte08/`), alle am 16×16-Raster, Schatten nur auf der eigenen Ebene,
  Verdeckung durch Hoehen, keine Ueberlappungen (Pixelpruefung, 2 px Abstand), keine Grabsteine auf Wegen.
