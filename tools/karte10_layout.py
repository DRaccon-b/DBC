"""Karte 10 (Toy Town): Kachelraster nach der Vorlage -> maps/karte10/layout.json

  python3 tools/karte10_layout.py

Vorlage assets/vorlagen/karte10_vorlage.png (1440x1200 = 90x75 Kacheln a 16 px). Das Raster wird von Hand
aus der Vorlage nachgezogen (Strassen, Gehwege, Plaetze sind geometrisch), Wege mit Boegen (Regel 6).
Klassen:  g Gras  a Asphalt  p rosa Gehweg  s Sandweg  b blaues Pflaster (Plaetze)  k Burghof (beige Platten)
          r rosa Rahmen im Burghof  m Bahnhofsboden (Kies)  q Bahnsteig  e Beeterde  x Wasser  H Hecke
Hoehen:   0 Wasser, 1 Boden, 3 Burgmauern, 5 Hecke (Rand).
"""
import json, math, os
import numpy as np
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte10')
C, R = 90, 75

# Burg: Achse der Burg / des Hofes (Kacheln, Mitte zwischen Spalte 75 und 76)
ACHSE = 75.5


def ellipse(k, cx, cy, rx, ry, art, raster=True):
    yy, xx = np.mgrid[0:R, 0:C]
    m = ((xx + 0.5 - cx) / rx) ** 2 + ((yy + 0.5 - cy) / ry) ** 2 <= 1
    k[m] = art
    return m


def pfad(k, punkte, art, breite=2, nur=None):
    """Weg entlang einer Punktfolge (Kacheln), Breite in Kacheln; diagonal erlaubt (Regel 6)."""
    for (x0, y0), (x1, y1) in zip(punkte, punkte[1:]):
        n = int(max(abs(x1 - x0), abs(y1 - y0)) * 2) + 1
        for i in range(n + 1):
            t = i / n
            x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            for dy in range(breite):
                for dx in range(breite):
                    X, Y = int(round(x)) + dx, int(round(y)) + dy
                    if 0 <= X < C and 0 <= Y < R and (nur is None or k[Y, X] in nur):
                        k[Y, X] = art


