"""16x16-Grundkacheln fuer Karte 14 (Spiral Mountain: Summit).

  python3 tools/karte14_kacheln.py   ->  assets/karte14/basis/<art>_<v>.png, vorschau.png

Wiederverwendet: Felskacheln der Karte 08 (f) fuer die Bergwand - dieselbe Wand wie Karte 11-13.
Neu: d Gipfelpflaster  k dunkler Schotter  p Kristallboden  v Felsnasen (oben)  c roter Teppich
     z Harlekin-Schachbrett  b dunkle Ziegel  f Steinplatten (Portalplatz)
"""
import os, random, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image
import basis_kacheln as k1
from karte04_kacheln import umfaerben, SAND_RAMPE

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
OUT = os.path.join(ROOT, 'assets', 'karte14', 'basis')
K8 = os.path.join(ROOT, 'assets', 'karte08', 'basis')
H = lambda h: tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))
RAMPEN = {
    'd': ['#4a4856', '#524f5e', '#5a5768', '#635f72', '#6c687c'],
    'k': ['#2a2832', '#312e3a', '#383442', '#403c4a', '#4a4654'],
    'p': ['#2c2240', '#34284a', '#3c2e54', '#46365e', '#503e6a'],
    'v': ['#5e6274', '#686c80', '#72768a', '#7c8096', '#888ca2'],
    'c': ['#6a1018', '#7a141e', '#8a1a24', '#9a202a', '#aa2832'],
    'z': ['#1a1424', '#221a2e', '#2a2038', '#a08ac8', '#b8a2dc'],
    'b': ['#2a2632', '#322d3c', '#3a3446', '#423c50', '#4c465a'],
    'f': ['#6c6e7c', '#767888', '#808294', '#8a8ca0', '#9698ac'],
}


def kachel(art, v):
    im = umfaerben(k1.sand(v).convert('RGB'), SAND_RAMPE, RAMPEN[art])
    px = im.load()
    r = random.Random(1400 + v * 7 + ord(art))
    dunkel, hell = H(RAMPEN[art][0]), H(RAMPEN[art][4])
    if art in 'dv':                                  # unregelmaessige Pflaster-/Felsplatten mit Fugen
        steine = [(0, 0, 9, 6), (9, 0, 16, 7), (0, 6, 6, 12), (6, 7, 13, 12), (13, 7, 16, 16), (0, 12, 8, 16), (8, 12, 13, 16)]
        if v % 2:
            steine = [(0, 0, 6, 8), (6, 0, 16, 5), (6, 5, 12, 11), (12, 5, 16, 11), (0, 8, 6, 16), (6, 11, 16, 16)]
        for (x0, y0, x1, y1) in steine:
            for x in range(x0, x1):
                px[x, y1 - 1] = dunkel
            for y in range(y0, y1):
                px[x1 - 1, y] = dunkel
            for x in range(x0, x1 - 1):
                px[x, y0] = hell
    if art == 'k':                                   # Schotter: dunkle Steinchen mit Licht oben links
        for _ in range(7):
            x, y = r.randint(0, 14), r.randint(0, 14)
            px[x, y] = H('#5a5666'); px[x + 1, y + 1] = H('#18161e')
    if art == 'p':                                   # Kristallboden: kleine violette Splitter
        for _ in range(4):
            x, y = r.randint(1, 14), r.randint(2, 14)
            px[x, y] = H('#a070e0'); px[x, y - 1] = H('#c8a0f8'); px[x + 1, y] = H('#5a3a8a')
    if art == 'c':                                   # roter Teppich: feine Webstruktur, einzelne Goldpunkte
        for y in range(16):
            for x in range(16):
                if (x + y) % 4 == 0:
                    px[x, y] = H('#7e1620')
        if v in (0, 3):
            px[r.randint(3, 12), r.randint(3, 12)] = H('#d0a040')
    if art == 'z':                                   # Harlekin-Schachbrett schwarz/lavendel 8x8
        for y in range(16):
            for x in range(16):
                hell_ = ((x // 8) + (y // 8)) % 2 == 0
                c = H('#9a84c4') if hell_ else H('#1c1626')
                if hell_ and (x % 8 == 0 or y % 8 == 0):
                    c = H('#b8a4dc')
                if not hell_ and (x % 8 == 7 or y % 8 == 7):
                    c = H('#120e18')
                px[x, y] = c
    if art == 'b':                                   # dunkle Ziegel 8x4
        for y in range(16):
            for x in range(16):
                xo = (x + (4 if (y // 4) % 2 else 0)) % 8
                if y % 4 == 3 or xo == 7:
                    px[x, y] = H('#16141c')
                elif y % 4 == 0 and xo < 6:
                    px[x, y] = hell
    if art == 'f':                                   # grosse Steinplatten 16x16 mit Rissen
        for y in range(16):
            for x in range(16):
                if y == 15 or x == 15:
                    px[x, y] = dunkel
                elif y == 0 or x == 0:
                    px[x, y] = hell
        if v == 2:
            x, y = 4, 2
            for _ in range(8):
                px[x, y] = dunkel; x += r.choice((0, 1)); y += 1
    return im


def main():
    os.makedirs(OUT, exist_ok=True)
    for v in range(5):
        shutil.copy(os.path.join(K8, 'f_%d.png' % v), os.path.join(OUT, 'r_%d.png' % v))
    arten = 'dkpvczbf'
    vor = Image.new('RGB', ((len(arten) + 1) * 68, 64))
    for i, art in enumerate(arten):
        ks = [kachel(art, v) for v in range(5)]
        for v, k in enumerate(ks):
            k.save(os.path.join(OUT, '%s_%d.png' % (art, v)))
        for yy in range(4):
            for xx in range(4):
                vor.paste(ks[(xx * 3 + yy * 2) % 5], (i * 68 + xx * 16, yy * 16))
    for yy in range(4):
        for xx in range(4):
            vor.paste(Image.open(os.path.join(OUT, 'r_%d.png' % ((xx + yy) % 5))), (len(arten) * 68 + xx * 16, yy * 16))
    vor.resize((vor.width * 3, vor.height * 3), Image.NEAREST).save(os.path.join(OUT, 'vorschau.png'))
    print('Kacheln ->', OUT)


if __name__ == '__main__':
    main()
