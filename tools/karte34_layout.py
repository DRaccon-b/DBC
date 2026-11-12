"""Karte 34 - Shinjuku Central Park (A03 Nr. 1), Layout nach der Vorlage -> maps/karte34/layout.json

  python3 tools/karte34_layout.py

Vorlage assets/vorlagen/karte34_vorlage.png: 1024x896 px = 64x56 Kacheln (1:1). Stadtpark: Wald-/Heckenrand ringsum
mit Heckenbloecken im Park, Rasen, geschwungene Sandwege, gepflasterte Plaetze (Rathausplatz oben rechts, Brunnenplatz
in der Mitte, Platz vor dem Buerohaus links, grosse Plaetze unten links und rechts), Teich mit Erdufer und Holzsteg,
Spielplatz auf Sand unten rechts, drei Ausgaenge (oben rechts, rechts, unten links).

Klassen:  h Wald/Hecke  g Rasen  w Sandweg  s Spielplatz-Sand  p Pflaster  x Wasser  m Ufer (Erde)  b Steg  e Ausgang
Alle Flaechen auf einer Hoehe (Park ohne Klippen).
"""
import json, os
import numpy as np
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte34')
VORLAGE = os.path.join(ROOT, 'assets', 'vorlagen', 'karte34_vorlage.png')
C, R, T = 64, 56, 16
REF = {'g': [(72, 132, 48), (84, 132, 60), (60, 132, 48), (60, 144, 48)],
       'h': [(36, 96, 36), (60, 96, 36), (24, 96, 36), (60, 96, 48), (12, 36, 24), (36, 48, 24)],
       'w': [(192, 168, 108), (180, 156, 108), (180, 168, 108)],
       'p': [(180, 180, 168), (168, 168, 156), (180, 168, 168)],
       'x': [(48, 84, 132), (48, 72, 96)],
       'm': [(132, 108, 84)],
       'b': [(168, 120, 60)]}
AUSGAENGE = [(55, 0, 4, 3), (61, 37, 3, 4), (6, 53, 4, 3)]       # (x, y, b, h) in Kacheln: oben rechts, rechts, unten links
SPIELPLATZ = (42, 43, 53, 49)                                     # Sandflaeche (x0, y0, x1, y1)
STEG = (37, 32, 42, 34)                                           # Holzsteg in den Teich
# Gebaeude und grosse Objekte (Fusszeile bzw. Flaeche bleibt Pflaster/Rasen)
GEBAEUDE = {'rathaus': (42, 11, 51, 21), 'buero': (5, 29, 15, 36), 'pavillon': (13, 14, 16, 17)}


def vorlage_klassen():
    a = np.array(Image.open(VORLAGE).convert('RGB')).astype(int)
    k = np.full((R, C), '?')
    for y in range(R):
        for x in range(C):
            m = np.median(a[y * T:(y + 1) * T, x * T:(x + 1) * T].reshape(-1, 3), 0)
            best, bd = '?', 1e9
            for c, refs in REF.items():
                for r in refs:
                    d = np.abs(m - np.array(r)).sum()
                    if d < bd:
                        best, bd = c, d
            k[y, x] = best if bd < 60 else '?'
    return k


def auffuellen(k):
    """Unbekannte Kacheln (Objekte, Gebaeude) -> haeufigste Nachbarklasse."""
    for _ in range(6):
        for y, x in zip(*np.nonzero(k == '?')):
            nb = [k[yy, xx] for yy in range(max(0, y - 1), min(R, y + 2)) for xx in range(max(0, x - 1), min(C, x + 2))
                  if k[yy, xx] != '?']
            if nb:
                k[y, x] = max(set(nb), key=nb.count)
    k[k == '?'] = 'g'
    return k


def kleine_weg(k, art, mind, ersatz=None):
    import karte04_bauen as k4
    for ys, xs in k4._komponenten(k == art):
        if len(ys) < mind:
            for y, x in zip(ys, xs):
                nb = [k[yy, xx] for yy in range(max(0, y - 1), min(R, y + 2)) for xx in range(max(0, x - 1), min(C, x + 2))
                      if k[yy, xx] != art]
                k[y, x] = ersatz or (max(set(nb), key=nb.count) if nb else 'g')
    return k


