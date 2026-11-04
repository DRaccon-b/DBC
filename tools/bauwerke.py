"""Handgezeichnete Bauwerke fuer Karte 01: Klippentreppen, Holzbruecken, Steg.

Wird von karte_bauen.py aufgerufen. Gleiche Regeln wie Klippen und Wasserfall:
Licht von oben links, Farben aus der Kartenpalette (Schiefer, Holz, Wasser), keine Streckung,
Masse exakt aus hoehenplan.json. Bruecken und Steg werfen Schatten aufs Wasser, Pfosten
haben Wasserringe (die im Animationsframe mitschimmern).
"""
import random
from klippen import S, WS, rgb

T = 16
HOLZ = [rgb(c) for c in ('#2a1a16', '#3a2420', '#5a3a2c', '#7a5236', '#9c6c44', '#c08c58', '#e0b47a')]
SEIL = (rgb('#d8b878'), rgb('#8a6a40'))
STEIN_HELL = S[5]


def _setz(px, W, H, x, y, c):
    if 0 <= x < W and 0 <= y < H:
        px[x, y] = c


def _abdunkeln(px, W, H, x, y, f=0.62):
    if 0 <= x < W and 0 <= y < H:
        r, g, b, a = px[x, y]
        px[x, y] = (int(r * f), int(g * f), int(b * (f + 0.08)), a)


# ---------------------------------------------------------------- Treppe
def zeichne_treppe(img, x0, x1, y_top, y_bot, seed=3):
    """Steintreppe in der Wandoeffnung x0..x1, von der Wiesenkante y_top bis zum Fuss y_bot."""
    rnd = random.Random(seed)
    px = img.load(); W, H = img.size
    wange = 5
    # Wangen: Schiefer wie die Klippe, Licht links, mit Abschlussstein und Grasbueschel oben
    for x in range(x0, x0 + wange):
        for y in range(y_top - 4, y_bot + 1):
            i = x - x0
            c = S[0] if i == 0 else S[4] if i == 1 else S[3] if i < wange - 1 else S[1]
            _setz(px, W, H, x, y, c)
    for x in range(x1 - wange, x1):
        for y in range(y_top - 4, y_bot + 1):
            i = x1 - 1 - x
            c = S[0] if i == 0 else S[2] if i < wange - 1 else S[1]
            _setz(px, W, H, x, y, c)
    for xs in (x0, x1 - wange):                      # Abschlusssteine oben
        for x in range(xs, xs + wange):
            _setz(px, W, H, x, y_top - 5, S[0])
            _setz(px, W, H, x, y_top - 4, S[5])
            _setz(px, W, H, x, y_top - 3, S[4])
        for k in range(3):                           # kleines Moos/Gras auf dem Stein
            _setz(px, W, H, xs + 1 + k, y_top - 6, (0x5f, 0xbb, 0x58, 255) if k != 1 else (0x93, 0xdb, 0x70, 255))
    # Stufen: Trittflaeche hell (oben), Setzstufe dunkel (vorne), je 6 px
    innen0, innen1 = x0 + wange, x1 - wange
    stufe = 6
    y = y_top - 2
    n = 0
    while y < y_bot:
        for x in range(innen0, innen1):
            rand_l = x == innen0
            for dy in range(stufe):
                yy = y + dy
                if yy >= y_bot + 1:
                    break
                if dy == 0:
                    c = S[6] if not rand_l else S[4]         # Lichtkante der Trittflaeche
                elif dy < 3:
                    c = S[5] if (x + n) % 11 else S[4]       # Trittflaeche
                elif dy < stufe - 1:
                    c = S[2] if not rand_l else S[1]         # Setzstufe
                else:
                    c = S[0]                                 # Fuge
                _setz(px, W, H, x, yy, c)
        # etwas Moos in den Ecken
        if rnd.random() < 0.6:
            mx = innen0 + (0 if rnd.random() < 0.5 else innen1 - innen0 - 2)
            _setz(px, W, H, mx, y + 3, (0x45, 0xa0, 0x52, 255))
            _setz(px, W, H, mx + 1, y + 2, (0x5f, 0xbb, 0x58, 255))
        y += stufe; n += 1
    # Licht von oben links: die linke Wange wirft einen schmalen Schatten auf die Stufen
    for y in range(y_top - 2, y_bot + 1):
        _abdunkeln(px, W, H, innen0, y, 0.72)
        _abdunkeln(px, W, H, innen0 + 1, y, 0.86)
    # unterste Stufe laeuft auf den Weg aus: weicher Schatten nur unter den Wangen
    for x in list(range(x0, x0 + wange)) + list(range(x1 - wange, x1)):
        for dy in (1, 2):
            _abdunkeln(px, W, H, x, y_bot + dy, 0.8)


