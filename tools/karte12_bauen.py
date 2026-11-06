"""Karte 12 (Spiral Mountain: Puppet Woods): schlammiger, duesterer Puppenwald. Ringsum dieselbe Bergwand wie
Karte 11 (dunkelberg, 44 px Front), fuenf Moos-Plateaus mit Treppen nach Sueden, Moorpfuetzen, Waldboden unter den
dichten Waldstuecken, Trampelpfad (unterbrochen) zum oberen Ausgang, Marionetten-Arena mit Holzrand und Schachbrett,
gepflasterter Platz am unteren Ausgang, Kuerbisaecker.

  python3 tools/karte12_layout.py && python3 tools/karte12_kacheln.py
  python3 tools/karte12_bauen.py && python3 tools/karte12_objekte.py && python3 tools/regeln_v11.py karte12 \\
    && python3 tools/karte12_objekte.py symmetrie && python3 tools/karte12_bauen.py
"""
import json, math, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageFilter
import karte_bauen as kb
import karte04_bauen as k4
import karte08_bauen as k8
import bauwerke
from karte11_bauen import bannkreis

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte12')
BASIS = os.path.join(ROOT, 'assets', 'karte12', 'basis')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte12')
T = 16
N_FRAMES = 16
H = k4.H
weich, zell_maske = k4.weich, k4.zell_maske
k4.FELS['dunkelberg'] = ['#12141c', '#1a1d28', '#242836', '#303546', '#3e4458', '#50586e', '#666e86']
LIPPE_BERG = ['#3c4050', '#4a4e60', '#585e70', '#686e80', '#7a8092', '#8c92a4']
LIPPE_MOOS = ['#1e2a22', '#26342a', '#2e3e32', '#384a3c', '#425646', '#4e6452']
FRONT = {2: 32, 5: 44}


def textur(art, cols, rows):
    t = np.zeros((rows * T, cols * T, 3), np.uint8)
    ks = [np.array(Image.open(os.path.join(BASIS, '%s_%d.png' % (art, v))).convert('RGB')) for v in range(5)]
    for y in range(rows):
        for x in range(cols):
            t[y * T:(y + 1) * T, x * T:(x + 1) * T] = ks[kb.variante(x, y)]
    return t


def kontur(m):
    return m & ~(np.roll(m, 1, 0) & np.roll(m, -1, 0) & np.roll(m, 1, 1) & np.roll(m, -1, 1))


def blur(m, r):
    return np.array(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(r))) / 255.0


