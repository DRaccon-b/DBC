"""Karte 23 - Harvest Hills (A02), Gelaende im Stil von Karte 20 / 21 (Bausteine Karte 01/04/06).

Gras/Sand aus Karte 01, weiche Raender, Waldboden, Hofboden (trockene Erde wie das Feld von Karte 20), sechs Aecker
mit Furchen (Karte 20), Teich mit Bach nach Sueden (vertieftes Wasser wie Karte 20), Plateau oben mit Erd-Felsfront,
Treppe und Hoehle (Karte 04), Terrassen oben rechts mit Steinfronten und drei Treppen, Senke unten rechts mit
Felsrand und Treppe, Maeuerchen, Hecken (Karte 04), Holzzaun (Karte 06), Teleporter an beiden Ausgaengen.

  python3 tools/karte23_layout.py && python3 tools/karte23_bauen.py
"""
import json, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
import karte_bauen as kb
import karte04_bauen as k4
import karte06_bauen as k6
import karte20_bauen as k20

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte23')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte23')
T = 16
N_FRAMES = 4
BILDDAUER = 250
k4.N_FRAMES = N_FRAMES
import karte_bauen as _kb
_kb.N_FRAMES = N_FRAMES                       # Windwelle (Pflanzen) ueber die 4 Bilder der Karte
H = k4.H
weich, zell_maske, flaeche = k4.weich, k4.zell_maske, k20.flaeche
k4.RASTER45 = True                       # Nutzer: ALLE Bodenkanten am 16er-Raster mit 45 Grad (Regel 6b)
k4.FELS['stein'] = ['#2e2c2a', '#46423e', '#5e5952', '#77716a', '#908a82', '#aaa49a', '#c6c0b4']   # Steinmauern (Vorlage grau)
FRONT = 32


def maske_aus(cls, arten, cols, rows):
    return np.kron(np.array([[c in arten for c in z] for z in cls]), np.ones((T, T), bool))


def hoehen_px(lay):
    h = np.array([[int(c) for c in z] for z in lay['hoehe']])
    return np.kron(h, np.ones((T, T), int))


