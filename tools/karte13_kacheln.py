"""16x16-Grundkacheln fuer Karte 13 (Spiral Mountain: Machine City).

  python3 tools/karte13_kacheln.py   ->  assets/karte13/basis/<art>_<v>.png, vorschau.png

Wiederverwendet: Felskacheln der Karte 08 (f) fuer die Bergwand - dieselbe Wand wie Karte 11 und 12.
Neu (umgefaerbte Karte-01-Sandkacheln mit eigener Zeichnung):
  s Asphalt (Risse, Flicken)  g Gehweg (Platten 8x8)  h Hof-Beton (grosse Platten, Fugen)  m Festungsboden
  (Metallplatten mit Nieten und roten Leuchtstrichen)  z Gitterrost  n Gras (verwildert)  p verseuchter Boden (violett)
"""
import os, random, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image
import basis_kacheln as k1
from karte04_kacheln import umfaerben, SAND_RAMPE

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
OUT = os.path.join(ROOT, 'assets', 'karte13', 'basis')
K8 = os.path.join(ROOT, 'assets', 'karte08', 'basis')
H = lambda h: tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))
RAMPEN = {
    's': ['#2a2e3a', '#30343f', '#363a46', '#3c404c', '#444856'],
    'g': ['#5a606e', '#626877', '#6a7080', '#727888', '#7c8292'],
    'h': ['#7e8890', '#868f98', '#8e98a0', '#96a0a8', '#a0aab2'],
    'm': ['#243440', '#2a3c48', '#304450', '#364c58', '#3e5662'],
    'z': ['#3a424c', '#424a56', '#4a5260', '#545c6a', '#5e6676'],
    'n': ['#2e4630', '#344e36', '#3a563c', '#425e42', '#4a684a'],
    'p': ['#3a3048', '#403652', '#463c5a', '#4e4464', '#584c6e'],
}


def kachel(art, v):
    im = umfaerben(k1.sand(v).convert('RGB'), SAND_RAMPE, RAMPEN[art])
    px = im.load()
    r = random.Random(1300 + v * 7 + ord(art))
    dunkel, hell = H(RAMPEN[art][0]), H(RAMPEN[art][4])
    if art == 's':                                   # Asphalt: helle Koernung, ab und zu ein Riss
        for _ in range(5):
            px[r.randint(0, 15), r.randint(0, 15)] = H('#52566a')
        if v % 3 == 0:
            x, y = r.randint(2, 12), r.randint(1, 4)
            for _ in range(9):
                if 0 <= x < 16 and 0 <= y < 16:
                    px[x, y] = H('#1c1e26')
                x += r.choice((0, 1)); y += 1
    if art in 'gh':                                  # Platten: g 8x8, h 16x16, Lichtkante oben links
        gr = 8 if art == 'g' else 16
        for y in range(16):
            for x in range(16):
                if y % gr == gr - 1 or x % gr == gr - 1:
                    px[x, y] = dunkel
                elif y % gr == 0 or x % gr == 0:
                    px[x, y] = hell
        if v == 3:                                   # gesprungene Platte
            x, y = r.randint(3, 10), 1
            for _ in range(7):
                px[x, y] = dunkel; x += r.choice((-1, 0, 1)); y += 2 if y < 13 else 0
    if art == 'm':                                   # Metallplatten 16x16, Nieten, roter Leuchtstrich (Karte der Vorlage)
        for y in range(16):
            for x in range(16):
                if y == 15 or x == 15:
                    px[x, y] = H('#141c24')
                elif y == 0 or x == 0:
                    px[x, y] = H('#4a6472')
        for (x, y) in ((2, 2), (13, 2), (2, 13), (13, 13)):
            px[x, y] = H('#6a8494'); px[x + 1, y + 1] = H('#141c24')
        if v in (1, 3):
            for x in range(5, 9):
                px[x, 7] = H('#b02c34')
            px[9, 7] = H('#e05060')
    if art == 'z':                                   # Gitterrost: Staebe senkrecht mit dunklen Spalten
        for y in range(16):
            for x in range(16):
                if x % 3 == 2:
                    px[x, y] = H('#1a1e24')
                elif x % 3 == 0:
                    px[x, y] = hell
                if y % 8 == 7:
                    px[x, y] = H('#2a3038')
    if art == 'n':                                   # verwildertes Gras: Halme
        for _ in range(6):
            x, y = r.randint(0, 15), r.randint(1, 15)
            px[x, y] = H('#5a7a56'); px[x, y - 1] = H('#4a6a48')
    if art == 'p':                                   # verseucht: violette Flecken, Schlieren
        for _ in range(4):
            x, y = r.randint(0, 14), r.randint(0, 15)
            px[x, y] = H('#6a5a86'); px[x + 1, y] = H('#5e507a')
    return im


def main():
    os.makedirs(OUT, exist_ok=True)
    for v in range(5):
        shutil.copy(os.path.join(K8, 'f_%d.png' % v), os.path.join(OUT, 'r_%d.png' % v))
    arten = 'sghmznp'
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
