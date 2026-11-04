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


# ---------------------------------------------------------------- Laterne (Objekt-Sprite)
GLAS = [rgb('#c87a2a'), rgb('#f5c842'), rgb('#fff2a0'), rgb('#fffbe6')]


def laterne_bild():
    """Laterne 11x26 px: Sockelstein, Holzpfahl, Ausleger, Schiefergehaeuse mit leuchtendem Glas."""
    from PIL import Image
    im = Image.new('RGBA', (11, 26), (0, 0, 0, 0))
    px = im.load()
    def s(x, y, c):
        px[x, y] = c
    # Sockelstein
    for x in range(2, 9):
        for y in range(22, 26):
            c = S[0] if x in (2, 8) or y == 25 else S[5] if y == 22 else S[3] if x < 5 else S[2]
            s(x, y, c)
    # Pfahl (3 px, Licht links)
    for y in range(9, 22):
        s(4, y, HOLZ[1]); s(5, y, HOLZ[5]); s(6, y, HOLZ[3]); s(7, y, HOLZ[1])
        if y in (12, 17):
            s(5, y, HOLZ[4])
    s(4, 21, HOLZ[1]); s(6, 21, HOLZ[1])
    for x in range(3, 8):                               # Bodenplatte unter dem Glas
        s(x, 10, S[0] if x in (3, 7) else S[2])
    # Dach (spitz, Schiefer)
    for y, (a, b) in enumerate(((5, 5), (4, 6), (3, 7))):
        for x in range(a, b + 1):
            s(x, y, S[0] if x in (a, b) else S[5] if x <= 5 else S[3])
    for x in range(1, 10):                              # Dach steht ueber
        s(x, 3, S[0] if x in (1, 9) else S[4] if x < 6 else S[3])
    # Gehaeuse mit Glas (Zeilen 4-9)
    for y in range(4, 10):
        for x in range(2, 9):
            if x in (2, 8) or y in (4, 9):
                c = S[0]
            elif x == 5:
                c = S[1]                                # Mittelsteg
            else:
                c = GLAS[2] if y in (6, 7) and x in (4, 6) else GLAS[1]
                if y == 5 and x == 3:
                    c = GLAS[3]                         # Glanz oben links
                if y == 8:
                    c = GLAS[0]
            s(x, y, c)
    s(5, 0, S[0]); s(5, 1, S[2])                        # Knauf
    return im


def laterne_glas_farben():
    return [g[:3] for g in GLAS]
