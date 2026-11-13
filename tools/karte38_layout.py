"""Karte 38 - Deva Transit (A03 Nr. 5), Layout nach der Vorlage -> maps/karte38/layout.json

  python3 tools/karte38_layout.py

Vorlage assets/vorlagen/karte38_vorlage.png: 1536x1280 px = 96x80 Kacheln (1:1). Bahnhof: drei Bahnsteig-Streifen aus
hellen Ziegelwegen und glatten Bahnsteigplatten, zwei Gleisbaender (je zwei Gleise) quer ueber die ganze Karte mit drei
Bahnuebergaengen, Wartehaeuschen, drei Bahnhofsgebaeude auf dunklem Pflaster, Treppenabgaenge, Leitstreifen. Der dunkle
Rand der Vorlage wird zum Baumguertel (Nutzer: Karte nie im Nichts enden lassen), die Karte ringsum um RAND Kacheln
erweitert; die Gleise laufen in voller Breite hindurch bis zum Kartenrand, die beiden Ausgaenge (oben, unten) als
Ziegelweg bis zum Teleporter am neuen Rand.

Klassen:  d dunkles Pflaster  k Ziegelweg  p Bahnsteigplatten  a Gleisbett  h Baumguertel (gesperrt)  e Teleporter
Alle Koordinaten unten sind Vorlagenkacheln; im Layout + RAND.
"""
import json, os
import numpy as np
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte38')
VORLAGE = os.path.join(ROOT, 'assets', 'vorlagen', 'karte38_vorlage.png')
C, R, T = 96, 80, 16
RAND = 4
STADT = (3, 3, 92, 76)                                            # Bahnhofsflaeche (x0, y0, x1, y1)
REF = {'d': (61, 80, 98), 'k': (145, 159, 164), 'p': (168, 178, 177), 'a': (52, 61, 73), 'x': (180, 178, 198),
       'l': (80, 80, 80), 'y': (168, 192, 80)}
GLEISBAENDER = [(25, 31), (49, 55)]                               # Zeilen der Gleisbaender (y0, y1)
GLEISE = [26, 30, 50, 54]                                         # Mittelzeile je Gleis
UEBERGAENGE = [(20, 26), (44, 49), (72, 78)]                      # Bahnuebergaenge = Breite der Ziegelwege (Durchgaenge passend)
AUSGAENGE = [(21, 0, 4, 3), (79, 77, 4, 3)]                       # (x, y, b, h): oben, unten
LEITZEILEN = [16, 39, 67]                                         # Leitstreifen auf den Bahnsteigen (Vorlage)
# Gebaeude auf dunklem Pflaster (x0, y0, x1, y1), Fusszeile = y1
GEBAEUDE = {'glas_oben': (4, 5, 13, 13), 'glas_mitte': (4, 33, 13, 38), 'beige_unten': (81, 64, 90, 70)}


