"""Karte 20 - Startkarte von A02 (Dorf am Fluss), Gelaende im Stil von Karte 06 (Primary Village).

Bausteine wie Karte 06: Gras/Sand aus Karte 01 (assets/basis), weiche Raender (Karte 04), Kopfsteinplatz aus den
Kieseln von Karte 03 (warm umgefaerbt) mit Bordstein, Fluss im vertieften Wasserstil (wie der Teich von Karte 06),
Holzbruecken (bauwerke), Holzzaeune (Karte 06), Waldboden dunkler. Neu: Beete (Ackerfurchen), Feld (trockene Erde),
Plateau oben rechts mit Erd-Felsfront und Steintreppe (Karte 04), Teleporter an den Ausgaengen.

  python3 tools/karte20_layout.py && python3 tools/karte20_bauen.py
"""
import json, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
import karte_bauen as kb
import karte04_bauen as k4
import karte06_bauen as k6
import bauwerke

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte20')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte20')
T = 16
N_FRAMES = 4                     # Regel: hoechstens 4 Animationsbilder
BILDDAUER = 250
k4.N_FRAMES = N_FRAMES
H = k4.H
weich, zell_maske = k4.weich, k4.zell_maske


def muehle20(sp, frame, o):
    """Windmuehle: nur die roten Fluegel drehen sich um die Nabe, 22,5 Grad je Bild (4 Bilder = 90 Grad, die vier
    Fluegel sind 4-fach symmetrisch -> nahtlos). Turm und Dach bleiben ruhig."""
    a = np.array(sp)
    r_, g_, b_ = a[..., 0].astype(int), a[..., 1].astype(int), a[..., 2].astype(int)
    fl = (a[..., 3] > 0) & (r_ > 120) & (r_ > g_ + 50) & (r_ > b_ + 50)
    fl |= (a[..., 3] > 0) & (r_ > 70) & (r_ > g_ + 30) & (r_ > b_ + 30) & (g_ < 60)   # dunkle Fluegelkanten
    if fl.sum() < 20:
        return sp
    ys, xs = np.nonzero(fl)
    cx, cy = (xs.min() + xs.max()) / 2.0, (ys.min() + ys.max()) / 2.0
    teil = np.zeros_like(a); teil[fl] = a[fl]
    rest = a.copy(); rest[fl, 3] = 0
    dreh = Image.fromarray(teil).rotate(-22.5 * ((frame or 0) % 4), resample=Image.NEAREST, center=(cx, cy))
    out = Image.fromarray(rest)
    out.alpha_composite(dreh)
    return out


k4.TEILANIM['muehle20'] = muehle20


def flaeche(ks, cols, rows):
    t = np.zeros((rows * T, cols * T, 3), np.uint8)
    for y in range(rows):
        for x in range(cols):
            t[y * T:(y + 1) * T, x * T:(x + 1) * T] = ks[kb.variante(x, y) % len(ks)]
    return t


def lippe_aus_gras(gras):
    """Grastoene der Karte-01-Kacheln (dunkel -> hell) fuer die ueberhaengende Graskante am Plateau."""
    px = gras.reshape(-1, 3).astype(int)
    lum = px.sum(1)
    qs = np.percentile(lum, [5, 20, 40, 60, 80, 95])
    out = []
    for q in qs:
        c = px[np.argmin(np.abs(lum - q))]
        out.append('#%02x%02x%02x' % tuple(c))
    return out


def beete(a, m, seed=20):
    """Acker: dunkle Erde mit waagerechten Furchen alle 4 px (Licht oben, Schatten unten), Rand leicht dunkler."""
    ys, xs = np.nonzero(m)
    rs = random.Random(seed)
    erde = [np.array(H(c), np.float32) for c in ('#4a2e1c', '#5e3a22', '#74482a', '#8a5a34')]
    for y, x in zip(ys, xs):
        r = y % 4
        c = erde[2] if r == 0 else erde[1] if r in (1, 2) else erde[0]
        if r == 0 and (x * 7 + y) % 11 == 0:
            c = erde[3]
        a[y, x] = c
    kante = m & ~(np.roll(m, 1, 0) & np.roll(m, -1, 0) & np.roll(m, 1, 1) & np.roll(m, -1, 1))
    a[kante] = H('#3a2416')


