"""Karte 30 - Odaiba (A02): Bucht-Stadtteil am Tag. Gelaende, Hochbahn, Objekte, Animation (4 Bilder).

  python3 tools/karte30_layout.py && python3 tools/karte30_bauen.py
  python3 tools/karte30_objekte.py && python3 tools/karte30_bauen.py

Kacheln und Strassenbau wie Karte 18 (Asphalt, Gehwegplatten, Bordsteine, Zebrastreifen, Hochbahn), aber am Tag:
Meer in den Farben von Karte 01 (Strand mit Schaumkante), Platz vor dem Fernsehgebaeude in Sandstein, Strand mit
Holzpromenade, steinerner Pier mit Kaimauer, Bruecke oben rechts ueber das Wasser, Wasserbecken links.
"""
import json, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageFilter
import karte04_bauen as k4
import karte08_bauen as k8
import karte18_bauen as k18
import karte06_bauen as k6

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte30')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte30')
T = 16
N_FRAMES = 4
BILDDAUER = 250
k4.N_FRAMES = N_FRAMES
k18.N_FRAMES = N_FRAMES
H = k4.H
gross, kontur, dunkeln, mischen = k18.gross, k18.kontur, k18.dunkeln, k18.mischen
GELB = np.array(H('#d8b048'), np.uint8)
WEISS = np.array(H('#e4e8ee'), np.uint8)


def sandstein(cols, rows):
    """Platz in Sandstein wie die Vorlage: Ziegelkacheln von Karte 18 (Terrasse) warm eingefaerbt."""
    t = k18.textur('t', cols, rows).astype(np.float32)
    l = t.mean(2, keepdims=True)
    return np.clip(l * np.array([1.02, 0.93, 0.78]) * 0.98, 0, 255).astype(np.uint8)


def striche(a, frei, x0, x1, y, farbe, s=12, l=10, senkrecht=False):
    for v in range(x0, x1):
        if (v - x0) % (s + l) < s:
            for d in (0, 1):
                Y, X = (v, y + d) if senkrecht else (y + d, v)
                if frei[Y, X]:
                    a[Y, X] = farbe


