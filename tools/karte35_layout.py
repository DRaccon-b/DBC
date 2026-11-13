"""Karte 35 - Shinjuku Digital Fog (A03 Nr. 2), Layout nach der Vorlage -> maps/karte35/layout.json

  python3 tools/karte35_layout.py

Vorlage assets/vorlagen/karte35_vorlage.png: 1536x1280 px = 96x80 Kacheln (1:1). Buero- und Wohnviertel bei Nacht:
Strassenraster (dunkler Asphalt, gelbe Mittelstriche, Zebrastreifen), erhoehte Gehweg-Bloecke mit Bordstein,
Gruenstreifen mit Baeumen, Fussgaengerbruecke ueber der mittleren Nord-Sued-Strasse, neun Gebaeude. Ausserhalb des
Stadtrands (aeusserer Ring) liegt der digitale Nebel - nicht begehbar; vier Ausgaenge mit Teleportern fuehren hinein.

Klassen:  a Fahrbahn  g Gehweg  n Rasen  x Nebel (Rand, gesperrt)  e Ausgang (Teleporter)
"""
import json, os, sys
import numpy as np
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte35')
VORLAGE = os.path.join(ROOT, 'assets', 'vorlagen', 'karte35_vorlage.png')
C, R, T = 96, 80, 16
STADT = (2, 1, 93, 77)                                            # oben eine Reihe mehr (Tuerme ganz auf Land)                                            # Stadtflaeche (x0, y0, x1, y1), aussen Nebel
AUSGAENGE = [(84, 0, 4, 3), (93, 58, 3, 4), (20, 77, 4, 3), (77, 77, 4, 3)]   # (x, y, b, h): oben rechts, rechts, unten
# Zebrastreifen (x0, x1, y0, y1): ueber die Nord-Sued-Strassen an den Blockkanten (Streifen senkrecht, Laufrichtung W-O)
ZEBRA = [(76, 81, 12, 12), (36, 42, 23, 23), (36, 42, 34, 34), (76, 82, 23, 23), (76, 82, 34, 34),
         (36, 42, 44, 44), (76, 82, 44, 44), (36, 42, 54, 54), (76, 82, 54, 54), (36, 42, 64, 64), (76, 82, 64, 64)]
# Gebaeude: Name -> (x0, y0, x1, y1) Grundflaeche der Vorlage in Kacheln (Fusszeile = y1)
GEBAEUDE = {
    'turm_a': (4, 3, 13, 21), 'turm_b': (17, 3, 26, 21), 'buero_oben': (32, 3, 73, 7),
    'wohn_links': (4, 26, 17, 34), 'buero_mitte': (46, 27, 67, 33), 'schmal_rechts_oben': (84, 21, 93, 31),
    'wohn_mitte': (21, 45, 34, 53), 'schmal_rechts_unten': (84, 44, 93, 54), 'buero_unten': (43, 68, 72, 76),
}
BRUECKE = (34, 27, 44, 31)                                        # Fussgaengerbruecke ueber der Strasse (Spalten 36-42)


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
    k = vorlage_klassen()
    k[k == '?'] = 'g'                                                  # Gebaeude/Objekte stehen auf dem Gehweg
    for (x0, x1, y0, y1) in ZEBRA:                                    # Zebrastreifen liegen auf der Fahrbahn
        k[y0:y1 + 1, x0:x1 + 1] = 'a'
    import karte34_layout as l34                                       # Einzelkacheln/Zipfel angleichen (Pruefliste)
    l34.R, l34.C = R, C
    k = l34.kleine_weg(k, 'a', 30)                                     # dunkle Baumstaemme/Objekte im Rasen: keine Fahrbahn
    bx0, by0, bx1, by1 = BRUECKE                                       # unter der Fussgaengerbruecke laeuft die Strasse
    k[by0 - 3:by1 + 3, bx0 + 2:bx1 - 1] = 'a'
    for name, (x0, y0, x1, y1) in GEBAEUDE.items():                   # Gebaeudeflaechen ganz auf Gehweg
        k[y0:y1 + 1, x0:x1 + 1] = 'g'
    k[68:76, 17:30][k[68:76, 17:30] == 'n'] = 'g'                      # Beet unten links als sauberes Rechteck (Vorlage)
    k[70:74, 19:27] = 'n'
    # Gruenstreifen an die (hoeheren) Gebaeude angepasst (Regel: Karte passt sich dem Gebaeude an):
    k[9:12, 44:70][k[9:12, 44:70] == 'n'] = 'g'                      # oben: Beete vor dem Glasbuero eine Reihe tiefer
    k[12:14, 47:54] = 'n'; k[12:14, 57:67] = 'n'
    k[22:26, 4:27][k[22:26, 4:27] == 'n'] = 'g'                      # links: Tuerme hoeher -> kleines Beet zwischen
    k[21:23, 14:17] = 'n'                                              # den Tuermen statt Streifen davor
    k[1, 2:94] = 'g'                                                   # oberste Stadtreihe: Gehweg hinter den Tuermen
    k[24:26, 45:72][k[24:26, 45:72] == 'n'] = 'g'                    # Mitte: Streifen ueber dem Glasbuero 2 Reihen
    k = l34.zipfel_weg(k, 'gn')
    k = l34.kleine_weg(k, 'n', 6, 'g')
    x0, y0, x1, y1 = STADT
    stadt = np.zeros((R, C), bool); stadt[y0:y1 + 1, x0:x1 + 1] = True
    k[~stadt] = 'x'
    for (x, y, b, h) in AUSGAENGE:                                    # Zugang zum Teleporter: Gehweg/Strasse fuehrt hinein
        k[y:y + h, x:x + b] = 'e'
    lay = {'groesse': [C, R], 'klassen': [''.join(z) for z in k], 'hoehe': ['1' * C for _ in range(R)],
           'teleporter': [{'x': x, 'y': y, 'b': b, 'h': h} for (x, y, b, h) in AUSGAENGE],
           'zebra': [[x0, x1, y0, y1, 'h'] for (x0, x1, y0, y1) in ZEBRA], 'gebaeude': GEBAEUDE, 'bruecke': BRUECKE,
           'stadt': STADT}
    os.makedirs(KARTE, exist_ok=True)
    json.dump(lay, open(os.path.join(KARTE, 'layout.json'), 'w'), indent=0)
    F = {'a': (50, 56, 70), 'g': (170, 170, 170), 'n': (80, 140, 60), 'x': (150, 120, 200), 'e': (120, 220, 255)}
    out = np.zeros((R, C, 3), np.uint8)
    for kk, c in F.items():
        out[k == kk] = c
    vor = Image.open(VORLAGE).convert('RGB').resize((C * 8, R * 8))
    bild = Image.new('RGB', (C * 16 + 8, R * 8))
    bild.paste(vor, (0, 0))
    bild.paste(Image.fromarray(out).resize((C * 8, R * 8), 0), (C * 8 + 8, 0))
    bild.save(os.path.join(KARTE, 'layout_vergleich.png'))
    print('Karte 35 Layout %dx%d' % (C, R))


if __name__ == '__main__':
    main()
