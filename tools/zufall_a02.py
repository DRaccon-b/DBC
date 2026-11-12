"""Bau eines Zufallskarten-Gelaendes nach dem aktuellen Kachel-Standard (A02, Stil Karte 20 Startdorf).

Ersetzt fuer die Zufallskarten (tools/zufall_karte.py, tools/zufall_export.py) den alten Karte-01-Weg
(Wang-Uebergaenge, runde Kanten). Bausteine wie Karte 20:
  Boden    Gras/Sand-Grundkacheln von Karte 01 (assets/basis), Waldboden = abgedunkeltes Gras,
           Sandwege ueber die Kachelmaske mit 45-Grad-Kanten (Regel 6b: k4.RASTER45, Gauss 5 px, 50 %) und
           dunklerem Saum, Teiche vertieft wie der Fluss von Karte 20.
  Objekte  kleinster Kachelblock, Fuss buendig, waagerecht zentriert (Regel 1/1b), Bodenfuss nach Untergrund;
           Wald auf jeder zweiten Waldkachel (wie Karte 06/20), Begleiter der Wiesenbaeume nach Regel 5d (wie Karte 23),
           Streudeko ohne Wiederholung, nie auf Wegen, nie am Wasser, Spawnfeld (Portal) frei.
  Zeichnen karte04_bauen.objekte_zeichnen (Kontakt- und Schlagschatten nur auf dem Boden), k4.animieren.

  bauen(raster, fest, symmetrie, obj_dir, seed) -> dict(bild, boden, objekte, cache, wasser)
  raster: Zeichenketten aus F (Wald) G (Wiese) P (Sandweg) W (Teich); fest: [(sprite, kachel_x, kachel_y)]
  (Fussmitte), symmetrie: [(achse, a, b)] als Eintraege aus fest.
"""
import math, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
OBJ01 = os.path.join(ROOT, 'assets', 'objekte', 'karte01')
T = 16

WALD = ['k01/baum%02d' % i for i in (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 12, 13, 14)]       # wie Karte 20/23
DEKO = ['k01/deko%02d' % i for i in (0, 1, 3, 5, 6, 8, 10, 14, 26, 27, 31, 33, 38, 61)]
DEKO_PFLANZE = {'k01/deko05', 'k01/deko06', 'k01/deko26', 'k01/deko27', 'k01/deko61', 'k01/deko00', 'k01/deko01',
                'k01/deko03', 'k01/deko38'}
FELS_GROSS = ['k01/deko09', 'k01/deko11']                 # bemooste Felsen (hinter den Blaettern)
HOCH_FELS = ['k01/deko09', 'k01/deko11']                  # Regel 5d: vor dem Stumpf nur 2 Kacheln hohe Objekte
HOCH_BLUME = ['k01/deko04', 'k01/deko27', 'k01/deko30']
BEGLEITET = ('gross/00', 'gross/01', 'gross/02')          # einzelne Baeume in der Karte (nicht Waldrand, nicht Arena)
FLACH = ('k01/deko',)                                     # flache Streudeko -> Ebene 0
FUSS_ART = {'zufall_portal/01': 'stein', 'zufall_brunnen/00': 'stein', 'gross/09': 'stein', 'gross/14': 'holz',
            'gross/13': 'holz', 'gross/00': 'baum', 'gross/01': 'baum', 'gross/02': 'baum', 'dschungel/00': None}


def quelle(name):
    if name.startswith('k01/baum'):
        return os.path.join(OBJ01, 'baeume', name[-2:] + '.png')
    if name.startswith('k01/deko'):
        return os.path.join(OBJ01, 'deko', name[-2:] + '.png')
    return os.path.join(OBJ01, name + '.png')


def flaeche(ks, cols, rows):
    import karte_bauen as kb
    t = np.zeros((rows * T, cols * T, 3), np.uint8)
    for y in range(rows):
        for x in range(cols):
            t[y * T:(y + 1) * T, x * T:(x + 1) * T] = ks[kb.variante(x, y) % len(ks)]
    return t


