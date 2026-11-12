"""Karte 31 - Highton View Terrace (A02), Layout nach der Vorlage -> maps/karte31/layout.json

  python3 tools/karte31_layout.py

Vorlage assets/vorlagen/karte31_vorlage.png: 1920x1664 px = 120x104 Kacheln (am 16er-Raster). Oben ein hoeher
gelegener Park (Erdwege, Pavillon, Uhrplatz, Kiosk), rechts oben eine nochmals hoehere, eingezaeunte Terrasse mit dem
Riss-Portal; eine lange Stuetzmauer mit drei Treppen trennt Park und Wohnsiedlung. Unten Wohnbloecke 1/2/3 und die
Hochhaeuser 12/5 auf Erdboden mit Spielplaetzen, eine Querstrasse mit Ginkgo-Allee, Bahnhof HIGHTON mit Hochbahn,
Ziegelplatz, Fussgaengerbruecke, Ladenzeile, zwei Strassen, Heckenraender.

Klassen:  n Rasen  w Erdweg (Park)  e Erdboden (Siedlung)  g Gehweg/Steinplatz  s Asphalt  p Ziegelplatz
          d Sand (Spielplatz)  y Leitstreifen (gelb)  h Hecke  W Stuetzmauer (Front)  T Treppe
Hoehen:   1 Siedlung, 2 Park, 3 Portal-Terrasse.  Gebaeude stehen als Objekte auf Gehweg (Liste 'gebaeude').
"""
import json, os
from collections import Counter
import numpy as np
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte31')
VORLAGE = os.path.join(ROOT, 'assets', 'vorlagen', 'karte31_vorlage.png')
C, R, T = 120, 104, 16
REF = {'n': (99, 142, 67), 'w': (187, 163, 118), 'e': (173, 155, 113), 'g': (147, 158, 155), 's': (52, 61, 73),
       'p': (176, 163, 137), 'd': (212, 188, 128), 'h': (132, 152, 68), 'k': (145, 159, 164)}
GEBAEUDE = [  # x0, y0, x1, y1 (Kacheln, Fuss = y1), Art
    [4, 37, 35, 49, 'block1'], [44, 37, 49, 72, 'turm12'], [68, 37, 109, 49, 'block2'], [113, 37, 118, 79, 'turm5'],
    [74, 67, 105, 79, 'block3'], [8, 77, 27, 83, 'bahnhof'], [73, 86, 117, 92, 'laeden']]
MAUER = (30, 32)                          # Stuetzmauer Park -> Siedlung (Front-Reihen)
MAUER_TREPPEN = [(10, 15), (56, 64), (98, 103)]
TERRASSE = (86, 0, 119, 18)               # Portal-Terrasse (Ebene 3), Front Reihen 19-20
TERRASSE_FRONT = (19, 20)
TERRASSE_TREPPE = (95, 98)
HOCHBAHN = {'x0': 0, 'x1': 27, 'y0': 74, 'y1': 77, 'zug': [1, 18], 'pfeiler': [3]}


def r_(k, x0, y0, x1, y1, art):
    k[y0:y1 + 1, x0:x1 + 1] = art


def klassen():
    a = np.array(Image.open(VORLAGE).convert('RGB')).astype(int)
    k = np.full((R, C), '?')
    for y in range(R):
        for x in range(C):
            m = np.median(a[y * T:(y + 1) * T, x * T:(x + 1) * T].reshape(-1, 3), 0)
            d = {c: np.abs(m - np.array(v)).sum() for c, v in REF.items()}
            c = min(d, key=d.get)
            k[y, x] = c if d[c] < 35 else '?'
    return k


