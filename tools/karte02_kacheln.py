"""Handgezeichnete 16x16-Grundkacheln fuer Karte 02 (Factorial Town).

  python3 tools/karte02_kacheln.py

Gleiche Regeln wie Karte 01 (tools/basis_kacheln.py): kontrastarme Textur, Licht von oben links,
kuehle Industrietoene mit Hue-Shifting (Schatten blaeulich, Licht leicht warm).
Ausgabe: assets/karte02/basis/<art>_<variante>.png und vorschau.png
  beton_<px><py>_<v>  Betonplatten 2x2 Kacheln (px, py = Position in der Platte), 3 Varianten
  asphalt_<v>, gehweg_<v>, platz_<v>, platz_hell_<v>, metall_<v>   je 5 Varianten
"""
import os, random
from PIL import Image

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets', 'karte02', 'basis')
VARIANTEN = 5


def hexrgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


PAL = {
    # Beton: kuehles Grau, Schatten blaeulich, Licht leicht warm
    'b0': '#4a555f', 'b1': '#5f6b75', 'b2': '#76828b', 'b3': '#86929a', 'b4': '#98a3aa', 'b5': '#b0b9be',
    # Asphalt
    'a0': '#262b33', 'a1': '#30363e', 'a2': '#3a4049', 'a3': '#474e58', 'a4': '#5a626c',
    # Gehweg (helle Pflastersteine)
    'g0': '#7e8a92', 'g1': '#929da4', 'g2': '#a5afb5', 'g3': '#b6bfc4', 'g4': '#c8cfd3',
    # Platz (helle, leicht tuerkise Fliesen)
    'p0': '#62777f', 'p1': '#748990', 'p2': '#869ba2', 'p3': '#97acb2', 'p4': '#aebfc4',
    # Metallboden (dunkle Paneele)
    'm0': '#1a2830', 'm1': '#22343e', 'm2': '#2b4150', 'm3': '#365062', 'm4': '#476577', 'm5': '#5d7f92',
}
RGB = {k: hexrgb(v) for k, v in PAL.items()}


def px(im, x, y, f):
    im.putpixel((x % 16, y % 16), RGB[f])


