"""Karte 10 (Toy Town): Spielzeugstadt mit Strassen, rosa Gehwegen, Plaetzen, Bahnhof mit Gleisen, rosa Burg mit
Burghof, Spielplatz, Teich mit Bruecke, Garten; Rand aus dichtem Wald wie Karte 01. Baut auf Karte 04/08/09 auf (Hecke, Wasser,
Schatten je Ebene, Verdeckung, Objekte, Animation).

  python3 tools/karte10_layout.py && python3 tools/karte10_kacheln.py
  python3 tools/karte10_bauen.py && python3 tools/karte10_objekte.py && python3 tools/regeln_v11.py karte10 \\
    && python3 tools/karte10_bauen.py
"""
import json, math, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageFilter
import karte_bauen as kb
import karte04_bauen as k4
import karte08_bauen as k8
import bauwerke
import wasser_vertieft

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte10')
BASIS = os.path.join(ROOT, 'assets', 'karte10', 'basis')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte10')
T = 16
N_FRAMES = 16
H = k4.H
weich, zell_maske = k4.weich, k4.zell_maske
WAND_H = 48
HECKE_HELL = ['#1c4a2a', '#286034', '#34783c', '#469044', '#5aa84c', '#74c058', '#9ad870']


def textur(art, cols, rows):
    t = np.zeros((rows * T, cols * T, 3), np.uint8)
    ks = [np.array(Image.open(os.path.join(BASIS, '%s_%d.png' % (art, v))).convert('RGB')) for v in range(5)]
    for y in range(rows):
        for x in range(cols):
            t[y * T:(y + 1) * T, x * T:(x + 1) * T] = ks[kb.variante(x, y)]
    return t


def kontur(m):
    return m & ~(np.roll(m, 1, 0) & np.roll(m, -1, 0) & np.roll(m, 1, 1) & np.roll(m, -1, 1))


def bordstein(a, flaeche, rand_farbe='#f0d4d8', schatten='#8a5a66'):
    """Bordstein um Gehwege/Plaetze: innen 1 px hell (Licht), aussen 1 px dunkle Kante."""
    innen = kontur(flaeche)
    a[innen] = H(rand_farbe)
    aussen = ~flaeche & (np.roll(flaeche, 1, 0) | np.roll(flaeche, -1, 0) | np.roll(flaeche, 1, 1) | np.roll(flaeche, -1, 1))
    a[aussen] = (a[aussen] * 0.7).astype(np.uint8)
    # unten/rechts eine Schattenkante (Kante steht 1 px hoch, Licht oben links)
    unten = flaeche & ~np.roll(flaeche, -1, 0)
    a[unten] = H(schatten)


