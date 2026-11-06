"""Vertieftes Wasser fuer Fluss und Teich (Karte 01): die Wasserflaeche liegt eine Stufe tiefer als der Boden.

  vertiefen(img, region, frame)   region: Pixelmaske, in der Wasser gesucht wird (Fluss-/Teichkacheln + Rand)

Aufbau (Licht oben links, Blick von Sueden):
  - Erdrand ringsum auf dem Boden (3 px Braun, aussen eine dunkle Graskante)
  - Nordseite: Ufermauer aus Steinbloecken, 12 px hoch, oben Lichtkante, unten Schatten aufs Wasser
  - West-/Ostseite: schmale Ufermauer (4 px), West im Schatten, Ost im Licht
  - Suedseite: nur die Kante (die Mauer zeigt vom Betrachter weg)
  - Grund: Kopfsteine, die durchs Wasser schimmern; Oberflaeche mit wandernden Lichtstrichen (16 Frames)
"""
import numpy as np
from PIL import Image, ImageFilter

H = lambda h: np.array(tuple(int(h[i:i + 2], 16) for i in (1, 3, 5)), np.uint8)
ERDE = [H(c) for c in ('#5a3420', '#7a4a2a', '#9a6236', '#b47a44')]
MAUER = [H(c) for c in ('#163248', '#1f4462', '#2a587c', '#366a92', '#4c84aa', '#7cb0cc')]
GRUND = [H(c) for c in ('#245694', '#2b62a2', '#3470b0', '#3e7cbc', '#4c8ac6')]
LICHT = [H(c) for c in ('#8cc4f4', '#dff3ff')]
MAUER_H = 12
SEITE = 4
RAND = 3


def wassermaske(a, region):
    r, g, b = a[..., 0].astype(int), a[..., 1].astype(int), a[..., 2].astype(int)
    roh = region & (b > r + 60) & (b > g + 30)
    glatt = np.array(Image.fromarray((roh * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2.0))) > 110
    return glatt & region


def _lauf(m, achse, rueckwaerts=False):
    """Fuer jedes Wasserpixel: Abstand zum naechsten Landpixel davor (oben bzw. links/rechts); Land = -1."""
    mm = np.moveaxis(m, achse, 0)
    if rueckwaerts:
        mm = mm[::-1]
    d = np.full(mm.shape, -1, np.int32)
    vorher = np.full(mm.shape[1:], -1, np.int32)
    for i in range(mm.shape[0]):
        cur = np.where(mm[i], vorher + 1, -1)
        d[i] = cur
        vorher = cur
    if rueckwaerts:
        d = d[::-1]
    return np.moveaxis(d, 0, achse)


_STEIN_CACHE = {}


