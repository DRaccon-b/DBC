"""Karte 41 - Digital World: Wind Desert (A03 Nr. 8), Gelaende nach maps/karte41/layout.json.

Wuestenboden aus den Sandkacheln (assets/basis) in drei Toenen der Vorlage (heller Sand, Windbahnen, dunkle Erde mit
Kieseln aus Karte 03), graue Pflasterflecken (Kies Karte 03, entsaettigt), Oase mit Gras (Karte 01) und vertieftem Teich
(Sandsteinufer wie Karte 23), erhoehte orange Plateaus mit Felsfront nach Sueden und schmalen Seitenkanten (Karte 04
hoehenkanten), Teleporter an den Ausgaengen. Alle Bodenkanten am 16er-Raster mit 45-Grad-Schraegen (Regel 6b).

  python3 tools/karte41_layout.py && python3 tools/karte41_bauen.py
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
KARTE = os.path.join(ROOT, 'maps', 'karte41')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte41')
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
        'r': flaeche(k6.kacheln(sand, 5, faerben((200, 148, 90), (238, 190, 128))), cols, rows),
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
    for art, blur, seed in (('b', 5.0, 3), ('d', 5.0, 4), ('k', 4.0, 5), ('n', 4.0, 6)):
        m = weich(zell_maske(cls, art + ('xT' if art == 'n' else ''), cols, rows), blur, 0, seed)
        if art == 'b':                                               # Windbahnen: leichter dunkler Saum
            saum = weich(zell_maske(cls, 'b', cols, rows), blur, 0, seed, 0.36) & ~m
            a[saum] = (a[saum] * 0.95).astype(np.uint8)
        a[m] = tex[art][m]
    tm = weich(zell_maske(cls, 'T', cols, rows), 4.0, 0, 7)
    a[tm] = tex['b'][tm]
    # ---------------- Plateaus
    hoch = weich((hp >= 2).astype(np.float32), 5, 0.0, 7, 0.5)
    a[hoch] = tex['r'][hoch]
    frei = np.zeros((Hp, Wp), bool)
    wand = k4.hoehenkanten(a, hoch, 'wueste', FRONT, SEITE, LIPPE, frei, 41, berg=False)
    # ---------------- Teich der Oase (vertieft, Sandsteinufer)
    import wasser_vertieft
    x_t = np.array([[ch == 'x' for ch in z] for z in cls])
    xm = weich(np.kron(x_t, np.ones((T, T))).astype(np.float32), 4, 0.15, 8, 0.45) & ~wand & (hp == 0)
    alt = wasser_vertieft.MAUER
    wasser_vertieft.MAUER = [H(c) for c in ('#5a4632', '#76603f', '#927a52', '#ac9468', '#c6ae82', '#dcc8a0')]
    try:
        img = wasser_vertieft.vertiefen(Image.fromarray(a), np.ones((Hp, Wp), bool), frame, maske=xm,
                                        rand=('#6e5236', '#8e6c48', '#ae8a60', '#c8a87a'), stufen=[(16, 0.72, 8)])
    finally:
        wasser_vertieft.MAUER = alt
    a = np.array(img.convert('RGB'))
    for tp in lay['teleporter']:
        k4.teleporter_zeichnen(a, tp['x'], tp['y'], tp['b'], tp['h'], frame)
    img = Image.fromarray(a).convert('RGBA')
    lvl = hp.astype(np.uint8) + 1
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
    print('Karte 41 %dx%d gebaut' % (cols, rows))
    return img


if __name__ == '__main__':
    bauen()
