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
    (36.0, 28.5, 9.2, 7.6),     # Brunnenplatz (Mitte = Brunnenmitte)
    (58.5, 11.0, 8.6, 7.4),     # Portalplatz
]
TEICH = (38.5, 48.0, 6.5, 4.2)
CYBER = (51, 41, 65, 53)        # Cyber-Datenplatz (Rechteck, Ecken gerundet)
PENSION = (5, 40, 29, 54)       # umzaeunt (Zaun auf dem Rand), Tor oben bei x 18..21
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
    cls[((xx - 17.5) / 6.5) ** 2 + ((yy - 47.5) / 4.0) ** 2 <= 1] = 's'
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
    """Holzzaun im Handheld-Stil: kraeftige Pfosten (mittig je Kachel, Kappe, Licht links), zwei breite
    Querlatten mit Lichtkante und dunkler Unterkante, Schatten nach rechts unten. Seiten: Pfosten mit
    senkrechten Latten. Tor oben (offen, zwei dickere Torpfosten)."""
    px = img.load()
    HOLZ = [(0x3a, 0x22, 0x14), (0x5e, 0x3a, 0x20), (0x84, 0x54, 0x2e), (0xa8, 0x72, 0x40), (0xc8, 0x92, 0x58),
            (0xe4, 0xb6, 0x7a)]
    x0, y0, x1, y1 = rect
    W, Hh = img.size

    def p(x, y, c):
        if 0 <= x < W and 0 <= y < Hh:
            px[x, y] = c + (255,)

    def schatten(x, y, f=0.72):
        if 0 <= x < W and 0 <= y < Hh:
            r, g, b, a = px[x, y]
            px[x, y] = (int(r * f), int(g * f), int(b * f), a)

    def latte(xa, xb, y):                       # waagerechte Latte, 4 px hoch
        for x in range(xa, xb):
            p(x, y, HOLZ[5]); p(x, y + 1, HOLZ[4]); p(x, y + 2, HOLZ[3]); p(x, y + 3, HOLZ[1])
            if (x - xa) % 9 == 4:
                p(x, y + 1, HOLZ[2])            # Maserung
            schatten(x + 1, y + 5, 0.8)

    def pfosten(x, yb, h=17, dick=False):
        b = 3 if dick else 2
        for y in range(yb - h, yb + 1):
            for dx in range(-b, b + 1):
                c = HOLZ[0] if abs(dx) == b else HOLZ[4] if dx < 0 else HOLZ[3] if dx == 0 else HOLZ[2]
                p(x + dx, y, c)
        for dx in range(-b, b + 1):            # Kappe
            p(x + dx, yb - h - 1, HOLZ[5] if dx <= 0 else HOLZ[4])
            p(x + dx, yb - h - 2, HOLZ[0] if abs(dx) == b else HOLZ[5])
        for dx in range(-b + 1, b + 3):        # Kontaktschatten
            schatten(x + dx, yb + 1, 0.7); schatten(x + dx + 1, yb + 2, 0.82)

    for ty in (y0, y1):                        # oben und unten
        yb = ty * T + 14
        for tx in range(x0, x1):
            if ty == y0 and tor[0] - 1 <= tx <= tor[1]:
                continue
            latte(tx * T + 8, (tx + 1) * T + 8, yb - 12)
            latte(tx * T + 8, (tx + 1) * T + 8, yb - 6)
        for tx in range(x0, x1 + 1):
            if ty == y0 and tor[0] <= tx <= tor[1]:
                continue
            pfosten(tx * T + 8, yb, dick=(ty == y0 and tx in (tor[0] - 1, tor[1] + 1)))
    for tx in (x0, x1):                        # Seiten: senkrechte Doppellatte, Pfosten je Kachel
        X = tx * T + 8
        for y in range(y0 * T + 14, y1 * T + 2):
            for dx, c in ((-3, HOLZ[0]), (-2, HOLZ[4]), (-1, HOLZ[3]), (1, HOLZ[3]), (2, HOLZ[2]), (3, HOLZ[0])):
                p(X + dx, y, c)
            p(X, y, HOLZ[1])
            schatten(X + 4, y, 0.78)
        for ty in range(y0 + 1, y1):
            pfosten(X, ty * T + 14)


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
    for art, blur, rausch, seed in (('w', 7.0, 0.5, 4), ('s', 4.0, 0.4, 5)):
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


ROST = [(0x2a, 0x1a, 0x12), (0x4a, 0x2e, 0x1c), (0x6e, 0x46, 0x28), (0x8e, 0x5c, 0x34), (0xb0, 0x76, 0x44),
        (0xd2, 0x96, 0x5a)]


