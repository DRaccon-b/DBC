"""Karte 47 - Deva Mountain (A03 Nr. 14), Layout nach der Vorlage -> maps/karte47/layout.json

  python3 tools/karte47_layout.py

Vorlage assets/vorlagen/karte47_vorlage.png (auf 1600x1200 skaliert, Original 1,25-fach) = 100x75 Kacheln. Berg der Devas:
graublauer Felsboden mit gepflasterten Wegen, erhoehter heller Felsrand und Felsinseln mit Klippen nach Sueden,
Grasflecken mit Baeumen, Geroellflaechen, runde Arena rechts mit dunklem Boden (begehbar, Nutzer), fuenf Ausgaenge.

Klassen:  g Felsboden  w Pflasterweg  k Geroell  n Gras  d dunkler Boden  h heller Felsrand/Felsinsel (Hoehe 1, gesperrt)
          T Teleporter
Verbesserungen: Zipfel/Einzelkacheln aller Klassen geglaettet, Felsinseln mit Boden ringsum (Front nie am Rand eines
anderen Bodens), Ausgaenge mit Weg in Teleporterbreite.
"""
import json, os
import numpy as np
from PIL import Image, ImageDraw
import karte43_layout as k43

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte47')
VORLAGE = os.path.join(ROOT, 'assets', 'vorlagen', 'karte47_vorlage.png')
C, R, T = 100, 75, 16
REF = {'g': (101, 118, 138), 'h': (137, 151, 165), 'w': (136, 144, 144), 'k': (118, 125, 127), 'n': (80, 136, 56),
       'd': (64, 72, 88), 'c': (90, 100, 112)}
GRABEN = (82.5, 50.5, 14.5, 17.5)       # Ellipse um die Arena (Mitte x, y, Halbachsen) in Kacheln
BRUECKEN_Y = [(42, 44), (57, 59)]       # Reihen der Grabenbruecken (Westseite)
TELEPORTER = [(19, 0, 3, 2), (62, 0, 3, 2), (97, 23, 3, 3), (0, 62, 3, 3), (22, 72, 3, 3)]
k43.R, k43.C = R, C


