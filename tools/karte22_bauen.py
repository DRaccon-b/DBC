"""Karte 22 - Digicasino: Gelaende im Stil von Karte 16/17 (schwebende Plattformen in der Leere des Netzes).

Boden aus den Plattenkacheln von Karte 16, Randring dunkler mit cyan glimmender Kante, Metallfront mit Lichtfaeden.
Casino-Boeden: roter Teppich mit Goldrauten (Mittelgang), Automatenreihen auf violett getoentem Boden,
Spieltisch-Bereiche auf dunkelgruenem Casino-Teppich, Buehne oben (dunkelviolett, mit Goldkante und Stufe),
Jackpot-Inseln mit magenta Ringen. Leere: Netzraster, Nebel, Datenstraenge, Fragmente (Funktionen von Karte 16).

  python3 tools/karte22_layout.py && python3 tools/karte22_bauen.py
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageFilter
import karte04_bauen as k4
import karte08_bauen as k8
import karte16_bauen as k16

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte22')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte22')
T = 16
N_FRAMES = k16.N_FRAMES
BILDDAUER = k16.BILDDAUER
CYAN, LEER = k16.CYAN, k16.LEER
kontur, mischen, puls = k16.kontur, k16.mischen, k16.puls
GOLD = np.array((236, 190, 80), np.float32)
GOLD_D = np.array((150, 104, 36), np.float32)


def teppich(a, m):
    """Roter Casino-Teppich: dunkelrot, alle 16 px eine goldene Raute (Kachelmitte), seitlich goldene Borte."""
    Hh, W = m.shape
    yy, xx = np.mgrid[0:Hh, 0:W]
    a[m] = (122, 22, 38)
    a[m & ((xx + yy) % 2 == 0)] = (112, 18, 34)                   # feiner Flor
    d = np.abs((xx % 16) - 7.5) + np.abs((yy % 16) - 7.5)
    a[m & (d < 4.2) & (d >= 3.2)] = GOLD_D.astype(np.uint8)        # Raute (Kontur)
    a[m & (d < 2.2)] = (176, 40, 56)
    a[m & (d < 1.2)] = GOLD.astype(np.uint8)
    rand = m & ~(np.roll(m, 3, 1) & np.roll(m, -3, 1))             # Borte links/rechts (3 px)
    a[rand] = GOLD_D.astype(np.uint8)
    a[m & ~(np.roll(m, 1, 1) & np.roll(m, -1, 1))] = (70, 14, 24)
    a[m & ~(np.roll(m, 2, 1) & np.roll(m, -2, 1)) & (np.roll(m, 1, 1) & np.roll(m, -1, 1))] = GOLD.astype(np.uint8)


def filz(a, m):
    """Dunkelgruener Casino-Teppich unter den Spieltischen, kleines Punktmuster alle 8 px."""
    Hh, W = m.shape
    yy, xx = np.mgrid[0:Hh, 0:W]
    a[m] = (22, 70, 60)
    a[m & ((xx + yy) % 2 == 0)] = (20, 64, 55)
    a[m & (xx % 8 == 4) & (yy % 8 == 4)] = (60, 140, 110)
    r = m & ~(np.roll(m, 1, 0) & np.roll(m, -1, 0) & np.roll(m, 1, 1) & np.roll(m, -1, 1))
    a[r] = GOLD_D.astype(np.uint8)


def buehne(a, m, frame):
    """Buehne/Preistheke: dunkelviolette Dielen, Goldkante, nach Sueden eine Stufe (6 px) mit Lichtleiste."""
    Hh, W = m.shape
    yy, xx = np.mgrid[0:Hh, 0:W]
    a[m] = (52, 30, 80)
    a[m & (yy % 8 == 7)] = (38, 20, 60)                            # Dielenfugen
    a[m & (yy % 8 == 0)] = (70, 44, 104)
    a[m & (xx % 32 == 0) & (yy % 16 < 8)] = (38, 20, 60)
    a[m & (xx % 32 == 16) & (yy % 16 >= 8)] = (38, 20, 60)
    r = m & ~(np.roll(m, 1, 0) & np.roll(m, -1, 0) & np.roll(m, 1, 1) & np.roll(m, -1, 1))
    a[r] = GOLD.astype(np.uint8)
    unten = m & ~np.roll(m, -1, 0)                                 # Stufe nach Sueden
    p = 0.5 + 0.5 * puls(frame, 0.2)
    for y, x in zip(*np.nonzero(unten)):
        for d, c in ((1, (36, 18, 56)), (2, (30, 14, 48)), (3, None), (4, (26, 12, 42)), (5, (26, 12, 42)), (6, (12, 6, 20))):
            if y + d < Hh and not m[y + d, x]:
                if c is None:                                     # Lichtleiste (Lauflichter)
                    an = ((x // 4) + int((frame or 0))) % 2 == 0
                    c = GOLD * (0.55 + 0.45 * p) if an else GOLD_D * 0.7
                a[y + d, x] = np.array(c, np.float32).astype(np.uint8)
    return unten


def automatenboden(a, m):
    """Violett getoenter Plattenboden unter den Spielautomaten."""
    mischen(a, m, (96, 40, 140), 0.32)


def jackpot(a, m, frame):
    """Jackpot-Insel: magenta getoent, zwei konzentrische Ringe um die Mitte, pulsierend."""
    mischen(a, m, (170, 40, 160), 0.3)
    ys, xs = np.nonzero(m)
    cy, cx = ys.mean(), xs.mean()
    yy, xx = np.mgrid[0:m.shape[0], 0:m.shape[1]]
    d = np.hypot(yy - cy, xx - cx)
    p = 0.4 + 0.5 * puls(frame, 0.7)
    for rr in (10, 20):
        mischen(a, m & (np.abs(d - rr) < 1.0), (255, 120, 230), p)


def bauen(frame=None, speichern=True):
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cols, rows = lay['groesse']
    Wp, Hp = cols * T, rows * T
    kl = np.array([list(r) for r in lay['klassen']])
    gross = lambda arten: np.kron(np.isin(kl, list(arten)), np.ones((T, T), int)).astype(bool)
    a = np.zeros((Hp, Wp, 3), np.uint8)
    a[:] = LEER
    land = gross('prtskbzgj')
    ring = gross('r')
    leer = ~land
    k16.leere(a, leer, frame)
    # ------------------------------------------------------------------ Boden
    bt = k16.boden_textur(cols, rows)
    a[land] = bt[land]
    a[ring] = (bt[ring] * 0.72).astype(np.uint8)
    innen = land & ~ring
    a[innen & np.roll(ring, -1, 0)] = (18, 26, 46)                # Stufe Ring -> Boden
    a[innen & np.roll(ring, 1, 0)] = (78, 104, 140)
    automatenboden(a, gross('s'))
    filz(a, gross('k'))
    teppich(a, gross('t'))
    for i in range(len(lay['inseln'])):
        x0, y0, x1, y1 = lay['inseln'][i]
        m = np.zeros((Hp, Wp), bool)
        m[(y0 + 1) * T:y1 * T, (x0 + 1) * T:x1 * T] = True
        jackpot(a, m, frame)
    stufe = buehne(a, gross('b'), frame)
    n = 0
    for y in range(rows):
        for x in range(cols):
            if kl[y, x] in 'zg':
                k16.pfeil_marke(a, x, y, (110, 225, 250) if kl[y, x] == 'z' else (250, 200, 90), frame, n * 0.25)
                n += 1
    # ------------------------------------------------------------------ Kanten, Front, Leere
    front = k16.front_und_faeden(a, land, frame)
    ak = kontur(land)
    a[ak] = (8, 14, 30)
    mischen(a, kontur(land & ~ak), CYAN, 0.4 + 0.3 * puls(frame, 0.6))
    nah = np.array(Image.fromarray(((land | front) * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(25))) > 0
    rest = leer & ~front
    k16.straenge(a, rest & ~nah, frame, seed=2222, zonen=((4, 110), (722, 828), (130, 340), (492, 700)), n=4,
                 y_bereich=(40, 300))
    stellen = [(20, 24), (150, 12), (300, 8), (520, 10), (690, 18), (800, 30), (24, 280), (790, 270),
               (40, 400), (150, 360), (300, 390), (530, 395), (660, 360), (780, 400), (110, 300), (720, 300)]
    k16.fragmente(a, rest & ~nah, frame, seed=2223, stellen=stellen)
    lvl = np.zeros((Hp, Wp), np.uint8)
    lvl[land] = 2
    lvl[front] = 9
    if speichern and frame is None:
        np.save(os.path.join(KARTE, 'pixelhoehe.npy'), lvl)
        np.save(os.path.join(KARTE, 'wasser.npy'), np.packbits(np.zeros((Hp, Wp), bool)))
        np.save(os.path.join(KARTE, 'leere.npy'), np.packbits(rest))
    img = Image.fromarray(a).convert('RGBA')
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain_basis.png'))
    pf_ = os.path.join(OBJ, 'platzierung.json')
    if os.path.exists(pf_):
        objs = sorted((o for o in json.load(open(pf_)) if os.path.exists(os.path.join(OBJ, o['datei']))),
                      key=lambda o: o['y'] + o['fuss'])
        cache = {o['datei']: Image.open(os.path.join(OBJ, o['datei'])).convert('RGBA') for o in objs}
        k8.schatten_ebene(img, objs, cache, lvl)
        vor = np.array(img)
        k4.objekte_zeichnen(img, objs, cache, np.zeros((Hp, Wp), bool), frame)
        img = img.copy()
        k4.animieren(img, objs, cache, frame or 0, ruhig=frame is None)
        k8.verdeckung(img, objs, cache, lvl, vor)
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain.png'))
    print('Karte 22 %dx%d gebaut' % (cols, rows))
    return img


if __name__ == '__main__':
    bauen()
