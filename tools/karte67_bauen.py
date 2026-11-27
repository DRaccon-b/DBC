"""Karte 67 - Colosseum (A01 Nr. 4), Gelaende nach maps/karte67/layout.json.

Roemisches Steinkolosseum (Nutzer): Sandarena in der Mitte, drei begehbare Tribuenenringe aus Travertin mit
umlaufenden Sitzstufen (nach aussen ansteigend, Fronten mit Sitzreihen nach Sueden sichtbar), Treppen auf der
Nord-Sued-Achse, aeussere Fassade mit dreigeschossiger Arkade (Bogenreihen) an der Suedseite, Torgaenge im Westen und
Osten, gepflasterter Platz aussen, Wiese mit Baumguertel, Teleporter im Sueden.

  python3 tools/karte67_layout.py && python3 tools/karte67_bauen.py && python3 tools/karte67_objekte.py && python3 tools/karte67_bauen.py
"""
import json, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
import karte_bauen as kb
import karte04_bauen as k4
import karte06_bauen as k6
import karte20_bauen as k20
import karte48_bauen as k48

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte67')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte67')
T = 16
N_FRAMES = 4
BILDDAUER = 250
k4.N_FRAMES = kb.N_FRAMES = N_FRAMES
H = k4.H
weich, zell_maske, flaeche = k4.weich, k4.zell_maske, k20.flaeche
k4.SCHATTEN = {'farbe': (60, 48, 36), 'dx': 0.3, 'dy': 0.15, 'kern': 100, 'wurf': (66, 52)}
k4.RASTER45 = True
k4.FELS['travertin'] = ['#3e3328', '#574837', '#715f4a', '#8c7a60', '#a89678', '#c3b294', '#ddcdb0']
LIPPE = ['#8a7c66', '#9a8c74', '#ab9d84', '#bcae94', '#cdbfa5', '#ddd0b6']
FRONT = 24
SEITE = 6
ARKADE = 64                              # Hoehe der Suedfassade (Arkaden, 2 Geschosse + Gesims)
faerben = k48.faerben


def texturen(cols, rows):
    basis = os.path.join(ROOT, 'assets', 'basis')
    sand = os.path.join(basis, 'sand_%d.png')
    gras = os.path.join(basis, 'gras_%d.png')
    kies = os.path.join(ROOT, 'assets', 'karte03', 'basis', 'kies_%d.png')
    return {
        'a': flaeche(k6.kacheln(sand, 5, faerben((176, 146, 100), (226, 200, 150), 0.3, 0.5)), cols, rows),   # Arenasand
        'n': flaeche(k6.kacheln(gras, 5), cols, rows),
        'stein': flaeche(k6.kacheln(kies, 5, faerben((150, 138, 116), (214, 204, 182), 0.25, 0.6)), cols, rows),
        'z': k48.platten(cols, rows, basis=(196, 186, 164), fuge=(138, 128, 108), seed=67),                  # Platz
        'g': k48.platten(cols, rows, basis=(150, 140, 120), fuge=(100, 92, 78), seed=68),                    # Torgang
        'f': k48.platten(cols, rows, basis=(170, 158, 134), fuge=(118, 108, 90), hoehe=8, seed=69),          # Mauerkrone
    }


def radius_px(lay, Hp, Wp):
    cx, cy = lay['mitte'][0] * T, lay['mitte'][1] * T
    A, B = lay['achsen'][0] * T, lay['achsen'][1] * T
    fx, fy = lay['flach'][0] * T, lay['flach'][1] * T
    yy, xx = np.mgrid[0:Hp, 0:Wp].astype(np.float32)
    dx = np.maximum(0, np.abs(xx + 0.5 - cx) - fx)
    dy = np.maximum(0, np.abs(yy + 0.5 - cy) - fy)
    return np.sqrt((dx / A) ** 2 + (dy / B) ** 2), B


