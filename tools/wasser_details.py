"""Unterwasser-Details fuer Karte 01: Felsen (unter Wasser / herausragend), Algen, terrassiertes Meer.

Logik der Tiefe:
  - Jeder Fels liegt mit seinem ganzen Umriss (plus Abstand) auf GENAU einer Stufe, nie ueber einer Kante.
  - Herausragende Felsen: kleine nur auf der flachsten Stufe, grosse (zwei Stufen hoch) auf der naechst
    tieferen; auf noch tieferen Stufen liegen Felsen nur unter Wasser.
  - Unterwasser-Teile werden mit der Wasserfarbe der Stufe getoent (tiefer = dunkler, blauer).

Meer (vom Strand nach Sueden): Sand | Flachwasser | Schaumkante + tieferes Wasser | Stufe | Platz | Stufe |
Platz | Tiefsee. Die Stufen folgen der Kuestenlinie (Abstandsfeld), Fronten zeigen zum Betrachter.
"""
import math, os, random
import numpy as np
from PIL import Image, ImageFilter

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
BASIS = os.path.join(ROOT, 'assets', 'basis')
N_FRAMES = 16
H = lambda h: np.array(tuple(int(h[i:i + 2], 16) for i in (1, 3, 5)), np.float32)
STEIN = [H(c) for c in ('#363e4c', '#4e5868', '#68727f', '#848e9c', '#a6aeb8', '#cad0d6')]
SCHAUM = H('#f2faff')
ALGE = [H(c) for c in ('#1e5a44', '#2c7a52', '#43a05e', '#6cc472')]


# ---------------------------------------------------------------- Felsen
def fels_maske(rx, ry, seed):
    """Unregelmaessiger, gerundeter Felsumriss (bool-Array) und Hilfsfelder u, v (-1..1)."""
    rs = random.Random(seed)
    w, h = int(2 * rx + 3), int(2 * ry + 3)
    cx, cy = w / 2, h / 2
    ph = [rs.random() * 6.28 for _ in range(3)]
    yy, xx = np.mgrid[0:h, 0:w]
    ang = np.arctan2(yy - cy, xx - cx)
    r = 1 + 0.12 * np.sin(3 * ang + ph[0]) + 0.08 * np.sin(5 * ang + ph[1]) + 0.05 * np.sin(7 * ang + ph[2])
    d = ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2
    m = d <= r ** 2
    return m, (xx - cx) / rx, (yy - cy) / ry


def passt(zone, cx, cy, rx, ry, rand=4):
    """Liegt der Fels (Ellipse + rand) vollstaendig in der Zone?"""
    Hh, W = zone.shape
    x0, x1, y0, y1 = int(cx - rx - rand), int(cx + rx + rand), int(cy - ry - rand), int(cy + ry + rand)
    if x0 < 0 or y0 < 0 or x1 >= W or y1 >= Hh:
        return False
    return bool(zone[y0:y1 + 1, x0:x1 + 1].all())


def fels(a, cx, cy, rx, ry, wasser, tiefe, raus, hoehe, frame, seed):
    """Fels zeichnen. wasser: Wasserfarbe der Stufe (RGB), tiefe 0..1 (Toenung unter Wasser).
    raus: ragt heraus (hoehe px ueber der Wasserlinie), sonst komplett unter Wasser."""
    m, u, v = fels_maske(rx, ry + (hoehe / 2 if raus else 0), seed)
    h, w = m.shape
    X0, Y0 = int(cx - w / 2), int(cy + ry - h + 1)
    Hh, W = a.shape[:2]
    lin = 0.35 if raus else 99.0                      # Wasserlinie (in v) - darunter ist der Fels nass/unter Wasser
    # Schatten / Dunkelzone im Wasser rechts unten
    for y in range(h):
        for x in range(w):
            if m[y, x]:
                X, Y = X0 + x + 2, Y0 + y + 2
                if 0 <= X < W and 0 <= Y < Hh and not (0 <= x + 2 < w and 0 <= y + 2 < h and m[y + 2, x + 2]):
                    a[Y, X] = a[Y, X] * 0.8
    rs = random.Random(seed)
    for y in range(h):
        for x in range(w):
            if not m[y, x]:
                continue
            X, Y = X0 + x, Y0 + y
            if not (0 <= X < W and 0 <= Y < Hh):
                continue
            uu, vv = u[y, x], v[y, x]
            rand_ = not (m[max(0, y - 1), x] and m[min(h - 1, y + 1), x] and m[y, max(0, x - 1)] and m[y, min(w - 1, x + 1)])
            t = uu + vv
            i = 4 if t < -0.9 else 3 if t < -0.2 else 2 if t < 0.5 else 1
            if rand_:
                i = 0 if t > -0.3 else 1
            if (x * 7 + y * 5 + seed) % 23 == 0 and not rand_:
                i = max(0, i - 1)                           # Riss/Pore
            c = STEIN[i].copy()
            unter = (not raus) or vv > lin
            if unter:
                c = c * (1 - 0.55 - 0.25 * tiefe) + wasser * (0.55 + 0.25 * tiefe)
            elif raus and vv > lin - 0.22:
                c = c * 0.72                                # nasser Streifen ueber der Wasserlinie
            a[Y, X] = np.clip(c, 0, 255)
    if raus:                                                # Schaumring an der Wasserlinie (Luecken wandern)
        for y in range(h):
            for x in range(w):
                if not m[y, x]:
                    continue
                vv = v[y, x]
                if abs(vv - lin) < 0.09 or (vv > lin and not m[min(h - 1, y + 1), x]):
                    X, Y = X0 + x, Y0 + y
                    if 0 <= X < W and 0 <= Y < Hh and (x + (frame or 0)) % 5 != 0:
                        a[Y, X] = SCHAUM
        for k in range(-2, w + 2):                          # Schaum seitlich auf dem Wasser
            X = X0 + k
            Y = int(Y0 + h / 2 + lin * h / 2) + (1 if (k + (frame or 0)) % 4 < 2 else 2)
            if 0 <= X < W and 0 <= Y < Hh and (k < 1 or k > w - 2) and (k + (frame or 0)) % 3:
                a[Y, X] = a[Y, X] * 0.4 + SCHAUM * 0.6


