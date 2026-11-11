"""Karte 28 - Tower Forest (A02), Layout nach der Vorlage -> maps/karte28/layout.json

  python3 tools/karte28_layout.py

Vorlage assets/vorlagen/karte28_vorlage.png: 1600x1360 px = 100x85 Kacheln. Vorgehen wie Karte 23 / 27.
Dichter Wald ringsum, links eine Schlamm-Arena (Hochflaeche mit Front und zwei Treppen im Sueden, im Norden
Steinwaende zum hoeheren Wald), rechts ein grauer Steinplatz mit Erdflecken (Spinnweben-Ring, Tuerme mit Draht),
Wiesen mit Feldwegen, Lagerfeuer, Ausgaenge oben rechts und unten Mitte.

Klassen:  h Wald  g Gras  w Feldweg  f Schlamm (Arena)  e Erde  k Steinboden  m Steinwand (Arena-Nordrand)
          t Treppe  T Ausgang
Hoehen:   2 = Arena: ERHOEHUNG (Nutzer, nur eine Ebene) - Wald dahinter gleich hoch, Suedfront mit Treppen hinauf
"""
import json, os
from collections import deque
import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte28')
VORLAGE = os.path.join(ROOT, 'assets', 'vorlagen', 'karte28_vorlage.png')
C, R, T = 100, 85, 16
REF = {'h': (40, 104, 40), 'h2': (24, 96, 32), 'g': (80, 136, 56), 'k': (80, 82, 98), 'f': (58, 56, 48),
       'w': (200, 168, 112), 'e': (96, 72, 48), 'm': (72, 80, 64), 'W': (150, 200, 230)}
TREPPEN = [(14, 41, 3, 2), (33, 41, 3, 2)]                        # (x, y, b, h) Kacheln, Arena-Sued nach der Vorlage
AUSGAENGE = [(98, 3, 2, 4), (44, 83, 6, 2)]
FRONT_REIHEN = 3


def klassen():
    a = np.array(Image.open(VORLAGE).convert('RGB')).astype(int)
    k = np.full((R, C), '?')
    for y in range(R):
        for x in range(C):
            m = np.median(a[y * T:(y + 1) * T, x * T:(x + 1) * T].reshape(-1, 3), 0)
            d = {c: np.abs(m - np.array(v)).sum() for c, v in REF.items()}
            c = min(d, key=d.get)
            k[y, x] = c[0] if d[c] < 60 else '?'
    return k


def komponenten(k, cl):
    gesehen = np.zeros(k.shape, bool)
    for y in range(R):
        for x in range(C):
            if k[y, x] == cl and not gesehen[y, x]:
                comp, q = [], deque([(y, x)]); gesehen[y, x] = True
                while q:
                    cy, cx = q.popleft(); comp.append((cy, cx))
                    for yy, xx in ((cy - 1, cx), (cy + 1, cx), (cy, cx - 1), (cy, cx + 1)):
                        if 0 <= yy < R and 0 <= xx < C and k[yy, xx] == cl and not gesehen[yy, xx]:
                            gesehen[yy, xx] = True; q.append((yy, xx))
                yield comp


