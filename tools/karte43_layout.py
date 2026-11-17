"""Karte 43 - Haunted Castle Outskirts (A03 Nr. 10), Layout nach der Vorlage -> maps/karte43/layout.json

  python3 tools/karte43_layout.py

Vorlage assets/vorlagen/karte43_vorlage.png: 1536x1280 px = 96x80 Kacheln (1:1). Vorland einer Spukburg: Wiesen mit
breiten Erdwegen, Waldguertel ringsum und erhoehte Waldbloecke mit niedriger Steinmauer, rechts die Burg auf einem
gepflasterten Vorplatz, links ein Torbau an einem Waldblock, Ausgaenge oben rechts und unten links.

Klassen:  g Wiese  w Erdweg  h Wald (erhoeht, Hoehe 1, gesperrt)  k Vorplatz-Pflaster  T Teleporter
Verbesserungen gegenueber der Vorlage: Waldraender ueberall mit Steinmauer nach Sueden (in der Vorlage nur stueckweise),
Zipfel/Einzelkacheln geglaettet, Weg auf der Achse des Torbaus, Ausgaenge in voller Wegbreite.
"""
import json, os
from collections import deque
import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte43')
VORLAGE = os.path.join(ROOT, 'assets', 'vorlagen', 'karte43_vorlage.png')
C, R, T = 96, 80, 16
REF = {'g': (87, 142, 61), 'w': (200, 173, 119), 'h': (44, 104, 40), 'k': (137, 144, 149), 'x': (68, 74, 90),
       'y': (102, 107, 122), 'z': (24, 98, 38)}
BURG = (66, 17, 89, 29)          # Burg-Grundflaeche (x0, y0, x1, y1) in Kacheln, auf dem Vorplatz
TOR = (30, 30, 41, 34)           # Torbau (Vorlage x 480-670, y 480-560)
TELEPORTER = [(93, 9, 3, 3), (7, 77, 4, 3)]     # oben rechts unter der Guertelfront (nicht auf der Mauer)


def flaechen(m):
    gesehen = np.zeros_like(m)
    out = []
    for y in range(R):
        for x in range(C):
            if m[y, x] and not gesehen[y, x]:
                q, teil = deque([(y, x)]), []
                gesehen[y, x] = True
                while q:
                    a_, b_ = q.popleft(); teil.append((a_, b_))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        u, v = a_ + dy, b_ + dx
                        if 0 <= u < R and 0 <= v < C and m[u, v] and not gesehen[u, v]:
                            gesehen[u, v] = True; q.append((u, v))
                out.append(teil)
    return out


def zipfel_weg(k, frei='gwkh'):
    for _ in range(6):
        geaendert = False
        for y in range(R):
            for x in range(C):
                if k[y, x] not in frei:
                    continue
                nb = [k[yy, xx] for yy, xx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)) if 0 <= yy < R and 0 <= xx < C]
                if nb.count(k[y, x]) <= 1:
                    fremd = [c for c in nb if c != k[y, x] and c in frei]
                    if fremd:
                        k[y, x] = max(set(fremd), key=fremd.count); geaendert = True
        for art in frei:
            for teil in flaechen(k == art):
                if len(teil) < 6:
                    for (y, x) in teil:
                        nb = [k[yy, xx] for yy, xx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1))
                              if 0 <= yy < R and 0 <= xx < C and k[yy, xx] != art and k[yy, xx] in frei]
                        if nb:
                            k[y, x] = max(set(nb), key=nb.count); geaendert = True
        if not geaendert:
            break
    return k


