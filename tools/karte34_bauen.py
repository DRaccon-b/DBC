"""Karte 34 - Shinjuku Central Park (A03 Nr. 1), Gelaende (Grundgeruest aus Karte 21, tools/neue_karte.py).

Bausteine: Rasen/Sand aus Karte 01 (assets/basis), Waldboden dunkler, Sandwege und Spielplatzsand mit 45-Grad-Kanten
(Regel 6b), graues Pflaster (Kiesel von Karte 03 grau, wie Karte 21) mit Bordkante, Teich im vertieften Wasserstil
(wie Karte 20/23) mit Erdufer, Holzsteg (Bruecke von Karte 20) in den Teich, Teleporter an den drei Ausgaengen.

  python3 tools/karte34_layout.py && python3 tools/karte34_bauen.py && python3 tools/karte34_objekte.py && python3 tools/karte34_bauen.py
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
import karte_bauen as kb
import karte04_bauen as k4
import karte06_bauen as k6
import karte20_bauen as k20
import karte21_bauen as k21
import bauwerke

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte34')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte34')
T = 16
N_FRAMES = 4                     # Regel: hoechstens 4 Animationsbilder
BILDDAUER = 250
k4.N_FRAMES = N_FRAMES
kb.N_FRAMES = N_FRAMES
H = k4.H
weich, zell_maske, flaeche = k4.weich, k4.zell_maske, k20.flaeche
k4.RASTER45 = True                       # Regel 6b: alle Bodenkanten am 16er-Raster mit 45 Grad


def bauen(frame=None, speichern=True):
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cls = lay['klassen']
    cols, rows = lay['groesse']
    Wp, Hp = cols * T, rows * T
    basis = os.path.join(ROOT, 'assets', 'basis')
    gras = flaeche(k6.kacheln(os.path.join(basis, 'gras_%d.png'), 5), cols, rows)
    sand = flaeche(k6.kacheln(os.path.join(basis, 'sand_%d.png'), 5), cols, rows)
    hell = np.clip(sand.astype(np.int16) * 1.06 + 6, 0, 255).astype(np.uint8)          # Spielplatzsand heller
    erde = flaeche(k6.kacheln(os.path.join(basis, 'sand_%d.png'), 5, k20.braun if hasattr(k20, 'braun') else None),
                   cols, rows) if False else (sand.astype(np.float32) * np.array([0.66, 0.54, 0.42])).astype(np.uint8)
    a = gras.copy()
    # Waldboden (unter Waldrand und Hecken)
    wm = weich(zell_maske(cls, 'h', cols, rows), 5.0, 0, 3)
    a[wm] = (gras[wm] * np.array([0.62, 0.7, 0.66])).astype(np.uint8)
    # Sandwege inkl. Ausgaenge und Weg unter dem Steg; Spielplatz heller
    roh = zell_maske(cls, 'web', cols, rows)
    m = weich(roh, 5.0, 0, 4)
    a[m] = sand[m]
    saum = weich(roh, 5.0, 0, 4, 0.28) & ~m
    a[saum] = (a[saum] * 0.9).astype(np.uint8)
    sm = weich(zell_maske(cls, 's', cols, rows), 5.0, 0, 4)
    a[sm] = hell[sm]
    a[weich(zell_maske(cls, 's', cols, rows), 5.0, 0, 4, 0.28) & ~sm & ~m] = (a[weich(zell_maske(cls, 's', cols, rows), 5.0, 0, 4, 0.28) & ~sm & ~m] * 0.9).astype(np.uint8)
    # Pflaster (grau, Bordkante, Kontaktschatten)
    import karte18_bauen as k18                                      # helle Gehwegplatten (Stadt, wie Karte 30/31)
    kies = k18.textur('g', cols, rows)
    pm = weich(zell_maske(cls, 'p', cols, rows), 5.0, 0, 6)
    a[pm] = kies[pm]
    a[k21.kante_rund(pm)] = H('#5a6270')
    k21.kontaktschatten(a, pm, 2, 0.82)
    # Teich: Erdufer (Klasse m und Wasser) + vertieftes Wasser
    import wasser_vertieft
    um = weich(zell_maske(cls, 'mx', cols, rows), 5.0, 0, 7)
    a[um] = erde[um]
    xm = weich(zell_maske(cls, 'xb', cols, rows), 5.0, 0, 8)       # Wasser laeuft unter dem Steg weiter
    a = np.array(wasser_vertieft.vertiefen(Image.fromarray(a), np.ones_like(xm), frame, maske=xm,
                                                 meiden=np.ones_like(xm)).convert('RGB'))   # Stadtteich: keine Felsnadeln
    img = Image.fromarray(a).convert('RGBA')
    sx0, sy0, sx1, sy1 = lay['steg']                                   # Holzsteg (Laufrichtung West-Ost)
    bauwerke.zeichne_bruecke(img, sx0 * T - 6, (sx1 + 1) * T, sy0 * T + 4, (sy1 + 1) * T - 4, frame or 0, seed=34)
    a = np.array(img.convert('RGB'))
    for tp in lay.get('teleporter', []):
        k4.teleporter_zeichnen(a, tp['x'], tp['y'], tp['b'], tp['h'], frame)
    img = Image.fromarray(a).convert('RGBA')
    lvl = np.ones((Hp, Wp), np.uint8)
    steg = np.zeros((Hp, Wp), bool)
    steg[sy0 * T + 4:(sy1 + 1) * T - 4, sx0 * T - 6:(sx1 + 1) * T] = True
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain_basis.png'))
        np.save(os.path.join(KARTE, 'wasser.npy'), np.packbits(xm & ~steg))
        np.save(os.path.join(KARTE, 'pixelhoehe.npy'), lvl)
    pf = os.path.join(OBJ, 'platzierung.json')
    if os.path.exists(pf):
        objs = sorted((o for o in json.load(open(pf)) if os.path.exists(os.path.join(OBJ, o['datei']))),
                      key=lambda o: o.get('sortier', o['y'] + o['fuss']))
        if objs:
            cache = {o['datei']: Image.open(os.path.join(OBJ, o['datei'])).convert('RGBA') for o in objs}
            ebenen = lvl.copy().astype(np.int16)
            ebenen[xm & ~steg] = 7
            k4.objekte_zeichnen(img, objs, cache, ~xm | steg, frame, ebenen=ebenen)
            k4.animieren(img, objs, cache, frame or 0)
            k6.animieren_k6(img, objs, cache, frame or 0)
            kb.laternen_licht(img, [o for o in objs if o.get('anim') == 'laterne'], frame)
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain.png'))
    print('Karte 34 %dx%d gebaut' % (cols, rows))
    return img


if __name__ == '__main__':
    bauen()
