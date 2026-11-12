"""Karte 32 (Dream Ruins, A02): Gelaende.

Zerfallenes Traumschloss in der Sternenleere (Aufbau wie Karte 09): Steinboden mit Plattenvariation, rote/lila/
braune Teppiche mit Goldsaum und Fransen, Mauern mit 3 Kacheln hoher Wandflaeche (Karte 09), Friedhof mit
Pflasterwegen (45-Grad-Kanten, Regel 6b). Wo Boden an die Leere grenzt, haengt ein gebrochener Fundamentrand
in die Tiefe (Suedkanten) bzw. eine dunkle Bruchkante (Seiten). Die Leere: tiefes Nachtblau mit lila Nebel und
funkelnden Sternen (4 Bilder).

  python3 tools/karte32_layout.py && python3 tools/karte32_kacheln.py && python3 tools/karte32_bauen.py
"""
import json, math, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageFilter
import karte_bauen as kb
import karte04_bauen as k4
import karte08_bauen as k8
import karte09_bauen as k9

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte32')
BASIS = os.path.join(ROOT, 'assets', 'karte32', 'basis')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte32')
T = 16
N_FRAMES = 4                     # Regel: hoechstens 4 Animationsbilder
BILDDAUER = 250
k4.N_FRAMES = N_FRAMES
kb.N_FRAMES = N_FRAMES
H = k4.H


def gross(m):
    return np.kron(np.asarray(m, np.uint8), np.ones((T, T), np.uint8)).astype(bool)


def textur(art, cols, rows):
    t = np.zeros((rows * T, cols * T, 3), np.uint8)
    ks = [np.array(Image.open(os.path.join(BASIS, '%s_%d.png' % (art, v))).convert('RGB')) for v in range(5)]
    for y in range(rows):
        for x in range(cols):
            t[y * T:(y + 1) * T, x * T:(x + 1) * T] = ks[kb.variante(x, y)]
    return t


