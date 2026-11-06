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
    for art in 'bhfz':
        m = zell_maske(cls, art, cols, rows) > 0
        a[m] = textur(art, cols, rows)[m]
    platz = zell_maske(cls, 'b', cols, rows) > 0
    arena = zell_maske(cls, 'hfz', cols, rows) > 0
    holz = zell_maske(cls, 'h', cols, rows) > 0
    a[kontur(platz)] = H('#1a1c24')
    a[kontur(holz) & ~kontur(arena)] = H('#2a1a10')               # innere Kante des Holzrands
    a[kontur(arena)] = H('#1e120a')
    for k_, fa in ((1, 0.62), (2, 0.76), (3, 0.88)):              # Kontaktschatten rund um Platz und Arena (rechts unten)
        sch = np.roll(np.roll(platz | arena, k_, 0), k_ // 2, 1) & ~(platz | arena)
        a[sch] = (a[sch] * fa).astype(np.uint8)
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
    lvl[waende] = 9
    if speichern and frame is None:
        np.save(os.path.join(KARTE, 'pixelhoehe.npy'), lvl)
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
        k8.verdeckung(img, [o for o in objs if not o.get('an_wand')], cache, lvl, vor_objekten)
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain.png'))
    print('Karte 12 %dx%d gebaut' % (cols, rows))
    return img


if __name__ == '__main__':
    bauen()
