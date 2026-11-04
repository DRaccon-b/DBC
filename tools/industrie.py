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

    def neutral(self, x, y, f, waerme=0):
        """Abdunkeln ohne Blaustich (waerme > 0: leicht braeunlich, z. B. Oel/Schmutz)."""
        if 0 <= x < self.W and 0 <= y < self.H:
            r, g, b, a = self.px[x, y]
            self.px[x, y] = (int(r * f + waerme), int(g * f + waerme * 0.6), int(b * f), a)

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
        # Seitenmauer wie die obere Mauer: Kappe mit Plattenfugen (Draufsicht), Innenkante mit Schatten.
        # Endet die Mauer an einem Ausgang (Ende oberhalb einer Oeffnung), zeigt das Ende seine Front
        # (Paneele wie die obere Mauer) - wie ein Torpfeiler.
        innen = x1 - 1 if seite == 'links' else x0
        ende_offen = r[3] < 70                       # unteres Ende an einem Ausgang
        front = 2 * T if ende_offen else 0
        for y in range(y0, y1 - front):
            for x in range(x0, x1):
                k = (x - x0) if seite == 'links' else (x1 - 1 - x)
                c = WAND[5] if k > 0 else WAND[4]
                if k == 0:
                    c = WAND[3]
                if (y - y0) % 32 == 0:
                    c = WAND[3]
                elif (y - y0) % 32 == 1:
                    c = WAND[6]
                if x == innen:
                    c = WAND[1]
                L.p(x, y, c)
        if ende_offen:
            ky = y1 - front
            for x in range(x0, x1):                  # Kappenkante vorne
                L.p(x, ky - 1, WAND[4]); L.p(x, ky, WAND[1])
            for y in range(ky + 1, y1):              # Front (Ansicht von Sueden)
                for x in range(x0, x1):
                    t = (y - ky) / front
                    c = WAND[4] if t < 0.15 else WAND[3] if t < 0.6 else WAND[2]
                    if (x - x0) % 24 == 0:
                        c = WAND[1]
                    elif (x - x0) % 24 == 1:
                        c = WAND[5] if t < 0.6 else WAND[4]
                    if x in (x0, x1 - 1):
                        c = WAND[0]
                    if y == y1 - 1:
                        c = WAND[0]
                    L.p(x, y, c)
            for x in range(x0, x1 + 2):              # Schatten vor die Front
                for d, f in ((0, 0.7), (1, 0.82), (2, 0.92)):
                    L.dunkel(x, y1 + d, f)
        else:
            # oberes Ende an einem Ausgang: Stirnkante dunkel
            for x in range(x0, x1):
                L.p(x, y0, WAND[1]); L.p(x, y0 + 1, WAND[6])
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
        if g.get('tor_mitte'):
            belegt.update(range(tx - g.get('torbreite', 4) // 2 - 1, tx + g.get('torbreite', 4) // 2 + 1))
        else:
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
            if g.get('tor_mitte'):                      # Tor mittig ueber Kachelkante tx, breit
                tb = g.get('torbreite', 4) * T // 2
                _rolltor(L, tx * T - tb, fy + 3, tx * T + tb, y1 - 1, offen=offen)
            else:
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
    """Gleis: Schotterbett mit ausfransendem Rand, Holzschwellen (laenger als die Spurweite, mit
    Licht-/Schattenkante), zwei Stahlschienen mit Glanzlinie und Schatten. Achsparallel."""
    rt, zellen = _linie_zellen(a, b)
    if not zellen:
        return
    xs = [c[0] for c in zellen]; ys = [c[1] for c in zellen]
    if rt == 'v':
        X0, X1, Y0, Y1 = min(xs) * T, (max(xs) + 1) * T, min(ys) * T, (max(ys) + 1) * T
    else:
        X0, X1, Y0, Y1 = min(xs) * T, (max(xs) + 1) * T, min(ys) * T, (max(ys) + 1) * T
    rnd = random.Random(X0 * 7 + Y0)
    for y in range(Y0, Y1):
        for x in range(X0, X1):
            q = (x - X0) if rt == 'v' else (y - Y0)        # quer 0..15
            l = y if rt == 'v' else x                      # laengs
            # Schotterbett 1..14, Rand ausgefranst
            if q in (0, 15) and rnd.random() < 0.55:
                continue
            c = SCHOTTER[(x * 7 + y * 13) % 4]
            if q in (0, 1, 14, 15):
                c = SCHOTTER[1] if (x + y) % 2 else SCHOTTER[0]
            # Schwellen: 3 px breit, alle 6 px, von q=2 bis 13
            s_ = l % 6
            if 2 <= q <= 13 and s_ in (0, 1, 2):
                c = HOLZ[3] if s_ == 0 else HOLZ[2] if s_ == 1 else HOLZ[1]
                if q in (2, 13):
                    c = HOLZ[1]
            # Schienen bei q = 4/5 und 10/11 (Kopf hell, Fuss dunkel), Schatten bei 6 und 12
            if q in (4, 10):
                c = STAHL[5] if (l % 9) else STAHL[4]
            elif q in (5, 11):
                c = STAHL[2]
            elif q in (6, 12) and not (2 <= q <= 13 and s_ in (0, 1, 2)):
                c = SCHOTTER[0]
            L.p(x, y, c)
    # Prellbock an offenen Enden
    for (cx, cy) in (zellen[0], zellen[-1]):
        X, Y = cx * T, cy * T
        if rt == 'v':
            yy = Y if (cx, cy) == zellen[0] else Y + T - 4
            L.rect(X + 3, yy, X + 13, yy + 4, GELB[2]); L.rect(X + 3, yy + 3, X + 13, yy + 4, GELB[0])
            for x in range(X + 3, X + 13, 4):
                L.rect(x, yy, x + 2, yy + 3, SCHWARZ)
        else:
            xx = X if (cx, cy) == zellen[0] else X + T - 4
            L.rect(xx, Y + 3, xx + 4, Y + 13, GELB[2]); L.rect(xx + 3, Y + 3, xx + 4, Y + 13, GELB[0])


def foerderband(L, a, b, frame=0, breite=2):
    """Foerderband `breite` Kacheln breit. a/b = (x, y) der linken bzw. oberen Kachel des Bandes.
    Seitenwangen gelb mit Warnmarken, Rollen alle 8 px, Bandglieder laufen in Foerderrichtung."""
    (x0, y0), (x1, y1) = a, b
    vert = x0 == x1
    if vert:
        X0, X1, Y0, Y1 = x0 * T, (x0 + breite) * T, min(y0, y1) * T, (max(y0, y1) + 1) * T
    else:
        X0, X1, Y0, Y1 = min(x0, x1) * T, (max(x0, x1) + 1) * T, y0 * T, (y0 + breite) * T
    B = breite * T
    for y in range(Y0, Y1):
        for x in range(X0, X1):
            q = (x - X0) if vert else (y - Y0)          # quer
            l = y if vert else x                        # laengs
            if q in (0, B - 1):
                c = SCHWARZ
            elif q in (1, 2):
                c = GELB[3] if q == 1 else GELB[2]
            elif q in (B - 3, B - 2):
                c = GELB[1] if q == B - 3 else GELB[0]
            elif q in (3, B - 4):
                c = rgb('#1a1d22')
            else:
                glied = (l - frame) % 6
                c = rgb('#3c424a') if glied == 0 else rgb('#33383f') if glied == 1 else rgb('#2a2e34')
                if q == 4:
                    c = rgb('#1e2126')                  # Schatten der linken/oberen Wange
                elif q == B - 5:
                    c = rgb('#444b54')
            L.p(x, y, c)
        if vert and (y - Y0) % 8 == 0:
            for x in (X0 + 1, X1 - 2):
                L.p(x, y, rgb('#2a2e34'))               # Rollenachsen in der Wange
    if not vert:
        for x in range(X0, X1, 8):
            for y in (Y0 + 1, Y1 - 2):
                L.p(x, y, rgb('#2a2e34'))
    # Schatten des Bandes nach rechts/unten
    for k in range(Y0, Y1) if vert else range(X0, X1):
        for d, f in ((0, 0.72), (1, 0.86)):
            if vert:
                L.neutral(X1 + d, k, f)
            else:
                L.neutral(k, Y1 + d, f)


ROHR = pal('#2a333b', '#3e4a54', '#56646f', '#73828c', '#94a2aa', '#b8c4ca', '#e2e9ec')


def rohr(L, a, b):
    """Rohrleitung auf Stuetzen: 8 px Zylinder (7 Toene, Glanzlinie oben/links), Flansche mit Bolzen
    alle 3 Kacheln, Betonstuetzen alle 4 Kacheln, Endkappen, Schlagschatten auf dem Boden
    (Rohr liegt etwas erhoeht -> Schatten 3 px nach rechts unten versetzt)."""
    rt, zellen = _linie_zellen(a, b)
    if not zellen:
        return
    xs = [c[0] for c in zellen]; ys = [c[1] for c in zellen]
    X0, X1, Y0, Y1 = min(xs) * T, (max(xs) + 1) * T, min(ys) * T, (max(ys) + 1) * T
    v = rt == 'v'
    q0 = 4                                             # Rohr belegt quer 4..11
    def P(l, q):
        return (X0 + q, l) if v else (l, Y0 + q)
    lang = range(Y0 + 2, Y1 - 2) if v else range(X0 + 2, X1 - 2)
    # Schatten
    for l in lang:
        for q in range(q0, q0 + 8):
            x, y = P(l, q)
            L.neutral(x + 3, y + 3, 0.78)
    # Stuetzen
    for n, l in enumerate(range(lang.start + 8, lang.stop, 4 * T)):
        for d in range(-3, 4):
            for q in (q0 - 2, q0 - 1, q0 + 8, q0 + 9):
                x, y = P(l + d, q)
                L.p(x, y, WAND[4] if d < 0 else WAND[2])
    # Zylinder
    toene = [ROHR[1], ROHR[4], ROHR[5], ROHR[6], ROHR[4], ROHR[3], ROHR[2], ROHR[0]]
    for l in lang:
        for i, q in enumerate(range(q0, q0 + 8)):
            x, y = P(l, q)
            L.p(x, y, toene[i])
    # Flansche mit Bolzen
    for l in list(range(lang.start + 2 * T, lang.stop - 4, 3 * T)):
        for d in (0, 1, 2):
            for q in range(q0 - 1, q0 + 9):
                x, y = P(l + d, q)
                L.p(x, y, ROHR[5] if d == 0 else ROHR[3] if d == 1 else ROHR[1])
        for q in (q0, q0 + 7):
            x, y = P(l + 1, q)
            L.p(x, y, ROHR[0])
    # Endkappen
    for l in (lang.start, lang.stop - 3):
        for d in range(3):
            for q in range(q0 - 1, q0 + 9):
                x, y = P(l + d, q)
                L.p(x, y, ROHR[2] if d < 2 else ROHR[0])
        x, y = P(l + 1, q0 + 2)
        L.p(x, y, ROHR[6])


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


def kran_sprite(spannweite, hoehe, container=None, katze_dx=0):
    """Portalkran in Frontalansicht: zwei Gitterbeine mit Fahrwerken, oberer Kastentraeger mit
    Katze, Seile mit Spreader und optional Container. Breite = spannweite (Aussenkante der Beine)."""
    im = Image.new('RGBA', (spannweite, hoehe), (0, 0, 0, 0))
    L = Leinwand(im)
    G = KRANGELB
    bein_b, traeger_h = 16, 18
    # Container am Haken (hinter den Seilen, vor dem Hintergrund)
    if container is not None:
        cw, ch = container.size
        cx = (spannweite - cw) // 2 + 6 + katze_dx
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
    kx = spannweite // 2 + 6 + katze_dx
    L.rect(kx - 14, 2, kx + 14, 14, STAHL[1])
    L.rect(kx - 13, 3, kx + 13, 6, STAHL[3])
    L.rect(kx + 4, 5, kx + 12, 12, GLAS[2]); L.p(kx + 5, 6, GLAS[4])
    # Seile
    for x in (kx - 8, kx - 2):
        for y in range(14, seil_unten):
            L.p(x, y, STAHL[0]); L.p(x + 1, y, STAHL[3])
    return im


# ---------------------------------------------------------------- Bodendetails (ersetzt bodenflecken)
MUELL = [
    [rgb('#e8e4d8'), rgb('#c8c2b0')],            # Papier
    [rgb('#d0d8de'), rgb('#a8b4bc')],            # Plastiktuete
    [rgb('#b5503e'), rgb('#8c3a30')],            # rote Dose
    [rgb('#aab6bd'), rgb('#717e87')],            # Blechdose
    [rgb('#3e6a44'), rgb('#5a8c5c')],            # gruene Flasche
    [rgb('#e8dcb4'), rgb('#c8a060')],            # Zigarettenstummel
    [rgb('#56626b'), rgb('#3e4850')],            # Schraube / Mutter
    [rgb('#94704e'), rgb('#5a4030')],            # Holzsplitter
]


def _hell(L, x, y, f=1.1):
    if 0 <= x < L.W and 0 <= y < L.H:
        r, g, b, a = L.px[x, y]
        L.px[x, y] = (min(255, int(r * f)), min(255, int(g * f)), min(255, int(b * f)), a)


def _riss(L, x, y, rnd, laenge, aste=True):
    dx = rnd.choice((1, -1))
    for i in range(laenge):
        L.neutral(x, y, 0.55)
        _hell(L, x, y + 1, 1.1)                      # Lichtkante unter dem Riss
        if aste and rnd.random() < 0.14:
            _riss(L, x, y, rnd, rnd.randint(3, 7), False)
        x += dx if rnd.random() < 0.7 else 0
        y += rnd.choice((0, 1, 1, -1))
    if rnd.random() < 0.35:                          # Unkraut im Riss
        for k in range(rnd.randint(1, 3)):
            L.p(x + k - 1, y - (k % 2), rgb('#5fbb58') if k % 2 else rgb('#45a052'))


def _abgesackt(L, X, Y, rnd):
    """Abgesackte 32x32-Betonplatte: etwas dunkler, breite Schattenkante oben/links, Licht unten/rechts."""
    for y in range(Y + 2, Y + 32):
        for x in range(X + 2, X + 32):
            L.neutral(x, y, 0.9)
    for i in range(2, 32):
        for d, f in ((2, 0.6), (3, 0.72), (4, 0.84)):
            L.neutral(X + i, Y + d, f); L.neutral(X + d, Y + i, f)
        _hell(L, X + i, Y + 31, 1.18); _hell(L, X + 31, Y + i, 1.12)
    for (cx, cy) in ((X + 4, Y + 5), (X + 27, Y + 27), (X + 26, Y + 6)):
        _riss(L, cx, cy, rnd, rnd.randint(4, 9), False)


def _schlagloch(L, x, y, rnd, asphalt=False):
    rx, ry = rnd.randint(3, 6), rnd.randint(2, 4)
    for dy in range(-ry, ry + 1):
        for dx in range(-rx, rx + 1):
            d = (dx / rx) ** 2 + (dy / ry) ** 2
            if d <= 1 + rnd.uniform(-0.2, 0.1):
                if d > 0.6 and (dx > 0 or dy > 0):
                    _hell(L, x + dx, y + dy, 1.2)                      # Lichtkante unten rechts
                elif d > 0.6:
                    L.neutral(x + dx, y + dy, 0.5)                     # Schattenkante oben links
                else:
                    L.p(x + dx, y + dy, SCHOTTER[rnd.randrange(4)] if rnd.random() < 0.6 else
                        (rgb('#1c2026') if asphalt else WAND[1]))


def _pfuetze(L, x, y, rnd):
    rx, ry = rnd.randint(4, 8), rnd.randint(2, 3)
    for dy in range(-ry, ry + 1):
        for dx in range(-rx, rx + 1):
            if (dx / rx) ** 2 + (dy / ry) ** 2 <= 1:
                L.dunkel(x + dx, y + dy, 0.74)
    L.p(x - rx // 2, y - 1, rgb('#c8d6e0')); L.p(x - rx // 2 + 1, y - 1, rgb('#9fb2c4'))


def _schutt(L, x, y, rnd):
    for _ in range(rnd.randint(6, 12)):
        px_, py_ = x + rnd.randint(-4, 4), y + rnd.randint(-2, 2)
        L.p(px_, py_, SCHOTTER[rnd.randrange(4)] if rnd.random() < 0.7 else WAND[rnd.randint(1, 4)])
        L.neutral(px_ + 1, py_ + 1, 0.7)


def boden_details(L, cls, rows, cols, nah_wand, seed=21, gesperrt=frozenset()):
    """Risse, abgesackte Platten, Schlagloecher, Flickstellen, Flecken, Pfuetzen, Kratzer, Schutt und Muell.
    Gibt die Kacheln der abgesackten Platten zurueck: dort liegt sonst nichts (keine Textur, kein Objekt)."""
    rnd = random.Random(seed)
    F = 0.9                                              # Haeufigkeit (90 % der ersten Fassung)
    dellen = set()
    for y in range(0, rows - 1, 2):
        for x in range(0, cols - 1, 2):
            if all(cls[y + j][x + i] == 'b' and (x + i, y + j) not in gesperrt for i in (0, 1) for j in (0, 1)) \
                    and rnd.random() < 0.045 * F:
                _abgesackt(L, x * T, y * T, rnd)
                dellen.update({(x, y), (x + 1, y), (x, y + 1), (x + 1, y + 1)})
    frei = lambda xx, yy: (xx // T, yy // T) not in dellen
    for y in range(rows):
        for x in range(cols):
            k = cls[y][x]
            X, Y = x * T + rnd.randint(2, 13), y * T + rnd.randint(2, 13)
            r = rnd.random()
            if (x, y) in dellen or any((x + dx, y + dy) in dellen for dx in (-1, 0, 1) for dy in (-1, 0, 1)):
                continue                                 # Dellen und ihr Rand bleiben sauber
            if k == 'b':
                if r < 0.10 * F:
                    _riss(L, X, Y, rnd, rnd.randint(10, 22))
                elif r < 0.12 * F:
                    _schlagloch(L, X, Y, rnd)
                elif r < 0.15 * F:
                    for dy in range(-3, 4):
                        for dx in range(-5, 6):
                            if dx * dx / 25 + dy * dy / 9 <= 1 and rnd.random() < 0.9:
                                L.neutral(X + dx, Y + dy, 0.72, waerme=4)
                elif r < 0.165 * F:
                    for _ in range(10):
                        L.p(X + rnd.randint(-4, 4), Y + rnd.randint(-2, 2), rgb('#8a5a3a') if rnd.random() < 0.5 else rgb('#a06a42'))
                elif r < 0.175 * F:
                    _pfuetze(L, X, Y, rnd)
                elif r < 0.19 * F:
                    _schutt(L, X, Y, rnd)
            elif k == 'a':
                if r < 0.04 * F:
                    _schlagloch(L, X, Y, rnd, asphalt=True)
                elif r < 0.08 * F:
                    w, h = rnd.randint(8, 16), rnd.randint(5, 10)
                    for yy in range(Y, Y + h):
                        for xx in range(X, X + w):
                            L.neutral(xx, yy, 0.84)
                elif r < 0.12 * F:
                    _riss(L, X, Y, rnd, rnd.randint(6, 12), False)
            elif k == 'm' and r < 0.15 * F:
                for i in range(rnd.randint(4, 10)):
                    L.p(X + i, Y + i // 3, rgb('#4c6878'))
            elif k in 'ph' and r < 0.06 * F:
                _riss(L, X, Y, rnd, rnd.randint(5, 10), False)
            for _ in range(2):
                if k in 'bawp' and rnd.random() < (0.16 if nah_wand(x, y) else 0.045):
                    farbe = MUELL[rnd.randrange(len(MUELL))]
                    mx, my = x * T + rnd.randint(1, 14), y * T + rnd.randint(1, 14)
                    L.p(mx, my, farbe[0]); L.p(mx + 1, my, farbe[1] if rnd.random() < 0.7 else farbe[0])
                    if rnd.random() < 0.5:
                        L.p(mx, my + 1, farbe[1])
                    L.neutral(mx + 1, my + 1, 0.72)
    return dellen


SCHLAMM = pal('#2e241c', '#3a2e24', '#4a3a2c', '#5a4634', '#6b5440', '#7d6650')
OELFILM = pal('#3a3a5a', '#4a5a3e', '#5a4a6a', '#3e5a5a')


def schlamm(L, zellen, seed=9):
    """Schlammige, oelige Flecken statt Gras: organischer Rand (unscharfe Maske + Rauschen), nasser
    dunkler Rand, hellere Kuppen, Pfuetzen mit Oelfilm (Regenbogen-Schimmer) und Spritzer drumherum."""
    from PIL import ImageFilter
    import numpy as np
    rnd = random.Random(seed)
    m = Image.new('L', (L.W, L.H), 0)
    mp = m.load()
    for (x, y) in zellen:
        for yy in range(y * T, (y + 1) * T):
            for xx in range(x * T, (x + 1) * T):
                mp[xx, yy] = 255
    m = np.array(m.filter(ImageFilter.GaussianBlur(6))).astype(np.float32) / 255
    h, w = m.shape
    rausch = np.random.RandomState(seed).rand(h // 4 + 2, w // 4 + 2)
    rausch = np.array(Image.fromarray((rausch * 255).astype(np.uint8)).resize((w + 8, h + 8), Image.BICUBIC))[:h, :w] / 255
    feld = m + (rausch - 0.5) * 0.35
    grob = np.random.RandomState(seed + 1).rand(h // 14 + 2, w // 14 + 2)
    grob = np.array(Image.fromarray((grob * 255).astype(np.uint8)).resize((w + 28, h + 28), Image.BICUBIC))[:h, :w] / 255
    ys, xs = np.nonzero(feld > 0.38)
    for y, x in zip(ys, xs):
        f = feld[y, x]
        if f <= 0.5:                                    # nasser Rand: nur abdunkeln
            L.neutral(x, y, 0.74, waerme=6)
            continue
        g = grob[y, x]
        c = SCHLAMM[3] if g > 0.55 else SCHLAMM[2]
        if f < 0.58:
            c = SCHLAMM[1]                              # dunkler, nasser Saum
        elif feld[max(0, y - 2), x] <= 0.5:
            c = SCHLAMM[5] if feld[max(0, y - 1), x] <= 0.5 else SCHLAMM[4]   # Lichtkante oben
        if f > 0.78 and g < 0.4:                        # Pfuetze mit Oelfilm
            c = SCHLAMM[0]
            if 0.30 < g < 0.325 or 0.2 < g < 0.215:      # Oelfilm als schimmernde Ringe
                c = OELFILM[(x // 3 + y // 2) % 4]
            if feld[max(0, y - 1), x] > 0.78 and grob[max(0, y - 1), x] >= 0.4:
                c = SCHLAMM[1]
        elif (x * 7 + y * 13) % 29 == 0:
            c = SCHLAMM[4]                              # einzelne Kiesel/Kuppen
        L.p(x, y, c)
    for _ in range(len(zellen) * 4):                   # Spritzer
        (x, y) = rnd.choice(zellen)
        sx, sy = x * T + rnd.randint(-8, 24), y * T + rnd.randint(-8, 24)
        L.p(sx, sy, SCHLAMM[2]); L.neutral(sx + 1, sy, 0.8, waerme=5)


# ---------------------------------------------------------------- Strommast (Hochspannung)
ISOLATOR = pal('#8a96a0', '#c8d0d6', '#e8eef2')


MAST = pal('#14181e', '#262d36', '#3a4450', '#55626e', '#7a8894')


def strommast_sprite(hoehe=104):
    """Stahlgitter-Strommast in Frontalansicht, exakt symmetrisch. Gibt (Bild, Leitungspunkte) zurueck;
    Leitungspunkte = Spitzen der Isolatoren an zwei Quertraegern (x, y relativ zum Sprite)."""
    B = 41
    im = Image.new('RGBA', (B, hoehe), (0, 0, 0, 0))
    L = Leinwand(im)
    M = B // 2
    fuss_b, kopf_b = 12, 3                                  # halbe Breite unten/oben
    def halb(y):
        return kopf_b + (fuss_b - kopf_b) * (y / (hoehe - 6))
    # Beine
    for y in range(6, hoehe - 4):
        h = halb(y)
        for s_ in (-1, 1):
            x = int(round(M + s_ * h))
            L.p(x, y, MAST[0]); L.p(x - s_, y, MAST[4] if s_ < 0 else MAST[2]); L.p(x - 2 * s_, y, MAST[0])
    # Gitter: Querstreben und Diagonalen
    stufen = list(range(14, hoehe - 6, 9))
    for i, y in enumerate(stufen):
        h = int(halb(y))
        for x in range(M - h, M + h + 1):
            L.p(x, y, MAST[1]); L.p(x, y + 1, MAST[0])
        if i + 1 < len(stufen):
            y2 = stufen[i + 1]
            h2 = int(halb(y2))
            for t in range(0, 101, 4):
                f = t / 100
                xa = int(round((M - h) + ((M + h2) - (M - h)) * f)); ya = int(round(y + (y2 - y) * f))
                xb = int(round((M + h) + ((M - h2) - (M + h)) * f))
                L.p(xa, ya, MAST[1]); L.p(xb, ya, MAST[1]); L.p(xa + 1, ya, MAST[3]); L.p(xb - 1, ya, MAST[0])
    # Spitze
    for y in range(0, 7):
        L.p(M, y, MAST[1]); L.p(M - 1, y, MAST[3])
    # Quertraeger mit Isolatoren
    punkte = []
    for ay, ab in ((10, 15), (24, 20)):
        for x in range(M - ab, M + ab + 1):
            L.p(x, ay, MAST[1]); L.p(x, ay - 1, MAST[4])
        for s_ in (-1, 1):
            xs = M + s_ * (ab - 1)
            for k in range(1, 6):
                c = ISOLATOR[2] if k % 2 else ISOLATOR[0]
                L.p(xs, ay + k, c); L.p(xs - 1, ay + k, ISOLATOR[1] if k % 2 else ISOLATOR[0])
            punkte.append((xs, ay + 6))
    # Fundamente
    for s_ in (-1, 1):
        x = M + s_ * fuss_b
        L.rect(x - 3, hoehe - 5, x + 4, hoehe, WAND[3])
        L.rect(x - 3, hoehe - 5, x + 4, hoehe - 4, WAND[5])
        L.rect(x - 3, hoehe - 1, x + 4, hoehe, WAND[1])
    return im, punkte


# ---------------------------------------------------------------- Bodenluefter (ins Dach/den Boden eingelassen)
def bodenluefter(L, tx, ty, frame=0, kacheln=2):
    """Ins Metalldach eingelassener Luefter, exakt auf dem Kachelraster (kacheln x kacheln).
    Vertieft: Schattenkante oben/links innen, Lichtkante unten/rechts; Rotor dreht sich je Frame,
    darueber ein Schutzgitter; Eckbolzen."""
    import math
    X, Y, S_ = tx * T, ty * T, kacheln * T
    M = MAST
    for y in range(Y, Y + S_):
        for x in range(X, X + S_):
            i, j = x - X, y - Y
            if i in (0, S_ - 1) or j in (0, S_ - 1):
                c = STAHL[0]
            elif i == 1 or j == 1:
                c = STAHL[4]                                # Rahmen-Licht oben links
            elif i == S_ - 2 or j == S_ - 2:
                c = STAHL[1]
            elif i in (2, 3) or j in (2, 3):
                c = STAHL[2]
            else:
                c = rgb('#10161c')                          # Schacht (dunkel)
                if i == 4 or j == 4:
                    c = rgb('#080c10')                      # Schatten der Rahmenkante
            L.p(x, y, c)
    # Rotor
    cx, cy, r = X + S_ / 2, Y + S_ / 2, S_ / 2 - 6
    winkel = frame / 16 * (math.pi / 2)                     # 4 Fluegel: Periode 90 Grad
    for y in range(Y + 5, Y + S_ - 5):
        for x in range(X + 5, X + S_ - 5):
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            d = math.hypot(dx, dy)
            if d > r:
                continue
            w = (math.atan2(dy, dx) - winkel) % (math.pi / 2)
            if d < 2.2:
                L.p(x, y, STAHL[4])                         # Nabe
            elif w < 0.62:
                L.p(x, y, STAHL[3] if w < 0.3 else STAHL[2])  # Fluegel mit Lichtkante
    # Schutzgitter darueber
    for k in range(X + 5, X + S_ - 5, 3):
        for y in range(Y + 5, Y + S_ - 5):
            L.p(k, y, STAHL[1])
    for (bx, by) in ((X + 2, Y + 2), (X + S_ - 3, Y + 2), (X + 2, Y + S_ - 3), (X + S_ - 3, Y + S_ - 3)):
        L.p(bx, by, STAHL[5])



def rohr_pfad(L, punkte):
    """Rohrleitung entlang einer Kachel-Polylinie [(x, y), ...] mit runden 90-Grad-Boegen an den Ecken."""
    import math
    if len(punkte) == 2:
        rohr(L, punkte[0], punkte[1])
        return
    # gerade Stuecke (an inneren Ecken um eine Kachel gekuerzt)
    for i in range(len(punkte) - 1):
        (ax, ay), (bx, by) = punkte[i], punkte[i + 1]
        dx, dy = (bx > ax) - (bx < ax), (by > ay) - (by < ay)
        if i > 0:
            ax, ay = ax + dx, ay + dy
        if i < len(punkte) - 2:
            bx, by = bx - dx, by - dy
        if (bx - ax) * dx >= 0 and (by - ay) * dy >= 0:
            rohr(L, (ax, ay), (bx, by))
    toene = [ROHR[1], ROHR[4], ROHR[5], ROHR[6], ROHR[4], ROHR[3], ROHR[2], ROHR[0]]
    for i in range(1, len(punkte) - 1):
        cx, cy = punkte[i]
        (px_, py_), (nx, ny) = punkte[i - 1], punkte[i + 1]
        d1 = ((cx > px_) - (cx < px_), (cy > py_) - (cy < py_))
        d2 = ((nx > cx) - (nx < cx), (ny > cy) - (ny < cy))
        mx, my = cx * T + 8 - 8 * d1[0] + 8 * d2[0], cy * T + 8 - 8 * d1[1] + 8 * d2[1]
        for y in range(cy * T - 2, cy * T + T + 2):
            for x in range(cx * T - 2, cx * T + T + 2):
                r = math.hypot(x + 0.5 - mx, y + 0.5 - my)
                if 4 <= r < 12 and cx * T <= x < cx * T + T and cy * T <= y < cy * T + T:
                    nxv, nyv = (x + 0.5 - mx) / r, (y + 0.5 - my) / r
                    t = int((r - 4))
                    licht = (nxv * -1 + nyv * -1) > 0          # Aussenseite zeigt zum Licht?
                    L.neutral(x + 3, y + 3, 0.8)
                    L.p(x, y, toene[7 - t] if licht else toene[t])


def dach_fassade(L, cls, rows, cols, hoehe=28, art='m'):
    """Flaechen der Art `art` (Metall) sind Daecher: an jeder Suedkante (darunter kein Dach) haengt eine
    Fassade (Paneele, Fensterband, Sockel) mit Schatten; Nord-/Seitenkanten bekommen eine Attika."""
    for y in range(rows):
        for x in range(cols):
            if cls[y][x] != art:
                continue
            X, Y = x * T, y * T
            unten = y + 1 < rows and cls[y + 1][x] == art
            if not unten and y + 1 < rows:
                F0 = (y + 1) * T
                for yy in range(F0, F0 + hoehe):
                    for xx in range(X, X + T):
                        k = yy - F0
                        c = REAK[3] if (xx % 16) == 1 else REAK[1] if (xx % 16) == 0 else REAK[2]
                        if k < 2:
                            c = REAK[4] if k == 0 else REAK[0]
                        elif 6 <= k <= 9 and (xx % 16) not in (0, 1, 15):
                            c = rgb('#1b3a3a') if k in (6, 9) else GRUEN[0] if (xx // 4) % 2 else rgb('#2a6a5a')
                        elif k >= hoehe - 2:
                            c = REAK[0]
                        L.p(xx, yy, c)
                for xx in range(X, X + T):
                    for d, f in ((0, 0.62), (1, 0.76), (2, 0.9)):
                        L.neutral(xx, F0 + hoehe + d, f)
            oben = y > 0 and cls[y - 1][x] == art
            if not oben:
                for xx in range(X, X + T):
                    L.p(xx, Y, REAK[5]); L.p(xx, Y + 1, REAK[4])
            for sx, nb in ((X, x - 1), (X + T - 1, x + 1)):
                if not (0 <= nb < cols and cls[y][nb] == art):
                    for yy in range(Y, Y + T + (hoehe if not unten else 0)):
                        L.p(sx, yy, REAK[0])
                    if nb > x:
                        for yy in range(Y, Y + T + (hoehe if not unten else 0)):
                            for d, f in ((1, 0.68), (2, 0.84)):
                                L.neutral(sx + d, yy, f)



def mauer_vorne(L, r):
    """Suedliche Aussenmauer im Vordergrund (nach allen Objekten gezeichnet): die Kappe ragt ueber die
    Kacheln dahinter (Wand ist hoch), darunter die nach Sueden gewandte Front mit Paneelen."""
    x0, x1 = r[0] * T, (r[2] + 1) * T
    yb = r[1] * T                                  # Mauerfuss (innen)
    kappe0 = yb - 14                               # Kappe ragt 14 px ueber den Boden davor
    y_end = (r[3] + 1) * T
    for x in range(x0, x1):
        for y in range(kappe0, yb + 6):            # Kappe (Draufsicht)
            k = y - kappe0
            c = WAND[6] if k == 0 else WAND[5] if k < 14 else WAND[4] if k < 18 else WAND[1]
            if (x - x0) % 32 == 0 and 0 < k < 18:
                c = WAND[3]
            L.p(x, y, c)
        L.p(x, kappe0 - 1, WAND[1])                # Innenkante
        for y in range(yb + 6, y_end):             # Front
            t = (y - yb - 6) / max(1, y_end - yb - 6)
            c = WAND[4] if t < 0.15 else WAND[3] if t < 0.6 else WAND[2]
            if (x - x0) % 24 == 0:
                c = WAND[1]
            elif (x - x0) % 24 == 1:
                c = WAND[5] if t < 0.6 else WAND[4]
            L.p(x, y, c)
    for x in range(x0, x1):                        # Kontaktschatten an der Innenkante
        for d, f in ((2, 0.7), (3, 0.85)):
            L.neutral(x, kappe0 - d, f)
