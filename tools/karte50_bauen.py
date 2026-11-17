"""Karte 50 - Zhuqiaomon's Sanctuary (A03 Nr. 17), Gelaende nach maps/karte50/layout.json.

Heiligtum auf Terrassen (Nutzer: echte Terrassen, steigt nach Norden an): Felsboden, Pflasterwege und -plaetze, Wiesen,
drei Terrassenkanten mit Felsfront (45-Grad-Raster), Steintreppen unter den Torii als einziger Uebergang, abgesenkter Hof
oben links (Nutzer) mit Steinplattenboden und eingeschnittener Treppe von Sueden, erhoehter Felsrand ringsum (gesperrt).

  python3 tools/karte50_layout.py && python3 tools/karte50_bauen.py
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
KARTE = os.path.join(ROOT, 'maps', 'karte50')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte50')
T = 16
N_FRAMES = 4
BILDDAUER = 250
k4.N_FRAMES = N_FRAMES
kb.N_FRAMES = N_FRAMES
H = k4.H
weich, zell_maske, flaeche = k4.weich, k4.zell_maske, k20.flaeche
k4.SCHATTEN = {'farbe': (22, 28, 44), 'dx': 0.3, 'dy': 0.15, 'kern': 100, 'wurf': (66, 52)}
k4.RASTER45 = True
k4.FELS['berg47'] = ['#262b38', '#353d4e', '#465064', '#59657a', '#6e7b90', '#8693a8', '#a3afc2']   # graublauer Fels
LIPPE = ['#4e5868', '#5e6878', '#6e7888', '#7e8898', '#8e98a8', '#a0aab8']
FRONT = 24                               # Terrassen und Felsrand
SEITE = 6
faerben = k48.faerben


def texturen(cols, rows):
    basis = os.path.join(ROOT, 'assets', 'basis')
    sand = os.path.join(basis, 'sand_%d.png')
    gras = os.path.join(basis, 'gras_%d.png')
    kies = os.path.join(ROOT, 'assets', 'karte03', 'basis', 'kies_%d.png')
    return {
        'g': flaeche(k6.kacheln(sand, 5, faerben((96, 112, 132), (138, 152, 168), 0.3, 0.5)), cols, rows),   # Felsboden
        'w': flaeche(k6.kacheln(kies, 5, faerben((118, 124, 132), (172, 176, 182), 0.25, 0.6)), cols, rows),  # Pflaster
        'k': flaeche(k6.kacheln(kies, 5, faerben((96, 100, 104), (142, 146, 148), 0.25, 0.6)), cols, rows),   # dunkles Pflaster
        'n': flaeche(k6.kacheln(gras, 5, faerben((62, 112, 46), (108, 158, 72), 0.3, 0.5)), cols, rows),     # Wiese
        'h': flaeche(k6.kacheln(kies, 5, faerben((120, 134, 150), (172, 184, 198), 0.25, 0.6)), cols, rows),  # Felsrand (rau)
        'd': k48.platten(cols, rows, basis=(84, 92, 110), fuge=(52, 58, 72), seed=50),                       # Hofboden
    }


def bauen(frame=None, speichern=True):
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cls = lay['klassen']
    cols, rows = lay['groesse']
    Wp, Hp = cols * T, rows * T
    hp = np.kron(np.array([[int(c) for c in z] for z in lay['hoehe']]), np.ones((T, T), int))
    tex = texturen(cols, rows)
    a0 = tex['g'].copy()
    for art, sd in (('w', 3), ('k', 5), ('n', 7), ('d', 9), ('h', 11)):
        m = weich(zell_maske(cls, art + ('tT' if art == 'w' else ''), cols, rows), 5.0, 0, sd)
        if art in 'wkn':
            saum = weich(zell_maske(cls, art, cols, rows), 5.0, 0, sd, 0.36) & ~m
            a0[saum] = (a0[saum] * 0.93).astype(np.uint8)
        a0[m] = tex[art][m]
    a = a0.copy()
    frei = np.zeros((Hp, Wp), bool)
    for (x0, x1, ry, r_) in lay['treppen']:
        if r_ == 's':
            frei[ry * T - 4:ry * T + FRONT + 10, x0 * T:(x1 + 1) * T] = True
    wand = np.zeros((Hp, Wp), bool)
    for L in (1, 2, 3, 4):                                           # Terrassen von unten nach oben, je mit Front
        m = weich((hp >= L).astype(np.float32), 5, 0.0, 7 + L, 0.5)
        a[m] = a0[m]
        wand &= ~m
        wand |= k4.hoehenkanten(a, m, 'berg47', FRONT, SEITE, LIPPE, frei if L < 4 else np.zeros((Hp, Wp), bool), 50 + L,
                                berg=False)
    # Hohe Felswand: liegt das Gelaende vor einer Front mehr als eine Stufe tiefer, waechst die Wand je Stufe um FRONT
    hpx = hp.copy()
    for x in range(Wp):
        y = 1
        col = wand[:, x]
        while y < Hp:
            if col[y] and not col[y - 1]:
                y0 = y
                while y < Hp and col[y]:
                    y += 1
                if y < Hp and y0 > 0:
                    d = int(hpx[max(0, y0 - 2), x]) - int(hpx[min(Hp - 1, y + 2), x])
                    lauf = y - y0
                    if d >= 2 and FRONT - 6 <= lauf <= FRONT + 6:            # nur Fronten, keine Seitenwaende
                        for yy in range(y, min(Hp, y0 + lauf * d)):
                            a[yy, x] = a[y0 + (yy - y0) % lauf, x] if (yy - y0) % lauf > 2 else a[y0 + 4, x]
                            wand[yy, x] = True
                        ye = min(Hp - 1, y0 + lauf * d)
                        for k_, f_ in ((0, 0.7), (1, 0.85)):
                            if ye + k_ < Hp:
                                a[ye + k_, x] = (a[ye + k_, x] * f_).astype(np.uint8)
                        y = y0 + lauf * d
            y += 1
    if lay.get('rand') == 'flanke':                                   # eigener Bergzug: dunklere Felstextur auf dem Rand
        rm = weich(zell_maske(cls, 'h', cols, rows), 5.0, 0, 11) & ~wand
        a[rm] = (a[rm].astype(float) * np.array([0.78, 0.8, 0.86])).astype(np.uint8)
    treppe_m = np.zeros((Hp, Wp), bool)
    for (x0, x1, ry, r_) in lay['treppen']:
        if r_ == 's':
            k4.treppe(a, x0 * T, (x1 + 1) * T, ry * T - 1, 's', FRONT, 'berg47', tex['w'])
            treppe_m[ry * T:(ry + 1) * T + 8, x0 * T:(x1 + 1) * T] = True
        else:                                                        # Hof: Treppe fuehrt vom Suedrand in den Hof hinunter
            k4.treppe(a, x0 * T, (x1 + 1) * T, ry * T - 8, 'n', FRONT, 'berg47', tex['w'])
            treppe_m[ry * T - 10:(ry + 1) * T + 8, x0 * T:(x1 + 1) * T] = True
    for tp in lay['teleporter']:
        k4.teleporter_zeichnen(a, tp['x'], tp['y'], tp['b'], tp['h'], frame)
    img = Image.fromarray(a).convert('RGBA')
    lvl = (hp + 1).astype(np.uint8)
    lvl[wand] = 9
    lvl[treppe_m] = 2                                                # Treppen begehbar (eigene Ebene, Uebergang)
    xm = np.zeros((Hp, Wp), bool)
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain_basis.png'))
        np.save(os.path.join(KARTE, 'pixelhoehe.npy'), lvl)
        np.save(os.path.join(KARTE, 'wand.npy'), np.packbits(wand))
        np.save(os.path.join(KARTE, 'wasser.npy'), np.packbits(xm))
        np.save(os.path.join(KARTE, 'treppe.npy'), np.packbits(treppe_m))
    pf = os.path.join(OBJ, 'platzierung.json')
    if os.path.exists(pf):
        objs = sorted((o for o in json.load(open(pf)) if os.path.exists(os.path.join(OBJ, o['datei']))),
                      key=lambda o: o.get('sortier', o['y'] + o['fuss']))
        if objs:
            cache = {o['datei']: Image.open(os.path.join(OBJ, o['datei'])).convert('RGBA') for o in objs}
            ebenen = lvl.copy().astype(np.int16)
            k4.objekte_zeichnen(img, objs, cache, ~wand, frame, ebenen=ebenen)
            k4.animieren(img, objs, cache, frame or 0)
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain.png'))
    print('Karte 50 %dx%d gebaut' % (cols, rows))
    return img


if __name__ == '__main__':
    bauen()