def main():
    k = np.full((R, C), 'g')
    h = np.ones((R, C), int)
    yy, xx = np.mgrid[0:R, 0:C]
    # ------------------------------------------------------------------ Strassen + Gehwege
    for x0 in (30, 44, 58):                          # senkrechte Strassen
        y1 = 47 if x0 == 44 else 38
        k[3:y1 + 1, x0 - 1:x0 + 3] = 'p'
        k[3:y1 + 1, x0:x0 + 2] = 'a'
    k[19:23, 17:62] = 'p'; k[20:22, 18:62] = 'a'     # obere Querstrasse (bis zum Bahnhof)
    k[35:39, 0:61] = 'p'; k[36:38, 0:61] = 'a'       # untere Querstrasse (bis zum Teleporter)
    for x0 in (30, 44, 58):                          # Kreuzungen frei von Gehweg
        for y0 in (20, 36):
            if x0 == 44 or y0 == 20 or x0 in (30, 58):
                k[y0:y0 + 2, x0:x0 + 2] = 'a'
    k[3, :] = np.where(k[3, :] == 'a', 'a', k[3, :])
    # ------------------------------------------------------------------ Brunnenplatz links
    pl = ellipse(k, 10, 37, 8.6, 7.6, 'b')
    k[pl & (yy >= 36) & (yy <= 37)] = 'b'
    ellipse(k, 10, 37, 4.4, 3.6, 's')
    k[36:38, 0:2] = 'a'
    # ------------------------------------------------------------------ Uhrenplatz
    ellipse(k, 54, 54, 5.6, 5.2, 'b')
    # ------------------------------------------------------------------ Sandwege (Boegen, diagonal)
    pfad(k, [(7, 13), (7, 15), (8, 17)], 's')                                   # Haus oben links -> Wohnturm
    pfad(k, [(7, 27), (7, 29), (8, 30)], 's', nur='g')                           # Wohnturm -> Brunnenplatz
    pfad(k, [(9, 45), (9, 50), (10, 54), (9, 58), (9, 60)], 's', nur='gs')       # Brunnenplatz -> Garten
    pfad(k, [(44, 48), (46, 50), (48, 52)], 's', nur='gsp')                      # Strassenende -> Uhrenplatz
    pfad(k, [(44, 48), (40, 50), (33, 51), (28, 52), (25, 55), (23, 59), (21, 63), (19, 67)], 's', nur='gs')
    # ------------------------------------------------------------------ Teich mit Bruecke, Garten
    t = ellipse(k, 39.5, 59, 4.0, 2.7, 'x')
    h[t] = 0
    gm = ellipse(k, 9.5, 64.5, 6.8, 4.6, 'e')
    k[gm & (xx > 14) & (yy < 62)] = 'g'
    # ------------------------------------------------------------------ Bahnhof oben rechts
    k[3:23, 62:89] = 's'
    k[5:21, 64:88] = 'm'
    k[15:17, 69:83] = 'q'                                                       # Bahnsteig vor dem Bahnhof
    k[20:23, 58:64] = np.where(k[20:23, 58:64] == 'a', 'a', k[20:23, 58:64])
    k[20:22, 62:64] = 'a'                                                       # Strasse endet am Bahnhof
    # ------------------------------------------------------------------ Burg und Burghof
    k[23:36, 61:90] = 's'                                                       # Vorplatz hinter der Burgfront
    k[35:72, 60:86] = 'k'
    k[35:47, 74:78] = 's'                                                       # Weg vom Tor zum Rahmen
    rahmen = (xx >= 69) & (xx <= 82) & (yy >= 47) & (yy <= 57)
    innen = (xx >= 70) & (xx <= 81) & (yy >= 48) & (yy <= 56)
    k[rahmen & ~innen] = 'r'
    ellipse(k, ACHSE + 0.5, 52.5, 3.2, 2.7, 'b')
    mauer = np.zeros((R, C), bool)
    mauer[30:32, 61:90] = True                     # Burgfront: Krone, darunter 3 Kacheln Wandflaeche (Reihen 32-34)
    mauer[32:72, 86:90] = True                     # Ostmauer
    mauer[72:75, 60:90] = True                     # Suedmauer
    h[mauer] = 3
    # ------------------------------------------------------------------ Hecke (Rand)
    hecke = np.zeros((R, C), bool)
    hecke[0:3, :] = True
    hecke[:, 0:2] = True
    hecke[72:75, 0:60] = True
    hecke[34:39, 0:2] = False                      # Durchgang zum Teleporter
    # unregelmaessige Innenkante (Buchten/Vorspruenge wie in der Vorlage)
    for (x, y) in ((2, 8), (2, 9), (2, 20), (2, 21), (2, 25), (2, 26), (2, 45), (2, 46), (2, 55), (2, 56), (2, 62),
                   (2, 63), (2, 68), (14, 3), (15, 3), (23, 3), (24, 3), (36, 3), (50, 3), (51, 3), (72 - 52, 71),
                   (21, 71), (35, 71), (36, 71), (47, 71), (48, 71), (57, 71)):
        hecke[y, x] = True
    k[hecke] = 'H'
    h[hecke] = 5
    k[36:38, 0:2] = 'a'
    lay = {
        'groesse': [C, R], 'klassen': [''.join(r) for r in k], 'hoehe': [''.join(str(c) for c in r) for r in h],
        'achse': ACHSE,
        'gleise': [{'y': 7, 'x': [64, 88]}, {'y': 19, 'x': [64, 88]}],          # Schienen (Kachelreihe der Schwellen)
        'bruecken': [[35, 58, 44, 59]],                                            # (x0, y0, x1, y1)
        'teleporter': [{'x': 0, 'y': 35, 'b': 2, 'h': 4}],
    }
    os.makedirs(KARTE, exist_ok=True)
    json.dump(lay, open(os.path.join(KARTE, 'layout.json'), 'w'), indent=0)
    F = {'g': (110, 180, 80), 'a': (120, 126, 140), 'p': (220, 160, 170), 's': (250, 236, 196), 'b': (130, 170, 200),
         'k': (210, 186, 146), 'r': (200, 120, 140), 'm': (130, 136, 126), 'q': (230, 150, 170), 'e': (120, 90, 60),
         'x': (60, 140, 200), 'H': (40, 90, 40)}
    out = np.zeros((R, C, 3), np.uint8)
    for kk, c in F.items():
        out[k == kk] = c
    out[h == 3] = (150, 70, 100)
    vor = Image.open(os.path.join(ROOT, 'assets', 'vorlagen', 'karte10_vorlage.png')).convert('RGB').resize((C * 8, R * 8))
    bild = Image.new('RGB', (C * 16 + 8, R * 8))
    bild.paste(vor, (0, 0))
    bild.paste(Image.fromarray(out).resize((C * 8, R * 8), 0), (C * 8 + 8, 0))
    bild.save(os.path.join(KARTE, 'layout_vergleich.png'))
    print('Karte 10 Layout %dx%d' % (C, R))


if __name__ == '__main__':
    main()
