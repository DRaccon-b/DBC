"""Karte 17 (Our War Game!), Neuaufbau im Stil von Karte 16: zwei schwebende Plattformen in der Leere des Netzes.

Boden aus den Plattenkacheln der Vorlage (wie Karte 16), Randring dunkler mit cyan glimmender Kante, schmale
Metallfront unter den Suedkanten mit haengenden Lichtfaeden. In jedem Raum ein Aufstellfeld (6x5 Kacheln mit
Eckmarken wie in der Vorlage) und zwei cyan Pfeilkacheln (Ankunft); im linken Raum eine Ringmarke in der Mitte und
2x2 goldene Pfeilkacheln (Weg in den zweiten Raum). Leere: Netzraster, blauer Nebel, Datenstraenge, Fragmente -
alles mit den Funktionen aus Karte 16.

  python3 tools/karte17_layout.py && python3 tools/karte17_bauen.py
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
import karte04_bauen as k4
import karte08_bauen as k8
import karte16_bauen as k16

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte17')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte17')
T = 16
N_FRAMES = k16.N_FRAMES
BILDDAUER = k16.BILDDAUER
CYAN, LEER = k16.CYAN, k16.LEER
kontur, mischen, puls = k16.kontur, k16.mischen, k16.puls


def gold_pfeil():
    """Pfeilkachel der Vorlage, cyan -> gold umgefaerbt (wie die goldenen Pfeile in der Vorlage)."""
    p = k16.kachel('pfeil.png').astype(np.float32)
    r_, g_, b_ = p[..., 0], p[..., 1], p[..., 2]
    m = (b_ > r_ + 30) & (g_ > r_ + 20) & (p.mean(axis=2) > 95)   # nur die hellen cyan Pixel (Pfeil, Rahmen)
    hell = (p[m].mean(axis=1) / 255.0)[:, None]
    p[m] = np.clip(np.array((250, 196, 90), np.float32) * (0.45 + 0.75 * hell), 0, 255)
    return p


def feld_marken(a, x0, y0, w, h, frame):
    """Aufstellfeld: in jeder Kachel vier kleine Eckklammern (wie in der Vorlage), leicht glimmend."""
    p = 0.6 + 0.4 * puls(frame, 0.4)
    farbe = np.array((150, 200, 225), np.float32)
    for ty in range(y0, y0 + h):
        for tx in range(x0, x0 + w):
            X, Y = tx * T, ty * T
            for (ex, ey, sx, sy) in ((2, 2, 1, 1), (13, 2, -1, 1), (2, 13, 1, -1), (13, 13, -1, -1)):
                for d in range(3):
                    for (xx, yy) in ((X + ex + sx * d, Y + ey), (X + ex, Y + ey + sy * d)):
                        a[yy, xx] = np.clip(a[yy, xx] * (1 - 0.7 * p) + farbe * 0.7 * p, 0, 255).astype(np.uint8)


def pfeil_marke(a, tx, ty, farbe, frame, ph):
    """Pfeilfeld passend zum Aufstellfeld: vier Eckklammern (wie feld_marken) und ein Doppel-Chevron nach Norden,
    beides direkt auf dem Boden, 1 px dunkler Schlagschatten rechts unten, Leuchten pulsiert."""
    p = 0.55 + 0.45 * puls(frame, ph)
    farbe = np.array(farbe, np.float32)
    X, Y = tx * T, ty * T
    pix = []
    for (ex, ey, sx, sy) in ((2, 2, 1, 1), (13, 2, -1, 1), (2, 13, 1, -1), (13, 13, -1, -1)):
        for d in range(3):
            pix += [(Y + ey, X + ex + sx * d), (Y + ey + sy * d, X + ex)]
    for oy in (4, 8):                                           # zwei Chevrons uebereinander
        for d in range(4):
            pix += [(Y + oy + d, X + 7 - d), (Y + oy + d, X + 8 + d)]
    for (yy, xx) in pix:                                        # Schatten zuerst
        a[yy + 1, xx + 1] = (a[yy + 1, xx + 1] * 0.75).astype(np.uint8)
    for (yy, xx) in pix:
        a[yy, xx] = np.clip(a[yy, xx] * (1 - 0.8 * p) + farbe * 0.8 * p, 0, 255).astype(np.uint8)


def ringmarke(a, tx, ty, frame):
    """Kleine Ringmarke in der Raummitte (Vorlage: heller Kreis)."""
    cx, cy = tx * T + 8, ty * T + 8
    yy, xx = np.mgrid[0:T, 0:T]
    d = np.hypot(xx + 0.5 - 8, yy + 0.5 - 8)
    m = np.abs(d - 5.5) <= 0.8
    p = 0.3 + 0.65 * puls(frame, 0.1)
    sub = a[ty * T:(ty + 1) * T, tx * T:(tx + 1) * T].astype(np.float32)
    sub[m] = sub[m] * (1 - p) + np.array((225, 235, 245), np.float32) * p
    a[ty * T:(ty + 1) * T, tx * T:(tx + 1) * T] = sub.astype(np.uint8)


def bauen(frame=None, speichern=True):
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cols, rows = lay['groesse']
    Wp, Hp = cols * T, rows * T
    kl = np.array([list(r) for r in lay['klassen']])
    gross = lambda m: np.kron(m, np.ones((T, T), int)).astype(bool)
    a = np.zeros((Hp, Wp, 3), np.uint8)
    a[:] = LEER
    land = gross(kl != '.')
    ring = gross(kl == 'r')
    leer = ~land
    k16.leere(a, leer, frame)
    # ------------------------------------------------------------------ Boden
    bt = k16.boden_textur(cols, rows)
    a[land] = bt[land]
    a[ring] = (bt[ring] * 0.72).astype(np.uint8)
    innen = land & ~ring
    a[innen & np.roll(ring, -1, 0)] = (18, 26, 46)                # Stufe Ring -> Boden
    a[innen & np.roll(ring, 1, 0)] = (78, 104, 140)
    RW, RH = lay['raum']
    for i, (x0, y0) in enumerate(lay['raeume']):
        feld_marken(a, x0 + 1, y0 + 16, 6, 5, frame)
        if i == 0:
            ringmarke(a, x0 + 14, y0 + 10, frame)
    # Pfeile im Stil des Sammelplatzes (wie Karte 19): Eckklammern + Doppel-Chevron direkt auf dem Boden,
    # cyan = Ankunft, gold = weiter; leuchten nacheinander
    n = 0
    for y in range(rows):
        for x in range(cols):
            if kl[y, x] in 'zg':
                pfeil_marke(a, x, y, (110, 225, 250) if kl[y, x] == 'z' else (250, 200, 90), frame, n * 0.25)
                n += 1
    # ------------------------------------------------------------------ Kanten, Front, Leere
    front = k16.front_und_faeden(a, land, frame)
    ak = kontur(land)
    a[ak] = (8, 14, 30)
    mischen(a, kontur(land & ~ak), CYAN, 0.4 + 0.3 * puls(frame, 0.6))
    nah = np.array(Image.fromarray(((land | front) * 255).astype(np.uint8)).filter(
        __import__('PIL.ImageFilter', fromlist=['x']).MaxFilter(25))) > 0
    rest = leer & ~front
    k16.straenge(a, rest & ~nah, frame, seed=1717, zonen=((8, 88), (552, 664), (1128, 1208), (100, 1100)), n=6,
                 y_bereich=(60, 420))
    stellen = [(20, 40), (40, 300), (16, 470), (300, 18), (720, 30), (1000, 20), (580, 140), (600, 300),
               (590, 470), (1140, 120), (1150, 330), (1130, 500), (200, 500), (860, 505)]
    k16.fragmente(a, rest & ~nah, frame, seed=1718, stellen=stellen)
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
    print('Karte 17 %dx%d gebaut' % (cols, rows))
    return img


if __name__ == '__main__':
    bauen()
