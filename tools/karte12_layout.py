"""Karte 12 (Spiral Mountain: Puppet Woods): Kachelraster nach der Vorlage -> maps/karte12/layout.json

  python3 tools/karte12_layout.py

Vorlage assets/vorlagen/karte12_vorlage.png (1280x1120 = 80x70 Kacheln a 16 px).
Schlammiger, duesterer Puppenwald: ringsum Bergwand (wie Karte 11), links dichte Waldstuecke mit duesteren Baeumen,
Moorpfuetzen, fuenf Felsplateaus mit Treppen, oben das Baumhaus, rechts oben die Marionetten-Arena, rechts
Obstbaumreihen und Kuerbisfelder, unten ein gepflasterter Platz am Ausgang. Ein Trampelpfad fuehrt vom Platz zum
oberen Ausgang - mit Unterbrechungen (Regel 6).
Klassen:  d Schlamm  g Waldboden (dunkles Moos)  q Trampelpfad  x Moorpfuetze  a Acker  v Plateau (Moos)
          r Fels (Bergwand)  b Pflaster (Platz)  f Arena-Steinboden  z Arena-Schachbrett  h Holzrand der Arena
Hoehen:   0 Moorpfuetze, 1 Boden, 2 Plateaus, 5 Bergwand.
"""
import json, math, os
import numpy as np
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte12')
C, R = 80, 70


def blob(k, x0, y0, x1, y1, art, seed, rund=0.35):
    """unregelmaessige, runde Flaeche im Rechteck (Waldstueck, Pfuetze)"""
    rs = np.random.RandomState(seed)
    cx, cy, rx, ry = (x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0 + 1) / 2, (y1 - y0 + 1) / 2
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            d = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
            if d <= 1 - rund * rs.rand() * (d > 0.45):
                k[y, x] = art


