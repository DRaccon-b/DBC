"""16x16-Grundkacheln fuer Karte 09 (Vamdemon's Keep).

  python3 tools/karte09_kacheln.py   ->  assets/karte09/basis/<art>_<v>.png, vorschau.png

Wiederverwendet: Friedhofs-Kacheln von Karte 08 (g, h, w, e, f) unveraendert; neu (umgefaerbte Karte-01-Kacheln):
  i Schloss-Steinplatten (grosse Platten mit Fugen)  c roter Teppich  v violetter Teppich  r roetlicher Randfels
"""
import os, random, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image
import basis_kacheln as k1
from karte04_kacheln import umfaerben, SAND_RAMPE

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
OUT = os.path.join(ROOT, 'assets', 'karte09', 'basis')
K8 = os.path.join(ROOT, 'assets', 'karte08', 'basis')
H = lambda h: tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))
RAMPEN = {
    'i': ['#5e6878', '#687284', '#727c8e', '#7c8698', '#8892a4'],
    'c': ['#5a0c1a', '#6a1020', '#7a1426', '#8a182c', '#9c2034'],
    'v': ['#2c1838', '#341c42', '#3c204c', '#462656', '#522c62'],
    'r': ['#2a1a1c', '#342022', '#3e2628', '#482c2e', '#543436'],
    'w': ['#3e3428', '#4a3e30', '#564838', '#625240', '#705e4a'],      # brauner Erdweg (Vorlage)
}
GRAS = {'g': ['#26322c', '#2e3c34', '#36463c', '#3e5044', '#485a4e', '#546658'],     # kuehles, dunkles Gras
        'h': ['#1c2622', '#222e28', '#28362e', '#2e3e34', '#36463c', '#405044']}


def kachel(art, v):
    if art in GRAS:
        from karte04_kacheln import GRAS_RAMPE
        return umfaerben(k1.gras(v).convert('RGB'), GRAS_RAMPE, GRAS[art])
    im = umfaerben(k1.sand(v).convert('RGB'), SAND_RAMPE, RAMPEN[art])
    px = im.load()
    r = random.Random(900 + v + ord(art))
    if art == 'i':                                   # grosse Steinplatten 8x8, versetzt, Fugen + Lichtkante
        for y in range(16):
            for x in range(16):
                xo = (x + (4 if (y // 8) % 2 else 0)) % 8
                if y % 8 == 7 or xo == 7:
                    px[x, y] = H('#4a5262')
                elif y % 8 == 0 or xo == 0:
                    c = px[x, y]
                    px[x, y] = (min(255, c[0] + 12), min(255, c[1] + 12), min(255, c[2] + 14))
    if art in 'cv':                                  # Samtteppich: feines Rautenmuster
        for y in range(16):
            for x in range(16):
                if (x + y) % 8 == 0 or (x - y) % 8 == 0:
                    c = px[x, y]
                    px[x, y] = (min(255, c[0] + 18), min(255, c[1] + 8), min(255, c[2] + 14))
    if art == 'r':
        for _ in range(3):
            x, y = r.randint(1, 14), r.randint(1, 14)
            px[x, y] = H('#6a4448')
    return im


def main():
    os.makedirs(OUT, exist_ok=True)
    for art in 'ef':
        for v in range(5):
            shutil.copy(os.path.join(K8, '%s_%d.png' % (art, v)), os.path.join(OUT, '%s_%d.png' % (art, v)))
    arten = 'icvrwgh'
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
