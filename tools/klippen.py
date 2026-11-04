"""Handgezeichnete Klippenwaende (prozedurale Pixelart) fuer Karte 01.

Wird von karte_bauen.py aufgerufen: zeichne_klippen(img, plan, ...).
Stil: Schiefer-Saeulen unterschiedlicher Breite, Licht von oben links (helle linke Kante,
dunkle rechte Kante), Risse und Gesteinsschichten, vereinzelte leuchtende Cyan-Runen,
buschige ueberhaengende Graskante oben, Schlagschatten am Fuss. Keine Wiederholung,
beliebige Hoehe. Farben aus basis_kacheln.PAL (Gras) und palette_hq.json (Schiefer/Rune).
"""
import random
from PIL import Image, ImageDraw

T = 16
SCHIEFER = ['#24304a', '#33466a', '#465e88', '#5e78a2', '#7c95bb', '#a2b6d4', '#c8d6ea']
RUNE = ['#2fc7d8', '#7ff0f5', '#e6ffff']
GRAS = {'g0': '#2e7a4c', 'g1': '#45a052', 'g2': '#5fbb58', 'g3': '#78cc60', 'g4': '#93db70', 'g5': '#b6eb8a'}


def rgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5)) + (255,)


S = [rgb(c) for c in SCHIEFER]
R = [rgb(c) for c in RUNE]
G = {k: rgb(v) for k, v in GRAS.items()}

RUNEN = [  # 3x5-Glyphen
    ["x.x", "xxx", ".x.", ".x.", "x.x"],
    ["xx.", "x.x", "xx.", "x.x", "xx."],
    [".x.", "x.x", ".x.", "xxx", ".x."],
    ["x..", "xx.", "x.x", "xx.", "x.."],
]


