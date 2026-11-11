"""Karte 30 - Odaiba (A02), Layout nach der Vorlage -> maps/karte30/layout.json

  python3 tools/karte30_layout.py

Vorlage assets/vorlagen/karte30_vorlage.png: 2080x1760 px = 130x110 Kacheln (genau am 16er-Raster). Bucht-Stadtteil
am Tag: Fernsehgebaeude mit Kugel oben, Platz davor, Buerohaeuser, Hauptstrasse mit Riesenrad, Hochbahn mit Bahnhof,
Uferstrasse, Parkstreifen mit Palmen, Strand mit Holzpromenade, Pier ins Meer, Bruecke oben rechts uebers Wasser.

Klassen (wie Karte 18):  s Asphalt  g Gehweg  p Platz (Sandstein)  n Rasen  d Sand  w Wasser
                         v Pier (Steinplatten)  k Kaikante  b Holzpromenade  o Wasserbecken  f Waldrand
Hoehen: 0 Wasser, 1 Boden.  Gebaeude stehen als Objekte auf Gehweg (Liste 'gebaeude').
"""
import json, os
from collections import Counter
import numpy as np
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte30')
VORLAGE = os.path.join(ROOT, 'assets', 'vorlagen', 'karte30_vorlage.png')
C, R, T = 130, 110, 16
REF = {'n': (99, 142, 67), 'g': (168, 178, 177), 's': (52, 61, 73), 'p': (176, 163, 137), 'd': (162, 133, 95),
       'w': (49, 91, 135), 'k': (145, 159, 164)}
GEBAEUDE = [  # x0, y0, x1, y1 (Kacheln, Fuss = y1), Art
    [50, 0, 79, 26, 'fernsehturm'], [4, 16, 41, 30, 'buero_lang'], [88, 32, 105, 44, 'buero_glas'],
    [119, 34, 127, 44, 'buero_klein'], [24, 56, 57, 66, 'laeden'], [64, 56, 93, 66, 'buero_flach'],
    [119, 56, 128, 66, 'buero_klein2'], [3, 70, 22, 78, 'bahnhof']]
BRUECKE = (110, 0, 117, 21)       # Bruecke ueber das Wasser (Fahrbahn 112-115, Gehwege/Gelaender aussen)
HOCHBAHN = {'x0': 3, 'x1': 129, 'y0': 68, 'y1': 71, 'pfeiler': [27, 34, 41, 48, 55, 69, 76, 83, 90, 104, 111, 118, 125],
            'zug': [4, 21]}


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
            k[y, x] = c if d[c] < 40 else '?'
    return k


