"""Karte 24 - The Kaiser's Canyon (A02), Layout nach der Vorlage -> maps/karte24/layout.json

  python3 tools/karte24_layout.py

Vorlage assets/vorlagen/karte24_vorlage.png: 1600x1360 px = 100x85 Kacheln a 16 px. Canyon: rote Felsmassen
(Hochflaeche, nicht begehbar) mit Felsfronten, dazwischen der Canyonboden mit Wegen, Sandflecken und Gruben;
in der Mitte eine erhoehte runde Arena (Treppen unten, Aufgang links), oben rechts ein erhoehter Schrein (Treppe
unten), unten eine Lorenbahn, Teleporter links und rechts.

Klassen:  r Fels (hoch)  b Canyonboden  w Weg  s Sand  x Grube  t Treppe  g Gleis  T Teleporter
Hoehen:   0 Canyonboden, 1 Arena / Schrein, 2 Fels
"""
import json, os
from collections import deque
import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte24')
VORLAGE = os.path.join(ROOT, 'assets', 'vorlagen', 'karte24_vorlage.png')
C, R, T = 100, 85, 16
ARENA = (33, 29, 62, 49)            # Suchbereich der Arena (x0, y0, x1, y1)
SCHREIN = (62, 6, 80, 20)
ARENA_TREPPEN = [(45, 49), (52, 56)]          # (x0, x1) an der Suedkante der Arena
ARENA_LINKS = (39, 43)                        # Aufgang links (Reihen)
SCHREIN_TREPPE = (68, 71)
GLEIS = (9, 88, 75)
TELEPORTER = [(0, 42, 2, 4), (98, 66, 2, 4)]      # nur auf dem Weg, nicht im Fels (Nutzer)


def klassen():
    a = np.array(Image.open(VORLAGE).convert('RGB')).astype(int)
    M = np.zeros((R, C, 3)); S = np.zeros((R, C))
    for y in range(R):
        for x in range(C):
            b = a[y * T:(y + 1) * T, x * T:(x + 1) * T]
            M[y, x] = np.median(b.reshape(-1, 3), 0); S[y, x] = b.std(axis=(0, 1)).mean()
    d = lambda c: np.abs(M - np.array(c)).sum(2)
    k = np.full((R, C), 'b')
    k[S > 20] = 'r'
    k[d((198, 182, 137)) < 40] = 's'
    k[(d((172, 134, 87)) < 25) & (S < 10)] = 'w'
    k[M.sum(2) < 160] = 'x'
    return k


def flaechen(m):
    gesehen = np.zeros_like(m)
    out = []
    for y in range(R):
        for x in range(C):
            if m[y, x] and not gesehen[y, x]:
                q, teil = deque([(y, x)]), []
                gesehen[y, x] = True
                while q:
                    a_, b_ = q.popleft(); teil.append((a_, b_))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        u, v = a_ + dy, b_ + dx
                        if 0 <= u < R and 0 <= v < C and m[u, v] and not gesehen[u, v]:
                            gesehen[u, v] = True; q.append((u, v))
                out.append(teil)
    return out


