"""Karte 16 (The Network): eine Netzwerk-Plattform im dunklen Datenraum - halbe Groesse der Vorlage (32x20 statt 64x40).

Blaue Netzwerk-Platten wie in der Vorlage, cyan glimmende Plattformkante, Suedfront aus Stahl mit Lichtband, in der
Mitte die Datenbahn (Datenpakete laufen nach Sueden), verzweigte Leiterbahnen mit wandernden Lichtpunkten, oben das
Firewall-Tor mit Teleportern darunter, unten die Teleporter zum Ausgang. Ringsum die Leere des Netzes mit Raster und
fallenden Datenstroemen. Animation: 4 Bilder (Regel).

  python3 tools/karte16_kacheln.py && python3 tools/karte16_bauen.py
  python3 tools/karte16_objekte.py && python3 tools/karte16_bauen.py
"""
import json, math, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
import karte_bauen as kb
import karte04_bauen as k4
import karte08_bauen as k8

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte16')
BASIS = os.path.join(ROOT, 'assets', 'karte16', 'basis')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte16')
T = 16
N_FRAMES = 4                     # Regel: hoechstens 4 Animationsbilder
BILDDAUER = 250
k4.N_FRAMES = N_FRAMES
H = k4.H
CYAN = np.array([90, 224, 236], np.float32)
ORANGE = np.array([240, 150, 70], np.float32)

C, R = 32, 20
BODEN = (2, 2, 29, 17)                                # x0, y0, x1, y1 (Kacheln, inklusive)
BAHN = (15, 16, 7, 15)                                # Datenbahn x0, x1, y0, y1
TOR = (14, 17, 5)                                     # Tor x0, x1, Fuss-Reihe
TELEPORTER = [{'x': 14, 'y': 6, 'b': 4, 'h': 1, 'farbe': 'cyan'}, {'x': 14, 'y': 16, 'b': 4, 'h': 1, 'farbe': 'cyan'}]
# Leiterbahnen: Punktfolgen in Kacheln (Mitte der Kachel = +0.5), rechte Haelfte wird gespiegelt
BAHNEN = [[(15, 9.5), (11.5, 9.5), (9.5, 11.5), (5.5, 11.5)],
          [(15, 13.5), (12.5, 13.5), (10.5, 15.5), (7.5, 15.5)],
          [(15, 8.0), (13.5, 8.0), (11.5, 6.0), (6.5, 6.0), (4.5, 4.0)]]


