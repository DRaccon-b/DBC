"""Karte 05 (Freezeland): Kachelraster aus der Vorlage ableiten -> maps/karte05/layout.json

  python3 tools/karte05_layout.py

Vorlage assets/vorlagen/karte05_vorlage.png (1760x1360 = 110x85 Kacheln a 16 px).
Klassen: s Schnee, w Weg (festgetretener Schnee), l Eisboden (gefrorene Flaeche), i Eissee, d Eisloch (offenes
Wasser im See), x Meer, k Gletscherspalte, e gefrorene Erde (Dorfplatz), r Felsboden, h Waldrand (Tannen).
Hoehen: 0 Meer/Spalten, 1 Schneefeld, 2 Nordplateau hinter den Eisklippen.
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from collections import Counter
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte05')
T = 16
ZENTREN = {'s': (225, 232, 236), 'w': (186, 206, 220), 'l': (157, 210, 231), 'i': (114, 185, 211),
           'c': (138, 176, 198), 'h': (90, 140, 150), 'e': (150, 122, 86), 'd': (10, 25, 60)}


def ableiten():
    im = np.array(Image.open(os.path.join(ROOT, 'assets', 'vorlagen', 'karte05_vorlage.png')).convert('RGB')).astype(float)
    R, C = im.shape[0] // T, im.shape[1] // T
    med = np.zeros((R, C, 3)); std = np.zeros((R, C))
    for y in range(R):
        for x in range(C):
            b = im[y * T:(y + 1) * T, x * T:(x + 1) * T].reshape(-1, 3)
            med[y, x] = np.median(b, axis=0); std[y, x] = b.std(axis=0).mean()
    keys = list(ZENTREN); cen = np.array([ZENTREN[k] for k in keys])
    cls = np.array(keys)[((med[:, :, None] - cen[None, None]) ** 2).sum(-1).argmin(-1)]
    return cls, std, R, C


def mehrheit(cls, maske, R, C, ausschluss=''):
    neu = cls.copy()
    for y in range(R):
        for x in range(C):
            if not maske[y, x]:
                continue
            nb = [cls[yy, xx] for yy in range(max(0, y - 2), min(R, y + 3)) for xx in range(max(0, x - 2), min(C, x + 3))
                  if not maske[yy, xx] and cls[yy, xx] not in ausschluss]
            if nb:
                neu[y, x] = Counter(nb).most_common(1)[0][0]
    return neu


def splitter_weg(neu, arten, minimum, ersatz='s'):
    from collections import deque
    R, C = neu.shape
    gesehen = np.zeros((R, C), bool)
    for y in range(R):
        for x in range(C):
            k = neu[y, x]
            if k not in arten or gesehen[y, x]:
                continue
            q = deque([(y, x)]); gesehen[y, x] = True; teil = []
            while q:
                a, b = q.popleft(); teil.append((a, b))
                for da, db in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    aa, bb = a + da, b + db
                    if 0 <= aa < R and 0 <= bb < C and not gesehen[aa, bb] and neu[aa, bb] == k:
                        gesehen[aa, bb] = True; q.append((aa, bb))
            if len(teil) < minimum:
                for a, b in teil:
                    neu[a, b] = ersatz
    return neu


def main():
    cls, std, R, C = ableiten()
    yy, xx = np.mgrid[0:R, 0:C]
    roh = cls.copy()
    # Objekt-Kacheln (hohe Varianz) nach Nachbarn; Klippen 'c' ebenfalls, die Hoehe kommt aus dem Plan
    unsicher = (std > 22) | (cls == 'c')
    cls = mehrheit(cls, unsicher, R, C, ausschluss='c')
    neu = cls.copy()

    # ---------------------------------------------------------------- Hoehe 2: Nordplateau
    # je Spalte die suedlichste Klippenkachel der Vorlage (Zeilen 0..22, Spalten 0..89); das Plateau reicht
    # bis 2 Kacheln oberhalb davon (die Front wird darunter gezeichnet)
    hoehe = np.ones((R, C), int)
    PLATEAU = [  # (x0, y0, x1, y1) in Kacheln: Oberkante der Eisklippen (Front 2,5 Kacheln wird darunter gezeichnet)
        (0, 0, 89, 5),       # Eisschild im Norden
        (3, 0, 11, 6),
        (16, 0, 30, 13),     # Bucht A (Treppe 24-27)
        (31, 0, 40, 6),
        (41, 0, 58, 16),     # Bucht B (Treppe 49-52)
        (59, 0, 71, 6),      # Hoehleneingang
        (72, 0, 87, 17),     # Bucht C (Treppe 77-80)
        (88, 0, 89, 7),
    ]
    for (x0, y0, x1, y1) in PLATEAU:
        hoehe[y0:y1 + 1, x0:x1 + 1] = 2
    # Meer oben (Eismeer hinter dem Plateau) und rechts
    neu[0:2, 0:90] = 'l'
    neu[(xx >= 105) & (yy >= 11)] = 'x'
    hoehe[(xx >= 105) & (yy >= 11)] = 0
    neu[(xx >= 104) & (yy >= 11) & (neu != 'x')] = 's'
    # Plateau-Innenflaechen: Schnee, Eisflecken bleiben
    pl = hoehe == 2
    neu[pl & ~np.isin(neu, list('xl'))] = 's'

    # ---------------------------------------------------------------- Waldrand links und unten
    neu[10:, 0:3] = 'h'
    neu[(xx <= 4) & (yy >= 10)] = 'h'
    neu[(yy >= 81) & (xx <= 103)] = 'h'
    neu[(yy >= 80) & (xx <= 103) & (np.isin(roh, list('hc')))] = 'h'
    # Ausgang unten (Weg zum Teleporter) und rechts unten Schnee
    neu[78:85, 30:34] = 'w'
    neu[80:85, 96:104] = 's'

    # ---------------------------------------------------------------- Eissee, Loecher, Spalten
    see = (xx >= 40) & (xx <= 75) & (yy >= 26) & (yy <= 50)
    neu[see & (roh == 'd')] = 'd'
    neu[see & (neu == 'i')] = 'i'
    spalte = (xx >= 82) & (xx <= 102) & (yy >= 20) & (yy <= 47) & (roh == 'd')
    neu[(xx >= 82) & (yy >= 20) & (yy <= 47) & (neu == 'd') & ~spalte] = 's'
    neu[spalte] = 'k'
    neu[(neu == 'd') & ~see] = 's'
    hoehe[spalte] = 0
    # Dorfplatz
    dorf = ((xx - 29.5) / 10.5) ** 2 + ((yy - 71) / 8.5) ** 2 <= 1
    neu[dorf & np.isin(neu, list('esl'))] = 'e'
    # Felsboden-Flecken
    for (x0, y0, x1, y1) in ((62, 55, 68, 57), (55, 74, 61, 78)):
        neu[y0:y1 + 1, x0:x1 + 1] = 'r'
    # Aufraeumen
    neu = splitter_weg(neu, 'wl', 4)
    neu = splitter_weg(neu, 'e', 6)
    neu = splitter_weg(neu, 'd', 3, 'i')
    hoehe[neu == 'x'] = np.where(hoehe[neu == 'x'] == 2, 2, 0)

    extras = {
        'teleporter': [{'x': 107, 'y': 3, 'b': 2, 'h': 3}, {'x': 30, 'y': 83, 'b': 4, 'h': 2}],
        # Treppen an den drei Plateaubuchten (x0, x1, y0, y1, Richtung)
        'treppen': [[24, 27, 11, 17, 's'], [49, 52, 13, 20, 's'], [77, 80, 14, 21, 's']],
        # Holzbruecken ueber die Spalten (x0, y0, x1, y1) und Steg in den See (x0, y0, x1, y1)
        'bruecken': [[92, 33, 95, 35], [90, 41, 93, 42]],
        'stege': [[43, 45, 49, 46]],
    }
    lay = {'groesse': [C, R], 'klassen': [''.join(r) for r in neu],
           'hoehe': [''.join(str(v) for v in r) for r in hoehe]}
    lay.update(extras)
    json.dump(lay, open(os.path.join(KARTE, 'layout.json'), 'w'), indent=0)

    F = {'s': (250, 250, 250), 'w': (170, 170, 190), 'l': (150, 210, 240), 'i': (60, 140, 200), 'x': (30, 80, 180),
         'h': (20, 90, 80), 'e': (150, 100, 50), 'd': (10, 10, 40), 'k': (60, 0, 60), 'r': (120, 120, 130)}
    out = np.zeros((R, C, 3), np.uint8)
    for k, v in F.items():
        out[neu == k] = v
    out[(hoehe == 2) & (neu == 's')] = (220, 240, 210)
    vor = Image.open(os.path.join(ROOT, 'assets', 'vorlagen', 'karte05_vorlage.png')).resize((C * 8, R * 8))
    bild = Image.new('RGB', (C * 16 + 8, R * 8))
    bild.paste(vor, (0, 0)); bild.paste(Image.fromarray(out).resize((C * 8, R * 8), 0), (C * 8 + 8, 0))
    bild.save(os.path.join(KARTE, 'layout_vergleich.png'))
    print(C, R)


if __name__ == '__main__':
    main()
