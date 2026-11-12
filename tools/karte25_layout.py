"""Karte 25 - Sunset Bay (A02), Layout nach der Vorlage -> maps/karte25/layout.json

  python3 tools/karte25_layout.py

Vorlage assets/vorlagen/karte25_vorlage.png: 1920x1280 px = 120x80 Kacheln a 16 px. Vorgehen wie Karte 23 / 24.
Kuestenkarte: Grasplateau oben links mit Felsfront, zwei Treppen und Weg, Leuchtturm; darunter breiter Sandstrand
mit Huetten, Palmen, Fackeln, Booten; flaches tuerkises Wasser mit Sandbaenken, tiefes Meer aussen; Lagune oben
rechts mit Steg und tiefer Mitte; Hafenkante rechts (nasser Sand) mit Anleger zum Schiff; Steg nach Sueden unten links.

Klassen:  x tiefes Meer  f flaches Wasser  s Sand  n nasser Sand (Hafenkante)  g Gras  w Weg (Plateau)
          t Treppe  p Steg (Holz)  S Schiff  T Teleporter
Hoehen:   0 Wasser  1 Strand  2 Grasplateau
"""
import json, os
import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte25')
VORLAGE = os.path.join(ROOT, 'assets', 'vorlagen', 'karte25_vorlage.png')
C, R, T = 120, 80, 16
REF = {'x': (48, 88, 136), 'f': (62, 170, 158), 's': (230, 218, 160), 'g': (84, 134, 62), 'g2': (62, 146, 50),
       'w': (184, 160, 100), 'w2': (194, 170, 110), 'k': (150, 132, 96), 'p': (122, 74, 38), 'S': (36, 36, 48)}
TREPPEN = [(10, 13, 21), (42, 45, 21)]          # (x0, x1, letzte Reihe des Plateaus) - Treppen unter den Wegen
STEGE = [(14, 46, 16, 64), (17, 58, 19, 59), (74, 3, 75, 10), (89, 17, 93, 18)]   # (x0, y0, x1, y1)
TELEPORTER = [(0, 31, 2, 4), (87, 17, 2, 2)]
SCHIFF = (89, 10, 119, 28)                     # Rechteck des Schiffs (Objekt, liegt im tiefen Wasser)


def vorlage_klassen():
    a = np.array(Image.open(VORLAGE).convert('RGB')).astype(int)
    k = np.full((R, C), '?')
    for y in range(R):
        for x in range(C):
            m = np.median(a[y * T:(y + 1) * T, x * T:(x + 1) * T].reshape(-1, 3), 0)
            d = {c: np.abs(m - np.array(v)).sum() for c, v in REF.items()}
            c = min(d, key=d.get)
            k[y, x] = c[0] if d[c] < 60 else '?'
    return k


