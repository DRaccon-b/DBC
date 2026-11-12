"""Karte 32 (Dream Ruins, A02): Kachelraster aus der Vorlage -> maps/karte32/layout.json

  python3 tools/karte32_layout.py

Vorlage assets/vorlagen/karte32_vorlage.png (1440x1280 = 90x80 Kacheln a 16 px). Ein zerfallenes Traumschloss
schwebt in der Sternenleere: oben Thronturm und grosser Saal (lila Teppich, Buntglasfenster, rechte Kante
abgebrochen), darunter die Bannerhalle (links ein Loch in die Leere) und rechts der Festsaal mit braunem
Musterteppich; ein roter Teppich laeuft vom Thron bis zum Tor. Unten Aussenmauer mit Tuermen und der Friedhof.
Aufbau wie Karte 09 (Vamdemon's Keep).

Klassen:  . Leere (Sterne)  i Steinboden  j Steinboden dunkel  c roter Teppich  v lila Teppich  o brauner Teppich
          g Friedhofsgras  p Pflasterweg
Hoehen:   0 Leere, 1 Boden, 3 Mauern (Krone; die Wandflaeche wird darunter auf den Boden gezeichnet).
"""
import json, os
import numpy as np
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte32')
VORLAGE = os.path.join(ROOT, 'assets', 'vorlagen', 'karte32_vorlage.png')
T, C, R = 16, 90, 80
WAND = 3                                       # Wandflaeche 3 Kacheln hoch (wie Karte 09)


WEGE = [  # (Stuetzpunkte in Kacheln, halbe Breite) -> Catmull-Rom-Kurven auf dem Friedhof
    ([(36.5, 57.6), (36.2, 60), (37.4, 62.4), (36.0, 64.6)], 1.5),                              # vom Durchgang
    ([(4.5, 64.6), (12, 63.5), (20, 65.1), (28, 64.0), (36, 64.6), (44, 63.6), (52, 64.8), (60, 63.8),
      (68, 65.0), (76, 64.0), (83.5, 64.6)], 1.5),                                               # Hauptweg
    ([(57.0, 57.6), (56.2, 60.4), (54.2, 63.6), (53.4, 67), (52.8, 71), (53.5, 77.6)], 1.5),     # Mitte senkrecht (neben dem Turm)
    ([(71.5, 57.6), (70.6, 61), (72.0, 66.5), (70.8, 70.5), (71.5, 73)], 1.5),                   # rechts senkrecht
    ([(24.5, 72.6), (32, 73.4), (40, 72.3), (48, 73.2), (56, 72.4), (64, 73.4), (72, 72.6), (83.5, 73.0)], 1.25),
    ([(43.8, 69.5), (45.2, 69.5)], 2.7), ([(44.5, 70.5), (45.0, 72.6)], 1.3),                  # Brunnenplatz links
    ([(77.8, 69.5), (79.2, 69.5)], 2.7), ([(78.5, 70.5), (78.0, 72.6)], 1.3),                  # Brunnenplatz rechts
]


def _kurve(pts, n=24):
    p = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for i in range(1, len(p) - 2):
        p0, p1, p2, p3 = (np.array(q, float) for q in p[i - 1:i + 3])
        for t in np.linspace(0, 1, n, endpoint=False):
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(np.array(pts[-1], float))
    return np.array(out)


def _weg(k, pts, r, erlaubt):
    c = _kurve(pts)
    yy, xx = np.mgrid[0:R, 0:C]
    d = np.min([(xx + 0.5 - px) ** 2 + (yy + 0.5 - py) ** 2 for px, py in c], axis=0)
    k[(d <= r * r) & erlaubt & (k == 'g')] = 'p'


def r_(m, x0, y0, x1, y1, v=True):
    m[y0:y1 + 1, x0:x1 + 1] = v