def main():
    os.makedirs(KARTE, exist_ok=True)
    k = klassen()
    k[k == 'k'] = 'g'
    k[(k == 'e') & (np.arange(R)[:, None] < 30)] = 'w'               # Park: Erdwege; Siedlung: Erdboden
    k[(k == 'w') & (np.arange(R)[:, None] >= 33)] = 'e'
    for (x0, y0, x1, y1, _) in GEBAEUDE:
        r_(k, x0, y0, x1, y1, 'g')
    for _ in range(6):                                               # unklare Kacheln aus den Nachbarn
        neu = k.copy()
        for y in range(R):
            for x in range(C):
                if k[y, x] == '?':
                    nb = [k[yy, xx] for yy, xx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1))
                          if 0 <= yy < R and 0 <= xx < C and k[yy, xx] != '?']
                    if nb:
                        neu[y, x] = Counter(nb).most_common(1)[0][0]
        k = neu
    k[k == '?'] = 'g'
    for y in list(range(2, 25)) + [100, 101]:                        # Baumstaemme als 'Hecke' erkannt -> Rasen
        for x in range(C):
            if k[y, x] == 'h':
                k[y, x] = 'n'
    r_(k, 2, 99, 119, 99, 'g')
    # ---- Park oben: Rasen, Hecken nur am oberen Rand und als Beete an der Promenade
    r_(k, 0, 0, 85, 1, 'h')
    r_(k, 86, 0, 119, 1, 'n')
    r_(k, 0, 26, 119, 29, 'g')                                       # Promenade auf der Mauer
    # ---- Stuetzmauer und Treppen
    r_(k, 0, MAUER[0], 119, MAUER[1], 'W')
    for (x0, x1) in MAUER_TREPPEN:
        r_(k, x0, MAUER[0], x1, MAUER[1], 'T')
    r_(k, TERRASSE[0] + 1, TERRASSE_FRONT[0], TERRASSE[2], TERRASSE_FRONT[1], 'W')
    r_(k, TERRASSE_TREPPE[0], TERRASSE_FRONT[0], TERRASSE_TREPPE[1], TERRASSE_FRONT[1], 'T')
    # ---- Siedlung: Heckenrand links/unten, Strassen
    r_(k, 0, 33, 1, 92, 'h')
    r_(k, 0, 102, 119, 103, 'h')
    r_(k, 57, 36, 63, 92, 's')                                       # Querstrasse (unter der Fussgaengerbruecke)
    r_(k, 66, 81, 119, 84, 's')                                      # Strasse rechts
    r_(k, 2, 94, 119, 98, 's')                                       # Strasse unten
    # ---- Bahnhof: Vorplatz mit Leitstreifen, Hochbahn links
    r_(k, 0, 74, 27, 92, 'g')
    r_(k, 2, 84, 7, 85, 'g')
    r_(k, 8, 84, 27, 84, 'y'); r_(k, 18, 84, 18, 91, 'y')            # Leitstreifen (Vorlage: gelbe Linie zum Bahnhof)
    r_(k, 2, 92, 27, 92, 'y')
    # ---- Hoehen
    h = np.ones((R, C), int)
    h[:MAUER[0], :] = 2
    h[TERRASSE[1]:TERRASSE[3] + 1, TERRASSE[0]:TERRASSE[2] + 1] = 3
    lay = {'groesse': [C, R], 'klassen': [''.join(z) for z in k], 'hoehe': [''.join(str(c) for c in z) for z in h],
           'gebaeude': GEBAEUDE, 'mauer': list(MAUER), 'mauer_treppen': MAUER_TREPPEN, 'terrasse': list(TERRASSE),
           'terrasse_front': list(TERRASSE_FRONT), 'terrasse_treppe': list(TERRASSE_TREPPE), 'hochbahn': HOCHBAHN,
           'zebra': [[57, 63, 88, 89, 'v'], [54, 55, 94, 98, 'h'], [64, 65, 94, 98, 'h']],
           'treppen_sued': [[x0, x1, 2, MAUER[0] - 1] for (x0, x1) in MAUER_TREPPEN] +
                           [[TERRASSE_TREPPE[0], TERRASSE_TREPPE[1], 3, TERRASSE_FRONT[0] - 1]],
           'teleporter': [{'x': 103, 'y': 2, 'b': 3, 'h': 3, 'farbe': 'violett'}]}
    json.dump(lay, open(os.path.join(KARTE, 'layout.json'), 'w'), indent=0)
    F = {'n': (99, 142, 67), 'w': (187, 163, 118), 'e': (173, 155, 113), 'g': (147, 158, 155), 's': (52, 61, 73),
         'p': (176, 163, 137), 'd': (212, 188, 128), 'y': (230, 200, 60), 'h': (60, 100, 40), 'W': (110, 116, 130),
         'T': (200, 200, 210)}
    out = np.zeros((R, C, 3), np.uint8)
    for kk, c in F.items():
        out[k == kk] = c
    out = (out * (0.8 + 0.1 * h[..., None])).clip(0, 255).astype(np.uint8)
    for (x0, y0, x1, y1, _) in GEBAEUDE:
        out[y0:y1 + 1, x0:x1 + 1] = (out[y0:y1 + 1, x0:x1 + 1] * 0.5 + np.array((200, 60, 60)) * 0.5).astype(np.uint8)
    vor = Image.open(VORLAGE).convert('RGB').resize((C * 4, R * 4))
    bild = Image.new('RGB', (C * 8 + 8, R * 4))
    bild.paste(vor, (0, 0))
    bild.paste(Image.fromarray(out).resize((C * 4, R * 4), 0), (C * 4 + 8, 0))
    bild.save(os.path.join(KARTE, 'layout_vergleich.png'))
    print('Karte 31 Layout %dx%d' % (C, R))


if __name__ == '__main__':
    main()
