"""Baut Karte 01 aus Basiskacheln, PixelLab-Wang-Tilesets und Objekten.

  python3 tools/karte_bauen.py

Eingaben
  maps/karte01/terrain_grid.json   Gelaendetyp je 16x16-Kachel (aus dem Original)
  maps/karte01/hoehenplan.json     Klippenverlauf (Segmente mit Unterkante t und Hoehe h), Treppen
  assets/basis/*.png               handgezeichnete Grundkacheln (Gras, Sand, Wasser, Meer; je 5 Varianten)
  assets/tilesets/pixellab/*.json  Wang-Uebergaenge: gras_weg, wasser_gras, wasser_sand, meer_sand, meer_wasser
  tools/klippen.py                 handgezeichnete Klippenwaende (prozedural)
  assets/objekte/karte01/platzierung.json  (optional) Objekte mit Position, von objekte_setzen.py
Ausgaben
  maps/karte01/terrain_basis.png   Boden + Klippen (ohne Objekte)
  maps/karte01/terrain.png         fertige Karte mit Objekten
  maps/karte01/tilemap.json        Tile je Kachel (Set + Tile-Name bzw. Basiskachel)

Prinzip: Jede Kachel liest ihre 4 Eck-Vertices (Wang-Ecken). Reine Flaechen werden durch
die handgezeichneten Basiskacheln ersetzt (zufaellig, aber reproduzierbar aus 5 Varianten),
Uebergaenge kommen aus den PixelLab-Sets, die mit genau diesen Basiskacheln als Referenz
erzeugt wurden. Klippen werden prozedural gezeichnet (Saeulen, Risse, Runen, Graskante),
damit sie in jeder Hoehe ohne Wiederholung funktionieren.
"""
import base64, io, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from collections import Counter
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte01')
TS_DIR = os.path.join(ROOT, 'assets', 'tilesets', 'pixellab')
BASIS = os.path.join(ROOT, 'assets', 'basis')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte01')
LOWER, UPPER, TRANS, ANY = 0, 1, 2, 255
T = 16

# Gelaendeklassen aus dem Raster: g = Gras (inkl. Wald), s = Sand (Wege, Strand), w = Suesswasser, m = Meer
KLASSE = {'G': 'g', 'F': 'g', 'C': 'g', 'R': 's', 'P': 's', 'p': 's', 'S': 's', 's': 's',
          'W': 'w', 'B': 'w', 'h': 'w', 'D': 'm'}   # h = Flachwasser am Strand
MIN_FLECK = {'s': 8, 'w': 6}     # kleinere Flecken (Baumstaemme/-schatten im Original) -> Gras
BASIS_NAME = {'g': 'gras', 's': 'sand', 'w': 'wasser', 'm': 'meer'}
# Welches Set fuer welche Paarung: (set, Klasse auf LOWER, Klasse auf UPPER)
PAARE = {frozenset('gs'): ('gras_weg', 's', 'g'),
         frozenset('gw'): ('wasser_gras', 'w', 'g'),
         frozenset('sw'): ('wasser_sand', 'w', 's'),
         frozenset('ms'): ('meer_sand', 'm', 's'),
         frozenset('gm'): ('meer_sand', 'm', 's'),      # Meer grenzt nie direkt an Gras: Sand dazwischen
         frozenset('mw'): ('meer_wasser', 'm', 'w')}


def lade_set(name):
    f = os.path.join(TS_DIR, name + '.json')
    if not os.path.exists(f):
        return None
    d = json.load(open(f))
    tiles = []
    for t in d['tileset']['tiles']:
        p = t['pattern_4x4']
        tiles.append({'name': t['name'], 'pat': [p['row_%d' % i] for i in range(4)],
                      'img': Image.open(io.BytesIO(base64.b64decode(t['image']['base64']))).convert('RGBA')})
    return {'id': d.get('id'), 'tiles': tiles}


