"""Karte 01 v1.1 - Regel 8: Baeume ueberlappen sich nur an den aeusseren Kachelspalten.

  python3 tools/karte01_v11_baeume.py      (nach karte01_raster.py, vor karte01_v11_begleiter.py)

- Baum ab 3 Kacheln Breite: darf einen Nachbarbaum nur mit seiner aeussersten Spalte links/rechts ueberlappen.
- Baum 1-2 Kacheln breit: ueberlappt gar nicht (steht daneben).
- Sockelregel: die unterste Kachelreihe zweier Baeume ueberlappt nie.
Vorgehen: Baeume nach Wichtigkeit behalten (Sonderbaeume, dann grosse zuerst), regelwidrige entfernen, danach den
Wald regelkonform wieder auffuellen (gleiche Baumarten wie vorher, am Raster, nur auf Wald-/Wiesenboden).
"""
import json, math, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
import bauwerke

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte01')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte01')
T = 16
WALD = ['baeume/00', 'baeume/01', 'baeume/02', 'baeume/06', 'baeume/07', 'baeume/09', 'baeume/15', 'baeume/03',
        'baeume/04', 'baeume/05', 'baeume/08']


def ist_baum(o):
    b = o['basis']
    return b.startswith(('baeume/', 'dschungel/')) or b in ('gross/00', 'gross/01', 'gross/02', 'gross/10')


def kacheln(block):
    bx, by, wt, ht = block
    return {(x, y) for x in range(bx, bx + wt) for y in range(by, by + ht)}


def erlaubt(a, b, wald=False):
    """Duerfen sich die Bloecke a und b (Baeume) so ueberlappen?
    Wiese: nur die aeusserste Spalte. Dichter Wald: bis zu zwei aeussere Spalten je Seite; mindestens eine Spalte
    jedes Baums bleibt frei; Baeume bis 2 Kacheln Breite nie; die Sockelreihe nie."""
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    sx = set(range(ax, ax + aw)) & set(range(bx, bx + bw))
    sy = set(range(ay, ay + ah)) & set(range(by, by + bh))
    if not sx or not sy:
        return True
    if aw < 3 or bw < 3:
        return False
    rand = 2 if wald else 1
    if len(sx) > rand or len(sx) >= min(aw, bw):
        return False
    aussen_a = set(range(ax, ax + rand)) | set(range(ax + aw - rand, ax + aw))
    aussen_b = set(range(bx, bx + bw)) and (set(range(bx, bx + rand)) | set(range(bx + bw - rand, bx + bw)))
    if not (sx <= aussen_a and sx <= aussen_b):
        return False
    if ay + ah == by + bh:
        return False                                                    # Sockel zweier Baeume nie auf einer Kachel
    return True


