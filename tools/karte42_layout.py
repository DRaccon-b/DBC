"""Karte 42 - Digital World: Wind Valley (A03 Nr. 9), Layout nach der Vorlage -> maps/karte42/layout.json

  python3 tools/karte42_layout.py

Vorlage assets/vorlagen/karte42_vorlage.png: 1536x1280 px = 96x80 Kacheln (1:1). Windtal: Talboden aus hellem Sand mit
breiten Windbahnen (dunklerer Sand), zwei begehbare Hochplateaus oben mit Treppen, ein rautenfoermiger Felsblock in der
Mitte und ein hoher Felsrand ringsum, graue Pflasterflecken, Ausgaenge oben rechts und unten links.

Korrigierte Vorlagenfehler (Nutzer: "viele Vorlagen-Fehler"):
  - Felsrand und Raute haben an ihren Suedkanten keine Felsfront -> Hoehenstufen 0/1/2, bauen() zeichnet alle Fronten.
  - Die Treppen sind Holzgatter -> echte Steintreppen in voller Breite, davor und dahinter 2 Reihen Weg (Pruefliste).
  - Einzelne Pixel-/Kachelreste (Quadrat oben links, Zacken, Inseln) -> Zipfel und Kleinflecken angeglichen.
  - Der Weg oben rechts laeuft blind in den Felsrand -> er endet am Ausgang (Bogen zum Teleporter).
  - Felsfront ueber dem Ausgang oben rechts wuerde auf dem Teleporter liegen -> 2 Reihen Boden darueber.

Klassen:  r Fels (Rand/Raute, Hoehe 2)  p Hochplateau (begehbar, Hoehe 1)  q Weg auf dem Plateau (Hoehe 1)
          s heller Sand  b Windbahn  k Pflaster  t Treppe  T Teleporter
"""
import json, os, sys
from collections import deque
import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte42')
VORLAGE = os.path.join(ROOT, 'assets', 'vorlagen', 'karte42_vorlage.png')
C, R, T = 96, 80, 16
REF = {'r': (222, 176, 114), 's': (230, 211, 151), 'b': (182, 154, 104), 'k': (155, 148, 124),
       'f': (161, 113, 72), 'g': (155, 96, 62), 'h': (199, 150, 97)}
PLATEAUS = [(7, 6, 36, 27), (51, 5, 82, 27)]          # (x0, y0, x1, y1): begehbare Hochplateaus (Hoehe 1)
TREPPEN = [(17, 22), (66, 71)]                        # Spalten der Treppen in der Plateaufront (Reihen 28-29)
FRONT_REIHE = 28                                      # erste Reihe unter den Plateaus (Front, Bodenhoehe)
TELEPORTER = [(93, 8, 3, 4), (7, 77, 4, 3)]           # (x, y, b, h): oben rechts, unten links


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


