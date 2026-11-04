"""Neue 16x16-Grundkacheln fuer Karte 03 (Server Desert). Sand, Gras und Wasser kommen aus Karte 01
(assets/basis), damit auch deren Wang-Uebergaenge (gras_weg, wasser_sand, wasser_gras) passen.

  python3 tools/karte03_kacheln.py   ->  assets/karte03/basis/<art>_<v>.png, vorschau.png
  weg (festgefahrener Sand), kies (Pflaster aus Feldsteinen), platz (blaugraue Ziegel), lehm (rissiger
  Lehm), duene (heller Duenensand mit Rippeln)
"""
import os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image
import basis_kacheln as k1

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets', 'karte03', 'basis')
H = lambda h: tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))
PAL = {
    'w0': '#a4784c', 'w1': '#bb8f5e', 'w2': '#cba06c', 'w3': '#d6ae7a', 'w4': '#e2c08e',
    'k0': '#7d7466', 'k1': '#958b7a', 'k2': '#aca18c', 'k3': '#c2b69e', 'k4': '#d6cbb2',
    'p0': '#4a5068', 'p1': '#5c6380', 'p2': '#6e7694', 'p3': '#828aa8', 'p4': '#9aa2bc',
    'l0': '#4a2a1e', 'l1': '#6e3c28', 'l2': '#8f5234', 'l3': '#a8643e', 'l4': '#c07a4e',
    'd0': '#e2c890', 'd1': '#ecd6a4', 'd2': '#f4e4bc', 'd3': '#faeed0', 'd4': '#fff8e6',
}
RGB = {k: H(v) for k, v in PAL.items()}


def px(im, x, y, f):
    im.putpixel((x % 16, y % 16), RGB[f])


def weg(v):
    r = random.Random(100 + v)
    im = Image.new('RGB', (16, 16), RGB['w2'])
    for _ in range(3):
        x, y = r.randint(0, 15), r.randint(0, 15)
        for dx, dy in ((0, 0), (1, 0), (2, 0), (1, 1)):
            px(im, x + dx, y + dy, r.choice(('w1', 'w3')))
    for _ in range(4):
        px(im, r.randint(0, 15), r.randint(0, 15), r.choice(('w1', 'w4', 'w0')))
    return im


def kies(v):
    """Feldsteinpflaster: vier groessere, gerundete Steine je Kachel, dunkle Fugen, Licht oben links."""
    r = random.Random(200 + v)
    im = Image.new('RGB', (16, 16), RGB['k0'])
    steine = [(4, 4), (12, 4), (8, 12), (0, 12)] if v % 2 else [(4, 4), (12, 4), (4, 12), (12, 12)]
    for (cx, cy) in steine:
        cx += r.randint(-1, 1); cy += r.randint(-1, 1)
        rx, ry = r.choice((3.8, 4.2)), r.choice((3.6, 4.0))
        ton = r.choice(('k2', 'k2', 'k3'))
        for dy in range(-5, 6):
            for dx in range(-5, 6):
                d = (dx / rx) ** 2 + (dy / ry) ** 2
                if d <= 1:
                    c = ton
                    if d > 0.55 and dx + dy < 0:
                        c = 'k4' if ton == 'k3' else 'k3'
                    elif d > 0.55 and dx + dy > 1:
                        c = 'k1'
                    px(im, cx + dx, cy + dy, c)
    for _ in range(3):
        px(im, r.randint(0, 15), r.randint(0, 15), 'k0')
    return im


def platz(v):
    """Blaugraue Ziegel 8x4 im Verband (wie der Gehweg aus Karte 02, kuehler)."""
    r = random.Random(300 + v)
    im = Image.new('RGB', (16, 16), RGB['p2'])
    for zeile in range(4):
        y0 = zeile * 4
        vers = 4 if zeile % 2 else 0
        for st in range(-1, 3):
            x0 = st * 8 + vers
            ton = r.choice(('p2', 'p2', 'p3', 'p1'))
            for y in range(y0, y0 + 4):
                for x in range(x0, x0 + 8):
                    if 0 <= x < 16:
                        k, l = y - y0, x - x0
                        c = 'p0' if k == 3 or l == 7 else 'p4' if (k == 0 and ton == 'p3') else ton
                        px(im, x, y, c)
    return im


def lehm(v):
    """Rissiger Lehmboden: Schollen mit dunklen Rissen."""
    r = random.Random(400 + v)
    im = Image.new('RGB', (16, 16), RGB['l2'])
    for y in range(16):
        for x in range(16):
            if r.random() < 0.12:
                px(im, x, y, r.choice(('l3', 'l1')))
    x, y = r.randint(0, 15), 0
    for _ in range(18):
        px(im, x, y, 'l0'); px(im, x, y + 1, 'l3')
        x += r.choice((-1, 0, 1)); y += 1
    y, x = r.randint(0, 15), 0
    for _ in range(18):
        px(im, x, y, 'l0'); px(im, x + 1, y, 'l1')
        y += r.choice((-1, 0, 1)); x += 1
    return im


def duene(v):
    """Heller Duenensand mit weichen Windrippeln."""
    r = random.Random(500 + v)
    im = Image.new('RGB', (16, 16), RGB['d2'])
    for k in range(2):
        y0 = (v * 3 + k * 8) % 16
        for x in range(16):
            y = y0 + (1 if (x // 4) % 2 else 0)
            px(im, x, y, 'd1'); px(im, x, y + 1, 'd3')
    for _ in range(4):
        px(im, r.randint(0, 15), r.randint(0, 15), r.choice(('d1', 'd4')))
    return im


def main():
    os.makedirs(OUT, exist_ok=True)
    arten = {'weg': weg, 'kies': kies, 'platz': platz, 'lehm': lehm, 'duene': duene}
    for n, f in arten.items():
        for v in range(5):
            f(v).save(os.path.join(OUT, '%s_%d.png' % (n, v)))
    rnd = random.Random(1)
    vor = Image.new('RGB', (6 * 96 + 5 * 8, 96))
    for i, n in enumerate(['weg', 'kies', 'platz', 'lehm', 'duene', 'sand']):
        for y in range(6):
            for x in range(6):
                if n == 'sand':
                    t = Image.open(os.path.join(k1.OUT, 'sand_%d.png' % rnd.randrange(5)))
                else:
                    t = Image.open(os.path.join(OUT, '%s_%d.png' % (n, rnd.randrange(5))))
                vor.paste(t, (i * 104 + x * 16, y * 16))
    vor.resize((vor.width * 3, vor.height * 3), Image.NEAREST).save(os.path.join(OUT, 'vorschau.png'))


if __name__ == '__main__':
    main()
