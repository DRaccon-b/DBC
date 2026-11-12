"""Karte 33 (The World of Dreams, A02): Gelaende.

Runde Traumplattform in der Sternenleere (Leere und Fundamentrand wie Karte 32): lavendelfarbene Platten, heller
Randstein, Rautenring und Mittelquadrat aus dunkleren Ringplatten, drei lila glimmende Runen auf dem Ring, Steg nach
Sueden mit Ankunftsfeldern (Pfeilfelder wie Karte 16). Schwebende Traumobjekte bewegen sich 1 px auf und ab.

  python3 tools/karte33_layout.py && python3 tools/karte33_kacheln.py && python3 tools/karte33_bauen.py
  python3 tools/karte33_objekte.py && python3 tools/karte33_bauen.py
"""
import json, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
import karte_bauen as kb
import karte04_bauen as k4
import karte08_bauen as k8
import karte16_bauen as k16
import karte32_bauen as k32

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte33')
BASIS = os.path.join(ROOT, 'assets', 'karte33', 'basis')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte33')
T = 16
N_FRAMES = 4                     # Regel: hoechstens 4 Animationsbilder
BILDDAUER = 250
k4.N_FRAMES = kb.N_FRAMES = k32.N_FRAMES = N_FRAMES
H = k4.H
gross = k32.gross


def textur(art, cols, rows):
    t = np.zeros((rows * T, cols * T, 3), np.uint8)
    ks = [np.array(Image.open(os.path.join(BASIS, '%s_%d.png' % (art, v))).convert('RGB')) for v in range(5)]
    for y in range(rows):
        for x in range(cols):
            t[y * T:(y + 1) * T, x * T:(x + 1) * T] = ks[kb.variante(x, y)]
    return t


def ring_kante(a, m):
    """Ringplatten liegen leicht vertieft: oben/links dunkle Kante, unten/rechts helle Kante (Licht oben links)."""
    oben = m & ~np.roll(m, 1, 0); links = m & ~np.roll(m, 1, 1)
    unten = m & ~np.roll(m, -1, 0); rechts = m & ~np.roll(m, -1, 1)
    a[oben | links] = (a[oben | links] * 0.7).astype(np.uint8)
    a[unten | rechts] = np.clip(a[unten | rechts].astype(int) + 26, 0, 255).astype(np.uint8)


def rune(a, tx, ty, frame):
    """Lila Rune: ovales Glyphenfeld mit innerem Kreis und Strahlen, glimmt im Takt (4 Bilder)."""
    f = 0.6 + 0.4 * math.sin(2 * math.pi * ((frame or 0) / N_FRAMES) + tx)
    cx, cy = tx * T + 8, ty * T + 8
    Hp, Wp = a.shape[:2]
    for y in range(cy - 12, cy + 13):
        for x in range(cx - 14, cx + 15):
            if not (0 <= y < Hp and 0 <= x < Wp):
                continue
            d = ((x - cx) / 7.0) ** 2 + ((y - cy) / 4.5) ** 2
            if d <= 1.0:
                c = np.array([70, 30, 120]) if d > 0.55 else np.array([120, 60, 200])
                if 0.25 < d < 0.4:
                    c = np.array([200, 150, 255])
                a[y, x] = np.clip(c * (0.75 + 0.35 * f), 0, 255).astype(np.uint8)
            elif d <= 2.6:                                           # weicher Schein auf den Platten
                t_ = (1 - (d - 1) / 1.6) * 0.35 * f
                a[y, x] = np.clip(a[y, x] * (1 - t_) + np.array([170, 110, 255]) * t_, 0, 255).astype(np.uint8)


def bauen(frame=None, speichern=True):
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cols, rows = lay['groesse']
    kl = np.array([list(r) for r in lay['klassen']])
    Wp, Hp = cols * T, rows * T
    leer = gross(kl == '.')
    land = ~leer
    a = k32.leere(Hp, Wp, frame)
    for art in 'irmp':
        m = gross(kl == art)
        a[m] = textur(art, cols, rows)[m]
    am = gross(kl == 'a')
    a[am] = textur('p', cols, rows)[am]
    ring_kante(a, gross(kl == 'm'))
    stegkante = gross(kl == 'p') | am                                 # Steg: dunkle Seitenkanten
    sk = stegkante & (~np.roll(stegkante, 1, 1) | ~np.roll(stegkante, -1, 1))
    a[sk] = (a[sk] * 0.62).astype(np.uint8)
    for (tx, ty) in lay.get('runen', []):
        rune(a, tx, ty, frame)
    fund = k32.fundament(a, land, leer, tiefe=12, seed=3333)
    for i, x in enumerate(range(20, 24)):                             # Ankunftsfelder (wie Karte 16)
        for y in (42, 43):
            k16.pfeil_marke(a, x, y, np.array([110, 220, 255], np.float32), frame, i + y)
    lvl = np.ones((Hp, Wp), np.uint8)
    lvl[leer] = 0
    lvl[fund] = 9
    if speichern and frame is None:
        np.save(os.path.join(KARTE, 'pixelhoehe.npy'), lvl)
    img = Image.fromarray(a).convert('RGBA')
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain_basis.png'))
    pf = os.path.join(OBJ, 'platzierung.json')
    if os.path.exists(pf):
        objs = sorted((o for o in json.load(open(pf)) if os.path.exists(os.path.join(OBJ, o['datei']))),
                      key=lambda o: o['y'] + o['fuss'])
        if frame is not None:
            for o in objs:
                if o.get('schwebend'):
                    o['y'] += (0, -1, -1, 0)[(frame + o.get('phase', 0)) % 4]
        cache = {o['datei']: Image.open(os.path.join(OBJ, o['datei'])).convert('RGBA') for o in objs}
        k8.schatten_ebene(img, [o for o in objs if not o.get('schwebend') and not o.get('kein_schatten')], cache, lvl)
        k4.objekte_zeichnen(img, objs, cache, np.zeros((Hp, Wp), bool), frame)
        k4.animieren(img, objs, cache, frame or 0, ruhig=frame is None)
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain.png'))
    print('Karte 33 %dx%d gebaut' % (cols, rows))
    return img


if __name__ == '__main__':
    bauen()
