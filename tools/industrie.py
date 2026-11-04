"""Prozedurale Industrie-Bauteile fuer Karte 02 (Factorial Town).

Gleiche Regeln wie Klippen/Bauwerke in Karte 01: Licht von oben links, eigene kleine Paletten mit
Hue-Shifting, keine Streckung, Masse exakt aus maps/karte02/layout.json (Kacheln a 16 px).
Alle Funktionen zeichnen direkt in ein RGBA-Bild (Pixelkoordinaten).
"""
import random
from PIL import Image

T = 16


def rgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5)) + (255,)


def pal(*hexe):
    return [rgb(h) for h in hexe]


WAND = pal('#4a555e', '#5f6b74', '#76838b', '#8d989f', '#a6b0b6', '#bec6ca', '#d3d9dc')
WELL = pal('#253238', '#2f4048', '#3d525c', '#4b6370', '#5c7784', '#6f8c99', '#87a4b0')
DACH = pal('#222e34', '#2a3940', '#34464f', '#3f535d', '#4c626d', '#5b737f', '#6d8793')
ZIEGEL = pal('#5e2f26', '#7a3c2f', '#8f4737', '#a5543f', '#b8664b', '#c97a5a')
FUGE = rgb('#6a4a3e')
FLACH = pal('#262f36', '#2e3840', '#36424b', '#3f4c56', '#4a5863', '#5a6974')
REAK = pal('#141c28', '#1b2635', '#233247', '#2d405a', '#3a5070', '#4c6688')
GRUEN = pal('#2f8f5a', '#4fd07a', '#9af5b0')
GLAS = pal('#142230', '#1f3446', '#2c4a60', '#4a7894', '#8ec0dc')
LICHT = pal('#c88a2a', '#e8b84a', '#f8dc8a')
TUER = pal('#1d4a48', '#2a6662', '#3a8a84', '#58b0a6')
ROLL = pal('#3e4850', '#525d66', '#66727b', '#7c8891', '#96a2aa')
GELB = pal('#8a6a12', '#c49a1e', '#e8c040', '#f6dc78')
SCHWARZ = rgb('#24272c')
STAHL = pal('#3e4850', '#56626b', '#717e87', '#8e9ba3', '#aab6bd', '#c8d1d6')
HOLZ = pal('#3a2a20', '#5a4030', '#7a5a40', '#94704e')
SCHOTTER = pal('#55595d', '#64686c', '#73777b', '#83878a')
WEISS = rgb('#e8ecee')
CREME = rgb('#e6dcb4')

# 3x5-Pixelschrift fuer Schilder
SCHRIFT = {
    'A': ['.x.', 'x.x', 'xxx', 'x.x', 'x.x'], 'E': ['xxx', 'x..', 'xx.', 'x..', 'xxx'],
    'G': ['.xx', 'x..', 'x.x', 'x.x', '.xx'], 'H': ['x.x', 'x.x', 'xxx', 'x.x', 'x.x'],
    'R': ['xx.', 'x.x', 'xx.', 'x.x', 'x.x'], 'T': ['xxx', '.x.', '.x.', '.x.', '.x.'],
    'O': ['.x.', 'x.x', 'x.x', 'x.x', '.x.'], 'K': ['x.x', 'x.x', 'xx.', 'x.x', 'x.x'],
    'L': ['x..', 'x..', 'x..', 'x..', 'xxx'], 'S': ['.xx', 'x..', '.x.', '..x', 'xx.'],
    'C': ['.xx', 'x..', 'x..', 'x..', '.xx'], 'P': ['xx.', 'x.x', 'xx.', 'x..', 'x..'],
    ' ': ['...', '...', '...', '...', '...'],
}


class Leinwand:
    def __init__(self, img):
        self.img = img
        self.px = img.load()
        self.W, self.H = img.size

    def p(self, x, y, c):
        if 0 <= x < self.W and 0 <= y < self.H:
            self.px[x, y] = c

    def rect(self, x0, y0, x1, y1, c):
        for y in range(max(0, y0), min(self.H, y1)):
            for x in range(max(0, x0), min(self.W, x1)):
                self.px[x, y] = c

    def dunkel(self, x, y, f):
        if 0 <= x < self.W and 0 <= y < self.H:
            r, g, b, a = self.px[x, y]
            self.px[x, y] = (int(r * f), int(g * f), int(b * min(1.0, f + 0.06)), a)

    def text(self, x, y, s, c):
        for i, ch in enumerate(s.upper()):
            g = SCHRIFT.get(ch, SCHRIFT[' '])
            for dy, z in enumerate(g):
                for dx, z2 in enumerate(z):
                    if z2 == 'x':
                        self.p(x + i * 4 + dx, y + dy, c)


