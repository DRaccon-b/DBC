"""Regeln aus CLAUDE.md auf bestehende Karten anwenden (v1.1) - Objekt-Teil.

  python3 tools/regeln_v11.py karte04      # nach karte04_objekte.py, vor karte04_bauen.py
  python3 tools/regeln_v11.py karte02

1/1b   jedes Objekt im kleinsten Kachelblock, waagerecht zentriert, Fuss buendig auf der Kachelunterkante
       (gemessen am eigentlichen Sprite ohne Bodenfuss-Halme)
       Liegende Objekte (Knochen, Aeste, Ketten, Schrott ...) werden markiert -> flacher Schatten der ganzen Form
       Keine ungewollten Ueberlappungen nach dem Einrasten (kleineres Objekt faellt weg; Baeume untereinander ok)
"""
import json, math, os, sys
import numpy as np
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
T = 16
LIEGEND = {
    'karte04': {'klein/%02d' % i for i in (2, 3, 4, 6, 9, 10, 12, 13, 15, 18, 20, 24, 29, 30, 33, 34, 43, 47, 49, 51,
                                          53, 54, 55, 58, 59, 60, 62, 63)},
    'karte02': set(),
    'karte03': {'klein/%02d' % i for i in (6, 7, 33, 34, 37, 51, 54, 63)},
}
NICHT_RASTERN = {'karte02': ('schatten', 'abgeleitet/laterne', 'abgeleitet/leer', 'kran'),
                 'karte03': ('abgeleitet/arena_tor', 'abgeleitet/buehne', 'abgeleitet/box_monitor')}
BAUM = ('baeume/', 'rand/')
ABSTAND = {'karte03': 1}                             # Pixelpruefung mit Abstand (je Seite 1 px = 2 px Luecke)


def umriss(obj_dir, o, cache):
    key = (o['datei'], o.get('basis'), bool(o.get('spiegeln')))
    if key not in cache:
        var = Image.open(os.path.join(obj_dir, o['datei'])).convert('RGBA')
        basis = os.path.join(obj_dir, (o.get('basis') or '') + '.png')
        off = 0
        im = var
        if o['datei'].startswith('varianten/') and os.path.exists(basis):
            orig = Image.open(basis).convert('RGBA')
            if var.size == (orig.width + 4, orig.height + 3):
                im, off = orig, 2
        if o.get('spiegeln'):
            im = im.transpose(Image.FLIP_LEFT_RIGHT)
        a = np.array(im.getchannel('A')) >= 128
        ys, xs = np.nonzero(a)
        cache[key] = (int(xs.min()) + off, int(ys.min()), int(xs.max()) + off, int(ys.max())) if len(xs) else None
    return cache[key]


