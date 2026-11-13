"""Karte 39 - West Shinjuku Siege (A03 Nr. 6), Layout nach der Vorlage -> maps/karte39/layout.json

  python3 tools/karte39_layout.py

Vorlage assets/vorlagen/karte39_vorlage.png: 1536x1280 px = 96x80 Kacheln (1:1). West-Shinjuku: grosser Platz mit dem
Zwillingsturm-Rathaus und zwei U-Bahn-Eingaengen, Fussgaengerbruecke ueber die linke Hauptstrasse, Ziegelplatz oben links,
Gruenflaechen mit Baeumen, fuenf Buerogebaeude, Hochhaus rechts; Strassenkreuzung mit Zebrastreifen. Der dunkle Rand der
Vorlage wird zum Baumguertel (Nutzer), die Karte ringsum um RAND Kacheln erweitert; drei Ausgaenge (rechts oben, rechts
Mitte, unten) laufen als Fahrbahn bis zu den Teleportern am neuen Rand, die anderen Strassenenden enden mit Bordstein.

Klassen:  a Fahrbahn  g Gehweg  k dunkler Gehwegstreifen  q Platzpflaster  b Ziegelplatz  n Rasen
          h Baumguertel (gesperrt)  e Ausgang (Teleporter)
Alle Koordinaten unten sind Vorlagenkacheln; im Layout + RAND.
"""
import json, os, sys
import numpy as np
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte39')
VORLAGE = os.path.join(ROOT, 'assets', 'vorlagen', 'karte39_vorlage.png')
C, R, T = 96, 80, 16
RAND = 4
STADT = (2, 2, 93, 77)
REF = {'a': (52, 61, 73), 'g': (168, 178, 177), 'q': (180, 180, 172), 'k': (148, 158, 162), 'b': (176, 163, 137),
       'n': (87, 142, 61)}
# Strassenbaender: waagerecht (y0, y1, x0, x1), senkrecht (x0, x1, y0, y1)
STRASSEN_H = [(46, 54, 0, 95), (12, 18, 73, 95)]
STRASSEN_V = [(24, 33, 0, 79), (73, 80, 12, 45)]
# Zebrastreifen (x0, x1, y0, y1, art): 'h' quer ueber eine Nord-Sued-Strasse, 'v' quer ueber eine Ost-West-Strasse
ZEBRA = [(24, 33, 21, 21, 'h'), (24, 33, 56, 56, 'h'), (73, 80, 39, 39, 'h'),
         (22, 22, 46, 54, 'v'), (35, 35, 46, 54, 'v'), (82, 82, 46, 54, 'v'), (82, 82, 12, 18, 'v')]
# Ausgaenge mit Teleporter am neuen Rand: (Strassenband, Seite)
AUSGAENGE = [('h', 1, 'rechts'), ('h', 0, 'rechts'), ('v', 0, 'unten')]
# Gebaeude: Name -> (x0, y0, x1, y1) Grundflaeche in Vorlagenkacheln (Fusszeile = y1), stehen auf Gehweg
GEBAEUDE = {'buero_oben': (72, 4, 89, 11), 'buero_links': (5, 23, 18, 29), 'turm': (83, 19, 93, 45),
            'buero_unten_links': (5, 65, 22, 75), 'buero_unten': (36, 70, 57, 77)}
RATHAUS = (42, 8, 56, 23)                                         # helle Flaeche unter dem Rathaus (Gehwegplatten)


