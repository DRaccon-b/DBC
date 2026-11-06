"""Baut Karte 03 (Server Desert).

  python3 tools/karte03_kacheln.py   # neue Grundkacheln (Weg, Kies, Platz, Lehm, Duene)
  python3 tools/karte03_bauen.py     # Boden + Bauwerke (+ Objekte, falls platziert)

Wiederverwendet: Sand/Gras/Wasser-Kacheln und die Wang-Sets gras_weg, wasser_sand, wasser_gras aus
Karte 01 (inkl. Wasseranimation), Bruecke aus tools/bauwerke.py, Bodenfuss/Schatten-Regeln aus Karte 02.
Neu: Weg/Kies/Platz/Lehm/Duene (tools/karte03_kacheln.py), erhoehte Sandsteinmauern der Ruinen-Arena
und der Ziegelring um den Garten, Duenenrand, Teleporter, Datenkabel.
"""
import json, math, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from collections import Counter
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import karte_bauen as kb
import industrie as ind
import karte03_prozedural as kp
import bauwerke

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte03')
BASIS1 = os.path.join(ROOT, 'assets', 'basis')
BASIS3 = os.path.join(ROOT, 'assets', 'karte03', 'basis')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte03')
T = 16
N_FRAMES = kb.N_FRAMES
CODE = {'sand': 's', 'gras': 'g', 'wasser': 'x', 'meer': 'm', 'weg': 'w', 'kies': 'k', 'platz': 'p', 'lehm': 'l', 'duene': 'd'}
SANDSTEIN = ind.pal('#6a4a2c', '#8a6640', '#a88250', '#c4a066', '#dcbc80', '#ecd49c', '#f8e8c0')
ZIEGEL = ind.pal('#3e2218', '#5a3020', '#7a4430', '#95553a', '#ae6a48', '#c48460', '#d89a74')


def r(n):
    return Image.open(n).convert('RGBA')


def zellen_der_form(z, cols, rows):
    if 'r' in z:
        x0, y0, x1, y1 = z['r']
        return [(x, y) for y in range(y0, y1 + 1) for x in range(x0, x1 + 1)]
    cx, cy, rx, ry = z['e']
    return [(x, y) for y in range(rows) for x in range(cols)
            if ((x + 0.5 - cx - 0.5) / rx) ** 2 + ((y + 0.5 - cy - 0.5) / ry) ** 2 <= 1]


def mauer_zellen(pfad, dicke=2):
    zellen = set()
    for (ax, ay), (bx, by) in zip(pfad, pfad[1:]):
        n = max(abs(bx - ax), abs(by - ay), 1)
        for i in range(n + 1):
            x = round(ax + (bx - ax) * i / n); y = round(ay + (by - ay) * i / n)
            for dx in range(dicke):
                for dy in range(dicke):
                    zellen.add((x + dx, y + dy))
    return zellen


