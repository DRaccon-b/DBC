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
N_FRAMES = 16
COLS, ROWS = 100, 90
H = k4.H
weich, zell_maske = k4.weich, k4.zell_maske
k4.FELS['heilig'] = ['#3c4048', '#545a64', '#6e7480', '#8a909a', '#a6abb4', '#c2c6cc', '#dcdfe3']
LIPPE_GRAS = ['#2e6a3a', '#3e8444', '#56a04e', '#6eb85a', '#8ccc6a', '#a8dc82']
LIPPE_SCHNEE = ['#90a6bc', '#b0c4d6', '#cad9e6', '#dfe9f2', '#f0f6fb', '#ffffff']
LIPPE_FELS = ['#5a606a', '#727882', '#8c929c', '#a6abb4', '#bcc0c6', '#d2d5da']


def R(cls, art, x0, y0, x1, y1):
    cls[y0:y1 + 1, x0:x1 + 1] = art


def layout():
    yy, xx = np.mgrid[0:ROWS, 0:COLS]
    cls = np.full((ROWS, COLS), 'o')              # o = Wolken
    hoehe = np.zeros((ROWS, COLS), int)
    # Insel-Umriss (leicht wellig) und Hoehen
    insel = (xx >= 3) & (xx <= 97) & (yy >= 2) & (yy <= 86)
    welle = (np.sin(yy / 3.1) + np.sin(xx / 2.7)) > 1.4
    insel &= ~(((xx <= 3) | (xx >= 97) | (yy <= 2) | (yy >= 86)) & welle)
    insel &= ~((xx >= 68) & (xx <= 73) & (yy <= 26))            # Wolkenspalt zwischen Gipfel und Schreinplateau
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
                             (72, 51, 81, 54), (64, 13, 68, 15),
                             (18, 60, 89, 63), (18, 63, 21, 74), (44, 63, 47, 85), (68, 63, 71, 85), (21, 82, 90, 85),
                             (84, 63, 86, 70)):
        m = (xx >= x0) & (xx <= x1) & (yy >= y0) & (yy <= y1) & insel
        cls[m & ~np.isin(cls, list('p'))] = 'w'
    # Teefelder (Heckenreihen), Hoefe unten
    for (x0, y0, x1, y1) in ((26, 64, 43, 81), (49, 64, 67, 81), (72, 64, 83, 80)):
        R(cls, 't', x0, y0, x1, y1)
    R(cls, 'p', 4, 76, 21, 87)
    R(cls, 'p', 85, 63, 96, 80)
    R(cls, 'p', 5, 62, 11, 66)
    cls[~insel] = 'o'
    hoehe[~insel] = 0
    lay = {'groesse': [COLS, ROWS], 'klassen': [''.join(r) for r in cls],
           'hoehe': [''.join(str(v) for v in r) for r in hoehe],
           'treppen': [[22, 26, 22, 26], [60, 64, 26, 30], [17, 21, 55, 60], [72, 76, 55, 60]],
           'bruecke': [67, 12, 74, 14],
           'teleporter': [{'x': 7, 'y': 86, 'b': 4, 'h': 1}]}
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


def roter_zaun(img, stuecke):
    """Roter Holzzaun (Schreinstil) mit dunkler Kontur: Pfosten mit Kappe je Kachel, zwei Querlatten.
    stuecke: (x0, x1, y, 'h') waagerecht oder (x, y0, y1, 'v') senkrecht (von oben gesehen)."""
    px = img.load()
    K = (0x3a, 0x10, 0x10)
    ROT = [(0x7a, 0x1c, 0x1c), (0xa8, 0x2a, 0x26), (0xd0, 0x3e, 0x34), (0xec, 0x66, 0x52)]
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
            p(x + dx, yb - h - 1, K); p(x + dx, yb - h - 2, (0x2a, 0x2e, 0x36))
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


