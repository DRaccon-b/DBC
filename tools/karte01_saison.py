"""Jahreszeiten fuer Karte 01 (Herbst, spaeter Winter) - gleiche Karte, gleiche Positionen, anderes Aussehen.

  python3 tools/karte01_saison.py herbst          # Sprites + platzierung_herbst.json erzeugen
  danach: karte_bauen.bauen(saison='herbst')       # Karte im Herbst rendern

Herbst:
  - Laubbaeume und Buesche: Laub in Herbstfarben (je Baum zufaellig Orange, Rot, Gelb oder Olivgelb),
    Nadelbaeume bleiben gruen, Sonderbaeume (Rosa, Kristall, Runenbaum, Dschungelbaum) bleiben.
  - Graeser/Farne: trocken-gelblich.
  - Blumen werden durch Herbst-Deko ersetzt (Laubhaufen, Blatt, Pilze, Eichel, Zapfen, trockenes Gras -
    aus den Gras-Sets von Karte 07, Regel 3). Gleiche Fusskachel, am Raster, mittig.
  - Boden: Gras wird waermer/gelblicher (boden()).
"""
import colorsys, json, math, os, random, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
import bauwerke

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte01')
K7 = os.path.join(ROOT, 'assets', 'objekte', 'karte07', 'deko_gras')
T = 16
NADEL = {'baeume/06', 'baeume/07', 'baeume/08', 'baeume/09'}
LAUB = {'baeume/%02d' % i for i in (0, 1, 2, 3, 4, 5, 15)} | {'baeume/12', 'baeume/13', 'baeume/14', 'deko/25'}
GRAESER = {'deko/05', 'deko/06', 'deko/07', 'deko/24', 'deko/26', 'deko/61', 'deko/28',
           'k7gras/01', 'k7gras/15', 'k7gras/54', 'k7gras/63', 'k7gras/34', 'k7gras/41', 'k7gras/42'}
BLUMEN = {'deko/00', 'deko/01', 'deko/02', 'deko/03', 'deko/04', 'deko/30', 'deko/38', 'deko/27'}
HERBST_DEKO = [18, 25, 16, 17, 38, 56, 19, 27, 22, 53, 18, 25]
TOENE = {'orange': 26, 'rot': 8, 'gelb': 46, 'oliv': 60}


def _umfaerben(sp, ziel_hue, sat_mul=1.15, val_mul=1.0, nur_gruen=True):
    a = np.array(sp.convert('RGBA')).astype(np.float32) / 255.0
    r, g, b, al = a[..., 0], a[..., 1], a[..., 2], a[..., 3]
    mx = np.maximum(np.maximum(r, g), b)
    mn = np.minimum(np.minimum(r, g), b)
    gruen = (al > 0) & (g >= r) & (g >= b - 0.02) & (mx - mn > 0.06)
    if not nur_gruen:
        gruen = al > 0
    out = a.copy()
    ys, xs = np.nonzero(gruen)
    for y, x in zip(ys, xs):
        h, s, v = colorsys.rgb_to_hsv(r[y, x], g[y, x], b[y, x])
        # Licht/Schatten bleiben: Schatten etwas roeter/dunkler, Licht gelber
        hz = (ziel_hue + (v - 0.5) * 18) / 360.0
        rr, gg, bb = colorsys.hsv_to_rgb(hz % 1.0, min(1.0, s * sat_mul + 0.08), min(1.0, v * val_mul))
        out[y, x, :3] = (rr, gg, bb)
    return Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8), 'RGBA')


def boden(img, klassen, saison):
    """Gras-Pixel des Bodens in die Jahreszeit faerben (Wasser/Meer bleiben unberuehrt)."""
    if saison == 'winter':
        return boden_winter(img, klassen)
    if saison != 'herbst':
        return img
    a = np.array(img.convert('RGB')).astype(np.int16)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    gras = (g > r + 18) & (g > b + 18)
    H, W = gras.shape
    land = np.zeros((H, W), bool)
    for y, z in enumerate(klassen):
        for x, k in enumerate(z):
            if k in 'gs':
                land[y * T:(y + 1) * T, x * T:(x + 1) * T] = True
    m = gras & land
    f = a[m].astype(np.float32)
    # Richtung Herbstgras: gruen etwas runter, rot rauf (oliv-gelblich), Helligkeit fast gleich
    ziel = np.stack([f[:, 0] * 1.0 + f[:, 1] * 0.34, f[:, 1] * 0.86, f[:, 2] * 0.6], axis=1)
    neu = f * 0.5 + ziel * 0.5                        # nur halb: gedaempftes Oliv mit goldenem Stich
    a[m] = np.clip(neu, 0, 255).astype(np.int16)
    return Image.fromarray(a.astype(np.uint8)).convert('RGBA')


