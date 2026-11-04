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
