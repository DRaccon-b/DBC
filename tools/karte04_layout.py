"""Karte 04 (Gear Savanna): Kachelraster aus der Vorlage ableiten -> maps/karte04/layout.json

  python3 tools/karte04_layout.py

Vorlage assets/vorlagen/karte04_vorlage.png (1760x1360 = 110x85 Kacheln a 16 px). Jede Kachel wird ueber
ihre Medianfarbe einer Bodenart zugeordnet, Objekt-/Klippenkacheln (hohe Varianz) ueber die Nachbarn.
Klassen: s Savanne, d Olivgras, e Erde, w Weg, g Plateau (hoch), c Canyonboden (tief), x Wasser,
m Schlamm, a Asche, t Teer (tief), h Hecke. Danach werden Formen geglaettet und von Hand nachgezogen.
"""
import json, os
import numpy as np
from collections import Counter
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
T = 16
ZENTREN = {'s': (200, 177, 107), 'c': (160, 137, 98), 'w': (183, 154, 105), 'd': (162, 158, 100),
           'g': (185, 195, 126), 't': (66, 64, 76), 'h': (102, 114, 70), 'e': (180, 138, 96),
           'x': (55, 122, 158), 'a': (108, 108, 96), 'm': (146, 128, 98)}


def ableiten():
    im = np.array(Image.open(os.path.join(ROOT, 'assets', 'vorlagen', 'karte04_vorlage.png')).convert('RGB')).astype(float)
    R, C = im.shape[0] // T, im.shape[1] // T
    med = np.zeros((R, C, 3)); std = np.zeros((R, C))
    for y in range(R):
        for x in range(C):
            b = im[y * T:(y + 1) * T, x * T:(x + 1) * T].reshape(-1, 3)
            med[y, x] = np.median(b, axis=0); std[y, x] = b.std(axis=0).mean()
    keys = list(ZENTREN); cen = np.array([ZENTREN[k] for k in keys])
    cls = np.array(keys)[((med[:, :, None] - cen[None, None]) ** 2).sum(-1).argmin(-1)]
    unsicher = std > 26
    # unsichere Kacheln (Objekte, Klippen) nach Mehrheit der sicheren Nachbarn
    for _ in range(3):
        neu = cls.copy()
        for y in range(R):
            for x in range(C):
                if not unsicher[y, x]:
                    continue
                nb = [cls[yy, xx] for yy in range(max(0, y - 2), min(R, y + 3)) for xx in range(max(0, x - 2), min(C, x + 3))
                      if not unsicher[yy, xx]]
                if nb:
                    neu[y, x] = Counter(nb).most_common(1)[0][0]
        cls = neu
    return cls, R, C


def glaetten(cls, R, C, arten='sdeam', runden=2):
    """Einzelne Ausreisser in weichen Bodenarten durch Nachbarmehrheit ersetzen."""
    for _ in range(runden):
        neu = cls.copy()
        for y in range(R):
            for x in range(C):
                if cls[y, x] not in arten:
                    continue
                nb = Counter(cls[yy, xx] for yy in range(max(0, y - 1), min(R, y + 2)) for xx in range(max(0, x - 1), min(C, x + 2)))
                k, n = nb.most_common(1)[0]
                if nb[cls[y, x]] <= 2 and n >= 5:
                    neu[y, x] = k
        cls = neu
    return cls


def setze(cls, art, x0, y0, x1, y1):
    cls[y0:y1 + 1, x0:x1 + 1] = art


def maske_schliessen(m, n=1):
    from PIL import ImageFilter
    im = Image.fromarray(m.astype(np.uint8) * 255)
    for _ in range(n):
        im = im.filter(ImageFilter.MaxFilter(3))
    for _ in range(n):
        im = im.filter(ImageFilter.MinFilter(3))
    return np.array(im) > 0


def splitter_weg(neu, arten, minimum):
    """Zusammenhaengende Flaechen einer Art mit weniger als minimum Kacheln -> Savanne."""
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
                    neu[a, b] = 's'
    return neu


