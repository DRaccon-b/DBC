"""Karte 18 (The Fog-Bound City), Neuaufbau: Kachelraster nach der Vorlage -> maps/karte18/layout.json

  python3 tools/karte18_layout.py

Vorlage assets/vorlagen/karte18_vorlage.png (2176x1792 = 136x112 Kacheln a 16 px), Kachel fuer Kachel vermessen
(Medianfarbe je Kachel, Klassen per Farbabstand, danach von Hand bereinigt). Hafenstadt am Abend, ringsum Nebel.

Klassen:  .  Nebel         s  Asphalt        g  Gehweg (graue Platten)     v  Betonvorplatz
          p  Platz (lavendel, grosse Platten)   q  Platz links unten (kleine Platten)
          c  Mittelweg (Schachbrett)          t  Terrasse vor der Halle
          n  Rasen   d  Sand   m  Mittelstreifen (Hecke)   e  Heckenbeet   x  Sperrflaeche (schraffiert)
          b  Holzpromenade   k  Kaikante   h  Holzsteg   w  Wasser
Hoehen:   0 Wasser/Nebel, 1 Boden, 2 Terrasse.  Gebaeude stehen als Objekte darauf (Liste 'gebaeude').
"""
import json, os
import numpy as np
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte18')
C, R = 136, 112
ACHSE = 102                         # Achse der Messehalle: Kachelgrenze 102 (x = 1632 px)


def rechteck(k, x0, y0, x1, y1, art):
    k[y0:y1 + 1, x0:x1 + 1] = art


def nebelrand(k, rs):
    """Unregelmaessiger, aber kachelgenauer Rand in den Nebel (Stufen von je 3-4 Reihen)."""
    for y in range(18, 100, 3):                                   # Westrand
        t = int(rs.choice([0, 0, 1, 1, 2]))
        k[y:y + 3, 4:4 + t] = '.'
    for y in range(20, 80, 4):                                    # Ostrand des Platzes (Ausgang bleibt frei)
        if 38 <= y <= 44:
            continue
        t = int(rs.choice([0, 1, 1, 2]))
        k[y:y + 4, 126 - t:126] = '.'


