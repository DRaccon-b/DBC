"""Karte 09 (Vamdemon's Keep): Kachelraster aus der Vorlage -> maps/karte09/layout.json

  python3 tools/karte09_layout.py

Vorlage assets/vorlagen/karte09_vorlage.png (1440x1376 = 90x86 Kacheln a 16 px).
Oben das Schloss (Raeume, Mauern, Teppiche), darunter Burggraben mit Zugbruecke, unten der Friedhof.
Klassen:  i Steinboden  c roter Teppich  v violetter Teppich  g Gras  h dunkles Gras  e Beeterde
          w Weg  x Wasser (Graben, Teiche)  f Felsplateau  r Fels (Rand)
Hoehen:   0 Wasser, 1 Boden (Schloss innen und Friedhof), 2 Felsplateaus, 3 Schlossmauern, 7 Felsrand.
"""
import json, os, sys
import numpy as np
from PIL import Image, ImageFilter

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte09')
T = 16
C, R = 90, 86
ZENTREN = {'.': (56, 70, 56), ',': (42, 56, 50), 'i': (98, 112, 126), 'I': (84, 98, 112), '#': (60, 64, 88),
           'r': (62, 44, 44), 'w': (98, 84, 70), '~': (0, 0, 28), 'c': (112, 14, 42), 'v': (56, 28, 70),
           's': (70, 70, 70), 'b': (98, 98, 112)}


def vorlage_klassen():
    im = np.array(Image.open(os.path.join(ROOT, 'assets', 'vorlagen', 'karte09_vorlage.png')).convert('RGB')).astype(float)
    med = np.zeros((R, C, 3))
    for y in range(R):
        for x in range(C):
            med[y, x] = np.median(im[y * T:(y + 1) * T, x * T:(x + 1) * T].reshape(-1, 3), axis=0)
    ks = list(ZENTREN)
    cen = np.array([ZENTREN[k] for k in ks], float)
    return np.array(ks)[((med[:, :, None] - cen[None, None]) ** 2).sum(-1).argmin(-1)]


def glaetten(m, n=1):
    k = Image.fromarray((m * 255).astype(np.uint8))
    for _ in range(n):
        k = k.filter(ImageFilter.ModeFilter(3))
    return np.array(k) > 127