def moor_zeichnen(a, m, frame):
    """Moorpfuetze: truebes, gruenbraunes Wasser (Grund schimmert am Rand durch), Entengruetze-Flecken, die langsam
    treiben, und kleine Blasen, die aufsteigen und platzen. Rand: nasser, dunkler Schlamm."""
    f = frame or 0
    Hh, W = m.shape
    lum = a[m].astype(np.float32) @ np.array([0.3, 0.59, 0.11], np.float32)
    tiefe = blur(m, 4)[m]
    farbe = np.array([34, 52, 40], np.float32) * (1 - 0.35 * tiefe[:, None]) + np.array([40, 34, 26], np.float32) * 0.0
    a[m] = np.clip(farbe + (lum[:, None] - lum.mean()) * 0.35, 0, 255).astype(np.uint8)
    rs = random.Random(7)
    ys, xs = np.nonzero(m)
    if not len(ys):
        return
    for _ in range(len(ys) // 120):                        # Entengruetze: kleine hellgruene Flecken, treiben
        i = rs.randrange(len(ys)); cy, cx = int(ys[i]), int(xs[i]) + int(round(math.sin(2 * math.pi * f / N_FRAMES + i) * 1.5))
        for dy, dx in ((0, 0), (0, 1), (1, 0), (0, -1)):
            Y, X = cy + dy, cx + dx
            if 0 <= Y < Hh and 0 <= X < W and m[Y, X] and rs.random() < 0.85:
                a[Y, X] = (70, 98, 54) if (dy, dx) == (0, 0) else (56, 82, 46)
    for _ in range(len(ys) // 700 + 1):                    # Blasen: steigen auf, werden hell, platzen
        i = rs.randrange(len(ys)); cy, cx = int(ys[i]), int(xs[i])
        t = (f / N_FRAMES + rs.random()) % 1.0
        if t < 0.5 and m[cy, cx]:
            a[cy, cx] = (92, 116, 90) if t < 0.35 else (60, 80, 62)
            if t < 0.2 and cx + 1 < W and m[cy, cx + 1]:
                a[cy, cx + 1] = (78, 100, 78)


def plateau_struktur(a, plat, cols, rows):
    """Plateau-Oberseite nicht glatt: freiliegende Felsnasen (dunkler Fels mit Lichtkante oben links und Schattenkante
    rechts unten), Moospolster dunkler zum Rand hin, ein paar Steine."""
    Hh, W = plat.shape
    n = np.random.RandomState(5).rand(Hh // 8 + 2, W // 8 + 2)
    n = np.array(Image.fromarray((n * 255).astype(np.uint8)).resize((W + 16, Hh + 16), Image.BICUBIC))[:Hh, :W] / 255.0
    innen = np.array(Image.fromarray((plat * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(9))) > 0
    fels = innen & (n > 0.64)
    fels = k4.splitter_weg(fels, 30)
    rt = textur('r', cols, rows)
    lum = rt[fels].astype(np.float32) @ np.array([0.3, 0.59, 0.11], np.float32)
    a[fels] = np.clip(lum[:, None] / max(1.0, lum.mean()) * np.array([62, 60, 56], np.float32), 0, 255).astype(np.uint8)
    lichtk = fels & (~np.roll(fels, 1, 0) | ~np.roll(fels, 1, 1))              # Lichtkante oben links
    a[lichtk] = H('#8a8478')
    dunkk = fels & (~np.roll(fels, -1, 0) | ~np.roll(fels, -1, 1)) & ~lichtk    # Schattenkante unten rechts
    a[dunkk] = H('#2a2824')
    schatt = ~fels & plat & (np.roll(fels, 1, 0) | np.roll(fels, 2, 0) | np.roll(fels, 1, 1))
    a[schatt] = (a[schatt] * 0.62).astype(np.uint8)                              # Moos im Schatten des Felsens
    rand_ = plat & ~(np.array(Image.fromarray((plat * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(7))) > 0)
    a[rand_ & ~fels] = (a[rand_ & ~fels] * 0.82).astype(np.uint8)


def arena_boden(a, arena, rand, lay, frame):
    """Holzpodest der Arena: Dielen mit Rissen, einige hochgeklappte Bretter (dunkles Loch darunter, Brett heller
    und schraeg nach oben, Schatten), Randbalken quer; in der Mitte ein Bannkreis wie auf Karte 11 (Boss-Spawn)."""
    Hh, W = arena.shape
    a[kontur(arena)] = H('#1e120a')
    innen_k = kontur(arena & ~rand) & ~kontur(arena)
    a[innen_k] = H('#2a1a10')
    cx, cy = lay['arena'][0] * T, lay['arena'][1] * T
    yy, xx = np.mgrid[0:Hh, 0:W]
    # Fleck unter dem Bannkreis: dunkel gebeiztes, verbranntes Holz
    fleck = (((xx - cx) / (5.6 * T)) ** 2 + ((yy - cy) / (4.9 * T)) ** 2 <= 1) & arena
    a[fleck] = (a[fleck] * np.array([0.42, 0.36, 0.44])).astype(np.uint8)
    rs = random.Random(12)
    ys, xs = np.nonzero(arena & ~rand & ~fleck)
    # Risse: duenne, gezackte dunkle Linien laengs der Bretter
    for _ in range(26):
        i = rs.randrange(len(ys)); y, x = int(ys[i]), int(xs[i])
        for d in range(rs.randint(6, 14)):
            if arena[y, x] and not fleck[y, x]:
                a[y, x] = H('#1c1008')
            x += 1
            if rs.random() < 0.3:
                y += rs.choice((-1, 1))
            if not (0 <= x < W and 0 <= y < Hh):
                break
    # hochgeklappte Dielen: an einer Stelle fehlt ein Brett (dunkles Loch, darunter ein Querbalken), das Brett ist am
    # einen Ende noch festgenagelt und steht am anderen schraeg hoch: Oberseite hell, darunter die Stirnseite,
    # Schatten nach rechts unten auf die Dielen
    from PIL import ImageDraw
    lage = Image.new('RGBA', (W, Hh), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lage)
    gesetzt = []
    for n_ in range(7):
        for _v in range(60):
            i = rs.randrange(len(ys)); y, x = int(ys[i]) // 4 * 4, int(xs[i])
            L = rs.randint(22, 30)
            frei_ = (arena[y - 14:y + 10, x - 4:x + L + 6] & ~rand[y - 14:y + 10, x - 4:x + L + 6]
                     & ~fleck[y - 14:y + 10, x - 4:x + L + 6])
            if frei_.size and frei_.all() and all(abs(y - gy) > 18 or abs(x - gx) > 40 for gy, gx in gesetzt):
                break
        else:
            continue
        gesetzt.append((y, x))
        a[y:y + 4, x:x + L] = H('#0e0804')                       # Loch, wo das Brett lag
        a[y + 1, x:x + L] = H('#1a0e06')
        jx = x + L // 2 + rs.randint(-4, 4)
        a[y:y + 4, jx:jx + 3] = H('#3a2414')                     # Querbalken darunter
        a[y, jx:jx + 3] = H('#5a3c24')
        a[y + 3, x:x + L] = H('#2a1a10')
        scharnier_rechts = rs.random() < 0.5
        hub = rs.randint(9, 12)
        if scharnier_rechts:                                     # rechtes Ende fest, linkes Ende hoch
            fx_, hx_ = x + 3, x + L
        else:
            fx_, hx_ = x + L - 3, x
        oben = [(hx_, y), (fx_, y - hub)]
        # Schatten (nach rechts unten versetzt, auf die Dielen und ins Loch)
        ld.polygon([(hx_ + 3, y + 4), (fx_ + 5, y - hub + 6), (fx_ + 5, y - hub + 10), (hx_ + 3, y + 7)], fill=(0, 0, 0, 90))
        # Stirnseite (Dicke 2 px) und Oberseite (4 px) als Viereck
        ld.polygon([(hx_, y + 3), (fx_, y - hub + 3), (fx_, y - hub + 5), (hx_, y + 5)], fill=(52, 32, 18, 255))
        ld.polygon([(hx_, y), (fx_, y - hub), (fx_, y - hub + 3), (hx_, y + 3)], fill=(168, 126, 84, 255))
        ld.line([(hx_, y), (fx_, y - hub)], fill=(206, 170, 120, 255))        # Lichtkante oben
        ld.line([(hx_, y + 2), (fx_, y - hub + 2)], fill=(136, 98, 62, 255))  # Maserung
        ld.line([(fx_, y - hub), (fx_, y - hub + 4)], fill=(40, 24, 12, 255))  # Bruchkante am freien Ende
        ld.point([(fx_ + (1 if scharnier_rechts else -1), y - hub)], fill=(230, 210, 170, 255))   # Splitter
        ld.point([(hx_ + (-2 if scharnier_rechts else 2), y + 1)], fill=(190, 190, 196, 255))     # Nagel am festen Ende
    la = np.array(lage).astype(np.float32)
    al = la[..., 3:4] / 255.0
    a[:] = np.clip(a * (1 - al) + la[..., :3] * al, 0, 255).astype(np.uint8)
    bannkreis(a, cx, cy, 4.8 * T, 4.1 * T, frame)


def podest_front(a, arena, lay):
    """Suedfront des Holzpodests (eine Etage, 32 px): senkrechte Bohlen mit Fugen, ein Querbalken, Pfosten an den
    Ecken, unten Kontaktschatten; seitlich nur schmale Kontur. Mittig eine Holztreppe mit Wangen."""
    Hh, W = arena.shape
    front = np.zeros_like(arena)
    F = 32
    sued = arena & ~np.roll(arena, -1, 0)
    tr = lay.get('arena_treppe')
    tx0, tx1 = (tr[0] * T, (tr[1] + 1) * T) if tr else (0, 0)
    for y, x in zip(*np.nonzero(sued)):
        for d in range(F + 3):
            Y = y + 1 + d
            if Y >= Hh or arena[Y, x]:
                break
            if d >= F:
                a[Y, x] = (a[Y, x] * (0.6 if d == F else 0.8)).astype(np.uint8)
                continue
            front[Y, x] = True
            if tx0 <= x < tx1:
                continue
            bohle = x % 6
            c = np.array((96, 66, 42) if bohle in (1, 2) else (78, 52, 32), np.float32)
            if bohle == 5:
                c = np.array((40, 24, 14), np.float32)
            if d in (10, 11):
                c = np.array((60, 40, 24), np.float32) if d == 11 else np.array((118, 86, 56), np.float32)   # Querbalken
            c = c * (1 - 0.35 * d / F)
            if d == 0:
                c = np.array((40, 26, 16), np.float32)
            a[Y, x] = np.clip(c, 0, 255).astype(np.uint8)
    # Pfosten an den Knicken der Front
    xs_s = sorted(set(np.nonzero(sued)[1].tolist()))
    for x in (min(xs_s), max(xs_s)):
        ys_ = np.nonzero(sued[:, x])[0]
        y = int(ys_.max())
        a[y + 1:y + F + 1, x - 2 if x == max(xs_s) else x:x + 3 if x == min(xs_s) else x + 1] = H('#5a3c24')
    if tr:                                                       # Holztreppe: Stufen 4 px, Wangen links/rechts
        y0 = (tr[2] + 1) * T
        for d in range(F + 2):
            Y = y0 + d
            for x in range(tx0 - 3, tx1 + 3):
                if x < tx0 or x >= tx1:
                    a[Y, x] = H('#3e2818') if x in (tx0 - 3, tx1 + 2) else H('#6a4a2e')
                else:
                    st = d % 6
                    a[Y, x] = H('#a07a50') if st == 0 else (H('#7a5838') if st < 4 else H('#3a2414'))
            front[Y, tx0 - 3:tx1 + 3] = False
        a[y0 + F + 2:y0 + F + 4, tx0 - 3:tx1 + 3] = (a[y0 + F + 2:y0 + F + 4, tx0 - 3:tx1 + 3] * 0.7).astype(np.uint8)
    return front


def bruecke(a, b, wasser):
    """Holzsteg ueber den Fluss: Bretter quer zur Laufrichtung, Laengsbalken als Rand, Pfosten an den Ecken,
    Schatten aufs Wasser rechts unten."""
    x0, y0, x1, y1, art = b
    X0, Y0, X1, Y1 = x0 * T + 2, y0 * T + 4, (x1 + 1) * T - 2, (y1 + 1) * T - 4
    if art == 'ns':
        X0, X1 = X0 + 4, X1 - 4
    else:
        Y0, Y1 = Y0 + 2, Y1 - 2
    a[Y0 + 3:Y1 + 3, X0 + 3:X1 + 3] = (a[Y0 + 3:Y1 + 3, X0 + 3:X1 + 3] * 0.62).astype(np.uint8)   # Schatten
    for Y in range(Y0, Y1):
        for X in range(X0, X1):
            q = (Y - Y0) if art == 'ns' else (X - X0)
            c = H('#8a6442') if q % 5 == 0 else (H('#6e4e32') if q % 5 < 4 else H('#2a1a10'))
            a[Y, X] = c
    if art == 'ns':
        a[Y0:Y1, X0:X0 + 2] = H('#4a3020'); a[Y0:Y1, X1 - 2:X1] = H('#4a3020')
        a[Y0:Y1, X0] = H('#a07a50')
    else:
        a[Y0:Y0 + 2, X0:X1] = H('#a07a50'); a[Y1 - 2:Y1, X0:X1] = H('#4a3020')
    for (px, py) in ((X0, Y0), (X1 - 3, Y0), (X0, Y1 - 4), (X1 - 3, Y1 - 4)):
        a[py:py + 4, px:px + 3] = H('#3a2414')
        a[py, px:px + 3] = H('#9a7450')


def brueckenschatten(a, b, wasser):
    """Schatten des Holzstegs (Sprite) nur auf dem Wasser, nach rechts unten versetzt."""
    x0, y0, x1, y1, art = b
    X0, Y0, X1, Y1 = x0 * T + 10, y0 * T + 2, (x1 + 1) * T - 4, (y1 + 1) * T + 2
    m = np.zeros(wasser.shape, bool)
    m[Y0 + 4:Y1 + 4, X0 + 4:X1 + 4] = True
    m &= wasser
    a[m] = (a[m] * 0.66).astype(np.uint8)


def quelle_zeichnen(a, lay, frame):
    """Fuss der Quelle: Aus dem Wasserspeier (geschnitzte Puppenmaske in der Bergwand, Objekt) faellt das Wasser in
    ein kleines Becken am Fuss der Wand; Gischt spritzt und wandert mit dem Bild, dann fliesst es in den Fluss."""
    f = frame or 0
    fx, fy = lay['fluss'][0]
    cx, yb = int(fx * T), int(fy * T) - 6
    Hh, W = a.shape[:2]
    pf = os.path.join(OBJ, 'platzierung.json')                     # Becken genau dort, wo der Strahl aufkommt
    if os.path.exists(pf):
        for o in json.load(open(pf)):
            if o.get('quelle'):
                sa = np.array(Image.open(os.path.join(OBJ, o['datei'])).getchannel('A')) > 0
                yb = o['y'] + int(np.nonzero(sa.any(axis=1))[0].max()) - 4
                cx = o['x'] + int(round(np.nonzero(sa[-4:].any(axis=0))[0].mean()))
    for y in range(yb - 2, yb + 12):
        for x in range(cx - 14, cx + 15):
            e = ((x - cx) / 14.0) ** 2 + ((y - yb - 4) / 6.5) ** 2
            if e <= 1:
                a[y, x] = (48, 80, 68) if e > 0.55 else (64, 100, 86)
    rs = random.Random(3)
    for i in range(20):
        ph = (f / N_FRAMES + rs.random()) % 1.0
        ang_ = rs.random() * math.pi
        rr = 2 + ph * 12
        x, y = int(cx + math.cos(ang_) * rr), int(yb + 3 - math.sin(ang_) * rr * 0.4)
        if ph < 0.7 and 0 <= y < Hh:
            a[y, x] = (210, 226, 214) if ph < 0.35 else (150, 180, 166)


def quelle_strahl(img, objs, frame):
    """Wasserstrahl des Speiers animieren: helle Streifen wandern im Strahl nach unten (nur die Wasserpixel)."""
    f = frame or 0
    px = img.load()
    for o in objs:
        if not o.get('quelle'):
            continue
        sp = Image.open(os.path.join(OBJ, o['datei'])).convert('RGBA')
        a = np.array(sp).astype(int)
        w = (a[..., 3] > 0) & (a[..., 1] > a[..., 0] + 12) & (a[..., 2] > a[..., 0] + 6) & (np.arange(a.shape[0])[:, None] > 20)
        for y, x in zip(*np.nonzero(w)):
            k_ = (y - f * 3 + (x % 3) * 2) % 8
            r, g, b, _ = px[o['x'] + x, o['y'] + y]
            if k_ == 0:
                px[o['x'] + x, o['y'] + y] = (min(255, r + 60), min(255, g + 60), min(255, b + 55), 255)
            elif k_ in (4, 5):
                px[o['x'] + x, o['y'] + y] = (int(r * 0.82), int(g * 0.82), int(b * 0.82), 255)


def bauen(frame=None, speichern=True):
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cols, rows = lay['groesse']
    cls = lay['klassen']
    hoehe = np.array([[int(c) for c in r] for r in lay['hoehe']])
    Wp, Hp = cols * T, rows * T
    a = textur('d', cols, rows)
    # --- weiche Boeden: Waldboden, Acker, Trampelpfad (natuerliche Raender)
    for art, bl, rausch, seed in (('g', 6.0, 0.5, 3), ('a', 2.0, 0.2, 9), ('q', 2.5, 0.35, 5)):
        roh = zell_maske(cls, art, cols, rows)
        m = weich(roh, bl, rausch, seed)
        a[m] = textur(art, cols, rows)[m]
        saum = weich(roh, bl, rausch, seed, 0.36) & ~m
        k4.dunkeln(a, saum, 0.88 if art != 'q' else 0.94)
    # --- gebaute Flaechen scharf: Pflaster, Arena
    m = zell_maske(cls, 'b', cols, rows) > 0
    a[m] = textur('b', cols, rows)[m]
    platz = m
    yy_, xx_ = np.mgrid[0:Hp, 0:Wp]                               # Holzpodest pixelgenau (glatte Achteck-Kanten)
    dxa, dya = np.abs(xx_ - lay['arena'][0] * T), np.abs(yy_ - lay['arena'][1] * T)
    arena = (dxa <= 10.6 * T) & (dya <= 10.6 * T) & (dxa + dya <= 14.6 * T)
    rand_a = arena & ~((dxa <= 10.6 * T - 9) & (dya <= 10.6 * T - 9) & (dxa + dya <= 14.6 * T - 12))
    a[arena] = textur('w', cols, rows)[arena]
    a[rand_a] = textur('h', cols, rows)[rand_a]
    a[kontur(platz)] = H('#1a1c24')
    for k_, fa in ((1, 0.62), (2, 0.76), (3, 0.88)):              # Kontaktschatten rund um den Platz (rechts unten)
        sch = np.roll(np.roll(platz, k_, 0), k_ // 2, 1) & ~platz
        a[sch] = (a[sch] * fa).astype(np.uint8)
    arena_boden(a, arena, rand_a, lay, frame)
    # --- Ebenen: Plateaus (2), Berg (5)
    em = {}
    em[5] = weich(k8.stufe(hoehe, 5, cols, rows), 5, 0.3, 37)
    plat = weich(zell_maske(cls, 'v', cols, rows), 3, 0, 0)          # Plateau-Ecken gerundet
    em[2] = plat | em[5]
    a[plat] = textur('v', cols, rows)[plat]
    fels = em[5]
    a[fels] = (textur('r', cols, rows)[fels] * np.array([0.56, 0.58, 0.66])).astype(np.uint8)   # dunkler Fels oben
    # --- Moorpfuetzen (vertieft, mit dunklem Schlammrand)
    mm = weich(zell_maske(cls, 'x', cols, rows), 5, 0.25, 47, 0.45) & ~em[2]
    mm = k4.splitter_weg(mm, 60)
    k4.wasser_zeichnen(a, mm, frame, np.zeros_like(mm))
    import wasser_vertieft
    a = np.array(wasser_vertieft.vertiefen(Image.fromarray(a), np.ones_like(mm), frame, maske=mm,
                                           rand=('#20160f', '#2a1e16', '#34261c', '#3e2e22'),
                                           stufen=[(14, 0.82, 5), (30, 0.68, 4)]).convert('RGB'))
    moor_zeichnen(a, mm, frame)
    nass = blur(mm, 3)
    feucht = ~mm & (nass > 0.04) & ~em[2] & ~platz & ~arena
    fak = (1 - 0.3 * np.clip(nass * 2.2, 0, 1))[..., None]
    a[feucht] = np.clip(a[feucht] * fak[feucht], 0, 255).astype(np.uint8)
    # --- Treppen (Suedseite der Plateaus) und Kanten
    treppen_info = []
    frei = np.zeros((Hp, Wp), bool)
    for (x0, x1, e, yb_kachel) in lay.get('treppen_sued', []):
        px0, px1 = x0 * T + 1, (x1 + 1) * T - 1
        yb = (yb_kachel + 1) * T - 1
        frei[yb - 14:yb + FRONT[e] + 8, px0 - 6:px1 + 6] = True
        treppen_info.append((px0, px1, yb, FRONT[e], e))
    waende = np.zeros((Hp, Wp), bool)
    waende |= k4.hoehenkanten(a, em[2] & ~em[5] | em[5], 'dunkelberg', FRONT[2], 12, LIPPE_MOOS, frei | em[5], 31, berg=False)
    waende |= k4.hoehenkanten(a, em[5], 'dunkelberg', FRONT[5], 12, LIPPE_BERG, frei, 35, berg=False)
    lvl = np.ones((Hp, Wp), np.uint8)
    lvl[em[2]] = 2
    lvl[em[5]] = 5
    lvl[mm] = 0
    lvl[arena] = 2
    lvl[waende] = 9
    lvl[podest_front(a, arena, lay)] = 9
    for b_ in lay.get('bruecken', []):
        brueckenschatten(a, b_, mm)
    if speichern and frame is None:
        np.save(os.path.join(KARTE, 'pixelhoehe.npy'), lvl)
        np.save(os.path.join(KARTE, 'wasser.npy'), np.packbits(mm))   # fuer das Kollisionsraster
    img = Image.fromarray(a).convert('RGBA')
    alt_S = bauwerke.S
    bauwerke.S = [H(c) + (255,) for c in k4.FELS['dunkelberg']]
    for (px0, px1, ye, f, e) in treppen_info:
        bauwerke.zeichne_treppe(img, px0 - 6, px1 + 6, ye + 2, ye + f + 2)
        for y in range(ye + 1, ye + f + 3):
            for x in range(px0 - 6, px1 + 6):
                lvl[min(Hp - 1, y), x] = 9
    bauwerke.S = alt_S
    a = np.array(img.convert('RGB'))
    quelle_zeichnen(a, lay, frame)
    for tp in lay.get('teleporter', []):
        k4.teleporter_zeichnen(a, tp['x'], tp['y'], tp['b'], tp['h'], frame)
    img = Image.fromarray(a).convert('RGBA')
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain_basis.png'))
    pf = os.path.join(OBJ, 'platzierung.json')
    if os.path.exists(pf):
        objs = sorted((o for o in json.load(open(pf)) if os.path.exists(os.path.join(OBJ, o['datei']))),
                      key=lambda o: (0 if o.get('an_wand') else 1, o['y'] + o['fuss']))
        cache = {o['datei']: Image.open(os.path.join(OBJ, o['datei'])).convert('RGBA') for o in objs}
        k8.schatten_ebene(img, [o for o in objs if not o.get('an_wand')], cache, lvl)
        vor_objekten = np.array(img)
        k4.objekte_zeichnen(img, objs, cache, np.zeros((Hp, Wp), bool), frame)
        k4.animieren(img, objs, cache, frame or 0, ruhig=frame is None)
        quelle_strahl(img, objs, frame)
        k8.verdeckung(img, [o for o in objs if not o.get('an_wand')], cache, lvl, vor_objekten)
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain.png'))
    print('Karte 12 %dx%d gebaut' % (cols, rows))
    return img


if __name__ == '__main__':
    bauen()
