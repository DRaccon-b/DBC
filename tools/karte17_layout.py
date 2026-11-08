"""Karte 17 (Our War Game!), Neuaufbau im Stil von Karte 16 -> maps/karte17/layout.json

  python3 tools/karte17_layout.py

Vorlage assets/vorlagen/karte17_vorlage.png (2000x1406, verkleinert: 15,6 px je Kachel): zwei Raeume nebeneinander,
je 28x22 Kacheln, 4 Kacheln Abstand. Im Stil von Karte 16 werden sie zu zwei schwebenden Plattformen in der Leere
des Netzes (Randring mit cyan Kante, Metallfront mit Lichtfaeden, Datenstraenge und Fragmente in der Leere).
Karte 76x36 Kacheln: Raum links x 6-33, Raum rechts x 42-69, Reihen 6-27 (Ecken um 1 Kachel gestuft).

Marken je Raum (Raumkoordinaten aus der Vorlage, x/y ab linker oberer Raumecke):
  feld     Aufstellfeld 6x5 Kacheln mit Eckmarken   x 1-6, y 16-20   (beide Raeume)
  ankunft  2 cyan Pfeilkacheln (Ankunft)            x 1-2, y 21      (beide Raeume)
  kreis    Ringmarke in der Mitte                   x 14,  y 10      (nur links)
  ausgang  2x2 goldene Pfeilkacheln (Weg zum 2. Raum) x 25-26, y 9-10 (nur links)
Klassen:  .  Leere   p  Boden   r  Randring   f  Aufstellfeld   z  Pfeil cyan   g  Pfeil gold   o  Ringmarke
"""
import json, os
import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte17')
C, R = 76, 36
RAEUME = [(6, 6), (42, 6)]            # linke obere Ecke
RW, RH = 28, 22


def main():
    os.makedirs(KARTE, exist_ok=True)
    k = np.full((R, C), '.')
    for i, (x0, y0) in enumerate(RAEUME):
        k[y0:y0 + RH, x0:x0 + RW] = 'r'
        k[y0 + 1:y0 + RH - 1, x0 + 1:x0 + RW - 1] = 'p'
        for (cx, cy) in ((x0, y0), (x0 + RW - 1, y0), (x0, y0 + RH - 1), (x0 + RW - 1, y0 + RH - 1)):
            k[cy, cx] = '.'                                   # Ecken gestuft
        for (cx, cy) in ((x0 + 1, y0 + 1), (x0 + RW - 2, y0 + 1), (x0 + 1, y0 + RH - 2), (x0 + RW - 2, y0 + RH - 2)):
            k[cy, cx] = 'r'
        k[y0 + 16:y0 + 21, x0 + 1:x0 + 7] = 'f'
        k[y0 + 21, x0 + 1:x0 + 3] = 'z'
        if i == 0:
            k[y0 + 10, x0 + 14] = 'o'
            k[y0 + 9:y0 + 11, x0 + 25:x0 + 27] = 'g'
    h = np.where(k == '.', 0, 2)
    lay = {'groesse': [C, R], 'klassen': [''.join(z) for z in k], 'hoehe': [''.join(str(c) for c in z) for z in h],
           'raeume': RAEUME, 'raum': [RW, RH],
           'teleporter': [{'x': RAEUME[0][0] + 1, 'y': RAEUME[0][1] + 21, 'b': 2, 'h': 1, 'art': 'ankunft'},
                          {'x': RAEUME[1][0] + 1, 'y': RAEUME[1][1] + 21, 'b': 2, 'h': 1, 'art': 'ankunft'},
                          {'x': RAEUME[0][0] + 25, 'y': RAEUME[0][1] + 9, 'b': 2, 'h': 2, 'art': 'ausgang'}]}
    json.dump(lay, open(os.path.join(KARTE, 'layout.json'), 'w'), indent=0)
    F = {'.': (10, 14, 30), 'p': (52, 70, 104), 'r': (34, 48, 78), 'f': (70, 100, 130), 'z': (60, 200, 230),
         'g': (230, 180, 70), 'o': (230, 230, 240)}
    im = Image.new('RGB', (C * 8, R * 8))
    dr = ImageDraw.Draw(im)
    for y in range(R):
        for x in range(C):
            dr.rectangle((x * 8, y * 8, x * 8 + 7, y * 8 + 7), fill=F[k[y, x]], outline=(0, 0, 0))
    im.save(os.path.join(KARTE, 'layout_vorschau.png'))
    print('Karte 17 Layout %dx%d, begehbar %d Kacheln' % (C, R, int((k != '.').sum())))


if __name__ == '__main__':
    main()
