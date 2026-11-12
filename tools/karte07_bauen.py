"""Karte 07 - The Holy Peaks: schwebende Bergterrassen ueber den Wolken.

  python3 tools/karte07_bauen.py layout    # Raster -> maps/karte07/layout.json (von Hand nach der Vorlage)
  python3 tools/karte07_objekte.py         # Objekte am 16x16-Raster
  python3 tools/karte07_bauen.py           # -> maps/karte07/terrain.png

Ebenen: 0 Wolken (nicht begehbar), 1 untere Terrasse (Teefelder), 2 mittlere Terrasse (Pagode), 3 Gipfel
(Schnee, Felsplateau, Drachenschrein). Bausteine: Gras/Sand aus Karte 01, Schnee aus Karte 05, Wegkacheln aus
Karte 04, Kopfstein aus Karte 03 (grau), Felswaende/Treppen/Bruecke aus Karte 01/04, Teleporter.
"""
import json, math, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import karte_bauen as kb
import karte04_bauen as k4
import bauwerke

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte07')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte07')
T = 16
N_FRAMES = 4                                      # Regel: hoechstens 4 Animationsbilder
import karte_bauen as _kb
_kb.N_FRAMES = N_FRAMES                       # Windwelle (Pflanzen) ueber die 4 Bilder der Karte
RAND = 6                                       # Wolkenring rundherum (Kacheln)
IC, IR = 100, 90                               # Inselbereich (Koordinaten wie Vorlage)
COLS, ROWS = IC + 2 * RAND, IR + 2 * RAND
H = k4.H
weich, zell_maske = k4.weich, k4.zell_maske
k4.RASTER45 = True                       # Nutzer: ALLE Bodenkanten am 16er-Raster mit 45 Grad (Regel 6b)
k4.FELS['heilig'] = ['#3c4048', '#545a64', '#6e7480', '#8a909a', '#a6abb4', '#c2c6cc', '#dcdfe3']
LIPPE_GRAS = ['#2e6a3a', '#3e8444', '#56a04e', '#6eb85a', '#8ccc6a', '#a8dc82']
LIPPE_SCHNEE = ['#90a6bc', '#b0c4d6', '#cad9e6', '#dfe9f2', '#f0f6fb', '#ffffff']
LIPPE_FELS = ['#5a606a', '#727882', '#8c929c', '#a6abb4', '#bcc0c6', '#d2d5da']


NEBEL = np.array(H('#e4e9f1'), np.float32)


