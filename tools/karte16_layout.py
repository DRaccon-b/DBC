"""Karte 16 (The Network), Neuaufbau nach Nutzer-Idee -> maps/karte16/layout.json

  python3 tools/karte16_layout.py

Groesse wie die Vorlage assets/vorlagen/karte16_vorlage.png: 1024x640 px = 64x40 Kacheln a 16 px (echtes 16er-Raster).
Aufbau (Nutzer): Ankunft unten auf den Pfeilfeldern, ein schmaler Pfad fuehrt nach Norden zu einer kreisrunden
Plattform (wie Apocalymon's Realm), oben auf der Plattform das Firewall-Tor, links davon ein Computer
('Dungeon Records'). Ringsum die Leere des Netzes mit blauen Datenstraengen und schwebenden Datenfragmenten.

Achse: Kachelgrenze 32 (x = 512 px) - Tor (4 breit), Pfad (2 breit), Pfeilfeld (4 breit) liegen spiegelgleich darauf.
Klassen:  .  Leere   p  Plattform (Bodenplatten der Vorlage)   r  Randring der Plattform
          s  Pfad    a  Ankunftsfeld   z  Pfeilkachel (Ankunft/Teleporter)
Hoehen:   0 Leere, 2 Plattform/Pfad/Ankunft.
"""
import json, os
import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte16')
C, R, T = 64, 40, 16
ACHSE = 32.0
CX, CY, RAD = ACHSE, 16.0, 10.4           # Plattform-Kreis (Kacheln)
PFAD = (31, 32, 26, 33)                   # x0, x1, y0, y1
ANKUNFT = (29, 34, 33, 36)                # x0, x1, y0, y1
PFEILE = (30, 33, 35)                     # x0, x1, y
TOR = (30, 9, 4)                          # x0, Fussreihe, Breite (Objekt kommt in Schritt 3)
COMPUTER = (25, 10)                       # ungefaehrer Platz links vom Tor


def main():
    os.makedirs(KARTE, exist_ok=True)
    yy, xx = np.mgrid[0:R, 0:C]
    d = np.hypot(xx + 0.5 - CX, yy + 0.5 - CY)
    k = np.full((R, C), '.')
    platt = d <= RAD
    k[platt] = 'p'
    k[platt & (d > RAD - 1.15)] = 'r'
    x0, x1, y0, y1 = PFAD
    k[(k == 'r') & (xx >= x0) & (xx <= x1) & (yy >= y0 - 1)] = 'p'      # Einmuendung des Pfads ohne Randstein
    m = (xx >= x0) & (xx <= x1) & (yy >= y0) & (yy <= y1) & ~platt
    k[m] = 's'
    x0, x1, y0, y1 = ANKUNFT
    k[(xx >= x0) & (xx <= x1) & (yy >= y0) & (yy <= y1)] = 'a'
    k[PFEILE[2], PFEILE[0]:PFEILE[1] + 1] = 'z'
    h = np.where(k == '.', 0, 2)
    lay = {'groesse': [C, R], 'klassen': [''.join(z) for z in k], 'hoehe': [''.join(str(c) for c in z) for z in h],
           'platte': [CX, CY, RAD], 'pfad': PFAD, 'ankunft': ANKUNFT, 'pfeile': PFEILE, 'tor': TOR,
           'computer': COMPUTER, 'teleporter': [{'x': PFEILE[0], 'y': PFEILE[2], 'b': 4, 'h': 1}]}
    json.dump(lay, open(os.path.join(KARTE, 'layout.json'), 'w'), indent=0)
    F = {'.': (10, 14, 30), 'p': (52, 70, 104), 'r': (34, 48, 78), 's': (60, 84, 120), 'a': (60, 84, 120),
         'z': (60, 200, 230)}
    im = Image.new('RGB', (C * 8, R * 8))
    dr = ImageDraw.Draw(im)
    for y in range(R):
        for x in range(C):
            dr.rectangle((x * 8, y * 8, x * 8 + 7, y * 8 + 7), fill=F[k[y, x]], outline=(0, 0, 0))
    im.save(os.path.join(KARTE, 'layout_vorschau.png'))
    print('Karte 16 Layout %dx%d, begehbar %d Kacheln' % (C, R, int((k != '.').sum())))


if __name__ == '__main__':
    main()
