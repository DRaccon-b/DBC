"""16x16-Grundkacheln fuer Karte 15 (Apocalymon's Realm): p Plattform (Steinplatten), r Rand, s Steg, v Riss,
. Leere; Fels f aus Karte 08 fuer die Fronten.

  python3 tools/karte15_kacheln.py
"""
import os, random, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image
import basis_kacheln as k1
from karte04_kacheln import umfaerben, SAND_RAMPE

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
OUT = os.path.join(ROOT, 'assets', 'karte15', 'basis')
K8 = os.path.join(ROOT, 'assets', 'karte08', 'basis')
H = lambda h: tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))
RAMPEN = {
    'p': ['#4a4a5c', '#525266', '#5a5a70', '#63637a', '#6c6c86'],
    'r': ['#2e2c3a', '#343242', '#3a384a', '#424052', '#4a485c'],
    's': ['#4a4a5c', '#525266', '#5a5a70', '#63637a', '#6c6c86'],
    'v': ['#16101e', '#1c1426', '#22182e', '#2a1e38', '#322444'],
    '.': ['#0a0c18', '#0c0e1c', '#0e1020', '#101224', '#121428'],
}


def kachel(art, v):
    im = umfaerben(k1.sand(v).convert('RGB'), SAND_RAMPE, RAMPEN[art])
    px = im.load()
    r = random.Random(1500 + v * 7 + ord(art))
    dunkel, hell = H(RAMPEN[art][0]), H(RAMPEN[art][4])
    if art in 'ps':                                  # Steinziegel wie in der Vorlage: Reihen 8x4, versetzt, Licht oben
        for y in range(16):
            for x in range(16):
                xo = (x + (4 if (y // 4) % 2 else 0)) % 8
                if y % 4 == 3 or xo == 7:
                    px[x, y] = dunkel
                elif y % 4 == 0 and xo < 6:
                    px[x, y] = hell
        if art == 'p' and v in (1, 4):               # vereinzelt violette Kristallsplitter (wie in der Vorlage)
            x, y = r.randint(2, 12), r.randint(5, 13)
            px[x, y] = H('#8a5ad0'); px[x, y - 1] = H('#b48ae8'); px[x + 1, y] = H('#4a3070')
        if v == 3:                                   # gesprungener Ziegel
            x, y = r.randint(3, 10), 1
            for _ in range(6):
                px[x, y] = H('#34324a'); x += r.choice((0, 1)); y += 2
    if art == 'r':                                   # dunkler Randstein: grobe Bloecke mit Kanten
        for y in range(16):
            for x in range(16):
                if y % 8 == 7 or (x + (8 if (y // 8) % 2 else 0)) % 16 == 15:
                    px[x, y] = H('#1c1a26')
                elif y % 8 == 0:
                    px[x, y] = hell
    if art == 'v':                                   # Riss: dunkles Violett mit feinen Leuchtadern
        for _ in range(3):
            x, y = r.randint(1, 14), r.randint(1, 14)
            px[x, y] = H('#6a3aa0')
    return im


def main():
    os.makedirs(OUT, exist_ok=True)
    for v in range(5):
        shutil.copy(os.path.join(K8, 'f_%d.png' % v), os.path.join(OUT, 'f_%d.png' % v))
    arten = 'prsv.'
    vor = Image.new('RGB', ((len(arten) + 1) * 68, 64))
    for i, art in enumerate(arten):
        ks = [kachel(art, v) for v in range(5)]
        for v, k in enumerate(ks):
            k.save(os.path.join(OUT, '%s_%d.png' % ({'.': 'leer'}.get(art, art), v)))
        for yy in range(4):
            for xx in range(4):
                vor.paste(ks[(xx * 3 + yy * 2) % 5], (i * 68 + xx * 16, yy * 16))
    for yy in range(4):
        for xx in range(4):
            vor.paste(Image.open(os.path.join(OUT, 'f_%d.png' % ((xx + yy) % 5))), (len(arten) * 68 + xx * 16, yy * 16))
    vor.resize((vor.width * 3, vor.height * 3), Image.NEAREST).save(os.path.join(OUT, 'vorschau.png'))
    print('Kacheln ->', OUT)


if __name__ == '__main__':
    main()
