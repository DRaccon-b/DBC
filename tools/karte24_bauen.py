"""Karte 24 - The Kaiser's Canyon (A02), Gelaende im Kachelstil der vorigen A02-Karten.

Canyonboden und Wege aus den Sandkacheln von Karte 01 (rot bzw. hell eingefaerbt), Sandflecken in Originalfarbe,
Felsmassen oben aus den Kieselkacheln von Karte 03 (rot eingefaerbt, wie die Felsbuckel der Vorlage), Felsfronten mit
hoehenkanten (Karte 04) in rotem Sandstein, erhoehte Arena und Schrein mit Treppen (Karte 04), Gruben, Lorenbahn,
Teleporter.

  python3 tools/karte24_layout.py && python3 tools/karte24_bauen.py
"""
import json, math, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
import karte_bauen as kb
import karte04_bauen as k4
import karte06_bauen as k6
import karte20_bauen as k20

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte24')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte24')
T = 16
N_FRAMES = 4
BILDDAUER = 250
k4.N_FRAMES = N_FRAMES
import karte_bauen as _kb
_kb.N_FRAMES = N_FRAMES                       # Windwelle (Pflanzen) ueber die 4 Bilder der Karte
H = k4.H
weich, zell_maske, flaeche = k4.weich, k4.zell_maske, k20.flaeche
k4.RASTER45 = True                       # Nutzer: ALLE Bodenkanten am 16er-Raster mit 45 Grad (Regel 6b)
k4.FELS['rot'] = ['#3e1e12', '#5c2c1a', '#7c3e24', '#9a5230', '#b8683e', '#cf8452', '#e2a270']
LIPPE_ROT = ['#5c2c1a', '#7c3e24', '#9a5230', '#b0623a', '#c47448', '#d68a5a']
FRONT = 32


def faerben(lo, hi, a0=0.35, a1=0.5):
    def f(a):
        l = a.mean(axis=2, keepdims=True) / 255.0
        return np.array(lo, np.float32) + (np.array(hi, np.float32) - np.array(lo, np.float32)) * np.clip((l - a0) / a1, 0, 1)
    return f