def boden_bauen(raster, frame=None, **_):
    """Boden nach Karte 20: Gras, Waldboden, Sandwege (45 Grad + Saum), vertiefte Teiche. -> (RGB-Array, Wassermaske)"""
    import karte04_bauen as k4
    import karte06_bauen as k6
    import wasser_vertieft
    k4.RASTER45 = True
    rows, cols = len(raster), len(raster[0])
    basis = os.path.join(ROOT, 'assets', 'basis')
    gras = flaeche(k6.kacheln(os.path.join(basis, 'gras_%d.png'), 5), cols, rows)
    sand = flaeche(k6.kacheln(os.path.join(basis, 'sand_%d.png'), 5), cols, rows)
    a = gras.copy()
    wm = k4.weich(k4.zell_maske(raster, 'F', cols, rows), 5, 0.4, 3)
    a[wm] = (gras[wm] * np.array([0.62, 0.7, 0.66])).astype(np.uint8)
    roh = k4.zell_maske(raster, 'P', cols, rows)
    m = k4.weich(roh, 5.0, 0, 4)
    a[m] = sand[m]
    saum = k4.weich(roh, 5.0, 0, 4, 0.28) & ~m
    a[saum] = (a[saum] * 0.9).astype(np.uint8)
    xm = k4.weich(k4.zell_maske(raster, 'W', cols, rows), 4, 0.15, 8, 0.45)
    if xm.any():
        a = np.array(wasser_vertieft.vertiefen(Image.fromarray(a), np.ones_like(xm), frame, maske=xm).convert('RGB'))
    return a, xm