def zipfel_weg(k, arten='pws'):
    """Kacheln, die nur ueber eine einzige gleichartige Nachbarkachel (4er-Nachbarschaft) an ihre Flaeche haengen,
    oder in einer Achse eingeklemmt sind (1 Kachel breiter Finger), bekommen die haeufigste Nachbarklasse
    (Pruefliste: keine Ein-Kachel-Zipfel, die das 45-Grad-Raster zu Tropfen rundet)."""
    for _ in range(3):
        neu = k.copy()
        for y in range(1, R - 1):
            for x in range(1, C - 1):
                a = k[y, x]
                if a not in arten:
                    continue
                n4 = [k[y - 1, x], k[y + 1, x], k[y, x - 1], k[y, x + 1]]
                gleich = sum(c == a for c in n4)
                finger = (k[y, x - 1] != a and k[y, x + 1] != a) or (k[y - 1, x] != a and k[y + 1, x] != a)
                if gleich <= 1 or finger:
                    andere = [c for c in n4 if c != a and c != 'b']
                    if andere:
                        neu[y, x] = max(set(andere), key=andere.count)
        k = neu
    return k


def main():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    k = auffuellen(vorlage_klassen())
    # Gebaeude stehen auf Pflaster (Rathaus, Buero) bzw. Rasen (Pavillon) - nicht auf Hecke/Weg
    for name, (x0, y0, x1, y1) in GEBAEUDE.items():
        k[y0:y1 + 1, x0:x1 + 1] = 'g' if name == 'pavillon' else 'p'
    x0, y0, x1, y1 = SPIELPLATZ
    sp = k[y0:y1 + 1, x0:x1 + 1]
    sp[np.isin(sp, ['w', 'g'])] = 's'
    x0, y0, x1, y1 = STEG
    k[y0:y1 + 1, x0:x1 + 1] = 'b'
    k[y0:y1 + 1, x0 - 3:x0] = 'w'                                     # Weg in voller Stegbreite (3 Spalten davor)
    # Ufer: Ring aus Erde um das Wasser (Vorlage), Steg bleibt
    for art, mind in (('x', 3), ('m', 2), ('p', 4), ('w', 3), ('h', 3), ('g', 2), ('s', 3)):
        k = kleine_weg(k, art, mind)
    k = zipfel_weg(k)                                                   # keine 1 Kachel breiten Zipfel/Finger
    k = kleine_weg(k, 'w', 8)                                           # Sand-Inselchen zwischen Plaetzen weg
    w_ = k == 'x'                                                       # Erdufer-Ring um den Teich (Vorlage), nicht auf Platz/Weg
    nb = np.zeros_like(w_)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            nb[max(0, dy):R + min(0, dy), max(0, dx):C + min(0, dx)] |= w_[max(0, -dy):R + min(0, -dy), max(0, -dx):C + min(0, -dx)]
    k[nb & (k == 'g')] = 'm'
    x0, y0, x1, y1 = STEG
    k[y0:y1 + 1, x0:x1 + 1] = 'b'
    k[y0:y1 + 1, x0 - 3:x0] = 'w'
    for (x, y, b, h) in AUSGAENGE:
        k[y:y + h, x:x + b] = 'e'
    # Rand: aussen ringsum Wald (Vorlage), ausser an den Ausgaengen
    rand = np.zeros((R, C), bool); rand[0, :] = rand[-1, :] = True; rand[:, 0] = rand[:, -1] = True
    k[rand & (k != 'e')] = 'h'
    import regeln_a02                                                   # Regel 6: Wege nie nur gerade
    k = regeln_a02.wege_schwingen(k, weg='w', frei='g', seed=34)
    lay = {'groesse': [C, R], 'klassen': [''.join(z) for z in k], 'hoehe': ['1' * C for _ in range(R)],
           'teleporter': [{'x': x, 'y': y, 'b': b, 'h': h} for (x, y, b, h) in AUSGAENGE],
           'spielplatz': list(SPIELPLATZ), 'steg': list(STEG), 'gebaeude_flaechen': GEBAEUDE}
    os.makedirs(KARTE, exist_ok=True)
    json.dump(lay, open(os.path.join(KARTE, 'layout.json'), 'w'), indent=0)
    F = {'h': (30, 80, 30), 'g': (80, 140, 60), 'w': (200, 170, 110), 's': (230, 200, 140), 'p': (180, 180, 170),
         'x': (50, 90, 150), 'm': (130, 100, 70), 'b': (160, 110, 50), 'e': (120, 200, 240)}
    out = np.zeros((R, C, 3), np.uint8)
    for kk, c in F.items():
        out[k == kk] = c
    vor = Image.open(VORLAGE).convert('RGB').resize((C * 8, R * 8))
    bild = Image.new('RGB', (C * 16 + 8, R * 8))
    bild.paste(vor, (0, 0))
    bild.paste(Image.fromarray(out).resize((C * 8, R * 8), 0), (C * 8 + 8, 0))
    bild.save(os.path.join(KARTE, 'layout_vergleich.png'))
    print('Karte 34 Layout %dx%d' % (C, R))


if __name__ == '__main__':
    main()