def main():
    k = np.full((R, C), 'd')
    h = np.ones((R, C), int)
    # ------------------------------------------------------------------ Bergwand ringsum (wie Karte 11)
    berg = np.zeros((R, C), bool)
    berg[0:2, :] = True
    berg[:, 0:2] = True
    berg[:, 77:80] = True
    berg[67:70, :] = True
    for (x0, x1, y1) in ((0, 3, 2), (4, 9, 3), (21, 24, 2), (50, 57, 2), (72, 79, 2), (76, 79, 7)):
        berg[0:y1 + 1, x0:x1 + 1] = True                     # unregelmaessige Oberkante
    for (y0, y1, x1) in ((12, 13, 2), (20, 21, 2), (36, 46, 2), (41, 43, 3), (62, 66, 2), (65, 66, 3)):
        berg[y0:y1 + 1, 0:x1 + 1] = True                     # linke Wand mit Vorspruengen
    for (y0, y1, x0) in ((37, 42, 75), (44, 56, 76), (60, 66, 76)):
        berg[y0:y1 + 1, x0:] = True
    for (x0, x1, y0) in ((0, 8, 66), (9, 17, 66), (47, 52, 65), (55, 60, 63), (61, 66, 66)):
        berg[y0:, x0:x1 + 1] = True                          # Unterkante mit Felsnasen
    berg[0:3, 12:16] = False                                 # Ausgang oben (Teleporter)
    berg[64:70, 38:42] = False                               # Ausgang unten (Teleporter)
    k[berg] = 'r'
    h[berg] = 5
    # ------------------------------------------------------------------ Waldstuecke (dichte duestere Baeume)
    WALD = [(3, 12, 9, 19), (29, 9, 36, 13), (19, 22, 23, 27), (31, 22, 36, 26), (4, 24, 10, 28), (15, 30, 20, 34),
            (31, 30, 38, 34), (3, 35, 8, 38), (33, 35, 38, 39), (3, 46, 8, 53), (7, 54, 12, 59), (24, 45, 29, 48),
            (15, 55, 19, 58), (26, 58, 31, 63), (15, 61, 19, 63)]
    for i, (x0, y0, x1, y1) in enumerate(WALD):
        blob(k, x0, y0, x1, y1, 'g', 10 + i)
    # ------------------------------------------------------------------ Moorpfuetzen
    MOOR = [(16, 15, 21, 19), (20, 28, 24, 31), (66, 5, 71, 8), (5, 42, 8, 45), (14, 46, 20, 48), (55, 37, 61, 40),
            (47, 36, 49, 39), (62, 54, 66, 57), (48, 57, 51, 60)]
    for i, (x0, y0, x1, y1) in enumerate(MOOR):
        blob(k, x0, y0, x1, y1, 'x', 40 + i, 0.25)
    # ------------------------------------------------------------------ Kuerbisfelder (Acker)
    for (x0, y0, x1, y1) in ((46, 33, 52, 36), (64, 32, 70, 34), (62, 42, 67, 44), (52, 51, 58, 53)):
        k[y0:y1 + 1, x0:x1 + 1] = 'a'
    # ------------------------------------------------------------------ Plateaus (Moos oben), Treppen nach Sueden
    PLATEAUS = [(17, 4, 26, 7), (27, 17, 34, 19), (9, 40, 13, 42), (22, 49, 28, 50), (52, 44, 62, 47)]
    for (x0, y0, x1, y1) in PLATEAUS:
        k[y0:y1 + 1, x0:x1 + 1] = 'v'
        h[y0:y1 + 1, x0:x1 + 1] = 2
    k[5:8, 16] = 'v'; h[5:8, 16] = 2
    k[5:8, 27] = 'v'; h[5:8, 27] = 2
    treppen = [[21, 22, 2, 7], [30, 31, 2, 19], [10, 11, 2, 42], [24, 25, 2, 50], [56, 58, 2, 47]]
    for (x0, x1, e, yb) in treppen:                          # vor der Treppe Schlamm, kein Wald/Moor
        k[yb + 1:yb + 5, x0 - 1:x1 + 2] = np.where(k[yb + 1:yb + 5, x0 - 1:x1 + 2] == 'r', 'r', 'd')
    # ------------------------------------------------------------------ Marionetten-Arena (rechts oben)
    yy, xx = np.mgrid[0:R, 0:C]
    dx, dy = np.abs(xx + 0.5 - 60.5), np.abs(yy + 0.5 - 17.0)
    achteck = (dx <= 10.6) & (dy <= 10.6) & (dx + dy <= 14.6)
    innen = (dx <= 9.6) & (dy <= 9.6) & (dx + dy <= 13.6)
    k[achteck] = 'h'
    k[innen] = 'f'
    ring = (np.maximum(dx, dy) <= 5.6) & (np.maximum(dx, dy) > 4.6) & (dx + dy <= 9.6)
    ring |= ((dx <= 1.6) & (dy > 4.6) & (dy <= 6.6)) | ((dy <= 1.6) & (dx > 4.6) & (dx <= 6.6))   # Kreuzarme
    ring |= (np.minimum(dx, dy) <= 0.6) & (np.maximum(dx, dy) <= 1.6)                           # Mittelkreuz
    ring |= (dx <= 1.6) & (dy <= 0.6) | (dy <= 1.6) & (dx <= 0.6)
    k[ring & innen] = 'z'
    k[(dx <= 1.6) & (dy > 9.0) & achteck] = 'f'                 # Eingaenge Nord und Sued durch den Holzrand
    # ------------------------------------------------------------------ Platz am unteren Ausgang
    dxp, dyp = np.abs(xx + 0.5 - 40.0), np.abs(yy + 0.5 - 60.5)
    platz = ((dxp <= 7.2) & (dyp <= 4.8) & ((dxp / 7.2) ** 2 + (dyp / 4.8) ** 2 <= 1.25)) | ((dxp <= 2.1) & (yy >= 60) & (yy <= 69))
    k[platz & (k != 'r')] = 'b'
    k[64:70, 38:42] = 'b'
    # ------------------------------------------------------------------ Trampelpfad zum oberen Ausgang (unterbrochen)
    PFAD = [(40, 55.5), (37.5, 52), (35, 49.5), (33.5, 46), (31.5, 42.5), (30, 39), (28, 36), (27, 32.5), (26.5, 29),
            (25.2, 25), (24.8, 21.5), (24, 17.5), (22.5, 14), (19.5, 11.5), (16.5, 10), (14.5, 7.5), (13.5, 4.5),
            (13.5, 2.5)]
    luecken = [(0.22, 0.27), (0.5, 0.56), (0.78, 0.82)]          # dort setzt der Weg aus und geht spaeter weiter
    pts = []
    for (ax, ay), (bx, by) in zip(PFAD, PFAD[1:]):
        n = int(max(abs(bx - ax), abs(by - ay)) * 4) + 1
        pts += [(ax + (bx - ax) * t / n, ay + (by - ay) * t / n) for t in range(n)]
    for i, (px, py) in enumerate(pts):
        t = i / len(pts)
        if any(a <= t <= b for a, b in luecken):
            continue
        breite = 0.95 + 0.35 * math.sin(i * 0.21)
        for y in range(int(py - 2), int(py + 3)):
            for x in range(int(px - 2), int(px + 3)):
                if 0 <= y < R and 0 <= x < C and (x + 0.5 - px) ** 2 + (y + 0.5 - py) ** 2 <= breite ** 2 \
                        and k[y, x] in 'dgxa':
                    k[y, x] = 'q'
    k[0:3, 12:16] = 'q'                                       # vor dem Teleporter oben
    h[k == 'x'] = 0
    lay = {
        'groesse': [C, R], 'klassen': [''.join(r) for r in k], 'hoehe': [''.join(str(c) for c in r) for r in h],
        'treppen_sued': treppen,
        'plateaus': PLATEAUS, 'wald': WALD,
        'arena': [60.5, 17.0], 'platz': [40.0, 60.5], 'baumhaus': [43, 14],
        'teleporter': [{'x': 12, 'y': 0, 'b': 4, 'h': 2}, {'x': 38, 'y': 68, 'b': 4, 'h': 2}],
    }
    os.makedirs(KARTE, exist_ok=True)
    json.dump(lay, open(os.path.join(KARTE, 'layout.json'), 'w'), indent=0)
    F = {'d': (75, 59, 50), 'g': (40, 62, 48), 'q': (110, 90, 70), 'x': (50, 90, 70), 'a': (60, 40, 30),
         'v': (60, 80, 60), 'r': (55, 51, 68), 'b': (68, 74, 90), 'f': (120, 124, 140), 'z': (110, 40, 80),
         'h': (100, 64, 40)}
    out = np.zeros((R, C, 3), np.uint8)
    for kk, c in F.items():
        out[k == kk] = c
    vor = Image.open(os.path.join(ROOT, 'assets', 'vorlagen', 'karte12_vorlage.png')).convert('RGB').resize((C * 8, R * 8))
    bild = Image.new('RGB', (C * 16 + 8, R * 8))
    bild.paste(vor, (0, 0))
    bild.paste(Image.fromarray(out).resize((C * 8, R * 8), 0), (C * 8 + 8, 0))
    bild.save(os.path.join(KARTE, 'layout_vergleich.png'))
    print('Karte 12 Layout %dx%d' % (C, R))


if __name__ == '__main__':
    main()
