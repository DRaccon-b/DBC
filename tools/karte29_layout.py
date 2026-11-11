"""Karte 29 - The Sea of Darkness (A02), Layout nach der Vorlage -> maps/karte29/layout.json

  python3 tools/karte29_layout.py

Vorlage assets/vorlagen/karte29_vorlage.png: 1440x1280 px = 90x80 Kacheln. Dunkles Meer, flaches Wasser am Ufer,
graublauer Sandstrand mit helleren Sandflecken, Felsbloecke (Hochflaechen mit Front), Tempelplatz rechts unten
(erhoeht, Steinsaeulen, Tor oben, Treppe unten), Bruecken/Stege, Leuchtturm oben rechts, Portale.

Klassen:  x tiefes Meer  s flaches Wasser  g Strand  l heller Sand  r Fels (Hochflaeche)  m Felsfront  p Tempelplatz
          q Pflasterplatz oben links
          b Bruecke/Steg  T Teleporter/Portal
Hoehen:   1 Strand/Wasser, 2 Felsbloecke und Tempelplatz
"""
import json, os
from collections import deque
import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte29')
VORLAGE = os.path.join(ROOT, 'assets', 'vorlagen', 'karte29_vorlage.png')
C, R, T = 90, 80, 16
REF = {'x': (53, 79, 104), 's': (101, 143, 154), 'g': (118, 138, 150), 'l': (152, 158, 170), 'r': (122, 130, 145),
       'm': (55, 62, 78), 'b': (10, 10, 18)}
FELSEN = [(44, 6, 52, 11), (60, 5, 65, 9), (4, 23, 7, 32), (22, 26, 30, 33), (43, 28, 46, 33), (7, 42, 14, 47),
          (30, 47, 35, 52), (20, 58, 27, 63), (36, 66, 39, 70), (82, 18, 86, 23)]   # Felsbloecke (x0, y0, x1, y1)
LANDEPLATZ = (4, 7, 15, 17)                      # gepflasterter Platz oben links (Portal, Laternen)
PLATZ = (47, 45, 72, 66)                         # Tempelplatz (x0, y0, x1, y1) Kacheln, Front darunter
PLATZ_TREPPE = (59, 62)                          # Treppe in der Suedfront (Spalten)
BRUECKEN = [(64, 17, 67, 44), (34, 55, 46, 57)]   # (Nutzer: kein Steg an der Tempeltreppe)   # (x0, y0, x1, y1)
TELEPORTER = [(5, 4, 2, 2), (82, 72, 3, 3), (82, 3, 5, 3)]          # Portal oben links, Strudel unten rechts, Riss oben rechts
FRONT_REIHEN = 2


def klassen():
    a = np.array(Image.open(VORLAGE).convert('RGB')).astype(int)
    k = np.full((R, C), '?')
    for y in range(R):
        for x in range(C):
            m = np.median(a[y * T:(y + 1) * T, x * T:(x + 1) * T].reshape(-1, 3), 0)
            d = {c: np.abs(m - np.array(v)).sum() for c, v in REF.items()}
            c = min(d, key=d.get)
            k[y, x] = c if d[c] < 45 else '?'
    return k