def mauer_zeichnen(L, zellen, pal, hoehe, ziegel=True, rnd=None):
    """Erhoehte Mauer aus Kacheln: Front (Ziegelverband) an jeder Suedkante, Kappe um `hoehe` nach oben
    versetzt, Seitenkanten dunkel; Schatten nach rechts unten auf den Boden."""
    rnd = rnd or random.Random(3)
    for (x, y) in sorted(zellen, key=lambda c: c[1]):
        X, Y = x * T, y * T
        # Schatten (Licht oben links)
        if (x + 1, y) not in zellen:
            for yy in range(Y - hoehe + 4, Y + T + 2):
                for d, f in ((0, 0.62), (1, 0.75), (2, 0.88)):
                    L.neutral(X + T + d, yy, f)
        if (x, y + 1) not in zellen:
            for xx in range(X + 3, X + T + 3):
                for d, f in ((0, 0.6), (1, 0.74), (2, 0.88)):
                    L.neutral(xx, Y + T + d, f)
    for (x, y) in sorted(zellen, key=lambda c: c[1]):
        X, Y = x * T, y * T
        if (x, y + 1) not in zellen:                        # Front
            for yy in range(Y + T - hoehe, Y + T):
                k = yy - (Y + T - hoehe)
                for xx in range(X, X + T):
                    zeile = k // 4
                    vers = 4 if zeile % 2 else 0
                    c = pal[2]
                    if ziegel and (k % 4 == 3 or (xx + vers) % 8 == 7):
                        c = pal[1]
                    elif ziegel and k % 4 == 0:
                        c = pal[3]
                    if k >= hoehe - 2:
                        c = pal[0]
                    L.p(xx, yy, c)
        for yy in range(Y - hoehe, Y + T - hoehe):          # Kappe
            k = yy - (Y - hoehe)
            for xx in range(X, X + T):
                c = pal[4] if (xx + yy) % 7 else pal[3]
                if ziegel and ((k % 8 == 7) or ((xx + (4 if (k // 8) % 2 else 0)) % 16 == 15)):
                    c = pal[3]
                if (x, y - 1) not in zellen and k < 2:
                    c = pal[6] if k == 0 else pal[5]
                if (x - 1, y) not in zellen and xx == X:
                    c = pal[5]
                if (x + 1, y) not in zellen and xx == X + T - 1:
                    c = pal[1]
                L.p(xx, yy, c)
        if (x - 1, y) not in zellen or (x + 1, y) not in zellen:      # Seitenkanten der Front
            if (x, y + 1) not in zellen:
                for yy in range(Y + T - hoehe, Y + T):
                    if (x - 1, y) not in zellen:
                        L.p(X, yy, pal[3])
                    if (x + 1, y) not in zellen:
                        L.p(X + T - 1, yy, pal[0])
        if rnd.random() < 0.25:                             # Verwitterung auf der Kappe
            L.p(X + rnd.randint(2, 13), Y - hoehe + rnd.randint(2, 13), pal[2])


SANDKAPPE = ind.pal('#d8bc84', '#e6cc96', '#efdaa8', '#f6e6c0', '#fff4dc')


def _sandkappe(L, x0, x1, y0, y1, rnd):
    """Oberseite der Sandwand: heller Sand mit Windrippeln, Kante unten leicht gewellt."""
    for y in range(y0, y1):
        for x in range(x0, x1):
            k = (y - y0 + int(2 * math.sin(x / 11.0))) % 9
            c = SANDKAPPE[2] if k not in (0, 1) else (SANDKAPPE[1] if k == 0 else SANDKAPPE[3])
            if (x * 7 + y * 13) % 41 == 0:
                c = SANDKAPPE[4]
            L.p(x, y, c)


def _sandfront(L, x0, x1, y0, y1, rnd, verweht=6):
    """Sandsteinfront der Wand (Bloecke im Verband) mit angewehtem Sand am Fuss."""
    for y in range(y0, y1):
        for x in range(x0, x1):
            k = y - y0
            zeile = k // 6
            vers = 8 if zeile % 2 else 0
            c = SANDSTEIN[3] if k < 2 else SANDSTEIN[2]
            if k % 6 == 5 or (x + vers) % 16 == 15:
                c = SANDSTEIN[1]
            elif k % 6 == 0 and k > 0:
                c = SANDSTEIN[4]
            if (x * 5 + y * 3) % 37 == 0:
                c = SANDSTEIN[1]
            L.p(x, y, c)
    for x in range(x0, x1):                                  # Lichtkante oben (Kappenrand)
        L.p(x, y0, SANDKAPPE[4]); L.p(x, y0 + 1, SANDSTEIN[5])
        hoch = int(verweht + 3 * math.sin(x / 13.0) + 2 * math.sin(x / 5.3))
        for d in range(max(0, hoch)):                        # Sandverwehung am Fuss
            yy = y1 - 1 - d
            L.p(x, yy, SANDKAPPE[1] if d == hoch - 1 else SANDKAPPE[0] if d > hoch - 3 else ind.rgb('#d0b07a'))


def sandwand_oben(L, cfg, rnd):
    """Noerdliche Grenze: Sanddecke + Sandsteinfront. Am Fluss (links) endet sie nicht hart:
    Stirnseite der Front im Schatten und eine Sandrampe davor."""
    x0, x1 = cfg['x'][0] * T, (cfg['x'][1] + 1) * T
    y0, y1 = cfg['kappe'][0] * T, (cfg['kappe'][1] + 1) * T
    fr = cfg['front']
    _sandkappe(L, x0, x1, y0, y1, rnd)
    _sandfront(L, x0, x1, y1, y1 + fr, rnd)
    for x in range(x0, x1):                                  # Schatten der Wand auf den Boden
        for d, f in ((0, 0.72), (1, 0.84), (2, 0.93)):
            L.neutral(x, y1 + fr + d, f)
    # Wandende am Fluss: saubere Kante. Decke mit Lichtkante, Stirnseite der Front im Schatten,
    # auf dem Wasser eine Schaumlinie entlang der Wand.
    for y in range(y0, y1):
        L.p(x0, y, SANDKAPPE[0]); L.p(x0 + 1, y, SANDKAPPE[4]); L.p(x0 + 2, y, SANDKAPPE[3])
    for x in range(x0, x0 + 3):
        L.p(x, y1, SANDKAPPE[4])
    for y in range(y1 + 1, y1 + fr):
        L.p(x0, y, SANDSTEIN[0]); L.p(x0 + 1, y, SANDSTEIN[1]); L.p(x0 + 2, y, SANDSTEIN[2])
    for y in range(y0, y1 + fr + 1):
        if cfg.get('enden_am_strand'):                       # v1.1: Wandende steht auf Sand, kein Schaum
            break
        if (y // 2) % 3 != 2:
            L.p(x0 - 1, y, ind.rgb('#cfe8ff'))
        if y % 5 == 0:
            L.p(x0 - 2, y, ind.rgb('#8cc4f4'))
    for x in range(x0, x0 + 3):
        L.neutral(x, y1 + fr, 0.75); L.neutral(x, y1 + fr + 1, 0.86)
    if cfg.get('ende_rechts_meer'):                          # v1.1: rechtes Wandende am Meer (gespiegelt,
        xe = x1 - 1                                          # Stirnseite im Schatten, Licht oben links)
        for y in range(y0, y1):
            L.p(xe, y, SANDKAPPE[0]); L.p(xe - 1, y, SANDKAPPE[1]); L.p(xe - 2, y, SANDKAPPE[2])
        for y in range(y1 + 1, y1 + fr):
            L.p(xe, y, SANDSTEIN[0]); L.p(xe - 1, y, SANDSTEIN[0]); L.p(xe - 2, y, SANDSTEIN[1])
        for y in range(y1, y1 + fr + 1):
            L.neutral(xe + 1, y, 0.8); L.neutral(xe + 2, y, 0.9)   # Schatten der Stirnseite auf den Strand


def sandwand_vorne(L, cfg, rnd, rechts_x=None):
    """Suedliche Kartengrenze im Vordergrund: nur die Sanddecke (ohne Front). Sie ragt ueber den Boden
    davor und deckt Objekte ab, die dahinter stehen; welliger Kamm mit Lichtkante und Kontaktschatten."""
    x0, x1 = cfg['x'][0] * T, (cfg['x'][1] + 1) * T
    k0 = cfg['fuss'] * T - 16
    R = 34
    for x in range(x0, x1):
        w = int(2 * math.sin(x / 9.0) + 1.5 * math.sin(x / 21.0))
        if rechts_x is not None:                           # Innenecke unten rechts: Kamm steigt weich an
            xe = rechts_x(k0 - R)
            if x >= xe - R:
                u = min(R, x - (xe - R))
                w -= int(R - math.sqrt(max(0, R * R - u * u)))
        for y in range(k0 + w, L.H):
            if x0 > 0 and x < x0 + 6 + int(2 * math.sin(y / 6.0)):
                continue                                   # Uferseite: wellige Kante statt Kachelkante
            if rechts_x is not None and x >= rechts_x(y) + 3:
                continue                                   # dort liegt schon die Seitendecke
            kk = (y - k0 + int(2 * math.sin(x / 11.0))) % 9
            c = SANDKAPPE[2] if kk not in (0, 1) else (SANDKAPPE[1] if kk == 0 else SANDKAPPE[3])
            if (x * 7 + y * 13) % 41 == 0:
                c = SANDKAPPE[4]
            L.p(x, y, c)
        if rechts_x is not None and x >= rechts_x(k0 + w) + 3:
            continue
        for d in range(3):
            L.p(x, k0 + w + d, SANDKAPPE[4] if d == 0 else SANDKAPPE[3])
        L.neutral(x, k0 + w - 1, 0.78); L.neutral(x, k0 + w - 2, 0.9)


def seiten_kante(y):
    """x-Versatz der Innenkante der rechten Sandwand (wellig, keine gerade Naht)."""
    return int(round(3.5 * math.sin(y / 23.0) + 2.0 * math.sin(y / 9.0 + 1.3) + 1.0 * math.sin(y / 4.1)))


def _verwehung_pixel(L, x, y, t):
    """Angewehter Sand auf dem Boden, t=1 direkt an der Wand, t->0 laeuft aus (gerastert)."""
    if t <= 0:
        return
    if t > 0.66:
        c = SANDKAPPE[1]
    elif t > 0.33:
        c = SANDKAPPE[0]
    else:
        if (x + y) % 2:
            return
        c = SANDKAPPE[0]
    L.p(x, y, c)


def sandwand_seite(L, cfg, rnd):
    """Seitliche Kartengrenze (rechts): Sanddecke von oben, wellige Innenkante mit heller Lichtkante
    (die Flanke zeigt zum Licht), am Fuss angewehter Sand, der weich in den Boden auslaeuft."""
    x0, x1 = cfg['x'][0] * T, (cfg['x'][1] + 1) * T
    y0, y1 = cfg['y'][0] * T, (cfg['y'][1] + 1) * T
    front = cfg.get('front_unten', 0)
    kap_ende = y1 - front
    for y in range(y0, kap_ende):
        xi = x0 + 5 + seiten_kante(y)
        breite = 7 + int(3 * math.sin(y / 13.0 + 0.7) + 2 * math.sin(y / 5.0))
        for d in range(1, breite + 1):                    # Verwehung am Fuss der Flanke
            _verwehung_pixel(L, xi - d, y, 1 - d / breite)
        for x in range(xi, x1):
            if y0 > 0 and not front:                       # Nordkante (oberes Segmentende): welliger Kamm
                wk = y0 + 2 + int(2 * math.sin(x / 9.0) + 1.5 * math.sin(x / 17.0))
                if y < wk:
                    continue
                if y < wk + 3:
                    L.p(x, y, SANDKAPPE[4] if y == wk else SANDKAPPE[3])
                    if y == wk:
                        L.neutral(x, y - 1, 0.8); L.neutral(x, y - 2, 0.9)
                    continue
            kk = (y + int(2 * math.sin(x / 11.0))) % 9
            c = SANDKAPPE[2] if kk not in (0, 1) else (SANDKAPPE[1] if kk == 0 else SANDKAPPE[3])
            if (x * 7 + y * 13) % 41 == 0:
                c = SANDKAPPE[4]
            L.p(x, y, c)
        L.p(xi, y, SANDKAPPE[0]); L.p(xi + 1, y, SANDKAPPE[4]); L.p(xi + 2, y, SANDKAPPE[3])
    if front:
        _sandfront(L, x0 + 2, x1, kap_ende, y1, rnd, verweht=4)
        for x in range(x0 + 2, x1):
            for d, f in ((0, 0.72), (1, 0.85)):
                L.neutral(x, y1 + d, f)


def eck_verwehung(L, cx, cy, rx, ry, links=True):
    """Sandhaufen in einer Innenecke (Wind treibt Sand hinein): Viertel-Ellipse am Boden,
    aussen gerastert auslaufend, Kuppe mit Lichtkante oben links."""
    for y in range(int(cy - ry), int(cy + ry) + 1):
        for x in range(int(cx - rx), int(cx + rx) + 1):
            if (x > cx) == links:
                continue
            dd = math.hypot((x - cx) / rx, (y - cy) / ry) + 0.08 * math.sin(x / 3.0 + y / 4.0)
            if dd < 1:
                _verwehung_pixel(L, x, y, 1 - dd)


def arena_uebergang(img, L, arena, ob, arena_flaeche):
    """Die Arena ist in die noerdliche Duene gegraben: Neben dem Ring fliesst die Duene schraeg ueber die
    Sandsteinfront bis auf den Boden, ueber der Arena woelbt sich ihr Kamm nach oben. Kamm mit Lichtkante,
    darunter ein weicher Sandhang und ein schmaler Schatten."""
    y1 = (ob['kappe'][1] + 1) * T
    fu = y1 + ob['front']
    zellen = [(x, y) for (x, y) in arena_flaeche if y * T < fu + 4]
    if not zellen:
        return
    xa = min(x for x, _ in zellen) * T
    xb = (max(x for x, _ in zellen) + 1) * T
    rampe = 40
    unten, oben = fu + 3, y1 + 15

    def glatt(t):
        t = min(1.0, max(0.0, t))
        return t * t * (3 - 2 * t)

    for x in range(xa - rampe, xb + rampe):
        if x < xa:
            kamm = y1 + (unten - y1) * glatt((x - (xa - rampe)) / rampe)
        elif x >= xb:
            kamm = y1 + (unten - y1) * glatt(((xb + rampe) - x) / rampe)
        else:
            u = (x - xa) / (xb - xa)
            kamm = unten - (unten - oben) * glatt(min(1.0, math.sin(math.pi * u) * 1.6))
        kamm = int(round(kamm + 1.5 * math.sin(x / 9.0) + math.sin(x / 4.7)))
        for y in range(0, kamm):
            kk = (y + int(2 * math.sin(x / 11.0))) % 9
            c = SANDKAPPE[2] if kk not in (0, 1) else (SANDKAPPE[1] if kk == 0 else SANDKAPPE[3])
            if (x * 7 + y * 13) % 41 == 0:
                c = SANDKAPPE[4]
            L.p(x, y, c)
        if kamm <= y1 + 1:
            continue                                            # dort liegt die normale Wandkante
        L.p(x, kamm - 2, SANDKAPPE[3]); L.p(x, kamm - 1, SANDKAPPE[4])
        hang = 6 + int(2 * math.sin(x / 5.3))
        w = 0.0 if x < xa or x >= xb else glatt(min(1.0, math.sin(math.pi * (x - xa) / (xb - xa)) * 1.6))
        if w > 0.5:                                              # verschuettetes Gemaeuer schaut hervor
            hm = int(round(11 * (w - 0.5) / 0.5))
            for k in range(hm):
                y = kamm + k
                zeile = k // 5
                c = SANDSTEIN[4] if k == 0 else SANDSTEIN[3] if k % 5 < 2 else SANDSTEIN[2]
                if k % 5 == 4 or (x + (5 if zeile % 2 else 0)) % 11 == 0:
                    c = SANDSTEIN[1]
                if (x * 5 + y * 3) % 29 == 0:
                    c = SANDSTEIN[1]
                L.p(x, y, c)
            for d in range(2):                                   # Fuss: Schatten + angewehter Sand
                L.neutral(x, kamm + hm + d, 0.82 if d == 0 else 0.92)
            if (x // 3) % 4 != 0:
                L.p(x, kamm + hm - 1, SANDKAPPE[1])
            # Sand bedeckt das Mauerwerk unregelmaessig: mal fast ganz, mal nur die Krone
            hang = 2 + int(round((hm - 4) * (0.5 + 0.38 * math.sin(x / 14.0 + 1.1) + 0.12 * math.sin(x / 5.5))))
            hang = max(2, min(hm, hang))
        for d in range(hang):                                    # Sandhang
            t = 1 - d / hang
            c = SANDKAPPE[2] if t > 0.75 else SANDKAPPE[1] if t > 0.4 else SANDKAPPE[0]
            if t <= 0.4 and (x + d) % 2:
                continue
            L.p(x, kamm + d, c)
        L.neutral(x, kamm + hang, 0.84); L.neutral(x, kamm + hang + 1, 0.92)


def pyramide_sprite(breite=240, hoehe=168):
    """Klassische Pyramide (prozedural, garantiert dreieckig): Spitze mittig, linke Flanke im Licht,
    rechte Flanke im Schatten, Steinlagen im Verband, Eingang mit Rundbogen unten in der Mitte und ein
    leuchtendes Auge (Cyan) unter der Spitze. Fuss ist die unterste Zeile."""
    im = Image.new('RGBA', (breite, hoehe), (0, 0, 0, 0))
    L = ind.Leinwand(im)
    cx = breite // 2
    licht = ind.pal('#8a6640', '#b08a58', '#c8a46c', '#dcbc84', '#ecd49c', '#f8e8c0')
    schatten = ind.pal('#4a3020', '#6a4630', '#82583a', '#9a6c46', '#ae7e52')
    teil = 0.62                                         # Kante zwischen Licht- und Schattenflanke
    for y in range(hoehe):
        t = y / (hoehe - 1)
        xl = int(round(cx - t * breite / 2)); xr = int(round(cx + t * breite / 2))
        xk = int(round(cx + t * (breite / 2) * (2 * teil - 1)))   # Grat (leicht rechts der Mitte)
        lage = y // 7
        for x in range(xl, xr + 1):
            licht_seite = x <= xk
            pal_ = licht if licht_seite else schatten
            c = pal_[3] if licht_seite else pal_[2]
            vers = 6 if lage % 2 else 0
            if y % 7 == 6:
                c = pal_[1]                             # Lagenfuge
            elif (x + vers) % 12 == 11:
                c = pal_[1]                             # Stossfuge
            elif y % 7 == 0:
                c = pal_[4] if licht_seite else pal_[3]  # Lichtkante der Lage
            if (x * 7 + y * 11) % 53 == 0:
                c = pal_[2]                             # Verwitterung
            if x in (xl, xl + 1) and licht_seite:
                c = licht[5]
            if x in (xr, xr - 1):
                c = schatten[0]
            if abs(x - xk) < 1:
                c = licht[5]                            # Grat im Licht
            L.p(x, y, c)
    for x in range(breite):                             # Sockelkante
        L.p(x, hoehe - 1, schatten[0])
    # Eingang (Rundbogen) mittig auf der Lichtflanke
    ex, eb, eh = cx - 8, 22, 30
    for y in range(hoehe - eh, hoehe - 1):
        for x in range(ex - eb // 2, ex + eb // 2):
            dx = x - ex
            oben = hoehe - eh + 8
            if y < oben and dx * dx + ((y - oben) * 1.3) ** 2 > (eb / 2) ** 2:
                continue
            rand = abs(dx) >= eb // 2 - 3 or (y < oben and dx * dx + ((y - oben) * 1.3) ** 2 > (eb / 2 - 3) ** 2)
            L.p(x, y, licht[4] if rand and dx < 0 else schatten[1] if rand else ind.rgb('#1c1a20'))
    # leuchtendes Auge
    ay = int(hoehe * 0.2); ax = cx - 2
    auge = ["..cccc..", ".c.ww.c.", "c.wwhw.c", ".c.ww.c.", "..cccc..", "...cc...", "..c..c.."]
    farbe = {'c': ind.rgb('#2fc7d8'), 'w': ind.rgb('#7ff0f5'), 'h': ind.rgb('#e6ffff')}
    for dy, z in enumerate(auge):
        for dx, ch in enumerate(z):
            if ch != '.':
                for sy in (0, 1):
                    for sx in (0, 1):
                        L.p(ax - 8 + dx * 2 + sx, ay + dy * 2 + sy, farbe[ch])
    return im


def bauen(frame=None, speichern=True):
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cols, rows = lay['groesse']
    cls = [['s'] * cols for _ in range(rows)]
    for z in lay['boden']:
        for (x, y) in zellen_der_form(z, cols, rows):
            if 0 <= x < cols and 0 <= y < rows:
                cls[y][x] = CODE[z['art']]

    # --- 0. Regel 6 (v1.1): Wege in natuerlichen Boegen; an Steg, Inselsteg, Teleportern, Arena-Tor und
    #        Kartenrand bleiben die Anschluesse exakt
    if lay.get('_v11'):
        import regeln_v11
        g = np.array(cls)
        anker = np.zeros((rows, cols), bool)
        anker[:, :8] = anker[:, -7:] = True
        anker[:4, :] = anker[-5:, :] = True
        st_ = lay.get('steg')
        if st_:
            anker[st_['y'] - 2:st_['y'] + st_['breite'] + 2, :st_['x'] + st_['laenge'] + 3] = True
        if lay.get('inselsteg'):
            x0_, x1_, y0_, y1_ = lay['inselsteg']
            anker[y0_ - 3:y1_ + 4, x0_ - 2:x1_ + 3] = True
        for (tx_, ty_) in lay.get('teleporter', []):
            anker[ty_ - 3:ty_ + 7, max(0, tx_ - 3):tx_ + 5] = True
        tor = lay.get('arena', {}).get('tor')
        if tor:
            anker[tor[1] - 2:tor[3] + 3, tor[0] - 2:tor[2] + 3] = True
        g = regeln_v11.boegen(g, anker, np.isin(g, ['s', 'w']), A=3.2, zelle=10)
        cls = [list(r_) for r_ in g]

    # --- 1. Basis: Sand/Gras/Wasser mit Wang-Uebergaengen aus Karte 01
    basis = {k: [r(os.path.join(BASIS1, '%s_%d.png' % (n, i))) for i in range(5)]
             for k, n in (('s', 'sand'), ('g', 'gras'), ('x', 'wasser'))}
    neu = {k: [r(os.path.join(BASIS3, '%s_%d.png' % (n, i))) for i in range(5)]
           for k, n in (('w', 'weg'), ('k', 'kies'), ('p', 'platz'), ('l', 'lehm'), ('d', 'duene'))}
    sets = {n: kb.lade_set(n) for n in ('gras_weg', 'wasser_sand', 'wasser_gras')}
    PAARE = {frozenset('gs'): ('gras_weg', 's', 'g'), frozenset('gx'): ('wasser_gras', 'x', 'g'),
             frozenset('sx'): ('wasser_sand', 'x', 's')}
    grund = lambda k: 'x' if k == 'm' else (k if k in 'gx' else 's')     # Meer: erst Wasser, dann Terrassen
    def zg(x, y):
        return grund(cls[min(max(y, 0), rows - 1)][min(max(x, 0), cols - 1)])
    vk = [[None] * (cols + 1) for _ in range(rows + 1)]
    for vy in range(rows + 1):
        for vx in range(cols + 1):
            c = Counter(zg(vx + dx, vy + dy) for dx in (-1, 0) for dy in (-1, 0))
            vk[vy][vx] = next((k for k in 'xsg' if c[k] >= 2), 's')
    for _ in range(4):                                     # keine Kachel mit drei Arten: Gras weicht
        for y in range(rows):
            for x in range(cols):
                ecken = [(x, y), (x + 1, y), (x, y + 1), (x + 1, y + 1)]
                if len({vk[b][a] for a, b in ecken}) == 3:
                    for a, b in ecken:
                        if vk[b][a] == 'g':
                            vk[b][a] = 's'
    img = Image.new('RGBA', (cols * T, rows * T))
    wasserzellen = []
    for y in range(rows):
        for x in range(cols):
            e = {vk[y][x], vk[y][x + 1], vk[y + 1][x], vk[y + 1][x + 1]}
            if len(e) == 1:
                k = e.pop()
                i = kb.variante(x, y)
                kachel, beschr = basis[k][i], 'basis:%s_%d' % ({'s': 'sand', 'g': 'gras', 'x': 'wasser'}[k], i)
            else:
                name, lo, up = PAARE[frozenset(e)]
                pat = [[255] * 4]
                for vy in (y, y + 1):
                    pat.append([255] + [0 if vk[vy][vx] == lo else 1 for vx in (x, x + 1)] + [255])
                pat.append([255] * 4)
                t, _ = kb.waehle(sets[name]['tiles'], pat)
                kachel, beschr = t['img'], '%s:%s' % (name, t['name'])
            if frame is not None and ('wasser' in beschr):
                kachel = kb.wasser_frame(kachel, beschr, 'W' if x < 6 else 'D', y, x, frame,
                                         {'w': basis['x'], 'm': basis['x']})
                wasserzellen.append((x, y))
            img.paste(kachel, (x * T, y * T))
    # --- 1b. Fluss und Oasenteiche vertieft (Stil von Karte 01: Ufermauer, Steingrund, Tiefenstufen)
    import wasser_vertieft
    region = np.zeros((rows * T, cols * T), bool)
    for y in range(rows):
        for x in range(cols):
            if cls[y][x] == 'x':
                region[max(0, y * T - T):(y + 2) * T, max(0, x * T - T):(x + 2) * T] = True
    img = wasser_vertieft.vertiefen(img, region, frame,
                                    rand=('#7a5434', '#a07448', '#c49a64', '#dcb886')).convert('RGBA')
    # --- 1c. Meer (v1.1) wie Karte 01: Flachwasser, Schaumkante, zwei Stufen, Tiefsee, Felsen, Algen
    import wasser_details
    meer_region = np.zeros((rows * T, cols * T), bool)
    for y in range(rows):
        for x in range(cols):
            if cls[y][x] == 'm':
                meer_region[max(0, y * T - 2 * T):(y + 3) * T, max(0, x * T - 2 * T):(x + 3) * T] = True
    if meer_region.any():
        meiden_m = np.zeros_like(meer_region)
        st_ = lay.get('steg')
        if st_:
            meiden_m[st_['y'] * T - 16:(st_['y'] + st_['breite']) * T + 16, : (st_['x'] + st_['laenge']) * T + 16] = True
        if lay.get('inselsteg'):
            x0_, x1_, y0_, y1_ = lay['inselsteg']
            meiden_m[y0_ * T - 16:(y1_ + 1) * T + 16, x0_ * T - 16:(x1_ + 1) * T + 16] = True
        for (tx_, ty_) in lay.get('teleporter', []):
            meiden_m[ty_ * T - 16:(ty_ + 4) * T + 16, max(0, tx_ * T - 16):(tx_ + 2) * T + 16] = True
        wasser_details.FELSEN_PROTOKOLL.clear()
        wasser_details.SPITZEN.clear()
        # schmalere Meeresflaechen als auf Karte 01: Stufen naeher am Ufer, damit es tief wird
        alt_k = (wasser_details.FLACH, wasser_details.SCHAUM_D, wasser_details.STUFE1, wasser_details.STUFE2)
        wasser_details.FLACH, wasser_details.SCHAUM_D, wasser_details.STUFE1, wasser_details.STUFE2 = 16, (14, 18), 40, 70
        try:
            img = wasser_details.meer_terrassen(img, meer_region, frame, meiden_m).convert('RGBA')
        finally:
            wasser_details.FLACH, wasser_details.SCHAUM_D, wasser_details.STUFE1, wasser_details.STUFE2 = alt_k
    L = ind.Leinwand(img)

    # --- 2. Boden-Overlays auf Sand: Weg, Kies, Platz, Lehm, Duene
    def maske_von(art, blur=3.0, rausch=0.3, seed=1):
        m = Image.new('L', img.size, 0)
        d = ImageDraw.Draw(m)
        for y in range(rows):
            for x in range(cols):
                if cls[y][x] == art:
                    d.rectangle((x * T, y * T, x * T + T - 1, y * T + T - 1), fill=255)
        a = np.array(m.filter(ImageFilter.GaussianBlur(blur))).astype(np.float32) / 255
        h, w = a.shape
        n = np.random.RandomState(seed).rand(h // 4 + 2, w // 4 + 2)
        n = np.array(Image.fromarray((n * 255).astype(np.uint8)).resize((w + 8, h + 8), Image.BICUBIC))[:h, :w] / 255
        return a + (n - 0.5) * rausch

    def textur(art):
        t = np.zeros((rows * T, cols * T, 4), np.uint8)
        for y in range(rows):
            for x in range(cols):
                t[y * T:(y + 1) * T, x * T:(x + 1) * T] = np.array(neu[art][kb.variante(x, y)])
        return t

    def kies_maske(blur=3.5, rausch=0.45, seed=9):
        m = Image.new('L', img.size, 0)
        d = ImageDraw.Draw(m)
        for z in lay['boden']:
            if z['art'] != 'kies':
                continue
            if 'e' in z:
                cx, cy, rx, ry = z['e']
                d.ellipse(((cx - rx + 0.5) * T, (cy - ry + 0.5) * T, (cx + rx + 0.5) * T, (cy + ry + 0.5) * T), fill=255)
            else:
                x0, y0, x1, y1 = z['r']
                d.rounded_rectangle((x0 * T, y0 * T, (x1 + 1) * T - 1, (y1 + 1) * T - 1), radius=26, fill=255)
        for y in range(rows):                              # Wege/Wasser schneiden den Kies
            for x in range(cols):
                if cls[y][x] != 'k':
                    d.rectangle((x * T, y * T, x * T + T - 1, y * T + T - 1), fill=0) if cls[y][x] in 'xg' else None
        a = np.array(m.filter(ImageFilter.GaussianBlur(blur))).astype(np.float32) / 255
        h, w = a.shape
        n = np.random.RandomState(seed).rand(h // 6 + 2, w // 6 + 2)
        n = np.array(Image.fromarray((n * 255).astype(np.uint8)).resize((w + 12, h + 12), Image.BICUBIC))[:h, :w] / 255
        return a + (n - 0.5) * rausch

    a_img = np.array(img)
    for art, blur, rausch, rand in (('k', 3.5, 0.45, 'steine'), ('w', 4.0, 0.22, 'weich')):
        f = kies_maske() if art == 'k' else maske_von(art, blur, rausch, seed=7)
        tex = textur(art)
        innen = f > 0.5
        a_img[innen] = tex[innen]
        saum = (f > 0.36) & ~innen
        if rand == 'weich':                                # Weg: weicher Uebergang, Sand dunkler
            a_img[saum, :3] = (a_img[saum, :3].astype(np.float32) * 0.94).astype(np.uint8)
        else:                                              # Kies: einzelne Steine im Rand, Schatten
            ys, xs = np.nonzero(saum)
            rs = np.random.RandomState(5)
            for yy, xx in zip(ys, xs):
                if rs.rand() < 0.10 and f[yy, xx] > 0.42:
                    a_img[yy, xx, :3] = tex[yy, xx, :3]
                else:
                    a_img[yy, xx, :3] = (a_img[yy, xx, :3] * 0.93).astype(np.uint8)
    img.paste(Image.fromarray(a_img))
    L = ind.Leinwand(img)
    # Platz: harte Kante mit Bordstein und Schatten; Lehm: leicht erhabene Scholle mit Front
    for y in range(rows):
        for x in range(cols):
            k = cls[y][x]
            if k in 'pld':
                img.paste(neu[k][kb.variante(x, y)], (x * T, y * T))
    for y in range(rows):
        for x in range(cols):
            k = cls[y][x]
            if k not in 'pld':
                continue
            X, Y = x * T, y * T
            nb = lambda dx, dy: cls[y + dy][x + dx] if 0 <= x + dx < cols and 0 <= y + dy < rows else k
            if k == 'p':
                pal_ = (ind.rgb('#3a3e52'), ind.rgb('#b0b8cc'))
                for i in range(T):
                    if nb(0, -1) != 'p': L.p(X + i, Y, pal_[1]); L.p(X + i, Y + 1, pal_[0])
                    if nb(0, 1) != 'p': L.p(X + i, Y + T - 1, pal_[0]); L.neutral(X + i, Y + T, 0.75)
                    if nb(-1, 0) != 'p': L.p(X, Y + i, pal_[1])
                    if nb(1, 0) != 'p': L.p(X + T - 1, Y + i, pal_[0]); L.neutral(X + T, Y + i, 0.78)
            elif k == 'l':
                for i in range(T):
                    if nb(0, -1) != 'l': L.p(X + i, Y, ind.rgb('#c07a4e'))
                    if nb(-1, 0) != 'l': L.p(X, Y + i, ind.rgb('#a8643e'))
                    if nb(1, 0) != 'l': L.p(X + T - 1, Y + i, ind.rgb('#4a2a1e'))
                    if nb(0, 1) != 'l':                    # Front 4 px + Schatten
                        for d, c in ((0, '#6e3c28'), (1, '#5a3020'), (2, '#4a2a1e'), (3, '#3a2018')):
                            L.p(X + i, Y + T - 4 + d, ind.rgb(c))
                        L.neutral(X + i + 2, Y + T, 0.7); L.neutral(X + i + 2, Y + T + 1, 0.85)
            elif k == 'd':
                rs = random.Random(x * 31 + y)
                if nb(0, 1) not in 'd':                    # Duene ueber Sand: Hang nach Sueden
                    for i in range(T):
                        welle = int(2 * math.sin((X + i) / 9.0) + 2 * math.sin((X + i) / 23.0))
                        for d in range(10):
                            yy = Y + T - 3 + welle + d
                            if d < 2:
                                L.p(X + i, yy, ind.rgb('#d8bc84'))
                            elif d < 7:
                                L.p(X + i, yy, ind.rgb('#e6cc96') if d < 4 else ind.rgb('#d6b47c'))
                            else:
                                L.neutral(X + i, yy, 0.86 + d * 0.012)
                if nb(0, -1) not in 'd':                   # Duene unter Sand: Kamm mit Lichtkante
                    for i in range(T):
                        welle = int(2 * math.sin((X + i) / 8.0 + 1) + 1.5 * math.sin((X + i) / 19.0))
                        for d in range(-3, 3):
                            yy = Y + welle + d
                            L.p(X + i, yy, ind.rgb('#fff8e6') if d == -3 else ind.rgb('#f4e4bc') if d < 0 else ind.rgb('#e2c890'))
                for (nx, ny, sx) in ((-1, 0, 0), (1, 0, T - 1)):
                    if nb(nx, ny) not in 'd':
                        for j in range(T):
                            welle = int(2 * math.sin((Y + j) / 7.0))
                            xx = X + sx + welle * (1 if nx > 0 else -1)
                            L.p(xx, Y + j, ind.rgb('#e2c890'))
                            L.p(xx + (1 if nx < 0 else -1), Y + j, ind.rgb('#fff8e6'))

    # Sandrippel und Steinchen auf freiem Sand
    rs = random.Random(21)
    for y in range(rows):
        for x in range(cols):
            if cls[y][x] != 's' or vk[y][x] != 's':
                continue
            r_ = rs.random()
            X, Y = x * T + rs.randint(2, 12), y * T + rs.randint(2, 12)
            if r_ < 0.08:
                for i in range(rs.randint(3, 6)):
                    L.p(X + i, Y + (i // 3), ind.rgb('#c9a46e')); L.p(X + i, Y + 1 + (i // 3), ind.rgb('#f2dba6'))
            elif r_ < 0.11:
                L.p(X, Y, ind.rgb('#9c7448')); L.p(X + 1, Y, ind.rgb('#c09a62')); L.neutral(X + 1, Y + 1, 0.8)

    # --- 3. Kabelnetz (Datenkabel am Boden, lila), Steg, Teleporter
    lila = (ind.rgb('#2a2050'), ind.rgb('#4a3a8a'), ind.rgb('#7a6ac8'))
    knoten = set()
    for (a, b) in lay.get('kabel', []):
        (ax, ay), (bx, by) = a, b
        knoten.update({(ax, ay), (bx, by)})
        if ax == bx:
            for yy in range(min(ay, by) * T + 8, max(ay, by) * T + 9):
                L.p(ax * T + 7, yy, lila[1]); L.p(ax * T + 8, yy, lila[0]); L.p(ax * T + 6, yy, lila[2])
                L.neutral(ax * T + 9, yy + 1, 0.8)
        else:
            for xx in range(min(ax, bx) * T + 8, max(ax, bx) * T + 9):
                L.p(xx, ay * T + 7, lila[2]); L.p(xx, ay * T + 8, lila[1]); L.p(xx, ay * T + 9, lila[0])
                L.neutral(xx + 1, ay * T + 10, 0.8)
    for (kx, ky) in knoten:                                # Verteilerdosen
        X, Y = kx * T + 4, ky * T + 4
        L.rect(X, Y, X + 8, Y + 8, ind.rgb('#3e4850')); L.rect(X, Y, X + 8, Y + 1, ind.rgb('#8e9ba3'))
        L.rect(X, Y + 7, X + 8, Y + 8, ind.rgb('#1c2128')); L.p(X + 5, Y + 3, ind.rgb('#7ff0f5'))
    st = lay.get('steg')
    if st:
        bauwerke.zeichne_bruecke(img, st['x'] * T, (st['x'] + st['laenge']) * T, st['y'] * T,
                                 (st['y'] + st['breite']) * T - 2, frame=frame or 0)
        L = ind.Leinwand(img)
    if lay.get('inselsteg'):                               # Holzsteg von der Insel nach Sueden zum Festland
        x0_, x1_, y0_, y1_ = lay['inselsteg']
        bauwerke.zeichne_steg(img, x0_ * T + 4, (x1_ + 1) * T - 4, y0_ * T, (y1_ + 1) * T - 2, frame=frame or 0)
        L = ind.Leinwand(img)
    puls = 0.5 + 0.5 * math.sin(2 * math.pi * (frame or 0) / N_FRAMES)
    for (tx, ty) in lay.get('teleporter', []):
        for i in range(2):
            for j in range(4):
                cx, cy = (tx + i) * T + 8, (ty + j) * T + 8
                for yy in range(-6, 7):
                    for xx in range(-7, 8):
                        d = (xx / 7) ** 2 + (yy / 6) ** 2
                        if d <= 1:
                            if d > 0.7:
                                c = ind.rgb('#3e4850') if yy > 0 else ind.rgb('#8e9ba3')
                            elif d > 0.35:
                                c = ind.rgb('#2fc7d8') if puls > 0.4 or d < 0.5 else ind.rgb('#2a8aa0')
                            else:
                                c = ind.rgb('#e6ffff') if puls > 0.6 else ind.rgb('#7ff0f5')
                            L.p(cx + xx, cy + yy, c)

    # --- 4. Erhoehte Mauern: Ruinen-Arena (Sandstein) und Garten-Ring (Ziegel)
    ar = lay.get('arena', {})
    arena = mauer_zellen(ar.get('pfad', [])) | mauer_zellen(ar.get('pfad2', []))
    if 'e' in ar:
        cx, cy, rx, ry = ar['e']
        dk = ar.get('dicke', 2)
        for y in range(rows):
            for x in range(cols):
                d = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
                di = ((x - cx) / (rx - dk)) ** 2 + ((y - cy) / (ry - dk)) ** 2
                if d <= 1 and di > 1:
                    oo = ar.get('ost_offen')
                    if oo and x > cx + 3 and oo[0] <= y <= oo[1]:
                        continue
                    arena.add((x, y))
    if 'tor' in ar:
        x0, y0, x1, y1 = ar['tor']
        arena = {c for c in arena if not (x0 <= c[0] <= x1 and y0 <= c[1] <= y1)}
    # Arena ragt ueber die noerdliche Sandwand: in ihrer Grundflaeche wird die Sandwand ausgespart
    arena_flaeche = set()
    if 'e' in ar:
        cx, cy, rx, ry = ar['e']
        arena_flaeche = {(x, y) for y in range(rows) for x in range(cols)
                         if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1}
    sw = lay.get('sandwand', {})
    if 'oben' in sw:
        vorher = np.array(img)
        sandwand_oben(L, sw['oben'], random.Random(4))
        ob = sw['oben']
        fu = (ob['kappe'][1] + 1) * T + ob['front']        # Fusslinie der Front
        if sw.get('rechts') and ob['x'][1] >= sw['rechts'][0]['x'][0] - 1 and sw['rechts'][0]['y'][0] <= ob['kappe'][1]:
            # Innenecke oben rechts: Sand in der Ecke (nur wenn sich die Waende dort wirklich treffen)
            sx = sw['rechts'][0]['x'][0] * T + 5 + seiten_kante(fu)
            eck_verwehung(L, sx, fu + 1, 30, 14, links=True)
        nachher = np.array(img)
        for (x, y) in arena_flaeche:
            if y * T < fu + 4:
                nachher[y * T:(y + 1) * T, x * T:(x + 1) * T] = vorher[y * T:(y + 1) * T, x * T:(x + 1) * T]
        img.paste(Image.fromarray(nachher))
        L = ind.Leinwand(img)
    mauer_zeichnen(L, arena, SANDSTEIN, 24)
    if 'oben' in sw and arena_flaeche:
        arena_uebergang(img, L, arena, sw['oben'], arena_flaeche)
        L = ind.Leinwand(img)
    for seg in sw.get('rechts', []):
        sandwand_seite(L, seg, random.Random(6))
    ga = lay.get('garten')
    garten = set()
    if ga:
        cx, cy, rx, ry = ga['e']
        for y in range(rows):
            for x in range(cols):
                d = ((x + 0.5 - cx - 0.5) / rx) ** 2 + ((y + 0.5 - cy - 0.5) / ry) ** 2
                dinnen = ((x + 0.5 - cx - 0.5) / (rx - ga['dicke'])) ** 2 + ((y + 0.5 - cy - 0.5) / (ry - ga['dicke'])) ** 2
                if d <= 1 and dinnen > 1 and not (ga['oeffnung'][0] <= x <= ga['oeffnung'][1] and y > cy):
                    garten.add((x, y))
        mauer_zeichnen(L, garten, ZIEGEL, 14)
    if speichern:
        img.save(os.path.join(KARTE, 'terrain_basis.png'))

    # Bodenmaske fuer Schatten: nicht auf Mauerkappen/-fronten, nicht auf Duenen
    boden = np.ones((rows * T, cols * T), np.float32)
    for y in range(rows):                                  # nie auf Wasser (Regel 7)
        for x in range(cols):
            if cls[y][x] in 'xm':
                boden[y * T:(y + 1) * T, x * T:(x + 1) * T] = 0
    if meer_region.any():
        boden[wasser_details.MEER_MASKE[0]] = 0
    for (x, y) in arena:
        boden[max(0, y * T - 24):(y + 1) * T, x * T:(x + 1) * T] = 0
    for (x, y) in garten:
        boden[max(0, y * T - 14):(y + 1) * T, x * T:(x + 1) * T] = 0
    if 'oben' in sw:
        boden[:(sw['oben']['kappe'][1] + 1) * T + sw['oben']['front'], :] = 0
        for (x, y) in arena_flaeche:
            boden[y * T:(y + 1) * T, x * T:(x + 1) * T] = 1
        for (x, y) in arena:
            boden[max(0, y * T - 24):(y + 1) * T, x * T:(x + 1) * T] = 0
    for seg in sw.get('rechts', []):                       # exakt entlang der welligen Innenkante
        for yy in range(seg['y'][0] * T, (seg['y'][1] + 1) * T):
            boden[yy, seg['x'][0] * T + 5 + seiten_kante(yy) - 1:] = 0

    # --- 5. Objekte
    pf = os.path.join(OBJ, 'platzierung.json')
    objs = []
    if os.path.exists(pf):
        objs = sorted(json.load(open(pf)), key=lambda o: (o.get('ebene', 1), o['y'] + o.get('fuss', 0)))
        cache = {}
        for o in objs:
            if o['datei'] not in cache:
                cache[o['datei']] = Image.open(os.path.join(OBJ, o['datei'])).convert('RGBA')
        if 'unten' in sw:                                 # hinter/an der Vorderkante: kein Schatten,
            kamm = sw['unten']['fuss'] * T - 16               # sonst lugt er unter der Sandkante hervor
            for o in objs:
                if o['y'] + o['fuss'] > kamm - 14:
                    o['ohne_schatten'] = True
        objekte_zeichnen(img, objs, cache, boden, frame)
    if objs:                                              # kleine Tiere im Sand
        viecher_zeichnen(img, viecher_positionen(objs, cols, rows, cls), frame or 0)
    if 'unten' in sw:                                     # Vordergrund ueber Objekten und Schatten
        Lv = ind.Leinwand(img)
        rx_ = None
        if sw.get('rechts'):
            sx0 = sw['rechts'][-1]['x'][0] * T
            rx_ = lambda y: sx0 + 5 + seiten_kante(y)
        sandwand_vorne(Lv, sw['unten'], random.Random(5), rx_)
    if frame is not None:
        animieren(img, objs, frame)
        return img
    if speichern:
        img.save(os.path.join(KARTE, 'terrain.png'))
        json.dump({'tile_size': T, 'cols': cols, 'rows': rows, 'klassen': [''.join(r_) for r_ in cls],
                   'arena': sorted(arena), 'garten': sorted(garten)},
                  open(os.path.join(KARTE, 'tilemap.json'), 'w'))
    print('Karte 03 %dx%d gebaut' % (cols, rows))
    return img


def objekte_zeichnen(img, objs, cache, boden, frame):
    """Kantenintegration (Sand angeweht, Steinchen), Fussschatten + Schlagschatten (nur auf Boden),
    dann die Sprites (mit Wind fuer Palmen)."""
    L = ind.Leinwand(img)
    rk = random.Random(11)
    for o in objs:
        if o.get('ohne_fuss'):
            continue
        a = np.array(cache[o['datei']].getchannel('A')) >= 200
        zeilen = np.nonzero(a.any(axis=1))[0]
        if len(zeilen) == 0:
            continue
        for xi in np.nonzero(a.any(axis=0))[0]:
            yu = int(np.nonzero(a[:, xi])[0].max())
            if yu < zeilen.max() - 4:
                continue
            X, Y = o['x'] + int(xi), o['y'] + yu
            for d, f in ((1, 0.7), (2, 0.84)):
                L.neutral(X, Y + d, f, waerme=4)
            if rk.random() < 0.25:                         # angewehter Sand vor der Kante
                L.p(X + rk.randint(-1, 1), Y + rk.randint(0, 2), ind.rgb('#e8cf98') if rk.random() < 0.5 else ind.rgb('#d8b87e'))
    # Schatten (Licht oben links): Kontaktschatten genau unter der Auflageflaeche, Schlagschatten der
    # Silhouette nach rechts unten, der mit der Hoehe heller wird. Zwei klare Stufen statt Verlauf.
    kern = np.zeros(boden.shape, np.float32)
    wurf = np.zeros(boden.shape, np.float32)
    for o in objs:
        sp = cache[o['datei']]
        a = np.array(sp.getchannel('A')) >= 200
        zeilen = np.nonzero(a.any(axis=1))[0]
        if o.get('ohne_schatten'):
            continue
        if o.get('liegend') and len(zeilen):                 # liegend: flacher Schatten der ganzen Form
            ys_, xs_ = np.nonzero(a)
            for d_, w_ in ((2, 0.83), (1, 1.0)):
                Y_, X_ = ys_ + o['y'] + d_, xs_ + o['x'] + d_
                ok_ = (Y_ >= 0) & (Y_ < wurf.shape[0]) & (X_ >= 0) & (X_ < wurf.shape[1])
                wurf[Y_[ok_], X_[ok_]] = np.maximum(wurf[Y_[ok_], X_[ok_]], w_)
            continue
        if len(zeilen) < 4:
            continue
        zu = zeilen.max()
        fuss_y = o['y'] + zu
        fuss = np.nonzero(a[max(0, zu - 3):zu + 1].any(axis=0))[0]       # Auflageflaeche
        if len(fuss):
            fx0, fx1 = o['x'] + fuss.min(), o['x'] + fuss.max()
            for yy in range(fuss_y - 1, fuss_y + 3):
                if 0 <= yy < kern.shape[0]:
                    ein = (yy - fuss_y + 1) if yy > fuss_y else 0
                    kern[yy, max(0, fx0 - 1 + ein):max(0, min(kern.shape[1], fx1 + 3 - ein))] = 1
        hoehe = max(1, zu - zeilen.min())
        for zi in zeilen:
            k = zu - zi
            ty = int(fuss_y + k * 0.24)
            dx = int(1 + k * 0.45)
            if 0 <= ty < wurf.shape[0]:
                xs = np.nonzero(a[zi])[0] + o['x'] + dx
                xs = xs[(xs >= 0) & (xs < wurf.shape[1])]
                wurf[ty, xs] = np.maximum(wurf[ty, xs], 1.0 - 0.35 * k / hoehe)
    wurf = np.array(Image.fromarray((wurf * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3))) / 255.0
    sch = np.where(kern > 0, 92, np.where(wurf > 0.82, 64, np.where(wurf > 0, 50, 0))).astype(np.float32)
    sch = (sch * boden).astype(np.uint8)
    dunkel = Image.new('RGBA', img.size, (64, 36, 30, 255))
    dunkel.putalpha(Image.fromarray(sch))
    img.alpha_composite(dunkel)
    for o in objs:
        sp = cache[o['datei']]
        if frame is not None:
            anim = o.get('anim')
            if o.get('proz'):
                sp = kp.PROZ[o['proz']](frame)
            elif anim == 'wehen':
                sp = kb.wehen(sp, kb.wind(frame, o['x']))
            elif anim == 'flagge':                         # nur der Stoff weht, Stange bleibt ruhig (Karte-04-Regel)
                import karte04_bauen as _k4
                sp = _k4.fahne_wehen(sp, frame, o['x'] * 0.37)
            elif anim == 'kaktus':
                sp = kaktus(sp, frame, o['x'], o['y'])
            if o.get('dreh'):
                sp = schuesseln_drehen(sp, frame, o['x'] + o['y'], o['basis'])
        img.alpha_composite(sp, (o['x'], o['y']))
        if o['datei'].endswith('_sand.png') and not o.get('ohne_fuss'):
            sandverwehung(img, o, cache[o['datei']])


_MAST_CACHE = {}


def schuesseln_drehen(sp, frame, phase, basis):
    """Funkmast: Schuesseln werden aus dem Sprite genommen (Gitter dahinter ergaenzt) und jedes Frame neu
    gezeichnet; sie schwenken weich von links nach rechts (+-45 Grad), jede mit eigenem Versatz."""
    if basis not in kp.SCHUESSELN:
        return sp
    key = (basis, sp.size)
    if key not in _MAST_CACHE:
        roh = Image.open(os.path.join(OBJ, basis + '.png')).convert('RGBA')
        ra, va = np.array(roh.getchannel('A')) > 0, np.array(sp.getchannel('A')) > 0
        best, off = -1, (0, 0)
        for oy in range(0, sp.height - roh.height + 1):
            for ox in range(0, sp.width - roh.width + 1):
                sc = (ra & va[oy:oy + roh.height, ox:ox + roh.width]).sum()
                if sc > best:
                    best, off = sc, (ox, oy)
        _MAST_CACHE[key] = (kp.mast_ohne_schuesseln(sp, basis, *off), off)
    kahl, (ox, oy) = _MAST_CACHE[key]
    out = kahl.copy()
    Lm = ind.Leinwand(out)
    for i, (cx, cy, rx, ry, seite) in enumerate(kp.SCHUESSELN[basis]['schalen']):
        gier = math.radians(45) * math.sin(2 * math.pi * frame / N_FRAMES + phase / 37.0 + i * 1.7)
        kp.schale(Lm, cx + ox, cy + oy, rx, ry, gier, seite)
    return out


def flagge(sp, frame, x0):
    """Fahnentuch weht: Zeilen unterhalb der Aufhaengung wandern sinusfoermig seitlich, unten staerker."""
    a = np.array(sp.getchannel('A')) > 0
    breit = np.nonzero(a.sum(axis=1) >= 8)[0]
    if len(breit) < 6:
        return sp
    oben, unten = breit.min() + 3, breit.max()
    out = sp.copy()
    out.paste((0, 0, 0, 0), (0, oben, sp.width, unten + 1))
    for y in range(oben, unten + 1):
        t = (y - oben) / max(1, unten - oben)
        d = round(2.2 * t * math.sin(2 * math.pi * frame / N_FRAMES * 2 - y / 4.0 + x0 / 50.0))
        out.alpha_composite(sp.crop((0, y, sp.width, y + 1)), (d, y)) if d >= 0 else \
            out.alpha_composite(sp.crop((-d, y, sp.width, y + 1)), (0, y))
    return out


def kaktus(sp, frame, x0, y0):
    """Kaktus: sehr leichtes Wiegen (1 px an der Spitze, selten), Blueten pulsieren rosa auf,
    ab und zu glitzert ein Tautropfen auf einem Dorn."""
    ph = 2 * math.pi * (frame / N_FRAMES - x0 / 300.0)
    v = 1 if math.sin(ph) > 0.55 else 0
    out = kb.wehen(sp, v) if v else sp.copy()
    a = np.array(out).astype(np.int16)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    bl = (a[..., 3] > 0) & (r > g + 50) & (b > g + 15)
    if bl.any():
        f = 0.18 * (0.5 + 0.5 * math.sin(ph * 2 + y0 / 40.0))
        a[bl, :3] = np.clip(a[bl, :3] + (255 - a[bl, :3]) * f, 0, 255)
    h = (x0 * 7 + y0 * 3) % N_FRAMES
    if frame % N_FRAMES in (h, (h + 1) % N_FRAMES):
        ys, xs = np.nonzero(a[..., 3] > 200)
        if len(ys):
            i = (x0 + y0) % len(ys)
            oben = ys < ys.min() + max(3, (ys.max() - ys.min()) // 2)
            if oben.any():
                k = np.nonzero(oben)[0][(x0 * 3 + y0) % oben.sum()]
                a[ys[k], xs[k], :3] = (255, 255, 240)
    return Image.fromarray(a.astype(np.uint8))


import basis_kacheln as _bk
SAND_V = [_bk.RGB[k] + (255,) for k in ('s0', 's1', 's2', 's2', 's3')]   # exakt die Bodensand-Toene


def sandverwehung(img, o, sp):
    """Objekt steckt im Sand: an der Auflagekante liegt ein kleiner Sandwall ueber dem Objektfuss
    (2-5 px, wellig, Licht oben), seitlich auslaufend, auf der Leeseite (rechts) eine Windfahne."""
    a = np.array(sp.getchannel('A')) >= 200
    spalten = np.nonzero(a.any(axis=0))[0]
    if len(spalten) == 0:
        return
    tief = int(np.nonzero(a.any(axis=1))[0].max())
    rs = random.Random(o['x'] * 7 + o['y'])
    px = img.load()
    W, H = img.size
    def setz(x, y, c):
        if 0 <= x < W and 0 <= y < H:
            px[x, y] = c
    kontakt = [x for x in spalten if np.nonzero(a[:, x])[0].max() >= tief - 3]
    if not kontakt:
        return
    k0, k1 = min(kontakt), max(kontakt)
    breit = k1 - k0 + 1
    hmax = 3 + min(4, breit // 9)
    for xi in range(k0 - 3, k1 + 4 + min(10, breit // 3)):
        if xi < k0:
            h = max(0, hmax - (k0 - xi))                   # links auslaufend
        elif xi > k1:
            h = max(0, int(hmax - (xi - k1) * 0.5))        # rechts Windfahne, flacher und laenger
        else:
            h = hmax + int(1.2 * math.sin(xi * 0.9 + o['x']))
        X = o['x'] + xi
        Yb = o['y'] + tief + 1
        for d in range(h):
            y = Yb - d
            c = SAND_V[4] if d == h - 1 and xi <= k1 else SAND_V[2] if d > 0 else SAND_V[1]
            setz(X, y, c)
        if h > 0 and rs.random() < 0.25:
            setz(X, Yb - h - 1, SAND_V[2])             # einzelne Koerner auf dem Objektfuss


# ---------------------------------------------------------------- kleine Wuestentiere (animiert)
VIECH = {
    'kaefer': {'farben': {'k': '#141c28', 'b': '#2a3a5a', 'h': '#7ff0f5', 'l': '#141c28'},
               'bild': [["l.l.l..", ".kkkk..", "kbhbbkk", ".kkkk..", "l.l.l.."],
                        [".l.l.l.", ".kkkk..", "kbhbbkk", ".kkkk..", ".l.l.l."]]},
    'eidechse': {'farben': {'k': '#4a3a20', 'b': '#8a7a3a', 'h': '#c8b060', 'l': '#6a5a30', 't': '#7a6a34'},
                 'bild': [["...l....l..", "t..kbbbbhkk", ".tkbbbbbbk.", "....l....l."],
                          ["....l....l.", "t..kbbbbhkk", ".tkbbbbbbk.", "...l....l.."]]},
    'skorpion': {'farben': {'k': '#4a2a14', 'b': '#9a5a2a', 'c': '#b8743a', 'l': '#6a3a1c'},
                 'bild': [["kk.......", "..k.l.l.cc", "..kbbbbbkc", "....l.l.cc"],
                          ["kk.......", "..k..l.lcc", "..kbbbbbkc", ".....l.lcc"]]},
}


def viecher_positionen(objs, cols, rows, cls, anzahl=11, seed=9):
    """Freie Sandstellen (abseits von Objekten, Wegen und Mauern) fuer die kleinen Tiere."""
    rnd = random.Random(seed)
    boxen = []
    for o in objs:
        sp = Image.open(os.path.join(OBJ, o['datei']))
        boxen.append((o['x'] - 12, o['y'] - 6, o['x'] + sp.width + 12, o['y'] + sp.height + 8))
    pos = []
    arten = ['kaefer', 'eidechse', 'skorpion']
    for _ in range(4000):
        if len(pos) >= anzahl:
            break
        x, y = rnd.randrange(8, cols - 8), rnd.randrange(8, rows - 8)
        if any(cls[y + dy][x + dx] != 's' for dx in (-1, 0, 1) for dy in (-1, 0, 1)):
            continue
        px_, py_ = x * T + 8, y * T + 8
        if any(b[0] - 20 < px_ < b[2] + 20 and b[1] - 12 < py_ < b[3] + 12 for b in boxen):
            continue
        if any(abs(px_ - q[0]) + abs(py_ - q[1]) < 140 for q in pos):
            continue
        pos.append((px_, py_, arten[len(pos) % 3], rnd.random()))
    return pos


def viecher_zeichnen(img, positionen, frame):
    px = img.load()
    W, H = img.size
    for i, (bx, by, art, ph) in enumerate(positionen):
        t = (frame / N_FRAMES + ph) % 1.0
        if art == 'kaefer':                                # langsam im Kreis
            w = 2 * math.pi * t
            x, y = bx + 8 * math.cos(w), by + 4 * math.sin(w)
            vx = -math.sin(w)
        elif art == 'eidechse':                            # flitzt hin und her, mit Pausen
            s_ = min(1, max(0, (t % 0.5) * 2 * 1.6 - 0.3))
            s_ = s_ * s_ * (3 - 2 * s_)
            x = bx - 10 + 20 * (s_ if t < 0.5 else 1 - s_)
            y = by
            vx = 1 if t < 0.5 else -1
        else:                                              # Skorpion: kleine Seitwaertsschritte
            x = bx + 5 * math.sin(2 * math.pi * t)
            y = by + 1.5 * math.sin(4 * math.pi * t)
            vx = math.cos(2 * math.pi * t)
        v = VIECH[art]
        bild = v['bild'][(frame // 1) % 2] if abs(vx) > 0.15 or art == 'kaefer' else v['bild'][0]
        if vx < 0:
            bild = [z[::-1] for z in bild]
        hb, wb = len(bild), max(len(z) for z in bild)
        x0, y0 = int(round(x - wb / 2)), int(round(y - hb / 2))
        # Spur im Sand (ein paar Tupfen hinter dem Tier)
        for k in range(1, 4):
            tx = int(x - (vx if vx else 1) * (wb / 2 + 2 * k))
            ty = int(y + (1 if k % 2 else -1))
            if 0 <= tx < W and 0 <= ty < H:
                r_, g_, b_, a_ = px[tx, ty]
                px[tx, ty] = (int(r_ * 0.88), int(g_ * 0.86), int(b_ * 0.82), a_)
        # Schatten
        for xx in range(x0 + 1, x0 + wb):
            yy = y0 + hb
            if 0 <= xx < W and 0 <= yy < H:
                r_, g_, b_, a_ = px[xx, yy]
                px[xx, yy] = (int(r_ * 0.8), int(g_ * 0.78), int(b_ * 0.75), a_)
        for dy, z in enumerate(bild):
            for dx, ch in enumerate(z):
                if ch == '.':
                    continue
                xx, yy = x0 + dx, y0 + dy
                if 0 <= xx < W and 0 <= yy < H:
                    px[xx, yy] = ind.rgb(v['farben'][ch])


FEUER = [(0xc8, 0x3a, 0x1e), (0xe8, 0x70, 0x2a), (0xf5, 0xb0, 0x42), (0xff, 0xf2, 0xa0)]


def animieren(img, objs, frame):
    """Feuer (Fackeln, Lagerfeuer) flackert mit Lichtschein, Kristall/Leuchten pulsieren, Antennen
    blinken, Musiknoten steigen von der Buehne auf."""
    a = np.array(img)
    puls = 0.5 + 0.5 * math.sin(frame / N_FRAMES * 2 * math.pi)
    glut = Image.new('RGBA', img.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glut)
    for i, o in enumerate(objs):
        anim = o.get('anim')
        if o.get('proz') in ('box_monitor', 'buehne'):            # Bass: Druckwellen vor den Membranen
            ph = frame % 4
            if ph < 3:
                for (bx, by) in kp.PROZ[o['proz']](0).info.get('bass', [])[:2]:
                    r = (9 if o['proz'] == 'box_monitor' else 15) + ph * 6
                    al = (120, 75, 35)[ph]
                    cx, cy = o['x'] + bx, o['y'] + by
                    gd.ellipse((cx - r, cy - r * 0.8, cx + r, cy + r * 0.8), outline=(255, 210, 245, al))
        if anim == 'schall':                                      # Schallboegen aus beiden Trichtern
            spr = Image.open(os.path.join(OBJ, o['datei'])).convert('RGBA')
            al = np.array(spr.getchannel('A')) > 0
            oben = al[:int(spr.height * 0.35)]
            spalten = np.nonzero(oben.any(axis=0))[0]
            if len(spalten):
                for seite, sx in ((-1, spalten.min()), (1, spalten.max())):
                    zy = np.nonzero(oben[:, sx])[0].mean()
                    cx, cy = o['x'] + sx, o['y'] + zy
                    for k in range(3):
                        t = ((frame + k * 5 + i * 3) % 15) / 15
                        r = 4 + t * 16
                        a_ = int(235 * (1 - t) ** 0.8)
                        box = (cx - r, cy - r * 0.9, cx + r, cy + r * 0.9)
                        if seite < 0:
                            gd.arc(box, 135, 225, fill=(255, 250, 235, a_), width=2 if t < 0.5 else 1)
                        else:
                            gd.arc(box, -45, 45, fill=(255, 250, 235, a_), width=2 if t < 0.5 else 1)
        if anim not in ('feuer', 'leuchten', 'blinken', 'musik'):
            continue
        sp = Image.open(os.path.join(OBJ, o['datei']))
        x0, y0 = max(0, o['x']), max(0, o['y'])
        x1, y1 = min(a.shape[1], o['x'] + sp.width), min(a.shape[0], o['y'] + sp.height)
        reg = a[y0:y1, x0:x1]
        rr = reg[..., :3].astype(np.int16)
        yy, xx = np.mgrid[y0:y1, x0:x1]
        if anim == 'feuer':
            m_all = np.zeros(rr.shape[:2], bool)
            stufe = (((yy * 2 + xx * 3 + frame * 5) % 7) > 3).astype(int) * 2 - 1
            for k, c in enumerate(FEUER):
                m = (rr == c).all(axis=2)
                m_all |= m
                ziel = np.clip(k + stufe, 0, 3)
                for j, cz in enumerate(FEUER):
                    reg[m & (ziel == j), :3] = cz
            ys, xs = np.nonzero(m_all)
            if len(xs):
                fx, fy = x0 + xs.mean(), y0 + ys.mean()
                fl = 0.75 + 0.25 * math.sin(frame * 2.3 + i)
                for rad, al in ((18, 30), (11, 44), (6, 60)):
                    gd.ellipse((fx - rad, fy - rad * 0.6, fx + rad, fy + rad * 0.6), fill=(255, 160, 70, int(al * fl)))
        elif anim == 'leuchten':
            m = ((rr[..., 2] > 180) & (rr[..., 1] > 150) & (rr[..., 0] < 160))
            reg[m, :3] = np.clip(reg[m, :3] * (0.75 + 0.45 * puls), 0, 255).astype(np.uint8)
        elif anim == 'blinken':
            m = ((rr[..., 0] > 170) & (rr[..., 1] < 120)) | ((rr[..., 2] > 200) & (rr[..., 0] < 140))
            if (frame + i * 3) % 8 < 3:
                reg[m, :3] = (reg[m, :3] * 0.45).astype(np.uint8)
        a[y0:y1, x0:x1] = reg
        if anim == 'musik':
            rnd = random.Random(i)
            for k in range(4):
                t = ((frame + k * 4) % 16) / 16
                nx = o['x'] + sp.width * (0.2 + 0.6 * ((k * 37 + i) % 10) / 10) + math.sin(t * 6 + k) * 3
                ny = o['y'] + 6 - t * 30
                farbe = (122, 106, 200, int(255 * (1 - t)))
                gd.rectangle((nx, ny, nx + 1, ny + 3), fill=farbe)
                gd.rectangle((nx - 2, ny + 3, nx + 1, ny + 4), fill=farbe)
                gd.point((nx + 2, ny), fill=farbe)
    img.paste(Image.fromarray(a))
    img.alpha_composite(glut)


def main():
    bauen()


if __name__ == '__main__':
    main()
