"""Karte 53 - Shinjuku Evacuation District (A03 Nr. 20), Layout nach der Vorlage -> maps/karte53/layout.json

  python3 tools/karte53_layout.py

Vorlage assets/vorlagen/karte53_vorlage.png: 1536x1280 px = 96x80 Kacheln (1:1). Evakuiertes Stadtviertel: sieben
Gehwegbloecke zwischen Strassen (zwei Nord-Sued-Strassen, Hauptstrasse West-Ost, Querstrasse oben), sechs Buerogebaeude,
Rasenbeete, neun Zebrastreifen, erste D-Reaper-Flecken (rot). Ringsum Baumguertel (Nutzer K35): der aeussere Asphaltrand
der Vorlage wird Gehweg (Strassenenden schliessen mit Bordstein), Ausgaenge links (Gehweg) und unten rechts (Fahrbahn in
voller Breite) laufen durch den Guertel zum Teleporter am neuen Rand.
Korrekturen der Vorlage: Beetluecken vor allen Eingaengen (Tuer auf der Gebaeudeachse), Gehwegstreifen rechts kreuzt die
Hauptstrasse nicht mehr, Teleporter mittig in seinem Weg.

Klassen:  a Fahrbahn  k Gehweg  n Rasen  r D-Reaper-Masse (gesperrt)  h Baumguertel (gesperrt)  e Teleporter
Alle Koordinaten unten sind Vorlagenkacheln; im Layout + RAND.
"""
import json, os
import numpy as np
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte53')
VORLAGE = os.path.join(ROOT, 'assets', 'vorlagen', 'karte53_vorlage.png')
C, R, T = 96, 80, 16
RAND = 4
BLOECKE = [(4, 3, 63, 23), (71, 3, 93, 52), (4, 26, 28, 52), (36, 31, 63, 52), (4, 61, 28, 77), (36, 61, 63, 77),
           (71, 61, 85, 77), (92, 53, 93, 77)]                       # (x0, y0, x1, y1) Gehwegbloecke
RASEN = [(4, 19, 26, 21), (38, 16, 61, 17), (73, 15, 92, 16), (4, 39, 26, 40), (54, 72, 60, 75)]
BEETE_KLEIN = [(74, 61, 77, 63), (21, 74, 24, 76)]            # kleine Beete unter Einzelbaeumen (Vorlage: Baum auf Gehweg)
REAPER = [(38, 3, 40, 12), (4, 19, 10, 21)]                           # D-Reaper-Flecken
# Gebaeude (x0, y0, x1, y1) - Tuer auf der Achse, davor Beetluecke
GEBAEUDE = {'glas_gross': (4, 3, 37, 17), 'glas_mitte': (42, 3, 62, 13), 'beige': (72, 3, 93, 13),
            'lila_rechts': (72, 18, 93, 28), 'lila_links': (4, 27, 25, 37), 'glas_zentrum': (40, 39, 61, 51)}
STRASSEN_H = [[53, 60, 0, 95], [24, 30, 29, 70]]   # (y0, y1, x0, x1) Mittellinie; Querstrasse links nur 2 Reihen (Gehweg hinter lila_links)
STRASSEN_V = [[29, 35, 24, 79], [64, 70, 0, 79], [86, 91, 61, 79]]    # (x0, x1, y0, y1)
ZEBRA = [(64, 70, 21, 21, 'h'), (29, 35, 33, 33, 'h'), (64, 70, 33, 33, 'h'), (29, 35, 51, 51, 'h'), (64, 70, 51, 51, 'h'),
         (29, 35, 63, 63, 'h'), (64, 70, 63, 63, 'h'), (37, 37, 53, 60, 'v'), (72, 72, 53, 60, 'v')]


def main():
    k = np.full((R, C), 'a')
    for (x0, y0, x1, y1) in BLOECKE:
        k[y0:y1 + 1, x0:x1 + 1] = 'k'
    for (x0, y0, x1, y1) in RASEN:
        k[y0:y1 + 1, x0:x1 + 1] = 'n'
    for (x0, y0, x1, y1) in BEETE_KLEIN:
        k[y0:y1 + 1, x0:x1 + 1] = 'n'
    for n_, (x0, y0, x1, y1) in GEBAEUDE.items():                    # Beetluecke vor der Tuer (4 Kacheln auf der Achse)
        ax = (x0 + x1 + 1) // 2
        for y in range(y1 + 1, y1 + 6):
            if y < R and (k[y, ax - 2:ax + 2] == 'n').any():
                k[y, ax - 2:ax + 2] = np.where(k[y, ax - 2:ax + 2] == 'n', 'k', k[y, ax - 2:ax + 2])
    for (x0, y0, x1, y1) in REAPER:
        k[y0:y1 + 1, x0:x1 + 1] = 'r'
    k[0:3, :] = 'k'; k[78:80, :] = 'k'; k[:, 0:4] = 'k'; k[:, 94:96] = 'k'   # aeusserer Rand: Gehweg vor dem Guertel
    k[53:61, 92:94] = 'k'
    k[78:80, 86:92] = 'a'                                             # Ausgang unten rechts: Fahrbahn durch den Rand
    P = RAND
    C2, R2 = C + 2 * P, R + 2 * P
    k2 = np.full((R2, C2), 'h')
    k2[P:P + R, P:P + C] = k
    k2[P + R:, 86 + P:92 + P] = 'a'                                   # Fahrbahn durch den Guertel bis zum Rand
    k2[71 + P:76 + P, 0:P] = 'k'                                      # Gehweg links (inkl. Reihe ueber dem Teleporter)
    tps = [(0, 72 + P, 3, 4), (87 + P, R2 - 3, 4, 3)]
    for (x, y, b, h) in tps:
        k2[y:y + h, x:x + b] = 'e'
    lay = {'groesse': [C2, R2], 'klassen': [''.join(z) for z in k2], 'hoehe': ['1' * C2 for _ in range(R2)],
           'versatz': P, 'teleporter': [{'x': x, 'y': y, 'b': b, 'h': h} for (x, y, b, h) in tps],
           'zebra': [[x0_ + P, x1_ + P, y0_ + P, y1_ + P, art] for (x0_, x1_, y0_, y1_, art) in ZEBRA],
           'strassen_h': [[a_ + P, b_ + P, c_ + P, d_ + P] for (a_, b_, c_, d_) in STRASSEN_H],
           'strassen_v': [[a_ + P, b_ + P, c_ + P, d_ + P] for (a_, b_, c_, d_) in STRASSEN_V],
           'gebaeude_flaechen': {n: [v[0] + P, v[1] + P, v[2] + P, v[3] + P] for n, v in GEBAEUDE.items()},
           'stadt': [P, P, P + C - 1, P + R - 1]}
    os.makedirs(KARTE, exist_ok=True)
    json.dump(lay, open(os.path.join(KARTE, 'layout.json'), 'w'), indent=0)
    F = {'a': (50, 56, 70), 'k': (150, 156, 160), 'n': (80, 140, 60), 'h': (30, 80, 30), 'e': (120, 220, 255),
         'r': (150, 30, 50)}
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
    print('Karte 53 Layout %dx%d' % (C2, R2))


if __name__ == '__main__':
    main()
