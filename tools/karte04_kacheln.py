"""16x16-Grundkacheln fuer Karte 04 (Gear Savanna).

  python3 tools/karte04_kacheln.py   ->  assets/karte04/basis/<art>_<v>.png, vorschau.png

Wiederverwendung: Gras- und Sandkacheln aus Karte 01 (assets/basis) werden ueber ihre Farbrampe auf die
Savannentoene umgefaerbt -> gleiche saubere Struktur, neue Palette. Teer, Asche und Furt prozedural.
  s Savanne (gelbes Trockengras)  g Plateau (blasses Gruen)  d Olivgras  e rote Erde  w Weg
  c Canyonboden  f Furt/Kies  m Schlamm  a Asche  t Teer
"""
import os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image
import basis_kacheln as k1

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
OUT = os.path.join(ROOT, 'assets', 'karte04', 'basis')
H = lambda h: tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))

GRAS_RAMPE = ['g0', 'g1', 'g2', 'g3', 'g4', 'g5']
SAND_RAMPE = ['s0', 's1', 's2', 's3', 's4']
RAMPEN = {
    # aus Gras: 6 Toene dunkel -> hell
    's': ('gras', ['#7a6430', '#957c3e', '#ad944e', '#c4aa60', '#d6bc70', '#e8d08a']),
    'g': ('gras', ['#66783e', '#82924e', '#9aa95e', '#afbd70', '#c2ce82', '#d6df9a']),
    'd': ('gras', ['#57552f', '#6e6c3d', '#84814b', '#99955b', '#ada86b', '#c1bb80']),
    # aus Sand: 5 Toene
    'e': ('sand', ['#7e5234', '#9a6844', '#b07c56', '#c08e66', '#d2a47c']),
    'w': ('sand', ['#94744a', '#aa8a5c', '#bb9c6a', '#c9ac7a', '#dac094']),
    'c': ('sand', ['#6a5034', '#826646', '#977c58', '#a88c66', '#bca27e']),
    'm': ('sand', ['#4e4136', '#64554a', '#7a6a5c', '#8c7e6e', '#a29684']),
    'a': ('sand', ['#55554c', '#69695e', '#7c7c70', '#8e8e80', '#a4a496']),
}


def umfaerben(im, quelle, ziel):
    q = [k1.RGB[k] for k in quelle]
    z = [H(h) for h in ziel]
    px = im.load()
    for y in range(16):
        for x in range(16):
            c = px[x, y][:3]
            i = min(range(len(q)), key=lambda j: sum((c[k] - q[j][k]) ** 2 for k in range(3)))
            px[x, y] = z[i]
    return im


def kachel(art, v):
    if art in RAMPEN:
        typ, ziel = RAMPEN[art]
        if typ == 'gras':
            im = umfaerben(k1.gras(v).convert('RGB'), GRAS_RAMPE, ziel)
        else:
            im = umfaerben(k1.sand(v).convert('RGB'), SAND_RAMPE, ziel)
        r = random.Random(400 + v + ord(art))
        if art == 's':                                      # trockene Halme: kurze helle Striche
            for _ in range(2):
                x, y = r.randint(0, 15), r.randint(0, 13)
                im.putpixel((x, y), H('#f0dc9a')); im.putpixel((x, y + 1), H('#c4aa60'))
        if art == 'c':                                      # Kiesel im Canyon
            for _ in range(2):
                x, y = r.randint(1, 14), r.randint(1, 14)
                im.putpixel((x, y), H('#c8b494')); im.putpixel((x + 1, y + 1), H('#5e4630'))
        if art == 'm':                                      # nasse Flecken
            for _ in range(2):
                x, y = r.randint(0, 14), r.randint(0, 15)
                im.putpixel((x, y), H('#3e342c')); im.putpixel((x + 1, y), H('#3e342c'))
        return im
    r = random.Random(500 + v + ord(art))
    if art == 't':                                          # Teer: fast schwarz, oeliger Schimmer
        im = Image.new('RGB', (16, 16), H('#24222c'))
        for _ in range(3):
            x, y = r.randint(0, 15), r.randint(0, 15)
            for dx in range(r.randint(2, 4)):
                im.putpixel(((x + dx) % 16, y), H('#2e2c38'))
        for _ in range(2):
            x, y = r.randint(0, 15), r.randint(0, 15)
            im.putpixel((x, y), H('#4a4658')); im.putpixel(((x + 1) % 16, y), H('#3a3846'))
        return im
    if art == 'f':                                          # Furt: heller, festgetretener Kies
        im = umfaerben(k1.sand(v).convert('RGB'), SAND_RAMPE, ['#8a7254', '#a28a68', '#b49c78', '#c4ae8a', '#d6c4a2'])
        for _ in range(4):
            x, y = r.randint(0, 14), r.randint(0, 14)
            im.putpixel((x, y), H('#e2d4b8')); im.putpixel((x + 1, y), H('#c4b090'))
            im.putpixel((x, y + 1), H('#7e6a50')); im.putpixel((x + 1, y + 1), H('#6a5842'))
        return im
    raise ValueError(art)


ARTEN = 'sgdewcfmat'


def main():
    os.makedirs(OUT, exist_ok=True)
    vor = Image.new('RGB', (len(ARTEN) * 64 + (len(ARTEN) - 1) * 4, 64), (0, 0, 0))
    for i, art in enumerate(ARTEN):
        ks = [kachel(art, v) for v in range(5)]
        for v, k in enumerate(ks):
            k.save(os.path.join(OUT, '%s_%d.png' % (art, v)))
        for yy in range(4):
            for xx in range(4):
                vor.paste(ks[(xx * 3 + yy * 2) % 5], (i * 68 + xx * 16, yy * 16))
    vor.resize((vor.width * 3, vor.height * 3), Image.NEAREST).save(os.path.join(OUT, 'vorschau.png'))
    print('Kacheln ->', OUT)


if __name__ == '__main__':
    main()
