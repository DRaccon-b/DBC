"""Karte 41 - Digital World: Wind Desert (A03 Nr. 8), Layout nach der Vorlage -> maps/karte41/layout.json

  python3 tools/karte41_layout.py

Vorlage assets/vorlagen/karte41_vorlage.png: 1536x1280 px = 96x80 Kacheln (1:1). Windwueste: weite Sandflaeche in drei
Toenen (heller Sand, breite Windbahnen aus mittlerem Sand, dunkle Erdflecken mit Steinen), ringsum und in der Mitte
erhoehte orange Plateaus (Hochflaeche, nicht begehbar) mit Felsfronten nach Sueden, Oase mit Teich und Gras unten links,
graue Pflasterflecken (Ruinen), fuenf Ausgaenge an den Raendern (oben 2, links 2, rechts 1).

Klassen:  r Plateau (hoch)  s heller Sand  b Windbahn (mittlerer Sand)  d dunkle Erde  k Pflaster
          n Gras (Oase)  x Teich  T Teleporter (Ausgang)
Hoehen:   0 Wuestenboden, 2 Plateau
"""
import json, os
from collections import deque
import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte41')
VORLAGE = os.path.join(ROOT, 'assets', 'vorlagen', 'karte41_vorlage.png')
C, R, T = 96, 80, 16
REF = {'r': (223, 176, 114), 's': (230, 210, 151), 'b': (200, 173, 118), 'd': (183, 154, 105),
       'k': (155, 148, 124), 'n': (88, 140, 62), 'x': (50, 124, 172), 'f': (142, 99, 64)}
# Ausgaenge (x, y, b, h) in Kacheln: 3 Kacheln tief am Rand, auf Bodenhoehe (Fels/Front daneben bleibt)
TELEPORTER = [(22, 0, 4, 3), (40, 0, 4, 3), (0, 38, 3, 4), (0, 58, 3, 4), (93, 66, 3, 4)]


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


