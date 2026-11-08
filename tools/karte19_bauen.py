"""Karte 19 (Revenge): zwei schwebende Plattformen in der Leere des Netzes (Stil von Karte 16/17).

Links Network-Stil: Plattenboden der Vorlage, Aufstellfeld, Ankunfts- und Goldpfeile, drei kleine Bodenplatten
(Metallplatten mit zwei Nieten, wie in der Vorlage). Rechts ein Hafen: oben das Hafenbecken (Wasser wie Karte 01/18
mit Flachwasser, Stufen, Schaumkante und Lichtstrichen; der Randring der Plattform ist die Beckenmauer), darunter
Pflaster (Plattenkacheln der Vorlage in Grau, wie in der Vorlage) mit Kaikante aus hellem Stein, Aufstellfeld,
Ankunftspfeilen und Ringmarke. Ringsum Netzraster, blauer Nebel, Datenstraenge und Fragmente (Funktionen Karte 16).

  python3 tools/karte19_layout.py && python3 tools/karte19_bauen.py
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageFilter
import karte04_bauen as k4
import karte08_bauen as k8
import karte16_bauen as k16
import karte17_bauen as k17

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte19')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte19')
T = 16
N_FRAMES = k16.N_FRAMES
BILDDAUER = k16.BILDDAUER
CYAN, LEER = k16.CYAN, k16.LEER
kontur, mischen, puls = k16.kontur, k16.mischen, k16.puls
PFLASTER = np.array((137, 154, 155), np.float32)              # Pflasterfarbe der Vorlage


def pflaster_textur(cols, rows):
    """Plattenkacheln von Karte 16 in das Grau der Vorlage umgefaerbt (Helligkeit bleibt erhalten)."""
    bt = k16.boden_textur(cols, rows).astype(np.float32)
    lum = bt.mean(axis=2, keepdims=True)
    basis = np.array((54, 94, 126), np.float32).mean()
    return np.clip(lum / basis * PFLASTER * 0.92, 0, 255).astype(np.uint8)


def bodenplatte(a, tx, ty):
    """Kleine Metallplatte mit zwei Nieten (Vorlage: hellgraue Platte 10x4 px), mittig in der Kachel."""
    X, Y = tx * T + 3, ty * T + 7
    a[Y - 1, X + 1:X + 9] = (40, 52, 70)                      # Kontur
    a[Y + 4, X:X + 10] = (24, 32, 48)
    a[Y:Y + 4, X - 1] = (40, 52, 70); a[Y:Y + 4, X + 10] = (24, 32, 48)
    a[Y:Y + 4, X:X + 10] = (150, 170, 180)
    a[Y, X:X + 10] = (196, 212, 220)                          # Licht oben
    a[Y + 3, X:X + 10] = (112, 130, 142)
    a[Y + 2, X + 2] = a[Y + 2, X + 7] = (90, 104, 116)        # Nieten
    a[Y + 5, X + 1:X + 11] = (a[Y + 5, X + 1:X + 11] * 0.7).astype(np.uint8)   # Kontaktschatten


def hafenbecken(a, wasser, frame):
    """Hafenbecken: tiefes Wasser direkt an den Mauern (kein Strand). Grundfarbe wie die Vorlage, zur Mitte etwas
    dunkler; Wellenzeichen wie in der Vorlage (kleine Boegen, versetzt je Reihe), die je Bild 2 px nach rechts
    treiben; an der Nordmauer die sichtbare Mauerfront (Stein, nass, mit Wasserlinie), an allen Mauern ein feiner
    heller Wellensaum, vereinzelt Lichtglitzer."""
    f = frame or 0
    ys, xs = np.nonzero(wasser)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    h, w = y1 - y0, x1 - x0
    yy, xx = np.mgrid[0:h, 0:w]
    rand = np.minimum(np.minimum(yy, h - 1 - yy), np.minimum(xx, w - 1 - xx)).astype(np.float32)
    tief = np.clip(rand / 40.0, 0, 1)[..., None]
    flach, dunkel = np.array((62, 108, 140), np.float32), np.array((34, 70, 104), np.float32)
    sub = flach * (1 - tief) + dunkel * tief
    # Wellenzeichen: Bogen aus 4 px (oben 2 hell, Enden 1 tiefer), Raster 16x8, jede 2. Reihe um 8 px versetzt
    for gy in range(2, h, 8):
        for gx in range(-16, w, 16):
            X = gx + (8 if (gy // 8) % 2 else 0) + (2 * f) % 16 + (3 if (gy // 8) % 3 == 1 else 0)
            for dx, dy, c in ((1, 0, (104, 150, 178)), (2, 0, (104, 150, 178)), (0, 1, (84, 128, 160)), (3, 1, (84, 128, 160))):
                X_, Y_ = X + dx, gy + dy
                if 0 <= X_ < w and 0 <= Y_ < h:
                    sub[Y_, X_] = sub[Y_, X_] * 0.35 + np.array(c, np.float32) * 0.65
    # Nordmauer: sichtbare Front (6 px Stein, nass und dunkel nach unten), darunter Wasserlinie
    stein = [(120, 126, 124), (104, 110, 110), (92, 98, 100), (80, 88, 92), (66, 76, 84), (54, 66, 78)]
    for d, c in enumerate(stein):
        sub[d, :] = c
    for x in range(0, w, 16):
        sub[1:5, x] = (70, 78, 82)
    p = 0.5 + 0.5 * np.sin(2 * np.pi * (f / N_FRAMES))
    saum = (yy == 6) | ((xx <= 1) & (yy > 6)) | ((xx >= w - 2) & (yy > 6)) | (yy == h - 1)
    sub[saum] = sub[saum] * (0.55 - 0.15 * p) + np.array((170, 210, 225), np.float32) * (0.45 + 0.15 * p)
    rs = np.random.RandomState(1919)                            # Glitzer, jedes im eigenen Takt
    for _ in range(26):
        gx, gy, ph = rs.randint(4, w - 4), rs.randint(10, h - 3), rs.randint(4)
        if (f + ph) % 4 == 0:
            sub[gy, gx] = (230, 245, 250)
            sub[gy, gx - 1] = sub[gy, gx + 1] = sub[gy, gx] * 0.5 + sub[gy, gx - 1] * 0.5
    a[y0:y1, x0:x1][wasser[y0:y1, x0:x1]] = np.clip(sub, 0, 255).astype(np.uint8)[wasser[y0:y1, x0:x1]]
    return a


def kaikante(a, kai):
    """Kaikante: Reihe aus hellem Stein an der Wasserseite (oben), mit Fugen alle 16 px und Schatten zum Pflaster."""
    ys, xs = np.nonzero(kai)
    if not len(ys):
        return
    y0, x0, x1 = ys.min(), xs.min(), xs.max() + 1
    stein = [(206, 210, 200), (186, 190, 182), (170, 174, 166), (170, 174, 166), (156, 160, 152), (120, 124, 118)]
    for d, c in enumerate(stein):
        a[y0 + d, x0:x1] = c
    a[y0 + 6, x0:x1] = (a[y0 + 6, x0:x1] * 0.72).astype(np.uint8)  # Schatten der Kante auf dem Pflaster
    for x in range(x0, x1, 16):
        a[y0 + 1:y0 + 6, x] = (128, 132, 124)


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
    wasser = gross(kl == 'w')
    leer = ~land
    k16.leere(a, leer, frame)
    # ------------------------------------------------------------------ Boden (links Platten, rechts Pflaster)
    bt = k16.boden_textur(cols, rows)
    pt = pflaster_textur(cols, rows)
    rechts = np.zeros((Hp, Wp), bool)
    rechts[:, lay['raeume'][1][0] * T:] = True
    a[land] = np.where(rechts[land][:, None], pt[land], bt[land])
    a[ring] = (a[ring] * 0.72).astype(np.uint8)
    innen = land & ~ring & ~wasser
    a[innen & np.roll(ring, -1, 0)] = (18, 26, 46)
    a[innen & np.roll(ring, 1, 0) & ~rechts] = (78, 104, 140)
    a[innen & np.roll(ring, 1, 0) & rechts] = (150, 166, 168)
    for i, (x0, y0) in enumerate(lay['raeume']):
        k17.feld_marken(a, x0 + 1, y0 + 18, 6, 5, frame)
        if i == 0:
            for (px, py) in lay['platten']:
                bodenplatte(a, x0 + px, y0 + py)
        else:
            k17.ringmarke(a, x0 + 14, y0 + 8, frame)
    kaikante(a, gross(kl == 'k'))
    a = hafenbecken(a, wasser, frame)
    sch = wasser & (np.roll(ring, 2, 1) | np.roll(ring, 1, 1))     # Westmauer: Schatten aufs Wasser (Licht oben links)
    a[sch] = (a[sch] * 0.75).astype(np.uint8)
    # Pfeilkacheln
    pf = k16.kachel('pfeil.png').astype(np.float32)
    gp = k17.gold_pfeil()
    n = 0
    for y in range(rows):
        for x in range(cols):
            if kl[y, x] in 'zg':
                q = puls(frame, n * 0.25); n += 1
                src = pf if kl[y, x] == 'z' else gp
                a[y * T:(y + 1) * T, x * T:(x + 1) * T] = np.clip(src * (0.9 + 0.25 * q), 0, 255).astype(np.uint8)
    # ------------------------------------------------------------------ Kanten, Front, Leere
    front = k16.front_und_faeden(a, land, frame)
    ak = kontur(land)
    a[ak] = (8, 14, 30)
    mischen(a, kontur(land & ~ak), CYAN, 0.4 + 0.3 * puls(frame, 0.6))
    nah = np.array(Image.fromarray(((land | front) * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(25))) > 0
    rest = leer & ~front
    k16.straenge(a, rest & ~nah, frame, seed=1919, zonen=((8, 88), (552, 664), (1128, 1208), (100, 1100)), n=6,
                 y_bereich=(60, 440))
    stellen = [(20, 40), (40, 300), (16, 500), (300, 18), (720, 30), (1000, 20), (580, 140), (600, 320),
               (590, 500), (1140, 120), (1150, 340), (1130, 530), (220, 540), (860, 545)]
    k16.fragmente(a, rest & ~nah, frame, seed=1920, stellen=stellen)
    lvl = np.zeros((Hp, Wp), np.uint8)
    lvl[land] = 2
    lvl[wasser] = 1
    lvl[front] = 9
    if speichern and frame is None:
        np.save(os.path.join(KARTE, 'pixelhoehe.npy'), lvl)
        np.save(os.path.join(KARTE, 'wasser.npy'), np.packbits(wasser))
        np.save(os.path.join(KARTE, 'leere.npy'), np.packbits(rest))
    img = Image.fromarray(a).convert('RGBA')
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain_basis.png'))
    pf_ = os.path.join(OBJ, 'platzierung.json')
    if os.path.exists(pf_):
        objs = sorted((o for o in json.load(open(pf_)) if os.path.exists(os.path.join(OBJ, o['datei']))),
                      key=lambda o: o['y'] + o['fuss'])
        if objs:
            cache = {o['datei']: Image.open(os.path.join(OBJ, o['datei'])).convert('RGBA') for o in objs}
            k8.schatten_ebene(img, objs, cache, lvl)
            vor = np.array(img)
            k4.objekte_zeichnen(img, objs, cache, np.zeros((Hp, Wp), bool), frame)
            img = img.copy()
            k4.animieren(img, objs, cache, frame or 0, ruhig=frame is None)
            k8.verdeckung(img, objs, cache, lvl, vor)
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain.png'))
    print('Karte 19 %dx%d gebaut' % (cols, rows))
    return img


if __name__ == '__main__':
    bauen()
