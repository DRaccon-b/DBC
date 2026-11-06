"""Karte 11 (Spiral Mountain: Dark Ocean): Kachelraster aus der Vorlage -> maps/karte11/layout.json

  python3 tools/karte11_layout.py

Vorlage assets/vorlagen/karte11_vorlage.png (1280x1120 = 80x70 Kacheln a 16 px).
Links schwarzes, verseuchtes Land (Asche, schwarze Tuempel, Felsblock, Ruinen-Platz, zwei lila Hochplateaus),
oben der Bergkamm mit Durchgang zum Teleporter, rechts das Meer der Finsternis: tuerkises Flachwasser mit
Seetangfeldern, dahinter Tiefsee mit der achteckigen Bannkreis-Plattform und einer Steinbruecke.
Klassen:  d Asche (schwarz verseucht)  m helle Asche  n nasser Strand  u Flachwasser  h Seetangfeld (im Flachwasser)
          ~ Tiefsee  x schwarzer Tuempel  v lila Erde (Plateau)  r Fels (Berg, Felsblock)  b Ruinen-Pflaster
          q Steinweg  f Plattform  z Bannkreis
Hoehen:   0 Tiefsee/Tuempel, 1 Land und Flachwasser, 2 Plateaus/Felsblock/Plattform, 5 Berg.
"""
import json, os
import numpy as np
from PIL import Image, ImageFilter

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte11')
T = 16
C, R = 80, 70


def glaetten(m, n=1):
    k = Image.fromarray((m * 255).astype(np.uint8))
    for _ in range(n):
        k = k.filter(ImageFilter.ModeFilter(3))
    return np.array(k) > 127


