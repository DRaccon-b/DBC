"""Rundturm (Karte 10, PixelLab k10_schloss2/02) ohne Tuer: die Tuer unten in der Mitte wird durch Mauerwerk
ersetzt - Ziegel aus dem Band ueber dem untersten Goldring, der unterste Goldring laeuft rundherum weiter (Form
vom Ring darueber, um den Ringabstand nach unten versetzt), unten die Sockelkontur wie an den Seiten.

  python3 tools/turm_ohne_tuer.py   ->  assets/objekte/karte10/schloss2/02_ohne_tuer.png
"""
import os
import numpy as np
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
QUELLE = os.path.join(ROOT, 'assets', 'objekte', 'karte10', 'schloss2', '02.png')
ZIEL = os.path.join(ROOT, 'assets', 'objekte', 'karte10', 'schloss2', '02_ohne_tuer.png')


def ohne_tuer(sp):
    """Tuerbereich (Mitte unten) durch das Mauerstueck genau einen Ringabstand darueber ersetzen: dort liegen
    Ziegel und der naechste Goldring in derselben Rundung - so laeuft der unterste Ring rundherum weiter.
    Die unterste Konturzeile wird von der Seite uebernommen."""
    a = np.array(sp.convert('RGBA'))
    ai = a.astype(int)
    h, w = a.shape[:2]
    gold = (ai[..., 3] > 0) & (ai[..., 0] > 200) & (ai[..., 1] > 130) & (ai[..., 2] < 120)
    mitte = w // 2
    g = np.nonzero(gold[:, mitte])[0]
    baender = []
    for y in g:
        if baender and y - baender[-1][1] <= 2:
            baender[-1][1] = y
        else:
            baender.append([y, y])
    P = baender[-1][0] - baender[-2][0]                      # Ringabstand
    x0, x1 = int(w * 0.25), int(w * 0.76)
    y0 = baender[-1][1] + 2                                  # unter dem untersten sichtbaren Ring
    unten = int(np.nonzero(a[:, mitte, 3])[0].max())
    out = a.copy()
    for y in range(y0, unten + 1):
        out[y, x0:x1 + 1] = a[y - P, x0:x1 + 1]
    out[unten, x0:x1 + 1] = a[unten, x0 - 1]
    out[unten - 1, x0:x1 + 1] = a[unten - 1, x0 - 1]
    return Image.fromarray(out)


if __name__ == '__main__':
    t = ohne_tuer(Image.open(QUELLE))
    t.save(ZIEL)
    sp = Image.open(QUELLE).convert('RGBA')
    w, h = t.size
    bg = Image.new('RGBA', (w * 2 + 4, h), (110, 180, 80, 255))
    bg.alpha_composite(sp, (0, 0)); bg.alpha_composite(t, (w + 4, 0))
    bg.crop((0, 60, w * 2 + 4, h)).resize(((w * 2 + 4) * 6, (h - 60) * 6), 0).save(
        os.path.join(ROOT, 'assets', 'objekte', 'karte10', 'schloss2', 'vergleich_ohne_tuer.png'))
    print('Turm ohne Tuer ->', ZIEL)
