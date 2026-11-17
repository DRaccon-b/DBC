"""Karte 51 - Suzaku Gate (A03 Nr. 18), Arena des Zhuqiaomon, Layout nach der Vorlage -> maps/karte51/layout.json

  python3 tools/karte51_layout.py

Vorlage assets/vorlagen/karte51_vorlage.png (768x576 = 48x36 Kacheln), Kacheln wie Karte 47/50: Felsboden, erhoehter
Felsrand, Wiesenflecken, erhoehter Ziegelplatz mit Arena (Pflasterquadrat mit Rautenmuster), Treppe im Sueden, Ziegelweg
zum Teleporter unten links.

Klassen:  g Felsboden  n Wiese  z Ziegelplatz  w Arena-Pflaster  h Felsrand  t Treppe  T Teleporter
Hoehen:   0 Boden  1 Platz/Arena (erhoeht, Treppe im Sueden)  2 Felsrand
Korrekturen: Raute exakt auf der berechneten Arenamitte (45-Grad-Raster), Zipfel/Einzelkacheln geglaettet, Treppe in voller
Breite mit 2 Reihen frei davor/dahinter, Teleporter auf dem Ziegelweg (Ebene des Platzes), Brandflecken (Nutzer: etwas
verbrannt, Zhuqiaomons Arena).
"""
import json, os
import numpy as np
from PIL import Image, ImageDraw
import karte43_layout as k43

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte51')
VORLAGE = os.path.join(ROOT, 'assets', 'vorlagen', 'karte51_vorlage.png')
C, R, T = 48, 36, 16
REF = {'h': (137, 151, 165), 'g': (115, 131, 147), 'z': (124, 135, 136), 'w': (138, 146, 155), 'n': (82, 138, 59),
       'y': (106, 126, 141), 'r': (89, 109, 128), 'q': (116, 131, 136)}
ARENA = (15, 7, 34, 21)                  # Pflasterquadrat (x0, y0, x1, y1) in Kacheln
TREPPE = (21, 28, 29)                    # Spalten x0..x1, Frontreihe (8 breit: Torii-Pfeiler am Treppenfuss, wie K50)
TELEPORTER = [(6, 33, 4, 3)]
# Brandflecken (Nutzer: etwas verbrannt) - Polygone in Pixeln
BRAND = [
    [(400, 168), (464, 232), (400, 296), (336, 232)],                                                 # Arenamitte: Raute im Rautenband
    [(610, 230), (680, 220), (712, 260), (700, 320), (640, 330), (600, 290)],                            # Wiese rechts
    [(470, 440), (560, 430), (610, 470), (590, 520), (500, 525), (460, 490)],                            # unten rechts
    [(60, 380), (130, 370), (150, 420), (110, 460), (60, 450)],                                         # links
]
k43.R, k43.C = R, C


