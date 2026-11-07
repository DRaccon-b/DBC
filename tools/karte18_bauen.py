"""Karte 18 (The Fog-Bound City): Hafenstadt am Abend im Nebel - Gelaende, Hochbahn, Objekte, Animation (4 Bilder).

  python3 tools/karte18_layout.py && python3 tools/karte18_kacheln.py && python3 tools/karte18_gebaeude.py
  python3 tools/karte18_bauen.py && python3 tools/karte18_objekte.py && python3 tools/karte18_bauen.py

Ebenen (Zeichenreihenfolge): Boden (Kacheln, Bordsteine, Markierungen, Rasen, Hecken, Terrasse, Gleise, Kai, Wasser,
Steg) -> Lichtkegel der Laternen -> Schatten -> Objekte und Gebaeude (nach Fusshoehe) -> Hochbahn (Fahrbahn, Front,
Zug; die Pfeiler sind Objekte auf dem Mittelstreifen) -> Nebel (liegt ueber dem Rand, Wellen und Nebel bewegen sich).
"""
import json, math, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageFilter
import karte_bauen as kb
import karte04_bauen as k4
import karte08_bauen as k8

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte18')
BASIS = os.path.join(ROOT, 'assets', 'karte18', 'basis')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte18')
T = 16
N_FRAMES = 4                     # Regel: hoechstens 4 Animationsbilder
BILDDAUER = 250
k4.N_FRAMES = N_FRAMES
H = k4.H
NEBEL = np.array(H('#9892b0'), np.float32)
WEISS = np.array(H('#c8ccd6'), np.float32)
GELB = np.array(H('#c8a848'), np.float32)
HECKE18 = ['#1c2c20', '#24382a', '#2e4632', '#3a563c', '#4a6a48', '#5c7e54', '#6e905e']


def textur(art, cols, rows):
    t = np.zeros((rows * T, cols * T, 3), np.uint8)
    ks = [np.array(Image.open(os.path.join(BASIS, '%s_%d.png' % (art, v))).convert('RGB')) for v in range(5)]
    for y in range(rows):
        for x in range(cols):
            t[y * T:(y + 1) * T, x * T:(x + 1) * T] = ks[kb.variante(x, y)]
    return t


def kontur(m):
    return m & ~(np.roll(m, 1, 0) & np.roll(m, -1, 0) & np.roll(m, 1, 1) & np.roll(m, -1, 1))


def mischen(a, m, farbe, s):
    a[m] = np.clip(a[m] * (1 - s) + np.asarray(farbe, np.float32) * s, 0, 255).astype(np.uint8)


def dunkeln(a, m, f):
    a[m] = (a[m].astype(np.float32) * f).astype(np.uint8)


def gross(m):
    return np.kron(m, np.ones((T, T), int)).astype(bool)


# ---------------------------------------------------------------------------------------------- Strassen
def bordsteine(a, asphalt, boden):
    """Bordstein: 2 px helle Kante auf der Gehwegseite, darunter 1 px dunkle Fuge; die Fahrbahn bekommt an der
    Nord- und Westkante einen weichen Schatten (Licht von oben links)."""
    um = boden & ~asphalt
    nah = np.zeros_like(asphalt)
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nah |= np.roll(np.roll(asphalt, dy, 0), dx, 1)
    kante = um & nah
    a[kante] = H('#9aa0ae')
    zweite = um & ~kante
    nah2 = np.zeros_like(asphalt)
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nah2 |= np.roll(np.roll(kante, dy, 0), dx, 1)
    a[zweite & nah2] = H('#7a8090')
    sch = asphalt & (np.roll(kante, 1, 0) | np.roll(kante, 1, 1))
    dunkeln(a, sch, 0.7)
    sch2 = asphalt & (np.roll(kante, 2, 0) | np.roll(kante, 2, 1)) & ~sch
    dunkeln(a, sch2, 0.85)


