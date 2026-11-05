# Karte 07 – The Holy Peaks

100 × 90 Kacheln à 16 px, Vorlage `assets/vorlagen/karte07_vorlage.png`.

```
python3 tools/karte07_bauen.py layout   # Raster (nach der Vorlage) -> layout.json
python3 tools/karte07_objekte.py        # Objekte am 16x16-Raster, ohne Ueberlappungen
python3 tools/karte07_bauen.py          # terrain.png
python3 tools/karte07_animation.py      # animation/
```

- Schwebende Insel über einem animierten Wolkenmeer, drei Terrassen mit grauen Felsfronten und Treppen.
- Gipfel: Schnee mit verschneiten Tannen (Karte 05), Felsplateau mit Steinring, Wirbelportal, Holzbrücke zum
  Drachenschrein (roter Zaun, Steinlaternen, Kristall-Obelisk).
- Mitte: Grasterrasse mit Bonsai-Kiefern, Pagodenhof. Unten: Teefelder, Pavillons, Torii, kleiner Schrein, Teleporter.
- Bausteine: Gras (Karte 01), Schnee/Fels (Karte 05), Weg (Karte 04), Kopfstein (Karte 03, grau), Wände/Treppen/Brücke.
