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

Klassen:  w  Bar (Nutzer)
          .  Leere   p  Boden   r  Randring   t  Teppich   s  Automatenreihe   k  Spieltisch-Bereich
          b  Buehne/Theke   z  Pfeil cyan (Ankunft)   g  Pfeil gold (Ausgang)   j  Jackpot-Insel
"""
import json, os
import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte22')
C, R = 70, 42                    # Nutzer: groesser, mehr Platz an den Automaten, Bar oben (vorher 52x28, 64x36)
CASINO = (8, 3, 61, 33)          # x0, y0, x1, y1 (inklusive)
ANKUNFT = (31, 36, 38, 38)
STEG = (33, 34, 36, 35)
INSELN = [(1, 15, 5, 20), (64, 15, 68, 20)]
INSEL_STEGE = [(6, 17, 7, 18), (62, 17, 63, 18)]
ACHSE = 34.5                     # Mittelachse (Spalten 34/35)


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
    rechteck(k, (9, 4, 60, 10), 'w')                              # Nutzer: ganze hintere Wand als Bar
    rechteck(k, (33, 5, 36, 32), 't')                             # Teppich bis zur VIP-Tuer                             # Teppich Mittelgang
    for x0 in (13, 53):                                           # Automatenreihen links/rechts (je 4 breit, Abstand zum Rand)
        rechteck(k, (x0, 12, x0 + 3, 28), 's')
    for x0 in (21, 41):                                           # Spieltische (je 8 breit, mehr Luft)
        rechteck(k, (x0, 13, x0 + 7, 25), 'k')

    for (x0, y0, x1, y1) in INSELN:
        rechteck(k, (x0 + 1, y0 + 1, x1 - 1, y1 - 1), 'j')
    k[ANKUNFT[1] + 1, 33:37] = 'z'                                # Ankunftspfeile
    k[4, 33:37] = 'g'                                             # Pruefung: Ausgang so breit wie der Teppich                                             # Ausgang (VIP-Tuer) hinter der Theke
    h = np.where(k == '.', 0, 2)
    lay = {'groesse': [C, R], 'klassen': [''.join(z) for z in k], 'hoehe': [''.join(str(c) for c in z) for z in h],
           'casino': CASINO, 'ankunft': ANKUNFT, 'steg': STEG, 'inseln': INSELN, 'achse': ACHSE,
           'teleporter': [{'x': 33, 'y': ANKUNFT[1] + 1, 'b': 4, 'h': 1, 'art': 'ankunft'},
                          {'x': 33, 'y': 4, 'b': 4, 'h': 1, 'art': 'ausgang'}]}
    json.dump(lay, open(os.path.join(KARTE, 'layout.json'), 'w'), indent=0)
    F = {'.': (10, 14, 30), 'p': (52, 70, 104), 'r': (34, 48, 78), 't': (150, 30, 50), 's': (200, 150, 40),
         'k': (30, 120, 70), 'b': (120, 60, 160), 'w': (110, 70, 40), 'z': (60, 200, 230), 'g': (230, 180, 70), 'j': (210, 80, 200)}
    S = 16
    im = Image.new('RGB', (C * S, R * S))
    dr = ImageDraw.Draw(im)
    for y in range(R):
        for x in range(C):
            dr.rectangle((x * S, y * S, x * S + S - 1, y * S + S - 1), fill=F[k[y, x]], outline=(0, 0, 0))
    for txt, (x, y) in (('Automaten', (13, 20)), ('Automaten', (53, 20)), ('Roulette', (22, 19)),
                        ('Karten', (42, 19)), ('Bar', (20, 6)), ('Bar', (46, 6)), ('Teppich', (33, 20)),
                        ('Ankunft', (32, 37)), ('Jackpot', (1, 17)), ('Jackpot', (64, 17))):
        dr.text((x * S + 2, y * S + 2), txt, fill=(255, 255, 255))
    im.save(os.path.join(KARTE, 'layout_vorschau.png'))
    print('Karte 22 Layout %dx%d, begehbar %d Kacheln' % (C, R, int((k != '.').sum())))


if __name__ == '__main__':
    main()