def beton(pos_x, pos_y, v):
    """Teil (pos_x, pos_y) einer 32x32-Betonplatte: Fuge oben/links an der Plattenkante."""
    r = random.Random(1000 + v * 7 + pos_x * 3 + pos_y)
    im = Image.new('RGB', (16, 16), RGB['b3'])
    # sehr sanfte Flecken
    for _ in range(3):
        x0, y0 = r.randint(0, 15), r.randint(0, 15)
        f = r.choice(('b2', 'b4'))
        for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1), (2, 0)):
            px(im, x0 + dx, y0 + dy, f)
    for _ in range(5):
        px(im, r.randint(0, 15), r.randint(0, 15), r.choice(('b2', 'b4', 'b2')))
    if v == 0 and r.random() < 0.5:            # kleiner Haarriss
        x, y = r.randint(3, 11), r.randint(3, 11)
        for k in range(4):
            px(im, x + k, y + (k // 2), 'b1')
    # Fugen an der Plattenkante (Licht von oben links: dunkle Fuge, helle Kante danach)
    if pos_y == 0:
        for x in range(16):
            px(im, x, 0, 'b1'); px(im, x, 1, 'b5')
    if pos_x == 0:
        for y in range(16):
            px(im, 0, y, 'b1'); px(im, 1, y, 'b4' if y > 1 or pos_y else 'b1')
    return im


def asphalt(v):
    r = random.Random(2000 + v)
    im = Image.new('RGB', (16, 16), RGB['a1'])
    for _ in range(10):
        px(im, r.randint(0, 15), r.randint(0, 15), r.choice(('a0', 'a2', 'a2', 'a0')))
    if r.random() < 0.5:
        px(im, r.randint(0, 15), r.randint(0, 15), 'a3')
    return im


def gehweg(v):
    """Pflastersteine 8x4, versetzt verlegt."""
    r = random.Random(3000 + v)
    im = Image.new('RGB', (16, 16), RGB['g2'])
    for zeile in range(4):
        y0 = zeile * 4
        versatz = 4 if zeile % 2 else 0
        for stein in range(-1, 3):
            x0 = stein * 8 + versatz
            ton = r.choice(('g2', 'g2', 'g2', 'g3'))
            for y in range(y0, y0 + 4):
                for x in range(x0, x0 + 8):
                    if 0 <= x < 16:
                        k, l = y - y0, x - x0
                        c = 'g1' if k == 3 or l == 7 else 'g3' if (k == 0 or l == 0) and ton != 'g3' else ton
                        px(im, x, y, c)
    return im


def platz(v, hell=False):
    r = random.Random(4000 + v + (50 if hell else 0))
    base, licht, fuge, fleck = (('p3', 'p4', 'p1', 'p2') if hell else ('p2', 'p3', 'p0', 'p1'))
    im = Image.new('RGB', (16, 16), RGB[base])
    for x in range(16):
        px(im, x, 0, fuge); px(im, x, 1, licht)
    for y in range(16):
        px(im, 0, y, fuge); px(im, 1, y, licht if y > 0 else fuge)
    for _ in range(4):
        px(im, r.randint(2, 15), r.randint(2, 15), fleck)
    return im


def metall(v):
    """Dunkles Bodenpaneel mit Kante (Licht oben links), Nieten, gelegentlich Lueftungsschlitz."""
    r = random.Random(5000 + v)
    im = Image.new('RGB', (16, 16), RGB['m2'])
    for i in range(16):
        px(im, i, 0, 'm0'); px(im, 0, i, 'm0')
        px(im, i, 1, 'm4'); px(im, 1, i, 'm3' if i > 1 else 'm4')
        px(im, i, 15, 'm1'); px(im, 15, i, 'm1')
    for (x, y) in ((3, 3), (12, 3), (3, 12), (12, 12)):
        px(im, x, y, 'm5'); px(im, x + 1, y + 1, 'm1')
    if v in (1, 3):                                 # Schlitz wie in der Vorlage
        for x in range(6, 11):
            px(im, x, 8, 'm0'); px(im, x, 9, 'm4')
    for _ in range(3):
        px(im, r.randint(2, 14), r.randint(2, 14), r.choice(('m1', 'm3')))
    return im


def main():
    os.makedirs(OUT, exist_ok=True)
    k = {}
    for v in range(3):
        for pxp in (0, 1):
            for pyp in (0, 1):
                k['beton_%d%d_%d' % (pxp, pyp, v)] = beton(pxp, pyp, v)
    for v in range(VARIANTEN):
        k['asphalt_%d' % v] = asphalt(v)
        k['gehweg_%d' % v] = gehweg(v)
        k['platz_%d' % v] = platz(v)
        k['platz_hell_%d' % v] = platz(v, hell=True)
        k['metall_%d' % v] = metall(v)
    for n, im in k.items():
        im.save(os.path.join(OUT, n + '.png'))
    # Vorschau: je Art eine 6x6-Flaeche
    arten = ['beton', 'asphalt', 'gehweg', 'platz', 'platz_hell', 'metall']
    rnd = random.Random(1)
    v = Image.new('RGB', (16 * 6 * len(arten) + 8 * (len(arten) - 1), 16 * 6), (0, 0, 0))
    for i, a in enumerate(arten):
        for y in range(6):
            for x in range(6):
                if a == 'beton':
                    t = k['beton_%d%d_%d' % (x % 2, y % 2, rnd.randrange(3))]
                else:
                    t = k['%s_%d' % (a, rnd.randrange(VARIANTEN))]
                v.paste(t, (i * (96 + 8) + x * 16, y * 16))
    v.resize((v.width * 3, v.height * 3), Image.NEAREST).save(os.path.join(OUT, 'vorschau.png'))


if __name__ == '__main__':
    main()
