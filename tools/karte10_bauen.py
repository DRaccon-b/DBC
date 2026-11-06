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


def gleis_pfade(lay):
    """Mittellinien aller Gleise (Pixel, 1 px Abstand): gerade Gleise und das Verbindungsgleis mit zwei Boegen."""
    pfade = []
    for g in lay.get('gleise', []):
        yc = g['y'] * T + 7
        pfade.append([(float(x), float(yc)) for x in range(g['x'][0] * T, g['x'][1] * T)])
    b = lay.get('gleisbogen')
    if b:
        x, r, yo, yu = b['x'], b['r'], b['oben_y'], b['unten_y']
        p = [(float(xx), float(yo)) for xx in range(b['von_x'], x - r)]
        n = int(math.pi / 2 * r)
        p += [(x - r + r * math.cos(-math.pi / 2 + math.pi / 2 * i / n), yo + r + r * math.sin(-math.pi / 2 + math.pi / 2 * i / n)) for i in range(n)]
        p += [(float(x), float(yy)) for yy in range(yo + r, yu - r)]
        p += [(x + r + r * math.cos(math.pi - math.pi / 2 * i / n), yu - r + r * math.sin(math.pi - math.pi / 2 * i / n)) for i in range(n)]
        p += [(float(xx), float(yu)) for xx in range(x + r, b['bis_x'] + 8)]
        pfade.append(p)
    return pfade


def gleise(a, lay):
    """Schienen entlang der Mittellinien: Schotterbett dunkler, Holzschwellen alle 6 px quer zur Fahrtrichtung,
    zwei Stahlschienen mit Lichtkante (auch in den Boegen)."""
    Hh, W = a.shape[:2]
    pfade = gleis_pfade(lay)

    def setz(x, y, c):
        xi, yi = int(round(x)), int(round(y))
        if 0 <= xi < W and 0 <= yi < Hh:
            a[yi, xi] = c
    bett = np.zeros((Hh, W), bool)
    for p in pfade:
        for (x, y) in p:
            xi, yi = int(round(x)), int(round(y))
            bett[max(0, yi - 8):min(Hh, yi + 10), max(0, xi - 8):min(W, xi + 9)] = True
    a[bett] = (a[bett] * 0.84).astype(np.uint8)
    rich = []
    for p in pfade:
        r_ = []
        for i in range(len(p)):
            x0, y0 = p[max(0, i - 2)]
            x1, y1 = p[min(len(p) - 1, i + 2)]
            l = math.hypot(x1 - x0, y1 - y0) or 1
            r_.append(((x1 - x0) / l, (y1 - y0) / l))
        rich.append(r_)
    for p, r_ in zip(pfade, rich):                       # Schwellen
        for i, ((x, y), (tx, ty)) in enumerate(zip(p, r_)):
            if i % 6 < 3:
                nx, ny = -ty, tx
                c = H('#7a5236') if i % 6 else H('#9c6c44')
                for o in np.arange(-6, 7.5, 0.5):
                    setz(x + nx * o + tx * 0, y + ny * o, c)
                setz(x + nx * 8, y + ny * 8, H('#4a3222'))
    for p, r_ in zip(pfade, rich):                       # Schienen
        for (x, y), (tx, ty) in zip(p, r_):
            nx, ny = -ty, tx
            for o in (-4, 4):
                setz(x + nx * o, y + ny * o, H('#d8dce8'))
                setz(x + nx * (o + 1), y + ny * (o + 1), H('#7c8496'))
                setz(x + nx * (o + 2), y + ny * (o + 2), H('#3a3e4c'))


def herz(a, cx, cy, farbe='#e04c6a', hell='#ff9ab0', dunkel='#8a2040'):
    """Kleines Herz 7x6 px (Burgwand-Schmuck wie an der Burgfront)."""
    form = ['.##.##.', '#######', '#######', '.#####.', '..###..', '...#...']
    for j, z in enumerate(form):
        for i, c in enumerate(z):
            if c == '#':
                f = hell if (j == 1 and i in (1, 2)) else farbe
                a[cy + j, cx + i] = H(f)
    a[cy + 5, cx + 3] = H(dunkel)


# Farben des Hauptschlosses (PixelLab k10_schloss) - Mauern, Zinnen und Wehrgang in genau diesem Stil
SCHLOSS = {'hell': '#ffd0e8', 'ziegel': '#f09ac8', 'fuge': '#d06a9a', 'kontur': '#6a3a9a', 'gold': '#f8d040',
           'gold2': '#e0a020', 'goldhell': '#fff080', 'glas': '#6aa8f0', 'glashell': '#a8d0ff', 'weg': '#f8c0dc',
           'weg2': '#f4b2d2', 'wegfuge': '#e098bc'}