def main():
    os.makedirs(KARTE, exist_ok=True)
    a = np.array(Image.open(VORLAGE).convert('RGB')).astype(int)
    M = np.median(a.reshape(R, T, C, T, 3).transpose(0, 2, 1, 3, 4).reshape(R, C, T * T, 3), 2)
    ks = list(REF)
    ref = np.array([REF[c] for c in ks], float)
    k = np.array(ks)[((M[:, :, None, :] - ref[None, None]) ** 2).sum(-1).argmin(-1)].astype('<U1')
    k[k == 'c'] = 'h'                                                 # Klippenfronten der Vorlage gehoeren zum Fels
    for teil in k43.flaechen(k == 'n'):                               # Baumkronen/Einzelgras -> Boden
        if len(teil) < 6:
            for (y, x) in teil:
                k[y, x] = 'g'
    k = k43.zipfel_weg(k, 'gwknhd')
    insel = np.zeros((R, C), bool)                                    # nur kleine Felsinseln (nicht der Rand) bekommen
    for teil in k43.flaechen(k == 'h'):                               # Boden ringsum - sonst verschwinden Wege am Rand
        if len(teil) < 300:
            for (y, x) in teil:
                insel[y, x] = True
    for _ in range(3):                                                # Felsinseln: 1 Reihe Boden ringsum, 2 unter der Front
        for y in range(1, R - 2):
            for x in range(1, C - 1):
                if k[y, x] == 'h' and insel[y, x]:
                    for dy, dx in [(d, e) for d in (1, 2) for e in (-1, 0, 1)]:
                        if 0 <= y + dy < R and k[y + dy, x + dx] in 'wknd':
                            k[y + dy, x + dx] = 'g'
        k = k43.zipfel_weg(k, 'gwknhd')
    k[0:2, :] = 'h'; k[-1, :] = 'h'; k[:, 0] = 'h'; k[:, -1] = 'h'     # Felsrand ringsum geschlossen
    # Graben um die Arena (Nutzer): Ring aus tieferem Fels (Klasse x, gesperrt), die Arena liegt dadurch wie auf einem
    # Plateau; zwei Bruecken an der Westseite (Hauptweg bei den Flaggen und unten links)
    yy_, xx_ = np.mgrid[0:R, 0:C]
    d_aussen = ((xx_ - GRABEN[0]) / GRABEN[2]) ** 2 + ((yy_ - GRABEN[1]) / GRABEN[3]) ** 2
    d_innen = ((xx_ - GRABEN[0]) / (GRABEN[2] - 2)) ** 2 + ((yy_ - GRABEN[1]) / (GRABEN[3] - 2)) ** 2
    graben = (d_aussen <= 1.0) & (d_innen > 1.0) & (k != 'h')
    k[graben] = 'x'
    for _ in range(3):
        for y in range(1, R - 1):                                     # 1-Spalten-Kerben/-Vorspruenge im Fels (Wandstummel)
            for x in range(1, C - 1):
                if k[y, x] != 'h' and k[y, x - 1] == 'h' and k[y, x + 1] == 'h':
                    k[y, x] = 'h'
                elif k[y, x] == 'h' and k[y, x - 1] != 'h' and k[y, x + 1] != 'h':
                    k[y, x] = 'g'
        for x in (1, C - 2):                                          # Seitenrand: kurze Kerben (<= 5 Reihen) schliessen
            y = 0
            while y < R:
                if k[y, x] != 'h':
                    y0 = y
                    while y < R and k[y, x] != 'h':
                        y += 1
                    if y - y0 <= 5 and y0 > 0 and y < R and k[y0:y, x - 1 if x == 1 else x + 1].tolist().count('h') == y - y0:
                        k[y0:y, x] = 'h'
                y += 1
        for y in range(1, R - 1):                                     # 1-Spalten-Vorsprung an Seitenkanten (Ende einer Stufe)
            for x in range(1, C - 1):
                if k[y, x] == 'h' and k[y, x + 1] != 'h' and k[y + 1, x] != 'h' and k[y - 1, x] != 'h' and k[y, x - 1] == 'h':
                    k[y, x] = k[y + 1, x]
                if k[y, x] == 'h' and k[y, x + 1] != 'h' and k[y + 1, x] != 'h' and k[y - 1, x] == 'h' and \
                        k[y - 1, x + 1] != 'h' and k[y - 2, x] != 'h' and k[y, x - 1] == 'h':
                    k[y, x] = k[y + 1, x]; k[y - 1, x] = k[y + 1, x]
        for y in range(R - 1):                                        # Schachbrett-Ecken (nur diagonal beruehrend)
            for x in range(C - 1):
                q = k[y:y + 2, x:x + 2]
                if q[0, 0] == q[1, 1] and q[0, 1] == q[1, 0] and q[0, 0] != q[0, 1]:
                    k[y + 1, x] = q[0, 0]
    for (tx, ty, b, hh) in TELEPORTER:                                # Ausgaenge: Weg in Teleporterbreite durch den Rand
        k[ty:ty + hh, tx:tx + b] = 'T'
        if ty == 0:
            k[ty + hh:ty + hh + 3, tx:tx + b] = np.where(k[ty + hh:ty + hh + 3, tx:tx + b] == 'h', 'g', k[ty + hh:ty + hh + 3, tx:tx + b])
        elif ty + hh == R:
            k[ty - 3:ty, tx:tx + b] = np.where(k[ty - 3:ty, tx:tx + b] == 'h', 'g', k[ty - 3:ty, tx:tx + b])
        elif tx == 0:
            k[ty:ty + hh, tx + b:tx + b + 3] = np.where(k[ty:ty + hh, tx + b:tx + b + 3] == 'h', 'g', k[ty:ty + hh, tx + b:tx + b + 3])
            k[ty - 2:ty, 0:tx + b + 3] = np.where(k[ty - 2:ty, 0:tx + b + 3] == 'h', 'g', k[ty - 2:ty, 0:tx + b + 3])
        else:
            k[ty:ty + hh, tx - 3:tx] = np.where(k[ty:ty + hh, tx - 3:tx] == 'h', 'g', k[ty:ty + hh, tx - 3:tx])
            k[ty - 2:ty, tx - 3:C] = np.where(k[ty - 2:ty, tx - 3:C] == 'h', 'g', k[ty - 2:ty, tx - 3:C])
    bruecken = []
    for (by0, by1) in BRUECKEN_Y:                                     # Bruecke = Grabenbreite, Weg 2 Kacheln davor/dahinter
        xs = [x for y in range(by0, by1 + 1) for x in range(C) if k[y, x] == 'x' and x < GRABEN[0]]
        bx0, bx1 = min(xs), max(xs)
        k[by0 - 1:by1 + 2, bx0:bx1 + 1] = 'x'
        k[by0:by1 + 1, bx0:bx1 + 1] = 'b'
        for x in list(range(bx0 - 2, bx0)) + list(range(bx1 + 1, bx1 + 3)):
            k[by0:by1 + 1, x] = 'w'
        bruecken.append([int(bx0), by0, int(bx1), by1])
    h = np.where(k == 'h', 1, 0)
    lay = {'groesse': [C, R], 'klassen': [''.join(z) for z in k], 'hoehe': [''.join(str(c) for c in z) for z in h],
           'bruecken': bruecken, 'stege': [], 'graben': list(GRABEN),
           'teleporter': [{'x': tx, 'y': ty, 'b': b, 'h': hh} for (tx, ty, b, hh) in TELEPORTER]}
    json.dump(lay, open(os.path.join(KARTE, 'layout.json'), 'w'), indent=0)
    F = {'x': (30, 32, 40), 'b': (150, 100, 50), 'g': (101, 118, 138), 'w': (170, 170, 165), 'h': (190, 200, 215), 'k': (130, 135, 120), 'n': (80, 150, 60),
         'd': (50, 55, 70), 'T': (80, 220, 240)}
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
    print('Karte 47 Layout %dx%d' % (C, R))


if __name__ == '__main__':
    main()