def boden_winter(img, klassen):
    """Winter: Gras -> Schnee (Kacheln aus Karte 05), Wege -> festgetretener Schnee, Suesswasser -> Eis,
    Meer bleibt offen."""
    a = np.array(img.convert('RGB')).astype(np.int16)
    H, W = a.shape[:2]
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    kl = np.zeros((H, W), 'U1')
    for y, z in enumerate(klassen):
        for x, k in enumerate(z):
            kl[y * T:(y + 1) * T, x * T:(x + 1) * T] = k
    schnee = np.zeros((H, W, 3), np.int16)
    ks = [np.array(Image.open(os.path.join(ROOT, 'assets', 'karte05', 'basis', 's_%d.png' % i)).convert('RGB'))
          for i in range(5)]
    for ty in range(H // T):
        for tx in range(W // T):
            schnee[ty * T:(ty + 1) * T, tx * T:(tx + 1) * T] = ks[(tx * 7 + ty * 13 + tx * ty) % 5]
    gras = (g > r + 18) & (g > b + 18) & np.isin(kl, ['g', 's'])
    hell = (r.astype(np.float32) + g + b) / 3.0
    ref = np.median(hell[gras]) if gras.any() else 120
    # Schnee hell (auf Weiss angehoben); dunklere Gruentoene (Waldboden, Grasschatten) -> leicht blaeulicher Schatten
    weiss = np.clip(schnee.astype(np.float32) * 0.55 + np.array([250, 252, 255]) * 0.45, 0, 255)
    schatten = (hell < ref - 18)[..., None]
    ziel = np.where(schatten, weiss * np.array([0.86, 0.9, 0.97]), weiss)
    a[gras] = ziel[gras].astype(np.int16)
    # Sand (Wege und Strand, inkl. dunkler Wegkante): festgetretener Schnee mit Hauch Sand
    sand = (r >= g - 4) & (r > b + 15) & (kl != 'm') & (kl != 'w') & (hell > 135)
    a[sand] = (a[sand] * 0.25 + np.array([232, 234, 240]) * 0.75).astype(np.int16)
    # Suesswasser (Fluss, Teich) -> Eis: helles Blau, Struktur bleibt schwach sichtbar
    wasser = (kl == 'w') & (b > r + 20)
    eis = np.array([196, 226, 242])
    a[wasser] = (a[wasser] * 0.35 + eis * 0.65).astype(np.int16)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert('RGBA')


def _schneehaube(sp, dicke=3, laub=None):
    """Schnee auf alle nach oben offenen Kanten (Licht oben links), optional Laub abdunkeln/entsaettigen."""
    a = np.array(sp.convert('RGBA')).astype(np.int16)
    al = a[..., 3] > 0
    h, w = al.shape
    if laub is not None:
        r, g, b = a[..., 0], a[..., 1], a[..., 2]
        gruen = al & (g >= r) & (g >= b - 5)
        grau = (r + g + b) // 3
        for c, f in ((0, laub[0]), (1, laub[1]), (2, laub[2])):
            a[..., c] = np.where(gruen, (a[..., c] * 0.45 + grau * 0.55) * f, a[..., c])
    oben = al & ~np.vstack([np.zeros((1, w), bool), al[:-1]])
    weiss = np.array([244, 248, 255]); blau = np.array([200, 214, 236])
    for y, x in zip(*np.nonzero(oben)):
        if y > h * 0.8:
            continue
        for d in range(dicke):
            if y + d < h and al[y + d, x]:
                a[y + d, x, :3] = weiss if d < dicke - 1 else blau
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), 'RGBA')


def winter():
    rnd = random.Random(41)
    objs = json.load(open(os.path.join(OBJ, 'platzierung.json')))
    os.makedirs(os.path.join(OBJ, 'winter'), exist_ok=True)
    K7S = os.path.join(ROOT, 'assets', 'objekte', 'karte07', 'deko_schnee')
    cache = {}

    def variante(o, art):
        key = (o['datei'], art)
        if key not in cache:
            sp = Image.open(os.path.join(OBJ, o['datei'])).convert('RGBA')
            if art == 'laub':
                neu = _schneehaube(sp, 4, laub=(0.82, 0.9, 1.05))
            elif art == 'nadel':
                neu = _schneehaube(sp, 3)
            elif art == 'gras':
                neu = _umfaerben(sp, 205, sat_mul=0.3, val_mul=1.25)
            else:
                neu = _schneehaube(sp, 2)
            name = 'winter/%s_%s.png' % (o['datei'][:-4].replace('/', '-'), art)
            neu.save(os.path.join(OBJ, name))
            cache[key] = name
        return cache[key]
    deko_cache = {}

    def deko(i):
        if i not in deko_cache:
            sp = Image.open(os.path.join(K7S, '%02d.png' % i)).convert('RGBA')
            basis = 'winter/k7schnee-%02d' % i
            sp.save(os.path.join(OBJ, basis + '.png'))
            al = np.array(sp.getchannel('A')) > 0
            ys, xs = np.nonzero(al)
            deko_cache[i] = (basis, basis + '.png', sp.height, int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()))
        return deko_cache[i]
    WINTER_DEKO = [5, 9, 28, 30, 36, 41, 44, 45, 0, 34]
    STEINE = {'deko/08', 'deko/09', 'deko/10', 'deko/11', 'deko/12', 'deko/13', 'deko/51', 'gross/09', 'gross/07'}
    neu, n = [], {'laub': 0, 'nadel': 0, 'gras': 0, 'deko': 0, 'stein': 0}
    for o in objs:
        b = o['basis']
        if b in ('deko/17', 'deko/18', 'deko/19', 'deko/07'):     # Seerosen/Schilf: Teich ist zugefroren
            continue
        o = dict(o)
        if b in LAUB or b in ('gross/00', 'gross/01', 'gross/02', 'dschungel/00'):
            o['datei'] = variante(o, 'laub'); n['laub'] += 1
        elif b in NADEL:
            o['datei'] = variante(o, 'nadel'); n['nadel'] += 1
        elif b in GRAESER:
            o['datei'] = variante(o, 'gras'); n['gras'] += 1
        elif b in STEINE or b.startswith(('gross/', 'zelt_strand/')) or b == 'laterne':
            o['datei'] = variante(o, 'haube'); n['stein'] += 1
        elif b in BLUMEN or b.startswith('deko/') and o.get('untergrund') == 'gras':
            basis, datei, h, x0, y0, x1, y1 = deko(rnd.choice(WINTER_DEKO))
            bw, bh = x1 - x0 + 1, y1 - y0 + 1
            wt, ht = math.ceil(bw / T), math.ceil(bh / T)
            kx, ky = o['kachel']
            bx = kx - (wt - 1) // 2
            o.update(datei=datei, basis=basis, x=bx * T + (wt * T - bw) // 2 - x0, y=(ky + 1) * T - 1 - y1, fuss=h,
                     block=[bx, ky - ht + 1, wt, ht])
            o.pop('anim', None); o.pop('untergrund', None)
            n['deko'] += 1
        neu.append(o)
    json.dump(neu, open(os.path.join(OBJ, 'platzierung_winter.json'), 'w'), indent=0)
    print('Winter:', n)