def bauen(frame=None, speichern=True):
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cls = lay['klassen']
    hoehe = np.array([[int(c) for c in r] for r in lay['hoehe']])
    Wp, Hp = COLS * T, ROWS * T
    a = wolken(frame)
    insel = weich(zell_maske([''.join('1' if v >= 1 else '0' for v in r) for r in hoehe], '1', COLS, ROWS), 5, 0.3, 20)
    gras = flaeche(kacheln(os.path.join(ROOT, 'assets', 'basis', 'gras_%d.png'), 5))
    a[insel] = gras[insel]
    schnee = flaeche(kacheln(os.path.join(ROOT, 'assets', 'karte05', 'basis', 's_%d.png'), 5))
    fels = flaeche(kacheln(os.path.join(ROOT, 'assets', 'karte05', 'basis', 'r_%d.png'), 5))
    weg = flaeche(kacheln(os.path.join(ROOT, 'assets', 'karte04', 'basis', 'w_%d.png'), 5))
    pflaster = flaeche(kacheln(os.path.join(ROOT, 'assets', 'karte03', 'basis', 'kies_%d.png'), 5, grau))
    for art, tex, blur, rausch, seed in (('n', schnee, 5, 0.45, 3), ('f', fels, 4, 0.4, 4), ('r', pflaster, 2.5, 0.2, 5),
                                         ('w', weg, 7, 0.5, 6)):
        m = weich(zell_maske(cls, art, COLS, ROWS), blur, rausch, seed) & insel
        a[m] = tex[m]
    pm = weich(zell_maske(cls, 'p', COLS, ROWS), 1.2, 0, 7) & insel
    a[pm] = pflaster[pm]
    rand = pm & ~(np.roll(pm, 1, 0) & np.roll(pm, -1, 0) & np.roll(pm, 1, 1) & np.roll(pm, -1, 1))
    a[rand] = H('#4a505a')
    tm = weich(zell_maske(cls, 't', COLS, ROWS), 1.5, 0, 8) & insel
    teefeld(a, tm, frame)
    # Hoehenkanten: Insel -> Wolken (tiefe Felsfront), Stufen 1->2->3 mit Treppen
    m1 = insel
    m2 = weich(zell_maske([''.join('1' if v >= 2 else '0' for v in r) for r in hoehe], '1', COLS, ROWS), 4, 0.25, 21)
    m3 = weich(zell_maske([''.join('1' if v >= 3 else '0' for v in r) for r in hoehe], '1', COLS, ROWS), 4, 0.25, 22)
    frei = np.zeros((Hp, Wp), bool)
    treppen = []
    for (x0, x1, y0, y1) in lay['treppen']:
        frei[y0 * T:(y1 + 1) * T, x0 * T - 6:(x1 + 1) * T + 6] = True
        treppen.append((x0, x1, y0, y1))
    k4.hoehenkanten(a, m3, 'heilig', 48, 8, LIPPE_SCHNEE, frei, 13, berg=True)
    k4.hoehenkanten(a, m2, 'heilig', 48, 8, LIPPE_GRAS, frei, 12, berg=True)
    k4.hoehenkanten(a, m1, 'heilig', 64, 8, LIPPE_GRAS, np.zeros((Hp, Wp), bool), 11, berg=True)
    img = Image.fromarray(a).convert('RGBA')
    alt = bauwerke.S
    bauwerke.S = [H(c) + (255,) for c in k4.FELS['heilig']]
    for (x0, x1, y0, y1) in treppen:
        spalte = (x0 + x1) // 2
        stufe = m3 if any(hoehe[y, spalte] == 3 for y in range(y0, y1 + 1)) else m2
        col = stufe[:, spalte * T + 8]
        kante = [y for y in range(y0 * T, (y1 + 1) * T) if col[y] and not col[min(Hp - 1, y + 1)]]
        if kante:
            ye = kante[0]
            bauwerke.zeichne_treppe(img, x0 * T, (x1 + 1) * T, ye + 2, ye + 50)
    bauwerke.S = alt
    bx0, by0, bx1, by1 = lay['bruecke']
    bauwerke.zeichne_bruecke(img, bx0 * T, (bx1 + 1) * T, by0 * T + 2, (by1 + 1) * T - 2, frame=frame or 0, wasser=False)
    a = np.array(img.convert('RGB'))
    for tp in lay['teleporter']:
        k4.teleporter_zeichnen(a, tp['x'], tp['y'], tp['b'], tp['h'], frame)
    img = Image.fromarray(a).convert('RGBA')
    roter_zaun(img, [(77, 96, 4, 'h'), (77, 96, 24, 'h'), (96, 4, 24, 'v'), (71, 77, 31, 'h'), (83, 89, 31, 'h'),
                     (96, 63, 80, 'v')])
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain_basis.png'))
    pf = os.path.join(OBJ, 'platzierung.json')
    if os.path.exists(pf):
        objs = sorted((o for o in json.load(open(pf)) if os.path.exists(os.path.join(OBJ, o['datei']))),
                      key=lambda o: o['y'] + o['fuss'])
        cache = {o['datei']: Image.open(os.path.join(OBJ, o['datei'])).convert('RGBA') for o in objs}
        k4.objekte_zeichnen(img, objs, cache, insel, frame)
        k4.animieren(img, objs, cache, frame or 0)
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