def feld(a, m, seed=21):
    """Trockenes Feld (unten links): helle Erde mit Strohhalmen und Krumen, weich zum Gras."""
    rs = np.random.RandomState(seed)
    ys, xs = np.nonzero(m)
    basis = np.array(H('#b89462'), np.float32)
    n = rs.rand(m.shape[0] // 8 + 1, m.shape[1] // 8 + 1)
    for y, x in zip(ys, xs):
        v = 0.92 + 0.12 * n[y // 8, x // 8]
        a[y, x] = np.clip(basis * v, 0, 255)
    for _ in range(int(m.sum() / 60)):
        i = rs.randint(len(ys))
        y, x = ys[i], xs[i]
        c = H('#e2c27a') if rs.rand() < 0.6 else H('#8a6a42')
        for d in range(rs.randint(2, 4)):
            if 0 <= x + d < m.shape[1] and m[y, x + d]:
                a[y, x + d] = c


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
    # Feld, Sandwege (inkl. Ausgaenge und Treppenweg)
    fm = weich(zell_maske(cls, 'f', cols, rows), 3.0, 0.3, 9)
    feld(a, fm)
    roh = zell_maske(cls, 'wet', cols, rows)
    m = weich(roh, 7.0, 0.5, 4)
    a[m] = sand[m]
    saum = weich(roh, 7.0, 0.5, 4, 0.36) & ~m
    a[saum] = (a[saum] * 0.9).astype(np.uint8)
    # Kopfsteinplatz mit Bordstein, Rasen in der Mitte
    kies = flaeche(k6.kacheln(os.path.join(ROOT, 'assets', 'karte03', 'basis', 'kies_%d.png'), 5, k6.beige), cols, rows)
    pm = weich(zell_maske(cls, 'p', cols, rows), 4, 0.12, 6)
    a[pm] = kies[pm]
    for mm in (pm,):
        rand = mm & ~(np.roll(mm, 1, 0) & np.roll(mm, -1, 0) & np.roll(mm, 1, 1) & np.roll(mm, -1, 1))
        a[rand] = H('#8a6a48')
        unten = mm & ~np.roll(mm, -1, 0)
        for y, x in zip(*np.nonzero(unten)):
            for d in (1, 2):
                if y + d < Hp and not mm[y + d, x]:
                    a[y + d, x] = (a[y + d, x] * 0.8).astype(np.uint8)
    # Beete
    for (x0, y0, x1, y1) in lay['beete']:
        bm = np.zeros((Hp, Wp), bool)
        bm[y0 * T + 2:(y1 + 1) * T - 2, x0 * T + 2:(x1 + 1) * T - 2] = True
        beete(a, bm)
    # Plateau oben rechts: Erd-Felsfront (Karte 04), Graslippe aus den Karte-01-Toenen, Treppe
    x0, y0, x1, y1 = lay['plateau']
    hm = np.zeros((Hp, Wp), bool)
    hm[(y0 + 1) * T:(y1 + 1) * T, x0 * T:(x1 + 1) * T] = True
    hoch = hm & (zell_maske(cls, 'h', cols, rows) < 0.5)
    tx0, tx1 = lay['treppe']
    ye = (y1 + 1) * T - 1
    frei = np.zeros((Hp, Wp), bool)
    frei[ye - 14:ye + 40, tx0 * T:(tx1 + 1) * T] = True          # Treppe schliesst buendig an die Felsfront an
    k4.hoehenkanten(a, hoch, 'erde', 32, 8, lippe_aus_gras(gras), frei, 31, berg=False)
    k4.treppe(a, tx0 * T, (tx1 + 1) * T, ye, 's', 32, 'erde', sand)
    # Fluss: vertieftes Wasser wie der Teich von Karte 06
    import wasser_vertieft
    xm = weich(zell_maske(cls, 'xb', cols, rows), 4, 0.15, 8, 0.45)
    a = np.array(wasser_vertieft.vertiefen(Image.fromarray(a), np.ones_like(xm), frame, maske=xm).convert('RGB'))
    img = Image.fromarray(a).convert('RGBA')
    for (bx0, by0, bx1, by1) in lay['bruecken']:
        bauwerke.zeichne_bruecke(img, bx0 * T - 6, (bx1 + 1) * T + 6, by0 * T, (by1 + 1) * T - 4, frame=frame or 0)   # Enden auf dem Ufer
    k6.zaun(img, lay['acker_zaun'], (-9, -9))                   # geschlossen wie in der Vorlage
    k6.zaun(img, lay['feld_zaun'], (-9, -9))
    a = np.array(img.convert('RGB'))
    for tp in lay.get('teleporter', []):
        k4.teleporter_zeichnen(a, tp['x'], tp['y'], tp['b'], tp['h'], frame)
    img = Image.fromarray(a).convert('RGBA')
    lvl = np.ones((Hp, Wp), np.uint8)
    lvl[hoch] = 2
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
            k4.objekte_zeichnen(img, objs, cache, ~xm, frame)
            k4.animieren(img, objs, cache, frame or 0)
            k6.animieren_k6(img, objs, cache, frame or 0)
            kb.laternen_licht(img, [o for o in objs if o.get('anim') == 'laterne'], frame)
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain.png'))
    print('Karte 20 %dx%d gebaut' % (cols, rows))
    return img


if __name__ == '__main__':
    bauen()
