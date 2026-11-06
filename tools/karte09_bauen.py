"""Karte 09 (Vamdemon's Keep): Schloss oben (Raeume, Mauern mit Fensterwaenden, Teppiche), Burggraben mit
Zugbruecke, Friedhof unten (Wege, dunkle Teiche mit Bruecken, Felsplateaus, roetlicher Felsrand).
Baut auf Karte 04/08 auf (Kanten, Schatten je Ebene, Verdeckung, Objekte, Animation).

  python3 tools/karte09_layout.py && python3 tools/karte09_kacheln.py
  python3 tools/karte09_bauen.py && python3 tools/karte09_objekte.py && python3 tools/regeln_v11.py karte09 \\
    && python3 tools/karte09_bauen.py
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
KARTE = os.path.join(ROOT, 'maps', 'karte09')
BASIS9 = os.path.join(ROOT, 'assets', 'karte09', 'basis')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte09')
T = 16
N_FRAMES = 16
H = k4.H
weich, zell_maske = k4.weich, k4.zell_maske
k4.FELS['rotfels'] = ['#140c0e', '#201416', '#2c1c1e', '#3a2628', '#4a3234', '#5c4042', '#705052']
LIPPE_ROT = ['#1e1416', '#2a1c1e', '#362426', '#422c2e', '#503638', '#5e4244']
WAND_H = 48                          # Hoehe der Mauer-Wandflaeche (3 Kacheln)


def textur(cls, art, cols, rows):
    t = np.zeros((rows * T, cols * T, 3), np.uint8)
    ks = [np.array(Image.open(os.path.join(BASIS9, '%s_%d.png' % (art, v))).convert('RGB')) for v in range(5)]
    for y in range(rows):
        for x in range(cols):
            t[y * T:(y + 1) * T, x * T:(x + 1) * T] = ks[kb.variante(x, y)]
    return t


def mauern_zeichnen(a, wm):
    """Schlossmauern: Krone aus dunklem Schiefer, nach Sueden eine 3 Kacheln hohe Wandflaeche (Ziegelverband,
    Lichtkante oben, Goldleiste unten, Schatten auf den Boden). Seitenkanten nur als schmale Kontur.
    -> Maske der Wandflaechen (fuer Fenster/Banner und als Sperre fuer Bodenobjekte)."""
    Hh, W = wm.shape
    flaeche = np.zeros_like(wm)
    yy, xx = np.mgrid[0:Hh, 0:W]
    # Krone
    krone = wm.copy()
    z = (xx // 8 + (yy // 8) % 2) % 2
    a[krone] = np.where(z[krone][:, None] == 0, H('#2c3040'), H('#323648'))
    fuge = krone & ((yy % 8 == 7) | ((xx + 4 * ((yy // 8) % 2)) % 8 == 7))
    a[fuge] = H('#22252f')
    rand = krone & ~(np.roll(wm, 1, 0) & np.roll(wm, -1, 0) & np.roll(wm, 1, 1) & np.roll(wm, -1, 1))
    a[rand] = H('#1a1c24')
    oben = krone & ~np.roll(wm, 1, 0)
    a[oben] = H('#4a5068')                                   # Lichtkante (Licht oben links)
    # Wandflaechen unter jeder Suedkante
    sued = wm & ~np.roll(wm, -1, 0)
    sued[-1] = False
    for y, x in zip(*np.nonzero(sued)):
        for d in range(WAND_H):
            Y = y + 1 + d
            if Y >= Hh or wm[Y, x]:
                break
            flaeche[Y, x] = True
    ys, xs = np.nonzero(flaeche)
    # Abstand zur Oberkante der Flaeche
    d = np.zeros((Hh, W), np.int32)
    for y in range(1, Hh):
        d[y] = np.where(flaeche[y], np.where(flaeche[y - 1], d[y - 1] + 1, 0), 0)
    reihe = d // 8
    vers = np.where(reihe % 2 == 1, 8, 0)
    ziegel = (xx + vers) % 16
    basis = np.where(((xx // 16 + reihe) % 3 == 0)[..., None], H('#464c60'), H('#4c5368'))
    f = flaeche
    a[f] = basis[f]
    a[f & ((d % 8 == 7) | (ziegel == 15))] = H('#353a4a')           # Fugen
    a[f & (d % 8 == 0) & (ziegel != 15)] = H('#586078')              # Lichtkante je Ziegelreihe
    a[f & (d <= 1)] = H('#6c7490')                                   # Oberkante der Wand im Licht
    a[f & (d >= WAND_H - 9) & (d <= WAND_H - 8)] = H('#e0b85a')      # Goldleiste
    a[f & (d == WAND_H - 7)] = H('#a07a30')
    a[f & (d >= WAND_H - 6) & (d < WAND_H - 2)] = H('#3a3f50')       # Sockel
    a[f & (d >= WAND_H - 2)] = H('#262a36')
    # seitliche Enden der Wandflaechen (an Tuer-Oeffnungen): Kontur und Licht/Schatten
    links = f & ~np.roll(f, 1, 1)
    rechts = f & ~np.roll(f, -1, 1)
    a[links] = H('#6c7490'); a[rechts] = H('#22252f')
    # Schatten der Wand auf den Boden darunter
    unten = f & ~np.roll(f, -1, 0)
    for k_, fa in ((1, 0.62), (2, 0.74), (3, 0.86), (4, 0.94)):
        m_ = np.roll(unten, k_, 0) & ~f & ~wm
        a[m_] = (a[m_] * fa).astype(np.uint8)
    # Seitenkanten der Mauern auf dem Boden: schmale Kontur + leichter Schatten rechts (Licht von links)
    for richtung, faktoren in ((1, (0.7, 0.85)), (-1, (0.9,))):
        kante = wm & ~np.roll(wm, -richtung, 1)
        for k_, fa in enumerate(faktoren, 1):
            m_ = np.roll(kante, richtung * k_, 1) & ~wm & ~f
            a[m_] = (a[m_] * fa).astype(np.uint8)
    return flaeche


def teppich_rand(a, m):
    """Goldener Saum um die Teppiche (innen 1 px Gold, aussen 1 px dunkle Kante)."""
    innen = m & ~(np.roll(m, 1, 0) & np.roll(m, -1, 0) & np.roll(m, 1, 1) & np.roll(m, -1, 1))
    a[innen] = H('#c8a048')
    aussen = ~m & (np.roll(m, 1, 0) | np.roll(m, -1, 0) | np.roll(m, 1, 1) | np.roll(m, -1, 1))
    a[aussen] = (a[aussen] * 0.6).astype(np.uint8)


def wasser_dunkel(a, m, frame):
    """Graben/Teiche: tiefes, fast schwarzes Wasser mit kaltem Schimmer."""
    k4.wasser_zeichnen(a, m, frame, np.zeros_like(m))
    lum = (a[m].astype(np.float32) @ np.array([0.3, 0.59, 0.11], np.float32))[:, None]
    a[m] = np.clip(lum * np.array([0.22, 0.26, 0.5]) + np.array([4, 6, 22]), 0, 255).astype(np.uint8)


def bauen(frame=None, speichern=True):
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cols, rows = lay['groesse']
    cls = lay['klassen']
    hoehe = np.array([[int(c) for c in r] for r in lay['hoehe']])
    Wp, Hp = cols * T, rows * T
    a = textur(cls, 'g', cols, rows)
    schloss = np.zeros((Hp, Wp), bool)
    schloss[:40 * T] = True
    # --- Friedhof: weiche Bodenarten
    for art, blur, rausch, seed in (('h', 6.0, 0.45, 3), ('e', 3.0, 0.2, 4), ('w', 4.0, 0.42, 6)):
        roh = zell_maske(cls, art, cols, rows)
        m = weich(roh, blur, rausch, seed) & ~schloss
        tx = textur(cls, art, cols, rows)
        a[m] = tx[m]
        saum = weich(roh, blur, rausch, seed, 0.38) & ~m & ~schloss
        k4.dunkeln(a, saum, 0.9)
    # --- Schloss innen: scharfe Kanten (Steinboden, Garten, Beet, Teppiche)
    for art in 'ihec':
        m = (zell_maske(cls, art, cols, rows) > 0) & schloss
        tx = textur(cls, art, cols, rows)
        a[m] = tx[m]
    vm = (zell_maske(cls, 'v', cols, rows) > 0) & schloss
    tx = textur(cls, 'v', cols, rows)
    a[vm] = tx[vm]
    cm = (zell_maske(cls, 'c', cols, rows) > 0) & schloss
    teppich_rand(a, cm)
    teppich_rand(a, vm)
    # --- Ebenen
    mauer = (k8.stufe(hoehe, 3, cols, rows) > 0) & (zell_maske([''.join('1' if c == '3' else '0' for c in r) for r in lay['hoehe']], '1', cols, rows) > 0)
    m2 = weich(k8.stufe(hoehe, 2, cols, rows), 5, 0.2, 31) & ~schloss & ~mauer
    m7 = weich(k8.stufe(hoehe, 7, cols, rows), 6, 0.3, 37)
    m2 |= m7
    tx = textur(cls, 'f', cols, rows)
    pl = m2 & ~m7
    a[pl] = tx[pl]
    tx = textur(cls, 'r', cols, rows)
    a[m7] = tx[m7]
    # --- Wasser: Graben (scharf) und Teiche (weich), vertieft mit Steinrand
    wroh = zell_maske(cls, 'x', cols, rows)
    graben = (wroh > 0) & schloss
    graben[40 * T:43 * T, :] = True
    teiche = weich(wroh, 7, 0.2, 41, 0.45) & ~schloss
    teiche = k4.splitter_weg(teiche, 150)
    wm = graben | teiche
    wasser_dunkel(a, wm, frame)
    import wasser_vertieft
    a = np.array(wasser_vertieft.vertiefen(Image.fromarray(a), np.ones_like(wm), frame, maske=wm,
                                           rand=('#1c1e26', '#2a2c36', '#383a46', '#464856'),
                                           stufen=[(20, 0.78, 6), (40, 0.6, 5)]).convert('RGB'))
    lum = (a[wm].astype(np.float32) @ np.array([0.3, 0.59, 0.11], np.float32))[:, None]
    a[wm] = np.clip(lum * np.array([0.34, 0.4, 0.72]) + np.array([2, 4, 16]), 0, 255).astype(np.uint8)
    # --- Kanten: Felsplateaus und Felsrand (wie Karte 08), Schlossmauern eigen
    frei = np.zeros((Hp, Wp), bool)
    waende = k4.hoehenkanten(a, m2, 'terrasse', 26, 12, k8.LIPPE_TERRASSE, frei | schloss, 52, berg=False)
    waende |= k4.hoehenkanten(a, m7, 'rotfels', 36, 12, LIPPE_ROT, frei | schloss, 57, berg=False)
    flaeche = mauern_zeichnen(a, mauer)
    lvl = np.ones((Hp, Wp), np.uint8)
    lvl[m2] = 2
    lvl[m7] = 7
    lvl[wm] = 0
    lvl[waende] = 9
    lvl[mauer] = 3
    lvl[flaeche] = 9
    if speichern and frame is None:
        np.save(os.path.join(KARTE, 'pixelhoehe.npy'), lvl)
        np.save(os.path.join(KARTE, 'wandflaeche.npy'), np.packbits(flaeche))
    img = Image.fromarray(a).convert('RGBA')
    # --- Zugbruecke, Bruecke, Steg, Teleporter
    zb = lay.get('zugbruecke')
    if zb:
        bauwerke.zeichne_steg(img, zb[0] * T + 2, (zb[2] + 1) * T - 2, zb[1] * T - 2, (zb[3] + 1) * T + 6,
                              frame=frame or 0, seed=3)
    for (x0, y0, x1, y1) in lay.get('bruecken', []):
        bauwerke.zeichne_bruecke(img, x0 * T - 6, (x1 + 1) * T + 6, y0 * T + 1, (y1 + 1) * T - 1, frame=frame or 0,
                                 seed=x0, wasser=True)
    for (x0, y0, x1, y1) in lay.get('stege', []):
        bauwerke.zeichne_steg(img, x0 * T + 2, (x1 + 1) * T - 2, y0 * T - 4, (y1 + 1) * T + 4, frame=frame or 0, seed=y0)
    a = np.array(img.convert('RGB'))
    for tp in lay.get('teleporter', []):
        k4.teleporter_zeichnen(a, tp['x'], tp['y'], tp['b'], tp['h'], frame)
    img = Image.fromarray(a).convert('RGBA')
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain_basis.png'))
    # --- Objekte
    pf = os.path.join(OBJ, 'platzierung.json')
    if os.path.exists(pf):
        objs = sorted((o for o in json.load(open(pf)) if os.path.exists(os.path.join(OBJ, o['datei']))),
                      key=lambda o: (0 if o.get('an_wand') else 1, o['y'] + o['fuss']))
        cache = {o['datei']: Image.open(os.path.join(OBJ, o['datei'])).convert('RGBA') for o in objs}
        lvl_s = lvl.copy()
        lvl_s[flaeche] = 9
        k8.schatten_ebene(img, [o for o in objs if not o.get('an_wand')], cache, lvl_s)
        vor_objekten = np.array(img)
        k4.objekte_zeichnen(img, objs, cache, np.zeros((Hp, Wp), bool), frame)
        k4.animieren(img, objs, cache, frame or 0, ruhig=frame is None)
        k8.verdeckung(img, [o for o in objs if not o.get('an_wand')], cache, lvl, vor_objekten)
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain.png'))
    print('Karte 09 %dx%d gebaut' % (cols, rows))
    return img


if __name__ == '__main__':
    bauen()
