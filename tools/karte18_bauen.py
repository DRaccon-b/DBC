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


def risse(a, asphalt, seed=1818):
    """Vereinzelte feine Risse im Asphalt (etwa jede 70. Kachel), unregelmaessig verteilt."""
    rs = random.Random(seed)
    ys, xs = np.nonzero(asphalt[::T, ::T])
    for i in rs.sample(range(len(ys)), len(ys) // 70):
        x, y = int(xs[i]) * T + rs.randint(2, 12), int(ys[i]) * T + rs.randint(1, 4)
        for _ in range(rs.randint(6, 12)):
            if asphalt[y, x]:
                a[y, x] = H('#22242c')
            x += rs.choice((-1, 0, 1)); y += 1


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


def striche(a, frei, sperre, festy, von, bis, farbe, strich, luecke, dicke=2, senkrecht=False):
    """Strichlinie: nur ganze Striche, die vollstaendig auf freiem Asphalt und >= 4 px neben Zebrastreifen liegen
    (keine Stummel an Kreuzungen)."""
    # erlaubte Abschnitte entlang der Linie bestimmen, je 8 px Abstand zu Kreuzung/Zebra, nur wenn >= 2 Striche passen
    if senkrecht:
        ok = frei[von:bis, festy:festy + dicke].all(axis=1) & ~sperre[von:bis, festy:festy + dicke].any(axis=1)
    else:
        ok = frei[festy:festy + dicke, von:bis].all(axis=0) & ~sperre[festy:festy + dicke, von:bis].any(axis=0)
    i = 0
    while i < len(ok):
        if not ok[i]:
            i += 1
            continue
        j = i
        while j < len(ok) and ok[j]:
            j += 1
        s0, s1 = von + i + (8 if i > 0 else 0), von + j - (8 if j < len(ok) else 0)
        if s1 - s0 >= 2 * strich + luecke:
            p = s0
            while p + strich <= s1:
                if senkrecht:
                    a[p:p + strich, festy:festy + dicke] = farbe
                else:
                    a[festy:festy + dicke, p:p + strich] = farbe
                p += strich + luecke
        i = j


def markierungen(a, asphalt, lay):
    """Mittellinien, Leitlinien, Pfeile, Zebrastreifen, Parkbuchten. Linien enden vor Kreuzungen und Zebrastreifen
    (keine Ueberkreuzungen, keine Stummel)."""
    zebra = np.zeros_like(asphalt)
    for (x0, x1, y0, y1, art) in lay['zebra']:
        zebra[y0 * T:(y1 + 1) * T, x0 * T:(x1 + 1) * T] = True
    sperre = zebra.copy()
    for d in range(1, 5):
        sperre |= np.roll(zebra, d, 0) | np.roll(zebra, -d, 0) | np.roll(zebra, d, 1) | np.roll(zebra, -d, 1)
    frei = asphalt & ~zebra
    gelb = GELB.astype(np.uint8)
    weiss = (WEISS * 0.9).astype(np.uint8)
    # obere Strasse: gelbe Doppellinie (durchgezogen) in der Mitte (Reihe 20..24 -> Mitte 22.5)
    y = int(22.5 * T)
    for yy in (y - 3, y + 2):
        for x in range(3 * T, 82 * T):
            if 27 * T - 4 <= x < 42 * T + 4:                     # Zebras und Einmuendung der Querstrasse frei
                continue
            if frei[yy, x] and not sperre[yy, x]:
                a[yy, x] = gelb
    # Querstrasse: gelbe Strichlinie nur zwischen den Kreuzungen
    xm = int(34.5 * T) - 1
    for (y0, y1) in ((25 * T, 42 * T), (54 * T, 82 * T)):
        striche(a, frei, sperre, xm, y0, y1, gelb, 10, 8, senkrecht=True)
    # mittlere Strasse: je Fahrbahn eine weisse Leitlinie, unterbrochen an der Kreuzung (x 32..36)
    for yc in (44.5, 51.5):
        for (x0, x1) in ((3 * T, 32 * T), (37 * T, 63 * T)):
            striche(a, frei, sperre, int(yc * T) - 1, x0, x1, weiss, 12, 10)
    # Uferstrasse: Nordfahrbahn 82..86 (Leitlinie 84.5), Suedfahrbahn 89..93 (Leitlinie 91.5); Einmuendung frei
    for yc in (84.5, 91.5):
        striche(a, frei, sperre, int(yc * T) - 1, 37 * T, 125 * T, weiss, 12, 10)
    for (cx, cy, r) in ((22 * T, int(21.4 * T), 1), (58 * T, int(23.6 * T), -1), (8 * T, int(43.3 * T), 1),
                        (46 * T, int(52.6 * T), -1), (70 * T, int(85.7 * T), 1), (118 * T, int(90.3 * T), -1)):
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
    # Parkplatz: Buchten je 3 Kacheln (Linien auf den Kachelkanten 42, 45, ... 60), Mittelgasse
    for x in range(42, 61, 3):                                  # Buchten nur im Norden, breite Fahrgasse (Reihen 33-37)
        for y in range(29 * T + 2, 32 * T + 15):
            a[y, x * T] = weiss
    for x in range(42 * T, 60 * T, 16):
        a[35 * T + 7, x:x + 8] = (GELB * 0.8).astype(np.uint8)


# ---------------------------------------------------------------------------------------------- Flaechen
def rasen_kanten(a, rasen):
    """Rasen mit Steinkante: 1 px heller Randstein aussen, innen eine dunkle Erdfuge."""
    rand = kontur(rasen)
    a[rand] = H('#8a8e98')
    innen = kontur(rasen & ~rand)
    dunkeln(a, innen, 0.72)


OLIV = np.array([H(c) for c in ('#2e3a1a', '#3e4e22', '#50642c', '#647a36', '#788e42', '#8ca050')], np.float32)


def mittelstreifen(a, m):
    """Mittelstreifen und Beete wie in der Vorlage: heller Bordstein ringsum, darin eine niedrige, kastenfoermig
    geschnittene Hecke in Olivgruen - je Kachel ein weich gewoelbter Block (Licht oben links, Schatten unten rechts,
    feine Blattstruktur), dunkle Fugen zwischen den Bloecken, unten eine schmale dunkle Blattfront."""
    rand = kontur(m)
    innen = m & ~rand
    rs = np.random.RandomState(1818)
    wert = np.full(m.shape, 0.6, np.float32)                       # dunkler Grund zwischen den Ballen
    ys, xs = np.nonzero(innen)
    if len(ys):
        y0_, y1_, x0_, x1_ = ys.min(), ys.max(), xs.min(), xs.max()
        mitten = [(y + rs.randint(-2, 3), x + rs.randint(-2, 3), rs.uniform(3.2, 4.6))
                  for y in range(y0_, y1_ + 1, 5) for x in range(x0_ + (y // 5 % 2) * 3, x1_ + 1, 6)]
        for (cy, cx, r) in sorted(mitten):                         # hintere Ballen zuerst, vordere decken
            ri = int(r) + 1
            ya, yb, xa, xb = max(0, cy - ri), min(m.shape[0], cy + ri + 1), max(0, cx - ri), min(m.shape[1], cx + ri + 1)
            gy, gx = np.mgrid[ya:yb, xa:xb]
            d = ((gy - cy) ** 2 + (gx - cx) ** 2) / (r * r)
            sel = (d <= 1) & innen[ya:yb, xa:xb]
            v = 3.2 - 1.5 * ((gx - cx) + (gy - cy)) / r * 0.6 - 2.2 * d * d
            v = v + ((gx * 7 + gy * 13) % 5 == 0) * 0.5            # einzelne Blattlichter
            blk = wert[ya:yb, xa:xb]
            blk[sel] = v[sel]
    idx = np.clip(np.round(wert), 0, len(OLIV) - 1).astype(int)
    a[innen] = OLIV[idx[innen]].astype(np.uint8)
    unten = innen & ~np.roll(innen, -1, 0)                         # Blattfront
    for d in range(3):
        dunkeln(a, np.roll(unten, -d, 0) & innen, 0.62 + 0.1 * d)
    a[rand] = H('#a4a8b4')
    a[rand & ~np.roll(m, -1, 0)] = H('#6a6e7a')                    # Bordstein unten im Schatten
    a[rand & ~np.roll(m, 1, 0)] = H('#c4c8d2')                     # oben im Licht


def platz_raster(a, platz, achse, nebel_m=None):
    """Grosser Platz wie die Vorlage: 4 px breite dunkle Fugenbaender (Pixel 6..9 der Kachel) in den Spalten 70, 79,
    88, 97, 106, 115, 124 und den Reihen 32, 40, ... 72 - spiegelsymmetrisch zur Achse; dazu ein heller abgesetzter
    Rahmen um den Mittelweg (Spalten 93 und 110, Reihe 35, Querband 52-53)."""
    for c in (70, 79, 88, 97, 106, 115, 124):
        m = np.zeros_like(platz); m[:, c * T + 6:c * T + 10] = True
        if nebel_m is None:
            rechts = np.roll(platz, -T, 1)
        else:                                                    # nur am Nebelrand weglassen (keine Stummel), sonst
            rechts = ~np.roll(nebel_m, -T, 1) & ~np.roll(nebel_m, -2 * T, 1)   # ueberall (Spalte 97 wie 106)
        dunkeln(a, m & platz & rechts, 0.7)
    for r in (32, 40, 48, 56, 64, 72):
        m = np.zeros_like(platz); m[r * T + 6:r * T + 10, :] = True
        dunkeln(a, m & platz, 0.7)
    rahmen = np.zeros_like(platz)
    rahmen[35 * T:77 * T, 93 * T:94 * T] = True
    rahmen[35 * T:77 * T, 110 * T:111 * T] = True
    rahmen[35 * T:36 * T, 93 * T:111 * T] = True
    rahmen[52 * T:54 * T, 93 * T:111 * T] = True
    dunkeln(a, rahmen & platz, 0.88)


def kompass(a, cx, cy):
    """Bodenmedaillon (Windrose) genau auf der Achse: gerader Durchmesser um die Kachelgrenze (cx, cy), zwei Ringe,
    vier Spitzen, roter Kern - spiegelsymmetrisch."""
    yy, xx = np.mgrid[-24:24, -24:24] + 0.5
    d = np.hypot(xx, yy)
    sub = a[cy - 24:cy + 24, cx - 24:cx + 24]
    for (r, c) in ((22, '#5e5672'), (20, '#aaa4c0'), (14, '#5e5672')):
        sub[np.abs(d - r) <= 0.8] = H(c)
    spitze = ((np.abs(xx) <= np.maximum(0.5, 3.5 - np.abs(yy) / 5)) & (np.abs(yy) <= 18)) | \
             ((np.abs(yy) <= np.maximum(0.5, 3.5 - np.abs(xx) / 5)) & (np.abs(xx) <= 18))
    sub[spitze & ((xx < 0) | (yy < 0))] = H('#d0cad8')            # Licht oben links
    sub[spitze & (xx > 0) & (yy > 0)] = H('#7e7692')
    sub[(np.abs(xx) <= 2) & (np.abs(yy) <= 2)] = H('#b03a40')
    sub[(xx < 0) & (xx > -2) & (yy < 0) & (yy > -2)] = H('#e06058')


def terrasse(a, lay, lvl):
    """Terrasse vor der Halle (Ebene 2, x 87..116): Belag im Schachbrett des Mittelwegs, 32 px Stuetzmauer (Reihen
    32-33) mit Lichtkante, Lueftungsschlitzen im festen Rhythmus und Kontaktschatten; mittig die Treppe (12 Kacheln,
    8 Stufen, Achse); Seitenkanten nur als Kontur."""
    x0, x1, ry = lay['treppe_terrasse']
    kl = np.array([list(r) for r in lay['klassen']])
    ter = gross(kl == 't')
    ct = textur('c', len(kl[0]), len(kl))
    a[ter] = ct[ter]
    ys = ry * T
    xs = np.nonzero(ter[ys - 1])[0]
    tx0, tx1 = x0 * T, (x1 + 1) * T
    for x in range(xs.min(), xs.max() + 1):
        for d in range(32):
            Y = ys + d
            if tx0 <= x < tx1:
                st = d % 4                                      # 8 Stufen: Trittkante hell, Setzstufe dunkel
                c = H('#c4bed8') if st == 0 else H('#a49eba') if st == 1 else H('#7a7494') if st == 2 else H('#4e4866')
                if x in (tx0, tx1 - 1):
                    c = H('#4a4460')
                lvl[Y, x] = 2
            else:
                c = H('#8a84a2') if d < 2 else H('#6e6888') if d < 28 else H('#4c4664')
                if d in (14, 15):
                    c = H('#625c7c')                            # Gesimsfuge
                dd = (tx0 - 1 - x) if x < tx0 else (x - tx1)     # Schlitze im 32-px-Raster ab der Treppenwange
                laenge = (tx0 - xs.min()) if x < tx0 else (xs.max() + 1 - tx1)
                if dd % 32 in range(10, 22) and dd - dd % 32 + 21 <= laenge - 1 and 19 <= d <= 23:
                    c = H('#3a3450')                            # Lueftungsschlitz
                lvl[Y, x] = 9
            a[Y, x] = c
        if not (tx0 <= x < tx1):
            dunkeln(a, (np.s_[ys + 32:ys + 34], np.s_[x]), 0.75)
    a[ys - 1, xs.min():xs.max() + 1] = H('#c2bcd4')               # Lichtkante an der Oberkante
    for x in (xs.min(), xs.max()):                                # Seitenkanten: Kontur
        col = ter[:, x].copy()
        col[ys:ys + 32] = True
        a[col, x] = H('#5a5470')


def promenade(a, lay, lvl):
    """Holzpromenade (Klasse b, Planken in der Kachel) und ein Gelaender an der Oberkante der Kaikante (Reihe 98):
    heller Handlauf, Pfosten alle 16 px, Luecke am Steg. Das Gelaender ist nicht begehbar."""
    sx0, sy0, sx1, sy1 = lay['steg']
    y = 98 * T
    for x in range(4 * T, 125 * T):
        if sx0 * T <= x < (sx1 + 1) * T:
            continue
        a[y + 1, x] = H('#b8bcc8'); a[y + 2, x] = H('#6a6e7c')
        if x % 16 in (7, 8):
            a[y + 1:y + 9, x] = H('#7a7e8c') if x % 16 == 7 else H('#4a4e5a')
        a[y + 9, x] = (a[y + 9, x] * 0.7).astype(np.uint8)
        lvl[y:y + 10, x] = 9


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


def wasser_stufen(a, kl):
    """Meer in drei Tiefenstufen wie auf den anderen Karten (Kachelraster): bis 2 Kacheln vom Land flach (heller,
    leicht tuerkis), bis 5 Kacheln mittel, dahinter tief (dunkel). An jeder Stufe eine Unterwasserkante: 1 px heller
    Grat auf der flachen Seite, 2 px Schatten auf der tiefen Seite."""
    w = kl == 'w'
    land = ~np.isin(kl, ['w', '.'])
    dist = np.full(kl.shape, 99)
    dist[land] = 0
    for d in range(1, 9):                                          # Kachelabstand (Chebyshev) zum Land
        nb = np.zeros_like(land)
        cur = dist == d - 1
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                nb |= np.roll(np.roll(cur, dy, 0), dx, 1)
        dist[nb & (dist == 99)] = d
    stufe = np.where(dist <= 2, 0, np.where(dist <= 5, 1, 2))
    st = np.kron(stufe, np.ones((T, T), int))
    W_ = gross(w)
    af = a.astype(np.float32)
    flach, tief = W_ & (st == 0), W_ & (st == 2)
    af[flach] = af[flach] * 1.25 + np.array([4, 14, 18], np.float32)
    af[tief] = af[tief] * 0.84
    a[:] = np.clip(af, 0, 255).astype(np.uint8)
    for s0 in (0, 1):                                              # Kanten zwischen Stufe s0 und s0+1
        hoeher = W_ & (st == s0)
        tiefer = W_ & (st == s0 + 1)
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            sch = lambda m, k: np.roll(np.roll(m, k * dy, 0), k * dx, 1)
            kante = tiefer & sch(hoeher, 1)
            zweite = tiefer & sch(hoeher, 2) & ~kante
            dunkeln(a, kante, 0.6)
            dunkeln(a, zweite, 0.82)
            mischen(a, hoeher & sch(tiefer, 1), (120, 150, 190), 0.35)


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
            cx0 = int(xs[i]) * 16                               # Zelle: Striche laufen zyklisch (Bild 4 = Bild 0)
            X = cx0 + ((x - cx0) + k_ + 4 * f) % 16
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
    dunkeln(a, sch & wasser & (lvl != 9), 0.65)


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
            muster = ['#8ad0ff', '#4a90d0', '#2a5a90', '#2a5a90'] * 2   # Lauflicht: dreht je Bild um 45 Grad
            for k_ in range(8):
                w = math.radians(22.5 + 45 * k_)
                X, Y = int(round(cx + 6.3 * math.cos(w))), int(round(cy + 6.0 * math.sin(w)))
                a[Y, X] = H(muster[(k_ - f) % 8])


# ---------------------------------------------------------------------------------------------- Nebel
def nebel_feld(Hh, W, periode, seed, gross_):
    """Weiches Rauschen, waagerecht nahtlos periodisch (Gitter vor dem Skalieren zyklisch aufgefuellt, dann genau
    eine Periode aus der Mitte geschnitten)."""
    rs = np.random.RandomState(seed)
    k = periode // gross_
    n = rs.rand(Hh // gross_ + 3, k)
    n = np.concatenate([n[:, -3:], n, n[:, :3]], axis=1)
    m = np.array(Image.fromarray((n * 255).astype(np.uint8)).resize(((k + 6) * gross_, (Hh // gross_ + 3) * gross_),
                                                                     Image.BICUBIC)).astype(np.float32) / 255
    m = m[:Hh, 3 * gross_:3 * gross_ + periode]
    return np.tile(m, (1, W // periode + 1))[:, :W]


def nebel(a, land, frame):
    """Dichter Nebel ausserhalb der Stadt: ueber den Nebelkacheln deckend, am Land nur ein schmaler weicher Saum
    (~8 px, mit unregelmaessigem Rand statt Kachelstufen). Farbe: grosse ruhige Wolken (statisch, nicht periodisch)
    + zwei Schwaden, die nahtlos nach rechts ziehen (Perioden 64/32 px, je Bild 16/8 px -> 4 Bilder)."""
    f = frame or 0
    Hh, W = land.shape
    n0 = nebel_feld(Hh, W, W, 80, 32)
    fern = np.array(Image.fromarray(((~land) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(6))).astype(np.float32) / 255
    dichte = np.clip(fern * 1.9 - 0.12 + 0.3 * (n0 - 0.5), 0, 1)
    dichte[~land] = np.maximum(dichte[~land], np.clip(0.75 + fern[~land], 0, 1))
    dichte = np.array(Image.fromarray((dichte * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2))).astype(np.float32) / 255
    tief = np.array(Image.fromarray((land * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(7))) == 0
    dichte[tief] = np.maximum(dichte[tief], 0.95)                # Nebelinneres (>= 3 px vom Land) deckend
    dichte[land & (dichte < 0.04)] = 0                           # Stadtinneres nebelfrei (kein Flimmern im GIF)
    n1 = np.roll(nebel_feld(Hh, W, 64, 81, 16), 16 * f, axis=1)
    n2 = np.roll(nebel_feld(Hh, W, 32, 82, 8), 8 * f, axis=1)
    s_ = dichte[..., None]
    farbe = NEBEL[None, None, :] * (0.86 + 0.12 * n0[..., None] + 0.08 * n1[..., None] + 0.04 * n2[..., None])
    a[:] = np.clip(a * (1 - s_) + farbe * s_, 0, 255).astype(np.uint8)
    return dichte


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
    a[y0 + 63, X0:X1, :3] = H('#2a2c36')
    if X0 > 0:
        a[y0:y0 + 64, X0:X0 + 2, :3] = H('#2a2c36')               # westlicher Abschluss: geschlossene Stirn
        a[y0:y0 + 64, X0 + 2, :3] = H('#c4c8d2')
        for d in (4, 8, 12):                                      # Prellbock
            for x in range(X0 + 4, X0 + 13):
                a[y0 + d:y0 + d + 2, x, :3] = H('#b03a40') if ((x - X0) // 3) % 2 == 0 else H('#e0e0e8')
    else:                                                         # Bahn kommt im Westen aus dem Nebel
        for x in range(0, 6 * T):
            s_ = 0.92 * (1 - x / (6.0 * T)) ** 1.5
            a[y0:y0 + 64, x, :3] = (a[y0:y0 + 64, x, :3] * (1 - s_) + NEBEL[:3] * s_).astype(np.uint8)
    img = Image.fromarray(a)
    if zug_sp is not None:
        zx0, zx1 = hb['zug']
        img.alpha_composite(zug_sp, (zx0 * T, y0 + 31 - zug_sp.height))      # Zug steht auf der Fahrbahn
    return img


def schatten_hochbahn(a, lay, boden):
    """Schatten der Hochbahn: die Bahn liegt hoch ueber dem Mittelstreifen (Pfeilerfuesse Reihe 88); ihr Schatten
    faellt nach rechts unten auf Hecke und Suedfahrbahn (Reihe 87.5..90.4), unten weich auslaufend, nicht aufs Wasser."""
    hb = lay['hochbahn']
    for y in range(1400, 1448):
        k_ = 0.75 if y < 1442 else 0.75 + (y - 1441) * 0.04
        m = np.zeros(boden.shape, bool)
        m[y, hb['x0'] * T + 40:(hb['x1'] + 1) * T] = True
        dunkeln(a, m & boden, k_)


def gebaeude_schatten(img, geb, lvl):
    """Gebaeudeschatten (Licht von oben links): rechts neben dem Gebaeude ein nach unten auslaufender Streifen,
    unter der Fassade ein schmaler Kontaktschatten - nur auf dem Boden der Grundebene (nicht auf Wasser/Terrasse)."""
    a = np.array(img).astype(np.float32)
    Hh, W = lvl.shape
    m = np.zeros((Hh, W), np.float32)
    for o in geb:
        x0, y0, x1, y1 = o['gebaeude']
        X0, X1, Y1 = x0 * T, (x1 + 1) * T, (y1 + 1) * T
        hoch = (y1 - y0 + 1) * T
        ebene_fuss = lvl[min(Hh - 1, Y1 + 1), min(W - 1, X0 + 6)]
        ms = np.zeros((Hh, W), np.float32)
        for y in range(Y1 - hoch, Y1 + 12):                      # rechts: 12 px, oben weich ein-, unten schraeg auslaufend
            if not (0 <= y < Hh):
                continue
            ende = X1 + 12 - max(0, y - Y1)
            st = 0.3 * min(1.0, (y - (Y1 - hoch)) / 8.0)
            ms[y, X1:min(W, ende)] = np.maximum(ms[y, X1:min(W, ende)], st)
        ms[lvl != 1] = 0
        mf = np.zeros((Hh, W), np.float32)                         # Kontaktschatten direkt an der Wand, je Spalte auf
        mf[Y1:min(Hh, Y1 + 5), X0:min(W, X1 + 8)] = 0.32           # der Ebene des Bodens vor der Fassade
        mf[Y1:min(Hh, Y1 + 2), X0:min(W, X1 + 10)] = 0.42
        fl = lvl[min(Hh - 1, Y1 + 1), :]
        mf[(lvl != fl[None, :]) | (lvl == 0) | (lvl == 9)] = 0
        m = np.maximum(m, np.maximum(ms, mf))
    a[..., :3] *= (1 - m[..., None])
    img.paste(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)))


def lichtkegel(img, lampen, cache, frame, lvl):
    """Warmer Lichtkreis der Laternen am Boden wie in der Vorlage: zwei Stufen (aussen 44x24 px, innen 26x14 px),
    nur auf der Bodenebene; die Helligkeit atmet in 4 Bildern."""
    a = np.array(img).astype(np.float32)
    f = (frame or 0) % 4
    for o in lampen:
        sp = cache[o['datei']]
        al = np.array(sp.getchannel('A')) > 0
        cx = o['x'] + (np.nonzero(al[o['fuss']])[0].mean() if al[o['fuss']].any() else sp.width / 2.0)
        cy = o['y'] + o['fuss'] - 1
        k_ = (0.94, 1.0, 1.06, 1.0)[(f + int(o['x']) // 40) % 4]
        if o.get('anim') == 'flammen18':
            k_ = FEUER_LICHT[f] * 1.1                            # Feuer: staerker, flackert mit den Flammen
        if o['basis'] == 'gebaeude/doppellaterne':
            cy = 48 * T                                          # Mitte des Mittelstreifens: Licht auf beide Fahrbahnen
        e = int(lvl[min(lvl.shape[0] - 1, int(o['y'] + o['fuss'] - 1)), min(lvl.shape[1] - 1, int(round(cx)))])
        x0, x1, y0, y1 = int(cx - 23), int(cx + 24), int(cy - 13), int(cy + 14)
        yy, xx = np.mgrid[y0:y1, x0:x1]
        aussen = ((xx - cx) / 22.0) ** 2 + ((yy - cy) / 12.0) ** 2 <= 1
        innen = ((xx - cx) / 13.0) ** 2 + ((yy - cy) / 7.0) ** 2 <= 1
        s_ = np.where(innen, 0.41, np.where(aussen, 0.26, 0.0)) * k_
        ok = (yy >= 0) & (yy < a.shape[0]) & (xx >= 0) & (xx < a.shape[1])
        if e == 9:
            erl = np.isin(lvl[yy[ok], xx[ok]], (1, 9))
            s_[ok] = s_[ok] * np.where(lvl[yy[ok], xx[ok]] == 9, 0.6, 1.0)
        else:
            erl = lvl[yy[ok], xx[ok]] == e
        ok[ok] &= erl
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


def rechtecke(sp, frame, o):
    """Nur echte Lichtquellen pulsieren: feste Rechtecke im Sprite (o['licht_rects'] = [x0, y0, x1, y1, phase]),
    z. B. Leuchtschilder und Papierlaternen der Laeden, Lampen ueber den Lagertueren, Signallampen der Wache, der
    Bildschirm des Geldautomaten. Markisen, Fenster und Waende bleiben ruhig; jedes Licht im eigenen Takt."""
    a = np.array(sp)
    ai = a.astype(int)
    out = a.copy()
    for (x0, y0, x1, y1, ph) in o.get('licht_rects', []):
        k_ = (0.82, 1.0, 1.14, 0.96)[((frame or 0) + ph) % 4]
        blk = ai[y0:y1 + 1, x0:x1 + 1]
        m = blk[..., 3] > 0
        sub = out[y0:y1 + 1, x0:x1 + 1]
        sub[m, :3] = np.clip(blk[m, :3] * k_, 0, 255).astype(np.uint8)
    return Image.fromarray(out)


def ampel18(sp, frame, o):
    """Ampel: nur die gerade leuchtende Lampe (gruen bzw. Fussgaenger-Signal) pulsiert leicht."""
    a = np.array(sp)
    ai = a.astype(int)
    m = (ai[..., 3] > 0) & (ai[..., 1] > 150) & (ai[..., 1] > ai[..., 0] + 40)
    k_ = (0.88, 1.0, 1.1, 1.0)[((frame or 0) + int(o.get('x', 0)) // 48) % 4]
    a[m, :3] = np.clip(ai[m, :3] * k_, 0, 255).astype(np.uint8)
    return Image.fromarray(a)


def fahne18(sp, frame, o):
    """Fahne/Banner: nur der Stoff weht. Mast, Ausleger, Querstange und Fuss bleiben pixelgleich; auch Schrift und
    Muster im Tuch bleiben unveraendert. Bewegt wird allein die freie Aussenkante des Tuchs: in einzelnen Zeilen
    bauscht sie sich um 1 px nach aussen (Kontur wandert mit, die Luecke wird mit Tuchfarbe gefuellt), die Welle
    laeuft in 4 Bildern am Tuch herunter."""
    a = np.array(sp)
    ai = a.astype(int)
    h, w = a.shape[:2]
    al = a[..., 3] > 0
    tuch = al & ((ai[..., 2] > ai[..., 0] + 40) | (ai[..., 0] > ai[..., 2] + 40))
    zeilen = np.nonzero(tuch.any(axis=1))[0]
    if not len(zeilen):
        return sp
    y0, y1 = int(zeilen.min()), int(zeilen.max())
    rechts = np.nonzero(tuch)[1].mean() >= w / 2.0 - 0.5
    out = a.copy()
    for y in range(y0, y1 + 1):
        if math.sin(2 * math.pi * (frame or 0) / 4.0 + y * 0.5) >= -0.3:
            continue
        xs = np.nonzero(al[y])[0]
        if not len(xs):
            continue
        e = int(xs.max()) if rechts else int(xs.min())
        n_, i_ = (e + 1, e - 1) if rechts else (e - 1, e + 1)
        if not (0 <= n_ < w) or al[y, n_] or not tuch[y, i_]:      # nur wo die Kante wirklich Tuch ist
            continue
        out[y, n_] = a[y, e]                                      # Kontur 1 px nach aussen
        out[y, e] = a[y, i_]                                      # Luecke mit dem Tuch daneben fuellen
    return Image.fromarray(out)


FEUER_HOEHEN = [(7, 10, 6), (9, 8, 8), (6, 9, 6), (8, 11, 9)]    # Zungenhoehen je Bild
FEUER_LICHT = (0.95, 1.03, 0.88, 1.14)                            # Lichtkreis flackert im Takt der Flammenhoehe


def flammen18(sp, frame, o):
    """Feuerschale: drei spitz zulaufende Flammenzungen ueber der Glut - unten breit mit hellgelbem Kern, Mitte orange,
    Rand und Spitze rot, dunkelrote Kontur; Hoehe und seitliche Neigung der Spitzen wechseln in 4 Bildern (die
    Flammen selbst bewegen sich). Die Schale bleibt ruhig."""
    a = np.array(sp)
    f = (frame or 0) % 4
    hw, ww = a.shape[0], a.shape[1]
    feld = np.zeros((hw, ww), np.uint8)                           # 0 leer, 1 rot, 2 orange, 3 gelb, 4 hellgelb
    neig = [(0, 1, -1), (1, -1, 0), (-1, 0, 1), (0, 1, 1)][f]
    for (fx, hmax, nk) in zip((7, 11, 15), FEUER_HOEHEN[f], neig):
        for d in range(hmax):
            y = 11 - d
            t = d / float(hmax)
            halb = int(round(2.4 * (1 - t) - 0.2))
            x0 = fx + int(round(nk * (t ** 2) * 2))
            for dx in range(-max(0, halb), max(0, halb) + 1):
                x = x0 + dx
                if not (0 <= y < hw and 0 <= x < ww):
                    continue
                rand = abs(dx) == halb and halb > 0
                if t < 0.4 and not rand:
                    c = 4 if (dx == 0 and t < 0.25) else 3
                elif t < 0.75 and not rand:
                    c = 2
                else:
                    c = 1
                feld[y, x] = max(feld[y, x], c)
    farben = {1: H('#c84a30'), 2: H('#f0a040'), 3: H('#f8d060'), 4: H('#fff4c0')}
    voll = feld > 0
    kontur_ = np.zeros_like(voll)
    for (dy, dx) in ((-1, 0), (0, -1), (0, 1)):
        kontur_ |= np.roll(np.roll(voll, dy, 0), dx, 1)
    kontur_ &= ~voll
    kontur_[12:] = False
    kontur_ &= a[..., 3] == 0
    for c, col in farben.items():
        a[feld == c] = list(col[:3]) + [255]
    a[kontur_] = list(H('#6a1e14')[:3]) + [255]
    return Image.fromarray(a)


def boot(sp, frame, o):
    """Boot schaukelt auf dem Wasser: hebt und senkt sich als Ganzes um 1 px."""
    d = (0, 1, 0, -1)[(frame or 0) % 4]
    out = Image.new('RGBA', sp.size)
    out.paste(sp, (0, d))
    return out


def wasserring(img, pfeiler, frame, wasser):
    """Wasserkontakt am Pfeiler im Kanal: feste 1-px-Schaumlinie entlang der Unterkante und ein heller Ring aus kurzen
    Schaumstrichen (2-3 px), der in 4 Bildern um den Pfeiler wandert; der Teil hinter dem Pfeiler bleibt verdeckt.
    Halbtransparent ueber das Wasser gelegt (im Schatten der Kaimauer dunkler), nur auf Wasserpixeln."""
    a = np.array(img).astype(np.float32)
    f = (frame or 0) % 4
    schaum, hell = np.array(H('#8a9aca')[:3], np.float32), np.array(H('#b0bce0')[:3], np.float32)

    def tupfen(X, Y, c, s_=0.7):
        if 0 <= Y < a.shape[0] and 0 <= X < a.shape[1] and wasser[Y, X]:
            a[Y, X, :3] = a[Y, X, :3] * (1 - s_) + c * s_

    for o in pfeiler:
        cx, fy = o['x'] + 16, o['y'] + o['fuss']
        for X in range(o['x'] + 6, o['x'] + 26):                  # Schaumlinie direkt am Fuss
            tupfen(X, fy + 1, hell if (X + f) % 3 else schaum, 0.75)
        for k_ in range(10):
            if k_ % 2:
                continue
            w0 = 2 * math.pi * (k_ + f * 0.5) / 10
            for j in range(4):                                    # Strich aus 4 Punkten entlang der Ellipse
                w_ = w0 + j * 0.08
                X, Y = int(round(cx + 16 * math.cos(w_))), int(round(fy + 2 + 4 * math.sin(w_)))
                if Y <= fy + 1 and o['x'] + 4 <= X <= o['x'] + 27:  # hinter dem Pfeiler / auf der Schaumlinie
                    continue
                tupfen(X, Y, hell if j in (1, 2) else schaum, 0.85)
    img.paste(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)))


k4.TEILANIM.update({'laterne18': laterne18, 'automat': leuchten18, 'ampel18': ampel18, 'rechtecke': rechtecke,
                    'boot': boot, 'fahne18': fahne18, 'flammen18': flammen18})


# ---------------------------------------------------------------------------------------------- Bau
def bauen(frame=None, speichern=True):
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cols, rows = lay['groesse']
    Wp, Hp = cols * T, rows * T
    kl = np.array([list(r) for r in lay['klassen']])
    a = textur('nebel', cols, rows)
    for art in 'gpqctndxbkhsv':
        m = gross(kl == art)
        a[m] = textur(art, cols, rows)[m]
    wasser = gross(kl == 'w')
    a[wasser] = textur('w', cols, rows)[wasser]
    wasser_stufen(a, kl)
    land = gross(kl != '.') & ~wasser
    asphalt = gross(np.isin(kl, ['s', 'x']))
    lvl = np.zeros((Hp, Wp), np.uint8)
    lvl[land] = 1
    lvl[gross(kl == 't')] = 2
    risse(a, gross(kl == 's'))
    bordsteine(a, asphalt, land)
    markierungen(a, asphalt, lay)
    rasen_kanten(a, gross(np.isin(kl, ['n', 'd'])))
    sand = gross(kl == 'd')
    r1 = kontur(sand); r2 = kontur(sand & ~r1); r3 = kontur(sand & ~r1 & ~r2)   # 3 px Holzrahmen
    a[r1 | r2] = H('#5a4228')
    a[(r1 | r2) & (np.roll(~sand, 1, 0) | np.roll(~sand, 2, 0) | np.roll(~sand, 1, 1) | np.roll(~sand, 2, 1))] = H('#8a6a44')
    a[r3] = H('#3a2a1a')
    mittelstreifen(a, gross(np.isin(kl, ['m', 'e'])))
    lvl[gross(np.isin(kl, ['m', 'e']))] = 9                        # Hecken (Mittelstreifen, Beete): nicht begehbar
    platz_raster(a, gross(kl == 'p'), lay['achse'], gross(kl == '.'))
    kompass(a, lay['kompass'][0] * T, lay['kompass'][1] * T)
    terrasse(a, lay, lvl)
    promenade(a, lay, lvl)
    kaimauer(a, wasser, land, lvl)
    kanal = np.zeros_like(wasser); kanal[18 * T:100 * T, 125 * T:126 * T] = True   # Kaikante Ostrand: Bruestung
    kanal[40 * T:45 * T] = False                                  # Mole zum Teleporter bleibt offen
    for y in range(18 * T, 100 * T):
        if 40 * T <= y < 45 * T:
            continue
        for x in range(125 * T, 126 * T):
            c = H('#9aa0ae') if x - 125 * T < 2 else H('#7a7e8c') if x - 125 * T < 13 else H('#3a3e4a')
            if (y % 8) == 3 and 5 <= x - 125 * T <= 9:
                c = H('#c4c8d2')                                # Nietpunkte
            a[y, x] = c
    lvl[kanal] = 9
    lvl[40 * T:41 * T, 125 * T:134 * T] = 9                      # Molenraender (Reihe 40/44): nicht begehbar
    lvl[44 * T:45 * T, 125 * T:134 * T] = 9
    lvl[99 * T:100 * T, 4 * T:104 * T] = 9                       # Kaistreifen hinter dem Gelaender: nicht erreichbar
    lvl[99 * T:100 * T, 110 * T:125 * T] = 9
    sch_k = np.zeros_like(wasser); sch_k[18 * T:100 * T, 126 * T:126 * T + 3] = True
    wasser_wellen(a, wasser & (lvl != 9), frame)
    dunkeln(a, sch_k & wasser, 0.75)
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
    dichte = nebel(a, land | wasser, frame)                        # Nebel liegt am Boden: Hohes ragt heraus
    img = Image.fromarray(a).convert('RGBA')
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain_basis.png'))
    zug = None
    pf = os.path.join(OBJ, 'platzierung.json')
    if os.path.exists(pf):
        objs = sorted((o for o in json.load(open(pf)) if os.path.exists(os.path.join(OBJ, o['datei']))),
                      key=lambda o: o.get('sortier', o['y'] + o['fuss']))
        for o in objs:                                               # veraltete Gebaeude-Kopien (sauber/) erneuern
            if o['basis'].startswith('gebaeude/'):
                q, z = os.path.join(OBJ, o['basis'] + '.png'), os.path.join(OBJ, o['datei'])
                if os.path.exists(q) and os.path.getmtime(q) > os.path.getmtime(z):
                    im_ = Image.open(q).convert('RGBA')
                    if z.endswith('_m.png'):
                        im_ = im_.transpose(Image.FLIP_LEFT_RIGHT)
                    if im_.size != Image.open(z).size:
                        raise SystemExit('Groesse von %s geaendert: erst karte18_objekte.py laufen lassen' % q)
                    im_.save(z)
                    print('  erneuert:', o['datei'])
        cache = {o['datei']: Image.open(os.path.join(OBJ, o['datei'])).convert('RGBA') for o in objs}
        vor = np.array(img).astype(np.float32)
        lvl_s = lvl.copy()
        lvl_s[gross(np.isin(kl, ['m', 'e']))] = 1                    # Objekte auf Hecken werfen Schatten auf den Boden
        k8.schatten_ebene(img, [o for o in objs if not o.get('kein_schatten')], cache, lvl_s)
        gebaeude_schatten(img, [o for o in objs if o.get('gebaeude')], lvl)
        lichtkegel(img, [o for o in objs if o.get('anim') in ('laterne18', 'flammen18')], cache, frame, lvl)
        nach = np.array(img).astype(np.float32)                      # Schatten/Licht verblassen im Nebelsaum
        d_ = dichte[..., None]
        nach[..., :3] = vor[..., :3] * d_ + nach[..., :3] * (1 - d_)
        img = Image.fromarray(np.clip(nach, 0, 255).astype(np.uint8))
        boden_vor_objekten = np.array(img)
        k4.objekte_zeichnen(img, [o for o in objs if not o.get('hochbahn')], cache, np.zeros((Hp, Wp), bool),
                            frame if frame is not None else 0)          # Standbild = Bild 0 (Flammen, Fahnen sichtbar)
        img = img.copy()
        k4.animieren(img, [o for o in objs if not o.get('hochbahn')], cache, frame or 0, ruhig=frame is None)
        wasserring(img, [o for o in objs if o.get('im_wasser')], frame, wasser)
        hecke = gross(np.isin(kl, ['m', 'e']))                       # Stamm-/Mastfuss in der Hecke: Laub davor
        hecke_innen = hecke & np.roll(hecke, -3, 0) & np.roll(hecke, 1, 1) & np.roll(hecke, -1, 1)
        ia = np.array(img)
        for o in objs:
            if o['basis'] != 'gebaeude/doppellaterne':
                continue
            fy, sp_ = o['y'] + o['fuss'], cache[o['datei']]
            al = np.array(sp_.getchannel('A')) > 0
            for dy in range(5):
                Y = fy - dy
                if not (0 <= Y < ia.shape[0]):
                    continue
                xs_ = np.nonzero(al[o['fuss'] - dy])[0] + o['x']
                for X in xs_:
                    if 0 <= X < ia.shape[1] and hecke_innen[Y, X] and (X * 7 + Y * 3 + dy) % 5 != 0:
                        ia[Y, X] = boden_vor_objekten[Y, X]
        img = Image.fromarray(ia)
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
