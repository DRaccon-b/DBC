"""Karte 44 - Chuchidarumon Village (A03 Nr. 11), Layout nach der Vorlage -> maps/karte44/layout.json

  python3 tools/karte44_layout.py

Vorlage assets/vorlagen/karte44_vorlage.png: 1536x1280 px = 96x80 Kacheln (1:1). Dorf der Chuchidarumon: Wiesen mit
breiten Erdwegen, ein Bach von Nord nach Sued mit fuenf Holzbruecken, Kuppelhuetten mit Schneedach, Waldguertel und
erhoehte Waldbloecke, sechs Ausgaenge am Rand.

Klassen:  g Wiese  w Erdweg  h Wald (erhoeht, Hoehe 1, gesperrt)  x Bach  b Bruecke (ueber dem Bach)  T Teleporter
Verbesserungen gegenueber der Vorlage: Waldbloecke mit Steinmauer an allen Suedkanten, Zipfel/Einzelkacheln und
1-Kachel-Graszungen zwischen Wegen geglaettet, Weg in voller Brueckenbreite vor und hinter jeder Bruecke, Ausgaenge in
voller Breite des Teleporters, Bach laeuft oben und unten aus der Karte (Wald ringsum, kein Ufer am Rand).
"""
import json, os
import numpy as np
from PIL import Image, ImageDraw
import karte43_layout as k43

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte44')
VORLAGE = os.path.join(ROOT, 'assets', 'vorlagen', 'karte44_vorlage.png')
C, R, T = 96, 80, 16
REF = {'g': (87, 142, 61), 'g2': (72, 132, 48), 'w': (200, 173, 119), 'h': (44, 104, 40), 'h2': (36, 96, 36),
       'x': (49, 124, 170), 'b': (174, 122, 64)}
BRUECKEN = [(42, 15, 48, 18), (47, 26, 53, 29), (46, 39, 52, 42), (57, 53, 63, 56), (59, 61, 65, 64)]
TELEPORTER = [(78, 0, 4, 3), (0, 22, 3, 4), (0, 54, 3, 4), (93, 66, 3, 4), (61, 77, 4, 3), (77, 77, 4, 3)]   # unten: 3 Spalten Wald bis zum Bach
# Huetten der Vorlage (Mitte in px) - Flaechen werden Wiese, die Huetten setzt objekte()
HUETTEN = [(370, 470), (1070, 355), (1200, 320), (590, 505), (1085, 800), (260, 700), (512, 1045), (320, 1150),
           (465, 1165), (1378, 915)]