def herbst():
    rnd = random.Random(31)
    objs = json.load(open(os.path.join(OBJ, 'platzierung.json')))
    ziel = os.path.join(OBJ, 'herbst')
    os.makedirs(ziel, exist_ok=True)
    cache = {}

    def variante(o, ton):
        """Herbst-Variante der Datei eines Objekts (inkl. Bodenfuss-Variante, gleiche Groesse/Lage)."""
        key = (o['datei'], ton)
        if key not in cache:
            sp = Image.open(os.path.join(OBJ, o['datei'])).convert('RGBA')
            if ton in TOENE:
                neu = _umfaerben(sp, TOENE[ton])
            else:                                         # trockenes Gras
                neu = _umfaerben(sp, 48, sat_mul=0.75, val_mul=1.02)
            name = 'herbst/%s_%s.png' % (o['datei'][:-4].replace('/', '-'), ton)
            neu.save(os.path.join(OBJ, name))
            cache[key] = name
        return cache[key]
    deko_cache = {}

    def deko(i):
        if i not in deko_cache:
            quelle = os.path.join(K7, '%02d.png' % i)
            sp = Image.open(quelle).convert('RGBA')
            basis = 'herbst/k7gras-%02d' % i
            sp.save(os.path.join(OBJ, basis + '.png'))
            v = bauwerke.bodenfuss(sp, 'gras', 'klein')
            datei = basis + '_gras.png'
            v.save(os.path.join(OBJ, datei))
            al = np.array(sp.getchannel('A')) > 0
            ys, xs = np.nonzero(al)
            off = 2 if v.size == (sp.width + 4, sp.height + 3) else 0
            deko_cache[i] = (basis, datei, v.height, int(xs.min()) + off, int(ys.min()), int(xs.max()) + off,
                             int(ys.max()))
        return deko_cache[i]
    neu, n_baum, n_gras, n_blume = [], 0, 0, 0
    for o in objs:
        b = o['basis']
        o = dict(o)
        if b in LAUB:
            ton = rnd.choice(['orange', 'orange', 'rot', 'gelb', 'gelb', 'oliv'])
            o['datei'] = variante(o, ton)
            n_baum += 1
        elif b in GRAESER:
            o['datei'] = variante(o, 'trocken')
            n_gras += 1
        elif b in BLUMEN:
            basis, datei, h, x0, y0, x1, y1 = deko(rnd.choice(HERBST_DEKO))
            bw, bh = x1 - x0 + 1, y1 - y0 + 1
            wt, ht = math.ceil(bw / T), math.ceil(bh / T)
            kx, ky = o['kachel']
            bx = kx - (wt - 1) // 2
            o.update(datei=datei, basis=basis, x=bx * T + (wt * T - bw) // 2 - x0, y=(ky + 1) * T - 1 - y1, fuss=h,
                     block=[bx, ky - ht + 1, wt, ht], untergrund='gras')
            o.pop('anim', None)
            n_blume += 1
        neu.append(o)
    json.dump(neu, open(os.path.join(OBJ, 'platzierung_herbst.json'), 'w'), indent=0)
    print('Herbst: %d Laubbaeume/Buesche umgefaerbt, %d Graeser trocken, %d Blumen -> Herbst-Deko'
          % (n_baum, n_gras, n_blume))


if __name__ == '__main__':
    {'herbst': herbst, 'winter': winter}[sys.argv[1]]()
