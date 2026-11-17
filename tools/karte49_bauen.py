"""Karte 49 - The Broken Promise (A03 Nr. 16), Bossarena von Beelzemon, Gelaende nach maps/karte49/layout.json.

Graublauer Felsboden (wie Karte 47) mit Pflasterflecken, erhoehter heller Felsrand ringsum (gesperrt, eigene Ebene)
mit Felsfronten nach Sueden und schmalen Seitenkanten, erhoehtes Plateau als Buehne des Bosses (Steinplatten, eigene
Front, Steintreppe in voller Breite), Teleporter-Ausgang durch den unteren Rand. Bodenkanten am 45-Grad-Raster.

  python3 tools/karte49_layout.py && python3 tools/karte49_bauen.py
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
KARTE = os.path.join(ROOT, 'maps', 'karte49')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte49')
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
FRONT = 24                               # Felsrand
FRONT_P = 16                             # Plateau (Buehne)
SEITE = 6
faerben = k48.faerben


def texturen(cols, rows):
    basis = os.path.join(ROOT, 'assets', 'basis')
    sand = os.path.join(basis, 'sand_%d.png')
    kies = os.path.join(ROOT, 'assets', 'karte03', 'basis', 'kies_%d.png')
    return {
        'g': flaeche(k6.kacheln(sand, 5, faerben((84, 100, 122), (124, 140, 160), 0.3, 0.5)), cols, rows),   # Felsboden
        'w': flaeche(k6.kacheln(kies, 5, faerben((112, 118, 122), (164, 168, 168), 0.25, 0.6)), cols, rows),  # Pflaster
        'h': flaeche(k6.kacheln(kies, 5, faerben((120, 134, 150), (172, 184, 198), 0.25, 0.6)), cols, rows),  # Felsrand (rau)
        'q': k48.platten(cols, rows, basis=(132, 140, 156), fuge=(84, 90, 106), seed=49),                     # Buehne
    }


def bauen(frame=None, speichern=True):
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cls = lay['klassen']
    cols, rows = lay['groesse']
    Wp, Hp = cols * T, rows * T
    tex = texturen(cols, rows)
    a = tex['g'].copy()
    m = weich(zell_maske(cls, 'w', cols, rows), 5.0, 0, 3)
    saum = weich(zell_maske(cls, 'w', cols, rows), 5.0, 0, 3, 0.36) & ~m
    a[saum] = (a[saum] * 0.92).astype(np.uint8)
    a[m] = tex['w'][m]
    # Plateau (Buehne, begehbar) und Felsrand (gesperrt) - beide erhoeht, je eigene Front
    pl = weich(zell_maske(cls, 'q', cols, rows), 5, 0.0, 7, 0.5)
    rand = weich(zell_maske(cls, 'h', cols, rows), 5, 0.0, 9, 0.5)
    a[pl] = tex['q'][pl]
    a[rand] = tex['h'][rand]
    frei = np.zeros((Hp, Wp), bool)
    for (x0, x1, ry) in lay['treppen']:
        frei[ry * T - 4:ry * T + FRONT_P + 10, x0 * T:(x1 + 1) * T] = True
    wand = k4.hoehenkanten(a, rand, 'berg47', FRONT, SEITE, LIPPE, np.zeros((Hp, Wp), bool), 49, berg=False)
    wand |= k4.hoehenkanten(a, pl, 'berg47', FRONT_P, SEITE, LIPPE, frei, 50, berg=False)
    for (x0, x1, ry) in lay['treppen']:
        k4.treppe(a, x0 * T, (x1 + 1) * T, ry * T - 1, 's', FRONT_P, 'berg47', tex['q'])
    for tp in lay['teleporter']:
        k4.teleporter_zeichnen(a, tp['x'], tp['y'], tp['b'], tp['h'], frame)
    img = Image.fromarray(a).convert('RGBA')
    lvl = np.ones((Hp, Wp), np.uint8)
    lvl[pl] = 2
    lvl[rand] = 3                                                    # Felsrand: eigene Ebene (gesperrt)
    lvl[wand] = 9
    treppe_m = np.zeros((Hp, Wp), bool)
    for (x0, x1, ry) in lay['treppen']:
        lvl[ry * T:(ry + 1) * T + 8, x0 * T:(x1 + 1) * T] = 2
        treppe_m[ry * T:(ry + 1) * T + 8, x0 * T:(x1 + 1) * T] = True
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
    print('Karte 49 %dx%d gebaut' % (cols, rows))
    return img


if __name__ == '__main__':
    bauen()
