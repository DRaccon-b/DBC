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
MEER_MASKE = [None]     # zuletzt gezeichnete Meeresflaeche (fuer die Kollision)
FELSEN_PROTOKOLL = []
SPITZEN = []            # (x, y) aller trockenen Felspixel ueber der Wasserlinie (fuer die Verdeckungs-Ebene)   # (x0, y0, x1, y1, Wasserlinie y, raus) je gezeichnetem Fels
BRAUN = [H(c) for c in ('#2e1c12', '#4a2e1c', '#6a4328', '#8a5a36', '#ab7646', '#cf9a62', '#ebc28a')]


def passt(zone, cx, cy, rx, ry, rand=4):
    """Liegt die Grundflaeche (Ellipse + rand) vollstaendig in der Zone?"""
    Hh, W = zone.shape
    x0, x1, y0, y1 = int(cx - rx - rand), int(cx + rx + rand), int(cy - ry - rand), int(cy + ry + rand)
    if x0 < 0 or y0 < 0 or x1 >= W or y1 >= Hh:
        return False
    return bool(zone[y0:y1 + 1, x0:x1 + 1].all())


def fels(a, cx, cy, rx, ry, wasser, tiefe, raus, hoehe, frame, seed):
    """Spitzer brauner Fels (Stalagmit) mit Haupt- und Nebenspitzen. Grundflaeche = Ellipse (rx, ry) um
    (cx, cy) auf dem Grund. raus: ragt hoehe px aus dem Wasser (trocken oben, nasser Streifen, Schaumring);
    sonst komplett unter Wasser (je nach Tiefe mit der Wasserfarbe getoent)."""
    rs = random.Random(seed)
    Hh, W = a.shape[:2]
    Hges = max(6, hoehe)
    unter_mix = 0.5 + 0.3 * tiefe

    def setz(x, y, c, unter):
        if 0 <= x < W and 0 <= y < Hh:
            if unter:
                c = c * (1 - unter_mix) + wasser * unter_mix
            a[y, x] = np.clip(c, 0, 255)

    # Schatten rechts unten auf dem Wasser
    for y in range(int(cy - ry), int(cy + ry * 1.6) + 1):
        for x in range(int(cx - rx * 0.2), int(cx + rx * 1.8) + 1):
            if ((x - cx - rx * 0.7) / (rx * 1.1)) ** 2 + ((y - cy - 2) / (ry * 0.9)) ** 2 <= 1 and 0 <= x < W and 0 <= y < Hh:
                a[y, x] = a[y, x] * 0.8
    # Sockel (Ellipse): vordere Haelfte liegt im Wasser
    for y in range(int(cy - ry), int(cy + ry) + 1):
        for x in range(int(cx - rx), int(cx + rx) + 1):
            u, v = (x - cx) / rx, (y - cy) / ry
            if u * u + v * v > 1:
                continue
            i = 4 if u + v < -0.6 else 3 if u + v < 0.2 else 2
            if u * u + v * v > 0.75:
                i = 1
            setz(x, y, BRAUN[i], (not raus) or v > -0.1)
    # Spitzen: Nebenspitzen zuerst, dann die Hauptspitze
    kegel = []
    for _ in range(rs.choice((1, 2, 2))):
        seite = rs.choice((-1, 1))
        kegel.append((seite * rx * rs.uniform(0.35, 0.6), rx * rs.uniform(0.35, 0.5), Hges * rs.uniform(0.45, 0.7),
                      rs.uniform(-2, 2)))
    kegel.append((rs.uniform(-1.5, 1.5), rx * 0.72, Hges, rs.uniform(-3, 3)))
    for (dx, bw, hk, biege) in kegel:
        hk = int(hk)
        for k in range(hk + 1):
            t = k / max(1, hk)
            w = bw * (1 - t) ** 0.85 + 0.6 * math.sin(k * 1.7 + seed)
            if w < 0.6:
                continue
            xc = cx + dx + biege * t * t
            y = int(round(cy - ry * 0.2 - k))
            for x in range(int(math.floor(xc - w)), int(math.ceil(xc + w)) + 1):
                r = (x - xc) / max(w, 1)
                if abs(r) > 1:
                    continue
                i = 5 if r < -0.45 else 4 if r < 0 else 3 if r < 0.45 else 2
                if r > 0.82:
                    i = 0
                elif r < -0.82:
                    i = 2
                if (int(x - xc) + k // 3) % 4 == 0 and abs(r) < 0.8:
                    i = max(0, i - 1)                     # senkrechte Rillen
                if t > 0.82:
                    i = min(6, i + 1)                     # helle Spitze
                c = BRAUN[i]
                unter = not raus
                if raus and k < 3:
                    c = c * 0.72                          # nasser Streifen ueber der Wasserlinie
                setz(x, y, c, unter)
                if raus:
                    SPITZEN.append((x, y))
    if raus:                                              # Schaumring um den Fuss (Luecken wandern)
        fr = frame or 0
        for x in range(int(cx - rx - 2), int(cx + rx + 3)):
            u = (x - cx) / (rx + 1.5)
            if abs(u) > 1:
                continue
            y = int(round(cy + (ry + 0.5) * math.sqrt(max(0, 1 - u * u)) * 0.55))
            if (x + fr) % 5 and 0 <= x < W and 0 <= y < Hh:
                a[y, x] = SCHAUM
            y2 = int(round(cy - ry * 0.25))
            if abs(u) > 0.8 and (x + fr) % 3 and 0 <= x < W and 0 <= y2 < Hh:
                a[y2, x] = a[y2, x] * 0.4 + SCHAUM * 0.6


FELSEN_AUSLASSEN = set()
FELSEN_GESETZT = []


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
            if art == 'unter' and hoehe == 0:
                hoehe = int(ry * rs.uniform(2.0, 3.0))
            rx_, ry_ = int(round(rx * rs.uniform(0.85, 1.15))), int(round(ry * rs.uniform(0.85, 1.15)))
            # am 16x16-Raster: Fels mittig im kleinsten Kachelblock, Fuss unten buendig auf der Kachelkante
            wt = math.ceil((2 * rx_ + 3) / 16)
            cx = (cx // 16) * 16 + 8 if wt % 2 else int(round(cx / 16.0)) * 16
            cy = ((cy + ry_) // 16) * 16 + 15 - ry_
            ry_eff = ry_ + (hoehe / 2 if art == 'raus' else 0)
            if not passt(z, cx, cy, rx_, ry_, 2):              # Grundflaeche muss auf einer Stufe liegen
                continue
            hh_ = hoehe * (2.2 if art == 'raus' else 1) if hoehe else ry_ * 3
            if meiden is not None and meiden[max(0, int(cy - ry_ - hh_) - 3):int(cy + ry_) + 4,
                                             max(0, int(cx - rx_) - 3):int(cx + rx_) + 4].any():
                continue                                       # auch die Spitze darf kein Objekt beruehren
            if belegt[max(0, cy - int(ry_ + hoehe * 2.2) - 4):cy + int(ry_) + 7, max(0, cx - int(rx_) - 6):cx + int(rx_) + 7].any():
                continue
            belegt[max(0, cy - int(ry_ + hoehe * 2.2)):cy + int(ry_) + 1, max(0, cx - int(rx_)):cx + int(rx_) + 1] = True
            gesetzt.append((i, art, cx, cy, rx_, ry_, hoehe, rs.randrange(10000)))
            n += 1
    for (i, art, cx, cy, rx, ry, hoehe, s) in sorted(gesetzt, key=lambda g: g[3]):
        if (cx, cy) in FELSEN_AUSLASSEN:                             # einzelne Felsen gezielt weglassen (Karte)
            continue
        FELSEN_GESETZT.append((i, art, cx, cy))
        hoehe = hoehe * (2.2 if art == 'raus' else 1)                # spitze Felsnadeln: hoch
        FELSEN_PROTOKOLL.append((int(cx - rx - 3), int(cy - ry * 0.2 - hoehe - 2), int(cx + rx + 4), int(cy + ry + 3),
                                 int(cy - ry * 0.25), art == 'raus'))
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
        bx, by = (int(xs[k]) // 16) * 16 + 8, (int(ys[k]) // 16) * 16 + 15   # Algen mittig in ihrer Kachel
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


def meer_terrassen(img, region, frame=None, meiden=None, maske=None, dist=None):
    """maske: feste Meeresflaeche (z. B. aus dem Standbild) - sonst Erkennung ueber die Farbe. Fuer Animationen
    immer die feste Maske uebergeben, sonst wandern Kueste, Stufen und Felsen von Bild zu Bild."""
    a = np.array(img.convert('RGB')).astype(np.float32)
    Hh, W = a.shape[:2]
    if maske is not None:
        m = maske & region
    else:
        r, g, b = a[..., 0], a[..., 1], a[..., 2]
        roh = region & (b > r + 40) & (b > g + 10)
        m = np.array(Image.fromarray((roh * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2.5))) > 120
        m &= region
    MEER_MASKE[0] = m
    dist_vorgabe = dist
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
    if dist_vorgabe is not None:                                   # eigenes Abstandsfeld (z. B. Flach/Tief nach Vorlage)
        d = dist_vorgabe.astype(np.float32).copy()
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
    vor_felsen = a.copy()
    n_proto = len(FELSEN_PROTOKOLL)
    felsen_setzen(a, zonen, FARBEN, tiefen, regeln, fr, 21, meiden, anzahl=[14, 12, 16, 6])
    nach_felsen = a.copy()
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
    # herausragende Felsspitzen liegen UEBER Schaum, Brandung und Lichtstrichen (sie ragen aus dem Wasser)
    for (x0, y0, x1, y1, linie, raus) in FELSEN_PROTOKOLL[n_proto:]:
        if not raus:
            continue
        x0, x1 = max(0, x0), min(W, x1)
        y0, y1 = max(0, y0), min(Hh, linie + 3)
        if x1 <= x0 or y1 <= y0:
            continue
        fels_px = (np.abs(nach_felsen[y0:y1, x0:x1] - vor_felsen[y0:y1, x0:x1]).sum(axis=2) > 0)
        teil = a[y0:y1, x0:x1]
        teil[fels_px] = nach_felsen[y0:y1, x0:x1][fels_px]
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
