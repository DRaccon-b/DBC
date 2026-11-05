"""Karte 06 - Startkarte (Dorf): Wald ringsum (Ausgang rechts), Fernseh-Portal, Blockhuette, Schrott-
Werkstatt, Meeres-Schmiede, Ring-Portal-Platz, Riesenbrunnen mit Laternen, Pension mit Spielplatz und
Datenbaum, Teich mit Steg, Cyber-Datenplatz.

  python3 tools/karte06_bauen.py layout    # Raster -> maps/karte06/layout.json (von Hand definiert)
  python3 tools/karte06_objekte.py         # Objekte (alle am 16x16-Raster)
  python3 tools/karte06_bauen.py           # -> maps/karte06/terrain.png

Bausteine: Gras/Sand/Wasser aus Karte 01, Kiesel aus Karte 03 (umgefaerbt), Betonplatten aus Karte 02,
weiche Raender und Schatten aus Karte 04, vertieftes Wasser (wasser_vertieft), Steg/Teleporter, Laternen.
"""
import json, math, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import karte_bauen as kb
import karte04_bauen as k4
import bauwerke

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte06')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte06')
T = 16
N_FRAMES = 16
COLS, ROWS = 72, 60
H = k4.H
weich, zell_maske = k4.weich, k4.zell_maske

# ---------------------------------------------------------------- Layout
WEGE = [  # (x0, y0, x1, y1) Kacheln, Sandwege
    (8, 21, 60, 24),            # Hauptweg oben
    (8, 15, 11, 21),            # zum Fernseher
    (20, 13, 23, 21),           # zur Blockhuette
    (32, 13, 35, 21),           # zur Werkstatt
    (43, 14, 46, 21),           # zur Schmiede
    (57, 17, 60, 33),           # vom Portalplatz nach Sueden
    (24, 24, 27, 39),           # links am Brunnenplatz
    (44, 24, 47, 52),           # rechts am Brunnenplatz, runter zum Cyberplatz
    (18, 36, 47, 39),           # unten am Brunnenplatz
    (18, 36, 21, 41),           # zur Pension
    (39, 39, 42, 43),           # zum Steg
    (44, 29, 71, 33),           # Ausgang rechts
]
PLAETZE = [  # (cx, cy, rx, ry) Ellipsen, Kopfstein
    (35.5, 30.5, 9.2, 7.6),     # Brunnenplatz
    (58.5, 11.0, 8.6, 7.4),     # Portalplatz
]
TEICH = (38.5, 48.0, 6.5, 4.2)
CYBER = (51, 41, 65, 53)        # Cyber-Datenplatz (Rechteck, Ecken gerundet)
PENSION = (6, 41, 26, 54)       # umzaeunt (Zaun auf dem Rand), Tor oben bei x 18..21
PENSION_TOR = (18, 21)
AUSGANG = (29, 33)              # Zeilen des Ausgangs rechts


