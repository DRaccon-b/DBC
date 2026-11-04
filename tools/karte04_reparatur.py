"""Abgeschnittene PixelLab-Kandidaten reparieren: breite Baumkronen ragen ueber die 80-px-Zelle hinaus,
das Reststueck landet am linken Rand des naechsten Kandidaten. Es wird abgetrennt und an der Schnittkante
(Hoehe per Kantenabgleich) wieder angesetzt.

  python3 tools/karte04_reparatur.py   -> assets/objekte/karte04/<gruppe>/NN.png wird ersetzt (Original *_roh.png)
"""
import os, shutil
from collections import deque
import numpy as np
from PIL import Image

OBJ = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets', 'objekte', 'karte04')
PAARE = [('rand/01', 'rand/02'), ('baeume/00', 'baeume/01')]


def komponenten(a):
    m = a[..., 3] > 0
    h, w = m.shape
    lab = np.zeros((h, w), int); n = 0
    for y in range(h):
        for x in range(w):
            if m[y, x] and not lab[y, x]:
                n += 1; q = deque([(y, x)]); lab[y, x] = n
                while q:
                    yy, xx = q.popleft()
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            y2, x2 = yy + dy, xx + dx
                            if 0 <= y2 < h and 0 <= x2 < w and m[y2, x2] and not lab[y2, x2]:
                                lab[y2, x2] = n; q.append((y2, x2))
    return lab, n


def roh(name):
    p = os.path.join(OBJ, name + '.png'); r = os.path.join(OBJ, name + '_roh.png')
    if not os.path.exists(r):
        shutil.copy(p, r)
    return np.array(Image.open(r).convert('RGBA'))


def main():
    for links, rechts in PAARE:
        A, B = roh(links), roh(rechts)
        lab, n = komponenten(B)
        stuecke = [k for k in range(1, n + 1) if (lab == k)[:, 0].any() and (lab == k).sum() < 0.25 * (lab > 0).sum()]
        if not stuecke:
            print('kein Reststueck:', rechts); continue
        m = np.isin(lab, stuecke)
        ys, xs = np.nonzero(m)
        frag = np.zeros((ys.max() - ys.min() + 1, xs.max() + 1, 4), np.uint8)
        frag[ys - ys.min(), xs] = B[ys, xs]
        # Reststueck aus dem rechten Kandidaten entfernen und neu zuschneiden
        B2 = B.copy(); B2[m] = 0
        bb = Image.fromarray(B2).getbbox()
        Image.fromarray(B2).crop(bb).save(os.path.join(OBJ, rechts + '.png'))
        # Hoehe per Kantenabgleich: rechte Kante von A gegen linke Kante des Stuecks
        ka = A[:, -1, 3] > 0
        kf = frag[:, 0, 3] > 0
        best, dy = -1, 0
        for d in range(-frag.shape[0], A.shape[0]):
            s = 0
            for i in np.nonzero(kf)[0]:
                if 0 <= i + d < A.shape[0] and ka[i + d]:
                    s += 1
            if s > best:
                best, dy = s, d
        y0 = min(0, dy); hoehe = max(A.shape[0], dy + frag.shape[0]) - y0
        neu = np.zeros((hoehe, A.shape[1] + frag.shape[1], 4), np.uint8)
        neu[-y0:-y0 + A.shape[0], :A.shape[1]] = A
        fy = dy - y0
        sub = neu[fy:fy + frag.shape[0], A.shape[1]:]
        sub[frag[..., 3] > 0] = frag[frag[..., 3] > 0]
        Image.fromarray(neu).save(os.path.join(OBJ, links + '.png'))
        print('repariert:', links, '+', frag.shape[1], 'px aus', rechts, 'dy', dy, 'Treffer', best)


if __name__ == '__main__':
    main()
