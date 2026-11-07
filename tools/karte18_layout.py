"""Karte 18 (The Fog-Bound City): Kachelraster nach der Vorlage -> maps/karte18/layout.json

  python3 tools/karte18_layout.py

Vorlage assets/vorlagen/karte18_vorlage.png (2176x1792 = 136x112 Kacheln a 16 px). Eine Hafenstadt am Abend, ringsum
dichter Nebel. Oben die Ladenzeile, der Spielplatz, ein Buerohaus und die grosse Messehalle (Achse x = 102); links der
Wohnblock, Parks und ein Platz mit Marktzelt; in der Mitte Buerohaus und Lagerhallen; rechts der grosse Platz vor der
Halle mit Mittelweg und Kompass; unten die Hochbahn ueber der Uferstrasse, Gleise am Kai, Meer und Steg.

Klassen:  .  Nebel        s  Asphalt      g  Gehweg (graue Platten)   p  Platz (lavendel, grosse Platten)
          q  Platz links (lavendel, kleine Platten)    c  Mittelweg (Schachbrett)   t  Terrasse vor der Halle
          n  Rasen        d  Sand (Sandkasten)   m  Mittelstreifen (Bordstein + Hecke)   x  Sperrflaeche (schraffiert)
          b  Gleisbett    k  Kaikante     h  Holzsteg     w  Wasser
Hoehen:   0 Wasser, 1 Boden, 2 Terrasse vor der Halle.
Gebaeude stehen als Objekte darauf (Liste 'gebaeude': x0, y0, x1, y1, Art).
"""
import json, os
import numpy as np
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte18')
C, R = 136, 112
ACHSE = 102                         # Messehalle, Treppe, Mittelweg, Kompass (Kachelgrenze 102 -> x = 1632 px)


def rechteck(k, x0, y0, x1, y1, art):
    k[y0:y1 + 1, x0:x1 + 1] = art


