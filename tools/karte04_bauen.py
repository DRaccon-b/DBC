"""Karte 04 (Gear Savanna): Boden, Hoehenstufen mit Felswaenden, Canyon mit Fluss, Hecken, Bruecke.

  python3 tools/karte04_layout.py    # Raster aus der Vorlage (einmalig)
  python3 tools/karte04_kacheln.py   # Grundkacheln
  python3 tools/karte04_bauen.py     # -> maps/karte04/terrain.png (+ Objekte, falls platziert)

Hoehen: 0 Canyon/Teerbecken, 1 Savanne, 2 Plateau. Waende werden pixelgenau aus den Hoehenmasken
abgeleitet (Ecken gerundet): Front unter jeder Hochkante (Fels aus klippen.wand, umgefaerbt),
Lippe mit ueberhaengendem Gras oben, Seitenraender, Schlagschatten nach rechts unten (Licht oben links).
"""
import json, math, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import karte_bauen as kb
import klippen
import bauwerke

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte04')
BASIS4 = os.path.join(ROOT, 'assets', 'karte04', 'basis')
BASIS1 = os.path.join(ROOT, 'assets', 'basis')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte04')
T = 16
N_FRAMES = 16
H = lambda h: tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))

FELS = {   # 7 Toene dunkel -> hell (ersetzt klippen.SCHIEFER)
    'sandstein': ['#3e3026', '#5a4634', '#765c44', '#927456', '#ac8e6c', '#c8ab86', '#e0c8a4'],
    'erde':      ['#4a3424', '#6a4c34', '#8a6646', '#a8825a', '#c09c72', '#d6b68c', '#e8d0a8'],
    'schiefer':  ['#24222a', '#36343e', '#4a4854', '#5e5c6a', '#767482', '#908e9c', '#acaab6'],
}
LIPPE = {   # ueberhaengender Rand oben: Grastoene der oberen Flaeche (dunkel -> hell)
    'g': ['#4e5e30', '#66783e', '#82924e', '#9aa95e', '#afbd70', '#c2ce82'],
    's': ['#5e4c24', '#7a6430', '#957c3e', '#ad944e', '#c4aa60', '#d6bc70'],
    'a': ['#3e3e38', '#55554c', '#69695e', '#7c7c70', '#8e8e80', '#a4a496'],
}
HECKE = ['#1e2a18', '#2c3e22', '#3a522c', '#4a6634', '#5c7c3e', '#73944c', '#8cac5c']


def lade_layout():
    return json.load(open(os.path.join(KARTE, 'layout.json')))


def textur(cls, art, cols, rows):
    t = np.zeros((rows * T, cols * T, 3), np.uint8)
    ks = [np.array(Image.open(os.path.join(BASIS4, '%s_%d.png' % (art, v))).convert('RGB')) for v in range(5)]
    for y in range(rows):
        for x in range(cols):
            t[y * T:(y + 1) * T, x * T:(x + 1) * T] = ks[kb.variante(x, y)]
    return t


def zell_maske(cls, arten, cols, rows):
    m = np.zeros((rows * T, cols * T), np.float32)
    for y in range(rows):
        for x in range(cols):
            if cls[y][x] in arten:
                m[y * T:(y + 1) * T, x * T:(x + 1) * T] = 1
    return m