def main():
    k = np.full((R, C), '.')
    mauer = np.zeros((R, C), bool)             # Mauerkoerper inkl. Wandflaeche (wie in der Vorlage)
    # ---------------------------------------------------------------- Schloss
    r_(mauer, 27, 1, 46, 4)                    # Thronturm: Nordwand
    r_(mauer, 27, 1, 28, 14); r_(mauer, 45, 1, 46, 14)
    r_(k, 29, 5, 44, 14, 'i')                  # Thronraum + Gang zum grossen Saal
    r_(mauer, 10, 10, 29, 14); r_(mauer, 43, 10, 57, 14)   # Seitenfluegel: Nordwaende mit Fenstern
    r_(mauer, 33, 10, 39, 14)                  # Thronnische (zweiter Thron vor der Nischenwand)
    r_(mauer, 10, 10, 11, 50)                  # linke Aussenwand
    r_(k, 12, 15, 56, 26, 'i')                 # grosser Saal
    r_(k, 33, 15, 39, 18, 'v')                 # lila Teppich vor dem Thron
    r_(mauer, 10, 27, 57, 32)                  # Mittelmauer mit Bannern
    r_(mauer, 57, 30, 89, 32)                  # Mauer ueber dem Festsaal
    r_(k, 12, 33, 58, 50, 'i')                 # Bannerhalle
    r_(k, 12, 33, 25, 50, 'j'); r_(k, 47, 33, 58, 50, 'j')   # Seitenschiffe dunkler
    r_(mauer, 59, 33, 62, 38); r_(mauer, 59, 44, 62, 50)   # Trennwand zum Festsaal (Durchgang 39-43)
    r_(k, 59, 39, 62, 43, 'i')
    r_(k, 63, 33, 85, 50, 'i')                 # Festsaal
    r_(k, 65, 33, 82, 50, 'o')                 # brauner Musterteppich
    r_(mauer, 86, 30, 89, 50)
    r_(k, 35, 19, 37, 57, 'c')                 # roter Teppich: Thron -> Mittelmauer -> Halle -> Tor
    r_(mauer, 35, 27, 37, 32, False)           # Durchgang in der Mittelmauer
    # Zerbrochene rechte Kante des grossen Saals (Vorlage): Boden reisst stufig in die Leere ab, keine Mauer
    for y, x1 in ((15, 57), (16, 57), (17, 56), (18, 56), (19, 56), (20, 56), (21, 55), (22, 54), (23, 55),
                  (24, 54), (25, 55), (26, 56)):
        k[y, x1 + 1:58] = '.'
    r_(mauer, 57, 15, 58, 26, False)
    # Loch in die Leere in der Bannerhalle links (Vorlage)
    loch = [(43, 17, 17), (44, 14, 19), (45, 14, 19), (46, 15, 19), (47, 17, 18)]
    for y, x0, x1 in loch:
        k[y, x0:x1 + 1] = '.'
    # ---------------------------------------------------------------- Aussenmauer + Friedhof
    r_(mauer, 0, 51, 89, 57)
    r_(mauer, 35, 51, 37, 57, False)           # Durchgang (Nutzer: ohne Tor, Waende je 1 Kachel laenger)
    r_(k, 35, 51, 37, 57, 'c')
    r_(k, 2, 58, 87, 77, 'g')
    r_(mauer, 0, 51, 1, 79); r_(mauer, 88, 51, 89, 79); r_(mauer, 0, 78, 89, 79)
    # Pflasterwege nach der Vorlage, aber geschwungen (Regel 6: nie nur gerade; Kanten 45 Grad beim Bauen, 6b)
    friedhof = np.zeros((R, C), bool); friedhof[58:78, 2:88] = True
    for pts, rad in WEGE:
        _weg(k, pts, rad, friedhof)
    # ---------------------------------------------------------------- Mauerkoerper -> Krone + Wandflaeche
    h = np.zeros((R, C), int)
    h[k != '.'] = 1
    krone = mauer.copy()
    for x in range(C):                          # die untersten WAND Reihen ueber Boden werden Wandflaeche
        y = 0
        while y < R:
            if mauer[y, x]:
                y0 = y
                while y < R and mauer[y, x]:
                    y += 1
                if y < R and k[y, x] != '.' and y - y0 > WAND:
                    krone[y - WAND:y, x] = False
                    for yy in range(y - WAND, y):
                        if k[yy, x] == '.':
                            k[yy, x] = k[y, x] if k[y, x] in 'ij' else 'i'
            else:
                y += 1
    k[mauer & (k == '.')] = 'i'
    h[krone] = 3
    h[(k != '.') & ~krone] = 1
    lay = {'groesse': [C, R], 'klassen': [''.join(z) for z in k], 'hoehe': [''.join(str(c) for c in z) for z in h],
           'durchgang': [35, 51, 37, 57], 'teleporter': [{'x': 11, 'y': 74, 'b': 2, 'h': 3, 'farbe': 'violett'}]}
    os.makedirs(KARTE, exist_ok=True)
    json.dump(lay, open(os.path.join(KARTE, 'layout.json'), 'w'), indent=0)
    F = {'.': (10, 12, 34), 'i': (125, 135, 150), 'j': (100, 110, 125), 'c': (120, 20, 35), 'v': (80, 45, 140),
         'o': (110, 60, 25), 'g': (60, 76, 58), 'p': (140, 148, 152)}
    out = np.zeros((R, C, 3), np.uint8)
    for kk, c in F.items():
        out[k == kk] = c
    out[h == 3] = (55, 62, 82)
    vor = Image.open(VORLAGE).convert('RGB').resize((C * 6, R * 6))
    bild = Image.new('RGB', (C * 12 + 8, R * 6))
    bild.paste(vor, (0, 0))
    bild.paste(Image.fromarray(out).resize((C * 6, R * 6), 0), (C * 6 + 8, 0))
    bild.save(os.path.join(KARTE, 'layout_vergleich.png'))
    print('Karte 32 Layout %dx%d' % (C, R))


if __name__ == '__main__':
    main()
