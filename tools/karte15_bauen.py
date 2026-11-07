"""Karte 15 (Apocalymon's Realm): eine runde Steininsel schwebt in der Leere. Ringsum der Sternenraum mit Nebel und
flackernden Datenstrichen, die Insel aus Steinziegeln mit dunklem Randring und magenta glimmender Kante, darunter
der felsige Inselbauch, der sich nach unten in die Leere verliert (violette Leuchtadern). In der Mitte reisst der
Boden auf: der Riss in die Leere (Boss-Spawn) mit Innenwand, Wirbel und Sternen in der Tiefe. Nach Sueden ein
Steinsteg mit Bordsteinen zum Teleporter am unteren Rand. Anspielung nur ueber Farben und Motive (Leere, Daten,
verlorene Welten), nichts nachgebaut.

  python3 tools/karte15_layout.py && python3 tools/karte15_kacheln.py
  python3 tools/karte15_bauen.py && python3 tools/karte15_objekte.py && python3 tools/karte15_bauen.py
"""
import json, math, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageFilter
import karte_bauen as kb
import karte04_bauen as k4
import karte08_bauen as k8
import karte14_bauen as k14                                       # registriert 'auge' (Obelisk blinzelt)

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte15')
BASIS = os.path.join(ROOT, 'assets', 'karte15', 'basis')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte15')
T = 16
N_FRAMES = 4                     # Regel: hoechstens 4 Animationsbilder
k4.N_FRAMES = k14.N_FRAMES = N_FRAMES
BILDDAUER = 250                  # ms je Bild
MIT_LOCH = False                 # True: Variante mit violettem Loch in der Mitte (nur fuer das Extra-GIF)
H = k4.H
k4.FELS['leerfels'] = ['#0e0c16', '#16131f', '#1e1a2a', '#282338', '#332d46', '#403a56', '#504a68']
MAGENTA = np.array([226, 70, 200], np.float32)
VIOLETT = np.array([150, 90, 230], np.float32)


def textur(art, cols, rows):
    t = np.zeros((rows * T, cols * T, 3), np.uint8)
    ks = [np.array(Image.open(os.path.join(BASIS, '%s_%d.png' % (art, v))).convert('RGB')) for v in range(5)]
    for y in range(rows):
        for x in range(cols):
            t[y * T:(y + 1) * T, x * T:(x + 1) * T] = ks[kb.variante(x, y)]
    return t


