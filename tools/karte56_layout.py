"""Karte 56 (Golden Digimentals), Film "Digimon Hurricane Landing!!" Teil 2 -> maps/karte56/layout.json

  python3 tools/karte56_layout.py

Drei Raeume wie Karte 55 (je 28x24 Kacheln, 8 Kacheln Abstand), ringsum ein Baumguertel (Nutzer, wie Karte 35):
  1  Blumenwiese mit See ("Summer Memory") - Kampf gegen Wendigomon / Andiramon. Sommerwiese, Blumenfelder, See
     oben in der Mitte (45-Grad-Ufer). Guertel: Sommerbaeume.
  2  Verzerrte Landschaft - dieselbe Wiese (gleicher See, gleiche Blumenfelder), aber verfaerbt und von Rissen ins
     Nichts durchzogen (45-Grad-Raster). Guertel: verdrehte, zerfallende Baeume.
  3  Cherubimons Inneres - Endkampf. Dunkler Membranboden mit leuchtenden Adern, vier Abgruende, Mitte frei.
     Guertel: dunkle Dornen, Kristalle, Fleischsaeulen.
Karte 112x38 Kacheln: Raeume x 6-33, 42-69, 78-105, Reihen 6-29.

Marken (Raumkoordinaten, wie Karte 55):
  alle:   Aufstellfeld x 1-6, y 18-22 · Ankunft (2 cyan Pfeile) x 1-2, y 23
  1, 2:   Ausgang (2x2 gold) x 25-26, y 14-15
  Ringmarken (Gegner): 1 (15,13) · 2 (15,13) · 3 (14,11)
Klassen:  h/u/k  Guertel (Raum 1/2/3, gesperrt)   m  Wiese   b  Blumenfeld   S  See (gesperrt)
          v  verzerrte Wiese   B  verzerrtes Blumenfeld   D  verzerrter See (gesperrt)   R  Riss (gesperrt)
          i  Membranboden   P  Abgrund (gesperrt)   f z g o  Marken
"""
import json, os
import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte56')
C, R = 112, 38
RAEUME = [(6, 6), (42, 6), (78, 6)]
RW, RH = 28, 24
GRENZEN = [38, 74]                                              # Guertelwechsel zwischen den Raeumen
RINGMARKEN = [[15, 13], [15, 13], [14, 11]]


def see_maske():
    """See oben in der Mitte (Raumkoordinaten), Ufer in Kachelstufen (wird beim Bauen auf 45 Grad gerastert)."""
    m = np.zeros((RH, RW), bool)
    zeilen = {2: (13, 21), 3: (11, 23), 4: (10, 24), 5: (10, 24), 6: (11, 23), 7: (12, 22), 8: (14, 20)}
    for y, (a, b) in zeilen.items():
        m[y, a:b + 1] = True
    return m


def blumen_maske():
    m = np.zeros((RH, RW), bool)
    for (x0, y0, x1, y1) in ((1, 1, 8, 6), (2, 7, 6, 10), (19, 17, 26, 22), (22, 11, 26, 16), (9, 18, 13, 22)):
        m[y0:y1 + 1, x0:x1 + 1] = True
    # 45-Grad-Ecken vorbereiten: Eckkacheln der Rechtecke weg
    for (x, y) in ((1, 1), (8, 1), (8, 6), (26, 22), (19, 17), (22, 11), (13, 18), (9, 22), (6, 10), (2, 10)):
        m[y, x] = False
    return m


def risse():
    """Risse ins Nichts in Raum 2: diagonale Baender (45 Grad), 2 Kacheln breit, nie durch Aufstellfeld/Marken."""
    m = np.zeros((RH, RW), bool)
    for (x0, y0, n, r) in ((3, 2, 6, 1), (17, 8, 5, 1), (14, 17, 5, -1), (23, 18, 4, -1)):
        for i in range(n):
            for d in range(2):
                x, y = x0 + i * r + d, y0 + i
                if 0 < x < RW - 1 and 0 < y < RH - 1:
                    m[y, x] = True
    return m


def abgruende():
    m = np.zeros((RH, RW), bool)
    for (x0, y0, x1, y1) in ((2, 2, 5, 5), (22, 2, 25, 5), (22, 17, 25, 20), (8, 17, 12, 20)):
        m[y0:y1 + 1, x0:x1 + 1] = True
        for (x, y) in ((x0, y0), (x1, y0), (x0, y1), (x1, y1)):
            m[y, x] = False
    return m


def main():
    os.makedirs(KARTE, exist_ok=True)
    k = np.full((R, C), 'h')
    k[:, GRENZEN[0]:] = 'u'
    k[:, GRENZEN[1]:] = 'k'
    see, blumen, riss, abgrund = see_maske(), blumen_maske(), risse(), abgruende()
    for i, (x0, y0) in enumerate(RAEUME):
        sub = k[y0:y0 + RH, x0:x0 + RW]
        if i < 2:
            sub[:] = 'mv'[i]
            sub[blumen] = 'bB'[i]
            sub[see] = 'SD'[i]
            if i == 1:
                sub[riss & ~see] = 'R'
        else:
            sub[:] = 'i'
            sub[abgrund] = 'P'
        sub[18:23, 1:7] = 'f'
        sub[23, 1:3] = 'z'
        mx, my = RINGMARKEN[i]
        sub[my, mx] = 'o'
        if i < 2:
            sub[14:16, 25:27] = 'g'
    gesperrt = list('hukSDRP')
    h = np.where(np.isin(k, gesperrt), 0, 2)
    tp = [{'x': x0 + 1, 'y': y0 + 23, 'b': 2, 'h': 1, 'art': 'ankunft'} for (x0, y0) in RAEUME]
    tp += [{'x': x0 + 25, 'y': y0 + 14, 'b': 2, 'h': 2, 'art': 'ausgang'} for (x0, y0) in RAEUME[:2]]
    lay = {'groesse': [C, R], 'klassen': [''.join(z) for z in k], 'hoehe': [''.join(str(c) for c in z) for z in h],
           'raeume': RAEUME, 'raum': [RW, RH], 'grenzen': GRENZEN, 'ringmarken': RINGMARKEN, 'teleporter': tp}
    json.dump(lay, open(os.path.join(KARTE, 'layout.json'), 'w'), indent=0)
    F = {'h': (40, 96, 40), 'u': (70, 50, 90), 'k': (30, 16, 36), 'm': (110, 180, 80), 'b': (230, 220, 120),
         'S': (60, 130, 200), 'v': (130, 110, 150), 'B': (170, 130, 170), 'D': (60, 30, 90), 'R': (10, 0, 20),
         'i': (80, 40, 90), 'P': (0, 0, 0), 'f': (70, 100, 130), 'z': (60, 200, 230), 'g': (230, 180, 70),
         'o': (240, 60, 60)}
    S = 8
    im = Image.new('RGB', (C * S, R * S))
    dr = ImageDraw.Draw(im)
    for y in range(R):
        for x in range(C):
            dr.rectangle((x * S, y * S, x * S + S - 1, y * S + S - 1), fill=F[k[y, x]], outline=(0, 0, 0))
    im.save(os.path.join(KARTE, 'layout_vorschau.png'))
    print('Karte 56 Layout %dx%d, begehbar %d Kacheln' % (C, R, int((~np.isin(k, gesperrt)).sum())))


if __name__ == '__main__':
    main()
