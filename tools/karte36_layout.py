"""Karte 36 - Shinjuku Backstreets (A03 Nr. 3), Layout nach der Vorlage -> maps/karte36/layout.json

  python3 tools/karte36_layout.py

Vorlage assets/vorlagen/karte36_vorlage.png: 1536x1280 px = 96x80 Kacheln (1:1). Seitenstrassen in Shinjuku:
Strassenraster (Asphalt, gelbe Mittelstriche, Zebrastreifen quer und laengs), erhoehte Gehweg-Bloecke mit Bordstein,
Gruenstreifen und Beete mit Baeumen, acht Gebaeude (drei lange beige Wohnbloecke, lila Haus, zwei Glasbueros, flacher Bau,
Ladenzeile). Die Karte ist ringsum um RAND Kacheln erweitert und von einem Baumguertel umschlossen (Nutzer, wie Karte 35);
zwei Ausgaenge (oben, links) fuehren durch den Guertel zu den Teleportern am Rand.

Klassen:  a Fahrbahn  g Gehweg  n Rasen  h Baumguertel (Rand, gesperrt)  e Ausgang (Teleporter)
Alle Koordinaten unten sind Vorlagenkacheln; im Layout + RAND.
"""
import json, os, sys
import numpy as np
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte36')
VORLAGE = os.path.join(ROOT, 'assets', 'vorlagen', 'karte36_vorlage.png')
C, R, T = 96, 80, 16
RAND = 4                                                          # Baumguertel ringsum (Kacheln, Nutzer)
STADT = (4, 2, 93, 78)                                            # Stadtflaeche (oben eine Reihe mehr: Bloecke hoeher)
AUSGAENGE = [(35, 0, 4, 3), (0, 72, 3, 4)]                        # (x, y, b, h): oben, links (Vorlage)
# Zebrastreifen (x0, x1, y0, y1, art): 'h' = quer ueber eine Nord-Sued-Strasse, 'v' = quer ueber eine Ost-West-Strasse
ZEBRA = [(59, 65, 21, 21, 'h'), (27, 33, 32, 32, 'h'), (27, 33, 42, 42, 'h'), (27, 33, 53, 53, 'h'),
         (27, 33, 69, 69, 'h'), (59, 65, 32, 32, 'h'), (59, 65, 42, 42, 'h'), (59, 65, 53, 53, 'h'),
         (36, 36, 45, 50, 'v'), (36, 36, 59, 64, 'v')]
# Strassenbaender fuer die Mittellinien: waagerecht (y0, y1, x0, x1), senkrecht (x0, x1, y0, y1)
STRASSEN_H = [(23, 29, 4, 93), (45, 50, 4, 93), (59, 64, 4, 93)]
STRASSEN_V = [(27, 33, 28, 77), (59, 65, 3, 77), (86, 93, 23, 77)]
# Gebaeude: Name -> (x0, y0, x1, y1) Grundflaeche der Vorlage in Kacheln (Fusszeile = y1)
GEBAEUDE = {
    'wohn_oben': (4, 3, 33, 13), 'lila': (41, 3, 58, 11), 'glas_oben': (69, 3, 90, 13),
    'wohn_links': (4, 28, 25, 39),                               # Block hoeher als die Vorlage: Fuss 3 Reihen tiefer
    'laeden': (38, 36, 58, 43), 'glas_rechts': (69, 44, 82, 54),
    'flach': (7, 54, 24, 58), 'wohn_unten': (39, 67, 68, 77),
}
# Beete unter Baeumen, die in der Vorlage auf dem Gehweg stehen (3x2, Baum mittig auf dem Gruen)
BEETE = [(21, 75, 23, 76), (35, 75, 37, 76), (78, 75, 80, 76), (4, 68, 7, 70)]


def vorlage_klassen():
    a = np.array(Image.open(VORLAGE).convert('RGB')).astype(int)
    k = np.full((R, C), '?')
    for y in range(R):
        for x in range(C):
            r, g, b = np.median(a[y * T:(y + 1) * T, x * T:(x + 1) * T].reshape(-1, 3), 0)
            if r < 75 and g < 80 and b < 95:
                k[y, x] = 'a'
            elif g > r + 25 and g > b + 30:
                k[y, x] = 'n'
            elif abs(r - g) < 20 and r > 130:
                k[y, x] = 'g'
    return k


