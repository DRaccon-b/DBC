"""Karte 46 - Gekomon Marsh (A03 Nr. 13), Layout nach der Vorlage -> maps/karte46/layout.json

  python3 tools/karte46_layout.py

Vorlage assets/vorlagen/karte46_vorlage.png: 1536x1280 px = 96x80 Kacheln (1:1). Sumpfinseln: Wiesen mit breiten Erdwegen,
zwei breite Holzbruecken ueber das Wasser, Bauernhaus auf einem Sandhof (Faesser, Karren, Brunnen, Baenke), Baeume,
Hecken, Ausgaenge oben rechts (Damm) und links.

Klassen:  g Wiese  w Erdweg/Hof  h Hecke/Waldblock (erhoeht)  x Wasser  b Bruecke (ueber Wasser)  T Teleporter
Verbesserungen: Bruecken exakt so breit wie das Wasser (Weg in voller Breite davor/dahinter), Einzelbaeume/Hecken-
stummel der Vorlage -> Wiese (Baeume setzt objekte), Wasserloecher und Landzipfel geglaettet, Hecken mit Land ringsum.
"""
import json, os
import numpy as np
from PIL import Image, ImageDraw
import karte43_layout as k43

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte46')
VORLAGE = os.path.join(ROOT, 'assets', 'vorlagen', 'karte46_vorlage.png')
C, R, T = 96, 80, 16
REF = {'g': (82, 138, 59), 'w': (200, 173, 119), 'h': (44, 104, 40), 'x': (49, 91, 135), 'p': (174, 122, 64)}
BRUECKEN = [(35, 15, 50, 20), (30, 35, 46, 40)]
HAUS = (71, 24, 84, 29)                 # Bauernhaus der Vorlage (Kacheln), Fuss auf Reihe 29
TELEPORTER = [(87, 0, 4, 3), (0, 70, 3, 4)]       # oben rechts mittig im Damm-Weg
k43.R, k43.C = R, C


