"""Karte 17 (Our War Game!): zwei Netzwerk-Inseln im Datenraum nach der Vorlage (je 28x22 Kacheln, 4 Kacheln Luecke).

Boden, Teleporter, Kante, Front und Leere wie Karte 16 (The Network). Linke Insel: Ring in der Mitte (Spawn),
vier orange Teleporter rechts (2x2), Feld mit 6x5 Aufstellplaetzen (Eckwinkel) links unten, zwei cyan Teleporter
darunter. Rechte Insel: 6x5 Aufstellplaetze und zwei cyan Teleporter. Animation: 4 Bilder (Regel).

  python3 tools/karte17_bauen.py
"""
import json, math, os, sys
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
                    c = k16.CYAN * (0.55 + 0.3 * (0.5 + 0.5 * math.sin(2 * math.pi * ((frame or 0) / N_FRAMES))))
                if (x - x0 * T) % 32 == 0 and d >= 5:
                    c = np.array(H('#0e1424'), np.float32)
                a[yf + d, x] = np.clip(c, 0, 255).astype(np.uint8)
                front[yf + d, x] = True
        for d in range(12, 18):
            k16.mischen(a, (np.s_[yf + d], np.s_[x0 * T:(x0 + b) * T]), (4, 6, 14), 0.5 * (1 - (d - 12) / 6))
    leer = ~boden & ~front
    k16.leere_zeichnen(a, leer, frame, seed=17)
    puls = 0.5 + 0.5 * math.sin(2 * math.pi * (frame or 0) / N_FRAMES)
    k16.mischen(a, k16.kontur(boden), k16.CYAN, 0.45 + 0.3 * puls)
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
