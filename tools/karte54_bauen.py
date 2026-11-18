"""Karte 54 - D-Reaper Kernel (A03 Nr. 21, letzte Bossarena von A03), Gelaende nach maps/karte54/layout.json.

  python3 tools/karte54_layout.py && python3 tools/karte54_bauen.py

Neu aufgebaut (Nutzer): runde Arena wie Karte 33, schwebend in einem Meer aus pulsierenden D-Reaper-Blasen (Karte 52,
tools/dreaper.py, Originalgroesse). Dunkler violetter Metallplattenboden, massive Ringmauer (Abdeckung mit rosa Fugen, Wand
mit Schattenfuge, Fusskante, Bodenschatten), ein befallener Ring und ein Mittelfeld mit pulsierenden roten Adern, Fundament
unter den Suedkanten ueber dem Blasenmeer, Steg nach Sueden zum Teleporter. In den Ecken reisst die Masse auf: Risse mit
echten animierten Ausschnitten von Shinjuku (Karte 52/53, rot gluehende Risskante). Die Mitte bleibt frei (Boss).
"""
import json, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
import karte_bauen as kb
import karte04_bauen as k4
import karte32_bauen as k32
import karte33_bauen as k33
import dreaper

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte54')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte54')
T = 16
N_FRAMES = 4
BILDDAUER = 250
k4.N_FRAMES = kb.N_FRAMES = k32.N_FRAMES = k33.N_FRAMES = N_FRAMES
H = k4.H
k4.SCHATTEN = {'farbe': (18, 10, 22), 'dx': 0.3, 'dy': 0.15, 'kern': 100, 'wurf': (66, 52)}
gross = k32.gross
RISS_FARBEN = ((255, 236, 240), (255, 96, 128), (190, 40, 80), ((255, 224, 232), (255, 120, 150)))   # rot gluehend


def boden_textur(cols, rows):
    """Metallboden: 32er-Platten, feine Fugen, Rauschen, kleine Winkelmarken (wie bisher in Karte 54)."""
    Hh, W = rows * T, cols * T
    n = dreaper._rauschen(Hh, W, 3, 540) - 0.5
    boden = np.zeros((Hh, W, 3), np.float32) + np.array((52, 38, 56), np.float32)
    boden += n[..., None] * 8
    yy, xx = np.mgrid[0:Hh, 0:W]
    boden[(yy % 32 == 0) | (xx % 32 == 0)] = (42, 30, 46)
    boden[(yy % 32 == 1) | (xx % 32 == 1)] += 5
    boden = np.clip(boden, 0, 255).astype(np.uint8)
    rs = np.random.RandomState(54)
    for y in range(rows):
        for x in range(cols):
            if rs.rand() < 0.35:
                px, py = x * T + rs.randint(3, 11), y * T + rs.randint(3, 11)
                boden[py, px:px + 3] = (70, 54, 76)
                boden[py:py + 3, px] = (70, 54, 76)
    return boden


def befallen(a, m, frame):
    """Befallene Platten: dunkles Karmin ueber dem Metall, rote Adern im Rauschen, die im Takt pulsieren (4 Bilder)."""
    f = (frame or 0) % N_FRAMES
    Hh, W = m.shape
    a[m] = np.clip(a[m].astype(np.float32) * np.array((1.25, 0.55, 0.62)) + np.array((26, 0, 6)), 0, 255).astype(np.uint8)
    n = dreaper._rauschen(Hh, W, 10, 5454)
    ader = m & (np.abs(n - 0.5) < 0.035)
    puls = 0.5 + 0.5 * math.sin(2 * math.pi * f / N_FRAMES)
    a[ader] = np.clip(np.array((150, 30, 60)) + puls * np.array((90, 50, 50)), 0, 255).astype(np.uint8)
    kern = m & (np.abs(n - 0.5) < 0.012)
    a[kern] = np.clip(np.array((220, 80, 110)) + puls * np.array((35, 60, 60)), 0, 255).astype(np.uint8)