def sitzstufen(a, maske, r, B, stein):
    """Tribuene: umlaufende Sitzstufen (je 8 px tief, entlang der Ellipse): helle Sitzflaeche, dunkle Fuge zur naechsten
    Stufe, leichte Lichtkante. Stein aus den Kieseltexturen (Travertin)."""
    s = r * B                                                         # Abstand in px (y-Massstab)
    band = np.mod(s, 8.0)
    af = stein.astype(np.float32)
    af[band < 1.2] *= 0.62                                            # Fuge (Schatten der hoeheren Stufe)
    af[(band >= 1.2) & (band < 2.4)] *= 1.12                          # Lichtkante der Sitzflaeche
    a[maske] = np.clip(af, 0, 255).astype(np.uint8)[maske]


def arkade(a, wand, lay, hp, r, B):
    """Suedfassade: an der Suedkante der Fassade (Ebene 4 -> Platz) eine Arkadenwand ARKADE px hoch - Gesims, zwei
    Geschosse mit Rundboegen zwischen Pfeilern (Bogenoeffnung dunkel, Pfeiler hell, Licht von oben links)."""
    Hp, Wp = hp.shape
    F = [np.array(H(c), np.float32) for c in k4.FELS['travertin']]
    fass = hp == 4
    cy = lay['mitte'][1] * T
    for x in range(Wp):
        col = fass[:, x]
        ys = np.nonzero(col[cy:])[0]
        if not len(ys):
            continue
        ye = cy + ys.max()                                            # letzte Fassadenzeile nach Sueden
        if ye + 1 >= Hp or hp[ye + 1, x] != 0:
            continue
        for k in range(ARKADE):
            y = ye + 1 + k
            if y >= Hp:
                break
            geschoss, iy = divmod(k, 30)
            if k >= 60:                                               # Sockel
                c = F[2] if k < ARKADE - 1 else F[1]
            elif iy < 4:                                              # Gesims
                c = F[6] if iy == 0 else (F[5] if iy == 1 else F[3])
            else:
                bx = (x + 8) % 20                                     # Bogenraster 20 px
                ih = iy - 4                                           # 0..25
                in_bogen = 4 <= bx <= 15
                if in_bogen:
                    ox = bx - 9.5
                    top = 4 + (ox * ox) / 6.0                          # Rundbogen
                    if ih >= top:
                        c = F[0] if ih > top + 2 else F[1]            # Oeffnung dunkel, Bogenkante
                        if bx == 4 or bx == 15:
                            c = F[2]
                    else:
                        c = F[5] if bx < 9 else F[4]
                else:
                    c = F[5] if bx < 4 else F[3]                      # Pfeiler, Licht von links
                    if bx in (16, 17, 18, 19):
                        c = F[4]
            a[y, x] = c.astype(np.uint8)
            wand[y, x] = True
        for d, f_ in ((0, 0.7), (1, 0.85)):                           # Kontaktschatten am Fuss
            y = ye + 1 + ARKADE + d
            if y < Hp and not wand[y, x]:
                a[y, x] = (a[y, x] * f_).astype(np.uint8)


