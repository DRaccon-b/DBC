"""Karte 42 - Digital World: Wind Valley (A03 Nr. 9), Gelaende nach maps/karte42/layout.json.

Talboden aus den Sandkacheln (assets/basis) in den zwei Toenen der Vorlage (heller Sand, Windbahnen), graue
Pflasterflecken (Kies Karte 03), zwei begehbare Hochplateaus (Hoehe 1, etwas heller) mit Steintreppen statt der
Holzgatter der Vorlage, Felsrand und Raute (Hoehe 2) - alle Suedkanten mit Felsfront (in der Vorlage fehlten sie),
schmale Seitenkanten (Karte 04 hoehenkanten), Teleporter an den Ausgaengen. Bodenkanten am 45-Grad-Raster (Regel 6b).

  python3 tools/karte42_layout.py && python3 tools/karte42_bauen.py
"""
import json, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
import karte_bauen as kb
import karte04_bauen as k4
import karte06_bauen as k6
import karte20_bauen as k20

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte42')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte42')
T = 16
N_FRAMES = 4
BILDDAUER = 250
k4.N_FRAMES = N_FRAMES
kb.N_FRAMES = N_FRAMES
H = k4.H
weich, zell_maske, flaeche = k4.weich, k4.zell_maske, k20.flaeche
k4.RASTER45 = True                       # Regel 6b: alle Bodenkanten am 16er-Raster mit 45 Grad
# Felsfront in den Toenen der Vorlage (rotbrauner Wuestenfels, Licht oben links)
k4.FELS['wueste'] = ['#3e2414', '#5c361e', '#7a4a2a', '#965e36', '#b07444', '#c88c56', '#e0a86c']
LIPPE = ['#8a5a32', '#a46c3c', '#bc8048', '#cf9256', '#dfa462', '#ecb874']   # Plateaukante (oranger Sand)
FRONT = 32
SEITE = 6                                # seitliche Plateaukanten nur schmal (Regel)


def faerben(lo, hi, a0=0.35, a1=0.5):
    def f(a):
        l = a.mean(axis=2, keepdims=True) / 255.0
        return np.array(lo, np.float32) + (np.array(hi, np.float32) - np.array(lo, np.float32)) * np.clip((l - a0) / a1, 0, 1)
    return f


def texturen(cols, rows):
    basis = os.path.join(ROOT, 'assets', 'basis')
    sand = os.path.join(basis, 'sand_%d.png')
    kies = os.path.join(ROOT, 'assets', 'karte03', 'basis', 'kies_%d.png')
    t = {
        's': flaeche(k6.kacheln(sand, 5, faerben((206, 184, 128), (242, 224, 168))), cols, rows),
        'b': flaeche(k6.kacheln(sand, 5, faerben((176, 148, 98), (214, 188, 134))), cols, rows),
        'd': flaeche(k6.kacheln(kies, 5, faerben((150, 120, 80), (198, 168, 118), 0.25, 0.6)), cols, rows),
        'k': flaeche(k6.kacheln(kies, 5, faerben((118, 112, 96), (178, 172, 150), 0.25, 0.6)), cols, rows),
        'n': flaeche(k6.kacheln(os.path.join(basis, 'gras_%d.png'), 5, faerben((62, 112, 46), (112, 156, 74), 0.3, 0.5)), cols, rows),
        'r': flaeche(k6.kacheln(kies, 5, faerben((176, 118, 70), (226, 166, 108), 0.25, 0.6)), cols, rows),   # Felsrand (hoch)
        'p': flaeche(k6.kacheln(sand, 5, faerben((206, 160, 104), (242, 200, 140))), cols, rows),   # Hochplateau
    }
    return t


