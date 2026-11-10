"""Karte 23 - Harvest Hills (A02), Gelaende im Stil von Karte 20 / 21 (Bausteine Karte 01/04/06).

Gras/Sand aus Karte 01, weiche Raender, Waldboden, Hofboden (trockene Erde wie das Feld von Karte 20), sechs Aecker
mit Furchen (Karte 20), Teich mit Bach nach Sueden (vertieftes Wasser wie Karte 20), Plateau oben mit Erd-Felsfront,
Treppe und Hoehle (Karte 04), Terrassen oben rechts mit Steinfronten und drei Treppen, Senke unten rechts mit
Felsrand und Treppe, Maeuerchen, Hecken (Karte 04), Holzzaun (Karte 06), Teleporter an beiden Ausgaengen.

  python3 tools/karte23_layout.py && python3 tools/karte23_bauen.py
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
KARTE = os.path.join(ROOT, 'maps', 'karte23')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte23')
T = 16
N_FRAMES = 4
BILDDAUER = 250
k4.N_FRAMES = N_FRAMES
H = k4.H
weich, zell_maske, flaeche = k4.weich, k4.zell_maske, k20.flaeche
k4.FELS['stein'] = ['#2e2c2a', '#46423e', '#5e5952', '#77716a', '#908a82', '#aaa49a', '#c6c0b4']   # Steinmauern (Vorlage grau)
FRONT = 32


def maske_aus(cls, arten, cols, rows):
    return np.kron(np.array([[c in arten for c in z] for z in cls]), np.ones((T, T), bool))


def hoehen_px(lay):
    h = np.array([[int(c) for c in z] for z in lay['hoehe']])
    return np.kron(h, np.ones((T, T), int))


def maeuerchen(a, m, seed=3):
    """Niedrige Feldsteinmauer (1 Kachel): Deckstein hell, darunter Feldsteine, Kontaktschatten."""
    rnd = random.Random(seed)
    F = [np.array(H(c), np.float32) for c in k4.FELS['stein']]
    ys, xs = np.nonzero(m)
    for (y0, y1, x0, x1) in [(ys.min(), ys.max() + 1, xs.min(), xs.max() + 1)]:
        pass
    Hh, W = m.shape
    zeilen = sorted(set(ys // T))
    laeufe = []
    for ty in zeilen:                                                   # zusammenhaengende Stuecke je Reihe
        reihe = m[ty * T:(ty + 1) * T].any(axis=0)
        xs_ = np.nonzero(reihe)[0]
        start = xs_[0]
        for i in range(1, len(xs_) + 1):
            if i == len(xs_) or xs_[i] != xs_[i - 1] + 1:
                laeufe.append((ty, start, xs_[i - 1] + 1))
                if i < len(xs_):
                    start = xs_[i]
    for (ty, x0, x1) in laeufe:
        Y = ty * T + 3                                                  # Mauer 3..13 in der Kachel
        a[Y:Y + 3, x0:x1] = F[5]
        a[Y, x0:x1] = F[6]
        a[Y + 2, x0:x1] = F[3]
        x = x0
        r = 0
        while x < x1:
            w = rnd.randint(6, 10)
            t = rnd.choice((3, 4, 4, 5))
            for yy in range(Y + 3, Y + 10):
                for xx in range(x, min(x + w, x1)):
                    dy, dx = yy - (Y + 3), xx - x
                    c = F[1] if (dx == w - 1 or dy == 6) else F[t + 1] if (dy == 0 or dx == 0) else F[t]
                    a[yy, xx] = c
            x += w
        a[Y:Y + 10, x0] = F[1]; a[Y:Y + 10, x1 - 1] = F[1]
        for d, f in ((10, 0.6), (11, 0.75), (12, 0.88)):
            a[Y + d, x0 + 1:x1 + 1] = (a[Y + d, x0 + 1:x1 + 1] * f).astype(np.uint8)


def hoehle(a, x0, x1, ytop, ybot):
    """Hoehleneingang in der Erd-Felsfront: dunkle Oeffnung mit runder Oberkante, Rand aus dunklem Fels."""
    F = [np.array(H(c), np.float32) for c in k4.FELS['erde']]
    cx = (x0 + x1) / 2.0
    hw = (x1 - x0) / 2.0 - 5
    oben = ytop + 6
    for y in range(ytop, ybot):
        for x in range(x0, x1):
            dx = abs(x + 0.5 - cx)
            gr = hw if y >= oben + hw else (hw ** 2 - (oben + hw - y) ** 2) ** 0.5 if (oben + hw - y) < hw else -1
            if dx <= gr:
                t = (y - oben) / max(1, ybot - oben)
                a[y, x] = np.array((22, 14, 10), np.float32) * (0.7 + 0.5 * dx / max(1, hw)) + 6 * (1 - t)
            elif dx <= gr + 2:
                a[y, x] = F[0] if x > cx else F[1]


def braun(a):                     # Sandkacheln von Karte 01 -> Erdboden im selben Kachelstil (Hof, Erdflecken, Felsrand)
    l = a.mean(axis=2, keepdims=True) / 255.0
    lo, hi = np.array([112, 78, 48], np.float32), np.array([198, 160, 108], np.float32)
    return lo + (hi - lo) * np.clip((l - 0.45) / 0.45, 0, 1)


def acker(a, m, erde):
    """Gepfluegter Acker im Kachelstil: Erdkacheln (wie Hof/Wege), quer liegende Furchen alle 8 px - Kamm mit
    Lichtkante oben, Flanke, dunkle Rinne -, kleine Erdkruemel, Rand leicht erhoeht (heller) mit dunkler Kante."""
    Hh, W = m.shape
    yy, xx = np.mgrid[0:Hh, 0:W]
    ys, xs = np.nonzero(m)
    y0 = ys.min()
    r = (yy - y0) % 8
    basis = erde.astype(np.float32) * 0.78
    f = np.select([r == 0, r == 1, r <= 4, r == 5, r == 6], [1.22, 1.12, 1.0, 0.86, 0.66], 0.72)
    neu = np.clip(basis * f[..., None], 0, 255)
    rs = np.random.RandomState(int(y0) * 7 + int(xs.min()))
    kr = rs.rand(Hh, W) < 0.035
    neu[kr & (r <= 3)] = np.clip(neu[kr & (r <= 3)] * 1.18, 0, 255)  # Kruemel auf den Kaemmen
    a[m] = neu[m].astype(np.uint8)
    rand = m & ~(np.roll(m, 2, 0) & np.roll(m, -2, 0) & np.roll(m, 2, 1) & np.roll(m, -2, 1))
    a[rand] = np.clip(erde[rand] * 0.95, 0, 255).astype(np.uint8)      # Feldrand (Erdwall)
    kante = m & ~(np.roll(m, 1, 0) & np.roll(m, -1, 0) & np.roll(m, 1, 1) & np.roll(m, -1, 1))
    a[kante] = (erde[kante] * 0.6).astype(np.uint8)


def hecken(img, lay, cls):
    """Hecken aus dem PixelLab-Objekt (k23_hecke): waagerecht nahtlose Stuecke mit runden Enden, senkrecht
    gestapelte Heckenbloecke; Schatten der Silhouette nach rechts unten."""
    d = os.path.join(OBJ, 'hecke')
    seg = Image.open(os.path.join(d, '00.png')).convert('RGBA')
    rund = Image.open(os.path.join(d, '01.png')).convert('RGBA')
    block = Image.open(os.path.join(d, '02.png')).convert('RGBA')
    lage = Image.new('RGBA', img.size, (0, 0, 0, 0))
    for (x0, y0, x1, y1) in lay['hecken']:
        if y0 == y1:                                                   # waagerecht
            X0, X1 = x0 * T, (x1 + 1) * T
            Y = (y0 + 1) * T - seg.height - 1
            x = X0
            while x < X1:
                w = min(seg.width, X1 - x)
                lage.alpha_composite(seg.crop((0, 0, w, seg.height)), (x, Y))
                x += w
            h2 = rund.width // 2
            lage.paste(Image.new('RGBA', (h2, rund.height), (0, 0, 0, 0)), (X0, Y))
            lage.alpha_composite(rund.crop((0, 0, h2, rund.height)), (X0, Y))
            lage.paste(Image.new('RGBA', (rund.width - h2, rund.height), (0, 0, 0, 0)), (X1 - (rund.width - h2), Y))
            lage.alpha_composite(rund.crop((h2, 0, rund.width, rund.height)), (X1 - (rund.width - h2), Y))
        else:                                                          # senkrecht
            X = x0 * T + (T - block.width) // 2
            y = y0 * T - 6
            while y + block.height <= (y1 + 1) * T:
                lage.alpha_composite(block, (X, y))
                y += 13
    al = np.array(lage.getchannel('A')) > 0
    sch = np.zeros_like(al)
    sch[3:, 2:] = al[:-3, :-2]
    sch &= ~al
    base = np.array(img).astype(np.float32)
    base[sch, :3] *= 0.68
    img.paste(Image.fromarray(base.astype(np.uint8)), (0, 0))
    img.alpha_composite(lage)


def nach_oben(hoch, bis=4 * T):
    """Hochflaechen, die (fast) am oberen Kartenrand beginnen, bis zum Rand verlaengern - nur in ihren eigenen Spalten
    (keine Kantenstummel am Kartenrand)."""
    out = hoch.copy()
    for x in range(hoch.shape[1]):
        ys = np.nonzero(hoch[:, x])[0]
        if len(ys) and ys.min() <= bis:
            out[:ys.min(), x] = True
    return out


def bauen(frame=None, speichern=True):
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cls = lay['klassen']
    cols, rows = lay['groesse']
    Wp, Hp = cols * T, rows * T
    hp = hoehen_px(lay)
    basis = os.path.join(ROOT, 'assets', 'basis')
    gras = flaeche(k6.kacheln(os.path.join(basis, 'gras_%d.png'), 5), cols, rows)
    sand = flaeche(k6.kacheln(os.path.join(basis, 'sand_%d.png'), 5), cols, rows)
    a = gras.copy()
    wm = weich(zell_maske(cls, 'h', cols, rows), 5, 0.4, 3)
    a[wm] = (gras[wm] * np.array([0.62, 0.7, 0.66])).astype(np.uint8)
    erde = flaeche(k6.kacheln(os.path.join(basis, 'sand_%d.png'), 5, braun), cols, rows)
    fm = weich(zell_maske(cls, 'f', cols, rows), 7.0, 0.5, 9)
    a[fm] = erde[fm]
    saum_f = weich(zell_maske(cls, 'f', cols, rows), 7.0, 0.5, 9, 0.36) & ~fm
    a[saum_f] = (a[saum_f] * 0.9).astype(np.uint8)
    roh = zell_maske(cls, 'wtTc', cols, rows)
    m = weich(roh, 7.0, 0.5, 4)
    a[m] = sand[m]
    saum = weich(roh, 7.0, 0.5, 4, 0.36) & ~m
    a[saum] = (a[saum] * 0.9).astype(np.uint8)
    cm = maske_aus(cls, 'c', cols, rows)
    a[cm] = (a[cm] * 0.92).astype(np.uint8)                          # Senke etwas dunkler
    for (x0, y0, x1, y1, _) in lay['felder']:
        bm = np.zeros((Hp, Wp), bool)
        bm[y0 * T + 2:(y1 + 1) * T - 2, x0 * T + 2:(x1 + 1) * T - 2] = True
        acker(a, bm, erde)
    # ---------------- Hoehen: Plateau (Erde), Terrassen (Stein), Senke (Erde, Felsrand)
    wald = maske_aus(cls, 'h', cols, rows)
    nord = np.zeros((Hp, Wp), bool); nord[:4 * T] = True
    lippe = k20.lippe_aus_gras(gras)
    # Plateau Mitte
    px0, px1 = lay['plateau']['x']
    reg = np.zeros((Hp, Wp), bool); reg[:, (px0 - 1) * T:(px1 + 2) * T] = True
    hoch = (hp >= 2) & reg
    oben2 = np.zeros((Hp, Wp), bool); oben2[:2 * T] = True
    hoch_k = nach_oben(hoch)                                     # oberer Kartenrand gehoert zur Hochflaeche
    frei = np.zeros((Hp, Wp), bool)
    tx0, tx1 = lay['plateau']['treppe']
    ye = (lay['plateau']['unten'][str(tx0)] + 1) * T - 1
    frei[ye - 14:ye + 40, tx0 * T:(tx1 + 1) * T] = True
    wand = k4.hoehenkanten(a, hoch_k, 'erde', FRONT, 8, lippe, frei, 31, berg=False)
    k4.treppe(a, tx0 * T, (tx1 + 1) * T, ye, 's', FRONT, 'erde', sand)
    hx0, hx1 = lay['plateau']['hoehle']
    yh = (lay['plateau']['unten'][str(hx0)] + 1) * T
    hoehle(a, hx0 * T, (hx1 + 1) * T, yh + 2, yh + FRONT)
    # Terrassen oben rechts (zuerst die mittlere, dann die obere in die mittlere hinein)
    reg = np.zeros((Hp, Wp), bool); reg[:, 68 * T:] = True
    hoch = (hp >= 2) & reg
    frei = np.zeros((Hp, Wp), bool)
    trs = lay['terrassen']['treppen']
    for (sx0, sx1, yl) in trs:
        yE = (yl + 1) * T - 1
        frei[yE - 14:yE + 40, sx0 * T:(sx1 + 1) * T] = True
    oben3 = np.zeros((Hp, Wp), bool); oben3[:3 * T] = True
    wand |= k4.hoehenkanten(a, nach_oben(hoch), 'stein', FRONT, 8, lippe, frei, 41, berg=False)
    hoch3 = (hp >= 3) & reg
    reg3 = np.zeros((Hp, Wp), bool); reg3[:, 74 * T:] = True
    wand |= k4.hoehenkanten(a, nach_oben(hoch3), 'stein', FRONT, 8, lippe, frei, 42, berg=False)
    for (sx0, sx1, yl) in trs:
        k4.treppe(a, sx0 * T, (sx1 + 1) * T, (yl + 1) * T - 1, 's', FRONT, 'stein', sand)
    # Senke unten rechts: alles ausser der Senke ist hoeher; Felsrand-Kacheln gehoeren zum Rand oben
    rand = maske_aus(cls, 'k', cols, rows)
    cm = weich(zell_maske(cls, 'c', cols, rows), 14, 0.0, 5, 0.5)     # Senke rund (keine Treppenstufen am Rand)
    hoch = ~cm
    frei = np.zeros((Hp, Wp), bool)
    # Zugang von oben (Weg durch den Rand) -> Treppe; Zugang von links -> Rampe ohne Kante
    zug_o = [x for x in range(70, 86) if any(cls[y][x] in 'wc' for y in range(47, 52)) and cls[52][x] == 'c']
    ys_c = [y for y in range(48, 70) if cls[y][68] == 'c' or cls[y][67] == 'w']
    if zug_o:
        tz0, tz1 = min(zug_o), max(zug_o)
        yt = max(y for y in range(44, 60) if cls[y][tz0] not in 'c') * T + T - 1
        frei[yt - 14:yt + 40, tz0 * T:(tz1 + 1) * T] = True
    ramp = np.zeros((Hp, Wp), bool)
    for y in range(48, 70):
        for x in range(62, 72):
            if cls[y][x] in 'wc' and any(cls[y][xx] == 'c' for xx in range(x, min(cols, x + 6))):
                ramp[y * T:(y + 1) * T, x * T:(x + 1) * T] = True
    frei |= ramp
    LIPPE_ERDE = ['#4a3424', '#6a4c34', '#7e5e40', '#94714c', '#a8835a', '#bc9a70']   # Rand der Senke: Erde statt Gras
    wand |= k4.hoehenkanten(a, hoch, 'erde', 20, 6, LIPPE_ERDE, frei, 51, berg=False)
    if zug_o:
        k4.treppe(a, tz0 * T, (tz1 + 1) * T, yt, 's', 20, 'erde', sand)
    rm = weich(zell_maske(cls, 'kc', cols, rows), 4, 0.35, 12) & ~wand & ~cm & ~maske_aus(cls, 'wt', cols, rows)   # Felsrand: steiniger Erdboden bis an die Senke
    a[rm] = (erde[rm] * 0.84).astype(np.uint8)
    rs = np.random.RandomState(62)
    ys_, xs_ = np.nonzero(rm)
    for i in rs.choice(len(ys_), len(ys_) // 40, replace=False):     # Steinchen
        y, x = ys_[i], xs_[i]
        if y + 2 < Hp and x + 3 < Wp and rm[y:y + 3, x:x + 3].all():
            a[y, x:x + 3] = H('#cfc2a8'); a[y + 1, x:x + 3] = H('#9c8c74'); a[y + 2, x + 1:x + 3] = H('#5e5040')
    # ---------------- Mauerchen, Hecken
    maeuerchen(a, maske_aus(cls, 'n', cols, rows))
    # ---------------- Wasser (Bach laeuft unten aus der Karte)
    import wasser_vertieft
    xm = weich(zell_maske(cls, 'x', cols, rows), 4, 0.15, 8, 0.45)
    P = 24
    ag = np.pad(a, ((0, P), (0, 0), (0, 0)), mode='edge')
    mg = np.pad(xm, ((0, P), (0, 0)), mode='edge')
    ag = np.array(wasser_vertieft.vertiefen(Image.fromarray(ag), np.ones_like(mg), frame, maske=mg).convert('RGB'))
    a = ag[:Hp].copy()
    img = Image.fromarray(a).convert('RGBA')
    hecken(img, lay, cls)
    zx0, zy0, zx1, zy1 = lay['zaun']
    k6.zaun(img, (zx0, zy0, zx1, zy1), (-9, -9))
    a = np.array(img.convert('RGB'))
    for tp in lay['teleporter']:
        k4.teleporter_zeichnen(a, tp['x'], tp['y'], tp['b'], tp['h'], frame)
    img = Image.fromarray(a).convert('RGBA')
    lvl = hp.astype(np.uint8) + 1
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain_basis.png'))
        np.save(os.path.join(KARTE, 'wasser.npy'), np.packbits(xm))
        np.save(os.path.join(KARTE, 'pixelhoehe.npy'), lvl)
        np.save(os.path.join(KARTE, 'wand.npy'), np.packbits(wand))
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
            k20.rauch20(img, objs, cache, frame)
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain.png'))
    print('Karte 23 %dx%d gebaut' % (cols, rows))
    return img


if __name__ == '__main__':
    bauen()
