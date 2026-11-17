"""Karte 52 - D-Reaper: Shinjuku (A03 Nr. 19), Layout nach der Vorlage -> maps/karte52/layout.json

  python3 tools/karte52_layout.py

Vorlage assets/vorlagen/karte52_vorlage.png: 1536x1280 px = 96x80 Kacheln (1:1). Shinjuku unter der D-Reaper-Masse:
dunkler, aufgerissener Asphalt, Gehwegstreifen um die Bloecke, zwei helle Plattenplaetze, ein Ziegelplatz unten rechts,
sechs Buerogebaeude, grosse rote Masseflaechen. Statt Baumguertel umschliesst die Masse selbst die Stadt (Nutzer K35:
Karte endet nie im Nichts - hier wuchert der D-Reaper ringsum, unregelmaessige Kante am 45-Grad-Raster); vier Ausgaenge
(zwei oben, zwei rechts) fuehren als Gehweg durch die Masse zum Teleporter am Rand.
Korrekturen der Vorlage: Gebaeude rechts steht ganz auf dem Gehwegring (nicht ueber dem Rand), Gehwegreihe vor dem
unteren Gebaeude, Einzelkacheln/Zipfel der Masse geglaettet, Teleporter mittig in ihrem Weg.

Klassen:  a Asphalt  k Gehweg (Ziegelstreifen)  q Plattenplatz  b Ziegelplatz  r D-Reaper-Masse (gesperrt)
          h Masse am Kartenrand (gesperrt)  e Teleporter
"""
import json, os
import numpy as np
from PIL import Image
import karte43_layout as k43

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte52')
VORLAGE = os.path.join(ROOT, 'assets', 'vorlagen', 'karte52_vorlage.png')
C, R, T = 96, 80, 16
RAND = 2
REF = {'a': (48, 60, 74), 'd': (62, 60, 74), 'k': (168, 168, 168), 'q': (150, 158, 158), 'b': (170, 156, 132),
       'r': (100, 38, 52), 'R': (112, 38, 62)}
PLATZ = [(43, 10, 50, 35), (46, 7, 47, 9), (8, 47, 48, 61), (13, 62, 19, 63)]      # helle Plattenplaetze
ZIEGEL = (74, 58, 92, 75)
GEBAEUDE = {'oben_links': (3, 3, 16, 11), 'beige_links': (3, 36, 12, 44), 'glas_mitte': (23, 36, 44, 44),
            'glas_rechts': (84, 18, 93, 28), 'beige_rechts': (66, 46, 75, 54), 'lila_unten': (24, 67, 45, 75)}
# Teleporter (Vorlage): oben x 44-47 und 88-91, rechts y 12-15 und 68-71
AUSGAENGE = [('o', 44, 4), ('o', 88, 4), ('r', 12, 4), ('r', 68, 4)]


