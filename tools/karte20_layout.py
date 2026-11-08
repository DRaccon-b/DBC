"""Karte 20 - Startkarte von A02 (Dorf am Fluss), Layout nach der Vorlage -> maps/karte20/layout.json

  python3 tools/karte20_layout.py

Vorlage assets/vorlagen/karte20_vorlage.png: 960x768 px = 60x48 Kacheln a 16 px. Stil wie Karte 06 (Primary Village):
Wald ringsum, Sandwege, Kopfsteinplatz, Fluss, Felder, Holzzaeune.
Wald, Wege und Fluss werden Kachel fuer Kachel aus der Vorlage gelesen (Medianfarbe), alles andere von Hand.

Klassen:  h Wald   g Gras   w Weg (Sand)   p Kopfsteinplatz   r Rasen auf dem Platz   x Wasser (Fluss)
          b Bruecke (ueber Wasser)   a Acker (Beete)   f Feld (Erde, unten links)   o Plateau (erhoeht, Gras)
          t Treppe   e Teleporter/Ausgang
Hoehen:   1 Boden, 2 Plateau oben rechts.
"""
import json, os
import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte20')
VORLAGE = os.path.join(ROOT, 'assets', 'vorlagen', 'karte20_vorlage.png')
C, R, T = 60, 48, 16
REF = {'h': (36, 96, 36), 'g': (84, 132, 60), 'G': (108, 156, 60), 'w': (192, 168, 108), 'p': (120, 132, 144),
       'x': (48, 120, 168), 'a': (132, 84, 60), 'f': (168, 144, 84)}

PLATZ = (19, 14, 36, 29)                 # Kopfsteinplatz (Ecken gerundet)
PLATZ_RASEN = (23, 18, 31, 23)           # Rasen in der Mitte (mit Brunnen)
ACKER_ZAUN = (40, 15, 54, 28)            # Zaun um die Beete rechts (Tor unten bei x 47)
BEETE = [(42, 16, 52, 19), (42, 22, 46, 26), (48, 22, 52, 26)]
FELD_ZAUN = (5, 35, 22, 45)              # Zaun um das Feld unten links (Tor oben rechts bei x 18..21)
FELD = (6, 36, 21, 44)
PLATEAU = (43, 2, 56, 9)                 # erhoeht, Front Reihen 10-11
TREPPE = (49, 51)                        # Spalten der Treppe in der Front
BRUECKEN = [(14, 18, 18, 20), (14, 23, 18, 25)]
AUSGAENGE = [(28, 46, 31, 47), (58, 37, 59, 39)]   # unten Mitte, rechts
# Fluss (von Hand, nach der Vorlage): Quellteich oben, dann nach Sueden, unten nach Westen aus der Karte
FLUSS = [(12.0, 4.5), (14.0, 6.0), (16.0, 8.5), (16.0, 14.0), (16.0, 20.0), (16.0, 26.0), (15.5, 29.0),
         (13.0, 30.8), (9.5, 32.2), (5.5, 33.6), (1.5, 34.6), (-1.0, 35.0)]
FLUSS_BREITE = 1.45                       # Radius in Kacheln (ca. 3 Kacheln breit)
TEICH = (12.0, 4.6, 3.4, 1.9)             # Quellteich (Ellipse)


def vorlage_klassen():
    a = np.array(Image.open(VORLAGE).convert('RGB')).astype(int)
    k = np.full((R, C), 'g')
    for y in range(R):
        for x in range(C):
            m = np.median(a[y * T:(y + 1) * T, x * T:(x + 1) * T].reshape(-1, 3), 0)
            d = {c: np.abs(m - np.array(v)).sum() for c, v in REF.items()}
            c = min(d, key=d.get)
            k[y, x] = c if d[c] < 70 else '?'
    return k


