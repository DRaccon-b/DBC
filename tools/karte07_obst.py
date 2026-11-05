"""Digitale Anbaufruechte fuer Karte 07: PixelLab-Fruechte (assets/objekte/karte07/obst) verkleinern und
nur die Fruechte digital machen (Voxel-Raster, cyanfarbene Kontur, Pixel-Glanz). Blaetter bleiben natuerlich.

  python3 tools/karte07_obst.py   -> assets/objekte/karte07/frucht/*.png
"""
import os
import numpy as np
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
QUELLE = os.path.join(ROOT, 'assets', 'objekte', 'karte07', 'obst')
ZIEL = os.path.join(ROOT, 'assets', 'objekte', 'karte07', 'frucht')
# name: (quelle, faktor)
SORTEN = {'kuerbis': (0, 0.55), 'kohl': (1, 0.5), 'tomate': (2, 0.55), 'mais': (3, 0.6), 'karotte': (4, 0.5),
          'erdbeere': (5, 0.5), 'aubergine': (6, 0.55), 'melone': (7, 0.55), 'zwiebel': (12, 0.5),
          'heidelbeere': (13, 0.5), 'weizen': (15, 0.55), 'trauben': (11, 0.75),
          'apfelbaum': (8, 1.0), 'orangenbaum': (9, 1.0), 'kirschbusch': (10, 0.8)}
CYAN = np.array([95, 240, 255], np.float32)


def frucht_maske(a):
    r, g, b = [a[..., i].astype(int) for i in range(3)]
    mx = np.maximum(np.maximum(r, g), b); mn = np.minimum(np.minimum(r, g), b)
    gruen = (g >= r - 5) & (g >= b - 5)
    braun = (r > g) & (g > b) & (r - b < 90) & (r < 160)            # Stiele/Holz
    m = (a[..., 3] > 0) & ~gruen & ~braun & (mx - mn > 55) & (mx > 110)
    # nur zusammenhaengende Fruchtflaechen (mind. 2 Nachbarn)
    n = sum(np.roll(np.roll(m, dy, 0), dx, 1) for dy in (-1, 0, 1) for dx in (-1, 0, 1)) - m
    return m & (n >= 3)


def digital(sp):
    a = np.array(sp).astype(np.float32)
    m = frucht_maske(a.astype(np.uint8))
    if m.sum() < 6:                                                  # Kohl, Weizen, Zwiebel: schon digital
        return sp
    yy, xx = np.mgrid[0:a.shape[0], 0:a.shape[1]]
    raster = m & ((yy % 3 == 0) | (xx % 3 == 0))                     # Voxel-Fugen
    a[raster, :3] *= 0.82
    rand = m & ~(np.roll(m, 1, 0) & np.roll(m, -1, 0) & np.roll(m, 1, 1) & np.roll(m, -1, 1))
    unten = rand & ~np.roll(m, -1, 0)                                # Datenkontur unten/rechts
    a[unten, :3] = a[unten, :3] * 0.4 + CYAN * 0.6
    glanz = m & ~np.roll(m, 1, 0) & ~np.roll(m, 1, 1)
    a[np.roll(np.roll(glanz, 1, 0), 1, 1) & m, :3] = 255             # Pixel-Glanz oben links
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


if __name__ == '__main__':
    os.makedirs(ZIEL, exist_ok=True)
    for name, (i, f) in SORTEN.items():
        sp = Image.open(os.path.join(QUELLE, '%02d.png' % i)).convert('RGBA')
        sp = sp.crop(sp.getbbox())
        if f != 1.0:
            sp = sp.resize((max(1, round(sp.width * f)), max(1, round(sp.height * f))), Image.NEAREST)
        al = np.array(sp)
        al[..., 3] = np.where(al[..., 3] >= 128, 255, 0)
        sp = digital(Image.fromarray(al))
        sp = sp.crop(sp.getbbox())
        sp.save(os.path.join(ZIEL, name + '.png'))
        print(name, sp.size)
