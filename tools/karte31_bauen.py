"""Karte 31 - Highton View Terrace (A02): Wohnsiedlung am Tag. Gelaende, Stuetzmauer, Hochbahn, Objekte, Animation.

  python3 tools/karte31_layout.py && python3 tools/karte31_bauen.py
  python3 tools/karte31_objekte.py && python3 tools/karte31_bauen.py

Kacheln wie Karte 18/30 (Gehweg, Asphalt, Rasen, Hecke), Erdboden und Parkwege aus der Sandkachel erdig gefaerbt,
Ziegelplatz in Sandstein (Karte 30), Hochbahn aus dem kachelbaren Segment von Karte 30. Neu: Stuetzmauer aus
Steinbloecken mit Heckenkrone (Front 3 Kacheln) und Treppen, Mauer der Portal-Terrasse, Zaun an der Terrassenseite,
gelbe Leitstreifen am Bahnhof.
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageFilter
import karte04_bauen as k4
import karte06_bauen as k6
import karte18_bauen as k18
import karte30_bauen as k30

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte31')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte31')
T = 16
N_FRAMES = 4
BILDDAUER = 250
k4.N_FRAMES = N_FRAMES
import karte_bauen as _kb
_kb.N_FRAMES = N_FRAMES                       # Windwelle (Pflanzen) ueber die 4 Bilder der Karte
H = k4.H
gross, kontur, dunkeln, mischen = k18.gross, k18.kontur, k18.dunkeln, k18.mischen
GELB = np.array(H('#d8b048'), np.uint8)
WEISS = np.array(H('#e4e8ee'), np.uint8)


def erde(cols, rows, f):
    t = k18.textur('d', cols, rows).astype(np.float32)
    return np.clip(t * np.array(f, np.float32), 0, 255).astype(np.uint8)


def hecke(a, m, seed=31):
    """Hecke (Vorlage: gelbgruene Buschstreifen): Blattbueschel in 3 Gruentoenen (Kreise 3-5 px), oben Lichtkante,
    unten 2 px Schatten, dunkle Kontur zum Boden. Fest je Pixel (kein Flimmern)."""
    if not m.any():
        return
    rs = np.random.RandomState(seed)
    a[m] = H('#6e9a3c')
    ys, xs = np.nonzero(m)
    for _ in range(len(ys) // 10):
        i = rs.randint(len(ys))
        y, x, r = ys[i], xs[i], rs.randint(2, 4)
        c = H(['#5a8432', '#86ae4a', '#9cc05a'][rs.randint(3)])
        yy, xx = np.ogrid[-r:r + 1, -r:r + 1]
        kreis = (yy ** 2 + xx ** 2) <= r * r
        y0, x0 = max(0, y - r), max(0, x - r)
        sub = m[y0:y + r + 1, x0:x + r + 1] & kreis[(y0 - (y - r)):(y0 - (y - r)) + m[y0:y + r + 1, x0:x + r + 1].shape[0],
                                                       (x0 - (x - r)):(x0 - (x - r)) + m[y0:y + r + 1, x0:x + r + 1].shape[1]]
        a[y0:y + r + 1, x0:x + r + 1][sub] = c
    oben = m & ~np.roll(m, 1, 0)
    a[oben] = H('#b0d070')
    unten = m & ~np.roll(m, -1, 0)
    a[unten] = H('#3c5a26'); a[np.roll(unten, -1, 0) & m] = H('#4a6c2e')
    rand = kontur(m) & ~oben & ~unten
    a[rand] = H('#4a6c2e')


def streugut(a, kl, seed=3131):
    """Kleinkram an den Strassen (Nutzer): vereinzelt Laub (unter der Ginkgo-Allee goldgelb, sonst braun/gruen),
    Papierschnipsel, Dosen, Kippen - auf Gehwegen nahe der Fahrbahn und am Fahrbahnrand, unregelmaessig, ohne Reihen.
    Fest je Position (kein Flimmern)."""
    rs = np.random.RandomState(seed)
    R_, C_ = kl.shape
    strasse = kl == 's'
    nah = np.zeros_like(strasse)
    for dy in (-2, -1, 0, 1, 2):
        for dx in (-2, -1, 0, 1, 2):
            nah |= np.roll(np.roll(strasse, dy, 0), dx, 1)
    kandidaten = [(y, x) for y in range(R_) for x in range(C_) if nah[y, x] and kl[y, x] in 'gs']
    rs.shuffle(kandidaten)
    gesetzt = []
    for (ty, tx) in kandidaten[:len(kandidaten) // 6]:
        if any(abs(ty - y) + abs(tx - x) < 3 for (y, x) in gesetzt):
            continue
        gesetzt.append((ty, tx))
        x0, y0 = tx * T + rs.randint(2, 13), ty * T + rs.randint(2, 13)
        art = rs.rand()
        ginkgo = 50 <= tx <= 69 and 36 <= ty <= 75
        if art < 0.55:                                                # Laub: 2-4 Blaetter
            farben = [(232, 196, 64), (214, 160, 40), (244, 214, 96)] if ginkgo else \
                [(150, 104, 52), (122, 140, 60), (176, 120, 56)]
            for _ in range(rs.randint(3, 7)):
                bx, by = x0 + rs.randint(-5, 6), y0 + rs.randint(-3, 4)
                c = farben[rs.randint(len(farben))]
                a[by, bx:bx + 3] = c; a[by - 1, bx + 1] = c                      # Blatt 3 px mit Spitze
                a[by + 1, bx:bx + 2] = tuple(int(v * 0.65) for v in c)          # Schatten
        elif art < 0.75:                                              # Papierschnipsel
            a[y0:y0 + 3, x0:x0 + 4] = (232, 234, 238)
            a[y0, x0 + 3] = (200, 204, 212); a[y0 + 1, x0 + 1:x0 + 3] = (180, 186, 196)
            a[y0 + 3, x0 + 1:x0 + 4] = (120, 124, 134)
        elif art < 0.9:                                               # Dose (rot oder silber)
            c = (196, 60, 52) if rs.rand() < 0.5 else (190, 196, 206)
            a[y0:y0 + 3, x0:x0 + 4] = c
            a[y0, x0] = (240, 240, 240); a[y0:y0 + 3, x0 + 3] = tuple(int(v * 0.7) for v in c)
            a[y0 + 3, x0:x0 + 4] = (70, 72, 80)
        else:                                                         # Kippen
            for _ in range(2):
                bx, by = x0 + rs.randint(0, 4), y0 + rs.randint(0, 3)
                a[by, bx] = (236, 228, 210); a[by, bx + 1] = (210, 140, 80)


def leitstreifen(a, m):
    """Gelbe Blindenleitstreifen (Vorlage): gelbe Platten mit Noppenreihen, 1 px Fuge."""
    ys, xs = np.nonzero(m)
    a[m] = H('#e0bc48')
    noppe = m & ((np.arange(a.shape[1])[None, :] % 4) == 1) & ((np.arange(a.shape[0])[:, None] % 4) == 1)
    a[noppe] = H('#f4dc80')
    fuge = m & (((np.arange(a.shape[1])[None, :] % 16) == 0) | ((np.arange(a.shape[0])[:, None] % 16) == 0))
    a[fuge] = H('#a8862e')


def mauerfront(a, m, lvl, treppen_m):
    """Stuetzmauer wie die Vorlage: helle Betonplatten (32 px breit) mit feinen Sprenkeln, Abdeckkante oben (Licht),
    dunkle Plattenfugen, kleine Wandleuchten im Raster, Gras-/Moosbueschel am Fuss, 2 px Schatten auf dem Boden davor.
    Nicht begehbar."""
    ys, xs = np.nonzero(m)
    if not len(ys):
        return
    rs = np.random.RandomState(311)
    top = {}; bot = {}
    for x in np.unique(xs):
        col = np.nonzero(m[:, x])[0]
        top[x], bot[x] = col.min(), col.max()
    for y, x in zip(ys, xs):
        d, hoehe = y - top[x], bot[x] - top[x] + 1
        if d < 2:
            c = H('#e6e9ee')
        elif d < 4:
            c = H('#9da3ad')
        elif d >= hoehe - 2:
            c = H('#5d636e')
        else:
            c = H('#c4c8cf') if (x // 32 + (d - 4) // 22) % 2 == 0 else H('#bcc1c9')
            if x % 32 == 0 or (d - 4) % 22 == 21:
                c = H('#7e8490')
            elif x % 32 == 1:
                c = H('#d8dbe1')
            elif rs.rand() < 0.07:
                c = H('#a6abb4')
        a[y, x] = c
        lvl[y, x] = 9
    for x in np.unique(xs):                                           # Wandleuchten + Bueschel am Fuss
        if x % 64 == 40 and m[top[x] + 12, x]:
            a[top[x] + 10:top[x] + 15, x - 1:x + 2] = H('#3a3e48')
            a[top[x] + 11:top[x] + 14, x] = H('#f0e0a0')
        if rs.rand() < 0.35:
            hh = rs.randint(2, 6)
            for d in range(hh):
                if m[bot[x] - 2 - d, x]:
                    a[bot[x] - 2 - d, x] = H('#5e8a3c') if d < hh - 1 else H('#8ab45a')
    unten = m & ~np.roll(m, -1, 0)
    for d in (1, 2):
        sch = np.roll(unten, d, 0) & ~m & ~treppen_m
        dunkeln(a, sch, 0.72 + 0.1 * d)


def maschendraht(a, lvl, y, x0, x1, ausnahmen=()):
    """Gruener Maschendrahtzaun oben auf der Mauerkante (Vorlage): Handlauf, Pfosten alle 16 px, Rautengeflecht."""
    for x in range(x0, x1):
        if any(e0 <= x < e1 for (e0, e1) in ausnahmen):
            continue
        for d in range(10):
            Y = y - 10 + d
            if d == 0:
                c = H('#2e6a36')
            elif d == 1:
                c = H('#5aa05a')
            elif x % 16 in (0, 1):
                c = H('#2e6a36') if x % 16 == 0 else H('#4a8a4a')
            elif (x + d) % 4 == 0 or (x - d) % 4 == 0:
                c = H('#3e7e44')
            else:
                continue
            a[Y, x] = c
            lvl[Y, x] = 9


def zaun_senkrecht(a, lvl, x, y0, y1):
    """Seitlicher Zaun der Terrasse (gruen wie die Vorlage): Pfosten alle 16 px, zwei Laengsstaebe."""
    for y in range(y0, y1):
        a[y, x - 1] = H('#2e6a36'); a[y, x] = H('#5aa05a'); a[y, x + 1] = H('#2e6a36')
        if y % 16 in (0, 1, 2):
            a[y, x - 2:x + 3] = H('#2e6a36')
        lvl[y, x - 2:x + 3] = 9


def treppe(a, m, lvl):
    """Treppe wie die Vorlage: dunkle Stufen alle 4 px (Kante hell, Setzstufe dunkel), Handlaeufe links/rechts."""
    ys, xs = np.nonzero(m)
    for y, x in zip(ys, xs):
        d = y % 4
        a[y, x] = H('#9298a6') if d == 0 else H('#6c7282') if d < 3 else H('#4a4f5c')
    links = m & ~np.roll(m, 1, 1)
    rechts = m & ~np.roll(m, -1, 1)
    for msk, sx in ((links, 1), (rechts, -1)):
        a[msk] = H('#2a2e38')
        a[np.roll(msk, sx, 1) & m] = H('#c8ccd6')
        a[np.roll(msk, 2 * sx, 1) & m] = H('#3a3e48')
    lvl[m] = 1


def zaun(a, x, y0, y1):
    """Senkrechter Zaun (Terrassenseite): Pfosten alle 16 px, zwei Laengsstaebe, Kontur."""
    for y in range(y0, y1):
        a[y, x - 1:x + 2] = H('#5a6070')
        a[y, x] = H('#b8bec8')
        if y % 16 in (0, 1, 2):
            a[y, x - 2:x + 3] = H('#3a3e48')
            a[y, x - 1:x + 2] = H('#8a909c')


def markierungen(a, asphalt, lay):
    zebra = np.zeros_like(asphalt)
    for (x0, x1, y0, y1, art) in lay['zebra']:
        zebra[y0 * T:(y1 + 1) * T, x0 * T:(x1 + 1) * T] = True
    sperre = np.array(Image.fromarray((zebra * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(9))) > 0
    frei = asphalt & ~sperre
    frei[80 * T:86 * T, 56 * T:65 * T] = False                        # Einmuendungen frei
    frei[93 * T:100 * T, 56 * T:65 * T] = False
    k30.striche(a, frei, 36 * T, 93 * T, int(60.5 * T) - 1, GELB, senkrecht=True)
    k30.striche(a, frei, 64 * T, 120 * T, int(83 * T) - 1, GELB)
    k30.striche(a, frei, 2 * T, 120 * T, int(96.5 * T) - 1, GELB)
    for (x0, x1, y0, y1, art) in lay['zebra']:
        for y in range(y0 * T, (y1 + 1) * T):
            for x in range(x0 * T, (x1 + 1) * T):
                if not asphalt[y, x]:
                    continue
                if art == 'v' and (y % 8) < 5 and 3 <= x - x0 * T < (x1 - x0 + 1) * T - 3:
                    a[y, x] = WEISS
                if art == 'h' and (x % 8) < 5 and 3 <= y - y0 * T < (y1 - y0 + 1) * T - 3:
                    a[y, x] = WEISS


def hochbahn(img, lay, zug_sp=None):
    """Hochbahn links (Vorlage): Segmente von Karte 30, rechts mit Prellbock-Stirn am Bahnsteigende."""
    hb = lay['hochbahn']
    y0 = hb['y0'] * T
    mit, ohne = k30.brueckensegment(True), k30.brueckensegment(False)
    streifen = Image.new('RGBA', ((hb['x1'] + 1) * T, mit.height), (0, 0, 0, 0))
    x = hb['pfeiler'][0] - k30.SEG_P
    while x > 0:
        x -= k30.SEG_B
    while x * T < streifen.width:
        streifen.alpha_composite(mit if x + k30.SEG_P == hb['pfeiler'][0] else ohne, (x * T, 0)) if x >= 0 else \
            streifen.paste(mit.crop((-x * T, 0, mit.width, mit.height)), (0, 0), mit.crop((-x * T, 0, mit.width, mit.height)))
        x += k30.SEG_B
    a = np.array(streifen)
    xe = streifen.width - 1                                           # Stirn am Ende: Kontur + Prellbock
    a[:64, xe - 1:xe + 1, :3] = H('#2a2c36'); a[:64, xe - 1:xe + 1, 3] = 255
    for d in (6, 10, 14):
        for xx in range(xe - 10, xe - 1):
            a[d:d + 2, xx, :3] = H('#b03a40') if ((xx - xe) // 3) % 2 == 0 else H('#e0e0e8')
    img.alpha_composite(Image.fromarray(a), (0, y0))
    if zug_sp is not None:
        zx0, zx1 = hb['zug']
        img.alpha_composite(zug_sp, (zx0 * T, y0 + 31 - zug_sp.height))
    return img


def _raute(m, r, wachsen):
    """r-mal mit dem 4er-Kreuz erweitern bzw. schrumpfen = Rauten-Strukturelement (L1-Radius r) -> 45-Grad-Kanten."""
    m = m.copy()
    for _ in range(r):
        n = [np.roll(m, 1, 0), np.roll(m, -1, 0), np.roll(m, 1, 1), np.roll(m, -1, 1)]
        m = (m | n[0] | n[1] | n[2] | n[3]) if wachsen else (m & n[0] & n[1] & n[2] & n[3])
    return m


def raute_schliessen(m, r):
    return _raute(_raute(m, r, True), r, False)


def raute_oeffnen(m, r):
    return _raute(_raute(m, r, False), r, True)


def weg_rund(kl, lay):
    """Erdweg-Pixelmaske mit 45-Grad-Kanten (Regel 6b): Kachelmaske der Wege weichzeichnen und bei 0.5 schneiden ->
    die Kachelstufen werden zu 45-Grad-Schraegen. Platz-, Treppen- und Mauerkacheln zaehlen beim Weichzeichnen mit
    (kein Rasenspalt am Anschluss), werden danach aber ausgespart."""
    rows, cols = kl.shape
    anschluss = gross(np.isin(kl, ['g', 'T', 'W', 'p', 'd', 's', 'h', 'f']))
    basis = ((gross(kl == 'w') | gross(np.isin(kl, ['g', 'T', 'W', 'p', 'd']))) * 255).astype(np.uint8)
    m = raute_oeffnen(raute_schliessen(basis > 0, 6), 6)            # Kachelecken -> exakte 45-Grad-Schraegen (6 px)
    wk = kl == 'w'                                                    # nur auf Wegkacheln und ihren direkten Nachbarn
    nah = wk | np.roll(wk, 1, 0) | np.roll(wk, -1, 0) | np.roll(wk, 1, 1) | np.roll(wk, -1, 1)
    m &= gross(nah)
    park = np.zeros_like(m); park[:26 * T] = True
    m = (m & park & ~anschluss) | (gross(kl == 'w') & ~park)
    # Regel 2: direkt ober- und unterhalb einer Treppe ist der Weg genau so breit wie die Treppe (eine Kachelreihe)
    for (ty, tx) in zip(*np.nonzero(kl == 'T')):
        for dy in (-1, 1):
            yy = ty + dy
            if 0 <= yy < rows and kl[yy, tx] == 'w':
                xs = np.nonzero(kl[ty] == 'T')[0]
                x0 = xs[xs <= tx]; x1 = xs[xs >= tx]
                x0 = x0[-1] if len(x0) else tx
                while x0 - 1 >= 0 and kl[ty, x0 - 1] == 'T':
                    x0 -= 1
                x1 = tx
                while x1 + 1 < cols and kl[ty, x1 + 1] == 'T':
                    x1 += 1
                for py in range(yy * T, (yy + 1) * T):              # zur Treppe hin schraeg zulaufend (45 Grad)
                    e = (yy * T + T - 1 - py) if dy == -1 else (py - yy * T)
                    l_, r_ = x0 * T - e, (x1 + 1) * T + e
                    m[py, max(0, l_ - 3 * T):max(0, l_)] = False
                    m[py, r_:r_ + 3 * T] = False
                    m[py, x0 * T:(x1 + 1) * T] = True
    m &= ~anschluss
    return m


def bauen(frame=None, speichern=True):
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cols, rows = lay['groesse']
    Wp, Hp = cols * T, rows * T
    kl = np.array([list(r) for r in lay['klassen']])
    hk = np.array([[int(c) for c in r] for r in lay['hoehe']])
    a = k18.textur('g', cols, rows)
    for art, tex in (('s', 's'), ('n', 'n'), ('h', 'n'), ('f', 'n'), ('d', 'd')):
        m = gross(kl == art)
        a[m] = k18.textur(tex, cols, rows)[m]
    m = gross(kl == 'e'); a[m] = erde(cols, rows, (0.93, 0.9, 0.86))[m]
    weg_px = weg_rund(kl, lay)                                             # Parkwege mit runden Kanten (Regel 6)
    w_kach = gross(kl == 'w')
    a[w_kach & ~weg_px] = k18.textur('n', cols, rows)[w_kach & ~weg_px]
    a[weg_px] = erde(cols, rows, (1.0, 0.95, 0.88))[weg_px]
    pm = gross(kl == 'p'); a[pm] = k30.sandstein(cols, rows)[pm]
    lvl = np.kron(hk, np.ones((T, T), int)).astype(np.uint8)
    asphalt = gross(kl == 's')
    k18.bordsteine(a, asphalt, ~asphalt)
    markierungen(a, asphalt, lay)
    rasen_px = (gross(np.isin(kl, ['n', 'f'])) | w_kach) & ~weg_px
    k18.rasen_kanten(a, rasen_px | weg_px)                            # Steinkante nur zu Gehweg/Platz, nicht zum Erdweg
    a[weg_px] = erde(cols, rows, (1.0, 0.95, 0.88))[weg_px]
    for art in ('e', 'd'):                                            # Erd-/Sandflaechen: feine dunkle Kante zum Rest
        m = gross(kl == art)
        dunkeln(a, kontur(m) & ~gross(np.isin(kl, ['w', 'e', 'd'])), 0.85)
    rand_w = kontur(weg_px) & ~gross(np.isin(kl, ['g', 'T', 'W', 'p', 'd']))   # Erdweg: weiche Kante zum Rasen
    dunkeln(a, rand_w, 0.8)
    dunkeln(a, kontur(weg_px & ~rand_w) & ~gross(np.isin(kl, ['g', 'T', 'W', 'p', 'd'])), 0.92)
    k18.mittelstreifen(a, gross(kl == 'h'), k18.textur('n', cols, rows)) if False else None
    hecke(a, gross(kl == 'h'))
    leitstreifen(a, gross(kl == 'y'))
    mauerfront(a, gross(kl == 'W'), lvl, gross(kl == 'T'))
    treppe(a, gross(kl == 'T'), lvl)
    tx0, ty0, tx1, ty1 = lay['terrasse']                              # Terrassenseite: schmale Kontur + gruener Zaun
    a[ty0 * T:(ty1 + 1) * T, tx0 * T:tx0 * T + 2] = H('#4a5040')
    zaun_senkrecht(a, lvl, tx0 * T + 4, (ty0 + 2) * T, (ty1 + 1) * T)
    my0 = lay['mauer'][0]                                             # Maschendraht oben auf den Mauern (Treppen frei)
    maschendraht(a, lvl, my0 * T, 0, 120 * T, [(x0 * T, (x1 + 1) * T) for (x0, x1) in lay['mauer_treppen']])
    fy0 = lay['terrasse_front'][0]
    tt0, tt1 = lay['terrasse_treppe']
    maschendraht(a, lvl, fy0 * T, (tx0 + 1) * T, 120 * T, [(tt0 * T, (tt1 + 1) * T)])
    f_ = gross(kl == 'f'); lvl[f_] = 9
    lvl[gross(kl == 'h')] = 9
    if speichern and frame is None:
        np.save(os.path.join(KARTE, 'pixelhoehe.npy'), lvl)
        np.save(os.path.join(KARTE, 'wasser.npy'), np.packbits(np.zeros((Hp, Wp), bool)))
        np.save(os.path.join(KARTE, 'wand.npy'), np.packbits(lvl == 9))
    img = Image.fromarray(a).convert('RGBA')
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain_basis.png'))
    zug = None
    objs = []
    pf = os.path.join(OBJ, 'platzierung.json')
    if os.path.exists(pf):
        objs = sorted((o for o in json.load(open(pf)) if os.path.exists(os.path.join(OBJ, o['datei']))),
                      key=lambda o: o.get('sortier', o['y'] + o['fuss']))
        cache = {o['datei']: Image.open(os.path.join(OBJ, o['datei'])).convert('RGBA') for o in objs}
        f_ = frame if frame is not None else 0
        boden = lvl != 9
        k4.objekte_zeichnen(img, [o for o in objs if not o.get('hochbahn') and not o.get('vor_hochbahn')], cache,
                            boden, f_, ebenen=lvl)
        img = img.copy()
        k4.animieren(img, [o for o in objs if not o.get('hochbahn')], cache, f_, ruhig=frame is None)
        k6.animieren_k6(img, [o for o in objs if not o.get('hochbahn')], cache, f_)
        zuege = [o for o in objs if o.get('hochbahn')]
        if zuege:
            zug = cache[zuege[0]['datei']]
    img = hochbahn(img.convert('RGBA'), lay, zug)
    if objs:
        for o in objs:
            if o.get('vor_hochbahn'):
                img.alpha_composite(cache[o['datei']], (o['x'], o['y']))
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain.png'))
    print('Karte 31 %dx%d gebaut' % (cols, rows))
    return img


if __name__ == '__main__':
    bauen()