def objekte_setzen(raster, fest, symmetrie, obj_dir, seed=1, innen=None):
    """Objekte am Raster im A02-Stil. Varianten mit Bodenfuss landen in obj_dir/varianten/. -> Liste wie platzierung.json"""
    import bauwerke
    rows, cols = len(raster), len(raster[0])
    rnd = random.Random(seed)
    objekte, belegt, gesperrt, cache = [], set(), set(), {}

    def k(tx, ty):
        return raster[min(rows - 1, max(0, ty))][min(cols - 1, max(0, tx))]

    def setze(name, fx, fy, opt=None, frei=False, wald=False):
        opt = dict(opt or {})
        spiegeln = opt.pop('spiegeln', False)
        flach = name.startswith(FLACH) and name not in HOCH_FELS + HOCH_BLUME
        tx, ty = int(math.floor(fx)), int(fy)
        if frei:
            if (tx, ty) in gesperrt or (tx, ty, flach) in belegt:
                return None
            if not flach and not wald and any((tx + dx, ty + dy, False) in belegt for dx in (-1, 0, 1) for dy in (-1, 0, 1)):
                return None
        b = 'sand' if k(tx, ty) == 'P' else 'gras'
        key = (name, b, spiegeln)
        if key not in cache:
            sp = Image.open(quelle(name)).convert('RGBA')
            if spiegeln:
                sp = sp.transpose(Image.FLIP_LEFT_RIGHT)
            aa = np.array(sp.getchannel('A')) > 0
            ys, xs = np.nonzero(aa)
            ux0, uy0, ux1, uy1 = int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())
            art = FUSS_ART.get(name, 'baum' if 'baum' in name else 'klein' if flach else 'stein')
            v = sp if art is None else bauwerke.bodenfuss(sp, b, art)
            off = 0 if art is None else 2
            datei = 'varianten/%s_%s%s.png' % (name.replace('/', '-'), b, '_m' if spiegeln else '')
            os.makedirs(os.path.join(obj_dir, 'varianten'), exist_ok=True)
            v.save(os.path.join(obj_dir, datei))
            cache[key] = (datei, v.height, ux0 + off, uy0, ux1 + off, uy1)
        datei, h, ux0, uy0, ux1, uy1 = cache[key]
        bw, bh = ux1 - ux0 + 1, uy1 - uy0 + 1
        wt, ht = math.ceil(bw / T), math.ceil(bh / T)
        bx = int(round(fx + 0.5 - wt / 2.0))
        o = {'datei': datei, 'basis': name, 'x': bx * T + (wt * T - bw) // 2 - ux0, 'y': (ty + 1) * T - 1 - uy1,
             'fuss': h, 'kachel': [tx, ty], 'block': [bx, ty - ht + 1, wt, ht], 'ebene': 0 if flach else 1}
        px_, py_ = opt.pop('px', None), opt.pop('py', None)
        if px_ is not None:                                      # pixelgenaue Lage (Begleiter nach Regel 5d)
            o['x'] = px_ - (ux0 + bw // 2)
            o['y'] = py_ - uy1
        o.update(opt)
        objekte.append(o)
        belegt.add((tx, ty, flach))
        for x in range(bx, bx + wt):
            for y in range(ty - ht + 1, ty + 1):
                gesperrt.add((x, y))
        return o

    # 1. feste Objekte der Stuecke (grosse Objekte zuerst)
    fest_objs = {}
    for (name, cx, cy) in fest:
        fest_objs[(name, cx, cy)] = setze(name, cx, cy, {'fest': True})
    # Symmetrische Paare exakt gespiegelt zur Achse (geht vor Regel 1b)
    for achse, a_, b_ in symmetrie:
        oa, o1, o2 = fest_objs.get(achse), fest_objs.get(a_), fest_objs.get(b_)
        if not (oa and o1 and o2):
            continue
        mitte = lambda o: (o['block'][0] + o['block'][2] / 2.0) * T
        m = mitte(oa)
        links, rechts = sorted((o1, o2), key=mitte)
        d = round((m - mitte(links) + mitte(rechts) - m) / 2.0)
        links['x'] += int(round(m - d - mitte(links)))
        rechts['x'] += int(round(m + d - mitte(rechts)))
    # Spawnfeld frei (Regel "Teleporter- und Spawnfelder frei"): um das Portal keine Streudeko
    for o in objekte:
        if o['basis'].startswith('zufall_portal/'):
            bx, by, wt, ht = o['block']
            for x in range(bx - 2, bx + wt + 2):
                for y in range(by - 1, by + ht + 3):
                    gesperrt.add((x, y))
    # 2. Begleiter der einzelnen Baeume (Regel 5d, wie Karte 23)
    for i, b in enumerate([o for o in objekte if o['basis'] in BEGLEITET]):
        bx, by, wt, ht = b['block']
        cx, fy = bx * T + wt * T // 2, (by + ht) * T - 1
        seite = -1 if i % 2 else 1
        art = rnd.randrange(3)
        if art == 0:                                             # vor dem Stumpf: hoher Fels, eine Kachel tiefer
            setze(rnd.choice(HOCH_FELS), cx / T, fy // T + 1, {'px': cx + seite * 5, 'py': fy + T, 'begleiter': True})
        elif art == 1:                                           # hinter den Blaettern + hohe Blume an der Sockelecke
            setze(rnd.choice(FELS_GROSS), cx / T, fy // T - 1, {'px': cx + seite * 8, 'py': fy - 7, 'begleiter': True})
            setze(rnd.choice(HOCH_BLUME), cx / T, fy // T + 1, {'px': cx - seite * 13, 'py': fy + T, 'anim': 'wehen',
                                                                'begleiter': True})
        else:                                                    # hinter den Blaettern + hohe Blume vor dem Stumpf
            setze(rnd.choice(FELS_GROSS), cx / T, fy // T - 1, {'px': cx + seite * 9, 'py': fy - 7, 'begleiter': True})
            setze(rnd.choice(HOCH_BLUME), cx / T, fy // T + 1, {'px': cx - seite * 5, 'py': fy + T, 'anim': 'wehen',
                                                                'begleiter': True})
        for x in range(bx - 1, bx + wt + 1):                     # nichts Freies auf Stammhoehe
            for y in (by + ht - 2, by + ht - 1, by + ht):
                gesperrt.add((x, y))
    # 3. Wald auf jeder zweiten Waldkachel (wie Karte 06/20)
    for ty in range(rows):
        for tx in range(cols):
            if raster[ty][tx] == 'F' and (tx + ty) % 2 == 0:
                setze(rnd.choice(WALD), tx, ty, {'spiegeln': rnd.random() < 0.5}, frei=True, wald=True)
    # 4. Streudeko auf der Wiese: nicht am Weg (1 Kachel), nicht am Wasser, ohne Wiederholung, dezent
    wiese = [(tx, ty) for ty in range(rows) for tx in range(cols) if raster[ty][tx] == 'G']
    if innen:                                                    # Export: 2 Kacheln Abstand zum Stueckrand (Nachbar unbekannt)
        x0, y0, x1, y1 = innen
        wiese = [(tx, ty) for (tx, ty) in wiese if x0 + 2 <= tx <= x1 - 3 and y0 + 2 <= ty <= y1 - 3]
    ziel = len(wiese) // 22 if wiese else 0
    vorrat, n = [], 0
    for _ in range(ziel * 40):
        if n >= ziel:
            break
        tx, ty = rnd.choice(wiese)
        if any(k(tx + dx, ty + dy) in 'PW' for dx in (-1, 0, 1) for dy in (-1, 0, 1, 2)):
            continue
        if not vorrat:
            vorrat = DEKO[:]
            rnd.shuffle(vorrat)
        name = vorrat[-1]
        nachbarn = [o['basis'] for o in objekte if abs(o['kachel'][0] - tx) <= 3 and abs(o['kachel'][1] - ty) <= 3]
        if name in nachbarn:                                     # gleiche Motive nie nebeneinander
            continue
        if setze(name, tx, ty, {'anim': 'wehen'} if name in DEKO_PFLANZE and rnd.random() < 0.6 else {}, frei=True):
            vorrat.pop()
            n += 1
    return objekte


def waldboden(boden_rgb, objekte, obj_dir):
    """Waldboden und Oberflaechenwurzeln unter dem Dschungelbaum (gehoeren zum Boden) -> neues RGB-Array."""
    import karte_bauen as kb
    img = Image.fromarray(boden_rgb).convert('RGBA')
    for o in objekte:
        if o['basis'].startswith('dschungel/'):
            kb.waldboden(img, o, Image.open(os.path.join(obj_dir, o['datei'])).convert('RGBA'))
    return np.array(img.convert('RGB'))


def zeichnen(boden_rgb, wasser, objekte, obj_dir, frame=None):
    """Boden (mit waldboden() vorbereitet) + Objekte (Schatten nur auf dem Boden, nie aufs Wasser) -> RGBA-Bild."""
    import karte04_bauen as k4
    img = Image.fromarray(boden_rgb).convert('RGBA')
    objs = sorted(objekte, key=lambda o: (o.get('ebene', 1), o['y'] + o['fuss']))
    cache = {o['datei']: Image.open(os.path.join(obj_dir, o['datei'])).convert('RGBA') for o in objs}
    ebenen = np.ones(wasser.shape, np.int16)
    ebenen[wasser] = 7
    k4.objekte_zeichnen(img, objs, cache, ~wasser, frame, ebenen=ebenen)
    k4.animieren(img, objs, cache, frame or 0)
    return img, cache


def bauen(raster, fest, symmetrie, obj_dir, seed=1, frame=None):
    boden, wasser = boden_bauen(raster, frame)
    objekte = objekte_setzen(raster, fest, symmetrie, obj_dir, seed)
    boden = waldboden(boden, objekte, obj_dir)
    bild, cache = zeichnen(boden, wasser, objekte, obj_dir, frame)
    return {'bild': bild, 'boden': boden, 'objekte': objekte, 'cache': cache, 'wasser': wasser}


def kollision(raster, objekte, cache, wasser, x0=0, y0=0, w=None, h=None):
    """Kollision je Kachel wie tools/kollision.py: 1 begehbar, 2 gesperrt (Wald, Wasser, Objektfuss), 3 begehbar und
    verdeckt (obere Teile hoher Objekte). Ausschnitt ab Kachel (x0, y0) mit Groesse w x h."""
    FUSS, MIN_FUSS, MIN_DECKT = 10, 4, 12
    rows, cols = len(raster), len(raster[0])
    w, h = w or cols, h or rows
    fuss = np.zeros((rows * T, cols * T), bool)
    deckt = np.zeros_like(fuss)
    for o in objekte:
        if o.get('ebene', 1) != 1 or o.get('anim') == 'wehen':
            continue
        a = np.array(cache[o['datei']].getchannel('A')) >= 200
        zl = np.nonzero(a.any(axis=1))[0]
        if not len(zl):
            continue
        unten = a.copy(); unten[:max(0, zl.max() - FUSS + 1)] = False
        oben = a & ~unten
        for m_, ziel in ((unten, fuss), (oben, deckt)):
            ys, xs = np.nonzero(m_)
            Y, X = ys + o['y'], xs + o['x']
            ok = (Y >= 0) & (Y < ziel.shape[0]) & (X >= 0) & (X < ziel.shape[1])
            ziel[Y[ok], X[ok]] = True
    out = []
    for ty in range(y0, y0 + h):
        zeile = ''
        for tx in range(x0, x0 + w):
            sl = (slice(ty * T, (ty + 1) * T), slice(tx * T, (tx + 1) * T))
            if raster[ty][tx] == 'F' or wasser[sl].mean() > 0.5 or fuss[sl].sum() >= MIN_FUSS:
                zeile += '2'
            elif deckt[sl].sum() >= MIN_DECKT:
                zeile += '3'
            else:
                zeile += '1'
        out.append(zeile)
    return out