# ---------------------------------------------------------------- Bruecke (Laufrichtung waagerecht)
def zeichne_bruecke(img, x0, x1, y0, y1, frame=0, seed=5):
    rnd = random.Random(seed)
    px = img.load(); W, H = img.size
    # Schatten aufs Wasser unter dem unteren Balken
    for x in range(x0 + 2, x1 - 1):
        for dy in range(1, 5):
            _abdunkeln(px, W, H, x, y1 + dy, 0.6 + dy * 0.07)
    # Planken quer zur Laufrichtung (senkrechte Bretter), je 4 px breit
    x = x0
    i = 0
    while x < x1:
        b = 4 if i % 5 else 5
        ton = 4 if i % 3 else 3
        vers = rnd.choice((0, 0, 1))                  # Bretter leicht versetzt
        for xx in range(x, min(x + b, x1)):
            for y in range(y0 + 3 - vers, y1 - 2 + vers):
                k = xx - x
                c = HOLZ[ton + 1] if k == 0 else HOLZ[1] if k == b - 1 else HOLZ[ton]
                if y == y0 + 3 - vers:
                    c = HOLZ[6] if k < b - 1 else HOLZ[2]     # Lichtkante oben
                _setz(px, W, H, xx, y, c)
        for ny in (y0 + 6, y1 - 6):                    # Naegel
            _setz(px, W, H, x + 1, ny, HOLZ[1])
        x += b; i += 1
    # Randbalken oben und unten
    for x in range(x0 - 1, x1 + 1):
        for y, c in ((y0, HOLZ[1]), (y0 + 1, HOLZ[5]), (y0 + 2, HOLZ[3]),
                     (y1 - 2, HOLZ[4]), (y1 - 1, HOLZ[2]), (y1, HOLZ[1])):
            _setz(px, W, H, x, y, c)
    # Pfosten an den Enden und in der Mitte, mit Seil dazwischen
    pfosten = [x0 - 1, (x0 + x1) // 2 - 2, x1 - 4]
    for yb in (y0, y1):
        for p in pfosten:
            unten = yb + (6 if yb == y1 else 2)          # untere Pfosten stehen als Pfaehle im Wasser
            for xx in range(p, p + 5):
                for yy in range(yb - 7, unten):
                    k = xx - p
                    c = HOLZ[1] if k in (0, 4) or yy == unten - 1 else HOLZ[5] if k == 1 else HOLZ[3]
                    if yy > yb + 1:
                        c = HOLZ[1] if k in (0, 4) else HOLZ[2]     # nasser, dunkler Pfahl
                    if yy == yb - 7:
                        c = HOLZ[1] if k in (0, 4) else HOLZ[6]
                    _setz(px, W, H, xx, yy, c)
        for a, b in zip(pfosten, pfosten[1:]):         # durchhaengendes Seil
            for xx in range(a + 5, b):
                t = (xx - a - 5) / max(1, b - a - 5)
                yy = yb - 5 + round(2.5 * 4 * t * (1 - t))
                _setz(px, W, H, xx, yy, SEIL[0])
                _setz(px, W, H, xx, yy + 1, SEIL[1])
    # Wasserringe an den Pfosten des unteren Balkens (schimmern je Frame)
    for p in pfosten:
        for k, xx in enumerate(range(p - 2, p + 7)):
            if (k + frame) % 3:
                _setz(px, W, H, xx, y1 + 7, WS['w4'] if k % 4 else WS['w5'])


# ---------------------------------------------------------------- Steg (Laufrichtung senkrecht)
def _pfosten(px, W, H, x, y_kopf, y_fuss, frame, ring=True):
    """Pfosten wie bei der Bruecke: 5 px breit, helle Kappe, dunkler nasser Fuss, Wasserring."""
    for xx in range(x, x + 5):
        for yy in range(y_kopf, y_fuss):
            k = xx - x
            c = HOLZ[1] if k in (0, 4) else HOLZ[5] if k == 1 else HOLZ[3]
            if yy == y_kopf:
                c = HOLZ[1] if k in (0, 4) else HOLZ[6]
            if yy > y_fuss - 4:
                c = HOLZ[1] if k in (0, 4) else HOLZ[2]
            _setz(px, W, H, xx, yy, c)
    if ring:
        for k, xx in enumerate(range(x - 2, x + 7)):
            if (k + frame) % 3:
                _setz(px, W, H, xx, y_fuss, WS['w4'] if k % 4 else WS['w5'])


def _planken(px, W, H, x0, x1, y0, y1, rnd):
    """Querplanken (Laufrichtung senkrecht), je 6 px: Lichtkante, Holz mit Maserung, dezente Fuge."""
    y, i = y0, 0
    while y < y1:
        ton = (3, 4, 4, 3, 4)[i % 5]
        vers_l, vers_r = rnd.choice((0, 0, 1)), rnd.choice((0, 0, 1))
        for yy in range(y, min(y + 6, y1)):
            k = yy - y
            for xx in range(x0 + vers_l, x1 - vers_r):
                if k == 0:
                    c = HOLZ[6] if xx < x1 - vers_r - 1 else HOLZ[4]
                elif k == 5:
                    c = HOLZ[2]
                else:
                    c = HOLZ[ton]
                    if k == 3 and (xx * 7 + i * 5) % 9 == 0:
                        c = HOLZ[ton - 1]                  # Maserung
                    if xx == x0 + vers_l:
                        c = HOLZ[5]                        # Licht von links
                    elif xx == x1 - vers_r - 1:
                        c = HOLZ[2]
                _setz(px, W, H, xx, yy, c)
        for nx in (x0 + 2, x1 - 3):                        # Naegel
            _setz(px, W, H, nx, y + 2, HOLZ[1])
        y += 6; i += 1


def zeichne_steg(img, x0, x1, y0, y1, frame=0, seed=9):
    """Steg von y0 (Weg-/Uferkante) bis y1, Breite x0..x1, mit breiterer Plattform am Ende."""
    rnd = random.Random(seed)
    px = img.load(); W, H = img.size
    plat = 22                                   # Laenge der Plattform
    px0, px1 = x0 - 6, x1 + 6                   # Plattform breiter
    # Schatten aufs Wasser (Licht von oben links -> rechts und unten)
    for y in range(y0 + 4, y1 + 5):
        rechts = px1 if y >= y1 - plat else x1
        for dx in range(1, 5):
            _abdunkeln(px, W, H, rechts + dx, y, 0.58 + dx * 0.08)
    for x in range(px0 + 3, px1 + 5):
        for dy in range(1, 5):
            _abdunkeln(px, W, H, x, y1 + dy, 0.58 + dy * 0.08)
    # Pfosten zuerst (stehen aussen, Holz liegt darueber)
    mitte = (y0 + y1 - plat) // 2
    for yp in (mitte,):
        _pfosten(px, W, H, x0 - 3, yp - 4, yp + 6, frame)
        _pfosten(px, W, H, x1 - 2, yp - 4, yp + 6, frame)
    for yp in (y1 - plat + 2, y1 - 2):
        _pfosten(px, W, H, px0 - 3, yp - 4, yp + 6, frame)
        _pfosten(px, W, H, px1 - 2, yp - 4, yp + 6, frame)
    # Laufsteg und Plattform
    _planken(px, W, H, x0 + 2, x1 - 2, y0, y1 - plat, rnd)
    _planken(px, W, H, px0 + 2, px1 - 2, y1 - plat, y1, rnd)
    # Laengsbalken (Licht links), an der Plattform nach aussen versetzt
    for yy in range(y0, y1 + 1):
        l, r = (px0, px1) if yy >= y1 - plat else (x0, x1)
        for xx, c in ((l, HOLZ[1]), (l + 1, HOLZ[4]), (r - 2, HOLZ[2]), (r - 1, HOLZ[1])):
            _setz(px, W, H, xx, yy, c)
    for xx in range(px0, px1):                  # Stirnbalken am Ende
        _setz(px, W, H, xx, y1, HOLZ[1]); _setz(px, W, H, xx, y1 - 1, HOLZ[3])
    for xx in range(px0, x0 + 1):               # Uebergang Steg -> Plattform
        _setz(px, W, H, xx, y1 - plat, HOLZ[1])
    for xx in range(x1 - 1, px1):
        _setz(px, W, H, xx, y1 - plat, HOLZ[1])
    # Poller mit Seil auf der Plattform (Anlegestelle)
    bx, by = px1 - 6, y1 - 10
    for xx in range(bx, bx + 3):
        for yy in range(by, by + 4):
            _setz(px, W, H, xx, yy, HOLZ[1] if xx in (bx, bx + 2) or yy == by + 3 else HOLZ[5])


# ---------------------------------------------------------------- Strassenlaterne (Objekt-Sprite)
GLAS = [rgb('#c87a2a'), rgb('#f5c842'), rgb('#fff2a0'), rgb('#fffbe6')]
EISEN = [rgb(c) for c in ('#161b28', '#232c40', '#35415c', '#4f5f80', '#7a8cb0')]
GRAS_L = [rgb(c) for c in ('#2e7a4c', '#45a052', '#5fbb58', '#78cc60', '#93db70')]
LATERNE_B, LATERNE_H = 15, 58
MAST_PLUS = 14               # zusaetzliche Masthoehe gegenueber der ersten Fassung
LATERNE_KOPF = (7, 9)        # Mitte des Glases (fuer den Lichtschein)


def laterne_bild():
    """Grosse Strassenlaterne 15x58 px, Silhouette exakt symmetrisch um x=7.

    Licht von oben links nur in der Schattierung. Unten: moosiger Steinsockel mit Grashalmen,
    die vorne ueber die Kanten wachsen (Kontaktschatten setzt karte_bauen.py darunter).
    """
    from PIL import Image
    B, H = LATERNE_B, LATERNE_H
    im = Image.new('RGBA', (B, H), (0, 0, 0, 0))
    px = im.load()
    M = 7

    def zeile(y, halb, fuell):
        """symmetrische Zeile von M-halb bis M+halb; fuell(dx) -> Farbe, dx = x - M"""
        for x in range(M - halb, M + halb + 1):
            c = fuell(x - M, halb)
            if c is not None:
                px[x, y] = c

    rand = lambda dx, h: EISEN[0] if abs(dx) == h else None
    def metall(dx, h):                       # Licht von links: links hell, rechts dunkel
        if abs(dx) == h:
            return EISEN[0]
        return EISEN[4] if dx == -h + 1 else EISEN[3] if dx < 0 else EISEN[2] if dx == 0 else EISEN[1]

    # Spitze und Dach
    zeile(0, 0, lambda dx, h: EISEN[0])
    zeile(1, 1, lambda dx, h: EISEN[0] if abs(dx) == 1 else EISEN[3])
    zeile(2, 1, metall)
    zeile(3, 3, metall)
    zeile(4, 5, metall)
    zeile(5, 6, lambda dx, h: EISEN[0])
    # Glaskasten (Zeilen 6-13), Sprossen bei dx = -3, 0, 3
    for y in range(6, 14):
        def glas(dx, h, y=y):
            if abs(dx) == h:
                return EISEN[0]
            if dx in (-3, 0, 3) or y == 13:
                return EISEN[1] if dx >= 0 else EISEN[2]
            if y == 6:
                return GLAS[2]
            if y in (8, 9, 10) and abs(dx) in (1, 2):
                return GLAS[3] if y == 9 else GLAS[2]
            if y == 12:
                return GLAS[0]
            return GLAS[1]
        zeile(y, 5, glas)
    px[M - 4, 7] = GLAS[3]                   # Glanz oben links
    zeile(14, 5, lambda dx, h: EISEN[0])
    zeile(15, 3, metall)                     # Kragen
    # Zierboegen links/rechts unter dem Kragen (spiegelgleich)
    for dy, dx in ((16, 3), (17, 4), (18, 4), (19, 3)):
        px[M - dx, dy] = EISEN[0]; px[M + dx, dy] = EISEN[0]
    zeile(16, 1, metall)
    P = MAST_PLUS
    # Mast 3 px + Kontur, Zierringe
    for y in range(17, 36 + P):
        zeile(y, 2, metall)
    for y in (22, 29 + P // 2, 36 + P - 7):
        zeile(y, 2, lambda dx, h: EISEN[0] if abs(dx) == 2 else EISEN[4] if dx < 0 else EISEN[2])
    # ausgestellter Fuss
    zeile(36 + P, 3, metall)
    zeile(37 + P, 4, metall)
    # Steinsockel (Schiefer wie die Klippen), oben Lichtkante
    for y in range(38 + P, 44 + P):
        def sockel(dx, h, y=y):
            if abs(dx) == h or y == 43 + P:
                return S[0]
            if y == 38 + P:
                return S[5] if dx < 2 else S[4]
            return S[4] if dx == -h + 1 else S[3] if dx < 0 else S[2]
        zeile(y, 5, sockel)
    # Moos am Sockelfuss und Grashalme vorne ueber den Kanten (spiegelgleich)
    for dx in (-4, -1, 2):
        px[M + dx, 42 + P] = GRAS_L[1]
    for dx in (-3, 1, 4):
        px[M + dx, 42 + P] = GRAS_L[2]
    for (dx, y, c) in ((-6, 43, 1), (-6, 42, 3), (-5, 43, 2), (-7, 43, 0),
                       (6, 43, 1), (6, 42, 3), (5, 43, 2), (7, 43, 0),
                       (-2, 43, 2), (2, 43, 2), (0, 43, 1)):
        px[M + dx, y + P] = GRAS_L[c]
    px[M - 6, 41 + P] = GRAS_L[4]; px[M + 6, 41 + P] = GRAS_L[4]
    return im


def laterne_glas_farben():
    return [g[:3] for g in GLAS]


# ---------------------------------------------------------------- Pflanzen: Gras- und Sand-Variante
def pflanzen_variante(sp, boden):
    """Pflanzen-Sprite mit Fuss fuer den Untergrund (4 px breiter, 3 px hoeher, Fuss an derselben Stelle).

    Gemeinsam: halbtransparenter Kontaktschatten (passt auf jedes Gruen/Beige) und leicht abgedunkelter
    Halmfuss, damit die Pflanze im Boden steckt statt aufgeklebt zu wirken.
    boden='gras': einzelne kurze Halme in den Grastoenen fransen nach aussen aus und gehen in die
    Wiesentextur ueber. boden='sand': flacher, unregelmaessiger Sandhuegel, der zu den Raendern hin
    ausduennt (Licht links, Schatten rechts/unten), dazu ein paar Sandkoerner und ein Kiesel.
    """
    import random
    from PIL import Image
    from basis_kacheln import RGB
    import numpy as np
    rnd = random.Random(hash((sp.size, boden, sp.tobytes()[:64])) & 0xffff)
    w, h = sp.size
    a = np.array(sp.getchannel('A')) > 0
    xs = np.nonzero(a[max(0, h - 3):].any(axis=0))[0]
    if len(xs) == 0:
        xs = np.array([w // 2])
    fx0, fx1 = int(xs.min()) + 2, int(xs.max()) + 2      # Fussbreite in neuen Koordinaten
    W, H = w + 4, h + 3
    cx, yb = (fx0 + fx1) / 2, h                          # Fussmitte (Zeile h = alte Unterkante + 1)
    rx = (fx1 - fx0) / 2 + 2.5

    # 1) Kontaktschatten (halbtransparent)
    schatten = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ps = schatten.load()
    farbe = (24, 70, 50) if boden == 'gras' else (120, 82, 52)
    for y in range(h - 2, H):
        for x in range(W):
            d = ((x - cx) / (rx + 1)) ** 2 + ((y - yb) / 2.2) ** 2
            if d <= 1.0:
                ps[x, y] = farbe + (int(120 if d < 0.45 else 70),)
    out = schatten

    # 2) Pflanze mit abgedunkeltem Fuss
    pfl = sp.convert('RGBA').copy()
    pp = pfl.load()
    for y in range(max(0, h - 2), h):
        f = 0.78 if y == h - 1 else 0.88
        for x in range(w):
            r_, g_, b_, a_ = pp[x, y]
            if a_:
                pp[x, y] = (int(r_ * f), int(g_ * f), int(b_ * f), a_)

    px = out.load()
    def setz(x, y, c):
        if 0 <= x < W and 0 <= y < H:
            px[x, y] = c + (255,)

    if boden == 'sand':
        # 3a) Sandhuegel hinter den Halmen: Mitte dicht, Rand ausgeduennt
        for y in range(h - 2, h + 2):
            for x in range(W):
                d = ((x - cx) / rx) ** 2 + ((y - (yb - 0.5)) / 1.8) ** 2
                if d > 1.0 or (d > 0.6 and rnd.random() < 0.55):
                    continue
                if y <= h - 2:
                    c = RGB['s4'] if x < cx else RGB['s3']
                elif y == h - 1:
                    c = RGB['s3'] if x < cx - 1 else RGB['s2']
                else:
                    c = RGB['s2'] if x < cx else RGB['s1']
                setz(x, y, c)
        out.alpha_composite(pfl, (2, 0))
        # Vorderkante des Huegels ueber den Halmen (Halme stecken im Sand)
        for x in range(int(cx - rx + 1), int(cx + rx)):
            if rnd.random() < 0.8:
                setz(x, h - 1, RGB['s3'] if x < cx else RGB['s2'])
            if rnd.random() < 0.6:
                setz(x, h, RGB['s2'] if x < cx else RGB['s1'])
        # Sandkoerner und ein kleiner Kiesel
        for _ in range(3):
            setz(int(cx + rnd.uniform(-rx - 2, rx + 2)), h + rnd.randint(0, 2), RGB[rnd.choice(('s1', 's4'))])
        kx = int(cx + rx) if rnd.random() < 0.5 else int(cx - rx - 1)
        setz(kx, h + 1, RGB['s4']); setz(kx + 1, h + 1, RGB['s1']); setz(kx + 1, h + 2, RGB['s0'])
    else:
        out.alpha_composite(pfl, (2, 0))
        # 3b) kurze Halme, die nach aussen ausfransen (vorne, unterschiedlich hoch)
        x = cx - rx - 1
        while x <= cx + rx + 1:
            xi = int(x)
            hoehe = rnd.choice((1, 2, 2, 3)) if abs(xi - cx) < rx else rnd.choice((1, 1, 2))
            for k in range(hoehe):
                y = h + 1 - k
                c = RGB['g4'] if k == hoehe - 1 else RGB['g2'] if k == 0 else RGB['g3']
                setz(xi, y, c)
            x += rnd.choice((1.5, 2, 2.5))
    return out


# ---------------------------------------------------------------- Bodenfuss fuer alle Objekte
FUSS_ARTEN = {
    # art: (Halm-Dichte auf Gras, max. Halmhoehe, Sandwall, Kontaktschatten-Staerke, Fuss abdunkeln)
    'stein': (0.55, 5, True, 120, 2),
    'busch': (0.45, 4, True, 110, 1),
    'baum':  (0.5, 4, True, 110, 2),
    'holz':  (0.5, 4, True, 110, 1),
    'klein': (0.3, 3, False, 80, 1),
}


def bodenfuss(sp, boden, art):
    """Objekt-Sprite mit Fuss fuer den Untergrund (4 px breiter, 3 px hoeher, Fuss an derselben Stelle).

    Erkennt die Auflagekante (unterste deckende Pixel je Spalte) und setzt dort: halbtransparenten
    Kontaktschatten, leicht abgedunkelten Fuss, auf Gras kurze Halme VOR der Unterkante (das Objekt
    steht im Gras), auf Sand einen kleinen, zum Rand ausduennenden Sandwall plus Koerner.
    """
    if art == 'pflanze':
        return pflanzen_variante(sp, boden)
    import random
    from PIL import Image
    from basis_kacheln import RGB
    import numpy as np
    dichte, hmax, wall, schatten_a, dunkel_n = FUSS_ARTEN[art]
    rnd = random.Random(hash((sp.size, boden, art, sp.tobytes()[:96])) & 0xffff)
    w, h = sp.size
    a = np.array(sp.getchannel('A')) >= 200
    W, H = w + 4, h + 3
    # Auflagekante: je Spalte die unterste deckende Zeile; Kontakt = innerhalb 3 px der tiefsten
    unten = {x: int(np.nonzero(a[:, x])[0].max()) for x in range(w) if a[:, x].any()}
    if not unten:
        return sp
    tief = max(unten.values())
    kontakt = sorted(x + 2 for x, y in unten.items() if y >= tief - 2)
    k0, k1 = kontakt[0], kontakt[-1]
    cx, yb = (k0 + k1) / 2, tief + 1                     # yb: Zeile direkt unter dem Fuss (neue Koord.)
    rx = (k1 - k0) / 2 + 2.5

    out = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    po = out.load()
    farbe = (24, 70, 50) if boden == 'gras' else (120, 82, 52)
    for y in range(yb - 3, min(H, yb + 3)):
        for x in range(W):
            d = ((x - cx) / (rx + 1)) ** 2 + ((y - yb + 0.5) / 2.3) ** 2
            if d <= 1.0:
                po[x, y] = farbe + (int(schatten_a if d < 0.45 else schatten_a * 0.55),)

    obj = sp.convert('RGBA').copy()
    pp = obj.load()
    for x, y in unten.items():                           # Fuss abdunkeln (steckt im Boden)
        if y >= tief - 2:
            for k in range(dunkel_n):
                if y - k >= 0 and pp[x, y - k][3]:
                    r_, g_, b_, a_ = pp[x, y - k]
                    f = 0.75 if k == 0 else 0.87
                    pp[x, y - k] = (int(r_ * f), int(g_ * f), int(b_ * f), a_)

    def setz(x, y, c):
        if 0 <= x < W and 0 <= y < H:
            po[x, y] = c + (255,)

    if boden == 'sand' and wall:
        out.alpha_composite(obj, (2, 0))
        for x in range(int(cx - rx), int(cx + rx) + 1):  # Sandwall vor der Unterkante
            rand = abs(x - cx) / rx
            if rnd.random() < 0.85 - rand * 0.5:
                setz(x, yb - 1, RGB['s3'] if x < cx else RGB['s2'])
            if rnd.random() < 0.75 - rand * 0.4:
                setz(x, yb, RGB['s2'] if x < cx else RGB['s1'])
        for _ in range(3):
            setz(int(cx + rnd.uniform(-rx - 2, rx + 2)), yb + rnd.randint(0, 1), RGB[rnd.choice(('s1', 's4'))])
    elif boden == 'sand':
        out.alpha_composite(obj, (2, 0))
        for _ in range(2):
            setz(int(cx + rnd.uniform(-rx, rx)), yb, RGB['s1'])
    else:
        out.alpha_composite(obj, (2, 0))
        # Grasbueschel (2-3 Halme) vor der Unterkante: unten dunkel, Spitze hell, ragen ueber die
        # Auflagekante; an den Kontaktspalten dichter, nach aussen kleiner und seltener
        def halm(xi, hoehe, neigung):
            for kk in range(hoehe):
                y = yb + 1 - kk
                xx = xi + (neigung if kk >= hoehe - 1 and hoehe > 2 else 0)
                c = RGB['g1'] if kk == 0 else RGB['g4'] if kk == hoehe - 1 else RGB['g2'] if kk == 1 else RGB['g3']
                setz(xx, y, c)
        x = k0 - 3.0
        while x <= k1 + 3:
            xi = int(x)
            innen = k0 <= xi <= k1
            if rnd.random() < (dichte if innen else dichte * 0.45):
                gross_ = hmax if innen else max(2, hmax - 2)
                hoehen = [rnd.randint(gross_ - 2, gross_), rnd.randint(max(1, gross_ - 1), gross_ + 1),
                          rnd.randint(max(1, gross_ - 3), gross_ - 1)]
                for k, hh in enumerate(hoehen[: rnd.choice((2, 3))]):
                    halm(xi + k, max(1, hh), (-1, 0, 1)[k])
                x += rnd.choice((3, 4, 5))
            else:
                x += rnd.choice((2, 3))
    return out
