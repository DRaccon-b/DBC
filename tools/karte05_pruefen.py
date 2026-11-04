"""Prueft die Objektplatzierung von Karte 05 gegen die Hoehenkarte (maps/karte05/pixelhoehe.npy).

Je Objekt: Fuss muss auf Schneefeld (1) oder Plateau (2) stehen; der untere Teil des Sprites (unterste 35 %)
und ein Streifen von 6 px unter dem Fuss muessen vollstaendig auf derselben Ebene liegen (sonst ragt das
Objekt ueber eine Kante, steht in einer Wand, im Wasser oder in einer Spalte).
"""
import json, os
import numpy as np
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte05')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte05')
NAMEN = {0: 'Wasser', 1: 'Schneefeld', 2: 'Plateau', 8: 'Spalte', 9: 'Klippenwand'}


def bewerten(lvl, sp_alpha, x, y):
    """-> (ok, Grund). sp_alpha: bool-Array des Sprites, (x, y) linke obere Ecke."""
    Hh, W = lvl.shape
    a = sp_alpha
    zeilen = np.nonzero(a.any(axis=1))[0]
    zu = int(zeilen.max())
    fuss = np.nonzero(a[max(0, zu - 2):zu + 1].any(axis=0))[0]
    fx = x + int((fuss.min() + fuss.max()) // 2); fy = y + zu + 1
    if not (0 <= fx < W and 0 <= fy < Hh):
        return False, 'ausserhalb der Karte'
    ebene = lvl[fy, fx]
    if ebene not in (1, 2):
        return False, 'Fuss auf %s' % NAMEN.get(int(ebene), ebene)
    unten = int(zu - (zu - zeilen.min()) * 0.35)
    ys, xs = np.nonzero(a[unten:zu + 1])
    ys, xs = ys + y + unten, xs + x
    ok = (ys >= 0) & (ys < Hh) & (xs >= 0) & (xs < W)
    if (~ok).any():
        return False, 'ragt aus der Karte'
    fremd = lvl[ys, xs] != ebene
    if fremd.mean() > 0.03:
        arten = sorted({NAMEN.get(int(v), v) for v in lvl[ys, xs][fremd]})
        return False, 'unterer Teil ueber %s' % '/'.join(arten)
    for dy in range(1, 7):
        yy = fy + dy
        if yy >= Hh:
            break
        xs_ = np.arange(x + fuss.min(), x + fuss.max() + 1)
        xs_ = xs_[(xs_ >= 0) & (xs_ < W)]
        if (lvl[yy, xs_] != ebene).mean() > 0.2:
            return False, 'Fuss direkt an einer Kante (%s darunter)' % NAMEN.get(int(lvl[yy, xs_][lvl[yy, xs_] != ebene][0]), '?')
    return True, ''


def main():
    lvl = np.load(os.path.join(KARTE, 'pixelhoehe.npy'))
    objs = json.load(open(os.path.join(OBJ, 'platzierung.json')))
    fehler = []
    for o in objs:
        a = np.array(Image.open(os.path.join(OBJ, o['datei'])).getchannel('A')) >= 128
        ok, grund = bewerten(lvl, a, o['x'], o['y'])
        if not ok:
            fehler.append((o['basis'], o['kachel'], grund))
    from collections import Counter
    print(len(objs), 'Objekte,', len(fehler), 'Probleme')
    print(Counter(g.split(' (')[0] for _, _, g in fehler))
    for f in fehler:
        if not f[0].startswith('klein/') and not f[0] in ('klein/27', 'klein/49'):
            print(' ', f)


if __name__ == '__main__':
    main()
