"""16x16-Grundkacheln fuer Karte 16 (The Network) und Karte 17 (Our War Game!) - Netzwerk-Boden nach der Vorlage.

  python3 tools/karte16_kacheln.py   ->  assets/karte16/basis/<art>_<v>.png, vorschau.png

  n  Netzwerk-Platte (blau, Lichtkante oben/links, dunkle Fuge unten/rechts; Variante mit Leiterbahn-Winkel und
     cyan Punkt wie in der Vorlage)
  b  Datenbahn (etwas hellere Platte, feine Mittelrille)
  leer  Leere des Netzes (sehr dunkles Blau mit schwachem Raster)
"""
import os, random
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
OUT = os.path.join(ROOT, 'assets', 'karte16', 'basis')
H = lambda h: tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def platte(v, grund, licht, fuge, rille=False):
    im = Image.new('RGB', (16, 16), H(grund))
    px = im.load()
    r = random.Random(1600 + v * 13 + (7 if rille else 0))
    for i in range(16):
        px[i, 15] = H(fuge); px[15, i] = H(fuge)                 # Fuge unten/rechts
    for i in range(1, 15):
        px[i, 1] = H(licht)                                      # Lichtkante oben (Licht von oben links)
    for i in range(2, 14):
        px[1, i] = tuple(int((a + b) / 2) for a, b in zip(H(licht), H(grund)))
    for _ in range(3):                                           # leichte Flecken, kein Rauschen
        x, y = r.randint(3, 12), r.randint(3, 12)
        c = px[x, y]
        px[x, y] = tuple(max(0, a - 6) for a in c)
    if rille:
        for i in range(3, 13):
            px[7, i] = tuple(max(0, a - 14) for a in H(grund))
            px[8, i] = tuple(min(255, a + 10) for a in H(grund))
    if not rille and v == 1:                                     # Leiterbahn-Winkel mit cyan Endpunkt
        x0, y0 = (4, 10) if v == 1 else (9, 11)
        for i in range(6):
            px[x0 + i, y0] = H('#1c2c48')
        for i in range(4):
            px[x0 + 5, y0 - i] = H('#1c2c48')
        px[x0 + 5, y0 - 4] = H('#5ad0e8')
    return im


def leer(v):
    im = Image.new('RGB', (16, 16), H('#0a0f20'))
    px = im.load()
    for i in range(16):
        px[i, 0] = H('#0d1428'); px[0, i] = H('#0d1428')
    if v == 2:
        px[8, 8] = H('#16264a')
    return im


def main():
    os.makedirs(OUT, exist_ok=True)
    sets = {'n': lambda v: platte(v, '#2c4468', '#3e5a84', '#1c2c48'),
            'b': lambda v: platte(v, '#33507a', '#4a6a96', '#203454', rille=True),
            'leer': leer}
    vor = Image.new('RGB', (len(sets) * 68, 64))
    for i, (art, f) in enumerate(sets.items()):
        ks = [f(v) for v in range(5)]
        for v, k in enumerate(ks):
            k.save(os.path.join(OUT, '%s_%d.png' % (art, v)))
        for yy in range(4):
            for xx in range(4):
                vor.paste(ks[(xx * 3 + yy * 2) % 5], (i * 68 + xx * 16, yy * 16))
    vor.resize((vor.width * 4, vor.height * 4), Image.NEAREST).save(os.path.join(OUT, 'vorschau.png'))
    print('Kacheln ->', OUT)


if __name__ == '__main__':
    main()
