"""Karte 43 - Haunted Castle Outskirts (A03 Nr. 10), Gelaende nach maps/karte43/layout.json.

Wiese aus den Graskacheln (assets/basis, Toene der Vorlage), breite Erdwege aus den Sandkacheln (erdig gefaerbt),
gepflasterter Burgvorplatz (Kies Karte 03, grau), Wald (Guertel und Bloecke) erhoeht auf dunklem Waldboden mit einer
niedrigen grauen Steinmauer an allen Suedkanten (in der Vorlage nur stueckweise) und schmalen Seitenkanten,
Teleporter an den Ausgaengen. Alle Bodenkanten am 16er-Raster mit 45-Grad-Schraegen (Regel 6b).

  python3 tools/karte43_layout.py && python3 tools/karte43_bauen.py
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
KARTE = os.path.join(ROOT, 'maps', 'karte43')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte43')
T = 16
N_FRAMES = 4
BILDDAUER = 250
k4.N_FRAMES = N_FRAMES
kb.N_FRAMES = N_FRAMES
H = k4.H
weich, zell_maske, flaeche = k4.weich, k4.zell_maske, k20.flaeche
k4.RASTER45 = True                       # Regel 6b: alle Bodenkanten am 16er-Raster mit 45 Grad
# niedrige Steinmauer der Waldbloecke (grauer Bruchstein wie in der Vorlage), Kante oben mit Waldboden
k4.FELS['mauer43'] = ['#2c2f38', '#3e434e', '#545a66', '#6a717e', '#828a96', '#9aa2ac', '#b6bcc4']
LIPPE = ['#1e3a1a', '#284a22', '#33592a', '#3e6a32', '#4a7a3a', '#588a44']   # Waldkante (dunkles Gras)
FRONT = 16
SEITE = 6                                # seitliche Plateaukanten nur schmal (Regel)


def faerben(lo, hi, a0=0.35, a1=0.5):
    def f(a):
        l = a.mean(axis=2, keepdims=True) / 255.0
        return np.array(lo, np.float32) + (np.array(hi, np.float32) - np.array(lo, np.float32)) * np.clip((l - a0) / a1, 0, 1)
    return f


def texturen(cols, rows):
    basis = os.path.join(ROOT, 'assets', 'basis')
    sand = os.path.join(basis, 'sand_%d.png')
    gras = os.path.join(basis, 'gras_%d.png')
    kies = os.path.join(ROOT, 'assets', 'karte03', 'basis', 'kies_%d.png')
    return {
        'g': flaeche(k6.kacheln(gras, 5, faerben((66, 118, 46), (116, 166, 78), 0.3, 0.5)), cols, rows),
        'w': flaeche(k6.kacheln(sand, 5, faerben((168, 138, 92), (218, 190, 136))), cols, rows),
        'k': flaeche(k6.kacheln(kies, 5, faerben((96, 100, 108), (168, 172, 178), 0.25, 0.6)), cols, rows),
        'h': flaeche(k6.kacheln(gras, 5, faerben((30, 70, 30), (64, 110, 50), 0.3, 0.5)), cols, rows),
    }


def bauen(frame=None, speichern=True):
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cls = lay['klassen']
    cols, rows = lay['groesse']
    Wp, Hp = cols * T, rows * T
    hp = np.kron(np.array([[int(c) for c in z] for z in lay['hoehe']]), np.ones((T, T), int))
    tex = texturen(cols, rows)
    a = tex['g'].copy()
    for art, blur, seed in (('w', 5.0, 3), ('k', 4.0, 5)):
        m = weich(zell_maske(cls, art + ('T' if art == 'w' else ''), cols, rows), blur, 0, seed)
        if art == 'w':                                               # Wegrand: leichter dunkler Saum im Gras
            saum = weich(zell_maske(cls, 'wT', cols, rows), blur, 0, seed, 0.36) & ~m
            a[saum] = (a[saum] * 0.9).astype(np.uint8)
        a[m] = tex[art][m]
    hoch = weich((hp >= 1).astype(np.float32), 5, 0.0, 7, 0.5)       # Wald erhoeht
    a[hoch] = tex['h'][hoch]
    frei = np.zeros((Hp, Wp), bool)
    wand = k4.hoehenkanten(a, hoch, 'mauer43', FRONT, SEITE, LIPPE, frei, 43, berg=False)
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
    print('Karte 43 %dx%d gebaut' % (cols, rows))
    return img


if __name__ == '__main__':
    bauen()