def main(karte):
    obj_dir = os.path.join(ROOT, 'assets', 'objekte', karte)
    pf = os.path.join(obj_dir, 'platzierung.json')
    objs = json.load(open(pf))
    cache = {}
    skip = NICHT_RASTERN.get(karte, ())
    n = 0
    for o in objs:
        b = o.get('basis') or ''
        if b in skip or any(s in b for s in skip if s == 'kran'):
            continue
        u = umriss(obj_dir, o, cache)
        if not u:
            continue
        x0, y0, x1, y1 = u
        bw, bh = x1 - x0 + 1, y1 - y0 + 1
        wt, ht = math.ceil(bw / T), math.ceil(bh / T)
        fx, fy = o['x'] + (x0 + x1) / 2.0, o['y'] + y1
        bx = int(round(fx / T - wt / 2.0))
        by = int(fy // T)
        nx, ny = bx * T + (wt * T - bw) // 2 - x0, (by + 1) * T - 1 - y1
        if (nx, ny) != (o['x'], o['y']):
            n += 1
        o['x'], o['y'] = nx, ny
        o['kachel'] = [bx + (wt - 1) // 2, by]
        o['block'] = [bx, by - ht + 1, wt, ht]
        if b in LIEGEND.get(karte, ()):
            o['liegend'] = True
    # Ueberlappungen nach dem Einrasten: kleinere Objekte entfernen (Baeume untereinander und Feste bleiben)
    alpha = {}
    abstand = ABSTAND.get(karte, 0)                        # Regel 'Keine Ueberlappungen': 2 px Abstand
    def maske(o):
        if o['datei'] not in alpha:
            m_ = np.array(Image.open(os.path.join(obj_dir, o['datei'])).getchannel('A')) >= 200
            if abstand:
                from PIL import ImageFilter as _IF
                m_ = np.array(Image.fromarray((m_ * 255).astype(np.uint8)).filter(_IF.MaxFilter(2 * abstand + 1))) > 0
            alpha[o['datei']] = m_
        a = alpha[o['datei']]
        return a[:, ::-1] if o.get('spiegeln') else a
    W = max(o['x'] + maske(o).shape[1] for o in objs) + 8
    Hh = max(o['y'] + maske(o).shape[0] for o in objs) + 8
    besitzer = -np.ones((Hh, W), np.int32)
    weg = set()
    reihenfolge = sorted(range(len(objs)), key=lambda i: (0 if objs[i].get('vorrang') else 1, -maske(objs[i]).sum()))
    for i in reihenfolge:
        o = objs[i]
        b = o.get('basis') or ''
        if b in skip:
            continue
        a = maske(o)
        h, w = a.shape
        xs0, ys0 = max(0, o['x']), max(0, o['y'])
        teil = a[ys0 - o['y']:, xs0 - o['x']:]
        ber = besitzer[ys0:ys0 + teil.shape[0], xs0:xs0 + teil.shape[1]]
        teil = teil[:ber.shape[0], :ber.shape[1]]
        konflikt = [j for j in set(np.unique(ber[teil & (ber >= 0)]).tolist())
                    if not (b.startswith(BAUM) and (objs[j].get('basis') or '').startswith(BAUM))]
        if o.get('begleiter'):                    # gewollte Ueberdeckung vor dem Sockel (Regel 5 / Einbettung)
            continue
        if konflikt and (o.get('ebene', 1) == 0 or b.startswith(('klein/', 'mittel/', 'rosa/', 'blueten/'))) and not b.startswith(BAUM) and not o.get('vorrang'):
            weg.add(i)
            continue
        ber[teil] = i
    objs = [o for i, o in enumerate(objs) if i not in weg]
    json.dump(objs, open(pf, 'w'), indent=0)
    print('%s: %d Objekte aufs Raster verschoben, %d liegend markiert, %d wegen Ueberlappung entfernt, %d gesamt'
          % (karte, n, sum(1 for o in objs if o.get('liegend')), len(weg), len(objs)))


def boegen(g, anker, erlaubt, A=3.6, zelle=9, weg_klasse='w', ersatz='s', seed=(3, 7)):
    """Regel 6 allgemein: Wegzellen (weg_klasse) in g (2D-Array Klassen) mit einem weichen Verschiebungsfeld
    verbiegen; an Ankern (anker=True) bleibt alles wie es ist, nur Zellen mit erlaubt=True aendern sich."""
    from PIL import ImageFilter
    g = g.copy()
    rows, cols = g.shape
    weg = g == weg_klasse
    anker = anker | ~erlaubt
    dist = np.where(anker, 0.0, 99.0)
    for _ in range(8):
        dist = np.minimum.reduce([dist, np.roll(dist, 1, 0) + 1, np.roll(dist, -1, 0) + 1,
                                  np.roll(dist, 1, 1) + 1, np.roll(dist, -1, 1) + 1])
    SUB = 4

    def glatt(f, s_):
        im = Image.fromarray((np.clip(f, 0, 1) * 255).astype(np.uint8))
        return np.array(im.filter(ImageFilter.GaussianBlur(s_))).astype(np.float32) / 255.0
    gew = glatt(np.kron(np.clip((dist - 1) / 4.0, 0, 1), np.ones((SUB, SUB))), SUB * 1.5)

    def rauschen(sd):
        rs = np.random.RandomState(sd)
        n = rs.rand(rows // zelle + 3, cols // zelle + 3).astype(np.float32) * 2 - 1
        im = Image.fromarray(n, mode='F').resize(((cols // zelle + 3) * zelle * SUB, (rows // zelle + 3) * zelle * SUB),
                                                 Image.BICUBIC)
        return np.array(im)[:rows * SUB, :cols * SUB]
    dx, dy = rauschen(seed[0]) * A * gew, rauschen(seed[1]) * A * gew
    m = np.kron(weg, np.ones((SUB, SUB))).astype(np.float32)
    Hs, Ws = m.shape
    yy, xx = np.mgrid[0:Hs, 0:Ws].astype(np.float32)
    sy = np.clip(np.round(yy + dy * SUB), 0, Hs - 1).astype(int)
    sx = np.clip(np.round(xx + dx * SUB), 0, Ws - 1).astype(int)
    neu = (glatt(m[sy, sx], SUB * 0.9) > 0.42).reshape(rows, SUB, cols, SUB).mean(axis=(1, 3)) > 0.4
    neu[anker] = weg[anker]
    g[neu & ~weg & erlaubt] = weg_klasse
    g[~neu & weg & erlaubt] = ersatz
    return g


def wege(karte, darf=('s', 'w', 'g', 'd'), A=3.6, zelle=9):
    """Regel 6: Wege (Klasse w) in natuerlichen Boegen; Treppen, Bruecken, Furten, Teleporter, Hoehenkanten und
    Kartenrand bleiben fest. Original: maps/<karte>/v1.0/layout_v1.0.json."""
    from PIL import ImageFilter
    km = os.path.join(ROOT, 'maps', karte)
    lay = json.load(open(os.path.join(km, 'v1.0', 'layout_v1.0.json')))
    g = np.array([list(r) for r in lay['klassen']])
    hoehe = np.array([[int(c) for c in r] for r in lay['hoehe']])
    rows, cols = g.shape
    weg = g == 'w'
    erlaubt = np.isin(g, list(darf))
    anker = np.zeros((rows, cols), bool)
    for t in lay.get('treppen', []):
        x0, x1, y0, y1 = t[:4]
        anker[max(0, y0 - 3):y1 + 4, max(0, x0 - 2):x1 + 3] = True
    for tp in lay.get('teleporter', []):
        anker[max(0, tp['y'] - 3):tp['y'] + tp['h'] + 3, max(0, tp['x'] - 3):tp['x'] + tp['b'] + 3] = True
    for f in lay.get('furten', []) + ([lay['bruecke']] if lay.get('bruecke') else []):
        anker[max(0, f[0] - 3):f[1] + 4, :] |= np.isin(g[max(0, f[0] - 3):f[1] + 4, :], ['c', 'x', 'f', 'w']) & False
        anker[max(0, f[0] - 2):f[1] + 3, :] |= weg[max(0, f[0] - 2):f[1] + 3, :] & \
            (np.abs(np.arange(cols) - np.argmax(np.isin(g, ['x']).any(axis=0))) < 14)[None, :]
    anker[:, :4] = anker[:, -4:] = True
    anker[:3, :] = anker[-3:, :] = True
    kante = np.zeros_like(anker)
    kante[:-1] |= hoehe[:-1] != hoehe[1:]
    kante[1:] |= hoehe[:-1] != hoehe[1:]
    kante[:, :-1] |= hoehe[:, :-1] != hoehe[:, 1:]
    kante[:, 1:] |= hoehe[:, :-1] != hoehe[:, 1:]
    anker |= kante | ~erlaubt
    dist = np.where(anker, 0.0, 99.0)
    for _ in range(8):
        dist = np.minimum.reduce([dist, np.roll(dist, 1, 0) + 1, np.roll(dist, -1, 0) + 1,
                                  np.roll(dist, 1, 1) + 1, np.roll(dist, -1, 1) + 1])
    SUB = 4

    def glatt(f, s_):
        im = Image.fromarray((np.clip(f, 0, 1) * 255).astype(np.uint8))
        return np.array(im.filter(ImageFilter.GaussianBlur(s_))).astype(np.float32) / 255.0
    gew = glatt(np.kron(np.clip((dist - 1) / 4.0, 0, 1), np.ones((SUB, SUB))), SUB * 1.5)

    def rauschen(seed):
        rs = np.random.RandomState(seed)
        n = rs.rand(rows // zelle + 3, cols // zelle + 3).astype(np.float32) * 2 - 1
        im = Image.fromarray(n, mode='F').resize(((cols // zelle + 3) * zelle * SUB, (rows // zelle + 3) * zelle * SUB),
                                                 Image.BICUBIC)
        return np.array(im)[:rows * SUB, :cols * SUB]
    dx, dy = rauschen(3) * A * gew, rauschen(7) * A * gew
    m = np.kron(weg, np.ones((SUB, SUB))).astype(np.float32)
    Hs, Ws = m.shape
    yy, xx = np.mgrid[0:Hs, 0:Ws].astype(np.float32)
    sy = np.clip(np.round(yy + dy * SUB), 0, Hs - 1).astype(int)
    sx = np.clip(np.round(xx + dx * SUB), 0, Ws - 1).astype(int)
    neu = (glatt(m[sy, sx], SUB * 0.9) > 0.42).reshape(rows, SUB, cols, SUB).mean(axis=(1, 3)) > 0.4
    neu[anker] = weg[anker]
    n = 0
    for y in range(rows):
        for x in range(cols):
            if not erlaubt[y, x]:
                continue
            if neu[y, x] and not weg[y, x]:
                g[y, x] = 'w'; n += 1
            elif not neu[y, x] and weg[y, x]:
                g[y, x] = 's'; n += 1
    lay['klassen'] = [''.join(r) for r in g]
    json.dump(lay, open(os.path.join(km, 'layout.json'), 'w'))
    print('%s Regel 6: %d Wegzellen geaendert' % (karte, n))


if __name__ == '__main__':
    if len(sys.argv) > 2 and sys.argv[2] == 'wege':
        wege(sys.argv[1])
    else:
        main(sys.argv[1])
