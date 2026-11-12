"""Karte 33 (The World of Dreams, A02): Kachelraster aus der Vorlage -> maps/karte33/layout.json

  python3 tools/karte33_layout.py

Vorlage assets/vorlagen/karte33_vorlage.png (704x704 = 44x44 Kacheln). Eine runde Traumplattform schwebt in der
Sternenleere (wie Karte 32): heller Randring, darin ein am Raster gestufter Rautenring aus dunkleren Platten mit drei
lila Runen (oben, unten links, unten rechts) und ein Mittelquadrat; nach Sueden ein 4 Kacheln breiter Steg bis zu den
Ankunftsfeldern am Kartenrand.

Klassen:  . Leere  i Plattenboden  r Randring  m Rautenring/Mittelquadrat  p Steg  a Ankunftsfelder
"""
import json, os
import numpy as np
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte33')
VORLAGE = os.path.join(ROOT, 'assets', 'vorlagen', 'karte33_vorlage.png')
T, C, R = 16, 44, 44
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
    k[rand] = 'r'
    for y, x0, x1 in RING:
        k[y, x0:x1 + 1] = 'm'
    k[19:22, 21:24] = 'm'                                  # Mittelquadrat
    k[33:44, 20:24] = 'p'                                  # Steg
    k[42:44, 20:24] = 'a'                                  # Ankunftsfelder
    lay = {'groesse': [C, R], 'klassen': [''.join(z) for z in k],
           'hoehe': [''.join('0' if c == '.' else '1' for c in z) for z in k],
           'runen': [[22, 12], [16, 24], [28, 24]], 'mitte': [22, 20]}
    os.makedirs(KARTE, exist_ok=True)
    json.dump(lay, open(os.path.join(KARTE, 'layout.json'), 'w'), indent=0)
    F = {'.': (12, 14, 38), 'i': (178, 170, 205), 'r': (205, 200, 225), 'm': (140, 140, 180), 'p': (190, 185, 215),
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
