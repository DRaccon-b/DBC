"""Casino-Karten 57-66 (Sondergebiet A0S): Grundriss + PixelLab-Wang-Tilesets + PixelLab-Objekte -> Standbild.

  python3 tools/casino_welt.py 57        # eine Karte
  python3 tools/casino_welt.py alle

Jede Karte hat eine eigene Struktur (Inseln, Hof, Kreuz, Zickzack, Raute, Terrassen, Wolken, Labyrinth, Boot, Hoehle).
Der Grundriss liegt auf dem Eckpunkt-Raster (Wang): Eckpunkt 0 = Hintergrund, 1 = Boden, 2 = Akzent. Kachel = vier Ecken.
Tileset A (Hintergrund/Boden) zeichnet alles, Tileset B (Boden/Akzent) darueber, wo eine Ecke Akzent ist (Akzent liegt
immer mind. 2 Eckpunkte im Boden, damit B nie an den Hintergrund stoesst). Ecken der Sets in 45 Grad (Regel 6b).
"""
import base64, io, json, math, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageFilter
import karte04_bauen as k4
from casino_themen import THEMEN

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
TS = os.path.join(ROOT, 'assets', 'tilesets', 'pixellab')
T = 16
k4.SCHATTEN = {'farbe': (20, 16, 30), 'dx': 0.3, 'dy': 0.15, 'kern': 110, 'wurf': (70, 48)}


# ------------------------------------------------------------------ Grundrisse (Eckpunkt-Raster, Kachelkoordinaten)
def _seg(X, Y, a, b, w):
    (x0, y0), (x1, y1) = a, b
    dx, dy = x1 - x0, y1 - y0
    t = np.clip(((X - x0) * dx + (Y - y0) * dy) / float(dx * dx + dy * dy), 0, 1)
    return np.hypot(X - (x0 + t * dx), Y - (y0 + t * dy)) <= w


