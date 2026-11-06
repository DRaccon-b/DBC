"""Karte 11 (Spiral Mountain: Dark Ocean): links schwarzes, verseuchtes Land (Asche, schwarze Tuempel, Felsblock,
Ruinen-Platz, lila Hochplateaus mit Treppen), oben der Bergkamm, rechts das Meer der Finsternis (tuerkises
Flachwasser mit Seetang, Tiefsee, achteckige Plattform mit Bannkreis und Steinbruecke).
Baut auf Karte 04/08 auf (Kanten, Treppen, Schatten je Ebene, Verdeckung, Objekte, Animation).

  python3 tools/karte11_layout.py && python3 tools/karte11_kacheln.py
  python3 tools/karte11_bauen.py && python3 tools/karte11_objekte.py && python3 tools/regeln_v11.py karte11 \\
    && python3 tools/karte11_bauen.py
"""
import json, math, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageFilter
import karte_bauen as kb
import karte04_bauen as k4
import karte08_bauen as k8
import bauwerke

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte11')
BASIS = os.path.join(ROOT, 'assets', 'karte11', 'basis')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte11')
T = 16
N_FRAMES = 16
H = k4.H
weich, zell_maske = k4.weich, k4.zell_maske
k4.FELS['dunkelberg'] = ['#12141c', '#1a1d28', '#242836', '#303546', '#3e4458', '#50586e', '#666e86']
LIPPE_BERG = ['#3c4050', '#4a4e60', '#585e70', '#686e80', '#7a8092', '#8c92a4']
LIPPE_LILA = ['#2a2034', '#34283e', '#3e3048', '#4a3a56', '#564464', '#625072']
FRONT = {2: 32, 5: 44}
VIOLETT = (170, 110, 230)
MAUER_TIEFE = [8, 14, 22, 30, 38, 46]      # Mauer unter Wasser bis zum Grund je Wasserstufe 0..5 (px)
STUFEN_ABSTAND = [22, 64, 120, 190, 270]


def textur(art, cols, rows):
    t = np.zeros((rows * T, cols * T, 3), np.uint8)
    ks = [np.array(Image.open(os.path.join(BASIS, '%s_%d.png' % (art, v))).convert('RGB')) for v in range(5)]
    for y in range(rows):
        for x in range(cols):
            t[y * T:(y + 1) * T, x * T:(x + 1) * T] = ks[kb.variante(x, y)]
    return t


def kontur(m):
    return m & ~(np.roll(m, 1, 0) & np.roll(m, -1, 0) & np.roll(m, 1, 1) & np.roll(m, -1, 1))


def blur(m, r):
    return np.array(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(r))) / 255.0


_STUFEN_CACHE = {}


