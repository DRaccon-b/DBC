"""Karte 50 - Zhuqiaomon's Sanctuary (A03 Nr. 17), Layout nach der Vorlage -> maps/karte50/layout.json

  python3 tools/karte50_layout.py

Vorlage assets/vorlagen/karte50_vorlage.png (1536x1280 = 96x80 Kacheln), Kacheln wie Karte 47: Felsboden, Pflasterwege und
-plaetze, Wiesenflecken, erhoehter Felsrand ringsum, abgesenkter Hof oben links, zwei rote Torii auf Treppen, untere Treppe,
drei Teleporter (links, rechts, unten rechts).

Klassen:  g Felsboden  w Pflaster  k dunkles Pflaster  n Wiese  h Felsrand (gesperrt, ueber allen Terrassen)
          d Hofboden (abgesenkter Hof)  t Treppe (Frontreihe)  T Teleporter
Hoehen (Nutzer: echte Terrassen, das Heiligtum steigt nach Norden an):
  0 unterste Ebene (Sueden)  1  2  3 oberste Terrasse (Norden)  Hof oben links = 2 (in Terrasse 3 abgesenkt)  Rand = 4
Korrekturen der Vorlage: Torii-Treppen ohne Hoehenunterschied -> durchgehende Terrassenkanten (45-Grad-Raster) mit den
Treppen als einzigem Uebergang; Felsbloecke neben den Treppen = Terrassenfront; Hof mit Nordtreppe hinunter (Nutzer:
abgesenkter Hof); Zipfel/Einzelkacheln geglaettet; Ausgaenge in Teleporterbreite.
"""
import json, os
import numpy as np
from PIL import Image, ImageDraw
import karte43_layout as k43

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte50')
VORLAGE = os.path.join(ROOT, 'assets', 'vorlagen', 'karte50_vorlage.png')
C, R, T = 96, 80, 16
REF = {'g': (115, 131, 147), 'w': (138, 146, 155), 'h': (137, 151, 165), 'f': (101, 118, 138), 'n': (82, 138, 59),
       'W': (137, 144, 149), 'd': (68, 74, 90), 'r': (73, 91, 112), 'x': (125, 144, 155), 'k': (123, 128, 129),
       't': (129, 135, 149), 'y': (89, 109, 128)}
# Terrassenkanten: erste Reihe der tieferen Ebene je Spaltenbereich (Front liegt dort); Treppen (x0, x1) darin
KANTEN = [  # (Hoehe darueber, [(x0, x1, Reihe)], Treppe)
    (3, [(0, 27, 34), (28, 66, 25), (67, 81, 24), (82, 95, 30)], (51, 58)),   # Teleporter links/rechts auf Ebene 3
    (2, [(0, 23, 53), (24, 59, 48), (60, 75, 47), (76, 95, 46)], (47, 54)),   # links Abstand zum Felsrand
    (1, [(0, 29, 72), (30, 63, 70), (64, 95, 69)], (41, 46)),
]
HOF = (12, 9, 26, 17)                    # abgesenkter Hof (x0, y0, x1, y1), Treppe in der Suedreihe darunter
HOF_TREPPE = (18, 20)                    # 3 Kacheln: Mitte = Hofachse (Hof 15 Kacheln breit)
TELEPORTER = [(0, 29, 3, 4), (93, 24, 3, 4), (85, 77, 4, 3)]
k43.R, k43.C = R, C
RAND = os.environ.get('K50_RAND', 'versetzt')   # folgt | hoch | versetzt | flanke (Nutzer: Varianten der Berglogik)