def main():
    os.makedirs(KARTE, exist_ok=True)
    k = klassen()
    for teil in flaechen(k == 'r'):                  # kleine Felsinseln = Objekte (Obelisken, Felsen) -> Boden
        if len(teil) < 24:
            for (y, x) in teil:
                k[y, x] = 'b'
    for teil in flaechen(k == 'x'):                  # einzelne dunkle Kacheln = Objektschatten -> Boden
        if len(teil) < 4:
            for (y, x) in teil:
                k[y, x] = 'b'
    for teil in flaechen((k != 'r') & (k != 'b')):   # Kleinstflecken Weg/Sand glaetten
        if len(teil) < 3:
            for (y, x) in teil:
                k[y, x] = 'b'
    for (x0, y0, x1, y1) in (ARENA, SCHREIN):        # schmale Felsfinger (Obelisken am Rand) in Arena/Schrein -> Boden
        for _ in range(2):
            for y in range(y0 + 1, y1):
                x = x0
                while x <= x1:
                    if k[y, x] == 'r':
                        e = x
                        while e <= x1 and k[y, e] == 'r':
                            e += 1
                        if e - x <= 2 and x > x0 + 1 and e < x1 - 1:
                            k[y, x:e] = 'b'
                        x = e
                    else:
                        x += 1
    for _ in range(2):                                 # schmale Felsfinger (<= 2 Kacheln breit) ueberall -> Boden
        for y in range(R):
            x = 0
            while x < C:
                if k[y, x] == 'r':
                    e = x
                    while e < C and k[y, e] == 'r':
                        e += 1
                    if e - x <= 2 and x > 0 and e < C:
                        k[y, x:e] = 'b'
                    x = e
                else:
                    x += 1
    gx0, gx1, gy = GLEIS
    k[gy, gx0:gx1 + 1] = 'g'
    yy, xx = np.mgrid[0:R, 0:C]                       # Schrein: achteckige Flaeche wie die Vorlage (Mitte 71/13)
    SX, SY = 70, 12                                   # Schrein groesser (Nutzer)
    okt = (np.abs(xx - SX) <= 9) & (np.abs(yy - SY) <= 7) & (np.abs(xx - SX) + np.abs(yy - SY) <= 12)
    ring = (np.abs(xx - SX) <= 11) & (np.abs(yy - SY) <= 9) & (np.abs(xx - SX) + np.abs(yy - SY) <= 15) & ~okt
    k[ring & (yy < 22)] = 'r'
    k[okt] = np.where(k[okt] == 's', 's', 'b')
    h = np.where(k == 'r', 2, 0)
    # Mitte (Nutzer): Felsblock oberhalb der Arena und Arenaring zu EINER Felsmasse schliessen (keine Rinne dazwischen)
    # nur die Rinne zwischen den beiden Felsmassen schliessen, die Aussenform der Vorlage bleibt (natuerlicher, Nutzer)
    for x in range(36, 65):
        oben = [y for y in range(20, 30) if k[y, x] == 'r']
        unten = [y for y in range(27, 36) if k[y, x] == 'r' and y > (max(oben) if oben else 99)]
        if oben and unten:
            for y in range(max(oben), min(unten)):
                k[y, x] = 'r'
    # Felsblock oben: unregelmaessige, natuerliche Aussenkante statt gerader Linien (Nutzer)
    import math as _m, random as _r
    rr = _r.Random(24)
    for x in range(37, 63):                                       # Nordkante
        top = 23 + int(round(1.2 * _m.sin(x / 2.3) + 0.8 * _m.sin(x / 5.1 + 1) + rr.uniform(-0.6, 0.6)))
        for y in range(20, 29):
            k[y, x] = 'r' if y >= top else ('b' if k[y, x] == 'r' else k[y, x])
    for y in range(22, 30):                                       # Westkante
        left = 39 + int(round(1.3 * _m.sin(y / 1.9) + rr.uniform(-0.7, 0.7)))
        for x in range(35, 43):
            if k[y, x] == 'r' and x < left and y < 29:
                k[y, x] = 'b'
            elif x >= left and y >= 23 + int(round(1.2 * _m.sin(x / 2.3) + 0.8 * _m.sin(x / 5.1 + 1))):
                k[y, x] = 'r'
    for y in range(22, 30):                                       # Ostkante
        right = 61 + int(round(1.2 * _m.sin(y / 1.7 + 2) + rr.uniform(-0.6, 0.6)))
        for x in range(57, 66):
            if x > right and k[y, x] == 'r' and y < 29:
                k[y, x] = 'b'
    # unten links an der Arena mehr Platz (Nutzer): Felsband unter dem Ring oeffnen
    for y in range(49, 53):
        for x in range(31, 45):
            if k[y, x] == 'r':
                k[y, x] = 'b'
    for _ in range(2):                                 # 1 Kachel breite Bodenschlitze zwischen Fels -> Fels
        for y in range(R):
            for x in range(1, C - 1):
                if k[y, x] != 'r' and k[y, x - 1] == 'r' and k[y, x + 1] == 'r' and k[y, x] in 'bs':
                    k[y, x] = 'r'
    for teil in flaechen(k != 'r'):                   # kleine Bodenloecher mitten im Fels -> Fels
        if len(teil) < 16:
            for (y, x) in teil:
                k[y, x] = 'r'
    for teil in flaechen(k == 'r'):                   # nach dem Schliessen: kleine Felsinseln erneut entfernen
        if len(teil) < 24:
            for (y, x) in teil:
                k[y, x] = 'b'
    h[(k == 'r')] = 2
    for (x0, y0, x1, y1) in (ARENA,):                 # erhoehte Flaeche nur die Arena (Schrein ebenerdig, Nutzer): Boden innerhalb des Felsrings
        sub = (k[y0:y1 + 1, x0:x1 + 1] != 'r')
        teile = flaechen(np.pad(sub, ((y0, R - y1 - 1), (x0, C - x1 - 1))))
        gross = max(teile, key=len)
        for (y, x) in gross:
            if y0 < y < y1 and x0 < x < x1:
                h[y, x] = 1
    for (x0, x1) in ARENA_TREPPEN:                    # Treppen: unterste Arenareihe -> 2 Kacheln Treppe in den Fels
        col = [y for y in range(ARENA[1], ARENA[3] + 3) if h[y, (x0 + x1) // 2] == 1]
        yb = max(col)
        k[yb + 1:yb + 3, x0:x1 + 1] = 't'; h[yb + 1:yb + 3, x0:x1 + 1] = 0
        k[yb + 3:yb + 5, x0:x1 + 1] = np.where(k[yb + 3:yb + 5, x0:x1 + 1] == 'r', 'b', k[yb + 3:yb + 5, x0:x1 + 1])
        h[yb + 3:yb + 5, x0:x1 + 1] = 0
    ya, yb_ = ARENA_LINKS                             # Aufgang links: Sandrampe
    xs = [x for x in range(ARENA[0], ARENA[0] + 8) if (h[ya:yb_ + 1, x] == 1).any()]
    xl = min(xs)
    k[ya:yb_ + 1, xl - 3:xl] = 't'; h[ya:yb_ + 1, xl - 3:xl] = 0
    for y in (ya - 2, ya - 1):                        # ueber dem Aufgang eine geschlossene Felskante (keine Taschen)
        for x in range(xl - 8, xl + 2):
            k[y, x] = 'r'; h[y, x] = 2
    x0, x1 = SCHREIN_TREPPE                           # Schrein: statt Treppe ein freier Durchgang (Nutzer)
    for y in range(SCHREIN[1] + 8, SCHREIN[3] + 4):
        for x in range(x0, x1 + 1):
            if k[y, x] == 'r':
                k[y, x] = 'w'; h[y, x] = 0
    # Nutzer: Arena links komplett zu (kein seitlicher Zugang mehr): Aufgang und Spalt mit Fels fuellen
    import math as _m2
    for y in range(37, 49):
        for x in range(30, 36):
            k[y, x] = 'r'; h[y, x] = 2
    # Felsmasse darunter: Oberkante mit Schwenkern statt gerade (Nutzer)
    for x in range(31, 59):
        top = 53 + int(round(0.9 + 0.9 * _m2.sin((x - 31) / 3.4) + 0.4 * _m2.sin(x / 1.6)))
        for y in range(53, top):
            if k[y, x] == 'r':
                k[y, x] = 'b'; h[y, x] = 0
    # Weg unter dem Arenaring zu den Treppen - geschwungen statt gerade
    for y in range(49, 53):
        for x in range(31, 45):
            k[y, x] = 'b'; h[y, x] = 0
    for x in range(27, 50):
        yc = 50.8 + 0.9 * _m2.sin((x - 27) / 3.1) + 0.4 * _m2.sin(x / 1.7)
        for y in (int(round(yc)), int(round(yc)) + 1):
            if 0 <= y < R and h[y, x] == 0 and k[y, x] in 'bsw':
                k[y, x] = 'w'
    # Abschluss (Nutzer: Flaechen fuellen): Klassen und Hoehen angleichen, Felsinseln und Bodentaschen entfernen
    h[(k != 'r') & (h == 2)] = 0
    h[(k == 'r')] = 2
    for _ in range(2):
        for teil in flaechen((h == 2)):
            if len(teil) < 24:
                for (y, x) in teil:
                    k[y, x] = 'b'; h[y, x] = 0
        for teil in flaechen((h == 0)):
            if len(teil) < 24:
                for (y, x) in teil:
                    k[y, x] = 'r'; h[y, x] = 2
        for y in range(R):                              # 1 Kachel breite Bodenkerben am Fels schliessen
            for x in range(1, C - 1):
                if h[y, x] == 0 and k[y, x] in 'bs' and h[y, x - 1] == 2 and h[y, x + 1] in (1, 2):
                    k[y, x] = 'r'; h[y, x] = 2
    for (y0, y1, x0, x1) in ((19, 23, 71, 78), (29, 33, 56, 63)):   # Taschen am Schrein und oben rechts an der Arena
        for y in range(y0, y1):
            for x in range(x0, x1):
                if h[y, x] == 0 and k[y, x] in 'bs':
                    k[y, x] = 'r'; h[y, x] = 2
    # Schrein wieder erhoeht mit Treppe (Nutzer), ordentlich: Plateau mit durchgehender Front nach Sueden,
    # davor ein Vorplatz auf Bodenhoehe, kein Sand auf dem Plateau, keine Absaetze neben der Treppe
    k[okt] = 'b'
    h[okt] = 1
    yb = max(y for y in range(R) if okt[y, SX])
    for y in range(yb + 1, yb + 5):                    # Vorplatz unter dem Schrein (Bodenhoehe)
        for x in range(SX - 7, SX + 8):
            k[y, x] = 'b'; h[y, x] = 0
    for y in range(SY + 3, yb + 1):                    # Felsring nur oben und an den Seiten, unten frei fuer die Front
        for x in range(SX - 12, SX + 13):
            if ring[y, x] and not okt[y, x] and abs(x - SX) <= 9:
                k[y, x] = 'b'; h[y, x] = 0
    x0, x1 = SCHREIN_TREPPE
    k[yb + 1:yb + 3, x0:x1 + 1] = 't'; h[yb + 1:yb + 3, x0:x1 + 1] = 0
    for y in range(yb + 3, yb + 5):
        for x in range(x0, x1 + 1):
            k[y, x] = 'w'
    # Platz fuer 2x4 Teleporter (Nutzer): Fels darueber 2 Reihen zurueck, rechts unten 1 Reihe weg
    for (x0_, x1_, ys_) in ((0, 7, (40, 41)), (93, 100, (64, 65, 69))):
        for y in ys_:
            for x in range(x0_, x1_):
                k[y, x] = 'w'; h[y, x] = 0
    for (tx, ty, b, hh) in TELEPORTER:
        k[ty:ty + hh, tx:tx + b] = 'T'; h[ty:ty + hh, tx:tx + b] = 0
    lay = {'groesse': [C, R], 'klassen': [''.join(z) for z in k], 'hoehe': [''.join(str(c) for c in z) for z in h],
           'arena_treppen': ARENA_TREPPEN, 'arena_links': ARENA_LINKS, 'schrein_treppe': SCHREIN_TREPPE,
           'gleis': GLEIS, 'teleporter': [{'x': tx, 'y': ty, 'b': b, 'h': hh} for (tx, ty, b, hh) in TELEPORTER]}
    json.dump(lay, open(os.path.join(KARTE, 'layout.json'), 'w'), indent=0)
    F = {'r': (120, 60, 30), 'b': (200, 130, 90), 's': (230, 215, 160), 'w': (170, 140, 90), 'x': (20, 10, 10),
         't': (240, 240, 240), 'g': (60, 60, 90), 'T': (80, 220, 240)}
    S_ = 6
    im = Image.new('RGB', (C * S_, R * S_))
    dr = ImageDraw.Draw(im)
    for y in range(R):
        for x in range(C):
            c = np.array(F[k[y, x]], float) * (1.0 + 0.18 * (h[y, x] == 1))
            dr.rectangle((x * S_, y * S_, x * S_ + S_ - 1, y * S_ + S_ - 1), fill=tuple(np.clip(c, 0, 255).astype(int)))
    vg = Image.open(VORLAGE).convert('RGB').resize((C * S_, R * S_))
    both = Image.new('RGB', (C * S_ * 2 + 8, R * S_))
    both.paste(vg, (0, 0)); both.paste(im, (C * S_ + 8, 0))
    both.save(os.path.join(KARTE, 'layout_vergleich.png'))
    print('Karte 24 Layout %dx%d' % (C, R))


if __name__ == '__main__':
    main()