def main():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import karte34_layout as l34
    l34.R, l34.C = R, C
    a = np.array(Image.open(VORLAGE).convert('RGB')).astype(int)
    med = np.zeros((R, C, 3), int)
    for y in range(R):
        for x in range(C):
            med[y, x] = np.median(a[y * T:(y + 1) * T, x * T:(x + 1) * T].reshape(-1, 3), 0)
    ks = list(REF)
    ref = np.array([REF[k] for k in ks])
    d = ((med[:, :, None, :] - ref[None, None]) ** 2).sum(-1)
    k = np.array(ks)[d.argmin(-1)]
    k[d.min(-1) > 700] = '?'
    band = np.zeros((R, C), bool)                                  # Fahrbahn nur in den Strassenbaendern (Pruefliste K36)
    for (y0, y1, x0, x1) in STRASSEN_H:
        band[y0:y1 + 1, x0:x1 + 1] = True
    for (x0, x1, y0, y1) in STRASSEN_V:
        band[y0:y1 + 1, x0:x1 + 1] = True
    k[band] = 'a'
    k[(k == 'a') & ~band] = '?'
    for (x0, y0, x1, y1) in GEBAEUDE.values():                    # Gebaeude stehen auf Gehweg
        k[y0:y1 + 1, x0:x1 + 1] = 'g'
    x0, y0, x1, y1 = RATHAUS
    k[y0:y1 + 1, x0:x1 + 1] = 'g'
    for _ in range(8):                                             # Objekte der Vorlage: Boden der Nachbarn
        for y, x in zip(*np.nonzero(k == '?')):
            nb = [k[yy, xx] for yy, xx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1))
                  if 0 <= yy < R and 0 <= xx < C and k[yy, xx] != '?']
            if nb:
                k[y, x] = max(set(nb), key=nb.count)
    k[2, 24:34] = 'k'                                              # Nordende der Hauptstrasse: Gehweg/Bordstein (kein Ausgang)
    k[(k == 'a') & ~band] = 'k'                                    # nie Fahrbahn ausserhalb der Baender (Bruecke)
    for art in 'bnq':                                              # Einzelkacheln angleichen
        k = l34.kleine_weg(k, art, 6)
    k = l34.kleine_weg(k, 'k', 14)                                 # Flecken unter Objekten der Vorlage
    for y in range(1, R - 1):                                      # 1-Kachel-Kerben (k mit q an drei Seiten)
        for x in range(1, C - 1):
            nb = [k[y - 1, x], k[y + 1, x], k[y, x - 1], k[y, x + 1]]
            if k[y, x] == 'k' and nb.count('q') >= 3:
                k[y, x] = 'q'
    k = l34.kleine_weg(k, 'g', 16)                                 # Brueckenpfeiler/Schatten der Vorlage
    k[30:42, 10:14][k[30:42, 10:14] == 'n'] = 'g'                  # Weg vom Eingang buero_links durch den Rasen
    k[40:42, 15:18][k[40:42, 15:18] == 'n'] = 'k'                  # Rasenzunge unter dem Brueckenfuss
    x0, y0, x1, y1 = STADT
    stadt = np.zeros((R, C), bool); stadt[y0:y1 + 1, x0:x1 + 1] = True
    k[~stadt] = 'h'
    P = RAND
    C2, R2 = C + 2 * P, R + 2 * P
    k2 = np.full((R2, C2), 'h')
    k2[P:P + R, P:P + C] = k
    tps = []
    for (art, i, seite) in AUSGAENGE:                              # Ausgaenge: Fahrbahn bis an den neuen Rand
        if art == 'h':
            y0_, y1_ = STRASSEN_H[i][0] + P, STRASSEN_H[i][1] + P
            k2[y0_:y1_ + 1, STADT[2] + P + 1:] = 'a'
            m = (y0_ + y1_ + 1) // 2
            tps.append((C2 - 3, m - 2, 3, 4))
        else:
            x0_, x1_ = STRASSEN_V[i][0] + P, STRASSEN_V[i][1] + P
            k2[STADT[3] + P + 1:, x0_:x1_ + 1] = 'a'
            m = (x0_ + x1_ + 1) // 2
            tps.append((m - 2, R2 - 3, 4, 3))
    for (x, y, b, h) in tps:
        k2[y:y + h, x:x + b] = 'e'
    lay = {'groesse': [C2, R2], 'klassen': [''.join(z) for z in k2], 'hoehe': ['1' * C2 for _ in range(R2)],
           'versatz': P, 'teleporter': [{'x': x, 'y': y, 'b': b, 'h': h} for (x, y, b, h) in tps],
           'zebra': [[x0_ + P, x1_ + P, y0_ + P, y1_ + P, art] for (x0_, x1_, y0_, y1_, art) in ZEBRA],
           'strassen_h': [[a_ + P, b_ + P, max(0, c_ + P), min(d_ + P, C2 - 1)] for (a_, b_, c_, d_) in STRASSEN_H],
           'strassen_v': [[a_ + P, b_ + P, max(0, c_ + P), min(d_ + P, R2 - 1)] for (a_, b_, c_, d_) in STRASSEN_V],
           'gebaeude_flaechen': {n: [v[0] + P, v[1] + P, v[2] + P, v[3] + P] for n, v in GEBAEUDE.items()},
           'stadt': [STADT[0] + P, STADT[1] + P, STADT[2] + P, STADT[3] + P]}
    os.makedirs(KARTE, exist_ok=True)
    json.dump(lay, open(os.path.join(KARTE, 'layout.json'), 'w'), indent=0)
    F = {'a': (50, 56, 70), 'g': (170, 178, 176), 'k': (140, 150, 156), 'q': (196, 196, 186), 'b': (176, 160, 130),
         'n': (80, 140, 60), 'h': (30, 80, 30), 'e': (120, 220, 255)}
    out = np.zeros((R2, C2, 3), np.uint8)
    for kk, c in F.items():
        out[k2 == kk] = c
    vor = Image.open(VORLAGE).convert('RGB').resize((C * 8, R * 8))
    bild = Image.new('RGB', (C2 * 16 + 8, R2 * 8))
    bild.paste(vor, (P * 8, P * 8))
    bild.paste(Image.fromarray(out).resize((C2 * 8, R2 * 8), 0), (C2 * 8 + 8, 0))
    bild.save(os.path.join(KARTE, 'layout_vergleich.png'))
    print('Karte 39 Layout %dx%d' % (C2, R2))


if __name__ == '__main__':
    main()
