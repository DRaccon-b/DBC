"""Karte 21 - Digi-Egg Valley (A02), Layout nach der Vorlage -> maps/karte21/layout.json

  python3 tools/karte21_layout.py

Vorlage assets/vorlagen/karte21_vorlage.png: 1440x1280 px = 90x80 Kacheln a 16 px. Stil wie Karte 20 / Karte 06.
Oben eine Wiese mit Wegen, quer ein Fluss mit drei Holzbruecken (laeuft links und rechts aus der Karte), darunter
Ruinen, ein grosser Steinplatz mit eingesenktem Schreinhof, die Burgmauer (Front nach Sueden) mit Hoehlentor in der
Mitte und zwei Treppen, unten das Lager auf Sandboden. Wald ringsum, Ausgang oben.

Klassen:  h Wald  g Gras  w Weg/Sand  x Wasser  b Bruecke  p Steinplatz  q Schreinhof (eingesenkt)  s Ruinenplatte
          t Treppe  e Ausgang
Hoehen:   0 Lager (unten), 1 Oberland (Wiese, Platz), 2 Ruinenplatten; Schreinhof liegt eine Stufe tiefer als der Platz.
"""
import json, os
from collections import deque
import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte21')
VORLAGE = os.path.join(ROOT, 'assets', 'vorlagen', 'karte21_vorlage.png')
C, R, T = 90, 80, 16
REF = {'g': (84, 132, 60), 'w': (168, 132, 84), 'h': (84, 108, 60), 'H': (72, 96, 48), 'p': (120, 132, 132),
       'm': (96, 108, 120), 'M': (96, 108, 108), 'x': (48, 132, 132), 'G': (120, 132, 60), 'b': (120, 72, 36)}
MAUER_KANTE = 56            # letzte Reihe des Oberlands; Front (Burgmauer) Reihen 57-59
TREPPEN = [(16, 19), (70, 73)]
TOR = (44, 46)              # Hoehlentor in der Mauer
HOF = (35, 48, 55, 55)      # eingesenkter Schreinhof (x0, y0, x1, y1)
BRUECKEN = [(20, 22), (43, 46), (68, 70)]
FLUSS = (32, 33)            # Wasserreihen
AUSGANG = (43, 0, 46, 1)


def vorlage_klassen():
    a = np.array(Image.open(VORLAGE).convert('RGB')).astype(int)
    k = np.full((R, C), '?')
    for y in range(R):
        for x in range(C):
            m = np.median(a[y * T:(y + 1) * T, x * T:(x + 1) * T].reshape(-1, 3), 0)
            d = {c: np.abs(m - np.array(v)).sum() for c, v in REF.items()}
            c = min(d, key=d.get)
            k[y, x] = c if d[c] < 45 else '?'
    return k


def rand_verbunden(m):
    zu = np.zeros_like(m)
    zu[0, :] = m[0, :]; zu[-1, :] = m[-1, :]; zu[:, 0] = m[:, 0]; zu[:, -1] = m[:, -1]
    while True:
        n = zu | (m & (np.roll(zu, 1, 0) | np.roll(zu, -1, 0) | np.roll(zu, 1, 1) | np.roll(zu, -1, 1)))
        if (n == zu).all():
            return zu
        zu = n


def inseln_weg(k, art, ersatz, mind):
    gesehen = np.zeros(k.shape, bool)
    for y in range(R):
        for x in range(C):
            if k[y, x] == art and not gesehen[y, x]:
                q, teil = deque([(y, x)]), []
                gesehen[y, x] = True
                while q:
                    a_, b_ = q.popleft(); teil.append((a_, b_))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        u, w_ = a_ + dy, b_ + dx
                        if 0 <= u < R and 0 <= w_ < C and k[u, w_] == art and not gesehen[u, w_]:
                            gesehen[u, w_] = True; q.append((u, w_))
                if len(teil) < mind:
                    for (a_, b_) in teil:
                        k[a_, b_] = ersatz