def burgmauern(a, wm):
    """Burgmauern im Stil des Hauptschlosses: oben ein Wehrgang aus hellrosa Platten mit violetter Kontur, an der
    Suedkante Zinnen (Merlons mit heller Oberkante), nach Sueden 3 Kacheln Wandflaeche aus rosa Ziegeln mit feinen
    Fugen, Schattenkante unter dem Wehrgang, Goldleiste und Sockel. An Ost- und Suedmauer (keine sichtbare
    Wandflaeche) stehen die Zinnen zum Burghof hin. Seitenkanten nur als schmale Kontur."""
    C = {k: np.array(H(v)) for k, v in SCHLOSS.items()}
    Hh, W = wm.shape
    yy, xx = np.mgrid[0:Hh, 0:W]
    # --- Wehrgang (Krone, von oben): Platten 8x8 im Verband
    pl = (xx // 8 + (yy // 8)) % 2
    a[wm] = np.where(pl[wm][:, None] == 0, C['weg'], C['weg2'])
    fuge = wm & ((yy % 8 == 7) | ((xx + 4 * ((yy // 8) % 2)) % 8 == 7))
    a[fuge] = C['wegfuge']
    rand = kontur(wm)
    a[rand] = C['kontur']
    # --- Wandflaechen unter jeder Suedkante
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
    f = flaeche
    reihe = d // 8
    zx = (xx + np.where(reihe % 2 == 1, 8, 0)) % 16
    a[f] = C['ziegel']
    a[f & ((d % 8 == 7) | (zx == 15))] = C['fuge']
    a[f & (d % 8 == 0) & (zx >= 1) & (zx <= 6)] = C['hell']                 # Lichtkante je Ziegel (Licht oben links)
    a[f & (d <= 1)] = C['hell']
    sch = f & (d >= 2) & (d <= 4)
    a[sch] = (a[sch] * 0.84).astype(np.uint8)                              # Schatten unter dem Wehrgang
    a[f & (d >= WAND_H - 10) & (d <= WAND_H - 9)] = C['gold']               # Goldleiste
    a[f & (d == WAND_H - 8)] = C['gold2']
    a[f & (d >= WAND_H - 7) & (d < WAND_H - 1)] = C['fuge']                 # Sockel
    a[f & (d >= WAND_H - 7) & (d < WAND_H - 1) & (zx == 15)] = C['kontur']
    a[f & (d == WAND_H - 7)] = C['ziegel']
    a[f & (d == WAND_H - 1)] = C['kontur']
    a[f & ~np.roll(f, 1, 1)] = C['kontur']; a[f & ~np.roll(f, -1, 1)] = C['kontur']
    # --- Zinnen an der Suedkante des Wehrgangs (ragen ueber den Wehrgang, vor der Wandflaeche)
    for y, x in zip(*np.nonzero(sued)):
        q = x % 16
        if q < 9:                                                            # Merlon 9 px breit, 8 px hoch
            for k in range(8):
                Y = y - k
                if Y < 0 or not wm[Y, x]:
                    break
                c = C['kontur'] if (q in (0, 8) or k == 7) else C['hell'] if k >= 5 else C['ziegel']
                a[Y, x] = c
            if 0 <= y - 8 and wm[y - 8, x]:
                a[y - 8, x] = (a[y - 8, x] * 0.8).astype(np.uint8)          # Schatten hinter der Zinne
    # --- Zinnen zum Burghof an Ost-/Suedmauer (Kanten ohne Wandflaeche): kleine Merlons von oben
    for richtung in ((0, 1), (0, -1), (-1, 0)):                              # West-, Ost- bzw. Nordkante
        dy, dx = richtung
        kante = wm & ~np.roll(np.roll(wm, -dy, 0), -dx, 1)
        kante &= ~sued
        for y, x in zip(*np.nonzero(kante)):
            lauf = y if dx else x
            if lauf % 12 < 6:
                for k in range(5):
                    Y, X = y + dy * k * 0 - (k if dy == 0 else 0) * 0, x
                    Y2, X2 = y - dy * k, x - dx * k
                    if 0 <= Y2 < Hh and 0 <= X2 < W and wm[Y2, X2]:
                        a[Y2, X2] = C['kontur'] if k == 4 or lauf % 12 in (0, 5) else C['hell'] if k <= 1 else C['ziegel']
    # --- Schatten der Wand auf den Boden, Seitenkanten auf dem Boden
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


def fenster_auf_wand(a, flaeche, x_liste):
    """Kleine Bogenfenster wie am Hauptschloss (violetter Rahmen, blaues Glas mit Lichtkante) mittig auf der
    Wandflaeche, frei haengend zwischen Wehrgang-Schatten und Goldleiste."""
    C = {k: H(v) for k, v in SCHLOSS.items()}
    form = ['..###..', '.#ggg#.', '#gGggg#', '#gGggg#', '#gGggg#', '#ggggg#', '#ggggg#', '#ggggg#', '#######']
    for cx in x_liste:
        sp = flaeche[:, cx]
        if not sp.any():
            continue
        y0 = np.nonzero(sp)[0].min() + 15
        for j, z in enumerate(form):
            for i, c in enumerate(z):
                if c == '.':
                    continue
                a[y0 + j, cx - 3 + i] = C['kontur'] if c == '#' else C['glashell'] if c == 'G' else C['glas']


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
    gleise(a, lay)
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
    # Bogenfenster im festen Rhythmus zwischen Torbau und Ecktuermen, symmetrisch zur Achse
    fenster_auf_wand(a, flaeche, [achse + s_ * d_ for s_ in (-1, 1) for d_ in (112, 140)])
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