def main():
    cls, R, C = ableiten()
    cls = glaetten(cls, R, C)
    yy, xx = np.mgrid[0:R, 0:C]
    # --- Plateaus: g-Flaechen schliessen, kleine Splitter weg
    g = maske_schliessen(cls == 'g', 1)
    # --- Canyon: zusammenhaengender Bereich um c/x in der Mitte (Spalten 44..68)
    can = np.isin(cls, list('cx')) & (xx >= 44) & (xx <= 68)
    for y in range(R):                                       # Zeilen fuellen zwischen erstem und letztem c
        xs = np.nonzero(can[y])[0]
        if len(xs):
            can[y, xs.min():xs.max() + 1] = True
    for y in list(range(20, 24)) + list(range(40, 43)) + list(range(58, 62)):   # Furten/Bruecke
        prev = [y0 for y0 in range(y - 1, -1, -1) if can[y0].any()][0]
        can[y] = can[prev]
    can = maske_schliessen(can, 1)
    neu = np.full((R, C), 's')
    # weiche Bodenarten aus der Vorlage uebernehmen
    for k in 'dematxh':
        neu[cls == k] = k
    neu[(cls == 't')] = 't'
    neu[g] = 'g'
    neu[can] = 'c'
    # Fluss: Wasser der Vorlage innerhalb des Canyons
    neu[can & (cls == 'x')] = 'x'
    # Wege (von Hand), Lagerplatz
    WEGE = [(0, 40, 109, 42), (84, 0, 88, 39), (39, 24, 41, 39), (39, 21, 46, 23), (64, 21, 72, 23),
            (70, 24, 72, 39), (77, 43, 79, 55), (77, 53, 85, 56), (41, 43, 43, 57), (41, 58, 48, 60),
            (63, 58, 77, 60), (76, 26, 80, 30), (92, 26, 96, 30), (76, 31, 78, 39), (92, 31, 94, 39),
            (22, 24, 24, 26), (23, 27, 38, 29)]
    for (x0, y0, x1, y1) in WEGE:
        m = (xx >= x0) & (xx <= x1) & (yy >= y0) & (yy <= y1)
        neu[m & ~can & (neu != 'g')] = 'w'
    lager = ((xx - 9.5) / 9.5) ** 2 + ((yy - 43) / 6.5) ** 2 <= 1
    neu[lager & (neu != 'h')] = 'w'
    # Furten im Canyon (heller Boden), Bruecke liegt auf der Hauptstrasse
    for (y0, y1) in ((20, 23), (58, 61)):
        m = can & (yy >= y0) & (yy <= y1)
        neu[m & (neu != 'x')] = 'f'
    neu[can & (yy >= 40) & (yy <= 42) & (neu != 'x')] = 'c'
    # Hecke nur am Rand (Vorlage) - zusammenhaengend machen
    h = maske_schliessen(neu == 'h', 1)
    h &= (xx <= 6) | (yy >= 79) | ((xx >= 105) & (yy >= 34) & (yy <= 47))
    neu[(neu == 'h') & ~h] = 's'
    neu[h] = 'h'
    # Wege enden vor der Canyonwand (Hoehenlogik); nur die Hauptstrasse fuehrt ueber die Bruecke
    for y in range(R):
        if 40 <= y <= 42:
            continue
        for x in range(C):
            if neu[y, x] == 'w' and not can[y, x] and can[y, max(0, x - 2):x + 3].any():
                neu[y, x] = 's'
    # Weg unter der Treppe des rechten Plateaustreifens
    neu[60:63, 107:110] = 'w'
    # Teer/Asche: Asche-Ring um das Teerbecken
    t = maske_schliessen(neu == 't', 1) & (xx >= 72)
    neu[(neu == 't') & ~t] = 'a'
    neu[t] = 't'
    # schmaler Teerkanal bis zum Monument schliessen (Asche)
    neu[(yy <= 61) & (xx >= 85) & (xx <= 91) & (neu == 't')] = 'a'
    # Aufraeumen: Plateau-Umriss per Mehrheit glaetten, kleine Splitter aller weichen Arten entfernen
    for _ in range(2):
        gm = neu == 'g'
        cnt = sum(np.roll(np.roll(gm, dy, 0), dx, 1) for dy in (-1, 0, 1) for dx in (-1, 0, 1))
        neu[(gm) & (cnt <= 3)] = 's'
        neu[(~gm) & (cnt >= 6) & (neu == 's')] = 'g'
    neu = splitter_weg(neu, 'dema', 5)
    neu = splitter_weg(neu, 'g', 8)
    # Fluss durchgehend: Zeilen im Canyon ohne Wasser bekommen Wasser zwischen den Nachbarzeilen
    wz = {y: np.nonzero((neu[y] == 'x') & can[y])[0] for y in range(R)}
    for y in range(R):
        if not can[y].any() or len(wz[y]):
            continue
        oben = [yy for yy in range(y - 1, -1, -1) if len(wz[yy])]
        unten = [yy for yy in range(y + 1, R) if len(wz[yy])]
        if not oben or not unten:
            continue
        ya, yb = oben[0], unten[0]
        t = (y - ya) / (yb - ya)
        ca = wz[ya].mean(); cb = wz[yb].mean()
        c = int(round(ca + (cb - ca) * t))
        neu[y, c - 1:c + 1] = 'x'
    hoehe = np.ones((R, C), int)
    hoehe[neu == 'g'] = 2
    hoehe[np.isin(neu, list('cxf')) & can] = 0
    hoehe[neu == 't'] = 0
    json.dump({'groesse': [C, R], 'klassen': [''.join(r) for r in neu],
               'hoehe': [''.join(str(v) for v in r) for r in hoehe]},
              open(os.path.join(ROOT, 'maps', 'karte04', 'layout_auto.json'), 'w'), indent=0)
    extras = {
        'teleporter': [{'x': 0, 'y': 40, 'b': 2, 'h': 3}, {'x': 108, 'y': 40, 'b': 2, 'h': 3},
                       {'x': 85, 'y': 0, 'b': 4, 'h': 2}],
        # Canyon-Rampen an den Uebergaengen (Kachel-Rechtecke)
        'rampen': [],
        'furten': [[20, 23], [58, 61]],
        'bruecke': [40, 42],
        'treppen': [[22, 24, 17, 23, 's'], [76, 79, 22, 29, 's'], [92, 95, 24, 31, 's'], [107, 109, 55, 61, 's'], [92, 94, 60, 64, 's', 'teer']],
    }
    lay = {'groesse': [C, R], 'klassen': [''.join(r) for r in neu],
           'hoehe': [''.join(str(v) for v in r) for r in hoehe]}
    lay.update(extras)
    json.dump(lay, open(os.path.join(ROOT, 'maps', 'karte04', 'layout.json'), 'w'), indent=0)
    F = {'s': (232, 204, 110), 'c': (140, 100, 60), 'w': (225, 170, 120), 'd': (150, 165, 80), 'g': (170, 230, 140),
         't': (30, 30, 40), 'h': (30, 90, 40), 'e': (200, 110, 70), 'x': (40, 110, 220), 'a': (130, 130, 120),
         'm': (110, 85, 80), 'f': (180, 140, 90)}
    out = np.zeros((R, C, 3), np.uint8)
    for k, v in F.items():
        out[neu == k] = v
    vor = Image.open(os.path.join(ROOT, 'assets', 'vorlagen', 'karte04_vorlage.png')).resize((C * 8, R * 8))
    bild = Image.new('RGB', (C * 16 + 8, R * 8))
    bild.paste(vor, (0, 0)); bild.paste(Image.fromarray(out).resize((C * 8, R * 8), 0), (C * 8 + 8, 0))
    bild.save(os.path.join(ROOT, 'maps', 'karte04', 'layout_vergleich.png'))
    print(C, R)


if __name__ == '__main__':
    main()
