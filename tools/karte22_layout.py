"""Karte 22 - Digicasino, Layout (ohne Vorlage, nach Beschreibung des Nutzers) -> maps/karte22/layout.json

  python3 tools/karte22_layout.py

Etwa halb so gross wie eine Karte des Keramon-Dungeons (Karte 16/17/19: ~70x38) -> 52x28 Kacheln (832x448 px).
Stil wie Karte 16/17: schwebende Plattformen in der Leere des Netzes mit Datenstraengen und Fragmenten.

Aufbau:
  - Casino-Plattform (36x19) in der Mitte oben, Ecken gestuft, Randring wie Karte 17.
  - Ankunftsplattform unten (8x3) mit cyan Pfeilen, schmaler Steg (4 breit) hinauf zum Eingang.
  - Innen: roter Teppich als Mittelgang vom Eingang zur Preistheke (oben), links und rechts Spielautomaten-Reihen,
    in der Mitte links/rechts je ein Spieltisch-Bereich (Roulette / Karten), oben die Preistheke mit Buehne,
    dahinter der goldene Ausgang (VIP-Tuer).
  - Zwei kleine Neben-Plattformen links/rechts (Jackpot-Inseln) ueber kurze Stege verbunden.

Klassen:  .  Leere   p  Boden   r  Randring   t  Teppich   s  Automatenreihe   k  Spieltisch-Bereich
          b  Buehne/Theke   z  Pfeil cyan (Ankunft)   g  Pfeil gold (Ausgang)   j  Jackpot-Insel
"""
import json, os
import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte22')
C, R = 64, 36                    # Nutzer: groesser, mit mehr freiem Raum (vorher 52x28)
CASINO = (8, 3, 55, 27)          # x0, y0, x1, y1 (inklusive)
ANKUNFT = (28, 30, 35, 32)
STEG = (30, 28, 33, 29)
INSELN = [(1, 12, 5, 17), (58, 12, 62, 17)]
INSEL_STEGE = [(6, 14, 7, 15), (56, 14, 57, 15)]
ACHSE = 31.5                     # Mittelachse (Spalten 31/32)


def rechteck(k, r, art):
    x0, y0, x1, y1 = r
    k[y0:y1 + 1, x0:x1 + 1] = art


def plattform(k, r):
    x0, y0, x1, y1 = r
    k[y0:y1 + 1, x0:x1 + 1] = 'r'
    k[y0 + 1:y1, x0 + 1:x1] = 'p'
    for (cx, cy) in ((x0, y0), (x1, y0), (x0, y1), (x1, y1)):
        k[cy, cx] = '.'                                           # Ecken gestuft


def main():
    os.makedirs(KARTE, exist_ok=True)
    k = np.full((R, C), '.')
    plattform(k, CASINO)
    for r in INSELN:
        plattform(k, r)
    for r in INSEL_STEGE + [STEG]:
        rechteck(k, r, 'p')
    plattform(k, ANKUNFT)
    k[CASINO[3], STEG[0]:STEG[2] + 1] = 'p'                      # Eingang im Randring
    k[ANKUNFT[1], STEG[0]:STEG[2] + 1] = 'p'
    for (x0, y0, x1, y1) in INSEL_STEGE:                          # Durchgaenge in den Ringen
        k[y0:y1 + 1, x0 - 1] = 'p'; k[y0:y1 + 1, x1 + 1] = 'p'
    # Innenaufteilung (symmetrisch zur Achse 25.5 -> Spalte x <-> 51 - x)
    rechteck(k, (30, 8, 33, 26), 't')                             # Teppich Mittelgang
    rechteck(k, (21, 4, 42, 6), 'b')                              # Buehne / Preistheke oben
    for x0 in (11, 49):                                           # Automatenreihen links/rechts (je 4 breit)
        rechteck(k, (x0, 7, x0 + 3, 24), 's')
    for x0 in (18, 38):                                           # Spieltische (je 8 breit, mehr Luft)
        rechteck(k, (x0, 10, x0 + 7, 21), 'k')
    for (x0, y0, x1, y1) in INSELN:
        rechteck(k, (x0 + 1, y0 + 1, x1 - 1, y1 - 1), 'j')
    k[ANKUNFT[1] + 1, 30:34] = 'z'                                # Ankunftspfeile
    k[4, 31:33] = 'g'                                             # Ausgang (VIP-Tuer) hinter der Theke
    h = np.where(k == '.', 0, 2)
    lay = {'groesse': [C, R], 'klassen': [''.join(z) for z in k], 'hoehe': [''.join(str(c) for c in z) for z in h],
           'casino': CASINO, 'ankunft': ANKUNFT, 'steg': STEG, 'inseln': INSELN, 'achse': ACHSE,
           'teleporter': [{'x': 30, 'y': ANKUNFT[1] + 1, 'b': 4, 'h': 1, 'art': 'ankunft'},
                          {'x': 31, 'y': 4, 'b': 2, 'h': 1, 'art': 'ausgang'}]}
    json.dump(lay, open(os.path.join(KARTE, 'layout.json'), 'w'), indent=0)
    F = {'.': (10, 14, 30), 'p': (52, 70, 104), 'r': (34, 48, 78), 't': (150, 30, 50), 's': (200, 150, 40),
         'k': (30, 120, 70), 'b': (120, 60, 160), 'z': (60, 200, 230), 'g': (230, 180, 70), 'j': (210, 80, 200)}
    S = 16
    im = Image.new('RGB', (C * S, R * S))
    dr = ImageDraw.Draw(im)
    for y in range(R):
        for x in range(C):
            dr.rectangle((x * S, y * S, x * S + S - 1, y * S + S - 1), fill=F[k[y, x]], outline=(0, 0, 0))
    for txt, (x, y) in (('Automaten', (11, 15)), ('Automaten', (49, 15)), ('Roulette', (19, 15)),
                        ('Karten', (39, 15)), ('Preistheke / Buehne', (24, 5)), ('Teppich', (30, 18)),
                        ('Ankunft', (29, 31)), ('Jackpot', (1, 14)), ('Jackpot', (58, 14))):
        dr.text((x * S + 2, y * S + 2), txt, fill=(255, 255, 255))
    im.save(os.path.join(KARTE, 'layout_vorschau.png'))
    print('Karte 22 Layout %dx%d, begehbar %d Kacheln' % (C, R, int((k != '.').sum())))


if __name__ == '__main__':
    main()