def main():
    os.makedirs(KARTE, exist_ok=True)
    a = np.array(Image.open(VORLAGE).convert('RGB')).astype(int)
    M = np.zeros((R, C, 3))
    for y in range(R):
        for x in range(C):
            M[y, x] = np.median(a[y * T:(y + 1) * T, x * T:(x + 1) * T].reshape(-1, 3), 0)
    ks = list(REF)
    ref = np.array([REF[c] for c in ks], float)
    k = np.array(ks)[((M[:, :, None, :] - ref[None, None]) ** 2).sum(-1).argmin(-1)]
    k[k == 'z'] = 'h'
    yy, xx = np.mgrid[0:R, 0:C]
    in_burg = (xx >= BURG[0] - 3) & (xx <= BURG[2] + 3) & (yy >= BURG[1] - 1) & (yy <= BURG[3] + 12)
    k[np.isin(k, ['x', 'y']) & in_burg] = 'k'                       # Burg steht auf dem Vorplatz (Objekt)
    k[np.isin(k, ['x', 'y'])] = 'g'                                  # Steinmauern/Torbau der Vorlage: bauen() zeichnet sie
    k[(k == 'k') & ~in_burg] = 'g'                                   # graue Steinreste ausserhalb des Platzes
    x0, y0, x1, y1 = TOR                                             # Torbau: Weg auf der Achse des Durchgangs
    k[y0:y1 + 1, x0:x1 + 1] = 'g'
    k[y0 + 1:y1 + 2, 35:40] = 'w'
    k[0:3, :] = 'h'; k[-3:, :] = 'h'; k[:, 0:3] = 'h'; k[:, -3:] = 'h'   # Waldguertel geschlossen
    for teil in flaechen(k == 'h'):                                  # einzelne Baeume der Vorlage -> Wiese
        if len(teil) < 12:
            for (y, x) in teil:
                k[y, x] = 'g'
    for teil in flaechen(k != 'h'):                                  # Loecher im Wald -> Wald
        if len(teil) < 10:
            for (y, x) in teil:
                k[y, x] = 'h'
    k = zipfel_weg(k)
    for (tx, ty, b, hh) in TELEPORTER:                               # Ausgaenge: Weg durch den Guertel bis zum Rand
        k[ty:ty + hh, tx:tx + b] = 'T'
    k[8:12, 88:93] = np.where(k[8:12, 88:93] == 'h', 'w', k[8:12, 88:93])
    k[74:77, 7:11] = np.where(k[74:77, 7:11] == 'h', 'w', k[74:77, 7:11])
    k[6, 36:58] = 'w'; k[7, 36:58] = np.where(k[7, 36:58] == 'g', 'w', k[7, 36:58])   # obere Wegkante ohne Zinnen
    k[8, 93:96] = 'w'                                                # Reihe ueber dem Teleporter: Weg (Front darueber)
    # 1-Spalten-Vorspruenge an Wald-Seitenkanten (Wandstummel) angleichen
    for _ in range(2):
        for y in range(1, R - 1):
            for x in range(1, C - 1):
                if k[y, x] == 'h' and k[y, x - 1] != 'h' and k[y, x + 1] == 'h' and k[y + 1, x] != 'h' and \
                        sum(1 for yy in range(max(0, y - 20), y) if k[yy, x - 1] == 'h') < 2:
                    pass
        for x in range(1, C - 1):                                   # senkrechte Kante: Spalte, die nur teilweise h ist
            col = (k[:, x] == 'h') & (k[:, x - 1] != 'h') & (k[:, x + 1] == 'h')
            col2 = (k[:, x] == 'h') & (k[:, x + 1] != 'h') & (k[:, x - 1] == 'h')
            for c_, m_ in ((x, col), (x, col2)):
                ys = np.nonzero(m_)[0]
                if 0 < len(ys) <= 16:
                    for y in ys:
                        if k[y + 1 if y + 1 < R else y, c_] != 'h':
                            k[y, c_] = 'g' if k[y, c_ - 1] == 'g' or k[y, c_ + 1] == 'g' else 'w'
    # Wege leicht schwingen (Regel 6): lange gerade Raender mit 1-Kachel-Versaetzen
    import math as _m
    for y in range(12, 60):                                         # linker Aussenweg: rechte Kante pendelt
        off = int(round(1.2 * _m.sin(y / 5.0)))
        x_r = max(x for x in range(3, 12) if k[y, x] == 'w') if any(k[y, x] == 'w' for x in range(3, 12)) else None
        if x_r is not None and off > 0 and k[y, x_r + 1] == 'g':
            k[y, x_r + 1] = 'w'
        elif x_r is not None and off < 0 and k[y, x_r - 2] == 'w':
            k[y, x_r] = 'g'
    k = zipfel_weg(k, 'gwh')
    k[8, 93:96] = 'w'                                                # nach der Glaettung: Front ueber dem Teleporter
    k[:, 92] = np.where((k[:, 92] == 'h') & (k[:, 91] != 'h'), np.where(k[:, 91] == 'w', 'w', 'g'), k[:, 92])   # Guertel einheitlich
    k[38:42, 41:44] = np.where(k[38:42, 41:44] == 'w', 'g', k[38:42, 41:44]) if False else k[38:42, 41:44]
    k[32:35, 42:45] = np.where(k[32:35, 42:45] == 'w', 'g', k[32:35, 42:45])   # Graszunge rechts vom Torbau (Busch)
    h = np.where(k == 'h', 1, 0)
    lay = {'groesse': [C, R], 'klassen': [''.join(z) for z in k], 'hoehe': [''.join(str(c) for c in z) for z in h],
           'burg': list(BURG), 'tor': list(TOR),
           'teleporter': [{'x': tx, 'y': ty, 'b': b, 'h': hh} for (tx, ty, b, hh) in TELEPORTER]}
    json.dump(lay, open(os.path.join(KARTE, 'layout.json'), 'w'), indent=0)
    F = {'g': (90, 150, 60), 'w': (200, 170, 110), 'h': (30, 90, 30), 'k': (140, 140, 150), 'T': (80, 220, 240)}
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
    print('Karte 43 Layout %dx%d' % (C, R))


if __name__ == '__main__':
    main()
