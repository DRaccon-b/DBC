"""Karte 10 (Toy Town): Kachelraster nach der Vorlage -> maps/karte10/layout.json

  python3 tools/karte10_layout.py

Vorlage assets/vorlagen/karte10_vorlage.png (1440x1200 = 90x75 Kacheln a 16 px). Das Raster wird von Hand
aus der Vorlage nachgezogen (Strassen, Gehwege, Plaetze sind geometrisch), Wege mit Boegen (Regel 6).
Klassen:  g Gras  a Asphalt  p rosa Gehweg  s Sandweg  b blaues Pflaster (Plaetze)  k Burghof (beige Platten)
          r rosa Rahmen im Burghof  m Bahnhofsboden (Kies)  q Bahnsteig  e Beeterde  x Wasser  W Waldboden (Rand)
Hoehen:   0 Wasser, 1 Boden (auch Waldrand), 3 Burgmauern.
"""
import json, math, os
import numpy as np
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte10')
C, R = 90, 75

# Burg: Achse der Burg / des Hofes (Kacheln; Weg 74-77, Rahmen 69-82 -> Mitte 76.0 = 1216 px)
# Haeuser: (Sprite, Mitte in px, Fussreihe, Tuer-Kachel, Weg bis Reihe) - Tuerweg fuehrt zum Gehweg
HAEUSER = [('haeuser/00', 128, 12, 6, None), ('haeuser/01', 368, 15, 22, 18), ('haeuser/02', 608, 14, 37, 18),
           ('haeuser2/00', 832, 14, 51, 18), ('haeuser2/03', 128, 26, 7, None), ('haeuser/03', 368, 31, 22, 34),
           ('haeuser2/01', 608, 31, 37, 34), ('haeuser2/02', 832, 31, 51, 34)]