def zipfel_weg(k):
    """Zipfel/Kerben (Pruefung K41): Kachel mit <= 1 gleichen Nachbarn -> haeufigster Nachbar; Kleinflecken < 6."""
    for _ in range(6):                                # Zipfel/Kerben (Pruefung): Kachel mit <= 1 gleichen Nachbarn
        geaendert = False                             # -> haeufigster Nachbar (wird sonst zum runden Punkt)
        for y in range(R):
            for x in range(C):
                if k[y, x] == 'r':
                    continue
                nb = [k[yy, xx] for yy, xx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1))
                      if 0 <= yy < R and 0 <= xx < C]
                if nb.count(k[y, x]) <= 1:
                    fremd = [c for c in nb if c != k[y, x] and c != 'r']
                    if fremd:
                        k[y, x] = max(set(fremd), key=fremd.count); geaendert = True
        for art in 'bsdkn':
            for teil in flaechen(k == art):
                if len(teil) < 6:
                    for (y, x) in teil:
                        nb = [k[yy, xx] for yy, xx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1))
                              if 0 <= yy < R and 0 <= xx < C and k[yy, xx] not in (art, 'r')]
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
    ref = np.array([REF[k] for k in ks], float)
    k = np.array(ks)[((M[:, :, None, :] - ref[None, None]) ** 2).sum(-1).argmin(-1)]
    # Felsfront der Vorlage ('f') liegt unter der Plateaukante auf Bodenhoehe: dort zeichnet bauen() die Front
    k[k == 'f'] = 'b'
    r_ = k == 'r'                                     # Felsfront-Pixel unter der Plateaukante sind kein Pflaster
    nah = r_.copy()
    for d in (1, 2, 3):
        nah[d:] |= r_[:-d]
    nah[:, 1:] |= nah[:, :-1].copy(); nah[:, :-1] |= nah[:, 1:].copy()
    k[(k == 'k') & nah] = 'b'
    k[0] = 'r'                                        # oberste Reihe: Plateau (darunter zeichnet bauen() die Front)
    unter = np.zeros_like(r_)
    r_ = k == 'r'
    for d in (1, 2):
        unter[d:] |= r_[:-d]
    k[(k == 'd') & unter] = 'b'                       # dunkle Frontpixel direkt unter der Kante -> Boden
    for teil in flaechen(k == 'r'):                   # kleine orange Flecken (Objekte) -> Boden
        if len(teil) < 20:
            for (y, x) in teil:
                k[y, x] = 'b'
    for art, mind in (('k', 4), ('d', 4), ('b', 3), ('s', 3), ('n', 4), ('x', 6)):   # Kleinflecken -> Nachbarn
        for teil in flaechen(k == art):
            if len(teil) < mind:
                for (y, x) in teil:
                    nb = [k[yy, xx] for yy, xx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1))
                          if 0 <= yy < R and 0 <= xx < C and k[yy, xx] != art]
                    k[y, x] = max(set(nb), key=nb.count) if nb else 'b'
    k = zipfel_weg(k)
    for teil in flaechen(k != 'r'):                   # Bodenloecher im Plateau -> Plateau
        if len(teil) < 16:
            for (y, x) in teil:
                k[y, x] = 'r'
    for _ in range(2):                                # 1 Kachel breite Schlitze/Finger glaetten (45-Grad-Raster)
        for y in range(1, R - 1):
            for x in range(1, C - 1):
                nb = [k[y - 1, x], k[y + 1, x], k[y, x - 1], k[y, x + 1]]
                if k[y, x] != 'r' and nb.count('r') >= 3:
                    k[y, x] = 'r'
                elif k[y, x] == 'r' and nb.count('r') <= 1:
                    k[y, x] = 'b'
    k = zipfel_weg(k)
    # Teich und Gras: Gras ringsum um das Wasser (mind. 1 Kachel), kein Wasser direkt am Sand
    x_ = k == 'x'
    um = x_.copy()
    um[1:] |= x_[:-1]; um[:-1] |= x_[1:]; um[:, 1:] |= x_[:, :-1]; um[:, :-1] |= x_[:, 1:]
    for _ in range(1):                                # Grasring 2 Kacheln breit (kein 1-Kachel-Grat am Ufer)
        um2 = um.copy()
        um2[1:] |= um[:-1]; um2[:-1] |= um[1:]; um2[:, 1:] |= um[:, :-1]; um2[:, :-1] |= um[:, 1:]
        um = um2
    k[um & ~x_ & (k != 'r')] = 'n'
    for _ in range(3):                                # Wasser-/Graszipfel und -kerben angleichen
        for y in range(1, R - 1):
            for x in range(1, C - 1):
                nb = [k[y - 1, x], k[y + 1, x], k[y, x - 1], k[y, x + 1]]
                if k[y, x] == 'x' and nb.count('x') <= 1:
                    k[y, x] = 'n'
                elif k[y, x] == 'n' and nb.count('x') >= 3:
                    k[y, x] = 'x'
                elif k[y, x] in 'sbdk' and nb.count('n') >= 3:
                    k[y, x] = 'n'
    h = np.where(k == 'r', 2, 0)
    for (tx, ty, b, hh) in TELEPORTER:                # Ausgang: Boden bis an den Rand, Teleporter darauf
        k[ty:ty + hh, tx:tx + b] = 'T'; h[ty:ty + hh, tx:tx + b] = 0
        for y in range(max(0, ty - 2), ty):           # Platz fuer die Felsfront ueber dem Ausgang (Front nie auf dem Teleporter)
            for x in range(tx, tx + b):
                if k[y, x] == 'r':
                    k[y, x] = 'b'; h[y, x] = 0
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    lay = {'groesse': [C, R], 'klassen': [''.join(z) for z in k], 'hoehe': [''.join(str(c) for c in z) for z in h],
           'teleporter': [{'x': tx, 'y': ty, 'b': b, 'h': hh} for (tx, ty, b, hh) in TELEPORTER]}
    json.dump(lay, open(os.path.join(KARTE, 'layout.json'), 'w'), indent=0)
    F = {'r': (223, 150, 90), 's': (236, 216, 160), 'b': (196, 168, 112), 'd': (150, 120, 80), 'k': (140, 140, 140),
         'n': (80, 150, 60), 'x': (40, 110, 200), 'T': (80, 220, 240)}
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
    print('Karte 41 Layout %dx%d' % (C, R))


if __name__ == '__main__':
    main()
