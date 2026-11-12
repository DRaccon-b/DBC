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


def leitstreifen(a, m):
    """Gelbe Blindenleitstreifen (Vorlage): gelbe Platten mit Noppenreihen, 1 px Fuge."""
    ys, xs = np.nonzero(m)
    a[m] = H('#e0bc48')
    noppe = m & ((np.arange(a.shape[1])[None, :] % 4) == 1) & ((np.arange(a.shape[0])[:, None] % 4) == 1)
    a[noppe] = H('#f4dc80')
    fuge = m & (((np.arange(a.shape[1])[None, :] % 16) == 0) | ((np.arange(a.shape[0])[:, None] % 16) == 0))
    a[fuge] = H('#a8862e')


def mauerfront(a, m, lvl, treppen_m):
    """Stuetzmauer (Vorlage): oben 3 px Heckenkrone, 3 px Abdeckstein (Licht), darunter Steinbloecke 16x8 im Verband
    mit Fugen und kleinen Entwaesserungsloechern, unten 2 px dunkler Fuss. Nicht begehbar."""
    ys, xs = np.nonzero(m)
    if not len(ys):
        return
    for y, x in zip(ys, xs):
        d = y - (y // T) * 0                                          # Abstand zur Oberkante der Mauer (spaltenweise)
    oben = m & ~np.roll(m, 1, 0)
    top = np.full(a.shape[1], -1)
    for x in np.unique(xs):
        col = np.nonzero(m[:, x])[0]
        top[x] = col.min()
    for y, x in zip(ys, xs):
        d = y - top[x]
        hoehe = (np.nonzero(m[:, x])[0].max() - top[x]) + 1
        if d < 3:
            c = H('#3e6a32') if (x + d) % 3 else H('#58884a')         # Heckenkrone
        elif d < 6:
            c = H('#d2d6de') if d == 3 else H('#b4b9c4')            # Abdeckstein
        elif d >= hoehe - 2:
            c = H('#4a4f5c')                                          # Fuss
        else:
            dd = d - 6
            reihe = dd // 8
            versatz = 8 if reihe % 2 else 0
            if dd % 8 == 7 or (x + versatz) % 16 == 0:
                c = H('#6a7080')                                      # Fuge
            else:
                c = H('#9aa1b0') if dd % 8 < 2 else H('#8a91a1')
            if (x + versatz) % 32 == 16 and dd % 8 == 4 and reihe == 1:
                c = H('#3a3e48')                                      # Entwaesserungsloch
        a[y, x] = c
        lvl[y, x] = 9


def treppe(a, m, lvl):
    """Treppe in der Mauer: Stufen alle 4 px (Kante hell, Setzstufe dunkler), Wangen links/rechts mit Kontur."""
    ys, xs = np.nonzero(m)
    for y, x in zip(ys, xs):
        d = y % 4
        c = H('#d4d8e0') if d == 0 else H('#b8bdc8') if d < 3 else H('#8e94a2')
        a[y, x] = c
    links = m & ~np.roll(m, 1, 1)
    rechts = m & ~np.roll(m, -1, 1)
    for msk, c1, c2 in ((links, '#6a7080', '#c4c9d4'), (rechts, '#4a4f5c', '#7a8090')):
        a[msk] = H(c1)
        a[np.roll(msk, 1 if msk is links else -1, 1) & m] = H(c2)
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


def bauen(frame=None, speichern=True):
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cols, rows = lay['groesse']
    Wp, Hp = cols * T, rows * T
    kl = np.array([list(r) for r in lay['klassen']])
    hk = np.array([[int(c) for c in r] for r in lay['hoehe']])
    a = k18.textur('g', cols, rows)
    for art, tex in (('s', 's'), ('n', 'n'), ('h', 'n'), ('d', 'd')):
        m = gross(kl == art)
        a[m] = k18.textur(tex, cols, rows)[m]
    m = gross(kl == 'e'); a[m] = erde(cols, rows, (0.93, 0.9, 0.86))[m]
    m = gross(kl == 'w'); a[m] = erde(cols, rows, (1.0, 0.95, 0.88))[m]
    pm = gross(kl == 'p'); a[pm] = k30.sandstein(cols, rows)[pm]
    lvl = np.kron(hk, np.ones((T, T), int)).astype(np.uint8)
    asphalt = gross(kl == 's')
    k18.bordsteine(a, asphalt, ~asphalt)
    markierungen(a, asphalt, lay)
    k18.rasen_kanten(a, gross(np.isin(kl, ['n'])))
    for art in ('w', 'e', 'd'):                                       # Erd-/Sandflaechen: feine dunkle Kante zum Rest
        m = gross(kl == art)
        dunkeln(a, kontur(m) & ~gross(np.isin(kl, ['w', 'e', 'd'])), 0.85)
    k18.mittelstreifen(a, gross(kl == 'h'), k18.textur('n', cols, rows)) if False else None
    hecke(a, gross(kl == 'h'))
    leitstreifen(a, gross(kl == 'y'))
    mauerfront(a, gross(kl == 'W'), lvl, gross(kl == 'T'))
    treppe(a, gross(kl == 'T'), lvl)
    tx0, ty0, tx1, ty1 = lay['terrasse']                              # Terrassenseite: schmale Kontur + Zaun
    a[ty0 * T:(ty1 + 1) * T, tx0 * T:tx0 * T + 2] = H('#4a5040')
    zaun(a, tx0 * T + 3, ty0 * T, (ty1 + 1) * T)
    lvl[ty0 * T:(ty1 + 1) * T, tx0 * T:tx0 * T + 5] = 9
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
