"""Karte 17 (Our War Game!): zwei Netzwerk-Inseln im Datenraum nach der Vorlage (je 28x22 Kacheln, 4 Kacheln Luecke).

Boden, Teleporter, Kante, Front und Leere wie Karte 16 (The Network). Linke Insel: Ring in der Mitte (Spawn),
vier orange Teleporter rechts (2x2), Feld mit 6x5 Aufstellplaetzen (Eckwinkel) links unten, zwei cyan Teleporter
darunter. Rechte Insel: 6x5 Aufstellplaetze und zwei cyan Teleporter. Animation: 4 Bilder (Regel).

  python3 tools/karte17_bauen.py
"""
import json, math, os, random, sys
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
H = k4.H
RAND = 3
IB, IH, LUECKE = 28, 22, 4
C, R = RAND * 2 + IB * 2 + LUECKE, RAND * 2 + IH
INSELN = [RAND, RAND + IB + LUECKE]                     # linke Kante je Insel (Kacheln), oben = RAND


def layout():
    k = np.full((R, C), '.')
    h = np.zeros((R, C), int)
    tele, plaetze = [], []
    for i, x0 in enumerate(INSELN):
        k[RAND:RAND + IH, x0:x0 + IB] = 'n'
        h[RAND:RAND + IH, x0:x0 + IB] = 1
        plaetze.append([x0 + 1, RAND + 16, 6, 5])                    # 6x5 Aufstellplaetze
        tele.append({'x': x0 + 1, 'y': RAND + 21, 'b': 2, 'h': 1, 'farbe': 'cyan'})
    tele.append({'x': INSELN[0] + 25, 'y': RAND + 9, 'b': 2, 'h': 2, 'farbe': 'orange'})
    lay = {'groesse': [C, R], 'klassen': [''.join(r) for r in k], 'hoehe': [''.join(str(c) for c in r) for r in h],
           'inseln': [[x0, RAND, IB, IH] for x0 in INSELN], 'plaetze': plaetze, 'teleporter': tele,
           'ring': [INSELN[0] + 14.5, RAND + 10.5]}
    os.makedirs(KARTE, exist_ok=True)
    json.dump(lay, open(os.path.join(KARTE, 'layout.json'), 'w'), indent=0)
    return lay


def platz_winkel(a, tx, ty, frame, phase):
    """Aufstellplatz wie in der Vorlage: vier helle Eckwinkel in der Kachel, glimmen leicht (4 Bilder)."""
    p = 0.55 + 0.25 * math.sin(2 * math.pi * ((frame or 0) / N_FRAMES + phase))
    c = np.clip(np.array([150, 190, 220], np.float32) * p + 40, 0, 255).astype(np.uint8)
    x0, y0 = tx * T, ty * T
    for (ex, ey, sx, sy) in ((2, 2, 1, 1), (13, 2, -1, 1), (2, 13, 1, -1), (13, 13, -1, -1)):
        for d in range(4):
            a[y0 + ey, x0 + ex + sx * d] = c
            a[y0 + ey + sy * d, x0 + ex] = c


def ring(a, cx, cy, frame):
    """Spawn-Ring in der Mitte der linken Insel: heller Kreis (r 6 px), pulsiert leicht."""
    p = 0.7 + 0.3 * math.sin(2 * math.pi * (frame or 0) / N_FRAMES)
    yy, xx = np.mgrid[-9:10, -9:10]
    d = np.hypot(xx, yy)
    for (dy, dx) in zip(*np.nonzero(np.abs(d - 6) <= 0.7)):
        a[int(cy) - 9 + dy, int(cx) - 9 + dx] = np.clip(np.array([200, 225, 245]) * p, 0, 255).astype(np.uint8)


ROT = np.array([230, 40, 60], np.float32)