def main():
    os.makedirs(KARTE, exist_ok=True)
    v = vorlage_klassen()
    yy, xx = np.mgrid[0:R, 0:C]
    k = np.full((R, C), 'g')
    wald = rand_verbunden(np.isin(v, ['h', 'H', 'G']))
    k[wald] = 'h'
    k[(v == 'w') | (v == 'b')] = 'w'                       # Wege, Lagersand (Baumstaemme werden Objekte)
    # Fluss: zwei Wasserreihen ueber die ganze Breite (auch durch den Waldrand), Ufer bleiben Sand
    wasser = (v == 'x') | (v == 'b') & (yy >= 27) & (yy <= 35)        # Fluss wie in der Vorlage (Mitte hoeher)
    wasser &= (yy >= 27) & (yy <= 35)
    for y in range(R):                                                   # Wasser bis an den Kartenrand (links/rechts)
        xs = np.nonzero(wasser[y])[0]
        if len(xs) and xs.min() <= 7:
            wasser[y, :xs.min()] = True
        if len(xs) and xs.max() >= C - 8:
            wasser[y, xs.max():] = True
    # Stufen zwischen den Abschnitten schliessen: jede Spalte bekommt mindestens 2 zusammenhaengende Wasserreihen
    for x in range(C):
        ys = np.nonzero(wasser[:, x])[0]
        if len(ys) == 1:
            wasser[ys[0] + 1, x] = True
    k[wasser] = 'x'
    for (x0, x1) in BRUECKEN:
        for x in range(x0, x1 + 1):
            ys = np.nonzero(wasser[:, x])[0]
            k[ys.min() - 1:ys.max() + 2, x] = 'b'
    # Steinflaechen: grosser Platz (Mitte) = p, abseits liegende Platten = Ruinen s
    stein = np.isin(v, ['p', 'm', 'M']) & (yy < MAUER_KANTE + 1) & ~wald
    platz = stein & (xx >= 22) & (xx <= 66) & (yy >= 43)
    k[platz] = 'p'
    # Ruinenplatten auf der mittleren Ebene entfernt (Nutzerwunsch) -> bleibt Gras
    k[HOF[1]:HOF[3] + 1, HOF[0]:HOF[2] + 1] = 'q'
    # Burgmauer: Reihen 57-59 ueber die ganze Breite (Front des Oberlands), Treppen und Tor
    k[MAUER_KANTE + 1:MAUER_KANTE + 4, 3:C - 3] = 'm'
    for (x0, x1) in TREPPEN:
        k[MAUER_KANTE + 1:MAUER_KANTE + 4, x0:x1 + 1] = 't'
        k[MAUER_KANTE - 1:MAUER_KANTE + 1, x0:x1 + 1] = 'w'
        k[MAUER_KANTE + 4:MAUER_KANTE + 6, x0:x1 + 1] = 'w'
    k[MAUER_KANTE + 1:MAUER_KANTE + 4, TOR[0]:TOR[1] + 1] = 'o'           # Hoehlentor
    k[MAUER_KANTE + 4:MAUER_KANTE + 6, TOR[0]:TOR[1] + 1] = 'w'
    x0, y0, x1, y1 = AUSGANG
    k[y0:y1 + 1, x0:x1 + 1] = 'e'
    k[k == '?'] = 'g'
    inseln_weg(k, 'w', 'g', 5)
    inseln_weg(k, 's', 'g', 6)
    h = np.where(yy <= MAUER_KANTE, 1, 0)
    h[k == 's'] = 2
    import regeln_a02                                                 # Regel 6: Wege nie nur gerade
    k = regeln_a02.wege_schwingen(k, seed=21)
    lay = {'groesse': [C, R], 'klassen': [''.join(z) for z in k], 'hoehe': [''.join(str(c) for c in z) for z in h],
           'mauer_kante': MAUER_KANTE, 'treppen': TREPPEN, 'tor': TOR, 'hof': HOF, 'bruecken': BRUECKEN,
           'fluss': FLUSS, 'treppen_sued': [[x0_, x1_, 1, MAUER_KANTE] for (x0_, x1_) in TREPPEN],
           'teleporter': [{'x': AUSGANG[0], 'y': 0, 'b': 4, 'h': 2}]}
    json.dump(lay, open(os.path.join(KARTE, 'layout.json'), 'w'), indent=0)
    F = {'h': (30, 80, 30), 'g': (84, 132, 60), 'w': (192, 168, 108), 'x': (48, 132, 160), 'b': (150, 100, 60),
         'p': (130, 136, 140), 'q': (100, 106, 116), 's': (150, 150, 150), 'm': (70, 76, 90), 't': (200, 200, 200),
         'o': (10, 10, 20), 'e': (80, 220, 240)}
    im = Image.new('RGB', (C * 6, R * 6))
    dr = ImageDraw.Draw(im)
    for y in range(R):
        for x in range(C):
            dr.rectangle((x * 6, y * 6, x * 6 + 5, y * 6 + 5), fill=F[k[y, x]])
    vg = Image.open(VORLAGE).convert('RGB').resize((C * 6, R * 6))
    both = Image.new('RGB', (C * 12 + 8, R * 6))
    both.paste(vg, (0, 0)); both.paste(im, (C * 6 + 8, 0))
    both.save(os.path.join(KARTE, 'layout_vergleich.png'))
    print('Karte 21 Layout %dx%d' % (C, R))


if __name__ == '__main__':
    main()
