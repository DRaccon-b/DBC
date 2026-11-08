"""Gebaeude fuer Karte 18 (The Fog-Bound City) - prozedural am 16x16-Raster, frontal mit sichtbarem Dach.

  python3 tools/karte18_gebaeude.py   ->  assets/objekte/karte18/gebaeude/<art>.png, uebersicht.png

Jedes Gebaeude fuellt genau sein Rechteck aus layout.json ('gebaeude'): oben die Dachflaeche von leicht oben (Attika
mit Lichtkante, Dachaufbauten), darunter die Suedfassade, unten der Sockel. Tueren liegen auf ganzen Kacheln und zeigen
zum Gehweg. Licht von oben links: linke/obere Kanten hell, rechte/untere dunkel; Umriss in der dunkelsten Farbe.
Abendstimmung: einzelne Fenster sind warm erleuchtet (echte Lichtquelle -> 'fensterlicht'), Reklame leuchtet.
Anspielung bei der Messehalle nur ueber die Form (zwei umgedrehte Pyramiden), kein Nachbau.
"""
import json, math, os, random, zlib
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


def dach(b, x0, x1, y0, y1, c, rs, aufbauten=True, schraeg=0, frei=None):
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
        if frei and x + 12 >= frei[0] and x <= frei[1]:         # Platz fuer einen grossen Dachaufbau freihalten
            x = frei[1] + 4
            continue
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
LICHT = {}                                                  # art -> [[x0, y0, x1, y1, phase], ...] echte Lichtquellen
LADEN = [   # Wand, Markise (2 Farben), Schildband, Art - 10 schmale Laeden je 4 Kacheln (wie die Vorlage)
    ('#e4e2dc', ('#c84a44', '#f0ece4'), '#e070a0', 'konbini'),
    ('#d6cfc0', ('#4a7a4a', '#d8e4c8'), '#3a6a3a', 'apotheke'),
    ('#b8b4ae', None, None, 'zu'),
    ('#e8d8d0', ('#e07a9a', '#f6e0e8'), '#e070a0', 'cafe'),
    ('#b8b2a8', ('#8a2a2a', '#c04040'), '#d8b040', 'ramen'),
    ('#c8c4c0', ('#2a3a5a', '#5a7ab0'), '#f0f0f0', 'buch'),
    ('#aeaaa4', None, None, 'zu'),
    ('#d8d4c8', ('#e08a3a', '#f6d0a0'), '#3a8ac0', 'baeckerei'),
    ('#e0dcd4', ('#3a6aa0', '#f0f0f0'), '#e070a0', 'konbini2'),
    ('#d4ccc4', ('#8a2a2a', '#d8b040'), '#c84a44', 'izakaya'),
]


