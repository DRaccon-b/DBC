"""Karte 14 (Spiral Mountain: Summit): Kachelraster nach der Vorlage -> maps/karte14/layout.json

  python3 tools/karte14_layout.py

Vorlage assets/vorlagen/karte14_vorlage.png (1280x1120 = 80x70 Kacheln a 16 px).
Gipfel des Spiral Mountain (letzte Karte der Reihe): ringsum dieselbe Bergwand wie Karte 11-13, oben das
Gauklerschloss mit Mauer und zwei Tuermen, davor das rote Boss-Feld (eine Etage hoeher, Schachbrettrahmen, Spirale
in der Mitte, Treppe nach Sueden), der Schachbrettweg mit Statuen und Bannern bis zum Treppenplatz und zum
Teleporter unten, rechts oben der erhoehte Portalplatz (dunkles Portal, Treppe), verstreute Felsnasen, dunkler
Schotter und violette Kristallflecken.
Klassen:  d Gipfelstein (Pflaster)  k dunkler Schotter  p Kristallboden (violett)  v Felsnase (oben)  r Fels (Wand)
          c roter Teppich  z Schachbrett (Harlekin)  b dunkle Ziegel (Treppenplatz)  f Portalplatz (Steinplatten)
Hoehen:   1 Boden, 2 Boss-Feld/Portalplatz/Felsnasen, 5 Bergwand.
"""
import json, os
import sys
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import karte14_form

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte14')
C, R = 80, 70


def blob(k, x0, y0, x1, y1, art, seed, rund=0.35, nur=None):
    rs = np.random.RandomState(seed)
    cx, cy, rx, ry = (x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0 + 1) / 2, (y1 - y0 + 1) / 2
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            d = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
            if d <= 1 - rund * rs.rand() * (d > 0.45) and (nur is None or k[y, x] in nur):
                k[y, x] = art


