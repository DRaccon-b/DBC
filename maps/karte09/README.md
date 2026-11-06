# Karte 09 – Vamdemon's Keep

90 × 86 Kacheln à 16 px, Vorlage `assets/vorlagen/karte09_vorlage.png`.

```
python3 tools/karte09_layout.py && python3 tools/karte09_kacheln.py && python3 tools/karte09_bauen.py
python3 tools/karte09_objekte.py && python3 tools/regeln_v11.py karte09 && python3 tools/karte09_objekte.py symmetrie
python3 tools/karte09_bauen.py
python3 tools/karte09_animation.py
```

- Schloss oben: Portalhalle, grosser Saal (roter Teppich als Kreuz), Ritualsaal mit Orgel, Altar, Saergen und
  violettem Teppichrahmen, zwei Gaerten; Mauern mit 3 Kacheln hoher Wandflaeche, Buntglasfenstern, Bannern, Bildern.
- Aussenmauer mit Tuermen, Haupttor, Burggraben mit Zugbruecke.
- Friedhof unten: Wege, dunkle Teiche mit Bruecke und Steg, Felsplateaus, Gruften und Kapellen (aus Overdell),
  Steinkreis, Lagerplatz, Teleporter links.
- Portal mit acht Kristallen in den acht Farben (Orange, Blau, Rot, Lila, Gruen, Grau, Gelb, Rosa); Wirbel dreht sich.
- Tore (PixelLab) mit offenem Durchgang, mittig auf dem Teppich; Wachtuerme in gleichen Abstaenden, Banner dazwischen.
- Raeume: Portalhalle, Bibliothek mit Kamin, Thron, Speisesaal, Ritualsaal; alle Paare symmetrisch zur Saalachse.
- Animation: Sumpfwasser, Flammen (Fackeln, Kerzen, Kamin, Feuerschalen), Portal, Geisterlicht, Glimmen, Gras im Wind.
- Objekte: PixelLab neu (`assets/objekte/karte09/{gross,moebel,tor,wand}`), wiederverwendet aus Karte 08 (`k8/`).