def _box(X, Y, x0, y0, x1, y1, fase=0):
    m = (X >= x0) & (X <= x1) & (Y >= y0) & (Y <= y1)
    if fase:                                                           # abgeschraegte Ecken (45 Grad)
        cx, cy, hx, hy = (x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2, (y1 - y0) / 2
        m &= (np.abs(X - cx) + np.abs(Y - cy)) <= hx + hy - fase
    return m


def struktur(art, C, R, seed):
    Y, X = np.mgrid[0:R + 1, 0:C + 1].astype(np.float32)
    F = np.zeros(X.shape, bool)
    A = np.zeros(X.shape, bool)
    tp = None
    if art == 'inseln':
        sat = [(9, 8), (37, 8), (9, 23), (37, 23)]
        F |= np.hypot(X - 23, Y - 15) <= 7.2
        A |= np.hypot(X - 23, Y - 15) <= 4.3
        for (x, y) in sat:
            F |= np.hypot(X - x, Y - y) <= 4.6
            A |= np.hypot(X - x, Y - y) <= 2.2
            F |= _seg(X, Y, (23, 15), (x, y), 1.6)
        F |= _seg(X, Y, (23, 15), (23, 29), 1.6) | (np.hypot(X - 23, Y - 28.5) <= 2.6)
        tp = (22, 27)
    elif art == 'hof':
        F |= _box(X, Y, 4, 3, 42, 27, fase=5) | _box(X, Y, 20, 26, 26, 31)
        A |= _box(X, Y, 20, 6, 26, 24) | _box(X, Y, 8, 12, 38, 18)
        tp = (22, 29)
    elif art == 'kreuz':
        F |= _box(X, Y, 15, 9, 31, 25, fase=3) | _box(X, Y, 3, 14, 43, 20) | _box(X, Y, 20, 2, 26, 33)
        F |= _box(X, Y, 1, 11, 10, 23, fase=2) | _box(X, Y, 36, 11, 45, 23, fase=2) | _box(X, Y, 17, 0.5, 29, 8, fase=2)
        A |= np.hypot(X - 23, Y - 17) <= 5.2
        A |= _box(X, Y, 3, 15, 8, 19) | _box(X, Y, 38, 15, 43, 19)
        tp = (22, 31)
    elif art == 'zickzack':
        plat = [(8, 8), (20, 18), (31, 8), (41, 18)]
        for (x, y) in plat:
            F |= _box(X, Y, x - 5.5, y - 4.5, x + 5.5, y + 4.5, fase=3)
            A |= _box(X, Y, x - 3, y - 2, x + 3, y + 2)
        for a, b in zip(plat, plat[1:]):
            F |= _seg(X, Y, a, b, 1.6)
        F |= _seg(X, Y, (20, 18), (20, 29), 1.6) | _box(X, Y, 17, 26, 23, 31, fase=1)
        tp = (19, 28)
    elif art == 'raute':
        F |= (np.abs(X - 22) + np.abs(Y - 16)) <= 15.5
        F |= _box(X, Y, 19, 28, 25, 33)
        A |= (np.abs(X - 22) + np.abs(Y - 16)) <= 8
        for (x, y) in ((22, 5), (11, 16), (33, 16)):
            A |= (np.abs(X - x) + np.abs(Y - y)) <= 2.5
        tp = (21, 31)
    elif art == 'terrassen':
        F |= _box(X, Y, 3, 3, 28, 18, fase=2) | _box(X, Y, 18, 12, 43, 27, fase=2) | _box(X, Y, 5, 19, 16, 28, fase=2)
        F |= _box(X, Y, 8, 16, 14, 21) | _box(X, Y, 27, 26, 33, 31)
        A |= _box(X, Y, 6, 6, 24, 14) | _box(X, Y, 22, 16, 40, 23)
        tp = (29, 29)
    elif art == 'wolken':
        kreise = [(12, 10, 6.2), (23, 14, 7.2), (34, 9, 5.6), (36, 22, 5.6), (13, 23, 5.2), (23, 27, 3.8),
                  (18, 11, 3.5), (30, 17, 3.5), (18, 20, 3.5)]
        for (x, y, r) in kreise:
            F |= np.hypot(X - x, Y - y) <= r
        A |= np.hypot(X - 23, Y - 14) <= 4.2
        A |= np.hypot(X - 12, Y - 10) <= 2.6
        A |= np.hypot(X - 36, Y - 22) <= 2.6
        tp = (22, 26)
    elif art == 'labyrinth':
        for y in (5, 15, 25):
            F |= _box(X, Y, 3, y - 1.5, 43, y + 1.5)
        for x, (y0, y1) in ((5, (5, 25)), (17, (5, 15)), (29, (15, 25)), (41, (5, 25)), (17, (20, 25)), (29, (5, 10))):
            F |= _box(X, Y, x - 1.5, y0, x + 1.5, y1)
        for (x, y) in ((5, 5), (41, 5), (5, 25), (41, 25)):
            F |= _box(X, Y, x - 3.5, y - 2.5, x + 3.5, y + 2.5)
        F |= _box(X, Y, 15, 10, 31, 20, fase=2) | _box(X, Y, 21, 25, 25, 31)
        A |= _box(X, Y, 18, 12.5, 28, 17.5)
        A |= _box(X, Y, 4, 14, 14, 16) | _box(X, Y, 32, 14, 42, 16)
        tp = (22, 29)
    elif art == 'boot':
        sx = np.where(X > 25, ((X - 25) / 23.0), ((25 - X) / 21.0))
        rumpf = (np.abs(sx) ** 2.2 + (np.abs(Y - 12) / 8.5) ** 4) <= 1
        F |= rumpf | _box(X, Y, 21, 19, 27, 27)
        A |= (np.abs(sx / 0.62) ** 2.2 + (np.abs(Y - 12) / 4.6) ** 4) <= 1
        tp = (23, 25)
    elif art == 'hoehle':
        rs = np.random.RandomState(seed)
        w = np.arctan2(Y - 16, X - 22)
        rr = 1 + 0.12 * np.sin(3 * w + 1.3) + 0.08 * np.sin(5 * w + 0.4) + 0.05 * np.sin(7 * w + 2.1)
        F |= ((X - 22) / 17.5) ** 2 + ((Y - 15.5) / 12.5) ** 2 <= rr ** 2
        F |= _box(X, Y, 19, 25, 25, 33)
        for (x, y) in ((12, 10), (32, 10), (10, 20), (34, 21)):              # Felssaeulen in der Hoehle (Hintergrund)
            F &= ~(np.hypot(X - x, Y - y) <= 1.8)
        A |= np.hypot(X - 22, Y - 15) <= 5.5
        A |= np.hypot(X - 22, Y - 6) <= 2.2
        tp = (21, 31)
    # Glaetten: keine Einzel-Eckpunkte (sonst runde Punkte/Kerben am 45-Grad-Raster)
    for _ in range(2):
        F = _oeffnen_schliessen(F)
    inner = F.copy()
    for _ in range(2):                                                  # Akzent mind. 2 Eckpunkte im Boden
        p = np.pad(inner, 1)
        inner = inner & p[:-2, 1:-1] & p[2:, 1:-1] & p[1:-1, :-2] & p[1:-1, 2:] & p[:-2, :-2] & p[:-2, 2:] & p[2:, :-2] & p[2:, 2:]
    A = _oeffnen_schliessen(A & inner) & inner
    V = F.astype(np.uint8) + A.astype(np.uint8)
    return V, tp


def _oeffnen_schliessen(m):
    im = Image.fromarray(m.astype(np.uint8) * 255)
    im = im.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.MaxFilter(3))      # oeffnen
    im = im.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.MinFilter(3))      # schliessen
    return np.array(im) > 0


