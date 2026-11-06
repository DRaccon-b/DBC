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
    # ------------------------------------------------------------------ Plateaus: organische Form (Hauptkoerper + Ausbuchtungen,
    # Felsnasen), Treppe an einer geraden Stelle der Suedkante
    PLATEAUS = [(16, 3, 27, 7), (26, 16, 35, 20), (8, 39, 14, 43), (21, 48, 29, 51), (51, 43, 63, 48)]
    treppen = [[21, 22, 2, 7], [30, 31, 2, 20], [10, 11, 2, 43], [24, 25, 2, 51], [56, 58, 2, 48]]
    for i, ((x0, y0, x1, y1), (tx0, tx1, e, yb)) in enumerate(zip(PLATEAUS, treppen)):
        rs = np.random.RandomState(70 + i)
        cx, cy, rx, ry = (x0 + x1 + 1) / 2, (y0 + y1 + 1) / 2, (x1 - x0 + 1) / 2, (y1 - y0 + 1) / 2
        form = ((xx_ := np.mgrid[0:R, 0:C][1]) * 0).astype(bool)
        yy_ = np.mgrid[0:R, 0:C][0]
        for j in range(4):                                      # Hauptkoerper und versetzte Ausbuchtungen
            ox, oy = (rs.rand() - 0.5) * rx * 1.1, (rs.rand() - 0.5) * ry * 0.8
            fx, fy = (0.95 if j == 0 else 0.45 + 0.3 * rs.rand()), (0.9 if j == 0 else 0.45 + 0.3 * rs.rand())
            form |= ((xx_ + 0.5 - cx - (ox if j else 0)) / (rx * fx)) ** 2 + ((yy_ + 0.5 - cy - (oy if j else 0)) / (ry * fy)) ** 2 <= 1
        form &= (yy_ >= y0 - 1) & (yy_ <= yb) & (k != 'r')
        form[yb, tx0 - 1:tx1 + 2] = True                        # gerade Kante fuer die Treppe
        form[yb + 1:, tx0 - 1:tx1 + 2] = False
        k[form] = 'v'
        h[form] = 2
    for (x0, x1, e, yb) in treppen:                          # vor der Treppe Schlamm, kein Wald/Moor
        k[yb + 1:yb + 5, x0 - 1:x1 + 2] = np.where(k[yb + 1:yb + 5, x0 - 1:x1 + 2] == 'r', 'r', 'd')
    # ------------------------------------------------------------------ Marionetten-Arena (rechts oben)
    yy, xx = np.mgrid[0:R, 0:C]
    dx, dy = np.abs(xx + 0.5 - 60.5), np.abs(yy + 0.5 - 17.0)
    achteck = (dx <= 10.6) & (dy <= 10.6) & (dx + dy <= 14.6)
    innen = (dx <= 9.6) & (dy <= 9.6) & (dx + dy <= 13.6)
    k[achteck] = 'h'                                          # Randbalken des Holzpodests
    k[innen] = 'w'                                            # Dielenboden (Risse, hochgeklappte Bretter im Bau-Skript)
    h[achteck] = 2                                            # eine Etage hoeher, Treppe nach Sueden
    arena_treppe = [58, 62, 27]
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
    # ------------------------------------------------------------------ Fluss: Quelle in der Bergwand oben, verbindet die
    # Moorpfuetzen, verschwindet unten in einer Felsspalte der Bergwand; wo er den Pfad kreuzt, kommt eine Bruecke hin
    FLUSS = [(30, 4.6), (29.6, 9), (27, 12.8), (23.5, 14.6), (21, 15.6), (18.6, 17.2), (16.6, 20), (16.3, 24), (18, 27),
             (21.5, 29.6), (23.2, 32), (22, 36), (19.6, 40), (18, 44), (17.4, 47), (18.6, 50.2), (22, 53.4), (28, 54.8),
             (33.5, 54), (38, 51), (44, 46), (48.4, 40.4), (52, 38.2), (57.5, 38.4), (61.5, 39.6), (68.6, 41.6), (70.4, 46),
             (69, 50), (65.6, 53.6), (63.6, 56.2), (60, 57.6), (52.5, 59.6), (50.2, 63), (52, 66), (53.5, 69.5)]
    pfad_vorher = (k == 'q')
    fl = []
    for (ax, ay), (bx, by) in zip(FLUSS, FLUSS[1:]):
        n = int(max(abs(bx - ax), abs(by - ay)) * 4) + 1
        fl += [(ax + (bx - ax) * t / n, ay + (by - ay) * t / n, bx - ax, by - ay) for t in range(n)]
    fluss = np.zeros((R, C), bool)
    for i, (px, py, _, _) in enumerate(fl):
        r_ = 1.05 + 0.25 * math.sin(i * 0.13)
        fluss |= ((xx + 0.5 - px) ** 2 + (yy + 0.5 - py) ** 2 <= r_ ** 2)
    fluss &= ~np.isin(k, ['v', 'h', 'w', 'b']) & ~((k == 'r') & (yy < 60))
    kreuz = fluss & pfad_vorher
    bruecken = []
    gesehen = np.zeros_like(kreuz)
    for (y0_, x0_) in zip(*np.nonzero(kreuz)):
        if gesehen[y0_, x0_]:
            continue
        st, teil = [(y0_, x0_)], []
        gesehen[y0_, x0_] = True
        while st:
            a_, b_ = st.pop(); teil.append((a_, b_))
            for da in (-1, 0, 1):
                for db in (-1, 0, 1):
                    p_, q_ = a_ + da, b_ + db
                    if 0 <= p_ < R and 0 <= q_ < C and kreuz[p_, q_] and not gesehen[p_, q_]:
                        gesehen[p_, q_] = True; st.append((p_, q_))
        ys_, xs_ = [t[0] for t in teil], [t[1] for t in teil]
        my, mx = sum(ys_) / len(ys_), sum(xs_) / len(xs_)
        d = min(fl, key=lambda f: (f[0] - mx - 0.5) ** 2 + (f[1] - my - 0.5) ** 2)
        quer = abs(d[2]) > abs(d[3])                          # Fluss laeuft waagerecht -> Bruecke Nord-Sued
        x0_, x1_, y0_, y1_ = min(xs_), max(xs_), min(ys_), max(ys_)
        if quer:
            while y0_ > 0 and fluss[y0_ - 1, x0_:x1_ + 1].any(): y0_ -= 1
            while y1_ < R - 1 and fluss[y1_ + 1, x0_:x1_ + 1].any(): y1_ += 1
            y0_, y1_ = y0_ - 1, y1_ + 1
            x0_, x1_ = min(x0_, int(mx) - 1), max(x1_, int(mx) + 1)
        else:
            while x0_ > 0 and fluss[y0_:y1_ + 1, x0_ - 1].any(): x0_ -= 1
            while x1_ < C - 1 and fluss[y0_:y1_ + 1, x1_ + 1].any(): x1_ += 1
            x0_, x1_ = x0_ - 1, x1_ + 1
            y0_, y1_ = min(y0_, int(my) - 1), max(y1_, int(my) + 1)
        bruecken.append([int(x0_), int(y0_), int(x1_), int(y1_), 'ns' if quer else 'ow'])
    k[fluss] = 'x'
    for (x0_, y0_, x1_, y1_, _) in bruecken:                 # Brueckenkoepfe auf festem Pfad
        for y in (y0_, y1_):
            for x in range(x0_, x1_ + 1):
                if k[y, x] == 'x':
                    pass
    h[k == 'x'] = 0
    lay = {
        'groesse': [C, R], 'klassen': [''.join(r) for r in k], 'hoehe': [''.join(str(c) for c in r) for r in h],
        'treppen_sued': treppen, 'arena_treppe': arena_treppe, 'bruecken': bruecken, 'fluss': FLUSS,
        'plateaus': PLATEAUS, 'wald': WALD,
        'arena': [60.5, 17.0], 'platz': [40.0, 60.5], 'baumhaus': [43, 14],
        'teleporter': [{'x': 12, 'y': 0, 'b': 4, 'h': 2}, {'x': 38, 'y': 68, 'b': 4, 'h': 2}],
    }
    os.makedirs(KARTE, exist_ok=True)
    json.dump(lay, open(os.path.join(KARTE, 'layout.json'), 'w'), indent=0)
    F = {'d': (75, 59, 50), 'g': (40, 62, 48), 'q': (110, 90, 70), 'x': (50, 90, 70), 'a': (60, 40, 30),
         'v': (60, 80, 60), 'r': (55, 51, 68), 'b': (68, 74, 90), 'f': (120, 124, 140), 'z': (110, 40, 80),
         'h': (100, 64, 40), 'w': (130, 96, 60)}
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
