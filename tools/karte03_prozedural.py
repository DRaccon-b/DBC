"""Prozedurale, animierte Sprites fuer Karte 03 (Server Desert):

  lautsprecher(frame, art)  frontale Boxen ('monitor' klein, 'turm' gross) mit pumpenden Membranen
  buehne(frame)             breite Konzertbuehne (256 px) mit Truss, LED-Wand (Equalizer), Spots, DJ-Pult
  tor_anpassen()            PixelLab-Arenator auf die Sandstein-Palette der Arena + Durchgang frei

Licht oben links. Takt: alle 4 Frames ein Bass-Schlag (16 Frames je Schleife).
"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
import industrie as ind

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte03')
N_FRAMES = 16

K = {n: ind.rgb(h) for n, h in dict(
    schwarz='#0e0d12', d0='#16141c', d1='#1e1c26', d2='#2a2833', d3='#3a3846', d4='#4c4a5a', d5='#6a6880',
    d6='#8a889a', m0='#3e4850', m1='#5a6670', m2='#8e9ba3', m3='#c4ccd2', cyan='#2fc7d8', cyan2='#7ff0f5',
    rosa='#e060a8', rosa2='#ff9ad0', weiss='#f4f2ff', rot='#d8443a', gelb='#f5c842').items()}


def schlag(frame):
    """Bass-Huellkurve: 1.0 auf dem Schlag, klingt in 4 Frames ab."""
    return (1.0, 0.55, 0.2, 0.0)[frame % 4]


def _gehaeuse(L, x0, y0, w, h):
    L.rect(x0, y0, x0 + w, y0 + h, K['d2'])
    for x in range(x0, x0 + w):
        L.p(x, y0, K['schwarz']); L.p(x, y0 + 1, K['d4']); L.p(x, y0 + h - 1, K['schwarz']); L.p(x, y0 + h - 2, K['d1'])
    for y in range(y0, y0 + h):
        L.p(x0, y, K['schwarz']); L.p(x0 + 1, y, K['d3']); L.p(x0 + w - 1, y, K['schwarz']); L.p(x0 + w - 2, y, K['d1'])
    for (cx, cy) in ((x0 + 1, y0 + 1), (x0 + w - 3, y0 + 1), (x0 + 1, y0 + h - 3), (x0 + w - 3, y0 + h - 3)):
        L.rect(cx, cy, cx + 2, cy + 2, K['m1']); L.p(cx, cy, K['m3'])     # Eckschutz


def _membran(L, cx, cy, r, pump):
    """Tieftoener frontal: Sicke, Konus mit Licht oben links, Staubkappe. pump 0..1 woelbt nach vorn."""
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            d = math.hypot(dx, dy)
            if d > r + 0.3:
                continue
            if d > r - 1.2:
                c = K['d0']                                   # Korb-Rand
            elif d > r - 2.4:
                c = K['d4'] if dx + dy < 0 else K['d3']        # Sicke
                if pump > 0.5 and dx + dy < 0:
                    c = K['d6']
            else:
                c = K['d1']
                if dx + dy < -d * 0.6 and d > r * 0.35:
                    c = K['d3'] if pump < 0.5 else K['d4']     # Konus-Licht
                if dx + dy > d * 0.9 and d > r * 0.5:
                    c = K['schwarz']
            L.p(cx + dx, cy + dy, c)
    rk = max(1.5, r * 0.32 + pump * 1.2)                       # Staubkappe kommt beim Schlag nach vorn
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            d = math.hypot(dx, dy)
            if d <= rk:
                c = K['d5'] if dx + dy < 0 else K['d4']
                if d < rk * 0.45 and dx + dy < 0:
                    c = K['d6'] if pump < 0.5 else K['weiss']
                L.p(cx + dx, cy + dy, c)


def _hochtoener(L, x0, y0, w):
    L.rect(x0, y0, x0 + w, y0 + 5, K['d0'])
    for x in range(x0 + 1, x0 + w - 1):
        L.p(x, y0 + 1, K['d4']); L.p(x, y0 + 4, K['d1'])
    L.rect(x0 + 3, y0 + 2, x0 + w - 3, y0 + 4, K['schwarz'])
    L.rect(x0 + w // 2 - 1, y0 + 2, x0 + w // 2 + 1, y0 + 4, K['d5'])


def lautsprecher(frame=0, art='monitor'):
    """Frontale Box. 'monitor': 2 Gehaeuse (30x44); 'turm': 3 Gehaeuse (40x92)."""
    p = schlag(frame)
    if art == 'monitor':
        im = Image.new('RGBA', (30, 46), (0, 0, 0, 0)); L = ind.Leinwand(im)
        _gehaeuse(L, 1, 2, 28, 20)
        _hochtoener(L, 7, 5, 16)
        _membran(L, 15, 15, 5, p * 0.6)
        _gehaeuse(L, 0, 22, 30, 22)
        _membran(L, 15, 33, 8, p)
        L.rect(2, 44, 6, 46, K['schwarz']); L.rect(24, 44, 28, 46, K['schwarz'])
        im.info['bass'] = [(15, 33), (15, 15)]
        return im
    im = Image.new('RGBA', (40, 94), (0, 0, 0, 0)); L = ind.Leinwand(im)
    _gehaeuse(L, 1, 0, 38, 30)
    _hochtoener(L, 6, 3, 28)
    _membran(L, 11, 19, 6, p * 0.6); _membran(L, 29, 19, 6, p * 0.6)
    _gehaeuse(L, 0, 30, 40, 28)
    _membran(L, 11, 44, 7, p * 0.8); _membran(L, 29, 44, 7, p * 0.8)
    _gehaeuse(L, 0, 58, 40, 34)
    _membran(L, 20, 75, 13, p)
    L.rect(2, 92, 8, 94, K['schwarz']); L.rect(32, 92, 38, 94, K['schwarz'])
    im.info['bass'] = [(20, 75), (11, 44), (29, 44)]
    return im


def _truss_senkrecht(L, x0, y0, y1, w=12):
    for y in range(y0, y1):
        L.p(x0, y, K['m2']); L.p(x0 + 1, y, K['m1'])
        L.p(x0 + w - 2, y, K['m1']); L.p(x0 + w - 1, y, K['m0'])
        k = (y - y0) % (w - 2)
        L.p(x0 + 1 + k, y, K['m1'])                             # Diagonale
        if (y - y0) % (w - 2) == 0:
            for x in range(x0, x0 + w):
                L.p(x, y, K['m1'])


def _truss_waagrecht(L, x0, x1, y0, h=12):
    for x in range(x0, x1):
        L.p(x, y0, K['m3']); L.p(x, y0 + 1, K['m2'])
        L.p(x, y0 + h - 2, K['m1']); L.p(x, y0 + h - 1, K['m0'])
        k = (x - x0) % (2 * (h - 2))
        yy = y0 + 1 + (k if k < h - 2 else 2 * (h - 2) - k)
        L.p(x, yy, K['m1'])
        if (x - x0) % (h - 2) == 0:
            for y in range(y0, y0 + h):
                L.p(x, y, K['m1'])


def buehne(frame=0, breite=256, hoehe=152):
    """Konzertbuehne frontal: Podest mit Lauflicht, Vorhang, LED-Wand mit Equalizer, Truss mit Spots,
    zwei Boxentuerme und DJ-Pult. Fuss = unterste Zeile."""
    W, H = breite, hoehe
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); L = ind.Leinwand(im)
    p = schlag(frame)
    deck_o, deck_u = H - 50, H - 24                              # Buehnenboden (Draufsicht)
    # Vorhang hinter allem
    for y in range(24, deck_o + 2):
        for x in range(22, W - 22):
            c = K['d1'] if (x // 3) % 3 else K['d0']
            if (x // 3) % 3 == 1 and (x % 3) == 0:
                c = K['d2']
            L.p(x, y, c)
    # LED-Wand
    sx0, sx1, sy0, sy1 = 72, W - 72, 32, deck_o - 4
    L.rect(sx0 - 3, sy0 - 3, sx1 + 3, sy1 + 3, K['schwarz'])
    L.rect(sx0 - 3, sy0 - 3, sx1 + 3, sy0 - 2, K['d4'])
    for y in range(sy0, sy1):
        for x in range(sx0, sx1):
            L.p(x, y, K['d0'] if y % 2 else ind.rgb('#12101a'))
    n_bar = (sx1 - sx0 - 4) // 7
    for i in range(n_bar):
        h_rel = 0.25 + 0.45 * abs(math.sin(frame * 0.9 + i * 0.75)) * (0.6 + 0.4 * abs(math.sin(i * 1.7)))
        h_rel = min(1.0, h_rel + 0.3 * p * (1 - abs(i - n_bar / 2) / (n_bar / 2)))
        hb = int(h_rel * (sy1 - sy0 - 6))
        bx = sx0 + 3 + i * 7
        for k in range(hb):
            y = sy1 - 3 - k
            t = k / max(1, (sy1 - sy0 - 6))
            c = K['cyan'] if t < 0.45 else K['cyan2'] if t < 0.6 else K['rosa'] if t < 0.85 else K['rosa2']
            if y % 2 == 0:
                for x in range(bx, bx + 5):
                    L.p(x, y, c)
        L.rect(bx, sy1 - 4 - hb - 1, bx + 5, sy1 - 3 - hb, K['weiss'])  # Spitze
    # Truss: zwei Tuerme + Traverse
    _truss_senkrecht(L, 8, 10, deck_u, 12); _truss_senkrecht(L, W - 20, 10, deck_u, 12)
    _truss_waagrecht(L, 8, W - 8, 8, 12)
    # Spots unter der Traverse, Lichtkegel auf den Boden
    farben = [K['rosa'], K['cyan'], K['gelb'], K['rosa'], K['cyan'], K['gelb'], K['rosa']]
    kegel = Image.new('RGBA', (W, H), (0, 0, 0, 0)); KL = kegel.load()
    for i in range(7):
        sx = 34 + i * 31
        f = farben[(i + frame // 2) % len(farben)]
        an = (i + frame // 4) % 3 != 0
        L.rect(sx - 3, 20, sx + 4, 27, K['d2']); L.p(sx - 3, 20, K['d4'])
        L.rect(sx - 2, 26, sx + 3, 28, f if an else K['d4'])
        if an:
            ziel = sx + int(18 * math.sin(frame * 2 * math.pi / N_FRAMES + i))
            for y in range(29, deck_u - 2):
                t = (y - 29) / (deck_u - 31)
                mx = sx + (ziel - sx) * t
                br = 2 + t * 9
                for x in range(int(mx - br), int(mx + br) + 1):
                    if 0 <= x < W:
                        KL[x, y] = f[:3] + (int(38 * (1 - 0.5 * t)),)
    # Buehnenboden
    for y in range(deck_o, deck_u):
        for x in range(2, W - 2):
            c = ind.rgb('#3a3644') if (y - deck_o) % 6 else ind.rgb('#2e2a36')
            if (x * 7 + y * 3) % 47 == 0:
                c = ind.rgb('#4a4656')
            L.p(x, y, c)
    for x in range(2, W - 2):
        L.p(x, deck_o, K['d4'])
    # Boxentuerme auf dem Boden, DJ-Pult in der Mitte
    turm = lautsprecher(frame, 'turm')
    im.alpha_composite(turm, (26, deck_u - 6 - turm.height))
    im.alpha_composite(turm, (W - 26 - turm.width, deck_u - 6 - turm.height))
    L = ind.Leinwand(im)
    dx0, dx1, dy0 = W // 2 - 26, W // 2 + 26, deck_u - 22
    L.rect(dx0, dy0, dx1, dy0 + 4, K['d4'])                       # Pultplatte
    L.rect(dx0, dy0 + 4, dx1, deck_u - 4, K['d2'])
    for x in range(dx0, dx1):
        L.p(x, dy0, K['d6']); L.p(x, dy0 + 6, K['cyan'] if (x + frame * 3) % 8 < 4 else K['rosa'])
    L.rect(dx0 + 6, dy0 - 6, dx0 + 20, dy0, K['d1']); L.rect(dx0 + 7, dy0 - 5, dx0 + 19, dy0 - 1, ind.rgb('#3a6a9a'))
    L.p(dx0 + 13, dy0 - 3, K['cyan2'])                             # Laptop
    for k in range(6):                                            # Mischpult-LEDs
        on = (k + frame) % 3 == 0
        L.p(dx1 - 22 + k * 3, dy0 + 2, K['gelb'] if on else K['d5'])
        L.p(dx1 - 22 + k * 3, dy0 + 1, K['rot'] if (k * 5 + frame) % 4 == 0 else K['d3'])
    # Podest-Front mit Lauflicht
    for y in range(deck_u, H):
        for x in range(0, W):
            c = K['d2'] if x % 8 else K['d0']
            if y == deck_u:
                c = K['m3']
            elif y == deck_u + 1:
                c = K['m1']
            elif y == H - 1:
                c = K['schwarz']
            L.p(x, y, c)
    for x in range(3, W - 3, 6):
        on = ((x // 6) + frame) % 4 == 0
        L.rect(x, deck_u + 5, x + 2, deck_u + 7, K['cyan2'] if on else K['d4'])
    for x in (0, W - 1):
        for y in range(deck_o, H):
            L.p(x, y, K['schwarz'])
    im.alpha_composite(kegel)
    im.info['bass'] = [(26 + 20, deck_u - 6 - 94 + 75), (W - 26 - 20, deck_u - 6 - 94 + 75)]
    return im


SANDSTEIN = ind.pal('#6a4a2c', '#8a6640', '#a88250', '#c4a066', '#dcbc80', '#ecd49c', '#f8e8c0')
STOFF = ind.pal('#4a2020', '#6e2c26', '#8e3a30', '#a84e3a', '#c06a4c')


def tor_anpassen():
    """tor/00 (PixelLab) -> abgeleitet/arena_tor.png: Stein nach Helligkeit auf die Sandstein-Rampe der
    Arena-Mauern, Stoffe auf gedecktes Rot; dunkler Durchgang + Fallgitter werden durchsichtig, nur ein
    Schattenstreifen unter dem Bogen bleibt."""
    import colorsys
    from collections import deque
    im = Image.open(os.path.join(OBJ, 'tor', '00.png')).convert('RGBA')
    a = np.array(im).astype(np.int16)
    h, w = a.shape[:2]
    lum = 0.3 * a[..., 0] + 0.59 * a[..., 1] + 0.11 * a[..., 2]
    # Durchgang: dunkle Pixel, zusammenhaengend vom unteren Rand in der Mitte
    dunkel = (lum < 78) & (a[..., 3] > 0)
    frei = np.zeros((h, w), bool)
    q = deque()
    for x in range(w // 2 - 12, w // 2 + 12):
        for y in range(h - 1, h - 26, -1):
            if dunkel[y, x]:
                q.append((y, x)); frei[y, x] = True
                break
    while q:
        y, x = q.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            yy, xx = y + dy, x + dx
            if 0 <= yy < h and 0 <= xx < w and not frei[yy, xx] and dunkel[yy, xx] and abs(xx - w // 2) < 30:
                frei[yy, xx] = True; q.append((yy, xx))
    # Fallgitter-Staebe zwischen den dunklen Flaechen: Zeilen der Oeffnung komplett leeren
    for y in range(h):
        xs = np.nonzero(frei[y])[0]
        if len(xs) > 2:
            frei[y, xs.min():xs.max() + 1] = True
    out = a.copy()
    for y in range(h):
        for x in range(w):
            if a[y, x, 3] == 0:
                continue
            r, g, b = a[y, x, :3] / 255.0
            hh, s, v = colorsys.rgb_to_hsv(r, g, b)
            if (hh < 0.04 or hh > 0.93) and s > 0.45:                # Stoff
                i = min(len(STOFF) - 1, int(v * len(STOFF) * 1.05))
                out[y, x, :3] = STOFF[i][:3]
            elif s > 0.12 and 0.04 <= hh <= 0.17:                     # Stein
                i = min(len(SANDSTEIN) - 1, max(0, int((lum[y, x] - 40) / 200 * len(SANDSTEIN))))
                out[y, x, :3] = SANDSTEIN[i][:3]
    out[frei, 3] = 0
    # Schatten unter dem Bogen (Laibung) und an der Innenseite links
    for x in range(w):
        ys = np.nonzero(frei[:, x])[0]
        if len(ys):
            for k in range(4):
                y = ys.min() + k
                out[y, x] = (30, 22, 20, 150 - k * 35)
    for y in range(h):
        xs = np.nonzero(frei[y])[0]
        if len(xs):
            for k in range(3):
                out[y, xs.min() + k] = (30, 22, 20, 110 - k * 35) if out[y, xs.min() + k, 3] == 0 else out[y, xs.min() + k]
    res = Image.fromarray(out.astype(np.uint8))
    os.makedirs(os.path.join(OBJ, 'abgeleitet'), exist_ok=True)
    res.save(os.path.join(OBJ, 'abgeleitet', 'arena_tor.png'))
    return res


def statisch_speichern():
    d = os.path.join(OBJ, 'abgeleitet')
    os.makedirs(d, exist_ok=True)
    lautsprecher(0, 'monitor').save(os.path.join(d, 'box_monitor.png'))
    lautsprecher(0, 'turm').save(os.path.join(d, 'box_turm.png'))
    buehne(0).save(os.path.join(d, 'buehne.png'))
    tor_anpassen()


# Satellitenschuesseln der Funkmasten (Koordinaten im PixelLab-Sprite): Mitte, Halbachsen, Seite der Halterung
SCHUESSELN = {
    'gross2/00': {'mast': (8, 30), 'schalen': [(33.5, 50.0, 10.5, 14.0, -1), (9.0, 23.0, 4.0, 6.5, 1),
                                               (31.5, 20.0, 2.5, 4.5, -1), (6.5, 42.0, 3.0, 5.0, 1)]},
    'gross2/01': {'mast': (9, 26), 'schalen': [(5.5, 17.5, 6.0, 9.0, 1), (28.5, 17.5, 6.0, 9.0, -1),
                                               (24.5, 34.5, 5.0, 7.0, -1)]},
}
SCH = {n: ind.rgb(h) for n, h in dict(rand='#1e2228', hell='#f4f8fa', licht='#dce6ec', mitte='#b8c4cc',
                                      dunkel='#8e9ba3', ruecken='#5a6670', ruecken2='#3e4850').items()}


def _in_ellipse(x, y, cx, cy, rx, ry):
    return ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1


def mast_ohne_schuesseln(sp, basis, ox=0, oy=0):
    """Schuesseln aus dem Sprite entfernen; im Mastbereich das Gitter aus der Zeile 8 px darueber/darunter
    (Gitterperiode) ergaenzen, ausserhalb des Masts bleibt es durchsichtig."""
    cfg = SCHUESSELN[basis]
    a = np.array(sp)
    h, w = a.shape[:2]
    weg = np.zeros((h, w), bool)
    for (cx, cy, rx, ry, _) in cfg['schalen']:
        for y in range(h):
            for x in range(w):
                if _in_ellipse(x, y, cx + ox, cy + oy, rx + 1.2, ry + 1.2):
                    weg[y, x] = True
    out = a.copy()
    m0, m1 = cfg['mast'][0] + ox, cfg['mast'][1] + ox
    for y, x in zip(*np.nonzero(weg)):
        out[y, x] = 0
        if m0 <= x <= m1:
            for dy in (8, -8, 16, -16):
                yy = y + dy
                if 0 <= yy < h and not weg[yy, x] and a[yy, x, 3] > 0:
                    out[y, x] = a[yy, x]
                    break
    return Image.fromarray(out)


def schale(L, cx, cy, rx, ry, gier, seite):
    """Eine Schuessel frontal mit Gierwinkel gier (rad): Breite ~cos, Rueckseite als Sichel, Speisearm."""
    sg = math.sin(gier)
    w = max(1.6, rx * (0.35 + 0.65 * math.cos(gier)))
    # Halterung zum Mast
    for x in range(int(round(cx)), int(round(cx + seite * (rx + 2))), seite):
        L.p(x, int(round(cy)), SCH['ruecken2']); L.p(x, int(round(cy)) + 1, SCH['rand'])
    # Rueckseite (Dicke der Schale) auf der abgewandten Seite
    dick = rx * 0.32 * abs(sg)
    if dick >= 0.6:
        bx = cx - math.copysign(dick, sg)
        for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
            for x in range(int(bx - w) - 1, int(bx + w) + 2):
                if _in_ellipse(x + 0.5, y + 0.5, bx, cy, w, ry):
                    L.p(x, y, SCH['ruecken'] if (x - bx) * sg < 0 else SCH['ruecken2'])
    # Schale: Rand dunkel, Innenseite (hohl): oben links im Schatten, unten rechts im Licht
    for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
        for x in range(int(cx - w) - 1, int(cx + w) + 2):
            px, py = x + 0.5, y + 0.5
            if not _in_ellipse(px, py, cx, cy, w, ry):
                continue
            d = ((px - cx) / w) ** 2 + ((py - cy) / ry) ** 2
            u, v = (px - cx) / w, (py - cy) / ry
            if not _in_ellipse(px, py, cx, cy, max(0.6, w - 1), ry - 1):
                c = SCH['rand']
            elif d > 0.62 and u + v < -0.3:
                c = SCH['hell']                                  # Lichtkante des Randes oben links
            else:
                t = u + v - 0.5 * sg
                c = SCH['dunkel'] if t < -0.55 else SCH['mitte'] if t < 0.25 else SCH['licht']
            L.p(x, y, c)
    # Speisearm und Empfaenger (zeigt zum Betrachter, wandert mit dem Winkel)
    fx, fy = cx + rx * 0.55 * sg, cy - ry * 0.05
    n = max(4, int(ry * 0.7) + 2)
    for k in range(n + 1):
        t = k / n
        L.p(int(round(cx + (fx - cx) * t)), int(round(cy + ry * 0.55 + (fy - cy - ry * 0.55) * t)), SCH['ruecken2'])
    L.rect(int(round(fx)) - 1, int(round(fy)) - 1, int(round(fx)) + 1, int(round(fy)) + 1, SCH['ruecken2'])
    L.p(int(round(fx)) - 1, int(round(fy)) - 1, SCH['dunkel'])


PROZ = {'box_monitor': lambda f: lautsprecher(f, 'monitor'), 'box_turm': lambda f: lautsprecher(f, 'turm'),
        'buehne': buehne}

if __name__ == '__main__':
    statisch_speichern()
