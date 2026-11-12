"""Karte 27 - Destiny Lake (A02), Layout nach der Vorlage -> maps/karte27/layout.json

  python3 tools/karte27_layout.py

Vorlage assets/vorlagen/karte27_vorlage.png: 1600x1360 px = 100x85 Kacheln. Vorgehen wie Karte 23 / 25.
Grosser See in der Mitte mit Inseln, Steinweg-Ring und Kristall-Schrein oben, Steinbruecken zu zwei Sandinseln,
Moor (Schlamm mit Pfuetzen) oben links, Plateau-Band oben mit Steinmauer-Fronten, Bach mit Wasserfaellen oben rechts,
Feldweg rechts und unten, zwei Stege mit Sandstrand unten, Wald ringsum, abgestuerztes Kaiser-Schiff unten links auf
einem Steinplatz, Teleporter rechts oben und beim Schiff.

Klassen:  h Wald  g Gras  f Schlamm/Moor  x Wasser  s Sand  w Feldweg  p Steinweg/Platz  m Steinmauer-Front
          b Bruecke/Steg (Holz)  q Steinbruecke  T Teleporter
Hoehen:   1 Grundebene, 2 Plateau (noerdlich der Mauerfronten)
"""
import json, os
import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte27')
VORLAGE = os.path.join(ROOT, 'assets', 'vorlagen', 'karte27_vorlage.png')
C, R, T = 100, 85, 16
REF = {'g': (84, 136, 62), 'g2': (60, 140, 48), 'h': (38, 98, 38), 'h2': (24, 50, 24), 'x': (48, 120, 168),
       'f': (108, 90, 62), 'w': (192, 168, 108), 's': (230, 208, 148), 'p': (124, 135, 136), 'm': (106, 112, 128),
       'b': (172, 122, 64), 'k': (50, 40, 80), 'W': (118, 206, 240)}
TELEPORTER = [(97, 6, 3, 3), (11, 72, 3, 2)]
# Hochflaechen (x0, y0, x1, y1) in Kacheln, nach den Mauerfronten der Vorlage; darunter 3 Reihen Mauerfront
PLATEAUS = [(0, 0, 19, 7), (20, 0, 26, 4), (27, 0, 32, 5), (33, 0, 40, 4), (41, 0, 67, 2), (68, 0, 88, 13),
            (0, 48, 25, 58)]
FRONT_REIHEN = 3
STEGE_WEG = [(24, 29, 30, 32), (15, 42, 18, 46)]
SCHIFF = (6, 57, 23, 70)                                       # Rechteck des Schiff-Wracks (Objekt), 4 Kacheln nach rechts
WALD_NEU = [(0, 59, 3, 66), (0, 67, 3, 71), (0, 72, 7, 80)]     # Nutzer: Baeume unten links vom Wrack


def klassen():
    a = np.array(Image.open(VORLAGE).convert('RGB')).astype(int)
    k = np.full((R, C), '?')
    for y in range(R):
        for x in range(C):
            t = a[y * T:(y + 1) * T, x * T:(x + 1) * T]
            m = np.median(t.reshape(-1, 3), 0)
            d = {c: np.abs(m - np.array(v)).sum() for c, v in REF.items()}
            c = min(d, key=d.get)
            if c in ('p', 'm'):                                      # Mauer: senkrechte Streifen (Spalten wechseln stark)
                g = t.mean(2)
                spalten = np.abs(np.diff(g, axis=1)).mean()
                zeilen = np.abs(np.diff(g, axis=0)).mean()
                c = 'm' if spalten > zeilen * 1.35 else 'p'
            k[y, x] = c[0] if d[min(d, key=d.get)] < 70 else '?'
            if c in ('W',):
                k[y, x] = 'x'
            elif c in ('m', 'p'):
                k[y, x] = c
    return k