def leere(Hp, Wp, frame):
    """Sternenleere: Nachtblau mit leichtem Verlauf, lila Nebelschleier, feine und funkelnde Sterne."""
    yy, xx = np.mgrid[0:Hp, 0:Wp].astype(np.float32)
    a = np.zeros((Hp, Wp, 3), np.float32)
    a[:] = np.array([12, 14, 38], np.float32)
    a += (yy / Hp)[..., None] * np.array([2, 2, 10], np.float32)
    rs = np.random.RandomState(3232)
    neb = np.zeros((Hp // 8 + 1, Wp // 8 + 1), np.float32)
    for _ in range(14):
        cy, cx, r = rs.randint(0, neb.shape[0]), rs.randint(0, neb.shape[1]), rs.randint(6, 16)
        y_, x_ = np.mgrid[0:neb.shape[0], 0:neb.shape[1]]
        neb += np.exp(-((y_ - cy) ** 2 + (x_ - cx) ** 2) / (2 * r * r)) * rs.uniform(0.4, 1.0)
    neb = np.array(Image.fromarray((np.clip(neb, 0, 1) * 255).astype(np.uint8)).resize((Wp, Hp), Image.BILINEAR)) / 255.0
    stufe = np.floor(neb * 4) / 4                                         # in Stufen (Pixelart)
    a += stufe[..., None] * np.array([16, 6, 26], np.float32)
    a = np.clip(a, 0, 255).astype(np.uint8)
    rr = random.Random(3233)
    for _ in range(Wp * Hp // 260):                                       # feine Sterne (ruhig)
        x, y = rr.randrange(Wp), rr.randrange(Hp)
        a[y, x] = rr.choice([(70, 76, 120), (90, 96, 150), (60, 60, 100)])
    f = frame or 0
    for i in range(Wp * Hp // 2600):                                      # funkelnde Sterne (Kreuz, Phase je Stern)
        x, y = rr.randrange(2, Wp - 2), rr.randrange(2, Hp - 2)
        ph = (f + i) % N_FRAMES
        hell = (255, 236, 170) if i % 3 else (200, 220, 255)
        a[y, x] = hell
        if ph in (0, 1):
            arm = 1 if ph == 1 else 2
            for d in range(1, arm + 1):
                c = tuple(int(v * (0.75 if d == 1 else 0.45)) for v in hell)
                for (dy, dx) in ((d, 0), (-d, 0), (0, d), (0, -d)):
                    a[y + dy, x + dx] = c
    return a


def fundament(a, land, leer, tiefe=14, seed=3234):
    """Unter Suedkanten des Bodens zur Leere: Fundament aus dunklem Stein (Fugen, Licht oben), unten stufig
    ausgebrochen; an Seiten- und Nordkanten nur eine dunkle Bruchkante. -> Maske des Fundaments."""
    Hp, Wp = land.shape
    rr = random.Random(seed)
    f = np.zeros_like(land)
    sued = land & ~np.roll(land, -1, 0)
    sued[-1] = False
    xs = np.nonzero(sued.any(0))[0]
    tiefe_x = {}
    for x in range(Wp):
        if x % 4 == 0:
            t_ = tiefe + rr.randint(-5, 6)
        tiefe_x[x] = t_ if x % 4 == 0 or x not in tiefe_x else tiefe_x[x]
    t_cur = tiefe
    for x in range(Wp):
        if x % 4 == 0:
            t_cur = max(6, tiefe + rr.randint(-6, 6))
        for y in np.nonzero(sued[:, x])[0]:
            for d in range(1, t_cur + 1):
                Y = y + d
                if Y >= Hp or not leer[Y, x]:
                    break
                f[Y, x] = True
                yy = d
                c = H('#3a3f52') if (yy // 5 + x // 9) % 2 else H('#343849')
                if yy % 5 == 0 or (x + (yy // 5) * 4) % 9 == 0:
                    c = H('#24273a')
                if yy <= 1:
                    c = H('#565d76')
                if d == t_cur:
                    c = H('#1a1c2a')
                a[Y, x] = c
    # Bruchkante: dunkle Kontur aussen an allen anderen Landkanten
    rand = leer & ~f & (np.roll(land, 1, 1) | np.roll(land, -1, 1) | np.roll(land, 1, 0))
    a[rand] = H('#06070f')
    innen = land & (np.roll(leer & ~f, 1, 1) | np.roll(leer & ~f, -1, 1) | np.roll(leer & ~f, -1, 0) | np.roll(leer & ~f, 1, 0))
    a[innen] = (a[innen] * 0.6).astype(np.uint8)
    return f


def weg_45(kl, art, anschluss):
    """Regel 6b: Kachelmaske weichzeichnen (Gauss 5 px) und bei 50 % schneiden -> 45-Grad-Ecken."""
    basis = ((gross(kl == art) | gross(np.isin(kl, anschluss))) * 255).astype(np.uint8)
    m = np.array(Image.fromarray(basis).filter(ImageFilter.GaussianBlur(5))) > 127
    return m & ~gross(np.isin(kl, anschluss))


def bauen(frame=None, speichern=True):
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cols, rows = lay['groesse']
    kl = np.array([list(r) for r in lay['klassen']])
    hk = np.array([[int(c) for c in r] for r in lay['hoehe']])
    Wp, Hp = cols * T, rows * T
    leer = gross(kl == '.')
    land = ~leer
    a = leere(Hp, Wp, frame)
    for art in 'ijcvog':
        m = gross(kl == art)
        a[m] = textur(art, cols, rows)[m]
    friedhof = np.zeros((Hp, Wp), bool); friedhof[58 * T:] = True
    pm = weg_45(kl, 'p', ['.']) & friedhof
    g_tex = textur('g', cols, rows)
    pg = gross(kl == 'p') & ~pm
    a[pg] = g_tex[pg]
    a[pm] = textur('p', cols, rows)[pm]
    k4.dunkeln(a, k4.kontur(pm) if hasattr(k4, 'kontur') else (pm & ~np.roll(pm, 1, 0)), 0.8) if False else None
    rand_p = pm & ~(np.roll(pm, 1, 0) & np.roll(pm, -1, 0) & np.roll(pm, 1, 1) & np.roll(pm, -1, 1))
    a[rand_p] = (a[rand_p] * 0.72).astype(np.uint8)
    boden = gross(np.isin(kl, ['i', 'j'])) & ~friedhof
    vorher = a.copy()
    k9.boden_variation(a, boden)                                       # Plattenvariation nur halb so stark
    a[boden] = ((a[boden].astype(np.uint16) + vorher[boden]) // 2).astype(np.uint8)
    cm, vm, om = gross(kl == 'c'), gross(kl == 'v'), gross(kl == 'o')
    for m in (cm, vm, om):
        k9.teppich_rand(a, m)
    k9.fransen(a, cm | vm | om, boden)
    mauer = gross(hk == 3)
    flaeche = k9.mauern_zeichnen(a, mauer)
    fund = fundament(a, land, leer)
    lvl = np.ones((Hp, Wp), np.uint8)
    lvl[leer] = 0
    lvl[mauer] = 3
    lvl[flaeche | fund] = 9
    if speichern and frame is None:
        np.save(os.path.join(KARTE, 'pixelhoehe.npy'), lvl)
        np.save(os.path.join(KARTE, 'wandflaeche.npy'), np.packbits(flaeche))
    for tp in lay.get('teleporter', []):
        k4.teleporter_zeichnen(a, tp['x'], tp['y'], tp['b'], tp['h'], frame)
    img = Image.fromarray(a).convert('RGBA')
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain_basis.png'))
    pf = os.path.join(OBJ, 'platzierung.json')
    if os.path.exists(pf):
        objs = sorted((o for o in json.load(open(pf)) if os.path.exists(os.path.join(OBJ, o['datei']))),
                      key=lambda o: (0 if o.get('an_wand') else 1, o['y'] + o['fuss']))
        if frame is not None:                                         # schwebende Traumobjekte: 1 px auf und ab
            for o in objs:
                if o.get('schwebend'):
                    o['y'] += (0, -1, -1, 0)[(frame + o.get('phase', 0)) % 4]
        cache = {o['datei']: Image.open(os.path.join(OBJ, o['datei'])).convert('RGBA') for o in objs}
        lvl_s = lvl.copy()
        k8.schatten_ebene(img, [o for o in objs if not o.get('an_wand') and not o.get('schwebend')], cache, lvl_s)
        k4.objekte_zeichnen(img, objs, cache, np.zeros((Hp, Wp), bool), frame)
        k4.animieren(img, objs, cache, frame or 0, ruhig=frame is None)
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain.png'))
    print('Karte 32 %dx%d gebaut' % (cols, rows))
    return img


if __name__ == '__main__':
    bauen()