def main():
    v = vorlage_klassen()
    yy, xx = np.mgrid[0:R, 0:C]
    h = np.ones((R, C), int)
    k = np.full((R, C), 'g')
    # ------------------------------------------------------------------ Schloss (Reihen 0-39)
    mauer = np.zeros((R, C), bool)
    mauer[0:2, :] = True
    mauer[0:37, 0:2] = mauer[0:37, 88:90] = True
    mauer[2:15, 10:12] = mauer[2:15, 44:46] = True
    mauer[2:35, 61:63] = True
    mauer[15:17, 0:63] = True
    mauer[17:35, 54:56] = True
    mauer[35:37, :] = True
    mauer[15:17, 25:30] = False                    # Tor zwischen Portalhalle und grossem Saal
    mauer[26:30, 54:56] = mauer[26:30, 61:63] = False   # Durchgang zum Ritualsaal
    mauer[35:37, 25:30] = False                    # Haupttor zur Zugbruecke
    h[mauer] = 3
    k[0:40] = 'i'
    k[5:15, 2:10] = 'g'                            # Garten links oben mit Beet
    k[8:12, 3:9] = 'e'
    k[5:15, 46:61] = 'g'                           # Gartenhof mit Teich
    k[(yy >= 6) & (yy <= 12) & (xx >= 47) & (xx <= 58) & (v == ',')] = 'h'
    k[10:13, 46:51] = 'x'
    k[10:15, 26:29] = 'c'                          # roter Teppich: Portal -> Tor -> grosser Saal -> Haupttor
    k[15:40, 26:29] = 'c'
    k[27:29, 3:54] = 'c'
    k[27:29, 54:67] = 'v'                          # violetter Teppich zum Ritualsaal
    rahmen = ((xx >= 66) & (xx <= 84) & (yy >= 12) & (yy <= 30)) & ~((xx >= 67) & (xx <= 83) & (yy >= 13) & (yy <= 29))
    k[rahmen] = 'v'
    # ------------------------------------------------------------------ Burggraben (Reihen 40-42)
    k[40:43, :] = 'x'
    h[40:43, :] = 0
    # ------------------------------------------------------------------ Friedhof (Reihen 43-85)
    aussen = yy >= 43
    k[aussen & np.isin(v, [',']) ] = 'h'
    k[aussen & (v == 'w')] = 'w'
    wasser = aussen & (v == '~')
    wasser = glaetten(wasser) | wasser
    k[wasser] = 'x'
    h[wasser] = 0
    wasser[56:65, 77:81] |= (xx[56:65, 77:81] >= 77)    # unter dem Steg rechts ist Wasser
    k[wasser] = 'x'
    h[wasser] = 0
    plateau = aussen & np.isin(v, ['I', '#'])
    plateau = glaetten(plateau)
    h[plateau] = 2
    k[plateau] = 'f'
    fels = aussen & (v == 'r')
    fels = glaetten(fels)
    fels[43:84, 0:2] = True
    fels[43:69, 0:3] = True
    fels[74:84, 0:3] = True
    fels[43:86, 87:90] = True
    fels[84:86, :] = True
    fels[69:74, 0:3] = False                       # Weg zum Teleporter links
    fels[46:53, 85:90] &= ~plateau[46:53, 85:90]
    h[fels] = 7
    k[fels] = 'r'
    k[70:74, 0:46] = 'w'
    k[(yy >= 43) & (yy <= 58) & (xx >= 25) & (xx <= 31) & (k == 'g')] = 'w'   # Weg von der Zugbruecke
    # Aufraeumen kleiner Splitter auf dem Friedhof
    for art in 'hw':
        m = (k == art) & aussen
        mm = glaetten(m)
        k[m & ~mm & (h == 1)] = 'g'
        k[mm & ~m & (k == 'g') & (h == 1)] = art
    lay = {
        'groesse': [C, R], 'klassen': [''.join(r) for r in k], 'hoehe': [''.join(str(c) for c in r) for r in h],
        'zugbruecke': [26, 40, 28, 42],                 # (x0, y0, x1, y1)
        'bruecken': [],                                 # Holzbruecke in der Mitte entfernt (Nutzer)
        'stege': [[78, 56, 79, 64]],                    # senkrecht (x0, y0, x1, y1)
        'teleporter': [{'x': 0, 'y': 69, 'b': 2, 'h': 4}],
    }
    os.makedirs(KARTE, exist_ok=True)
    json.dump(lay, open(os.path.join(KARTE, 'layout.json'), 'w'), indent=0)
    F = {'i': (100, 110, 125), 'c': (130, 20, 40), 'v': (80, 40, 110), 'g': (70, 90, 60), 'h': (45, 60, 45),
         'e': (90, 65, 45), 'w': (120, 100, 80), 'x': (10, 10, 40), 'f': (110, 110, 120), 'r': (80, 50, 50)}
    out = np.zeros((R, C, 3), np.uint8)
    for kk, c in F.items():
        out[k == kk] = c
    out[h == 3] = (40, 44, 60)
    vor = Image.open(os.path.join(ROOT, 'assets', 'vorlagen', 'karte09_vorlage.png')).convert('RGB').resize((C * 8, R * 8))
    bild = Image.new('RGB', (C * 16 + 8, R * 8))
    bild.paste(vor, (0, 0))
    bild.paste(Image.fromarray(out).resize((C * 8, R * 8), 0), (C * 8 + 8, 0))
    bild.save(os.path.join(KARTE, 'layout_vergleich.png'))
    print('Karte 09 Layout %dx%d' % (C, R))


if __name__ == '__main__':
    main()