def waehle(tiles, pat):
    """Tile mit bestem pattern_4x4 (255 = egal). Rueckgabe (tile, Fehler in den Kernecken)."""
    best = None
    for t in tiles:
        core = sum(t['pat'][r][c] != pat[r][c] for r in (1, 2) for c in (1, 2))
        err = sum(1 for r in range(4) for c in range(4)
                  if t['pat'][r][c] != ANY and t['pat'][r][c] != pat[r][c])
        spec = sum(1 for r in range(4) for c in range(4) if t['pat'][r][c] != ANY)
        score = (core, err, -spec)
        if best is None or score < best[0]:
            best = (score, t)
    return best[1], best[0][0]


def variante(x, y, n=5):
    h = (x * 73856093) ^ (y * 19349663) ^ 0x5bd1e995
    h = (h ^ (h >> 13)) * 0x5bd1e995 & 0xffffffff
    return (h ^ (h >> 15)) % n


def bereinigen(cls, rows, cols):
    """Kleine zusammenhaengende Flecken einer Klasse zu Gras machen."""
    gesehen = set()
    for y0 in range(rows):
        for x0 in range(cols):
            k = cls[y0][x0]
            if k not in MIN_FLECK or (x0, y0) in gesehen:
                continue
            comp, stack = [], [(x0, y0)]
            gesehen.add((x0, y0))
            while stack:
                x, y = stack.pop(); comp.append((x, y))
                for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                    if 0 <= nx < cols and 0 <= ny < rows and (nx, ny) not in gesehen and cls[ny][nx] == k:
                        gesehen.add((nx, ny)); stack.append((nx, ny))
            if len(comp) < MIN_FLECK[k]:
                for x, y in comp:
                    cls[y][x] = 'g'


# ---------------------------------------------------------------- Animation
N_FRAMES = 16
PENDEL = [0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 3, 3, 2, 2, 1, 1]      # Hin-und-her-Schwappen (Teich, Meer)
WASSERSETS = {'wasser_gras': ('wasser',), 'wasser_sand': ('wasser',), 'meer_sand': ('meer',),
              'meer_wasser': ('meer', 'wasser')}
SCHAUM = {(0xdf, 0xf3, 0xff), (0xff, 0xff, 0xff), (0x9a, 0xe8, 0xe0), (0x5f, 0xd0, 0xd0)}


def verschiebung(art, gridzeichen, y, frame):
    """Wie weit sich das Wasser dieser Kachel im Frame bewegt (dx, dy)."""
    if art == 'wasser' and gridzeichen in 'WB' and y < 53:
        return 0, frame                      # Fluss: fliesst nach unten, 1 px pro Frame (16er-Schleife)
    return PENDEL[frame], 0                  # Teich, Flachwasser, Meer: sanftes Schwappen


def wasser_frame(kachel, beschr, gridzeichen, y, x, frame, basis):
    from PIL import ImageChops
    art, _, rest = beschr.partition(':')
    if art == 'basis' and rest.startswith(('wasser', 'meer')):
        name, i = rest.rsplit('_', 1)
        dx, dy = verschiebung(name, gridzeichen, y, frame)
        return ImageChops.offset(basis['w' if name == 'wasser' else 'm'][int(i)], dx, dy)
    if art not in WASSERSETS:
        return kachel
    out = kachel.copy()
    po, pk = out.load(), kachel.load()
    for name in WASSERSETS[art]:
        ref = basis['w' if name == 'wasser' else 'm'][0]
        dx, dy = verschiebung(name, gridzeichen, y, frame)
        bewegt = ImageChops.offset(ref, dx, dy).load()
        pr = ref.load()
        for yy in range(T):
            for xx in range(T):
                if pk[xx, yy] == pr[xx, yy]:          # reine Wasserflaeche -> bewegtes Wasser
                    po[xx, yy] = bewegt[xx, yy]
    # Schaum glitzert: einzelne Schaumpixel wechseln von Frame zu Frame
    for yy in range(T):
        for xx in range(T):
            c = pk[xx, yy]
            if c[:3] in SCHAUM and variante(x * T + xx, y * T + yy + frame * 7, 4) == 0:
                po[xx, yy] = (0x8c, 0xc4, 0xf4, 255)
    return out