def main():
    os.makedirs(KARTE, exist_ok=True)
    k = klassen()
    k[k == 'k'] = 'g'                                                # Bordsteine/Kanten zeichnet der Bau selbst
    for (x0, y0, x1, y1, _) in GEBAEUDE:                             # unter Gebaeuden Gehweg
        r_(k, x0, y0, x1, y1, 'g')
    for _ in range(6):                                               # unklare Kacheln (Objekte) aus den Nachbarn
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
    # ---- Ausreisser der Farberkennung (Schraffuren, Schilder) bereinigen
    for y in range(R):
        for x in range(C):
            strand = y >= 85 or (x >= 85 and y <= 24)
            if k[y, x] == 'd' and not strand:
                k[y, x] = 'g'
            if k[y, x] == 'p' and not (50 <= x <= 78 and 26 <= y <= 49):
                k[y, x] = 'g'
            if k[y, x] == 'w' and y < 85 and not (x >= 85 and y <= 24):
                k[y, x] = 'g'
    # ---- Fernsehgebaeude oben: ringsum Rasen, Gehweg nur unter dem Bau
    r_(k, 50, 0, 79, 26, 'g')
    r_(k, 79, 0, 87, 15, 'n')
    # ---- Platz vor dem Fernsehgebaeude: Rahmen (Sandstein), Gehwegring, Innenfeld
    r_(k, 52, 27, 77, 48, 'g')
    r_(k, 55, 28, 74, 47, 'p')
    r_(k, 58, 31, 71, 44, 'g')
    r_(k, 60, 33, 69, 42, 'p')
    # ---- Becken links (Vorlage: dunkle Flaeche mit Rasen-Insel) und Rasenstreifen
    r_(k, 10, 35, 33, 39, 'o')
    r_(k, 16, 36, 27, 38, 'n')
    # ---- Strassen
    r_(k, 0, 50, 125, 54, 's')                                       # Hauptstrasse
    r_(k, 59, 55, 62, 67, 's'); r_(k, 95, 55, 98, 67, 's')          # Querstrassen bis unter die Hochbahn
    r_(k, 23, 72, 129, 72, 's')                                      # Fahrbahn unter der Hochbahn (Schattenseite)
    r_(k, 23, 73, 129, 74, 'n')                                      # Rasen-Mittelstreifen mit Pfeilern
    r_(k, 59, 73, 62, 74, 's'); r_(k, 95, 73, 98, 74, 's')          # Durchfahrten
    r_(k, 23, 75, 125, 78, 's')                                      # Uferstrasse
    r_(k, 112, 0, 115, 49, 's')                                      # Brueckenstrasse
    r_(k, 110, 22, 111, 48, 'g'); r_(k, 116, 22, 117, 48, 'g')      # Gehwege neben der Brueckenstrasse an Land
    r_(k, 110, 0, 111, 21, 'g'); r_(k, 116, 0, 117, 21, 'g')        # Gehwege auf der Bruecke
    r_(k, 106, 0, 109, 21, 'w'); r_(k, 118, 0, 121, 21, 'w')        # Wasser direkt neben der Bruecke
    # ---- Bahnhof / Hochbahn
    r_(k, 0, 66, 22, 79, 'g')
    r_(k, 23, 66, 129, 67, 'g')                                      # Gehweg hinter der Hochbahn
    r_(k, 3, 68, 129, 71, 'g')                                       # unter der Hochbahn (verdeckt)
    # ---- Waldrand rechts
    r_(k, 126, 21, 129, 48, 'f'); r_(k, 126, 55, 129, 90, 'f')
    r_(k, 129, 49, 129, 54, 'f')
    # ---- Strand, Holzpromenade, Pier
    r_(k, 0, 91, 126, 100, 'd')
    for y in range(85, 101):                                         # Bucht am Pier: Wasser aus der Vorlage behalten
        for x in range(40, 80):
            if blau_cache[y, x]:
                k[y, x] = 'w'
    r_(k, 26, 92, 41, 93, 'b'); r_(k, 75, 92, 125, 93, 'b')
    r_(k, 50, 90, 67, 107, 'v')                                      # Pier
    r_(k, 57, 85, 60, 89, 'v')                                       # Stufen vom Park zum Pier
    r_(k, 127, 91, 129, 100, 'w')
    r_(k, 0, 101, 129, 109, 'w')
    r_(k, 50, 101, 67, 107, 'v')
    r_(k, 4, 100, 7, 103, 'd')                                       # Sandinsel mit Strudel-Teleporter
    h = np.ones((R, C), int)
    h[np.isin(k, ['w'])] = 0
    lay = {'groesse': [C, R], 'klassen': [''.join(z) for z in k], 'hoehe': [''.join(str(c) for c in z) for z in h],
           'gebaeude': GEBAEUDE, 'bruecke': list(BRUECKE), 'hochbahn': HOCHBAHN, 'platz': [55, 28, 74, 47],
           'achse': 65, 'pier': [50, 85, 67, 107],
           'zebra': [[59, 62, 49, 50, 'h'], [95, 98, 49, 50, 'h'], [59, 62, 73, 74, 'h'], [95, 98, 73, 74, 'h'],
                     [56, 58, 75, 78, 'v'], [63, 65, 75, 78, 'v'], [92, 94, 75, 78, 'v'], [99, 101, 75, 78, 'v']],
           'teleporter': [{'x': 5, 'y': 101, 'b': 2, 'h': 2, 'farbe': 'violett'}],
           'treppen_sued': []}
    json.dump(lay, open(os.path.join(KARTE, 'layout.json'), 'w'), indent=0)
    F = {'s': (52, 61, 73), 'g': (168, 178, 177), 'p': (176, 163, 137), 'n': (99, 142, 67), 'd': (162, 133, 95),
         'w': (49, 91, 135), 'v': (130, 140, 150), 'k': (90, 90, 100), 'b': (120, 84, 50), 'o': (40, 120, 160),
         'f': (40, 80, 40)}
    out = np.zeros((R, C, 3), np.uint8)
    for kk, c in F.items():
        out[k == kk] = c
    for (x0, y0, x1, y1, _) in GEBAEUDE:
        out[y0:y1 + 1, x0:x1 + 1] = (out[y0:y1 + 1, x0:x1 + 1] * 0.5 + np.array((200, 60, 60)) * 0.5).astype(np.uint8)
    out[68:72, 3:130] = (out[68:72, 3:130] * 0.5 + np.array((60, 60, 200)) * 0.5).astype(np.uint8)
    vor = Image.open(VORLAGE).convert('RGB').resize((C * 4, R * 4))
    bild = Image.new('RGB', (C * 8 + 8, R * 4))
    bild.paste(vor, (0, 0))
    bild.paste(Image.fromarray(out).resize((C * 4, R * 4), 0), (C * 4 + 8, 0))
    bild.save(os.path.join(KARTE, 'layout_vergleich.png'))
    print('Karte 30 Layout %dx%d' % (C, R))


blau_cache = None
if __name__ == '__main__':
    _a = np.array(Image.open(VORLAGE).convert('RGB')).astype(int)
    _b = (_a[..., 2] > _a[..., 0] + 40).reshape(R, T, C, T).mean(axis=(1, 3))
    blau_cache = _b > 0.5
    main()
