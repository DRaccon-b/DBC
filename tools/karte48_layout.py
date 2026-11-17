"""Karte 48 - Water Realm: Outer Currents (A03 Nr. 15), Layout nach der Vorlage -> maps/karte48/layout.json

  python3 tools/karte48_layout.py

Vorlage assets/vorlagen/karte48_vorlage.png (1536x1280 = 96x80 Kacheln): Flachwasser-Inseln (tuerkis, begehbar, Nutzer)
im tiefen Meer (blau, gesperrt), helle Steinplattformen (Hoehe 1) mit Treppen nach Sueden, rechts eine offene
Wasserbibliothek (Halle mit Rueckwand, Seitenwaenden, Regalen und Saeulen), zwei Teleporter (Blasen) am Kartenrand.

Klassen:  x Tiefwasser  s Flachwasser  p Steinplattform (Hoehe 1)  i Hallenboden (Hoehe 1)  m Hallenwand (Hoehe 1,
          gesperrt)  t Treppe (Frontreihe unter der Plattform)  T Teleporter
Verbesserungen: Zipfel/Einzelkacheln geglaettet; jede Plattform bekommt eine Treppe (in der Vorlage fehlen sie bei den
kleinen Plattformen und den Teleporter-Plattformen), vor/hinter jeder Treppe 2 Reihen Flachwasser bzw. Plattform.
"""
import json, os
import numpy as np
from PIL import Image, ImageDraw
import karte43_layout as k43

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte48')
VORLAGE = os.path.join(ROOT, 'assets', 'vorlagen', 'karte48_vorlage.png')
C, R, T = 96, 80, 16
REF = {'x': (49, 124, 170), 's': (78, 142, 153), 'p': (145, 159, 164), 'q': (129, 135, 149), 'i': (101, 114, 130),
       'j': (83, 91, 108)}
HALLE = (66, 21, 89, 39)                 # Plattform der Halle (x0, y0, x1, y1)
RAUM = (68, 22, 87, 32)                  # Innenraum mit Rueckwand (Reihen 22-24) und Seitenwaenden (Spalten 68/87)
# Treppen aus der Vorlage (x0, x1, Frontreihe = erste Reihe unter der Plattform)
TREPPEN = [(14, 21, 43), (43, 48, 40), (73, 80, 40), (51, 54, 59), (82, 84, 61, 'n')]   # letzte: ergaenzt (Plattform unten Mitte)
TELEPORTER = [(93, 8, 3, 3), (7, 77, 4, 3)]
k43.R, k43.C = R, C