def markierungen(a, asphalt, lay):
    zebra = np.zeros_like(asphalt)
    for (x0, x1, y0, y1, art) in lay['zebra']:
        zebra[y0 * T:(y1 + 1) * T, x0 * T:(x1 + 1) * T] = True
    sperre = np.array(Image.fromarray((zebra * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(9))) > 0
    frei = asphalt & ~sperre
    for xs in ((59, 62), (95, 98)):                                   # Kreuzungen frei
        frei[50 * T:55 * T, xs[0] * T - 6:(xs[1] + 1) * T + 6] = False
        frei[75 * T:79 * T, xs[0] * T - 6:(xs[1] + 1) * T + 6] = False
    frei[50 * T:55 * T, 112 * T - 6:116 * T + 6] = False
    striche(a, frei, 0, 126 * T, int(52.5 * T) - 1, GELB)            # Hauptstrasse: gelbe Mittellinie gestrichelt
    striche(a, frei, 23 * T, 126 * T, int(77 * T) - 1, GELB)         # Uferstrasse
    for xc in (61, 97):                                                # Querstrassen
        striche(a, frei, 55 * T, 75 * T, xc * T - 1, GELB, senkrecht=True)
    striche(a, frei, 0, 50 * T, 114 * T - 1, GELB, senkrecht=True)   # Brueckenstrasse
    for (x0, x1, y0, y1, art) in lay['zebra']:
        for y in range(y0 * T, (y1 + 1) * T):
            for x in range(x0 * T, (x1 + 1) * T):
                if not asphalt[y, x]:
                    continue
                if art == 'v' and (y % 8) < 5 and 3 <= x - x0 * T < (x1 - x0 + 1) * T - 3:
                    a[y, x] = WEISS
                if art == 'h' and (x % 8) < 5 and 3 <= y - y0 * T < (y1 - y0 + 1) * T - 3:
                    a[y, x] = WEISS


def becken(a, m, frame, lvl):
    """Wasserbecken: Steinrand (3 px, oben hell), Wasser Karte-01-Tuerkis mit Innenschatten oben links,
    Lichtstriche wandern (4 Bilder)."""
    f = frame or 0
    rand = kontur(m); rand2 = kontur(m & ~rand); rand3 = kontur(m & ~rand & ~rand2)
    innen = m & ~rand & ~rand2 & ~rand3
    a[innen] = H('#3aa0c0')
    sch = innen & (np.roll(rand3, 1, 0) | np.roll(rand3, 2, 0) | np.roll(rand3, 3, 0) | np.roll(rand3, 1, 1) | np.roll(rand3, 2, 1))
    a[sch] = H('#2a7c9e')
    ys, xs = np.nonzero(innen)
    hell = innen & (((np.arange(a.shape[1])[None, :] + np.arange(a.shape[0])[:, None] * 5 + f * 4) % 37) < 3) & \
        ((np.arange(a.shape[0])[:, None] % 6) == 0)
    a[hell & ~sch] = H('#9ee0f0')
    a[rand | rand2 | rand3] = H('#b4b8c4')
    a[rand & ~np.roll(m, -1, 0)] = H('#7a7e8c')
    a[rand & ~np.roll(m, 1, 0)] = H('#d4d8e0')
    a[rand3] = H('#8a8e9a')
    lvl[m] = 9


def bruecke(a, lay, wasser_m, lvl, frame):
    """Bruecke ueber das Wasser: Gehwege mit Gelaender aussen (Handlauf hell, Pfosten alle 16 px), dunkle Kante,
    Schatten auf dem Wasser rechts daneben."""
    x0, y0, x1, y1 = lay['bruecke']
    X0, X1, Y1 = x0 * T, (x1 + 1) * T, (y1 + 1) * T
    for links in (True, False):                                       # Gelaender: Bruestung 5 px, Pfosten alle 16 px
        X = X0 if links else X1 - 5
        a[:Y1, X:X + 5] = H('#c4c8d2')
        a[:Y1, X + (0 if links else 4)] = H('#eef0f4')
        a[:Y1, X + (4 if links else 0)] = H('#6a6e7c')
        for Y in range(0, Y1, 16):
            a[Y + 5:Y + 11, X + 1:X + 4] = H('#8a8e9c')
            a[Y + 5, X + 1:X + 4] = H('#eef0f4')
            a[Y + 10, X + 1:X + 4] = H('#4a4e5a')
    a[:Y1, X0 - 1] = H('#2e3444'); a[:Y1, X1] = H('#2e3444')
    for d in range(1, 7):                                              # Schatten aufs Wasser (rechts)
        m = np.zeros_like(wasser_m); m[:Y1, X1 + d] = True
        dunkeln(a, m & wasser_m, 0.7 + d * 0.03)
    lvl[:Y1, X0:X0 + 5] = 9; lvl[:Y1, X1 - 5:X1] = 9


def hochbahn(img, lay, zug_sp=None):
    """Hochbahn wie Karte 18 (Oberseite 2 Kacheln mit Fuehrungsschiene, Front 2 Kacheln), aber durchgehend von Rand
    zu Rand (kein Prellbock, kein Nebel); der Zug steht auf der Fahrbahn."""
    hb = lay['hochbahn']
    a = np.array(img)
    X0, X1, y0 = hb['x0'] * T, (hb['x1'] + 1) * T, hb['y0'] * T
    xs = np.arange(X0, X1)
    for d in range(32):
        if d < 2:
            c = np.tile(H('#aeb2c0'), (len(xs), 1))
        elif d < 4:
            c = np.tile(H('#6a6e7c'), (len(xs), 1))
        elif 13 <= d <= 18:
            c = np.tile(H('#8a8e9a') if d in (13, 18) else H('#c0c4ce'), (len(xs), 1))
        elif d == 30:
            c = np.tile(H('#9a9eac'), (len(xs), 1))
        else:
            c = np.where(((xs // 32) % 2)[:, None] == 1, H('#7c808e'), H('#787c8a'))
        a[y0 + d, X0:X1, :3] = c[:, :3]
        a[y0 + d, X0:X1, 3] = 255
    for d in range(32):
        c = H('#9a9eaa') if d < 3 else H('#82869a') if d < 26 else H('#5a5e6e')
        row = np.tile(c, (len(xs), 1))
        if d >= 3:
            row[((xs - X0) % 256) < 2] = H('#4e5262')
        if d == 3:
            row[:] = H('#4e5262')
        if 10 <= d <= 12:
            row[:] = H('#6e7284')
        a[y0 + 32 + d, X0:X1, :3] = row[:, :3]
        a[y0 + 32 + d, X0:X1, 3] = 255
    a[y0 + 63, X0:X1, :3] = H('#2a2c36')[:3]
    img = Image.fromarray(a)
    if zug_sp is not None:
        zx0, zx1 = hb['zug']
        x_ = zx0 * T + (-(-zug_sp.width // T) * T - zug_sp.width) // 2
        img.alpha_composite(zug_sp, (x_, y0 + 31 - zug_sp.height))
    return img


def schatten_hochbahn(a, lay, boden):
    hb = lay['hochbahn']
    y0 = (hb['y1'] + 1) * T
    for i, y in enumerate(range(y0, y0 + 26)):
        m = np.zeros(boden.shape, bool)
        m[y, (hb['x0'] + 2) * T:(hb['x1'] + 1) * T] = True
        dunkeln(a, m & boden, 0.72 if i < 20 else 0.72 + (i - 19) * 0.04)


def meer(a, kl, wasser, frame, lay):
    import wasser_details as wd
    alt = (wd.N_FRAMES, wd.FLACH, wd.SCHAUM_D, wd.STUFE1, wd.STUFE2)
    wd.N_FRAMES = N_FRAMES
    wd.FLACH, wd.SCHAUM_D, wd.STUFE1, wd.STUFE2 = 22, (18, 22), 56, 110
    meiden = gross(np.isin(kl, ['v', 'b']))
    bx0, by0, bx1, by1 = lay['bruecke']
    meiden[:(by1 + 1) * T, (bx0 - 3) * T:(bx1 + 4) * T] = True
    for tp in lay['teleporter']:
        meiden[(tp['y'] - 3) * T:(tp['y'] + tp['h'] + 3) * T, (tp['x'] - 3) * T:(tp['x'] + tp['b'] + 3) * T] = True
    meiden = np.array(Image.fromarray((meiden * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(9))) > 0
    wd.FELSEN_PROTOKOLL.clear()
    see = wasser.copy()
    see[:(by1 + 1) * T, bx0 * T:(bx1 + 1) * T] = True                # das Meer laeuft unter der Bruecke durch
    vorher = a.copy()
    img = wd.meer_terrassen(Image.fromarray(a), see, frame, meiden, maske=see)
    wd.N_FRAMES, wd.FLACH, wd.SCHAUM_D, wd.STUFE1, wd.STUFE2 = alt
    out = np.array(img.convert('RGB'))
    deck = np.zeros_like(wasser); deck[:(by1 + 1) * T, bx0 * T:(bx1 + 1) * T] = True
    out[deck] = vorher[deck]
    return out


def bauen(frame=None, speichern=True):
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cols, rows = lay['groesse']
    Wp, Hp = cols * T, rows * T
    kl = np.array([list(r) for r in lay['klassen']])
    a = k18.textur('g', cols, rows)
    for art, tex in (('s', 's'), ('n', 'n'), ('f', 'n'), ('d', 'd'), ('b', 'b'), ('v', 'v'), ('w', 'w'), ('o', 'w')):
        m = gross(kl == art)
        a[m] = k18.textur(tex, cols, rows)[m]
    pm = gross(kl == 'p')
    a[pm] = sandstein(cols, rows)[pm]
    wasser = gross(kl == 'w')
    a = meer(a, kl, wasser, frame, lay)
    land = ~wasser
    asphalt = gross(kl == 's')
    lvl = np.zeros((Hp, Wp), np.uint8)
    lvl[land] = 1
    k18.bordsteine(a, asphalt, land)
    markierungen(a, asphalt, lay)
    rasen = gross(np.isin(kl, ['n', 'f']))
    k18.rasen_kanten(a, rasen)
    sand = gross(kl == 'd')                                           # Sand: Steinkante nur zur Promenade hin
    nahw = np.array(Image.fromarray((wasser * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(5))) > 0
    rand_s = kontur(sand) & ~nahw & ~gross(kl == 'b')
    rand_s &= ~(np.roll(gross(kl == 'b'), 1, 0) | np.roll(gross(kl == 'b'), -1, 0))
    a[rand_s] = H('#8a8e98')
    pr = kontur(pm)                                                   # Sandstein-Rahmen: feine Fugenkante
    a[pr] = H('#8c7c62')
    holz = gross(kl == 'b')                                           # Holzpromenade: dunkle Kante ringsum
    a[kontur(holz)] = H('#5a4228')
    becken(a, gross(kl == 'o'), frame, lvl)
    pier = gross(kl == 'v')
    k18.kaimauer(a, wasser, pier, lvl)
    rand_p = kontur(pier) & (np.roll(wasser, 1, 1) | np.roll(wasser, -1, 1) | np.roll(wasser, -1, 0))
    a[rand_p] = H('#d0d4dc')
    bruecke(a, lay, wasser, lvl, frame)
    schatten_hochbahn(a, lay, land & ~wasser)
    lvl[gross(kl == 'f')] = 9                                         # Waldrand: nicht begehbar
    if speichern and frame is None:
        np.save(os.path.join(KARTE, 'pixelhoehe.npy'), lvl)
        np.save(os.path.join(KARTE, 'wasser.npy'), np.packbits(wasser))
        np.save(os.path.join(KARTE, 'wand.npy'), np.packbits(lvl == 9))
    img = Image.fromarray(a).convert('RGBA')
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain_basis.png'))
    zug = None
    pf = os.path.join(OBJ, 'platzierung.json')
    if os.path.exists(pf):
        objs = sorted((o for o in json.load(open(pf)) if os.path.exists(os.path.join(OBJ, o['datei']))),
                      key=lambda o: o.get('sortier', o['y'] + o['fuss']))
        cache = {o['datei']: Image.open(os.path.join(OBJ, o['datei'])).convert('RGBA') for o in objs}
        f_ = frame if frame is not None else 0
        for o in objs:                                                # Riesenrad: Ring und Gondeln drehen sich
            if o.get('anim') == 'riesenrad':
                d_ = 'gebaeude/riesenrad_%d.png' % (f_ % 4)
                cache[o['datei']] = Image.open(os.path.join(OBJ, d_)).convert('RGBA')
        boden = land & (lvl != 9)
        boden_sch = boden.copy()
        for o in objs:                                                # kein Schatten der Baeume im Waldrand
            pass
        k4.objekte_zeichnen(img, [o for o in objs if not o.get('hochbahn') and o.get('anim') != 'riesenrad'] , cache,
                            boden_sch, f_, ebenen=lvl)
        rr = [o for o in objs if o.get('anim') == 'riesenrad']
        for o in rr:                                                  # Riesenrad nach Fusshoehe einsortiert ueber allem
            img.alpha_composite(cache[o['datei']], (o['x'], o['y']))
        nach = [o for o in objs if not o.get('hochbahn') and o.get('anim') != 'riesenrad' and rr and
                o['y'] + o['fuss'] > rr[0]['y'] + rr[0]['fuss']]
        for o in nach:
            img.alpha_composite(cache[o['datei']], (o['x'], o['y']))
        img = img.copy()
        k4.animieren(img, [o for o in objs if not o.get('hochbahn')], cache, f_, ruhig=frame is None)
        k6.animieren_k6(img, [o for o in objs if not o.get('hochbahn')], cache, f_)
        zuege = [o for o in objs if o.get('hochbahn')]
        if zuege:
            zug = cache[zuege[0]['datei']]
    img = hochbahn(img, lay, zug)
    if os.path.exists(pf):                                            # Bahnhof steht VOR der Strecke (Nutzer)
        for o in objs:
            if o.get('vor_hochbahn'):
                img.alpha_composite(cache[o['datei']], (o['x'], o['y']))
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain.png'))
    print('Karte 30 %dx%d gebaut' % (cols, rows))
    return img


if __name__ == '__main__':
    bauen()
