"""Karte 19 (Revenge), drittes Gebiet des Keramon-Dungeons -> maps/karte19/layout.json

  python3 tools/karte19_layout.py

Vorlage assets/vorlagen/karte19_vorlage.png (2048x1472, echtes 16er-Raster): zwei Raeume je 28x24 Kacheln, 4 Kacheln
Abstand. Wie Karte 16/17 schweben beide Raeume als Plattformen in der Leere des Netzes.
  links:  Network-Stil (Plattenboden wie Karte 16)
  rechts: Hafen - oben 6 Reihen Wasserbecken (Raumreihen 1-6), darunter Pflaster mit Kaikante (Reihe 7)
Karte 76x38 Kacheln: Raum links x 6-33, Raum rechts x 42-69, Reihen 6-29.

Marken (Raumkoordinaten aus der Vorlage, Kachel fuer Kachel vermessen):
  beide:  Aufstellfeld x 1-6, y 18-22 · Ankunft (2 cyan Pfeile) x 1-2, y 23
  links:  3 Bodenplatten (6,12) (22,12) (14,18) · Ausgang (2x2 goldene Pfeile) x 25-26, y 11-12
  rechts: Ringmarke (14,8)
Klassen:  .  Leere  p  Boden  r  Randring  f  Aufstellfeld  z  Pfeil cyan  g  Pfeil gold  o  Ringmarke
          b  Bodenplatte  w  Wasser  k  Kaikante  h  Pflaster (Hafen)
"""
import json, os
import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte19')
C, R = 76, 38
RAEUME = [(6, 6), (42, 6)]
RW, RH = 28, 24
PLATTEN = [(6, 12), (22, 12), (14, 18)]


def main():
    os.makedirs(KARTE, exist_ok=True)
    k = np.full((R, C), '.')
    for i, (x0, y0) in enumerate(RAEUME):
        innen = 'p' if i == 0 else 'h'
        k[y0:y0 + RH, x0:x0 + RW] = 'r'
        k[y0 + 1:y0 + RH - 1, x0 + 1:x0 + RW - 1] = innen
        if i == 0:                                              # Network-Raum: Ecken gestuft
            for (cx, cy) in ((x0, y0), (x0 + RW - 1, y0), (x0, y0 + RH - 1), (x0 + RW - 1, y0 + RH - 1)):
                k[cy, cx] = '.'
            for (cx, cy) in ((x0 + 1, y0 + 1), (x0 + RW - 2, y0 + 1), (x0 + 1, y0 + RH - 2), (x0 + RW - 2, y0 + RH - 2)):
                k[cy, cx] = 'r'
        # Hafen (Nutzerwunsch): Kaimauer ringsum geschlossen, volle Ecken
        k[y0 + 18:y0 + 23, x0 + 1:x0 + 7] = 'f'
        k[y0 + 23, x0 + 1:x0 + 3] = 'z'
        if i == 0:
            for (px, py) in PLATTEN:
                k[y0 + py, x0 + px] = 'b'
            k[y0 + 11:y0 + 13, x0 + 25:x0 + 27] = 'g'
        else:
            k[y0 + 1:y0 + 7, x0 + 1:x0 + RW - 1] = 'w'          # Hafenbecken (der Randring ist die Beckenmauer)
            k[y0 + 7, x0 + 1:x0 + RW - 1] = 'k'
            k[y0 + 8, x0 + 14] = 'o'
    h = np.where(k == '.', 0, np.where(k == 'w', 1, 2))
    lay = {'groesse': [C, R], 'klassen': [''.join(z) for z in k], 'hoehe': [''.join(str(c) for c in z) for z in h],
           'raeume': RAEUME, 'raum': [RW, RH], 'platten': PLATTEN,
           'teleporter': [{'x': RAEUME[0][0] + 1, 'y': RAEUME[0][1] + 23, 'b': 2, 'h': 1, 'art': 'ankunft'},
                          {'x': RAEUME[1][0] + 1, 'y': RAEUME[1][1] + 23, 'b': 2, 'h': 1, 'art': 'ankunft'},
                          {'x': RAEUME[0][0] + 25, 'y': RAEUME[0][1] + 11, 'b': 2, 'h': 2, 'art': 'ausgang'}]}
    json.dump(lay, open(os.path.join(KARTE, 'layout.json'), 'w'), indent=0)
    F = {'.': (10, 14, 30), 'p': (52, 70, 104), 'r': (34, 48, 78), 'f': (70, 100, 130), 'z': (60, 200, 230),
         'g': (230, 180, 70), 'o': (230, 230, 240), 'b': (180, 190, 200), 'w': (50, 90, 130), 'k': (200, 200, 190),
         'h': (137, 154, 155)}
    im = Image.new('RGB', (C * 8, R * 8))
    dr = ImageDraw.Draw(im)
    for y in range(R):
        for x in range(C):
            dr.rectangle((x * 8, y * 8, x * 8 + 7, y * 8 + 7), fill=F[k[y, x]], outline=(0, 0, 0))
    im.save(os.path.join(KARTE, 'layout_vorschau.png'))
    print('Karte 19 Layout %dx%d, begehbar %d Kacheln' % (C, R, int((~np.isin(k, ['.', 'w'])).sum())))


if __name__ == '__main__':
    main()