def linie_h(a, asphalt, y, x0, x1, farbe, strich=0, luecke=0, dicke=2):
    for x in range(x0, x1):
        if strich and (x - x0) % (strich + luecke) >= strich:
            continue
        for d in range(dicke):
            if asphalt[y + d, x]:
                a[y + d, x] = farbe


def linie_v(a, asphalt, x, y0, y1, farbe, strich=0, luecke=0, dicke=2):
    for y in range(y0, y1):
        if strich and (y - y0) % (strich + luecke) >= strich:
            continue
        for d in range(dicke):
            if asphalt[y, x + d]:
                a[y, x + d] = farbe


def pfeil(a, cx, cy, richtung):
    """Fahrbahnpfeil (weiss, verblasst), richtung +1 nach Osten, -1 nach Westen."""
    for i in range(10):
        a[cy, cx + richtung * i] = WEISS * 0.85
    for d in range(4):
        a[cy - d, cx + richtung * (9 - d)] = WEISS * 0.85
        a[cy + d, cx + richtung * (9 - d)] = WEISS * 0.85


def markierungen(a, asphalt, lay):
    """Mittellinien, Fahrstreifen, Pfeile, Zebrastreifen, Parkbuchten."""
    zebra = np.zeros_like(asphalt)
    for (x0, x1, y0, y1, art) in lay['zebra']:
        zebra[y0 * T:(y1 + 1) * T, x0 * T:(x1 + 1) * T] = True
    frei = asphalt & ~zebra
    gelb = GELB.astype(np.uint8)
    weiss = (WEISS * 0.9).astype(np.uint8)
    # obere Strasse: gelbe Doppellinie in der Mitte (Reihe 20..24 -> Mitte 22.5)
    y = int(22.5 * T)
    linie_h(a, frei, y - 3, 3 * T, 83 * T, gelb, dicke=1)
    linie_h(a, frei, y + 2, 3 * T, 83 * T, gelb, dicke=1)
    # Querstrasse: gelbe Strichlinie (x 32..36 -> Mitte 34.5)
    linie_v(a, frei, int(34.5 * T) - 1, 25 * T, 96 * T, gelb, strich=10, luecke=8)
    # mittlere Strasse: je Fahrbahn weisse Strichlinie (Reihen 42..46 und 49..53)
    for yc in (44.5, 51.5):
        linie_h(a, frei, int(yc * T) - 1, 3 * T, 63 * T, weiss, strich=12, luecke=10)
    # Uferstrasse: Fahrbahn Nord 84..86, Sued 89..93
    linie_h(a, frei, int(85.5 * T) - 1, 32 * T, 126 * T, weiss, strich=12, luecke=10)
    for yc in (90.5, 92.0):
        linie_h(a, frei, int(yc * T) - 1, 32 * T, 126 * T, weiss, strich=12, luecke=10)
    for (cx, cy, r) in ((22 * T, int(21.4 * T), 1), (58 * T, int(23.6 * T), -1), (8 * T, int(43.3 * T), 1),
                        (46 * T, int(52.6 * T), -1), (70 * T, int(84.8 * T), 1), (118 * T, int(91.4 * T), -1)):
        pfeil(a, cx, cy, r)
    # Zebrastreifen: 'v' = Streifen quer zur Strasse (Strasse waagerecht), 'h' = Strasse senkrecht
    for (x0, x1, y0, y1, art) in lay['zebra']:
        for y in range(y0 * T, (y1 + 1) * T):
            for x in range(x0 * T, (x1 + 1) * T):
                if not asphalt[y, x]:
                    continue
                if art == 'v' and (y % 8) < 5 and 3 <= x - x0 * T < (x1 - x0 + 1) * T - 3:
                    a[y, x] = weiss
                if art == 'h' and (x % 8) < 5 and 3 <= y - y0 * T < (y1 - y0 + 1) * T - 3:
                    a[y, x] = weiss
    # Parkplatz: Buchten (Linien alle 3 Kacheln), Mittelgasse
    for x in range(42, 61, 3):
        linie_v(a, frei, x * T + 7, 29 * T + 2, 31 * T + 12, weiss, dicke=1)
        linie_v(a, frei, x * T + 7, 35 * T + 4, 38 * T - 2, weiss, dicke=1)
    linie_h(a, frei, 33 * T + 7, 42 * T, 61 * T, (GELB * 0.8).astype(np.uint8), strich=8, luecke=8, dicke=1)


