"""Karte 26 - The Kaiser's Fortress (A02), Layout nach der Vorlage -> maps/karte26/layout.json

  python3 tools/karte26_layout.py

Vorlage assets/vorlagen/karte26_vorlage.png: 1440x1280 px = 90x80 Kacheln. Das Innere des Kaiser-Flaggschiffs
(Karte 25): Raeume aus Stahlplatten in der dunklen Schiffshuelle - Thronsaal oben links, Labor mit Tanks oben rechts,
Zellen links Mitte, Saeulenraum, Portalraum, grosse Halle mit Warnstreifen, Raum unten; Gaenge dazwischen,
Teleporter oben und unten.

Klassen:  # Huelle (Wand/Aussen)  . Stahlboden  g Gitterboden  p Podest (heller, erhoeht)  W Wandfront (Rueckwand)
          r Warnstreifen  T Teleporter
"""
import json, os
import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte26')
VORLAGE = os.path.join(ROOT, 'assets', 'vorlagen', 'karte26_vorlage.png')
C, R, T = 90, 80, 16
HUELLE_PROBEN = ((1, 1), (2, 1), (1, 2), (2, 2), (0, 30), (1, 79), (89, 40))
TELEPORTER = [(35, 0, 6, 2), (42, 78, 6, 2)]
STREIFEN = (4, 55, 85, 55)
PODEST = [(4, 5, 33, 10)]
HALLE_WAND = [(4, 16), (20, 42), (48, 57), (61, 85)]   # Tueren bei x 17-19, 43-47, 58-60
RUECKWAENDE = [(42, 2, 85, 7)]                 # Labor: hohe Rueckwand mit Lueftungsgittern                      # Thronpodest (heller Boden), Kante darunter
WAENDE_EXTRA = [(34, 2, 34, 11), (34, 19, 34, 20)]   # duenne Wand Thronsaal | Gang (Durchgang Reihen 12-18, Nutzer: groesser)
DURCHGAENGE = [(34, 12, 34, 18)]
ZELLENWAENDE = [(12, 42, 12, 46), (25, 42, 25, 46)]


def main():
    os.makedirs(KARTE, exist_ok=True)
    a = np.array(Image.open(VORLAGE).convert('RGB')).astype(int)
    ex = [a[y * T:(y + 1) * T, x * T:(x + 1) * T] for (x, y) in HUELLE_PROBEN]
    k = np.full((R, C), '.')
    for y in range(R):
        for x in range(C):
            t = a[y * T:(y + 1) * T, x * T:(x + 1) * T]
            d = min(np.abs(t - e).mean() for e in ex)
            med = np.median(t.reshape(-1, 3), 0)
            if d < 12:
                k[y, x] = '#'
            elif np.abs(med - (33, 41, 58)).sum() < 14 and t.reshape(-1, 3).std(0).mean() > 18:
                k[y, x] = 'g'
    for (x0, y0, x1, y1) in WAENDE_EXTRA:
        k[y0:y1 + 1, x0:x1 + 1] = '#'
    # Wandfront: die ersten 3 Reihen unter der Huelle (Rueckwand mit Paneelen)
    for y in range(R):
        for x in range(C):
            if k[y, x] != '#' and any(y - d >= 0 and k[y - d, x] == '#' for d in (1, 2, 3)) and \
                    all(y - d < 0 or k[y - d, x] != '#' or True for d in (1,)):
                if y >= 1 and (k[y - 1, x] == '#' or (y >= 2 and k[y - 2, x] in '#W') or (y >= 3 and k[y - 3, x] == '#' and k[y - 1, x] == 'W')):
                    k[y, x] = 'W'
    # Aufraeumen: kleine Huellen-/Gitter-Inseln sind Objekte der Vorlage (Tanks, Kisten, Schatten) -> Boden
    from collections import deque
    for art, min_n in (('#', 8), ('g', 5)):
        gesehen = np.zeros((R, C), bool)
        for y in range(R):
            for x in range(C):
                if k[y, x] == art and not gesehen[y, x]:
                    comp, q = [], deque([(y, x)]); gesehen[y, x] = True
                    while q:
                        cy, cx = q.popleft(); comp.append((cy, cx))
                        for yy, xx in ((cy - 1, cx), (cy + 1, cx), (cy, cx - 1), (cy, cx + 1)):
                            if 0 <= yy < R and 0 <= xx < C and k[yy, xx] == art and not gesehen[yy, xx]:
                                gesehen[yy, xx] = True; q.append((yy, xx))
                    rand = any(cy in (0, R - 1) or cx in (0, C - 1) for cy, cx in comp)
                    if len(comp) < min_n and not rand:
                        for cy, cx in comp:
                            k[cy, cx] = '.'
    k[8:25, 42:86][k[8:25, 42:86] == 'g'] = '.'                     # Labor: Linien der Vorlage sind Tank-Schatten
    for (x0, x1) in HALLE_WAND:                                      # Halle: Wandfront mit Tueren zu den Raeumen darueber
        k[47, x0:x1 + 1] = '#'
        k[48:50, x0:x1 + 1] = 'W'
    for (x0, y0, x1, y1) in RUECKWAENDE:
        sub = k[y0:y1 + 1, x0:x1 + 1]
        sub[sub != '#'] = 'W'
    for (x0, y0, x1, y1) in ZELLENWAENDE:                          # Eckzellen unten: Seitenwand mit Decke (Nutzer)
        k[y0:y1 + 1, x0:x1 + 1] = '#'
    for (x0, y0, x1, y1) in DURCHGAENGE:                           # offene Durchgaenge (keine Wandstuecke)
        k[y0:y1 + 1, x0:x1 + 1] = '.'
        k[y0 - 2:y0, x0:x1 + 1] = 'W'                              # Decke ueber dem Durchgang: Wandfront (Nutzer)
    for (x0, y0, x1, y1) in PODEST:
        sub = k[y0:y1 + 1, x0:x1 + 1]
        sub[np.isin(sub, list('.g'))] = 'p'
    x0, y0, x1, y1 = STREIFEN
    sub = k[y0:y1 + 1, x0:x1 + 1]
    sub[sub != '#'] = 'r'
    for (tx, ty, b, hh) in TELEPORTER:
        k[ty:ty + hh, tx:tx + b] = 'T'
    lay = {'groesse': [C, R], 'klassen': [''.join(z) for z in k], 'podest': PODEST, 'streifen': STREIFEN,
           'teleporter': [{'x': tx, 'y': ty, 'b': b, 'h': hh} for (tx, ty, b, hh) in TELEPORTER]}
    json.dump(lay, open(os.path.join(KARTE, 'layout.json'), 'w'), indent=0)
    F = {'#': (24, 28, 40), '.': (70, 82, 104), 'g': (44, 54, 72), 'p': (110, 124, 150), 'W': (120, 70, 140),
         'r': (200, 40, 40), 'T': (240, 90, 200)}
    S = 6
    im = Image.new('RGB', (C * S, R * S))
    dr = ImageDraw.Draw(im)
    for y in range(R):
        for x in range(C):
            dr.rectangle((x * S, y * S, x * S + S - 1, y * S + S - 1), fill=F[k[y, x]])
    vg = Image.open(VORLAGE).convert('RGB').resize((C * S, R * S))
    both = Image.new('RGB', (C * S * 2 + 8, R * S))
    both.paste(vg, (0, 0)); both.paste(im, (C * S + 8, 0))
    both.save(os.path.join(KARTE, 'layout_vergleich.png'))
    print('Karte 26 Layout %dx%d' % (C, R))


if __name__ == '__main__':
    main()