def mauern(a, m):
    """Ringmauer: Abdeckung (Kachel) mit Licht-/Schattenkante und rosa Fugen, Wand (8 px) unter Suedkanten, Bodenschatten,
    schmaler Schatten rechts neben senkrechten Mauern. -> gesperrte Pixelmaske."""
    Hh, W = a.shape[:2]
    sperre = m.copy()
    yy, xx = np.mgrid[0:Hh, 0:W]
    a[m] = (92, 60, 96)
    a[m & ((yy % T) == 7) & ((xx % T) >= 5) & ((xx % T) <= 10)] = (168, 92, 124)
    a[m & ((xx % T) == 7) & ((yy % T) >= 5) & ((yy % T) <= 10) & ~((yy % T) == 7)] = (150, 84, 116)
    p_ = np.pad(m, 1)
    oben = m & ~p_[:-2, 1:-1]
    links = m & ~p_[1:-1, :-2]
    rechts = m & ~p_[1:-1, 2:]
    unten = m & ~p_[2:, 1:-1]
    a[oben | links] = (126, 88, 128)
    a[rechts] = (64, 40, 68)
    for y in range(Hh):
        xs = np.nonzero(unten[y])[0]
        if not len(xs):
            continue
        for d in range(1, 9):
            yy_ = y + d
            if yy_ >= Hh:
                break
            ok = xs[~m[yy_, xs]]
            if d == 1:
                a[yy_, ok] = (34, 20, 38)
            elif d < 8:
                c = np.array((66, 42, 70), np.float32) * (1.0 - 0.04 * d)
                a[yy_, ok] = c
                a[yy_, ok[(ok % 8 == (0 if (d // 3) % 2 else 4))]] = (48, 30, 52)
                if d == 4:
                    a[yy_, ok] = (52, 32, 56)
            else:
                a[yy_, ok] = (28, 16, 32)
            sperre[yy_, ok] = True
        for d in range(9, 12):
            yy_ = y + d
            if yy_ < Hh:
                ok = xs[~m[yy_, xs] & ~sperre[yy_, xs]]
                a[yy_, ok] = (a[yy_, ok] * (0.62 + 0.1 * (d - 9))).astype(np.uint8)
    for d in range(1, 4):
        sh = np.zeros_like(m)
        sh[:, d:] = rechts[:, :-d]
        sh &= ~sperre
        a[sh] = (a[sh] * (0.6 + 0.1 * d)).astype(np.uint8)
    return sperre


def bauen(frame=None, speichern=True):
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cols, rows = lay['groesse']
    kl = np.array([list(r) for r in lay['klassen']])
    Wp, Hp = cols * T, rows * T
    leer = gross(kl == '.')
    land = ~leer
    a = np.zeros((Hp, Wp, 3), np.uint8)
    a[:] = (40, 6, 14)                                                # Tiefe zwischen den Blasen
    riss = k33.risse(a, lay, frame, land, farben=RISS_FARBEN)        # Risse nach Shinjuku (zuerst: Blasen liegen darueber)
    from PIL import ImageFilter
    riss_d = np.array(Image.fromarray((riss * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(5))) > 0
    dreaper.masse(a, leer & ~riss_d, frame, 54)                      # Blasenmeer: ganze Haufen rings um die Risse
    boden = boden_textur(cols, rows)
    a[land] = boden[land]
    bm = gross(kl == 'm')
    befallen(a, bm, frame)
    k33.ring_kante(a, bm)
    steg = gross(kl == 'p')
    sk = steg & (~np.roll(steg, 1, 1) | ~np.roll(steg, -1, 1))
    a[sk] = (a[sk] * 0.62).astype(np.uint8)
    fund = k32.fundament(a, land, leer, tiefe=12, seed=5454)          # Arena schwebt: Fundament ueber dem Blasenmeer
    sperre_m = mauern(a, gross(kl == 'w'))
    for tp in lay['teleporter']:
        k4.teleporter_zeichnen(a, tp['x'], tp['y'], tp['b'], tp['h'], frame)
    lvl = np.ones((Hp, Wp), np.uint8)
    lvl[leer] = 0                                                     # Blasenmeer: Leere (gesperrt)
    lvl[fund] = 9
    lvl[sperre_m] = 9
    for tp in lay['teleporter']:
        lvl[tp['y'] * T:(tp['y'] + tp['h']) * T, tp['x'] * T:(tp['x'] + tp['b']) * T] = 1
    if speichern and frame is None:
        np.save(os.path.join(KARTE, 'pixelhoehe.npy'), lvl)
        np.save(os.path.join(KARTE, 'leere.npy'), np.packbits(leer & ~fund))
        np.save(os.path.join(KARTE, 'wand.npy'), np.packbits(fund | sperre_m))
        np.save(os.path.join(KARTE, 'wasser.npy'), np.packbits(np.zeros((Hp, Wp), bool)))
        np.save(os.path.join(KARTE, 'treppe.npy'), np.packbits(np.zeros((Hp, Wp), bool)))
    img = Image.fromarray(a).convert('RGBA')
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain_basis.png'))
    pf = os.path.join(OBJ, 'platzierung.json')
    if os.path.exists(pf):
        objs = sorted((o for o in json.load(open(pf)) if os.path.exists(os.path.join(OBJ, o['datei']))),
                      key=lambda o: o.get('sortier', o['y'] + o['fuss']))
        if objs:
            cache = {o['datei']: Image.open(os.path.join(OBJ, o['datei'])).convert('RGBA') for o in objs}
            k4.objekte_zeichnen(img, objs, cache, land & ~(fund | sperre_m), frame, ebenen=lvl.astype(np.int16))
            k4.animieren(img, objs, cache, frame or 0)
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain.png'))
    print('Karte 54 %dx%d gebaut' % (cols, rows))
    return img


if __name__ == '__main__':
    bauen()
