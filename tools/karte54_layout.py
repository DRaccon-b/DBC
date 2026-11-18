"""Karte 54 - D-Reaper Kernel (A03 Nr. 21, letzte Bossarena von A03): Kachelraster -> maps/karte54/layout.json

  python3 tools/karte54_layout.py && python3 tools/karte54_bauen.py

Neu aufgebaut (Nutzer): Bossarena wie die letzten Karten aus A01 (Karte 19) und A02 (Karte 33, The World of Dreams).
Eine runde Arena-Plattform (Form wie Karte 33, 45-Grad-Raster) schwebt in einem Meer aus pulsierenden D-Reaper-Blasen
(Karte 52). Massive Ringmauer, im Boden ein am Raster gestufter Ring und ein Mittelfeld, die der D-Reaper befallen hat
(pulsierende Adern). Nach Sueden ein 4 Kacheln breiter Steg bis zum Teleporter am Kartenrand. In den Ecken reisst die
Masse auf: Risse mit echten, animierten Ausschnitten von Shinjuku (Karte 52/53) im selben Massstab. Die Mitte bleibt frei
(Nutzer: der Boss ist beim Betreten schon da).

Klassen:  . Blasenmeer (Leere)  i Arenaboden  m befallener Ring/Mittelfeld  w Ringmauer  p Steg
"""
import json, os
import numpy as np
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte54')
T, C, R = 16, 44, 44
MX, MY = 22, 20                                # Arenamitte (Kachelkante): Achse aller Symmetrien
# Arena-Zeilen (Reihe, x0, x1) - dieselbe runde Form wie Karte 33, exakt symmetrisch zu MX
SCHEIBE = [(6, 18, 25), (7, 16, 27), (8, 14, 29), (9, 13, 30), (10, 12, 31), (11, 11, 32), (12, 10, 33), (13, 10, 33),
           (14, 9, 34), (15, 9, 34), (16, 8, 35), (17, 8, 35), (18, 8, 35), (19, 8, 35), (20, 8, 35), (21, 8, 35),
           (22, 8, 35), (23, 8, 35), (24, 9, 34), (25, 9, 34), (26, 10, 33), (27, 10, 33), (28, 11, 32), (29, 12, 31),
           (30, 13, 30), (31, 14, 29), (32, 16, 27), (33, 18, 25)]


def main():
    k = np.full((R, C), '.')
    for y, x0, x1 in SCHEIBE:
        k[y, x0:x1 + 1] = 'i'
    rand = (k == 'i') & ~(np.roll(k == 'i', 1, 0) & np.roll(k == 'i', -1, 0) & np.roll(k == 'i', 1, 1)
                          & np.roll(k == 'i', -1, 1))
    yy, xx = np.mgrid[0:R, 0:C]
    dx, dy = xx + 0.5 - MX, yy + 0.5 - MY
    d = np.maximum(np.maximum(abs(dx), abs(dy)), (abs(dx) + abs(dy)) * 0.72)
    k[(d >= 7.5) & (d < 9.5)] = 'm'                        # befallener Ring (weiter aussen als in Karte 33: Kampfflaeche)
    k[d < 2.1] = 'm'                                       # befallenes Mittelfeld
    k[rand] = 'w'                                          # Ringmauer, 1 Kachel dick
    k[33, 20:24] = 'i'                                     # Tor im Sueden: Stegbreite, auf der Achse
    k[34:44, 20:24] = 'p'                                  # Steg bis zum Kartenrand
    lay = {'groesse': [C, R], 'klassen': [''.join(z) for z in k], 'mitte': [MX, MY],
           'teleporter': [{'x': 20, 'y': 41, 'b': 4, 'h': 3}],
           # Risse im Blasenmeer (Kachelkoordinaten, Kante von Kartenrand zu Kartenrand), darunter Shinjuku im selben
           # Massstab (quelle = Pixel der Quellkarte an der linken oberen Ecke des Riss-Rahmens)
           'risse': [{'kante': [(0, 8.4), (2.4, 8.0), (3.0, 5.2), (5.8, 4.6), (6.4, 1.8), (8.6, 0)],
                      'ecke': (0, 0), 'karte': 'karte52', 'quelle': [560, 470]},
                     {'kante': [(35.4, 0), (37.6, 1.8), (38.2, 4.6), (41.0, 5.2), (41.6, 8.0), (44, 8.4)],
                      'ecke': (44, 0), 'karte': 'karte53', 'quelle': [700, 140]},
                     {'kante': [(0, 34.6), (2.6, 35.2), (3.4, 38.2), (6.4, 39.0), (7.2, 41.8), (9.0, 44)],
                      'ecke': (0, 44), 'karte': 'karte53', 'quelle': [80, 1040]},
                     {'kante': [(44, 34.6), (41.4, 35.2), (40.6, 38.2), (37.6, 39.0), (36.8, 41.8), (35.0, 44)],
                      'ecke': (44, 44), 'karte': 'karte52', 'quelle': [1180, 960]}]}
    os.makedirs(KARTE, exist_ok=True)
    json.dump(lay, open(os.path.join(KARTE, 'layout.json'), 'w'), indent=0)
    F = {'.': (150, 20, 40), 'i': (60, 44, 66), 'm': (120, 40, 70), 'w': (100, 70, 104), 'p': (80, 62, 86)}
    out = np.zeros((R, C, 3), np.uint8)
    for kk, c in F.items():
        out[k == kk] = c
    Image.fromarray(out).resize((C * 8, R * 8), 0).save(os.path.join(KARTE, 'layout_vergleich.png'))
    print('Karte 54 Layout %dx%d' % (C, R))


if __name__ == '__main__':
    main()