def layout():
    yy, xx = np.mgrid[0:ROWS, 0:COLS]
    cls = np.full((ROWS, COLS), 'g')
    # Waldrand: rundlich, 3-6 Kacheln breit, Ausgang rechts frei
    rs = np.random.RandomState(6)
    rand = 3.6 + 1.3 * np.sin(xx / 4.3 + 1) * np.cos(yy / 5.1) + 0.9 * np.sin((xx + yy) / 2.7)
    d = np.minimum(np.minimum(xx, COLS - 1 - xx), np.minimum(yy, ROWS - 1 - yy))
    wald = d < rand
    wald &= ~((xx >= COLS - 8) & (yy >= AUSGANG[0]) & (yy <= AUSGANG[1]))
    cls[wald] = 'h'
    for (cx, cy, rx, ry) in PLAETZE:
        cls[((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2 <= 1] = 'p'
    for (x0, y0, x1, y1) in WEGE:
        m = (xx >= x0) & (xx <= x1) & (yy >= y0) & (yy <= y1)
        cls[m & (cls != 'p')] = 'w'
    x0, y0, x1, y1 = CYBER
    cls[(xx >= x0) & (xx <= x1) & (yy >= y0) & (yy <= y1)] = 'c'
    cx, cy, rx, ry = TEICH
    cls[((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2 <= 1] = 'x'
    x0, y0, x1, y1 = PENSION                      # Spielplatz: Sandflaeche in der Mitte der Pension
    cls[((xx - 18) / 5.5) ** 2 + ((yy - 48) / 3.6) ** 2 <= 1] = 's'
    lay = {'groesse': [COLS, ROWS], 'klassen': [''.join(r) for r in cls],
           'pension': PENSION, 'pension_tor': PENSION_TOR, 'teich': TEICH,
           'steg': [40, 43, 41, 47], 'teleporter': [{'x': 70, 'y': 30, 'b': 2, 'h': 3}]}
    json.dump(lay, open(os.path.join(KARTE, 'layout.json'), 'w'), indent=0)
    print('Layout', COLS, ROWS)


# ---------------------------------------------------------------- Texturen
def kacheln(pfad, n, umfaerben=None):
    ks = []
    for v in range(n):
        im = Image.open(pfad % v).convert('RGB')
        a = np.array(im).astype(np.float32)
        if umfaerben is not None:
            a = umfaerben(a)
        ks.append(np.clip(a, 0, 255).astype(np.uint8))
    return ks


def flaeche(ks):
    t = np.zeros((ROWS * T, COLS * T, 3), np.uint8)
    for y in range(ROWS):
        for x in range(COLS):
            t[y * T:(y + 1) * T, x * T:(x + 1) * T] = ks[kb.variante(x, y) % len(ks)]
    return t


def beige(a):                                   # Kiesel aus Karte 03 -> warmes Kopfsteinpflaster
    l = a.mean(axis=2, keepdims=True) / 255.0
    lo, hi = np.array([150, 120, 86], np.float32), np.array([246, 226, 190], np.float32)
    return lo + (hi - lo) * np.clip((l - 0.25) / 0.6, 0, 1)


def kabel_netz(a, m, frame):
    """Blaue und rote Kabel auf dem Plattenboden: Strecken entlang der Plattenfugen, Lichtpulse wandern."""
    rs = random.Random(3)
    Hh, W = m.shape
    ys, xs = np.nonzero(m)
    y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    farben = [(H('#1f3f8f'), H('#3e7ae0'), H('#9cd0ff')), (H('#7a1e24'), H('#d23a3a'), H('#ffb0a0'))]
    fr = frame or 0
    for i in range(14):
        dunkel, mitte, puls = farben[i % 2]
        if i % 3 == 0:                         # waagerecht
            y = rs.randrange(y0 + 6, y1 - 6) // 4 * 4
            pts = [(x, y + int(1.5 * math.sin(x / 9.0 + i))) for x in range(x0 + 4, x1 - 4)]
        else:                                   # senkrecht
            x = rs.randrange(x0 + 6, x1 - 6) // 4 * 4
            pts = [(x + int(1.5 * math.sin(y / 9.0 + i)), y) for y in range(y0 + 4, y1 - 4)]
        for k, (x, y) in enumerate(pts):
            if not m[y, x]:
                continue
            a[y, x] = mitte
            a[min(Hh - 1, y + 1), x] = dunkel
            if (k - fr * 6) % 48 < 3:
                a[y, x] = puls
            if 0 <= y + 2 < Hh and m[y + 2, x]:
                a[y + 2, x] = (a[y + 2, x] * 0.8).astype(np.uint8)


def zaun(img, rect, tor):
    """Holzzaun auf dem Rand des Rechtecks (Kacheln), Pfosten mittig je Kachel, zwei Querlatten; Tor oben."""
    px = img.load()
    HOLZ = [(0x4a, 0x2e, 0x1c), (0x6e, 0x46, 0x28), (0x94, 0x64, 0x3a), (0xb8, 0x86, 0x50), (0xd6, 0xa8, 0x6c)]
    x0, y0, x1, y1 = rect

    def p(x, y, c):
        if 0 <= x < img.width and 0 <= y < img.height:
            px[x, y] = c + (255,)

    def schatten(x, y):
        if 0 <= x < img.width and 0 <= y < img.height:
            r, g, b, a = px[x, y]
            px[x, y] = (int(r * 0.72), int(g * 0.74), int(b * 0.72), a)

    def latte_waagerecht(xa, xb, y):
        for x in range(xa, xb):
            p(x, y - 1, HOLZ[4]); p(x, y, HOLZ[3]); p(x, y + 1, HOLZ[2]); p(x, y + 2, HOLZ[1]); p(x, y + 3, HOLZ[0])
            schatten(x + 1, y + 5)

    def pfosten(x, yb, h=16):
        for y in range(yb - h, yb + 1):
            p(x - 2, y, HOLZ[0]); p(x - 1, y, HOLZ[4]); p(x, y, HOLZ[3]); p(x + 1, y, HOLZ[2]); p(x + 2, y, HOLZ[0])
        for dx in (-1, 0, 1):
            p(x + dx, yb - h - 1, HOLZ[4])
        schatten(x + 2, yb + 1); schatten(x + 3, yb + 1)

    for ty in (y0, y1):                       # oben und unten
        yb = ty * T + 13
        for tx in range(x0, x1 + 1):
            if ty == y0 and tor[0] <= tx <= tor[1]:
                continue
            xa, xb = tx * T, (tx + 1) * T
            if not (ty == y0 and tx + 1 == tor[0]):
                latte_waagerecht(xa + 8, xb + 8 if tx < x1 else xb - 8, yb - 9)
                latte_waagerecht(xa + 8, xb + 8 if tx < x1 else xb - 8, yb - 4)
            pfosten(xa + 8, yb)
    for tx in (x0, x1):                       # links und rechts: Pfosten mit senkrechter Latte
        X = tx * T + 8
        for ty in range(y0, y1 + 1):
            for y in range(ty * T + 2, (ty + 1) * T + 6):
                p(X - 1, y, HOLZ[3]); p(X, y, HOLZ[2]); p(X + 1, y, HOLZ[1])
            schatten(X + 2, ty * T + 8)
            pfosten(X, ty * T + 13)


# ---------------------------------------------------------------- Bauen
def bauen(frame=None, speichern=True):
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cls = lay['klassen']
    Wp, Hp = COLS * T, ROWS * T
    basis = os.path.join(ROOT, 'assets', 'basis')
    gras = flaeche(kacheln(os.path.join(basis, 'gras_%d.png'), 5))
    a = gras.copy()
    # Waldboden (dunkles Gras)
    wm = weich(zell_maske(cls, 'h', COLS, ROWS), 5, 0.4, 3)
    a[wm] = (gras[wm] * np.array([0.62, 0.7, 0.66])).astype(np.uint8)
    # Sandwege, Spielplatz-Sand
    sand = flaeche(kacheln(os.path.join(basis, 'sand_%d.png'), 5))
    for art, blur, rausch, seed in (('w', 3.5, 0.35, 4), ('s', 4.0, 0.4, 5)):
        roh = zell_maske(cls, art, COLS, ROWS)
        m = weich(roh, blur, rausch, seed)
        a[m] = sand[m]
        saum = weich(roh, blur, rausch, seed, 0.36) & ~m
        a[saum] = (a[saum] * 0.9).astype(np.uint8)
    # Kopfsteinplaetze mit Bordstein
    kies = flaeche(kacheln(os.path.join(ROOT, 'assets', 'karte03', 'basis', 'kies_%d.png'), 5, beige))
    pm = weich(zell_maske(cls, 'p', COLS, ROWS), 4, 0.12, 6)
    a[pm] = kies[pm]
    rand = pm & ~(np.roll(pm, 1, 0) & np.roll(pm, -1, 0) & np.roll(pm, 1, 1) & np.roll(pm, -1, 1))
    a[rand] = H('#8a6a48')
    unten = pm & ~np.roll(pm, -1, 0)
    for y, x in zip(*np.nonzero(unten)):
        for d in (1, 2):
            if y + d < Hp and not pm[y + d, x]:
                a[y + d, x] = (a[y + d, x] * 0.8).astype(np.uint8)
    # Cyber-Platz: Betonplatten aus Karte 02 (graublau), Bordstein, Kabel
    k2 = os.path.join(ROOT, 'assets', 'karte02', 'basis')
    platten = flaeche(kacheln(os.path.join(k2, 'platz_%d.png'), 3,
                              lambda a_: a_ * np.array([0.82, 0.88, 1.0]) + np.array([20, 24, 30])))
    cm = weich(zell_maske(cls, 'c', COLS, ROWS), 2.5, 0, 7)
    a[cm] = platten[cm]
    crand = cm & ~(np.roll(cm, 1, 0) & np.roll(cm, -1, 0) & np.roll(cm, 1, 1) & np.roll(cm, -1, 1))
    a[crand] = H('#3a4252')
    kabel_netz(a, cm & ~crand, frame)
    # Teich: vertieftes Wasser (Stil Karte 01) mit Erdrand
    import wasser_vertieft
    tm = weich(zell_maske(cls, 'x', COLS, ROWS), 6, 0.2, 8, 0.45)
    a = np.array(wasser_vertieft.vertiefen(Image.fromarray(a), np.ones_like(tm), frame, maske=tm).convert('RGB'))
    img = Image.fromarray(a).convert('RGBA')
    # Steg, Zaun, Teleporter
    sx0, sy0, sx1, sy1 = lay['steg']
    bauwerke.zeichne_steg(img, sx0 * T, (sx1 + 1) * T, sy0 * T, (sy1 + 1) * T - 5, frame=frame or 0)
    zaun(img, lay['pension'], lay['pension_tor'])
    a = np.array(img.convert('RGB'))
    for tp in lay.get('teleporter', []):
        k4.teleporter_zeichnen(a, tp['x'], tp['y'], tp['b'], tp['h'], frame)
    img = Image.fromarray(a).convert('RGBA')
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain_basis.png'))
        np.save(os.path.join(KARTE, 'wasser.npy'), np.packbits(tm))
    # Objekte
    pf = os.path.join(OBJ, 'platzierung.json')
    if os.path.exists(pf):
        objs = sorted((o for o in json.load(open(pf)) if os.path.exists(os.path.join(OBJ, o['datei']))),
                      key=lambda o: o['y'] + o['fuss'])
        cache = {o['datei']: Image.open(os.path.join(OBJ, o['datei'])).convert('RGBA') for o in objs}
        k4.objekte_zeichnen(img, objs, cache, ~tm, frame)
        k4.animieren(img, objs, cache, frame or 0)
        animieren_k6(img, objs, cache, frame or 0)
        kb.laternen_licht(img, [o for o in objs if o.get('anim') == 'laterne'], frame)
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain.png'))
    print('Karte 06 %dx%d gebaut' % (COLS, ROWS))
    return img


def animieren_k6(img, objs, cache, frame):
    """Portal/Fernseher wirbeln (Cyan-Pixel zyklisch), Brunnen glitzert, Datenfragmente um den Datenbaum."""
    px = img.load()
    for i, o in enumerate(objs):
        anim = o.get('anim')
        sp = cache[o['datei']]
        if anim == 'portal':
            a = np.array(sp).astype(np.int16)
            m = (a[..., 2] > 170) & (a[..., 1] > 140) & (a[..., 0] < 170) & (a[..., 3] > 0)
            ys, xs = np.nonzero(m)
            if not len(xs):
                continue
            cx, cy = xs.mean(), ys.mean()
            for y, x in zip(ys, xs):
                w = math.atan2(y - cy, x - cx) + math.hypot(x - cx, y - cy) / 6.0 - frame * 2 * math.pi / N_FRAMES
                f = 0.75 + 0.35 * math.sin(3 * w)
                X, Y = o['x'] + x, o['y'] + y
                r_, g_, b_, _ = px[X, Y]
                px[X, Y] = (min(255, int(r_ * f)), min(255, int(g_ * f + 20 * (f - 0.75))), min(255, int(b_ * f + 30 * (f - 0.75))), 255)
        elif anim == 'brunnen':
            a = np.array(sp).astype(np.int16)
            m = (a[..., 2] > a[..., 0] + 40) & (a[..., 3] > 0)
            ys, xs = np.nonzero(m)
            rs = random.Random(frame * 31 + i)
            for _ in range(max(1, len(xs) // 25)):
                k = rs.randrange(len(xs))
                X, Y = o['x'] + xs[k], o['y'] + ys[k]
                px[X, Y] = (235, 248, 255, 255)
        elif anim == 'daten':
            cx = o['x'] + sp.width // 2
            cy = o['y'] + sp.height // 2
            for k in range(10):
                t = ((frame + k * 1.6) % N_FRAMES) / N_FRAMES
                w = k * 2.4 + t * 2.0
                r = sp.width * 0.45 + 6 * math.sin(k)
                x = int(cx + r * math.cos(w)); y = int(cy - t * sp.height * 0.6 + r * 0.3 * math.sin(w))
                c = (120, 240, 255) if k % 2 else (150, 255, 170)
                al = 1 - t
                for dx in range(2):
                    for dy in range(2):
                        X, Y = x + dx, y + dy
                        if 0 <= X < img.width and 0 <= Y < img.height:
                            r_, g_, b_, _ = px[X, Y]
                            px[X, Y] = (int(r_ + (c[0] - r_) * al), int(g_ + (c[1] - g_) * al), int(b_ + (c[2] - b_) * al), 255)


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'layout':
        layout()
    else:
        bauen()