def zahnrad(img, cx, cy, frame, r_aussen=20, r_innen=16, zaehne=10):
    """Rostiges Zahnrad frontal (10 Zaehne, 5 Speichen), dreht sich 72 Grad je 16 Frames (nahtlos). Licht oben links."""
    px = img.load()
    teil = 2 * math.pi / zaehne
    phase = frame / N_FRAMES * 2 * teil              # 2 Zahnteilungen = 1 Speichenteilung (5 Speichen) je Schleife
    for y in range(cy - r_aussen - 1, cy + r_aussen + 2):
        for x in range(cx - r_aussen - 1, cx + r_aussen + 2):
            dx, dy = x - cx + 0.5, y - cy + 0.5
            r = math.hypot(dx, dy)
            if r > r_aussen + 0.5:
                continue
            w = math.atan2(dy, dx) - phase
            licht = -(dx + dy) / max(r, 1) * 0.7                       # -1 (Schatten) .. +1 (Licht)
            c = None
            if r > r_innen:                                            # Zahnkranz
                if ((w % teil) / teil) < 0.5:
                    c = ROST[3] if licht > 0.2 else ROST[2]
                    if r > r_aussen - 1:
                        c = ROST[1]
            elif r > r_innen - 4:                                      # Ring
                c = ROST[4] if licht > 0.3 else ROST[3] if licht > -0.3 else ROST[2]
                if r > r_innen - 1:
                    c = ROST[1]
            elif r < 5:                                                # Nabe
                c = ROST[5] if r < 2 and licht > 0 else ROST[4] if licht > 0 else ROST[2]
                if r > 4:
                    c = ROST[1]
            else:                                                      # Speichen (4) und Loecher
                sp_t = 2 * math.pi / 5
                ws = (math.atan2(dy, dx) - phase) % sp_t
                if min(ws, sp_t - ws) * r < 2.6:
                    c = ROST[3] if licht > 0 else ROST[2]
                else:
                    c = ROST[0]
            if c is not None:
                px[x, y] = c + (255,)
            elif r <= r_aussen + 0.5:
                px[x, y] = ROST[0] + (255,)                            # Nische hinter den Zahnluecken


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
        elif anim == 'brunnen':                    # nur das Wasser: faellt aus den Schalen, plaetschert im Becken
            a = np.array(sp).astype(np.int16)
            r0, g0, b0 = a[..., 0], a[..., 1], a[..., 2]       # nur helles Wasser, nicht der tuerkise Stein
            m = (((g0 >= 180) & (b0 >= 190)) | ((b0 >= 150) & (b0 > g0 + 20) & (b0 > r0 + 40))) & (a[..., 3] > 0)
            ys, xs = np.nonzero(m)
            if not len(xs):
                continue
            basis = a[..., :3].copy()
            cx = xs.mean()
            for y, x in zip(ys, xs):
                # fallende Straehnen: Helligkeitsband wandert nach unten; im Becken: Ringe laufen nach aussen
                stroem = math.sin(2 * math.pi * (y / 7.0 - frame / N_FRAMES * 2) + x * 0.9)
                ring = math.sin(2 * math.pi * (abs(x - cx) / 9.0 - frame / N_FRAMES * 2) + y * 0.5)
                welle = stroem if (y < sp.height * 0.62) else ring
                f = 1.0 + 0.16 * welle
                r_, g_, b_ = basis[y, x]
                X, Y = o['x'] + x, o['y'] + y
                px[X, Y] = (min(255, max(0, int(r_ * f))), min(255, max(0, int(g_ * f))), min(255, max(0, int(b_ * f + 6 * welle))), 255)
        elif anim == 'werkstatt':                  # Zahnrad an der Fassade dreht sich (jedes Frame neu gezeichnet)
            zahnrad(img, o['x'] + 2 + 47, o['y'] + 50, frame)
            px = img.load()
        elif anim == 'schmiede':                   # Schornstein raucht, Ofen flackert
            a = np.array(sp).astype(np.int16)
            m = (a[..., 0] > 200) & (a[..., 1] > 70) & (a[..., 1] < 210) & (a[..., 2] < 110) & (a[..., 3] > 0)
            m[:50] = False
            f = 0.8 + 0.3 * math.sin(frame * 2.1) * math.sin(frame * 0.7 + 1)
            ys, xs = np.nonzero(m)
            for y, x in zip(ys, xs):
                X, Y = o['x'] + x, o['y'] + y
                r_, g_, b_, _ = px[X, Y]
                px[X, Y] = (min(255, int(r_ * f + 10)), min(255, int(g_ * f)), min(255, int(b_ * f * 0.9)), 255)
            if len(xs):
                glut = Image.new('RGBA', img.size, (0, 0, 0, 0))
                gd = ImageDraw.Draw(glut)
                fx, fy = o['x'] + xs.mean(), o['y'] + ys.mean()
                for rr, al in ((16, 26), (9, 40)):
                    gd.ellipse((fx - rr, fy - rr * 0.7, fx + rr, fy + rr * 0.7), fill=(255, 150, 60, int(al * f)))
                img.alpha_composite(glut)
                px = img.load()
            rauch = Image.new('RGBA', img.size, (0, 0, 0, 0))
            rd = ImageDraw.Draw(rauch)
            sx, sy = o['x'] + 2 + 87, o['y'] + 2
            for k in range(4):
                t = ((frame + k * 4) % N_FRAMES) / N_FRAMES
                rr = 3 + t * 7
                x = sx + t * 14 + 2 * math.sin(t * 6 + k)
                y = sy - t * 34
                al = int(225 * (1 - t) ** 0.7)
                rd.ellipse((x - rr, y - rr, x + rr, y + rr), fill=(214, 214, 222, al))
                rd.ellipse((x - rr * 0.5 - 1, y - rr * 0.6 - 1, x + rr * 0.3, y), fill=(240, 240, 246, al))
            img.alpha_composite(rauch)
            px = img.load()
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
