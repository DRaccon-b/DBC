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


_MUEHLE_CACHE = {}


def _muehle_ohne_fluegel(sp, ohne_fluegel=False):
    """Turm ohne Fluegel: Fluegelpixel (alle Rottoene und ihre braunen Konturen) entfernen und den Turm samt Dach
    dahinter auffuellen - zuerst vom gespiegelten Turmpixel (der Turm ist symmetrisch), sonst vom naechsten
    Turmpixel derselben Spalte. Die Turmbreite je Zeile wird ebenfalls gespiegelt ergaenzt.
    Gibt (Bild, Nabe, Fluegellaenge) zurueck."""
    key = id(sp)
    if key in _MUEHLE_CACHE:
        return _MUEHLE_CACHE[key]
    from PIL import ImageFilter as _IF
    a = np.array(sp).astype(np.int16)
    h, w = a.shape[:2]
    r_, g_, b_, al = a[..., 0], a[..., 1], a[..., 2], a[..., 3]
    kern = (al > 0) & (r_ > 45) & (g_ < 0.55 * r_) & (b_ < 0.62 * r_)
    if ohne_fluegel or kern.sum() < 20:                          # fluegelloser Turm (k20_turm): Nabe = Holzscheibe am Dach
        holz = (al > 0) & (r_ > g_ + 15) & (g_ > b_) & (r_ > 70)
        holz[int(h * 0.6):] = False
        holz[:, :int(w * 0.3)] = False; holz[:, int(w * 0.7):] = False
        hy, hx = np.nonzero(holz)
        res = (sp.copy(), (float(hx.mean()), float(hy.mean())), 56.0)
        _MUEHLE_CACHE[key] = res
        return res
    ys, xs = np.nonzero(kern)
    cy, cx = (ys.min() + ys.max()) / 2.0, (xs.min() + xs.max()) / 2.0
    nabe = (al > 0) & (np.abs(r_ - 90) < 18) & (np.abs(g_ - 58) < 18) & (np.abs(b_ - 44) < 18)   # Nabenfarbe
    ny, nx = np.nonzero(nabe & (np.abs(np.mgrid[0:a.shape[0], 0:a.shape[1]][0] - cy) < 14)
                        & (np.abs(np.mgrid[0:a.shape[0], 0:a.shape[1]][1] - cx) < 14))
    if len(ny):
        cy, cx = float(np.median(ny)), float(np.median(nx))
    laenge = float(np.percentile(np.hypot(ys - cy, xs - cx), 99))
    nah = np.array(Image.fromarray((kern * 255).astype(np.uint8)).filter(_IF.MaxFilter(7))) > 0
    fl = kern | (nah & (al > 0) & (r_ > b_ + 6))
    yy, xx = np.mgrid[0:h, 0:w]
    fl &= np.hypot(yy - cy, xx - cx) > 3.5                      # Nabe bleibt
    turm = (al > 0) & ~fl
    out = a.copy()
    out[fl, 3] = 0
    for y in range(h):
        z = np.nonzero(turm[y])[0]
        if len(z) < 2:
            continue
        lo = int(min(z.min(), round(2 * cx - z.max())))
        hi = int(max(z.max(), round(2 * cx - z.min())))
        for x in range(max(0, lo), min(w, hi + 1)):
            if turm[y, x]:
                continue
            xm = int(round(2 * cx - x))
            if 0 <= xm < w and turm[y, xm]:
                out[y, x] = a[y, xm]
                continue
            for d in range(1, 14):
                for y2 in (y - d, y + d):
                    if 0 <= y2 < h and turm[y2, x]:
                        out[y, x] = a[y2, x]
                        break
                else:
                    continue
                break
    res = (Image.fromarray(out.astype(np.uint8)), (cx, cy), laenge)
    _MUEHLE_CACHE[key] = res
    return res