def zipfel_weg(k, frei='sbk'):
    """Zipfel/Kerben: Kachel mit <= 1 gleichen Nachbarn -> haeufigster Nachbar; Kleinflecken < 6 Kacheln."""
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
    k[np.isin(k, ['f', 'g', 'h'])] = 'b'              # Felsfront/Treppe der Vorlage: bauen() zeichnet sie neu
    k[0] = 'r'; k[-1] = 'r'; k[:, 0] = 'r'; k[:, -1] = 'r'
    for teil in flaechen(k == 'r'):                   # orange Kleinflecken (Objekte, Quadrat oben links) -> Boden
        if len(teil) < 16:
            for (y, x) in teil:
                k[y, x] = 's'
    # Hochplateaus: orange Flaeche in den Plateau-Rechtecken, Front bis Reihe 27 gerade (ganze Breite auf Plateauhoehe)
    for (x0, y0, x1, y1) in PLATEAUS:
        sub = k[y0:y1 + 1, x0:x1 + 1]
        sub[sub == 'r'] = 'p'
        k[y1, x0:x1 + 1] = 'p'; k[y1 - 1, x0:x1 + 1] = 'p'
        k[FRONT_REIHE:FRONT_REIHE + 2, x0:x1 + 1] = np.where(k[FRONT_REIHE:FRONT_REIHE + 2, x0:x1 + 1] == 'r', 'b',
                                                             k[FRONT_REIHE:FRONT_REIHE + 2, x0:x1 + 1])
    for (x0, y0, x1, y1) in PLATEAUS:                 # Sand-/Wegflecken im Plateau (Objekte der Vorlage) -> Plateau
        sub = np.zeros((R, C), bool); sub[y0:y1 + 1, x0:x1 + 1] = True
        for teil in flaechen(sub & (k != 'p') & (k != 'r')):
            if len(teil) < 20 and all(y0 < y < y1 and x0 < x < x1 for (y, x) in teil):
                for (y, x) in teil:
                    k[y, x] = 'p'
    for teil in flaechen(k == 'p'):                   # p-Reste ausserhalb der grossen Flaechen -> Fels
        if len(teil) < 40:
            for (y, x) in teil:
                k[y, x] = 'r'
    for teil in flaechen(np.isin(k, ['s', 'b', 'k'])):   # Bodenloecher im Fels -> Fels
        if len(teil) < 16:
            for (y, x) in teil:
                k[y, x] = 'r'
    for _ in range(2):                                # 1 Kachel breite Felsfinger/-schlitze glaetten (45-Grad-Raster)
        for y in range(1, R - 1):
            for x in range(1, C - 1):
                nb = [k[y - 1, x], k[y + 1, x], k[y, x - 1], k[y, x + 1]]
                if k[y, x] in 'sbk' and nb.count('r') >= 3:
                    k[y, x] = 'r'
                elif k[y, x] == 'r' and nb.count('r') <= 1 and 0 < y < R - 1:
                    k[y, x] = 's'
                elif k[y, x] == 'p' and nb.count('p') <= 1:
                    k[y, x] = 'r'
    k = zipfel_weg(k)
    # Treppen in voller Breite: 2 Reihen Weg auf dem Plateau (q) und 2 Reihen Windbahn davor (Pruefliste Weg-Treppe)
    for (x0, x1) in TREPPEN:
        k[FRONT_REIHE:FRONT_REIHE + 2, x0:x1 + 1] = 't'
        k[FRONT_REIHE - 2:FRONT_REIHE, x0:x1 + 1] = 'q'
        k[FRONT_REIHE + 2:FRONT_REIHE + 4, x0 - 1:x1 + 2] = 'b'
    # Ausgang oben rechts: Weg biegt zum Teleporter, Fels darueber 2 Reihen zurueck (Front nie auf dem Teleporter)
    k[6:12, 84:93][k[6:12, 84:93] == 'r'] = 'b'
    k[1:6, 84:93] = 'r'                               # kein blinder Wegstummel am oberen Rand
    for (tx, ty, b_, hh) in TELEPORTER:
        k[ty:ty + hh, tx:tx + b_] = 'T'
        for y in range(max(0, ty - 2), ty):
            for x in range(tx, tx + b_):
                if k[y, x] == 'r':
                    k[y, x] = 'b'
    k[77:80, 7:11] = 'T'
    # Vorlagenfehler: Huette stand mitten auf der Windbahn, Zeltreste als b-Zacken -> Sandplaetze fuer Huette und Lager
    k[33:38, 14:24] = 's'                             # Platz der Huette (links neben dem Weg, nicht am Treppenaustritt)
    k[54:58, 4:14] = np.where(k[54:58, 4:14] == 'r', 'r', 's')   # Lagerplatz am Unterstand
    # Pruefung: Plateaufront darf nicht auf dem Felsrand stehen (Graben ohne Breite) -> Rand schliesst an das Plateau an
    for (x0, y0, x1, y1) in PLATEAUS:
        for x in range(x0, x1 + 1):
            if k[FRONT_REIHE + 2, x] == 'r' and k[FRONT_REIHE, x] != 't':
                k[FRONT_REIHE:FRONT_REIHE + 2, x] = 'r'
    # Pruefung: Talstreifen <= 2 Reihen zwischen Felsrand (oben) und Plateau (unten) verschwindet unter der Front ->
    # Rand und Plateau schliessen dort auf gleicher Hoehe an (keine Wandstummel mitten im Plateausand)
    for x in range(C):
        y = 1
        while y < R - 1:
            if k[y, x] in 'sbk' and k[y - 1, x] == 'r':
                e = y
                while e < R and k[e, x] in 'sbk':
                    e += 1
                if e < R and k[e, x] == 'p' and e - y <= 2:
                    k[y:e, x] = 'p'
                y = e
            else:
                y += 1
    # Pruefung: 1-Kachel-Sandstufen zwischen Plateau und Felsfront (Wandknick auf dem Plateau) -> Plateau buendig
    for (yy0, yy1, x_) in ((6, 9, 32), (6, 7, 77), (6, 7, 78)):
        for y_ in range(yy0, yy1):
            if k[y_, x_] in 'sb':
                k[y_, x_] = 'p'
    k = zipfel_weg(k)
    h = np.zeros((R, C), int)
    h[k == 'r'] = 2
    h[np.isin(k, ['p', 'q'])] = 1
    # Nutzer: Bergkette auf dem Felsrand als Abgrenzung zum Plateau (Rand und Plateau liegen gleich hoch): Rand-Kacheln
    # bis 5 Kacheln vom Plateau, mind. 3 Kacheln vom Talboden entfernt (sonst doppelte Waende), Hoehe 3, Klasse 'm'
    def abstand(m):
        d = np.full((R, C), 99)
        d[m] = 0
        for i in range(1, 8):
            m2 = m.copy()
            m2[1:] |= m[:-1]; m2[:-1] |= m[1:]; m2[:, 1:] |= m[:, :-1]; m2[:, :-1] |= m[:, 1:]
            m2[1:, 1:] |= m[:-1, :-1]; m2[:-1, :-1] |= m[1:, 1:]; m2[1:, :-1] |= m[:-1, 1:]; m2[:-1, 1:] |= m[1:, :-1]
            d[m2 & (d == 99)] = i
            m = m2
        return d
    d_p = abstand(np.isin(k, ['p', 'q']))
    d_b = abstand(np.isin(k, ['s', 'b', 'k', 't', 'T']))
    kette = (k == 'r') & (d_p <= 5) & (d_b >= 4)
    for teil in flaechen(kette):                      # kleine Kettenstuecke weglassen
        if len(teil) < 12:
            for (y, x) in teil:
                kette[y, x] = False
    for _ in range(2):                                # 1-Kachel-Zacken der Kette glaetten
        nb = np.zeros((R, C), int)
        nb[1:] += kette[:-1]; nb[:-1] += kette[1:]; nb[:, 1:] += kette[:, :-1]; nb[:, :-1] += kette[:, 1:]
        kette = (kette & (nb >= 2)) | ((k == 'r') & (nb >= 3) & (d_b >= 4))
    k[kette] = 'm'
    h[kette] = 3
    lay = {'groesse': [C, R], 'klassen': [''.join(z) for z in k], 'hoehe': [''.join(str(c) for c in z) for z in h],
           'treppen': [[x0, x1, FRONT_REIHE] for (x0, x1) in TREPPEN],
           'teleporter': [{'x': tx, 'y': ty, 'b': b_, 'h': hh} for (tx, ty, b_, hh) in TELEPORTER]}
    json.dump(lay, open(os.path.join(KARTE, 'layout.json'), 'w'), indent=0)
    F = {'m': (150, 90, 50), 'r': (223, 150, 90), 'p': (240, 180, 120), 'q': (200, 160, 110), 's': (236, 216, 160), 'b': (190, 160, 110),
         'k': (140, 140, 140), 't': (120, 80, 40), 'T': (80, 220, 240)}
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
    print('Karte 42 Layout %dx%d' % (C, R))


if __name__ == '__main__':
    main()
