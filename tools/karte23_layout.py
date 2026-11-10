"""Karte 23 - Harvest Hills (A02), Layout nach der Vorlage -> maps/karte23/layout.json

  python3 tools/karte23_layout.py

Vorlage assets/vorlagen/karte23_vorlage.png: 1600x1280 px = 100x80 Kacheln a 16 px. Stil wie Karte 20 / 21.
Bauernland: Wald ringsum, Obstwiese oben links, Hof mit Scheune links, Felder (6 Beete) mit Hecken und
Maeuerchen in der Mitte, Teich mit Bach nach Sueden, Plateau oben in der Mitte (Erd-Felsfront, Treppe, Hoehle),
Terrassen oben rechts mit Steinmauer-Fronten und Treppen, Senke (Krater) unten rechts mit Felsrand, Teleporter
links und rechts unten.

Klassen:  h Wald  g Gras  w Weg  f Hofboden/Erde  a Acker  x Wasser  k Felsrand der Senke  c Senke (innen)
          m Steinmauer-Front (Terrassen)  n Maeuerchen  e Hecke  z Zaun  t Treppe  o Hoehle  T Teleporter
Hoehen:   1 Grundebene, 2 Plateau / mittlere Terrasse, 3 obere Terrasse, 0 Senke
"""
import json, os
from collections import deque
import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte23')
VORLAGE = os.path.join(ROOT, 'assets', 'vorlagen', 'karte23_vorlage.png')
C, R, T = 100, 80, 16
REF = {'h': (46, 101, 42), 'g': (108, 160, 67), 'G': (108, 156, 60), 'g2': (108, 168, 72), 'w': (200, 173, 117),
       'f': (170, 145, 97), 'a': (134, 94, 62), 'k': (143, 115, 77), 'm': (102, 101, 90), 'x': (50, 124, 172),
       'e': (60, 96, 36)}
FELDER = [(19, 45, 28, 52, 'moehren'), (34, 45, 43, 52, 'weizen'), (20, 58, 28, 64, 'kohl'),
          (34, 58, 41, 65, 'salat'), (19, 67, 27, 72, 'weizen'), (34, 68, 39, 72, 'leer')]
MAEUERCHEN = [(3, 28, 16, 28), (22, 28, 35, 28), (19, 42, 28, 42), (34, 42, 43, 42)]
HECKEN = [(19, 54, 28, 54), (34, 54, 43, 54), (19, 66, 28, 66), (34, 66, 41, 66), (43, 58, 43, 65), (18, 67, 18, 73)]
ZAUN = (11, 47, 17, 51)
PLATEAU_X = (37, 62)               # Plateau Mitte oben (Erd-Felsfront 2 Kacheln, Seiten schmal)
PLATEAU_TREPPE = (42, 45)
HOEHLE = (53, 54)
TERRASSE_MITTE = (71, 10, 97, 20)  # Terrassen oben rechts (Steinmauer-Fronten 2 Kacheln)
TERRASSE_OBEN = (75, 3, 97, 8)
TERRASSE_TREPPEN = [(82, 85, 8), (76, 79, 20), (90, 93, 20)]   # (x0, x1, letzte Reihe der hoeheren Ebene)
TELEPORTER = [(0, 37, 2, 4), (98, 71, 2, 3)]


def vorlage_klassen():
    a = np.array(Image.open(VORLAGE).convert('RGB')).astype(int)
    k = np.full((R, C), '?')
    for y in range(R):
        for x in range(C):
            m = np.median(a[y * T:(y + 1) * T, x * T:(x + 1) * T].reshape(-1, 3), 0)
            d = {c: np.abs(m - np.array(v)).sum() for c, v in REF.items()}
            c = min(d, key=d.get)
            k[y, x] = (c[0] if c not in ('G', 'g2') else 'g') if d[c] < 40 else '?'
    return k


def rand_verbunden(m):
    zu = np.zeros_like(m)
    zu[0, :] = m[0, :]; zu[-1, :] = m[-1, :]; zu[:, 0] = m[:, 0]; zu[:, -1] = m[:, -1]
    while True:
        n = zu | (m & (np.roll(zu, 1, 0) | np.roll(zu, -1, 0) | np.roll(zu, 1, 1) | np.roll(zu, -1, 1)))
        if (n == zu).all():
            return zu
        zu = n