def main():
    os.makedirs(KARTE, exist_ok=True)
    v = vorlage_klassen()
    k = v.copy()
    h = np.ones((R, C), int)
    # unbekannte Kacheln (Objekte) aus den Nachbarn fuellen
    for _ in range(4):
        for y in range(R):
            for x in range(C):
                if k[y, x] in '?S':
                    nb = [k[yy, xx] for yy, xx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1))
                          if 0 <= yy < R and 0 <= xx < C and k[yy, xx] not in '?S']
                    if nb:
                        k[y, x] = max(set(nb), key=nb.count)
    k[k == '?'] = 'x'
    # Holz/dunkler Sand mitten im Strand oder auf dem Gras sind Objekte (Huetten, Palmen, Leuchtturm, Boote)
    steg = np.zeros((R, C), bool)
    for (sx0, sy0, sx1, sy1) in STEGE:
        steg[sy0:sy1 + 1, sx0:sx1 + 1] = True
    wasser = np.isin(k, list('xf'))
    nah_w = wasser.copy()
    for _ in range(2):
        nah_w = nah_w | np.roll(nah_w, 1, 0) | np.roll(nah_w, -1, 0) | np.roll(nah_w, 1, 1) | np.roll(nah_w, -1, 1)
    fremd = ((k == 'p') & ~steg) | ((k == 'k') & ~(np.arange(R)[:, None] < 50)) | ((k == 'w') & ~nah_w & (np.arange(R)[:, None] >= 24))
    for _ in range(6):
        for y, x in zip(*np.nonzero(fremd)):
            nb = [k[yy, xx] for yy, xx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1))
                  if 0 <= yy < R and 0 <= xx < C and not fremd[yy, xx]]
            if nb:
                k[y, x] = max(set(nb), key=nb.count); fremd[y, x] = False
    # Schiff liegt im tiefen Meer
    x0, y0, x1, y1 = SCHIFF
    k[y0:y1 + 1, x0:x1 + 1][np.isin(k[y0:y1 + 1, x0:x1 + 1], list('sfwkpS'))] = 'x'
    # Plateau: Gras + Weg auf Gras; die Felsfront der Vorlage wird Strand (die Front zeichnet bauen darunter)
    # schmaler Sandstreifen oben (Leuchtturm der Vorlage, Nutzer): wird Berg/Gras
    st = k[3:12, 50:56]
    st[np.isin(st, list('sw'))] = 'g'
    gras = (k == 'g')
    gras &= ~((np.arange(R)[:, None] > 30) & (np.arange(C)[None, :] > 8))   # einzelne Palmblaetter auf dem Strand
    plateau = gras.copy()
    for _ in range(3):                                            # Wege, die vom Gras umschlossen sind
        nb = np.roll(plateau, 1, 0) | np.roll(plateau, -1, 0) | np.roll(plateau, 1, 1) | np.roll(plateau, -1, 1)
        plateau |= (k == 'w') & nb & (np.arange(R)[:, None] < 22)
    from collections import deque                                 # Loecher im Plateau (Sandplatz am Leuchtturm) fuellen
    aussen = np.zeros((R, C), bool)
    q = deque((y, x) for y in range(R) for x in range(C)
              if (y in (0, R - 1) or x in (0, C - 1)) and not plateau[y, x])
    for y, x in q:
        aussen[y, x] = True
    while q:
        y, x = q.popleft()
        for yy, xx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
            if 0 <= yy < R and 0 <= xx < C and not aussen[yy, xx] and not plateau[yy, xx]:
                aussen[yy, xx] = True; q.append((yy, xx))
    plateau |= ~aussen
    h[plateau] = 2
    k[(k == 'w') & ~plateau] = 'n'                                # dunkler Sand am Meer = nasser Sand / Hafenkante
    k[k == 'k'] = 's'
    k[(k == 'g') & ~plateau] = 's'
    k[plateau & (k == 'p')] = 'w'
    h[np.isin(k, list('xf'))] = 0
    for (tx0, tx1, ye) in TREPPEN:
        h[:ye + 1, tx0:tx1 + 1][k[:ye + 1, tx0:tx1 + 1] != 'x'] = 2
        k[ye - 1:ye + 1, tx0:tx1 + 1] = 'w'
        k[ye + 1:ye + 3, tx0:tx1 + 1] = 't'
    for (sx0, sy0, sx1, sy1) in STEGE:
        k[sy0:sy1 + 1, sx0:sx1 + 1] = 'p'
    for (tx, ty, b, hh) in TELEPORTER:
        k[ty:ty + hh, tx:tx + b] = 'T'
        h[ty:ty + hh, tx:tx + b] = 1
    import regeln_a02                                                 # Regel 6: Wege nie nur gerade
    k = regeln_a02.wege_schwingen(k, seed=25)
    lay = {'groesse': [C, R], 'klassen': [''.join(z) for z in k], 'hoehe': [''.join(str(c) for c in z) for z in h],
           'treppen': TREPPEN, 'stege': STEGE, 'schiff': SCHIFF,
           'teleporter': [{'x': tx, 'y': ty, 'b': b, 'h': hh} for (tx, ty, b, hh) in TELEPORTER]}
    json.dump(lay, open(os.path.join(KARTE, 'layout.json'), 'w'), indent=0)
    F = {'x': (40, 80, 140), 'f': (60, 170, 160), 's': (232, 216, 150), 'n': (180, 150, 96), 'g': (84, 140, 60),
         'w': (200, 170, 110), 't': (240, 240, 240), 'p': (130, 80, 40), 'S': (30, 30, 40), 'T': (190, 80, 240)}
    S = 6
    im = Image.new('RGB', (C * S, R * S))
    dr = ImageDraw.Draw(im)
    for y in range(R):
        for x in range(C):
            c = np.array(F[k[y, x]], float) * (0.85 + 0.1 * h[y, x])
            dr.rectangle((x * S, y * S, x * S + S - 1, y * S + S - 1), fill=tuple(np.clip(c, 0, 255).astype(int)))
    x0, y0, x1, y1 = SCHIFF
    dr.rectangle((x0 * S, y0 * S, (x1 + 1) * S - 1, (y1 + 1) * S - 1), outline=(255, 60, 60))
    vg = Image.open(VORLAGE).convert('RGB').resize((C * S, R * S))
    both = Image.new('RGB', (C * S * 2 + 8, R * S))
    both.paste(vg, (0, 0)); both.paste(im, (C * S + 8, 0))
    both.save(os.path.join(KARTE, 'layout_vergleich.png'))
    print('Karte 25 Layout %dx%d' % (C, R))


if __name__ == '__main__':
    main()