def layout():
    k = np.full((R, C), '.')
    h = np.zeros((R, C), int)
    x0, y0, x1, y1 = BODEN
    k[y0:y1 + 1, x0:x1 + 1] = 'n'
    h[y0:y1 + 1, x0:x1 + 1] = 1
    bx0, bx1, by0, by1 = BAHN
    k[by0:by1 + 1, bx0:bx1 + 1] = 'b'
    lay = {'groesse': [C, R], 'klassen': [''.join(r) for r in k], 'hoehe': [''.join(str(c) for c in r) for r in h],
           'boden': list(BODEN), 'bahn': list(BAHN), 'tor': list(TOR), 'teleporter': TELEPORTER,
           'achse': C * T // 2}
    os.makedirs(KARTE, exist_ok=True)
    json.dump(lay, open(os.path.join(KARTE, 'layout.json'), 'w'), indent=0)
    return lay


def textur(art, cols, rows):
    t = np.zeros((rows * T, cols * T, 3), np.uint8)
    ks = [np.array(Image.open(os.path.join(BASIS, '%s_%d.png' % (art, v))).convert('RGB')) for v in range(5)]
    for y in range(rows):
        for x in range(cols):
            t[y * T:(y + 1) * T, x * T:(x + 1) * T] = ks[kb.variante(x, y)]
    return t


def mischen(a, m, farbe, s):
    a[m] = np.clip(a[m] * (1 - s) + np.asarray(farbe, np.float32) * s, 0, 255).astype(np.uint8)


def kontur(m):
    return m & ~(np.roll(m, 1, 0) & np.roll(m, -1, 0) & np.roll(m, 1, 1) & np.roll(m, -1, 1))


def leere_zeichnen(a, leer, frame, seed=16):
    """Leere des Netzes: schwaches Raster mit Knotenpunkten, dazu einzelne fallende Datenstroeme (Bits fallen je Bild
    um 4 px, Periode 16 px -> nahtlos in 4 Bildern)."""
    f = frame or 0
    Hh, W = leer.shape
    rs = random.Random(seed)
    for _ in range(26):                                           # Knoten mit kurzen Verbindungen (statisch)
        x, y = rs.randrange(4, W - 4), rs.randrange(4, Hh - 4)
        if not leer[y, x]:
            continue
        a[y, x] = H('#2a4a78')
        lang, rx = rs.randint(6, 18), rs.choice((1, -1))
        for i in range(1, lang):
            X = x + rx * i
            if 0 <= X < W and leer[y, X]:
                a[y, X] = np.maximum(a[y, X], np.array(H('#14223e')))
    for _ in range(16):                                           # fallende Datenstroeme
        x = rs.randrange(2, W - 2)
        y0, lang = rs.randrange(0, Hh), rs.randint(20, 56)
        for i in range(lang):
            Y = (y0 + i + 4 * f) % Hh
            if not leer[Y, x] or i % 4 == 3:
                continue
            s_ = (i / lang) ** 1.5 * 0.7
            a[Y, x] = np.clip(a[Y, x] * (1 - s_) + np.array([60, 190, 215]) * s_, 0, 255).astype(np.uint8)


def pad(a, tx, ty, farbe, frame, phase=0):
    """Teleporter-Feld wie in der Vorlage: dunkle Fassung, farbiger Rahmen, zwei Pfeile nach oben; ein Lichtschein
    wandert in 4 Bildern von unten nach oben durch die Pfeile."""
    f = ((frame or 0) + phase) % N_FRAMES
    c = CYAN if farbe == 'cyan' else ORANGE
    x0, y0 = tx * T, ty * T
    for y in range(1, 15):
        for x in range(1, 15):
            ecke = (x in (1, 14)) and (y in (1, 14))
            if ecke:
                continue
            rand = x in (1, 14) or y in (1, 14)
            innen = x in (2, 13) or y in (2, 13)
            if rand:
                v = c * 0.55
            elif innen:
                v = np.array(H('#10182c'), np.float32)
            else:
                v = np.array(H('#1a2a44'), np.float32)
            a[y0 + y, x0 + x] = np.clip(v, 0, 255).astype(np.uint8)
    for x in range(2, 14):                                        # Lichtkante oben am Rahmen
        a[y0 + 1, x0 + x] = np.clip(c * 0.85, 0, 255).astype(np.uint8)
    for k_, yy in enumerate((5, 9)):                              # zwei Pfeile (Spitze oben)
        hell = 1.0 if (3 - f) % 4 == k_ * 2 % 4 or (3 - f) % 4 == k_ * 2 % 4 + 1 else 0.55
        for d in range(5):
            for dx in (-d, d):
                X, Y = x0 + 8 + dx - (1 if dx < 0 else 0), y0 + yy + d
                a[Y, X] = np.clip(c * hell + 40 * hell, 0, 255).astype(np.uint8)
                if Y + 1 < y0 + 13:
                    a[Y + 1, X] = np.clip(c * 0.35, 0, 255).astype(np.uint8)


def bahnen_zeichnen(a, achse, frame):
    """Leiterbahnen: 2 px Rille mit cyan Lichtlinie, Knotenpunkte an den Enden; ein Lichtpunkt laeuft in 4 Bildern
    von der Datenbahn nach aussen. Rechte Seite exakt gespiegelt zur Achse."""
    f = frame or 0
    for bahn in BAHNEN:
        for seite in (1, -1):
            pts = [((x * T) if seite == 1 else (2 * achse - x * T - 1), y * T) for x, y in bahn]
            pfad = []
            for (xa, ya), (xb, yb) in zip(pts, pts[1:]):
                n = int(max(abs(xb - xa), abs(yb - ya)))
                for i in range(n):
                    pfad.append((int(round(xa + (xb - xa) * i / n)), int(round(ya + (yb - ya) * i / n))))
            for i, (x, y) in enumerate(pfad):
                a[y, x] = H('#142238'); a[y + 1, x] = H('#3a5680')
                a[y - 1, x] = np.clip(a[y - 1, x] * 0.6 + CYAN * 0.4 * 0.6, 0, 255).astype(np.uint8)
            ex, ey = pfad[-1]
            for dy in range(-2, 3):
                for dx in range(-2, 3):
                    if abs(dx) + abs(dy) <= 3:
                        a[ey + dy, ex + dx] = H('#142238') if abs(dx) == 2 or abs(dy) == 2 else np.clip(CYAN * 0.8, 0, 255).astype(np.uint8)
            schritt = len(pfad) / N_FRAMES                        # Lichtpunkt wandert nach aussen
            for k_ in range(2):
                j = int((f + k_ * 2) % N_FRAMES * schritt + schritt * 0.5)
                for jj in range(max(0, j - 3), min(len(pfad), j + 1)):
                    x, y = pfad[jj]
                    s_ = 0.4 + 0.15 * (jj - j + 3)
                    a[y - 1, x] = np.clip(a[y - 1, x] * (1 - s_) + np.array([210, 255, 255]) * s_, 0, 255).astype(np.uint8)


def datenbahn(a, frame):
    """Datenbahn auf der Achse: Datenpakete (helle Pfeile) laufen nach Sueden, je Bild 4 px (Periode 16 px)."""
    f = frame or 0
    bx0, bx1, by0, by1 = BAHN
    x0, x1 = bx0 * T, (bx1 + 1) * T
    for x in (x0, x1 - 1):
        a[by0 * T:(by1 + 1) * T, x] = np.clip(CYAN * 0.7, 0, 255).astype(np.uint8)
    for y in range(by0 * T + 2, (by1 + 1) * T - 4):
        ph = (y - by0 * T - 4 * f) % 16
        if ph < 3:
            breite = 6 - ph * 2
            cx = (x0 + x1) // 2
            for dx in range(-breite, breite):
                a[y, cx + dx] = np.clip(a[y, cx + dx] * 0.4 + CYAN * 0.6 * (1 - ph * 0.2), 0, 255).astype(np.uint8)


def bauen(frame=None, speichern=True):
    lay = layout()
    cols, rows = lay['groesse']
    Wp, Hp = cols * T, rows * T
    kl = np.array([list(r) for r in lay['klassen']])
    gross = lambda m: np.kron(m, np.ones((T, T), int)).astype(bool)
    boden = gross(kl != '.')
    a = textur('leer', cols, rows)
    a[boden] = textur('n', cols, rows)[boden]
    bahn = gross(kl == 'b')
    a[bahn] = textur('b', cols, rows)[bahn]
    achse = lay['achse']
    # Suedfront: Stahl 12 px mit cyan Lichtband, darunter Schatten in die Leere
    x0, y0, x1, y1 = BODEN
    yf = (y1 + 1) * T
    front = np.zeros((Hp, Wp), bool)
    for d in range(12):
        for x in range(x0 * T, (x1 + 1) * T):
            c = np.array(H('#1a2840') if d < 2 else H('#24344e') if d < 9 else H('#141c30'), np.float32)
            if d == 4:
                c = CYAN * (0.55 + 0.3 * (0.5 + 0.5 * math.sin(2 * math.pi * ((frame or 0) / N_FRAMES))))
            if (x - x0 * T) % 32 == 0 and d >= 5:
                c = np.array(H('#0e1424'), np.float32)
            a[yf + d, x] = np.clip(c, 0, 255).astype(np.uint8)
            front[yf + d, x] = True
    for d in range(12, 18):
        mischen(a, (np.s_[yf + d], np.s_[x0 * T:(x1 + 1) * T]), (4, 6, 14), 0.5 * (1 - (d - 12) / 6))
    leer = ~boden & ~front
    leere_zeichnen(a, leer & (np.mgrid[0:Hp, 0:Wp][0] >= 0), frame)
    # Kante: cyan Kontur, aussen dunkel (Seiten nur schmale Abgrenzung)
    rand = kontur(boden)
    puls = 0.5 + 0.5 * math.sin(2 * math.pi * (frame or 0) / N_FRAMES)
    mischen(a, rand, CYAN, 0.45 + 0.3 * puls)
    datenbahn(a, frame)
    bahnen_zeichnen(a, achse, frame)
    for i, tp in enumerate(lay['teleporter']):
        for j in range(tp['b']):
            pad(a, tp['x'] + j, tp['y'], tp['farbe'], frame, 0)
    lvl = np.zeros((Hp, Wp), np.uint8)
    lvl[boden] = 1
    lvl[front] = 9
    if speichern and frame is None:
        np.save(os.path.join(KARTE, 'pixelhoehe.npy'), lvl)
        np.save(os.path.join(KARTE, 'wasser.npy'), np.packbits(np.zeros((Hp, Wp), bool)))
        np.save(os.path.join(KARTE, 'leere.npy'), np.packbits(leer))
    img = Image.fromarray(a).convert('RGBA')
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain_basis.png'))
    pf = os.path.join(OBJ, 'platzierung.json')
    if os.path.exists(pf):
        objs = sorted((o for o in json.load(open(pf)) if os.path.exists(os.path.join(OBJ, o['datei']))),
                      key=lambda o: o['y'] + o['fuss'])
        cache = {o['datei']: Image.open(os.path.join(OBJ, o['datei'])).convert('RGBA') for o in objs}
        k8.schatten_ebene(img, objs, cache, lvl)
        k4.objekte_zeichnen(img, objs, cache, np.zeros((Hp, Wp), bool), frame)
        img = img.copy()
        k4.animieren(img, objs, cache, frame or 0, ruhig=frame is None)
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain.png'))
    print('Karte 16 %dx%d gebaut' % (cols, rows))
    return img


if __name__ == '__main__':
    bauen()
