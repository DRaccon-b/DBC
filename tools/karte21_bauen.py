"""Karte 21 - Digi-Egg Valley (A02), Gelaende im Stil von Karte 20 / Karte 06.

Bausteine: Gras/Sand aus Karte 01 (assets/basis), weiche Raender (Karte 04), Fluss im vertieften Wasserstil (wie
Karte 20, laeuft links und rechts aus der Karte), drei Holzbruecken in Nord-Sued-Richtung, grauer Kopfsteinplatz
(Kiesel von Karte 03 grau umgefaerbt), Ruinenplatten mit niedriger Bruchsteinfront, eingesenkter Schreinhof mit
Rueckwand und Treppe, Burgmauer (Bruchstein, 3 Kacheln hoch) mit Hoehlentor und zwei Steintreppen, Lager auf Sand.

  python3 tools/karte21_layout.py && python3 tools/karte21_bauen.py
"""
import json, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
import karte_bauen as kb
import karte04_bauen as k4
import karte06_bauen as k6
import karte20_bauen as k20

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte21')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte21')
T = 16
N_FRAMES = 4                     # Regel: hoechstens 4 Animationsbilder
BILDDAUER = 250
k4.N_FRAMES = N_FRAMES
import karte_bauen as _kb
_kb.N_FRAMES = N_FRAMES                       # Windwelle (Pflanzen) ueber die 4 Bilder der Karte
H = k4.H
weich, zell_maske, flaeche = k4.weich, k4.zell_maske, k20.flaeche
BURG = ['#1c222c', '#2a323e', '#3c4554', '#505a6a', '#667182', '#808b9a', '#a0a9b6']   # Bruchstein dunkel -> hell
k4.FELS['burg'] = BURG
MAUER_H = 48                     # Burgmauer: 3 Kacheln
RUINE_H = 12                     # Front der Ruinenplatten
HOF_H = 24                       # Rueckwand des Schreinhofs


def grau(a):                     # Kiesel aus Karte 03 -> graues Kopfsteinpflaster (Vorlage)
    l = a.mean(axis=2, keepdims=True) / 255.0
    lo, hi = np.array([88, 96, 106], np.float32), np.array([196, 202, 208], np.float32)
    return lo + (hi - lo) * np.clip((l - 0.25) / 0.6, 0, 1)