ACHSE = 76.0


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
        k[7:y1 + 1, x0 - 1:x0 + 3] = 'p'
        k[7:y1 + 1, x0:x0 + 2] = 'a'
    k[19:23, 17:62] = 'p'; k[20:22, 18:62] = 'a'     # obere Querstrasse (bis zum Bahnhof)
    k[35:39, 0:61] = 'p'; k[36:38, 0:61] = 'a'       # untere Querstrasse (bis zum Teleporter)
    for x0 in (30, 44, 58):                          # Kreuzungen frei von Gehweg
        for y0 in (20, 36):
            if x0 == 44 or y0 == 20 or x0 in (30, 58):
                k[y0:y0 + 2, x0:x0 + 2] = 'a'
    # ------------------------------------------------------------------ Brunnenplatz links
    pl = ellipse(k, 10, 37, 8.6, 7.6, 'b')
    k[pl & (yy >= 36) & (yy <= 37)] = 'b'
    ellipse(k, 10, 37, 4.4, 3.6, 's')
    k[36:38, 0:2] = 'a'
    # ------------------------------------------------------------------ Uhrenplatz
    ellipse(k, 54, 53.5, 6.4, 6.0, 'b')
    # ------------------------------------------------------------------ Sandwege (Boegen, diagonal)
    pfad(k, [(6, 13), (7, 15), (10, 17), (14, 19), (16, 20)], 's', nur='g')     # Haus oben links -> Strasse
    pfad(k, [(7, 27), (7, 29), (8, 30)], 's', nur='g')                           # Feuerwache -> Brunnenplatz
    for (_, _, fy, tx, bis) in HAEUSER:
        if bis:
            k[fy + 1:bis + 1, tx:tx + 2] = np.where(k[fy + 1:bis + 1, tx:tx + 2] == 'g', 's', k[fy + 1:bis + 1, tx:tx + 2])
    pfad(k, [(9, 45), (9, 50), (10, 54), (9, 58), (9, 60)], 's', nur='gs')       # Brunnenplatz -> Garten
    pfad(k, [(44, 48), (46, 50), (48, 52)], 's', nur='gsp')                      # Strassenende -> Uhrenplatz
    pfad(k, [(44, 48), (40, 50), (33, 51), (28, 52), (25, 55), (23, 59), (24, 59), (24, 63), (23, 66), (20, 67)], 's', nur='gs')   # ... -> Pilzhaus-Tuer
    # ------------------------------------------------------------------ Teich mit Bruecke, Garten
    pfad(k, [(25, 56), (29, 57), (33, 58)], 's', nur='g')                         # Wege zur Bruecke
    pfad(k, [(45, 58), (47, 57), (49, 56)], 's', nur='g')
    t = ellipse(k, 39.5, 59, 4.0, 2.7, 'x')
    h[t] = 0
    gm = ellipse(k, 9.5, 64.5, 6.8, 4.6, 'e')
    k[gm & (xx > 14) & (yy < 62)] = 'g'
    # ------------------------------------------------------------------ Bahnhof oben rechts
    k[2:7, 0:90] = 'm'                                                          # Bahnstrecke oben (Schotterbett)
    k[2:23, 61:90] = 's'
    k[2:21, 61:89] = 'm'                                                        # Bahnhof + Verbindungsgleis links
    k[13:16, 69:83] = 'q'                                                       # Bahnsteig vor dem Bahnhof
    k[20:23, 58:64] = np.where(k[20:23, 58:64] == 'a', 'a', k[20:23, 58:64])
    k[19:23, 60:64] = 'p'                                                       # Strasse endet am Bahnhof
    k[20:22, 58:64] = 'a'
    k[19, 62:64] = 'm'                                                          # Verbindungsgleis (Bogen) liegt hier
    # ------------------------------------------------------------------ Burg und Burghof
    k[23:36, 61:90] = 's'                                                       # Vorplatz hinter der Burgfront
    k[23:30, 64:90] = 'k'                                                       # innerer Burghof (Hallen)
    k[35:72, 60:86] = 'k'
    k[35:47, 74:78] = 's'                                                       # Weg vom Tor zum Rahmen
    rahmen = (xx >= 69) & (xx <= 82) & (yy >= 47) & (yy <= 57)
    innen = (xx >= 70) & (xx <= 81) & (yy >= 48) & (yy <= 56)
    k[rahmen & ~innen] = 'r'
    ellipse(k, ACHSE, 52.5, 3.2, 2.7, 'b')
    mauer = np.zeros((R, C), bool)
    mauer[30:32, 61:90] = True                     # Burgfront: Krone, darunter 3 Kacheln Wandflaeche (Reihen 32-34)
    mauer[32:72, 86:90] = True                     # Ostmauer
    mauer[72:75, 60:90] = True                     # Suedmauer
    h[mauer] = 3
    # ------------------------------------------------------------------ Waldrand (wie Karte 01): Waldboden W
    wald = np.zeros((R, C), bool)
    wald[0:2, :] = True
    wald[:, 0:2] = True
    wald[:, 2] = k[:, 2] == 'g'
    wald[72:75, 0:60] = True
    wald[71, 0:60] = k[71, 0:60] == 'g'
    wald[34:39, 0:3] = False                       # Durchgang zum Teleporter
    # unregelmaessige Innenkante: Buchten und Vorspruenge
    for (x, y) in ((3, 8), (3, 9), (3, 20), (3, 21), (3, 25), (3, 26), (3, 46), (3, 47), (3, 55), (3, 56),
                   (3, 69), (20, 70), (21, 70),
                   (35, 70), (36, 70), (47, 70), (48, 70), (57, 70)):
        if k[y, x] == 'g':
            wald[y, x] = True
    k[wald] = 'W'
    k[36:38, 0:2] = 'a'
    lay = {
        'groesse': [C, R], 'klassen': [''.join(r) for r in k], 'hoehe': [''.join(str(c) for c in r) for r in h],
        'achse': ACHSE, 'haeuser': HAEUSER,
        # Gleise als Mittellinien in Pixeln: Strecke oben (durch den Bahnhof), Verbindungsgleis mit Boegen zum
        # unteren Bahnhofsgleis
        'gleise': [{'y': 4, 'x': [0, 89]}, {'y': 19, 'x': [64, 88]}],
        'gleisbogen': {'von_x': 56 * 16, 'oben_y': 4 * 16 + 7, 'x': 62 * 16 + 8, 'unten_y': 19 * 16 + 7, 'bis_x': 64 * 16, 'r': 48},
        'bruecken': [[35, 58, 44, 59]],                                            # (x0, y0, x1, y1)
        'teich': [632, 944, 70, 44],
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
