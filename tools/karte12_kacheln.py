"""16x16-Grundkacheln fuer Karte 12 (Spiral Mountain: Puppet Woods).

  python3 tools/karte12_kacheln.py   ->  assets/karte12/basis/<art>_<v>.png, vorschau.png

Wiederverwendet: Felskacheln der Karte 08 (f = Terrassenfels) fuer die Bergwand - dieselbe Wand wie Karte 11.
Neu (umgefaerbte Karte-01-Sandkacheln mit eigener Zeichnung):
  d Schlamm (feuchte Flecken, Steinchen, Wurzelreste)  g Waldboden (dunkles Moos, Nadeln)  q Trampelpfad (festgetreten,
  heller, Kiesel)  a Acker (Furchen)  v Moos auf den Plateaus  b Pflaster (blaugraue Ziegel)
  f Arena-Steinboden (Platten)  z Arena-Schachbrett (rot/violett)  h Holzrand (Bretter)
"""
import os, random, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image
import basis_kacheln as k1
from karte04_kacheln import umfaerben, SAND_RAMPE

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
OUT = os.path.join(ROOT, 'assets', 'karte12', 'basis')
K8 = os.path.join(ROOT, 'assets', 'karte08', 'basis')
H = lambda h: tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))
RAMPEN = {
    'd': ['#3a2a22', '#43312a', '#4b3830', '#543f35', '#5e473c'],
    'g': ['#1c2a22', '#223228', '#283a2e', '#2e4234', '#364c3c'],
    'q': ['#58463a', '#625042', '#6c5a4a', '#766452', '#826e5c'],
    'a': ['#2c1e18', '#34241c', '#3c2a20', '#463226', '#503a2c'],
    'v': ['#26362a', '#2c3e30', '#344836', '#3c523e', '#465e46'],
    'b': ['#2e3240', '#363a4a', '#3e4454', '#484e60', '#545a6c'],
    'f': ['#5c6274', '#666c80', '#70768a', '#7a8296', '#868ea2'],
    'z': ['#3a1a34', '#44203c', '#4e2646', '#5a2c50', '#66345c'],
    'h': ['#3a2416', '#442c1a', '#4e3420', '#5a3c26', '#66462e'],
}


def kachel(art, v):
    im = umfaerben(k1.sand(v).convert('RGB'), SAND_RAMPE, RAMPEN[art])
    px = im.load()
    r = random.Random(1200 + v * 7 + ord(art))
    dunkel, hell = H(RAMPEN[art][0]), H(RAMPEN[art][4])
    if art == 'd':                                   # Schlamm: nasse dunkle Flecken mit Glanzpunkt, kleine Steine
        for _ in range(2):
            x, y = r.randint(1, 12), r.randint(1, 13)
            for dx in range(3):
                px[x + dx, y] = H('#2e211b')
                px[x + dx, y + 1] = H('#33251e')
            px[x + 1, y] = H('#6a5446')
        for _ in range(2):
            x, y = r.randint(0, 15), r.randint(0, 14)
            px[x, y] = H('#6e5a4c'); px[x, y + 1] = dunkel
    if art == 'g':                                   # Waldboden: Moospolster, Nadeln
        for _ in range(4):
            x, y = r.randint(0, 14), r.randint(0, 15)
            px[x, y] = H('#3e5842'); px[x + 1, y] = H('#344c3a')
        for _ in range(2):
            x, y = r.randint(0, 13), r.randint(0, 15)
            px[x, y] = H('#4a3a2c'); px[x + 1, y] = H('#4a3a2c')
    if art == 'q':                                   # Trampelpfad: Kiesel mit Licht oben links
        for _ in range(3):
            x, y = r.randint(1, 14), r.randint(1, 14)
            px[x, y] = H('#94806c'); px[x + 1, y + 1] = H('#4c3c30')
    if art == 'a':                                   # Acker: waagerechte Furchen
        for y in range(16):
            for x in range(16):
                if y % 4 == 3:
                    px[x, y] = H('#22160f')
                elif y % 4 == 0:
                    px[x, y] = H('#5a4232') if (x + v) % 5 else H('#4a3426')
    if art == 'v':                                   # Moos: helle Polster
        for _ in range(4):
            x, y = r.randint(0, 14), r.randint(0, 14)
            px[x, y] = H('#56705a'); px[x + 1, y] = H('#4c6650'); px[x, y + 1] = H('#2a3a2e')
    if art == 'b':                                   # Pflaster: Ziegel 8x4 im Verband
        for y in range(16):
            for x in range(16):
                xo = (x + (4 if (y // 4) % 2 else 0)) % 8
                if y % 4 == 3 or xo == 7:
                    px[x, y] = H('#1e2028')
                elif y % 4 == 0 and xo < 6:
                    px[x, y] = hell
    if art == 'f':                                   # Arena: Platten 8x8 versetzt
        for y in range(16):
            for x in range(16):
                xo = (x + (4 if (y // 8) % 2 else 0)) % 8
                if y % 8 == 7 or xo == 7:
                    px[x, y] = dunkel
                elif y % 8 == 0 or xo == 0:
                    px[x, y] = hell
    if art == 'z':                                   # Schachbrett rot/violett 8x8 mit Fugen
        for y in range(16):
            for x in range(16):
                rot = ((x // 8) + (y // 8)) % 2 == 0
                c = H('#8a2a3a') if rot else H('#4a2a70')
                if x % 8 == 7 or y % 8 == 7:
                    c = H('#24101e')
                elif x % 8 == 0 or y % 8 == 0:
                    c = H('#a84a56') if rot else H('#66468e')
                px[x, y] = c
    if art == 'h':                                   # Holzbretter waagerecht, Maserung, Naegel
        for y in range(16):
            for x in range(16):
                if y % 8 == 7:
                    px[x, y] = H('#22140c')
                elif y % 8 == 0:
                    px[x, y] = H('#7a5636')
                elif (x * 3 + y * 7 + v) % 11 == 0:
                    px[x, y] = H('#3e2818')
        for y in (2, 10):
            px[1, y] = H('#9a9aa0'); px[14, y] = H('#9a9aa0')
    return im


def main():
    os.makedirs(OUT, exist_ok=True)
    for v in range(5):
        shutil.copy(os.path.join(K8, 'f_%d.png' % v), os.path.join(OUT, 'r_%d.png' % v))
    arten = 'dgqavbfzh'
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
