"""16x16-Grundkacheln fuer Karte 10 (Toy Town).

  python3 tools/karte10_kacheln.py   ->  assets/karte10/basis/<art>_<v>.png, vorschau.png

Wiederverwendet: Gras der Karte 01 (unveraendert, hell und freundlich), Sand der Karte 01 als Sandweg und als
Grundlage aller umgefaerbten Flaechen. Pflaster/Platten bekommen ein Fugenraster wie Spielzeugbausteine:
  g Gras  s Sandweg  a Asphalt  p rosa Gehweg (Ziegel)  b blaues Pflaster (Schachbrett)  k Burghof (beige Platten)
  r rosa Rahmen  m Bahnhofskies  q Bahnsteig (rosa Platten)  e Beeterde
"""
import os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image
import basis_kacheln as k1
from karte04_kacheln import umfaerben, SAND_RAMPE

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
OUT = os.path.join(ROOT, 'assets', 'karte10', 'basis')
H = lambda h: tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))
RAMPEN = {
    'a': ['#5e6474', '#686e80', '#727a8c', '#7c8496', '#8a92a2'],
    'p': ['#b0707c', '#c08490', '#cc96a0', '#d8a6ae', '#e4b8be'],
    'b': ['#7c9aae', '#88a6b8', '#94b2c2', '#a2bece', '#b2cad8'],
    'k': ['#ae9068', '#bc9e76', '#c8aa82', '#d2b690', '#dcc4a2'],
    'r': ['#a65a70', '#b46a7e', '#c27a8c', '#ce8a9a', '#da9ca8'],
    'm': ['#6a7068', '#767c72', '#82887c', '#8e9486', '#9ca090'],
    'q': ['#b8788a', '#c88a9a', '#d49aa8', '#e0aab6', '#eabcc4'],
    'e': ['#5a3e28', '#6a4a30', '#7a5638', '#8a6444', '#9a7250'],
}


def kachel(art, v):
    if art == 'g':
        return k1.gras(v).convert('RGB')
    if art == 's':
        return k1.sand(v).convert('RGB')
    im = umfaerben(k1.sand(v).convert('RGB'), SAND_RAMPE, RAMPEN[art])
    px = im.load()
    r = random.Random(1000 + v + ord(art))
    dunkel = H(RAMPEN[art][0])
    hell = H(RAMPEN[art][4])
    if art == 'p' or art == 'q':                     # Ziegel 8x4 im Verband (Gehweg) bzw. 8x8-Platten (Bahnsteig)
        hoch = 4 if art == 'p' else 8
        for y in range(16):
            for x in range(16):
                xo = (x + (4 if (y // hoch) % 2 else 0)) % 8
                if y % hoch == hoch - 1 or xo == 7:
                    px[x, y] = dunkel
                elif y % hoch == 0 or xo == 0:
                    px[x, y] = hell
    if art == 'b':                                   # Schachbrett aus 8x8-Steinen, zwei Blautoene
        for y in range(16):
            for x in range(16):
                c = px[x, y]
                if (x // 8 + y // 8) % 2:
                    px[x, y] = (max(0, c[0] - 14), max(0, c[1] - 10), max(0, c[2] - 4))
                if x % 8 == 7 or y % 8 == 7:
                    px[x, y] = dunkel
                elif x % 8 == 0 or y % 8 == 0:
                    px[x, y] = hell
    if art in 'kr':                                  # grosse 16x16-Platten
        for y in range(16):
            for x in range(16):
                if x == 15 or y == 15:
                    px[x, y] = dunkel
                elif x == 0 or y == 0:
                    px[x, y] = hell
    if art == 'a':                                   # Asphalt: feine helle/dunkle Koerner
        for _ in range(5):
            px[r.randint(0, 15), r.randint(0, 15)] = hell if r.random() < 0.5 else dunkel
    if art == 'm':                                   # Kies: kleine Steinchen
        for _ in range(6):
            x, y = r.randint(0, 14), r.randint(0, 14)
            px[x, y] = hell
            px[x + 1, y + 1] = dunkel
    if art == 'e':                                   # Erde: Kluempchen
        for _ in range(4):
            x, y = r.randint(0, 14), r.randint(0, 14)
            px[x, y] = H('#a88060')
            px[x, y + 1] = dunkel
    return im


def main():
    os.makedirs(OUT, exist_ok=True)
    arten = 'gsapbkrmqe'
    vor = Image.new('RGB', (len(arten) * 68, 64))
    for i, art in enumerate(arten):
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
