"""Karte 40 - Shinjuku Siege (A03 Nr. 7), Layout nach der Vorlage -> maps/karte40/layout.json

  python3 tools/karte40_layout.py

Vorlage assets/vorlagen/karte40_vorlage.png: 768x576 px = 48x36 Kacheln (1:1). Breite Shinjuku-Kreuzung (nach rechts
unten aufgeweitet) mit vier Zebrastreifen, drei Buerogebaeude (beige oben links, Glas oben rechts, lila unten), zwei
Baumbeete, Ziegel-Gehwege, Platz unten links mit Teleporter. Ringsum Baumguertel (Nutzer), die Strassenenden schliessen
mit Bordstein vor dem Guertel ab, der Teleporter liegt am neuen Rand am Ende eines Gehwegs durch den Guertel. Vor dem
unteren Block liegt eine zusaetzliche Gehwegreihe (Gebaeude nie direkt am Wald, Pruefliste K39).

Klassen:  a Fahrbahn  k Ziegel-Gehweg  q Platzpflaster  n Rasen  h Baumguertel (gesperrt)  e Teleporter
Alle Koordinaten unten sind Vorlagenkacheln; im Layout + RAND.
"""
import json, os, sys
import numpy as np
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte40')
VORLAGE = os.path.join(ROOT, 'assets', 'vorlagen', 'karte40_vorlage.png')
C, R, T = 48, 36, 16
RAND = 4
STRASSEN_H = [(12, 21, 0, 15), (12, 24, 16, 36), (13, 24, 37, 47)]   # (y0, y1, x0, x1)
STRASSEN_V = [(18, 31, 0, 11)]                                       # (x0, x1, y0, y1)
ZEBRA = [(18, 31, 10, 10, 'h'), (17, 32, 22, 22, 'h'), (14, 14, 12, 21, 'v'), (34, 34, 13, 24, 'v')]
GEBAEUDE = {'beige': (1, 1, 14, 9), 'glas': (37, 2, 46, 11), 'lila': (19, 27, 36, 35)}
BEETE = [(2, 12, 8, 13), (39, 25, 44, 26)]                           # (x0, y0, x1, y1) Rasen mit Baeumen
TELEPORTER_X = (6, 9)                                                # unten links (Vorlage), Weg durch den Guertel


def main():
    k = np.full((R, C), 'k')
    band = np.zeros((R, C), bool)
    for (y0, y1, x0, x1) in STRASSEN_H:
        band[y0:y1 + 1, x0:x1 + 1] = True
    for (x0, x1, y0, y1) in STRASSEN_V:
        band[y0:y1 + 1, x0:x1 + 1] = True
    k[band] = 'a'
    for (x0, y0, x1, y1) in BEETE:
        k[y0:y1 + 1, x0:x1 + 1] = 'n'
    k[band] = 'a'                                                    # Beet links oben liegt am Strassenrand: Fahrbahn bleibt
    k[12:14, 2:9] = 'n'; k[12:14, 0:15][k[12:14, 0:15] == 'a'] = 'k'  # linkes Beet + Gehweg davor (Vorlage)
    band[12:14, 0:15] = False
    k[26:R, 0:18][k[26:R, 0:18] == 'k'] = 'q'                        # Platz unten links (Teleporter-Platz)
    P = RAND
    C2, R2 = C + 2 * P, R + 2 * P + 1                                # unten eine Reihe mehr: Gehweg vor dem lila Block
    k2 = np.full((R2, C2), 'h')
    k2[P:P + R, P:P + C] = k
    k2[P + R, P:P + C] = 'k'
    x0, x1 = TELEPORTER_X
    k2[P + R:, x0 + P:x1 + P + 1] = 'q'                              # Gehweg durch den Guertel zum Teleporter
    tps = [(x0 + P, R2 - 3, x1 - x0 + 1, 3)]
    for (x, y, b, h) in tps:
        k2[y:y + h, x:x + b] = 'e'
    lay = {'groesse': [C2, R2], 'klassen': [''.join(z) for z in k2], 'hoehe': ['1' * C2 for _ in range(R2)],
           'versatz': P, 'teleporter': [{'x': x, 'y': y, 'b': b, 'h': h} for (x, y, b, h) in tps],
           'zebra': [[x0_ + P, x1_ + P, y0_ + P, y1_ + P, art] for (x0_, x1_, y0_, y1_, art) in ZEBRA],
           'strassen_h': [[12 + P, 21 + P, P, C - 1 + P]],              # Mittellinie gemeinsam (Vorlage: Reihe 17)
           'strassen_v': [[a_ + P, b_ + P, c_ + P, d_ + P] for (a_, b_, c_, d_) in STRASSEN_V],
           'gebaeude_flaechen': {n: [v[0] + P, v[1] + P, v[2] + P, v[3] + P] for n, v in GEBAEUDE.items()},
           'stadt': [P, P, P + C - 1, P + R]}
    os.makedirs(KARTE, exist_ok=True)
    json.dump(lay, open(os.path.join(KARTE, 'layout.json'), 'w'), indent=0)
    F = {'a': (50, 56, 70), 'k': (140, 150, 156), 'q': (196, 196, 186), 'n': (80, 140, 60), 'h': (30, 80, 30),
         'e': (120, 220, 255)}
    out = np.zeros((R2, C2, 3), np.uint8)
    for kk, c in F.items():
        out[k2 == kk] = c
    vor = Image.open(VORLAGE).convert('RGB').resize((C * 8, R * 8))
    bild = Image.new('RGB', (C2 * 16 + 8, R2 * 8))
    bild.paste(vor, (P * 8, P * 8))
    bild.paste(Image.fromarray(out).resize((C2 * 8, R2 * 8), 0), (C2 * 8 + 8, 0))
    bild.save(os.path.join(KARTE, 'layout_vergleich.png'))
    print('Karte 40 Layout %dx%d' % (C2, R2))


if __name__ == '__main__':
    main()
