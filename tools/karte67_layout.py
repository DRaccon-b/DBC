"""Karte 67 - Colosseum (A01 Nr. 4, Nutzer): roemisches Steinkolosseum ohne Vorlage -> maps/karte67/layout.json

  python3 tools/karte67_layout.py && python3 tools/karte67_bauen.py

Aufbau (Nutzer: in der Mitte die Arena, ringsum die Tribuene, auf der man sich bewegen kann):
  - Elliptisches Bauwerk (an den Scheiteln abgeflacht, damit Treppen und Tore an geraden Kanten liegen).
  - Arena (Sand) auf Ebene 0, darum drei Tribuenenringe (Sitzstufen aus Travertin) auf Ebene 1, 2, 3 - begehbar,
    nach aussen ansteigend; Nordtreppe und Suedtreppe verbinden Arena und alle Ringe (Achse x = Mitte).
  - Aeussere Fassade (Ebene 4, gesperrt) mit Arkaden.
  - Tore im Westen und Osten (Hauptachse): ebenerdige Gaenge durch Fassade und Ringe bis in die Arena.
  - Aussen ein gepflasterter Platz (Travertinplatten), Wiese mit Baumguertel am Kartenrand, Teleporter im Sueden.

Klassen:  a Arena-Sand  1/2/3 Tribuenenringe  f Fassade (gesperrt)  g Torgang  z Platz  n Wiese/Guertel
          t Treppe  T Teleporter
Hoehen:   0 Arena, Torgang, Platz, Wiese  1..3 Ringe  4 Fassade
"""
import json, os
import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte67')
C, R, T = 80, 76, 16
CX, CY = 40, 32                          # Mitte (Kachelkante)
A, B = 29.0, 22.0                        # Halbachsen der Fassade aussen (ohne Abflachung)
FLACH_X, FLACH_Y = 4.0, 3.0              # gerade Stuecke an den Scheiteln (Treppen N/S, Tore W/O)
GRENZEN = [0.38, 0.54, 0.70, 0.86, 1.0]  # Arena | Ring 1 | Ring 2 | Ring 3 | Fassade
TOR_H = (CY - 2, CY + 1)                 # Torgaenge W/O: Reihen (4 breit)
TREPPE_X = (CX - 2, CX + 1)              # Treppen N/S: Spalten (4 breit)
TELEPORTER = {'x': CX - 2, 'y': R - 3, 'b': 4, 'h': 2}


def radius():
    yy, xx = np.mgrid[0:R, 0:C].astype(float)
    dx = np.maximum(0, np.abs(xx + 0.5 - CX) - FLACH_X)
    dy = np.maximum(0, np.abs(yy + 0.5 - CY) - FLACH_Y)
    return np.sqrt((dx / A) ** 2 + (dy / B) ** 2)


def main():
    os.makedirs(KARTE, exist_ok=True)
    r = radius()
    k = np.full((R, C), 'z', '<U1')
    hp = np.zeros((R, C), int)
    namen = ['a', '1', '2', '3', 'f']
    for i in range(len(GRENZEN) - 1, -1, -1):
        m = r < GRENZEN[i]
        k[m] = namen[i]
        hp[m] = i
    # Wiese mit Baumguertel am Kartenrand (4 Kacheln), Weg vom Teleporter zum Platz
    rand = np.zeros((R, C), bool)
    rand[:4, :] = rand[-4:, :] = True
    rand[:, :4] = rand[:, -4:] = True
    k[rand] = 'n'
    tx0 = TELEPORTER['x']
    k[R - 4:, tx0 - 1:tx0 + 5] = 'z'                                  # Ausgang in voller Breite durch den Guertel
    # Torgaenge West/Ost: ebenerdig durch Fassade und Ringe bis in die Arena
    y0, y1 = TOR_H
    gang = np.zeros((R, C), bool)
    gang[y0:y1 + 1, :] = True
    gang &= (k != 'n') & (k != 'z') & (k != 'a')
    k[gang] = 'g'
    hp[gang] = 0
    # Treppen N/S auf der Achse: je Ringkante eine Treppe (Frontreihe = erste Reihe des hoeheren Rings)
    x0, x1 = TREPPE_X
    treppen = []
    spalte = hp[:, CX]
    for y in range(1, R):
        if spalte[y - 1] > spalte[y] and spalte[y - 1] <= 3 and spalte[y] >= 0 and y < CY:   # Nordhaelfte: hoeher im Norden
            # Front liegt in der tieferen Flaeche: Treppe in der ersten Reihe der tieferen Ebene
            treppen.append([x0, x1, y, 's'])
        if spalte[y] > spalte[y - 1] and spalte[y] <= 3 and y > CY:  # Suedhaelfte: hoeher im Sueden
            treppen.append([x0, x1, y - 1, 'n'])
    for (a0, a1, ry, ri) in treppen:
        if ri == 's':
            k[ry, a0:a1 + 1] = 't'
    lay = {'groesse': [C, R], 'klassen': [''.join(z) for z in k], 'hoehe': [''.join(str(c) for c in z) for z in hp],
           'mitte': [CX, CY], 'achsen': [A, B], 'flach': [FLACH_X, FLACH_Y], 'grenzen': GRENZEN,
           'treppen': treppen, 'tore': [TOR_H[0], TOR_H[1]], 'teleporter': [TELEPORTER]}
    json.dump(lay, open(os.path.join(KARTE, 'layout.json'), 'w'), indent=0)
    F = {'a': (214, 190, 140), '1': (200, 194, 176), '2': (184, 178, 160), '3': (166, 160, 142), 'f': (120, 110, 96),
         'g': (150, 140, 120), 'z': (190, 184, 170), 'n': (80, 140, 60), 't': (240, 170, 60)}
    S_ = 8
    im = Image.new('RGB', (C * S_, R * S_))
    dr = ImageDraw.Draw(im)
    for y in range(R):
        for x in range(C):
            dr.rectangle((x * S_, y * S_, x * S_ + S_ - 1, y * S_ + S_ - 1), fill=F[k[y, x]])
    im.save(os.path.join(KARTE, 'layout_vergleich.png'))
    print('Karte 67 Layout %dx%d, %d Treppen' % (C, R, len(treppen)), treppen)


if __name__ == '__main__':
    main()