def _kopfsteine(h, w):
    """Unterwasser-Grund: unregelmaessige, abgerundete Kiesel (versetztes Raster mit Zufallsversatz und
    Groessen), weich und kontrastarm, damit es nach Wasser und nicht nach Mauer aussieht."""
    if (h, w) in _STEIN_CACHE:
        return _STEIN_CACHE[(h, w)]
    import random
    rs = random.Random(3)
    t = np.zeros((h, w, 3), np.uint8)
    t[:] = GRUND[1]
    for gy in range(-4, h + 8, 7):
        for gx in range(-4, w + 8, 9):
            cx = gx + (4 if (gy // 7) % 2 else 0) + rs.randint(-2, 2)
            cy = gy + rs.randint(-1, 1)
            rx, ry = rs.choice((3, 3.5, 4)), rs.choice((2.5, 3))
            ton = rs.choice((2, 2, 3, 1))
            for y in range(int(cy - ry - 1), int(cy + ry + 2)):
                for x in range(int(cx - rx - 1), int(cx + rx + 2)):
                    if not (0 <= y < h and 0 <= x < w):
                        continue
                    d = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
                    if d > 1:
                        continue
                    u, v = (x - cx) / rx, (y - cy) / ry
                    c = GRUND[ton]
                    if u + v < -0.9 and d > 0.35:
                        c = GRUND[min(4, ton + 1)]
                    elif u + v > 0.9 and d > 0.45:
                        c = GRUND[max(0, ton - 1)]
                    t[y, x] = c
    _STEIN_CACHE[(h, w)] = t
    return t


UNTER = [H(c) for c in ('#1c3c6c', '#24508a', '#3466a0', '#6aa2d4')]   # Unterwasser-Stufenkanten
STUFEN = [(26, 0.8, 8), (54, 0.64, 7)]    # (Abstand zum Ufer in px, Helligkeit des Grunds, Kantenhoehe)


def _stufe(m, abstand):
    """Innenflaeche: Wasserpixel mit mindestens `abstand` px Abstand zum Ufer, gerundet und ohne schmale Reste."""
    k = Image.fromarray((m * 255).astype(np.uint8))
    for _ in range(abstand // 2):
        k = k.filter(ImageFilter.MinFilter(5))
    for _ in range(3):                                  # schmale Streifen (Fluss) entfernen, dann zurueckwachsen
        k = k.filter(ImageFilter.MinFilter(5))
    for _ in range(3):
        k = k.filter(ImageFilter.MaxFilter(5))
    k = k.filter(ImageFilter.GaussianBlur(6))
    return (np.array(k) > 128) & m


def vertiefen(img, region, frame=None, meiden=None, maske=None, rand=None, stufen=None):
    """maske: fertige Wassermaske (sonst Erkennung ueber die Farbe), rand: 4 Farben fuer den Uferrand
    (dunkel -> hell), Standard Erde. stufen: eigene Tiefenstufen [(Abstand, Helligkeit, Kantenhoehe), ...]
    fuer kleinere Teiche."""
    global ERDE, STUFEN
    erde_alt, stufen_alt = ERDE, STUFEN
    if rand is not None:
        ERDE = [H(c) for c in rand]
    if stufen is not None:
        STUFEN = stufen
    try:
        return _vertiefen(img, region, frame, meiden, maske)
    finally:
        ERDE, STUFEN = erde_alt, stufen_alt


def _vertiefen(img, region, frame, meiden, maske):
    a = np.array(img.convert('RGB'))
    Hh, W = a.shape[:2]
    m = (maske & region) if maske is not None else wassermaske(a, region)
    if not m.any():
        return img
    oben = _lauf(m, 0)                     # Pixel seit Landkante oben
    links = _lauf(m, 1)
    rechts = _lauf(m, 1, rueckwaerts=True)
    # Erdrand auf dem Land
    land = ~m
    umg = np.array(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(2 * RAND + 1))) > 0
    rand = umg & land & region_erweitert(region)
    dist = np.full((Hh, W), 99, np.int32)
    k = m.copy()
    for d in range(1, RAND + 2):
        k2 = np.array(Image.fromarray((k * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3))) > 0
        dist[(dist == 99) & k2 & land] = d
        k = k2
    a[(dist == 1) & rand] = ERDE[1]
    a[(dist == 2) & rand] = ERDE[2]
    a[(dist == 3) & rand] = ERDE[3]
    a[(dist == 4) & region_erweitert(region) & land] = (a[(dist == 4) & region_erweitert(region) & land] * 0.82).astype(np.uint8)
    # Grund mit Kopfsteinen, Wasserfarbe darueber
    t = _kopfsteine(Hh, W)
    a[m] = t[m]
    # Ufermauer Nord (Bloecke 6 px breit, Lichtkante oben, Fugen)
    nord = m & (oben < MAUER_H)
    ys, xs = np.nonzero(nord)
    for y, x in zip(ys, xs):
        d = oben[y, x]
        blk = (x + (3 if (d // 6) % 2 else 0)) % 6
        if d == 0:
            c = MAUER[5]
        elif d == 1:
            c = MAUER[4]
        elif blk == 5 or d == 6:
            c = MAUER[1]
        else:
            c = MAUER[3] if d < 6 else MAUER[2]
        if d == MAUER_H - 1:
            c = MAUER[0]
        a[y, x] = c
    # Seitenmauern (nur unterhalb der Nordmauer)
    rest = m & ~nord
    w_seite = rest & (links < SEITE)
    o_seite = rest & (rechts < SEITE)
    for msk, dist_, pal in ((w_seite, links, (MAUER[0], MAUER[1], MAUER[2], MAUER[2])),
                            (o_seite, rechts, (MAUER[2], MAUER[4], MAUER[3], MAUER[3]))):
        ys, xs = np.nonzero(msk)
        for y, x in zip(ys, xs):
            c = pal[min(3, dist_[y, x])]
            if y % 6 == 5:
                c = MAUER[1]
            a[y, x] = c
    # Schatten der Mauern aufs Wasser + Wasserfarbe
    boden = m & ~nord & ~w_seite & ~o_seite
    tief = np.ones((Hh, W), np.float32)
    tief[boden & (oben < MAUER_H + 4)] = 0.72
    tief[boden & (links < SEITE + 3)] = np.minimum(tief[boden & (links < SEITE + 3)], 0.8)
    f = tief[boden][:, None]
    a[boden] = np.clip(a[boden] * f, 0, 255).astype(np.uint8)
    # Suedkante: dunkle Linie (Ufer zeigt weg)
    sued = m & ~np.roll(m, -1, 0)
    a[sued] = MAUER[1]
    # Tiefere Stufen im Wasser (nur wo die Flaeche breit genug ist, also im Teich, nicht im schmalen Fluss)
    zonen = []
    vorige = boden.copy()
    for (abstand, dunkel, mauer_h) in STUFEN:
        innen = _stufe(m, abstand)
        if not innen.any():
            continue
        io = _lauf(innen, 0)
        il = _lauf(innen, 1)
        ir = _lauf(innen, 1, rueckwaerts=True)
        a[innen] = np.clip(a[innen] * dunkel, 0, 255).astype(np.uint8)          # Grund tiefer = dunkler
        nw = innen & (io < mauer_h)
        ys, xs = np.nonzero(nw)
        for y, x in zip(ys, xs):                                                 # Unterwasser-Kante Nord
            d = io[y, x]
            blk = (x + (3 if (d // 5) % 2 else 0)) % 6
            c = UNTER[3] if d == 0 else UNTER[2] if d == 1 else UNTER[0] if blk == 5 else UNTER[1]
            if d == mauer_h - 1:
                c = UNTER[0]
            a[y, x] = np.clip(c * (dunkel + 0.12), 0, 255).astype(np.uint8)
        rest = innen & ~nw
        for msk, wert in ((rest & (il < 2), UNTER[0]), (rest & (ir < 2), UNTER[2])):
            a[msk] = np.clip(wert * (dunkel + 0.1), 0, 255).astype(np.uint8)
        schatten = rest & (io < mauer_h + 3) & (io >= mauer_h)
        a[schatten] = (a[schatten] * 0.8).astype(np.uint8)
        kante_s = innen & ~np.roll(innen, -1, 0)                                  # Suedkante der Stufe
        a[kante_s] = np.clip(UNTER[3] * 0.9, 0, 255).astype(np.uint8)
        zonen.append(vorige & ~innen)
        vorige = rest & ~(il < 2) & ~(ir < 2) & ~kante_s
    zonen.append(vorige)
    # Oberflaeche: kurze Lichtstriche je Kachel, wandern in 16 Frames eine Kachel nach unten
    fr = frame or 0
    yy, xx = np.nonzero(boden)
    for y, x in zip(yy, xx):
        ky, kx = (y - fr) // 16, x // 16
        h = (kx * 73856093 ^ ky * 19349663) & 0xffff
        py, px = (y - fr) % 16, x % 16
        for j in range(2):
            sy, sx = (h >> (4 * j)) % 13 + 1, (h >> (4 * j + 8)) % 11 + 1
            if py == sy and sx <= px < sx + 3:
                a[y, x] = LICHT[1] if px == sx + 1 else LICHT[0]
    if len(zonen) == 3:                                   # Felsen und Algen nach Tiefenregel
        import wasser_details
        a = wasser_details.teich_details(a, zonen, GRUND[2].astype(np.float32), fr, meiden)
    return Image.fromarray(a).convert('RGBA')


_ERW = {}


def region_erweitert(region):
    key = id(region)
    if key not in _ERW:
        _ERW.clear()
        _ERW[key] = np.array(Image.fromarray((region * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(11))) > 0
    return _ERW[key]
