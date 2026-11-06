# Karte 03 – Server Desert – v1.1

112 × 80 Kacheln à 16 px. Original v1.0: `maps/karte03/v1.0/`.

## Neu bauen und Aenderungen

```bash
python3 tools/karte03_v11.py && python3 tools/karte03_bauen.py && python3 tools/karte03_objekte.py \
  && python3 tools/regeln_v11.py karte03 && python3 tools/karte03_bauen.py && python3 tools/karte03_animation.py
```

- Meer links breiter und terrassiert wie Karte 01 (Flachwasser, Schaumkante, zwei Tiefenstufen, Tiefsee, Felsen, Algen).
- Grenzen nach Skizze: links Meer bis zum unteren Rand, oben Sandwand bis vor die Lagune, oben rechts Meer um die Insel
  bis zum Kartenrand, rechts unterhalb der Lagune Sandwand (Luecke fuer den Teleporter).
- Oase oben rechts als Insel im Meer: Gras mit Pavillon und Teich, Sandstrand mit Palmen/Kakteen, Holzsteg nach Sueden.
- Regel 1/1b Raster, Regel 6 Wege in Boegen (Anschluesse an Stegen, Teleportern und Arena-Tor bleiben exakt),
  Regel 7 Schatten nie auf Wasser, liegende Objekte mit flachem Schatten, keine Objekte im Wasser, Ueberlappungen entfernt.
- Original v1.0: `maps/karte03/v1.0/`.

- 12 neue Palmen (PixelLab) als Baeume der Karte: Haine, Palmen hinter Haeusern, Begleiter vor den Staemmen.
- Grabhaus mit Pyramidendach statt flachem Torbogen; Gebaeude stehen ganz auf Land.
- Schatten folgen der Objektform und beginnen direkt am Fuss; Fahnen: nur das Tuch weht.
- Meer mit fester Flaeche fuer alle Animationsbilder (keine wandernden Felsen).
