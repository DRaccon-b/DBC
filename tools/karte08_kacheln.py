"""16x16-Grundkacheln fuer Karte 08 (Overdell).

  python3 tools/karte08_kacheln.py   ->  assets/karte08/basis/<art>_<v>.png, vorschau.png

Wiederverwendung: Gras- und Sandkacheln aus Karte 01 (assets/basis), ueber ihre Farbrampe in gedeckte,
duestere Toene umgefaerbt. Kopfsteinplatz (q) und Schlossplatz (k) bekommen zusaetzlich Steinfugen.
  g Gras  h dunkles Gras  w Steinweg  e Graberde  q Kopfsteinplatz  m Schlamm  f Terrassenboden
  a ausgetretener Terrassenboden  k Schlossplatz  r Geroellfeld (schwarzer Fels)
"""
import os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image
import basis_kacheln as k1
from karte04_kacheln import umfaerben, GRAS_RAMPE, SAND_RAMPE

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
OUT = os.path.join(ROOT, 'assets', 'karte08', 'basis')
H = lambda h: tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))
RAMPEN = {
    'g': ('gras', ['#2e3524', '#3a432c', '#465034', '#525d3c', '#5f6a46', '#6d7852']),
    'h': ('gras', ['#22281c', '#2b3222', '#343c28', '#3e462e', '#485236', '#545e40']),
    'w': ('sand', ['#55566a', '#62637a', '#6f7086', '#7c7d92', '#8c8da0']),
    'e': ('sand', ['#2e231d', '#3a2c24', '#46362c', '#524034', '#604c3e']),
    'q': ('sand', ['#3a3f52', '#454b60', '#50566c', '#5c6278', '#6a7086']),
    'm': ('sand', ['#26231c', '#2f2b22', '#38332a', '#423c31', '#4e473a']),
    'f': ('sand', ['#4a4f5e', '#545a6a', '#5f6576', '#6a7082', '#777d8e']),
    'a': ('sand', ['#62656f', '#6d707a', '#787b85', '#848790', '#91949c']),
    'k': ('sand', ['#2a2634', '#332e3e', '#3c3748', '#464052', '#524b5e']),
    'r': ('sand', ['#1a1a26', '#20202e', '#272736', '#2e2e40', '#37374a']),
}


def fugen(im, art, v):
    """Steinplatten: Kopfsteine (q) versetzt 8x5, Schlossplatz (k) grosse Platten 8x8 im Schachbrett."""
    px = im.load()
    if art == 'q':
        dunkel = H('#2c3040')
        for y in range(16):
            for x in range(16):
                reihe = y // 5
                if y % 5 == 4 or (x + (4 if reihe % 2 else 0) + v) % 8 == 7:
                    px[x, y] = dunkel
                elif y % 5 == 0 or (x + (4 if reihe % 2 else 0) + v) % 8 == 0:
                    r, g, b = px[x, y]
                    px[x, y] = (min(255, r + 14), min(255, g + 14), min(255, b + 16))
    elif art == 'k':
        for y in range(16):
            for x in range(16):
                r, g, b = px[x, y]
                if (x // 8 + y // 8) % 2:
                    px[x, y] = (max(0, r - 10), max(0, g - 10), max(0, b - 8))
                if x % 8 == 7 or y % 8 == 7:
                    px[x, y] = H('#1c1824')
                elif x % 8 == 0 or y % 8 == 0:
                    px[x, y] = (min(255, r + 12), min(255, g + 10), min(255, b + 14))


def kachel(art, v):
    typ, ziel = RAMPEN[art]
    if typ == 'gras':
        im = umfaerben(k1.gras(v).convert('RGB'), GRAS_RAMPE, ziel)
    else:
        im = umfaerben(k1.sand(v).convert('RGB'), SAND_RAMPE, ziel)
    r = random.Random(800 + v + ord(art))
    if art in 'qk':
        fugen(im, art, v)
    if art in 'fa':                                         # feine Risse im Fels
        if r.random() < 0.6:
            x, y = r.randint(2, 12), r.randint(2, 13)
            for d in range(4):
                im.putpixel(((x + d) % 16, (y + d // 2) % 16), H('#3e4250' if art == 'f' else '#545864'))
    if art == 'r':                                          # Geroell: kleine helle Kanten
        for _ in range(2):
            x, y = r.randint(1, 14), r.randint(1, 14)
            im.putpixel((x, y), H('#4a4a62'))
    return im


ARTEN = 'ghweqmfakr'


def main():
    os.makedirs(OUT, exist_ok=True)
    vor = Image.new('RGB', (len(ARTEN) * 68, 64), (0, 0, 0))
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