def meer_stufen(tief_m, n=5):
    """Stufe 0..n-1 je Tiefsee-Pixel: Abstand zum Flachwasser/Land (auf 1/4 Aufloesung berechnet), mit leichtem
    Rauschen fuer natuerliche Kanten, gleichmaessig bis zum Kartenrand verteilt. Fest (fuer alle Animationsbilder gleich)."""
    key = (tief_m.shape, int(tief_m.sum()))
    if key in _STUFEN_CACHE:
        return _STUFEN_CACHE[key]
    Hh, W = tief_m.shape
    k = tief_m[::4, ::4]
    nah = (~k).astype(np.float32)
    feld = np.zeros(k.shape, np.float32)
    for r in (3, 6, 12, 24, 48):                                  # weiches Naehe-Feld: gross = nahe am Flachwasser
        feld += np.array(Image.fromarray((nah * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(r))) / 255.0
    rs = np.random.RandomState(13)
    rausch = np.array(Image.fromarray((rs.rand(*feld.shape) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(5)))
    feld = feld + (rausch / 255.0 - 0.5) * 0.12
    werte = feld[k]
    grenzen = np.quantile(werte, [1 - (i + 1) / n for i in range(n - 1)]) if len(werte) else [0] * (n - 1)
    st = np.zeros(k.shape, np.uint8)
    for g in grenzen:
        st += (feld < g).astype(np.uint8)
    st = np.array(Image.fromarray(st).filter(ImageFilter.ModeFilter(5)))
    groß = np.kron(st, np.ones((4, 4), np.uint8))[:Hh, :W]
    groß = np.array(Image.fromarray(groß).filter(ImageFilter.ModeFilter(7))).astype(int)
    groß[~tief_m] = 0
    _STUFEN_CACHE[key] = groß
    return groß


def meer_zeichnen(a, wasser, flach, seetang, frame):
    """Meer der Finsternis: Flachwasser (tuerkis, Grund sichtbar, Lichtnetze wandern), Seetangfelder (dunkel,
    Blaetter wiegen sich), zur Tiefsee hin dunkler werdend; Tiefsee dunkel nachtblau-violett mit langsamen Wellen."""
    Hh, W = wasser.shape
    f = frame or 0
    yy, xx = np.mgrid[0:Hh, 0:W]
    grund = a.copy().astype(np.float32)
    tiefe = 1 - blur(flach, 9)                                   # 0 = Flachwasser, 1 = Tiefsee
    tiefe = np.clip(tiefe * 1.15, 0, 1)
    tuerkis = np.array([46, 128, 122], np.float32)
    nacht = np.array([30, 34, 74], np.float32)
    farbe = tuerkis[None, None] * (1 - tiefe[..., None]) + nacht[None, None] * tiefe[..., None]
    lum = grund @ np.array([0.3, 0.59, 0.11], np.float32)
    misch = 0.55 + 0.4 * tiefe                                   # in der Tiefe verschwindet der Grund
    neu = grund * (1 - misch[..., None]) * np.array([0.6, 0.9, 0.95]) + farbe * misch[..., None] \
        + (lum[..., None] - 60) * 0.25 * (1 - tiefe[..., None])
    # Tiefsee in 5 Stufen bis zum Kartenrand (wie das terrassierte Meer von Karte 01): je weiter vom Flachwasser,
    # desto tiefer und dunkler; an jeder Stufenkante ein heller Grat auf der hoeheren und Schatten auf der tieferen Seite
    tief_m = wasser & ~flach
    stufe = meer_stufen(tief_m)
    if frame is None:
        np.save(os.path.join(KARTE, 'meer_stufen.npy'), stufe.astype(np.uint8))
    farben = np.array([[38, 56, 98], [32, 44, 88], [27, 35, 76], [22, 27, 64], [17, 19, 50]], np.float32)
    tex = (lum - lum[tief_m].mean()) * 0.18
    st_f = farben[stufe] + tex[..., None]
    rand_f = np.clip(blur(flach, 6) * 1.6, 0, 1)[..., None]          # weicher Uebergang zum Flachwasser
    if False:
        neu[tief_m] = (neu * rand_f + st_f * (1 - rand_f))[tief_m]
    for dy, dx in (() if True else ((1, 0), (-1, 0), (0, 1), (0, -1))):
        nb = np.roll(np.roll(stufe, dy, 0), dx, 1)
        kante = tief_m & (nb > stufe)                                   # hoehere Stufe neben tieferer: Grat
        neu[kante] = neu[kante] * 0.6 + np.array([92, 110, 160]) * 0.4
    for k_, fa in (() if True else ((1, 0.7), (2, 0.8), (3, 0.9))):
        oben = np.roll(stufe, k_, 0)
        sch = tief_m & (oben < stufe)
        neu[sch] *= fa
    # Lichtnetz im Flachwasser: duenne, helle Linien (Kaustik), wandern langsam
    ph = 2 * math.pi * f / N_FRAMES
    kau = np.sin(xx * 0.11 + np.sin(yy * 0.07 + ph) * 2.2) + np.sin(yy * 0.13 + np.sin(xx * 0.05 - ph) * 2.4)
    netz = (np.abs(kau) < 0.07) & flach
    neu[netz] = neu[netz] * 0.75 + np.array([70, 110, 100]) * 0.25 + 10
    # Tiefsee: einzelne Wellenkaemme (kurze helle Striche), die auftauchen, wandern und wieder vergehen
    rs_w = random.Random(21)
    tief_m = wasser & ~flach
    ys_t, xs_t = np.nonzero(tief_m[::6, ::6])
    for i in range(len(ys_t) // 9):
        j = rs_w.randrange(len(ys_t))
        y0, x0 = int(ys_t[j] * 6), int(xs_t[j] * 6)
        p0 = rs_w.random()
        t = ((f / N_FRAMES) + p0) % 1.0
        if t > 0.7:
            continue
        hell = math.sin(t / 0.7 * math.pi)
        x0 += int(t * 10)
        laenge = rs_w.randint(3, 6)
        for d in range(laenge):
            X = x0 + d
            if 0 <= X < W and tief_m[y0, X]:
                neu[y0, X] = neu[y0, X] * (1 - 0.5 * hell) + np.array([90, 96, 150]) * 0.5 * hell
                if y0 + 1 < Hh:
                    neu[y0 + 1, X] = neu[y0 + 1, X] * (1 - 0.25 * hell)
    # Seetangfelder: dunkler Grund, darauf Blattbueschel (wiegen sich mit dem Bild)
    st = seetang
    neu[st] = neu[st] * 0.62 + np.array([6, 22, 18])
    rs = random.Random(11)
    ys, xs = np.nonzero(st)
    for _ in range(len(ys) // 90):
        i = rs.randrange(len(ys)); cy, cx = int(ys[i]), int(xs[i])
        d = int(round(math.sin(ph + cx * 0.3) * 1.2))
        for k in range(5):
            Y, X = cy - k, cx + (d if k >= 3 else 0)
            if 0 <= Y < Hh and 0 <= X < W and st[Y, X]:
                neu[Y, X] = (40, 104, 88) if k < 4 else (70, 150, 120)
    # Uferkante: nasser, dunkler Saum auf dem Land, heller Schaum am Wasserrand (gestrichelt, wandert)
    rand_in = kontur(wasser)
    neu[rand_in] = neu[rand_in] * 0.7 + np.array([60, 80, 80])
    schaum = rand_in & (((xx + yy * 2 + f) % 7) < 3)
    neu[schaum] = (150, 196, 190)
    a[wasser] = np.clip(neu[wasser], 0, 255).astype(np.uint8)
    aussen = ~wasser & (np.roll(wasser, 1, 0) | np.roll(wasser, -1, 0) | np.roll(wasser, 1, 1) | np.roll(wasser, -1, 1))
    a[aussen] = (a[aussen] * 0.72).astype(np.uint8)


def tuempel_zeichnen(a, m, frame):
    """Schwarze, oelige Tuempel des verseuchten Landes: fast schwarzes Violett, Regenbogenschimmer der Oelhaut
    (wandert), dunkler Schlammrand."""
    f = frame or 0
    Hh, W = m.shape
    yy, xx = np.mgrid[0:Hh, 0:W]
    lum = a[m].astype(np.float32) @ np.array([0.3, 0.59, 0.11], np.float32)
    a[m] = np.clip(lum[:, None] * np.array([0.22, 0.2, 0.3]) + np.array([10, 8, 18]), 0, 255).astype(np.uint8)
    # Oelhaut: einzelne, unregelmaessige Schlieren (violett/tuerkis), die langsam treiben
    rs = random.Random(5)
    ys, xs = np.nonzero(m)
    for _ in range(max(1, len(ys) // 260)):
        i = rs.randrange(len(ys)); cy, cx = int(ys[i]), int(xs[i]) + (f // 4) % 3
        c = (70, 44, 96) if rs.random() < 0.6 else (34, 72, 82)
        laenge = rs.randint(3, 7)
        for d in range(laenge):
            Y, X = cy + (d // 3), cx + d
            if 0 <= Y < Hh and 0 <= X < W and m[Y, X]:
                a[Y, X] = c


def kaimauer(a, m, tiefe=24, ebene=None):
    """Plattform/Bruecke in der Tiefsee: Rand aus dunklen Ziegeln (12 px), nach Sueden die Mauerfront: 16 px ueber
    Wasser, an der Wasserlinie ein heller Strich, darunter geht die Mauer fest weiter bis zum Meeresboden der
    Wasserstufe an dieser Stelle (ebene: Stufe je Pixel, 0..5) - unter Wasser blaeulich, unten Kontaktkante und
    Schatten auf dem Grund. Seitenkanten schmal."""
    Hh, W = m.shape
    yy, xx = np.mgrid[0:Hh, 0:W]
    ring = m & ~(np.array(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(9))) > 0)
    z = (xx // 8 + (yy // 4) % 2) % 2
    a[ring] = np.where(z[ring][:, None] == 0, H('#262634'), H('#2e2e3e'))
    a[ring & ((yy % 4 == 3) | ((xx + 4 * ((yy // 4) % 2)) % 8 == 7))] = H('#16161e')
    a[kontur(m)] = H('#4a4a5e')
    front = np.zeros_like(m)
    sued = m & ~np.roll(m, -1, 0)
    UEBER = 16
    for y, x in zip(*np.nonzero(sued)):
        st_ = 0
        if ebene is not None:
            yp = min(Hh - 1, y + UEBER + 30)
            st_ = int(ebene[yp, x])
        gesamt = UEBER + MAUER_TIEFE[min(st_, len(MAUER_TIEFE) - 1)] if ebene is not None else tiefe
        for d in range(gesamt + 3):
            Y = y + 1 + d
            if Y >= Hh or m[Y, x]:
                break
            if d >= gesamt:                                      # Schatten auf dem Meeresboden
                a[Y, x] = (a[Y, x] * (0.62 if d == gesamt else 0.8)).astype(np.uint8)
                continue
            front[Y, x] = True
            reihe = d // 4
            if d % 4 == 3 or (x + 4 * (reihe % 2)) % 8 == 7:
                c = np.array((22, 22, 30), np.float32)
            else:
                c = np.array((52, 52, 66) if reihe % 2 else (46, 46, 60), np.float32)
            if d == UEBER:
                c = np.array((90, 120, 140), np.float32)         # Wasserlinie
            elif d > UEBER:
                tief_ = (d - UEBER) / max(1, gesamt - UEBER)
                c = c * (0.62 - 0.22 * tief_) + np.array((24, 34, 70), np.float32) * (0.38 + 0.22 * tief_)
            if d == gesamt - 1:
                c = np.array((12, 12, 22), np.float32)           # Fuss auf dem Grund
            a[Y, x] = np.clip(c, 0, 255).astype(np.uint8)
    return front


def bruecke_zeichnen(a, m, ebene, wasser):
    """Steinbruecke: Deck aus Platten, Bruestungen an Nord- und Suedkante (dunkle Ziegel, helle Oberkante), nach
    Sueden die Bogenreihe - Pfeiler alle 48 px gehen fest bis zum Meeresboden der jeweiligen Wasserstufe, dazwischen
    runde Boegen, durch die das Wasser sichtbar bleibt."""
    Hh, W = m.shape
    ys, xs = np.nonzero(m)
    if not len(ys):
        return np.zeros_like(m)
    y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    yy, xx = np.mgrid[0:Hh, 0:W]
    br = m & ((yy <= y0 + 4) | (yy >= y1 - 4))
    z = ((yy % 4 == 3) | ((xx + 4 * ((yy // 4) % 2)) % 8 == 7))
    a[br] = np.where(z[br][:, None], H('#16161e'), H('#2e2e3e'))
    a[m & ((yy == y0) | (yy == y1 - 4))] = H('#5a5a70')                 # Oberkante der Bruestungen im Licht
    a[m & (yy == y0 + 5)] = (a[m & (yy == y0 + 5)] * 0.7).astype(np.uint8)   # Schatten der Nordbruestung aufs Deck
    front = np.zeros_like(m)
    UEBER = 10
    for x in range(x0, x1 + 1):
        st_ = int(ebene[min(Hh - 1, y1 + 24), x]) if wasser[min(Hh - 1, y1 + 24), x] else 0
        tiefe = UEBER + MAUER_TIEFE[min(st_, len(MAUER_TIEFE) - 1)]
        q = (x - x0) % 48
        pfeiler = q < 12 or x > x1 - 12
        if pfeiler:
            bis = tiefe
        else:
            t = (q - 12) / 36.0                                         # Bogen zwischen zwei Pfeilern
            bis = UEBER + int(round(8 * (1 - math.sqrt(max(0.0, 1 - (2 * t - 1) ** 2)))))
        for d in range(bis + (2 if pfeiler else 1)):
            Y = y1 + 1 + d
            if Y >= Hh:
                break
            if d >= bis:
                a[Y, x] = (a[Y, x] * (0.62 if pfeiler else 0.5)).astype(np.uint8)   # Fuss-/Bogenschatten
                continue
            front[Y, x] = True
            reihe = d // 4
            if d % 4 == 3 or (x + 4 * (reihe % 2)) % 8 == 7:
                c = np.array((22, 22, 30), np.float32)
            else:
                c = np.array((52, 52, 66) if reihe % 2 else (46, 46, 60), np.float32)
            if pfeiler and (q in (0, 1)):
                c = c + 18                                              # Lichtkante am Pfeiler
            if d > UEBER - 3:
                tief_ = (d - UEBER + 3) / max(1, tiefe - UEBER + 3)
                c = c * (0.7 - 0.25 * tief_) + np.array((24, 34, 70), np.float32) * (0.3 + 0.25 * tief_)
            if d == UEBER - 3:
                c = np.array((90, 120, 140), np.float32)               # Wasserlinie
            a[Y, x] = np.clip(c, 0, 255).astype(np.uint8)
    return front


def wasser_ebenen(tief):
    """Wasserstufe 0..5 je Pixel (wie wasser_vertieft: Abstand zum Ufer >= Schwellen), fest fuer alle Bilder."""
    pf = os.path.join(KARTE, 'wasser_ebenen.npy')
    if os.path.exists(pf):
        e = np.load(pf)
        if e.shape == tief.shape:
            return e
    import wasser_vertieft as _wv
    e = np.zeros(tief.shape, np.uint8)
    for ab in STUFEN_ABSTAND:
        e += _wv._stufe(tief, ab).astype(np.uint8)
    np.save(pf, e)
    return e


def fundament(a, m, wasser):
    """Fundament der Plattform/Bruecke unter Wasser: das Mauerwerk setzt sich unter der Kaimauer in 5 Absaetzen bis
    zur tiefsten Stufe fort - jeder Absatz etwas breiter und tiefer, vom Wasser staerker ueberdeckt (zuerst die
    tiefsten). Rund um das Fundament ist das Wasser am tiefsten und dunkelsten."""
    Hh, W = m.shape
    yy, xx = np.mgrid[0:Hh, 0:W]
    def dil(mm, r):
        return np.array(Image.fromarray((mm * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(2 * r + 1))) > 0
    ring = dil(m, 14) & wasser & ~m
    a[ring] = (a[ring] * 0.72).astype(np.uint8)
    stein = np.array([46, 46, 60], np.float32)
    fuge = np.array([22, 22, 30], np.float32)
    for k in range(4, -1, -1):                                   # tiefster Absatz zuerst
        breite = 3 * (k + 1)
        unten = 24 + 9 * (k + 1)
        tier = np.roll(dil(m, breite), unten, 0) & wasser & ~m
        tier[:unten] = False
        if not tier.any():
            continue
        z = ((yy % 6 == 5) | ((xx + 4 * ((yy // 6) % 2)) % 10 == 9))
        farbe = np.where(z[..., None], fuge, stein)
        deck = 0.62 - 0.11 * k                                   # tiefer = staerker vom Wasser ueberdeckt
        a[tier] = np.clip(a[tier] * (1 - deck) + farbe[tier] * deck, 0, 255).astype(np.uint8)
        kante = tier & ~np.roll(tier, 1, 0)                      # Oberkante des Absatzes: heller Grat
        a[kante] = np.clip(a[kante] * 0.45 + np.array([88, 100, 140]) * 0.55 * (1 - 0.12 * k), 0, 255).astype(np.uint8)
        for d_, fa in ((1, 0.78), (2, 0.88)):                      # Schatten unter der Kante des Absatzes darueber
            sch = np.roll(kante, d_, 0) & tier
            a[sch] = (a[sch] * fa).astype(np.uint8)


def bannkreis(a, cx, cy, rx, ry, frame):
    """Bannkreis auf der Plattform: doppelter Ring mit Runenzeichen und eine dreiarmige Spirale in der Mitte
    (Spiral Mountain), violett leuchtend; das Leuchten pulsiert, die Spirale dreht sich langsam."""
    f = frame or 0
    Hh, W = a.shape[:2]
    puls = 0.6 + 0.4 * math.sin(2 * math.pi * f / N_FRAMES)
    hell = tuple(int(c * (0.75 + 0.25 * puls)) for c in VIOLETT)
    dunkel = tuple(int(c * 0.5) for c in VIOLETT)

    def setz(x, y, c):
        x, y = int(round(x)), int(round(y))
        if 0 <= x < W and 0 <= y < Hh:
            a[y, x] = c
    for (fr, c) in ((1.0, hell), (0.86, dunkel), (0.8, hell)):
        for i in range(720):
            w = 2 * math.pi * i / 720
            setz(cx + math.cos(w) * rx * fr, cy + math.sin(w) * ry * fr, c)
    for k in range(12):                                           # Runen zwischen den Ringen
        w = 2 * math.pi * k / 12
        x0, y0 = cx + math.cos(w) * rx * 0.93, cy + math.sin(w) * ry * 0.93
        for d in (-2, -1, 0, 1, 2):
            setz(x0 + d * math.sin(w), y0 - d * math.cos(w) * 0.5, hell if abs(d) < 2 else dunkel)
    dreh = 2 * math.pi * f / N_FRAMES / 3
    for arm in range(3):
        for i in range(160):
            t = i / 160
            w = dreh + arm * 2 * math.pi / 3 + t * 3.6
            r = t * 0.62
            setz(cx + math.cos(w) * rx * r, cy + math.sin(w) * ry * r, hell if i % 9 else dunkel)
    setz(cx, cy, (240, 220, 255))


def bauen(frame=None, speichern=True):
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cols, rows = lay['groesse']
    cls = lay['klassen']
    hoehe = np.array([[int(c) for c in r] for r in lay['hoehe']])
    Wp, Hp = cols * T, rows * T
    a = textur('d', cols, rows)
    # --- weiche Boeden: helle Asche, nasser Strand
    for art, bl, rausch, seed in (('m', 5.0, 0.45, 3), ('n', 4.0, 0.35, 5)):
        roh = zell_maske(cls, art, cols, rows)
        if art == 'n':
            roh = zell_maske(cls, 'nuh~', cols, rows)
        m = weich(roh, bl, rausch, seed)
        tx = textur(art, cols, rows)
        a[m] = tx[m]
        saum = weich(roh, bl, rausch, seed, 0.38) & ~m
        k4.dunkeln(a, saum, 0.9)
    # --- gebaute Flaechen scharf
    for art in 'bqfz':
        m = zell_maske(cls, art, cols, rows) > 0
        a[m] = textur(art, cols, rows)[m]
    # --- Ebenen: Plateaus (2), Berg (5)
    em = {}
    em[5] = weich(k8.stufe(hoehe, 5, cols, rows), 5, 0.3, 37)
    plat = (zell_maske(cls, 'v', cols, rows) > 0) | ((zell_maske(cls, 'r', cols, rows) > 0) & (k8.stufe(hoehe, 2, cols, rows) > 0)
                                                    & ~(k8.stufe(hoehe, 5, cols, rows) > 0))
    em[2] = plat | em[5]
    v = zell_maske(cls, 'v', cols, rows) > 0
    a[v] = textur('v', cols, rows)[v]
    fels = em[2] & ~v
    a[fels] = (textur('r', cols, rows)[fels] * np.array([0.56, 0.58, 0.66])).astype(np.uint8)   # dunkler Fels
    # --- Wasser
    wasser_roh = zell_maske(cls, 'uh~fz', cols, rows)        # um das Achteck herum ist Tiefsee
    wasser = weich(wasser_roh, 6, 0.25, 41, 0.5)
    flach = weich(zell_maske(cls, 'uh', cols, rows), 6, 0.25, 43, 0.5) & wasser
    seetang = weich(zell_maske(cls, 'h', cols, rows), 7, 0.35, 45, 0.5) & flach
    yy_, xx_ = np.mgrid[0:Hp, 0:Wp]
    dx_, dy_ = np.abs(xx_ - 69.5 * T), np.abs(yy_ - 39.5 * T)
    plattform = (dx_ <= 9.6 * T) & (dy_ <= 10.4 * T) & (dx_ / (9.6 * T) + dy_ / (10.4 * T) <= 1.45)   # Achteck
    a[plattform] = textur('f', cols, rows)[plattform]
    kreis_m = ((xx_ - 69.5 * T) / (5.2 * T)) ** 2 + ((yy_ - 38.5 * T) / (4.6 * T)) ** 2 <= 1
    a[kreis_m] = textur('z', cols, rows)[kreis_m]
    bruecke_m = np.zeros((Hp, Wp), bool)
    b_ = lay.get('bruecke')
    if b_:
        bruecke_m[b_[1] * T + 4:(b_[3] + 1) * T - 4, b_[0] * T - 8:(b_[2] + 1) * T + 4] = True
    wasser |= (zell_maske(cls, 'fz', cols, rows) > 0) & ~plattform    # um das Achteck bis zum Rand Wasser
    wasser &= ~plattform & ~bruecke_m & ~em[2]
    flach &= wasser
    meer_zeichnen(a, wasser, flach, seetang, frame)
    # Tiefsee im Stil des Flusses von Karte 01: Wassertextur, vertiefte Stufen mit Kanten (5 Stufen ueber die ganze
    # Meeresbreite bis zum Kartenrand), danach fuer das Meer der Finsternis abgedunkelt (Struktur bleibt erhalten)
    tief = (wasser & ~flach) | plattform | bruecke_m          # das Meer laeuft unter Plattform und Bruecke durch
    k4.wasser_zeichnen(a, tief, frame, np.zeros_like(tief))
    import wasser_vertieft as _wv
    a = np.array(_wv.vertiefen(Image.fromarray(a), np.ones_like(tief), frame, maske=tief,
                               rand=('#1c3a40', '#24484e', '#2e565c', '#386468'),
                               stufen=[(22, 0.84, 7), (64, 0.72, 6), (120, 0.62, 6), (190, 0.53, 5), (270, 0.45, 5)]).convert('RGB'))
    # dunkel wie das uebrige Wasser der Karte (Nachtblau der Vorlage): Helligkeit bleibt als Struktur, Farbe nachtblau
    lum_t = a[tief].astype(np.float32) @ np.array([0.3, 0.59, 0.11], np.float32)
    lum_t = lum_t / max(1.0, float(lum_t.mean()))
    a[tief] = np.clip(lum_t[:, None] * np.array([30, 36, 76], np.float32), 0, 255).astype(np.uint8)
    tm = weich(zell_maske(cls, 'x', cols, rows), 5, 0.2, 47, 0.45) & ~em[2]
    tm = k4.splitter_weg(tm, 60)
    k4.wasser_zeichnen(a, tm, frame, np.zeros_like(tm))
    import wasser_vertieft
    a = np.array(wasser_vertieft.vertiefen(Image.fromarray(a), np.ones_like(tm), frame, maske=tm,
                                           rand=('#16141c', '#201c28', '#2a2434', '#342c40'),
                                           stufen=[(14, 0.8, 5), (28, 0.65, 4)]).convert('RGB'))
    tuempel_zeichnen(a, tm, frame)
    # --- Plattform und Bruecke: Steinplatten, Ziegelrand, Kaimauer, Fundament bis in die tiefste Stufe
    a[plattform] = textur('f', cols, rows)[plattform]
    a[kreis_m] = textur('z', cols, rows)[kreis_m]
    bt = textur('q', cols, rows)
    a[bruecke_m] = bt[bruecke_m]
    ebenen_ = wasser_ebenen(tief)
    front = kaimauer(a, plattform, ebene=ebenen_)
    front |= bruecke_zeichnen(a, bruecke_m, ebenen_, tief | flach)
    bannkreis(a, 69.5 * T, 38.5 * T, 4.4 * T, 3.7 * T, frame)
    # --- Treppen (Suedseite der Plateaus) und Kanten
    treppen_info = []
    frei = np.zeros((Hp, Wp), bool)
    for (x0, x1, e) in lay.get('treppen', []):
        px0, px1 = x0 * T + 1, (x1 + 1) * T - 1
        oben = em[e] & ~em[5]
        ys_ = [int(np.nonzero(oben[:Hp // 2 if x0 < 20 else Hp, xc])[0].max()) for xc in range(px0, px1) if oben[:, xc].any()]
        for yb in sorted(set([max(ys_)])):
            frei[yb - 14:yb + FRONT[e] + 8, px0 - 6:px1 + 6] = True
            treppen_info.append((px0, px1, yb, FRONT[e], e))
    for (x0, x1, e, yb_kachel) in lay.get('treppen_sued', []):
        px0, px1 = x0 * T + 1, (x1 + 1) * T - 1
        yb = (yb_kachel + 1) * T - 1
        frei[yb - 14:yb + FRONT[e] + 8, px0 - 6:px1 + 6] = True
        treppen_info.append((px0, px1, yb, FRONT[e], e))
    waende = np.zeros((Hp, Wp), bool)
    waende |= k4.hoehenkanten(a, em[2] & ~em[5] | em[5], 'nacht', FRONT[2], 12, LIPPE_LILA, frei | em[5], 31, berg=False)
    waende |= k4.hoehenkanten(a, em[5], 'dunkelberg', FRONT[5], 12, LIPPE_BERG, frei, 35, berg=False)
    lvl = np.ones((Hp, Wp), np.uint8)
    lvl[em[2]] = 2
    lvl[em[5]] = 5
    lvl[plattform] = 2
    lvl[wasser & ~flach] = 0
    lvl[tm] = 0
    lvl[waende] = 9
    lvl[front] = 9
    if speichern and frame is None:
        np.save(os.path.join(KARTE, 'pixelhoehe.npy'), lvl)
    img = Image.fromarray(a).convert('RGBA')
    alt_S = bauwerke.S
    bauwerke.S = [H(c) + (255,) for c in k4.FELS['nacht']]
    alt_moos, alt_moos_st = bauwerke.MOOS, bauwerke.MOOS_STUFE
    bauwerke.MOOS = [(0x3a, 0x30, 0x46, 255), (0x4a, 0x3c, 0x58, 255)]   # lila Flechten statt Moos
    bauwerke.MOOS_STUFE = [(0x30, 0x28, 0x3c, 255), (0x40, 0x34, 0x4e, 255)]
    for (px0, px1, ye, f, e) in treppen_info:
        bauwerke.zeichne_treppe(img, px0 - 6, px1 + 6, ye + 2, ye + f + 2)
        for y in range(ye + 1, ye + f + 3):
            for x in range(px0 - 6, px1 + 6):
                lvl[min(Hp - 1, y), x] = 9
    bauwerke.S = alt_S
    bauwerke.MOOS, bauwerke.MOOS_STUFE = alt_moos, alt_moos_st
    a = np.array(img.convert('RGB'))
    for tp in lay.get('teleporter', []):
        k4.teleporter_zeichnen(a, tp['x'], tp['y'], tp['b'], tp['h'], frame)
    img = Image.fromarray(a).convert('RGBA')
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain_basis.png'))
    pf = os.path.join(OBJ, 'platzierung.json')
    if os.path.exists(pf):
        objs = sorted((o for o in json.load(open(pf)) if os.path.exists(os.path.join(OBJ, o['datei']))),
                      key=lambda o: (0 if o.get('an_wand') else 1, o['y'] + o['fuss']))
        cache = {o['datei']: Image.open(os.path.join(OBJ, o['datei'])).convert('RGBA') for o in objs}
        k8.schatten_ebene(img, [o for o in objs if not o.get('an_wand')], cache, lvl)
        vor_objekten = np.array(img)
        k4.objekte_zeichnen(img, objs, cache, np.zeros((Hp, Wp), bool), frame)
        k4.animieren(img, objs, cache, frame or 0, ruhig=frame is None)
        k8.verdeckung(img, [o for o in objs if not o.get('an_wand')], cache, lvl, vor_objekten)
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain.png'))
    print('Karte 11 %dx%d gebaut' % (cols, rows))
    return img


if __name__ == '__main__':
    bauen()
