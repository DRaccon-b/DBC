"""Karte 37 - Hypnos Rooftop (A03 Nr. 4), Layout nach der Vorlage -> maps/karte37/layout.json

  python3 tools/karte37_layout.py

Vorlage assets/vorlagen/karte37_vorlage.png: 768x576 px = 48x36 Kacheln (1:1). Dach des Hypnos-Hochhauses: helle
Ziegelwege (U oben, breites Band unten), tiefer liegende dunkle Dachflaeche in der Mitte mit Lueftungsgittern, Teleporter
auf einer kleinen Plattform unten links. Die aeusseren 3 Kacheln ringsum sind kein Boden: dort sieht man tief unten die
Stadt von Karte 35 (Shinjuku Digital Fog) - nicht begehbar (Nutzer).

Klassen:  k Ziegelweg  u Dachflaeche (dunkel)  z Blick hinunter (Ring, gesperrt)  e Teleporter-Plattform
"""
import json, os
import numpy as np
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte37')
VORLAGE = os.path.join(ROOT, 'assets', 'vorlagen', 'karte37_vorlage.png')
C, R, T = 48, 36, 16
RING = 3                                                          # aeussere Kacheln: Blick auf Karte 35 (Nutzer)
DACH = (3, 3, 44, 32)                                             # Dachflaeche (x0, y0, x1, y1)
TELEPORTER = (6, 33, 4, 3)                                        # Plattform mit Teleporter (x, y, b, h)
GITTERREIHEN = [(17, 38, 25), (17, 38, 31)]                       # Lueftungsgitter-Reihen der Vorlage (x0, x1, y)


def main():
    a = np.array(Image.open(VORLAGE).convert('RGB')).astype(int)
    k = np.full((R, C), 'z')
    for y in range(R):
        for x in range(C):
            s = np.median(a[y * T:(y + 1) * T, x * T:(x + 1) * T].reshape(-1, 3), 0).sum()
            k[y, x] = 'k' if s > 420 else 'u'
    x0, y0, x1, y1 = DACH
    dach = np.zeros((R, C), bool); dach[y0:y1 + 1, x0:x1 + 1] = True
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import karte34_layout as l34
    l34.R, l34.C = R, C
    for (gx0, gx1, gy) in GITTERREIHEN:                               # Gitter sind Objekte auf dem Ziegelweg
        k[gy, gx0:gx1 + 1] = 'k'
    k = l34.kleine_weg(k, 'u', 6, 'k')                                # einzelne dunkle Objekt-Kacheln -> Weg
    k[~dach] = 'z'
    tx, ty, tb, th = TELEPORTER
    k[ty:ty + th, tx:tx + tb] = 'e'
    lay = {'groesse': [C, R], 'klassen': [''.join(z) for z in k], 'hoehe': ['1' * C for _ in range(R)],
           'teleporter': [{'x': tx, 'y': ty, 'b': tb, 'h': th}], 'dach': list(DACH), 'ring': RING,
           'gitterreihen': GITTERREIHEN}
    os.makedirs(KARTE, exist_ok=True)
    json.dump(lay, open(os.path.join(KARTE, 'layout.json'), 'w'), indent=0)
    F = {'k': (170, 175, 180), 'u': (90, 110, 130), 'z': (40, 50, 70), 'e': (120, 220, 255)}
    out = np.zeros((R, C, 3), np.uint8)
    for kk, c in F.items():
        out[k == kk] = c
    bild = Image.new('RGB', (C * 16 + 8, R * 8))
    bild.paste(Image.open(VORLAGE).convert('RGB').resize((C * 8, R * 8)), (0, 0))
    bild.paste(Image.fromarray(out).resize((C * 8, R * 8), 0), (C * 8 + 8, 0))
    bild.save(os.path.join(KARTE, 'layout_vergleich.png'))
    print('Karte 37 Layout %dx%d' % (C, R))


if __name__ == '__main__':
    main()