def wolkenfels(breite, hoehe, seed):
    """Felswand: gerade gestapelte, unregelmaessige Steinbloecke (blaugrau, Licht oben links, dunkle Fugen,
    einzelne Risse), nach unten leicht abgedunkelt."""
    rs = random.Random(seed)
    P = [np.array(H(c), np.float32) for c in ('#2e333c', '#444b57', '#5c6472', '#77808e', '#959dab', '#b6bdc8', '#d6dbe2')]
    a = np.zeros((hoehe, breite, 3), np.float32)
    a[:] = P[1]
    y = 0
    while y < hoehe:
        bh = rs.randint(5, 10)
        x = -rs.randint(0, 8)
        while x < breite:
            bw = rs.randint(6, 15)
            ton = rs.choice((2, 2, 3, 3, 4))
            for yy in range(y, min(hoehe, y + bh)):
                for xx in range(max(0, x), min(breite, x + bw)):
                    dy, dx = yy - y, xx - x
                    c = P[ton]
                    if dy == 0 or dx == 0:
                        c = P[min(6, ton + 2)] if dy == 0 else P[min(6, ton + 1)]
                    if dy == bh - 1 or dx == bw - 1:
                        c = P[0]
                    elif dy == bh - 2 or dx == bw - 2:
                        c = P[max(0, ton - 1)]
                    a[yy, xx] = c
            x += bw
        y += bh
    t = (np.arange(hoehe, dtype=np.float32) / max(1, hoehe - 1))[:, None, None]
    a = a * (1 - 0.22 * t)                                # nach unten etwas dunkler (gerade, ohne Nebel)
    for _ in range(breite // 40):                         # vereinzelte Bruchstuecke / Risse in Bloecken
        fx, fy = rs.randrange(2, breite - 6), rs.randrange(2, max(3, hoehe - 6))
        for i in range(rs.randint(3, 6)):
            if fy + i < hoehe and fx + i // 2 < breite:
                a[fy + i, fx + i // 2] = P[0]
    return np.clip(a, 0, 255).astype(np.uint8)


_alt_fels = k4.fels_textur


def _fels(name, breite, hoehe, seed):
    return wolkenfels(breite, hoehe, seed) if name == 'wolkenfels' else _alt_fels(name, breite, hoehe, seed)


k4.fels_textur = _fels
k4.FELS['wolkenfels'] = ['#2e333c', '#444b57', '#5c6472', '#77808e', '#959dab', '#b6bdc8', '#d6dbe2']


def R(cls, art, x0, y0, x1, y1):
    cls[y0:y1 + 1, x0:x1 + 1] = art


KUESTE = [  # (Punkte, Achse der Kante, -1 = davor/darueber weg, +1 = dahinter/darunter weg) - Inselkoordinaten
    ([(8.5, 1.5), (7.8, 3.7), (3.6, 7.9), (2.9, 14.9), (5.0, 23.2), (7.8, 30.1), (5.7, 38.5), (7.1, 46.8),
      (3.5, 52.0), (2.9, 55.2)], 'y', -1),
    ([(14.0, 1.5), (18.1, 2.6), (21.5, 4.4), (28.4, 5.1), (35.3, 4.4), (40.8, 1.0)], 'x', -1),
    ([(60.0, 1.0), (63.0, 2.6), (66.0, 4.4), (68.0, 6.0)], 'x', -1),
    ([(97.5, 33.0), (96.5, 35.0), (95.1, 39.9), (91.0, 45.4), (90.3, 48.9), (93.0, 53.8), (96.5, 59.3),
      (97.5, 61.0)], 'y', 1),
    ([(38.0, 87.0), (40.1, 86.5), (44.9, 85.2), (49.0, 84.4), (58.7, 83.4), (68.3, 83.8), (76.6, 85.0),
      (80.7, 86.3), (83.0, 87.0)], 'x', 1),
]


def layout():
    yy, xx = np.mgrid[0:IR, 0:IC]
    cls = np.full((IR, IC), 'o')                  # o = Wolken
    hoehe = np.zeros((IR, IC), int)
    # Insel-Umriss (leicht wellig) und Hoehen
    insel = (xx >= 3) & (xx <= 97) & (yy >= 2) & (yy <= 86)
    insel &= ~((xx >= 68) & (xx <= 73) & (yy <= 26))            # Wolkenspalt zwischen Gipfel und Schreinplateau
    # Kuestenlinie nach den eingezeichneten Linien (Buchten statt Quadrat)
    for (punkte, achse, seite) in KUESTE:
        p_ = np.array(punkte, float)
        if achse == 'y':                                         # Kante x(y): links/rechts abschneiden
            lo, hi = p_[:, 1].min(), p_[:, 1].max()
            kante = np.interp(yy + 0.5, p_[:, 1], p_[:, 0])
            weg = (yy + 0.5 >= lo) & (yy + 0.5 <= hi) & ((xx + 0.5 < kante) if seite < 0 else (xx + 0.5 > kante))
        else:                                                    # Kante y(x): oben/unten abschneiden
            lo, hi = p_[:, 0].min(), p_[:, 0].max()
            kante = np.interp(xx + 0.5, p_[:, 0], p_[:, 1])
            weg = (xx + 0.5 >= lo) & (xx + 0.5 <= hi) & ((yy + 0.5 < kante) if seite < 0 else (yy + 0.5 > kante))
        insel &= ~weg
    cls[insel] = 'g'
    hoehe[insel] = 1
    oben = insel & (yy <= 59)
    hoehe[oben] = 2
    # Gipfelstufe (3): Kante mit Stufen wie in der Vorlage
    gipfel = insel & ((((xx <= 33) & (yy <= 24)) | ((xx >= 33) & (xx <= 67) & (yy <= 28)) |
                       ((xx >= 74) & (yy <= 27))))
    hoehe[gipfel] = 3
    # Boden der Gipfelstufe: Schnee links, Fels in der Mitte, Pflaster am Schrein
    cls[gipfel & (xx <= 30)] = 'n'
    cls[gipfel & (xx >= 26) & (xx <= 67)] = 'f'
    cls[gipfel & (xx <= 9) & (yy <= 9)] = 'f'
    cls[gipfel & (xx >= 74)] = 'n'
    R(cls, 'p', 77, 4, 96, 24)
    ring = ((((xx - 47) / 15.0) ** 2 + ((yy - 15) / 8.5) ** 2) <= 1) & ((((xx - 47) / 11.5) ** 2 + ((yy - 15) / 5.8) ** 2) > 1)
    cls[ring & gipfel] = 'r'
    for (cx, cy, rx, ry) in ((56, 11, 4, 2.5), (47, 19, 6, 2.5), (51, 23, 3, 1.5)):   # Schneeflecken im Ring
        cls[(((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2 <= 1) & gipfel & ~ring] = 'n'
    # Mittelstufe: Schnee links, sonst Gras, Pagodenhof
    mitte = (hoehe == 2)
    cls[mitte & (xx <= 37)] = 'n'
    cls[mitte & (xx <= 37) & (((xx - 17) / 4.5) ** 2 + ((yy - 34) / 2.5) ** 2 <= 1)] = 'f'
    cls[mitte & (xx <= 37) & (((xx - 13) / 5) ** 2 + ((yy - 43) / 2.5) ** 2 <= 1)] = 'f'
    R(cls, 'p', 71, 31, 89, 46)
    # Wege
    for (x0, y0, x1, y1) in ((22, 25, 26, 57), (26, 41, 67, 45), (61, 15, 64, 35), (64, 31, 70, 35), (78, 47, 81, 58),
                             (72, 51, 81, 54), (64, 12, 68, 15),
                             (18, 60, 89, 63), (18, 63, 21, 74), (44, 63, 47, 85), (68, 63, 71, 85),
                             (84, 63, 86, 70)):
        m = (xx >= x0) & (xx <= x1) & (yy >= y0) & (yy <= y1) & insel
        cls[m & ~np.isin(cls, list('p'))] = 'w'
    # Teefelder (Heckenreihen), Hoefe unten
    for (x0, y0, x1, y1) in ((26, 64, 43, 81), (49, 64, 67, 81), (72, 64, 83, 80)):
        R(cls, 't', x0, y0, x1, y1)
    for x in range(21, 91):                                     # unterer Weg folgt der Kueste (3-4 Reihen)
        ys = np.nonzero(insel[:, x])[0]
        if len(ys):
            yu = min(85, ys.max())
            for y in range(yu - 3, yu + 1):
                if cls[y, x] != 'p':
                    cls[y, x] = 'w'
    R(cls, 'p', 4, 76, 21, 87)
    R(cls, 'p', 85, 63, 96, 80)
    R(cls, 'p', 5, 62, 11, 66)
    spalt = (xx >= 68) & (xx <= 73) & (yy >= 2) & (yy <= 26)
    cls[~insel] = 'o'
    hoehe[~insel] = 0
    cls = np.pad(cls, RAND, constant_values='o')
    hoehe = np.pad(hoehe, RAND)
    r = RAND
    lay = {'groesse': [COLS, ROWS], 'rand': RAND, 'klassen': [''.join(z) for z in cls],
           'hoehe': [''.join(str(v) for v in z) for z in hoehe],
           'treppen': [[x0 + r, x1 + r, y0 + r, y1 + r] for (x0, x1, y0, y1) in
                       [[22, 26, 22, 26], [60, 64, 26, 30], [22, 26, 55, 60], [77, 81, 55, 60]]],
           'bruecke': [67 + r, 12 + r, 74 + r, 15 + r],
           'teleporter': [{'x': 7 + r, 'y': 86 + r, 'b': 4, 'h': 1}]}
    # Regel 2: Weg setzt oben und unten genau in Treppenbreite an (Luecken zwischen Wegende und Treppe schliessen)
    k_ = [list(z) for z in lay['klassen']]
    for (x0, x1, y0, y1) in lay['treppen']:
        for richtung, start in ((-1, y0 - 1), (1, y1 + 1)):
            for d_ in range(0, 7):
                y = start + richtung * d_
                if any(k_[y][x] == 'w' for x in range(x0, x1 + 1)) and d_ > 0:
                    for yy in range(min(start, y), max(start, y) + 1):
                        for x in range(x0, x1 + 1):
                            if k_[yy][x] in 'gnf':
                                k_[yy][x] = 'w'
                    break
                if all(k_[y][x] == 'w' for x in range(x0, x1 + 1)):
                    break
            for d_ in range(0, 3):                                    # Wegbreite = Treppenbreite direkt am Fuss/Kopf
                y = start + richtung * d_
                for x in range(x0, x1 + 1):
                    if k_[y][x] in 'gnf':
                        k_[y][x] = 'w'
    for (x0, x1, y0, y1) in lay['treppen']:                         # im Treppenbereich selbst: Weg in voller Breite
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if k_[y][x] in 'gnf':
                    k_[y][x] = 'w'
    import regeln_a02                                               # Regel 6/6b: am Kachelraster biegen (statt Pixel)
    k_ = regeln_a02.wege_schwingen(np.array([list(z) for z in k_]), frei='gn', seed=7, amp=1.6, platz_r=3)
    lay['klassen'] = [''.join(z) for z in k_]
    json.dump(lay, open(os.path.join(KARTE, 'layout.json'), 'w'), indent=0)
    print('Layout', COLS, ROWS)


def kacheln(pfad, n, f=None):
    ks = []
    for v in range(n):
        a = np.array(Image.open(pfad % v).convert('RGB')).astype(np.float32)
        if f is not None:
            a = f(a)
        ks.append(np.clip(a, 0, 255).astype(np.uint8))
    return ks


def flaeche(ks):
    t = np.zeros((ROWS * T, COLS * T, 3), np.uint8)
    for y in range(ROWS):
        for x in range(COLS):
            t[y * T:(y + 1) * T, x * T:(x + 1) * T] = ks[kb.variante(x, y) % len(ks)]
    return t


def grau(a):
    l = a.mean(axis=2, keepdims=True) / 255.0
    lo, hi = np.array([92, 98, 106], np.float32), np.array([196, 200, 206], np.float32)
    return lo + (hi - lo) * np.clip((l - 0.2) / 0.65, 0, 1)


def wolken(frame):
    """Wolkenmeer: helles Lavendel-Weiss, weiche Wolkenbaeusche (Licht oben links), driften langsam."""
    W, Hh = COLS * T, ROWS * T
    a = np.zeros((Hh, W, 3), np.float32)
    a[:] = H('#dfe5ef')
    yy, xx = np.mgrid[0:Hh, 0:W]
    a -= (np.sin(xx / 37.0 + yy / 53.0) * 4)[..., None]
    rs = random.Random(7)
    fr = frame or 0
    for _ in range(170):
        cx, cy = rs.randrange(W), rs.randrange(Hh)
        r = rs.randint(10, 26)
        cx = (cx + fr * 2 * (1 + r % 3)) % W
        x0, x1, y0, y1 = max(0, cx - r), min(W, cx + r), max(0, cy - r), min(Hh, cy + r)
        sub = (((xx[y0:y1, x0:x1] - cx) / r) ** 2 + ((yy[y0:y1, x0:x1] - cy) / (r * 0.6)) ** 2)
        m = sub <= 1
        hell = (xx[y0:y1, x0:x1] - cx) + (yy[y0:y1, x0:x1] - cy) < -r * 0.3
        teil = a[y0:y1, x0:x1]
        teil[m & hell] = H('#f6f8fc')
        teil[m & ~hell & (sub > 0.55)] = H('#cdd5e3')
        teil[m & ~hell & (sub <= 0.55)] = H('#e8edf5')
    return np.clip(a, 0, 255).astype(np.uint8)


WOLKE = {'hl': np.array(H('#ffffff'), np.float32), 'basis': np.array(H('#eef2f9'), np.float32),
         'mitte': np.array(H('#d9e1ee'), np.float32), 'schatten': np.array(H('#bcc7db'), np.float32),
         'kontur': np.array(H('#9aa7c2'), np.float32)}


def bausch(a, cx, cy, r, erlaubt=None, dunkel=0.0):
    """Ein Wolkenbausch (Kugel): Licht oben links, Schattensichel unten rechts, Kontur unten."""
    Hh, W = a.shape[:2]
    x0, x1, y0, y1 = int(max(0, cx - r - 1)), int(min(W, cx + r + 2)), int(max(0, cy - r - 1)), int(min(Hh, cy + r + 2))
    if x0 >= x1 or y0 >= y1:
        return
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    dx, dy = xx - cx, yy - cy
    d2 = dx * dx + dy * dy
    innen = d2 <= r * r
    if erlaubt is not None:
        innen &= erlaubt[y0:y1, x0:x1]
    teil = a[y0:y1, x0:x1].astype(np.float32)
    c = np.zeros_like(teil)
    c[:] = WOLKE['basis']
    c[(dx + 0.3 * r) ** 2 + (dy + 0.3 * r) ** 2 > (0.95 * r) ** 2] = WOLKE['mitte']
    c[(dx + 0.2 * r) ** 2 + (dy + 0.15 * r) ** 2 > (1.05 * r) ** 2] = WOLKE['schatten']
    c[((dx - 0.4 * r) ** 2 + (dy - 0.4 * r) ** 2 > (1.05 * r) ** 2) & (dx + dy < -0.3 * r)] = WOLKE['hl']
    c[(d2 > (r - 1.3) ** 2) & (dy > -0.2 * r)] = WOLKE['kontur']
    if dunkel:
        c = c * (1 - dunkel)
    teil[innen] = c[innen]
    a[y0:y1, x0:x1] = teil.astype(a.dtype)


SCHICHTEN = [  # (Fuellung, Licht, Schatten, Kontur) von hinten nach vorne - Palette der Felsnadel-Wolken
    ('#a2b6d4', '#c8d6ea', '#7c95bb', '#5e78a2'),
    ('#c8d6ea', '#ffffff', '#a2b6d4', '#7c95bb'),
    ('#c8d6ea', '#ffffff', '#a2b6d4', '#7c95bb'),
]


def wolkenschicht(a, kreise, farben, erlaubt=None):
    """Wolkenbank aus vereinigten Kreisen, als EINE Flaeche schattiert: heller Saum oben links, Schattensaum
    unten rechts, feine Kontur unten - wirkt wie zusammenhaengende Cumulus-Waende, nicht wie Blasen."""
    Hh, W = a.shape[:2]
    im = Image.new('L', (W, Hh), 0)
    d = ImageDraw.Draw(im)
    for (cx, cy, r) in kreise:
        d.ellipse((cx - r, cy - r * 0.8, cx + r, cy + r * 0.8), fill=255)
    m = np.array(im) > 0
    if erlaubt is not None:
        m &= erlaubt

    def nb(dy, dx):
        z = np.zeros_like(m)
        ys = slice(max(0, dy), Hh + min(0, dy)); yd = slice(max(0, -dy), Hh + min(0, -dy))
        xs = slice(max(0, dx), W + min(0, dx)); xd = slice(max(0, -dx), W + min(0, -dx))
        z[yd, xd] = m[ys, xs]
        return z
    fu, li, sc, ko = [np.array(H(c), np.uint8) for c in farben]
    a[m] = fu
    a[m & ~nb(-3, -3)] = li                     # oben links liegt Luft -> Licht
    a[m & ~nb(5, 4)] = sc                       # unten rechts liegt Luft -> Schatten
    a[m & ~nb(1, 0)] = ko                       # Unterkante


def wolkenmeer(frame):
    """Dichtes Wolkenmeer rund um die Insel: drei Wolkenbaenke hintereinander, driften sanft hin und her."""
    W, Hh = COLS * T, ROWS * T
    a = np.zeros((Hh, W, 3), np.uint8)
    a[:] = H('#a2b6d4')
    fr = frame or 0
    for k, farben in enumerate(SCHICHTEN):
        rs = random.Random(70 + k)
        dx = 3 * math.sin(2 * math.pi * fr / N_FRAMES + k * 2.1)
        kreise = []
        y = -10 + k * 9
        while y < Hh + 30:
            x = rs.randrange(-60, 0)
            while x < W + 40:
                n = rs.randint(3, 7)                # Wolkenbank: Kette von Baeuschen, Mitte hoeher
                for i in range(n):
                    r = rs.randint(12, 20) + int(8 * math.sin(math.pi * (i + 0.5) / n))
                    kreise.append((x + dx, y - int(6 * math.sin(math.pi * (i + 0.5) / n)) + rs.randint(-3, 3), r))
                    x += int(r * 1.1)
                x += rs.randint(20, 60) + k * 45
            y += 26 + k * 9
        wolkenschicht(a, kreise, farben)
    return a


def wolken_vorne(a, insel_hart, punkte, frame):
    """Wolkenbank vor dem Fuss der Felswaende: die Insel schwebt im Wolkenmeer."""
    rs = random.Random(31)
    dx = 2 * math.sin(2 * math.pi * (frame or 0) / N_FRAMES + 1.3)
    kreise = [(x + rs.randint(-6, 6) + dx, y + rs.randint(-4, 4), rs.randint(11, 19)) for (x, y) in punkte]
    wolkenschicht(a, kreise, SCHICHTEN[2], ~insel_hart)


def teefeld(a, m, frame):
    """Teestraeucher in Reihen: runde, dunkelgruene Buesche mit hellen Blattspitzen, Erdgassen dazwischen."""
    Hh, W = m.shape
    G = [H(c) for c in ('#1e4a2c', '#2c6438', '#3e7e44', '#56984e', '#78b45e', '#9ccc72')]
    ys, xs = np.nonzero(m)
    for y in range(ys.min(), ys.max() + 1):
        reihe = (y - ys.min()) % 16
        for x in np.nonzero(m[y])[0]:
            if reihe >= 12:
                a[y, x] = H('#8a6a46') if reihe < 14 else H('#6e5236')                # Gasse
                continue
            k = (x + (8 if ((y - ys.min()) // 16) % 2 else 0)) % 8
            r = math.hypot(k - 3.5, reihe - 5.5)
            licht = (k - 3.5) + (reihe - 5.5) < -2
            c = G[4] if licht else G[2] if r < 3.2 else G[1]
            if reihe == 11:
                c = G[0]
            if (x * 7 + y * 11) % 31 == 0 and licht:
                c = G[5]
            a[y, x] = c


AZUR_ZAUN = ((0x10, 0x22, 0x44), [(0x1c, 0x4a, 0x8c), (0x2a, 0x6a, 0xb8), (0x46, 0x8e, 0xd8), (0x8c, 0xc4, 0xf2)],
             (0xd8, 0xa8, 0x3c))


def roter_zaun(img, stuecke, palette=None):
    """Roter Holzzaun (Schreinstil) mit dunkler Kontur: Pfosten mit Kappe je Kachel, zwei Querlatten.
    stuecke: (x0, x1, y, 'h') waagerecht oder (x, y0, y1, 'v') senkrecht (von oben gesehen)."""
    px = img.load()
    K = (0x3a, 0x10, 0x10)
    ROT = [(0x7a, 0x1c, 0x1c), (0xa8, 0x2a, 0x26), (0xd0, 0x3e, 0x34), (0xec, 0x66, 0x52)]
    KAPPE = (0x2a, 0x2e, 0x36)
    if palette:
        K, ROT, KAPPE = palette
    W, Hh = img.size

    def p(x, y, c):
        if 0 <= x < W and 0 <= y < Hh:
            px[x, y] = c + (255,)

    def sch(x, y, f=0.72):
        if 0 <= x < W and 0 <= y < Hh:
            r, g, b, a = px[x, y]
            px[x, y] = (int(r * f), int(g * f), int(b * f), a)

    def pfosten(x, yb, h=14):
        for y in range(yb - h, yb + 1):
            for dx in range(-2, 3):
                p(x + dx, y, K if abs(dx) == 2 else ROT[3] if dx == -1 else ROT[2] if dx == 0 else ROT[1])
        for dx in range(-3, 4):
            p(x + dx, yb - h - 1, K); p(x + dx, yb - h - 2, KAPPE)
        for dx in range(0, 5):
            sch(x + dx, yb + 1); sch(x + dx + 1, yb + 2, 0.84)

    for st in stuecke:
        if st[3] == 'h':
            x0, x1, ty, _ = st
            yb = ty * T + 13
            for X in range(x0 * T + 8, x1 * T + 8):
                for yl in (yb - 10, yb - 5):
                    p(X, yl - 1, K); p(X, yl, ROT[3]); p(X, yl + 1, ROT[2]); p(X, yl + 2, ROT[1]); p(X, yl + 3, K)
                    sch(X + 1, yl + 5, 0.8)
            for tx in range(x0, x1 + 1):
                pfosten(tx * T + 8, yb)
        else:
            tx, y0, y1, _ = st
            X = tx * T + 8
            for y in range(y0 * T + 13, y1 * T + 13):
                for dx in range(-2, 3):
                    p(X + dx, y, K if abs(dx) == 2 else ROT[2] if dx < 1 else ROT[1])
                sch(X + 3, y); sch(X + 4, y, 0.85)
            for ty in range(y0, y1 + 1):
                pfosten(X, ty * T + 13)


def _rauschen(Hh, W, zelle, seed):
    rs = np.random.RandomState(seed)
    n = rs.rand(Hh // zelle + 3, W // zelle + 3)
    im = Image.fromarray((n * 255).astype(np.uint8)).resize(((W // zelle + 3) * zelle, (Hh // zelle + 3) * zelle), Image.BICUBIC)
    return np.array(im)[:Hh, :W].astype(np.float32) / 255.0


def bergboden(frame):
    """Bergmassiv am Kartenrand (von oben): dunkler Fels mit weichen Schneefeldern, Felsbrocken-Struktur
    und ziehenden, weichen Nebelfeldern."""
    W, Hh = COLS * T, ROWS * T
    fels = flaeche(kacheln(os.path.join(ROOT, 'assets', 'karte05', 'basis', 'r_%d.png'), 5,
                           lambda x: x * np.array([0.7, 0.72, 0.78])))
    a = fels.astype(np.float32)
    schnee = (_rauschen(Hh, W, 20, 3) * 0.6 + _rauschen(Hh, W, 6, 4) * 0.4) > 0.68
    a[schnee] = a[schnee] * 0.45 + np.array(H('#dfe6ee')) * 0.55
    kante = schnee & ~(np.roll(schnee, 1, 0) & np.roll(schnee, -1, 0))
    a[kante] = a[kante] * 0.8
    fr = frame or 0
    n = np.roll(_rauschen(Hh, W, 96, 5), fr * 4, axis=1)
    f = np.clip((n - 0.45) * 0.9, 0, 0.35)[..., None]
    a = a * (1 - f) + NEBEL * f
    return np.clip(a, 0, 255).astype(np.uint8)


def digitalfeld(a, m, frame):
    """Digitale Felder: dunkler Datenboden mit feinem Cyan-Gitter, unregelmaessige Beetreihen (Furchen mit
    leuchtender Kante); die Pflanzen kommen als Objekte."""
    rs = random.Random(9)
    ys, xs = np.nonzero(m)
    a[m] = H('#2a3040')
    gitter = m & (((np.arange(a.shape[1])[None, :] % 8) == 0) | ((np.arange(a.shape[0])[:, None] % 8) == 0))
    a[gitter] = H('#33405a')
    pfad = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'maps', 'karte07', 'feldreihen.json')
    reihen = json.load(open(pfad)) if os.path.exists(pfad) else []
    for (xa, xe, yf) in reihen:                          # Beetreihe unter den Pflanzen (Fusslinie yf)
        dy = rs.randint(-1, 1)
        for x in range(xa, xe):
            y = yf + dy
            if not (0 <= y - 4 and y + 2 < a.shape[0] and m[y, x]):
                continue
            a[y - 4, x] = H('#4be0e8') if (x + (frame or 0) * 3) % 24 < 2 else H('#2c8a9a')
            a[y - 3, x] = H('#6a5438'); a[y - 2, x] = H('#5a4630'); a[y - 1, x] = H('#4a3a28')
            a[y, x] = H('#3a2e22'); a[y + 1, x] = H('#30261c'); a[y + 2, x] = H('#262836')


def beete(a, frame):
    """Hochbeete: Holzrahmen (Licht oben links), dunkle, gelockerte Erde mit Furchenreihen, Schatten rechts unten."""
    pfad = os.path.join(KARTE, 'beete.json')
    if not os.path.exists(pfad):
        return
    HOLZ = [H('#3a2414'), H('#6a4426'), H('#8a5c34'), H('#a87444'), H('#c48e58')]
    ERDE = [H('#2e2018'), H('#3e2c1e'), H('#4c3624'), H('#5c442e'), H('#6c5238')]
    for (x0, x1, y0, y1) in json.load(open(pfad)):
        # Schatten
        a[y1:y1 + 3, x0 + 3:x1 + 3] = (a[y1:y1 + 3, x0 + 3:x1 + 3] * 0.72).astype(np.uint8)
        a[y0 + 3:y1, x1:x1 + 3] = (a[y0 + 3:y1, x1:x1 + 3] * 0.72).astype(np.uint8)
        rs = random.Random(x0 * 7 + y0)
        for y in range(y0, y1):
            for x in range(x0, x1):
                dy, dx = y - y0, x - x0
                rand = dy < 3 or dy >= y1 - y0 - 3 or dx < 3 or dx >= x1 - x0 - 3
                if rand:
                    aussen = dy == 0 or dx == 0 or dy == y1 - y0 - 1 or dx == x1 - x0 - 1
                    if aussen:
                        c = HOLZ[0]
                    elif dy == 1 or dx == 1:
                        c = HOLZ[4] if dy == 1 else HOLZ[3]
                    elif dy >= y1 - y0 - 3 or dx >= x1 - x0 - 3:
                        c = HOLZ[1]
                    else:
                        c = HOLZ[2]
                    if not aussen and dy in (1, 2, y1 - y0 - 3, y1 - y0 - 2) and (x - x0) % 23 == 22:
                        c = HOLZ[0]                                   # Brettfuge
                else:
                    f = (dy - 3) % 6                                  # Furchen: Kamm hell, Tal dunkel
                    c = ERDE[[3, 4, 3, 2, 1, 2][f]]
                    if rs.random() < 0.05:
                        c = ERDE[0] if rs.random() < 0.5 else ERDE[4]
                    if dy == 3 or dx == 3:
                        c = ERDE[0]                                   # Innenschatten am Rahmen
                a[y, x] = c


def treppe07(img, xa, xb, y_top, y_bot, seed=3):
    """Steintreppe in der Wandoeffnung: Wangen aus denselben Steinbloecken wie die Felswand (mit Deckstein),
    Stufen als Steinplatten mit versetzten Fugen, helle Trittkante, dunkle Setzstufe, Schlagschatten der linken
    Wange und unter jeder Trittkante, Antrittsplatte unten."""
    rs = random.Random(seed)
    px = img.load()
    W, Hh = img.size
    P = [tuple(int(v) for v in H(c)) for c in ('#1f232b', '#2e333c', '#444b57', '#5c6472', '#77808e', '#959dab', '#b6bdc8', '#d6dbe2')]

    def setz(x, y, c):
        if 0 <= x < W and 0 <= y < Hh:
            px[x, y] = c + (255,)

    def dunkel(x, y, f):
        if 0 <= x < W and 0 <= y < Hh:
            r, g, b, a_ = px[x, y]
            px[x, y] = (int(r * f), int(g * f), int(b * f), a_)
    wange = 12
    # Stufen
    i0, i1 = xa + wange, xb - wange
    for x in range(i0, i1):                                       # obere Austrittsplatte (deckt die Kante ab)
        for dy, c in ((-9, P[5]), (-8, P[7]), (-7, P[6]), (-6, P[6]), (-5, P[6]), (-4, P[5]), (-3, P[2])):
            if (x - i0) % 22 == 21 and -8 < dy < -3:
                c = P[3]
            setz(x, y_top + dy, c)
    stufe = 8
    y, n = y_top - 2, 0
    while y < y_bot:
        ton = max(0, min(2, 2 - n // 2))                          # oben etwas heller
        fugen = set()
        x = i0 + (n % 2) * 9 + rs.randint(0, 4)
        while x < i1:
            fugen.add(x)
            x += rs.randint(14, 22)
        for x in range(i0, i1):
            for dy in range(stufe):
                yy = y + dy
                if yy > y_bot:
                    break
                if dy == 0:
                    c = P[7 - (ton == 0)]                          # Trittkante (Licht)
                elif dy < 3:
                    c = P[6 - (ton == 0)]                          # Trittflaeche
                elif dy == 3:
                    c = P[2]                                       # Schatten unter der Kante
                elif dy < stufe - 1:
                    c = P[4 - (ton < 2)] if (x + yy * 3) % 13 else P[3]   # Setzstufe mit Koernung
                else:
                    c = P[1]                                       # Fuge
                if x in fugen and 0 < dy < stufe - 1:
                    c = P[2] if dy < 3 else P[1]
                if x - 1 in fugen and 0 < dy < 3:
                    c = P[7]                                       # Lichtkante rechts der Fuge
                setz(x, yy, c)
        y += stufe
        n += 1
    # Antrittsplatte
    for x in range(i0 - 2, i1 + 2):
        for dy, c in ((0, P[6]), (1, P[5]), (2, P[4]), (3, P[1])):
            setz(x, y_bot + dy, c)
    # Wangen aus Steinbloecken
    for (w0, hell) in ((xa, True), (xb - wange, False)):
        yb = y_top - 6
        while yb < y_bot + 4:
            bh = rs.randint(6, 9)
            for yy in range(yb, min(y_bot + 4, yb + bh)):
                for x in range(w0, w0 + wange):
                    k, dy = x - w0, yy - yb
                    c = P[5] if hell else P[3]
                    if k == 0 or k == wange - 1:
                        c = P[0]
                    elif dy == 0:
                        c = P[7] if hell else P[5]
                    elif dy == bh - 1:
                        c = P[1]
                    elif k == 1:
                        c = P[6] if hell else P[4]
                    elif k == wange - 2:
                        c = P[3] if hell else P[2]
                    setz(x, yy, c)
            yb += bh
        for x in range(w0, w0 + wange):                           # Deckstein
            for dy, c in ((-8, P[0]), (-7, P[7]), (-6, P[6])):
                setz(x, y_top + dy, c)
    # Schlagschatten: linke Wange auf die Stufen, rechte Wange auf den Boden daneben
    for yy in range(y_top - 2, y_bot + 1):
        for k, f in ((0, 0.6), (1, 0.72), (2, 0.85)):
            dunkel(i0 + k, yy, f)
    for x in range(xa + 3, xb + 3):
        for dy, f in ((4, 0.75), (5, 0.85)):
            if not (i0 - 2 <= x < i1 + 2):
                dunkel(x, y_bot + dy, f)


def azulhof(a, x0, y0, x1, y1, mitte, weg_x0=None):
    """Reich des azurblauen Drachen: hellblaue Steinplatten im Verband (Licht oben links), weisser Marmorweg mit
    Goldkanten vom Westeingang zum Altar, goldenes Wolkenring-Emblem um den Raeucherkessel."""
    P = {'f1': H('#a6bedd'), 'f2': H('#b4cae6'), 'f3': H('#98b2d4'), 'fuge': H('#6a86b0'), 'licht': H('#d4e2f2'),
         'm1': H('#e8eef6'), 'm2': H('#dbe4ef'), 'mf': H('#b4c4d8'), 'gold': H('#d8a83c'), 'gold2': H('#f2d27a'),
         'gold0': H('#8a6420')}
    rs = random.Random(12)
    for ty in range(y0, y1, T):
        for tx in range(x0 - (8 if (ty // T) % 2 else 0), x1, T):
            ton = rs.choice(('f1', 'f1', 'f2', 'f3'))
            for y in range(ty, min(y1, ty + T)):
                for x in range(max(x0, tx), min(x1, tx + T)):
                    dy, dx = y - ty, x - tx
                    c = P[ton]
                    if dy == T - 1 or dx == T - 1:
                        c = P['fuge']
                    elif dy == 0 or dx == 0:
                        c = P['licht']
                    a[y, x] = c
    # Marmorweg (waagerecht, Eingang West -> Altar)
    wy0, wy1, wx1 = mitte[1] - 28, mitte[1] + 28, mitte[0]
    wx0 = weg_x0 if weg_x0 is not None else x0
    for y in range(wy0, wy1):
        for x in range(wx0, wx1):
            c = P['m1'] if ((x - x0) // 24 + (y - wy0) // 16) % 2 == 0 else P['m2']
            if (x - x0) % 24 == 23 or (y - wy0) % 16 == 15:
                c = P['mf']
            if y in (wy0, wy1 - 1):
                c = P['gold0'] if y == wy1 - 1 else P['gold2']
            elif y in (wy0 + 1, wy1 - 2):
                c = P['gold']
            a[y, x] = c
    a[wy1:wy1 + 3, wx0:wx1] = (a[wy1:wy1 + 3, wx0:wx1] * 0.8).astype(np.uint8)


def emblem(a, cx, cy, r):
    """Goldener Wolkenring (Bodenintarsie): Ring mit sechs Wolkenwirbeln, Licht oben links."""
    G = [H('#8a6420'), H('#d8a83c'), H('#f2d27a')]
    yy, xx = np.mgrid[cy - r - 8:cy + r + 9, cx - r - 8:cx + r + 9]
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    teil = a[cy - r - 8:cy + r + 9, cx - r - 8:cx + r + 9]
    ring = (d >= r - 5) & (d <= r)
    teil[ring] = G[1]
    teil[ring & ((d > r - 1) | (d < r - 4))] = G[0]
    teil[ring & (d > r - 3) & (d < r - 1.5) & (xx + yy < cx + cy)] = G[2]
    for k in range(6):
        w = k * math.pi / 3
        wx, wy = cx + r * math.cos(w), cy + r * math.sin(w)
        dw = np.sqrt((xx - wx) ** 2 + (yy - wy) ** 2)
        wirbel = (dw <= 8) & (dw >= 4)
        teil[wirbel] = G[1]
        teil[wirbel & ((dw > 7) | (dw < 5))] = G[0]
        teil[(dw < 2.5)] = G[2]
    innen = d <= r - 6
    teil[innen & ((np.floor(d / 4) % 2) == 0) & (d > r - 10)] = (teil[innen & ((np.floor(d / 4) % 2) == 0) & (d > r - 10)] * 0.9).astype(np.uint8)


def drachenbruecke(img, x0, x1, y0, y1, frame=None, spalt=None):
    """Drachenbruecke (Nutzer: ueberarbeitet, sauber eingefuegt): Marmordeck ueber der Wolkenluecke, von oben gesehen.
    Hinten und vorne je eine niedrige Bruestung (Marmorpfosten mit Goldkappe, Handlauf), an den vier Ecken ueber
    den Kanten der Luecke hohe Pfeiler mit Bernsteinkugel; vorne ueber der Luecke eine azurblaue Stirnseite mit
    flachem Bogen und Goldkante, Schatten nur auf die Wolken darunter. An Land laeuft das Deck flach als
    Marmorpodest aus (ohne Bruestung)."""
    px = img.load()
    W, Hh = img.size
    M = [(0x8a, 0x98, 0xb0), (0xb8, 0xc4, 0xd6), (0xd8, 0xe0, 0xec), (0xee, 0xf2, 0xf8), (0xff, 0xff, 0xff)]
    A = [(0x10, 0x22, 0x44), (0x1c, 0x4a, 0x8c), (0x2a, 0x6a, 0xb8), (0x46, 0x8e, 0xd8), (0x8c, 0xc4, 0xf2)]
    G = [(0x6a, 0x48, 0x14), (0xa8, 0x7a, 0x26), (0xd8, 0xa8, 0x3c), (0xf2, 0xd2, 0x7a), (0xff, 0xf2, 0xc0)]
    K = (0x2c, 0x34, 0x48)
    fr = frame or 0
    ga, gb = spalt if spalt else (x0, x1)

    def p(x, y, c):
        if 0 <= x < W and 0 <= y < Hh:
            px[x, y] = tuple(c) + (255,)

    def d(x, y, f):
        if 0 <= x < W and 0 <= y < Hh:
            r, g, b, a = px[x, y]
            px[x, y] = (int(r * f), int(g * f), int(b * f), a)
    # 1) Stirnseite vorne ueber der Luecke (flacher Bogen) + Schatten auf die Wolken
    tiefe = 16
    for x in range(ga, gb):
        t = (x - ga) / max(1, gb - ga - 1)
        bogen = int(round(tiefe - 6 * max(0.0, 1 - ((t - 0.5) / 0.45) ** 2) ** 0.5))
        for dy in range(bogen):
            y = y1 + dy
            if dy == 0:
                c = G[3]
            elif dy == 1:
                c = G[1]
            elif dy == bogen - 1:
                c = K
            elif dy == bogen - 2:
                c = G[2]
            else:
                c = A[2] if ((x - ga) // 4 + dy // 3) % 2 else A[1]
            p(x, y, c)
        for k, f in ((0, 0.7), (1, 0.8), (2, 0.9)):
            d(x + 2, y1 + bogen + k, f)
    # 2) Deck (ganze Laenge): Marmorplatten 16x8 versetzt, azurblauer Laeufer mit Goldborte
    mitte = (y0 + y1) // 2
    for y in range(y0, y1):
        for x in range(x0, x1):
            r = (y - y0) // 8
            c = M[3] if ((x - x0 + (r % 2) * 8) // 16) % 2 else M[2]
            if (y - y0) % 8 == 7 or (x - x0 + (r % 2) * 8) % 16 == 15:
                c = M[1]
            if abs(y - mitte) <= 6:
                c = A[2] if ((x // 6) + (y // 3)) % 2 else A[1]
                if abs(y - mitte) == 6:
                    c = G[2]
                elif abs(y - mitte) == 5:
                    c = G[0]
            p(x, y, c)
    for x in range(x0, x1):                                            # Kontaktkanten des Podests an Land
        p(x, y1 - 1, M[0])
        if not (ga <= x < gb):
            d(x + 1, y1, 0.8); d(x + 1, y1 + 1, 0.9)
    for y in range(y0, y1):
        p(x0, y, M[1]); p(x1 - 1, y, M[0])

    # 3) Bruestungen hinten (oben) und vorne (unten) nur ueber der Luecke: Pfosten alle 12 px, Handlauf
    def bruestung(yb, h):
        for x in range(ga, gb):
            p(x, yb - h, G[3]); p(x, yb - h + 1, G[1])                    # Handlauf
            p(x, yb, M[0])
            if (x - ga) % 12 < 3:
                for y in range(yb - h + 2, yb + 1):
                    p(x, y, M[3] if (x - ga) % 12 == 0 else M[2] if (x - ga) % 12 == 1 else M[1])
            else:
                for y in range(yb - h + 2, yb):
                    p(x, y, A[3] if y == yb - h + 2 else A[2])
    bruestung(y0 + 6, 8)
    bruestung(y1 - 1, 8)

    # 4) Eckpfeiler ueber den Kanten der Luecke mit pulsierender Bernsteinkugel
    puls = (0, 1, 2, 1)[fr % 4]
    for xc in (ga - 5, gb + 4):                                       # Pfeiler stehen an Land, direkt an der Kante
        for (yb, h) in ((y0 + 8, 20), (y1 + 1, 22)):
            for y in range(yb - h, yb):
                for x in range(xc - 4, xc + 5):
                    c = M[3] if x < xc - 1 else M[2] if x < xc + 2 else M[1]
                    if x in (xc - 4, xc + 4):
                        c = M[0]
                    p(x, y, c)
            for x in range(xc - 5, xc + 6):
                p(x, yb - h, G[2]); p(x, yb - h + 1, G[1])
            cy = yb - h - 4
            for yy in range(cy - 3, cy + 4):
                for xx in range(xc - 3, xc + 4):
                    if (xx - xc) ** 2 + (yy - cy) ** 2 <= 10:
                        hell = (xx - xc) + (yy - cy) < -1
                        p(xx, yy, G[4] if hell and puls else G[3] if hell else G[2])
            for k in range(3):
                d(xc + 5 + k, yb - 1, 0.8)



def steinbruecke(img, x0, x1, y0, y1):
    """Steinbruecke: Steinplatten-Deck im Verband, niedrige Bruestung mit Pfeilern oben und unten, Schatten."""
    px = img.load()
    P = [(0x3a, 0x3e, 0x48), (0x56, 0x5c, 0x68), (0x74, 0x7a, 0x86), (0x94, 0x9a, 0xa6), (0xb4, 0xb9, 0xc2), (0xd2, 0xd6, 0xdc)]
    W, Hh = img.size
    for x in range(x0, x1):
        for y in range(y1 + 1, y1 + 7):
            if 0 <= y < Hh:
                r, g, b, a_ = px[x, y]
                f = 0.6 + (y - y1) * 0.06
                px[x, y] = (int(r * f), int(g * f), int(b * f), a_)
    for y in range(y0 + 4, y1 - 3):
        for x in range(x0, x1):
            reihe = (y - y0) // 6
            k = (x - x0 + (5 if reihe % 2 else 0)) % 11
            c = P[3] if k not in (0, 10) else P[1]
            if (y - y0) % 6 == 0:
                c = P[4]
            elif (y - y0) % 6 == 5:
                c = P[1]
            px[x, y] = c + (255,)
    for yb in (y0, y1 - 4):
        for x in range(x0 - 2, x1 + 2):
            for d, c in enumerate((P[0], P[5], P[4], P[2], P[0])):
                if 0 <= yb + d < Hh:
                    px[x, yb + d] = c + (255,)
        for pxl in list(range(x0 - 2, x1 - 4, 18)) + [x1 - 4]:
            for x in range(pxl, pxl + 6):
                for y in range(yb - 6, yb + 5):
                    c = P[0] if x in (pxl, pxl + 5) or y == yb - 6 else P[5] if x == pxl + 1 else P[3]
                    px[x, y] = c + (255,)


def bauen(frame=None, speichern=True):
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cls = lay['klassen']
    hoehe = np.array([[int(c) for c in r] for r in lay['hoehe']])
    Wp, Hp = COLS * T, ROWS * T
    a = wolkenmeer(frame)
    insel_hart = zell_maske([''.join('1' if 1 <= v <= 3 else '0' for v in r) for r in hoehe], '1', COLS, ROWS) > 0
    insel = insel_hart.copy()                                   # Inselkante genau am 16er-Raster (Nutzer)
    gras = flaeche(kacheln(os.path.join(ROOT, 'assets', 'basis', 'gras_%d.png'), 5))
    a[insel] = gras[insel]
    schnee = flaeche(kacheln(os.path.join(ROOT, 'assets', 'karte05', 'basis', 's_%d.png'), 5))
    fels = flaeche(kacheln(os.path.join(ROOT, 'assets', 'karte05', 'basis', 'r_%d.png'), 5))
    weg = flaeche(kacheln(os.path.join(ROOT, 'assets', 'karte04', 'basis', 'w_%d.png'), 5))
    pflaster = flaeche(kacheln(os.path.join(ROOT, 'assets', 'karte03', 'basis', 'kies_%d.png'), 5, grau))
    def weg_biegen(roh):
        """Regel 6: Wege nie nur gerade - die Wegmaske wird sanft verbogen (Boegen, Versatz); an Treppen, Bruecke,
        Teleporter und Plaetzen bleibt sie fest, damit die Anschluesse stimmen."""
        yy, xx = np.mgrid[0:Hp, 0:Wp]
        dx = 9 * np.sin(2 * np.pi * yy / 176.0 + 1.0) + 5 * np.sin(2 * np.pi * yy / 92.0 + 2.4)
        dy = 9 * np.sin(2 * np.pi * xx / 168.0 + 0.3) + 5 * np.sin(2 * np.pi * xx / 86.0 + 1.7)
        fest = np.zeros((Hp, Wp), bool)
        for (x0, x1, y0, y1) in lay['treppen']:
            fest[max(0, (y0 - 2) * T):(y1 + 3) * T, max(0, (x0 - 1) * T):(x1 + 2) * T] = True
        bx0, by0, bx1, by1 = lay['bruecke']
        fest[(by0 - 1) * T:(by1 + 2) * T, (bx0 - 3) * T:(bx1 + 4) * T] = True
        for tp in lay['teleporter']:
            fest[(tp['y'] - 3) * T:(tp['y'] + tp['h'] + 2) * T, (tp['x'] - 2) * T:(tp['x'] + tp['b'] + 2) * T] = True
        f = np.array(Image.fromarray((~fest * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(24))) / 255.0
        sy = np.clip((yy + dy * f).round().astype(int), 0, Hp - 1)
        sx = np.clip((xx + dx * f).round().astype(int), 0, Wp - 1)
        return roh[sy, sx]
    for art, tex, blur, rausch, seed in (('n', schnee, 5, 0.45, 3), ('f', fels, 4, 0.4, 4), ('r', pflaster, 2.5, 0.2, 5),
                                         ('w', weg, 5, 0, 6)):   # Regel 6b: Weg 45-Grad-Kanten
        roh_ = zell_maske(cls, art, COLS, ROWS)
        # (frueher: Pixel-Verbiegung weg_biegen - jetzt am Kachelraster im Layout, Regel 6b)
        m = weich(roh_, blur, rausch, seed) & insel
        if art == 'w':                                              # Nutzer: Uebergang Weg -> Schnee/Rasen (6 px Saum)
            ringe, cur = [], m.copy()
            for _ in range(6):
                nb = cur | np.roll(cur, 1, 0) | np.roll(cur, -1, 0) | np.roll(cur, 1, 1) | np.roll(cur, -1, 1)
                ringe.append(nb & ~cur & insel); cur = nb
            rr = random.Random(77)
            for i, ring in enumerate(ringe):                         # innen viel Erde, aussen wenig + Krumen
                anteil = (0.55, 0.45, 0.32, 0.2, 0.1, 0.05)[i]
                a[ring] = (a[ring] * (1 - anteil) + tex[ring] * anteil).astype(np.uint8)
                if i >= 2:                                          # leichter Schatten/Feuchte im Boden
                    a[ring] = (a[ring] * 0.96).astype(np.uint8)
                ys, xs = np.nonzero(ring)
                for _ in range(len(ys) // (10 + 8 * i)):            # Erdkrumen, nach aussen seltener
                    j = rr.randrange(len(ys))
                    a[ys[j], xs[j]] = tex[ys[j], xs[j]]
        a[m] = tex[m]
    pm = weich(zell_maske(cls, 'p', COLS, ROWS), 1.2, 0, 7) & insel
    a[pm] = pflaster[pm]
    rand = pm & ~(np.roll(pm, 1, 0) & np.roll(pm, -1, 0) & np.roll(pm, 1, 1) & np.roll(pm, -1, 1))
    a[rand] = H('#4a505a')
    r_ = RAND
    azulhof(a, (77 + r_) * T, (4 + r_) * T, (97 + r_) * T, (25 + r_) * T, ((91 + r_) * T, (14 + r_) * T), weg_x0=(74 + r_) * T)
    emblem(a, (87 + r_) * T, (21 + r_) * T + 2, 34)
    beete(a, frame)
    # Hoehenkanten: Insel -> Wolken (tiefe Felsfront), Stufen 1->2->3 mit Treppen
    m1 = insel
    m2 = zell_maske([''.join('1' if 2 <= v <= 3 else '0' for v in r) for r in hoehe], '1', COLS, ROWS) > 0   # am Raster
    m3 = zell_maske([''.join('1' if v == 3 else '0' for v in r) for r in hoehe], '1', COLS, ROWS) > 0   # am Raster
    frei = np.zeros((Hp, Wp), bool)
    treppen = []
    for (x0, x1, y0, y1) in lay['treppen']:
        frei[y0 * T:(y1 + 1) * T, x0 * T - 6:(x1 + 1) * T + 6] = True
        treppen.append((x0, x1, y0, y1))
    k4.hoehenkanten(a, m3, 'wolkenfels', 48, 1, LIPPE_SCHNEE, frei, 13, berg=True)
    k4.hoehenkanten(a, m2, 'wolkenfels', 48, 1, LIPPE_GRAS, frei, 12, berg=True)
    k4.hoehenkanten(a, insel, 'wolkenfels', 64, 1, LIPPE_SCHNEE, np.zeros((Hp, Wp), bool), 11, berg=True)
    # Wolken vor dem Wandfuss (Sueden) und an den Seiten
    unten = []
    for x in range(0, Wp, 14):
        ys = np.nonzero(insel[:, x])[0]
        if len(ys):
            for y in ys:
                if y + 1 < Hp and not insel[y + 1, x] and (y + 70 >= Hp or not insel[y + 70, x]):
                    unten.append((x, y + 62))
    rs_ = random.Random(5)
    for y in range(0, Hp, 22):                     # an den Seiten nur vereinzelte Baeusche
        xs = np.nonzero(insel[y])[0]
        for x in xs:
            if x + 1 < Wp and not insel[y, x + 1] and rs_.random() < 0.45:
                unten.append((x + rs_.randint(10, 22), y))
            if x > 0 and not insel[y, x - 1] and rs_.random() < 0.45:
                unten.append((x - rs_.randint(10, 22), y))
    wolken_vorne(a, insel_hart, unten, frame)
    img = Image.fromarray(a).convert('RGBA')
    alt = bauwerke.S
    bauwerke.S = [H(c) + (255,) for c in k4.FELS['wolkenfels']]
    for (x0, x1, y0, y1) in treppen:
        spalte = (x0 + x1) // 2
        stufe = m3 if any(hoehe[y, spalte] == 3 for y in range(y0, y1 + 1)) else m2
        col = stufe[:, spalte * T + 8]
        kante = [y for y in range(y0 * T, (y1 + 1) * T) if col[y] and not col[min(Hp - 1, y + 1)]]
        if kante:
            ye = kante[0]
            treppe07(img, x0 * T - 6, (x1 + 1) * T + 6, ye + 2, ye + 50, seed=x0 + y0)
    bauwerke.S = alt
    bx0, by0, bx1, by1 = lay['bruecke']
    hz = np.array([[int(c) for c in z] for z in lay['hoehe']])
    luecke = [x for x in range(bx0, bx1 + 1) if hz[(by0 + by1) // 2, x] == 0]     # Wolkenspalt pixelgenau
    ga_, gb_ = luecke[0] * T, (luecke[-1] + 1) * T
    drachenbruecke(img, ga_ - T, gb_ + 8, by0 * T + 4, (by1 + 1) * T - 4, frame, spalt=(ga_, gb_))
    a = np.array(img.convert('RGB'))
    for tp in lay['teleporter']:
        k4.teleporter_zeichnen(a, tp['x'], tp['y'], tp['b'], tp['h'], frame)
    img = Image.fromarray(a).convert('RGBA')
    r = RAND
    zaun_azur = [(a_ + r, b_ + r, c_ + r, d_) for (a_, b_, c_, d_) in [(77, 96, 4, 'h'), (77, 96, 24, 'h'), (96, 4, 24, 'v')]]
    zaun_pal = AZUR_ZAUN[:2] + ((0xd8, 0xa8, 0x3c),)
    roter_zaun(img, zaun_azur, zaun_pal)
    roter_zaun(img, [(a_ + r, b_ + r, c_ + r, d_) for (a_, b_, c_, d_) in
                     [(71, 77, 31, 'h'), (83, 89, 31, 'h'), (96, 63, 80, 'v')]])
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain_basis.png'))
    pf = os.path.join(OBJ, 'platzierung.json')
    if os.path.exists(pf):
        objs = sorted((o for o in json.load(open(pf)) if os.path.exists(os.path.join(OBJ, o['datei']))),
                      key=lambda o: o['y'] + o['fuss'])
        cache = {o['datei']: Image.open(os.path.join(OBJ, o['datei'])).convert('RGBA') for o in objs}
        k4.objekte_zeichnen(img, objs, cache, insel, frame)
        k4.animieren(img, objs, cache, frame or 0)
        roter_zaun(img, zaun_azur, zaun_pal)                         # Schreinzaun liegt ueber den Objekten (Nutzer)
        import karte06_bauen as k6
        k6.animieren_k6(img, objs, cache, frame or 0)
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain.png'))
    print('Karte 07 %dx%d gebaut' % (COLS, ROWS))
    return img


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'layout':
        layout()
    else:
        bauen()