# ---------------------------------------------------------------- Wind, Wippen, Schmetterlinge
def wind(frame, x):
    """Windwelle, die von links nach rechts ueber die Karte laeuft: -1, 0 oder 1 (Pixel an der Spitze)."""
    import math
    return round(1.2 * math.sin(2 * math.pi * (frame / N_FRAMES - x / 420)))


def wehen(sp, versatz):
    """Spitzen (obere 60 %) um versatz Pixel seitlich neigen, nach unten auslaufend; Fuss bleibt stehen."""
    if versatz == 0:
        return sp
    out = Image.new('RGBA', sp.size)
    grenze = sp.height * 0.6
    for y in range(sp.height):
        d = round(versatz * (1 - y / grenze)) if y < grenze else 0
        out.paste(sp.crop((0, y, sp.width, y + 1)), (d, y))
    return out


def wippen(frame, phase):
    import math
    return round(math.sin(2 * math.pi * (frame / N_FRAMES + (phase % 97) / 97)))


FALTER_FARBEN = {'gelb': ((0xf5, 0xc8, 0x42), (0xff, 0xf2, 0xa0), (0xe8, 0x70, 0x2a)),
                 'weiss': ((0xf4, 0xf6, 0xff), (0xff, 0xff, 0xff), (0x9f, 0xb2, 0xcf)),
                 'blau': ((0x3f, 0x7f, 0xe0), (0x7f, 0xb8, 0xf8), (0x2a, 0x4f, 0xb0)),
                 'rosa': ((0xe0, 0x60, 0xa8), (0xff, 0xd2, 0xe8), (0xb2, 0x3c, 0x82))}
FALTER = {  # a = Fluegel, b = Fluegellicht, r = Fluegelrand (dunkel), x = Koerper
    'offen': ["ra...ar",
              "rbaxabr",
              ".raxar.",
              "..rxr..",
              "...x..."],
    'zu':    ["..rxr..",
              "..bxb..",
              "..axa..",
              "...x...",
              "......."],
}


def schmetterlinge(img, falter, frame):
    import math
    px = img.load()
    W, H = img.size
    for f in falter:
        a = 2 * math.pi * (frame / N_FRAMES * f['richtung'] + f['phase'])
        x = f['x'] + f['rx'] * math.cos(a)
        y = f['y'] + f['ry'] * math.sin(a) + 2 * math.sin(2 * a)       # Auf und Ab beim Flattern
        bild = FALTER['offen' if (frame + int(f['phase'] * 8)) % 4 < 2 else 'zu']
        fa, fb, fr = FALTER_FARBEN[f['farbe']]
        # kleiner Schatten am Boden
        sx, sy = int(x), int(f['y'] + f['ry'] + 10)
        for dx in (-1, 0, 1):
            if 0 <= sx + dx < W and 0 <= sy < H:
                r_, g_, b_, a_ = px[sx + dx, sy]
                px[sx + dx, sy] = (int(r_ * 0.75), int(g_ * 0.78), int(b_ * 0.8), a_)
        for dy, zeile in enumerate(bild):
            for dx, ch in enumerate(zeile):
                if ch == '.':
                    continue
                c = {'a': fa, 'b': fb, 'r': fr, 'x': (0x3a, 0x24, 0x20)}[ch]
                xx, yy = int(x) - 3 + dx, int(y) - 2 + dy
                if 0 <= xx < W and 0 <= yy < H:
                    px[xx, yy] = c + (255,)


RUNENFARBEN = [(0x2f, 0xc7, 0xd8), (0x7f, 0xf0, 0xf5), (0xe6, 0xff, 0xff)]
FEUER = [(0xc8, 0x3a, 0x3a), (0xe8, 0x70, 0x2a), (0xf5, 0xc8, 0x42), (0xff, 0xf2, 0xa0)]