def main():
    os.makedirs(KARTE, exist_ok=True)
    a = np.array(Image.open(VORLAGE).convert('RGB')).astype(int)
    M = np.median(a.reshape(R, T, C, T, 3).transpose(0, 2, 1, 3, 4).reshape(R, C, T * T, 3), 2)
    ks = list(REF)
    ref = np.array([REF[c] for c in ks], float)
    k = np.array([c[0] for c in ks])[((M[:, :, None, :] - ref[None, None]) ** 2).sum(-1).argmin(-1)]
    k = k.astype('<U1')
    for (cx, cy) in HUETTEN:                                          # Huettenflaechen -> Wiese
        x0, x1, y0, y1 = cx // T - 2, cx // T + 2, cy // T - 2, cy // T + 1
        sub = k[y0:y1 + 1, x0:x1 + 1]
        sub[sub != 'w'] = 'g'
        sub[(sub == 'w')] = 'g' if (k[y0 - 1:y1 + 2, x0 - 1:x1 + 2] == 'g').mean() > 0.4 else 'w'
    k[k == 'b'] = 'w'                                                 # Bruecken setzt unten die Liste
    for teil in k43.flaechen(k == 'h'):                               # einzelne Baeume -> Wiese
        if len(teil) < 14:
            for (y, x) in teil:
                k[y, x] = 'g'
    for teil in k43.flaechen(k == 'x'):                               # Steine/Gras im Bach -> nur der Bach
        if len(teil) < 6:
            for (y, x) in teil:
                k[y, x] = 'g'
    for teil in k43.flaechen((k != 'h')):
        if len(teil) < 10:
            for (y, x) in teil:
                k[y, x] = 'h'
    # Bach: Spalten des Laufs je Reihe aus der Vorlage, Steine/Bueschel im Wasser auffuellen, 4-6 Kacheln breit
    xr = []
    for y in range(R):
        xs = np.nonzero(k[y] == 'x')[0]
        xs = xs[(xs > 35) & (xs < 80)]
        xr.append((xs.min(), xs.max()) if len(xs) else None)
    xr[63], xr[67] = (60, 63), (64, 67)                                # Vorlagenfehler: Bach verschwindet unter dem Weg
    for y in (64, 65, 66, 68, 69, 70):                                 # -> eigener Lauf mit zweiter Bruecke (68-71)
        xr[y] = None
    for y in range(R):
        if xr[y] is None:                                             # unter Bruecken und Vorlagenluecke: linear
            yo = next(yy for yy in range(y, -1, -1) if xr[yy])
            yu = next(yy for yy in range(y, R) if xr[yy])
            t_ = (y - yo) / float(yu - yo)
            xr[y] = tuple(int(round(xr[yo][i] + (xr[yu][i] - xr[yo][i]) * t_)) for i in (0, 1))
    xr[0:3] = [xr[3]] * 3; xr[R - 3:] = [xr[R - 4]] * 3                 # Bach laeuft gerade aus der Karte
    k[k == 'x'] = 'g'
    for y in range(R):
        x0, x1 = xr[y]
        if x1 - x0 < 3:
            x1 = x0 + 3
        k[y, x0:x1 + 1] = 'x'
    rand = np.zeros((R, C), bool)
    rand[0:3, :] = rand[-3:, :] = True; rand[:, 0:3] = rand[:, -3:] = True
    k[rand & (k != 'x')] = 'h'                                        # Guertel geschlossen (Bach laeuft hindurch)
    k[:, 3:5][k[:, 3:5] == 'g'] = 'h'                                  # Seitenguertel mind. 5 Kacheln (sonst nur eine
    k[:, C - 5:C - 3][k[:, C - 5:C - 3] == 'g'] = 'h'                  # Baumsaeule mit kahlem Boden)
    for y in range(R):                                                # Wege ohne Ausgang enden vor dem Guertel
        if not any(tx == 0 and ty - 1 <= y <= ty + hh for (tx, ty, b, hh) in TELEPORTER):
            k[y, 3:5] = np.where(k[y, 3:5] == 'w', 'h', k[y, 3:5])
        if not any(tx + b == C and ty - 1 <= y <= ty + hh for (tx, ty, b, hh) in TELEPORTER):
            k[y, C - 5:C - 3] = np.where(k[y, C - 5:C - 3] == 'w', 'h', k[y, C - 5:C - 3])
    k = k43.zipfel_weg(k, 'gwh')
    bru = BRUECKEN + [(64, 68, 70, 71)]
    for y in (65, 66, 67):                                            # Bach zwischen den Bruecken im Gras
        xs_ = np.nonzero(k[y] == 'x')[0]
        k[y, xs_.min() - 2:xs_.max() + 3] = np.where(k[y, xs_.min() - 2:xs_.max() + 3] == 'x', 'x', 'g')
    for (x0, y0, x1, y1) in bru:                                      # Bruecke: Weg in voller Breite 2 Reihen davor/danach
        for y in range(y0, y1 + 1):
            wx = np.nonzero(k[y] == 'x')[0]
            wx = wx[(wx >= x0 - 3) & (wx <= x1 + 3)]
            bx0, bx1 = wx.min(), wx.max()
            k[y, bx0:bx1 + 1] = 'b'
            k[y, bx0 - 3:bx0] = np.where(k[y, bx0 - 3:bx0] == 'h', 'h', 'w')
            k[y, bx1 + 1:bx1 + 4] = np.where(k[y, bx1 + 1:bx1 + 4] == 'h', 'h', 'w')
    for (tx, ty, b, hh) in TELEPORTER:                                # Ausgaenge: Weg durch den Guertel
        k[ty:ty + hh, tx:tx + b] = 'T'
        if tx == 0:
            k[ty:ty + hh, tx + b:tx + b + 2] = 'w'                     # durch den Guertel bis in die Wiese
            k[ty:ty + hh, tx + b:tx + b + 4] = np.where(k[ty:ty + hh, tx + b:tx + b + 4] == 'x', 'x', 'w')
        elif tx + b == C:
            k[ty:ty + hh, tx - 4:tx] = np.where(k[ty:ty + hh, tx - 4:tx] == 'x', 'x', 'w')
        elif ty == 0:
            k[ty + hh:ty + hh + 4, tx:tx + b] = 'w'
        else:
            k[ty - 4:ty, tx:tx + b] = np.where(k[ty - 4:ty, tx:tx + b] == 'x', 'x', 'w')
    for (tx, ty, b, hh) in TELEPORTER:                                # Seitenausgaenge: Reihe ueber dem Teleporter Weg
        if (tx == 0 or tx + b == C) and k[ty - 1, tx] == 'h':          # (die Guertelfront liegt dort, nicht auf den
            k[ty - 1, tx:tx + b] = 'w'                                # Teleporterplatten; Karte 43)
            for x_ in list(range(tx + b, tx + b + 4)) + list(range(tx - 4, tx)):   # 1-Spalten-Vorsprung daneben
                if 0 <= x_ < C and k[ty - 1, x_] == 'h' and k[ty, x_] == 'w':
                    k[ty - 1, x_] = 'w'
    k[57, 8] = 'w'                                                    # Schachbrett-Ecke Weg/Gras aufgeloest
    for y in range(1, R - 1):                                         # einzelne Graskacheln im Weg (Brueckenende)
        for x in range(1, C - 1):
            if k[y, x] == 'g' and sum(k[y + dy, x + dx] == 'g' for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1))) <= 1 \
                    and sum(k[y + dy, x + dx] in 'wb' for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1))) >= 2:
                k[y, x] = 'w'
    for y in (73, 74):                                                # Waldblock unten: Mauer frei vor den Guertelkronen
        k[y, 28:46] = np.where(k[y, 28:46] == 'h', 'g', k[y, 28:46])
    for y in range(R - 5, R - 3):                                      # 1-Kachel-Waldnasen ueber dem Bachauslauf
        for x in range(1, C - 1):
            if k[y, x] == 'h' and k[y, x - 1] != 'h' and k[y, x + 1] != 'h':
                k[y, x] = 'g'
    h = np.where(k == 'h', 1, 0)
    bruecken = []
    for (x0, y0, x1, y1) in bru:
        xs = [x for y in range(y0, y1 + 1) for x in range(C) if k[y, x] == 'b']
        bruecken.append([min(xs), y0, max(xs), y1])
    lay = {'groesse': [C, R], 'klassen': [''.join(z) for z in k], 'hoehe': [''.join(str(c) for c in z) for z in h],
           'bruecken': bruecken, 'huetten': HUETTEN,
           'teleporter': [{'x': tx, 'y': ty, 'b': b, 'h': hh} for (tx, ty, b, hh) in TELEPORTER]}
    json.dump(lay, open(os.path.join(KARTE, 'layout.json'), 'w'), indent=0)
    F = {'g': (90, 150, 60), 'w': (200, 170, 110), 'h': (30, 90, 30), 'x': (50, 120, 200), 'b': (150, 90, 40),
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
    print('Karte 44 Layout %dx%d' % (C, R))


if __name__ == '__main__':
    main()