def wand(breite, hoehe, rnd, rune_chance=0.12):
    """Wandflaeche breite x hoehe (ohne Graskante), RGBA."""
    im = Image.new('RGBA', (breite, hoehe), S[2])
    px = im.load()
    x = 0
    while x < breite:
        w = rnd.choice((5, 6, 6, 7, 7, 8, 9))
        w = min(w, breite - x)
        ton = rnd.choice((1, 2, 2, 2, 3, 3))          # Grundton der Saeule
        versatz = rnd.randint(0, hoehe)
        for yy in range(hoehe):
            # Saeule: oben etwas heller, unten dunkler (Licht von oben)
            stufe = max(1, ton + (1 if yy < hoehe * 0.2 else 0) - (1 if yy > hoehe * 0.6 else 0))
            for xx in range(x, x + w):
                if xx == x:
                    c = S[0]                           # Riss/Fuge links
                elif xx == x + 1:
                    c = S[min(5, stufe + 1)]           # Lichtkante
                elif xx == x + w - 1:
                    c = S[max(1, stufe - 1)]           # Schattenkante
                else:
                    c = S[stufe]
                px[xx, yy] = c
        # Gesteinsschichten: kurze waagerechte Fugen mit Lichtlinie darunter
        for _ in range(max(1, hoehe // 14)):
            yy = (versatz + rnd.randint(4, hoehe - 4)) % max(1, hoehe - 3) + 2
            for xx in range(x + 1, x + w - 1):
                px[xx, yy] = S[1]
                if yy + 1 < hoehe:
                    px[xx, yy + 1] = S[min(6, ton + 1)]
        # Rune
        if w >= 6 and hoehe > 18 and rnd.random() < rune_chance:
            g = rnd.choice(RUNEN)
            ry = rnd.randint(6, hoehe - 10)
            rx = x + (w - 3) // 2 + (1 if w % 2 == 0 else 0)
            for dy, zeile in enumerate(g):
                for dx, ch in enumerate(zeile):
                    if ch == 'x':
                        px[rx + dx, ry + dy] = R[2] if (dx + dy) % 3 == 0 else R[1]
                        # Glimmen links/rechts
                        for gx in (rx + dx - 1, rx + dx + 1):
                            if x < gx < x + w - 1 and px[gx, ry + dy] not in (R[1],):
                                px[gx, ry + dy] = R[0]
        x += w
    # Fuss: unterste 2 Zeilen dunkler
    for xx in range(breite):
        px[xx, hoehe - 1] = S[0]
        px[xx, hoehe - 2] = S[1] if px[xx, hoehe - 2] != S[0] else S[0]
    return im


def graskante(img, x0, x1, y, rnd):
    """Buschige, ueberhaengende Graskante entlang y (Unterkante der Wiese) von x0 bis x1."""
    px = img.load()
    W, H = img.size
    x = x0
    while x < x1:
        b = rnd.randint(5, 9)                 # Buckelbreite
        tief = rnd.randint(3, 6)              # wie weit der Buckel ueber die Wand haengt
        for dx in range(b):
            xx = x + dx
            if not (0 <= xx < W) or xx >= x1:
                continue
            # runde Buckelform
            rand = 2 if dx in (0, b - 1) else 1 if dx in (1, b - 2) else 0
            unten = y + tief - rand
            for yy in range(y - 3, unten + 1):
                if 0 <= yy < H:
                    if yy == unten:
                        c = G['g0']                    # dunkle Unterkante (Schatten des Ueberhangs)
                    elif yy == unten - 1:
                        c = G['g1']
                    elif yy <= y:
                        c = G['g4'] if (xx + yy) % 5 == 0 else G['g3']
                    else:
                        c = G['g2'] if dx < b // 2 else G['g3']
                    px[xx, yy] = c
            # Halmspitzen oben hell
            if rnd.random() < 0.35 and 0 <= y - 3 < H:
                px[xx, y - 3] = G['g5']
            # Schatten des Ueberhangs auf der Wand
            for yy in (unten + 1, unten + 2):
                if 0 <= yy < H and px[xx, yy][2] > px[xx, yy][1]:   # nur auf Fels (blaeulich)
                    r_, g_, b_, a_ = px[xx, yy]
                    px[xx, yy] = (int(r_ * 0.7), int(g_ * 0.7), int(b_ * 0.75), a_)
        # gelegentlich Moos, das an der Wand herabhaengt
        if rnd.random() < 0.25:
            mx = x + rnd.randint(1, max(1, b - 2))
            for yy in range(y + tief, y + tief + rnd.randint(2, 6)):
                if 0 <= mx < W and 0 <= yy < H:
                    px[mx, yy] = G['g1'] if yy % 2 else G['g0']
        x += b - 2                            # Buckel ueberlappen


def zeichne_klippen(img, plan, cols, treppen_spalten=frozenset(), seed=7):
    """Zeichnet alle Klippensegmente in img (RGBA, in Pixeln). Nord zuerst, Sued ueberdeckt."""
    rnd = random.Random(seed)
    W, H = img.size
    segs = sorted(plan['segmente'], key=lambda s: s['t'])
    schatten = Image.new('L', img.size, 0)
    sd = ImageDraw.Draw(schatten)
    for s in segs:
        t, h = s['t'], s.get('h', 3)
        x0, x1 = s['von'] * T, min((s['bis'] + 1) * T, W)
        y_top = (t - h) * T + 8                 # Unterkante der Wiese / Oberkante der Wand
        y_bot = (t + 1) * T - 2                 # Fuss der Wand
        wf = wand(x1 - x0, y_bot - y_top, rnd)
        # Treppen-Oeffnungen aussparen
        maske = Image.new('L', wf.size, 255)
        md = ImageDraw.Draw(maske)
        for (tx0, tx1) in treppen_spalten:
            if tx1 > x0 and tx0 < x1:
                md.rectangle((tx0 - x0, 0, tx1 - x0 - 1, wf.height), fill=0)
        img.paste(wf, (x0, y_top), maske)
        # Seitenkanten an Segmentenden (wo keine Nachbarwand auf gleicher Hoehe anschliesst)
        px = img.load()
        for xe, richtung in ((x0, 1), (x1 - 1, -1)):
            if 0 < xe < W - 1:
                for yy in range(y_top, y_bot):
                    px[xe, yy] = S[0]
                    px[xe + richtung, yy] = S[1]
        sd.rectangle((x0, y_bot, x1 - 1, y_bot + 3), fill=110)
        sd.rectangle((x0, y_bot + 4, x1 - 1, y_bot + 5), fill=50)
        graskante(img, x0, x1, y_top, rnd)
        # Treppen-Oeffnungen: Graskante dort wieder entfernen? -> Treppe ueberdeckt sie
    dunkel = Image.new('RGBA', img.size, (18, 40, 52, 255))
    dunkel.putalpha(schatten)
    img.alpha_composite(dunkel)


WASSER = {'w0': '#173f86', 'w1': '#2358b0', 'w2': '#3274d2', 'w3': '#4c93e6', 'w4': '#8cc4f4', 'w5': '#dff3ff'}
WS = {k: rgb(v) for k, v in WASSER.items()}
WEISS = (255, 255, 255, 255)


def zeichne_wasserfall(img, x0, x1, y_top, y_bot, seed=11):
    """Wasserfall ueber die volle Flussbreite x0..x1 von der Wandoberkante y_top bis zum Fuss y_bot.

    Aufbau (Licht von oben links): Abbruchkante, an der das Wasser ueber den Rand kippt ->
    fallendes Wasser mit senkrechten Streifen -> Gischtbecken mit Schaumblasen -> Ringe im Fluss.
    """
    rnd = random.Random(seed)
    px = img.load()
    W, H = img.size
    breite = x1 - x0

    def setz(x, y, c):
        if 0 <= x < W and 0 <= y < H:
            px[x, y] = c

    # 0) Graskante der Klippe ueber dem Fluss entfernen: Flusswasser bis zur Abbruchkante fortsetzen
    for i in range(breite):
        for y in range(y_top - 6, y_top - 1):
            setz(x0 + i, y, WS['w3'] if (y == y_top - 3 and i % 6 in (1, 2, 3)) else WS['w2'])
    # 1) fallendes Wasser: Grundton je Spalte (Raender dunkel und nass) + Streifen
    for i in range(breite):
        x = x0 + i
        rand = min(i, breite - 1 - i)
        basis = WS['w0'] if rand == 0 else WS['w1'] if rand == 1 else WS['w2'] if rand <= 3 else WS['w3']
        art, phase, laenge = rnd.random(), rnd.randint(0, 60), rnd.randint(18, 34)
        for y in range(y_top + 2, y_bot):
            c = basis
            if rand >= 2:
                v = (y + phase) % laenge
                if art < 0.45 and v < laenge * 2 // 3:          # lange helle Fallstreifen
                    c = WS['w4'] if 0 < v < laenge * 2 // 3 - 1 else WS['w3']
                elif art < 0.6 and v < 6:                       # weisse Glanzstriche
                    c = WS['w5']
                elif art > 0.8 and v < laenge // 2:             # dunklere Tiefenstreifen
                    c = WS['w2']
                # unten wird das Wasser durch Luft und Schaum heller
                if y > y_bot - 8 and rnd.random() < (y - (y_bot - 8)) / 10:
                    c = WS['w5'] if rnd.random() < 0.6 else WEISS
            setz(x, y, c)
        if rand == 0:                                           # nasser Fels direkt am Rand
            for y in range(y_top + 2, y_bot):
                setz(x - 1 if i == 0 else x + 1, y, S[0])
    # 2) Abbruchkante: Wasser kippt ueber den Rand (Wulst mit Glanzlinie, Licht von oben)
    for i in range(breite):
        x = x0 + i
        rand = min(i, breite - 1 - i)
        setz(x, y_top - 1, WS['w3'] if rand else WS['w1'])
        setz(x, y_top, WS['w4'] if rand >= 1 else WS['w1'])
        setz(x, y_top + 1, WS['w5'] if rand >= 2 and i % 5 != 4 else WS['w4'] if rand else WS['w1'])
        setz(x, y_top + 2, WS['w4'] if rand >= 2 else WS['w2'])
    # 3) Gischtbecken am Fuss: unregelmaessige Schaumwolke, breiter als der Fall
    cx, cy = (x0 + x1) / 2, y_bot + 1
    rx, ry = breite / 2 + 5, 6
    for y in range(int(cy - ry - 3), int(cy + ry + 1)):
        for x in range(int(cx - rx - 1), int(cx + rx + 2)):
            d = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
            if d <= 1.0 + rnd.uniform(-0.18, 0.1):
                if y < cy - 1 and not (x0 <= x < x1):
                    continue                       # oberhalb des Fusses nur im Fall selbst
                if d < 0.35:
                    c = WEISS if rnd.random() < 0.7 else WS['w5']
                elif d < 0.75:
                    c = WS['w5'] if rnd.random() < 0.75 else WEISS
                else:
                    c = WS['w4'] if rnd.random() < 0.7 else WS['w5']
                setz(x, y, c)
    # Schaumblasen mit Schatten unten rechts
    for _ in range(breite // 2):
        bx = int(cx + rnd.uniform(-rx, rx)); by = int(cy + rnd.uniform(-ry * 0.6, ry * 0.8))
        setz(bx, by, WEISS); setz(bx + 1, by, WS['w5']); setz(bx + 1, by + 1, WS['w4'])
    # 4) Ringe/Wellen im Fluss darunter
    for k, (dy, farbe) in enumerate(((ry + 2, WS['w4']), (ry + 5, WS['w4']), (ry + 9, WS['w3']))):
        for x in range(int(cx - rx + 3 + k * 2), int(cx + rx - 2 - k * 2)):
            if rnd.random() < 0.55:
                setz(x, int(cy + dy), farbe)
    # 5) feiner Spruehnebel
    for _ in range(breite):
        setz(int(cx + rnd.uniform(-rx - 4, rx + 4)), int(cy - rnd.uniform(2, 14)),
             (230, 245, 255, 255) if rnd.random() < 0.5 else WS['w5'])
