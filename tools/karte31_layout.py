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
    [4, 37, 36, 49, 'block1'], [44, 37, 49, 72, 'turm12'], [67, 37, 110, 49, 'block2'], [113, 37, 118, 79, 'turm5'],
    [77, 67, 109, 79, 'block3'], [8, 75, 27, 83, 'bahnhof'], [71, 86, 117, 92, 'laeden']]
MAUER = (30, 32)                          # Stuetzmauer Park -> Siedlung (Front-Reihen)
MAUER_TREPPEN = [(10, 15), (56, 64), (98, 103)]
TERRASSE = (86, 0, 119, 18)               # Portal-Terrasse (Ebene 3), Front Reihen 19-20
TERRASSE_FRONT = (19, 20)
TERRASSE_TREPPE = (95, 98)
HOCHBAHN = {'x0': 0, 'x1': 27, 'y0': 72, 'y1': 75, 'zug': [1, 18], 'pfeiler': [3]}


WEGE = [  # (Stuetzpunkte in Kacheln, halbe Breite) -> Catmull-Rom-Kurven
    ([(13.5, 25.5), (12, 21), (14, 16.5), (12.8, 11), (15, 7.2), (22, 6.4), (31, 7)], 1.45),     # links hoch zum Pavillon
    ([(36, 7.5), (38.5, 9.5), (38, 13)], 1.2),                                                 # Pavillon -> Hauptweg
    ([(12.5, 13), (20, 14.2), (28, 13), (36, 12.6), (44, 14.3), (50, 13.6), (56, 13.2)], 1.5),   # Hauptweg -> Uhrplatz
    ([(65, 13), (71, 12.2), (77, 14), (82, 13.2), (84, 16), (82.6, 20.5), (84.5, 25.5)], 1.45),   # Uhrplatz -> Osten -> Promenade
    ([(60.5, 16.5), (59.2, 20), (61.5, 23), (60.5, 25.8)], 2.2),                               # Uhrplatz -> Treppe Mitte
    ([(77, 13.5), (77.5, 15.6)], 0.9),                                                          # Kiosk
]
WEGE_TERRASSE = [
    ([(103, 15.5), (100.5, 17), (97, 18.6)], 1.6),                                            # Portalplatz -> Terrassentreppe
    ([(96.5, 21), (98.5, 23), (100.5, 25.8)], 1.6),                                           # Terrassentreppe -> Promenadentreppe
]


def _kurve(pts, n=24):
    p = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for i in range(1, len(p) - 2):
        p0, p1, p2, p3 = (np.array(q, float) for q in p[i - 1:i + 3])
        for t in np.linspace(0, 1, n, endpoint=False):
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(np.array(pts[-1], float))
    return np.array(out)


def _weg(k, pts, r, erlaubt):
    c = _kurve(pts)
    yy, xx = np.mgrid[0:R, 0:C]
    cx, cy = xx + 0.5, yy + 0.5
    d = np.min([(cx - px) ** 2 + (cy - py) ** 2 for px, py in c], axis=0)
    m = (d <= r * r) & erlaubt & np.isin(k, ['n', 'h', 'w'])
    k[m] = 'w'


def r_(k, x0, y0, x1, y1, art):
    k[y0:y1 + 1, x0:x1 + 1] = art


