"""16x16-Grundkacheln fuer Karte 05 (Freezeland).

  python3 tools/karte05_kacheln.py   ->  assets/karte05/basis/<art>_<v>.png, vorschau.png

Wiederverwendung: Sand- und Graskacheln aus Karte 01 (assets/basis) werden ueber ihre Farbrampe umgefaerbt.
  s Schnee  g Plateauschnee  w festgetretener Weg  l Eisboden  i Eissee  e gefrorene Erde  r Felsboden
  c Spaltengrund (dunkles Eis)  h Waldboden (Schatten unter Tannen)
"""
import os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image
import basis_kacheln as k1
from karte04_kacheln import umfaerben, GRAS_RAMPE, SAND_RAMPE

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
OUT = os.path.join(ROOT, 'assets', 'karte05', 'basis')
H = lambda h: tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))
RAMPEN = {
    's': ('sand', ['#b6c8d8', '#cbd9e5', '#dfe8f0', '#ecf2f7', '#fbfdff']),
    'g': ('sand', ['#b0c6d8', '#c6d8e6', '#dbe7f1', '#e9f1f8', '#f8fcff']),
    'w': ('sand', ['#94a6b8', '#a8b8c8', '#bac8d6', '#c9d5e0', '#d9e2ea']),
    'l': ('sand', ['#6eb2d2', '#84c0dc', '#9acde5', '#b0d9ec', '#cfeaf5']),
    'i': ('sand', ['#4f9ac2', '#62a8cc', '#78b7d6', '#8ec6df', '#b4dcee']),
    'e': ('sand', ['#5e4430', '#765838', '#8a6a46', '#9c7c56', '#b4966e']),
    'r': ('sand', ['#7a8494', '#8e98a8', '#a2aab8', '#b4bcc8', '#cbd2dc']),
    'c': ('sand', ['#1a2440', '#22304e', '#2c3c5e', '#36486c', '#48608a']),
    'h': ('gras', ['#22383a', '#2c4646', '#385652', '#46665e', '#56766a', '#688a7a']),
}


def kachel(art, v):
    typ, ziel = RAMPEN[art]
    if typ == 'gras':
        im = umfaerben(k1.gras(v).convert('RGB'), GRAS_RAMPE, ziel)
    else:
        im = umfaerben(k1.sand(v).convert('RGB'), SAND_RAMPE, ziel)
    r = random.Random(700 + v + ord(art))
    if art in 'sg':                                       # Glitzern im Schnee
        for _ in range(2):
            im.putpixel((r.randint(0, 15), r.randint(0, 15)), H('#ffffff'))
    if art in 'li':                                       # Eis: helle Spiegelstriche, feiner Riss
        for _ in range(2):
            x, y = r.randint(0, 12), r.randint(0, 14)
            for d in range(3):
                im.putpixel((x + d, y), H('#e6f6fc'))
        if r.random() < 0.6:
            x, y = r.randint(2, 13), r.randint(2, 13)
            for d in range(4):
                im.putpixel(((x + d) % 16, (y + d // 2) % 16), H('#4a8ab0' if art == 'i' else '#5e9ec2'))
    if art == 'w':                                        # Fussspuren
        for _ in range(2):
            x, y = r.randint(1, 13), r.randint(1, 13)
            im.putpixel((x, y), H('#8a9cae')); im.putpixel((x + 1, y + 1), H('#8a9cae'))
    return im


ARTEN = 'sgwlierch'


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