def weich(m, blur, rausch, seed, schwelle=0.5):
    a = np.array(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(blur))) / 255.0
    if rausch:
        h, w = a.shape
        n = np.random.RandomState(seed).rand(h // 5 + 2, w // 5 + 2)
        n = np.array(Image.fromarray((n * 255).astype(np.uint8)).resize((w + 10, h + 10), Image.BICUBIC))[:h, :w] / 255.0
        a = a + (n - 0.5) * rausch
    return a > schwelle


def gerundet(m, r=2.5):
    return weich(m, r, 0, 0)


def fels_textur(name, breite, hoehe, seed):
    rnd = random.Random(seed)
    w = klippen.wand(breite, hoehe, rnd, rune_chance=0.0)
    q = [klippen.rgb(c)[:3] for c in klippen.SCHIEFER]
    z = [H(c) for c in FELS[name]]
    a = np.array(w.convert('RGB'))
    out = a.copy()
    for i, c in enumerate(q):
        out[(a == c).all(axis=2)] = z[i]
    return out


def dunkeln(a, m, f):
    a[m] = (a[m].astype(np.float32) * f).astype(np.uint8)


def hoehenkanten(a, hoch, fels, front, seite, lippe_pal, frei, seed, treppen=(), min_breite=10, berg=False, filtern=False):
    """a: RGB-Bild. hoch: Pixelmaske der hoeheren Ebene. Waende werden in die tiefere Flaeche gezeichnet:
    Front (Sueden) front px hoch, Seitenwaende seite px breit (Westwand im Licht, Ostwand im Schatten),
    Lippe mit Ueberhang, Kontaktschatten. frei: Pixelmaske ohne Kanten (Rampen). treppen: Liste (x0, x1) in px."""
    Hh, W = hoch.shape
    tex = fels_textur(fels, W, front + 2, seed)
    stex = fels_textur(fels, Hh, seite + 2, seed + 1)          # [k, y]
    F = [np.array(H(c)) for c in FELS[fels]]
    Lp = [np.array(H(c)) for c in lippe_pal]
    wand = np.zeros_like(hoch)
    # Seitenwaende (zuerst, die Fronten liegen davor): gestapelte Felsbloecke, Westwand im Licht,
    # Ostwand im Schatten, aussen dunkle Kante, oben ueberhaengendes Gras
    rechts = hoch & ~np.roll(hoch, -1, axis=1); rechts[:, -1] = False   # Hochflaeche endet nach Osten
    links = hoch & ~np.roll(hoch, 1, axis=1); links[:, 0] = False       # Hochflaeche endet nach Westen

    if berg:
        # Berge: schmale seitliche Felswand (gestapelte Bloecke), Westseite im Licht, Ostseite im Schatten,
        # oben ueberhaengendes Gras - wirkt wie "frontal, ein bisschen seitlich"
        def block(y, k, hell):
            versatz = 6 if (k // 6) % 2 else 0
            yb = (y + versatz) % 12
            if k == seite - 1:
                c = F[0]
            elif yb == 0:
                c = F[5] if hell else F[4]
            elif yb == 11:
                c = F[1]
            elif k % 6 == 5:
                c = F[2]
            else:
                c = F[4] if hell else F[3]
                if ((y + versatz) // 12 * 7 + yb * 3 + k) % 41 == 0:
                    c = F[2]
            return c if hell else (c.astype(np.float32) * 0.84).astype(np.uint8)
        for kante, richtung, hell in ((rechts, 1, False), (links, -1, True)):
            for y, x in zip(*np.nonzero(kante)):
                if frei[y, x]:
                    continue
                n = 0
                for k in range(seite):
                    xx = x + richtung * (1 + k)
                    if not (0 <= xx < W) or hoch[y, xx]:
                        break
                    n += 1
                for k in range(n):
                    xx = x + richtung * (1 + k)
                    a[y, xx] = block(y, k + (seite - n), hell); wand[y, xx] = True
                if n == seite and not hell:
                    for k, f in ((0, 0.72), (1, 0.84), (2, 0.93)):
                        xx = x + richtung * (1 + seite + k)
                        if 0 <= xx < W and not hoch[y, xx]:
                            a[y, xx] = (a[y, xx] * f).astype(np.uint8)
                u = 1 + int(1 + math.sin(y / 3.1 + x) + 0.8 * math.sin(y / 1.9))
                for d in range(-1, u):
                    xx = x + richtung * (1 + d) if d >= 0 else x
                    if 0 <= xx < W:
                        a[y, xx] = Lp[1] if d == u - 1 else Lp[3] if d < 0 else Lp[2]
    else:
      for kante, richtung in ((rechts, 1), (links, -1)):
        for y, x in zip(*np.nonzero(kante)):
            if frei[y, x]:
                continue
            a[y, x] = Lp[0]                                             # Kontur
            xi = x - richtung
            if 0 <= xi < W and hoch[y, xi]:
                a[y, xi] = Lp[4] if richtung < 0 else Lp[1]
            stufen = ((1, 0.7), (2, 0.82), (3, 0.92)) if richtung > 0 else ((1, 0.82), (2, 0.93))
            for k, f in stufen:
                xx = x + richtung * k
                if 0 <= xx < W and not hoch[y, xx]:
                    a[y, xx] = (a[y, xx] * f).astype(np.uint8)
                    wand[y, xx] = True
    # Fronten
    unten = hoch & ~np.roll(hoch, -1, axis=0); unten[-1] = False
    trm = np.zeros((Hh, W), bool)
    for (t0, t1, ya, yb) in treppen:
        trm[ya:yb, t0:t1] = True
    a_vor = a.copy()
    frontm = np.zeros_like(hoch)
    front_kanten = []
    for y, x in zip(*np.nonzero(unten)):
        if frei[min(Hh - 1, y + 1), x]:
            continue
        tr = trm[y]
        if not tr[x]:
            front_kanten.append((y, x))
        for d in range(front):
            yy = y + 1 + d
            if yy >= Hh or hoch[yy, x]:
                break
            if tr[x]:
                st = d % 8                                              # Stufen: Tritt hell, Setzstufe
                c = F[5] if st < 2 else F[4] if st < 3 else F[3] if st < 7 else F[1]
                if x > 0 and not tr[x - 1] or x < W - 1 and not tr[x + 1]:
                    c = F[1]
                a[yy, x] = c
            else:
                a[yy, x] = tex[d, x]
                frontm[yy, x] = True
            wand[yy, x] = True
        else:
            for k, f in ((0, 0.62), (1, 0.75), (2, 0.86), (3, 0.94)):
                yy = y + 1 + front + k
                if yy < Hh and not hoch[yy, x] and not tr[x]:
                    a[yy, x] = (a[yy, x] * f).astype(np.uint8)
        if tr[x]:
            continue
        # Lippe: ueberhaengender Rand
        tief = 2 + int(1.5 + 1.5 * math.sin(x / 3.3 + y) + math.sin(x / 1.7))
        for d in range(-2, tief):
            yy = y + 1 + d
            if 0 <= yy < Hh:
                c = Lp[0] if d == tief - 1 else Lp[1] if d == tief - 2 else (Lp[4] if (x + d) % 4 == 0 else Lp[3]) if d < 0 else Lp[2]
                a[yy, x] = c
        yy = y + 1 + tief
        if yy < Hh and wand[yy, x]:
            a[yy, x] = (a[yy, x] * 0.72).astype(np.uint8)
    # Stummel und schraege Streifen entfernen: Kantenzuege (benachbarte Spalten, Hoehensprung <= 2 px)
    # werden einzeln bewertet - steiler als ~30 Grad oder schmaler als 10 px -> nur Graskante
    kanten = {}
    for y, x in front_kanten:
        kanten.setdefault(x, []).append(y)
    benutzt = set()
    for x0 in sorted(kanten):
        for y0 in kanten[x0]:
            if (y0, x0) in benutzt:
                continue
            zug = [(y0, x0)]; benutzt.add((y0, x0))
            y, x = y0, x0
            while True:
                nxt = [yy for yy in kanten.get(x + 1, []) if abs(yy - y) <= 2 and (yy, x + 1) not in benutzt]
                if not nxt:
                    break
                y = min(nxt, key=lambda v: abs(v - y)); x += 1
                zug.append((y, x)); benutzt.add((y, x))
            breite_ = len(zug)
            steig = abs(zug[-1][0] - zug[0][0]) / max(1, breite_)
            if filtern and (breite_ < min_breite or steig > 0.58):
                for (yk, xk) in zug:
                    a[yk + 1:yk + front + 6, xk] = a_vor[yk + 1:yk + front + 6, xk]
                    wand[yk + 1:yk + front + 1, xk] = False
    # Seitliche Frontenden sauber abschliessen (dunkle Kante + Lichtkante)
    fm = wand & ~hoch
    for y, x in zip(*np.nonzero(fm)):
        if x + 1 < W and not fm[y, x + 1] and not hoch[y, x + 1]:
            a[y, x] = F[0]
        if x - 1 >= 0 and not fm[y, x - 1] and not hoch[y, x - 1]:
            a[y, x] = F[5]
    # Nordkante: schmale Felskante
    oben = hoch & ~np.roll(hoch, 1, axis=0); oben[0] = False
    for y, x in zip(*np.nonzero(oben)):
        if frei[y, x]:
            continue
        a[y, x] = F[1]
        if y + 1 < Hh and hoch[y + 1, x]:
            a[y + 1, x] = Lp[4]
    return wand


def treppe(a, x0, x1, ye, richtung, front, fels, wegtex):
    """Steintreppe an einer Plateaukante. richtung 's': Front nach Sueden (Stufen frontal sichtbar, Wangen
    links/rechts, oben ein Wegstueck auf dem Plateau). 'n': Nordkante - Stufen von oben gesehen steigen
    nach Sueden an (Tritte mit Lichtkante), Wangen seitlich."""
    F = [np.array(H(c)) for c in FELS[fels]]
    Hh, W = a.shape[:2]
    if richtung == 's':
        for y in range(ye - 12, ye + 1):                          # Wegstueck oben
            for x in range(x0 + 1, x1 - 1):
                if (y - (ye - 12)) + min(x - x0, x1 - 1 - x) > 2:
                    a[y, x] = wegtex[y, x]
        n = 5
        hoehe = front + 4
        sh = hoehe / n
        for y in range(ye + 1, ye + 1 + hoehe):
            i = int((y - ye - 1) / sh)
            yy = (y - ye - 1) - i * sh
            for x in range(x0, x1):
                k = x - x0
                if k < 3:
                    c = (F[1], F[5], F[4])[k]
                elif x >= x1 - 3:
                    c = (F[3], F[2], F[0])[x - (x1 - 3)]
                elif yy < 1:
                    c = F[6]
                elif yy < 3:
                    c = F[5] if k < (x1 - x0) * 0.6 else F[4]
                elif yy >= sh - 1:
                    c = F[1]
                else:
                    c = F[3] if k < (x1 - x0) * 0.6 else F[2]
                a[y, x] = c
        for x in range(x0, x1):                                   # Kontaktschatten unter der letzten Stufe
            for d, f in ((0, 0.7), (1, 0.85)):
                yy = ye + 1 + hoehe + d
                if yy < Hh:
                    a[yy, x] = (a[yy, x] * f).astype(np.uint8)
        for y in range(ye + 1, ye + 1 + hoehe):                   # Schatten der rechten Wange
            for d, f in ((0, 0.75), (1, 0.88)):
                if x1 + d < W:
                    a[y, x1 + d] = (a[y, x1 + d] * f).astype(np.uint8)
    else:
        n, sh = 4, 6
        for y in range(ye - 1, ye + n * sh):
            i = (y - ye + 1) // sh
            yy = (y - ye + 1) % sh
            for x in range(x0, x1):
                k = x - x0
                if k < 3:
                    c = (F[1], F[4], F[3])[k]
                elif x >= x1 - 3:
                    c = (F[3], F[2], F[0])[x - (x1 - 3)]
                elif yy == 0:
                    c = F[1]
                elif yy == 1:
                    c = F[6] if i > 0 else F[5]
                else:
                    t = i / n
                    c = F[4] if t < 0.5 else F[5]
                a[y, x] = c


def rampe_zeichnen(a, x0, y0, x1, y1, abwaerts_nach_osten, fels):
    """Rampe in den Canyon: Furtboden, zur tiefen Seite dunkler, oben und unten Felskanten."""
    F = [np.array(H(c)) for c in FELS[fels]]
    breite = x1 - x0
    for y in range(y0, y1):
        for x in range(x0, x1):
            t = (x - x0) / max(1, breite)
            t = t if abwaerts_nach_osten else 1 - t
            a[y, x] = (a[y, x] * (1.0 - 0.18 * t)).astype(np.uint8)
            if (x + y) % 7 == 0 and (y - y0) % 4 == 2:
                a[y, x] = (a[y, x] * 0.85).astype(np.uint8)     # Querrillen
    for x in range(x0, x1):
        a[y0, x] = F[1]; a[y0 + 1, x] = F[4]
        a[y1 - 1, x] = F[0]; a[y1 - 2, x] = F[2]


def stromschnelle(a, wm, y0, y1, frame):
    """Furt: flaches, schnelles Wasser - unterbrochene Schaumkaemme wandern flussabwaerts, Trittsteine."""
    f = frame or 0
    for y in range(y0, y1):
        xs = np.nonzero(wm[y])[0]
        for x in xs:
            k = (y - y0 - f) % 6
            luecke = (x * 7 + (y - f) * 3) % 13 < 3
            if k == 0 and not luecke:
                a[y, x] = H('#f0faff')
            elif k == 1 and not luecke:
                a[y, x] = H('#9fd2f6')
    rs = random.Random(y0)
    for _ in range(4):
        y = rs.randint(y0 + 4, y1 - 6)
        xs = np.nonzero(wm[y])[0]
        if len(xs) < 6:
            continue
        x = int(rs.choice(list(xs[2:-3])))
        for dy, dx, c in ((-1, 0, '#e6dcc8'), (-1, 1, '#d4c8b0'), (0, -1, '#c8bca4'), (0, 0, '#b4a88e'), (0, 1, '#a89c84'),
                          (0, 2, '#8a7e68'), (1, 0, '#6e6454'), (1, 1, '#5e5446'), (2, 0, '#cfe8ff'), (2, 1, '#cfe8ff')):
            a[y + dy, x + dx] = H(c)


def teleporter_zeichnen(a, tx, ty, b, h, frame):
    puls = 0.5 + 0.5 * math.sin(2 * math.pi * (frame or 0) / N_FRAMES)
    for i in range(b):
        for j in range(h):
            cx, cy = (tx + i) * T + 8, (ty + j) * T + 8
            for yy in range(-6, 7):
                for xx in range(-7, 8):
                    d = (xx / 7) ** 2 + (yy / 6) ** 2
                    if d <= 1:
                        if d > 0.7:
                            c = H('#3e4850') if yy > 0 else H('#8e9ba3')
                        elif d > 0.35:
                            c = H('#2fc7d8') if puls > 0.4 or d < 0.5 else H('#2a8aa0')
                        else:
                            c = H('#e6ffff') if puls > 0.6 else H('#7ff0f5')
                        a[cy + yy, cx + xx] = c


def hecke(a, m, seed):
    """Dichte Buschhecke: runde Buschballen (Licht oben links), unten eine dunkle Blattfront + Schatten."""
    Hh, W = m.shape
    rnd = random.Random(seed)
    G = [np.array(H(c)) for c in HECKE]
    ys, xs = np.nonzero(m)
    if not len(ys):
        return
    a[m] = G[1]
    punkte = []
    for gy in range(0, Hh, 7):
        for gx in range(0, W, 7):
            px_, py_ = gx + rnd.randint(-2, 2), gy + rnd.randint(-2, 2)
            if 0 <= py_ < Hh and 0 <= px_ < W and m[py_, px_]:
                punkte.append((py_, px_, rnd.randint(4, 6)))
    punkte.sort()
    for (cy, cx, r) in punkte:
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                d = math.hypot(dx, dy)
                yy, xx = cy + dy, cx + dx
                if d > r or not (0 <= yy < Hh and 0 <= xx < W) or not m[yy, xx]:
                    continue
                if d > r - 1:
                    c = G[0] if dx + dy > 0 else G[2]
                else:
                    t = (dx + dy) / (2 * r)
                    c = G[5] if t < -0.45 else G[4] if t < -0.1 else G[3] if t < 0.3 else G[2]
                    if (xx * 7 + yy * 3) % 23 == 0:
                        c = G[6]
                a[yy, xx] = c
    # Unterkante: Blattfront 6 px + Schatten
    unten = m & ~np.roll(m, -1, axis=0)
    unten[-1] = False
    for y, x in zip(*np.nonzero(unten)):
        for d in range(6):
            yy = y + 1 + d
            if yy < Hh and not m[yy, x]:
                a[yy, x] = G[1] if d < 2 else G[0] if d < 5 else G[0] // 2 + 10
        for k, f in ((6, 0.65), (7, 0.8), (8, 0.92)):
            yy = y + 1 + k
            if yy < Hh and not m[yy, x]:
                a[yy, x] = (a[yy, x] * f).astype(np.uint8)


def wasser_zeichnen(a, m, frame, fluss_m):
    """Wasser mit Uferlinie: Textur aus Karte 01 (Fluss scrollt nach unten, Teiche ruhen), dunkler nasser
    Saum aussen, heller Schaumrand innen (gestrichelt, wandert)."""
    Hh, W = m.shape
    w1 = [np.array(Image.open(os.path.join(BASIS1, 'wasser_%d.png' % v)).convert('RGB')) for v in range(5)]
    tex = np.zeros((Hh, W, 3), np.uint8)
    f = frame or 0
    for y in range(0, Hh, T):
        for x in range(0, W, T):
            tex[y:y + T, x:x + T] = w1[kb.variante(x // T, y // T)]
    fl = np.roll(tex, f, axis=0)                                 # Fliessrichtung Sued
    t2 = np.where(fluss_m[..., None], fl, np.roll(tex, f // 4, axis=1))
    a[m] = t2[m]
    rand_in = m & ~(np.roll(m, 1, 0) & np.roll(m, -1, 0) & np.roll(m, 1, 1) & np.roll(m, -1, 1))
    aussen = ~m & (np.roll(m, 1, 0) | np.roll(m, -1, 0) | np.roll(m, 1, 1) | np.roll(m, -1, 1))
    a[aussen] = (a[aussen] * 0.62).astype(np.uint8)
    yy, xx = np.nonzero(rand_in)
    for y, x in zip(yy, xx):
        if (x + y * 2 + f) % 6 < 4:
            a[y, x] = H('#cfe8ff')
        else:
            a[y, x] = H('#8cc4f4')


def klippen_verdeckung(img, objs, cache, hoch, ebene_fuss, grund):
    """Regel Verdeckung durch Hoehen: Objekt auf tieferem Boden wird von einem seitlich daneben liegenden hoeheren
    Plateau abgeschnitten (Spalten, in denen das hoehere Gelaende bis zur Fusshoehe reicht)."""
    Hh, W = hoch.shape
    a = np.array(img)
    for o in objs:
        sp = cache[o['datei']]
        al = np.array(sp.getchannel('A')) > 0
        if o.get('spiegeln'):
            al = al[:, ::-1]
        ys, xs = np.nonzero(al)
        if not len(ys):
            continue
        fy = min(Hh - 1, max(0, o['y'] + int(ys.max())))
        fx = min(W - 1, max(0, o['x'] + int(xs.mean())))
        if hoch[max(0, fy - 4):min(Hh, fy + 3), max(0, fx - 4):fx + 5].any() or not ebene_fuss[min(Hh - 1, fy + 1), fx]:
            continue                                   # Fuss auf/am Plateau: gehoert zum Plateau, nicht abschneiden
        if o.get('waldrand'):
            continue                                   # Waldrand am Kartenrand bleibt ganz (Kronen davor)
        Y, X = ys + o['y'], xs + o['x']
        ok = (Y >= 0) & (Y < Hh) & (X >= 0) & (X < W)
        Y, X = Y[ok], X[ok]
        m = hoch[np.clip(fy - 2, 0, Hh - 1), X] & hoch[Y, X]
        if m.any():
            a[Y[m], X[m]] = grund[Y[m], X[m]]
    img.paste(Image.fromarray(a))


def objekte_zeichnen(img, objs, cache, boden, frame, ebenen=None):
    """Kontaktschatten unter der Auflage + Schlagschatten der Silhouette nach rechts unten (2 Stufen),
    nur auf Boden (nicht auf Wasser); dann die Sprites (Wind fuer Akazien und Graeser)."""
    # ebenen (optional): Hoehenstufe je Pixel (9 = Wand). Schatten eines Objekts nur auf seiner eigenen Ebene
    # (Regel 7: nie ueber Kanten, Waende, Wasser)
    stufen = {}

    def felder(o, a_):
        if ebenen is None:
            k_ = None
        else:
            zl = np.nonzero(a_.any(axis=1))[0]
            fy_ = min(ebenen.shape[0] - 1, max(0, o['y'] + int(zl.max()) + 1)) if len(zl) else 0
            xs_ = np.nonzero(a_[zl.max()])[0] if len(zl) else [0]
            fx_ = min(ebenen.shape[1] - 1, max(0, o['x'] + int(np.mean(xs_))))
            k_ = int(ebenen[fy_, fx_])
        if k_ not in stufen:
            stufen[k_] = (np.zeros(boden.shape, np.float32), np.zeros(boden.shape, np.float32))
        return stufen[k_]
    for o in objs:
        sp = cache[o['datei']]
        a = np.array(sp.getchannel('A')) >= 200
        zeilen = np.nonzero(a.any(axis=1))[0]
        if not len(zeilen):
            continue
        kern, wurf = felder(o, a)
        if o.get('liegend') and len(zeilen):              # liegend: flacher Schatten der ganzen Form
            ys_, xs_ = np.nonzero(a)
            for d_, w_ in ((2, 0.83), (1, 1.0)):
                Y_, X_ = ys_ + o['y'] + d_, xs_ + o['x'] + d_
                ok_ = (Y_ >= 0) & (Y_ < kern.shape[0]) & (X_ >= 0) & (X_ < kern.shape[1])
                wurf[Y_[ok_], X_[ok_]] = np.maximum(wurf[Y_[ok_], X_[ok_]], w_)
            continue
        if len(zeilen) < 4:
            continue
        zu = zeilen.max()
        fuss_y = o['y'] + zu
        fuss = np.nonzero(a[max(0, zu - 3):zu + 1].any(axis=0))[0]
        if len(fuss):
            fx0, fx1 = o['x'] + fuss.min(), o['x'] + fuss.max()
            for yy in range(fuss_y - 1, fuss_y + 3):
                if 0 <= yy < kern.shape[0]:
                    ein = (yy - fuss_y + 1) if yy > fuss_y else 0
                    kern[yy, max(0, fx0 - 1 + ein):max(0, min(kern.shape[1], fx1 + 3 - ein))] = 1
        hoehe_ = max(1, zu - zeilen.min())
        for zi in zeilen:
            k = zu - zi
            ty = int(fuss_y + k * 0.24)
            dx = int(1 + k * 0.45)
            if 0 <= ty < wurf.shape[0]:
                xs = np.nonzero(a[zi])[0] + o['x'] + dx
                xs = xs[(xs >= 0) & (xs < wurf.shape[1])]
                wurf[ty, xs] = np.maximum(wurf[ty, xs], 1.0 - 0.35 * k / hoehe_)
    sch = np.zeros(boden.shape, np.float32)
    for k_, (kern, wurf) in stufen.items():
        wurf = np.array(Image.fromarray((wurf * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3))) / 255.0
        s_ = np.where(kern > 0, 92, np.where(wurf > 0.82, 64, np.where(wurf > 0, 50, 0))).astype(np.float32)
        if k_ is not None:
            s_ *= (ebenen == k_)
        sch = np.maximum(sch, s_)
    sch = (sch * boden).astype(np.uint8)
    dunkel = Image.new('RGBA', img.size, (60, 40, 24, 255))
    dunkel.putalpha(Image.fromarray(sch))
    img.alpha_composite(dunkel)
    grund = np.array(img.convert('RGB'))
    for o in objs:
        sp = cache[o['datei']]
        if frame is not None and o.get('anim') in ('wehen', 'blume'):
            sp = kb.wehen(sp, kb.wind(frame, o['x']))
        elif frame is not None and o.get('anim') == 'baum':
            sp = baum_wind(sp, frame, o['x'] + o['y'] * 0.3)
        elif frame is not None and o.get('anim') == 'fahne':
            sp = fahne_wehen(sp, frame, o['x'] * 0.37)
        elif frame is not None and o.get('anim') == 'reaktor':
            sp = reaktor_ruetteln(sp, frame, o['x'])
        img.alpha_composite(sp, (o['x'], o['y']))
        if frame is not None and o.get('anim') == 'blume':
            bluete_puls(img, o, sp, frame)
        if not o['basis'].startswith(('rand/', 'klein/0', 'klein/1', 'klein/2', 'klein/5')):
            bodenwall(img, grund, o, cache[o['datei']])


RUETTEL_X = (0, 1, 0, -1, 1, 0, -1, 0, 0, 1, -1, 0, 1, 0, 0, -1)
RUETTEL_Y = (0, 0, -1, 0, 0, -1, 0, 0, -1, 0, 0, 0, -1, 0, 0, 0)
FUSS_STILL = 4                      # unterste Pixelreihen (Fuesse, Kabel am Boden) bleiben ruhig


def ruettel(frame, phase):
    """Versatz (dx, dy) des laufenden Gehaeuses in diesem Bild - unregelmaessiges Motorruetteln."""
    k = (frame + int(phase) * 7) % len(RUETTEL_X)
    return RUETTEL_X[k], RUETTEL_Y[k]


def reaktor_ruetteln(sp, frame, phase):
    """Gehaeuse ruettelt um 1 px, die Fuesse stehen fest auf dem Boden."""
    dx, dy = ruettel(frame, phase)
    if not (dx or dy):
        return sp
    zl = np.nonzero(np.array(sp.getchannel('A')).any(axis=1))[0]
    schnitt = int(zl.max()) + 1 - FUSS_STILL
    neu = Image.new('RGBA', sp.size, (0, 0, 0, 0))
    koerper = sp.crop((0, 0, sp.width, schnitt))
    neu.paste(koerper, (dx, dy), koerper)
    fuss = sp.crop((0, schnitt - 1, sp.width, sp.height))          # Naht doppelt -> keine Luecke beim Hochruetteln
    neu.alpha_composite(fuss, (0, schnitt - 1))
    return neu


def fahne_wehen(sp, frame, phase=0.0):
    """Nur der Stoff weht (Regel: Mast/Stange bleibt ruhig). Stoff = farbige Flaeche unterhalb der Querstange
    rechts vom Mast samt Kontur; Zeilen werden nach unten zunehmend seitlich verschoben."""
    a = np.array(sp.convert('RGBA')).astype(np.int16)
    al = a[..., 3] > 0
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    bunt = al & ((b > r + 15) | (r > g + 40) & (r > b + 40)) & ~((r > g) & (g > b) & (r - b < 120) & (r < 170))
    if bunt.sum() < 10:
        return sp
    ys, xs = np.nonzero(bunt)
    y0, x0 = int(ys.min()), int(xs.min()) - 1
    braun = (r > g) & (g >= b) & (r - b > 25) & (r < 190)
    stoff = al.copy()
    stoff[:y0] = False
    stoff[:, :max(0, x0)] = False
    stoff &= ~braun
    h = max(1, int(ys.max()) - y0)
    out = a.copy()
    out[stoff] = 0
    for y in range(y0, a.shape[0]):
        t = (y - y0) / h
        d = int(round(1.6 * t * math.sin(2 * math.pi * frame / N_FRAMES + phase + y / 7.0)))
        for x in np.nonzero(stoff[y])[0]:
            xn = x + d
            if 0 <= xn < a.shape[1]:
                out[y, xn] = a[y, x]
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), 'RGBA')


def bodenwall(img, grund, o, sp):
    """Objekt steckt im Boden: an der Auflagekante liegt ein kleiner, unregelmaessiger Wall aus genau der
    Bodentextur darunter (oberste Reihe heller), seitlich auslaufend - so wirkt nichts aufgesetzt."""
    a = np.array(sp.getchannel('A')) >= 200
    if not a.any():
        return
    zu = int(np.nonzero(a.any(axis=1))[0].max())
    spalten = [x for x in range(a.shape[1]) if a[max(0, zu - 3):zu + 1, x].any()]
    if len(spalten) < 3:
        return
    x0, x1 = spalten[0], spalten[-1]
    px = img.load()
    W, H = img.size
    rnd = random.Random(o['x'] * 7 + o['y'])
    for x in range(x0 - 2, x1 + 3):
        rand = min(x - (x0 - 2), (x1 + 2) - x)
        h = min(3, 1 + rand // 2) + (1 if rnd.random() < 0.3 else 0) - (1 if rnd.random() < 0.25 else 0)
        X = o['x'] + x
        Yf = o['y'] + zu
        for k in range(max(0, h)):
            Y = Yf - k + 1
            Q = min(H - 1, Yf + 4 + k)
            if 0 <= X < W and 0 <= Y < H:
                c = grund[Q, X].astype(np.float32)
                if k == h - 1:
                    c = np.minimum(255, c * 1.12 + 6)
                px[X, Y] = tuple(int(v) for v in c) + (255,)


def bluete_puls(img, o, sp, frame):
    """Blueten leuchten im Takt sanft auf (bunte, gesaettigte Pixel werden heller)."""
    a = np.array(sp).astype(np.int16)
    mx, mn = a[..., :3].max(axis=2), a[..., :3].min(axis=2)
    m = (a[..., 3] > 0) & (mx - mn > 70) & (a[..., 0] > a[..., 1] + 30)
    f = 0.25 * (0.5 + 0.5 * math.sin(2 * math.pi * frame / N_FRAMES + o['x'] / 60.0))
    px = img.load()
    for y, x in zip(*np.nonzero(m)):
        X, Y = o['x'] + x, o['y'] + y
        r_, g_, b_, _ = px[X, Y]
        px[X, Y] = (min(255, int(r_ + (255 - r_) * f)), min(255, int(g_ + (255 - g_) * f)),
                    min(255, int(b_ + (255 - b_) * f)), 255)


def baum_wind(sp, frame, phase):
    """Baum im Wind: die Krone (obere 65 %) schwingt weich bis 2 px seitlich, unten weniger, der Stamm steht;
    dazu flirren einzelne Blattpixel hell auf."""
    t = 2 * math.pi * (frame / N_FRAMES - phase / 520.0)
    amp = 1.6 * math.sin(t) + 0.5 * math.sin(2 * t + 1.0)
    out = Image.new('RGBA', sp.size)
    grenze = sp.height * 0.65
    for y in range(sp.height):
        d = round(amp * (1 - y / grenze)) if y < grenze else 0
        out.paste(sp.crop((0, y, sp.width, y + 1)), (d, y))
    a = np.array(out)
    g = (a[..., 1] > a[..., 0] + 15) & (a[..., 1] > a[..., 2] + 15) & (a[..., 3] > 0)
    ys, xs = np.nonzero(g)
    if len(ys):
        rs = random.Random(int(phase) * 31 + frame)
        for _ in range(max(1, len(ys) // 90)):
            i = rs.randrange(len(ys))
            a[ys[i], xs[i], :3] = np.minimum(255, a[ys[i], xs[i], :3].astype(int) + 55)
    return Image.fromarray(a)


FLAMME = [  # 7x9, f1 dunkelrot .. f4 hellgelb
    ["...4...", "..343..", "..343..", ".23432.", ".23432.", "1234321", "1233321", ".12221.", "..111.."],
    ["..4....", "..34...", ".3443..", ".2343..", "123432.", "1234321", "1233321", ".12221.", "..111.."],
    ["....4..", "...43..", "..3443.", "..3432.", ".234321", "1234321", "1233321", ".12221.", "..111.."],
]
FEUERFARBE = {'1': (160, 40, 30), '2': (230, 90, 30), '3': (250, 170, 50), '4': (255, 236, 150)}


ROHRE = {'baeume/04': [(19, 1, -1), (58, 5, 1)], 'rand/08': [(41, 1, 0), (50, 1, 0)]}   # Rohr x, y, Austrittsrichtung


def animieren(img, objs, cache, frame, ruhig=False):
    """Lagerfeuer (Flammen + Lichtschein), Monument-Juwel pulsiert, Kristalle glitzern, Laterne glimmt."""
    glut = Image.new('RGBA', img.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glut)
    px = img.load()
    puls = 0.5 + 0.5 * math.sin(2 * math.pi * frame / N_FRAMES)
    for i, o in enumerate(objs):
        anim = o.get('anim')
        sp = cache[o['datei']]
        if anim == 'feuer':
            cx, cy = o['x'] + sp.width // 2, o['y'] + int(sp.height * 0.55)
            fl = FLAMME[(frame + i) % 3]
            for dy, z in enumerate(fl):
                for dx, ch in enumerate(z):
                    if ch != '.':
                        px[cx - 3 + dx, cy - 8 + dy] = FEUERFARBE[ch] + (255,)
            st = 0.75 + 0.25 * math.sin(frame * 2.1 + i)
            for r, al in ((26, 26), (16, 40), (8, 56)):
                gd.ellipse((cx - r, cy - r * 0.6, cx + r, cy + r * 0.6), fill=(255, 150, 60, int(al * st)))
        elif anim == 'juwel':
            a = np.array(sp)
            m = (a[..., 0] > 150) & (a[..., 1] < 90) & (a[..., 3] > 0)
            ys, xs = np.nonzero(m)
            if len(xs):
                cx, cy = o['x'] + xs.mean(), o['y'] + ys.mean()
                for y_, x_ in zip(ys, xs):
                    r_, g_, b_, _ = px[o['x'] + x_, o['y'] + y_]
                    f = 0.85 + 0.45 * puls
                    px[o['x'] + x_, o['y'] + y_] = (min(255, int(r_ * f)), min(255, int(g_ * f + 20 * puls)),
                                                    min(255, int(b_ * f + 20 * puls)), 255)
                for r, al in ((20, 30), (12, 50), (6, 80)):
                    gd.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(255, 60, 60, int(al * (0.4 + 0.6 * puls))))
                # Funkeln: Sternblitze wandern ueber das Juwel (wachsen und schrumpfen)
                for k in range(2):
                    ph = (frame + k * 8) % N_FRAMES
                    gr = (0, 2, 4, 5, 4, 2, 1, 0)[ph // 2] if ph < 16 else 0
                    if gr:
                        j = (k * 5 + frame // 8 * 3) % len(xs)
                        sx_, sy_ = o['x'] + xs[j], o['y'] + ys[j]
                        if k == 1:
                            sx_, sy_ = int(cx - 2), int(cy - 3)
                        for d in range(-gr, gr + 1):
                            al_ = 255 if abs(d) < gr else 170
                            gd.point((sx_ + d, sy_), fill=(255, 255, 255, al_))
                            gd.point((sx_, sy_ + d), fill=(255, 255, 255, al_))
                        if gr >= 2:
                            for dx_, dy_ in ((1, 1), (-1, -1), (1, -1), (-1, 1)):
                                gd.point((sx_ + dx_, sy_ + dy_), fill=(255, 230, 230, 150))
        elif anim == 'glitzern':
            a = np.array(sp)
            m = (a[..., 2] > 200) & (a[..., 0] > 150) & (a[..., 3] > 0)
            ys, xs = np.nonzero(m)
            if len(xs):
                k = (frame * 3 + i * 5) % (len(xs) * 3)
                if k < len(xs):
                    x_, y_ = o['x'] + xs[k], o['y'] + ys[k]
                    for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
                        px[x_ + dx, y_ + dy] = (255, 255, 255, 255)
                cx, cy = o['x'] + xs.mean(), o['y'] + ys.mean()
                gd.ellipse((cx - 9, cy - 7, cx + 9, cy + 7), fill=(160, 210, 255, int(22 + 22 * puls)))
        elif anim == 'reaktor':
            # Generator/Reaktor: Kontrolllampen und Anzeigen pulsieren (nur helle, gesaettigte Pixel), aus den
            # Auspuffrohren steigen Rauchwoelkchen auf (nur ueber dem Objekt, nicht auf dem Gehaeuse)
            a = np.array(sp).astype(np.int16)
            r_, g_, b_ = a[..., 0], a[..., 1], a[..., 2]
            mx, mn = np.maximum(np.maximum(r_, g_), b_), np.minimum(np.minimum(r_, g_), b_)
            licht = (a[..., 3] > 0) & (mx > 150) & (mx - mn > 70) & ((g_ > r_ + 20) | (b_ > r_ + 20) | (r_ > g_ + 90))
            rdx, rdy = (0, 0) if ruhig else ruettel(frame, o['x'])
            ys_l, xs_l = np.nonzero(licht)
            for y_, x_ in zip(ys_l, xs_l):
                f = 0.55 + 0.9 * (0.5 + 0.5 * math.sin(2 * math.pi * frame / N_FRAMES * 2 + (x_ // 4) * 1.3 + i))
                X, Y = o['x'] + x_ + rdx, o['y'] + y_ + rdy
                rr, gg, bb, _ = px[X, Y]
                px[X, Y] = (min(255, int(rr * f)), min(255, int(gg * f)), min(255, int(bb * f)), 255)
            if len(xs_l):
                # schwacher Lichtschein um die Lampengruppe
                st = 0.5 + 0.5 * math.sin(2 * math.pi * frame / N_FRAMES * 2 + i)
                fa = tuple(int(c) for c in a[ys_l, xs_l, :3].mean(axis=0))
                cx_l, cy_l = o['x'] + rdx + xs_l.mean(), o['y'] + rdy + ys_l.mean()
                rx, ry = (xs_l.max() - xs_l.min()) / 2 + 4, (ys_l.max() - ys_l.min()) / 2 + 3
                gd.ellipse((cx_l - rx, cy_l - ry, cx_l + rx, cy_l + ry), fill=fa + (int(55 * st),))
            # Rauch genau aus den Rohroeffnungen (Pixel im Original-Sprite, Variante hat 2 px Rand links)
            basis = Image.open(os.path.join(OBJ, o['basis'] + '.png'))
            off = 2 if sp.size == (basis.width + 4, basis.height + 3) else 0
            for j, (rx_, ry_, seit) in enumerate(ROHRE.get(o['basis'], ())):
                if o.get('spiegeln') or o['datei'].endswith('_m.png'):
                    rx_, seit = basis.width - 1 - rx_, -seit
                cx, cy0 = o['x'] + off + rx_ + rdx, o['y'] + ry_ + rdy
                for z in range(4):
                    t = ((frame + z * N_FRAMES / 4 + j * 2) % N_FRAMES) / N_FRAMES
                    cy = cy0 - 1 - t * 30
                    r = 1.5 + t * 4.5
                    dx = seit * min(t * 4, 1) * 4 + math.sin(t * 6 + j * 2) * 1.5 + t * 7      # Austritt + Wind
                    k_ = 1 - t
                    x0, y0 = round(cx + dx), round(cy)
                    gd.ellipse((x0 - r - 1, y0 - r - 1, x0 + r + 1, y0 + r + 1), fill=(95, 90, 88, int(170 * k_)))
                    gd.ellipse((x0 - r, y0 - r, x0 + r, y0 + r), fill=(175, 170, 165, int(210 * k_)))
                    if r > 2.5:
                        gd.ellipse((x0 - r + 1, y0 - r + 1, x0, y0), fill=(220, 216, 210, int(200 * k_)))
        elif anim == 'leuchten':
            cx, cy = o['x'] + sp.width // 2, o['y'] + sp.height // 2
            for r, al in ((14, 30), (7, 50)):
                gd.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(255, 200, 110, int(al * (0.6 + 0.4 * puls))))
    img.alpha_composite(glut)


def splitter_weg(m, minimum):
    """Zusammenhaengende Teile einer Pixelmaske unter minimum Pixeln entfernen."""
    from collections import deque
    m = m.copy()
    Hh, W = m.shape
    gesehen = np.zeros_like(m)
    for y0, x0 in zip(*np.nonzero(m)):
        if gesehen[y0, x0]:
            continue
        q = deque([(y0, x0)]); gesehen[y0, x0] = True; teil = []
        while q:
            y, x = q.popleft(); teil.append((y, x))
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                yy, xx = y + dy, x + dx
                if 0 <= yy < Hh and 0 <= xx < W and m[yy, xx] and not gesehen[yy, xx]:
                    gesehen[yy, xx] = True; q.append((yy, xx))
        if len(teil) < minimum:
            for y, x in teil:
                m[y, x] = False
    return m


def _laeufe(ys):
    out = []
    for y in ys:
        if out and y == out[-1][1] + 1:
            out[-1][1] = y
        else:
            out.append([y, y])
    return out


def bauen(frame=None, speichern=True):
    lay = lade_layout()
    cols, rows = lay['groesse']
    cls = lay['klassen']
    hoehe = np.array([[int(c) for c in r] for r in lay['hoehe']])
    Wp, Hp = cols * T, rows * T
    a = textur(cls, 's', cols, rows)
    # --- weiche Bodenarten
    for art, blur, rausch, seed in (('d', 6.0, 0.55, 3), ('e', 6.0, 0.5, 4), ('m', 5.0, 0.4, 5),
                                    ('a', 6.0, 0.45, 6), ('w', 4.0, 0.42, 7)):
        roh = zell_maske(cls, art, cols, rows)
        m = weich(roh, blur, rausch, seed)
        tx = textur(cls, art, cols, rows)
        a[m] = tx[m]
        saum = weich(roh, blur, rausch, seed, 0.38) & ~m
        if art == 'd':                                        # Grasbueschel am Rand
            ys, xs = np.nonzero(saum)
            rs = np.random.RandomState(seed)
            sel = rs.rand(len(ys)) < 0.12
            for y, x in zip(ys[sel], xs[sel]):
                a[y, x] = H('#ada86b')
                if y > 0:
                    a[y - 1, x] = H('#c1bb80')
        else:
            dunkeln(a, saum, 0.93)
    # --- Hoehenmasken (stark gerundet, damit die Kanten nicht treppig wirken)
    stufe = lambda n: zell_maske([''.join('1' if v >= n else '0' for v in r) for r in hoehe], '1', cols, rows)
    m1 = weich(stufe(1), 6, 0, 21)
    m2 = weich(stufe(2), 6, 0, 22)
    teer = weich(zell_maske(cls, 't', cols, rows), 6, 0, 23)
    can = ~m1 & ~teer
    for art, m in (('c', can), ('t', teer)):
        tx = textur(cls, art, cols, rows)
        a[m] = tx[m]
    rampen_roh = np.zeros((Hp, Wp), np.float32)
    for r in lay.get('rampen', []):
        x0, y0, x1, y1 = r
        rampen_roh[y0 * T:(y1 + 1) * T, x0 * T:(x1 + 1) * T] = 1
    furt = weich(np.maximum(zell_maske(cls, 'f', cols, rows), rampen_roh), 3.5, 0.3, 25)
    tx = textur(cls, 'f', cols, rows)
    a[furt & can] = tx[furt & can]
    tx = textur(cls, 'g', cols, rows)
    a[m2] = tx[m2]
    # --- Wasser
    xm = zell_maske(cls, 'x', cols, rows)
    wm = (weich(xm, 9, 0.1, 24, 0.33) & can) | (weich(xm, 12, 0.12, 26, 0.5) & m1)        # Teiche rund (v1.1)
    wm = splitter_weg(wm, 120)
    fluss = wm & can
    wasser_zeichnen(a, wm, frame, fluss)
    import wasser_vertieft                                  # Stil von Karte 01: vertieftes Wasser
    import wasser_details                                   # Felsen/Algen in den Tiefenstufen (wie Karte 01)
    wasser_details.FELSEN_PROTOKOLL.clear()
    wasser_details.SPITZEN.clear()
    wasser_meiden = np.zeros((Hp, Wp), bool)                # Bruecke und Objekte: dort keine Felsen/Algen
    _pf = os.path.join(OBJ, 'platzierung.json')
    if os.path.exists(_pf):
        for _o in json.load(open(_pf)):
            _w, _h = Image.open(os.path.join(OBJ, _o['datei'])).size
            wasser_meiden[max(0, _o['y'] - 4):_o['y'] + _h + 4, max(0, _o['x'] - 4):_o['x'] + _w + 4] = True
    a = np.array(wasser_vertieft.vertiefen(Image.fromarray(a), np.ones_like(wm), frame, maske=wm,
                                           rand=('#5e3e26', '#7e5634', '#9c7044', '#b88a58'),
                                           meiden=wasser_meiden, stufen=[(20, 0.8, 7), (40, 0.64, 6)]).convert('RGB'))
    for (y0, y1) in lay.get('furten', []):
        stromschnelle(a, fluss, y0 * T, (y1 + 1) * T, frame)
    # --- Rampen (keine Kanten dort)
    rampen = np.zeros((Hp, Wp), bool)
    for r in lay.get('rampen', []):
        x0, y0, x1, y1 = r
        rampen[y0 * T:(y1 + 1) * T, x0 * T:(x1 + 1) * T] = True
    # Treppen: 's' an Plateau-Fronten (Sandstein, 40 px), 't' ins Teerbecken (Schiefer, 20 px)
    treppen_info = []
    frei_pl = np.zeros((Hp, Wp), bool)
    frei_t = np.zeros((Hp, Wp), bool)
    for eintrag in lay.get('treppen', []):
        x0, x1, y0, y1, r = eintrag[:5]
        art = eintrag[5] if len(eintrag) > 5 else 'plateau'
        maske, front, frei = (m1 | can, 20, frei_t) if art == 'teer' else (m2, 40, frei_pl)
        px0, px1 = x0 * T + 1, (x1 + 1) * T - 1
        ye = max((max(np.nonzero(maske[y0 * T:(y1 + 1) * T, xc])[0]) + y0 * T
                  for xc in range(px0, px1) if maske[y0 * T:(y1 + 1) * T, xc].any()
                  and not maske[y0 * T:(y1 + 1) * T, xc].all()), default=None)
        if ye is None:
            continue
        frei[ye - 14:ye + front + 6, px0 - 6:px1 + 6] = True
        treppen_info.append((px0, px1, ye, art, front))
    treppen = []
    # --- Waende: Canyon (Erde), Teerbecken (Schiefer), Plateaus (Sandstein)
    waende = hoehenkanten(a, m1 | teer, 'erde', 26, 14, LIPPE['s'], rampen, 11, min_breite=22)
    waende |= hoehenkanten(a, m1 | can, 'schiefer', 20, 8, LIPPE['a'], rampen | frei_t, 12, berg=True)
    waende |= hoehenkanten(a, m2, 'sandstein', 40, 8, LIPPE['g'], frei_pl, 13, treppen, berg=False)   # Seiten: nur Abgrenzung
    if speichern and frame is None:
        np.save(os.path.join(KARTE, 'waende.npy'), np.packbits(waende))
    wegtex = textur(cls, 'w', cols, rows)
    img_t = Image.fromarray(a).convert("RGBA")
    alt_S = bauwerke.S
    for (px0, px1, ye, art, front) in treppen_info:
        bauwerke.S = [H(c) + (255,) for c in FELS['schiefer' if art == 'teer' else 'sandstein']]
        oben = textur(cls, 'a', cols, rows) if art == 'teer' else wegtex
        for y in range(ye - 12, ye + 1):                          # Wegstueck oben
            for x in range(px0 + 4, px1 - 4):
                if (y - (ye - 12)) + min(x - px0 - 4, px1 - 5 - x) > 2:
                    img_t.putpixel((x, y), tuple(oben[y, x] if art != 'teer' else (oben[y, x] * 0.8).astype(np.uint8)) + (255,))
        bauwerke.zeichne_treppe(img_t, px0 - 6, px1 + 6, ye + 2, ye + front + 2)
    bauwerke.S = alt_S
    a = np.array(img_t.convert('RGB'))
    # Rampen-Oberflaechen: Furtboden, der zur Tiefe hin leicht dunkler wird
    rm = weich(rampen_roh, 3.0, 0.3, 27) & ~fluss
    tx = textur(cls, 'f', cols, rows)
    a[rm] = tx[rm]
    xs_c = np.nonzero(can.any(axis=0))[0]
    mitte = (xs_c.min() + xs_c.max()) / 2 if len(xs_c) else Wp / 2
    for y, x in zip(*np.nonzero(rm)):
        if not can[y, x]:
            d = min(abs(x - mitte) / (Wp * 0.1), 1.0)
            a[y, x] = (a[y, x] * (0.9 + 0.1 * d)).astype(np.uint8)
    # --- Bruecke ueber den Fluss (Hauptstrasse)
    br = lay.get('bruecke')
    img = Image.fromarray(a).convert('RGBA')
    if br:
        y0, y1 = br
        ym = (y0 * T + (y1 + 1) * T) // 2
        xs = np.nonzero(can[ym])[0]
        if len(xs):
            bx0, bx1 = int(xs.min()) - 12, int(xs.max()) + 13
            by0, by1 = y0 * T + 2, (y1 + 1) * T - 2
            px_ = img.load()
            # Stuetzen bis auf den Canyonboden und Schlagschatten der hohen Bruecke auf dem Grund
            for x in range(bx0 + 10, bx1 - 10):
                for d in range(14, 24):
                    yy = by1 + d
                    if can[yy, x]:
                        r_, g_, b_, _ = px_[x, yy]
                        px_[x, yy] = (int(r_ * 0.7), int(g_ * 0.7), int(b_ * 0.72), 255)
            HOLZ = [H(c) for c in ('#3a2416', '#5a3a22', '#7a5232', '#94683e', '#b0844e', '#c89c62')]
            for sx in range(bx0 + 30, bx1 - 20, 44):
                for x in range(sx, sx + 5):
                    for yy in range(by1, by1 + 22):
                        k = x - sx
                        c = HOLZ[0] if k in (0, 4) else HOLZ[3] if k == 1 else HOLZ[2]
                        px_[x, yy] = c + (255,)
                    for yy in range(by1 + 22, by1 + 24):
                        r_, g_, b_, _ = px_[x, yy]
                        px_[x, yy] = (int(r_ * 0.7), int(g_ * 0.7), int(b_ * 0.7), 255)
            seg = 80
            x = bx0
            while x < bx1:
                bauwerke.zeichne_bruecke(img, x, min(bx1, x + seg), by0, by1, frame=frame or 0, seed=x, wasser=False)
                x += seg
    a = np.array(img.convert('RGB'))
    for tp in lay.get('teleporter', []):
        teleporter_zeichnen(a, tp['x'], tp['y'], tp['b'], tp['h'], frame)
    # --- Hecke
    # Waldrand: schattiger Waldboden (Olivgras, dunkler), die Baeume kommen als Objekte
    hroh = zell_maske(cls, 'h', cols, rows)
    hm = weich(hroh, 5, 0.4, 8)
    tx = textur(cls, 'd', cols, rows)
    a[hm] = (tx[hm] * np.array([0.7, 0.76, 0.66])).astype(np.uint8)
    saum = weich(hroh, 5, 0.4, 8, 0.32) & ~hm
    a[saum] = (a[saum] * 0.85).astype(np.uint8)
    img = Image.fromarray(a).convert('RGBA')
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain_basis.png'))
    pf = os.path.join(OBJ, 'platzierung.json')
    objs = []
    if os.path.exists(pf):
        objs = sorted((o for o in json.load(open(pf)) if os.path.exists(os.path.join(OBJ, o['datei']))),
                      key=lambda o: o['y'] + o['fuss'])
        cache = {}
        for o in objs:
            if o['datei'] not in cache:
                cache[o['datei']] = Image.open(os.path.join(OBJ, o['datei'])).convert('RGBA')
        vor_objekten = np.array(img)
        ebenen = np.ones((Hp, Wp), np.int16)
        ebenen[can] = 0
        ebenen[m2] = 2
        ebenen[waende] = 9
        objekte_zeichnen(img, objs, cache, ~wm, frame, ebenen)
        animieren(img, objs, cache, frame or 0, ruhig=frame is None)
        for o in objs:
            kx_, ky_ = (o['x'] + cache[o['datei']].width // 2) // T, (o['y'] + o['fuss']) // T
            o['waldrand'] = o['basis'].startswith('rand/') or cls[min(rows - 1, max(0, ky_))][min(cols - 1, max(0, kx_))] == 'h'
        klippen_verdeckung(img, objs, cache, m2, ~m2, vor_objekten)
        blumen = [o for o in objs if o.get('anim') == 'blume']
        rf = random.Random(4)
        falter = []
        for o in rf.sample(blumen, min(14, len(blumen))):
            falter.append({'x': o['x'] + 8, 'y': o['y'] - 6, 'rx': rf.randint(8, 14), 'ry': rf.randint(4, 8),
                           'phase': rf.random(), 'richtung': rf.choice((1, -1)),
                           'farbe': rf.choice(('gelb', 'weiss', 'blau', 'rosa'))})
        kb.schmetterlinge(img, falter, frame or 0)
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain.png'))
    print('Karte 04 %dx%d gebaut' % (cols, rows))
    return img


if __name__ == '__main__':
    bauen()