def main():
    k = np.full((R, C), '.')
    rs = np.random.RandomState(1818)
    # ---------------------------------------------------------------- Land (Grundflaeche Gehweg), Raender gestuft
    rechteck(k, 4, 18, 63, 99, 'g')                              # linker Stadtteil
    rechteck(k, 64, 20, 125, 99, 'p')                            # rechter Teil (Platz, unten Strasse)
    rechteck(k, 46, 5, 61, 17, 'g')                              # Spielplatz-Block
    rechteck(k, 62, 8, 83, 19, 'g')                              # Buerohaus oben
    rechteck(k, 84, 12, 119, 27, 'g')                            # Messehalle (Grund; die Pyramiden ragen in den Nebel)
    rechteck(k, 120, 18, 125, 27, 'p')
    rechteck(k, 4, 12, 45, 17, 'g')                              # Ladenzeile (Grund)
    rechteck(k, 120, 39, 135, 44, 'p')                           # Ausgang rechts (Teleporter)
    # gestufte, unregelmaessige Raender in den Nebel (links, rechts am Platz) - am Kachelraster
    for y in range(18, 100):
        tiefe = [0, 0, 1, 1, 2][rs.randint(0, 5)] if y % 3 == 0 else None
        if tiefe is not None:
            for yy in range(y, min(100, y + 3)):
                k[yy, 4:4 + tiefe] = '.'
    for y in range(20, 80):
        if y in range(39, 45):
            continue
        if y % 4 == 0:
            t = rs.randint(0, 3)
            for yy in range(y, y + 4):
                k[yy, 126 - t:126] = '.'
    # ---------------------------------------------------------------- Strassen
    rechteck(k, 3, 20, 82, 24, 's')                              # obere Strasse (verschwindet links im Nebel)
    rechteck(k, 32, 25, 36, 95, 's')                             # Querstrasse
    rechteck(k, 3, 42, 62, 53, 's')                              # mittlere Strasse mit Mittelstreifen
    for (x0, x1) in ((5, 13), (17, 26), (42, 49), (53, 61)):
        rechteck(k, x0, 47, x1, 48, 'm')
    rechteck(k, 41, 29, 61, 37, 's')                             # Parkplatz
    rechteck(k, 37, 32, 40, 35, 's')                             # Einfahrt Parkplatz von der Querstrasse
    rechteck(k, 62, 80, 125, 83, 'g')                            # Gehweg unter der Hochbahn
    rechteck(k, 32, 94, 125, 95, 'g')                            # Uferpromenade
    rechteck(k, 32, 84, 125, 93, 's')                            # Uferstrasse
    for (x0, x1) in ((62, 97), (102, 125)):
        rechteck(k, x0, 87, x1, 88, 'm')
    rechteck(k, 38, 87, 61, 88, 'x')                             # Sperrflaeche (schraffiert)
    # ---------------------------------------------------------------- Flaechen
    rechteck(k, 6, 77, 30, 93, 'q')                              # Platz links unten (Marktzelt, Teleporter)
    rechteck(k, 84, 28, 119, 32, 't')                            # Terrasse vor der Halle (Front in Reihe 33)
    rechteck(k, ACHSE - 4, 34, ACHSE + 3, 79, 'c')               # Mittelweg (8 Kacheln, Achse 102)
    for (x0, y0, x1, y1) in ((47, 6, 52, 8), (56, 6, 61, 12), (47, 13, 52, 16), (8, 58, 14, 66), (19, 57, 27, 65),
                             (6, 71, 12, 76), (20, 70, 27, 76), (12, 89, 15, 93), (24, 89, 29, 93)):
        rechteck(k, x0, y0, x1, y1, 'n')
    rechteck(k, 47, 9, 52, 12, 'd')                              # Sandkasten
    rechteck(k, 4, 96, 125, 97, 'b')                             # Gleise am Kai
    rechteck(k, 4, 98, 125, 99, 'k')                             # Kaikante
    # Meer: unter dem Kai, Rand gestuft in den Nebel
    for x in range(8, 126):
        tief = 100 + [2, 3, 3, 4, 5][rs.randint(0, 5)] if x % 3 == 0 else None
        if tief is not None:
            for xx in range(x, min(126, x + 3)):
                k[100:tief + 1, xx] = 'w'
    rechteck(k, 126, 78, 131, 99, 'w')                           # Kanal rechts (unter der Hochbahn hindurch)
    for y in range(100, 104):
        k[y, 126:131 - (y - 100)] = 'w'
    rechteck(k, 104, 100, 109, 106, 'h')                         # Holzsteg (beginnt an der Kaimauer)
    hoehe = np.ones((R, C), int)
    hoehe[k == 'w'] = 0
    hoehe[k == '.'] = 0
    hoehe[k == 't'] = 2
    hoehe[k == 'h'] = 1
    gebaeude = [
        [4, 12, 45, 17, 'laeden'], [62, 8, 83, 17, 'buero_oben'], [84, 4, 119, 27, 'halle'],
        [5, 28, 28, 39, 'wohnblock'], [42, 56, 59, 67, 'buero_mitte'], [38, 71, 50, 79, 'lager_rolltor'],
        [52, 71, 63, 79, 'lager_shed'],
    ]
    lay = {
        'groesse': [C, R], 'klassen': [''.join(r) for r in k], 'hoehe': [''.join(str(c) for c in r) for r in hoehe],
        'achse': ACHSE, 'gebaeude': gebaeude,
        'treppe_terrasse': [ACHSE - 6, ACHSE + 5, 33],          # x0, x1, Reihe der Front/Stufen (12 breit, Achse 102)
        'kompass': [ACHSE, 64],
        'treppen_sued': [[ACHSE - 6, ACHSE + 5, 2, 32]],      # fuer die Kollision: Treppe als Durchgang
        'zebra': [[27, 29, 20, 24, 'v'], [39, 41, 20, 24, 'v'], [32, 36, 27, 29, 'h'], [32, 36, 37, 39, 'h'],
                  [14, 16, 42, 53, 'v'], [27, 29, 42, 53, 'v'], [39, 41, 42, 53, 'v'], [50, 52, 42, 53, 'v'],
                  [32, 36, 55, 57, 'h'], [32, 36, 69, 71, 'h'], [ACHSE - 2, ACHSE + 1, 84, 93, 'v']],
        'hochbahn': {'x0': 60, 'x1': 135, 'y0': 80, 'y1': 83, 'pfeiler': [62, 78, 94, 110, 126], 'zug': [86, 107]},
        'teleporter': [{'x': 8, 'y': 85, 'b': 3, 'h': 2, 'farbe': 'violett'},
                       {'x': 132, 'y': 40, 'b': 2, 'h': 4, 'farbe': 'violett'}],
        'steg': [104, 100, 109, 106],
    }
    os.makedirs(KARTE, exist_ok=True)
    json.dump(lay, open(os.path.join(KARTE, 'layout.json'), 'w'), indent=0)
    F = {'.': (152, 146, 177), 's': (48, 53, 69), 'g': (96, 102, 118), 'p': (118, 110, 134), 'q': (128, 118, 140),
         'c': (140, 134, 156), 't': (150, 146, 166), 'n': (44, 72, 52), 'd': (170, 150, 110), 'm': (70, 110, 60),
         'x': (70, 74, 88), 'b': (60, 48, 44), 'k': (150, 150, 160), 'h': (120, 84, 50), 'w': (20, 26, 72)}
    out = np.zeros((R, C, 3), np.uint8)
    for kk, c in F.items():
        out[k == kk] = c
    for (x0, y0, x1, y1, art) in gebaeude:
        out[y0:y1 + 1, x0:x1 + 1] = (out[y0:y1 + 1, x0:x1 + 1] * 0.5 + np.array((200, 60, 60)) * 0.5).astype(np.uint8)
    vor = Image.open(os.path.join(ROOT, 'assets', 'vorlagen', 'karte18_vorlage.png')).convert('RGB').resize((C * 4, R * 4))
    bild = Image.new('RGB', (C * 8 + 8, R * 4))
    bild.paste(vor, (0, 0))
    bild.paste(Image.fromarray(out).resize((C * 4, R * 4), 0), (C * 4 + 8, 0))
    bild.save(os.path.join(KARTE, 'layout_vergleich.png'))
    print('Karte 18 Layout %dx%d' % (C, R))


if __name__ == '__main__':
    main()