def main():
    a = np.array(Image.open(VORLAGE).convert('RGB')).astype(int)
    med = np.zeros((R, C, 3), int)
    for y in range(R):
        for x in range(C):
            med[y, x] = np.median(a[y * T:(y + 1) * T, x * T:(x + 1) * T].reshape(-1, 3), 0)
    ks = list(REF)
    ref = np.array([REF[k] for k in ks])
    d = ((med[:, :, None, :] - ref[None, None]) ** 2).sum(-1)
    k = np.array(ks)[d.argmin(-1)]
    k[d.min(-1) > 900] = '?'
    for (x0, y0, x1, y1) in GEBAEUDE.values():                    # Gebaeude stehen auf dunklem Pflaster
        k[y0:y1 + 1, x0:x1 + 1] = 'd'
    # Leitstreifen merken (Segmente), Boden darunter wie die Nachbarzeile
    leit = []
    for y in LEITZEILEN:
        x = 0
        while x < C:
            if k[y, x] != 'l':
                x += 1; continue
            e = x
            while e < C and k[y, e] in 'l?':
                e += 1
            if e - x >= 2:
                leit.append([x, e - 1, y])
            x = e
        for x in range(C):
            if k[y, x] in 'l?':
                k[y, x] = k[y - 1, x] if k[y - 1, x] not in 'l?' else k[y + 1, x]
    band_z = np.zeros(R, bool)
    for (g0, g1) in GLEISBAENDER:
        band_z[g0:g1 + 1] = True
    k[(np.isin(k, ['a', 'x'])) & ~band_z[:, None]] = '?'           # dunkle Objektpixel ausserhalb der Gleise (Automaten)
    k[np.isin(k, ['y', 'l'])] = 'k'                                # Bahnsteigkanten: Ziegel (Kante in bauen)
    k[k == 'x'] = 'a'                                              # Uebergaenge liegen auf dem Gleisbett
    for (y0, y1) in GLEISBAENDER:
        k[y0:y1 + 1, :] = 'a'
    for _ in range(6):                                             # Objekte/Daecher der Vorlage: Boden der Nachbarn
        for y, x in zip(*np.nonzero(k == '?')):
            nb = [k[yy, xx] for yy, xx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1))
                  if 0 <= yy < R and 0 <= xx < C and k[yy, xx] != '?']
            if nb:
                k[y, x] = max(set(nb), key=nb.count)
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import karte34_layout as l34
    l34.R, l34.C = R, C
    k = l34.kleine_weg(k, 'd', 3, 'k')                             # Einzelkacheln angleichen (Pruefliste)
    k = l34.kleine_weg(k, 'p', 3, 'k')
    k = l34.kleine_weg(k, 'k', 4, 'p')                             # Objekt-Reste auf den Bahnsteigen
    # Bahnsteige sind Rechtecke: je Bahnsteig-Streifen und Spalte Ziegel/Platten nach Mehrheit (Objekt-Reste der Vorlage)
    grenzen = [3] + [g for b in GLEISBAENDER for g in (b[0] - 2, b[1] + 2)] + [76]
    for s0, s1 in zip(grenzen[0::2], grenzen[1::2]):
        for x in range(C):
            sp = k[s0:s1 + 1, x]
            kp = np.isin(sp, ['k', 'p'])
            if kp.sum() < 3:
                continue
            maj = 'p' if (sp == 'p').sum() > (sp == 'k').sum() else 'k'
            sp[kp & (np.arange(len(sp)) > 0) & (np.arange(len(sp)) < len(sp) - 1)] = maj
    k = l34.kleine_weg(k, 'p', 3, 'k')
    for _ in range(2):                                             # 1-Kachel-Zipfel/Kerben im dunklen Pflaster (Pruefliste)
        for y in range(1, R - 1):
            for x in range(1, C - 1):
                if k[y, x] == 'd' and k[y - 1, x] == 'd' and k[y + 1, x] != 'd' and k[y, x - 1] != 'd' and k[y, x + 1] != 'd':
                    k[y, x] = k[y + 1, x]
                if k[y, x] != 'd' and k[y, x - 1] == 'd' and k[y, x + 1] == 'd':
                    k[y, x] = 'd'
    sub = k[71:73, 81:91]                                          # Eingangsstufen des beigen Bahnhofs -> Pflaster
    sub[sub == 'k'] = 'd'
    x0, y0, x1, y1 = STADT
    innen = np.zeros((R, C), bool); innen[y0:y1 + 1, x0:x1 + 1] = True
    for (g0, g1) in GLEISBAENDER:
        innen[g0:g1 + 1, :] = True                                 # Gleise laufen bis an den Rand
    k[~innen] = 'h'
    P = RAND
    C2, R2 = C + 2 * P, R + 2 * P
    k2 = np.full((R2, C2), 'h')
    k2[P:P + R, P:P + C] = k
    for (g0, g1) in GLEISBAENDER:                                   # Gleisbaender durch den Guertel
        k2[g0 + P:g1 + P + 1, :] = 'a'
    tps = []
    for (x, y, b, h) in AUSGAENGE:                                 # Ausgaenge als Ziegelweg bis an den neuen Rand
        x += P
        if y == 0:
            k2[0:STADT[1] + P, x:x + b] = 'k'
            tps.append((x, 0, b, 3))
        else:
            k2[STADT[3] + P + 1:, x:x + b] = 'k'
            tps.append((x, R2 - 3, b, 3))
    for (x, y, b, h) in tps:
        k2[y:y + h, x:x + b] = 'e'
    lay = {'groesse': [C2, R2], 'klassen': [''.join(z) for z in k2], 'hoehe': ['1' * C2 for _ in range(R2)],
           'versatz': P, 'teleporter': [{'x': x, 'y': y, 'b': b, 'h': h} for (x, y, b, h) in tps],
           'gleisbaender': [[a_ + P, b_ + P] for (a_, b_) in GLEISBAENDER], 'gleise': [g + P for g in GLEISE],
           'uebergaenge': [[a_ + P, b_ + P] for (a_, b_) in UEBERGAENGE],
           'leitstreifen': [[x0_ + P, x1_ + P, y_ + P] for (x0_, x1_, y_) in leit],
           'gebaeude_flaechen': {n: [v[0] + P, v[1] + P, v[2] + P, v[3] + P] for n, v in GEBAEUDE.items()},
           'stadt': [STADT[0] + P, STADT[1] + P, STADT[2] + P, STADT[3] + P]}
    os.makedirs(KARTE, exist_ok=True)
    json.dump(lay, open(os.path.join(KARTE, 'layout.json'), 'w'), indent=0)
    F = {'a': (50, 56, 70), 'k': (150, 160, 165), 'p': (190, 196, 196), 'd': (60, 80, 100), 'h': (30, 80, 30),
         'e': (120, 220, 255)}
    out = np.zeros((R2, C2, 3), np.uint8)
    for kk, c in F.items():
        out[k2 == kk] = c
    vor = Image.open(VORLAGE).convert('RGB').resize((C * 8, R * 8))
    bild = Image.new('RGB', (C2 * 16 + 8, R2 * 8))
    bild.paste(vor, (P * 8, P * 8))
    bild.paste(Image.fromarray(out).resize((C2 * 8, R2 * 8), 0), (C2 * 8 + 8, 0))
    bild.save(os.path.join(KARTE, 'layout_vergleich.png'))
    print('Karte 38 Layout %dx%d, %d Leitstreifen' % (C2, R2, len(leit)))


if __name__ == '__main__':
    main()