def main():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import karte34_layout as l34                                       # Einzelkacheln/Zipfel angleichen (Pruefliste)
    l34.R, l34.C = R, C
    k = vorlage_klassen()
    k[k == '?'] = 'g'                                                  # Gebaeude/Objekte stehen auf dem Gehweg
    for (x0, x1, y0, y1, art) in ZEBRA:                               # Zebrastreifen liegen auf der Fahrbahn
        k[y0:y1 + 1, x0:x1 + 1] = 'a'
    k = l34.kleine_weg(k, 'a', 30)                                     # Baumstaemme im Rasen sind keine Fahrbahn
    for name, (x0, y0, x1, y1) in GEBAEUDE.items():                   # Gebaeudeflaechen ganz auf Gehweg
        k[y0:y1 + 1, x0:x1 + 1] = 'g'
    for (x0, y0, x1, y1) in BEETE:
        k[y0:y1 + 1, x0:x1 + 1] = 'n'
    k[2, 4:94][k[2, 4:94] == 'a'] = 'g'                               # oberste Stadtreihe Gehweg hinter den Bloecken
    k[37:39, 4:26][k[37:39, 4:26] == 'n'] = 'g'                       # Gruenstreifen vor den linken Block verlegt,
    k[41:43, 4:25] = 'n'                                              # eine Gehwegreihe vor der Fassade,
    k[41:43, 10:14] = 'g'; k[41:43, 16:20] = 'g'                      # Luecken vor den beiden Tueren (Eingaenge frei)
    k[15:18, 77:82] = 'g'                                             # Beetluecke vor der Tuer des Glasbueros oben
    k[55:57, 74:77] = 'g'                                             # Beet rechts Mitte erst rechts der Tuer
    k[78, 4:94] = 'g'                                                 # Gehweg vor dem unteren Block (Tueren nicht im Wald)
    # Fahrbahn nur in den Strassenbaendern/Zebrastreifen: Asphaltreste der Vorlage (Tueren, Staemme) werden Gehweg
    band = np.zeros((R, C), bool)
    for (y0, y1, x0, x1) in STRASSEN_H:
        band[y0:y1 + 1, x0:x1 + 1] = True
    for (x0, x1, y0, y1) in STRASSEN_V:
        band[y0:y1 + 1, x0:x1 + 1] = True
    k[(k == 'a') & ~band] = 'g'
    k = l34.zipfel_weg(k, 'gn')
    k = l34.kleine_weg(k, 'n', 6, 'g')
    x0, y0, x1, y1 = STADT
    stadt = np.zeros((R, C), bool); stadt[y0:y1 + 1, x0:x1 + 1] = True
    k[~stadt] = 'h'
    P = RAND
    C2, R2 = C + 2 * P, R + 2 * P
    k2 = np.full((R2, C2), 'h')
    k2[P:P + R, P:P + C] = k
    tps = []
    for (x, y, b, h) in AUSGAENGE:                                    # Ausgaenge als Gehweg bis an den neuen Rand
        x, y = x + P, y + P
        if y == P:                                                     # oben: Gehweg von der Stadt bis zur Kante
            y_stadt = STADT[1] + P
            innen = k2[y_stadt, x:x + b].copy()
            for yy in range(0, y_stadt):
                k2[yy, x:x + b] = innen
            tps.append((x, 0, b, 3))
        elif x == P:                                                   # links
            x_stadt = STADT[0] + P
            innen = k2[y:y + h, x_stadt].copy()
            for xx in range(0, x_stadt):
                k2[y:y + h, xx] = innen
            tps.append((0, y, 3, h))
    for (x, y, b, h) in tps:
        k2[y:y + h, x:x + b] = 'e'
    k = k2
    lay = {'groesse': [C2, R2], 'klassen': [''.join(z) for z in k], 'hoehe': ['1' * C2 for _ in range(R2)],
           'versatz': P, 'teleporter': [{'x': x, 'y': y, 'b': b, 'h': h} for (x, y, b, h) in tps],
           'zebra': [[x0 + P, x1 + P, y0 + P, y1 + P, art] for (x0, x1, y0, y1, art) in ZEBRA],
           'strassen_h': [[a + P, b + P, c + P, min(d + P, C2 - 1)] for (a, b, c, d) in STRASSEN_H],
           'strassen_v': [[a + P, b + P, c + P, min(d + P, R2 - 1)] for (a, b, c, d) in STRASSEN_V],
           'gebaeude_flaechen': {n: [v[0] + P, v[1] + P, v[2] + P, v[3] + P] for n, v in GEBAEUDE.items()},
           'stadt': [STADT[0] + P, STADT[1] + P, STADT[2] + P, STADT[3] + P]}
    os.makedirs(KARTE, exist_ok=True)
    json.dump(lay, open(os.path.join(KARTE, 'layout.json'), 'w'), indent=0)
    F = {'a': (50, 56, 70), 'g': (170, 170, 170), 'n': (80, 140, 60), 'h': (30, 80, 30), 'e': (120, 220, 255)}
    out = np.zeros((R2, C2, 3), np.uint8)
    for kk, c in F.items():
        out[k == kk] = c
    vor = Image.open(VORLAGE).convert('RGB').resize((C * 8, R * 8))
    bild = Image.new('RGB', (C2 * 16 + 8, R2 * 8))
    bild.paste(vor, (P * 8, P * 8))
    bild.paste(Image.fromarray(out).resize((C2 * 8, R2 * 8), 0), (C2 * 8 + 8, 0))
    bild.save(os.path.join(KARTE, 'layout_vergleich.png'))
    print('Karte 36 Layout %dx%d' % (C2, R2))


if __name__ == '__main__':
    main()