def komponenten(k, arten):
    gesehen = np.zeros(k.shape, bool)
    for y in range(R):
        for x in range(C):
            if k[y, x] in arten and not gesehen[y, x]:
                comp, q = [], deque([(y, x)]); gesehen[y, x] = True
                while q:
                    cy, cx = q.popleft(); comp.append((cy, cx))
                    for yy, xx in ((cy - 1, cx), (cy + 1, cx), (cy, cx - 1), (cy, cx + 1)):
                        if 0 <= yy < R and 0 <= xx < C and k[yy, xx] in arten and not gesehen[yy, xx]:
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
    k[k == 'b'] = 'x'                                                # Bruecken kommen aus BRUECKEN
    k[np.isin(k, list('rm'))] = 'g'                                  # Fels/Fronten/Objekte -> Boden, Felsen von Hand
    for comp in list(komponenten(k, 'x')):                           # kleine Wasserflecken im Sand: Pfuetzen
        if len(comp) < 8:
            for cy, cx in comp:
                k[cy, cx] = 's'
    h = np.ones((R, C), int)
    for (x0, y0, x1, y1) in FELSEN:
        k[y0:y1 + 1, x0:x1 + 1] = 'r'
        h[y0:y1 + 1 - FRONT_REIHEN, x0:x1 + 1] = 2                   # unterste Reihen: Front (Boden der unteren Ebene)
        k[y1 + 1 - FRONT_REIHEN:y1 + 1, x0:x1 + 1] = 'm'
        if x1 - x0 >= 4 and y1 - y0 >= 5:                            # obere Ecken abrunden (natuerlicher, Raster)
            for xc in (x0, x1):
                h[y0, xc] = 1
                k[y0, xc] = 'g'
    for y in range(PLATZ[3] + 1, PLATZ[3] + 4):                       # Treppe trifft direkt aufs helle Wasser
        for x in range(PLATZ_TREPPE[0] - 1, PLATZ_TREPPE[1] + 2):
            if k[y, x] == 'x':
                k[y, x] = 's'
    for (bx, by) in ((180, 446), (660, 222), (885, 286), (150, 944), (545, 420)):   # Boote der Vorlage: Strand, keine Pfuetze
        for y in range(by // T - 2, by // T + 2):
            for x in range(bx // T - 3, bx // T + 4):
                if k[y, x] == 's':
                    k[y, x] = 'g'
    lx0, ly0, lx1, ly1 = LANDEPLATZ
    k[ly0:ly1 + 1, lx0:lx1 + 1] = 'q'
    px0, py0, px1, py1 = PLATZ
    k[py0:py1 + 1, px0:px1 + 1] = 'p'
    h[py0:py1 + 1, px0:px1 + 1] = 2
    for (x0, y0, x1, y1) in BRUECKEN:
        k[y0:y1 + 1, x0:x1 + 1] = 'b'
    lay = {'groesse': [C, R], 'klassen': [''.join(z) for z in k], 'hoehe': [''.join(str(c) for c in z) for z in h],
           'platz': list(PLATZ), 'platz_treppe': list(PLATZ_TREPPE), 'bruecken': BRUECKEN, 'front_reihen': FRONT_REIHEN,
           'treppen_sued': [[PLATZ_TREPPE[0], PLATZ_TREPPE[1], 2, PLATZ[3]]],
           'teleporter': [{'x': tx, 'y': ty, 'b': b, 'h': hh} for (tx, ty, b, hh) in TELEPORTER]}
    json.dump(lay, open(os.path.join(KARTE, 'layout.json'), 'w'), indent=0)
    F = {'x': (40, 60, 90), 's': (100, 150, 165), 'g': (130, 145, 155), 'l': (175, 180, 190), 'r': (95, 100, 115),
         'p': (150, 150, 170), 'q': (140, 140, 155), 'm': (60, 65, 80), 'b': (20, 20, 30), 'T': (190, 80, 240)}
    S = 6
    im = Image.new('RGB', (C * S, R * S))
    dr = ImageDraw.Draw(im)
    for y in range(R):
        for x in range(C):
            c = np.array(F.get(k[y, x], (255, 0, 255)), float) * (0.85 + 0.15 * (h[y, x] - 1))
            dr.rectangle((x * S, y * S, x * S + S - 1, y * S + S - 1), fill=tuple(np.clip(c, 0, 255).astype(int)))
    vg = Image.open(VORLAGE).convert('RGB').resize((C * S, R * S))
    both = Image.new('RGB', (C * S * 2 + 8, R * S))
    both.paste(vg, (0, 0)); both.paste(im, (C * S + 8, 0))
    both.save(os.path.join(KARTE, 'layout_vergleich.png'))
    print('Karte 29 Layout %dx%d, Hochflaechen %d Kacheln' % (C, R, (h == 2).sum()))


if __name__ == '__main__':
    main()