def befall_karte(lay):
    """Welche Kacheln sind befallen (0 rein, 1 leicht, 2 schwer): Wolken aus Rauschen, nach rechts immer staerker
    (linke Insel: fruehe Stufen, rechte Insel: spaete Stufen). Aufstellplaetze, Teleporter und Ring bleiben frei."""
    cols, rows = lay['groesse']
    rs = np.random.RandomState(1717)
    n = np.array(Image.fromarray((rs.rand(rows // 3 + 2, cols // 3 + 2) * 255).astype(np.uint8))
                 .resize((cols, rows), Image.BICUBIC)).astype(np.float32) / 255
    xs = np.arange(cols)[None, :] / cols
    wert = n * 0.75 + xs * 0.55
    st = np.zeros((rows, cols), int)
    st[wert > 0.78] = 1
    st[wert > 0.98] = 2
    kl = np.array([list(r) for r in lay['klassen']])
    st[kl == '.'] = 0
    frei = np.zeros_like(st, bool)
    for (x0, y0, b, h) in lay['plaetze']:
        frei[y0 - 1:y0 + h + 1, x0 - 1:x0 + b + 1] = True
    for tp in lay['teleporter']:
        frei[tp['y'] - 1:tp['y'] + tp['h'] + 1, tp['x'] - 1:tp['x'] + tp['b'] + 1] = True
    rx, ry = lay['ring']
    frei[int(ry) - 2:int(ry) + 2, int(rx) - 2:int(rx) + 2] = True
    st[frei] = 0
    return st


def befall_zeichnen(a, st, frame):
    """Befallene Kacheln: leicht = rot verfaerbt mit Glitch-Pixeln, schwer = schwarz mit rot pulsierenden Adern;
    Glitch-Bloecke flackern (4 Bilder)."""
    f = frame or 0
    rows, cols = st.shape
    for y in range(rows):
        for x in range(cols):
            if not st[y, x]:
                continue
            rs = random.Random(y * 131 + x * 7)
            sub = a[y * T:(y + 1) * T, x * T:(x + 1) * T].astype(np.float32)
            if st[y, x] == 1:
                sub = sub * np.array([1.05, 0.55, 0.62])
            else:
                sub = sub * np.array([0.42, 0.22, 0.28])
            a[y * T:(y + 1) * T, x * T:(x + 1) * T] = np.clip(sub, 0, 255).astype(np.uint8)
            p = 0.55 + 0.45 * math.sin(2 * math.pi * (f / N_FRAMES + rs.random()))
            X, Y = x * T + rs.randint(2, 13), y * T + rs.randint(2, 13)        # Ader (Riss mit Licht)
            for i in range(rs.randint(8, 16) if st[y, x] == 2 else rs.randint(4, 8)):
                if x * T <= X < (x + 1) * T and y * T <= Y < (y + 1) * T:
                    a[Y, X] = np.clip(ROT * (0.5 + 0.5 * p) if st[y, x] == 2 else ROT * 0.6, 0, 255).astype(np.uint8)
                X += rs.choice((-1, 0, 1)); Y += rs.choice((-1, 0, 1))
            for k_ in range(2 if st[y, x] == 1 else 3):                       # Glitch-Bloecke flackern
                if (f + k_ + x + y) % 4 == 0:
                    continue
                gx, gy = x * T + rs.randint(1, 12), y * T + rs.randint(1, 12)
                c = rs.choice(((230, 40, 90), (20, 10, 16), (200, 30, 40), (230, 40, 90), (20, 10, 16), (250, 240, 240)))
                a[gy:gy + 2, gx:gx + rs.choice((2, 3))] = c


def kabelnetz(a, lay, leer, frame):
    """Netz aus schwarzen Kabeln zwischen den Inseln (an den Kanten verankert, haengt leicht durch), rote Knoten;
    ein roter Lichtpunkt laeuft in 4 Bildern von rechts (Befall) nach links."""
    f = frame or 0
    (lx, ly_, lb, lh), (rx, _, _, _) = lay['inseln']
    xa, xb = (lx + lb) * T, rx * T - 1
    for k_, (ya, yb, durch) in enumerate(((RAND + 4, RAND + 6, 10), (RAND + 9, RAND + 8, 14), (RAND + 14, RAND + 16, 12),
                                          (RAND + 19, RAND + 18, 8))):
        pts = []
        for i in range(xb - xa + 1):
            t = i / (xb - xa)
            y = (ya + (yb - ya) * t) * T + 8 + durch * 4 * t * (1 - t)
            pts.append((xa + i, int(round(y))))
        for (x, y) in pts:
            if leer[y, x]:
                a[y, x] = H('#06060c'); a[y + 1, x] = H('#2a1a24')
        j = int((N_FRAMES - 1 - f) / N_FRAMES * len(pts) + k_ * 7) % len(pts)
        for jj in range(max(0, j - 3), min(len(pts), j + 1)):
            x, y = pts[jj]
            a[y, x] = np.clip(ROT * 1.1, 0, 255).astype(np.uint8)
        for (x, y) in (pts[len(pts) // 3], pts[2 * len(pts) // 3]):              # Knoten
            a[y - 1:y + 2, x - 1:x + 2] = H('#a01c2a'); a[y, x] = H('#ff6070')


def bauen(frame=None, speichern=True):
    lay = layout()
    cols, rows = lay['groesse']
    Wp, Hp = cols * T, rows * T
    kl = np.array([list(r) for r in lay['klassen']])
    gross = lambda m: np.kron(m, np.ones((T, T), int)).astype(bool)
    boden = gross(kl != '.')
    a = k16.textur('leer', cols, rows)
    a[boden] = k16.textur('n', cols, rows)[boden]
    front = np.zeros((Hp, Wp), bool)
    for (x0, y0, b, h) in lay['inseln']:                          # Suedfront wie Karte 16
        yf = (y0 + h) * T
        for d in range(12):
            for x in range(x0 * T, (x0 + b) * T):
                c = np.array(H('#1a2840') if d < 2 else H('#24344e') if d < 9 else H('#141c30'), np.float32)
                if d == 4:
                    c = (k16.CYAN if x0 == INSELN[0] else ROT) * (0.55 + 0.3 * (0.5 + 0.5 * math.sin(2 * math.pi * ((frame or 0) / N_FRAMES))))
                if (x - x0 * T) % 32 == 0 and d >= 5:
                    c = np.array(H('#0e1424'), np.float32)
                a[yf + d, x] = np.clip(c, 0, 255).astype(np.uint8)
                front[yf + d, x] = True
        for d in range(12, 18):
            k16.mischen(a, (np.s_[yf + d], np.s_[x0 * T:(x0 + b) * T]), (4, 6, 14), 0.5 * (1 - (d - 12) / 6))
    leer = ~boden & ~front
    k16.leere_zeichnen(a, leer, frame, seed=17)
    puls = 0.5 + 0.5 * math.sin(2 * math.pi * (frame or 0) / N_FRAMES)
    kante = k16.kontur(boden)
    rechts = np.zeros_like(kante); rechts[:, lay['inseln'][1][0] * T:] = True
    k16.mischen(a, kante & ~rechts, k16.CYAN, 0.45 + 0.3 * puls)
    k16.mischen(a, kante & rechts, ROT, 0.5 + 0.3 * puls)           # rechte Insel: Kante vom Virus rot gefaerbt
    befall_zeichnen(a, befall_karte(lay), frame)
    kabelnetz(a, lay, leer, frame)
    for (x0, y0, b, h) in lay['plaetze']:
        for j in range(h):
            for i in range(b):
                platz_winkel(a, x0 + i, y0 + j, frame, (i + j) * 0.25)
    ring(a, lay['ring'][0] * T, lay['ring'][1] * T, frame)
    for tp in lay['teleporter']:
        for j in range(tp['h']):
            for i in range(tp['b']):
                k16.pad(a, tp['x'] + i, tp['y'] + j, tp['farbe'], frame, j)
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
    print('Karte 17 %dx%d gebaut' % (cols, rows))
    return img


if __name__ == '__main__':
    bauen()