def mittellinien(a, asph, cols, rows):
    """Gestrichelte gelbe Mittellinie auf Strassen (2 Kacheln breit) - nur auf geraden Stuecken, nicht in Kreuzungen."""
    Hh, W = asph.shape
    for y in range(Hh):
        for x in range(W):
            pass
    # senkrecht: Linie zwischen den beiden Asphaltspalten
    roh = asph[::T, ::T]
    for ty in range(rows):
        for tx in range(cols - 1):
            if roh[ty, tx] and roh[ty, tx + 1] and not (tx > 0 and roh[ty, tx - 1]) and not (tx + 2 < cols and roh[ty, tx + 2]):
                for y in range(ty * T, ty * T + T):
                    if (y // 6) % 2 == 0:
                        a[y, (tx + 1) * T - 1:(tx + 1) * T + 1] = H('#f4d860')
    for ty in range(rows - 1):
        for tx in range(cols):
            if roh[ty, tx] and roh[ty + 1, tx] and not (ty > 0 and roh[ty - 1, tx]) and not (ty + 2 < rows and roh[ty + 2, tx]):
                for x in range(tx * T, tx * T + T):
                    if (x // 6) % 2 == 0:
                        a[(ty + 1) * T - 1:(ty + 1) * T + 1, x] = H('#f4d860')


def zebra(a, x0, y0, b, h, senkrecht):
    """Zebrastreifen (Pixel): weisse Balken quer zur Fahrtrichtung."""
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + b):
            q = (x - x0) if senkrecht else (y - y0)   # senkrecht: Strasse laeuft N-S, Balken wechseln quer (x)
            if q % 6 < 3:
                a[y, x] = H('#f2f2f6') if q % 6 else H('#d8dae4')


def gleise(a, gl):
    """Schienen: Holzschwellen alle 6 px, zwei Stahlschienen mit Lichtkante, Schotterbett dunkler."""
    for g in gl:
        y = g['y'] * T
        x0, x1 = g['x'][0] * T, (g['x'][1]) * T
        bett = a[y - 1:y + 17, x0:x1]
        a[y - 1:y + 17, x0:x1] = (bett * 0.84).astype(np.uint8)
        for x in range(x0, x1):
            if x % 6 < 3:
                a[y + 1:y + 15, x] = H('#7a5236') if x % 6 else H('#9c6c44')
                a[y + 15, x] = H('#4a3222')
        for ys in (y + 3, y + 11):
            a[ys, x0:x1] = H('#d8dce8')
            a[ys + 1, x0:x1] = H('#7c8496')
            a[ys + 2, x0:x1] = H('#3a3e4c')


def herz(a, cx, cy, farbe='#e04c6a', hell='#ff9ab0', dunkel='#8a2040'):
    """Kleines Herz 7x6 px (Burgwand-Schmuck wie an der Burgfront)."""
    form = ['.##.##.', '#######', '#######', '.#####.', '..###..', '...#...']
    for j, z in enumerate(form):
        for i, c in enumerate(z):
            if c == '#':
                f = hell if (j == 1 and i in (1, 2)) else farbe
                a[cy + j, cx + i] = H(f)
    a[cy + 5, cx + 3] = H(dunkel)


def burgmauern(a, wm):
    """Rosa Burgmauern: Krone aus rosa Steinen mit Zinnen, nach Sueden 3 Kacheln Wandflaeche (Ziegel, Goldleiste,
    Sockel), Herzen in festem Rhythmus wie an der Burgfront; Seitenkanten nur als schmale Kontur."""
    Hh, W = wm.shape
    yy, xx = np.mgrid[0:Hh, 0:W]
    krone = wm
    z = (xx // 8 + (yy // 8) % 2) % 2
    a[krone] = np.where(z[krone][:, None] == 0, H('#d88a9e'), H('#e096a8'))
    fuge = krone & ((yy % 8 == 7) | ((xx + 4 * ((yy // 8) % 2)) % 8 == 7))
    a[fuge] = H('#b06a80')
    rand = kontur(wm)
    a[rand] = H('#7a3a52')
    obere = krone & ~np.roll(wm, 1, 0)
    for y, x in zip(*np.nonzero(obere)):
        if (x // 8) % 2 == 0:
            for dd in range(4):
                if y + dd < Hh and wm[y + dd, x]:
                    a[y + dd, x] = H('#ffd0dc') if dd == 0 else H('#eeaabb')
        else:
            for dd in range(3):
                if y + dd < Hh and wm[y + dd, x]:
                    a[y + dd, x] = H('#a05a70')
    flaeche = np.zeros_like(wm)
    sued = wm & ~np.roll(wm, -1, 0)
    sued[-1] = False
    for y, x in zip(*np.nonzero(sued)):
        for d in range(WAND_H):
            Y = y + 1 + d
            if Y >= Hh or wm[Y, x]:
                break
            flaeche[Y, x] = True
    d = np.zeros((Hh, W), np.int32)
    for y in range(1, Hh):
        d[y] = np.where(flaeche[y], np.where(flaeche[y - 1], d[y - 1] + 1, 0), 0)
    reihe = d // 8
    vers = np.where(reihe % 2 == 1, 8, 0)
    ziegel = (xx + vers) % 16
    basis = np.where(((xx // 16 + reihe) % 3 == 0)[..., None], H('#d48298'), H('#dc8ea2'))
    f = flaeche
    a[f] = basis[f]
    a[f & ((d % 8 == 7) | (ziegel == 15))] = H('#b0687e')
    a[f & (d % 8 == 0) & (ziegel != 15)] = H('#eaa8b8')
    a[f & (d <= 1)] = H('#f6c4d0')
    a[f & (d >= 2) & (d <= 4)] = (a[f & (d >= 2) & (d <= 4)] * 0.8).astype(np.uint8)
    a[f & (d >= WAND_H - 9) & (d <= WAND_H - 8)] = H('#f4cc5a')       # Goldleiste
    a[f & (d == WAND_H - 7)] = H('#b08a30')
    a[f & (d >= WAND_H - 6) & (d < WAND_H - 2)] = H('#c87890')       # Sockel
    a[f & (d >= WAND_H - 2)] = H('#9a5068')
    links = f & ~np.roll(f, 1, 1)
    rechts = f & ~np.roll(f, -1, 1)
    a[links] = H('#f6c4d0'); a[rechts] = H('#9a5068')
    unten = f & ~np.roll(f, -1, 0)
    for k_, fa in ((1, 0.62), (2, 0.74), (3, 0.86), (4, 0.94)):
        m_ = np.roll(unten, k_, 0) & ~f & ~wm
        a[m_] = (a[m_] * fa).astype(np.uint8)
    for richtung, faktoren in ((1, (0.7, 0.85)), (-1, (0.9,))):
        kante = wm & ~np.roll(wm, -richtung, 1)
        for k_, fa in enumerate(faktoren, 1):
            m_ = np.roll(kante, richtung * k_, 1) & ~wm & ~f
            a[m_] = (a[m_] * fa).astype(np.uint8)
    return flaeche


def herzen_auf_wand(a, flaeche, x_liste):
    """Herzreihen (je 3 Herzen) mittig auf der Wandflaeche - x_liste: Mittelpunkte in Pixeln."""
    ys, xs = np.nonzero(flaeche)
    for cx in x_liste:
        sp = flaeche[:, cx]
        if not sp.any():
            continue
        y_oben = np.nonzero(sp)[0].min()
        for dx in (-10, 0, 10):
            herz(a, cx + dx - 3, y_oben + 18)


def bauen(frame=None, speichern=True):
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cols, rows = lay['groesse']
    cls = lay['klassen']
    hoehe = np.array([[int(c) for c in r] for r in lay['hoehe']])
    Wp, Hp = cols * T, rows * T
    a = textur('g', cols, rows)
    # --- weiche Boeden: Sandweg, Erde
    for art, blur, rausch, seed in (('e', 4.0, 0.35, 4), ('s', 3.0, 0.3, 6)):
        roh = zell_maske(cls, art, cols, rows)
        m = weich(roh, blur, rausch, seed)
        tx = textur(art, cols, rows)
        a[m] = tx[m]
        saum = weich(roh, blur, rausch, seed, 0.4) & ~m
        k4.dunkeln(a, saum, 0.9)
    # Sand im Burg-/Bahnhofsbereich mit scharfen Kanten (gebaut)
    bau = np.zeros((Hp, Wp), bool)
    bau[:, 60 * T:] = True
    m = (zell_maske(cls, 's', cols, rows) > 0) & bau
    a[m] = textur('s', cols, rows)[m]
    # --- gebaute Flaechen: scharf
    for art in 'pbkrmqa':
        m = zell_maske(cls, art, cols, rows) > 0
        tx = textur(art, cols, rows)
        a[m] = tx[m]
    asph = zell_maske(cls, 'a', cols, rows) > 0
    geh = zell_maske(cls, 'p', cols, rows) > 0
    bordstein(a, geh)
    for art, hell in (('b', '#dceaf2'), ('q', '#ffe0e8'), ('r', '#f4c0cc'), ('k', '#f0dcc0'), ('m', '#b4b8ac')):
        mm = zell_maske(cls, art, cols, rows) > 0
        if art == 'k':
            mm |= zell_maske(cls, 'r', cols, rows) > 0
        bordstein(a, mm, hell, '#5a6070' if art in 'bm' else '#9a6a5a')
    mittellinien(a, asph, cols, rows)
    # Zebrastreifen vor den Kreuzungen (Gehweg zu Gehweg)
    for (x, y, b, h_, s) in ((30 * T + 2, 23 * T + 2, 28, 12, True), (44 * T + 2, 23 * T + 2, 28, 12, True),
                             (44 * T + 2, 39 * T + 2, 28, 12, True), (46 * T + 2, 36 * T + 2, 12, 28, False),
                             (41 * T + 2, 36 * T + 2, 12, 28, False)):
        zebra(a, x, y, b, h_, s)
    gleise(a, lay.get('gleise', []))
    # --- Wasser (Teich): klares Blau wie Karte 01, vertieft mit Steinrand
    wroh = zell_maske(cls, 'x', cols, rows)
    yy_, xx_ = np.mgrid[0:Hp, 0:Wp]
    tc = lay['teich']                                        # runder Teich (Pixel-Ellipse mit leichtem Wellenrand)
    wink = np.arctan2(yy_ - tc[1], xx_ - tc[0])
    wm = ((xx_ - tc[0]) / tc[2]) ** 2 + ((yy_ - tc[1]) / tc[3]) ** 2 <= 1 + 0.06 * np.sin(3 * wink) + 0.04 * np.cos(5 * wink)
    k4.wasser_zeichnen(a, wm, frame, np.zeros_like(wm))
    a = np.array(wasser_vertieft.vertiefen(Image.fromarray(a), np.ones_like(wm), frame, maske=wm,
                                           rand=('#6a6e80', '#868aa0', '#a2a6ba', '#c2c6d6'),
                                           stufen=[(16, 0.82, 5), (30, 0.66, 4)]).convert('RGB'))
    # --- Waldrand (wie Karte 01): schattiger, moosiger Waldboden, die Baeume kommen als Objekte
    wroh_ = zell_maske(cls, 'W', cols, rows)
    hm = weich(wroh_, 5, 0.4, 8)
    a[hm] = (a[hm] * np.array([0.72, 0.8, 0.7])).astype(np.uint8)
    saum = weich(wroh_, 5, 0.4, 8, 0.32) & ~hm
    a[saum] = (a[saum] * 0.86).astype(np.uint8)
    mauer = zell_maske([''.join('1' if c == '3' else '0' for c in r) for r in lay['hoehe']], '1', cols, rows) > 0
    flaeche = burgmauern(a, mauer)
    achse = int(lay['achse'] * T)
    # Herzreihen zwischen Burgfront und Ecktuermen (symmetrisch zur Achse)
    herzen_auf_wand(a, flaeche, [achse - 141, achse + 141])
    lvl = np.ones((Hp, Wp), np.uint8)
    lvl[wm] = 0
    lvl[mauer] = 3
    lvl[flaeche] = 9
    if speichern and frame is None:
        np.save(os.path.join(KARTE, 'pixelhoehe.npy'), lvl)
        np.save(os.path.join(KARTE, 'wandflaeche.npy'), np.packbits(flaeche))
    img = Image.fromarray(a).convert('RGBA')
    for (x0, y0, x1, y1) in lay.get('bruecken', []):
        bauwerke.zeichne_bruecke(img, x0 * T - 2, (x1 + 1) * T + 2, y0 * T + 2, (y1 + 1) * T - 2, frame=frame or 0,
                                 seed=x0, wasser=True)
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
        k8.schatten_ebene(img, [o for o in objs if not o.get('an_wand')], cache, lvl_s)
        vor_objekten = np.array(img)
        k4.objekte_zeichnen(img, objs, cache, np.zeros((Hp, Wp), bool), frame)
        k4.animieren(img, objs, cache, frame or 0, ruhig=frame is None)
        k8.verdeckung(img, [o for o in objs if not o.get('an_wand')], cache, lvl, vor_objekten)
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain.png'))
    print('Karte 10 %dx%d gebaut' % (cols, rows))
    return img


if __name__ == '__main__':
    bauen()