def bauen(frame=None, speichern=True):
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cls = lay['klassen']
    cols, rows = lay['groesse']
    Wp, Hp = cols * T, rows * T
    hpk = np.array([[int(c) for c in z] for z in lay['hoehe']])
    hp = np.kron(hpk, np.ones((T, T), int))
    tex = texturen(cols, rows)
    r, B = radius_px(lay, Hp, Wp)
    gr = lay['grenzen']
    # Hoehen pixelgenau aus der Ellipse (glatte Ringe), Torgaenge und Rand aus dem Raster
    hp_px = np.zeros((Hp, Wp), int)
    for i in range(4, -1, -1):
        hp_px[r < gr[i]] = i
    gk = np.kron(np.array([[c == 'g' for c in z] for z in cls]), np.ones((T, T), bool))
    hp_px[gk] = 0
    a0 = tex['z'].copy()
    nm = weich(zell_maske(cls, 'n', cols, rows), 5.0, 0, 3)
    a0[nm] = tex['n'][nm]
    a0[hp_px == 0] = np.where(nm[hp_px == 0][:, None], a0[hp_px == 0], a0[hp_px == 0])
    arena = (r < gr[0]) & ~gk
    a0[arena] = tex['a'][arena]
    ring = (hp_px >= 1) & (hp_px <= 3)
    sitzstufen(a0, ring, r, B, tex['stein'])
    a0[hp_px == 4] = tex['f'][hp_px == 4]
    a0[gk] = tex['g'][gk]
    a = a0.copy()
    frei = np.zeros((Hp, Wp), bool)
    for (x0, x1, ry, ri) in lay['treppen']:
        if ri == 's':
            frei[ry * T - 4:ry * T + FRONT + 10, x0 * T:(x1 + 1) * T] = True
    wand = np.zeros((Hp, Wp), bool)
    for L in (1, 2, 3, 4):                                            # Ringe und Fassade, je mit Front nach Sueden
        m = hp_px >= L
        a[m] = a0[m]
        wand &= ~m
        wand |= k4.hoehenkanten(a, m, 'travertin', FRONT, SEITE, LIPPE, frei, 60 + L, berg=False)
    arkade(a, wand, lay, hp_px, r, B)
    treppe_m = np.zeros((Hp, Wp), bool)
    for (x0, x1, ry, ri) in lay['treppen']:
        if ri == 's':
            k4.treppe(a, x0 * T, (x1 + 1) * T, ry * T - 1, 's', FRONT, 'travertin', tex['stein'])
            treppe_m[ry * T:(ry + 1) * T + 8, x0 * T:(x1 + 1) * T] = True
        else:
            k4.treppe(a, x0 * T, (x1 + 1) * T, (ry + 1) * T + 1, 'n', FRONT, 'travertin', tex['stein'])
            treppe_m[(ry + 1) * T:(ry + 2) * T + 8, x0 * T:(x1 + 1) * T] = True
    for tp in lay['teleporter']:
        k4.teleporter_zeichnen(a, tp['x'], tp['y'], tp['b'], tp['h'], frame)
    img = Image.fromarray(a).convert('RGBA')
    lvl = (hp_px + 1).astype(np.uint8)
    lvl[hp_px == 4] = 9                                               # Fassade (Mauerkrone) gesperrt
    lvl[wand] = 9
    lvl[treppe_m] = 2
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain_basis.png'))
        gesperrt = lvl.copy()
        nk = np.kron(np.array([[c == 'n' for c in z] for z in cls]), np.ones((T, T), bool))
        gesperrt[nk] = 9                                              # Baumguertel nicht begehbar
        np.save(os.path.join(KARTE, 'pixelhoehe.npy'), gesperrt)
        np.save(os.path.join(KARTE, 'wand.npy'), np.packbits(wand))
        np.save(os.path.join(KARTE, 'wasser.npy'), np.packbits(np.zeros((Hp, Wp), bool)))
        np.save(os.path.join(KARTE, 'treppe.npy'), np.packbits(treppe_m))
    pf = os.path.join(OBJ, 'platzierung.json')
    if os.path.exists(pf):
        objs = sorted((o for o in json.load(open(pf)) if os.path.exists(os.path.join(OBJ, o['datei']))),
                      key=lambda o: o.get('sortier', o['y'] + o['fuss']))
        if objs:
            cache = {o['datei']: Image.open(os.path.join(OBJ, o['datei'])).convert('RGBA') for o in objs}
            k4.objekte_zeichnen(img, objs, cache, ~wand, frame, ebenen=lvl.copy().astype(np.int16))
            k4.animieren(img, objs, cache, frame or 0)
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain.png'))
    print('Karte 67 %dx%d gebaut' % (cols, rows))
    return img


if __name__ == '__main__':
    bauen()