def main():
    k = np.full((R, C), '.')
    rs = np.random.RandomState(1818)
    # ------------------------------------------------------------ Grundflaechen
    rechteck(k, 4, 18, 63, 99, 'g')                               # linker Stadtteil (Gehweg als Grund)
    rechteck(k, 64, 20, 125, 99, 'p')                             # grosser Platz rechts
    rechteck(k, 4, 12, 45, 17, 'g')                               # Ladenzeile
    rechteck(k, 46, 6, 61, 17, 'g')                               # Spielplatz
    rechteck(k, 62, 8, 83, 19, 'g')                               # Buerohaus oben
    rechteck(k, 84, 13, 119, 27, 'g')                             # Messehalle (Dach ab Reihe 13)
    rechteck(k, 120, 18, 125, 27, 'p')
    rechteck(k, 120, 40, 135, 44, 'p')                            # Ausgang Ost (Teleporter)
    nebelrand(k, rs)
    # ------------------------------------------------------------ Strassen
    rechteck(k, 3, 20, 81, 24, 's')                               # obere Strasse
    rechteck(k, 82, 20, 83, 24, 'g')                              # Strassenende mit Pollern
    rechteck(k, 64, 25, 83, 26, 'g')                              # Gehweg an der Halle
    rechteck(k, 32, 25, 36, 95, 's')                              # Querstrasse
    rechteck(k, 41, 29, 61, 37, 's')                              # Parkplatz
    rechteck(k, 37, 32, 40, 35, 's')                              # Einfahrt
    rechteck(k, 3, 42, 63, 53, 's')                               # mittlere Strasse
    for (x0, x1) in ((5, 13), (17, 26), (42, 49), (53, 62)):      # Mittelstreifen, Luecken = Zebrastreifen
        rechteck(k, x0, 47, x1, 48, 'm')
    rechteck(k, 62, 80, 124, 81, 'g')                             # Gehweg unter der Hochbahn
    rechteck(k, 32, 82, 124, 93, 's')                             # Uferstrasse
    rechteck(k, 44, 80, 48, 81, 's')                              # Zufahrt zum offenen Rolltor
    for (x0, x1) in ((62, 97), (102, 124)):                       # Mittelstreifen, Luecke 98-101 = Zebra (Vorlage)
        rechteck(k, x0, 87, x1, 88, 'm')
    rechteck(k, 38, 87, 61, 88, 'x')                              # Sperrflaeche
    rechteck(k, 32, 94, 124, 95, 'g')                             # Uferpromenade
    # ------------------------------------------------------------ Flaechen
    rechteck(k, 6, 77, 30, 93, 'q')                               # Platz links unten (Notlager, Teleporter)
    rechteck(k, 87, 28, 116, 31, 't')                             # Terrasse vor der Halle
    rechteck(k, ACHSE - 4, 34, ACHSE + 3, 79, 'c')                # Mittelweg (8 Kacheln auf der Achse)
    rechteck(k, 39, 68, 63, 70, 'v')                              # Betonvorplatz
    for (x0, y0, x1, y1) in ((47, 6, 52, 9), (56, 6, 61, 13),    # Spielplatz
                             (8, 57, 14, 66), (19, 57, 27, 65), (6, 71, 12, 76), (20, 70, 27, 76),   # Park SW
                             (15, 74, 16, 76), (4, 78, 6, 81), (12, 89, 15, 93), (24, 89, 29, 93), (6, 90, 7, 93),
                             (37, 71, 38, 72), (37, 75, 38, 76)):  # Baumscheiben der Ginkgo-Allee
        rechteck(k, x0, y0, x1, y1, 'n')
    rechteck(k, 47, 10, 52, 13, 'd')                              # Sandkasten
    rechteck(k, 46, 8, 46, 16, 'm')                               # Hecke am Spielplatz
    for (x0, y0, x1, y1) in ((66, 28, 71, 29), (69, 37, 74, 39), (80, 44, 85, 46), (69, 67, 74, 69),
                             (118, 38, 123, 40), (118, 58, 123, 60), (118, 70, 123, 72), (121, 21, 123, 23)):
        rechteck(k, x0, y0, x1, y1, 'e')                          # Heckenbeete wie in der Vorlage
    rechteck(k, 4, 96, 124, 97, 'b')                              # Holzpromenade
    rechteck(k, 4, 98, 124, 99, 'k')                              # Kaikante
    rechteck(k, 125, 78, 125, 99, 'k')                            # Kaikante am Kanal
    for x in range(8, 126, 3):                                    # Meer, Rand gestuft in den Nebel
        tief = 100 + int(rs.choice([2, 3, 3, 4, 5]))
        k[100:tief + 1, x:min(126, x + 3)] = 'w'
    rechteck(k, 126, 78, 131, 99, 'w')                            # Kanal unter der Hochbahn
    for y in range(100, 104):
        k[y, 126:131 - (y - 100)] = 'w'
    rechteck(k, 104, 100, 109, 106, 'h')                          # Holzsteg
    # ------------------------------------------------------------ Feinkorrekturen am Rand
    k[33:39, 4] = '.'
    k[84:93, 4:6] = '.'; k[82:84, 5] = '.'; k[93:96, 5] = '.'      # Platz links beginnt bei x 6
    k[20:24, 124] = '.'
    k[13:18, 119] = '.'                                           # Nebel neben der Dachschraege der Halle
    rechteck(k, 4, 78, 6, 81, 'n')

    hoehe = np.ones((R, C), int)
    hoehe[np.isin(k, ['w', '.'])] = 0
    hoehe[k == 't'] = 2
    gebaeude = [[4, 12, 45, 17, 'laeden'], [62, 8, 83, 17, 'buero_oben'], [84, 4, 119, 27, 'halle'],
                [5, 27, 28, 39, 'wohnblock'], [42, 56, 59, 67, 'buero_mitte'], [39, 71, 50, 79, 'lager_rolltor'],
                [52, 71, 63, 79, 'lager_shed']]
    lay = {
        'groesse': [C, R], 'klassen': [''.join(r) for r in k], 'hoehe': [''.join(str(c) for c in r) for r in hoehe],
        'achse': ACHSE, 'gebaeude': gebaeude,
        'treppe_terrasse': [ACHSE - 6, ACHSE + 5, 32], 'kompass': [ACHSE, 64],
        'treppen_sued': [[ACHSE - 6, ACHSE + 5, 2, 31]],
        'zebra': [[27, 29, 20, 24, 'v'], [39, 41, 20, 24, 'v'], [32, 36, 27, 29, 'h'], [32, 36, 37, 39, 'h'],
                  [14, 16, 42, 53, 'v'], [27, 29, 42, 53, 'v'], [39, 41, 42, 53, 'v'], [50, 52, 42, 53, 'v'],
                  [32, 36, 55, 57, 'h'], [32, 36, 77, 79, 'h'], [98, 101, 82, 93, 'v']],
        'hochbahn': {'x0': 62, 'x1': 135, 'y0': 80, 'y1': 83, 'pfeiler': [62, 78, 94, 110, 126], 'zug': [86, 107]},
        'teleporter': [{'x': 8, 'y': 84, 'b': 3, 'h': 2, 'farbe': 'violett'},
                       {'x': 132, 'y': 40, 'b': 2, 'h': 4, 'farbe': 'violett'}],
        'steg': [104, 100, 109, 106],
    }
    os.makedirs(KARTE, exist_ok=True)
    json.dump(lay, open(os.path.join(KARTE, 'layout.json'), 'w'), indent=0)
    F = {'.': (152, 146, 177), 's': (48, 53, 69), 'g': (96, 102, 118), 'p': (118, 110, 134), 'q': (128, 118, 140),
         'c': (140, 134, 156), 't': (150, 146, 166), 'n': (44, 72, 52), 'd': (170, 150, 110), 'm': (70, 110, 60),
         'x': (70, 74, 88), 'e': (60, 100, 60), 'v': (140, 144, 150), 'b': (120, 84, 50), 'k': (150, 150, 160),
         'h': (120, 84, 50), 'w': (20, 26, 72)}
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