GROESSE = {'inseln': (46, 32), 'hof': (46, 32), 'kreuz': (46, 34), 'zickzack': (48, 32), 'raute': (44, 34),
           'terrassen': (46, 32), 'wolken': (46, 32), 'labyrinth': (46, 32), 'boot': (50, 28), 'hoehle': (44, 34)}


# ------------------------------------------------------------------ Wang-Tilesets
def wang(name):
    d = json.load(open(os.path.join(TS, name + '.json')))
    tab = {}
    for t in d['tileset']['tiles']:
        c = t['corners']
        key = tuple(c[k] == 'upper' for k in ('NW', 'NE', 'SW', 'SE'))
        tab[key] = Image.open(io.BytesIO(base64.b64decode(t['image']['base64']))).convert('RGBA')
    return tab


def malen(V, schwelle, tab, nur_wo=None, seed=0):
    R, C = V.shape[0] - 1, V.shape[1] - 1
    ts = next(iter(tab.values())).size
    img = Image.new('RGBA', (C * T, R * T + (ts[1] - T)), (0, 0, 0, 0))
    rs = random.Random(seed)
    for y in range(R):
        for x in range(C):
            ecken = (V[y, x] >= schwelle, V[y, x + 1] >= schwelle, V[y + 1, x] >= schwelle, V[y + 1, x + 1] >= schwelle)
            if nur_wo is not None and not any(nur_wo[y:y + 2, x:x + 2].ravel()):
                continue
            t = tab.get(ecken)
            if t is None:
                continue
            if all(ecken) or not any(ecken):                          # volle Kacheln: gespiegelt fuer weniger Wiederholung
                if rs.random() < 0.5:
                    t = t.transpose(Image.FLIP_LEFT_RIGHT)
            img.alpha_composite(t, (x * T, y * T))
    return img.crop((0, 0, C * T, R * T))


# ------------------------------------------------------------------ Objekte
def sprite(nr, datei):
    im = Image.open(os.path.join(ROOT, 'assets', 'objekte', 'karte%d' % nr, datei)).convert('RGBA')
    a = np.array(im)
    a[a[..., 3] < 128] = 0
    im = Image.fromarray(a)
    return im.crop(im.getbbox())