# ---------------------------------------------------------------- Aussenmauer
def mauer(L, r, seite, rnd):
    x0, y0, x1, y1 = r[0] * T, r[1] * T, (r[2] + 1) * T, (r[3] + 1) * T
    if seite in ('oben', 'unten'):
        kappe = 2 * T if seite == 'oben' else T
        # Kappe (Draufsicht): helle Betonoberseite mit Plattenfugen
        for y in range(y0, y0 + kappe):
            for x in range(x0, x1):
                k = y - y0
                c = WAND[6] if k == 0 else WAND[5] if k < kappe - 3 else WAND[4] if k < kappe - 1 else WAND[1]
                if (x - x0) % 32 == 0 and 0 < k < kappe - 1:
                    c = WAND[3]
                L.p(x, y, c)
        # Wandflaeche (Ansicht von Sueden): Paneele mit Fugen, oben heller, unten dunkler
        for y in range(y0 + kappe, y1):
            for x in range(x0, x1):
                k = (y - y0 - kappe) / max(1, (y1 - y0 - kappe))
                c = WAND[4] if k < 0.15 else WAND[3] if k < 0.6 else WAND[2]
                if (x - x0) % 24 == 0:
                    c = WAND[1]
                elif (x - x0) % 24 == 1:
                    c = WAND[5] if k < 0.6 else WAND[4]
                if y == y1 - 1:
                    c = WAND[0]
                L.p(x, y, c)
        if seite == 'oben':                       # Schatten der Mauer auf den Boden
            for x in range(x0, x1):
                for d, f in ((0, 0.7), (1, 0.8), (2, 0.9)):
                    L.dunkel(x, y1 + d, f)
    else:
        # Seitenmauer: nur die Kappe ist zu sehen, Innenkante mit Schatten
        innen = x1 - 1 if seite == 'links' else x0
        for y in range(y0, y1):
            for x in range(x0, x1):
                k = (x - x0) if seite == 'links' else (x1 - 1 - x)
                c = WAND[5] if k < (x1 - x0) - 4 else WAND[4]
                if (y - y0) % 32 == 0:
                    c = WAND[3]
                if x == innen:
                    c = WAND[1]
                L.p(x, y, c)
        for y in range(y0, y1):
            for d, f in ((1, 0.72), (2, 0.85)):
                L.dunkel(innen + d if seite == 'links' else innen - d, y, f)


# ---------------------------------------------------------------- Gebaeude
def _wellblech_dach(L, x0, y0, x1, y1):
    for y in range(y0, y1):
        for x in range(x0, x1):
            k = (y - y0) % 4
            c = DACH[4] if k == 0 else DACH[3] if k == 1 else DACH[2]
            if x in (x0, x1 - 1):
                c = DACH[0]
            elif x == x0 + 1:
                c = DACH[5] if k == 0 else DACH[4]
            L.p(x, y, c)
    for x in range(x0, x1):                       # Dachkante vorne (Traufe)
        L.p(x, y1 - 3, DACH[6]); L.p(x, y1 - 2, DACH[5]); L.p(x, y1 - 1, DACH[0])
        L.p(x, y0, DACH[0])


def _flachdach(L, x0, y0, x1, y1):
    for y in range(y0, y1):
        for x in range(x0, x1):
            c = FLACH[2]
            if y in (y0, y0 + 1) or x in (x0, x0 + 1):
                c = FLACH[4] if y > y0 and x > x0 else FLACH[0]
            if x in (x1 - 1, x1 - 2) or y in (y1 - 3,):
                c = FLACH[1]
            if y == y1 - 2:
                c = FLACH[5]
            if y == y1 - 1:
                c = FLACH[0]
            L.p(x, y, c)
    # Brüstung innen (schmale Kante)
    for x in range(x0 + 3, x1 - 3):
        L.p(x, y0 + 3, FLACH[1])
    for y in range(y0 + 3, y1 - 4):
        L.p(x0 + 3, y, FLACH[1])


