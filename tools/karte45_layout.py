"""Karte 45 - Orochimon's Marsh (A03 Nr. 12), Layout nach der Vorlage -> maps/karte45/layout.json

  python3 tools/karte45_layout.py

Vorlage assets/vorlagen/karte45_vorlage.png: 768x576 px = 48x36 Kacheln (1:1). Insel im Sumpfsee: Wiese mit Erdwegen,
Baeume, erhoehte Waldbloecke, grosser Holzsteg im Sueden (Ausgang unten links am Stegende).

Klassen:  g Wiese  w Erdweg  h Wald (erhoeht, Hoehe 1)  x Wasser  p Holzsteg (ueber Wasser)  T Teleporter
Verbesserungen gegenueber der Vorlage: Steg liegt ganz ueber Wasser und schliesst an die Uferkante an (in der Vorlage
ueber dem Land), Graszipfel zwischen den Stegarmen -> Wasser, 1 Kachel breite Wege auf 2 Kacheln, Zipfel geglaettet,
Weg trifft den Steg in voller Breite.
"""
import json, os
import numpy as np
from PIL import Image, ImageDraw
import karte43_layout as k43

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte45')
VORLAGE = os.path.join(ROOT, 'assets', 'vorlagen', 'karte45_vorlage.png')
C, R, T = 48, 36, 16
REF = {'g': (82, 138, 59), 'w': (200, 173, 119), 'h': (44, 104, 40), 'x': (49, 91, 135), 'p': (174, 122, 64)}
TELEPORTER = [(6, 33, 4, 3)]
k43.R, k43.C = R, C


def main():
    os.makedirs(KARTE, exist_ok=True)
    a = np.array(Image.open(VORLAGE).convert('RGB')).astype(int)
    M = np.median(a.reshape(R, T, C, T, 3).transpose(0, 2, 1, 3, 4).reshape(R, C, T * T, 3), 2)
    ks = list(REF)
    ref = np.array([REF[c] for c in ks], float)
    k = np.array(ks)[((M[:, :, None, :] - ref[None, None]) ** 2).sum(-1).argmin(-1)].astype('<U1')
    k[26, 14:20] = 'x'                                                # Graszipfel zwischen den Stegarmen
    k[33:36, 6:10] = 'p'                                              # Steg bis zum Teleporter
    for teil in k43.flaechen(k == 'h'):                               # Einzelbaeume der Vorlage -> Wiese
        if len(teil) < 8:
            for (y, x) in teil:
                k[y, x] = 'g'
    # 1 Kachel breite Wege auf 2 Kacheln verbreitern (sonst runde Punkte im 45-Grad-Raster)
    w = k == 'w'
    for y in range(1, R - 1):
        for x in range(1, C - 1):
            if w[y, x] and not w[y, x - 1] and not w[y, x + 1] and k[y, x + 1] == 'g':
                k[y, x + 1] = 'w'
            if w[y, x] and not w[y - 1, x] and not w[y + 1, x] and k[y + 1, x] == 'g':
                k[y + 1, x] = 'w'
    k = k43.zipfel_weg(k, 'gwh')
    for teil in k43.flaechen(k == 'x'):                               # Pfuetzen auf der Insel -> Wiese
        if len(teil) < 6:
            for (y, x) in teil:
                k[y, x] = 'g'
    for (tx, ty, b, hh) in TELEPORTER:
        k[ty:ty + hh, tx:tx + b] = 'T'
    h = np.where(k == 'h', 1, 0)
    stege = []                                                        # Steg als Rechtecke (zeilenweise Laeufe)
    for y in range(R):
        x = 0
        while x < C:
            if k[y, x] in 'pT':
                x0 = x
                while x < C and k[y, x] in 'pT':
                    x += 1
                stege.append([x0, y, x - 1, y])
            x += 1
    lay = {'groesse': [C, R], 'klassen': [''.join(z) for z in k], 'hoehe': [''.join(str(c) for c in z) for z in h],
           'stege': stege, 'bruecken': stege,
           'teleporter': [{'x': tx, 'y': ty, 'b': b, 'h': hh} for (tx, ty, b, hh) in TELEPORTER]}
    json.dump(lay, open(os.path.join(KARTE, 'layout.json'), 'w'), indent=0)
    F = {'g': (90, 150, 60), 'w': (200, 170, 110), 'h': (30, 90, 30), 'x': (50, 90, 140), 'p': (150, 100, 50),
         'T': (80, 220, 240)}
    S_ = 8
    im = Image.new('RGB', (C * S_, R * S_))
    dr = ImageDraw.Draw(im)
    for y in range(R):
        for x in range(C):
            dr.rectangle((x * S_, y * S_, x * S_ + S_ - 1, y * S_ + S_ - 1), fill=F[k[y, x]])
    vg = Image.open(VORLAGE).convert('RGB').resize((C * S_, R * S_))
    both = Image.new('RGB', (C * S_ * 2 + 8, R * S_))
    both.paste(vg, (0, 0)); both.paste(im, (C * S_ + 8, 0))
    both.save(os.path.join(KARTE, 'layout_vergleich.png'))
    print('Karte 45 Layout %dx%d' % (C, R))


if __name__ == '__main__':
    main()
