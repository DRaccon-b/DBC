"""Karte 08 (Overdell): Kachelraster aus der Vorlage -> maps/karte08/layout.json

  python3 tools/karte08_layout.py

Vorlage assets/vorlagen/karte08_vorlage.png (1600x1440 = 100x90 Kacheln a 16 px).
Klassen:  g Gras (dunkel, gedeckt)  h dunkles Gras  w Steinweg  e Graberde  q Kopfsteinplatz  m Schlamm
          x Sumpfwasser  f Terrassenboden  a ausgetretener Terrassenboden  k Schlossplatz  r Geroellfeld
Hoehen:   1 Friedhof, 2-5 Terrassen (unten -> oben), 6 Schlossplateau, 7 schwarzer Fels / Geroell ringsum.
Treppen wechseln von Terrasse zu Terrasse zwischen links und rechts (wie in der Vorlage).
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageFilter

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte08')
T = 16
C, R = 100, 90
ZENTREN = {'g': (84, 96, 72), 'r': (36, 36, 60), 'p': (84, 96, 108), 'c': (48, 48, 60), 't': (120, 120, 120),
           'v': (24, 24, 36), 'G': (60, 60, 48), 'u': (108, 120, 120), 'q': (60, 72, 84), 'd': (84, 72, 60),
           's': (36, 60, 48), 'k': (84, 84, 96), 'o': (132, 72, 36)}


def vorlage_klassen():
    im = np.array(Image.open(os.path.join(ROOT, 'assets', 'vorlagen', 'karte08_vorlage.png')).convert('RGB')).astype(float)
    med = np.zeros((R, C, 3))
    for y in range(R):
        for x in range(C):
            med[y, x] = np.median(im[y * T:(y + 1) * T, x * T:(x + 1) * T].reshape(-1, 3), axis=0)
    ks = list(ZENTREN)
    cen = np.array([ZENTREN[k] for k in ks], float)
    return np.array(ks)[((med[:, :, None] - cen[None, None]) ** 2).sum(-1).argmin(-1)]


def glaetten(m, n=1):
    k = Image.fromarray((m * 255).astype(np.uint8))
    for _ in range(n):
        k = k.filter(ImageFilter.ModeFilter(3))
    return np.array(k) > 127


def main():
    v = vorlage_klassen()
    yy, xx = np.mgrid[0:R, 0:C]
    h = np.ones((R, C), int)
    # ------------------------------------------------------------ Berg in der Mitte: Terrassen
    # (Ebene, x0, x1, y0, y1) - jede Terrasse reicht nach Norden unter die Front der naechsthoeheren
    TERR = [(2, 30, 78, 44, 56), (3, 30, 78, 36, 43), (4, 30, 78, 28, 35), (5, 30, 78, 20, 27), (6, 30, 79, 5, 19)]
    for (e, x0, x1, y0, y1) in TERR:
        h[y0:y1 + 1, x0:x1 + 1] = e
    # Schlossplateau: Nordrand unregelmaessig wie in der Vorlage (Mitte hinter dem Schloss bis Zeile 3)
    h[3:5, 47:63] = 6
    h[5:8, 31:35] = 7
    h[5:9, 72:80] = 7
    # rechter Friedhof auf dem Berg (Ebene 3, an Terrasse 3 angeschlossen), Nordrand schraeg
    for y in range(31, 44):
        x0 = 76 if y >= 36 else 88 - 2 * (y - 31)
        h[y, max(79, x0):95] = 3
    h[36:44, 79:80] = 3
    # ------------------------------------------------------------ schwarzer Fels (7) ringsum
    fels = np.zeros((R, C), bool)
    fels[0:3, :] = True
    fels[3:5, :] = True
    fels[3:5, 47:63] = False
    fels[5:7, 0:31] = True
    fels[5:7, 80:] = True
    fels[0:31, 79:] = True                                         # Geroellfeld rechts oben
    fels[31:36, 80:] |= h[31:36, 80:] < 3
    fels[36:52, 79:] |= h[36:52, 79:] < 3
    fels[44:52, 79:96] = True
    fels[5:58, 26:30] = True                                       # Felsgrat zwischen Friedhof links und Berg
    fels[:, 0:2] = True
    fels[52:, 96:] = True
    fels[86:, :] = True
    fels[86:, 9:13] = False                                        # Ausgang unten links (Teleporter)
    fels |= (v == 'v')                                             # schwarze Felsnasen und Loch links
    fels[(yy >= 7) & (yy < 86) & (xx >= 2) & (xx < 26)] &= (v == 'v')[(yy >= 7) & (yy < 86) & (xx >= 2) & (xx < 26)]
    fels[52:86, 30:96] &= (v == 'v')[52:86, 30:96]
    fels[58:86, 2:30] &= (v == 'v')[58:86, 2:30]
    fels = glaetten(fels)
    fels[0:3, :] = True
    fels[:, 0:2] = True
    fels[86:, :] = True
    fels[86:, 9:13] = False
    fels[52:, 96:] = True
    berg = h >= 2
    fels &= ~berg | (h == 7)
    h[fels] = 7
    # ------------------------------------------------------------ Klassen
    k = np.full((R, C), 'g')
    boden = h == 1
    links = boden & (xx < 26) & (yy < 60)
    k[links & np.isin(v, ['d', 'G'])] = 'h'
    k[boden & (v == 't')] = 'w'
    # Graeberfelder (braune Reihen) unten in der Mitte
    k[boden & (v == 'd') & (yy >= 60) & (xx < 64)] = 'e'
    # Sumpf, Schlamm, Bruecke
    sumpf = boden & (xx >= 64) & (xx <= 92) & (yy >= 64) & (yy <= 82)
    k[sumpf & (v == 's')] = 'x'
    k[sumpf & (v == 'o')] = 'x'
    k[sumpf & (v == 'd')] = 'm'
    # Plaetze: unten links (Lagerplatz), Ruinen rechts, vor dem Mausoleum
    platz = ((xx - 9.5) / 8.5) ** 2 + ((yy - 80) / 7.5) ** 2 <= 1
    k[boden & platz] = 'q'
    k[boden & (xx >= 78) & (yy >= 57) & (yy <= 66) & np.isin(v, ['q', 'k', 'p'])] = 'q'
    k[(xx >= 48) & (xx <= 60) & (yy >= 68) & (yy <= 69)] = 'q'
    # Terrassen: Grundboden f, ausgetretene Flaechen a
    k[berg & (h <= 6)] = 'f'
    k[berg & (h <= 6) & np.isin(v, ['t', 'u'])] = 'a'
    k[(xx >= 47) & (xx <= 63) & (yy >= 4) & (yy <= 16)] = 'k'      # Schlossplatz
    k[h == 7] = 'r'
    # Aufraeumen: kleine Splitter
    for art in 'whea':
        m = k == art
        mm = glaetten(m)
        k[m & ~mm] = 'g' if art in 'whe' else 'f'
        k[mm & ~m & ((k == 'g') if art in 'whe' else (k == 'f'))] = art
    # Wege ergaenzen: Treppenanschluesse, Weg rechts unten zum Teleporter, Ausgang unten links
    k[59:64, 39:43] = 'w'
    k[82:86, 74:98] = 'w'
    k[80:90, 9:13] = 'w'
    k[(h == 1) & (xx >= 96)] = 'r'
    lay = {
        'groesse': [C, R], 'klassen': [''.join(r) for r in k], 'hoehe': [''.join(str(c) for c in r) for r in h],
        # Treppen (x0, x1, Ebene oben): abwechselnd links / rechts
        'treppen': [[52, 55, 6], [37, 40, 5], [70, 73, 4], [35, 38, 3], [39, 42, 2]],
        'bruecken': [[71, 72, 87, 74]],                                  # (x0, y0, x1, y1) ueber den Sumpf
        'teleporter': [{'x': 98, 'y': 82, 'b': 2, 'h': 4}, {'x': 9, 'y': 88, 'b': 4, 'h': 2}],
    }
    os.makedirs(KARTE, exist_ok=True)
    json.dump(lay, open(os.path.join(KARTE, 'layout.json'), 'w'), indent=0)
    F = {'g': (80, 92, 64), 'h': (52, 60, 42), 'w': (140, 140, 150), 'e': (100, 72, 52), 'q': (90, 100, 130),
         'm': (60, 50, 36), 'x': (30, 70, 60), 'f': (96, 104, 120), 'a': (150, 152, 160), 'k': (70, 60, 90),
         'r': (30, 30, 46)}
    out = np.zeros((R, C, 3), np.uint8)
    for kk, c in F.items():
        out[k == kk] = c
    for e in range(2, 7):                                            # Ebenen leicht aufhellen
        out[(h == e) & (k != 'k')] = np.clip(out[(h == e) & (k != 'k')].astype(int) + (e - 2) * 12, 0, 255)
    vor = Image.open(os.path.join(ROOT, 'assets', 'vorlagen', 'karte08_vorlage.png')).convert('RGB').resize((C * 8, R * 8))
    bild = Image.new('RGB', (C * 16 + 8, R * 8))
    bild.paste(vor, (0, 0))
    bild.paste(Image.fromarray(out).resize((C * 8, R * 8), 0), (C * 8 + 8, 0))
    bild.save(os.path.join(KARTE, 'layout_vergleich.png'))
    print('Karte 08 Layout %dx%d' % (C, R))


if __name__ == '__main__':
    main()