def _luefter(L, x, y, gross=2):
    s = gross * T - 4
    L.rect(x + 2, y + 2, x + 2 + s, y + 2 + s, STAHL[1])
    L.rect(x + 3, y + 3, x + 1 + s, y + 1 + s, STAHL[2])
    for i in range(s):                            # Rahmen mit Licht oben links
        L.p(x + 2 + i, y + 2, STAHL[4]); L.p(x + 2, y + 2 + i, STAHL[4])
        L.p(x + 2 + i, y + 1 + s, STAHL[0]); L.p(x + 1 + s, y + 2 + i, STAHL[0])
    cx, cy, rr = x + 2 + s // 2, y + 2 + s // 2, s // 2 - 3
    for yy in range(cy - rr, cy + rr + 1):
        for xx in range(cx - rr, cx + rr + 1):
            if (xx - cx) ** 2 + (yy - cy) ** 2 <= rr * rr:
                L.p(xx, yy, STAHL[1])
    for k in range(-rr + 1, rr):                  # Fluegel als X
        L.p(cx + k, cy + k, STAHL[3]); L.p(cx + k, cy - k, STAHL[3])
    L.p(cx, cy, STAHL[5])


def _fenster(L, x, y, w=10, h=6, licht=False):
    rahmen = STAHL[0]
    for xx in range(x, x + w):
        for yy in range(y, y + h):
            if xx in (x, x + w - 1) or yy in (y, y + h - 1):
                c = rahmen
            elif licht:
                c = LICHT[2] if yy == y + 1 else LICHT[1] if yy < y + h - 2 else LICHT[0]
            else:
                c = GLAS[3] if (yy == y + 1 and xx < x + w // 2) else GLAS[1] if yy > y + h // 2 else GLAS[2]
            L.p(xx, yy, c)
    L.p(x + 1, y + 1, GLAS[4] if not licht else LICHT[2])


def _rolltor(L, x0, y0, x1, y1, offen=False):
    # Rahmen mit Warnstreifen oben
    for y in range(y0, y1):
        for x in range(x0, x1):
            if y < y0 + 3:
                c = GELB[2] if ((x + y) // 3) % 2 == 0 else SCHWARZ
            elif x in (x0, x0 + 1, x1 - 2, x1 - 1):
                c = STAHL[1] if x in (x0, x1 - 1) else (STAHL[3] if x == x0 + 1 else STAHL[0])
            elif offen:
                tief = (y - y0) / max(1, y1 - y0)
                c = rgb('#0e1418') if tief > 0.25 else rgb('#1b252c')
            else:
                k = (y - y0 - 3) % 3
                c = ROLL[3] if k == 0 else ROLL[2] if k == 1 else ROLL[1]
                if y == y1 - 3:
                    c = ROLL[0]
            L.p(x, y, c)
    if not offen:
        L.rect((x0 + x1) // 2 - 3, y1 - 5, (x0 + x1) // 2 + 3, y1 - 4, ROLL[4])


def _tuer(L, x, y0, y1, farbe=TUER):
    for y in range(y0, y1):
        for xx in range(x, x + 9):
            c = farbe[2]
            if xx in (x, x + 8) or y == y0:
                c = STAHL[0]
            elif xx == x + 1:
                c = farbe[3]
            elif xx == x + 7:
                c = farbe[1]
            L.p(xx, y, c)
    L.rect(x + 2, y0 + 3, x + 7, y0 + 7, GLAS[2])
    L.p(x + 6, (y0 + y1) // 2 + 1, GELB[3])


def gebaeude(L, g, rnd):
    x0, y0, x1, y1 = g['r'][0] * T, g['r'][1] * T, (g['r'][2] + 1) * T, (g['r'][3] + 1) * T
    fy = y1 - g['fassade'] * T                   # Fassadenoberkante
    typ = g['typ']
    # Schatten des Gebaeudes nach rechts unten (Licht von oben links)
    for y in range(y0 + 6, y1 + 4):
        for d, f in ((0, 0.62), (1, 0.75), (2, 0.88)):
            L.dunkel(x1 + d, y, f)
    for x in range(x0 + 4, x1 + 3):
        for d, f in ((0, 0.62), (1, 0.78), (2, 0.9)):
            L.dunkel(x, y1 + d, f)
    # Dach
    if typ == 'wellblech':
        _wellblech_dach(L, x0, y0, x1, fy)
    elif typ == 'backstein':
        _flachdach(L, x0, y0, x1, fy)
        # Dachdetails: Klimageraete und eine Dachluke (Licht oben links, Schatten rechts unten)
        breite = x1 - x0
        for i, ax in enumerate(range(x0 + 10, x1 - 44, max(40, breite // 3))):   # Platz fuer die Luke lassen
            ay = y0 + 8 + (i % 2) * 10
            if any(lx * T <= ax + 16 and ax <= lx * T + 2 * T for lx, ly in g.get('luefter', [])):
                continue
            L.rect(ax, ay, ax + 14, ay + 10, STAHL[2])
            L.rect(ax, ay, ax + 14, ay + 1, STAHL[4]); L.rect(ax, ay, ax + 1, ay + 10, STAHL[4])
            L.rect(ax + 13, ay, ax + 14, ay + 10, STAHL[0]); L.rect(ax, ay + 9, ax + 14, ay + 10, STAHL[0])
            for k in range(3):
                L.rect(ax + 3, ay + 2 + k * 2, ax + 11, ay + 3 + k * 2, STAHL[1])
            for d in range(1, 3):
                for yy in range(ay + 2, ay + 11):
                    L.dunkel(ax + 13 + d, yy, 0.75)
        lx0, ly0 = x1 - 26, y0 + 10
        L.rect(lx0, ly0, lx0 + 12, ly0 + 9, FLACH[4])
        L.rect(lx0 + 1, ly0 + 1, lx0 + 11, ly0 + 8, FLACH[1])
        L.rect(lx0 + 1, ly0 + 1, lx0 + 11, ly0 + 2, FLACH[5])
    else:
        for y in range(y0, fy):
            for x in range(x0, x1):
                L.p(x, y, REAK[2] if (y // 4) % 2 else REAK[1])
        for x in range(x0, x1):
            L.p(x, fy - 2, REAK[4]); L.p(x, fy - 1, REAK[0])
    for (lx, ly) in g.get('luefter', []):
        _luefter(L, lx * T, ly * T)
    # Fassade
    for y in range(fy, y1):
        for x in range(x0, x1):
            if typ == 'wellblech':
                k = (x - x0) % 4
                c = WELL[5] if k == 0 else WELL[4] if k == 1 else WELL[3] if k == 2 else WELL[2]
                if y < fy + 3:
                    c = WELL[1] if y > fy else WELL[0]
                if y >= y1 - 3:
                    c = WELL[1] if y < y1 - 1 else WELL[0]
            elif typ == 'backstein':
                zeile = (y - fy) // 4
                versatz = 4 if zeile % 2 else 0
                if (y - fy) % 4 == 3 or (x - x0 + versatz) % 8 == 7:
                    c = FUGE
                else:
                    c = ZIEGEL[3] if (x - x0 + versatz) % 8 < 1 or (y - fy) % 4 == 0 else ZIEGEL[2]
                    if ((x - x0 + versatz) // 8 + zeile) % 5 == 0:
                        c = ZIEGEL[1] if c == ZIEGEL[2] else ZIEGEL[2]
                if y >= y1 - 2:
                    c = ZIEGEL[0]
            else:
                k = (x - x0) % 16
                c = REAK[3] if k == 1 else REAK[1] if k == 0 else REAK[2]
                if (y - fy) % 16 == 0:
                    c = REAK[0]
                if y >= y1 - 2:
                    c = REAK[0]
            if x in (x0, x1 - 1):
                c = WELL[0] if typ == 'wellblech' else ZIEGEL[0] if typ == 'backstein' else REAK[0]
            L.p(x, y, c)
    hoehe = y1 - fy
    # Fensterband
    belegt = set()
    for tx in g.get('tore', []):
        belegt.update(range(tx - 1, tx + 3))
    for tx in g.get('tueren', []):
        belegt.update(range(tx, tx + 1))
    for sx, _ in g.get('schilder', []):
        belegt.update(range(sx, sx + 4))
    for kx in range(g['r'][0], g['r'][2] + 1):
        if kx in belegt or kx in (g['r'][0], g['r'][2]):
            continue
        if typ == 'wellblech':
            _fenster(L, kx * T + 3, fy + 5, 10, 6)
        elif typ == 'backstein':
            _fenster(L, kx * T + 4, fy + 6, 8, 7, licht=True)
        else:
            if kx % 2 == 0:
                for xx in range(kx * T + 4, kx * T + 12):
                    for yy in range(fy + 7, fy + 11):
                        L.p(xx, yy, GRUEN[1] if yy < fy + 9 else GRUEN[0])
    # Tore, Tueren, Schilder
    for tx in g.get('tore', []):
        if typ == 'backstein':
            bx0, bx1 = tx * T + 2, (tx + 2) * T - 2
            by0 = y1 - min(hoehe - 6, 30)
            for y in range(by0, y1 - 1):
                for x in range(bx0, bx1):
                    c = ROLL[2] if (x - bx0) % 2 else ROLL[3]
                    if x in (bx0, bx1 - 1) or y == by0:
                        c = STAHL[0]
                    if x == (bx0 + bx1) // 2:
                        c = STAHL[0]
                    L.p(x, y, c)
            L.rect(bx0, by0 - 3, bx1, by0, GELB[2])
            for x in range(bx0, bx1, 6):
                L.rect(x, by0 - 3, x + 3, by0, SCHWARZ)
        elif typ == 'reaktor':
            bx0, bx1 = tx * T - 8, (tx + 2) * T + 8
            by0 = fy + 6
            for y in range(by0, y1 - 1):
                for x in range(bx0, bx1):
                    c = REAK[3] if x < (bx0 + bx1) // 2 else REAK[2]
                    if x in (bx0, bx1 - 1, (bx0 + bx1) // 2) or y == by0:
                        c = REAK[0]
                    L.p(x, y, c)
            for x in range(bx0, bx1):
                L.p(x, by0 - 2, GELB[2] if (x // 3) % 2 else SCHWARZ)
                L.p(x, by0 - 1, GELB[2] if (x // 3) % 2 else SCHWARZ)
            cx = (bx0 + bx1) // 2
            for x in range(cx - 5, cx + 6):
                L.p(x, (by0 + y1) // 2, GRUEN[1])
        else:
            offen = g.get('name') == 'fabrikhalle'
            _rolltor(L, tx * T - 4, fy + 3, (tx + 2) * T + 4, y1 - 1, offen=offen)
    for tx in g.get('tueren', []):
        _tuer(L, tx * T + 3, y1 - min(hoehe - 4, 22), y1 - 1)
    for sx, text in g.get('schilder', []):
        bx, by = sx * T + 2, fy + 2
        w = len(text) * 4 + 12
        L.rect(bx, by, bx + w, by + 9, rgb('#2a5450'))
        L.rect(bx, by, bx + w, by + 1, rgb('#4a8a82'))
        L.rect(bx, by + 8, bx + w, by + 9, rgb('#16302e'))
        L.rect(bx + 2, by + 3, bx + 5, by + 6, GELB[2])           # Logo-Punkt
        L.text(bx + 8, by + 2, text, rgb('#c8f0e6'))


# ---------------------------------------------------------------- Linien: Schienen, Foerderband, Rohr
def _linie_zellen(a, b):
    (x0, y0), (x1, y1) = a, b
    if x0 == x1:
        return 'v', [(x0, y) for y in range(min(y0, y1), max(y0, y1) + 1)]
    return 'h', [(x, y0) for x in range(min(x0, x1), max(x0, x1) + 1)]


def schiene(L, a, b):
    rt, zellen = _linie_zellen(a, b)
    for cx, cy in zellen:
        X, Y = cx * T, cy * T
        for i in range(T):
            for j in range(T):
                x, y = (X + j, Y + i)
                q = j if rt == 'v' else i                 # quer zur Fahrtrichtung
                l = i if rt == 'v' else j                 # laengs
                if 2 <= q <= 13:
                    c = SCHOTTER[(x * 7 + y * 3) % 4] if (x * 5 + y * 11) % 3 else SCHOTTER[1]
                    if l % 5 in (0, 1) and 2 <= q <= 13:
                        c = HOLZ[2] if l % 5 == 0 else HOLZ[1]
                    if q in (4, 11):
                        c = STAHL[4]
                    elif q in (5, 12):
                        c = STAHL[1]
                    L.p(x, y, c)


def foerderband(L, a, b, frame=0):
    rt, zellen = _linie_zellen(a, b)
    for cx, cy in zellen:
        X, Y = cx * T, cy * T
        for i in range(T):
            for j in range(T):
                x, y = X + j, Y + i
                q = j if rt == 'v' else i
                l = (i if rt == 'v' else j) + (Y if rt == 'v' else X)
                if q in (1, 14):
                    c = GELB[1]
                elif q in (2, 13):
                    c = GELB[2] if q == 2 else GELB[0]
                elif q in (0, 15):
                    c = SCHWARZ
                else:
                    c = rgb('#2c3036') if (l - frame) % 4 else rgb('#3c424a')   # laufende Bandglieder
                    if q == 3:
                        c = rgb('#1e2126')
                L.p(x, y, c)
        if rt == 'v':
            for y in range(Y, Y + T, 8):
                L.p(X + 1, y, GELB[3]); L.p(X + 14, y + 4, GELB[3])


def rohr(L, a, b):
    rt, zellen = _linie_zellen(a, b)
    for n, (cx, cy) in enumerate(zellen):
        X, Y = cx * T, cy * T
        for i in range(T):
            for j in range(T):
                q = j if rt == 'v' else i
                if 5 <= q <= 10:
                    c = STAHL[5] if q == 6 else STAHL[4] if q == 7 else STAHL[3] if q < 10 else STAHL[1]
                    if q == 5:
                        c = STAHL[2]
                    L.p(X + j, Y + i, c)
        if n % 3 == 0 or n == len(zellen) - 1:      # Flansch
            for k in range(3, 13):
                for d in (0, 1, 2):
                    if rt == 'v':
                        L.p(X + k, Y + 6 + d, STAHL[2] if d == 2 else STAHL[4])
                    else:
                        L.p(X + 6 + d, Y + k, STAHL[2] if d == 2 else STAHL[4])
        # Schatten neben dem Rohr
        for k in range(T):
            if rt == 'v':
                L.dunkel(X + 11, Y + k, 0.75)
            else:
                L.dunkel(X + k, Y + 11, 0.75)


# ---------------------------------------------------------------- Markierungen
def markierung(L, m):
    x0, y0, x1, y1 = m['r'][0] * T, m['r'][1] * T, (m['r'][2] + 1) * T, (m['r'][3] + 1) * T
    art = m['art']
    if art == 'warnstreifen':
        for y in range(y0 + 3, y1 - 3):
            for x in range(x0, x1):
                c = GELB[2] if ((x + y) // 4) % 2 == 0 else SCHWARZ
                if y == y0 + 3:
                    c = GELB[3] if c == GELB[2] else rgb('#3a3e44')
                L.p(x, y, c)
    elif art == 'parklinie':
        for y in range(y0, y1):
            L.p(x0 + 7, y, WEISS); L.p(x0 + 8, y, rgb('#c8ced2'))
    elif art == 'zebra':
        for y in range(y0 + 2, y1 - 2):
            if (y - y0) % 6 < 3:
                for x in range(x0 + 2, x1 - 2):
                    L.p(x, y, WEISS if (y - y0) % 6 == 0 else rgb('#d2d8dc'))


def mittellinie(L, x0, x1, y):
    for x in range(x0, x1):
        if (x // 8) % 2 == 0:
            L.p(x, y, CREME); L.p(x, y + 1, rgb('#bdb38e'))


def bordstein(L, x0, x1, y, oben=True):
    """Bordstein zwischen Gehweg und Strasse: helle Kante + Schatten auf den Asphalt."""
    for x in range(x0, x1):
        if oben:
            L.p(x, y - 2, WAND[6]); L.p(x, y - 1, WAND[4])
            L.dunkel(x, y, 0.7); L.dunkel(x, y + 1, 0.85)
        else:
            L.p(x, y, WAND[2]); L.p(x, y + 1, WAND[5])


def bodenflecken(L, zellen_beton, zellen_asphalt, seed=21):
    """Risse, Oelflecken und Gullydeckel (sparsam, kontrastarm)."""
    rnd = random.Random(seed)
    for (cx, cy) in zellen_beton:
        r = rnd.random()
        X, Y = cx * T + rnd.randint(2, 12), cy * T + rnd.randint(2, 12)
        if r < 0.025:                                 # Riss
            x, y = X, Y
            for _ in range(rnd.randint(5, 9)):
                L.dunkel(x, y, 0.72)
                x += rnd.choice((1, 1, 0)); y += rnd.choice((0, 1, -1))
        elif r < 0.04:                                # Oelfleck
            for dy in range(-2, 3):
                for dx in range(-3, 4):
                    if dx * dx / 9 + dy * dy / 4 <= 1 and rnd.random() < 0.85:
                        L.dunkel(X + dx, Y + dy, 0.8)
    for (cx, cy) in zellen_asphalt:
        if rnd.random() < 0.03:                       # Gullydeckel
            X, Y = cx * T + 4, cy * T + 5
            for dy in range(6):
                for dx in range(8):
                    c = STAHL[1] if dy in (0, 5) or dx in (0, 7) else (STAHL[2] if dy % 2 else STAHL[0])
                    L.p(X + dx, Y + dy, c)


# ---------------------------------------------------------------- Sprites: Container und Portalkran
CONTAINER = {
    'rot': pal('#4a201c', '#6e2c25', '#8c3a30', '#a8483a', '#c35e4a', '#d97a62'),
    'blau': pal('#1a2a44', '#243a5e', '#2f4c78', '#3d6094', '#5078ad', '#6e96c6'),
    'orange': pal('#5e3612', '#8a5018', '#ad6a22', '#c9822e', '#dd9a44', '#ecb666'),
    'gruen': pal('#1e3424', '#2a4a32', '#365e40', '#447452', '#5a8c66', '#78a882'),
}


def container_sprite(farbe, variante=0, breite=80, dach=12, wand=32):
    """Container in Frontalansicht (Draufsicht 3/4): Dach oben, lange Seitenwand vorne mit Rippen,
    Tueren rechts, Eckbeschlaege, Etikett, etwas Rost. Licht von oben links."""
    rnd = random.Random(hash((farbe, variante)) & 0xffff)
    c = CONTAINER[farbe]
    H = dach + wand
    im = Image.new('RGBA', (breite, H), (0, 0, 0, 0))
    L = Leinwand(im)
    # Dach: Laengsrippen, Licht von oben
    for y in range(dach):
        for x in range(breite):
            k = y % 3
            col = c[5] if y == 0 else c[4] if k == 1 else c[3]
            if x in (0, breite - 1):
                col = c[0]
            L.p(x, y, col)
    # Dachkante vorne
    for x in range(breite):
        L.p(x, dach - 1, c[1]); L.p(x, dach, c[0])
    # Seitenwand: senkrechte Rippen (Trapezblech), unten dunkler
    tuer_x = breite - 16
    for y in range(dach + 1, H):
        tief = (y - dach) / wand
        for x in range(breite):
            k = (x - 2) % 5
            col = c[4] if k == 0 else c[3] if k in (1, 2) else c[2] if k == 3 else c[1]
            if tief > 0.75 and col in (c[3], c[4]):
                col = c[2]
            if x >= tuer_x:                                  # Tuerfluegel
                col = c[3] if (x - tuer_x) % 8 not in (0, 7) else c[1]
                if (x - tuer_x) % 8 in (2, 5) and dach + 4 < y < H - 4:
                    col = STAHL[3]                           # Verriegelungsstangen
            if x in (0, breite - 1) or y == H - 1:
                col = c[0]
            L.p(x, y, col)
    # Eckbeschlaege
    for (ex, ey) in ((0, 0), (breite - 4, 0), (0, H - 4), (breite - 4, H - 4)):
        L.rect(ex, ey, ex + 4, ey + 4, c[0])
        L.p(ex + 1, ey + 1, c[2])
    # Etikett
    if variante % 2 == 0:
        L.rect(6, dach + 5, 18, dach + 12, rgb('#e6e9ea'))
        for yy in (dach + 7, dach + 9):
            L.rect(8, yy, 16, yy + 1, rgb('#7d868c'))
    # Rost / Gebrauchsspuren
    for _ in range(10 + variante * 8):
        x, y = rnd.randrange(2, breite - 2), rnd.randrange(dach + 2, H - 2)
        L.p(x, y, rgb('#7a4a2e') if rnd.random() < 0.6 else c[1])
    return im


KRANGELB = pal('#6a5010', '#9a7414', '#c8961e', '#e2b432', '#f2cf5c', '#fbe69a')


def kran_sprite(spannweite, hoehe, container=None):
    """Portalkran in Frontalansicht: zwei Gitterbeine mit Fahrwerken, oberer Kastentraeger mit
    Katze, Seile mit Spreader und optional Container. Breite = spannweite (Aussenkante der Beine)."""
    im = Image.new('RGBA', (spannweite, hoehe), (0, 0, 0, 0))
    L = Leinwand(im)
    G = KRANGELB
    bein_b, traeger_h = 16, 18
    # Container am Haken (hinter den Seilen, vor dem Hintergrund)
    if container is not None:
        cw, ch = container.size
        cx = (spannweite - cw) // 2 + 6
        im.alpha_composite(container, (cx, hoehe - ch - 30))
        # Spreader
        L.rect(cx + 6, hoehe - ch - 36, cx + cw - 6, hoehe - ch - 31, G[2])
        for x in range(cx + 6, cx + cw - 6):
            L.p(x, hoehe - ch - 36, G[4])
            if ((x - cx) // 4) % 2:
                L.p(x, hoehe - ch - 33, SCHWARZ); L.p(x, hoehe - ch - 34, SCHWARZ)
        seil_unten = hoehe - ch - 36
    else:
        seil_unten = hoehe // 2
    # Beine (Gitter) links und rechts
    for bx in (0, spannweite - bein_b):
        for y in range(traeger_h, hoehe - 10):
            for x in range(bx, bx + bein_b):
                k = x - bx
                if k in (0, bein_b - 1):
                    col = G[0]
                elif k in (1, 2):
                    col = G[4] if k == 1 else G[3]
                elif k in (bein_b - 3, bein_b - 2):
                    col = G[2] if k == bein_b - 3 else G[1]
                else:
                    # Diagonalverstrebung im Gitter
                    d = (y - traeger_h) % 16
                    if abs((k - 3) - d * (bein_b - 6) / 16) < 1.2 or abs((bein_b - 4 - k) - d * (bein_b - 6) / 16) < 1.2:
                        col = G[2]
                    elif d == 0:
                        col = G[1]
                    else:
                        continue
                L.p(x, y, col)
        # Fahrwerk mit Raedern
        L.rect(bx - 2, hoehe - 12, bx + bein_b + 2, hoehe - 6, STAHL[1])
        L.rect(bx - 2, hoehe - 12, bx + bein_b + 2, hoehe - 11, STAHL[3])
        for rx in (bx + 1, bx + bein_b - 6):
            L.rect(rx, hoehe - 7, rx + 5, hoehe, SCHWARZ)
            L.p(rx + 2, hoehe - 4, STAHL[3])
    # Obertraeger (Kastentraeger mit Bolzen)
    for y in range(0, traeger_h):
        for x in range(spannweite):
            col = G[4] if y == 0 else G[3] if y < 6 else G[2] if y < traeger_h - 3 else G[1]
            if y == traeger_h - 1 or x in (0, spannweite - 1):
                col = G[0]
            L.p(x, y, col)
    for x in range(6, spannweite - 6, 10):
        L.p(x, 8, G[0]); L.p(x, 9, G[5])
    # Katze mit Kabine
    kx = spannweite // 2 + 6
    L.rect(kx - 14, 2, kx + 14, 14, STAHL[1])
    L.rect(kx - 13, 3, kx + 13, 6, STAHL[3])
    L.rect(kx + 4, 5, kx + 12, 12, GLAS[2]); L.p(kx + 5, 6, GLAS[4])
    # Seile
    for x in (kx - 8, kx - 2):
        for y in range(14, seil_unten):
            L.p(x, y, STAHL[0]); L.p(x + 1, y, STAHL[3])
    return im
