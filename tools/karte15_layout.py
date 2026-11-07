"""Karte 15 (Apocalymon's Realm): Kachelraster nach der Vorlage -> maps/karte15/layout.json

  python3 tools/karte15_layout.py

Vorlage assets/vorlagen/karte15_vorlage.png (640x640 = 40x40 Kacheln a 16 px).
Eine runde Steininsel schwebt in der Leere (eine Etage ueber dem 'Nichts'), in der Mitte der Riss in die Leere
(Boss-Spawn), nach Sueden ein Steinsteg auf der Achse zum Teleporter am unteren Rand.
Klassen:  . Leere  p Plattform (Stein)  r Rand der Plattform (dunkler Stein)  s Steg  v Riss (Boss-Feld)
Hoehen:   0 Leere, 2 Plattform und Steg.
"""
import json, os
import numpy as np
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte15')
C, R = 40, 40
CX, CY, RAD = 20.0, 19.0, 12.6           # Plattform-Kreis (Kacheln)


def main():
    yy, xx = np.mgrid[0:R, 0:C]
    d = np.sqrt((xx + 0.5 - CX) ** 2 + (yy + 0.5 - CY) ** 2)
    k = np.full((R, C), '.')
    h = np.zeros((R, C), int)
    platt = d <= RAD
    k[platt] = 'p'
    k[platt & (d > RAD - 1.6)] = 'r'
    steg = (xx >= 18) & (xx <= 21) & (yy >= 30)
    k[steg] = 's'
    h[platt | steg] = 2
    dx, dy = np.abs(xx + 0.5 - CX), np.abs(yy + 0.5 - CY)
    riss = ((dx <= 1.5) & (dy <= 3.5)) | ((dx <= 3.5) & (dy <= 1.5)) | ((dx <= 2.5) & (dy <= 2.5))   # Kreuz, gestuft
    k[riss] = 'v'
    lay = {'groesse': [C, R], 'klassen': [''.join(r) for r in k], 'hoehe': [''.join(str(c) for c in r) for r in h],
           'platte': [CX, CY, RAD], 'steg': [18, 21, 30], 'boss': [CX, CY],
           'teleporter': [{'x': 18, 'y': 38, 'b': 4, 'h': 2}]}
    os.makedirs(KARTE, exist_ok=True)
    json.dump(lay, open(os.path.join(KARTE, 'layout.json'), 'w'), indent=0)
    F = {'.': (14, 16, 34), 'p': (110, 110, 130), 'r': (70, 66, 86), 's': (110, 110, 130), 'v': (40, 28, 50)}
    out = np.zeros((R, C, 3), np.uint8)
    for kk, c in F.items():
        out[k == kk] = c
    vor = Image.open(os.path.join(ROOT, 'assets', 'vorlagen', 'karte15_vorlage.png')).convert('RGB').resize((C * 8, R * 8))
    bild = Image.new('RGB', (C * 16 + 8, R * 8))
    bild.paste(vor, (0, 0))
    bild.paste(Image.fromarray(out).resize((C * 8, R * 8), 0), (C * 8 + 8, 0))
    bild.save(os.path.join(KARTE, 'layout_vergleich.png'))
    print('Karte 15 Layout %dx%d' % (C, R))


if __name__ == '__main__':
    main()
