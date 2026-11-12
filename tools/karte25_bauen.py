"""Karte 25 - Sunset Bay (A02), Gelaende im Stil von Karte 01 / 20 / 23.

Gras und Sand aus Karte 01 (assets/basis), Weg auf dem Plateau aus Sandkacheln, nasser Sand an der Hafenkante,
Grasplateau mit Sandstein-Felsfront (Karte 04) und zwei Treppen, Meer wie Karte 01 (wasser_details.meer_terrassen):
Flachwasser mit Sandgrund, Schaum und Brandung am Strand, Stufenkante an der Grenze Flach/Tief laut Vorlage, Tiefsee
mit zweiter Stufe; Holzstege (Planken mit Pfaehlen), Teleporter (Karte 04).

  python3 tools/karte25_layout.py && python3 tools/karte25_bauen.py
"""
import json, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageFilter
import karte_bauen as kb
import karte04_bauen as k4
import karte06_bauen as k6
import karte20_bauen as k20
import wasser_details as wd

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte25')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte25')
T = 16
N_FRAMES = 4
k4.N_FRAMES = N_FRAMES
import karte_bauen as _kb
_kb.N_FRAMES = N_FRAMES                       # Windwelle (Pflanzen) ueber die 4 Bilder der Karte
H = k4.H
weich, zell_maske, flaeche = k4.weich, k4.zell_maske, k20.flaeche
k4.RASTER45 = True                       # Nutzer: ALLE Bodenkanten am 16er-Raster mit 45 Grad (Regel 6b)
FRONT = 32


def maske(cls, arten):
    return np.kron(np.array([[c in arten for c in z] for z in cls]), np.ones((T, T), bool))


