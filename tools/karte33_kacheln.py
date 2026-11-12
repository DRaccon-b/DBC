"""16x16-Grundkacheln fuer Karte 33 (The World of Dreams): umgefaerbte Schlossplatten von Karte 09/32.

  python3 tools/karte33_kacheln.py   ->  assets/karte33/basis/<art>_<v>.png, vorschau.png

  i lavendelfarbene Platten  r heller Randstein  m dunklere Ringplatten mit feiner Raute  p Steg (Laengsbohlen)
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
K32 = os.path.join(ROOT, 'assets', 'karte32', 'basis')
OUT = os.path.join(ROOT, 'assets', 'karte33', 'basis')


def ton(im, dunkel, hell):
    a = np.array(im.convert('RGB')).astype(np.float32)
    l = a @ np.array([0.3, 0.59, 0.11], np.float32)
    t = np.clip((l - l.min()) / max(1.0, l.max() - l.min()), 0, 1)[..., None]
    out = np.array(dunkel, np.float32) * (1 - t) + np.array(hell, np.float32) * t
    return Image.fromarray(out.astype(np.uint8))


def main():
    os.makedirs(OUT, exist_ok=True)
    for v in range(5):
        i = Image.open(os.path.join(K32, 'i_%d.png' % v))
        ton(i, (132, 124, 168), (200, 194, 226)).save(os.path.join(OUT, 'i_%d.png' % v))
        ton(i, (160, 154, 196), (226, 222, 242)).save(os.path.join(OUT, 'r_%d.png' % v))
        m = ton(i, (96, 98, 140), (156, 156, 196))
        px = m.load()
        for y in range(16):
            for x in range(16):
                if (x + y) % 8 == 4 or (x - y) % 8 == 4:
                    c = px[x, y]
                    px[x, y] = (min(255, c[0] + 14), min(255, c[1] + 14), min(255, c[2] + 20))
        m.save(os.path.join(OUT, 'm_%d.png' % v))
        p = Image.new('RGB', (16, 16))
        q = p.load()
        rs = np.random.RandomState(330 + v)
        for x in range(16):
            for y in range(16):
                base = (186, 180, 214) if (x // 4) % 2 == 0 else (176, 170, 206)
                n = rs.randint(-4, 5)
                c = tuple(max(0, min(255, b + n)) for b in base)
                if x % 4 == 3:
                    c = (124, 118, 160)                         # Fuge zwischen den Bohlen
                elif x % 4 == 0:
                    c = tuple(min(255, b + 18) for b in base)   # Lichtkante (Licht von links)
                q[x, y] = c
        p.save(os.path.join(OUT, 'p_%d.png' % v))
    arten = 'irmp'
    vor = Image.new('RGB', (len(arten) * 68, 64))
    for n, art in enumerate(arten):
        for yy in range(4):
            for xx in range(4):
                vor.paste(Image.open(os.path.join(OUT, '%s_%d.png' % (art, (xx * 3 + yy * 2) % 5))),
                          (n * 68 + xx * 16, yy * 16))
    vor.resize((vor.width * 3, vor.height * 3), Image.NEAREST).save(os.path.join(OUT, 'vorschau.png'))
    print('Kacheln ->', OUT)


if __name__ == '__main__':
    main()
