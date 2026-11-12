"""16x16-Grundkacheln fuer Karte 32 (Dream Ruins).

  python3 tools/karte32_kacheln.py   ->  assets/karte32/basis/<art>_<v>.png, vorschau.png

Wiederverwendet (Karte 09): i Schloss-Steinplatten, c roter Teppich, v lila Teppich, g Friedhofsgras.
Neu: j Steinplatten dunkler (Seitenschiffe), o brauner Festsaal-Teppich mit goldenem Rautenmuster,
     p helles Friedhofspflaster (Platten 8x8 versetzt).
"""
import os, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image
import karte09_kacheln as k9

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
OUT = os.path.join(ROOT, 'assets', 'karte32', 'basis')
K9 = os.path.join(ROOT, 'assets', 'karte09', 'basis')
H = k9.H


def dunkler(im, f):
    return Image.eval(im, lambda v: int(v * f))


def teppich_braun(v):
    im = k9.kachel('c', v)
    px = im.load()
    for y in range(16):
        for x in range(16):
            r, g, b = px[x, y]
            l = (r + g + b) / 3
            px[x, y] = (int(34 + l * 0.75), int(16 + l * 0.36), int(6 + l * 0.1))
            if (x + y) % 8 == 0 or (x - y) % 8 == 0:              # goldenes Rautengitter
                px[x, y] = H('#7e4c22') if (x + y) % 2 == 0 else H('#6a3e1c')
            if (x % 8 == 4 and y % 8 == 0):
                px[x, y] = H('#b0783a')
    return im


def pflaster(v):
    im = k9.kachel('i', v)
    px = im.load()
    for y in range(16):
        for x in range(16):
            r, g, b = px[x, y]
            px[x, y] = (min(255, int(r * 1.12 + 6)), min(255, int(g * 1.12 + 8)), min(255, int(b * 1.06 + 6)))
    return im


def main():
    os.makedirs(OUT, exist_ok=True)
    for art in 'icvg':
        for v in range(5):
            shutil.copy(os.path.join(K9, '%s_%d.png' % (art, v)), os.path.join(OUT, '%s_%d.png' % (art, v)))
    for v in range(5):
        dunkler(Image.open(os.path.join(K9, 'i_%d.png' % v)).convert('RGB'), 0.82).save(os.path.join(OUT, 'j_%d.png' % v))
        teppich_braun(v).save(os.path.join(OUT, 'o_%d.png' % v))
        pflaster(v).save(os.path.join(OUT, 'p_%d.png' % v))
    arten = 'ijcvogp'
    vor = Image.new('RGB', (len(arten) * 68, 64))
    for i, art in enumerate(arten):
        ks = [Image.open(os.path.join(OUT, '%s_%d.png' % (art, v))) for v in range(5)]
        for yy in range(4):
            for xx in range(4):
                vor.paste(ks[(xx * 3 + yy * 2) % 5], (i * 68 + xx * 16, yy * 16))
    vor.resize((vor.width * 3, vor.height * 3), Image.NEAREST).save(os.path.join(OUT, 'vorschau.png'))
    print('Kacheln ->', OUT)


if __name__ == '__main__':
    main()
