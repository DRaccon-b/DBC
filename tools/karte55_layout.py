"""Karte 55 (Hurricane Landing), Film "Digimon Hurricane Landing!!" Teil 1 -> maps/karte55/layout.json

  python3 tools/karte55_layout.py

Zwei Raeume wie Karte 19 (je 28x24 Kacheln, 8 Kacheln Abstand), schweben als Plattformen in der Leere des Netzes.
  links:  New York - Wendigomons erstes Auftauchen. Nordrand Hochhausfassaden (gesperrt), Gehweg, breite Avenue
          (4 Spuren, Mittellinie) mit Zebrastreifen, suedlicher Gehweg mit Aufstellfeld.
  rechts: Colorado-Landstrasse - Kampf gegen Wendigomon. Praerie (trockenes Gras), Landstrasse in Boegen mit
          45-Grad-Stufen (Regel 6/6b), Bankett aus Schotter, Weidezaeune folgen spaeter als Objekte.
Karte 76x38 Kacheln: Raum links x 6-33, Raum rechts x 42-69, Reihen 6-29.

Marken (Raumkoordinaten, wie Karte 19):
  beide:  Aufstellfeld x 1-6, y 18-22 · Ankunft (2 cyan Pfeile) x 1-2, y 23
  links:  Ringmarke (Gegner) (14,11) auf der Avenue · Ausgang (2x2 gold) x 25-26, y 10-11 (auf der Avenue)
  rechts: Ringmarke (Gegner) auf der Landstrasse
Klassen:  .  Leere  r  Randring  f  Aufstellfeld  z  Pfeil cyan  g  Pfeil gold  o  Ringmarke
          x  Fassade (gesperrt)  s  Gehweg  b  Bordstein  a  Asphalt  m  Mittellinie  c  Zebrastreifen
          q  Praerie  l  Landstrasse  e  Bankett (Schotter)
"""
import json, os
import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte55')
C, R = 76, 38
RAEUME = [(6, 6), (42, 6)]
RW, RH = 28, 24
# Landstrasse: Mittellinie in Raumkoordinaten (Kachelmitten), Breite 4 Kacheln, Bankett 1 Kachel
STRASSE = [(-1, 7.5), (6, 7.5), (11, 11.5), (17, 11.5), (22, 15.5), (28, 15.5)]


def abstand_polylinie(px, py, pts):
    d = np.full(px.shape, 1e9)
    for (x1, y1), (x2, y2) in zip(pts[:-1], pts[1:]):
        vx, vy = x2 - x1, y2 - y1
        t = np.clip(((px - x1) * vx + (py - y1) * vy) / (vx * vx + vy * vy), 0, 1)
        d = np.minimum(d, np.hypot(px - (x1 + t * vx), py - (y1 + t * vy)))
    return d


def main():
    os.makedirs(KARTE, exist_ok=True)
    k = np.full((R, C), '.')
    for i, (x0, y0) in enumerate(RAEUME):
        k[y0:y0 + RH, x0:x0 + RW] = 'r'
        sub = k[y0 + 1:y0 + RH - 1, x0 + 1:x0 + RW - 1]          # Innenflaeche, Raumkoordinate = Index + 1
        if i == 0:                                               # ---------------- New York
            sub[:] = 's'
            sub[0:4, :] = 'x'                                    # Fassaden Reihen 1-4
            sub[5, :] = 'b'                                      # Bordstein Nord (Reihe 6)
            sub[6:15, :] = 'a'                                   # Avenue Reihen 7-15
            sub[10, :] = 'm'                                     # Mittellinie Reihe 11
            sub[15, :] = 'b'                                     # Bordstein Sued (Reihe 16)
            sub[6:15, 9:12] = 'c'                                # Zebrastreifen Spalten 10-12
            sub[10, 9:12] = 'c'
        else:                                                    # ---------------- Colorado
            yy, xx = np.mgrid[1:RH - 1, 1:RW - 1].astype(float)
            d = abstand_polylinie(xx + 0.5, yy + 0.5, STRASSE)
            sub[:] = 'q'
            sub[d <= 3.0] = 'e'
            sub[d <= 2.0] = 'l'
        k[y0 + 18:y0 + 23, x0 + 1:x0 + 7] = 'f'
        k[y0 + 23, x0 + 1:x0 + 3] = 'z'
        if i == 0:
            k[y0 + 11, x0 + 14] = 'o'
            k[y0 + 10:y0 + 12, x0 + 25:x0 + 27] = 'g'
        else:
            k[y0 + 12, x0 + 14] = 'o'
    h = np.where(k == '.', 0, 2)
    lay = {'groesse': [C, R], 'klassen': [''.join(z) for z in k], 'hoehe': [''.join(str(c) for c in z) for z in h],
           'raeume': RAEUME, 'raum': [RW, RH], 'strasse': STRASSE,
           'teleporter': [{'x': RAEUME[0][0] + 1, 'y': RAEUME[0][1] + 23, 'b': 2, 'h': 1, 'art': 'ankunft'},
                          {'x': RAEUME[1][0] + 1, 'y': RAEUME[1][1] + 23, 'b': 2, 'h': 1, 'art': 'ankunft'},
                          {'x': RAEUME[0][0] + 25, 'y': RAEUME[0][1] + 10, 'b': 2, 'h': 2, 'art': 'ausgang'}]}
    json.dump(lay, open(os.path.join(KARTE, 'layout.json'), 'w'), indent=0)
    F = {'.': (10, 14, 30), 'r': (34, 48, 78), 'f': (70, 100, 130), 'z': (60, 200, 230), 'g': (230, 180, 70),
         'o': (240, 60, 60), 'x': (120, 96, 84), 's': (170, 168, 160), 'b': (210, 210, 205), 'a': (62, 64, 70),
         'm': (220, 190, 60), 'c': (235, 235, 235), 'q': (176, 160, 92), 'l': (80, 80, 84), 'e': (150, 132, 108)}
    S = 12
    im = Image.new('RGB', (C * S, R * S))
    dr = ImageDraw.Draw(im)
    for y in range(R):
        for x in range(C):
            dr.rectangle((x * S, y * S, x * S + S - 1, y * S + S - 1), fill=F[k[y, x]], outline=(0, 0, 0))
    im.save(os.path.join(KARTE, 'layout_vorschau.png'))
    print('Karte 55 Layout %dx%d, begehbar %d Kacheln' % (C, R, int((~np.isin(k, ['.', 'x'])).sum())))


if __name__ == '__main__':
    main()