# ---------------------------------------------------------------------------------------------- Flaechen
def rasen_kanten(a, rasen):
    """Rasen mit Steinkante: 1 px heller Randstein aussen, innen eine dunkle Erdfuge."""
    rand = kontur(rasen)
    a[rand] = H('#8a8e98')
    innen = kontur(rasen & ~rand)
    dunkeln(a, innen, 0.72)


def mittelstreifen(a, m):
    """Mittelstreifen: Bordstein ringsum, darin eine niedrige Hecke (Licht oben links, unten dunkle Blattfront)."""
    rand = kontur(m)
    a[m] = H('#3a3a30')
    a[rand] = H('#9aa0ae')
    innen = m & ~rand & ~kontur(m & ~rand)
    alt = k4.HECKE
    k4.HECKE = HECKE18
    k4.hecke(a, innen, 18)
    k4.HECKE = alt
    unten = innen & ~np.roll(innen, -1, 0)
    for d in range(2):
        dunkeln(a, np.roll(unten, -d, 0) & innen, 0.7)


def platz_raster(a, platz, achse):
    """Grosser Platz: dunklere Fugenbaender im 8-Kachel-Raster, symmetrisch zur Achse der Halle."""
    Hh, W = platz.shape
    ax = achse * T
    for x in range(W):
        if (x - ax) % (8 * T) in (0, 1):
            m = platz[:, x]
            a[m, x] = (a[m, x] * 0.82).astype(np.uint8)
    for y in range(Hh):
        if (y - 36 * T) % (8 * T) in (0, 1):
            m = platz[y]
            a[y, m] = (a[y, m] * 0.82).astype(np.uint8)