def main():
    k = np.full((R, C), 'd')
    h = np.ones((R, C), int)
    # ------------------------------------------------------------------ Bergwand ringsum (wie Karte 11-13)
    berg = np.zeros((R, C), bool)
    berg[0:4, :] = True
    berg[:, 0:3] = True
    berg[:, 77:80] = True
    berg[66:70, :] = True
    berg[4:8, 0:6] = True                                    # Felsnase oben links an der Wand
    berg[8:25, 3:4] = True
    for (x0, x1, y0) in ((3, 8, 62), (9, 15, 64), (16, 21, 65), (30, 36, 65), (43, 49, 65), (57, 63, 64), (70, 76, 63)):
        berg[y0:, x0:x1 + 1] = True                          # gestufte Unterkante wie in der Vorlage
    for (y0, y1) in ((5, 9), (20, 27), (44, 50)):
        berg[y0:y1 + 1, 76:77] = True
    berg[66:70, 38:42] = False                               # Ausgang unten (Teleporter)
    berg[4:8, 19:53] = False                                 # Schlosshof (Schloss/Mauern als Objekte)
    k[berg] = 'r'
    h[berg] = 5
    # ------------------------------------------------------------------ dunkler Schotter, Kristallboden
    for i, (x0, y0, x1, y1) in enumerate(((11, 5, 17, 10), (15, 20, 20, 27), (5, 41, 10, 45), (22, 39, 27, 42),
                                          (63, 6, 68, 15), (14, 27, 21, 31), (43, 27, 52, 31), (6, 51, 11, 57),
                                          (55, 32, 62, 38), (68, 40, 75, 47), (16, 51, 21, 56), (46, 52, 52, 56),
                                          (56, 25, 60, 28))):
        blob(k, x0, y0, x1, y1, 'k', 20 + i, 0.4, nur='d')
    for i, (x0, y0, x1, y1) in enumerate(((17, 8, 22, 11), (5, 19, 10, 23), (54, 14, 58, 17), (63, 22, 69, 28),
                                          (9, 38, 15, 42), (20, 36, 26, 38), (47, 32, 51, 36), (67, 43, 73, 46))):
        blob(k, x0, y0, x1, y1, 'p', 40 + i, 0.3, nur='dk')
    # ------------------------------------------------------------------ Felsnasen (erhoeht, organisch)
    FELS = [(7, 10, 14, 15), (20, 25, 24, 29), (8, 34, 17, 38), (11, 44, 17, 47), (19, 50, 28, 54), (57, 21, 61, 26),
            (66, 27, 73, 32), (58, 37, 66, 43), (61, 48, 66, 52)]
    for i, f in enumerate(FELS):
        blob(k, *f, 'v', 60 + i, 0.45, nur='dkp')
    h[k == 'v'] = 2
    # ------------------------------------------------------------------ Boss-Feld (eine Etage hoeher) mit Schachbrett
    form = os.environ.get('BOSSFORM', 'achteck')             # Form siehe karte14_form.py (Saum/Ring im Bau-Skript)
    yy, xx = np.mgrid[0:R, 0:C]
    feld = karte14_form.maske(form, (xx + 0.5) * 16, (yy + 0.5) * 16)
    feld[:7] = False
    k[feld] = 'c'
    h[feld] = 2
    treppen = [[38, 41, 2, 28]]
    # ------------------------------------------------------------------ Schachbrettweg, Treppenplatz unten
    k[30:69, 38:42] = 'z'
    yy, xx = np.mgrid[0:R, 0:C]
    platz = (np.abs(xx + 0.5 - 40) <= 8.5 - np.maximum(0, 56 - yy) * 0.9) & (yy >= 52) & (yy <= 64)
    k[platz & (k != 'r') & (k != 'z')] = 'b'
    # ------------------------------------------------------------------ Portalplatz rechts oben (erhoeht)
    # nicht rechteckig: Kern mit abgeschraegten Ecken, vorne mittig eine runde Apsis unter dem Portal (Treppe dort),
    # dazu ein paar ausgebrochene Kanten und Felsnasen
    pc = (yy + 0.5 - 9.5) ** 2 / 5.6 ** 2 + (xx + 0.5 - 62.0) ** 2 / 5.6 ** 2 <= 1        # Apsis
    kern = (xx >= 54) & (xx <= 69) & (yy >= 4) & (yy <= 11)
    kern &= ~(((69 - xx) + (yy - 4) < 2) | ((xx - 54) + (11 - yy) < 3) | ((69 - xx) + (11 - yy) < 3))  # Ecken schraeg
    platz_p = (kern | (pc & (yy >= 4))) & (yy <= 14)
    platz_p[14, 60:64] = True                                            # gerader Absatz fuer die Treppe
    rs_p = np.random.RandomState(77)
    for (y_, x_) in ((6, 54), (9, 54), (5, 69), (8, 69), (10, 69)):     # ausgebrochene Kanten
        platz_p[y_:y_ + rs_p.randint(1, 3), x_] = False
    platz_p[7:9, 53] = True                                              # Felsnase links
    platz_p &= (k != 'r') | (yy >= 4)
    k[platz_p] = 'f'
    h[platz_p] = 2
    treppen.append([61, 62, 2, 14])
    lay = {
        'groesse': [C, R], 'klassen': [''.join(r) for r in k], 'hoehe': [''.join(str(c) for c in r) for r in h],
        'treppen_sued': treppen, 'boss': [40.5, 18.0], 'bossform': form, 'portal': [62.0, 8.0], 'felsnasen': FELS,
        'teleporter': [{'x': 38, 'y': 68, 'b': 4, 'h': 2}],
    }
    os.makedirs(KARTE, exist_ok=True)
    json.dump(lay, open(os.path.join(KARTE, 'layout.json'), 'w'), indent=0)
    F = {'d': (100, 98, 112), 'k': (62, 60, 72), 'p': (70, 50, 100), 'v': (130, 134, 150), 'r': (30, 30, 50),
         'c': (150, 30, 40), 'z': (150, 130, 200), 'b': (64, 60, 72), 'f': (120, 124, 136)}
    out = np.zeros((R, C, 3), np.uint8)
    for kk, c in F.items():
        out[k == kk] = c
    vor = Image.open(os.path.join(ROOT, 'assets', 'vorlagen', 'karte14_vorlage.png')).convert('RGB').resize((C * 8, R * 8))
    bild = Image.new('RGB', (C * 16 + 8, R * 8))
    bild.paste(vor, (0, 0))
    bild.paste(Image.fromarray(out).resize((C * 8, R * 8), 0), (C * 8 + 8, 0))
    bild.save(os.path.join(KARTE, 'layout_vergleich.png'))
    print('Karte 14 Layout %dx%d' % (C, R))


if __name__ == '__main__':
    main()