def main():
    os.makedirs(KARTE, exist_ok=True)
    a = np.array(Image.open(VORLAGE).convert('RGB')).astype(int)
    M = np.median(a.reshape(R, T, C, T, 3).transpose(0, 2, 1, 3, 4).reshape(R, C, T * T, 3), 2)
    ks = list(REF)
    ref = np.array([REF[c] for c in ks], float)
    k = np.array(ks)[((M[:, :, None, :] - ref[None, None]) ** 2).sum(-1).argmin(-1)].astype('<U1')
    x0, y0, x1, y1 = HAUS
    k[y0:y1 + 1, x0:x1 + 1] = 'w'                                     # Haus steht auf dem Hof (Objekt)
    k[k == 'p'] = 'w'                                                  # Steg-Pixel/Objekte der Vorlage -> Weg
    for (bx0, by0, bx1, by1) in BRUECKEN:                              # unter den Bruecken Wasser
        k[by0:by1 + 1, bx0:bx1 + 1] = 'x'
    for teil in k43.flaechen(k == 'h'):                               # Einzelbaeume der Vorlage -> Wiese
        if len(teil) < 8:
            for (y, x) in teil:
                k[y, x] = 'g'
    for teil in k43.flaechen(k == 'x'):                               # Pfuetzen -> Wiese
        if len(teil) < 8:
            for (y, x) in teil:
                k[y, x] = 'g'
    for teil in k43.flaechen(k != 'x'):                               # Mini-Inseln -> Wasser
        if len(teil) < 8:
            for (y, x) in teil:
                k[y, x] = 'x'
    k = k43.zipfel_weg(k, 'gwh')
    for _ in range(2):                                                # schmale Landzungen (Sandbaenke der Vorlage) -> Wasser
        for y in range(1, R - 1):
            for x in range(1, C - 1):
                if k[y, x] in 'gw' and sum(k[y + dy, x + dx] == 'x' for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1))) >= 2 \
                        and (k[y - 1, x] == 'x' and k[y + 1, x] == 'x' or k[y, x - 1] == 'x' and k[y, x + 1] == 'x'):
                    k[y, x] = 'x'
    for _ in range(3):                                                # Wasserfinger (1 Kachel breit) -> Land
        for y in range(1, R - 1):
            for x in range(1, C - 1):
                if k[y, x] == 'x':
                    nb = [k[y + dy, x + dx] for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1))]
                    if nb.count('x') <= 1:
                        fremd = [c for c in nb if c != 'x']
                        k[y, x] = max(set(fremd), key=fremd.count)
    for _ in range(3):
        for y in range(1, R - 2):                                     # Hecken: ringsum Land, unter der Front 2 Reihen
            for x in range(1, C - 1):
                if k[y, x] == 'h':
                    for dy, dx in [(d, e) for d in (-1, 0, 1, 2) for e in (-1, 0, 1)]:
                        if k[y + dy, x + dx] == 'x':
                            k[y + dy, x + dx] = 'g'
        for y in range(1, R - 1):
            for x in range(1, C - 1):
                if k[y, x] == 'g':
                    nb = [k[y + dy, x + dx] for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1))]
                    if nb.count('g') + nb.count('w') <= 1 and 'h' in nb:
                        k[y, x] = 'h'
    # Bruecken (Nutzer: exakt ans Wasser): unter der Bruecke und 2 Reihen davor/danach genau die Brueckenspalten Wasser,
    # an beiden Enden gerade Uferkanten (3 Spalten Land) - so liegt kein Brueckenende auf Land und kein Wasser daneben
    bruecken = []
    for (bx0, by0, bx1, by1) in BRUECKEN:
        k[by0 - 2:by1 + 3, bx0:bx1 + 1] = 'x'
        for x in list(range(bx0 - 3, bx0)) + list(range(bx1 + 1, bx1 + 4)):
            k[by0 - 1:by1 + 2, x] = np.where(k[by0 - 1:by1 + 2, x] == 'x', 'w', k[by0 - 1:by1 + 2, x])
            k[by0:by1 + 1, x] = 'w'                                   # Weg in voller Brueckenbreite
        k[by0:by1 + 1, bx0:bx1 + 1] = 'b'
        bruecken.append([bx0, by0, bx1, by1])
    for (tx, ty, b, hh) in TELEPORTER:
        k[ty:ty + hh, tx:tx + b] = 'T'
    k[70:74, 3:5] = 'w'                                                # Westausgang: Weg bis zum Teleporter
    h = np.where(k == 'h', 1, 0)
    lay = {'groesse': [C, R], 'klassen': [''.join(z) for z in k], 'hoehe': [''.join(str(c) for c in z) for z in h],
           'bruecken': bruecken, 'haus': list(HAUS), 'stege': [],
           'teleporter': [{'x': tx, 'y': ty, 'b': b, 'h': hh} for (tx, ty, b, hh) in TELEPORTER]}
    json.dump(lay, open(os.path.join(KARTE, 'layout.json'), 'w'), indent=0)
    F = {'g': (90, 150, 60), 'w': (200, 170, 110), 'h': (30, 90, 30), 'x': (50, 90, 140), 'b': (150, 100, 50),
         'T': (80, 220, 240)}
    S_ = 6
    im = Image.new('RGB', (C * S_, R * S_))
    dr = ImageDraw.Draw(im)
    for y in range(R):
        for x in range(C):
            dr.rectangle((x * S_, y * S_, x * S_ + S_ - 1, y * S_ + S_ - 1), fill=F[k[y, x]])
    vg = Image.open(VORLAGE).convert('RGB').resize((C * S_, R * S_))
    both = Image.new('RGB', (C * S_ * 2 + 8, R * S_))
    both.paste(vg, (0, 0)); both.paste(im, (C * S_ + 8, 0))
    both.save(os.path.join(KARTE, 'layout_vergleich.png'))
    print('Karte 46 Layout %dx%d' % (C, R), bruecken)


if __name__ == '__main__':
    main()