def _laeufe(zeile, c):
    out, x = [], 0
    while x < len(zeile):
        if zeile[x] == c:
            x0 = x
            while x < len(zeile) and zeile[x] == c:
                x += 1
            out.append((x0, x - 1))
        else:
            x += 1
    return out


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
    from collections import deque                                    # kleine Asphalt-Inseln (Baumstaemme/Schatten der
    gesehen = np.zeros((R, C), bool)                                 # Vorlage) -> Umgebung
    for y in range(R):
        for x in range(C):
            if k[y, x] == 's' and not gesehen[y, x]:
                comp, q = [], deque([(y, x)]); gesehen[y, x] = True
                while q:
                    cy, cx = q.popleft(); comp.append((cy, cx))
                    for yy, xx in ((cy - 1, cx), (cy + 1, cx), (cy, cx - 1), (cy, cx + 1)):
                        if 0 <= yy < R and 0 <= xx < C and k[yy, xx] == 's' and not gesehen[yy, xx]:
                            gesehen[yy, xx] = True; q.append((yy, xx))
                if len(comp) < 12:
                    for cy, cx in comp:
                        nb = [k[yy, xx] for yy, xx in ((cy - 1, cx), (cy + 1, cx), (cy, cx - 1), (cy, cx + 1))
                              if 0 <= yy < R and 0 <= xx < C and k[yy, xx] != 's']
                        k[cy, cx] = Counter(nb).most_common(1)[0][0] if nb else 'g'
    for y in list(range(2, 25)) + [100, 101]:                        # Baumstaemme als 'Hecke' erkannt -> Rasen
        for x in range(C):
            if k[y, x] == 'h':
                k[y, x] = 'n'
    r_(k, 2, 99, 119, 99, 'g')
    # ---- Park oben: Rasen, Hecken nur am oberen Rand und als Beete an der Promenade
    r_(k, 0, 0, 85, 1, 'h')
    r_(k, 86, 0, 119, 1, 'n')
    r_(k, 0, 26, 119, 29, 'g')                                       # Promenade auf der Mauer
    hecken = [(x0, x1) for (x0, x1) in _laeufe(k[25], 'h')]           # Heckenbeete -> Rasen, Hecken als Objekte
    k[25][k[25] == 'h'] = 'n'
    k[7, 102:106] = 'g'                                               # Portalplatz: Luecke vom alten Tor schliessen
    # ---- Parkwege natuerlich (Regel 6: nie nur gerade, Boegen/Diagonalen): Vorlagen-Rechteckwege -> Kurven
    park = np.zeros((R, C), bool); park[2:26, 2:118] = True
    park[TERRASSE[1]:TERRASSE[3] + 1, TERRASSE[0]:TERRASSE[2] + 1] &= False
    k[park & (k == 'w')] = 'n'
    terr = np.zeros((R, C), bool); terr[2:19, TERRASSE[0] + 1:118] = True
    k[terr & (k == 'w')] = 'n'
    for pts, r in WEGE + WEGE_TERRASSE:
        _weg(k, pts, r, np.arange(R)[:, None] < 26)
    # ---- Stuetzmauer und Treppen
    r_(k, 0, MAUER[0], 119, MAUER[1], 'W')
    for (x0, x1) in MAUER_TREPPEN:
        r_(k, x0, MAUER[0], x1, MAUER[1], 'T')
    r_(k, TERRASSE[0], TERRASSE_FRONT[0], TERRASSE[2], TERRASSE_FRONT[1], 'W')
    r_(k, TERRASSE_TREPPE[0], TERRASSE_FRONT[0], TERRASSE_TREPPE[1], TERRASSE_FRONT[1], 'T')
    # ---- Siedlung: Heckenrand links/unten, Strassen
    r_(k, 0, 33, 1, 92, 'n')
    r_(k, 57, 36, 63, 92, 's')                                       # Querstrasse (unter der Fussgaengerbruecke)
    r_(k, 66, 81, 119, 84, 's')                                      # Strasse rechts
    r_(k, 2, 94, 119, 98, 's')                                       # Strasse unten
    # ---- Bahnhof: Vorplatz mit Leitstreifen, Hochbahn links
    r_(k, 0, 74, 27, 92, 'g')
    r_(k, 2, 84, 7, 85, 'g')
    r_(k, 8, 84, 27, 84, 'y'); r_(k, 18, 84, 18, 91, 'y')            # Leitstreifen (Vorlage: gelbe Linie zum Bahnhof)
    r_(k, 2, 92, 27, 92, 'y')
    # ---- Baumrand am Kartenrand (Nutzer: Baeume statt Hecken): oben 2 Reihen, links/rechts 2 Spalten, unten 3 Reihen
    r_(k, 0, 0, 119, 1, 'f')
    for y in range(R):
        for x in (0, 1, 118, 119):
            if 26 <= y <= 35 or k[y, x] in 'sWT':                     # Promenade, Mauer, Strassen bleiben frei
                continue
            if k[y, x] in 'nhfeg' and not (72 <= y <= 92 and x <= 1):   # (links unten: Bahnhofsvorplatz frei)
                k[y, x] = 'f'
    r_(k, 0, 101, 119, 103, 'f')
    k[k == 'h'] = 'h'
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
           'hecken': hecken,
           'parkwege': [[[list(map(float, q)) for q in _kurve(pts).tolist()], r] for pts, r in WEGE + WEGE_TERRASSE],
           'teleporter': [{'x': 102, 'y': 11, 'b': 4, 'h': 3, 'farbe': 'violett'}]}
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
