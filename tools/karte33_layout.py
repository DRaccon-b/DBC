"""Karte 33 (The World of Dreams, A02): Kachelraster aus der Vorlage -> maps/karte33/layout.json

  python3 tools/karte33_layout.py

Vorlage assets/vorlagen/karte33_vorlage.png (704x704 = 44x44 Kacheln). Eine runde Traumplattform schwebt in der
Sternenleere (wie Karte 32): heller Randring, darin ein am Raster gestufter Rautenring aus dunkleren Platten mit drei
lila Runen (oben, unten links, unten rechts) und ein Mittelquadrat; nach Sueden ein 4 Kacheln breiter Steg bis zu den
Ankunftsfeldern am Kartenrand.

Klassen:  . Leere  i Plattenboden  r Randring  m Rautenring/Medaillon  w Ringmauer  p Steg  a Ankunftsfelder
"""
import json, os
import numpy as np
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte33')
VORLAGE = os.path.join(ROOT, 'assets', 'vorlagen', 'karte33_vorlage.png')
T, C, R = 16, 44, 44
MX, MY = 22, 20                                # Plattformmitte (Kachelkante): Achse aller Symmetrien
# Plattform-Zeilen aus der Vorlage: (Reihe, x0, x1)
SCHEIBE = [(6, 18, 25), (7, 16, 27), (8, 14, 29), (9, 13, 30), (10, 12, 31), (11, 11, 32), (12, 10, 33), (13, 10, 33),
           (14, 9, 34), (15, 9, 34), (16, 8, 35), (17, 8, 35), (18, 8, 35), (19, 8, 35), (20, 8, 35), (21, 8, 35),
           (22, 8, 35), (23, 8, 35), (24, 9, 34), (25, 9, 34), (26, 10, 33), (27, 10, 33), (28, 11, 32), (29, 12, 31),
           (30, 13, 30), (31, 14, 29), (32, 16, 27), (33, 18, 25)]
RING = [(12, 21, 23), (13, 18, 26), (14, 17, 20), (14, 24, 27), (15, 16, 18), (15, 26, 28), (16, 15, 17), (16, 27, 29),
        (17, 15, 16), (17, 28, 29), (18, 15, 16), (18, 28, 29), (19, 14, 15), (19, 29, 30), (20, 14, 15), (20, 29, 30),
        (21, 14, 15), (21, 29, 30), (22, 15, 16), (22, 28, 29), (23, 15, 16), (23, 28, 29), (24, 15, 17),
        (24, 27, 29), (25, 16, 18), (25, 26, 28), (26, 17, 20), (26, 24, 27), (27, 18, 26), (28, 21, 23)]


def main():
    k = np.full((R, C), '.')
    for y, x0, x1 in SCHEIBE:
        k[y, x0:x1 + 1] = 'i'
    rand = (k == 'i') & ~(np.roll(k == 'i', 1, 0) & np.roll(k == 'i', -1, 0) & np.roll(k == 'i', 1, 1)
                          & np.roll(k == 'i', -1, 1))
    # Ring, Ringmauer und Medaillon exakt symmetrisch zur Plattformmitte (Nutzer): Achteck um (22, 20) Kachelkanten
    yy, xx = np.mgrid[0:R, 0:C]
    dx, dy = xx + 0.5 - MX, yy + 0.5 - MY
    d = np.maximum(np.maximum(abs(dx), abs(dy)), (abs(dx) + abs(dy)) * 0.72)
    k[(d >= 5.5) & (d < 7.5)] = 'm'                        # Rautenring
    k[d < 2.1] = 'm'                                       # Medaillon in der Mitte
    k[rand] = 'w'                                          # Ringmauer um die ganze Arena, 1 Kachel dick (Nutzer)
    k[33, 20:24] = 'i'                                     # Tor im Sueden: Stegbreite, auf der Achse
    k[33:44, 20:24] = 'p'                                  # Steg
    k[42:44, 20:24] = 'a'                                  # Ankunftsfelder
    lay = {'groesse': [C, R], 'klassen': [''.join(z) for z in k],
           'hoehe': [''.join('0' if c == '.' else ('2' if c == 'w' else '1') for c in z) for z in k],
           'runen_px': [[MX * T + sx * 72, MY * T + sy * 72] for sy in (-1, 1) for sx in (-1, 1)],   # 4 Runen diagonal
           'mitte': [MX, MY],
           # Raum-Zeit-Risse in den vier Ecken (Nutzer-Skizze): Risskante als Linie von Kartenrand zu Kartenrand (Kacheln),
           # die Ecke dahinter ist der Riss; darunter eine andere A02-Karte (quelle = Pixel der Quellkarte an der
           # linken oberen Ecke des Riss-Rahmens)
           'risse': [{'kante': [(0, 15.1), (2.8, 15), (3.1, 10.9), (9.4, 10.6), (10, 5.9), (15, 5.9), (16.6, 3.4),
                                (20.6, 3.1), (22.2, 0)], 'ecke': (0, 0), 'karte': 'karte20', 'quelle': [50, 116]},
                     {'kante': [(30.6, 0), (30.9, 3.1), (35, 5), (38.8, 5.9), (36.9, 8.8), (37.5, 11.6), (44, 11.9)],
                      'ecke': (44, 0), 'karte': 'karte07', 'quelle': [500, 1080]},   # Felder (Nutzer)
                     {'kante': [(0, 23.8), (1.6, 23.8), (5.3, 26.9), (6.3, 33.8), (9.4, 35.6), (10.6, 36.3), (14.7, 38.1),
                                (16.6, 40.6), (16.6, 44)], 'ecke': (0, 44), 'karte': 'karte25', 'quelle': [440, 400]},
                     {'kante': [(44, 25.6), (40.9, 25.9), (40.6, 27.5), (35, 30), (34, 35.6), (29.4, 36.6), (28.4, 40),
                                (28.8, 44)], 'ecke': (44, 44), 'karte': 'karte27', 'quelle': [520, 230]}]}
    os.makedirs(KARTE, exist_ok=True)
    json.dump(lay, open(os.path.join(KARTE, 'layout.json'), 'w'), indent=0)
    F = {'w': (90, 86, 120), '.': (12, 14, 38), 'i': (178, 170, 205), 'r': (205, 200, 225), 'm': (140, 140, 180), 'p': (190, 185, 215),
         'a': (110, 200, 230)}
    out = np.zeros((R, C, 3), np.uint8)
    for kk, c in F.items():
        out[k == kk] = c
    vor = Image.open(VORLAGE).convert('RGB').resize((C * 8, R * 8))
    bild = Image.new('RGB', (C * 16 + 8, R * 8))
    bild.paste(vor, (0, 0))
    bild.paste(Image.fromarray(out).resize((C * 8, R * 8), 0), (C * 8 + 8, 0))
    bild.save(os.path.join(KARTE, 'layout_vergleich.png'))
    print('Karte 33 Layout %dx%d' % (C, R))


if __name__ == '__main__':
    main()