def bauen(frame=None, speichern=True):
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cls = lay['klassen']
    cols, rows = lay['groesse']
    Wp, Hp = cols * T, rows * T
    hp = np.kron(np.array([[int(c) for c in z] for z in lay['hoehe']]), np.ones((T, T), int))
    tex = texturen(cols, rows)
    a = tex['s'].copy()
    for art, blur, seed in (('b', 5.0, 3), ('k', 4.0, 5)):
        m = weich(zell_maske(cls, art + ('Tt' if art == 'b' else ''), cols, rows), blur, 0, seed)
        if art == 'b':                                               # Windbahnen: leichter dunkler Saum
            saum = weich(zell_maske(cls, 'bTt', cols, rows), blur, 0, seed, 0.36) & ~m
            a[saum] = (a[saum] * 0.95).astype(np.uint8)
        a[m] = tex[art][m]
    # ---------------- Hoehen: Hochplateaus (1, begehbar) und Felsrand/Raute (2); alle Suedkanten mit Felsfront
    h1m = weich((hp >= 1).astype(np.float32), 5, 0.0, 7, 0.5)
    hoch2 = weich((hp >= 2).astype(np.float32), 5, 0.0, 9, 0.5)
    a[h1m] = tex['p'][h1m]
    qm = weich(zell_maske(cls, 'qt', cols, rows), 4.0, 0, 11) & h1m   # Weg auf dem Plateau vor der Treppe
    a[qm] = tex['b'][qm]
    a[hoch2] = tex['r'][hoch2]
    frei = np.zeros((Hp, Wp), bool)
    for (x0, x1, ry) in lay['treppen']:                              # Treppen schneiden die Front
        frei[ry * T - 4:ry * T + FRONT + 10, x0 * T:(x1 + 1) * T] = True
    wand = k4.hoehenkanten(a, h1m, 'wueste', FRONT, SEITE, LIPPE, frei, 42, berg=False)
    wand |= k4.hoehenkanten(a, hoch2, 'wueste', FRONT, SEITE, LIPPE, np.zeros_like(frei), 43, berg=False)
    for (x0, x1, ry) in lay['treppen']:                              # Steintreppe frontal, volle Breite
        k4.treppe(a, x0 * T, (x1 + 1) * T, ry * T - 1, 's', FRONT, 'wueste', tex['b'])
    xm = np.zeros((Hp, Wp), bool)                                    # kein Wasser auf dieser Karte
    for tp in lay['teleporter']:
        k4.teleporter_zeichnen(a, tp['x'], tp['y'], tp['b'], tp['h'], frame)
    img = Image.fromarray(a).convert('RGBA')
    lvl = hp.astype(np.uint8) + 1
    lvl[wand] = 9                                                    # Felsfront = Wand (Kollision, Schatten)
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain_basis.png'))
        np.save(os.path.join(KARTE, 'pixelhoehe.npy'), lvl)
        np.save(os.path.join(KARTE, 'wand.npy'), np.packbits(wand))
        np.save(os.path.join(KARTE, 'wasser.npy'), np.packbits(xm))
        np.save(os.path.join(KARTE, 'treppe.npy'), np.packbits(np.kron(np.array([[c == 't' for c in z] for z in cls]),
                                                                       np.ones((T, T), bool))))
    pf = os.path.join(OBJ, 'platzierung.json')
    if os.path.exists(pf):
        objs = sorted((o for o in json.load(open(pf)) if os.path.exists(os.path.join(OBJ, o['datei']))),
                      key=lambda o: o.get('sortier', o['y'] + o['fuss']))
        if objs:
            cache = {o['datei']: Image.open(os.path.join(OBJ, o['datei'])).convert('RGBA') for o in objs}
            ebenen = lvl.copy().astype(np.int16)
            ebenen[wand] = 9
            ebenen[xm] = 7
            k4.objekte_zeichnen(img, objs, cache, ~xm & ~wand, frame, ebenen=ebenen)
            k4.animieren(img, objs, cache, frame or 0)
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain.png'))
    print('Karte 42 %dx%d gebaut' % (cols, rows))
    return img


if __name__ == '__main__':
    bauen()