def abstand(m, schritte=160):
    """Abstand (px, halbe Aufloesung, dann hochskaliert) jedes Pixels zur Maske m."""
    Hh, W = m.shape
    k = np.array(Image.fromarray((m * 255).astype(np.uint8)).resize((W // 2, Hh // 2), Image.NEAREST)) > 0
    d = np.full(k.shape, 999.0, np.float32)
    d[k] = 0
    for i in range(1, schritte):
        k2 = np.array(Image.fromarray((k * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3))) > 0
        neu = k2 & ~k
        if not neu.any():
            break
        d[neu] = i * 2
        k = k2
    return np.array(Image.fromarray(d).resize((W, Hh), Image.BILINEAR))


def stege(a, lay, wasser):
    """Holzstege: Planken quer zur Laufrichtung, Kontur nur am Aussenrand der ganzen Steganlage (Abzweige gehen
    nahtlos in den Hauptsteg ueber), Suedfront mit Pfaehlen ins Wasser, Schatten auf dem Wasser rechts unten."""
    HELL, MITTE, DUNKEL, KONTUR = H('#a8784a'), H('#8a5e38'), H('#6a4428'), H('#3a2616')
    oben = np.zeros(wasser.shape, bool)
    for (x0, y0, x1, y1) in lay['stege']:
        oben[y0 * T:(y1 + 1) * T, x0 * T:(x1 + 1) * T] = True
    for (x0, y0, x1, y1) in lay['stege']:
        X0, X1, Y0, Y1 = x0 * T, (x1 + 1) * T, y0 * T, (y1 + 1) * T
        senk = (y1 - y0) >= (x1 - x0)
        for y in range(Y0, Y1):
            for x in range(X0, X1):
                i = (y - Y0) if senk else (x - X0)
                c = HELL if i % 4 == 0 else (DUNKEL if i % 4 == 3 else MITTE)
                if (x * 7 + y * 3) % 23 == 0:
                    c = DUNKEL
                a[y, x] = c
    Hh, W = oben.shape
    nb = lambda dy, dx: np.roll(np.roll(oben, dy, 0), dx, 1)
    rand = oben & (~nb(0, 1) | ~nb(0, -1) | ~nb(1, 0))               # links, rechts, oben offen -> Kontur
    a[rand] = KONTUR
    unten = oben & ~nb(-1, 0)                                         # unterste Plankenzeile je Spalte
    ys, xs = np.nonzero(unten)
    for y, x in zip(ys, xs):                                          # Suedfront 5 px + Pfaehle
        for d in range(1, 10):
            yy = y + d
            if yy >= Hh or oben[yy, x]:
                break
            if d < 6:
                a[yy, x] = HELL if d == 1 else DUNKEL
            elif (x % 16) in (3, 4, 5, 11, 12, 13):
                a[yy, x] = KONTUR
    front = np.zeros_like(oben)
    for d in range(1, 10):
        front |= np.roll(unten, d, 0)
    front &= ~oben
    sch = (np.roll(np.roll(oben | front, 4, 0), 6, 1)) & ~oben & ~front & wasser
    a[sch] = (a[sch] * 0.68).astype(np.uint8)
    return oben | front


SCHIFF_POS = (1424, 93)                  # Kaiser-Flaggschiff (eigener Entwurf, Nutzer: Variante A): Deck am Bug auf Hoehe des Anlegers
SCHIFF_DATEI = os.path.join('schiff_a', '00_sauber.png')


def schiff(a, wasser, frame):
    """Schiff (PixelLab Pro-Generator, Ausnahme Nutzer) im tiefen Wasser: Schatten nach rechts unten nur auf dem Wasser,
    Schaum an der Wasserlinie (wandert je Bild), Sprite darueber."""
    sp = np.array(Image.open(os.path.join(OBJ, SCHIFF_DATEI)).convert('RGBA'))
    if frame is not None:                                            # Wimpel wehen, Auge und Bullaugen gluehen
        sp = np.array(k4.wimpel(Image.fromarray(sp), frame, {'wimpel': [[149, 86, 192, 112, 1], [377, 76, 418, 102, 1]],
                                                               'x': SCHIFF_POS[0]}))
        si = sp.astype(np.int16)
        rot = (si[..., 3] > 0) & (si[..., 0] > 150) & (si[..., 1] < 90) & (si[..., 2] < 90)
        auge = rot & k4._box_maske(sp.shape, [272, 62, 306, 94])
        luken = rot & k4._box_maske(sp.shape, [140, 200, 430, 240])
        f1 = 0.85 + 0.3 * (0.5 + 0.5 * math.sin(2 * math.pi * frame / N_FRAMES))
        f2 = 0.9 + 0.2 * (0.5 + 0.5 * math.sin(2 * math.pi * frame / N_FRAMES + 2.0))
        si[auge, :3] = np.clip(si[auge, :3] * f1, 0, 255)
        si[luken, :3] = np.clip(si[luken, :3] * f2, 0, 255)
        sp = si.astype(np.uint8)
    al = sp[..., 3] > 0
    x0, y0 = SCHIFF_POS
    h, w = al.shape
    Hh, W = a.shape[:2]
    sch = np.zeros((Hh, W), bool)                                    # Schatten: Silhouette 8 px rechts, 6 px tiefer
    ys, xs = np.nonzero(al)
    Y, X = ys + y0 + 6, xs + x0 + 8
    ok = (Y < Hh) & (X < W)
    sch[Y[ok], X[ok]] = True
    rumpf = np.zeros((Hh, W), bool); rumpf[ys + y0, xs + x0] = True
    sch &= wasser & ~rumpf
    a[sch] = (a[sch] * 0.62).astype(np.uint8)
    f = frame or 0
    for x in range(w):                                               # Schaum an der Wasserlinie
        col = np.nonzero(al[:, x])[0]
        if not len(col):
            continue
        yb = y0 + col.max()
        X_ = x0 + x
        for d in (1, 2):
            if yb + d < Hh and wasser[yb + d, X_] and ((X_ + 3 * f) // 3) % 4 != (0 if d == 1 else 2):
                a[yb + d, X_] = np.clip(a[yb + d, X_] * 0.35 + np.array((230, 245, 250)) * 0.65, 0, 255).astype(np.uint8)
    im = Image.fromarray(a).convert('RGBA')
    im.alpha_composite(Image.fromarray(sp), (x0, y0))
    a[:] = np.array(im.convert('RGB'))
    return rumpf


def bauen(frame=None, speichern=True):
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cls = lay['klassen']
    cols, rows = lay['groesse']
    Wp, Hp = cols * T, rows * T
    hp = np.kron(np.array([[int(c) for c in z] for z in lay['hoehe']]), np.ones((T, T), int))
    basis = os.path.join(ROOT, 'assets', 'basis')
    gras = flaeche(k6.kacheln(os.path.join(basis, 'gras_%d.png'), 5), cols, rows)
    sand = flaeche(k6.kacheln(os.path.join(basis, 'sand_%d.png'), 5), cols, rows)
    a = sand.copy()
    # nasser Sand (Hafenkante, Wasserlinie)
    nm = weich(zell_maske(cls, 'n', cols, rows), 6.0, 0.5, 5)
    a[nm] = (sand[nm] * np.array([0.82, 0.78, 0.72])).astype(np.uint8)
    # Plateau: Gras, darauf Wege und Sandplatz aus Sandkacheln
    hoch = weich((hp >= 2).astype(np.float32), 5, 0.0, 7, 0.5)
    a[hoch] = gras[hoch]
    wm = weich(zell_maske(cls, 'wst', cols, rows), 5.0, 0, 4) & hoch
    a[wm] = sand[wm]
    saum = weich(zell_maske(cls, 'wst', cols, rows), 5.0, 0, 4, 0.28) & ~wm & hoch
    a[saum] = (a[saum] * 0.9).astype(np.uint8)
    # Felsfront des Plateaus (Sandstein wie die Vorlage) mit zwei Treppen
    lippe = k20.lippe_aus_gras(gras)
    frei = np.zeros((Hp, Wp), bool)
    for (x0, x1, ye) in lay['treppen']:
        yE = (ye + 1) * T - 1
        frei[yE - 14:yE + 40, x0 * T:(x1 + 1) * T] = True
    oben = np.zeros((Hp, Wp), bool)
    hoch_k = hoch.copy()
    for x in range(Wp):                                              # Plateau am oberen Kartenrand bis zum Rand
        ys = np.nonzero(hoch[:, x])[0]
        if len(ys) and ys.min() <= 4 * T and not maske(cls, 'x')[0, x]:
            hoch_k[:ys.min(), x] = True
    wand = k4.hoehenkanten(a, hoch_k, 'sandstein', FRONT, 8, lippe, frei, 25, berg=False)
    for (x0, x1, ye) in lay['treppen']:
        k4.treppe(a, x0 * T, (x1 + 1) * T, (ye + 1) * T - 1, 's', FRONT, 'sandstein', sand)
    # Meer wie Karte 01: Flach/Tief nach der Vorlage
    flach = maske(cls, 'f')
    steg_f = maske(cls, 'p')
    tief = maske(cls, 'x')
    steg_roh = maske(cls, 'p')                                     # Stege stehen ueber dem Wasser
    wasser = weich((flach | tief | steg_roh).astype(np.float32), 4, 0.15, 6, 0.5) & ~hoch & ~wand
    land = ~wasser
    dl = abstand(land)                                              # Abstand zum Land
    df = abstand(land | (weich(flach.astype(np.float32), 6, 0.0, 9, 0.5) & wasser))   # Abstand zum Flachwasser
    yy, xx = np.mgrid[0:Hp, 0:Wp]
    welle = 3.0 * np.sin(xx / 23.0) + 2.0 * np.sin(xx / 9.0 + yy / 31.0)
    d = np.where(df <= 0.5, np.minimum(dl + welle, wd.STUFE1 - 6), wd.STUFE1 + df)
    meiden = maske(cls, 'pT')
    meiden = np.array(Image.fromarray((meiden * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(9))) > 0
    s_al = np.array(Image.open(os.path.join(OBJ, SCHIFF_DATEI)))[..., 3] > 0      # keine Felsen unter/am Schiff
    s_m = np.zeros((Hp, Wp), bool)
    sh_, sw_ = s_al.shape
    s_m[SCHIFF_POS[1]:SCHIFF_POS[1] + sh_, SCHIFF_POS[0]:SCHIFF_POS[0] + sw_] = s_al[:Hp - SCHIFF_POS[1], :Wp - SCHIFF_POS[0]]
    meiden |= np.array(Image.fromarray((s_m * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(25))) > 0
    wd.FELSEN_PROTOKOLL.clear()
    wd.FELSEN_AUSLASSEN = {(912, 952), (1024, 936), (1080, 902), (904, 1096)}   # 4 Felsspitzen in der Mitte weg (Nutzer)
    alt = wd.N_FRAMES
    wd.N_FRAMES = N_FRAMES
    img = wd.meer_terrassen(Image.fromarray(a), np.ones((Hp, Wp), bool), frame, meiden, maske=wasser, dist=d)
    wd.N_FRAMES = alt
    wd.FELSEN_AUSLASSEN = set()
    a = np.array(img.convert('RGB'))
    steg_m = stege(a, lay, wasser)
    schiff_m = schiff(a, wasser, frame)
    for tp in lay['teleporter']:
        k4.teleporter_zeichnen(a, tp['x'], tp['y'], tp['b'], tp['h'], frame)
    img = Image.fromarray(a).convert('RGBA')
    lvl = hp.astype(np.uint8) + 1
    lvl[steg_m] = 2
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain_basis.png'))
        np.save(os.path.join(KARTE, 'wasser.npy'), np.packbits(wasser & ~steg_m))
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
            ebenen[wasser & ~steg_m] = 7
            k4.objekte_zeichnen(img, objs, cache, ~(wasser & ~steg_m) & ~wand, frame, ebenen=ebenen)
            k4.animieren(img, objs, cache, frame or 0)
            k6.animieren_k6(img, objs, cache, frame or 0)
            kb.laternen_licht(img, [o for o in objs if o.get('anim') == 'laterne'], frame)
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain.png'))
    print('Karte 25 %dx%d gebaut' % (cols, rows))
    return img


if __name__ == '__main__':
    bauen()