def grube(a, m, frame=None):
    """Oelbecken (Nutzer: besser): runde, im Boden eingelassene Grube. Aussen ein Ring aus dunkler, oelverschmierter
    Erde, oben (Nordseite) die sichtbare Innenwand aus Erdschichten, darin schwarz-violettes Oel mit Spiegelung:
    helle Glanzbaender (Licht von oben links) und ein paar Blasen; Glanz wandert je Bild ein Stueck (Animation)."""
    Hh, W = m.shape
    f = frame or 0
    yy, xx = np.mgrid[0:Hh, 0:W]
    from PIL import ImageFilter as _IF
    aus = np.array(Image.fromarray((m * 255).astype(np.uint8)).filter(_IF.MaxFilter(5))) > 0
    ring = aus & ~m
    a[ring] = (a[ring] * 0.55 + np.array((46, 26, 22)) * 0.45).astype(np.uint8)          # oelverschmierter Rand
    d = np.zeros((Hh, W), np.int32)                                    # Abstand zur Nordkante (Innenwand)
    for y in range(1, Hh):
        d[y] = np.where(m[y], np.where(m[y - 1], d[y - 1] + 1, 0), 0)
    WAND = [np.array(H(c), np.float32) for c in ('#8a4a2c', '#6a3620', '#4e2616', '#341a10', '#24120c')]
    oel = m & (d >= len(WAND))
    for k, c in enumerate(WAND):
        a[m & (d == k)] = c.astype(np.uint8)
    rs = np.random.RandomState(31)
    n = rs.rand(Hh // 8 + 2, W // 8 + 2)
    fl = np.array(Image.fromarray((n * 255).astype(np.uint8)).resize((W, Hh), Image.BICUBIC)).astype(np.float32) / 255
    basis = np.array((10, 8, 8), np.float32) + np.array((14, 10, 8), np.float32) * fl[..., None]   # fast schwarz
    a[oel] = basis[oel].astype(np.uint8)
    # weicher Oelglanz: unregelmaessige, wolkige Flecken (kein Eis: keine geraden Linien, kein Blau)
    n2 = rs.rand(Hh // 6 + 2, W // 6 + 2)
    w2 = np.array(Image.fromarray((n2 * 255).astype(np.uint8)).resize((W, Hh), Image.BICUBIC)).astype(np.float32) / 255
    ph = (f % 4) / 4.0
    g = np.abs(((w2 + ph) % 1.0) - 0.5)                                 # wandernde Isolinien = schillernde Oelringe
    ring1 = oel & (g < 0.018)
    ring2 = oel & (g >= 0.018) & (g < 0.03)
    a[ring1] = (a[ring1] * 0.3 + np.array((92, 70, 48)) * 0.7).astype(np.uint8)
    a[ring2] = (a[ring2] * 0.5 + np.array((58, 52, 70)) * 0.5).astype(np.uint8)
    glanz = oel & (d == len(WAND))                                     # Lichtkante unter der Innenwand
    a[glanz] = (a[glanz] * 0.6 + np.array((70, 56, 44)) * 0.4).astype(np.uint8)
    ys, xs = np.nonzero(oel)                                           # Blasen (pulsieren)
    if len(ys):
        rb = np.random.RandomState(7)
        for i in rb.choice(len(ys), max(1, len(ys) // 350), replace=False):
            y, x = ys[i], xs[i]
            if (i + f) % 4 == 0 or not oel[max(0, y - 2):y + 3, max(0, x - 2):x + 3].all():
                continue
            a[y - 1, x] = (120, 100, 80); a[y, x - 1] = (60, 48, 40); a[y, x + 1] = (24, 18, 14); a[y + 1, x] = (24, 18, 14)
    kante = m & ~(np.roll(m, 1, 0) & np.roll(m, -1, 0) & np.roll(m, 1, 1) & np.roll(m, -1, 1))
    a[kante] = (22, 12, 8)


def eisenzaun(img, rect, offen):
    """Eisenzaun der Gefangenen-Pferche (Vorlage): dunkle blaugraue Stangen alle 8 px mit Spitze, zwei Querstreben,
    Schatten nach rechts unten. offen: 'unten_rechts' / 'unten_links' = dort ist die Unterseite zur Haelfte offen."""
    a = np.array(img).astype(np.int16)
    x0, y0, x1, y1 = rect
    K, M, L = (24, 28, 40), (58, 66, 86), (104, 116, 140)
    def stange(x, yb, hh=14):
        for y in range(yb - hh, yb + 1):
            a[y, x - 1] = K + (255,); a[y, x] = M + (255,); a[y, x + 1] = K + (255,)
            a[y, x - 1 + 0, :3] = K
        a[yb - hh - 1, x] = L + (255,); a[yb - hh - 2, x] = K + (255,)
        for d in range(1, 4):
            a[yb + d, x + d - 1, :3] = (a[yb + d, x + d - 1, :3] * 0.7).astype(np.int16)
    def strebe(xa, xb, y):
        a[y, xa:xb, :3] = M; a[y - 1, xa:xb, :3] = L; a[y + 1, xa:xb, :3] = K
        a[y + 3, xa + 2:xb + 2, :3] = (a[y + 3, xa + 2:xb + 2, :3] * 0.75).astype(np.int16)
    yt, yb_ = y0 * T + 13, y1 * T + 13
    X0, X1 = x0 * T + 4, x1 * T + 12
    strebe(X0, X1, yt - 9); strebe(X0, X1, yt - 3)                   # oben
    for x in range(X0, X1 + 1, 8):
        stange(x, yt)
    mitte = (X0 + X1) // 2
    ua, ub = (X0, mitte - 24) if offen == 'unten_rechts' else (mitte + 24, X1)
    strebe(ua, ub, yb_ - 9); strebe(ua, ub, yb_ - 3)                # unten (teilweise offen)
    for x in range(ua, ub + 1, 8):
        stange(x, yb_)
    for xs_ in ((X0,) if offen == 'unten_rechts' else (X1,)) + ((X1,) if offen == 'unten_links' else ()):
        pass
    seite = X0 if offen == 'unten_rechts' else X1                    # geschlossene Seite (senkrecht, von oben)
    for y in range(yt, yb_ + 1):
        a[y, seite - 1:seite + 2, :3] = (K, M, K)
    for y in range(yt, yb_ + 1, 8):
        a[y - 1:y + 1, seite - 1:seite + 2, :3] = L
    img.paste(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)), (0, 0))


def gleis(a, x0, x1, y):
    """Lorenbahn waagerecht im Stil der Loren-Sprites (PixelLab k24_loren): Schotterbett, Holzschwellen mit
    dunkler Kontur und Lichtkante oben links, zwei blaugraue Stahlschienen. Die Enden laufen rund aus."""
    Y = y * T
    X0, X1 = x0 * T + 4, (x1 + 1) * T - 4
    rng = np.random.RandomState(24)
    for yy in range(Y + 1, Y + 16):                                  # Schotterbett, etwas dunkler, gesprenkelt
        for xx in range(X0 - 3, X1 + 3):
            if (yy in (Y + 1, Y + 15)) and (xx < X0 or xx >= X1):
                continue
            f = 0.82 if rng.rand() < 0.75 else (0.68 if rng.rand() < 0.5 else 0.95)
            a[yy, xx] = (a[yy, xx] * f).astype(np.uint8)
    KO, HO, HL, HD = (58, 14, 16), (122, 82, 54), (150, 106, 70), (92, 58, 38)
    for x in range(X0, X1 - 3, 8):                                   # Schwellen 4 px breit, 12 px lang
        a[Y + 1:Y + 15, x:x + 4] = KO                                # Schwelle ragt oben und unten ueber die Schienen
        a[Y + 2:Y + 14, x + 1:x + 3] = HO
        a[Y + 2, x + 1:x + 3] = HL
        a[Y + 2:Y + 14, x + 1] = HL
        a[Y + 13, x + 1:x + 3] = HD
        a[Y + 15, x + 1:x + 4] = (a[Y + 15, x + 1:x + 4] * 0.7).astype(np.uint8)   # Schatten unter der Schwelle
    for ys in (Y + 4, Y + 10):                                       # Schienen schmal: Kontur, Lauffläche, Unterseite
        a[ys - 1, X0:X1] = (18, 51, 58)
        a[ys, X0:X1] = (124, 149, 187)
        a[ys + 1, X0:X1] = (58, 36, 32)
        a[ys + 2, X0:X1] = (a[ys + 2, X0:X1] * 0.78).astype(np.uint8)   # Schlagschatten der Schiene
        for xe in (X0, X1 - 1):                                      # Schienenenden mit Kontur
            a[ys - 1:ys + 2, xe] = (18, 51, 58)


def seilbahn(img, maste, cache, frame):
    """Seilbahn vom Schrein zu den Kraenen: Seil von Radmitte zu Radmitte (laeuft hinter dem unteren Mast),
    zwei Gondeln haengen am Seil und wippen am Haken (Nutzer: nicht fahren, 4 Bilder). Kein Bodenschatten: die Gondeln haengen
    hoch ueber Fels und Canyon."""
    oben = [o for o in maste if o['seil'] == 'oben']
    unten = [o for o in maste if o['seil'] == 'unten']
    if not oben or not unten:
        return
    o1, o2 = oben[0], unten[0]
    cx = o1['x'] + 17
    y0, y1 = o1['y'] + 9, o2['y'] + 9
    a = np.array(img)
    sp2 = np.array(cache[o2['datei']])[..., 3] > 0
    for y in range(y0, y1 + 1):
        ly, lx = y - o2['y'], cx - o2['x']
        if 0 <= ly < sp2.shape[0] and 0 <= lx < sp2.shape[1] and sp2[ly, lx]:
            continue                                                 # hinter dem unteren Mast
        a[y, cx, :3] = (28, 32, 40)
        a[y, cx + 1, :3] = (96, 104, 120)
    gon = Image.open(os.path.join(OBJ, 'gondel', '00.png')).convert('RGBA')
    im = Image.fromarray(a).convert("RGBA")
    L = y1 - y0 - gon.height - 24
    for i, f in enumerate((0.25, 0.62)):                              # stehen still und wippen (Nutzer)
        gy = y0 + 12 + int(f * L)
        winkel = round(3.0 * math.sin(2 * math.pi * frame / N_FRAMES + i * math.pi), 1)   # ein ruhiger Schwung pro Schleife
        g = gon.rotate(winkel, resample=Image.NEAREST, center=(gon.width // 2, 0)) if winkel else gon
        im.alpha_composite(g, (cx - 11 + 1, gy))
    img.paste(im.convert(img.mode))


# Weitere Felsebenen rechts (Nutzer, rote Linien): Kachel-Polygone, rechts/oberhalb der Linie liegt die hoehere Ebene
EBENE3 = [(80, -1), (85, 15), (82, 24), (73, 30), (71, 41), (73, 54), (80, 56), (90, 57), (101, 58), (101, -1)]
EBENE4 = [(89, -1), (92, 12), (90, 19), (94, 17), (101, 16), (101, -1)]


def hoehere_felsen(hp):
    """Wie der vorhandene Fels: am Kachelraster mit unregelmaessigen Stufen (Nutzer). Die Linie wird je Kachel mit
    leichtem Rauschen (ca. 1 Kachel, Wellenlaenge ~3 Kacheln) gerastert, Einzelkacheln werden entfernt; die
    runden Ecken entstehen danach wie ueberall mit weich()."""
    from PIL import ImageDraw as _ID
    Hh, W = hp.shape
    R, C = Hh // T, W // T
    ht = hp[::T, ::T]
    fels = ht >= 2
    for _ in range(3):                                               # 3 Kacheln Abstand zum unteren Felsrand
        f = fels.copy()
        f[1:] &= fels[:-1]; f[:-1] &= fels[1:]; f[:, 1:] &= fels[:, :-1]; f[:, :-1] &= fels[:, 1:]
        fels = f
    rng = np.random.RandomState(24)
    grob = rng.uniform(-1, 1, (R // 3 + 3, C // 3 + 3, 2))
    yy, xx = np.mgrid[0:R, 0:C]
    def rausch(k):
        g = Image.fromarray(((grob[..., k] + 1) * 127).astype(np.uint8)).resize((C + 9, R + 9), Image.BICUBIC)
        return (np.array(g, np.float32)[:R, :C] / 127.0 - 1) * 1.3
    nx, ny = rausch(0), rausch(1)
    for stufe, poly in ((3, EBENE3), (4, EBENE4)):
        m = Image.new('L', (C * 8, R * 8), 0)                        # feines Polygon, dann je Kachel abgetastet
        _ID.Draw(m).polygon([(x * 8, y * 8) for x, y in poly], fill=255)
        m = np.array(m) > 0
        sx = np.clip(((xx + 0.5 + nx) * 8).astype(int), 0, C * 8 - 1)
        sy = np.clip(((yy + 0.5 + ny) * 8).astype(int), 0, R * 8 - 1)
        k = m[sy, sx]
        for _ in range(2):                                           # keine einzelnen Zacken/Loecher
            nb = (np.roll(k, 1, 0).astype(int) + np.roll(k, -1, 0) + np.roll(k, 1, 1) + np.roll(k, -1, 1))
            k = np.where(k & (nb <= 1), False, np.where(~k & (nb >= 3), True, k))
        k &= fels & (ht >= stufe - 1)
        ht = np.where(k, stufe, ht)
    return np.where(np.kron(ht, np.ones((T, T), int)) > hp, np.kron(ht, np.ones((T, T), int)), hp)


SEIL_RAD = (110, 64)                  # Austritt des Seils am Seilrad der Bergstation (Sprite-Pixel)
SEIL_ENDE = (1600, 150)               # das Seil laeuft nach Nordosten aus der Karte (Nutzer, blaue Linie)


def stahlseil(img, stationen, frame):
    """Stahlseil von der Bergstation nach Nordosten, daran eine grosse Gondel (Nutzer: lila). Das Seil haengt hoch
    ueber dem Fels: kein Bodenschatten. Die Gondeln fahren nicht, sie wippen am Haken (Nutzer, 4 Bilder)."""
    if not stationen:
        return
    o = stationen[0]
    x0, y0 = o['x'] + SEIL_RAD[0], o['y'] + SEIL_RAD[1]
    x1, y1 = SEIL_ENDE
    a = np.array(img)
    n = int(max(abs(x1 - x0), abs(y1 - y0)))
    for i in range(n + 1):
        x = int(round(x0 + (x1 - x0) * i / n)); y = int(round(y0 + (y1 - y0) * i / n))
        if 0 <= y < a.shape[0] and 0 <= x < a.shape[1] - 2:
            a[y, x, :3] = (24, 28, 36); a[y, x + 1, :3] = (110, 120, 138); a[y, x + 2, :3] = (24, 28, 36)
    im = Image.fromarray(a).convert('RGBA')
    gon = Image.open(os.path.join(OBJ, 'gondel_gross', '00.png')).convert('RGBA')
    ga = np.array(gon)[..., 3] > 0                                    # Haken = Mitte der obersten Pixelzeile
    hy = int(np.nonzero(ga.any(1))[0][0]); hx = np.nonzero(ga[hy])[0]
    HAKEN = (int(round(hx.mean())), hy)
    for i, t in enumerate((0.32, 0.72)):                             # zwei Gondeln (Nutzer): stehen still und wippen
        gx, gy = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
        winkel = round(2.5 * math.sin(2 * math.pi * frame / N_FRAMES + i * math.pi), 1)           # Schaukeln als Ganzes um den Haken am Seil
        g = gon.rotate(winkel, resample=Image.NEAREST, center=(HAKEN[0], HAKEN[1])) if winkel else gon
        im.alpha_composite(g, (int(gx) - HAKEN[0], int(gy) - HAKEN[1]))
    img.paste(im.convert(img.mode))


def bauen(frame=None, speichern=True):
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cls = lay['klassen']
    cols, rows = lay['groesse']
    Wp, Hp = cols * T, rows * T
    hp = np.kron(np.array([[int(c) for c in z] for z in lay['hoehe']]), np.ones((T, T), int))
    hp = hoehere_felsen(hp)                                          # zwei weitere Felsebenen rechts (Nutzer)
    basis = os.path.join(ROOT, 'assets', 'basis')
    boden = flaeche(k6.kacheln(os.path.join(basis, 'sand_%d.png'), 5, faerben((150, 82, 50), (214, 140, 96))), cols, rows)
    weg = flaeche(k6.kacheln(os.path.join(basis, 'sand_%d.png'), 5, faerben((160, 118, 76), (214, 172, 120))), cols, rows)
    sand = flaeche(k6.kacheln(os.path.join(basis, 'sand_%d.png'), 5), cols, rows)
    fels = flaeche(k6.kacheln(os.path.join(ROOT, 'assets', 'karte03', 'basis', 'kies_%d.png'), 5,
                              faerben((120, 58, 32), (214, 132, 84), 0.25, 0.6)), cols, rows)
    a = boden.copy()
    m = weich(zell_maske(cls, 'wtT', cols, rows), 5.0, 0, 4)        # Regel 6b: 45-Grad-Kanten
    a[m] = weg[m]
    s = weich(zell_maske(cls, 's', cols, rows), 6.0, 0.5, 5)
    a[s] = sand[s]
    saum = weich(zell_maske(cls, 's', cols, rows), 6.0, 0.5, 5, 0.36) & ~s
    a[saum] = (a[saum] * 0.92).astype(np.uint8)
    hoch2 = weich((hp >= 2).astype(np.float32), 5, 0.0, 7, 0.5)       # Felskanten rund statt Kachelstufen
    h1m = weich((hp >= 1).astype(np.float32), 5, 0.0, 7, 0.5)
    a[hoch2] = fels[hoch2]
    hoch1 = (hp == 1)
    a[hoch1] = (boden[hoch1] * 1.04).clip(0, 255).astype(np.uint8)
    a[hoch1 & s] = sand[hoch1 & s]
    # Kanten: erst Arena/Schrein (+Fels) gegen den Boden, dann der Fels gegen alles
    frei = np.zeros((Hp, Wp), bool)
    for (x0, x1) in lay['arena_treppen'] + [tuple(lay['schrein_treppe'])]:
        col = np.nonzero(hp[:, ((x0 + x1 + 1) * T) // 2] == 1)[0]
        frei[:, x0 * T:(x1 + 1) * T] |= False
    tmask = zell_maske(cls, 't', cols, rows) > 0.5
    ya_, yb_ = lay['arena_links']
    frei_t = np.kron(np.array([[c == 't' and not (ya_ <= y <= yb_) for c in z] for y, z in enumerate(cls)]),
                     np.ones((T, T), bool))                         # nur die Arena-Treppen schneiden den Fels
    frei_t = frei_t | np.roll(frei_t, -T, 0) | np.roll(frei_t, -2 * T, 0)
    ya_, yb_ = lay['arena_links']                                    # Aufgang links: keine Kante quer ueber den Weg
    tx_ = [x for y in range(ya_, yb_ + 1) for x in range(cols) if cls[y][x] == 't']
    if tx_:
        frei_t[ya_ * T + FRONT + 2:(yb_ + 1) * T - 3, (min(tx_) - 1) * T:(max(tx_) + 4) * T] = True   # Front bleibt
    wand = k4.hoehenkanten(a, h1m, 'rot', 24, 8, LIPPE_ROT, frei_t, 71, berg=False)
    wand |= k4.hoehenkanten(a, hoch2, 'rot', FRONT, 8, LIPPE_ROT, frei_t & ~h1m, 72, berg=False)
    for st in (3, 4):                                                # hoehere Felsebenen: heller, eigene Front
        hst = weich((hp >= st).astype(np.float32), 5, 0.0, 7, 0.5)
        a[hst] = (fels[hst] * (1 + 0.05 * (st - 2))).clip(0, 255).astype(np.uint8)
        wand |= k4.hoehenkanten(a, hst, 'rot', FRONT, 8, LIPPE_ROT, np.zeros_like(frei_t), 70 + st, berg=False)
    # Treppen der Arena und des Schreins (frontal nach Sueden)
    for (x0, x1) in lay['arena_treppen'] + [tuple(lay['schrein_treppe'])]:
        xc = ((x0 + x1 + 1) * T) // 2
        col = np.nonzero(hp[:, xc] == 1)[0]
        ye = int(col.max())
        k4.treppe(a, x0 * T, (x1 + 1) * T, ye, 's', 24, 'rot', weg)
    # Aufgang links: der Weg laeuft als Rampe hinauf
    ya, yb = lay['arena_links']
    rm = np.zeros((Hp, Wp), bool)
    tl = []                                                          # Aufgang links entfernt (Nutzer)
    if tl:
        xs = [x for _, x in tl]
        x0, x1 = min(xs) * T, (max(xs) + 3) * T
        rm[ya * T:(yb + 1) * T, x0:x1] = True
        rm = weich(rm.astype(np.float32), 5, 0.4, 9) & ~wand & ~hoch2   # Weg nur auf dem Boden, Waende liegen darueber
        a[rm] = weg[rm]
    # Gruben, Gleis, Teleporter
    xm = zell_maske(cls, 'x', cols, rows) > 0.5
    xm[:30 * T] = False                                           # oben: liegender Obelisk der Vorlage, keine Grube
    xm &= (hp == 0) & ~wand                                       # Becken im Boden, nie auf Fels oder Wand (Nutzer)
    from PIL import ImageFilter as _IF
    xm = np.array(Image.fromarray((xm * 255).astype(np.uint8)).filter(_IF.MinFilter(5))) > 0      # Abstand zur Wand
    nah = np.array(Image.fromarray((((hp > 0) | wand) * 255).astype(np.uint8)).filter(_IF.MaxFilter(13))) > 0
    xm = weich(xm.astype(np.float32), 6, 0.25, 21, 0.5) & ~nah                                       # rund, Abstand zum Fels
    grube(a, xm, frame)
    gx0, gx1, gy = lay['gleis']
    gleis(a, gx0, gx1, gy)
    for tp in lay['teleporter']:                                  # nur Kacheln ohne Felswand darueber (Nutzer)
        frei_r = [ty for ty in range(tp['y'], tp['y'] + tp['h'])
                  if not wand[ty * T:(ty + 1) * T, tp['x'] * T:(tp['x'] + tp['b']) * T].any()]
        if frei_r:
            k4.teleporter_zeichnen(a, tp['x'], frei_r[0], tp['b'], len(frei_r), frame)
    img = Image.fromarray(a).convert('RGBA')
    zf = os.path.join(OBJ, 'zaeune.json')
    if os.path.exists(zf):
        boden_ok = (hp == 0) & ~wand
        for (x0, y0, x1, y1, offen) in json.load(open(zf)):
            vor = np.array(img)
            eisenzaun(img, (x0, y0, x1, y1), offen)
            nach = np.array(img)
            nach[~boden_ok] = vor[~boden_ok]                      # Zaun nie ueber Fels oder Felswand
            img = Image.fromarray(nach).copy()
    lvl = hp.astype(np.uint8) + 1
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain_basis.png'))
        np.save(os.path.join(KARTE, 'pixelhoehe.npy'), lvl)
        np.save(os.path.join(KARTE, 'wand.npy'), np.packbits(wand))
        np.save(os.path.join(KARTE, 'wasser.npy'), np.packbits(xm))
    pf = os.path.join(OBJ, 'platzierung.json')
    if os.path.exists(pf):
        objs = sorted((o for o in json.load(open(pf)) if os.path.exists(os.path.join(OBJ, o['datei']))),
                      key=lambda o: o['y'] + o['fuss'])
        if objs:
            cache = {o['datei']: Image.open(os.path.join(OBJ, o['datei'])).convert('RGBA') for o in objs}
            ebenen = lvl.copy().astype(np.int16)
            ebenen[wand] = 9
            ebenen[xm] = 7
            vor = np.array(img)
            k4.objekte_zeichnen(img, objs, cache, ~xm & ~wand, frame, ebenen=ebenen)
            nach = np.array(img)                                     # Fels/Felswand liegt ueber Objekten 'hinter_fels'
            fels = (hp >= 1) | wand
            for o in objs:
                if o.get('hinter_fels'):
                    sp = cache[o['datei']]
                    y0_, x0_ = max(0, o['y']), max(0, o['x'])
                    y1_, x1_ = min(Hp, o['y'] + sp.height + 6), min(Wp, o['x'] + sp.width + 6)
                    m_ = fels[y0_:y1_, x0_:x1_]
                    nach[y0_:y1_, x0_:x1_][m_] = vor[y0_:y1_, x0_:x1_][m_]
            img = Image.fromarray(nach).copy()
            k4.animieren(img, objs, cache, frame or 0)
            kb.laternen_licht(img, [o for o in objs if o.get('anim') == 'laterne'], frame)
            seilbahn(img, [o for o in objs if o.get('seil') in ('oben', 'unten')], cache, frame or 0)
            stahlseil(img, [o for o in objs if o.get('seil') == 'station'], frame or 0)
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain.png'))
    print('Karte 24 %dx%d gebaut' % (cols, rows))
    return img


if __name__ == '__main__':
    bauen()
