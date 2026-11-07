"""Gebaeude fuer Karte 18 (The Fog-Bound City) - prozedural am 16x16-Raster, frontal mit sichtbarem Dach.

  python3 tools/karte18_gebaeude.py   ->  assets/objekte/karte18/gebaeude/<art>.png, uebersicht.png

Jedes Gebaeude fuellt genau sein Rechteck aus layout.json ('gebaeude'): oben die Dachflaeche von leicht oben (Attika
mit Lichtkante, Dachaufbauten), darunter die Suedfassade, unten der Sockel. Tueren liegen auf ganzen Kacheln und zeigen
zum Gehweg. Licht von oben links: linke/obere Kanten hell, rechte/untere dunkel; Umriss in der dunkelsten Farbe.
Abendstimmung: einzelne Fenster sind warm erleuchtet (echte Lichtquelle -> 'fensterlicht'), Reklame leuchtet.
Anspielung bei der Messehalle nur ueber die Form (zwei umgedrehte Pyramiden), kein Nachbau.
"""
import json, math, os, random
import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte18')
OUT = os.path.join(ROOT, 'assets', 'objekte', 'karte18', 'gebaeude')
T = 16
H = lambda h: np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)] + [255], np.uint8)
UMRISS = H('#1c1e2a')
WARM = [H('#f0c878'), H('#e8b060'), H('#f6dc9a')]
NACHT = [H('#2a3550'), H('#24304a'), H('#30405e')]