def main():
    a = np.array(Image.open(VORLAGE).convert('RGB')).astype(int)
    M = np.median(a.reshape(R, T, C, T, 3).transpose(0, 2, 1, 3, 4).reshape(R, C, T * T, 3), 2)
    ks = list(REF)
    ref = np.array([REF[c] for c in ks], float)
    d = ((M[:, :, None, :] - ref[None, None]) ** 2).sum(-1)
    k = np.array(ks)[d.argmin(-1)].astype('<U1')
    k[d.min(-1) > 500] = 'B'
    k[k == 'R'] = 'r'
    k[k == 'd'] = 'a'
    k[np.isin(k, ['q', 'B'])] = 'k'                                    # Streifen, Gebaeudeflaechen: Gehweg
    k[k == 'b'] = 'k'
    for (x0, y0, x1, y1) in PLATZ:
        k[y0:y1 + 1, x0:x1 + 1] = np.where(k[y0:y1 + 1, x0:x1 + 1] == 'r', 'r', 'q')
    x0, y0, x1, y1 = ZIEGEL
    k[y0:y1 + 1, x0:x1 + 1] = 'b'
    k[2, 2:94] = 'k'; k[77, 2:94] = 'k'; k[2:78, 2] = 'k'; k[2:78, 93] = 'k'   # Gehwegring
    for n_, (x0, y0, x1, y1) in GEBAEUDE.items():
        k[y0:y1 + 1, x0:x1 + 1] = 'k'
    k[76, 23:47] = 'k'                                                 # Gehwegreihe vor dem unteren Gebaeude
    k[29, 84:94] = 'k'                                                 # vor dem Gebaeude rechts
    k[12, 3:17] = 'k'; k[55, 66:76] = 'k'                              # vor den Gebaeuden oben links / Mitte rechts
    k[45, 2:46] = np.where(k[45, 2:46] == 'a', 'k', k[45, 2:46])       # vor den beiden mittleren Gebaeuden
    k[0:2, :] = 'h'; k[78:, :] = 'h'; k[:, 0:2] = 'h'; k[:, 94:] = 'h'
    k = k43.zipfel_weg(k, 'r')
    for _ in range(2):                                                 # Gehweg-/Platzinseln, die die Masse fast umschliesst
        for y in range(1, R - 1):
            for x in range(1, C - 1):
                if k[y, x] not in 'rh' and sum(k[y + dy, x + dx] == 'r' for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1))) >= 3:
                    k[y, x] = 'r'
    for teil in k43.flaechen(k == 'r'):                                 # winzige Masseflecken weg
        if len(teil) < 6:
            for (y, x) in teil:
                k[y, x] = 'a'
    for _ in range(2):                                                 # Schachbrett-Ecken
        for y in range(R - 1):
            for x in range(C - 1):
                q = k[y:y + 2, x:x + 2]
                if q[0, 0] == q[1, 1] and q[0, 1] == q[1, 0] and q[0, 0] != q[0, 1]:
                    k[y + 1, x] = q[0, 0]
    for _ in range(3):                                                 # letzte Glaettung: Massezipfel und Asphalttaschen
        for y in range(2, R - 2):
            for x in range(2, C - 2):
                nb = [k[y + dy, x + dx] for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1))]
                if k[y, x] == 'r' and nb.count('r') <= 1:
                    andere = [c for c in nb if c != 'r']
                    k[y, x] = max(set(andere), key=andere.count)
                elif k[y, x] == 'a' and nb.count('a') <= 1 and nb.count('r') >= 2:
                    k[y, x] = 'r'
    for n_, (x0, y0, x1, y1) in GEBAEUDE.items():                     # Gebaeudeflaechen + Gehwegring (Seiten 1, hinten 2 Reihen)
        k[max(2, y0 - 2):min(R - 2, y1 + 2), max(2, x0 - 1):min(C - 2, x1 + 2)] = 'k'
    P = RAND
    C2, R2 = C + 2 * P, R + 2 * P
    k2 = np.full((R2, C2), 'h')
    k2[P:P + R, P:P + C] = k
    # unregelmaessige Massekante: Randstreifen (2 Kacheln) wird stellenweise Asphalt (Masse weicht zurueck)
    rs = np.random.RandomState(52)
    for seite in range(4):
        n = C2 if seite < 2 else R2
        tiefe, i = [], 0                                               # Laeufe von 3-8 Kacheln, Stufen je 1
        t_alt = 1
        while len(tiefe) < n:
            t_alt = int(np.clip(t_alt + rs.choice([-1, 0, 1]), 0, 2))
            tiefe += [t_alt] * rs.randint(3, 9)
        for i in range(P + 2, n - P - 2):
            for t_ in range(tiefe[i]):
                if seite == 0:
                    y, x = P + 1 - t_, i
                elif seite == 1:
                    y, x = R2 - P - 2 + t_, i
                elif seite == 2:
                    y, x = i, P + 1 - t_
                else:
                    y, x = i, C2 - P - 2 + t_
                if 0 <= y < R2 and 0 <= x < C2 and k2[y, x] == 'h':
                    innen = (seite == 0 and y >= P) or (seite == 1 and y < R2 - P) or (seite == 2 and x >= P) or \
                            (seite == 3 and x < C2 - P)
                    if innen:
                        k2[y, x] = 'a'
    tps = []
    for (seite, s0, b) in AUSGAENGE:
        if seite == 'o':
            x0_ = s0 + P
            k2[0:P + 2, x0_ - 1:x0_ + b + 1] = 'k'
            tps.append((x0_, 0, b, 3))
        else:
            y0_ = s0 + P
            k2[y0_ - 1:y0_ + b + 1, C2 - P - 2:] = 'k'
            tps.append((C2 - 3, y0_, 3, b))
    for (x, y, b, h) in tps:
        k2[y:y + h, x:x + b] = 'e'
    k43.R, k43.C = R2, C2
    for _ in range(2):                                                 # Zipfel im Rand nach den Ausgaengen
        for y in range(1, R2 - 1):
            for x in range(1, C2 - 1):
                if k2[y, x] == 'a' and sum(k2[y + dy, x + dx] == 'a' for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1))) <= 1 \
                        and sum(k2[y + dy, x + dx] in 'kqb' for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1))) == 0:
                    k2[y, x] = 'h'
    lay = {'groesse': [C2, R2], 'klassen': [''.join(z) for z in k2], 'hoehe': ['1' * C2 for _ in range(R2)],
           'versatz': P, 'teleporter': [{'x': x, 'y': y, 'b': b, 'h': h} for (x, y, b, h) in tps],
           'zebra': [], 'strassen_h': [], 'strassen_v': [],
           'gebaeude_flaechen': {n: [v[0] + P, v[1] + P, v[2] + P, v[3] + P] for n, v in GEBAEUDE.items()},
           'stadt': [P, P, P + C - 1, P + R - 1]}
    os.makedirs(KARTE, exist_ok=True)
    json.dump(lay, open(os.path.join(KARTE, 'layout.json'), 'w'), indent=0)
    F = {'a': (50, 56, 70), 'k': (150, 156, 160), 'q': (196, 196, 186), 'b': (180, 160, 130), 'h': (90, 20, 40),
         'e': (120, 220, 255), 'r': (150, 30, 50)}
    out = np.zeros((R2, C2, 3), np.uint8)
    for kk, c in F.items():
        out[k2 == kk] = c
    for n_, (x0, y0, x1, y1) in GEBAEUDE.items():
        out[y0 + P:y1 + P + 1, x0 + P:x1 + P + 1] = (out[y0 + P:y1 + P + 1, x0 + P:x1 + P + 1] * 0.6).astype(np.uint8)
    vor = Image.open(VORLAGE).convert('RGB').resize((C * 8, R * 8))
    bild = Image.new('RGB', (C2 * 16 + 8, R2 * 8))
    bild.paste(vor, (P * 8, P * 8))
    bild.paste(Image.fromarray(out).resize((C2 * 8, R2 * 8), 0), (C2 * 8 + 8, 0))
    bild.save(os.path.join(KARTE, 'layout_vergleich.png'))
    print('Karte 52 Layout %dx%d' % (C2, R2))


if __name__ == '__main__':
    main()