def main():
    os.makedirs(KARTE, exist_ok=True)
    k = klassen()
    for _ in range(4):                                               # unklare Kacheln (Objekte) aus den Nachbarn
        for y in range(R):
            for x in range(C):
                if k[y, x] == '?':
                    nb = [k[yy, xx] for yy, xx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1))
                          if 0 <= yy < R and 0 <= xx < C and k[yy, xx] != '?']
                    if nb:
                        k[y, x] = max(set(nb), key=nb.count)
    k[k == '?'] = 'g'
    for cl in 'ekf':                                                 # Obelisk-Fuesse u. a. Objekte: kleine Flecken -> Umgebung
        for comp in list(komponenten(k, cl)):
            if len(comp) <= 4:
                nb = [k[yy, xx] for cy, cx in comp for yy, xx in ((cy - 1, cx), (cy + 1, cx), (cy, cx - 1), (cy, cx + 1))
                      if 0 <= yy < R and 0 <= xx < C and k[yy, xx] != cl]
                if nb:
                    for cy, cx in comp:
                        k[cy, cx] = max(set(nb), key=nb.count)
    for comp in list(komponenten(k, 'h')):                          # einzelne Baeume der Vorlage sind kein Wald
        if len(comp) < 12:
            for cy, cx in comp:
                k[cy, cx] = 'g'
    # Arena links: Schlamm 'f' (Erdflecken in der Arena bleiben 'e'), Hoehe 2
    h = np.ones((R, C), int)
    arena = np.zeros((R, C), bool)
    for comp in komponenten(k, 'f'):
        if len(comp) > 200:
            for cy, cx in comp:
                arena[cy, cx] = True
    ys, xs = np.nonzero(arena)
    ax0, ax1, ay0, ay1 = xs.min(), xs.max(), ys.min(), ys.max()
    for y in range(ay0, ay1 + 1):                                    # Loecher (Erdflecken, Objekte) fuellen
        reihe = np.nonzero(arena[y])[0]
        if len(reihe):
            for x in range(reihe.min(), reihe.max() + 1):
                if k[y, x] in 'feg?':
                    arena[y, x] = True
    h[arena] = 2
    k[arena & np.isin(k, list('gk'))] = 'f'
    # Nordrand: Steinwaende = Front des hoeheren Waldes (Hoehe 3); je Spalte ab der obersten Wandkachel 3 Reihen Front
    for x in range(max(0, ax0 - 2), min(C, ax1 + 3)):
        ms = [y for y in range(max(0, ay0 - 4), ay0 + 10) if k[y, x] == 'm']
        if not ms:
            continue
        ym = min(ms)
        h[:ym, x] = np.where(k[:ym, x] == 'h', 3, h[:ym, x])
        for y in range(ym, min(R, ym + FRONT_REIHEN)):
            k[y, x] = 'm'
            h[y, x] = 2
    for y in range(R):                                               # restliche Wandkacheln (Seiten, Reste) -> Arena / Gras
        for x in range(C):
            if k[y, x] == 'm' and not (y > 0 and (k[y - 1, x] == 'm' or h[y - 1, x] == 3)):
                k[y, x] = 'f' if arena[y, x] else 'g'
    for x in range(C):                                               # Wand nur direkt unter dem hohen Wald (zusammenhaengend)
        y = 0
        while y < R:
            if k[y, x] == 'm' and (y == 0 or (k[y - 1, x] != 'm' and h[y - 1, x] != 3)):
                k[y, x] = 'f' if arena[y, x] else 'g'
            y += 1
    k[(k == 'm') & ~((h == 2) | (h == 3))] = 'g'
    for y in range(max(0, ay0 - 4), ay1 + 1):                        # Arena zeilenweise geschlossen (Randluecken fuellen)
        xs_ = [x for x in range(max(0, ax0 - 1), min(C, ax1 + 2)) if k[y, x] in 'fekm' and h[y, x] != 3]
        if not xs_:
            continue
        for x in range(min(xs_), max(xs_) + 1):
            if h[y, x] != 3:
                h[y, x] = 2
                if k[y, x] in 'gkh':
                    k[y, x] = 'f'
    for (tx, ty, b, hh) in TREPPEN:
        k[ty:ty + hh, tx:tx + b] = 't'
    for (tx, ty, b, hh) in AUSGAENGE:
        k[ty:ty + hh, tx:tx + b] = 'T'
    lay = {'groesse': [C, R], 'klassen': [''.join(z) for z in k], 'hoehe': [''.join(str(c) for c in z) for z in h],
           'arena': [int(ax0), int(ay0), int(ax1), int(ay1)],
           'treppen': [{'x': tx, 'y': ty, 'b': b, 'h': hh} for (tx, ty, b, hh) in TREPPEN],
           'ausgaenge': [{'x': tx, 'y': ty, 'b': b, 'h': hh} for (tx, ty, b, hh) in AUSGAENGE]}
    json.dump(lay, open(os.path.join(KARTE, 'layout.json'), 'w'), indent=0)
    F = {'h': (30, 80, 30), 'g': (84, 136, 62), 'f': (70, 60, 48), 'e': (130, 90, 50), 'k': (110, 112, 128),
         'w': (200, 170, 110), 'm': (90, 96, 84), 't': (220, 220, 220), 'T': (80, 200, 250)}
    S = 6
    im = Image.new('RGB', (C * S, R * S))
    dr = ImageDraw.Draw(im)
    for y in range(R):
        for x in range(C):
            c = np.array(F.get(k[y, x], (255, 0, 255)), float) * (0.85 + 0.15 * (h[y, x] - 1) * 2)
            dr.rectangle((x * S, y * S, x * S + S - 1, y * S + S - 1), fill=tuple(np.clip(c, 0, 255).astype(int)))
    vg = Image.open(VORLAGE).convert('RGB').resize((C * S, R * S))
    both = Image.new('RGB', (C * S * 2 + 8, R * S))
    both.paste(vg, (0, 0)); both.paste(im, (C * S + 8, 0))
    both.save(os.path.join(KARTE, 'layout_vergleich.png'))
    print('Karte 28 Layout %dx%d, Arena %d Kacheln (%d..%d, %d..%d)' % (C, R, arena.sum(), ax0, ax1, ay0, ay1))


if __name__ == '__main__':
    main()