def main():
    os.makedirs(KARTE, exist_ok=True)
    a = np.array(Image.open(VORLAGE).convert('RGB')).astype(int)
    M = np.median(a.reshape(R, T, C, T, 3).transpose(0, 2, 1, 3, 4).reshape(R, C, T * T, 3), 2)
    ks = list(REF)
    ref = np.array([REF[c] for c in ks], float)
    k = np.array(ks)[((M[:, :, None, :] - ref[None, None]) ** 2).sum(-1).argmin(-1)].astype('<U1')
    k[(k == 'q') | (k == 'i') | (k == 'j')] = 'p'                    # Treppen/Halle werden unten gezielt gesetzt
    k = k43.zipfel_weg(k, 'xsp')
    for _ in range(3):
        for y in range(1, R - 1):                                     # 1-Spalten-Kerben/-Vorspruenge der Plattformen
            for x in range(1, C - 1):
                if k[y, x] != 'p' and k[y, x - 1] == 'p' and k[y, x + 1] == 'p':
                    k[y, x] = 'p'
                elif k[y, x] == 'p' and k[y, x - 1] != 'p' and k[y, x + 1] != 'p':
                    k[y, x] = k[y, x - 1]
                if k[y, x] == 'p' and k[y - 1, x] != 'p' and k[y + 1, x] != 'p':
                    k[y, x] = k[y + 1, x]
        for y in range(R - 1):                                        # Schachbrett-Ecken
            for x in range(C - 1):
                q = k[y:y + 2, x:x + 2]
                if q[0, 0] == q[1, 1] and q[0, 1] == q[1, 0] and q[0, 0] != q[0, 1]:
                    k[y + 1, x] = q[0, 0]
        k = k43.zipfel_weg(k, 'xsp')
    k[54:59, 50:57] = 'p'                                             # Plattform unten Mitte rechteckig (Vorlage gestuft)
    k[60:62, 55:58] = np.where(k[60:62, 55:58] == 'x', 's', k[60:62, 55:58])   # Tiefwasser-Zipfel neben der Treppe
    # Halle: Plattform rechteckig, Innenraum, Rueckwand und Seitenwaende
    x0, y0, x1, y1 = HALLE
    k[y0:y1 + 1, x0:x1 + 1] = 'p'
    rx0, ry0, rx1, ry1 = RAUM
    k[ry0:ry1 + 1, rx0:rx1 + 1] = 'i'
    k[ry0:ry0 + 3, rx0:rx1 + 1] = 'm'
    k[ry0:ry1 + 1, rx0] = 'm'; k[ry0:ry1 + 1, rx1] = 'm'
    # Teleporter-Stege zum Kartenrand
    k[8:11, 92:96] = 'p'
    k[76:80, 7:11] = 'p'
    for (tx, ty, b, hh) in TELEPORTER:
        k[ty:ty + hh, tx:tx + b] = 'T'
    # Treppen: Vorlage + je eine fuer Plattformen ohne Treppe (Suedkante mit 2 Reihen Flachwasser davor, sonst Nord)
    plattform = np.isin(k, list('pimT'))
    treppen = []
    for tr in TREPPEN:
        treppen.append([tr[0], tr[1], tr[2], tr[3] if len(tr) > 3 else 's'])
    for teil in k43.flaechen(plattform):
        zs = set(teil)
        if any((ry - 1, xx) in zs or (ry + 1, xx) in zs for (tx0, tx1, ry, *_r) in TREPPEN for xx in range(tx0, tx1 + 1)):
            continue
        ys_ = [y for y, x in teil]; xs_ = [x for y, x in teil]
        best = None
        for richtung in ('s', 'n'):
            for b in (4, 3):
                for x in range(min(xs_), max(xs_) - b + 2):
                    if richtung == 's':
                        rand = [max(y for y, xx in teil if xx == x_) if any(xx == x_ for y, xx in teil) else -9
                                for x_ in range(x - 1, x + b + 1)]
                        if len(set(rand)) != 1 or rand[0] < 0:
                            continue
                        ry = rand[0] + 1
                        if ry + 2 >= R or not all(k[ry + d, x_] == 's' for d in (0, 1, 2) for x_ in range(x - 1, x + b + 1)):
                            continue
                        if not all((ry - d, x_) in zs and k[ry - d, x_] == 'p' for d in (1, 2) for x_ in range(x, x + b)):
                            continue
                    else:
                        rand = [min(y for y, xx in teil if xx == x_) if any(xx == x_ for y, xx in teil) else -9
                                for x_ in range(x - 1, x + b + 1)]
                        if len(set(rand)) != 1 or rand[0] < 3:
                            continue
                        ry = rand[0] - 1
                        if not all(k[ry - d, x_] == 's' for d in (0, 1, 2) for x_ in range(x - 1, x + b + 1)):
                            continue
                        if not all((ry + d, x_) in zs and k[ry + d, x_] == 'p' for d in (1, 2) for x_ in range(x, x + b)):
                            continue
                    mitte = abs(x + b / 2 - (min(xs_) + max(xs_) + 1) / 2)
                    if best is None or (richtung, -b, mitte) < (best[0], -best[1], best[2]):
                        best = (richtung, b, mitte, x, ry)
                if best is not None and best[0] == richtung:
                    break
            if best is not None:
                break
        if best:
            richtung, b, _, x, ry = best
            treppen.append([x, x + b - 1, ry, richtung])
        else:
            print('Plattform ohne Treppe:', min(xs_), min(ys_), max(xs_), max(ys_))
    for (tx0, tx1, ry, r_) in treppen:                               # Flachwasser vor der Treppe (2 Reihen, volle Breite)
        for d in (0, 1, 2):
            yy = ry + d if r_ == 's' else ry - d
            for x in range(tx0 - 1, tx1 + 2):
                if k[yy, x] == 'x':
                    k[yy, x] = 's'
        k[ry, tx0:tx1 + 1] = 't'
    h = np.isin(k, list('pimT')).astype(int)
    lay = {'groesse': [C, R], 'klassen': [''.join(z) for z in k], 'hoehe': [''.join(str(c) for c in z) for z in h],
           'treppen': treppen, 'halle': list(HALLE), 'raum': list(RAUM), 'bruecken': [], 'stege': [],
           'teleporter': [{'x': tx, 'y': ty, 'b': b, 'h': hh} for (tx, ty, b, hh) in TELEPORTER]}
    json.dump(lay, open(os.path.join(KARTE, 'layout.json'), 'w'), indent=0)
    F = {'x': (40, 100, 160), 's': (80, 150, 155), 'p': (190, 200, 205), 'i': (100, 110, 130), 'm': (50, 55, 70),
         't': (240, 170, 60), 'T': (80, 220, 240)}
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
    print('Karte 48 Layout %dx%d, %d Treppen' % (C, R, len(treppen)))


if __name__ == '__main__':
    main()