class Bild:
    def __init__(self, w, h):
        self.a = np.zeros((h, w, 4), np.uint8)
        self.w, self.h = w, h

    def r(self, x0, y0, x1, y1, c):                       # Rechteck inklusive
        x0, y0, x1, y1 = max(0, x0), max(0, y0), min(self.w - 1, x1), min(self.h - 1, y1)
        if x1 >= x0 and y1 >= y0:
            self.a[y0:y1 + 1, x0:x1 + 1] = c

    def px(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.a[y, x] = c

    def kasten(self, x0, y0, x1, y1, c, hell, dunkel, umriss=None):
        """Kasten mit Licht oben links, Schatten unten rechts."""
        self.r(x0, y0, x1, y1, c)
        self.r(x0, y0, x1, y0, hell); self.r(x0, y0, x0, y1, hell)
        self.r(x0, y1, x1, y1, dunkel); self.r(x1, y0, x1, y1, dunkel)
        if umriss is not None:
            self.r(x0 - 1, y0 - 1, x1 + 1, y0 - 1, umriss); self.r(x0 - 1, y1 + 1, x1 + 1, y1 + 1, umriss)
            self.r(x0 - 1, y0, x0 - 1, y1, umriss); self.r(x1 + 1, y0, x1 + 1, y1, umriss)

    def umriss(self):
        al = self.a[..., 3] > 0
        rand = al & ~(np.roll(al, 1, 0) & np.roll(al, -1, 0) & np.roll(al, 1, 1) & np.roll(al, -1, 1))
        rand[0, :] |= al[0, :]; rand[-1, :] |= al[-1, :]; rand[:, 0] |= al[:, 0]; rand[:, -1] |= al[:, -1]
        self.a[rand] = UMRISS

    def save(self, name):
        os.makedirs(OUT, exist_ok=True)
        Image.fromarray(self.a).save(os.path.join(OUT, name + '.png'))


def dach(b, x0, x1, y0, y1, c, rs, aufbauten=True, schraeg=0):
    """Flachdach mit Attika: aussen 2 px Rand (oben/links hell), innen Dachpappe, Aufbauten (Lueftung, Klimageraete,
    Treppenhaus) unregelmaessig verteilt."""
    hell, mittel, dunkel = c
    b.r(x0, y0, x1, y1, mittel)
    b.r(x0, y0, x1, y0 + 1, hell); b.r(x0, y0, x0 + 1, y1, hell)
    b.r(x1 - 1, y0, x1, y1, dunkel)
    b.r(x0 + 3, y0 + 3, x1 - 3, y1 - 1, (mittel.astype(int) * 0.86).astype(np.uint8) | np.array([0, 0, 0, 255], np.uint8))
    if not aufbauten:
        return
    x = x0 + 8 + rs.randint(0, 10)
    while x < x1 - 24:
        art = rs.choice(('klima', 'luefter', 'leer', 'leer'))
        if art == 'klima' and y1 - y0 > 10:
            yy = y0 + 4 + rs.choice((0, max(0, y1 - y0 - 14) // 2, max(0, y1 - y0 - 14)))
            b.kasten(x, yy, x + 11, yy + 7, H('#9aa0ac'), H('#c4c8d2'), H('#5a5e6a'))
            b.r(x + 3, yy + 2, x + 8, yy + 5, H('#4a4e5a'))
            b.r(x, yy + 8, x + 12, yy + 8, H('#3a3c48'))
            x += 18 + rs.randint(4, 22)
        elif art == 'luefter':
            yy = y0 + 4 + rs.choice((0, max(0, y1 - y0 - 10)))
            b.kasten(x, yy, x + 5, yy + 4, H('#7a808c'), H('#a4aab4'), H('#4a4e5a'))
            x += 14 + rs.randint(4, 24)
        else:
            x += 20 + rs.randint(0, 20)


def fenster(b, x0, y0, w, h, rs, licht=0.3, rahmen=H('#c8ccd4'), sprosse=True):
    """Fenster: Rahmen, Glas dunkelblau mit Lichtreflex oben links oder warm erleuchtet."""
    b.r(x0 - 1, y0 - 1, x0 + w, y0 + h, rahmen)
    an = rs.random() < licht
    g = rs.choice(WARM) if an else rs.choice(NACHT)
    b.r(x0, y0, x0 + w - 1, y0 + h - 1, g)
    if not an:
        b.r(x0, y0, x0 + max(1, w // 3), y0, H('#5a6c90'))
        b.px(x0, y0 + 1, H('#4a5a7c'))
    else:
        b.r(x0, y0 + h - 2, x0 + w - 1, y0 + h - 1, H('#c8904a'))
    if sprosse and w >= 8:
        b.r(x0 + w // 2, y0, x0 + w // 2, y0 + h - 1, rahmen)
    b.r(x0 - 1, y0 + h, x0 + w, y0 + h, H('#5a5e6c'))           # Sims-Schatten


def tuer(b, x0, y1, w, h, glas=False, farbe=H('#4a3a34')):
    """Tuer (unten buendig auf y1): Laibung dunkel, Blatt, Griff."""
    b.r(x0 - 1, y1 - h - 1, x0 + w, y1, H('#2a2c36'))
    if glas:
        b.r(x0, y1 - h, x0 + w - 1, y1, H('#3a4a6a'))
        b.r(x0 + w // 2, y1 - h, x0 + w // 2, y1, H('#8a92a4'))
        b.r(x0, y1 - h, x0 + w - 1, y1 - h, H('#9aa2b4'))
        b.r(x0 + 1, y1 - h + 2, x0 + 2, y1 - h + 8, H('#6a7a9a'))
    else:
        b.r(x0, y1 - h, x0 + w - 1, y1, farbe)
        b.r(x0, y1 - h, x0 + w - 1, y1 - h, (farbe.astype(int) + 30).clip(0, 255).astype(np.uint8))
        b.px(x0 + w - 3, y1 - h // 2, H('#d0c8a0'))


def sockel(b, y0, x0, x1, c=H('#4a4e5a')):
    b.r(x0, y0, x1, y0 + 2, c)
    b.r(x0, y0, x1, y0, H('#6a6e7c'))


# ---------------------------------------------------------------------------------------------- Ladenzeile
LADEN = [   # Wand, Markise (2 Farben), Schildband, Art
    ('#e4e2dc', ('#c84a44', '#f0ece4'), '#e070a0', 'konbini'),
    ('#d6cfc0', ('#4a7a4a', '#d8e4c8'), '#3a6a3a', 'apotheke'),
    ('#c8c4c0', ('#2a3a5a', '#5a7ab0'), '#f0f0f0', 'buch'),
    ('#e8d8d0', ('#e07a9a', '#f6e0e8'), '#e070a0', 'cafe'),
    ('#b8b2a8', ('#8a2a2a', '#c04040'), '#d8b040', 'ramen'),
    ('#d8d4c8', ('#e08a3a', '#f6d0a0'), '#3a8ac0', 'baeckerei'),
    ('#e0dcd4', ('#3a6aa0', '#f0f0f0'), '#e070a0', 'konbini2'),
]


def ladenzeile(w, h, rs):
    b = Bild(w, h)
    n = w // 96
    for i in range(n):
        x0, x1 = i * 96, i * 96 + 95
        wand, (m1, m2), schild, art = LADEN[i % len(LADEN)]
        wand = H(wand)
        hoehe_dach = 14 + (4 if i % 3 == 1 else 0)            # leicht unterschiedliche Traufhoehen
        dach(b, x0, x1, 0, hoehe_dach, (H('#8a8e9c'), H('#6e7280'), H('#4e5260')), rs)
        if i % 2 == 0:                                       # Dachschild auf jedem zweiten Haus
            b.kasten(x0 + 30, 3, x0 + 65, hoehe_dach - 3, H(schild), H('#ffffff'), H('#3a3a44'))
            for k in range(4):
                b.r(x0 + 35 + k * 7, 6, x0 + 39 + k * 7, hoehe_dach - 6, H('#ffffff') if schild != '#f0f0f0' else H('#3a4a6a'))
        y = hoehe_dach + 1
        b.r(x0, y, x1, h - 1, wand)                          # Fassade
        b.r(x0, y, x1, y + 1, (wand.astype(int) + 14).clip(0, 255).astype(np.uint8))
        b.r(x1 - 1, y, x1, h - 1, (wand.astype(int) * 0.8).astype(np.uint8) | np.array([0, 0, 0, 255], np.uint8))
        # Obergeschoss: zwei Fenster, bei manchen ein Balkongitter
        for fx in (x0 + 12, x0 + 54):
            fenster(b, fx, y + 6, 26, 16, rs, licht=0.45)
        if i % 3 == 2:
            b.r(x0 + 8, y + 24, x0 + 88, y + 24, H('#5a5e6a'))
            for gx in range(x0 + 8, x0 + 89, 4):
                b.r(gx, y + 18, gx, y + 24, H('#5a5e6a'))
        b.kasten(x0 + 82, y + 4, x0 + 91, y + 11, H('#a4a8b2'), H('#d0d4dc'), H('#5a5e6a'))   # Klimageraet
        # Schildband ueber dem Laden
        ys = y + 30
        b.r(x0 + 2, ys, x1 - 2, ys + 7, H(schild))
        b.r(x0 + 2, ys, x1 - 2, ys, (H(schild).astype(int) + 40).clip(0, 255).astype(np.uint8))
        for k in range(5):
            b.r(x0 + 14 + k * 14, ys + 2, x0 + 22 + k * 14, ys + 5, H('#ffffff') if schild not in ('#f0f0f0', '#d8b040') else H('#2a2a34'))
        # Markise gestreift mit Volant
        ym = ys + 8
        for x in range(x0 + 2, x1 - 1):
            for d in range(7):
                c = H(m1) if ((x - x0) // 6) % 2 == 0 else H(m2)
                if d >= 5:
                    c = (c.astype(int) * 0.78).astype(np.uint8) | np.array([0, 0, 0, 255], np.uint8)
                b.px(x, ym + d, c)
            if ((x - x0) // 6) % 2 == 0:
                b.px(x, ym + 7, H(m1))
        # Erdgeschoss: Schaufenster (warm erleuchtet), Tuer auf einer ganzen Kachel
        ye = ym + 9
        tx = x0 + 48 if art not in ('ramen',) else x0 + 64
        b.r(x0 + 6, ye, x1 - 6, h - 4, H('#3a3e4a'))
        for (sx0, sx1) in ((x0 + 8, tx - 4), (tx + 20, x1 - 8)):
            if sx1 - sx0 < 8:
                continue
            b.r(sx0, ye + 2, sx1, h - 6, rs.choice(WARM))
            b.r(sx0, ye + 2, sx1, ye + 2, H('#fff0c0'))
            for k in range(sx0 + 3, sx1 - 2, 7):              # Ware im Schaufenster
                b.r(k, h - 11, k + 3, h - 7, rs.choice((H('#c04a44'), H('#4a7a4a'), H('#3a6aa0'), H('#e8c040'))))
            b.r(sx0, h - 6, sx1, h - 6, H('#8a8e9a'))
        if art == 'ramen':                                    # Noren-Vorhang und rote Laternen
            b.r(tx, ye, tx + 15, ye + 8, H('#2a3a5a'))
            for k in range(tx, tx + 16, 4):
                b.r(k, ye, k, ye + 8, H('#1a2440'))
            for lx in (x0 + 10, x0 + 84):
                b.kasten(lx, ye - 2, lx + 5, ye + 6, H('#d04030'), H('#f07050'), H('#802020'))
        tuer(b, tx, h - 4, 16, 22, glas=art in ('konbini', 'konbini2', 'cafe', 'apotheke', 'buch', 'baeckerei'))
        if art == 'apotheke':
            b.r(x0 + 84, ys - 12, x0 + 92, ys - 4, H('#3a8a4a'))
            b.r(x0 + 87, ys - 11, x0 + 89, ys - 5, H('#ffffff')); b.r(x0 + 85, ys - 9, x0 + 91, ys - 7, H('#ffffff'))
        sockel(b, h - 3, x0, x1)
        b.r(x1, hoehe_dach + 1, x1, h - 1, H('#3a3c48'))      # Hausfuge
    b.umriss()
    return b


# ---------------------------------------------------------------------------------------------- Buerohaeuser
def buero(w, h, rs, glas=('#2a3654', '#3a4a6e', '#56709c'), wand='#3e4454', dach_h=30, tuer_x=None, stockwerke=4):
    b = Bild(w, h)
    dach(b, 0, w - 1, 0, dach_h, (H('#7a7e8c'), H('#5a5e6c'), H('#3e4250')), rs)
    # Treppenhaus-Aufbau auf dem Dach
    b.kasten(w - 70, 4, w - 30, dach_h - 6, H('#6a6e7c'), H('#8e92a0'), H('#40444e'))
    b.r(w - 58, 10, w - 50, dach_h - 6, H('#2a2e3a'))
    y = dach_h + 1
    b.r(0, y, w - 1, h - 1, H(wand))
    b.r(0, y, w - 1, y + 2, H('#8a8e9c'))                      # Gesims
    b.r(0, y + 3, w - 1, y + 3, H('#2a2e38'))
    eg = 40
    hoehe = (h - y - 4 - eg) // stockwerke
    g0, g1, g2 = H(glas[0]), H(glas[1]), H(glas[2])
    for s in range(stockwerke):
        ys = y + 6 + s * hoehe
        b.r(4, ys, w - 5, ys + hoehe - 9, g0)                  # Fensterband
        for x in range(4, w - 4):
            if (x - 4) % 16 == 0:
                b.r(x, ys, x, ys + hoehe - 9, H('#7a8294'))     # Pfosten
        for x in range(8, w - 8, 16):                          # Reflexe / Licht
            if rs.random() < 0.25:
                b.r(x - 3, ys + 1, x + 10, ys + hoehe - 10, rs.choice(WARM))
            else:
                b.r(x - 3, ys + 1, x + 3, ys + 2, g2)
                b.px(x - 3, ys + 3, g1)
        b.r(4, ys + hoehe - 8, w - 5, ys + hoehe - 8, H('#8a8e9c'))   # Bruestung Licht
        b.r(4, ys + hoehe - 7, w - 5, ys + hoehe - 5, H(wand))
    # Erdgeschoss: Glasfront, Vordach, Tuer (2 Kacheln) auf dem Raster
    ye = h - eg
    b.r(4, ye + 6, w - 5, h - 5, g0)
    for x in range(4, w - 4, 16):
        b.r(x, ye + 6, x, h - 5, H('#7a8294'))
    tx = tuer_x if tuer_x is not None else (w // 2 - 16)
    b.kasten(tx - 10, ye, tx + 41, ye + 5, H('#9aa0ac'), H('#c8ccd6'), H('#4a4e5a'))   # Vordach
    b.r(tx - 8, ye + 6, tx + 39, ye + 7, H('#2a2c36'))         # Schatten unter dem Vordach
    tuer(b, tx, h - 4, 15, 26, glas=True)
    tuer(b, tx + 16, h - 4, 15, 26, glas=True)
    for x in range(tx - 6, tx + 38, 6):                        # warmes Licht im Foyer
        b.px(x, ye + 9, H('#f0c878'))
    sockel(b, h - 3, 0, w - 1)
    b.umriss()
    return b


def wohnblock(w, h, rs):
    b = Bild(w, h)
    dh = 22
    dach(b, 0, w - 1, 0, dh, (H('#8a8478'), H('#6e685e'), H('#4e4a44')), rs)
    b.kasten(20, 3, 60, dh - 5, H('#a49e94'), H('#c8c2b8'), H('#6a645c'))           # Treppenhaus
    b.r(34, 8, 42, dh - 5, H('#3a3a40'))
    b.kasten(w - 52, 4, w - 32, dh - 7, H('#8a9098'), H('#b0b6be'), H('#5a6068'))    # Wassertank
    y = dh + 1
    wand = H('#a8a6a2')
    b.r(0, y, w - 1, h - 1, wand)
    b.r(0, y, w - 1, y + 1, H('#c8c6c0'))
    stock = 5
    hs = (h - y - 6) // stock
    for s in range(stock):
        ys = y + 3 + s * hs
        for u in range(w // 64):
            ux = u * 64
            if s == stock - 1 and u == (w // 64) // 2:
                continue                                       # Eingang in der Mitte
            fenster(b, ux + 8, ys + 6, 16, 14, rs, licht=0.35)
            # Balkontuer + Balkon mit Gelaender
            b.r(ux + 30, ys + 4, ux + 54, ys + 22, H('#3a4050'))
            b.r(ux + 31, ys + 5, ux + 41, ys + 21, rs.choice(NACHT + [WARM[0]]))
            b.r(ux + 44, ys + 5, ux + 53, ys + 21, rs.choice(NACHT))
            b.r(ux + 28, ys + 14, ux + 56, ys + 14, H('#d8d6d0'))
            b.r(ux + 28, ys + 22, ux + 56, ys + 23, H('#7a7874'))
            for gx in range(ux + 28, ux + 57, 3):
                b.r(gx, ys + 15, gx, ys + 21, H('#6a6864'))
            if rs.random() < 0.35:                             # Waesche auf dem Balkon
                for k in range(3):
                    c = rs.choice((H('#e8e8f0'), H('#c84a5a'), H('#5a8ac0'), H('#e8c040')))
                    b.r(ux + 32 + k * 7, ys + 9, ux + 36 + k * 7, ys + 15, c)
            if rs.random() < 0.4:
                b.kasten(ux + 47, ys + 16, ux + 54, ys + 21, H('#b8bcc4'), H('#dcdfe4'), H('#6a6e78'))
        b.r(0, ys + hs - 1, w - 1, ys + hs - 1, H('#8a8884'))
    # Eingang (2 Kacheln, mittig auf Kachelgrenze), Vordach, Briefkaesten
    mx = (w // 64) // 2 * 64
    tx = mx + 16
    b.kasten(tx - 6, h - 34, tx + 37, h - 30, H('#8a8e98'), H('#b8bcc6'), H('#4a4e58'))
    tuer(b, tx, h - 4, 15, 24, glas=True)
    tuer(b, tx + 16, h - 4, 15, 24, glas=True)
    b.r(tx - 4, h - 26, tx - 1, h - 12, H('#6a6e78'))
    sockel(b, h - 3, 0, w - 1, H('#6a6660'))
    b.umriss()
    return b


def lager(w, h, rs, art):
    b = Bild(w, h)
    dh = 52
    if art == 'shed':                                          # Sheddach: drei Zaehne (Firste N-S), Glas am First
        zahn = w // 3
        for z in range(3):
            x0 = z * zahn
            for y in range(dh):
                for x in range(x0, x0 + zahn):
                    t = (x - x0) / zahn
                    if t > 0.82:
                        c = H('#2a3a5a') if (y % 6) else H('#5a6a8a')            # senkrechtes Oberlicht am First
                    else:
                        c = (H('#b0b4be') * (1 - 0.25 * t)).astype(np.uint8) | np.array([0, 0, 0, 255], np.uint8)
                        if (y % 8) == 0:
                            c = H('#8a8e9a')
                    if y < 2:
                        c = H('#c8ccd6')
                    b.px(x, y, c)
            b.r(x0 + int(zahn * 0.82), 0, x0 + int(zahn * 0.82), dh, H('#e0e4ec'))
            b.r(x0 + zahn - 1, 0, x0 + zahn - 1, dh, H('#3a3e4a'))
        b.r(0, dh - 3, w - 1, dh - 1, H('#5a5e68'))
    else:                                                      # flaches Wellblechdach
        for y in range(dh):
            for x in range(w):
                c = H('#8a8e98') if (x % 6) < 4 else H('#727680')
                if y < 2:
                    c = H('#b0b4be')
                b.px(x, y, c)
        b.r(0, dh - 3, w - 1, dh - 1, H('#5a5e68'))            # Dachrinne
        b.kasten(30, 12, 50, 26, H('#9aa0ac'), H('#c4c8d2'), H('#5a5e6a'))
    y = dh
    wand = H('#a4a8b0') if art == 'rolltor' else H('#b4b0a8')
    b.r(0, y, w - 1, h - 1, wand)
    b.r(0, y, w - 1, y + 1, H('#cfd2d8'))
    if art == 'rolltor':                                       # rot-weiss-blaues Band
        for x in range(w):
            c = (H('#c84a44'), H('#f0f0f0'), H('#3a6aa0'))[(x // 16) % 3]
            b.r(x, y + 8, x, y + 12, c)
        tore = [(16, 63), (96, 143)]
        tuer_x = 160
    else:
        b.r(0, y + 8, w - 1, y + 11, H('#e08a3a'))
        tore = [(16, 79)]
        tuer_x = 128
        fenster(b, 160, y + 24, 18, 12, rs, licht=1.0)
    for i, (x0, x1) in enumerate(tore):                        # Rolltore
        b.r(x0 - 2, y + 16, x1 + 2, h - 4, H('#5a5e68'))
        offen = (i == 1)
        for yy in range(y + 18, h - 4):
            if offen and yy > y + 46:
                b.r(x0, yy, x1, yy, H('#1a1c24'))
                continue
            c = H('#8e929c') if (yy - y) % 4 else H('#6a6e78')
            b.r(x0, yy, x1, yy, c)
        b.r(x0, y + 18, x1, y + 18, H('#b8bcc6'))
    tuer(b, tuer_x, h - 4, 15, 26, farbe=H('#3a5a7a'))
    b.kasten(tuer_x + 4, h - 38, tuer_x + 10, h - 34, H('#f0d890'), H('#fff4c0'), H('#a08040'))   # Lampe ueber der Tuer
    sockel(b, h - 3, 0, w - 1)
    b.umriss()
    return b


# ---------------------------------------------------------------------------------------------- Messehalle
def halle(w, h, rs):
    """Messehalle (Rechteck x 84..119, y 4..27): Glasfassade unten (8 Kacheln), Dach darueber, zwei umgedrehte
    Pyramiden auf Kernen, exakt spiegelsymmetrisch zur Achse (w/2)."""
    b = Bild(w, h)
    mx = w // 2
    dach_y0, fass_y0 = 124, 256                              # Dach ab Reihe 12, Fassade ab Reihe 20
    # Dach der Halle (leicht von oben): Attika, Oberlichtbaender, Kanten
    b.r(0, dach_y0, w - 1, fass_y0 - 1, H('#9aa0ae'))
    b.r(0, dach_y0, w - 1, dach_y0 + 2, H('#c4c8d4'))
    b.r(0, dach_y0, 2, fass_y0 - 1, H('#b4b8c4'))
    b.r(w - 3, dach_y0, w - 1, fass_y0 - 1, H('#6a6e7c'))
    b.r(6, dach_y0 + 6, w - 7, fass_y0 - 12, H('#868a98'))
    for x in range(6, w - 7):                                  # Dachbahnen (Fugen alle 32 px, symmetrisch)
        if (x - mx) % 32 == 0:
            b.r(x, dach_y0 + 7, x, fass_y0 - 13, H('#7a7e8c'))
    for x0 in (24, w - 24 - 48):                               # Oberlichter (symmetrisch)
        b.kasten(x0, dach_y0 + 20, x0 + 48, dach_y0 + 30, H('#3a4a6a'), H('#7a8aaa'), H('#2a2e3a'))
    b.r(0, fass_y0 - 11, w - 1, fass_y0 - 2, H('#aeb2be'))       # Gesims ueber der Fassade
    b.r(0, fass_y0 - 11, w - 1, fass_y0 - 11, H('#d4d8e2'))
    b.r(0, fass_y0 - 2, w - 1, fass_y0 - 1, H('#5a5e6c'))
    # Glasfassade mit Steinpfeilern im festen Rhythmus (alle 64 px, symmetrisch)
    b.r(0, fass_y0, w - 1, h - 1, H('#2c3a58'))
    for y in range(fass_y0, h - 4):
        for x in range(0, w):
            if (y - fass_y0) % 24 == 0:
                b.px(x, y, H('#8a94aa'))
            elif (x - mx) % 16 == 0:
                b.px(x, y, H('#6a7894'))
    for x in range(8, w - 8, 16):                              # Reflexe / Licht innen
        for y in range(fass_y0 + 3, h - 8, 24):
            if rs.random() < 0.22:
                b.r(x + 2, y, x + 12, y + 18, H('#e8c070'))
            else:
                b.r(x + 2, y, x + 7, y + 1, H('#5a6e98'))
    for k in range(-4, 5):                                     # Pfeiler
        px_ = mx + k * 64
        if 0 < px_ < w:
            b.kasten(px_ - 6, fass_y0, px_ + 5, h - 4, H('#b8bcc8'), H('#dcdfe8'), H('#6e7280'))
    b.kasten(0, fass_y0, 9, h - 4, H('#b8bcc8'), H('#dcdfe8'), H('#6e7280'))
    b.kasten(w - 10, fass_y0, w - 1, h - 4, H('#b8bcc8'), H('#dcdfe8'), H('#6e7280'))
    # Eingang mittig (8 Kacheln = Mittelweg), Vordach, Glastueren
    ex0, ex1 = mx - 64, mx + 63
    b.kasten(ex0 - 6, h - 58, ex1 + 6, h - 50, H('#c8ccd6'), H('#eef0f6'), H('#6a6e7c'))
    b.r(ex0 - 4, h - 49, ex1 + 4, h - 48, H('#2a2c36'))
    for tx in range(ex0, ex1, 16):
        tuer(b, tx + 1, h - 4, 14, 40, glas=True)
    sockel(b, h - 3, 0, w - 1, H('#6a6e7c'))
    # Pyramiden: oben breit (224), unten schmal (96), Hoehe 150; Deckflaeche 14 px von oben sichtbar
    for cx in (mx - 128, mx + 128):
        top, hoch, ob, ub, deck = 4, 132, 112, 44, 20
        ky0 = top + deck + hoch
        for (kx0, kx1) in ((cx - 40, cx - 17), (cx + 16, cx + 39)):      # zwei Kerne (Stuetzen) bis aufs Dach
            b.kasten(kx0, ky0 - 6, kx1, 214, H('#a8acb8'), H('#ccd0da'), H('#62667a'))
            for y in range(ky0 + 4, 206, 12):
                b.r(kx0 + 6, y, kx1 - 6, y + 5, H('#3a4a6a'))
            b.r(kx0 - 2, 215, kx1 + 3, 217, H('#5a5e6c'))                   # Kontaktschatten auf dem Dach
        b.r(cx - 16, ky0 - 6, cx + 15, ky0 + 30, H('#7a7e8c'))                # Bruecke zwischen den Kernen
        b.r(cx - 16, ky0 - 6, cx + 15, ky0 - 6, H('#a4a8b4'))
        for x in range(cx - 14, cx + 13, 8):
            b.r(x, ky0 + 2, x + 4, ky0 + 14, H('#3a4a6a'))
        for y in range(top, top + deck):                                   # Deckflaeche von oben (Trapez)
            einzug = (top + deck - y) // 4
            for x in range(cx - ob + einzug, cx + ob - einzug):
                c = H('#ccd0da') if (y - top) < deck - 3 else H('#e6e8ee')
                if (x - cx) % 32 == 0 or (y - top) % 7 == 0:
                    c = H('#aeb2be')
                b.px(x, y, c)
        b.r(cx - ob + 5, top, cx + ob - 6, top, H('#9aa0ac'))
        for y in range(top + deck, top + deck + hoch):
            t = (y - top - deck) / hoch
            halb = int(round(ob + (ub - ob) * t))
            for x in range(cx - halb, cx + halb):
                u = (x - (cx - halb)) / (2 * halb)
                c = H('#b4b8c4') if u < 0.55 else H('#8e92a0')          # links Licht, rechts Schatten
                if (y - top - deck) % 18 == 0:
                    c = H('#7a7e8c')
                if abs(x - cx) % 32 == 0:
                    c = (c.astype(int) * 0.86).astype(np.uint8) | np.array([0, 0, 0, 255], np.uint8)
                b.px(x, y, c)
            b.px(cx - halb, y, H('#d8dce4')); b.px(cx + halb - 1, y, H('#5a5e6c'))
        b.r(cx - ub, top + deck + hoch - 2, cx + ub - 1, top + deck + hoch - 1, H('#5a5e6c'))   # Unterkante
    b.umriss()
    return b


def pfeiler():
    """Hochbahn-Pfeiler: 2 Kacheln breit, von der Unterkante der Fahrbahn (Reihe 84) bis auf den Mittelstreifen
    (Fuss Reihe 88): Kapitell oben, Saeule mit Licht links / Schatten rechts, Sockel unten."""
    b = Bild(32, 80)
    b.kasten(2, 0, 29, 7, H('#9a9eaa'), H('#c4c8d2'), H('#5a5e6c'))           # Kapitell (unter der Fahrbahn)
    b.r(2, 8, 29, 9, H('#4a4e5c'))
    for y in range(10, 72):
        for x in range(6, 26):
            t = (x - 6) / 20
            c = H('#b4b8c4') if t < 0.3 else H('#9a9eaa') if t < 0.65 else H('#787c8a')
            if (y - 10) % 20 == 0:
                c = H('#6a6e7c')
            b.px(x, y, c)
    b.kasten(3, 72, 28, 79, H('#8a8e9a'), H('#b0b4be'), H('#4a4e5c'))          # Sockel
    b.umriss()
    return b


def zug(wagen=3, laenge=112):
    """Hochbahn-Zug frontal von der Seite: weisse Wagen mit dunkelblauem Fensterband, Fenster, Tueren, Schuerze;
    vorn (Osten) eine runde Nase mit Scheibe, hinten (Westen) gerade. 3 Wagen, Kupplungen dazwischen."""
    w, h = wagen * laenge + 2, 30
    b = Bild(w, h)
    for i in range(wagen):
        x0, x1 = i * laenge + 1, (i + 1) * laenge - 2
        nase = (i == wagen - 1)
        for y in range(2, 27):
            xe = x1
            if nase:                                          # Nase: Rundung nach vorn
                einzug = int(round(10 * (1 - math.sqrt(max(0.0, 1 - ((y - 16) / 15.0) ** 2)))))
                xe = x1 - einzug
            for x in range(x0, xe + 1):
                c = H('#e8eaf0')
                if y < 4:
                    c = H('#f6f8fc')                          # Dach (Licht)
                elif 8 <= y <= 15:
                    c = H('#24345a')                          # Fensterband
                elif y == 16:
                    c = H('#3a5aa0')
                elif y >= 22:
                    c = H('#9aa0b0') if y < 25 else H('#5a6070')   # Schuerze
                b.px(x, y, c)
        for fx in range(x0 + 6, x1 - 12, 14):                 # Fenster
            if nase and fx > x1 - 26:
                continue
            b.r(fx, 9, fx + 9, 14, H('#5a78b0'))
            b.r(fx, 9, fx + 3, 9, H('#a8c0e8'))
        for tx in (x0 + 24, x0 + 80):                          # Tueren
            b.r(tx, 7, tx + 9, 21, H('#c8ccd6'))
            b.r(tx + 4, 7, tx + 5, 21, H('#8a90a0'))
            b.r(tx + 1, 9, tx + 3, 14, H('#3a4a70')); b.r(tx + 6, 9, tx + 8, 14, H('#3a4a70'))
        if nase:
            b.r(x1 - 18, 8, x1 - 6, 15, H('#1a2440'))         # Frontscheibe
            b.r(x1 - 18, 8, x1 - 14, 8, H('#7a9ad0'))
            b.r(x1 - 5, 18, x1 - 3, 19, H('#fff0b0'))         # Scheinwerfer
        if i < wagen - 1:
            b.r(x1 + 1, 12, x1 + 3, 22, H('#3a3e4c'))         # Kupplung / Faltenbalg
    b.umriss()
    return b


def kuebel():
    """Pflanzkuebel auf dem Platz: 4x2 Kacheln, Steinrand mit Lichtkante, innen Hecke von oben, vorn 8 px Steinfront."""
    b = Bild(64, 32)
    b.r(0, 0, 63, 31, H('#8a8496'))
    b.r(0, 0, 63, 1, H('#b4aec4')); b.r(0, 0, 1, 23, H('#a49eb6'))
    b.r(62, 0, 63, 23, H('#5e5872'))
    b.r(3, 3, 60, 21, H('#2e4632'))
    rs = random.Random(64)
    for _ in range(90):                                       # Blattballen, Licht oben links
        x, y = rs.randint(4, 58), rs.randint(4, 19)
        r_ = rs.randint(2, 3)
        for dy in range(-r_, r_ + 1):
            for dx in range(-r_, r_ + 1):
                if dx * dx + dy * dy <= r_ * r_ and 3 <= x + dx <= 60 and 3 <= y + dy <= 21:
                    c = H('#5a7e54') if dx + dy < -1 else H('#3e5e40') if dx + dy < 2 else H('#2a4230')
                    b.px(x + dx, y + dy, c)
    b.r(3, 20, 60, 21, H('#1e3024'))
    b.r(0, 24, 63, 31, H('#7a7488'))                          # Steinfront
    b.r(0, 24, 63, 24, H('#9a94aa'))
    for x in range(0, 64, 16):
        b.r(x, 25, x, 31, H('#5e5872'))
    b.umriss()
    return b


def poller():
    b = Bild(8, 14)
    b.kasten(1, 2, 6, 13, H('#8a8e9a'), H('#c4c8d2'), H('#4a4e5c'))
    b.r(1, 0, 6, 1, H('#b0b4be'))
    b.r(1, 5, 6, 6, H('#e0c040'))
    b.umriss()
    return b


def ginkgo(quelle, name):
    """Ginkgo im Herbst: Krone eines vorhandenen Baums (Karte 01/10) nach Helligkeit auf eine goldgelbe Rampe
    umgefaerbt, Stamm und Umriss bleiben (Wiederverwenden zuerst, Regel 3)."""
    im = np.array(Image.open(os.path.join(ROOT, 'assets', 'objekte', quelle + '.png')).convert('RGBA')).astype(int)
    r_, g_, b_, a_ = im[..., 0], im[..., 1], im[..., 2], im[..., 3]
    gruen = (a_ > 0) & (g_ > r_ + 8) & (g_ > b_ + 8)
    kontur = (a_ > 0) & ~gruen & (0.3 * r_ + 0.59 * g_ + 0.11 * b_ < 60) & ~(r_ > g_ + 10)   # dunkle Kontur -> dunkles Braun
    lum = (0.3 * r_ + 0.59 * g_ + 0.11 * b_)
    rampe = np.array([[96, 62, 22], [150, 98, 26], [196, 140, 34], [226, 178, 52], [244, 210, 96], [252, 236, 156]])
    t = np.clip((lum - lum[gruen].min()) / max(1, np.ptp(lum[gruen])), 0, 0.999) if gruen.any() else lum * 0
    idx = (t * len(rampe)).astype(int)
    out = im.copy()
    out[gruen, :3] = rampe[idx[gruen]]
    out[kontur, :3] = [58, 36, 14]
    os.makedirs(OUT, exist_ok=True)
    Image.fromarray(out.astype(np.uint8)).save(os.path.join(OUT, name + '.png'))


def main():
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    os.makedirs(OUT, exist_ok=True)
    teile = []
    for (x0, y0, x1, y1, art) in lay['gebaeude']:
        w, h = (x1 - x0 + 1) * T, (y1 - y0 + 1) * T
        rs = random.Random(hash(art) % 1000 + 18)
        if art == 'laeden':
            b = ladenzeile(w, h, rs)
        elif art == 'buero_oben':
            b = buero(w, h, rs, tuer_x=(73 - 62) * T - 16)
        elif art == 'buero_mitte':
            b = buero(w, h, rs, glas=('#2c3c56', '#40567a', '#6a86ae'), wand='#4a5060', tuer_x=(51 - 42) * T - 16,
                      stockwerke=3)
        elif art == 'wohnblock':
            b = wohnblock(w, h, rs)
        elif art == 'lager_rolltor':
            b = lager(w, h, rs, 'rolltor')
        elif art == 'lager_shed':
            b = lager(w, h, rs, 'shed')
        elif art == 'halle':
            b = halle(w, h, rs)
        b.save(art)
        teile.append((art, Image.fromarray(b.a)))
    for name, fn in (('pfeiler', pfeiler), ('poller', poller), ('zug', zug), ('kuebel', kuebel)):
        b = fn(); b.save(name); teile.append((name, Image.fromarray(b.a)))
    for q, n in (('karte01/baeume/00', 'ginkgo'), ('karte10/baeume/01', 'ginkgo_gross'), ('karte01/baeume/03', 'ginkgo_klein')):
        ginkgo(q, n)
        teile.append((n, Image.open(os.path.join(OUT, n + '.png'))))
    W = max(im.width for _, im in teile)
    Hs = sum(im.height + 8 for _, im in teile)
    sheet = Image.new('RGBA', (W, Hs), (90, 96, 110, 255))
    y = 0
    for _, im in teile:
        sheet.alpha_composite(im, (0, y)); y += im.height + 8
    sheet.save(os.path.join(OUT, 'uebersicht.png'))
    print('Gebaeude ->', OUT, [a for a, _ in teile])


if __name__ == '__main__':
    main()