def abstand_innen(m, maxd):
    """Abstand jedes Pixels der Maske zum Rand (px, bis maxd)."""
    d = np.zeros(m.shape, np.int16)
    m_ = m.copy()
    for i in range(1, maxd + 1):
        m_ = np.array(Image.fromarray((m_ * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(3))) > 0
        d[m_] = i
        if not m_.any():
            break
    return d


def kontur(m):
    return m & ~(np.roll(m, 1, 0) & np.roll(m, -1, 0) & np.roll(m, 1, 1) & np.roll(m, -1, 1))


def mischen(a, m, farbe, s):
    a[m] = np.clip(a[m] * (1 - s) + np.array(farbe, np.float32) * s, 0, 255).astype(np.uint8)


def puls(frame, ph=0.0, takt=1):
    return 0.5 + 0.5 * math.sin(2 * math.pi * ((frame or 0) * takt / N_FRAMES + ph))


def schweben(sp, frame, o):
    """Schwebende Brocken in der Leere heben und senken sich langsam als Ganzes (bis 2 px), jeder im eigenen Takt."""
    d = (0, 1, 0, -1)[(frame + (o.get('x', 0) // 37)) % 4]       # 4 Bilder: Mitte, oben... 1 px auf und ab
    out = Image.new('RGBA', sp.size)
    out.paste(sp, (0, d))
    return out


k4.TEILANIM['schweben'] = schweben


# ---------------------------------------------------------------------------------------------- Leere
def nebel(a, leer, seed):
    """Weicher Nebel in der Leere (statisch): zwei Schichten Violett und Tiefblau."""
    Hh, W = leer.shape
    for farbe, staerke, sd, gross in (((52, 26, 84), 0.55, seed, 7), ((18, 34, 80), 0.45, seed + 1, 5),
                                      ((90, 30, 90), 0.25, seed + 2, 11)):
        rs = np.random.RandomState(sd)
        n = rs.rand(gross, gross)
        m = np.array(Image.fromarray((n * 255).astype(np.uint8)).resize((W, Hh), Image.BICUBIC)).astype(np.float32) / 255
        m = np.clip((m - 0.45) / 0.55, 0, 1) ** 1.6 * staerke
        m = np.where(leer, m, 0)[..., None]
        a[:] = np.clip(a * (1 - m) + np.array(farbe, np.float32) * m, 0, 255).astype(np.uint8)


def sterne(a, himmel, frame, seed=1515, dichte=9):
    """Funkelnde Sterne: Punkte, Kreuze und Funkelsterne in Weiss, Violett, Gold und Blau, jeder im eigenen Takt."""
    f = frame or 0
    Hh, W = himmel.shape
    rs = random.Random(seed)
    ys, xs = np.nonzero(himmel[::5, ::5])
    farben = [(240, 240, 255), (200, 170, 255), (255, 220, 140), (170, 200, 255), (255, 170, 230)]
    for _ in range(len(ys) // dichte):
        i = rs.randrange(len(ys)); y, x = int(ys[i]) * 5 + rs.randint(0, 4), int(xs[i]) * 5 + rs.randint(0, 4)
        art = rs.choices(('punkt', 'kreuz', 'funkel'), weights=(6, 3, 1))[0]
        farbe = np.array(rs.choice(farben), np.float32)
        takt = rs.choice((1, 1, 2))
        ph = (f * takt / N_FRAMES + rs.random()) % 1.0
        k_ = max(0.0, math.sin(ph * 2 * math.pi)) ** 1.5
        if art == 'punkt':
            k_ = 0.35 + 0.65 * k_                                 # kleine Sterne verschwinden nie ganz
        if k_ < 0.08:
            continue

        def setz(X, Y, s_):
            if 0 <= X < W and 0 <= Y < Hh and himmel[Y, X]:
                a[Y, X] = np.clip(a[Y, X] * (1 - s_) + farbe * s_, 0, 255).astype(np.uint8)
        setz(x, y, 0.5 + 0.5 * k_)
        if art == 'kreuz' and k_ > 0.4:
            for d in (-1, 1):
                setz(x + d, y, 0.45 * k_); setz(x, y + d, 0.45 * k_)
        if art == 'funkel':
            lang = 1 + int(round(2 * k_))
            for d in range(1, lang + 1):
                s_ = (0.75 - 0.2 * d) * k_
                setz(x + d, y, s_); setz(x - d, y, s_); setz(x, y + d, s_); setz(x, y - d, s_)


def datenstriche(a, leer, frame, seed=77):
    """Flackernde Datenstriche (Glitch) in der Leere: kleine Gruppen kurzer Striche in Cyan, Magenta und Gruen,
    wie in der Vorlage. Sie flackern im eigenen Takt und springen ab und zu um 1-2 px."""
    f = frame or 0
    Hh, W = leer.shape
    rs = random.Random(seed)
    farben = [(70, 230, 230), (230, 80, 200), (110, 230, 120), (150, 110, 250)]
    n = 0
    while n < 34:
        x, y = rs.randint(4, W - 20), rs.randint(4, Hh - 8)
        if not leer[max(0, y - 6):y + 8, max(0, x - 6):x + 20].all():
            rs.random(); continue
        n += 1
        ph, takt = rs.random(), rs.choice((1, 2, 2, 3))
        zeilen = [(rs.randint(0, 3), rs.randint(3, 9), rs.choice(farben)) for _ in range(rs.randint(1, 3))]
        an = math.sin(2 * math.pi * (f * takt / N_FRAMES + ph))
        if an < -0.3:
            continue
        sprung = 1 if ((f + int(ph * 16)) % 5 == 0) else 0
        for j, (dx, lang, c) in enumerate(zeilen):
            s_ = 0.55 + 0.35 * max(0.0, an)
            for k_ in range(lang):
                X, Y = x + dx + k_ + sprung * (j + 1), y + j * 2
                if 0 <= X < W and 0 <= Y < Hh and leer[Y, X]:
                    a[Y, X] = np.clip(a[Y, X] * (1 - s_) + np.array(c, np.float32) * s_, 0, 255).astype(np.uint8)


# ---------------------------------------------------------------------------------------------- Insel
def insel_maske(Wp, Hp, cx, cy, r):
    yy, xx = np.mgrid[0:Hp, 0:Wp]
    w = np.arctan2(yy + 0.5 - cy, xx + 0.5 - cx)
    rr = r + 2.2 * np.sin(5 * w + 1.0) + 1.4 * np.sin(11 * w + 0.3) + 0.8 * np.sin(23 * w)
    return np.hypot(xx + 0.5 - cx, yy + 0.5 - cy) <= rr


def riss_maske(Wp, Hp, cx, cy):
    """Rundes Kreuz wie in der Vorlage, mit leicht zerrissenem Rand."""
    yy, xx = np.mgrid[0:Hp, 0:Wp]
    dx, dy = np.abs(xx + 0.5 - cx), np.abs(yy + 0.5 - cy)
    w = np.arctan2(yy + 0.5 - cy, xx + 0.5 - cx)
    zack = 0.9 * np.sin(13 * w + 0.7) + 0.6 * np.sin(29 * w)
    arm = lambda lx, ly, rad: (np.hypot(np.maximum(dx - (lx - rad), 0), np.maximum(dy - (ly - rad), 0)) <= rad + zack)
    m = arm(58, 26, 10) | arm(26, 58, 10)
    zu = np.array(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.MinFilter(9))) > 0
    return zu                                                     # Innenecken des Kreuzes leicht gerundet
    return m


def unterseite(a, insel, steg_px, cx, cy_, r, frame, seed=15):
    """Inselbauch: unter der Suedkante haengt der Fels und verliert sich nach unten in der Leere. Tiefe nach einer
    Ellipse (in der Mitte am tiefsten, an den Seiten nur eine schmale Kante), unten zackige Felszapfen, violette
    Leuchtadern pulsieren. Wo der Steg liegt, verdeckt er den Bauch."""
    Hh, W = insel.shape
    rs = random.Random(seed)
    ft = textur('f', W // T, 10)                                  # Felsbrocken der Karte-08-Kacheln, umgefaerbt
    lum = ft.astype(np.float32).mean(axis=2)
    lum = (lum - lum.min()) / max(1.0, lum.max() - lum.min())
    pal = np.array([H(c) for c in k4.FELS['leerfels']], np.float32)
    tex = pal[np.clip((lum * 0.999 * (len(pal) - 1)).astype(int) + 0, 0, len(pal) - 1)]
    F = [np.array(H(c), np.float32) for c in k4.FELS['leerfels']]
    leer_c = np.array(H('#0e1020'), np.float32)
    bauch = np.zeros((Hh, W), bool)
    tiefe = {}
    zapf = 0.0
    for x in range(W):
        sp = np.nonzero(insel[:, x])[0]
        if not len(sp):
            continue
        t = (x + 0.5 - cx) / r
        if abs(t) >= 1:
            continue
        zapf = 0.75 * zapf + rs.uniform(-5, 5)
        spitze = 22 * max(0.0, math.sin(x * 0.29 + 1.3)) ** 8 + 14 * max(0.0, math.sin(x * 0.13 + 0.4)) ** 10
        y0 = int(sp.max())
        unten = cy_ + (r + 128) * (1 - t * t) ** 0.75             # Kegel: in der Mitte tief, aussen flach
        D = int(max(5, unten - y0 + (zapf + spitze) * (1 - t * t) ** 0.5))
        tiefe[x] = (y0, D)
    for x, (y0, D) in tiefe.items():
        t = (x + 0.5 - cx) / r
        for d in range(D):
            Y = y0 + 1 + d
            if Y >= Hh:
                break
            if insel[Y, x]:
                break
            bauch[Y, x] = True
            if steg_px[Y, x]:
                continue
            c = tex[min(d, 159), x].astype(np.float32) * (1.08 - 0.3 * (t + 1) / 2)   # links Licht, rechts Schatten
            if d < 2:
                c = F[5] if d == 0 else F[4]                      # Lippe (Licht von oben)
            elif d < 5:
                c = c * 0.8                                       # Schatten unter der Lippe
            q = d / max(1, D)
            c = c * (1 - 0.35 * q)
            if q > 0.55:                                          # verliert sich in der Leere
                s_ = ((q - 0.55) / 0.45) ** 1.2
                c = c * (1 - s_) + leer_c * s_
            if d == D - 1 or (x - 1 in tiefe and d >= tiefe[x - 1][1]) or (x + 1 in tiefe and d >= tiefe[x + 1][1]):
                c = c * 0.7                                       # dunkle Kontur der Zapfen
            if x > 0 and x - 1 not in tiefe and d > 1:
                c = c * 0.7
            a[Y, x] = np.clip(c, 0, 255).astype(np.uint8)
    # Leuchtadern: zackige Risse von der Lippe nach unten, Licht der Leere pulsiert
    p = 0.55 + 0.45 * puls(frame)
    for k_ in range(14):
        x = int(cx + rs.uniform(-0.85, 0.85) * r)
        if x not in tiefe:
            continue
        y0, D = tiefe[x]
        lang = int(D * rs.uniform(0.35, 0.7))
        y = y0 + 4
        farbe = MAGENTA if k_ % 3 == 0 else VIOLETT
        for t in range(lang):
            Y = y + t
            if 0 <= Y < Hh and 0 <= x < W and bauch[Y, x] and not steg_px[Y, x]:
                s_ = (0.85 - 0.6 * t / max(1, lang)) * p
                a[Y, x] = np.clip(a[Y, x] * (1 - s_) + farbe * s_, 0, 255).astype(np.uint8)
            if rs.random() < 0.3:
                x += rs.choice((-1, 1))
    return bauch


def riss_zeichnen(a, riss, cx, cy, frame, vtex):
    """Boss-Feld in der Mitte: fester, begehbarer Boden aus dunklem Leere-Gestein (Kreuz, am 16er-Raster gestuft).
    Darin dreht sich langsam ein violetter Wirbel, die Mitte pulsiert, Funken glitzern; am Rand eine magenta
    glimmende Kante mit dunklem Saum."""
    f = frame or 0
    Hh, W = riss.shape
    yy, xx = np.mgrid[0:Hh, 0:W]
    d = np.hypot(xx + 0.5 - cx, yy + 0.5 - cy)
    w = np.arctan2(yy + 0.5 - cy, xx + 0.5 - cx)
    a[riss] = vtex[riss]
    dreh = 2 * math.pi * f / N_FRAMES / 3                         # Drittelumdrehung pro Schleife
    arm = (np.sin(3 * (w - dreh) + d * 0.11) + 1) / 2
    s_ = (arm ** 3) * np.clip(1 - d / 64.0, 0, 1) * 0.7
    m = riss & (s_ > 0.02)
    a[m] = np.clip(a[m] * (1 - s_[m, None]) + np.array([120, 56, 180], np.float32) * s_[m, None], 0, 255).astype(np.uint8)
    p = puls(frame)
    mischen(a, riss & (d <= 7 + 2 * p), (200, 150, 255), 0.45 + 0.35 * p)
    mischen(a, riss & (d <= 3), (240, 220, 255), 0.6 + 0.3 * p)
    sterne(a, riss & (d > 9), frame, seed=1616, dichte=14)
    aussen = kontur(np.array(Image.fromarray((riss * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3))) > 0) & ~riss
    a[aussen] = (a[aussen] * 0.55).astype(np.uint8)
    mischen(a, kontur(riss), MAGENTA, 0.45 + 0.4 * p)
    return np.zeros_like(riss)


def bodenzeichen(a, boden, cx, cy, frame):
    """Eingelassene Zeichen im Inselboden: zwei helle Ringe, dazwischen kleine Glyphen, acht feine Strahlen zum
    Riss; von der Bruchkante laufen Risse mit violettem Licht durch den Stein (pulsiert langsam)."""
    Hh, W = boden.shape
    yy, xx = np.mgrid[0:Hh, 0:W]
    d = np.hypot(xx + 0.5 - cx, yy + 0.5 - cy)
    w = np.arctan2(yy + 0.5 - cy, xx + 0.5 - cx)
    hell = lambda m, f_: a.__setitem__(m, np.clip(a[m] * f_, 0, 255).astype(np.uint8))
    for rr in (142, 130):
        hell(boden & (np.abs(d - rr) <= 1.0), 1.22)
    for k_ in range(16):                                          # Glyphen zwischen den Ringen
        ww = 2 * math.pi * k_ / 16 + math.pi / 16
        X, Y = int(cx + math.cos(ww) * 136), int(cy + math.sin(ww) * 136)
        g = np.zeros_like(boden)
        if k_ % 2:
            g[Y - 2:Y + 3, X] = True; g[Y, X - 2:X + 3] = True
        else:
            g[Y - 2:Y + 3, X - 2:X + 3] = True; g[Y - 1:Y + 2, X - 1:X + 2] = False
        hell(g & boden, 1.25)
    for k_ in range(8):                                           # Strahlen vom Riss zum inneren Ring
        ww = 2 * math.pi * k_ / 8 + math.pi / 8
        strahl = (np.abs(((w - ww + math.pi) % (2 * math.pi)) - math.pi) * d <= 0.8) & (d > 74) & (d < 129)
        hell(strahl & boden, 1.16)
    rs = random.Random(1501)
    p = 0.55 + 0.45 * puls(frame, 0.3)
    for k_ in range(11):                                          # Risse mit Licht aus der Leere
        ww = 2 * math.pi * k_ / 11 + rs.uniform(-0.15, 0.15)
        x, y = cx + math.cos(ww) * 62, cy + math.sin(ww) * 62
        for t in range(rs.randint(20, 46)):
            X, Y = int(x), int(y)
            if 0 <= X < W and 0 <= Y < Hh and boden[Y, X]:
                a[Y, X] = H('#160e20')
                if t % 3 == 0:
                    s_ = (0.9 - t / 70.0) * p
                    a[Y, X] = np.clip(a[Y, X] * (1 - s_) + VIOLETT * s_, 0, 255).astype(np.uint8)
            x += math.cos(ww) + rs.uniform(-0.6, 0.6); y += math.sin(ww) + rs.uniform(-0.6, 0.6)


def bauen(frame=None, speichern=True):
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cols, rows = lay['groesse']
    Wp, Hp = cols * T, rows * T
    cx, cy, rad = [v * T for v in lay['platte']]
    sx0, sx1, sy0 = lay['steg']
    # ------------------------------------------------------------------ Leere
    a = textur('leer', cols, rows)
    kl = np.array([list(r) for r in lay['klassen']])
    gross = lambda m: np.kron(m, np.ones((T, T), int)).astype(bool)   # Kachelraster -> Pixel (Rand am 16er-Raster)
    ty, tx = np.mgrid[0:rows, 0:cols]
    im_kreis = np.hypot(tx + 0.5 - lay['platte'][0], ty + 0.5 - lay['platte'][1]) <= lay['platte'][2]
    insel = gross(np.isin(kl, list('prv')) | ((kl == 's') & im_kreis))
    steg = gross(kl == 's')
    leer = ~(insel | steg)
    nebel(a, leer, 150)
    # ------------------------------------------------------------------ Insel: Boden, Randring, Kante
    a[insel] = textur('p', cols, rows)[insel]
    bx0, bx1 = sx0 * T, (sx1 + 1) * T
    ring = gross(kl == 'r')
    a[ring] = textur('r', cols, rows)[ring]
    innen = insel & ~ring & ~steg
    a[innen & np.roll(ring, -1, 0)] = H('#22202c')                # Stufe Ring -> Boden: Kante unten dunkel,
    a[innen & np.roll(ring, 1, 0)] = H('#7a7890')                 # oben Licht
    a[innen & (np.roll(ring, 1, 1) | np.roll(ring, -1, 1))] = H('#4e4c60')
    if MIT_LOCH:                                                  # Variante: violettes Loch (gestuftes Kreuz) in der Mitte
        dx_, dy_ = np.abs(tx + 0.5 - lay['platte'][0]), np.abs(ty + 0.5 - lay['platte'][1])
        riss = gross(((dx_ <= 1.5) & (dy_ <= 3.5)) | ((dx_ <= 3.5) & (dy_ <= 1.5)) | ((dx_ <= 2.5) & (dy_ <= 2.5)))
        boden = innen & ~riss
    else:
        riss = gross(kl == 'v')
        boden = innen                                             # Mitte mit Pflaster gefuellt (Nutzerwunsch)
    bodenzeichen(a, boden, cx, cy, frame)
    # ------------------------------------------------------------------ Steg mit Bordsteinen
    st = textur('s', cols, rows)
    deck = steg & ~insel
    a[deck] = st[deck]
    bx0, bx1 = sx0 * T, (sx1 + 1) * T
    bord = np.zeros((Hp, Wp), bool)
    for x0, x1 in ((bx0, bx0 + 6), (bx1 - 6, bx1)):
        bord[:, x0:x1] = True
    bord &= steg
    rt = textur('r', cols, rows)
    a[bord] = rt[bord]
    zeilen = np.nonzero(bord[:, bx0])[0]
    for x, c in ((bx0 + 5, '#1a1824'), (bx0, '#5a5870'), (bx1 - 6, '#1a1824'), (bx1 - 1, '#24222e')):
        a[zeilen, x] = H(c)                                       # Kanten der Bordsteine (Licht von links oben)
    frei = np.nonzero((steg & ~insel)[:, bx0 + 6])[0]
    a[frei, bx0 + 6] = (a[frei, bx0 + 6] * 0.78).astype(np.uint8)  # Bordschatten auf dem Deck
    a[frei, bx0 + 7] = (a[frei, bx0 + 7] * 0.9).astype(np.uint8)
    # ------------------------------------------------------------------ Inselbauch, Kanten, Riss
    land = insel | steg
    bauch = unterseite(a, insel, steg, cx, cy, rad, frame)
    p = puls(frame, 0.15)
    aussenkante = kontur(land)
    a[aussenkante] = H('#14121c')
    innen1 = kontur(land & ~aussenkante)
    mischen(a, innen1, MAGENTA, 0.5 + 0.3 * p)                   # magenta glimmende Inselkante (wie die Vorlage)
    if MIT_LOCH:
        wand_riss = riss_zeichnen(a, riss, cx, cy, frame, textur('v', cols, rows))
    else:
        wand_riss = np.zeros_like(riss)                          # kein Riss mehr: Mitte ist Pflaster
    leer_rest = leer & ~bauch
    sterne(a, leer_rest, frame)
    datenstriche(a, leer_rest, frame)
    for tp in lay.get('teleporter', []):
        k4.teleporter_zeichnen(a, tp['x'], tp['y'], tp['b'], tp['h'], frame)
    lvl = np.zeros((Hp, Wp), np.uint8)
    lvl[land] = 2
    lvl[bauch & ~steg] = 9
    lvl[bord & ~insel] = 9
    if speichern and frame is None:
        np.save(os.path.join(KARTE, 'pixelhoehe.npy'), lvl)
        np.save(os.path.join(KARTE, 'wasser.npy'), np.packbits(np.zeros((Hp, Wp), bool)))
        np.save(os.path.join(KARTE, 'leere.npy'), np.packbits(leer_rest))
    img = Image.fromarray(a).convert('RGBA')
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain_basis.png'))
    pf = os.path.join(OBJ, 'platzierung.json')
    if os.path.exists(pf):
        objs = sorted((o for o in json.load(open(pf)) if os.path.exists(os.path.join(OBJ, o['datei']))),
                      key=lambda o: (0 if o.get('schwebt') else 1, o['y'] + o['fuss']))
        cache = {o['datei']: Image.open(os.path.join(OBJ, o['datei'])).convert('RGBA') for o in objs}
        k8.schatten_ebene(img, [o for o in objs if not o.get('schwebt')], cache, lvl)
        vor_objekten = np.array(img)
        k4.objekte_zeichnen(img, objs, cache, np.zeros((Hp, Wp), bool), frame)
        img = img.copy()
        k4.animieren(img, objs, cache, frame or 0, ruhig=frame is None)
        k8.verdeckung(img, [o for o in objs if not o.get('schwebt')], cache, lvl, vor_objekten)
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain.png'))
    print('Karte 15 %dx%d gebaut' % (cols, rows))
    return img


if __name__ == '__main__':
    bauen()