def main():
    os.makedirs(KARTE, exist_ok=True)
    v = vorlage_klassen()
    k = np.full((R, C), 'g')
    # Wald: nur die mit dem Kartenrand verbundenen dunklen Kacheln (Baeume im Dorf sind Objekte)
    wald = (v == 'h')
    rand = np.zeros_like(wald)
    rand[0, :] = rand[-1, :] = rand[:, 0] = rand[:, -1] = True
    zu = wald & rand
    while True:
        n = zu | (wald & (np.roll(zu, 1, 0) | np.roll(zu, -1, 0) | np.roll(zu, 1, 1) | np.roll(zu, -1, 1)))
        if (n == zu).all():
            break
        zu = n
    k[zu] = 'h'
    k[v == 'w'] = 'w'
    # einzelne Weg-Flecken aus der Vorlage (Objektschatten, Steine) entfernen: Weg-Inseln unter 6 Kacheln
    from collections import deque
    gesehen = np.zeros((R, C), bool)
    for y in range(R):
        for x in range(C):
            if k[y, x] == 'w' and not gesehen[y, x]:
                q, teil = deque([(y, x)]), []
                gesehen[y, x] = True
                while q:
                    a_, b_ = q.popleft(); teil.append((a_, b_))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        u, w_ = a_ + dy, b_ + dx
                        if 0 <= u < R and 0 <= w_ < C and k[u, w_] == 'w' and not gesehen[u, w_]:
                            gesehen[u, w_] = True; q.append((u, w_))
                if len(teil) < 6:
                    for (a_, b_) in teil:
                        k[a_, b_] = 'g'
    yy, xx = np.mgrid[0:R, 0:C]
    fl = np.zeros((R, C), bool)
    for (ax, ay), (bx, by) in zip(FLUSS, FLUSS[1:]):
        for t in np.linspace(0, 1, 40):
            px, py = ax + (bx - ax) * t, ay + (by - ay) * t
            fl |= np.hypot(xx + 0.5 - px, yy + 0.5 - py) <= FLUSS_BREITE
    cx, cy, rx, ry = TEICH
    fl |= ((xx + 0.5 - cx) / rx) ** 2 + ((yy + 0.5 - cy) / ry) ** 2 <= 1
    k[fl & (k != 'h') | (fl & (xx < 3))] = 'x'
    # Platz mit gerundeten Ecken und Rasen in der Mitte
    x0, y0, x1, y1 = PLATZ
    m = (xx >= x0) & (xx <= x1) & (yy >= y0) & (yy <= y1)
    for (cx, cy) in ((x0, y0), (x1, y0), (x0, y1), (x1, y1)):
        m[cy, cx] = False
    k[m] = 'p'
    x0, y0, x1, y1 = PLATZ_RASEN
    rm = (xx >= x0) & (xx <= x1) & (yy >= y0) & (yy <= y1)
    for (cx, cy) in ((x0, y0), (x1, y0), (x0, y1), (x1, y1)):
        rm[cy, cx] = False
    k[rm] = 'r'
    # Felder
    for (x0, y0, x1, y1) in BEETE:
        k[y0:y1 + 1, x0:x1 + 1] = 'a'
    x0, y0, x1, y1 = FELD
    k[y0:y1 + 1, x0:x1 + 1] = 'f'
    # Plateau oben rechts mit Front und Treppe
    x0, y0, x1, y1 = PLATEAU
    pl = (xx >= x0) & (xx <= x1) & (yy >= y0 + 1) & (yy <= y1)
    k[pl & (k == 'h')] = 'o'                                   # Plateau oben bis an den Wald, ohne Einkerbungen
    k[y0, x0:x1 + 1] = 'h'
    k[pl & (k != 'w')] = 'o'
    k[10:12, TREPPE[0]:TREPPE[1] + 1] = 't'
    # Bruecken, Ausgaenge
    for (x0, y0, x1, y1) in BRUECKEN:
        bm = (xx >= x0) & (xx <= x1) & (yy >= y0) & (yy <= y1)
        k[bm & (k == 'x')] = 'b'
        k[bm & (k != 'b') & (k != 'h')] = 'w'
    for (x0, y0, x1, y1) in AUSGAENGE:
        k[y0:y1 + 1, x0:x1 + 1] = 'e'
    # Reste aus der Vorlage (Objektflecken) -> Gras
    k[k == '?'] = 'g'
    h = np.where(np.isin(k, ['o']) | ((k == 'w') & pl), 2, 1)
    lay = {'groesse': [C, R], 'klassen': [''.join(z) for z in k], 'hoehe': [''.join(str(c) for c in z) for z in h],
           'platz': PLATZ, 'platz_rasen': PLATZ_RASEN, 'acker_zaun': ACKER_ZAUN, 'beete': BEETE,
           'feld_zaun': FELD_ZAUN, 'plateau': PLATEAU, 'treppe': TREPPE, 'bruecken': BRUECKEN,
           'teleporter': [{'x': 28, 'y': 46, 'b': 4, 'h': 2}, {'x': 58, 'y': 37, 'b': 2, 'h': 3}]}
    json.dump(lay, open(os.path.join(KARTE, 'layout.json'), 'w'), indent=0)
    F = {'h': (30, 80, 30), 'g': (84, 132, 60), 'w': (192, 168, 108), 'p': (120, 132, 144), 'r': (108, 156, 60),
         'x': (48, 120, 168), 'b': (150, 100, 60), 'a': (110, 70, 50), 'f': (170, 140, 90), 'o': (120, 170, 70),
         't': (200, 200, 200), 'e': (80, 220, 240)}
    im = Image.new('RGB', (C * 8, R * 8))
    dr = ImageDraw.Draw(im)
    for y in range(R):
        for x in range(C):
            dr.rectangle((x * 8, y * 8, x * 8 + 7, y * 8 + 7), fill=F[k[y, x]], outline=(0, 0, 0))
    vg = Image.open(VORLAGE).convert('RGB').resize((C * 8, R * 8))
    both = Image.new('RGB', (C * 16 + 8, R * 8))
    both.paste(vg, (0, 0)); both.paste(im, (C * 8 + 8, 0))
    both.save(os.path.join(KARTE, 'layout_vergleich.png'))
    print('Karte 20 Layout %dx%d' % (C, R))


if __name__ == '__main__':
    main()