def kompass(a, cx, cy):
    """Bodenmedaillon (Windrose) in der Mitte des Mittelwegs: zwei Ringe, vier Spitzen, roter Kern."""
    yy, xx = np.mgrid[-24:25, -24:25]
    d = np.hypot(xx, yy)
    for (r, c) in ((22, '#5e5672'), (20, '#aaa4c0'), (14, '#5e5672')):
        m = np.abs(d - r) <= 0.8
        a[cy - 24:cy + 25, cx - 24:cx + 25][m] = H(c)
    for (sx, sy) in ((0, -1), (1, 0), (0, 1), (-1, 0)):
        for i in range(18):
            b = max(0, 3 - i // 5)
            for j in range(-b, b + 1):
                X = cx + sx * i + (j if sx == 0 else 0)
                Y = cy + sy * i + (j if sy == 0 else 0)
                a[Y, X] = H('#d0cad8') if (j <= 0) else H('#7e7692')
    a[cy - 2:cy + 3, cx - 2:cx + 3] = H('#b03a40')
    a[cy - 1:cy + 1, cx - 1:cx + 1] = H('#e06058')


def terrasse(a, lay, lvl):
    """Terrasse vor der Halle (Ebene 2): 16 px Front (Steinplatten, Lichtkante oben, Kontaktschatten), mittig die
    breite Treppe (12 Kacheln, Achse der Halle); Seitenkanten nur als schmale Kontur."""
    x0, x1, ry = lay['treppe_terrasse']
    kl = np.array([list(r) for r in lay['klassen']])
    ter = gross(kl == 't')
    ys = ry * T
    xs = np.nonzero(ter[ys - 1])[0]
    tx0, tx1 = x0 * T, (x1 + 1) * T
    for x in range(xs.min(), xs.max() + 1):
        for d in range(16):
            Y = ys + d
            if tx0 <= x < tx1:
                st = d % 4                                      # 4 Stufen: Trittkante hell, Setzstufe dunkel
                c = H('#c4bed8') if st == 0 else H('#a49eba') if st == 1 else H('#7a7494') if st == 2 else H('#4e4866')
                if x in (tx0, tx1 - 1):
                    c = H('#4a4460')
            else:
                c = H('#8a84a2') if d < 2 else H('#6e6888') if d < 13 else H('#4c4664')
                if (x // 16) % 2 == 0 and d == 7:
                    c = H('#625c7c')
                if x % 32 == 31 and 2 <= d < 13:
                    c = H('#565070')
            a[Y, x] = c
            lvl[Y, x] = 9 if not (tx0 <= x < tx1) else 2
        if not (tx0 <= x < tx1):
            dunkeln(a, (np.s_[ys + 16:ys + 18], np.s_[x]), 0.75)
    a[ys - 1, xs.min():xs.max() + 1] = H('#c2bcd4')               # Lichtkante an der Oberkante
    for x in (xs.min(), xs.max()):                                # Seitenkanten: Kontur
        col = ter[:, x]
        a[col, x] = H('#5a5470')


def gleise(a, lay):
    """Gleis am Kai: zwei Schienen (Licht oben), Schwellen sind in der Kachel."""
    y0 = 96 * T
    for yr in (y0 + 7, y0 + 23):
        a[yr, 4 * T:126 * T] = H('#b0b4bc')
        a[yr + 1, 4 * T:126 * T] = H('#6a6e78')
        a[yr + 2, 4 * T:126 * T] = H('#2a2a30')


def kaimauer(a, wasser, land, lvl):
    """Kaimauer: unter der Kaikante faellt eine 14 px Steinwand ins Wasser (Front nach Sueden); am Kanal gibt es eine
    Front an der Nordkante und schmale Seitenkonturen."""
    Hh, W = wasser.shape
    sued = land & np.roll(wasser, -1, 0)
    for y, x in zip(*np.nonzero(sued)):
        for d in range(14):
            Y = y + 1 + d
            if Y >= Hh or not wasser[Y, x]:
                break
            if d < 2:
                c = H('#7a7e8c')
            elif d < 12:
                c = H('#5a5e6c') if ((x + (8 if (d // 6) % 2 else 0)) % 16) != 15 else H('#3a3e4a')
                if d == 7:
                    c = H('#4a4e5a')
            else:
                c = H('#2e3444')                                  # Wasserlinie (nass, dunkel)
            a[Y, x] = c
            lvl[Y, x] = 9
    seite = land & (np.roll(wasser, 1, 1) | np.roll(wasser, -1, 1))
    a[seite] = H('#4a4e5a')


def wasser_wellen(a, wasser, frame, seed=18):
    """Wasser: dunkles Nachtblau, nach unten etwas heller (Nebel), helle Wellenstriche wandern je Bild 4 px nach
    rechts (Periode 16 px -> 4 Bilder nahtlos); ueber Wand und Steg wird nicht gezeichnet."""
    f = frame or 0
    Hh, W = wasser.shape
    rs = random.Random(seed)
    for _ in range(int(wasser.sum() / 90)):
        ys, xs = np.nonzero(wasser[::4, ::16])
        i = rs.randrange(len(ys))
        y, x = int(ys[i]) * 4 + rs.randint(0, 3), int(xs[i]) * 16 + rs.randint(0, 15)
        lang = rs.choice((3, 4, 5))
        for k_ in range(lang):
            X = x + k_ + 4 * f
            X = (X - x) % 16 + x if False else X
            if 0 <= X < W and wasser[y, X]:
                a[y, X] = H('#3a4a7a') if k_ in (0, lang - 1) else H('#5a6a9a')


def steg(a, lay, wasser, lvl):
    """Holzsteg: Planken (Kachel), seitlich dunkle Kontur, Suedfront 6 px Holz mit Pfaehlen ins Wasser, Schatten
    auf dem Wasser nach rechts unten."""
    x0, y0, x1, y1 = lay['steg']
    X0, X1, Y1 = x0 * T, (x1 + 1) * T, (y1 + 1) * T
    a[y0 * T:Y1, X0] = H('#3a2616'); a[y0 * T:Y1, X1 - 1] = H('#3a2616')
    for d in range(10):
        for x in range(X0, X1):
            if d < 6:
                a[Y1 + d, x] = H('#5a3c24') if d > 0 else H('#8a6440')
            elif (x - X0) % 24 in range(2, 6):
                a[Y1 + d, x] = H('#3a2818')
            lvl[Y1 + d, x] = 9
    for x in range(X0 + 2, X1 - 2, 24):
        for y in range(y0 * T + 8, Y1, 32):
            a[y, x:x + 3] = H('#2a1a10')                          # Pollerloecher/Pfahlkoepfe
    sch = np.zeros_like(wasser)
    sch[y0 * T + 4:Y1 + 10, X1:X1 + 6] = True
    dunkeln(a, sch & wasser, 0.65)


def teleporter(a, tp, frame):
    """Violette Teleporter-Ringe wie in der Vorlage: dunkle Fassung, violetter Ring, heller Kern pulsiert."""
    f = frame or 0
    p = (0.75, 0.9, 1.05, 0.9)[f % 4]
    for j in range(tp['h']):
        for i in range(tp['b']):
            cx, cy = (tp['x'] + i) * T + 8, (tp['y'] + j) * T + 8
            for yy in range(-7, 8):
                for xx in range(-7, 8):
                    d = math.hypot(xx, yy * 1.1)
                    if d > 7:
                        continue
                    if d > 5.6:
                        c = np.array(H('#2a2038'), np.float32)
                    elif d > 3.6:
                        c = np.array(H('#8a5ad0'), np.float32) * p
                    elif d > 2:
                        c = np.array(H('#3a2a58'), np.float32)
                    else:
                        c = np.array(H('#d0b0ff'), np.float32) * p
                    if yy < -3 and 3.6 < d <= 5.6:
                        c = c * 1.15
                    a[cy + yy, cx + xx] = np.clip(c, 0, 255).astype(np.uint8)


# ---------------------------------------------------------------------------------------------- Nebel
def nebel_feld(Hh, W, periode, seed, gross_):
    """Weiches Rauschen, waagerecht periodisch (Periode in px) - verschoben um periode/4 je Bild laeuft es nahtlos."""
    rs = np.random.RandomState(seed)
    n = rs.rand(Hh // gross_ + 2, periode // gross_)
    n = np.concatenate([n, n[:, :1]], axis=1)
    m = np.array(Image.fromarray((n * 255).astype(np.uint8)).resize((periode + periode // (periode // gross_), Hh + 2 * gross_),
                                                                     Image.BICUBIC)).astype(np.float32) / 255
    m = m[:Hh, :periode]
    return np.tile(m, (1, W // periode + 1))[:, :W]


def nebel(a, land, frame):
    """Dichter Nebel ausserhalb der Stadt: deckt den Rand weich ab (ueber 2 Kacheln ausgeblendet), zwei Schwaden-
    Schichten ziehen langsam nach rechts (je Bild 16 bzw. 8 px, Perioden 64/32 px -> nahtlos in 4 Bildern)."""
    f = frame or 0
    Hh, W = land.shape
    weit = np.array(Image.fromarray((land * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(10))).astype(np.float32) / 255
    dichte = np.clip((1.0 - weit) * 2.6, 0, 1) ** 1.2             # 1 im Nebel, faellt zum Land hin weich ab (~2 Kacheln)
    dichte[~land] = np.maximum(dichte[~land], 0.82)
    n1 = np.roll(nebel_feld(Hh, W, 64, 81, 16), 16 * f, axis=1)
    n2 = np.roll(nebel_feld(Hh, W, 32, 82, 8), 8 * f, axis=1)
    schwade = 0.62 + 0.28 * n1 + 0.12 * n2
    s_ = np.clip(dichte * schwade, 0, 1)[..., None]
    farbe = NEBEL[None, None, :] * (0.9 + 0.16 * n1[..., None] + 0.05 * n2[..., None])
    a[:] = np.clip(a * (1 - s_) + farbe * s_, 0, 255).astype(np.uint8)


# ---------------------------------------------------------------------------------------------- Hochbahn
def hochbahn(img, lay, frame, zug_sp=None):
    """Hochbahn ueber der Uferstrasse: Fahrbahn (Oberseite mit Fuehrungsschiene, Gelaender), 32 px Front aus hellem
    Beton mit dunklen Fugen im Pfeilerraster, Abschlussblock im Westen; Zug steht auf der Fahrbahn. Liegt ueber allem,
    was darunter und dahinter ist (Platzrand, Gehweg)."""
    hb = lay['hochbahn']
    a = np.array(img)
    X0, X1 = hb['x0'] * T, (hb['x1'] + 1) * T
    y0 = hb['y0'] * T
    for y in range(y0, y0 + 32):                                  # Oberseite (2 Kacheln)
        d = y - y0
        for x in range(X0, X1):
            if d < 2:
                c = H('#aeb2c0')                                  # Gelaender oben (Licht)
            elif d < 4:
                c = H('#6a6e7c')
            elif 13 <= d <= 18:
                c = H('#8a8e9a') if d in (13, 18) else H('#c0c4ce')   # Fuehrungsschiene (Beton)
            else:
                c = H('#7c808e') if (x // 32) % 2 else H('#787c8a')
            if d == 30:
                c = H('#9a9eac')
            a[y, x, :3] = c
            a[y, x, 3] = 255
    for y in range(y0 + 32, y0 + 64):                             # Front (2 Kacheln)
        d = y - y0 - 32
        for x in range(X0, X1):
            c = H('#9a9eaa') if d < 3 else H('#82869a') if d < 26 else H('#5a5e6e')
            if d == 3 or ((x - X0) % 256 in (0, 1) and d >= 3):
                c = H('#4e5262')
            if 10 <= d <= 12:
                c = H('#6e7284')
            a[y, x, :3] = c
            a[y, x, 3] = 255
    for y in range(y0, y0 + 64):                                  # Westlicher Abschluss: dunkle Stirnkante
        a[y, X0:X0 + 2, :3] = H('#3a3e4c')
    img = Image.fromarray(a)
    if zug_sp is not None:
        zx0, zx1 = hb['zug']
        img.alpha_composite(zug_sp, (zx0 * T, y0 + 22 - zug_sp.height))      # Schuerze sitzt auf dem Fahrbalken
    return img


def schatten_hochbahn(a, lay, boden):
    """Schatten der Hochbahn faellt nach rechts unten auf die Fahrbahn darunter (nur auf den Boden)."""
    hb = lay['hochbahn']
    y = (hb['y1'] + 1) * T
    m = np.zeros(boden.shape, bool)
    m[y:y + 14, hb['x0'] * T + 10:(hb['x1'] + 1) * T] = True
    dunkeln(a, m & boden, 0.72)


def gebaeude_schatten(img, geb, lvl):
    """Gebaeudeschatten (Licht von oben links): rechts neben dem Gebaeude ein nach unten auslaufender Streifen,
    unter der Fassade ein schmaler Kontaktschatten - nur auf dem Boden der Grundebene (nicht auf Wasser/Terrasse)."""
    a = np.array(img).astype(np.float32)
    Hh, W = lvl.shape
    m = np.zeros((Hh, W), np.float32)
    for o in geb:
        x0, y0, x1, y1 = o['gebaeude']
        X0, X1, Y1 = x0 * T, (x1 + 1) * T, (y1 + 1) * T
        hoch = min(6 * T, (y1 - y0 + 1) * T)
        for y in range(Y1 - hoch, Y1 + 8):                       # rechts: 12 px, unten schraeg auslaufend
            if not (0 <= y < Hh):
                continue
            ende = X1 + 12 - max(0, y - Y1) * 1
            m[y, X1:min(W, ende)] = np.maximum(m[y, X1:min(W, ende)], 0.3)
        m[Y1:min(Hh, Y1 + 5), X0 + 4:min(W, X1 + 8)] = np.maximum(m[Y1:min(Hh, Y1 + 5), X0 + 4:min(W, X1 + 8)], 0.32)
        m[Y1:min(Hh, Y1 + 2), X0 + 2:min(W, X1 + 10)] = np.maximum(m[Y1:min(Hh, Y1 + 2), X0 + 2:min(W, X1 + 10)], 0.42)
    m[lvl != 1] = 0
    a[..., :3] *= (1 - m[..., None])
    img.paste(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)))


def lichtkegel(img, lampen, cache, frame):
    """Warmer Lichtkreis der Laternen auf dem Boden (vor den Objekten gezeichnet), Helligkeit atmet in 4 Bildern."""
    a = np.array(img).astype(np.float32)
    f = (frame or 0) % 4
    for o in lampen:
        sp = cache[o['datei']]
        cx = o['x'] + sp.width / 2.0
        cy = o['y'] + o['fuss'] - 2
        k_ = (0.9, 1.0, 1.06, 1.0)[(f + int(o['x']) // 40) % 4]
        x0, x1, y0, y1 = int(cx - 22), int(cx + 23), int(cy - 10), int(cy + 11)
        yy, xx = np.mgrid[y0:y1, x0:x1]
        d = ((xx - cx) / 22.0) ** 2 + ((yy - cy) / 10.0) ** 2
        s_ = np.clip(1 - d, 0, 1) ** 1.4 * 0.34 * k_
        ok = (yy >= 0) & (yy < a.shape[0]) & (xx >= 0) & (xx < a.shape[1])
        Y, X, S = yy[ok], xx[ok], s_[ok][:, None]
        a[Y, X, :3] = a[Y, X, :3] * (1 - S) + np.array([250, 214, 150]) * S
    img.paste(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)))


def laterne18(sp, frame, o):
    """Lampenkopf leuchtet und atmet leicht (warme helle Pixel), Mast bleibt unveraendert."""
    a = np.array(sp)
    ai = a.astype(int)
    m = (ai[..., 3] > 0) & (ai[..., 0] > 170) & (ai[..., 1] > 130) & (ai[..., 0] >= ai[..., 2])
    k_ = (0.88, 1.0, 1.1, 1.0)[((frame or 0) + int(o.get('x', 0)) // 40) % 4]
    a[m, :3] = np.clip(ai[m, :3] * k_, 0, 255).astype(np.uint8)
    return Image.fromarray(a)


def leuchten18(sp, frame, o):
    """Automaten, Ampeln, Reklame: gesaettigte helle Pixel pulsieren leicht (4 Bilder), Gehaeuse bleibt ruhig."""
    a = np.array(sp)
    ai = a.astype(int)
    mx, mn = ai[..., :3].max(axis=2), ai[..., :3].min(axis=2)
    m = (ai[..., 3] > 0) & (mx > 170) & (mx - mn > 70)
    k_ = (0.86, 1.0, 1.12, 1.0)[((frame or 0) + int(o.get('x', 0)) // 48) % 4]
    a[m, :3] = np.clip(ai[m, :3] * k_, 0, 255).astype(np.uint8)
    return Image.fromarray(a)


def boot(sp, frame, o):
    """Boot schaukelt auf dem Wasser: hebt und senkt sich als Ganzes um 1 px."""
    d = (0, 1, 0, -1)[(frame or 0) % 4]
    out = Image.new('RGBA', sp.size)
    out.paste(sp, (0, d))
    return out


k4.TEILANIM.update({'laterne18': laterne18, 'automat': leuchten18, 'ampel18': leuchten18, 'reklame': leuchten18,
                    'boot': boot})


# ---------------------------------------------------------------------------------------------- Bau
def bauen(frame=None, speichern=True):
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cols, rows = lay['groesse']
    Wp, Hp = cols * T, rows * T
    kl = np.array([list(r) for r in lay['klassen']])
    a = textur('nebel', cols, rows)
    for art in 'gpqctndxbkhs':
        m = gross(kl == art)
        a[m] = textur(art, cols, rows)[m]
    wasser = gross(kl == 'w')
    a[wasser] = textur('w', cols, rows)[wasser]
    land = gross(kl != '.') & ~wasser
    asphalt = gross(np.isin(kl, ['s', 'x']))
    lvl = np.zeros((Hp, Wp), np.uint8)
    lvl[land] = 1
    lvl[gross(kl == 't')] = 2
    bordsteine(a, asphalt, land)
    markierungen(a, asphalt, lay)
    rasen_kanten(a, gross(np.isin(kl, ['n', 'd'])))
    sand = gross(kl == 'd')
    a[kontur(sand)] = H('#8a6a44')                                 # Holzeinfassung des Sandkastens
    mittelstreifen(a, gross(kl == 'm'))
    lvl[gross(kl == 'm')] = 9                                      # Hecke: nicht begehbar
    platz_raster(a, gross(kl == 'p'), lay['achse'])
    kompass(a, lay['kompass'][0] * T, lay['kompass'][1] * T)
    terrasse(a, lay, lvl)
    gleise(a, lay)
    kaimauer(a, wasser, land, lvl)
    wasser_wellen(a, wasser & (lvl != 9), frame)
    steg(a, lay, wasser, lvl)
    for tp in lay['teleporter']:
        teleporter(a, tp, frame)
    schatten_hochbahn(a, lay, land)
    lvl[wasser & (lvl != 9)] = 0
    lvl[gross(kl == 'h')] = 1
    if speichern and frame is None:
        np.save(os.path.join(KARTE, 'pixelhoehe.npy'), lvl)
        np.save(os.path.join(KARTE, 'wasser.npy'), np.packbits(wasser & (lvl == 0)))
        np.save(os.path.join(KARTE, 'leere.npy'), np.packbits(gross(kl == '.')))
    nebel(a, land | wasser, frame)                                 # Nebel liegt am Boden: Hohes ragt heraus
    img = Image.fromarray(a).convert('RGBA')
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain_basis.png'))
    zug = None
    pf = os.path.join(OBJ, 'platzierung.json')
    if os.path.exists(pf):
        objs = sorted((o for o in json.load(open(pf)) if os.path.exists(os.path.join(OBJ, o['datei']))),
                      key=lambda o: o.get('sortier', o['y'] + o['fuss']))
        cache = {o['datei']: Image.open(os.path.join(OBJ, o['datei'])).convert('RGBA') for o in objs}
        k8.schatten_ebene(img, [o for o in objs if not o.get('kein_schatten')], cache, lvl)
        gebaeude_schatten(img, [o for o in objs if o.get('gebaeude')], lvl)
        lichtkegel(img, [o for o in objs if o.get('anim') == 'laterne18'], cache, frame)
        k4.objekte_zeichnen(img, [o for o in objs if not o.get('hochbahn')], cache, np.zeros((Hp, Wp), bool), frame)
        img = img.copy()
        k4.animieren(img, [o for o in objs if not o.get('hochbahn')], cache, frame or 0, ruhig=frame is None)
        zuege = [o for o in objs if o.get('hochbahn')]
        if zuege:
            zug = cache[zuege[0]['datei']]
    img = hochbahn(img, lay, frame, zug)
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain.png'))
    print('Karte 18 %dx%d gebaut' % (cols, rows))
    return img


if __name__ == '__main__':
    bauen()
