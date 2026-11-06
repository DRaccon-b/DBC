"""16x16-Grundkacheln fuer Karte 11 (Spiral Mountain: Dark Ocean).

  python3 tools/karte11_kacheln.py   ->  assets/karte11/basis/<art>_<v>.png, vorschau.png

Wiederverwendet: Felskacheln der Karte 08 (f = Terrassenfels) fuer Berg und Felsblock. Neu (umgefaerbte Karte-01-
Sandkacheln mit eigener Zeichnung):
  d schwarze Asche (Risse, Schlackekoerner)  m helle Asche  n nasser Strand  v lila Erde
  b Ruinen-Pflaster (dunkle Ziegel)  q Steinweg  f Plattform (grosse Platten)  z Bannkreis-Boden
"""
import os, random, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image
import basis_kacheln as k1
from karte04_kacheln import umfaerben, SAND_RAMPE

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
OUT = os.path.join(ROOT, 'assets', 'karte11', 'basis')
K8 = os.path.join(ROOT, 'assets', 'karte08', 'basis')
H = lambda h: tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))
RAMPEN = {
    'd': ['#22222c', '#2a2a36', '#323240', '#3a3a4a', '#444456'],
    'm': ['#40424e', '#4a4c5a', '#545666', '#5e6072', '#6a6c7e'],
    'n': ['#34484c', '#3c5256', '#445c60', '#4e666a', '#587276'],
    'v': ['#30243a', '#382a44', '#40304e', '#4a3858', '#544264'],
    'b': ['#1c1c26', '#22222e', '#282836', '#30303e', '#3a3a4a'],
    'q': ['#4a4c58', '#545664', '#5e6070', '#686a7a', '#747688'],
    'f': ['#4c4e5c', '#565868', '#606374', '#6a6d80', '#76798c'],
    'z': ['#1e1a26', '#24202e', '#2a2636', '#322c40', '#3a344a'],
}


def kachel(art, v):
    im = umfaerben(k1.sand(v).convert('RGB'), SAND_RAMPE, RAMPEN[art])
    px = im.load()
    r = random.Random(1100 + v * 7 + ord(art))
    dunkel, hell = H(RAMPEN[art][0]), H(RAMPEN[art][4])
    if art in 'dm':                                  # Asche: Schlackekoerner und feine Risse
        for _ in range(4):
            x, y = r.randint(0, 15), r.randint(0, 14)
            px[x, y] = dunkel
            px[x, y + 1] = hell if art == 'm' else H('#4e4e62')
        if v % 2 == 0:
            x, y = r.randint(2, 12), r.randint(2, 12)
            for _ in range(5):
                if 0 <= x < 16 and 0 <= y < 16:
                    px[x, y] = H('#18181f')
                x += r.choice((-1, 0, 1)); y += 1
    if art == 'v':                                   # lila Erde: kleine helle Kristallsplitter
        for _ in range(2):
            x, y = r.randint(1, 14), r.randint(1, 14)
            px[x, y] = H('#8a6a9e')
    if art == 'b':                                   # dunkle Ziegel 8x4 im Verband
        for y in range(16):
            for x in range(16):
                xo = (x + (4 if (y // 4) % 2 else 0)) % 8
                if y % 4 == 3 or xo == 7:
                    px[x, y] = H('#14141c')
                elif y % 4 == 0 and xo < 6:
                    px[x, y] = hell
    if art in 'qfz':                                 # Platten: q 8x8, f/z 16x16 mit Lichtkante
        g = 8 if art == 'q' else 16
        for y in range(16):
            for x in range(16):
                xo = (x + (g // 2 if art == 'q' and (y // 8) % 2 else 0)) % g
                if y % g == g - 1 or xo == g - 1:
                    px[x, y] = dunkel
                elif y % g == 0 or xo == 0:
                    px[x, y] = hell
    return im


def main():
    os.makedirs(OUT, exist_ok=True)
    for v in range(5):
        shutil.copy(os.path.join(K8, 'f_%d.png' % v), os.path.join(OUT, 'r_%d.png' % v))
    arten = 'dmnvbqfz'
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