def maeuerchen(a, m, seed=3):
    """Niedrige Feldsteinmauer (1 Kachel): Deckstein hell, darunter Feldsteine, Kontaktschatten."""
    rnd = random.Random(seed)
    F = [np.array(H(c), np.float32) for c in k4.FELS['stein']]
    ys, xs = np.nonzero(m)
    for (y0, y1, x0, x1) in [(ys.min(), ys.max() + 1, xs.min(), xs.max() + 1)]:
        pass
    Hh, W = m.shape
    zeilen = sorted(set(ys // T))
    laeufe = []
    for ty in zeilen:                                                   # zusammenhaengende Stuecke je Reihe
        reihe = m[ty * T:(ty + 1) * T].any(axis=0)
        xs_ = np.nonzero(reihe)[0]
        start = xs_[0]
        for i in range(1, len(xs_) + 1):
            if i == len(xs_) or xs_[i] != xs_[i - 1] + 1:
                laeufe.append((ty, start, xs_[i - 1] + 1))
                if i < len(xs_):
                    start = xs_[i]
    for (ty, x0, x1) in laeufe:
        Y = ty * T + 3                                                  # Mauer 3..13 in der Kachel
        a[Y:Y + 3, x0:x1] = F[5]
        a[Y, x0:x1] = F[6]
        a[Y + 2, x0:x1] = F[3]
        x = x0
        r = 0
        while x < x1:
            w = rnd.randint(6, 10)
            t = rnd.choice((3, 4, 4, 5))
            for yy in range(Y + 3, Y + 10):
                for xx in range(x, min(x + w, x1)):
                    dy, dx = yy - (Y + 3), xx - x
                    c = F[1] if (dx == w - 1 or dy == 6) else F[t + 1] if (dy == 0 or dx == 0) else F[t]
                    a[yy, xx] = c
            x += w
        a[Y:Y + 10, x0] = F[1]; a[Y:Y + 10, x1 - 1] = F[1]
        for d, f in ((10, 0.6), (11, 0.75), (12, 0.88)):
            a[Y + d, x0 + 1:x1 + 1] = (a[Y + d, x0 + 1:x1 + 1] * f).astype(np.uint8)


def hoehle(a, x0, x1, ytop, ybot):
    """Hoehleneingang in der Erd-Felsfront: dunkle Oeffnung mit runder Oberkante, Rand aus dunklem Fels."""
    F = [np.array(H(c), np.float32) for c in k4.FELS['erde']]
    cx = (x0 + x1) / 2.0
    hw = (x1 - x0) / 2.0 - 5
    oben = ytop + 6
    for y in range(ytop, ybot):
        for x in range(x0, x1):
            dx = abs(x + 0.5 - cx)
            gr = hw if y >= oben + hw else (hw ** 2 - (oben + hw - y) ** 2) ** 0.5 if (oben + hw - y) < hw else -1
            if dx <= gr:
                t = (y - oben) / max(1, ybot - oben)
                a[y, x] = np.array((22, 14, 10), np.float32) * (0.7 + 0.5 * dx / max(1, hw)) + 6 * (1 - t)
            elif dx <= gr + 2:
                a[y, x] = F[0] if x > cx else F[1]


def braun(a):                     # Sandkacheln von Karte 01 -> Erdboden im selben Kachelstil (Hof, Erdflecken, Felsrand)
    l = a.mean(axis=2, keepdims=True) / 255.0
    lo, hi = np.array([112, 78, 48], np.float32), np.array([198, 160, 108], np.float32)
    return lo + (hi - lo) * np.clip((l - 0.45) / 0.45, 0, 1)


def acker(a, m, erde):
    """Gepfluegter Acker im Kachelstil: Erdkacheln (wie Hof/Wege), quer liegende Furchen alle 8 px - Kamm mit
    Lichtkante oben, Flanke, dunkle Rinne -, kleine Erdkruemel, Rand leicht erhoeht (heller) mit dunkler Kante."""
    Hh, W = m.shape
    yy, xx = np.mgrid[0:Hh, 0:W]
    ys, xs = np.nonzero(m)
    y0 = ys.min()
    r = (yy - y0) % 8
    basis = erde.astype(np.float32) * 0.78
    f = np.select([r == 0, r == 1, r <= 4, r == 5, r == 6], [1.22, 1.12, 1.0, 0.86, 0.66], 0.72)
    neu = np.clip(basis * f[..., None], 0, 255)
    rs = np.random.RandomState(int(y0) * 7 + int(xs.min()))
    kr = rs.rand(Hh, W) < 0.035
    neu[kr & (r <= 3)] = np.clip(neu[kr & (r <= 3)] * 1.18, 0, 255)  # Kruemel auf den Kaemmen
    a[m] = neu[m].astype(np.uint8)
    rand = m & ~(np.roll(m, 2, 0) & np.roll(m, -2, 0) & np.roll(m, 2, 1) & np.roll(m, -2, 1))
    a[rand] = np.clip(erde[rand] * 0.95, 0, 255).astype(np.uint8)      # Feldrand (Erdwall)
    kante = m & ~(np.roll(m, 1, 0) & np.roll(m, -1, 0) & np.roll(m, 1, 1) & np.roll(m, -1, 1))
    a[kante] = (erde[kante] * 0.6).astype(np.uint8)


def hecken(img, lay, cls):
    """Hecken aus dem PixelLab-Objekt (k23_hecke): waagerecht nahtlose Stuecke mit runden Enden, senkrecht
    gestapelte Heckenbloecke; Schatten der Silhouette nach rechts unten."""
    d = os.path.join(OBJ, 'hecke')
    seg = Image.open(os.path.join(d, '00.png')).convert('RGBA')
    rund = Image.open(os.path.join(d, '01.png')).convert('RGBA')
    block = Image.open(os.path.join(d, '02.png')).convert('RGBA')
    senk = Image.open(os.path.join(OBJ, 'hecke_senk', '00.png')).convert('RGBA')
    kappe = Image.open(os.path.join(OBJ, 'hecke_senk', '02.png')).convert('RGBA')

    def angleichen(sp):                                                # senkrechte Hecke in die Farbpalette der waagerechten:
        q = np.array(seg).astype(np.float32); z = np.array(sp).astype(np.float32)   # Helligkeits-Rang -> Farbe
        qm, zm = q[..., 3] > 0, z[..., 3] > 0
        ql = q[qm][:, :3] @ np.array([0.3, 0.59, 0.11]); qc = q[qm][:, :3][np.argsort(ql)]
        zl = z[zm][:, :3] @ np.array([0.3, 0.59, 0.11])
        rang = np.argsort(np.argsort(zl)) / max(1, len(zl) - 1)
        z[zm, :3] = qc[np.clip((rang * (len(qc) - 1)).round().astype(int), 0, len(qc) - 1)]
        return Image.fromarray(z.astype(np.uint8))
    senk, kappe = angleichen(senk), angleichen(kappe)
    # Endstueck unten: aus dem runden waagerechten Heckenstueck (Oberseite + Vorderseite) die linken und rechten
    # Haelften auf die Breite der senkrechten Hecke zusammengesetzt -> gleiche Perspektive wie die waagerechten Hecken
    hb = senk.width // 2
    block = Image.new('RGBA', (senk.width, rund.height), (0, 0, 0, 0))
    block.paste(rund.crop((0, 0, hb, rund.height)), (0, 0))
    block.paste(rund.crop((rund.width - (senk.width - hb), 0, rund.width, rund.height)), (hb, 0))
    al_ = np.array(block.getchannel('A')) > 0
    ob = int(np.nonzero(al_[:, senk.width // 2])[0].min())
    block = block.crop((0, ob + 3, senk.width, block.height))           # ohne obere Kontur -> nahtlos an die Hecke
    lage = Image.new('RGBA', img.size, (0, 0, 0, 0))
    for (x0, y0, x1, y1) in lay['hecken']:
        if y0 == y1:                                                   # waagerecht
            X0, X1 = x0 * T, (x1 + 1) * T
            Y = (y0 + 1) * T - seg.height - 1
            x = X0
            while x < X1:
                w = min(seg.width, X1 - x)
                lage.alpha_composite(seg.crop((0, 0, w, seg.height)), (x, Y))
                x += w
            h2 = rund.width // 2
            lage.paste(Image.new('RGBA', (h2, rund.height), (0, 0, 0, 0)), (X0, Y))
            lage.alpha_composite(rund.crop((0, 0, h2, rund.height)), (X0, Y))
            lage.paste(Image.new('RGBA', (rund.width - h2, rund.height), (0, 0, 0, 0)), (X1 - (rund.width - h2), Y))
            lage.alpha_composite(rund.crop((h2, 0, rund.width, rund.height)), (X1 - (rund.width - h2), Y))
        else:                                                          # senkrecht: neue senkrechte Heckenstuecke
            X = x0 * T + (T - senk.width) // 2
            Y0, Y1 = y0 * T - 8, (y1 + 1) * T - 2
            Y1s = Y1 - block.height + 1                                # unten endet die Hecke mit dem Endstueck:
            y = Y0                                                     # Oberseite + sichtbare Vorderseite (Perspektive)
            while y < Y1s:
                hh = min(senk.height, Y1s - y)
                lage.alpha_composite(senk.crop((0, 0, senk.width, hh)), (X, y))
                y += hh
            kap = kappe.crop((0, 0, kappe.width, 10))                     # runde Kappe oben
            lage.paste(Image.new('RGBA', kap.size, (0, 0, 0, 0)), (X, Y0))
            lage.alpha_composite(kap, (X, Y0))
            lage.alpha_composite(block, (x0 * T + (T - block.width) // 2, Y1 - block.height))
    mauer = Image.open(os.path.join(OBJ, 'mauer', '00.png')).convert('RGBA')
    for (x0, y0, x1, y1) in lay['maeuerchen']:                          # Feldsteinmauern (PixelLab k23_mauer)
        X0, X1 = x0 * T, (x1 + 1) * T
        Y = (y0 + 1) * T - mauer.height - 1
        x = X0
        while x < X1:
            w = min(mauer.width, X1 - x)
            lage.alpha_composite(mauer.crop((0, 0, w, mauer.height)), (x, Y))
            x += w
    # Enden sauber abschliessen: Schnittkanten bekommen die dunkle Kontur des Sprites, Ecken abgerundet
    L = np.array(lage)
    def kante_schliessen(x0_, x1_, y0_, y1_, seite):
        sub = L[y0_:y1_, x0_:x1_]
        al_ = sub[..., 3] > 0
        if not al_.any():
            return
        hell = sub[..., :3].astype(int).sum(-1)
        dunkel = sub[al_][:, :3][np.argmin(hell[al_])]
        if seite in ('l', 'r'):
            cols_ = [0, 1] if seite == 'l' else [sub.shape[1] - 1, sub.shape[1] - 2]
            ys_ = np.nonzero(al_[:, cols_[0]])[0]
            if not len(ys_):
                return
            ya, yb = ys_.min(), ys_.max()
            for yy_ in (ya, ya + 1, yb - 1, yb):                      # runde Ecken
                sub[yy_, cols_[0], 3] = 0
            sub[ya, cols_[1], 3] = 0; sub[yb, cols_[1], 3] = 0
            for yy_ in range(ya + 2, yb - 1):
                sub[yy_, cols_[0], :3] = dunkel
            for yy_ in (ya + 1, yb - 1):
                sub[yy_, cols_[1], :3] = dunkel
        else:                                                         # unten
            xs_ = np.nonzero(al_[-1])[0] if al_[-1].any() else np.nonzero(al_.any(0))[0]
            xa, xb = xs_.min(), xs_.max()
            yb = sub.shape[0] - 1
            for xx_ in (xa, xa + 1, xb - 1, xb):
                sub[yb, xx_, 3] = 0
            sub[yb - 1, xa, 3] = 0; sub[yb - 1, xb, 3] = 0
            sub[yb, xa + 2:xb - 1, :3] = dunkel
            sub[yb - 1, xa + 1, :3] = dunkel; sub[yb - 1, xb - 1, :3] = dunkel
            sub[yb - 3:yb - 1, xa + 2:xb - 1, :3] = (sub[yb - 3:yb - 1, xa + 2:xb - 1, :3] * 0.75).astype(np.uint8)
    for (x0, y0, x1, y1) in lay['maeuerchen']:
        Y = (y0 + 1) * T - mauer.height - 1
        kante_schliessen(x0 * T, x0 * T + 4, Y, Y + mauer.height, 'l')
        kante_schliessen((x1 + 1) * T - 4, (x1 + 1) * T, Y, Y + mauer.height, 'r')
    lage = Image.fromarray(L)
    al = np.array(lage.getchannel('A')) > 0
    sch = np.zeros_like(al)
    sch[3:, 2:] = al[:-3, :-2]
    sch &= ~al
    base = np.array(img).astype(np.float32)
    base[sch, :3] *= 0.68
    img.paste(Image.fromarray(base.astype(np.uint8)), (0, 0))
    img.alpha_composite(lage)


def felsboden(a, m, seed=61):
    """Steiniger Erdboden am Senkenrand: dicht gesetzte runde Feldsteine (Licht oben links, Schatten unten rechts)
    in brauner Erde, dazwischen dunkle Fugen."""
    rnd = random.Random(seed)
    Hh, W = m.shape
    F = [np.array(H(c), np.float32) for c in ('#3e2c1e', '#5a4130', '#76583e', '#8e6e4e', '#a8865f', '#c4a276', '#dcc09a')]
    ys, xs = np.nonzero(m)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    sub = np.zeros((y1 - y0, x1 - x0, 3), np.float32); sub[:] = F[1]
    yy, xx = np.mgrid[0:y1 - y0, 0:x1 - x0]
    for r, cy in enumerate(range(2, y1 - y0 + 6, 7)):
        cx = rnd.randint(-4, 2) + (4 if r % 2 else 0)
        while cx < x1 - x0 + 6:
            rx, ry = rnd.uniform(3.6, 5.2), rnd.uniform(2.8, 3.8)
            px, py = cx + rnd.uniform(-1, 1), cy + rnd.uniform(-1, 1)
            t = rnd.choice((3, 3, 4, 4, 5))
            d = ((xx - px) / rx) ** 2 + ((yy - py) / ry) ** 2
            inn = d <= 1.0
            licht = (-(xx - px) / rx - (yy - py) / ry) * 0.5
            ton = np.clip(t + np.round(licht * 1.5 - (d > 0.75)), 1, 6).astype(int)
            for k in range(1, 7):
                sub[inn & (ton == k)] = F[k]
            cx += 2 * rx + rnd.uniform(0.6, 1.8)
    mm = m[y0:y1, x0:x1]
    a[y0:y1, x0:x1][mm] = sub[mm].astype(np.uint8)


def schlamm(a, m, erde, seed=63):
    """Schlammiger Rand: Erdkacheln dunkler und satter (nass), weiche Flecken, glaenzende Nassstellen (Licht oben
    links) und ein paar kleine Pfuetzen."""
    Hh, W = m.shape
    rs = np.random.RandomState(seed)
    n = rs.rand(Hh // 16 + 2, W // 16 + 2)
    fl = np.array(Image.fromarray((n * 255).astype(np.uint8)).resize((W, Hh), Image.BICUBIC)).astype(np.float32) / 255
    basis = erde.astype(np.float32) * np.array([0.66, 0.56, 0.5]) * (0.86 + 0.22 * fl[..., None])
    a[m] = np.clip(basis[m], 0, 255).astype(np.uint8)
    ys, xs = np.nonzero(m)
    for i in rs.choice(len(ys), max(1, len(ys) // 260), replace=False):   # Nassglanz: kleine helle Sicheln
        y, x = ys[i], xs[i]
        if y + 3 < Hh and x + 5 < W and m[y:y + 3, x:x + 5].all():
            a[y, x + 1:x + 4] = H('#b59a7a'); a[y + 1, x:x + 2] = H('#9c8062')
            a[y + 2, x + 1:x + 5] = (a[y + 2, x + 1:x + 5] * 0.8).astype(np.uint8)
    for i in rs.choice(len(ys), max(1, len(ys) // 2500), replace=False):  # Pfuetzen
        y, x = ys[i], xs[i]
        yy, xx = np.mgrid[-4:5, -7:8]
        e = (xx / 7.0) ** 2 + (yy / 4.0) ** 2 <= 1
        if 4 <= y < Hh - 5 and 7 <= x < W - 8 and m[y - 4:y + 5, x - 7:x + 8][e].all():
            sub = a[y - 4:y + 5, x - 7:x + 8]
            sub[e] = H('#4c4a48')
            sub[e & (yy <= -2)] = H('#36302c')
            sub[e & (yy == -1) & (xx < -1)] = H('#8a8e94')
            sub[e & (yy == 0) & (xx > -4) & (xx < 0)] = H('#a8b0b8')


SENKE_STIL = os.environ.get('K23_SENKE', 'boeschung')   # gewaehlt: Boeschung (Nutzer)
TEICH_STIL = os.environ.get('K23_TEICH', 'erde')       # erde | sandstein
STUFEN = int(os.environ.get('K23_STUFEN', '2'))         # Terrassen der Senke (Nutzer: Variante A = 3)   # erde | hoch | stein | sandstein | holz | boeschung | karte01


def senkenwand(a, m, stil, front):
    """Wand der Senke nach Stil neu einfaerben (die Form kommt aus hoehenkanten)."""
    if stil in ('erde', 'hoch', 'stein', 'sandstein') or not m.any():
        return
    Hh, W = m.shape
    # Tiefe je Pixel ab Oberkante der Wand
    d = np.zeros((Hh, W), np.int32)
    for y in range(1, Hh):
        d[y] = np.where(m[y], np.where(m[y - 1], d[y - 1] + 1, 0), 0)
    yy, xx = np.mgrid[0:Hh, 0:W]
    if stil == 'holz':                                               # Holzpalisade: senkrechte Bohlen, Pfosten, Querlatte
        HOLZ = [np.array(H(c)) for c in ('#3a220f', '#5c3818', '#7a4c24', '#9a6432', '#b67c44', '#d29c60')]
        b = xx % 6
        c = np.where(b[..., None] == 0, HOLZ[0], np.where(b[..., None] == 1, HOLZ[4], np.where(b[..., None] == 5, HOLZ[1], HOLZ[3])))
        c = np.where((d[..., None] >= front - 3), HOLZ[1], c)
        c = np.where(((d[..., None] == 6) | (d[..., None] == 7)) & (b[..., None] >= 0), HOLZ[2], c)
        c = np.where((xx[..., None] % 24 < 3), np.where((xx[..., None] % 24 == 0), HOLZ[0], HOLZ[5]), c)
        c = np.where(d[..., None] <= 1, HOLZ[5], c)
        a[m] = c[m].astype(np.uint8)
    elif stil == 'boeschung':                                        # Erdboeschung: weiche Schraege von hell nach dunkel
        E = [np.array(H(c), np.float32) for c in ('#5a4030', '#6e4e38', '#836044', '#987252', '#ad8662', '#c29c76')]
        t = np.clip(d / max(1, front - 1), 0, 1)
        idx = np.clip((5 - t * 5).round().astype(int), 0, 5)
        c = np.array(E)[idx]
        rs = np.random.RandomState(5)
        kr = rs.rand(Hh, W) < 0.05
        c[kr] = c[kr] * 0.85
        a[m] = c[m].astype(np.uint8)
    elif stil == 'karte01':                                          # Schieferklippe wie Karte 01 / 21
        import klippen
        w = np.array(klippen.wand(W, front + 2, random.Random(7), rune_chance=0.0).convert('RGB'))
        a[m] = w[np.clip(d[m], 0, front + 1), xx[m]]


def treppe_ost(a, x0, x1, y0, y1, fels, wegtex):
    """Seitliche Treppe an einer Westkante (von West nach Ost abwaerts): Stufen als senkrechte Baender, je Stufe
    Tritt hell, Kante dunkel; oben und unten schmale Wangen."""
    F = [np.array(H(c)) for c in k4.FELS[fels]]
    n = max(3, (x1 - x0) // 6)
    sw = (x1 - x0) / n
    for x in range(x0, x1):
        i = int((x - x0) / sw)
        k = (x - x0) - i * sw
        for y in range(y0, y1):
            if y - y0 < 3:
                c = (F[1], F[5], F[4])[y - y0]                       # Wange oben
            elif y1 - 1 - y < 3:
                c = (F[0], F[2], F[3])[y1 - 1 - y]                   # Wange unten
            elif k < 1:
                c = F[6] if i > 0 else F[5]                            # Lichtkante des Tritts
            elif k >= sw - 1.5:
                c = F[1]                                               # Setzstufe (Schatten)
            else:
                t = i / n
                c = F[5] if t < 0.5 else F[4]
            a[y, x] = c
    for y in range(y0 + 3, y1 - 3):                                    # Kontaktschatten am Fuss (Ostende)
        for d, f in ((0, 0.7), (1, 0.85)):
            if x1 + d < a.shape[1]:
                a[y, x1 + d] = (a[y, x1 + d] * f).astype(np.uint8)


def nach_oben(hoch, bis=4 * T):
    """Hochflaechen, die (fast) am oberen Kartenrand beginnen, bis zum Rand verlaengern - nur in ihren eigenen Spalten
    (keine Kantenstummel am Kartenrand)."""
    out = hoch.copy()
    for x in range(hoch.shape[1]):
        ys = np.nonzero(hoch[:, x])[0]
        if len(ys) and ys.min() <= bis:
            out[:ys.min(), x] = True
    return out


def bauen(frame=None, speichern=True):
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cls = lay['klassen']
    cols, rows = lay['groesse']
    Wp, Hp = cols * T, rows * T
    hp = hoehen_px(lay)
    basis = os.path.join(ROOT, 'assets', 'basis')
    gras = flaeche(k6.kacheln(os.path.join(basis, 'gras_%d.png'), 5), cols, rows)
    sand = flaeche(k6.kacheln(os.path.join(basis, 'sand_%d.png'), 5), cols, rows)
    a = gras.copy()
    wm = weich(zell_maske(cls, 'h', cols, rows), 5, 0.4, 3)
    a[wm] = (gras[wm] * np.array([0.62, 0.7, 0.66])).astype(np.uint8)
    erde = flaeche(k6.kacheln(os.path.join(basis, 'sand_%d.png'), 5, braun), cols, rows)
    fm = weich(zell_maske(cls, 'f', cols, rows), 7.0, 0.5, 9)
    a[fm] = erde[fm]
    saum_f = weich(zell_maske(cls, 'f', cols, rows), 7.0, 0.5, 9, 0.36) & ~fm
    a[saum_f] = (a[saum_f] * 0.9).astype(np.uint8)
    roh = zell_maske(cls, 'wtTc', cols, rows)
    # Regel 6b: Wegkanten in 45 Grad (Kachelmaske Gauss 5 px, Schwelle 50 %) statt ausgefranstem Rand
    from PIL import ImageFilter as _IF
    kach = (np.kron(np.array([[c in 'wtTc' for c in r] for r in cls], np.uint8), np.ones((T, T), np.uint8)) * 255)
    m = np.array(Image.fromarray(kach).filter(_IF.GaussianBlur(5))) > 127
    a[m] = sand[m]
    weg_maske = m.copy()                                              # (m wird spaeter fuer Stufen wiederverwendet)
    m_g = np.array(Image.fromarray(kach).filter(_IF.GaussianBlur(5))) > 70
    saum = m_g & ~m
    a[saum] = (a[saum] * 0.9).astype(np.uint8)
    cm = maske_aus(cls, 'c', cols, rows)
    a[cm] = (a[cm] * 0.92).astype(np.uint8)                          # Senke etwas dunkler
    for (x0, y0, x1, y1, _) in lay['felder']:
        bm = np.zeros((Hp, Wp), bool)
        bm[y0 * T + 2:(y1 + 1) * T - 2, x0 * T + 2:(x1 + 1) * T - 2] = True
        acker(a, bm, erde)
    # ---------------- Hoehen: Plateau (Erde), Terrassen (Stein), Senke (Erde, Felsrand)
    wald = maske_aus(cls, 'h', cols, rows)
    nord = np.zeros((Hp, Wp), bool); nord[:4 * T] = True
    lippe = k20.lippe_aus_gras(gras)
    # Plateau Mitte
    px0, px1 = lay['plateau']['x']
    reg = np.zeros((Hp, Wp), bool); reg[:, (px0 - 1) * T:(px1 + 2) * T] = True
    hoch = (hp >= 2) & reg
    oben2 = np.zeros((Hp, Wp), bool); oben2[:2 * T] = True
    hoch_k = nach_oben(hoch)                                     # oberer Kartenrand gehoert zur Hochflaeche
    frei = np.zeros((Hp, Wp), bool)
    tx0, tx1 = lay['plateau']['treppe']
    ye = (lay['plateau']['unten'][str(tx0)] + 1) * T - 1
    frei[ye - 14:ye + 40, tx0 * T:(tx1 + 1) * T] = True
    wand = k4.hoehenkanten(a, hoch_k, 'erde', FRONT, 8, lippe, frei, 31, berg=False)
    k4.treppe(a, tx0 * T, (tx1 + 1) * T, ye, 's', FRONT, 'erde', sand)
    hx0, hx1 = lay['plateau']['hoehle']
    yh = (lay['plateau']['unten'][str(hx0)] + 1) * T
    hoehle(a, hx0 * T, (hx1 + 1) * T, yh + 2, yh + FRONT)
    # Terrassen oben rechts (zuerst die mittlere, dann die obere in die mittlere hinein)
    reg = np.zeros((Hp, Wp), bool); reg[:, 68 * T:] = True
    hoch = (hp >= 2) & reg
    frei = np.zeros((Hp, Wp), bool)
    trs = lay['terrassen']['treppen']
    for (sx0, sx1, yl) in trs:
        yE = (yl + 1) * T - 1
        frei[yE - 14:yE + 40, sx0 * T:(sx1 + 1) * T] = True
    oben3 = np.zeros((Hp, Wp), bool); oben3[:3 * T] = True
    wand |= k4.hoehenkanten(a, nach_oben(hoch), 'stein', FRONT, 8, lippe, frei, 41, berg=False)
    hoch3 = (hp >= 3) & reg
    reg3 = np.zeros((Hp, Wp), bool); reg3[:, 74 * T:] = True
    wand |= k4.hoehenkanten(a, nach_oben(hoch3), 'stein', FRONT, 8, lippe, frei, 42, berg=False)
    for (sx0, sx1, yl) in trs:
        k4.treppe(a, sx0 * T, (sx1 + 1) * T, (yl + 1) * T - 1, 's', FRONT, 'stein', sand)
    # Senke unten rechts (Nutzer): groesser, in STUFEN Terrassen nach unten, Boeschungswaende, Boden aus Erdkacheln;
    # oben fuehrt der Weg ueber Treppen Stufe fuer Stufe hinunter, links als sanfte Rampe
    def wachsen(m, n):
        for i in range(n):                                            # abwechselnd 4er/8er-Nachbarn -> rundlich, nicht spitz
            m2 = m | np.roll(m, 1, 0) | np.roll(m, -1, 0) | np.roll(m, 1, 1) | np.roll(m, -1, 1)
            if i % 2 == 0:
                for dy in (-1, 1):
                    for dx in (-1, 1):
                        m2 |= np.roll(np.roll(m, dy, 0), dx, 1)
            m = m2
        return m

    def schrumpfen(m, n):
        return ~wachsen(~m, n)
    c_t = np.array([[ch == 'c' for ch in z] for z in cls])
    c_t[:53] = False                                                  # Weg-Zipfel oben nicht mitwachsen lassen (Form bleibt rund)
    stufen = [wachsen(c_t, 3)]                                        # groesser (Nutzer): unten mehr Platz
    for _ in range(STUFEN - 1):
        stufen.append(schrumpfen(stufen[-1], 2))
    px_m = lambda m: weich(np.kron(m, np.ones((T, T))).astype(np.float32), 6, 0.0, 5, 0.5)
    L = [px_m(m) for m in stufen]
    cm = L[0]
    LIPPE_ERDE = ['#4a3424', '#6a4c34', '#7e5e40', '#94714c', '#a8835a', '#bc9a70']
    kc_t = np.array([[ch in 'kc' for ch in z] for z in cls])
    rm = weich(np.kron(wachsen(kc_t, 2), np.ones((T, T))).astype(np.float32), 4, 0.35, 12) & ~cm & ~maske_aus(cls, 'wt', cols, rows)
    a[rm] = erde[rm]                                                  # Rand: Erdkacheln wie der Hof
    for k, m in enumerate(L):                                         # Boeden: Erdkacheln, je Stufe etwas dunkler
        a[m] = (erde[m] * (0.97 - 0.06 * k)).astype(np.uint8)
    # Gaenge: oben (Treppen) und links (Rampe)
    zug_o = [x for x in range(70, 86) if any(cls[y][x] == 'w' for y in range(46, 50)) and c_t[52, x]]
    tz0, tz1 = (min(zug_o), max(zug_o)) if zug_o else (76, 78)
    reihen = [y for y in range(50, 66) if cls[y][66] == 'w' and cls[y][62] == 'w']
    ya, yb = (reihen[0] * T, (reihen[-1] + 1) * T) if reihen else (56 * T, 60 * T)
    gang_o = np.zeros((Hp, Wp), bool); gang_o[44 * T:62 * T, tz0 * T:(tz1 + 1) * T] = True
    gang_l = np.zeros((Hp, Wp), bool); gang_l[ya + 4:yb - 4, 60 * T:77 * T] = True
    frei = gang_o | gang_l
    FR = 12
    for k, m in enumerate(L):                                         # Waende von aussen nach innen
        sw = k4.hoehenkanten(a, ~m, 'erde', FR, 6, LIPPE_ERDE, frei, 51 + k, berg=False)
        senkenwand(a, sw & ~(~m), 'boeschung', FR)
        wand |= sw
    # Treppen im oberen Gang an jeder Stufenkante
    for k, m in enumerate(L):
        col = np.nonzero(m[:, (tz0 * T + (tz1 + 1) * T) // 2])[0]
        if len(col):
            ye = int(col.min()) - 1
            k4.treppe(a, tz0 * T, (tz1 + 1) * T, ye, 's', FR, 'erde', sand if k == 0 else erde)
    # Seitliche Treppen im linken Gang an jeder Stufenkante (Weg fuehrt nicht ohne Stufen in die Senke)
    zeile_ = (ya + yb) // 2
    kanten_ = []
    for k, m_s in enumerate(L):
        xs_ = np.nonzero(m_s[zeile_, 60 * T:77 * T])[0]
        if len(xs_):
            kanten_.append(60 * T + int(xs_.min()))
    if kanten_:
        x_r = kanten_[0] - 3 * T                                     # Wegbreite vor der Senke messen (zusammenhaengend)
        py0 = py1 = zeile_
        while py0 > 0 and weg_maske[py0 - 1, x_r]:
            py0 -= 1
        while py1 < Hp and weg_maske[py1, x_r]:
            py1 += 1
        band0 = np.zeros((Hp, Wp), bool)                              # Weg auch auf dem Rand bis zur ersten Stufe voll breit
        band0[py0:py1, x_r:kanten_[0]] = True
        a[band0] = sand[band0]
        x_e = kanten_[-1] + 3 * T                                     # Weg laeuft ueber die Boeden bis unten weiter
        band = np.zeros((Hp, Wp), bool)
        band[py0:py1, kanten_[0] - 8:x_e] = True
        yy_, xx_ = np.mgrid[0:Hp, 0:Wp]
        band &= ~(((x_e - xx_) + (yy_ - py0) < 8) | ((x_e - xx_) + (py1 - 1 - yy_) < 8))   # 45-Grad-Ende
        a[band] = sand[band]
        for xk in kanten_:                                            # Treppe in voller Wegbreite an jeder Stufe
            treppe_ost(a, xk - 6, xk + 22, py0, py1, 'erde', sand)
    # ---------------- Mauerchen, Hecken
    # ---------------- Wasser (Bach laeuft unten aus der Karte)
    import wasser_vertieft
    # Teich und Bach groesser (Nutzer): eine Kachel breiter nach Osten und Westen (nicht in die Hecke bei x 43)
    x_t = np.array([[ch == 'x' for ch in z] for z in cls])
    g_t = x_t | np.roll(x_t, 1, 1) | np.roll(x_t, -1, 1) | np.roll(x_t, 1, 0)
    g_t[:66, :44] &= x_t[:66, :44]
    teich = g_t.copy(); teich[67:] = False                            # Teich (oberer Teil) weiter nach rechts (Nutzer)
    g_t |= np.roll(teich, 1, 1) | np.roll(teich, 2, 1) | np.roll(teich, 3, 1)
    g_t |= np.roll(g_t, 1, 1)                                         # alles noch eine Kachel breiter (Nutzer)
    xm = weich(np.kron(g_t, np.ones((T, T))).astype(np.float32), 4, 0.15, 8, 0.45)
    P = 24
    ag = np.pad(a, ((0, P), (0, 0), (0, 0)), mode='edge')
    mg = np.pad(xm, ((0, P), (0, 0)), mode='edge')
    alt_mauer = wasser_vertieft.MAUER
    rand_ = None
    if TEICH_STIL == 'sandstein':                                     # Ufer und Beckenrand in Sandstein
        rand_ = ('#6e5236', '#8e6c48', '#ae8a60', '#c8a87a')
        wasser_vertieft.MAUER = [H(c) for c in ('#5a4632', '#76603f', '#927a52', '#ac9468', '#c6ae82', '#dcc8a0')]
    try:                                                              # eine Tiefenstufe (Nutzer)
        ag = np.array(wasser_vertieft.vertiefen(Image.fromarray(ag), np.ones_like(mg), frame, maske=mg, rand=rand_,
                                                stufen=[(16, 0.72, 8)]).convert('RGB'))
    finally:
        wasser_vertieft.MAUER = alt_mauer
    a = ag[:Hp].copy()
    img = Image.fromarray(a).convert('RGBA')
    hecken(img, lay, cls)
    zx0, zy0, zx1, zy1 = lay['zaun']
    k6.zaun(img, (zx0, zy0, zx1, zy1), (-9, -9))
    a = np.array(img.convert('RGB'))
    for tp in lay['teleporter']:
        k4.teleporter_zeichnen(a, tp['x'], tp['y'], tp['b'], tp['h'], frame)
    img = Image.fromarray(a).convert('RGBA')
    lvl = hp.astype(np.uint8) + 1
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain_basis.png'))
        np.save(os.path.join(KARTE, 'wasser.npy'), np.packbits(xm))
        np.save(os.path.join(KARTE, 'pixelhoehe.npy'), lvl)
        np.save(os.path.join(KARTE, 'wand.npy'), np.packbits(wand))
    pf = os.path.join(OBJ, 'platzierung.json')
    if os.path.exists(pf):
        objs = sorted((o for o in json.load(open(pf)) if os.path.exists(os.path.join(OBJ, o['datei']))),
                      key=lambda o: o['y'] + o['fuss'])
        if objs:
            cache = {o['datei']: Image.open(os.path.join(OBJ, o['datei'])).convert('RGBA') for o in objs}
            neu = []                                                 # Windmuehlen (Karte 20): Fluegel je Bild fest ins Sprite
            for o in objs:
                if o.get('anim') == 'muehle20':
                    o = dict(o); o.pop('anim')
                    key_ = o['datei'] + '#f%d' % (frame or 0)
                    cache[key_] = k20.muehle20(cache[o['datei']], frame or 0, dict(o, basis=o['basis']))
                    o['datei'] = key_
                neu.append(o)
            objs = neu
            ebenen = lvl.copy().astype(np.int16)
            ebenen[wand] = 9
            ebenen[xm] = 7
            k4.objekte_zeichnen(img, objs, cache, ~xm & ~wand, frame, ebenen=ebenen)
            k4.animieren(img, objs, cache, frame or 0)
            k6.animieren_k6(img, objs, cache, frame or 0)
            kb.laternen_licht(img, [o for o in objs if o.get('anim') == 'laterne'], frame)
            k20.rauch20(img, objs, cache, frame)
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain.png'))
    print('Karte 23 %dx%d gebaut' % (cols, rows))
    return img


if __name__ == '__main__':
    bauen()