def main():
    os.makedirs(KARTE, exist_ok=True)
    a = np.array(Image.open(VORLAGE).convert('RGB')).astype(int)
    M = np.median(a.reshape(R, T, C, T, 3).transpose(0, 2, 1, 3, 4).reshape(R, C, T * T, 3), 2)
    ks = list(REF)
    ref = np.array([REF[c] for c in ks], float)
    k = np.array(ks)[((M[:, :, None, :] - ref[None, None]) ** 2).sum(-1).argmin(-1)].astype('<U1')
    k[np.isin(k, list('frxyt'))] = 'g'
    k[k == 'W'] = 'w'
    k[k == 'd'] = 'g'
    for teil in k43.flaechen(k == 'h'):                               # kleine Fels-Einzelkacheln (Objekte) -> Boden
        if len(teil) < 8:
            for (y, x) in teil:
                k[y, x] = 'n' if any(k[yy, xx] == 'n' for yy, xx in ((y, x - 1), (y, x + 1), (y - 1, x), (y + 1, x))
                                     if 0 <= yy < R and 0 <= xx < C) else 'g'
    for kl in ('n', 'k', 'w'):
        for teil in k43.flaechen(k == kl):
            if len(teil) < 5:
                for (y, x) in teil:
                    k[y, x] = 'g'
    k = k43.zipfel_weg(k, 'gwknh')
    # Hoehen: Terrassen nach Norden ansteigend
    hp = np.zeros((R, C), int)
    for (hoehe, seg, _) in KANTEN:
        for (x0, x1, ry) in seg:
            hp[:ry, x0:x1 + 1] = np.maximum(hp[:ry, x0:x1 + 1], hoehe)
    hp_ter = hp.copy()                                                # Terrassenhoehe je Kachel (auch unter dem Rand)
    if RAND == 'hoch' or RAND == 'flanke':
        hp_rand = np.full((R, C), 3)                                  # Rand ueberall hoechster Berg (Hoehe 4)
    elif RAND == 'versetzt':                                          # Rand steigt ab, Stufen 4 Reihen suedlich der Kante
        hp_rand = np.zeros((R, C), int)
        for (hoehe, seg, _) in KANTEN:
            for (x0, x1, ry) in seg:
                versatz = 1 if any(x0 <= tx_ <= x1 and ty_ > ry for (tx_, ty_, _b, _h) in TELEPORTER if ty_ + _h == R) else 4
                hp_rand[:ry + versatz, x0:x1 + 1] = np.maximum(hp_rand[:ry + versatz, x0:x1 + 1], hoehe)   # unten am
                # Teleporter frueher absetzen: sonst stapeln sich die Fronten direkt ueber dem Ausgang (Nutzer)
    else:
        hp_rand = hp_ter
    if RAND == 'flanke':                                              # Terrassenkanten steigen zum Rand schraeg an
        for (hoehe, seg, _) in KANTEN:
            for (x0, x1, ry) in seg:
                for x in range(x0, x1 + 1):
                    for rx in range(1, 5):                            # Abstand zum Rand links/rechts
                        if any(0 <= x + s_ * rx < C and k[ry, x + s_ * rx] == 'h' and k[ry - 1, x + s_ * rx] == 'h'
                               for s_ in (-1, 1)):
                            hp[ry:ry + 5 - rx, x] = np.maximum(hp[ry:ry + 5 - rx, x], hoehe)
                            break
    # Hof oben links: zwei Stufen tiefer als die oberste Terrasse liegt er nicht - eine Stufe (Hoehe 2)
    hx0, hy0, hx1, hy1 = HOF
    k[hy0:hy1 + 1, hx0:hx1 + 1] = 'd'
    hp[hy0:hy1 + 1, hx0:hx1 + 1] = 2
    k[hy1 + 1:hy1 + 4, hx0 - 1:hx1 + 2] = np.where(k[hy1 + 1:hy1 + 4, hx0 - 1:hx1 + 2] == 'h', 'g', k[hy1 + 1:hy1 + 4, hx0 - 1:hx1 + 2])
    k[hy0 - 1, hx0 - 1:hx1 + 2] = np.where(k[hy0 - 1, hx0 - 1:hx1 + 2] == 'h', 'g', k[hy0 - 1, hx0 - 1:hx1 + 2])   # Rand um den Hof
    for y in range(hy0 - 1, hy1 + 2):
        for x in (hx0 - 1, hx1 + 1):
            if k[y, x] == 'h':
                k[y, x] = 'g'
    # Felsrand: ueber allen Terrassen
    hp[k == 'h'] = hp_rand[k == 'h'] + 1                              # Nutzer: Berglogik je Variante
    # An jeder Terrassenkante: Pflaster/Wiese enden 2 Reihen vor und nach der Front (kein Weg durch die Wand, kein Ueberstand)
    for (hoehe, seg, (tx0, tx1)) in KANTEN:
        for (x0, x1, ry) in seg:
            for x in range(x0, x1 + 1):
                if tx0 - 1 <= x <= tx1 + 1:
                    continue
                for y in range(ry - 2, ry + 3):
                    if 0 <= y < R and k[y, x] in 'wkn':
                        k[y, x] = 'g'
    for kl in ('n', 'k', 'w'):                                        # Reste (Zungen, Zipfel) angleichen
        for teil in k43.flaechen(k == kl):
            if len(teil) < 8:
                for (y, x) in teil:
                    k[y, x] = 'g'
    # Seitenkanten der Terrassen: Pflaster/Wiese nie ueber eine Hoehengrenze (1 Kachel Abstand auf beiden Seiten)
    hq = hp.copy(); hq[k == 'h'] = 4
    for y in range(R):
        for x in range(C):
            if k[y, x] in 'wkn' and any(0 <= y + dy < R and 0 <= x + dx < C and hq[y + dy, x + dx] != hq[y, x]
                                        and k[y + dy, x + dx] != 'h' for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0))):
                k[y, x] = 'g'
    for kl in ('n', 'k', 'w'):
        for teil in k43.flaechen(k == kl):
            if len(teil) < 8:
                for (y, x) in teil:
                    k[y, x] = 'g'
    # Felsrand links/rechts: kurze 1-Spalten-Einspruenge schliessen (kein Front-Stummel)
    for x, nb in ((2, 1), (C - 3, C - 2)):
        y = 0
        while y < R:
            if k[y, x] != 'h' and k[y, nb] == 'h':
                y0 = y
                while y < R and k[y, x] != 'h' and k[y, nb] == 'h':
                    y += 1
                if y - y0 <= 8 and y0 > 0 and y < R and k[y0 - 1, x] == 'h' and k[y, x] == 'h':
                    k[y0:y, x] = 'h'
            y += 1
    hp[k == 'h'] = hp_rand[k == 'h'] + 1                              # geschlossene Einspruenge gehoeren zum Rand
    # Wiesen der Vorlage, die an den Kanten verloren gingen, ganz auf ihrer Ebene neu anlegen (Baeume der Vorlage)
    for (y0, y1, x0, x1) in ((63, 68, 20, 28), (31, 35, 36, 42)):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if k[y, x] in 'gwk' and hp[y, x] == hp[y0, x0] and not ((y in (y0, y1)) and (x in (x0, x1))):
                    k[y, x] = 'n'
    for _ in range(2):                                                # Finger/Zipfel der Wiesen angleichen
        for y in range(1, R - 1):
            for x in range(1, C - 1):
                if k[y, x] == 'n':
                    gleich = sum(k[y + dy, x + dx] == 'n' for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)))
                    if gleich <= 1 or (k[y, x - 1] != 'n' and k[y, x + 1] != 'n'):
                        k[y, x] = 'g'
    # Treppen: Frontreihe 't', 2 Reihen frei davor/dahinter (kein Rand, kein Gras-Zipfel)
    treppen = []
    for (hoehe, seg, (tx0, tx1)) in KANTEN:
        ry = [r_ for (x0, x1, r_) in seg if x0 <= tx0 <= x1][0]
        for y in range(ry - 2, ry + 3):                                # Pflaster in voller Treppenbreite davor/dahinter
            for x in range(tx0 - 1, tx1 + 2):
                if k[y, x] != 'T':
                    k[y, x] = 'w'
        k[ry, tx0:tx1 + 1] = 't'
        treppen.append([tx0, tx1, ry, 's'])
    # Hoftreppe (von Sueden hinunter nach Norden) liegt im Hof selbst (bauen), kein Pflasterstummel davor
    treppen.append([HOF_TREPPE[0], HOF_TREPPE[1], hy1, 'n'])
    for (tx, ty, b, hh) in TELEPORTER:                                # Ausgaenge in Teleporterbreite durch den Rand
        k[ty:ty + hh, tx:tx + b] = 'T'
        if tx == 0 or tx + b == C:                                      # seitlich: 2 Reihen frei unter der Randfront (K47)
            xs_ = slice(0, b + 3) if tx == 0 else slice(tx - 3, C)
            k[ty - 2:ty, xs_] = np.where(k[ty - 2:ty, xs_] == 'h', 'g', k[ty - 2:ty, xs_])
        if tx == 0:
            hp[ty - 2:ty, 0:b + 3] = hp[ty - 2:ty, b + 3:b + 4]
            k[ty:ty + hh, b:b + 3] = np.where(k[ty:ty + hh, b:b + 3] == 'h', 'g', k[ty:ty + hh, b:b + 3])
            hp[ty:ty + hh, 0:b + 3] = hp[ty:ty + hh, b + 3:b + 4]  # Ebene des Bodens daneben
        elif tx + b == C:
            k[ty:ty + hh, tx - 3:tx] = np.where(k[ty:ty + hh, tx - 3:tx] == 'h', 'g', k[ty:ty + hh, tx - 3:tx])
            hp[ty - 2:ty + hh, tx - 3:C] = hp[ty - 2:ty + hh, tx - 4:tx - 3]
        else:
            k[ty - 3:ty, tx:tx + b] = np.where(k[ty - 3:ty, tx:tx + b] == 'h', 'g', k[ty - 3:ty, tx:tx + b])
            hp[ty - 3:R, tx:tx + b] = 0                                   # unterste Ebene
    if RAND != 'flanke':
        hp[(k != 'h') & (hp > hp_ter)] = hp_ter[(k != 'h') & (hp > hp_ter)]
    lay = {'rand': RAND, 'groesse': [C, R], 'klassen': [''.join(z) for z in k], 'hoehe': [''.join(str(c) for c in z) for z in hp],
           'treppen': treppen, 'hof': list(HOF), 'bruecken': [], 'stege': [],
           'teleporter': [{'x': tx, 'y': ty, 'b': b, 'h': hh} for (tx, ty, b, hh) in TELEPORTER]}
    json.dump(lay, open(os.path.join(KARTE, 'layout.json'), 'w'), indent=0)
    F = {'g': (115, 131, 147), 'w': (170, 170, 165), 'k': (120, 120, 110), 'n': (80, 150, 60), 'h': (210, 215, 225),
         'd': (60, 60, 80), 't': (240, 170, 60), 'T': (80, 220, 240)}
    S_ = 6
    im = Image.new('RGB', (C * S_, R * S_))
    dr = ImageDraw.Draw(im)
    for y in range(R):
        for x in range(C):
            c = np.array(F[k[y, x]]) * (0.7 + 0.1 * min(hp[y, x], 3))
            dr.rectangle((x * S_, y * S_, x * S_ + S_ - 1, y * S_ + S_ - 1), fill=tuple(int(v) for v in np.clip(c, 0, 255)))
    vg = Image.open(VORLAGE).convert('RGB').resize((C * S_, R * S_))
    both = Image.new('RGB', (C * S_ * 2 + 8, R * S_))
    both.paste(vg, (0, 0)); both.paste(im, (C * S_ + 8, 0))
    both.save(os.path.join(KARTE, 'layout_vergleich.png'))
    print('Karte 50 Layout %dx%d' % (C, R))


if __name__ == '__main__':
    main()