def leuchten(img, frame, objs):
    """Runen pulsieren (ganze Karte), Lagerfeuer flackert."""
    import math
    import numpy as np
    a = np.array(img)
    puls = 0.5 + 0.5 * math.sin(frame / N_FRAMES * 2 * math.pi)       # 0..1
    rgb = a[..., :3].astype(np.int16)
    for i, c in enumerate(RUNENFARBEN):
        m = (rgb == c).all(axis=2)
        dunkel = np.array([int(v * 0.55) for v in c]); hell = np.array([min(255, v + 70) for v in c])
        neu = dunkel + (hell - dunkel) * (0.35 + 0.65 * puls)
        a[m, :3] = neu.astype(np.uint8)
    for o in objs:
        if o['datei'] != 'gross/14.png':
            continue
        sp = Image.open(os.path.join(OBJ, o['datei']))
        y0, y1, x0, x1 = o['y'], o['y'] + sp.height, o['x'], o['x'] + sp.width
        reg = a[y0:y1, x0:x1]
        rr = reg[..., :3].astype(np.int16)
        yy, xx = np.mgrid[y0:y1, x0:x1]
        for i, c in enumerate(FEUER):
            m = (rr == c).all(axis=2)
            # Flammen wandern: Farbe je Pixel um eine Stufe rauf/runter, je nach Frame und Ort
            stufe = (((yy + xx * 3 + frame * 5) % 7) > 3).astype(int) * 2 - 1
            ziel = np.clip(i + stufe, 0, len(FEUER) - 1)
            for j, cz in enumerate(FEUER):
                mm = m & (ziel == j)
                reg[mm, :3] = cz
        a[y0:y1, x0:x1] = reg
    img.paste(Image.fromarray(a))