def main():
    os.makedirs(KARTE, exist_ok=True)
    v = vorlage_klassen()
    k = np.full((R, C), 'g')
    h = np.ones((R, C), int)
    wald = rand_verbunden(v == 'h')
    k[wald] = 'h'
    k[(v == 'w') & ~wald] = 'w'
    k[(v == 'f') & ~wald] = 'f'
    # Wege der Terrassen oben rechts sind in der Vorlage braun -> Weg
    k[3:21, 71:98][v[3:21, 71:98] == 'f'] = 'w'
    k[(v == 'x')] = 'x'
    # ---- Plateau Mitte: je Spalte bis zur ersten Felszeile (Front) ab Reihe 20
    x0, x1 = PLATEAU_X
    plateau_unten = {}
    for x in range(x0, x1 + 1):
        ys = [y for y in range(20, 32) if v[y, x] in 'ka']
        yf = ys[0] if ys else 22
        plateau_unten[x] = yf - 1
        h[2:yf, x] = 2
        k[2:yf, x][k[2:yf, x] == 'h'] = 'g'
    for x in range(PLATEAU_TREPPE[0], PLATEAU_TREPPE[1] + 1):
        yf = plateau_unten[x] + 1
        k[yf:yf + 2, x] = 't'
        k[yf - 2:yf, x] = 'w'
        k[yf + 2:yf + 4, x] = 'w'
    for x in range(HOEHLE[0], HOEHLE[1] + 1):
        yf = plateau_unten[x] + 1
        k[yf:yf + 2, x] = 'o'
    # ---- Terrassen oben rechts
    a0, b0, a1, b1 = TERRASSE_MITTE
    h[3:b1 + 1, a0:a1 + 1] = 2
    a0, b0, a1, b1 = TERRASSE_OBEN
    h[b0:b1 + 1, a0:a1 + 1] = 3
    for (tx0, tx1, ye) in TERRASSE_TREPPEN:
        k[ye + 1:ye + 3, tx0:tx1 + 1] = 't'
        k[ye - 1:ye + 1, tx0:tx1 + 1] = 'w'
        k[ye + 3:ye + 5, tx0:tx1 + 1] = 'w'
    k[3:23, 69:99][k[3:23, 69:99] == 'h'] = 'g'
    # ---- Senke unten rechts: Felsrand aus der Vorlage, innen tiefer
    rand = (v == 'k') & (np.mgrid[0:R, 0:C][0] >= 48) & (np.mgrid[0:R, 0:C][1] >= 64)
    k[rand] = 'k'
    innen = np.zeros((R, C), bool)
    for y in range(48, 70):
        xs = np.nonzero(rand[y])[0]
        if len(xs) >= 2:
            innen[y, xs.min() + 1:xs.max()] = True
    innen &= ~rand
    k[innen] = 'c'
    h[innen | rand] = 0
    # ---- Felder, Maeuerchen, Hecken, Zaun
    for (fx0, fy0, fx1, fy1, _) in FELDER:
        k[fy0:fy1 + 1, fx0:fx1 + 1] = 'a'
    for (ax0, ay0, ax1, ay1) in MAEUERCHEN:
        k[ay0:ay1 + 1, ax0:ax1 + 1] = 'n'
    for (ax0, ay0, ax1, ay1) in HECKEN:
        k[ay0:ay1 + 1, ax0:ax1 + 1] = 'e'
    for (tx, ty, b, hh) in TELEPORTER:
        k[ty:ty + hh, tx:tx + b] = 'T'
    k[k == '?'] = 'g'
    lay = {'groesse': [C, R], 'klassen': [''.join(z) for z in k], 'hoehe': [''.join(str(c) for c in z) for z in h],
           'felder': FELDER, 'maeuerchen': MAEUERCHEN, 'hecken': HECKEN, 'zaun': ZAUN,
           'plateau': {'x': PLATEAU_X, 'unten': plateau_unten, 'treppe': PLATEAU_TREPPE, 'hoehle': HOEHLE},
           'terrassen': {'mitte': TERRASSE_MITTE, 'oben': TERRASSE_OBEN, 'treppen': TERRASSE_TREPPEN},
           'teleporter': [{'x': tx, 'y': ty, 'b': b, 'h': hh} for (tx, ty, b, hh) in TELEPORTER]}
    json.dump(lay, open(os.path.join(KARTE, 'layout.json'), 'w'), indent=0)
    F = {'h': (30, 80, 30), 'g': (84, 132, 60), 'w': (192, 168, 108), 'f': (150, 110, 70), 'a': (100, 60, 30),
         'x': (48, 132, 200), 'k': (200, 100, 40), 'c': (210, 180, 120), 'm': (130, 130, 140), 'n': (170, 170, 180),
         'e': (20, 50, 20), 'z': (140, 90, 40), 't': (230, 230, 230), 'o': (10, 10, 20), 'T': (80, 220, 240)}
    S = 6
    im = Image.new('RGB', (C * S, R * S))
    dr = ImageDraw.Draw(im)
    for y in range(R):
        for x in range(C):
            c = np.array(F[k[y, x]], float) * (0.8 + 0.12 * h[y, x])
            dr.rectangle((x * S, y * S, x * S + S - 1, y * S + S - 1), fill=tuple(np.clip(c, 0, 255).astype(int)))
    vg = Image.open(VORLAGE).convert('RGB').resize((C * S, R * S))
    both = Image.new('RGB', (C * S * 2 + 8, R * S))
    both.paste(vg, (0, 0)); both.paste(im, (C * S + 8, 0))
    both.save(os.path.join(KARTE, 'layout_vergleich.png'))
    print('Karte 23 Layout %dx%d' % (C, R))


if __name__ == '__main__':
    main()