def felsen_setzen(a, zonen, wasserfarben, tiefen, regeln, frame, seed, meiden=None, anzahl=None):
    """zonen: Liste bool-Masken (flach -> tief). regeln[i]: Liste (art, rx, ry, hoehe) erlaubter Felsen je Zone.
    anzahl[i]: Zielanzahl je Zone. Platziert deterministisch auf einem gestreuten Raster."""
    rs = random.Random(seed)
    Hh, W = zonen[0].shape
    belegt = np.zeros((Hh, W), bool)
    gesetzt = []
    for i, zone in enumerate(zonen):
        z = zone & ~(meiden if meiden is not None else np.zeros_like(zone))
        ys, xs = np.nonzero(z)
        if not len(ys) or not regeln[i]:
            continue
        ziel = anzahl[i] if anzahl else max(1, len(ys) // 4000)
        versuche = 0
        n = 0
        while n < ziel and versuche < ziel * 60:
            versuche += 1
            k = rs.randrange(len(ys))
            cx, cy = int(xs[k]), int(ys[k])
            art, rx, ry, hoehe = rs.choice(regeln[i])
            rx_, ry_ = rx * rs.uniform(0.85, 1.15), ry * rs.uniform(0.85, 1.15)
            ry_eff = ry_ + (hoehe / 2 if art == 'raus' else 0)
            if not passt(z, cx, cy, rx_, ry_, 2):              # Grundflaeche muss auf einer Stufe liegen
                continue
            if belegt[max(0, cy - int(ry_ + hoehe) - 6):cy + int(ry_) + 7, max(0, cx - int(rx_) - 6):cx + int(rx_) + 7].any():
                continue
            belegt[max(0, cy - int(ry_ + hoehe)):cy + int(ry_) + 1, max(0, cx - int(rx_)):cx + int(rx_) + 1] = True
            gesetzt.append((i, art, cx, cy, rx_, ry_, hoehe, rs.randrange(10000)))
            n += 1
    for (i, art, cx, cy, rx, ry, hoehe, s) in sorted(gesetzt, key=lambda g: g[3]):
        fels(a, cx, cy, rx, ry, wasserfarben[i], tiefen[i], art == 'raus', hoehe, frame, s)
    return belegt


# ---------------------------------------------------------------- Algen
def algen(a, zone, wasser, tiefe, dichte, frame, seed, meiden=None):
    """Algenbueschel: 3-5 wellige Halme, wiegen sich (16 Frames), unter Wasser getoent."""
    rs = random.Random(seed)
    Hh, W = zone.shape
    z = zone & ~(meiden if meiden is not None else np.zeros_like(zone))
    ys, xs = np.nonzero(z)
    if not len(ys):
        return
    for _ in range(int(len(ys) * dichte)):
        k = rs.randrange(len(ys))
        bx, by = int(xs[k]), int(ys[k])
        if not passt(z, bx, by - 6, 5, 8, 1):
            continue
        for s in range(rs.randint(3, 5)):
            hx = bx + rs.randint(-4, 4)
            laenge = rs.randint(9, 18)
            ph = rs.random() * 6.28
            for j in range(laenge):
                t = j / laenge
                x = int(round(hx + 2.2 * t * math.sin(2 * math.pi * (frame or 0) / N_FRAMES + ph + j * 0.5)))
                y = by - j
                if 0 <= x < W and 0 <= y < Hh:
                    c = ALGE[1] if j < laenge * 0.4 else ALGE[2]
                    if j == laenge - 1:
                        c = ALGE[3]
                    if (x + y) % 3 == 0:
                        c = ALGE[0]
                    c = c * (1 - 0.35 - 0.3 * tiefe) + wasser * (0.35 + 0.3 * tiefe)
                    a[y, x] = np.clip(c, 0, 255)
                    if j % 3 == 1 and 0 <= x + 1 < W:
                        a[y, x + 1] = np.clip(c * 0.9, 0, 255)


# ---------------------------------------------------------------- Meer
def _kacheln(name, Hh, W):
    ks = [np.array(Image.open(os.path.join(BASIS, '%s_%d.png' % (name, v))).convert('RGB')).astype(np.float32) for v in range(5)]
    t = np.zeros((Hh, W, 3), np.float32)
    for y in range(0, Hh, 16):
        for x in range(0, W, 16):
            t[y:y + 16, x:x + 16] = ks[((x // 16) * 7 + (y // 16) * 13) % 5][:min(16, Hh - y), :min(16, W - x)]
    return t


# Abstand vom Strand (px): Flachwasser | Schaum | Mittel | Stufe 1 | Platz | Stufe 2 | Platz | Tiefsee
FLACH, SCHAUM_D, STUFE1, STUFE2 = 24, (22, 26), 68, 138
WAND = 10
FARBEN = [H('#5fcfd6'), H('#38a8cc'), H('#2a7cbc'), H('#1d58a0')]   # Wasser je Zone (flach -> tief)
MISCH = [0.45, 0.62, 0.78, 0.9]                                  # Anteil Wasserfarbe ueber dem Grund


def meer_terrassen(img, region, frame=None, meiden=None):
    a = np.array(img.convert('RGB')).astype(np.float32)
    Hh, W = a.shape[:2]
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    roh = region & (b > r + 40) & (b > g + 10)
    m = np.array(Image.fromarray((roh * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2.5))) > 120
    m &= region
    if not m.any():
        return img
    # Abstandsfeld zum Land (halbe Aufloesung, dann weich hochskaliert + leichte Welligkeit)
    klein = Image.fromarray(((~m) * 255).astype(np.uint8)).resize((W // 2, Hh // 2), Image.NEAREST)
    dist = np.full((Hh // 2, W // 2), 999.0, np.float32)
    k = np.array(klein) > 0
    dist[k] = 0
    for i in range(1, 200):
        k2 = np.array(Image.fromarray((k * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3))) > 0
        neu = k2 & ~k
        if not neu.any():
            break
        dist[neu] = i * 2
        k = k2
    d = np.array(Image.fromarray(dist).resize((W, Hh), Image.BILINEAR))
    yy, xx = np.mgrid[0:Hh, 0:W]
    d = d + 3.0 * np.sin(xx / 23.0) + 2.0 * np.sin(xx / 9.0 + yy / 31.0)
    d[~m] = -1
    sand = _kacheln('sand', Hh, W)
    meer = _kacheln('meer', Hh, W)
    z0 = m & (d < FLACH)
    z1 = m & (d >= FLACH) & (d < STUFE1)
    w1 = m & (d >= STUFE1) & (d < STUFE1 + WAND)
    z2 = m & (d >= STUFE1 + WAND) & (d < STUFE2)
    w2 = m & (d >= STUFE2) & (d < STUFE2 + WAND)
    z3 = m & (d >= STUFE2 + WAND)
    # Grund + Wasserfarbe
    a[z0] = sand[z0] * (1 - MISCH[0]) + FARBEN[0] * MISCH[0]
    a[z1] = sand[z1] * (1 - MISCH[1]) * 0.9 + FARBEN[1] * MISCH[1]
    a[z2] = meer[z2] * (1 - MISCH[2]) + FARBEN[2] * MISCH[2]
    a[z3] = meer[z3] * (1 - MISCH[3]) + FARBEN[3] * MISCH[3]
    # Stufenwaende (Front zeigt zum Betrachter / vom Strand weg): Lichtkante, Felsfuge, dunkler Fuss
    for wand, oben, unten, start in ((w1, FARBEN[1], FARBEN[2], STUFE1), (w2, FARBEN[2], FARBEN[3], STUFE2)):
        t = (d[wand] - start) / WAND
        basis = oben * 0.78
        c = basis[None, :] * (1 - 0.35 * t[:, None])
        a[wand] = c
        kante = wand & (d < start + 1.2)
        a[kante] = np.clip(oben * 1.35 + 20, 0, 255)
        fuge = wand & ((xx // 7) % 2 == 0) & (np.abs(d - start - WAND * 0.55) < 0.6)
        a[fuge] = oben * 0.55
        fuss = wand & (d >= start + WAND - 1.5)
        a[fuss] = unten * 0.65
    # Schatten unterhalb jeder Wand
    for start in (STUFE1 + WAND, STUFE2 + WAND):
        sch = m & (d >= start) & (d < start + 5)
        a[sch] = a[sch] * 0.82
    fr = frame or 0
    # Felsen + Algen (je Zone nach der Tiefenregel)
    zonen = [z0 & (d > 3), z1 & (d > FLACH + 5), z2, z3]
    tiefen = [0.0, 0.3, 0.6, 0.9]
    regeln = [[('raus', 7, 4, 6), ('raus', 6, 4, 5), ('raus', 8, 4, 6), ('unter', 6, 4, 0)],  # flach: kleine ragen heraus
              [('raus', 13, 8, 16), ('raus', 15, 9, 18), ('raus', 12, 7, 15), ('unter', 8, 5, 0)],  # gross = 2 Stufen hoch
              [('unter', 11, 7, 0), ('unter', 8, 5, 0), ('unter', 15, 9, 0)],    # tiefer: nur unter Wasser
              [('unter', 18, 11, 0)]]
    algen(a, z1 & (d > FLACH + 8), FARBEN[1], 0.2, 0.0004, fr, 11, meiden)
    algen(a, z2, FARBEN[2], 0.45, 0.0006, fr, 12, meiden)
    algen(a, z3 & (d < STUFE2 + 60), FARBEN[3], 0.8, 0.0002, fr, 13, meiden)
    felsen_setzen(a, zonen, FARBEN, tiefen, regeln, fr, 21, meiden, anzahl=[14, 12, 16, 6])
    # Schaumkante am Uebergang Flach -> tiefer (wellig, wandert) und Wellen am Strand
    welle = 1.8 * np.sin(xx / 11.0 + 2 * math.pi * fr / N_FRAMES) + 1.2 * np.sin(xx / 5.0 - 2 * math.pi * fr / N_FRAMES)
    schaum = m & (np.abs(d - (SCHAUM_D[0] + SCHAUM_D[1]) / 2 - welle) < 1.6) & (((xx + fr) // 3) % 5 != 0)
    a[schaum] = SCHAUM
    schaum2 = m & (np.abs(d - (SCHAUM_D[0] + SCHAUM_D[1]) / 2 - welle) < 2.6) & ~schaum
    a[schaum2] = a[schaum2] * 0.5 + SCHAUM * 0.5
    brandung = 2.5 + 2.0 * math.sin(2 * math.pi * fr / N_FRAMES)
    ufer = m & (np.abs(d - brandung) < 1.0) & (((xx + 2 * fr) // 4) % 4 != 0)
    a[ufer] = a[ufer] * 0.3 + SCHAUM * 0.7
    nass = ~m & region & (np.array(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(5))) > 0)
    a[nass] = a[nass] * 0.82                                       # nasser Sand an der Wasserlinie
    # Lichtstriche auf der Oberflaeche (ab Mittelwasser), wandern seitlich
    tiefw = m & (d > FLACH + 2)
    ys, xs = np.nonzero(tiefw)
    for y, x in zip(ys, xs):
        kx, ky = (x - fr) // 16, y // 16
        h = (kx * 73856093 ^ ky * 19349663) & 0xffff
        px_, py_ = (x - fr) % 16, y % 16
        sy, sx = h % 13 + 1, (h >> 8) % 11 + 1
        if py_ == sy and sx <= px_ < sx + 4:
            a[y, x] = np.clip(a[y, x] * 0.4 + H('#cfeeff') * 0.6, 0, 255)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert('RGBA')


# ---------------------------------------------------------------- Teich
def teich_details(a, stufen_masken, wasserfarbe, frame, meiden=None):
    """stufen_masken: [Ufer-/Flachzone, Stufe 1, Stufe 2] (ohne Kanten). Felsen nach Tiefenregel + Algen."""
    af = a.astype(np.float32)
    farben = [wasserfarbe * 1.0, wasserfarbe * 0.8, wasserfarbe * 0.64]
    regeln = [[('raus', 6, 4, 6), ('raus', 7, 4, 6), ('unter', 5, 3, 0)],
              [('raus', 10, 7, 13), ('raus', 11, 7, 14), ('unter', 7, 5, 0)],
              [('unter', 9, 6, 0), ('unter', 7, 4, 0)]]
    algen(af, stufen_masken[1], farben[1], 0.35, 0.0006, frame, 31, meiden)
    algen(af, stufen_masken[2], farben[2], 0.6, 0.0007, frame, 32, meiden)
    felsen_setzen(af, stufen_masken, farben, [0.0, 0.35, 0.65], regeln, frame, 41, meiden, anzahl=[6, 3, 4])
    return np.clip(af, 0, 255).astype(np.uint8)
