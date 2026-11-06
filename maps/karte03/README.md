# Karte 03 – Server Desert

Fertige Karte: `terrain.png` (1792×1280 px, 112×80 Kacheln à 16×16), ohne Objekte: `terrain_basis.png`.
Animation: `animation/karte03_animiert.webp`, Discord: `animation/karte03_discord.gif` (volle Auflösung,
16 Frames, unter 10 MB), Ausschnitte `animation/detail_*.gif`. Vorlage: `assets/vorlagen/karte03_vorlage.png`.

## Neu bauen

```bash
python3 tools/karte03_kacheln.py    # neue Grundkacheln (Weg, Kies, Platz, Lehm, Duene)
python3 tools/karte03_bauen.py      # Boden, Duenen, Arena, Gartenmauer, Kabel, Steg, Teleporter
python3 tools/karte03_objekte.py    # Objekte setzen
python3 tools/karte03_bauen.py      # fertige Karte
python3 tools/karte03_animation.py  # Animation und Discord-GIF
```

## v1.1 (Regeln aus CLAUDE.md)

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

## Wiederverwendet

- Sand-, Gras- und Wasserkacheln aus Karte 01 (`assets/basis/`) samt Wang-Uebergaengen `gras_weg`,
  `wasser_sand`, `wasser_gras` und Wasseranimation.
- Bruecke (`bauwerke.zeichne_bruecke`), Bodenfuss (`bauwerke.bodenfuss`), Wind (`karte_bauen.wehen`),
  GIF-Export (`animation_bauen.discord_gif`).
- Regeln aus Karte 02: Schlagschatten aus der Silhouette (Licht oben links), Schatten nur auf ebenem
  Boden (nicht auf Mauerkappen/-fronten), Kantenintegration an der Auflagekante, Pixel-Kollision.

## Neu

- Kacheln: festgefahrener Weg, Feldsteinpflaster, blaugraue Ziegel (Buehnenplatz), rissiger Lehm, Duenensand.
- Prozedural (`tools/karte03_bauen.py`): Duenenrand mit Hang/Kamm, Ruinen-Arena als erhoehter
  Sandstein-Ellipsenring (offen nach Osten, Tor im Sueden), Ziegelring um den Garten, Lehm-Schollen mit
  Front, Datenkabel mit Verteilerdosen, Teleporter.
- Objekte (PixelLab-Objekt-Manager, Gruppen `k3_*`): Kuppelhuetten, Lehmhaeuser, Palmen, Kakteen, Zelte,
  Bus, Buehne, Antennenmasten, Server, Skarabaeen, Obelisk, Saeulen, Ruinenbloecke, Torbogen, Pavillon,
  Pyramide und Wuestendeko.
