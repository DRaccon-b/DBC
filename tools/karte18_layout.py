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
BEETE = [(65, 27, 72, 30), (68, 36, 75, 40), (79, 43, 86, 47), (68, 66, 75, 70),     # Rasenbeete auf dem Platz,
         (117, 37, 124, 41), (117, 57, 124, 61), (117, 69, 124, 73), (121, 21, 123, 23)]  # je 1 Kachel groesser


def rechteck(k, x0, y0, x1, y1, art):
    k[y0:y1 + 1, x0:x1 + 1] = art


def nebelrand(k, rs):
    """Unregelmaessiger, aber kachelgenauer Rand in den Nebel (Stufen von je 3-4 Reihen)."""
    for y in range(18, 100, 3):                                   # Westrand
        t = int(rs.choice([0, 0, 1, 1, 2]))
        k[y:y + 3, 4:4 + t] = '.'


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
    rechteck(k, 6, 56, 30, 72, 'q')                               # Platz links (Notlager, Teleporter)
    rechteck(k, 87, 28, 116, 31, 't')                             # Terrasse vor der Halle
    rechteck(k, ACHSE - 4, 34, ACHSE + 3, 79, 'c')                # Mittelweg (8 Kacheln auf der Achse)
    rechteck(k, 39, 68, 63, 70, 'v')                              # Betonvorplatz
    for (x0, y0, x1, y1) in ((47, 6, 52, 9), (56, 6, 61, 13),    # Spielplatz
                             (8, 73, 14, 78), (19, 73, 27, 78), (7, 86, 12, 93), (19, 86, 27, 93),  # Park SW
                             (16, 91, 17, 93),                    # (Reihen 79-84 frei: Hochbahn darueber)
                             (37, 71, 38, 72), (37, 75, 38, 76)):  # Baumscheiben der Ginkgo-Allee
        rechteck(k, x0, y0, x1, y1, 'n')
    rechteck(k, 6, 27, 27, 30, 'n')                               # Rasen vor den Wohnhaeusern (die PixelLab-Haeuser
    rechteck(k, 43, 56, 58, 59, 'n')                              # sind niedriger als die alten Bloecke)
    rechteck(k, 47, 10, 52, 13, 'd')                              # Sandkasten
    rechteck(k, 46, 8, 46, 16, 'm')                               # Hecke am Spielplatz
    for (x0, y0, x1, y1) in BEETE:                                # Rasenbeete mit Bordstein (Baum + Blumen)
        rechteck(k, x0, y0, x1, y1, 'e')
    rechteck(k, 4, 96, 124, 97, 'b')                              # Holzpromenade
    rechteck(k, 4, 98, 124, 99, 'k')                              # Kaikante
    rechteck(k, 125, 78, 125, 99, 'k')                            # Kaikante am Kanal
    rechteck(k, 125, 18, 125, 99, 'k')                            # Kaikante am Ostrand des Platzes
    for x in range(4, C, 3):                                      # Meer unten, Rand gestuft in den Nebel
        tief = 108 + int(rs.choice([0, 1, 1, 2]))                # Nebel erst ganz unten (2-4 Reihen)
        k[100:tief + 1, x:min(C, x + 3)] = 'w'
    for y in range(2, 100, 3):                                    # Meer rechts bis an den Kartenrand
        k[y:y + 3, 126 + int(rs.choice([0, 0, 1])):C] = 'w'
    rechteck(k, 126, 18, 126, 99, 'w')
    rechteck(k, 125, 40, 133, 44, 'p')                            # Mole nach Osten mit Teleporter
    rechteck(k, 125, 40, 133, 40, 'k'); rechteck(k, 125, 44, 133, 44, 'k')
    rechteck(k, 104, 100, 109, 106, 'h')                          # Holzsteg
    # ------------------------------------------------------------ Feinkorrekturen am Rand
    k[33:39, 4] = '.'
    k[20:24, 124] = '.'
    k[13:18, 119] = '.'                                           # Nebel neben der Dachschraege der Halle
    for y in range(0, R, 3):                                      # Wolkenrand ganz rechts ueber dem Meer
        k[y:y + 3, C - int(rs.choice([1, 2, 2, 3])):] = '.'

    for (x0, y0, x1, y1, art) in [[4, 12, 45, 17, 'laeden'], [62, 8, 83, 17, 'buero_oben'], [5, 27, 28, 39, 'wohnblock'],
                                  [42, 56, 59, 67, 'buero_mitte'], [39, 71, 50, 79, 'lager'], [52, 71, 63, 79, 'lager']]:
        rechteck(k, x0, y0, x1, y1, 'n')                          # Restflaechen der alten Gebaeude: Rasen (wird bepflanzt)
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
        'hochbahn': {'x0': 0, 'x1': 135, 'y0': 80, 'y1': 83, 'pfeiler': [14, 30, 46, 62, 78, 94, 110, 126],
                     'zug': [86, 107]},
        'beete': BEETE,
        'teleporter': [{'x': 8, 'y': 63, 'b': 3, 'h': 2, 'farbe': 'violett'},
                       {'x': 131, 'y': 41, 'b': 2, 'h': 3, 'farbe': 'violett'}],
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
