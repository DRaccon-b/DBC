"""Karte 54 - D-Reaper Kernel (A03 Nr. 21), Layout nach der Vorlage -> maps/karte54/layout.json

  python3 tools/karte54_layout.py

Vorlage assets/vorlagen/karte54_vorlage.png (768x576 = 48x36 Kacheln): dunkle violette Kammer, erhoehter Gewebe-Felsrand
ringsum, zwei Mauerringe (aussen mit Zugang unten links, innen mit Tor unten in der Mitte), rote Gewebebahnen (links,
rechts, L-Bahn unten), dunkles Becken unten links, Teleporter unten.

Klassen:  g Boden (Metallplatten)  m Mauerring (gesperrt)  f Gewebebahn (begehbar)  w Becken (gesperrt)
          h Felsrand (gesperrt)  T Teleporter
Korrekturen der Vorlage:
  - Teleporter lag im Becken -> Becken endet drei Reihen ueber dem Rand, Teleporter auf dem Boden davor (Ausgang durch den Rand)
  - Zugang zum Mauerring muendete ins Becken -> Becken schmaler, Zugang ueber zwei Spalten Boden mit der L-Bahn verbunden
  - Mauerringe exakt symmetrisch zur Kammerachse, Tor des Innenrings mittig
"""
import json, os
import numpy as np
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte54')
VORLAGE = os.path.join(ROOT, 'assets', 'vorlagen', 'karte54_vorlage.png')
C, R, T = 48, 36, 16
AUSSEN = (11, 4, 37, 22)                  # Aussenring (x0, y0, x1, y1), Zugang unten links (Spalten 11-13)
INNEN = (14, 7, 34, 19)                   # Innenring, Tor unten mittig
TOR = (22, 26)                            # Torspalten im Innenring (Vorlage x 352-432)
GEWEBE = [(5, 7, 8, 18), (39, 9, 42, 26), (14, 23, 42, 26)]   # rote Gewebebahnen (x0, y0, x1, y1)
BECKEN = (4, 21, 10, 29)
TELEPORTER = [(6, 33, 4, 3)]


def main():
    k = np.full((R, C), 'g')
    x0, y0, x1, y1 = AUSSEN
    k[y0, x0:x1 + 1] = 'm'; k[y1, x0 + 3:x1 + 1] = 'm'; k[y0:y1 - 1, x0] = 'm'; k[y0:y1 + 1, x1] = 'm'
    x0, y0, x1, y1 = INNEN
    k[y0, x0:x1 + 1] = 'm'; k[y1, x0:x1 + 1] = 'm'; k[y0:y1 + 1, x0] = 'm'; k[y0:y1 + 1, x1] = 'm'
    k[y1, TOR[0]:TOR[1] + 1] = 'g'
    for (a0, b0, a1, b1) in GEWEBE:
        k[b0:b1 + 1, a0:a1 + 1] = 'f'
    x0, y0, x1, y1 = BECKEN
    k[y0:y1 + 1, x0:x1 + 1] = 'w'
    k[0:3, :] = 'h'; k[-3:, :] = 'h'; k[:, 0:3] = 'h'; k[:, -3:] = 'h'
    for (tx, ty, b, hh) in TELEPORTER:
        k[ty:ty + hh, tx:tx + b] = 'T'
    hp = np.where(k == 'h', 2, np.where(k == 'm', 1, 0))
    lay = {'groesse': [C, R], 'klassen': [''.join(z) for z in k], 'hoehe': [''.join(str(c) for c in z) for z in hp],
           'treppen': [], 'aussen': list(AUSSEN), 'innen': list(INNEN), 'tor': list(TOR), 'becken': list(BECKEN),
           'bruecken': [], 'stege': [], 'teleporter': [{'x': tx, 'y': ty, 'b': b, 'h': hh} for (tx, ty, b, hh) in TELEPORTER]}
    os.makedirs(KARTE, exist_ok=True)
    json.dump(lay, open(os.path.join(KARTE, 'layout.json'), 'w'), indent=0)
    F = {'g': (52, 40, 56), 'm': (110, 70, 110), 'f': (140, 40, 70), 'w': (30, 44, 64), 'h': (80, 50, 70), 'T': (80, 220, 240)}
    S_ = 8
    out = np.zeros((R, C, 3), np.uint8)
    for kk, c in F.items():
        out[k == kk] = c
    vg = Image.open(VORLAGE).convert('RGB').resize((C * S_, R * S_))
    both = Image.new('RGB', (C * S_ * 2 + 8, R * S_))
    both.paste(vg, (0, 0)); both.paste(Image.fromarray(out).resize((C * S_, R * S_), 0), (C * S_ + 8, 0))
    both.save(os.path.join(KARTE, 'layout_vergleich.png'))
    print('Karte 54 Layout %dx%d' % (C, R))


if __name__ == '__main__':
    main()