def main():
    os.makedirs(KARTE, exist_ok=True)
    a = np.array(Image.open(VORLAGE).convert('RGB')).astype(int)
    M = np.median(a.reshape(R, T, C, T, 3).transpose(0, 2, 1, 3, 4).reshape(R, C, T * T, 3), 2)
    ks = list(REF)
    ref = np.array([REF[c] for c in ks], float)
    k = np.array(ks)[((M[:, :, None, :] - ref[None, None]) ** 2).sum(-1).argmin(-1)].astype('<U1')
    k[np.isin(k, list('yr'))] = 'h'
    k[k == 'q'] = 'z'
    # Arena: Pflasterquadrat mit Ziegelrahmen, Raute exakt auf der Mitte (45-Grad-Raster)
    x0, y0, x1, y1 = ARENA
    k[(k == 'w')] = 'z'
    k[y0:y1 + 1, x0:x1 + 1] = 'w'
    cx, cy = (x0 + x1 + 1) / 2.0, (y0 + y1 + 1) / 2.0
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            d = abs(x + 0.5 - cx) / 1.0 + abs(y + 0.5 - cy)
            if False and 6.0 <= d < 7.0:                             # Raute zeichnet bauen als 45-Grad-Band (Pixel)
                k[y, x] = 'z'
    for teil in k43.flaechen(k == 'n'):
        if len(teil) < 6:
            for (y, x) in teil:
                k[y, x] = 'g'
    k[0:3, :] = 'h'; k[-3:, :] = 'h'; k[:, 0:3] = 'h'; k[:, -3:] = 'h'
    k = k43.zipfel_weg(k, 'gnhz')
    for _ in range(2):
        for y in range(R - 1):                                        # Schachbrett-Ecken
            for x in range(C - 1):
                q = k[y:y + 2, x:x + 2]
                if q[0, 0] == q[1, 1] and q[0, 1] == q[1, 0] and q[0, 0] != q[0, 1] and 'w' not in q:
                    k[y + 1, x] = q[0, 0]
    # Treppe: Platz endet ueber der Frontreihe, 2 Reihen Boden davor, 2 Reihen Platz dahinter
    tx0, tx1, ry = TREPPE
    k[23:ry, tx0 - 3:tx1 + 4] = 'z'                                     # Platzkante 2+ Kacheln gerade neben der Treppe
    k[4:7, 12:15] = np.where(k[4:7, 12:15] == 'z', 'g', k[4:7, 12:15])   # Nordecken ohne 1-Spalten-Stufen unter der Front
    k[4:7, 35:38] = np.where(k[4:7, 35:38] == 'z', 'g', k[4:7, 35:38])
    k[ry:ry + 3, tx0 - 1:tx1 + 2] = np.where(np.isin(k[ry:ry + 3, tx0 - 1:tx1 + 2], ['z', 'n']), 'g', k[ry:ry + 3, tx0 - 1:tx1 + 2])
    k[ry, tx0:tx1 + 1] = 't'
    wt = (7, 10, 22)                                                 # Nordtreppe: Westboden -> Ziegelweg (Reihe 22 = Boden)
    k[wt[2] - 2:wt[2] + 1, wt[0] - 1:wt[1] + 2] = np.where(np.isin(k[wt[2] - 2:wt[2] + 1, wt[0] - 1:wt[1] + 2], ['z', 'n', 'h']), 'g',
                                                           k[wt[2] - 2:wt[2] + 1, wt[0] - 1:wt[1] + 2])
    k[wt[2] + 1:wt[2] + 4, wt[0]:wt[1] + 1] = 'z'
    for (tx, ty, b, hh) in TELEPORTER:                               # Ausgang am Ende des Ziegelwegs
        k[ty:ty + hh, tx:tx + b] = 'T'
    hp = np.where(np.isin(k, list('zwT')), 1, 0)
    hp[k == 'h'] = 2
    brand = Image.new('L', (C, R), 0)
    for poly in BRAND:
        ImageDraw.Draw(brand).polygon([(x / T, y / T) for (x, y) in poly], fill=255)
    brand = (np.array(brand) > 0).astype(int)
    for _ in range(2):                                               # keine Einzelkachel-Spitzen (werden runde Knubbel)
        nb = sum(np.roll(np.roll(np.pad(brand, 1), dy, 0), dx, 1)[1:-1, 1:-1] for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        brand[(brand == 1) & (nb <= 1)] = 0
        brand[(brand == 0) & (nb >= 3)] = 1
    lay = {'groesse': [C, R], 'klassen': [''.join(z) for z in k], 'hoehe': [''.join(str(c) for c in z) for z in hp],
           'treppen': [[tx0, tx1, ry, 's'], [wt[0], wt[1], wt[2], 'n']], 'arena': [x0, y0, x1, y1], 'brand': [''.join(str(c) for c in z) for z in brand],
           'bruecken': [], 'stege': [], 'teleporter': [{'x': tx, 'y': ty, 'b': b, 'h': hh} for (tx, ty, b, hh) in TELEPORTER]}
    json.dump(lay, open(os.path.join(KARTE, 'layout.json'), 'w'), indent=0)
    F = {'g': (115, 131, 147), 'n': (80, 150, 60), 'z': (150, 120, 110), 'w': (175, 175, 170), 'h': (210, 215, 225),
         't': (240, 170, 60), 'T': (80, 220, 240)}
    S_ = 8
    im = Image.new('RGB', (C * S_, R * S_))
    dr = ImageDraw.Draw(im)
    for y in range(R):
        for x in range(C):
            c = F[k[y, x]] if not brand[y, x] else tuple(int(v * 0.5) for v in F[k[y, x]])
            dr.rectangle((x * S_, y * S_, x * S_ + S_ - 1, y * S_ + S_ - 1), fill=c)
    vg = Image.open(VORLAGE).convert('RGB').resize((C * S_, R * S_))
    both = Image.new('RGB', (C * S_ * 2 + 8, R * S_))
    both.paste(vg, (0, 0)); both.paste(im, (C * S_ + 8, 0))
    both.save(os.path.join(KARTE, 'layout_vergleich.png'))
    print('Karte 51 Layout %dx%d' % (C, R))


if __name__ == '__main__':
    main()