def muehle20(sp, frame, o):
    """Windmuehle: die vier Gitterfluegel werden in jedem Bild sauber neu gezeichnet (statt das Pixelbild zu drehen)
    und um 22,5 Grad je Bild weitergedreht (4 Bilder = 90 Grad, 4-fach symmetrisch -> nahtlos). Der Turm hinter
    den Fluegeln ist aufgefuellt; Turm, Dach und Tuer bleiben ruhig."""
    from PIL import ImageDraw
    turm, (cx, cy), R = _muehle_ohne_fluegel(sp, 'turm/' in o.get('basis', ''))
    img = turm.copy()
    d = ImageDraw.Draw(img)
    DUNKEL, ROT, HELL = (94, 20, 24, 255), (138, 31, 34, 255), (200, 58, 58, 255)
    breite = 6.5                                                  # halbe Fluegelbreite
    r0, r1 = 7.0, R - 1
    import math as m_
    for k in range(4):
        w = m_.radians(45 + 90 * k + 22.5 * ((frame or 0) % 4))
        ux, uy = m_.cos(w), m_.sin(w)                            # entlang des Fluegels
        nx, ny = -uy, ux                                          # quer
        P = lambda r, q: (cx + ux * r + nx * q, cy + uy * r + ny * q)
        ecken = [P(r0, -breite), P(r1, -breite), P(r1, breite), P(r0, breite)]
        d.line([P(0, 0), P(r1, 0)], fill=DUNKEL, width=3)         # Rute (Holm)
        for q in (-breite, breite):                               # Laengslatten
            d.line([P(r0, q), P(r1, q)], fill=DUNKEL, width=2)
        r = r0
        while r <= r1 + 0.1:                                      # Querlatten
            d.line([P(r, -breite), P(r, breite)], fill=DUNKEL, width=2)
            r += 7.0
        d.line([P(0, 0), P(r1, 0)], fill=ROT, width=1)            # Licht auf den Latten
        for q in (-breite, breite):
            d.line([P(r0, q), P(r1, q)], fill=HELL if q < 0 else ROT, width=1)
        r = r0
        while r <= r1 + 0.1:
            d.line([P(r, -breite), P(r, breite)], fill=ROT, width=1)
            r += 7.0
    d.ellipse((cx - 3, cy - 3, cx + 3, cy + 3), fill=(90, 58, 44, 255))   # Nabe
    d.point((cx - 1, cy - 1), fill=(192, 140, 88, 255))
    return img


def rauch20(img, objs, cache, frame):
    """Kaminrauch der Strohdachhaeuser: kleine Woelkchen steigen genau aus der Schornsteinoeffnung (hoechster
    Punkt des Sprites = Schornstein) und treiben mit dem Wind nach rechts, werden groesser und blasser.
    3 Woelkchen im Abstand eines Drittels, je Bild ein Viertel weiter -> nach 4 Bildern nahtlos."""
    from PIL import ImageDraw
    lage = Image.new('RGBA', img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lage)
    f = frame or 0
    for o in objs:
        if o.get('anim') != 'rauch20':
            continue
        a = np.array(cache[o['datei']].getchannel('A')) > 0
        ys, xs = np.nonzero(a)
        top = ys.min()
        kx = xs[ys <= top + 1].mean()
        X0, Y0 = o['x'] + kx, o['y'] + top - 1
        for i in range(3):                                        # 3 Woelkchen, je Bild 1/4 weiter -> sichtbare Bewegung
            ph = (f / 4.0 + i / 3.0) % 1.0
            cx, cy = X0 + 1 + ph * 12, Y0 - 2 - ph * 24
            rr = 2.5 + ph * 3.5
            al = int(235 * (1 - ph) ** 0.8)
            d.ellipse((cx - rr + 1, cy - rr + 1, cx + rr + 1, cy + rr + 1), fill=(170, 172, 182, int(al * 0.7)))   # Schattenseite
            d.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), fill=(232, 233, 240, al))
            d.point((cx - rr + 1.5, cy - rr + 1.5), fill=(255, 255, 255, al))
    img.alpha_composite(lage)


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
    # Fluss laeuft oben und links aus der Karte: Bild dort 24 px erweitern (Wasser laeuft weiter), damit am Kartenrand
    # keine Uferkante entsteht; danach wieder zuschneiden
    P = 24
    ag = np.pad(a, ((P, 0), (P, 0), (0, 0)), mode='edge')
    mg = np.pad(xm, ((P, 0), (P, 0)), mode='edge')
    ag = np.array(wasser_vertieft.vertiefen(Image.fromarray(ag), np.ones_like(mg), frame, maske=mg).convert('RGB'))
    a = ag[P:, P:]
    img = Image.fromarray(a).convert('RGBA')
    for (bx0, by0, bx1, by1) in lay['bruecken']:
        bauwerke.zeichne_bruecke(img, bx0 * T - 6, (bx1 + 1) * T + 6, by0 * T, (by1 + 1) * T - 4, frame=frame or 0)   # Enden auf dem Ufer
    vor_zaun = img.copy()
    k6.zaun(img, lay['acker_zaun'], (-9, -9))
    k6.zaun(img, lay['feld_zaun'], (-9, -9))
    # Seitentore, wo die Wege auf die Zaeune treffen (Weg endet nicht mehr stumpf am Zaun)
    for (tx, ty0, ty1) in lay.get('zaun_tore', []):
        box = (tx * T - 2, ty0 * T + 2, (tx + 1) * T + 6, (ty1 + 1) * T - 1)
        img.paste(vor_zaun.crop(box), box[:2])
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
            rauch20(img, objs, cache, frame)
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain.png'))
    print('Karte 20 %dx%d gebaut' % (cols, rows))
    return img


if __name__ == '__main__':
    bauen()