def bauen(frame=None, speichern=True):
    """Baut die Karte. frame=None: statisch; frame=0..N_FRAMES-1: Animationsbild."""
    g = json.load(open(os.path.join(KARTE, 'terrain_grid.json')))
    plan = json.load(open(os.path.join(KARTE, 'hoehenplan.json')))
    grid, cols, rows = g['grid'], g['cols'], g['rows']
    sets = {n: lade_set(n) for n in ('gras_weg', 'wasser_gras', 'wasser_sand', 'meer_sand', 'meer_wasser')}
    basis = {k: [Image.open(os.path.join(BASIS, '%s_%d.png' % (n, i))).convert('RGBA') for i in range(5)]
             for k, n in BASIS_NAME.items()}

    # --- Klassen je Kachel
    cls = [[KLASSE.get(ch, 'g') for ch in row] for row in grid]
    for y in range(rows):            # Bruecke nur als Wasser, wenn sie an Wasser grenzt (sonst Baumstamm)
        for x in range(cols):
            if grid[y][x] == 'B' and not any(0 <= x + dx < cols and 0 <= y + dy < rows and grid[y + dy][x + dx] == 'W'
                                             for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                cls[y][x] = 'g'
    bereinigen(cls, rows, cols)
    # Unter Bruecken laeuft der Fluss weiter: Spalten, die ober- oder unterhalb Wasser haben, werden Wasser
    for br in plan.get('bruecken', []):
        y0, y1 = br['y'], br['y'] + br['hoehe'] - 1
        for x in range(br['x'], br['x'] + br['breite']):
            if (y0 > 0 and grid[y0 - 1][x] == 'W') or (y1 + 1 < rows and grid[y1 + 1][x] == 'W'):
                for y in range(y0, y1 + 1):
                    cls[y][x] = 'w'

    # --- Hoehenplan: Unterkante t und Hoehe h je Vertex-Spalte
    tcol, hcol = [None] * (cols + 1), [2] * (cols + 1)
    for s in plan['segmente']:
        for vx in range(s['von'], min(s['bis'], cols) + 1):
            tcol[vx], hcol[vx] = s['t'], s.get('h', 3)
    # Treppen: Weg durch die gesamte Wandhoehe fuehren
    treppen_zellen = set()
    for tr in plan.get('treppen', []):
        t, h = tcol[tr['x']], hcol[tr['x']]
        for x in range(tr['x'], tr['x'] + tr['breite']):
            for y in range(t - h - 2, t + 3):
                if 0 <= y < rows:
                    cls[y][x] = 's'
            for y in range(t - h, t + 1):
                treppen_zellen.add((x, y))

    # --- Vertex-Raster Boden: Klasse mit >=2 von 4 angrenzenden Kacheln, Vorrang m > w > s > g
    def zelle(x, y):
        return cls[min(max(y, 0), rows - 1)][min(max(x, 0), cols - 1)]
    vk = [[None] * (cols + 1) for _ in range(rows + 1)]
    for vy in range(rows + 1):
        for vx in range(cols + 1):
            c = Counter(zelle(vx + dx, vy + dy) for dx in (-1, 0) for dy in (-1, 0))
            vk[vy][vx] = next((k for k in 'mwsg' if c[k] >= 2), 'g')
    # Meer und Suesswasser nie direkt an Gras: an solchen Vertices Sand erzwingen
    for vy in range(rows + 1):
        for vx in range(cols + 1):
            if vk[vy][vx] == 'g' and any(0 <= vy + dy <= rows and 0 <= vx + dx <= cols and vk[vy + dy][vx + dx] == 'm'
                                         for dx in (-1, 0, 1) for dy in (-1, 0, 1)):
                vk[vy][vx] = 's'

    # --- Vertex-Raster Hoehe
    vh = [[(UPPER if vy < tcol[vx] else TRANS if vy == tcol[vx] else LOWER) if tcol[vx] is not None else LOWER
           for vx in range(cols + 1)] for vy in range(rows + 1)]

    def muster(v, x, y, abb=lambda a: a):
        out = []
        for vy in (y - 1, y, y + 1, y + 2):
            row = [ANY]
            for vx in (x, x + 1):
                row.append(abb(v[vy][vx]) if 0 <= vy <= rows else ANY)
            out.append(row + [ANY])
        return out

    # --- 1. Bodenebene
    karte = [[None] * cols for _ in range(rows)]      # (bild, beschreibung)
    warn = []
    for y in range(rows):
        for x in range(cols):
            ecken = {vk[y][x], vk[y][x + 1], vk[y + 1][x], vk[y + 1][x + 1]}
            if len(ecken) == 1:
                k = ecken.pop()
                i = variante(x, y)
                karte[y][x] = (basis[k][i], 'basis:%s_%d' % (BASIS_NAME[k], i))
                continue
            if len(ecken) >= 3:          # drei Gelaende an einer Kachel: das seltenste weicht (Gras zuerst)
                c = Counter([vk[y][x], vk[y][x + 1], vk[y + 1][x], vk[y + 1][x + 1]])
                while len(ecken) > 2:
                    weg = min(ecken, key=lambda k: (c[k], k != 'g'))
                    ecken.discard(weg)
            name, lo, up = PAARE[frozenset(ecken)]
            st = sets[name]
            if st is None:
                karte[y][x] = (basis[lo][0], 'fehlt:' + name)
                continue
            abb = lambda a, lo=lo, up=up: LOWER if a == lo or (a not in (lo, up) and lo in 'wm' and a in 'wm') else UPPER
            t, e = waehle(st['tiles'], muster(vk, x, y, abb))
            if e:
                warn.append((x, y, name))
            karte[y][x] = (t['img'], '%s:%s' % (name, t['name']))

    # --- Rendern (bei Animation: Wasserflaechen je Kachel verschoben, Schaum glitzert)
    img = Image.new('RGBA', (cols * T, rows * T))
    for y in range(rows):
        for x in range(cols):
            kachel = karte[y][x][0]
            if frame is not None:
                kachel = wasser_frame(kachel, karte[y][x][1], grid[y][x], y, x, frame, basis)
            img.paste(kachel, (x * T, y * T))

    # --- 2. Klippen: handgezeichnete Waende (tools/klippen.py), h Kacheln hoch
    import klippen
    treppen_px = frozenset((tr['x'] * T, (tr['x'] + tr['breite']) * T) for tr in plan.get('treppen', []))
    runen = klippen.zeichne_klippen(img, plan, cols, treppen_px)
    # Wasserfaelle: volle Flussbreite an der Wandoberkante (Spalten mit Wasser direkt oberhalb der Wand)
    for wf in plan.get('wasserfaelle', []):
        t, h = tcol[wf['x']], hcol[wf['x']]
        oben = t - h - 1
        spalten = [x for x in range(wf['x'] - 2, wf['x'] + wf['breite'] + 2) if cls[oben][x] == 'w']
        if spalten:
            # Wasserflaeche reicht durch die Wang-Ecken eine halbe Kachel weiter, minus Uferkante
            klippen.zeichne_wasserfall(img, min(spalten) * T - 5, (max(spalten) + 1) * T + 5,
                                       (t - h) * T + 8, (t + 1) * T - 2, frame=frame or 0)
    if speichern:
        img.save(os.path.join(KARTE, 'terrain_basis.png'))

    # --- 3. Objekte
    pf = os.path.join(OBJ, 'platzierung.json')
    if os.path.exists(pf):
        cache = {}
        objs = sorted(json.load(open(pf)), key=lambda o: (o.get('ebene', 1), o['y'] + o.get('fuss', 0)))
        # weiche Bodenschatten (Ellipse unter dem Fuss), vor allen Sprites
        from PIL import ImageDraw, ImageFilter
        schatten = Image.new('L', img.size, 0)
        sd = ImageDraw.Draw(schatten)
        for o in objs:
            if 'schatten' in o:
                w, h = o['schatten']
                cx, cy = o['x'] + Image.open(os.path.join(OBJ, o['datei'])).width // 2, o['y'] + o['fuss'] - 2
                sd.ellipse((cx - w // 2, cy - h // 2, cx + w // 2, cy + h // 2), fill=95)
        schatten = schatten.filter(ImageFilter.GaussianBlur(1.2))
        dunkel = Image.new('RGBA', img.size, (18, 52, 48, 255))
        dunkel.putalpha(schatten)
        img.alpha_composite(dunkel)
        for o in objs:
            if o['datei'] not in cache:
                cache[o['datei']] = Image.open(os.path.join(OBJ, o['datei'])).convert('RGBA')
            sp = cache[o['datei']]
            if o.get('spiegeln'):
                sp = sp.transpose(Image.FLIP_LEFT_RIGHT)
            ox, oy = o['x'], o['y']
            if frame is not None and o.get('anim') == 'wehen':
                sp = wehen(sp, wind(frame, o['x']))
            elif frame is not None and o.get('anim') == 'wippen':
                oy += wippen(frame, o['x'] * 7 + o['y'])
            img.alpha_composite(sp, (ox, oy))
        sf = os.path.join(OBJ, 'schmetterlinge.json')
        if os.path.exists(sf):
            schmetterlinge(img, json.load(open(sf)), frame or 0)
    if frame is not None:
        leuchten(img, frame, objs if os.path.exists(pf) else [])
        return img
    if speichern:
        img.save(os.path.join(KARTE, 'terrain.png'))

    json.dump({'tile_size': T, 'cols': cols, 'rows': rows,
               'tilesets': {n: s['id'] for n, s in sets.items() if s},
               'zellen': [[karte[y][x][1] for x in range(cols)] for y in range(rows)],
               'treppen': plan.get('treppen', []),
               'klassen': [''.join(r) for r in cls]},
              open(os.path.join(KARTE, 'tilemap.json'), 'w'))
    for w in warn[:20]:
        print('  ungenau:', w)
    print('Karte %dx%d gebaut, %d ungenaue Kacheln' % (cols, rows, len(warn)))
    return img


def main():
    bauen()


if __name__ == '__main__':
    main()