def main():
    pf = os.path.join(OBJ, 'platzierung.json')
    objs = json.load(open(pf))
    tm = json.load(open(os.path.join(KARTE, 'tilemap.json')))
    cls, cols, rows = tm['klassen'], tm['cols'], tm['rows']
    grid = json.load(open(os.path.join(KARTE, 'terrain_grid.json')))['grid']
    plan = json.load(open(os.path.join(KARTE, 'hoehenplan.json')))
    baeume = [o for o in objs if ist_baum(o)]
    # Deko mitten im Wald (Fuss auf F) blockiert das dichte Packen -> zuerst die Baeume, Deko danach in die Luecken
    def im_wald(o):
        x, y = o['kachel']
        return 0 <= y < len(grid) and 0 <= x < len(grid[0]) and grid[y][x] == 'F'
    wald_deko = [o for o in objs if not ist_baum(o) and im_wald(o) and o['basis'].startswith(('deko/', 'k7gras/'))]
    rest = [o for o in objs if not ist_baum(o) and o not in wald_deko]
    vorher = len(baeume)
    wichtig = lambda o: (0 if not o['basis'].startswith('baeume/') else 1, -o['block'][2] * o['block'][3])
    behalten = []
    def ist_wald(o):
        x, y = o['kachel']
        return 0 <= y < len(grid) and 0 <= x < len(grid[0]) and (grid[y][x] == 'F' or (x, y) in wald_zellen)
    wald_zellen = set()
    for o in baeume:
        if len([p for p in baeume if abs(p['kachel'][0] - o['kachel'][0]) <= 3 and
                abs(p['kachel'][1] - o['kachel'][1]) <= 3]) >= 6:
            wald_zellen.add(tuple(o['kachel']))
    for o in sorted(baeume, key=wichtig):
        if all(erlaubt(o['block'], p['block'], ist_wald(o) and ist_wald(p)) for p in behalten):
            behalten.append(o)
    entfernt = vorher - len(behalten)
    # Auffuellen: freie Stellen im Wald (Gelaende F) mit regelkonformen Baeumen
    tcol = {}
    for s in plan['segmente']:
        for vx in range(s['von'], s['bis'] + 1):
            tcol[vx] = (s['t'], s.get('h', 3))
    tabu = set()
    for x in range(cols):
        t, h = tcol.get(x, (0, 0))
        for y in range(t - h - 1, t + 2):
            tabu.add((x, y))
    for tr in plan['treppen']:
        t, h = tcol[tr['x']]
        tabu |= {(x, y) for x in range(tr['x'] - 1, tr['x'] + tr['breite'] + 1) for y in range(t - h - 4, t + 5)}
    for br in plan.get('bruecken', []) + plan.get('stege', []):
        tabu |= {(x, y) for x in range(br['x'] - 1, br['x'] + br['breite'] + 1)
                 for y in range(br['y'] - 2, br['y'] + br['hoehe'] + 3)}
    rest_kacheln = set()
    for o in rest:
        if o.get('ebene', 1) == 1:
            rest_kacheln |= kacheln(o['block'])
    schatten = {o['basis']: o['schatten'] for o in objs if 'schatten' in o}
    cache = {}

    def sprite(name):
        if name not in cache:
            sp = Image.open(os.path.join(OBJ, name + '.png')).convert('RGBA')
            datei = 'varianten/%s_gras.png' % name.replace('/', '-')
            if not os.path.exists(os.path.join(OBJ, datei)):
                bauwerke.bodenfuss(sp, 'gras', 'baum').save(os.path.join(OBJ, datei))
            v = Image.open(os.path.join(OBJ, datei))
            a = np.array(sp.getchannel('A')) > 0
            ys, xs = np.nonzero(a)
            off = 2 if v.size == (sp.width + 4, sp.height + 3) else 0
            cache[name] = (datei, v.height, int(xs.min()) + off, int(ys.min()), int(xs.max()) + off, int(ys.max()))
        return cache[name]
    rnd = random.Random(5)
    gewichte = {}
    for o in baeume:
        if o['basis'] in WALD:
            gewichte[o['basis']] = gewichte.get(o['basis'], 0) + 1
    namen = list(gewichte)
    gw = [gewichte[n] for n in namen]
    neu = 0
    # Packbereich: Wald (F) und alle Stellen, an denen in der Vorlage ein Baumsockel stand
    vorher_wald = set()
    for o in baeume:
        bx, by, wt, ht = o['block']
        for xx in range(bx - 1, bx + wt + 1):
            for yy in range(by + ht - 2, by + ht + 1):
                vorher_wald.add((xx, yy))
    # systematisch dicht packen: Fusszeile von oben nach unten, je Stelle alle Baumarten probieren
    for y in range(rows):
        for x in range(cols):
            if grid[y][x] != 'F' and (x, y) not in vorher_wald:
                continue
            for name in rnd.sample(namen, len(namen)):
                datei, h, x0, y0, x1, y1 = sprite(name)
                bw, bh = x1 - x0 + 1, y1 - y0 + 1
                wt, ht = math.ceil(bw / T), math.ceil(bh / T)
                bx = x - wt // 2
                block = [bx, y - ht + 1, wt, ht]
                k = kacheln(block)
                sockel = {(xx, y) for xx in range(bx, bx + wt)}
                if any(not (0 <= xx < cols and 0 <= yy < rows) for (xx, yy) in k):
                    continue
                if any(cls[yy][xx] != 'g' or (xx, yy) in tabu or grid[yy][xx] not in 'FG' for (xx, yy) in sockel):
                    continue
                if k & rest_kacheln:
                    continue
                wald_hier = grid[y][x] == 'F' or (x, y) in vorher_wald
                if not all(erlaubt(block, p['block'], wald_hier and ist_wald(p)) for p in behalten):
                    continue
                o = {'datei': datei, 'basis': name, 'x': bx * T + (wt * T - bw) // 2 - x0,
                     'y': (y + 1) * T - 1 - y1, 'fuss': h, 'ebene': 1, 'untergrund': 'gras',
                     'kachel': [bx + (wt - 1) // 2, y], 'block': block}
                if name in schatten:
                    o['schatten'] = schatten[name]
                behalten.append(o)
                neu += 1
                break
    # Wald-Deko zurueck, wo sie keinen Baumsockel und kein anderes Objekt trifft
    belegt = set(rest_kacheln)
    for b in behalten:
        bx, by, wt, ht = b['block']
        belegt |= {(xx, by + ht - 1) for xx in range(bx, bx + wt)}
    deko_zurueck = []
    for o in wald_deko:
        k = kacheln(o['block'])
        if not (k & belegt):
            deko_zurueck.append(o)
            belegt |= k
    rest += deko_zurueck
    print('Wald-Deko: %d von %d wieder eingesetzt' % (len(deko_zurueck), len(wald_deko)))
    json.dump(rest + behalten, open(pf, 'w'), indent=0)
    print('Regel 8: %d Baeume vorher, %d regelwidrige entfernt, %d regelkonform neu gesetzt, %d Baeume jetzt'
          % (vorher, entfernt, neu, len(behalten)))


if __name__ == '__main__':
    main()
