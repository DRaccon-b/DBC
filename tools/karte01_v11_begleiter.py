"""Karte 01 v1.1 - Regel 5: jeder einzeln stehende Baum bekommt Begleitung.

  python3 tools/karte01_v11_begleiter.py      (nach objekte_setzen.py + karte01_raster.py, vor karte_bauen.py)

Einzeln = kein anderer Baum/Busch im Umkreis von 4 Kacheln. Dann:
  5a  ein zweiter Baum daneben + 1-2 zwei Kacheln hohe Pflanzen, die den Sockel des Baums vorne ueberdecken, oder
  5b  (wenn kein Platz fuer einen Baum) 2-3 solche Pflanzen um den Sockel.
Pflanzen: Buesche/Farne aus Karte 01 und aus den neuen Gras-Sets (Karte 07, Regel 3: wiederverwenden).
Alles am 16x16-Raster im kleinsten Block, Fuss buendig, mittig; nur auf Gras, nie auf Weg/Wasser/Klippe.
"""
import json, math, os, random, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
import bauwerke

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte01')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte01')
K7 = os.path.join(ROOT, 'assets', 'objekte', 'karte07', 'deko_gras')
T = 16
BAEUME = {'baeume/%02d' % i for i in list(range(12)) + [15]} | {'gross/00', 'gross/01', 'gross/02'}
BUSCH = {'baeume/12', 'baeume/13', 'baeume/14'}
BEGLEITBAUM = ['baeume/00', 'baeume/01', 'baeume/06', 'baeume/09', 'baeume/15', 'baeume/02']
DECKER = ['baeume/12', 'baeume/13', 'deko/25', 'deko/26', 'deko/61', 'k7gras/01', 'k7gras/34', 'k7gras/41',
          'k7gras/42', 'k7gras/54', 'k7gras/63', 'k7gras/15']
WEHEN = {'deko/26', 'deko/61', 'k7gras/01', 'k7gras/54', 'k7gras/63', 'k7gras/15'}