def main():
    os.makedirs(KARTE, exist_ok=True)
    k = klassen()
    for _ in range(4):                                               # unklare Kacheln (Objekte) aus den Nachbarn
        for y in range(R):
            for x in range(C):
                if k[y, x] in '?k':
                    nb = [k[yy, xx] for yy, xx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1))
                          if 0 <= yy < R and 0 <= xx < C and k[yy, xx] not in '?k']
                    if nb:
                        k[y, x] = max(set(nb), key=nb.count)
    k[k == '?'] = 'g'
    k[k == 'k'] = 'g'
    from collections import deque                                    # einzelne Baeume der Vorlage sind kein Wald
    gesehen = np.zeros((R, C), bool)
    for y in range(R):
        for x in range(C):
            if k[y, x] == 'h' and not gesehen[y, x]:
                comp, q = [], deque([(y, x)]); gesehen[y, x] = True
                while q:
                    cy, cx = q.popleft(); comp.append((cy, cx))
                    for yy, xx in ((cy - 1, cx), (cy + 1, cx), (cy, cx - 1), (cy, cx + 1)):
                        if 0 <= yy < R and 0 <= xx < C and k[yy, xx] == 'h' and not gesehen[yy, xx]:
                            gesehen[yy, xx] = True; q.append((yy, xx))
                if len(comp) < 12:
                    for cy, cx in comp:
                        k[cy, cx] = 'g'
    for (x0, y0, x1, y1) in STEGE_WEG:                                # Nutzer: die beiden Stege links entfernen
        sub = k[y0:y1 + 1, x0:x1 + 1]
        sub[sub == 'b'] = 'x'
    seite = k[46:62, 23:29]                                          # Mauerreste an der Seite des Plateaus unten links
    seite[seite == 'p'] = 'g'
    sub = k[SCHIFF[1]:SCHIFF[3] + 1, SCHIFF[0]:SCHIFF[2] + 1]      # abgestuerztes Schiff (Objekt) steht auf Gras
    sub[np.isin(sub, list('hp'))] = 'g'
    for (x0, y0, x1, y1) in WALD_NEU:
        k[y0:y1 + 1, x0:x1 + 1] = 'h'
    h = np.ones((R, C), int)
    for (x0, y0, x1, y1) in PLATEAUS:
        h[y0:y1 + 1, x0:x1 + 1] = 2
    for (x0, y0, x1, y1) in PLATEAUS:                                 # Mauerfront-Reihen: Boden der unteren Ebene
        sub = k[y1 + 1:y1 + 1 + FRONT_REIHEN, x0:x1 + 1]
        sub[np.isin(sub, list('mp'))] = 'g'
    k[(k == 'm')] = 'g'                                               # restliche Mauerteile (Seiten) -> Gras
    for (tx, ty, b, hh) in TELEPORTER:
        k[ty:ty + hh, tx:tx + b] = 'T'
    import regeln_a02                                                 # Regel 6: Wege nie nur gerade
    # Destiny Lake: Wege waren schon natuerlich geschwungen -> nicht zusaetzlich biegen (nur 45-Grad-Kanten)
    lay = {'groesse': [C, R], 'klassen': [''.join(z) for z in k], 'hoehe': [''.join(str(c) for c in z) for z in h],
           'schiff': SCHIFF, 'plateaus': PLATEAUS, 'front_reihen': FRONT_REIHEN,
           'teleporter': [{'x': tx, 'y': ty, 'b': b, 'h': hh} for (tx, ty, b, hh) in TELEPORTER]}
    json.dump(lay, open(os.path.join(KARTE, 'layout.json'), 'w'), indent=0)
    F = {'h': (30, 80, 30), 'g': (84, 136, 62), 'f': (110, 80, 50), 'x': (48, 120, 200), 's': (232, 210, 150),
         'w': (200, 170, 110), 'p': (160, 165, 170), 'm': (80, 80, 95), 'b': (140, 90, 40), 'q': (120, 120, 130),
         'T': (190, 80, 240)}
    S = 6
    im = Image.new('RGB', (C * S, R * S))
    dr = ImageDraw.Draw(im)
    for y in range(R):
        for x in range(C):
            c = np.array(F.get(k[y, x], (255, 0, 255)), float) * (0.8 + 0.15 * h[y, x])
            dr.rectangle((x * S, y * S, x * S + S - 1, y * S + S - 1), fill=tuple(np.clip(c, 0, 255).astype(int)))
    vg = Image.open(VORLAGE).convert('RGB').resize((C * S, R * S))
    both = Image.new('RGB', (C * S * 2 + 8, R * S))
    both.paste(vg, (0, 0)); both.paste(im, (C * S + 8, 0))
    both.save(os.path.join(KARTE, 'layout_vergleich.png'))
    print('Karte 27 Layout %dx%d, Plateau %d Kacheln' % (C, R, (h == 2).sum()))


if __name__ == '__main__':
    main()