def bruchstein(a, m, seed, hell=0, reihe=10):
    """Bruchsteinmauer frontal: Reihen aus unregelmaessig breiten Steinen (9-15 px), je Stein Licht oben/links,
    Schatten unten/rechts, dunkle Fuge, abgerundete Ecken, feine Koernung. hell verschiebt die Toene."""
    rnd = random.Random(seed)
    F = [np.array(H(c), np.float32) for c in BURG]
    ys, xs = np.nonzero(m)
    if not len(ys):
        return
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    rs = np.random.RandomState(seed)
    y = y0
    r = 0
    while y < y1:
        h = reihe if r % 3 else reihe - 1
        x = x0 - rnd.randint(0, 12)
        while x < x1:
            w = rnd.randint(10, 18)
            t = min(5, max(1, rnd.choice((3, 4, 4, 3, 5, 4)) + hell))
            for yy in range(y, min(y + h, y1)):
                for xx in range(max(x, x0), min(x + w, x1)):
                    if not m[yy, xx]:
                        continue
                    dy, dx = yy - y, xx - x
                    ex, ey = min(dx, w - 1 - dx), min(dy, h - 1 - dy)
                    ecke = ex + ey < 2                              # runde Ecken (Bruchstein)
                    if dy == h - 1 or dx == w - 1 or ecke:
                        c = F[0]
                    elif dy == h - 2 or dx == w - 2 or (ex + ey == 2 and (dy > h // 2 or dx > w // 2)):
                        c = F[max(1, t - 2)]
                    elif dy == 0 or dx == 0 or ex + ey == 2:
                        c = F[min(6, t + 1)]
                    elif dy == 1 and dx < w - 4:
                        c = (F[t] + F[min(6, t + 1)]) / 2
                    else:
                        c = F[t] * (0.94 + 0.12 * rs.rand())
                    a[yy, xx] = c
            x += w
        y += h
        r += 1


MAUER_STIL = os.environ.get('K21_MAUER', 'karte01')   # karte01 (gewaehlt) | bruch | fels | quader | feldstein | pfeiler | moos
import klippen, bauwerke
if MAUER_STIL == 'karte01':                              # Klippen von Karte 01: Schiefer-Blautoene fuer Mauer, Tor, Kanten
    BURG = list(klippen.SCHIEFER)
    k4.FELS['burg'] = BURG
TOR_MITTE = 45.5 * 16                                   # Achse des Hoehlentors (Rhythmus der Pfeiler)


def _box(m):
    ys, xs = np.nonzero(m)
    return ys.min(), ys.max() + 1, xs.min(), xs.max() + 1


def fels_mauer(a, m, seed, hell=0):
    """Natuerliche Felswand wie die Klippen der anderen Karten (Karte 04), in den Burgtoenen."""
    y0, y1, x0, x1 = _box(m)
    tex = k4.fels_textur('burg', x1 - x0, y1 - y0, seed)
    sub = m[y0:y1, x0:x1]
    a[y0:y1, x0:x1][sub] = tex[:y1 - y0, :x1 - x0][sub]


def quader_mauer(a, m, seed, hell=0, bh=12, bw=24):
    """Glatte Quadermauer: grosse behauene Bloecke im Verband, Fase oben/links hell, unten/rechts dunkel,
    feine Fuge, vereinzelt Abplatzer."""
    rnd = random.Random(seed)
    F = [np.array(H(c), np.float32) for c in BURG]
    y0, y1, x0, x1 = _box(m)
    rs = np.random.RandomState(seed)
    for r, y in enumerate(range(y0, y1, bh)):
        off = (bw // 2) * (r % 2)
        for bx in range(x0 - off, x1, bw):
            t = min(5, max(2, rnd.choice((4, 4, 3, 5, 4)) + hell))
            for yy in range(y, min(y + bh, y1)):
                for xx in range(max(bx, x0), min(bx + bw, x1)):
                    if not m[yy, xx]:
                        continue
                    dy, dx = yy - y, xx - bx
                    if dy == bh - 1 or dx == bw - 1:
                        c = F[1]
                    elif dy == bh - 2 or dx == bw - 2:
                        c = F[t - 2]
                    elif dy <= 1 or dx == 0:
                        c = F[t + 1]
                    else:
                        c = F[t] * (0.97 + 0.06 * rs.rand())
                    a[yy, xx] = c
            if rnd.random() < 0.25:                                # Abplatzer
                cx, cy = bx + rnd.randint(4, bw - 6), y + rnd.randint(3, bh - 4)
                if x0 <= cx < x1 - 2 and m[cy, cx]:
                    a[cy, cx] = F[t - 2]; a[cy, cx + 1] = F[t - 1]; a[cy + 1, cx] = F[t + 1]


def feldstein_mauer(a, m, seed, hell=0):
    """Feldsteinmauer: runde, unterschiedlich grosse Steine dicht gepackt (wie die Vorlage), dunkle Fugen,
    jeder Stein kugelig schattiert (Licht oben links)."""
    rnd = random.Random(seed)
    F = [np.array(H(c), np.float32) for c in BURG]
    y0, y1, x0, x1 = _box(m)
    sub = np.zeros((y1 - y0, x1 - x0, 3), np.float32)
    sub[:] = F[1]
    yy, xx = np.mgrid[0:y1 - y0, 0:x1 - x0]
    for r, cy in enumerate(range(4, y1 - y0 + 6, 9)):
        cx = -rnd.randint(0, 6) + (5 if r % 2 else 0)
        while cx < x1 - x0 + 8:
            rx, ry = rnd.uniform(5.0, 7.5), rnd.uniform(4.0, 5.2)
            px, py = cx + rnd.uniform(-1, 1), cy + rnd.uniform(-1, 1)
            t = min(5, max(2, rnd.choice((3, 4, 4, 5, 3)) + hell))
            d = ((xx - px) / rx) ** 2 + ((yy - py) / ry) ** 2
            inn = d <= 1.0
            licht = (-(xx - px) / rx - (yy - py) / ry) * 0.5           # oben links hell
            ton = np.clip(t + np.round(licht * 1.6 + (d > 0.7) * -1), 1, 6).astype(int)
            for k in range(1, 7):
                sel = inn & (ton == k)
                sub[sel] = F[k]
            cx += 2 * rx + rnd.uniform(0.5, 1.5)
    s_ = m[y0:y1, x0:x1]
    a[y0:y1, x0:x1][s_] = sub[s_]


def pfeiler_mauer(a, m, seed, hell=0, pfeiler=True):
    """Burgmauer aus kleinen Ziegelsteinen (16x8) mit Wandpfeilern im festen Rhythmus (alle 8 Kacheln,
    symmetrisch zum Tor): Pfeiler heller, nach rechts Schlagschatten auf die Mauer."""
    F = [np.array(H(c), np.float32) for c in BURG]
    y0, y1, x0, x1 = _box(m)
    rs = np.random.RandomState(seed)
    for y in range(y0, y1):
        r = (y - y0) // 8
        for x in range(x0, x1):
            if not m[y, x]:
                continue
            dy = (y - y0) % 8
            dx = (x + 8 * (r % 2)) % 16
            t = 3 + ((x + 8 * (r % 2)) // 16 * 7 + r * 3) % 3 % 2 + hell
            if dy == 7 or dx == 15:
                c = F[1]
            elif dy == 0:
                c = F[t + 1]
            else:
                c = F[t] * (0.96 + 0.08 * rs.rand())
            a[y, x] = c
    if not pfeiler or y1 - y0 < 30:
        return
    k = 0
    xs = sorted({int(TOR_MITTE + s * 128 * i) for i in range(1, 8) for s in (-1, 1)})
    for px in xs:
        p0, p1 = px - 6, px + 6
        if p0 < x0 or p1 > x1 or not m[y0 + 10, p0:p1].all():
            continue
        for y in range(y0, y1):
            for x in range(p0, p1):
                dx = x - p0
                dy = (y - y0) % 12
                c = F[5] if dx < 2 else F[2] if dx >= 10 else F[4]
                if dy == 11:
                    c = F[2]
                a[y, x] = c
            for d, f in ((0, 0.6), (1, 0.72), (2, 0.86)):                # Schatten rechts auf die Mauer
                a[y, p1 + d] = (a[y, p1 + d] * f).astype(np.uint8)
        a[y0:y0 + 2, p0 - 1:p1 + 1] = F[6]                              # Kapitell
        a[y0 + 2, p0 - 1:p1 + 1] = F[2]


def moos_mauer(a, m, seed, hell=0):
    """Alte Ruinenmauer: grosse, unregelmaessige Bloecke, Risse, Moos waechst aus den Fugen und von der Krone."""
    bruchstein(a, m, seed, hell, reihe=13)
    rnd = random.Random(seed + 3)
    MOOS = [np.array(H(c), np.float32) for c in ('#2e4a22', '#3e6228', '#567e34', '#74a044')]
    y0, y1, x0, x1 = _box(m)
    for _ in range(int((x1 - x0) * (y1 - y0) / 180)):                   # Moospolster
        cx, cy = rnd.randint(x0, x1 - 1), rnd.randint(y0, y1 - 1)
        if rnd.random() < 0.5:
            cy = y0 + rnd.randint(0, 6)
        r = rnd.uniform(1.5, 4.0)
        for yy in range(int(cy - r), int(cy + r) + 1):
            for xx in range(int(cx - r * 1.4), int(cx + r * 1.4) + 1):
                if y0 <= yy < y1 and x0 <= xx < x1 and m[yy, xx]:
                    d = ((xx - cx) / (r * 1.4)) ** 2 + ((yy - cy) / r) ** 2
                    if d <= 1 and rnd.random() < 1.1 - d * 0.6:
                        k = 3 if (yy - cy) < -r * 0.3 else 2 if d < 0.5 else 1
                        a[yy, xx] = MOOS[k] if rnd.random() > 0.15 else MOOS[0]
    for _ in range(int((x1 - x0) / 60) + 1):                            # Risse
        x, y = rnd.randint(x0 + 4, x1 - 5), rnd.randint(y0 + 2, y1 - 10)
        for i in range(rnd.randint(6, 12)):
            if m[y, x]:
                a[y, x] = H(BURG[0])
                if x + 1 < x1:
                    a[y, x + 1] = (a[y, x + 1] * 0.8).astype(np.uint8)
            y += 1; x += rnd.choice((-1, 0, 0, 1))
            if y >= y1 or not (x0 <= x < x1):
                break


def k01_mauer(a, m, seed, runen=True):
    """Klippenwand genau wie Karte 01 (klippen.wand): Schiefersaeulen, Schichtfugen, vereinzelte Cyan-Runen."""
    y0, y1, x0, x1 = _box(m)
    w = np.array(klippen.wand(x1 - x0, y1 - y0, random.Random(seed), rune_chance=0.12 if runen else 0.0).convert('RGB'))
    sub = m[y0:y1, x0:x1]
    a[y0:y1, x0:x1][sub] = w[sub]


def mauer_textur(a, m, seed, hell=0, pfeiler=False):
    if not m.any():
        return
    if MAUER_STIL == 'karte01':
        k01_mauer(a, m, seed, runen=pfeiler)
    elif MAUER_STIL == 'fels':
        fels_mauer(a, m, seed, hell)
    elif MAUER_STIL == 'quader':
        quader_mauer(a, m, seed, hell)
    elif MAUER_STIL == 'feldstein':
        feldstein_mauer(a, m, seed, hell)
    elif MAUER_STIL == 'pfeiler':
        pfeiler_mauer(a, m, seed, hell, pfeiler)
    elif MAUER_STIL == 'moos':
        moos_mauer(a, m, seed, hell)
    else:
        bruchstein(a, m, seed, hell)


def mauerkrone(a, y, x0, x1):
    """Abdeckung oben auf der Front je nach Stil."""
    if MAUER_STIL == 'fels':
        return                                                        # Felsen: Lippe kommt aus der Textur
    if MAUER_STIL == 'karte01':                                       # wie Karte 01: Graskante; unter Stein eine Steinkante
        a[y:y + 2, x0:x1] = np.array([H(BURG[5]), H(BURG[1])])[:, None, :]
        img = Image.fromarray(a).convert('RGBA')
        rnd = random.Random(17)
        gruen = np.ones(a.shape[1], bool)
        for d in range(1, 7):                                        # nur wo darueber wirklich Wiese liegt
            gruen &= (a[y - d, :, 1].astype(int) > a[y - d, :, 0].astype(int) + 12)
        x = x0
        while x < x1:
            if gruen[x]:
                e = x
                while e < x1 and gruen[e]:
                    e += 1
                klippen.graskante(img, x, e, y, rnd)
                x = e
            else:
                x += 1
        a[:] = np.array(img.convert('RGB'))
        return
    if MAUER_STIL == 'quader':
        a[y:y + 4, x0:x1] = np.array([H(BURG[6]), H(BURG[5]), H(BURG[5]), H(BURG[2])])[:, None, :]
        for x in range(x0, x1, 32):
            a[y:y + 4, x] = H(BURG[3])
        return
    if MAUER_STIL == 'pfeiler':
        a[y:y + 3, x0:x1] = np.array([H(BURG[6]), H(BURG[4]), H(BURG[1])])[:, None, :]
        return
    a[y:y + 3, x0:x1] = np.array([H(BURG[5]), H(BURG[6]), H(BURG[3])])[:, None, :]
    for x in range(x0, x1, 8):
        a[y:y + 3, x] = H(BURG[2])


def kontaktschatten(a, m, n=3, f=0.62):
    """Schatten unter einer Front (nach Sueden) auf den Boden darunter."""
    unten = m & ~np.roll(m, -1, 0)
    for y, x in zip(*np.nonzero(unten)):
        for d in range(1, n + 1):
            if y + d < a.shape[0] and not m[y + d, x]:
                a[y + d, x] = (a[y + d, x] * (f + (1 - f) * (d - 1) / n)).astype(np.uint8)


def kante_rund(m):
    return m & ~(np.roll(m, 1, 0) & np.roll(m, -1, 0) & np.roll(m, 1, 1) & np.roll(m, -1, 1))


def bruecke_ns(img, x0, x1, y0, y1, seed=5):
    """Holzbruecke in Nord-Sued-Richtung (von oben): quer liegende Planken (4 px) mit Lichtkante und dunkler Fuge,
    seitliche Balken mit Pfostenkoepfen an den Enden, Schatten nach rechts aufs Wasser."""
    rnd = random.Random(seed)
    a = np.array(img.convert('RGB'))
    HOLZ = [H(c) for c in ('#3a220f', '#5c3818', '#7a4c24', '#9a6432', '#b67c44', '#d29c60')]
    K = H('#26160a')
    for y in range(y0 + 2, y1 + 2):                              # Schatten rechts aufs Wasser/Ufer
        for d, f in ((0, 0.55), (1, 0.66), (2, 0.8)):
            if x1 + d < a.shape[1]:
                a[y, x1 + d] = (a[y, x1 + d] * f).astype(np.uint8)
    y = y0
    i = 0
    while y < y1:
        b = 4 if i % 5 else 5
        ton = rnd.choice((3, 3, 4, 2))
        versatz = rnd.randint(-1, 1)
        for yy in range(y, min(y + b, y1)):
            for x in range(x0 + 3 + versatz, x1 - 3 + versatz + 1):
                if not (x0 + 3 <= x < x1 - 3):
                    continue
                dy = yy - y
                c = HOLZ[0] if dy == b - 1 else HOLZ[ton + 1] if dy == 0 else HOLZ[ton]
                if dy not in (0, b - 1) and (x * 7 + yy * 3 + i) % 13 == 0:
                    c = HOLZ[ton - 1]                                # Maserung
                a[yy, x] = c
        y += b
        i += 1
    for (bx, links) in ((x0, True), (x1 - 3, False)):              # Laengsbalken
        for y in range(y0, y1):
            for k in range(3):
                c = (HOLZ[4], HOLZ[3], HOLZ[1])[k] if links else (HOLZ[3], HOLZ[2], HOLZ[1])[k]
                a[y, bx + k] = c
        a[y0:y1, bx - 1 if links else bx + 3] = K
    for py in (y0 + 1, y1 - 7):                                     # Pfostenkoepfe an den vier Ecken
        for px_ in (x0 - 1, x1 - 5):
            a[py:py + 6, px_:px_ + 6] = K
            a[py + 1:py + 5, px_ + 1:px_ + 5] = HOLZ[3]
            a[py + 1, px_ + 1:px_ + 5] = HOLZ[5]
            a[py + 1:py + 5, px_ + 1] = HOLZ[4]
            a[py + 4, px_ + 2:px_ + 5] = HOLZ[1]
    img.paste(Image.fromarray(a).convert('RGBA'), (0, 0))


def hoehlentor(a, x0, x1, ytop, ybot, seed=7, boden=None, hinten=None):
    """Offenes Tor in der Burgmauer: runder Bogen aus Bogensteinen; durch die Oeffnung sieht man hindurch -
    vorn laeuft der Sandweg hinein, dahinter liegt das Pflaster des Platzes. Laibung links im Licht, rechts im
    Schatten, unter dem Bogen ein weicher Schatten (keine dunkle Flaeche)."""
    F = [np.array(H(c), np.float32) for c in BURG]
    cx = (x0 + x1) / 2.0
    hw = (x1 - x0) / 2.0 - 6                                       # halbe Oeffnungsbreite
    oben = ytop + 4
    yy, xx = np.mgrid[ytop - 4:ybot, x0 - 4:x1 + 4]
    def innen(y, x, hw_, oben_):
        if abs(x - cx) > hw_:
            return False
        if y >= oben_ + hw_:
            return True
        return ((x - cx) / hw_) ** 2 + ((y - (oben_ + hw_)) / hw_) ** 2 <= 1.0
    for y in range(ytop - 4, ybot):
        for x in range(x0 - 4, x1 + 4):
            if innen(y, x, hw, oben):
                if x < cx - hw + 3 and y >= oben + hw:
                    c = F[4] if x < cx - hw + 2 else F[3]            # Laibung links (Licht)
                elif x > cx + hw - 3 and y >= oben + hw:
                    c = F[2] if x > cx + hw - 2 else F[1]            # Laibung rechts (Schatten)
                else:
                    c = (boden[y, x] if y >= ybot - 14 else hinten[y, x]).astype(np.float32)
                    if ybot - 16 <= y < ybot - 14:
                        c = c * 0.72                                 # Kante Weg -> Platz
                    tief = y - oben                                  # Schatten unter dem Bogen
                    rad = np.hypot(x - cx, max(0, (oben + hw) - y))
                    if y < oben + hw + 6:
                        c = c * (0.55 + 0.45 * min(1.0, (oben + hw + 6 - y) and (y - oben) / (hw + 6)))
                    if x < cx - hw + 7:
                        c = c * 0.85                                 # Schatten der linken Laibung
                a[y, x] = c
            elif innen(y, x, hw + 6, oben - 6) and y < ybot:
                # Bogensteine: Keile um die Oeffnung
                import math
                w = math.degrees(math.atan2(y - (oben + hw), x - cx))
                k = int((w + 180) // 22)
                rad = math.hypot(y - (oben + hw), x - cx)
                if y >= oben + hw:
                    k = (y - ytop) // 9 + (0 if x < cx else 50)
                t = 4 + (k % 2)
                c = F[t]
                if (y >= oben + hw and (y - ytop) % 9 == 8) or (y < oben + hw and (w + 180) % 22 < 1.5):
                    c = F[0]
                elif innen(y, x, hw + 1, oben - 1):
                    c = F[1]                                       # innere Laibung im Schatten
                elif not innen(y, x, hw + 5, oben - 5):
                    c = F[0]
                a[y, x] = c


def bauen(frame=None, speichern=True):
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cls = lay['klassen']
    cols, rows = lay['groesse']
    Wp, Hp = cols * T, rows * T
    basis = os.path.join(ROOT, 'assets', 'basis')
    gras = flaeche(k6.kacheln(os.path.join(basis, 'gras_%d.png'), 5), cols, rows)
    sand = flaeche(k6.kacheln(os.path.join(basis, 'sand_%d.png'), 5), cols, rows)
    a = gras.copy()
    # Waldboden
    wm = weich(zell_maske(cls, 'h', cols, rows), 5, 0.4, 3)
    a[wm] = (gras[wm] * np.array([0.62, 0.7, 0.66])).astype(np.uint8)
    # Sandwege und Lager (inkl. Ausgang)
    roh = zell_maske(cls, 'wet', cols, rows)
    m = weich(roh, 5.0, 0, 4)   # Regel 6b: 45-Grad-Kanten
    a[m] = sand[m]
    saum = weich(roh, 5.0, 0, 4, 0.28) & ~m
    a[saum] = (a[saum] * 0.9).astype(np.uint8)
    # Steinplatz (Kopfstein grau) mit Bordstein; Ruinen und Hof ebenfalls Stein
    kies = flaeche(k6.kacheln(os.path.join(ROOT, 'assets', 'karte03', 'basis', 'kies_%d.png'), 5, grau), cols, rows)
    pm = weich(zell_maske(cls, 'pq', cols, rows), 4, 0.12, 6)
    yk = (lay['mauer_kante'] + 1) * T                                 # Platz reicht buendig bis an die Mauerkrone
    for y in range(yk - 6, yk):
        pm[y] |= pm[yk - 7]
    a[pm] = kies[pm]
    a[kante_rund(pm)] = H('#4a5260')
    kontaktschatten(a, pm, 2, 0.8)
    # Ruinenplatten (Hoehe 2): Kacheln exakt, Oberseite helleres Pflaster, Front RUINE_H px Bruchstein
    sm = np.kron(np.array([[c == 's' for c in z] for z in cls]), np.ones((T, T), bool))
    top = sm & np.roll(sm, -RUINE_H, 0)
    a[sm] = np.clip(kies[sm].astype(np.int16) + 14, 0, 255).astype(np.uint8)
    front = sm & ~top
    mauer_textur(a, front, 31, hell=0)
    a[kante_rund(sm) & top] = H(BURG[1])
    a[top & ~np.roll(top, 1, 0)] = H(BURG[6])                       # Lichtkante oben
    a[top & ~np.roll(top, -1, 0) & sm] = H(BURG[5])                  # Kante zur Front
    for y, x in zip(*np.nonzero(sm & ~np.roll(sm, -1, 1))):          # Schatten nach rechts
        for d, f in ((1, 0.62), (2, 0.78)):
            if x + d < Wp and not sm[y, x + d]:
                a[y, x + d] = (a[y, x + d] * f).astype(np.uint8)
    kontaktschatten(a, sm, 3)
    # Schreinhof (eingesenkt): Rueckwand HOF_H px, Boden dunkleres Pflaster, Seiten schmale Kontur, Treppe im Sueden
    hx0, hy0, hx1, hy1 = lay['hof']
    hm = np.zeros((Hp, Wp), bool)
    hm[hy0 * T:(hy1 + 1) * T, hx0 * T:(hx1 + 1) * T] = True
    a[hm] = (kies[hm] * 0.84).astype(np.uint8)
    rw = np.zeros_like(hm)
    rw[hy0 * T:hy0 * T + HOF_H, hx0 * T:(hx1 + 1) * T] = True
    mauer_textur(a, rw, 41, hell=-1)
    a[hy0 * T:hy0 * T + 2, hx0 * T:(hx1 + 1) * T] = H(BURG[6])       # Mauerkrone (Lichtkante)
    a[hy0 * T + 2, hx0 * T:(hx1 + 1) * T] = H(BURG[2])
    yb = (hy1 + 1) * T
    a[hy0 * T:yb, hx0 * T] = H(BURG[1]); a[hy0 * T:yb, hx0 * T + 1] = H(BURG[5])          # West: Kontur
    a[hy0 * T:yb, (hx1 + 1) * T - 1] = H(BURG[0]); a[hy0 * T:yb, (hx1 + 1) * T - 2] = H(BURG[3])
    for d, f in ((2, 0.6), (3, 0.7), (4, 0.82)):                     # Schatten der Westkante in den Hof
        a[hy0 * T + HOF_H:yb, hx0 * T + d] = (a[hy0 * T + HOF_H:yb, hx0 * T + d] * f).astype(np.uint8)
    for d, f in ((0, 0.55), (1, 0.7), (2, 0.85)):                    # Kontaktschatten am Fuss der Rueckwand
        a[hy0 * T + HOF_H + d, hx0 * T + 2:(hx1 + 1) * T - 2] = (a[hy0 * T + HOF_H + d, hx0 * T + 2:(hx1 + 1) * T - 2] * f).astype(np.uint8)
    a[yb - 2, hx0 * T:(hx1 + 1) * T] = H(BURG[2]); a[yb - 1, hx0 * T:(hx1 + 1) * T] = H(BURG[6])   # Suedkante (Stufe hoch)
    # Fluss: vertieftes Wasser; laeuft links und rechts aus der Karte -> Bild dort 24 px erweitern
    import wasser_vertieft
    xm_roh = zell_maske(cls, 'x', cols, rows)
    for (bx0, bx1) in lay['bruecken']:                              # unter den Bruecken fliesst das Wasser weiter
        for x in range(bx0, bx1 + 1):
            ys = [y for y in range(rows) if cls[y][x] == 'b']
            xm_roh[(ys[0] + 1) * T:ys[-1] * T, x * T:(x + 1) * T] = 1.0
    xm = weich(xm_roh, 4, 0.15, 8, 0.45)
    P = 24
    ag = np.pad(a, ((0, 0), (P, P), (0, 0)), mode='edge')
    mg = np.pad(xm, ((0, 0), (P, P)), mode='edge')
    ag = np.array(wasser_vertieft.vertiefen(Image.fromarray(ag), np.ones_like(mg), frame, maske=mg).convert('RGB'))
    a = ag[:, P:-P].copy()
    # Burgmauer: Front MAUER_H px unter der Oberkante (Reihe mauer_kante) ueber die ganze Breite
    mk = lay['mauer_kante']
    ym0, ym1 = (mk + 1) * T, (mk + 1) * T + MAUER_H
    mauer = np.zeros((Hp, Wp), bool)
    mauer[ym0:ym1, :] = True
    mauer_textur(a, mauer, 51, hell=0, pfeiler=True)
    mauerkrone(a, ym0, 0, Wp)
    kontaktschatten(a, mauer, 4, 0.55)
    # Treppen in der Burgmauer (frontal, wie Karte 04) und Hoehlentor
    for (sx0, sx1) in lay['treppen']:
        if MAUER_STIL == 'karte01':                                   # Treppe wie Karte 01
            img_ = Image.fromarray(a).convert('RGBA')
            bauwerke.zeichne_treppe(img_, sx0 * T, (sx1 + 1) * T, ym0, ym1 + 1, seed=sx0)
            a[:] = np.array(img_.convert('RGB'))
        else:
            k4.treppe(a, sx0 * T, (sx1 + 1) * T, ym0 - 1, 's', MAUER_H - 4, 'burg', sand)
    gx0, gx1 = lay['tor']
    hoehlentor(a, gx0 * T, (gx1 + 1) * T, ym0, ym1, boden=sand, hinten=kies)
    img = Image.fromarray(a).convert('RGBA')
    for (bx0, bx1) in lay['bruecken']:
        ys = [y for y in range(rows) if cls[y][bx0] == 'b']
        bruecke_ns(img, bx0 * T, (bx1 + 1) * T, ys[0] * T + 6, (ys[-1] + 1) * T - 6, seed=bx0)
    a = np.array(img.convert('RGB'))
    for tp in lay.get('teleporter', []):
        k4.teleporter_zeichnen(a, tp['x'], tp['y'], tp['b'], tp['h'], frame)
    img = Image.fromarray(a).convert('RGBA')
    # Hoehenebenen fuer Schatten: Lager 1, Oberland 2, Ruinen 3, Hof 2 (Rueckwand 9), Mauer 9, Wasser 7
    lvl = np.ones((Hp, Wp), np.uint8)
    lvl[:ym0] = 2
    lvl[sm & top] = 3
    wand = mauer.copy()
    wand[front] = True
    wand[rw] = True
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain_basis.png'))
        np.save(os.path.join(KARTE, 'wasser.npy'), np.packbits(xm))
        np.save(os.path.join(KARTE, 'pixelhoehe.npy'), lvl)
    pf = os.path.join(OBJ, 'platzierung.json')
    if os.path.exists(pf):
        objs = sorted((o for o in json.load(open(pf)) if os.path.exists(os.path.join(OBJ, o['datei']))),
                      key=lambda o: o['y'] + o['fuss'])
        if objs:
            cache = {o['datei']: Image.open(os.path.join(OBJ, o['datei'])).convert('RGBA') for o in objs}
            ebenen = lvl.copy().astype(np.int16)
            ebenen[wand] = 9
            ebenen[xm] = 7
            k4.objekte_zeichnen(img, objs, cache, ~xm & ~wand, frame, ebenen=ebenen)
            k4.animieren(img, objs, cache, frame or 0)
            k6.animieren_k6(img, objs, cache, frame or 0)
            kb.laternen_licht(img, [o for o in objs if o.get('anim') == 'laterne'], frame)
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain.png'))
    print('Karte 21 %dx%d gebaut' % (cols, rows))
    return img


if __name__ == '__main__':
    bauen()