def main():
    im = np.array(Image.open(os.path.join(ROOT, 'assets', 'vorlagen', 'karte11_vorlage.png')).convert('RGB')).astype(float)
    med = np.zeros((R, C, 3))
    for y in range(R):
        for x in range(C):
            med[y, x] = np.median(im[y * T:(y + 1) * T, x * T:(x + 1) * T].reshape(-1, 3), axis=0)
    r_, g_, b_ = med[..., 0], med[..., 1], med[..., 2]
    yy, xx = np.mgrid[0:R, 0:C]
    k = np.full((R, C), 'd')
    h = np.ones((R, C), int)
    # ------------------------------------------------------------------ Wasser und Strand aus den Farben
    blau = (b_ > g_ + 22) & (b_ > r_ + 35) & (g_ < 95)
    land_bereich = (xx < 44) & (yy < 57)
    tief = blau & ~land_bereich
    tief = glaetten(tief, 2)
    tuerkis = (g_ > r_ + 45)
    seetang = tuerkis & (g_ < 118)
    strand = (g_ > r_ + 12) & (b_ > r_ + 15) & ~tuerkis & ~tief
    tuempel = blau & land_bereich
    k[glaetten(strand | tuerkis, 1)] = 'n'
    k[glaetten(tuerkis, 1)] = 'u'
    k[glaetten(seetang, 1) & (k == 'u')] = 'h'
    hell = ((r_ + g_ + b_) / 3 > 84) & (k == 'd')
    k[glaetten(hell, 1)] = 'm'
    k[glaetten(tuempel, 1)] = 'x'
    k[tief] = '~'
    # ------------------------------------------------------------------ Berg oben, Felswand links
    berg = np.zeros((R, C), bool)
    berg[0:3, 0:47] = True
    berg[0:2, 47:75] = True
    berg[:58, 0:2] = True
    berg[25:37, 0:2] = False                       # Ruinen-Platz reicht bis an den Rand (Teleporter)
    berg[0:5, 29:36] = False                       # Durchgang zum Teleporter oben
    for (x, y) in ((3, 3), (4, 3), (8, 3), (12, 3), (13, 3), (21, 3), (22, 3), (40, 3), (41, 3), (44, 3)):
        berg[y, x] = True                          # unregelmaessige Bergkante
    k[berg] = 'r'
    h[berg] = 5
    k[0:6, 29:36] = 'q'                            # Steinweg zum Teleporter
    # ------------------------------------------------------------------ lila Hochplateaus, Felsblock
    for (x0, y0, x1, y1) in ((2, 5, 9, 21), (2, 40, 9, 53)):
        k[y0:y1 + 1, x0:x1 + 1] = 'v'
        h[y0:y1 + 1, x0:x1 + 1] = 2
    k[17:22, 16:22] = 'r'
    h[17:22, 16:22] = 2
    # ------------------------------------------------------------------ Ruinen-Platz links
    k[25:37, 0:15] = 'b'
    for (y, x0) in ((25, 4), (26, 3), (36, 4), (35, 13), (34, 14)):
        k[y, x0:] = np.where(k[y, x0:] == 'b', 'd', k[y, x0:]) if False else k[y, x0:]
    k[25, 0:3] = 'd'
    k[36, 12:15] = 'd'
    # ------------------------------------------------------------------ Plattform mit Bannkreis, Bruecke
    platt = (np.abs(xx + 0.5 - 69.5) / 9.6 + np.abs(yy + 0.5 - 39.5) / 10.4 <= 1.45) & \
            (np.abs(xx + 0.5 - 69.5) <= 9.6) & (np.abs(yy + 0.5 - 39.5) <= 10.4)
    k[platt] = 'f'
    h[platt] = 2
    kreis = ((xx + 0.5 - 69.5) ** 2 / 5.2 ** 2 + (yy + 0.5 - 38.5) ** 2 / 4.6 ** 2) <= 1
    k[kreis] = 'z'
    k[35:42, 52:58] = np.where(np.isin(k[35:42, 52:58], ['d', 'm', 'n']), 'u', k[35:42, 52:58])   # keine Landreste im Riff
    k[37:40, 42:60] = 'q'                          # Steinbruecke vom Strand ueber Riff und Tiefsee zur Plattform
    h[37:40, 42:60] = 1
    k[36:41, 39:42] = 'q'                          # Brueckenkopf am Strand (gepflastert)
    # rund um die Plattform nur Tiefsee (die Vorlage hat am rechten Rand noch einen Streifen Land)
    um = (xx >= 58) & (yy >= 24) & (yy <= 56) & np.isin(k, ['d', 'm', 'n'])
    k[um] = '~'
    # Tiefe und Hoehe
    h[np.isin(k, ['~', 'x'])] = 0
    lay = {
        'groesse': [C, R], 'klassen': [''.join(r) for r in k], 'hoehe': [''.join(str(c) for c in r) for r in h],
        # Treppen (x0, x1, Ebene): Sued-Treppe des oberen Plateaus; Osttreppen als (y0, y1, x, Ebene)
        # Treppen nach Sueden von beiden lila Plateaus: (x0, x1, Ebene, unterste Plateaureihe)
        'treppen_sued': [[5, 8, 2, 21], [5, 8, 2, 53]],
        'bruecke': [42, 37, 59, 39],
        'teleporter': [{'x': 29, 'y': 0, 'b': 6, 'h': 2}, {'x': 0, 'y': 30, 'b': 2, 'h': 4}],
    }
    os.makedirs(KARTE, exist_ok=True)
    json.dump(lay, open(os.path.join(KARTE, 'layout.json'), 'w'), indent=0)
    F = {'d': (60, 60, 72), 'm': (92, 94, 106), 'n': (80, 118, 122), 'u': (50, 140, 130), 'h': (28, 90, 84),
         '~': (40, 46, 92), 'x': (30, 40, 70), 'v': (86, 66, 96), 'r': (110, 114, 130), 'b': (50, 50, 64),
         'q': (130, 130, 140), 'f': (120, 120, 132), 'z': (60, 40, 80)}
    out = np.zeros((R, C, 3), np.uint8)
    for kk, c in F.items():
        out[k == kk] = c
    vor = Image.open(os.path.join(ROOT, 'assets', 'vorlagen', 'karte11_vorlage.png')).convert('RGB').resize((C * 8, R * 8))
    bild = Image.new('RGB', (C * 16 + 8, R * 8))
    bild.paste(vor, (0, 0))
    bild.paste(Image.fromarray(out).resize((C * 8, R * 8), 0), (C * 8 + 8, 0))
    bild.save(os.path.join(KARTE, 'layout_vergleich.png'))
    print('Karte 11 Layout %dx%d' % (C, R))


if __name__ == '__main__':
    main()
