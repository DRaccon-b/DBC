"""Karte 13 (Spiral Mountain: Machine City): Kachelraster nach der Vorlage -> maps/karte13/layout.json

  python3 tools/karte13_layout.py

Vorlage assets/vorlagen/karte13_vorlage.png (1280x1120 = 80x70 Kacheln a 16 px).
Zerstoerte Maschinenstadt: ringsum dieselbe Bergwand wie Karte 11/12, oben in der Mitte die Maschinenfestung (eine
Etage hoeher, Metallboden, Gitterring und Boss-Kreis in der Mitte, Treppe nach Sueden), links oben ein Industriehof,
rechts oben ein Hof mit Funkturm und Tanks, darunter ein Strassenraster mit Haeuserbloecken, unten der Bahnhofsplatz.
Klassen:  s Asphalt  g Gehweg/Pflaster  h Hof-Beton  m Festungsboden (Metall)  z Gitterrost  n Gras  p verseuchter Boden
          r Fels (Bergwand)
Hoehen:   1 Boden, 2 Festung, 5 Bergwand.
"""
import json, os
import numpy as np
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte13')
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
    k = np.full((R, C), 'g')
    h = np.ones((R, C), int)
    # ------------------------------------------------------------------ Bergwand ringsum (wie Karte 11/12)
    berg = np.zeros((R, C), bool)
    berg[0:3, :] = True
    berg[:, 0:3] = True
    berg[:, 77:80] = True
    berg[67:70, :] = True
    for (y0, y1, x1) in ((47, 49, 1), (58, 61, 1)):           # kleine Buchten links wie in der Vorlage
        berg[y0:y1 + 1, 2:3] = False
    berg[0:3, 66:69] = False                                  # Ausgang oben rechts (Teleporter)
    berg[67:70, 38:42] = False                                # Ausgang unten (Teleporter)
    k[berg] = 'r'
    h[berg] = 5
    # ------------------------------------------------------------------ Hoefe oben (heller Beton)
    k[3:29, 3:27] = 'h'
    k[3:29, 54:66] = 'h'
    k[3:29, 69:77] = 'h'
    for (x0, y0, x1, y1, sd) in ((5, 15, 9, 18, 1), (59, 19, 64, 24, 2)):
        blob(k, x0, y0, x1, y1, 'n', sd, 0.3)
    # ------------------------------------------------------------------ Maschinenfestung (eine Etage hoeher)
    k[3:26, 27:54] = 'm'
    h[3:26, 27:54] = 2
    for y in range(9, 21):                                    # Gitterring um den Boss-Kreis
        for x in range(34, 46):
            if y in (9, 20) or x in (34, 45):
                k[y, x] = 'z'
    treppen = [[38, 41, 2, 25]]
    # ------------------------------------------------------------------ Strassen
    for y0 in (29, 39, 49, 59):
        k[y0:y0 + 2, 3:77] = 's'
    for x0 in (11, 25, 53):
        k[29:67, x0:x0 + 2] = 's'
    k[28:67, 38:42] = 's'                                     # Hauptstrasse (Mittellinie zwischen Spalte 39 und 40)
    k[0:67, 66:69] = 's'                                      # Strasse vom oberen Ausgang
    k[11:29, 17:19] = 's'                                     # Zufahrt im Industriehof
    k[67:70, 38:42] = 's'
    # ------------------------------------------------------------------ verseuchter Boden in den Bloecken, Bahnhof
    for i, (x0, y0, x1, y1) in enumerate(((28, 32, 34, 37), (56, 32, 62, 37), (43, 42, 49, 46), (5, 43, 9, 46),
                                          (14, 52, 19, 56), (29, 52, 34, 57), (59, 43, 64, 47), (70, 44, 75, 48),
                                          (14, 61, 20, 65), (69, 62, 74, 65), (45, 31, 51, 35))):
        blob(k, x0, y0, x1, y1, 'p', 30 + i, 0.35, nur='g')
    k[61:67, 27:38] = 'z'                                     # Bahnhof: Gitterrost-Bahnsteige
    k[61:67, 42:53] = 'z'
    lay = {
        'groesse': [C, R], 'klassen': [''.join(r) for r in k], 'hoehe': [''.join(str(c) for c in r) for r in h],
        'treppen_sued': treppen, 'boss': [40.0, 15.0], 'hauptstrasse': [38, 41],
        'zebra': [[42, 43, 31, 'l'], [36, 37, 31, 'l'], [42, 43, 41, 'l'],
                  [36, 37, 41, 'l'], [36, 37, 51, 'l'], [42, 43, 51, 'l']],
        'teleporter': [{'x': 66, 'y': 0, 'b': 3, 'h': 2}, {'x': 38, 'y': 68, 'b': 4, 'h': 2}],
    }
    os.makedirs(KARTE, exist_ok=True)
    json.dump(lay, open(os.path.join(KARTE, 'layout.json'), 'w'), indent=0)
    F = {'s': (52, 56, 70), 'g': (100, 106, 118), 'h': (150, 160, 166), 'm': (52, 80, 96), 'z': (90, 100, 110),
         'n': (70, 120, 70), 'p': (80, 70, 100), 'r': (40, 30, 60)}
    out = np.zeros((R, C, 3), np.uint8)
    for kk, c in F.items():
        out[k == kk] = c
    vor = Image.open(os.path.join(ROOT, 'assets', 'vorlagen', 'karte13_vorlage.png')).convert('RGB').resize((C * 8, R * 8))
    bild = Image.new('RGB', (C * 16 + 8, R * 8))
    bild.paste(vor, (0, 0))
    bild.paste(Image.fromarray(out).resize((C * 8, R * 8), 0), (C * 8 + 8, 0))
    bild.save(os.path.join(KARTE, 'layout_vergleich.png'))
    print('Karte 13 Layout %dx%d' % (C, R))


if __name__ == '__main__':
    main()