def ladenzeile(w, h, rs):
    """Ladenzeile x 4..45: Endstuecke (je 1 Kachel) und 10 Laeden zu je 4 Kacheln; zwei mit heruntergelassenem
    Rollladen. Tuer je Laden auf einer ganzen Kachel (gerade Laeden 3. Kachel, ungerade 2. Kachel)."""
    b = Bild(w, h)
    licht = []
    for (ex0, ex1) in ((0, 15), (w - 16, w - 1)):                 # Endstuecke: schmale Brandwand mit Fallrohr
        dach(b, ex0, ex1, 0, 14, (H('#8a8e9c'), H('#6e7280'), H('#4e5260')), rs, aufbauten=False)
        b.r(ex0, 15, ex1, h - 1, H('#9a968e'))
        b.r(ex0 + 7, 15, ex0 + 8, h - 4, H('#5a5e6a'))
        sockel(b, h - 3, ex0, ex1)
    for i in range(10):
        x0, x1 = 16 + i * 64, 16 + i * 64 + 63
        wand, mark, schild, art = LADEN[i]
        wand = H(wand)
        hd = 14 + (4 if i % 3 == 1 else 0)
        dach(b, x0, x1, 0, hd, (H('#8a8e9c'), H('#6e7280'), H('#4e5260')), rs)
        if art != 'zu' and i % 3 == 0:                           # Dachschild (leuchtet)
            b.kasten(x0 + 16, 3, x0 + 47, hd - 3, H(schild), H('#ffffff'), H('#3a3a44'))
            for k in range(3):
                b.r(x0 + 21 + k * 8, 6, x0 + 25 + k * 8, hd - 6, H('#ffffff') if schild != '#f0f0f0' else H('#3a4a6a'))
            licht.append([x0 + 16, 3, x0 + 47, hd - 3, i])
        y = hd + 1
        b.r(x0, y, x1, h - 1, wand)
        b.r(x0, y, x1, y + 1, (wand.astype(int) + 14).clip(0, 255).astype(np.uint8))
        b.r(x1 - 1, y, x1, h - 1, (wand.astype(int) * 0.8).astype(np.uint8) | np.array([0, 0, 0, 255], np.uint8))
        fenster(b, x0 + 8, y + 6, 18, 16, rs, licht=0.15 if art == 'zu' else 0.45)
        fenster(b, x0 + 38, y + 6, 18, 16, rs, licht=0.15 if art == 'zu' else 0.45)
        if i % 4 == 1:
            b.r(x0 + 4, y + 24, x0 + 59, y + 24, H('#5a5e6a'))
            for gx in range(x0 + 4, x0 + 60, 4):
                b.r(gx, y + 18, gx, y + 24, H('#5a5e6a'))
        ys = y + 30
        if art == 'zu':                                          # geschlossener Laden: Rollladen ueber das ganze Erdgeschoss
            b.r(x0 + 4, ys, x1 - 4, h - 4, H('#7a7e88'))
            for yy in range(ys, h - 4, 3):
                b.r(x0 + 4, yy, x1 - 4, yy, H('#5e626c'))
            b.r(x0 + 4, ys, x1 - 4, ys, H('#a4a8b2'))
            b.r(x0 + 28, h - 8, x0 + 35, h - 6, H('#3a3e48'))     # Griff/Schloss
            sockel(b, h - 3, x0, x1)
            b.r(x1, hd + 1, x1, h - 1, H('#3a3c48'))
            continue
        b.r(x0 + 2, ys, x1 - 2, ys + 7, H(schild))               # Schildband (leuchtet)
        b.r(x0 + 2, ys, x1 - 2, ys, (H(schild).astype(int) + 40).clip(0, 255).astype(np.uint8))
        for k in range(4):
            b.r(x0 + 10 + k * 12, ys + 2, x0 + 16 + k * 12, ys + 5, H('#ffffff') if schild not in ('#f0f0f0', '#d8b040') else H('#2a2a34'))
        licht.append([x0 + 2, ys, x1 - 2, ys + 7, i + 1])
        m1, m2 = mark
        ym = ys + 8
        for x in range(x0 + 2, x1 - 1):                          # Markise gestreift mit Volant
            for d in range(7):
                c = H(m1) if ((x - x0) // 6) % 2 == 0 else H(m2)
                if d >= 5:
                    c = (c.astype(int) * 0.78).astype(np.uint8) | np.array([0, 0, 0, 255], np.uint8)
                b.px(x, ym + d, c)
            if ((x - x0) // 6) % 2 == 0:
                b.px(x, ym + 7, H(m1))
        ye = ym + 9
        tx = x0 + (32 if i % 2 == 0 else 16)
        b.r(x0 + 4, ye, x1 - 4, h - 4, H('#3a3e4a'))
        for (sx0, sx1) in ((x0 + 6, tx - 4), (tx + 20, x1 - 6)):
            if sx1 - sx0 < 8:
                continue
            b.r(sx0, ye + 2, sx1, h - 6, rs.choice(WARM))
            b.r(sx0, ye + 2, sx1, ye + 2, H('#fff0c0'))
            for k in range(sx0 + 3, sx1 - 2, 7):
                b.r(k, h - 11, k + 3, h - 7, rs.choice((H('#c04a44'), H('#4a7a4a'), H('#3a6aa0'), H('#e8c040'))))
            b.r(sx0, h - 6, sx1, h - 6, H('#8a8e9a'))
        if art in ('ramen', 'izakaya'):                           # Noren und rote Papierlaternen (leuchten)
            b.r(tx, ye, tx + 15, ye + 8, H('#2a3a5a'))
            for k in range(tx, tx + 16, 4):
                b.r(k, ye, k, ye + 8, H('#1a2440'))
            for lx in (x0 + 6, x0 + 52):
                b.kasten(lx, ye - 2, lx + 5, ye + 6, H('#d04030'), H('#f07050'), H('#802020'))
                licht.append([lx, ye - 2, lx + 5, ye + 6, i + 2])
        tuer(b, tx, h - 4, 16, 22, glas=art not in ('ramen', 'izakaya'))
        if art == 'apotheke':
            b.r(x0 + 50, ys - 12, x0 + 58, ys - 4, H('#3a8a4a'))
            b.r(x0 + 53, ys - 11, x0 + 55, ys - 5, H('#ffffff')); b.r(x0 + 51, ys - 9, x0 + 57, ys - 7, H('#ffffff'))
            licht.append([x0 + 50, ys - 12, x0 + 58, ys - 4, i + 3])
        sockel(b, h - 3, x0, x1)
        b.r(x1, hd + 1, x1, h - 1, H('#3a3c48'))
    b.umriss()
    LICHT['laeden'] = licht
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
        b.r(8, ys, w - 9, ys + hoehe - 9, g0)                  # Fensterband: nur volle 15-px-Scheiben, 8 px Rand
        for x in range(8, w - 7, 16):
            b.r(x, ys, x, ys + hoehe - 9, H('#7a8294'))         # Pfosten
        for x in range(9, w - 8, 16):                          # Reflexe / Licht
            if rs.random() < 0.25:
                b.r(x, ys + 1, x + 14, ys + hoehe - 10, rs.choice(WARM))
            else:
                b.r(x, ys + 1, x + 6, ys + 2, g2)
                b.px(x, ys + 3, g1)
        b.r(8, ys + hoehe - 8, w - 9, ys + hoehe - 8, H('#8a8e9c'))   # Bruestung Licht
        b.r(8, ys + hoehe - 7, w - 9, ys + hoehe - 5, H(wand))
    # Erdgeschoss: Glasfront, Vordach, Tuer (2 Kacheln) auf dem Raster
    ye = h - eg
    b.r(8, ye + 6, w - 9, h - 5, g0)
    for x in range(8, w - 7, 16):
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
    tx = 144                                                    # Treppenhaus x 14-15 (wie Vorlage)
    dach(b, 0, w - 1, 0, dh, (H('#8a8478'), H('#6e685e'), H('#4e4a44')), rs, frei=(tx - 8, tx + 39))
    b.kasten(tx - 4, 3, tx + 35, dh - 5, H('#a49e94'), H('#c8c2b8'), H('#6a645c'))   # Dachaufbau ueber dem Treppenhaus
    b.r(tx + 12, 8, tx + 19, dh - 5, H('#3a3a40'))
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
            if ux < tx + 32 and ux + 64 > tx:                    # Einheit am Treppenhaus auslassen (keine Anschnitte)
                continue
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
    # Treppenhaus (wie Vorlage) als helles senkrechtes Band x 14-15, schmale Querfenster je Geschoss, Eingang unten
    b.r(tx, y, tx + 31, h - 4, H('#c4c2bc'))
    b.r(tx, y, tx + 31, y + 1, H('#dcdad4'))
    b.r(tx, y, tx, h - 4, H('#dcdad4')); b.r(tx + 31, y, tx + 31, h - 4, H('#8a8884'))
    for s_ in range(stock - 1):
        ys = y + 3 + s_ * hs
        fenster(b, tx + 6, ys + 10, 20, 6, rs, licht=0.6, sprosse=False)
    b.kasten(tx - 4, h - 34, tx + 35, h - 30, H('#8a8e98'), H('#b8bcc6'), H('#4a4e58'))
    tuer(b, tx, h - 4, 15, 24, glas=True)
    tuer(b, tx + 16, h - 4, 15, 24, glas=True)
    sockel(b, h - 3, 0, w - 1, H('#6a6660'))
    for (kx0, kx1) in ((8, tx - 6), (tx + 38, w - 8)):        # Pflanzkaesten am Sockel links/rechts des Eingangs
        b.r(kx0, h - 9, kx1, h - 1, H('#8a8e98'))
        b.r(kx0, h - 9, kx1, h - 9, H('#b4b8c2'))
        for x in range(kx0 + 1, kx1):
            for yy in range(h - 13, h - 8):
                if (x * 7 + yy * 3) % 5 < 3 and rs.random() < 0.85:
                    b.px(x, yy, H('#4a6a48') if yy < h - 11 else H('#2e4632'))
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
    LICHT['lager_' + art] = [[tuer_x + 4, h - 38, tuer_x + 10, h - 34, 1]]
    sockel(b, h - 3, 0, w - 1)
    b.umriss()
    return b


# ---------------------------------------------------------------------------------------------- Messehalle
def halle(w, h, rs):
    """Messehalle (Rechteck x 84..119, y 4..27): Glasfassade unten (8 Kacheln), Dach darueber, zwei umgedrehte
    Pyramiden auf Kernen, exakt spiegelsymmetrisch zur Achse (w/2)."""
    b = Bild(w, h)
    mx = w // 2
    dach_y0, fass_y0 = 144, 256                              # Dach ab Reihe 13 (wie Vorlage), Fassade ab Reihe 20
    # Dach der Halle (leicht von oben): Seitenkanten als durchgehende Schraege (oben 12 px eingerueckt, unten buendig),
    # Attika mit Lichtkante oben/links, Dachplatten, drei Luefter; alles spiegelsymmetrisch zur Achse mx
    dy_ = fass_y0 - 11 - dach_y0
    for y in range(dach_y0, fass_y0 - 11):
        ein = int(round(12 * (1 - (y - dach_y0) / dy_)))
        b.r(ein, y, w - 1 - ein, y, H('#9aa0ae'))
        b.r(ein, y, ein + 2, y, H('#b4b8c4'))                  # linke Schraege im Licht
        b.r(w - 3 - ein, y, w - 1 - ein, y, H('#6a6e7c'))      # rechte Schraege im Schatten
        if y >= dach_y0 + 6 and y <= fass_y0 - 13:
            b.r(ein + 6, y, w - 7 - ein, y, H('#868a98'))
    b.r(12, dach_y0, w - 13, dach_y0 + 2, H('#c4c8d4'))
    for x in range(18, w - 18):                                # Dachbahnen (Fugen alle 32 px, symmetrisch)
        if (x - mx) % 32 == 0:
            b.r(x, dach_y0 + 7, x, fass_y0 - 13, H('#7a7e8c'))
    for y in range(dach_y0 + 8, fass_y0 - 13, 16):             # Dachplatten in Draufsicht
        ein = int(round(12 * (1 - (y - dach_y0) / dy_)))
        b.r(ein + 6, y, w - 7 - ein, y, H('#7a7e8c'))
    for (cx_, cy_) in ((72, dach_y0 + 14), (mx, dach_y0 + 14), (w - 72, dach_y0 + 14)):   # Dachluefter, symmetrisch
        b.kasten(cx_ - 8, cy_, cx_ + 7, cy_ + 9, H('#9aa0ac'), H('#c4c8d2'), H('#5a5e6a'))
        b.r(cx_ - 5, cy_ + 3, cx_ + 4, cy_ + 6, H('#4a4e5a'))
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
    for x in range(mx % 16, w - 1, 16):                        # Spiegelungen statt Einzellicht (eine hohe Halle),
        for y in range(fass_y0 + 1, h - 8, 24):                 # an der Achse gespiegelt
            idx = ((x - mx) // 16)
            b.r(x + 1, y, x + 15, y + 10, H('#34466c'))
            if idx % 2 == 0:
                for k in range(8):
                    for xx_ in (x + 3 + k, x + 6 + k):
                        yy_ = y + 20 - k * 2
                        if fass_y0 <= yy_ < h - 4:
                            xx2 = xx_ if x >= mx else 2 * mx - 1 - (2 * mx - 1 - xx_)
                            b.px(xx2, yy_, H('#6a86b8') if xx_ == x + 3 + k else H('#4e6894'))
    b.r(0, fass_y0 + 2, w - 1, fass_y0 + 4, H('#e8c070'))         # durchgehendes warmes Lichtband oben in der Halle
    b.r(0, fass_y0 + 5, w - 1, fass_y0 + 5, H('#c8904a'))
    for k in range(-4, 5):                                     # Pfeiler
        px_ = mx + k * 64
        if 0 < px_ < w:
            b.kasten(px_ - 6, fass_y0, px_ + 5, h - 4, H('#b8bcc8'), H('#dcdfe8'), H('#6e7280'))
    b.kasten(0, fass_y0, 9, h - 4, H('#b8bcc8'), H('#dcdfe8'), H('#6e7280'))
    b.kasten(w - 10, fass_y0, w - 1, h - 4, H('#b8bcc8'), H('#dcdfe8'), H('#6e7280'))
    # Eingang mittig (8 Kacheln = Mittelweg), Vordach, Glastueren
    ex0, ex1 = mx - 64, mx + 63
    b.kasten(ex0 - 6, h - 58, ex1 + 6, h - 50, H('#c8ccd6'), H('#eef0f6'), H('#6a6e7c'))
    b.r(ex0 - 4, h - 49, ex1 + 4, h - 46, H('#2a2c36'))
    for tx in range(ex0, ex1, 16):
        tuer(b, tx + 1, h - 4, 14, 40, glas=True)
    sockel(b, h - 3, 0, w - 1, H('#6a6e7c'))
    # Pyramiden: oben breit (224), unten schmal (96), Hoehe 150; Deckflaeche 14 px von oben sichtbar
    for cx in (mx - 128, mx + 128):                            # Pyramiden: oberer Block, Gesimsplatte, Trichter
        top, ob, ub = 4, 112, 44
        ky0 = 202                                                  # Unterkante des Trichters (Reihe 16,6)
        ku = fass_y0 - 12                                          # Saeulen reichen bis aufs Fassadengesims
        b.r(cx - 25, ky0, cx + 24, ku, H('#1e2434'))                # dunkle Oeffnung zwischen den Saeulen
        b.r(cx - 25, ky0, cx + 24, ky0 + 3, H('#141824'))
        for gx in (cx - 9, cx + 8):                                # schlanke Pfosten in der Oeffnung
            b.r(gx, ky0 + 4, gx, ku, H('#3a4256'))
        for (kx0, kx1) in ((cx - 40, cx - 26), (cx + 25, cx + 39)):      # zwei Saeulen (Stuetzen) bis zum Gesims
            b.kasten(kx0, ky0 - 4, kx1, ku, H('#a8acb8'), H('#ccd0da'), H('#62667a'))
            b.r(kx0 + 3, ky0, kx0 + 3, ku - 2, H('#bcc0cc'))
        for y in range(top, top + 18):                                     # Deckflaeche von oben
            einzug = (top + 18 - y) // 4
            for x in range(cx - ob + einzug, cx + ob - einzug):
                c = H('#ccd0da') if (y - top) < 15 else H('#e6e8ee')
                if (x - cx) % 32 == 0 or (y - top) % 6 == 0:
                    c = H('#aeb2be')
                b.px(x, y, c)
        for y in range(top + 18, 64):                                      # oberer Block: fast gerade
            t = (y - top - 18) / (64 - top - 18)
            halb = int(round(ob - 8 * t))
            for x in range(cx - halb, cx + halb):
                c = H('#b4b8c4') if (x - (cx - halb)) / (2 * halb) < 0.55 else H('#8e92a0')
                if (y - top) % 12 == 0 or abs(x - cx) % 32 == 0:
                    c = (c.astype(int) * 0.86).astype(np.uint8) | np.array([0, 0, 0, 255], np.uint8)
                b.px(x, y, c)
            b.px(cx - halb, y, H('#d8dce4')); b.px(cx + halb - 1, y, H('#5a5e6c'))
        b.r(cx - ob, 64, cx + ob - 1, 70, H('#c8ccd6'))                     # Gesimsplatte, 8 px ueber den Block
        b.r(cx - ob, 64, cx + ob - 1, 64, H('#e6e8ee'))                     # hinaus; zwischen den Pyramiden frei
        b.r(cx - ob, 71, cx + ob - 1, 72, H('#5a5e6c'))
        for y in range(73, ky0):                                           # Trichter nach unten
            t = (y - 73) / (ky0 - 73)
            halb = int(round((ob - 8) + (ub - (ob - 8)) * t))
            for x in range(cx - halb, cx + halb):
                c = H('#b4b8c4') if (x - (cx - halb)) / (2 * halb) < 0.55 else H('#8e92a0')
                if (y - 73) % 16 == 0 or abs(x - cx) % 32 == 0:
                    c = (c.astype(int) * 0.86).astype(np.uint8) | np.array([0, 0, 0, 255], np.uint8)
                b.px(x, y, c)
            b.px(cx - halb, y, H('#d8dce4')); b.px(cx + halb - 1, y, H('#5a5e6c'))
        b.r(cx - ub, ky0 - 2, cx + ub - 1, ky0 - 1, H('#5a5e6c'))
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
    w, h = wagen * laenge + 2, 36
    b = Bild(w, h)
    for i in range(wagen):
        x0, x1 = i * laenge + 1, (i + 1) * laenge - 2
        nase = (i == wagen - 1)
        for y in range(2, 34):
            xe = x1
            if nase:                                          # Nase: Rundung nach vorn
                einzug = int(round(12 * (1 - math.sqrt(max(0.0, 1 - ((y - 19) / 17.0) ** 2)))))
                xe = x1 - einzug
            for x in range(x0, xe + 1):
                c = H('#e8eaf0')
                if y < 5:
                    c = H('#f6f8fc')                          # Dach (Licht)
                elif 9 <= y <= 19:
                    c = H('#24345a')                          # Fensterband (11 px)
                elif y == 20:
                    c = H('#3a5aa0')
                elif y >= 28:
                    c = H('#9aa0b0') if y < 31 else H('#5a6070')   # Schuerze
                b.px(x, y, c)
        for fx in range(x0 + 6, x1 - 12, 14):                 # Fenster
            if nase and fx > x1 - 28:
                continue
            b.r(fx, 10, fx + 9, 18, H('#5a78b0'))
            b.r(fx, 10, fx + 3, 10, H('#a8c0e8'))
        for tx in (x0 + 24, x0 + 80):                          # Tueren
            b.r(tx, 8, tx + 9, 27, H('#c8ccd6'))
            b.r(tx + 4, 8, tx + 5, 27, H('#8a90a0'))
            b.r(tx + 1, 10, tx + 3, 18, H('#3a4a70')); b.r(tx + 6, 10, tx + 8, 18, H('#3a4a70'))
        if nase:
            b.r(x1 - 20, 9, x1 - 7, 19, H('#1a2440'))         # Frontscheibe
            b.r(x1 - 20, 9, x1 - 15, 9, H('#7a9ad0'))
            b.r(x1 - 6, 23, x1 - 4, 24, H('#fff0b0'))         # Scheinwerfer
        if i < wagen - 1:
            b.r(x1 + 1, 14, x1 + 3, 28, H('#3a3e4c'))         # Kupplung / Faltenbalg
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


def pfeiler_wasser():
    """Pfeiler im Kanal: ohne Zierplinthe, der Schaft laeuft gerade ins Wasser; unten nass und dunkler."""
    b = pfeiler()
    b.a[72:80] = 0
    for y in range(72, 80):
        for x in range(6, 26):
            t = (x - 6) / 20
            c = H('#8a8e9a') if t < 0.3 else H('#72768a') if t < 0.65 else H('#5a5e6c')
            if y >= 76:
                c = (c.astype(int) * 0.7).astype(np.uint8) | np.array([0, 0, 0, 255], np.uint8)
            b.px(x, y, c)
    b.umriss()
    return b


def doppellaterne():
    """Zweiarmige Strassenleuchte fuer die Mittelstreifen: T-Mast mit Querarm, an beiden Enden ein Leuchtenkopf der
    Karte-02-Laterne (Wiederverwendung), frontal und symmetrisch."""
    lat = np.array(Image.open(os.path.join(ROOT, 'assets', 'objekte', 'karte02', 'abgeleitet', 'laterne.png')).convert('RGBA'))
    al = lat[..., 3] > 0
    zeilen = np.nonzero(al.any(axis=1))[0]
    kopf = lat[zeilen.min():zeilen.min() + 16]
    kw = kopf.shape[1]
    w, h = 40, 60
    b = Bild(w, h)
    for y in range(12, h - 3):                                 # Mast
        b.r(19, y, 20, y, H('#4a4e5a')); b.px(19, y, H('#6a6e7c'))
    b.r(6, 14, 33, 15, H('#4a4e5a')); b.r(6, 14, 33, 14, H('#6a6e7c'))   # Querarm
    b.kasten(15, h - 4, 24, h - 1, H('#4a4e5a'), H('#6a6e7c'), H('#2a2c36'))
    for kx in (6 - kw // 2, 33 - kw // 2):
        sub = b.a[0:16, max(0, kx):kx + kw]
        k = kopf[:, max(0, -kx):max(0, -kx) + sub.shape[1]]
        m = k[..., 3] > 0
        sub[m] = k[m]
    b.umriss()
    return b


def koban_mit_dach():
    """Kleine Polizeiwache (PixelLab-Sprite) mit sichtbarer Dachflaeche von leicht oben: flaches Dach mit Attika
    (Lichtkante oben/links) ueber die Fassade gesetzt, Sprite eine Kachel hoeher, Fuss unveraendert."""
    p = os.path.join(ROOT, 'assets', 'objekte', 'karte18', 'frontal', '08.png')
    if not os.path.exists(p):
        return None
    sp = np.array(Image.open(p).convert('RGBA'))
    al = sp[..., 3] > 0
    xs = np.nonzero(al.any(axis=0))[0]
    w, h = sp.shape[1], sp.shape[0] + 12
    b = Bild(w, h)
    b.a[12:] = sp
    x0, x1 = xs.min(), xs.max()
    b.r(x0, 2, x1, 13, H('#6a6e7c'))
    b.r(x0, 2, x1, 3, H('#a4a8b4')); b.r(x0, 2, x0 + 1, 13, H('#8e92a0'))
    b.r(x1 - 1, 2, x1, 13, H('#4a4e5a'))
    b.r(x0 + 4, 5, x1 - 4, 12, H('#5a5e6c'))
    b.kasten(x0 + 8, 6, x0 + 17, 10, H('#9aa0ac'), H('#c4c8d2'), H('#4a4e5a'))
    b.umriss()
    LICHT['koban'] = [[x0 + 6, 27, x0 + 11, 31, 0], [x1 - 11, 27, x1 - 7, 31, 2]]   # nur die roten Lampen
    return b


def bus():
    """Stadtbus als reiner Seitenaufriss (Front nach rechts = Osten), 128x34: weiss mit gruenem Band, Fensterreihe,
    senkrechte Frontscheibe mit Zielanzeige, zwei Raeder; Einstieg auf der (nicht sichtbaren) linken Seite."""
    w, h = 128, 34
    b = Bild(w, h)
    b.r(1, 2, w - 2, 27, H('#e4e6ec'))
    b.r(1, 2, w - 2, 3, H('#f6f8fc'))
    b.r(1, 20, w - 2, 23, H('#3e7a4a'))                       # gruenes Band
    b.r(1, 24, w - 2, 27, H('#9aa0ae'))
    for fx in range(6, w - 24, 12):
        b.r(fx, 7, fx + 9, 16, H('#2a3a5a')); b.r(fx, 7, fx + 3, 7, H('#6a86b8'))
    b.r(w - 18, 5, w - 4, 18, H('#1a2440'))                  # Frontscheibe
    b.r(w - 17, 3, w - 5, 5, H('#f0c060'))                   # Zielanzeige (leuchtet)
    b.r(w - 4, 21, w - 3, 23, H('#fff0b0'))                  # Scheinwerfer
    b.r(2, 21, 3, 23, H('#c04040'))                          # Ruecklicht
    for wx in (22, w - 30):                                   # Raeder
        b.r(wx - 2, 24, wx + 13, 27, H('#2a2c36'))
        for dy in range(9):
            for dx in range(11):
                if (dx - 5) ** 2 + (dy - 4) ** 2 <= 20:
                    b.px(wx + dx, 25 + dy, H('#1c1e26') if (dx - 5) ** 2 + (dy - 4) ** 2 > 6 else H('#8a8e9a'))
    b.umriss()
    LICHT['bus'] = [[w - 17, 3, w - 5, 5, 0]]
    return b


def lkw():
    """Kastenwagen als reiner Seitenaufriss, 80x46: Fuehrerhaus links (Westen), Kofferaufbau rechts, Raeder."""
    w, h = 80, 46
    b = Bild(w, h)
    b.kasten(26, 2, w - 2, 34, H('#d8d4cc'), H('#f0ece4'), H('#8a8680'))   # Koffer
    for x in range(30, w - 4, 12):
        b.r(x, 4, x, 32, H('#b8b4ac'))
    b.r(30, 14, w - 6, 20, H('#3a6aa0'))                      # Firmenstreifen
    b.kasten(2, 12, 25, 36, H('#c84a44'), H('#e07060'), H('#7a2a26'))       # Fuehrerhaus
    b.r(4, 14, 16, 22, H('#2a3a5a')); b.r(4, 14, 8, 14, H('#6a86b8'))
    b.r(2, 30, 4, 32, H('#fff0b0'))
    b.r(2, 34, w - 2, 37, H('#3a3c48'))
    for wx in (6, 52):
        for dy in range(10):
            for dx in range(12):
                if (dx - 5.5) ** 2 + (dy - 4.5) ** 2 <= 25:
                    b.px(wx + dx, 35 + dy, H('#1c1e26') if (dx - 5.5) ** 2 + (dy - 4.5) ** 2 > 7 else H('#8a8e9a'))
    b.umriss()
    return b


def kletterkuppel():
    """Klettergeruest-Kuppel (Spielplatz): Halbkugel aus gedaempft roten/blauen Stangen, frontal, 44x26."""
    w, h = 44, 26
    b = Bild(w, h)
    cx, cy, r = 22, 24, 20
    for y in range(h):
        for x in range(w):
            d = math.hypot((x - cx) / r, (y - cy) / (r * 1.05))
            if d <= 1 and y <= cy:
                ring = abs(d - 1) < 0.06 or abs(d - 0.66) < 0.06 or abs(d - 0.33) < 0.08
                speiche = abs(math.atan2(cy - y, x - cx) % (math.pi / 4)) < 0.07
                if ring or speiche:
                    b.px(x, y, H('#a8605a') if (x + y) % 2 else H('#6a84b0'))
    b.r(0, 24, w - 1, 25, H('#4a4e5a'))
    b.umriss()
    return b


def feuerschale():
    """Feuerschale fuer das Notlager: Metallschale auf drei Beinen, Glut; die Flammen zeichnet die Animation."""
    w, h = 22, 28
    b = Bild(w, h)
    for y in range(12, 18):
        einzug = (y - 12) // 2
        b.r(2 + einzug, y, w - 3 - einzug, y, H('#5a5e6c') if y > 12 else H('#8a8e9a'))
    b.r(4, 12, w - 5, 12, H('#c8603a'))                       # Glut
    for lx in (5, 10, 16):
        b.r(lx, 18, lx, h - 1, H('#3a3c48'))
    b.umriss()
    return b


def banner_hoch():
    """Hohes senkrechtes Banner (Nobori-Art) fuer den Vorplatz der Halle: Mast 58 px, Querarm oben, Tuch 8x24 hellblau."""
    w, h = 14, 58
    b = Bild(w, h)
    b.r(2, 2, 3, h - 2, H('#6a6e7c')); b.r(2, 2, 2, h - 2, H('#9aa0ae'))
    b.r(2, 2, 12, 3, H('#6a6e7c'))
    b.r(5, 4, 12, 27, H('#8ab6e0'))
    b.r(5, 4, 12, 5, H('#c4dcf0'))
    for y in range(9, 25, 4):
        b.r(7, y, 10, y + 1, H('#3a5a8a'))
    b.r(0, h - 3, 5, h - 1, H('#4a4e5a'))
    b.umriss()
    return b


def container(name, basis, hell, dunkel, dach):
    """Schiffscontainer als reiner Seitenaufriss (frontal), 62x28 (4 Kacheln breit mit je 1 px Luft): Dach von leicht
    oben, Wellblech-Rippen (Licht links), Eckpfosten, Bodenrahmen mit Eckbeschlaegen."""
    w, h = 62, 28
    b = Bild(w, h)
    b.r(0, 0, w - 1, 3, H(dach)); b.r(0, 0, w - 1, 0, H('#d8dce4'))
    for x in range(0, w):
        c = (H(hell), H(basis), H(basis), H(dunkel))[x % 4]
        b.r(x, 4, x, 23, c)
    b.r(0, 4, w - 1, 5, H(dunkel))
    for (x0, x1) in ((0, 3), (w - 4, w - 1)):                  # Eckpfosten
        b.r(x0, 4, x1, 25, H(dunkel)); b.r(x0, 4, x0, 25, H(hell))
    b.r(0, 24, w - 1, 25, H('#3a3c48'))
    for x0 in (0, w - 6):
        b.r(x0, 26, x0 + 5, 27, H('#2a2c36'))                  # Eckbeschlaege als Fuesse
    b.r(8, 8, 15, 10, H('#d8d8dc')); b.r(8, 12, 12, 12, H('#d8d8dc'))   # Kennzeichnung
    b.umriss()
    return b


def zelt():
    """Dunkelblaues Spitzzelt (Pavillon) fuer das Notlager, frontal 64x44: Spitzdach (links im Licht), gewellte Blende,
    zwei Stangen links/rechts, Rueckwand aus Zeltstoff; darunter Kuehlbox und Truhe."""
    w, h = 64, 44
    b = Bild(w, h)
    for y in range(1, 17):                                     # Spitzdach
        halb = 2 + (y - 1) * 30 / 15.0
        x0, x1 = int(round(31.5 - halb)), int(round(31.5 + halb))
        b.r(x0, y, 31, y, H('#4a6a9e'))
        b.r(32, y, x1, y, H('#2e4878'))
        b.px(x0, y, H('#6a8abe'))
    for k in (1, 3):                                           # Naehte vom First zur Traufe
        for y in range(2, 17):
            t = (y - 1) / 15.0
            b.px(int(round(31.5 - t * 30 * k / 4)), y, H('#3a5888'))
            b.px(int(round(31.5 + t * 30 * k / 4)), y, H('#243a66'))
    b.r(0, 17, w - 1, 19, H('#3a5888')); b.r(0, 17, w - 1, 17, H('#5a7ab0'))
    for x in range(0, w, 8):                                   # gewellte Blende
        b.r(x + 2, 20, x + 5, 20, H('#3a5888'))
    b.r(5, 20, w - 6, h - 2, H('#1e2a44'))                    # Rueckwand (Zeltstoff im Schatten)
    for x in range(9, w - 8, 8):
        b.r(x, 21, x, h - 3, H('#26345a'))
    for px_ in (2, w - 5):                                     # Stangen
        b.r(px_, 18, px_ + 2, h - 1, H('#8a8e9a')); b.r(px_, 18, px_, h - 1, H('#c4c8d2'))
    b.kasten(10, 30, 26, h - 2, H('#c8d0dc'), H('#eef0f6'), H('#7a8496'))   # Kuehlbox
    b.r(10, 30, 26, 32, H('#3a6aa0')); b.r(16, 33, 20, 33, H('#5a6070'))
    b.kasten(35, 29, 54, h - 2, H('#7a5236'), H('#a07450'), H('#4a3222'))   # Truhe
    b.r(35, 33, 54, 33, H('#4a3222'))
    for x in (39, 50):
        b.r(x, 29, x + 1, h - 2, H('#4a3222'))
    b.r(44, 35, 45, 37, H('#c8b060'))
    b.r(0, h - 1, w - 1, h - 1, H('#2a2c36'))
    b.umriss()
    return b


def trinkbrunnen():
    """Trinkbrunnen (Spielplatz): Steinsaeule mit Becken und kleinem Hahn, frontal 12x24."""
    w, h = 12, 24
    b = Bild(w, h)
    b.kasten(1, 2, 10, 6, H('#9aa0ac'), H('#c4c8d2'), H('#5a5e6a'))
    b.r(3, 3, 8, 4, H('#4a6a9a')); b.r(3, 3, 5, 3, H('#8aaad0'))   # Wasser im Becken
    b.r(6, 0, 7, 1, H('#6a6e7c'))                              # Hahn
    b.kasten(3, 7, 8, h - 3, H('#8a8e9a'), H('#b0b4be'), H('#5a5e6a'))
    b.kasten(1, h - 3, 10, h - 1, H('#6a6e7c'), H('#8a8e9a'), H('#3a3e4a'))
    b.umriss()
    return b


def taube():
    """Stadttaube von der Seite, 10x8: grau, dunkle Fluegelbinden, schillernder Hals, rote Fuesse."""
    b = Bild(10, 8)
    b.r(2, 3, 7, 5, H('#8a8e9e')); b.r(3, 2, 6, 2, H('#9aa0b0'))
    b.r(7, 1, 8, 3, H('#9aa0b0')); b.px(8, 2, H('#1c1e2a')); b.px(9, 2, H('#c8b8a0'))
    b.px(7, 3, H('#5a8a7a')); b.px(6, 3, H('#7a5a8a'))
    b.r(3, 4, 5, 4, H('#5a5e6c')); b.r(0, 3, 1, 4, H('#5a5e6c'))
    b.px(4, 6, H('#c86a5a')); b.px(6, 6, H('#c86a5a'))
    b.umriss()
    b.px(4, 6, H('#c86a5a')); b.px(6, 6, H('#c86a5a'))
    return b


def stadtbaum(seed=7):
    """Stadtbaum wie in der Vorlage, frontal 48x58: luftige Krone aus vielen Blattbuescheln (Licht oben links, einzelne
    Luecken), darunter sichtbarer Stamm mit zwei Aesten und Wurzeln, die sich am Boden spreizen."""
    w, h = 56, 64
    rs = random.Random(seed)
    b = Bild(w, h)
    cx, fuss = 28, h - 2
    GR = [H(c) for c in ('#16280e', '#24441a', '#33601f', '#467e26', '#5e9a2e', '#7cb63a', '#9ccc4c')]
    BR = (H('#3a2616'), H('#5a3c22'), H('#7a5632'))
    # Wurzeln und Stamm
    for (dx, l) in ((-1, 6), (1, 6), (-1, 3), (1, 4)):
        for k in range(l):
            x = cx + dx * (2 + k)
            y = fuss - (1 if k < l // 2 else 0)
            b.px(x, y, BR[0] if k > l // 2 else BR[1])
    for y in range(34, fuss + 1):
        breite = 3 if y < fuss - 4 else 4
        for x in range(cx - breite // 2 - 1, cx + breite - breite // 2):
            t = (x - (cx - breite // 2 - 1)) / max(1, breite)
            b.px(x, y, BR[2] if t < 0.3 else BR[1] if t < 0.75 else BR[0])
    for (sx, sy, ex, ey) in ((cx, 46, cx - 11, 34), (cx, 43, cx + 10, 33), (cx, 39, cx - 1, 28)):   # Aeste
        n = max(abs(ex - sx), abs(ey - sy))
        for i in range(n + 1):
            x = int(round(sx + (ex - sx) * i / n)); y = int(round(sy + (ey - sy) * i / n))
            b.px(x, y, BR[1]); b.px(x + 1, y, BR[0])
    # Krone: viele kleine Bueschel in einer Ellipse um (cx, 21), rx 21, ry 19
    wert = np.full((h, w), -1.0)
    bueschel = []
    for _ in range(160):
        while True:
            px_, py_ = rs.uniform(-1, 1), rs.uniform(-1, 1)
            if px_ * px_ + py_ * py_ <= 1:
                break
        bueschel.append((24 + py_ * 18, cx + px_ * 22, rs.uniform(2.8, 4.6)))
    for (by_, bx_, r) in sorted(bueschel):                      # hintere (obere) Bueschel zuerst, vordere decken
        for y in range(int(by_ - r), int(by_ + r) + 1):
            for x in range(int(bx_ - r), int(bx_ + r) + 1):
                d = ((x - bx_) ** 2 + (y - by_) ** 2) / (r * r)
                if d <= 1 and 0 <= x < w and 0 <= y < h:
                    lokal = -((x - bx_) + (y - by_)) / r            # Licht oben links im Bueschel
                    glob = -((x - cx) / 24.0 + (y - 24) / 21.0)     # und auf der ganzen Krone
                    v = 3.4 + 1.6 * lokal + 1.0 * glob - 2.6 * d * d
                    wert[y, x] = max(0.0, v)
    krone = wert >= 0
    idx = np.clip(np.round(wert), 1, len(GR) - 1).astype(int)
    for y, x in zip(*np.nonzero(krone)):
        b.a[y, x] = GR[idx[y, x]]
    rand = krone & ~(np.roll(krone, 1, 0) & np.roll(krone, -1, 0) & np.roll(krone, 1, 1) & np.roll(krone, -1, 1))
    b.a[rand] = GR[0]
    stamm = (b.a[..., 3] > 0) & ~krone
    rand2 = stamm & ~(np.roll(stamm | krone, 1, 1) & np.roll(stamm | krone, -1, 1))
    b.a[rand2] = H('#22160c')
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
    rampe = np.array([[96, 62, 22], [150, 98, 26], [196, 140, 34], [226, 178, 52], [244, 210, 96]])
    lo, hi = np.percentile(lum[gruen], (2, 98)) if gruen.any() else (0, 1)
    t = np.clip((lum - lo) / max(1.0, hi - lo), 0, 0.999)
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
        rs = random.Random(zlib.crc32(art.encode()) % 1000 + 18)   # fest (hash() wechselt je Lauf)
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
    for name, fn in (('bus', bus), ('lkw', lkw), ('kletterkuppel', kletterkuppel), ('feuerschale', feuerschale),
                     ('banner_hoch', banner_hoch), ('pfeiler', pfeiler), ('pfeiler_wasser', pfeiler_wasser), ('poller', poller), ('zug', zug),
                     ('kuebel', kuebel), ('doppellaterne', doppellaterne), ('koban', koban_mit_dach), ('stadtbaum', stadtbaum),
                     ('stadtbaum2', lambda: stadtbaum(23)),
                     ('zelt', zelt), ('trinkbrunnen', trinkbrunnen), ('taube', taube),
                     ('container_rot', lambda: container('rot', '#8e4038', '#ac5a4c', '#5e2a26', '#b86e60')),
                     ('container_blau', lambda: container('blau', '#3a5a86', '#5274a2', '#24405e', '#6a88b0')),
                     ('container_blau2', lambda: container('blau2', '#3e6478', '#587e92', '#284656', '#7094a8'))):
        b = fn()
        if b is None:
            continue
        b.save(name); teile.append((name, Image.fromarray(b.a)))
    json.dump({k: [[int(v) for v in r] for r in l] for k, l in LICHT.items()}, open(os.path.join(OUT, 'lichter.json'), 'w'), indent=0)
    for q, n in (('karte18/gebaeude/stadtbaum', 'ginkgo_beet'), ('karte01/baeume/00', 'ginkgo'), ('karte10/baeume/01', 'ginkgo_gross'), ('karte01/baeume/03', 'ginkgo_klein')):
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