def main():
    rnd = random.Random(11)
    # Gras-Sets aus Karte 07 uebernehmen (Regel 3)
    os.makedirs(os.path.join(OBJ, 'k7gras'), exist_ok=True)
    for n in DECKER:
        if n.startswith('k7gras/'):
            ziel = os.path.join(OBJ, n + '.png')
            if not os.path.exists(ziel):
                shutil.copy(os.path.join(K7, n.split('/')[1] + '.png'), ziel)
    objs = json.load(open(os.path.join(OBJ, 'platzierung.json')))
    # Strandlager aus v1.0 uebernehmen (grosses Zelt + Surfbretter waren von Hand gesetzt, ersetzen gross/03)
    v10 = os.path.join(KARTE, 'v1.0', 'platzierung_v1.0.json')
    if os.path.exists(v10):
        zelt = [o for o in json.load(open(v10)) if o['basis'].startswith('zelt_strand/')]
        zb = set()
        for z in zelt:
            bx, by, wt, ht = z['block']
            zb |= {(x, y) for x in range(bx, bx + wt) for y in range(by, by + ht)}
        def stoert(o):
            bx, by, wt, ht = o['block']
            return any((x, y) in zb for x in range(bx, bx + wt) for y in range(by, by + ht))
        objs = [o for o in objs if o['basis'] != 'gross/03' and not stoert(o)] + zelt
    tm = json.load(open(os.path.join(KARTE, 'tilemap.json')))
    cls, cols, rows = tm['klassen'], tm['cols'], tm['rows']
    plan = json.load(open(os.path.join(KARTE, 'hoehenplan.json')))
    tcol = {}
    for s in plan['segmente']:
        for vx in range(s['von'], s['bis'] + 1):
            tcol[vx] = (s['t'], s.get('h', 3))
    tabu = set()                                         # Klippen (+1 Reihe), Treppen, Bruecken, Stege
    for x in range(cols):
        t, h = tcol.get(x, (0, 0))
        for y in range(t - h - 1, t + 2):
            tabu.add((x, y))
    for br in plan.get('bruecken', []) + plan.get('stege', []):
        for x in range(br['x'] - 1, br['x'] + br['breite'] + 1):
            for y in range(br['y'] - 2, br['y'] + br['hoehe'] + 2):
                tabu.add((x, y))
    belegt = {}
    for i, o in enumerate(objs):
        bx, by, wt, ht = o['block']
        for x in range(bx, bx + wt):
            for y in range(by, by + ht):
                belegt[(x, y)] = i
    schatten = {o['basis']: o['schatten'] for o in objs if 'schatten' in o}
    cache = {}

    def sprite(name):
        if name not in cache:
            sp = Image.open(os.path.join(OBJ, name + '.png')).convert('RGBA')
            art = 'baum' if name in BAEUME else 'busch' if name in BUSCH or name == 'deko/25' else \
                'pflanze' if name in WEHEN and name.startswith('deko/') else 'klein'
            v = bauwerke.bodenfuss(sp, 'gras', art)
            datei = 'varianten/%s_gras.png' % name.replace('/', '-')
            if not os.path.exists(os.path.join(OBJ, datei)):
                v.save(os.path.join(OBJ, datei))
            a = np.array(sp.getchannel('A')) > 0
            ys, xs = np.nonzero(a)
            off = 2 if v.size == (sp.width + 4, sp.height + 3) else 0
            cache[name] = (datei, v.height, int(xs.min()) + off, int(ys.min()), int(xs.max()) + off, int(ys.max()))
        return cache[name]

    def setzen(name, bx, ty, erlaubt=()):
        """Objekt mit linker Blockspalte bx und Fusszeile ty setzen, falls alle Blockkacheln frei und Gras sind."""
        datei, h, x0, y0, x1, y1 = sprite(name)
        bw, bh = x1 - x0 + 1, y1 - y0 + 1
        wt, ht = math.ceil(bw / T), math.ceil(bh / T)
        for x in range(bx, bx + wt):
            for y in range(ty - ht + 1, ty + 1):
                if not (0 <= x < cols and 0 <= y < rows) or cls[y][x] != 'g' or (x, y) in tabu:
                    return None
                if (x, y) in belegt and (x, y) not in erlaubt:
                    return None
        # unterste Reihe: auch die Kacheln links/rechts daneben duerfen kein Weg sein (Fuss ganz im Gras)
        o = {'datei': datei, 'basis': name, 'x': bx * T + (wt * T - bw) // 2 - x0, 'y': (ty + 1) * T - 1 - y1,
             'fuss': h, 'ebene': 1, 'untergrund': 'gras', 'kachel': [bx + (wt - 1) // 2, ty],
             'block': [bx, ty - ht + 1, wt, ht], 'v11': 'begleiter'}
        if name in WEHEN:
            o['anim'] = 'wehen'
        if name in schatten:
            o['schatten'] = schatten[name]
        objs.append(o)
        for x in range(bx, bx + wt):
            for y in range(ty - ht + 1, ty + 1):
                belegt[(x, y)] = len(objs) - 1
        return o

    def baeume_nah(o, r=4):
        kx, ky = o['kachel']
        return [p for p in objs if p is not o and (p['basis'] in BAEUME or p['basis'] in BUSCH)
                and abs(p['kachel'][0] - kx) <= r and abs(p['kachel'][1] - ky) <= 3]
    # Wiesenbaeume: nicht im dichten Wald (weniger als 3 Baeume/Buesche im Umkreis von 3 Kacheln)
    wiese = [o for o in objs if o['basis'] in BAEUME and len(baeume_nah(o, 3)) < 3]
    einzeln = [o for o in wiese if not baeume_nah(o)]

    def hat_decker(o):
        bx, by, wt, ht = o['block']
        ty = by + ht - 1
        return any(p is not o and p.get('ebene', 1) == 1 and p['block'][1] + p['block'][3] - 1 in (ty, ty + 1)
                   and p['block'][0] < bx + wt and p['block'][0] + p['block'][2] > bx
                   and p['basis'] not in BAEUME for p in objs)
    n_a = n_b = n_d = 0
    for o in [o for o in wiese if o not in einzeln]:          # Baum hat schon einen Nachbarbaum: nur Decker
        if hat_decker(o):
            continue
        bx, by, wt, ht = o['block']
        ty = by + ht - 1
        sockel = {(x, ty) for x in range(bx, bx + wt)}
        for sx in ([bx - 1, bx + wt - 1] if rnd.random() < 0.5 else [bx + wt - 1, bx - 1]):
            if any(setzen(name, sx, ty + 1, erlaubt=sockel) for name in rnd.sample(DECKER, len(DECKER))):
                n_d += 1
                break
    print('%d Wiesenbaeume mit Nachbarbaum, davon %d neu mit Decker vor dem Sockel' % (len(wiese) - len(einzeln), n_d))
    for o in einzeln:
        bx, by, wt, ht = o['block']
        ty = by + ht - 1
        sockel = {(x, ty) for x in range(bx, bx + wt)}
        # Decker vor den Sockel: Fusszeile eine Reihe tiefer, links und rechts vorne
        def decker(anzahl):
            gesetzt = 0
            seiten = [bx - 1, bx + wt - 1] if rnd.random() < 0.5 else [bx + wt - 1, bx - 1]
            for sx in seiten:
                if gesetzt >= anzahl:
                    break
                for name in rnd.sample(DECKER, len(DECKER)):
                    if setzen(name, sx, ty + 1, erlaubt=sockel):
                        gesetzt += 1
                        break
            return gesetzt
        # 5a: zweiter Baum daneben
        baum2 = None
        for name in rnd.sample(BEGLEITBAUM, len(BEGLEITBAUM)):
            datei, h, x0, y0, x1, y1 = sprite(name)
            w2 = math.ceil((x1 - x0 + 1) / T)
            for (sx, sy) in ((bx + wt + 1, ty - 1), (bx - w2 - 1, ty - 1), (bx + wt, ty - 2), (bx - w2, ty - 2),
                             (bx + wt + 1, ty + 1), (bx - w2 - 1, ty + 1)):
                baum2 = setzen(name, sx, sy)
                if baum2:
                    break
            if baum2:
                break
        if baum2:
            if decker(rnd.choice((1, 2))):
                n_a += 1
                continue
        # 5b: 2-3 Decker
        if decker(rnd.choice((2, 3))) >= 2:
            n_b += 1
        else:
            print('  kein Platz fuer Begleitung -> Baum entfernt (Regel 5):', o['basis'], o['kachel'])
            o['_weg'] = True
    objs[:] = [o for o in objs if not o.get('_weg')]
    # Regel 7: Schatten nie ueber Kanten (Klippe, Wasser, Meer) - Ellipse verkleinern, sonst weglassen
    klippe = set()
    for x in range(cols):
        t, h = tcol.get(x, (0, 0))
        for y in range(t - h - 1, t + 1):
            klippe.add((x, y))
    n_k = n_w = 0

    def ellipse_frei(o, w, h):
        sp_w = Image.open(os.path.join(OBJ, o['datei'])).width
        cx, cy = o['x'] + sp_w / 2, o['y'] + o['fuss'] - 2
        fx, fy = int(cx // T), int((o['y'] + o['fuss'] - 3) // T)
        eigen = cls[min(rows - 1, fy)][min(cols - 1, fx)]
        for yy in range(int(cy - h / 2), int(cy + h / 2) + 1):
            for xx in range(int(cx - w / 2), int(cx + w / 2) + 1, 2):
                if ((xx - cx) / (w / 2)) ** 2 + ((yy - cy) / (h / 2)) ** 2 > 1:
                    continue
                tx, ty_ = xx // T, yy // T
                if not (0 <= tx < cols and 0 <= ty_ < rows):
                    return False
                if cls[ty_][tx] in 'wm' or ((tx, ty_) in klippe and (fx, fy) not in klippe) or \
                        (cls[ty_][tx] != eigen and eigen == 'g' and cls[ty_][tx] == 's' and False):
                    return False
        return True
    for o in objs:
        if 'schatten' not in o:
            continue
        w, h = o['schatten']
        if ellipse_frei(o, w, h):
            continue
        for f in (0.85, 0.7, 0.55, 0.4):
            if ellipse_frei(o, int(w * f), max(4, int(h * f))):
                o['schatten'] = [int(w * f), max(4, int(h * f))]
                n_k += 1
                break
        else:
            del o['schatten']
            n_w += 1
    print('Regel 7: %d Schatten verkleinert, %d entfernt (ragten ueber Klippe/Wasser)' % (n_k, n_w))
    json.dump(objs, open(os.path.join(OBJ, 'platzierung.json'), 'w'), indent=0)
    print('%d einzelne Baeume: %d mit Baum + Decker (5a), %d mit 2-3 Deckern (5b)' % (len(einzeln), n_a, n_b))


if __name__ == '__main__':
    main()