def platzieren(nr, V, tp, rs):
    namen = json.load(open(os.path.join(ROOT, 'assets', 'objekte', 'karte%d' % nr, 'namen.json')))
    R, C = V.shape[0] - 1, V.shape[1] - 1
    geh = np.zeros((R, C), bool)
    akz = np.zeros((R, C), bool)
    for y in range(R):
        for x in range(C):
            geh[y, x] = (V[y:y + 2, x:x + 2] >= 1).all()
            akz[y, x] = (V[y:y + 2, x:x + 2] >= 2).all()
    frei = np.zeros((R, C), bool)                                      # Teleporter + Umkreis frei
    frei[max(0, tp[1] - 3):tp[1] + 3, max(0, tp[0] - 2):tp[0] + 4] = True
    rects, objekte = [], []

    def versuche(name, tx, ty, extra=None):
        im = sprite(nr, namen[name])
        wt = -(-im.width // T)
        cx = tx * T + (wt * T) / 2.0 if wt % 2 == 0 else tx * T + T / 2.0
        x = int(round(cx - im.width / 2.0))
        fy = ty * T + T - 1
        y = fy - im.height + 1
        r = (x, y, x + im.width - 1, fy)
        if r[0] < 0 or r[1] < 0 or r[2] >= C * T or r[3] >= R * T:
            return False
        if any(not (r[2] + 2 < q[0] or q[2] + 2 < r[0] or r[3] + 2 < q[1] or q[3] + 2 < r[1]) for q in rects):
            return False
        x0, x1 = r[0] // T, r[2] // T
        unten = range(max(0, (fy - min(im.height, 2 * T) + 1) // T), ty + 1)    # untere zwei Reihen auf Boden
        for yy in unten:
            for xx in range(x0, x1 + 1):
                if not geh[yy, xx] or frei[yy, xx]:
                    return False
        rects.append(r)
        o = {'datei': namen[name], 'basis': name, 'x': x, 'y': y, 'fuss': im.height - 1, 'kachel': [tx, ty], 'ebene': 1}
        o.update(extra or {})
        objekte.append(o)
        return True

    zellen = [(x, y) for y in range(R) for x in range(C)]
    # 1) Zentrum: Mitte der groessten Akzentflaeche
    ys, xs = np.nonzero(akz)
    if len(ys):
        cx0, cy0 = int(round(xs.mean())), int(round(ys.mean()))
    else:
        ys, xs = np.nonzero(geh); cx0, cy0 = int(round(xs.mean())), int(round(ys.mean()))
    for d in range(0, 6):
        if any(versuche('zentrum', cx0 + dx, cy0 + d) for dx in (0, -1, 1)):
            break
    # 2) Automaten an den Nordkanten (Boden darueber endet), mit Abstand
    kand = [(x, y + 1) for (x, y) in zellen if y + 1 < R and geh[y, x] and (y == 0 or not geh[y - 1, x]) and geh[y + 1, x]]
    rs.shuffle(kand)
    n = 0
    for (x, y) in sorted(kand, key=lambda p: (p[1], p[0])):
        if n >= 10:
            break
        if versuche('automat', x, y):
            n += 1
    # 3) Spieltische auf Akzent (sonst Boden), weit auseinander
    kand = [p for p in zellen if akz[p[1], p[0]]] or [p for p in zellen if geh[p[1], p[0]]]
    rs.shuffle(kand)
    n = 0
    for (x, y) in kand:
        if n >= 4:
            break
        if versuche('tisch', x, y):
            n += 1
    # 4) Lichter als Paar beidseits des Weges zum Teleporter + weitere Paare gespiegelt zur Kartenachse
    mx = C / 2.0
    paare = 0
    for (x, y) in sorted([p for p in zellen if geh[p[1], p[0]] and p[0] < mx - 1], key=lambda p: -p[1]):
        if paare >= 3:
            break
        x2 = int(round(2 * mx - 1 - x))
        if 0 <= x2 < C and geh[y, x2] and abs(y - tp[1]) < 10:
            if versuche('licht', x, y):
                if versuche('licht', x2, y):
                    paare += 1
                else:
                    rects.pop(); objekte.pop()
    # 5) Deko locker verteilt (keine Reihen, abwechselnd)
    kand = [p for p in zellen if geh[p[1], p[0]] and not akz[p[1], p[0]]]
    rs.shuffle(kand)
    n = 0
    for (x, y) in kand:
        if n >= 10:
            break
        if versuche(('deko1', 'deko2')[n % 2], x, y):
            n += 1
    return objekte, geh


def bauen(nr):
    th = THEMEN[nr]
    art = th['struktur']
    C, R = GROESSE[art]
    V, tp = struktur(art, C, R, nr)
    A, B = wang('casino%d_a' % nr), wang('casino%d_b' % nr)
    img = malen(V, 1, A, seed=nr)
    img.alpha_composite(malen(V, 2, B, nur_wo=(V >= 2), seed=nr + 1))
    karte = os.path.join(ROOT, 'maps', 'karte%d' % nr)
    os.makedirs(karte, exist_ok=True)
    a = np.array(img.convert('RGB'))
    k4.teleporter_zeichnen(a, tp[0], tp[1], 2, 2, None)
    img = Image.fromarray(a).convert('RGBA')
    img.save(os.path.join(karte, 'terrain_basis.png'))
    objekte, geh = platzieren(nr, V, tp, random.Random(nr * 7))
    boden = np.kron(geh, np.ones((T, T), bool))
    cache = {o['datei']: sprite(nr, o['datei']) for o in objekte}
    objekte.sort(key=lambda o: o['y'] + o['fuss'])
    k4.objekte_zeichnen(img, objekte, cache, boden, None)
    img.save(os.path.join(karte, 'terrain.png'))
    json.dump({'name': th['name'], 'struktur': art, 'groesse': [C, R], 'ecken': V.tolist(),
               'teleporter': [{'x': tp[0], 'y': tp[1], 'b': 2, 'h': 2}]},
              open(os.path.join(karte, 'layout.json'), 'w'))
    obj = os.path.join(ROOT, 'assets', 'objekte', 'karte%d' % nr)
    json.dump(objekte, open(os.path.join(obj, 'platzierung.json'), 'w'), indent=0)
    print('Karte %d %s (%s) %dx%d, %d Objekte' % (nr, th['name'], art, C, R, len(objekte)))


if __name__ == '__main__':
    arg = sys.argv[1]
    for n in (sorted(THEMEN) if arg == 'alle' else [int(arg)]):
        bauen(n)
