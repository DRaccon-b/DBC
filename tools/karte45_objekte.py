# Grundgeruest aus karte44 (tools/neue_karte.py) - an die Vorlage von karte45 "Orochimon's Marsh" anpassen!
"""Objekte fuer Karte 45 - Orochimon's Marsh (A03 Nr. 12), Platzierung nach der Vorlage (verbessert).

  python3 tools/karte45_bauen.py   (einmal -> pixelhoehe.npy, wand.npy, wasser.npy)
  python3 tools/karte45_objekte.py && python3 tools/karte45_bauen.py

Baeume der Vorlage (Eichen, runde Laubbaeume, Zypressen, Karte 01) mit Begleitern (Regel 5/5d), Waldbloecke gefuellt,
Weinfaesser zwischen den Baeumen (Nutzer, k44_fass), treibende Faesser im Wasser (PixelLab k45_treib, 1 px Auf-und-ab
mit Wasserring), Seerosen, Rohrkolben und Wasserfelsen am Ufer (Karte 01), sparsame Streudeko.
"""
import json, math, os, random, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte45')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte45')
T = 16
FREMD = {'gras': 'karte04/klein/00.png', 'gras2': 'karte04/klein/01.png',
         'pilz': 'karte04/klein/11.png', 'kiesel': 'karte04/klein/02.png', 'zweig': 'karte04/klein/09.png',
         'blume': 'karte04/klein/07.png', 'gras3': 'karte04/klein/27.png',
         'fass_a': 'karte45/fass_klein/01s.png', 'fass_b': 'karte45/fass_klein/02.png',
         'fass_c': 'karte45/fass_klein/00s.png', 'fass_d': 'karte45/fass_klein/04s.png'}
for _n, _i in (('rose', 17), ('lotus', 18), ('rose2', 19), ('kolben', 7), ('wfels', 22)):
    FREMD[_n] = 'karte01/deko/%02d.png' % _i                          # Wasserpflanzen und Wasserfels
for _i in range(2):
    FREMD['treib%d' % _i] = 'karte45/treib/%02d.png' % (22, 0)[_i]   # halb versunkene Faesser (Kandidat 22, 0)
for _i in (0, 1, 2, 3, 5, 6, 7, 8, 9, 12, 13, 14):
    FREMD['b%02d' % _i] = 'karte01/baeume/%02d.png' % _i
for _i in (2, 3, 14):
    FREMD['fels%02d' % _i] = 'karte27/fels/%02d.png' % _i
KLEINFELS = [0, 3, 4, 15, 24, 26, 27, 31, 52, 55]          # bemooste Felsen, Farn, Buesche, Pilze
for _i in KLEINFELS:
    FREMD['kf%02d' % _i] = 'karte27/fels_klein/%02d.png' % _i
WALD = ['b00', 'b02', 'b06', 'b07', 'b08']                   # ohne Runen-Baeume (b01/b05/b09: Leuchtrunen)
BUSCH = ['b12', 'b13']
# Baeume der Vorlage (Sprite, Kachel-x, Fusszeile): Eichen, runde Baeume, Zypressen; dichte Gruppen aufgelockert
BAEUME = [('b00', 16, 7), ('b03', 14, 9), ('b00', 19, 8), ('b02', 17, 11), ('b03', 13, 13), ('b00', 12, 16),
          ('b00', 30, 11), ('b03', 33, 9), ('b00', 36, 18), ('b07', 15, 11), ('b08', 35, 7), ('b07', 42, 11),
          ('b03', 24, 6), ('b02', 28, 16)]


def main():
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cls = [list(z) for z in lay['klassen']]
    cols, rows = lay['groesse']
    lvl = np.load(os.path.join(KARTE, 'pixelhoehe.npy'))
    wand = np.unpackbits(np.load(os.path.join(KARTE, 'wand.npy')))[:lvl.size].reshape(lvl.shape).astype(bool)
    xmask_ = np.unpackbits(np.load(os.path.join(KARTE, 'wasser.npy')))[:lvl.size].reshape(lvl.shape).astype(bool)
    os.makedirs(os.path.join(OBJ, 'fremd'), exist_ok=True)
    os.makedirs(os.path.join(OBJ, 'varianten'), exist_ok=True)
    for n, q in FREMD.items():
        if not q.startswith('karte45/'):
            shutil.copy(os.path.join(ROOT, 'assets', 'objekte', q), os.path.join(OBJ, 'fremd', n + '.png'))
    pfad = lambda n: os.path.join(ROOT, 'assets', 'objekte', FREMD[n]) if FREMD[n].startswith('karte45/') \
        else os.path.join(OBJ, 'fremd', n + '.png')
    tps = [(t['x'] * T - 2 * T, t['y'] * T - 2 * T, (t['x'] + t['b'] + 2) * T, (t['y'] + t['h'] + 2) * T)
           for t in lay['teleporter']]
    objekte, rects, stumpf = [], [], []
    k = lambda tx, ty: cls[ty][tx] if 0 <= tx < cols and 0 <= ty < rows else 'h'
    rnd = random.Random(44)

    def schnitt(a, b, d):
        return not (a[2] + d < b[0] or b[2] + d < a[0] or a[3] + d < b[1] or b[3] + d < a[1])

    def setze(name, cx, fy, opt=None, spiegeln=False, klassen='g', pruefen=True, ohne=(), art='objekt'):
        opt = dict(opt or {})
        sp = Image.open(pfad(name)).convert('RGBA')
        if spiegeln:
            sp = sp.transpose(Image.FLIP_LEFT_RIGHT)
        datei = 'varianten/%s%s.png' % (name, '_m' if spiegeln else '')
        sp.save(os.path.join(OBJ, datei))
        bb = sp.getbbox()
        x = int(round(cx - (bb[0] + bb[2]) / 2.0))
        y = int(fy - (bb[3] - 1))
        r = (x + bb[0], y + bb[1], x + bb[2] - 1, y + bb[3] - 1)
        if r[0] < 0 or r[1] < 0 or r[2] >= cols * T or r[3] >= rows * T:
            return None
        if art == 'wald':                                          # Waldbaeume: Fuss im Wald, 1 Reihe von der Mauer,
            if any(schnitt((r[0], r[3] - 8, r[2], r[3]), (t['x'] * T, t['y'] * T, (t['x'] + t['b']) * T - 1,
                                                          (t['y'] + t['h']) * T - 1), 1) for t in lay['teleporter']):
                return None                                          # nur der Fuss nie auf dem Teleporter
            cxw = (r[0] + r[2]) // 2
            if (lvl[r[3] - 2:min(r[3] + 3, lvl.shape[0]), cxw - 3:cxw + 4] != 2).any():
                return None                                          # Fuss auf dem Waldboden (nicht auf der Mauer)
            for yy in range(max(0, r[1] // T), r[3] // T + 1):
                for xx in range(r[0] // T, r[2] // T + 1):
                    if k(xx, yy) in 'kT' or (k(xx, yy) == 'w' and yy >= r[3] // T - 1):
                        return None                                  # Krone darf etwas ueber den Weg ragen (Rand natuerlich)
            if any(art2 != 'wald' and schnitt(r, tuple(rr), 3) for (*rr, art2) in rects):
                return None
        elif pruefen:
            gap = 2 if opt.get('streu') else 4
            if any(schnitt(r, tuple(rr), gap) for i_, (*rr, art2) in enumerate(rects) if i_ not in ohne):
                return None
            if any(schnitt(r, z, 0) for j_, z in enumerate(stumpf) if j_ != opt.get('_eigen')):
                return None                                          # Stammzonen (Begleiter nur an ihrem eigenen Baum)
            if any(schnitt(r, t_, 0) for t_ in tps):
                return None
            if any(k(xx // T, yy // T) not in klassen for yy in (r[3] - 6, r[3] + 6) for xx in range(r[0] - 3, r[2] + 4, 4)):
                return None
            y_ab = r[1] if opt.get('liegend') else max(r[1], r[3] - 2 * T + 1)   # untere zwei Reihen (liegend: alles)
            if any(k(xx // T, yy // T) not in klassen for yy in range(y_ab, r[3] + 1, 4) for xx in range(r[0], r[2] + 1, 4)):
                return None                                          # nichts auf Weg/Wasser (ganzes Bildrechteck)                                          # Fuss und Schatten mit Abstand zu Weg/Platz/Wald
            if (lvl[r[3] - 3:r[3] + 9, r[0]:r[2] + 1] != 1).any() or wand[r[3] - 3:r[3] + 2, r[0]:r[2] + 1].any():
                return None
            if xmask_[max(0, r[3] - 2 * T - 2):r[3] + 4, max(0, r[0] - 3):r[2] + 4].any():
                return None                                          # untere zwei Reihen nie auf Ufer/Wasser
            if (lvl[max(0, r[3] - 2 * T + 1):r[3] + 1, max(0, r[0] - 3):r[2] + 4] != 1).any():
                return None                                          # untere zwei Reihen mit 3 px Abstand zu Kanten
            hoch = lvl[max(0, r[1]):r[3] - T, r[0]:r[2] + 1] > 1     # Verdeckung durch Hoehen: Wald seitlich davor
            if hoch.any() and hoch[-T:].any():
                return None
        if opt.pop('_reihe', False) and any(not o_.get('nur_kontakt') and not o_.get('streu') and not o_.get('wasserdeko') and
                                             abs(o_['y'] + o_['fuss'] - (y + bb[3] - 1)) < 12 and abs(o_['x'] - x) < 110
                                             for o_ in objekte):
            objekte_rm = None
            return None                                              # Baeume nie auf derselben Fusszeile nebeneinander
        opt.pop('_eigen', None)
        o = {'datei': datei, 'basis': name, 'x': x, 'y': y, 'fuss': bb[3] - 1, 'kachel': [int(cx) // T, int(fy) // T],
             'ebene': 1}
        o.update(opt)
        objekte.append(o)
        rects.append(list(r) + [art])
        return o

    def kachel(name, tx, ty, opt=None, spiegeln=False, klassen='g', suche=5):
        sp = Image.open(pfad(name))
        bw = sp.getbbox()[2] - sp.getbbox()[0]
        wt = max(1, math.ceil(bw / T))
        for d in range(suche + 1):
            for dy in range(-d, d + 1):
                for dx in range(-d, d + 1):
                    if max(abs(dx), abs(dy)) != d:
                        continue
                    x0 = tx + dx - (wt - 1) // 2
                    o = setze(name, x0 * T + wt * T / 2.0, (ty + dy) * T + T - 1, opt, spiegeln, klassen)
                    if o:
                        return o
        print('  nicht gesetzt:', name, tx, ty)
        return None

    # ---------------- Baeume der Vorlage mit Begleitern
    felsen = ['kf52', 'kf00']                       # hinter den Blaettern: 2 Kacheln hohe Felsen
    klein = ['kf%02d' % i for i in KLEINFELS]
    rnd.shuffle(klein)
    zug = {'k': 0, 'f': 0}

    def naechster(art):                                          # ohne Wiederholung: Motiv weiterdrehen
        zug[art] += 1
        return klein[zug[art] % len(klein)] if art == 'k' else felsen[zug[art] % len(felsen)]
    _setze = setze

    def setze(name, cx, fy, opt=None, *a_, **kw):                # gleiches Motiv nie in der Naehe (10 Kacheln)
        if (opt or {}).get('begleiter') and any(o_['basis'] == name and abs(o_['x'] - cx) < 160 and abs(o_['y'] - fy) < 160
                                               for o_ in objekte):
            return None
        return _setze(name, cx, fy, opt, *a_, **kw)
    gesetzt = []
    for i, (n, tx, ty) in enumerate(BAEUME):
        o = kachel(n, tx, ty, {'anim': 'baum', '_reihe': True}, i % 2 == 1)
        if not o:
            continue
        tsp = np.array(Image.open(os.path.join(OBJ, o['datei'])).convert('RGBA'))[..., 3] > 0
        zl = np.nonzero(tsp.any(1))[0][-1]
        sx = o['x'] + int(np.nonzero(tsp[zl - 3:zl + 1].any(0))[0].mean()); sy = o['y'] + int(zl)
        stumpf.append((sx - 32, sy - 28, sx + 32, sy + 30))
        gesetzt.append((i, n, len(rects) - 1, sx, sy))
    vorne = ['kf00', 'kf24', 'kf26', 'kf31', 'kf52']                # vor dem Stumpf nur 2 Kacheln hohe Begleiter
    zug['v'] = 0
    for j_eig, (i, n, ti, sx, sy) in enumerate(gesetzt):
        seite = 1 if i % 2 == 0 else -1
        vor = lambda: any(setze(vorne[(zug.__setitem__('v', zug['v'] + 1) or zug['v']) % len(vorne)], sx + d, sy + T,
                                {'begleiter': True, '_eigen': j_eig}, seite < 0, 'g', ohne=(ti,))
                          for d in (0, 3, -3, 6, -6))
        hinter = lambda sd: (n != 'totbaum') and any(setze(naechster('f'), sx + sd * d, sy - T, {'begleiter': True, '_eigen': j_eig}, sd < 0,
                                                           'g', ohne=(ti,)) for d in (20, 28, 36))
        seitlich = lambda sd: any(setze(naechster('k'), sx + sd * d, sy + dy, {'begleiter': True, 'ebene': 0}, sd > 0, 'g')
                                  for d in (48, 56, 64, 72) for dy in (2 * T, -2 * T)
                                  if not any(abs(o_['y'] + o_['fuss'] - (sy + dy)) < 10 and abs(o_['x'] - (sx + sd * d)) < 140
                                             for o_ in objekte if o_.get('begleiter')))
        nah = sum(1 for (_, _, _, x2, y2) in gesetzt if (x2, y2) != (sx, sy) and abs(x2 - sx) < 6 * T and abs(y2 - sy) < 5 * T)
        soll = 1 if nah else 2
        plan = [[vor, lambda: seitlich(-seite)], [vor, lambda: hinter(seite)], [lambda: hinter(-seite), lambda: seitlich(seite)]][i % 3]
        if n == 'b03':                                            # kleiner Baum: kein Begleiter vor dem Stumpf (verdeckt sonst
            plan = [lambda: hinter(seite), lambda: seitlich(-seite)]   # Stamm und Krone)
        hat = 0
        for f_ in plan + [lambda: seitlich(seite), lambda: seitlich(-seite)] + ([] if n == 'b03' else [vor]):
            if hat >= soll and f_ not in plan:
                break
            if f_():
                hat += 1
        if hat < soll:                                            # Ersatz: Begleiter weiter weg (Regel 5b)
            for dx_, dy_ in ((-40, T), (40, T), (-56, 0), (56, 0), (0, 2 * T), (-72, T), (72, T)):
                if hat >= soll:
                    break
                if setze(naechster('k'), sx + dx_, sy + dy_, {'begleiter': True, 'ebene': 0}, dx_ > 0, 'g'):
                    hat += 1
        if hat < soll:
            print('  Baum mit zu wenig Begleitern:', n, hat)
    # ---------------- Weinfaesser zwischen den Baeumen (Nutzer: ein, zwei)
    n_fass = 0
    for n_ in ('fass_a', 'fass_b'):                                  # direkt neben einem Baum (nicht frei auf der Wiese)
        ok_ = None
        for (j_g, (i_, nb_, ti_, sx_, sy_)) in sorted(enumerate(gesetzt), key=lambda g_: abs(g_[1][3] - (18 if n_ == 'fass_a' else 30) * T)
                                                              + abs(g_[1][4] - 10 * T)):
            if any(o_['basis'].startswith('fass') and abs(o_['x'] - sx_) < 12 * T for o_ in objekte):
                continue
            for dx_, dy_ in ((36, 6), (-36, 6), (40, 12), (-40, 12), (34, -4), (-34, -4), (44, 0), (-44, 0), (50, 8), (-50, 8), (48, -8), (-48, -8)):
                ok_ = setze(n_, sx_ + dx_, sy_ + dy_, {'begleiter': True, '_eigen': j_g}, dx_ < 0, 'g', ohne=(ti_,))
                if ok_:
                    break
            if ok_:
                break
        if not ok_:                                                  # sonst am Waldrand (vor den Waldbloecken)
            for (tx_, ty_) in ((36, 14), (12, 19), (35, 13), (11, 20)):
                ok_ = kachel(n_, tx_, ty_, {}, False, 'g', suche=1)
                if ok_:
                    break
        n_fass += 1 if ok_ else 0
    # ---------------- Nutzer: noch 1-2 Faesser am Inselrand (nicht in der Mitte), 2-3 Kacheln vom Ufer, weit auseinander
    wasser_t = np.array([[c == 'x' for c in z] for z in cls])
    rand_k = []
    for y in range(2, rows - 2):
        for x in range(2, cols - 2):
            if cls[y][x] != 'g':
                continue
            d_ = min((abs(yy - y) + abs(xx - x)) for yy in range(max(0, y - 4), min(rows, y + 5))
                     for xx in range(max(0, x - 4), min(cols, x + 5)) if wasser_t[yy, xx]) \
                if wasser_t[max(0, y - 4):y + 5, max(0, x - 4):x + 5].any() else 99
            if 2 <= d_ <= 3 and y < 20:                                 # Nord-/Ost-/Westufer (nicht am Steg)
                rand_k.append((x, y))
    rnd.shuffle(rand_k)
    for n_ in ('fass_c', 'fass_d'):
        for (x, y) in rand_k:
            if any(o_['basis'].startswith('fass') and abs(o_['kachel'][0] - x) < 10 and abs(o_['kachel'][1] - y) < 8
                   for o_ in objekte):
                continue
            if setze(n_, x * T + 8, y * T + 13, {'_reihe': True}, rnd.random() < 0.5, 'g'):
                n_fass += 1
                break
    # ---------------- Wasser: Seerosen, Rohrkolben, Wasserfelsen nah am Ufer; treibende Faesser weiter draussen
    xmask = np.unpackbits(np.load(os.path.join(KARTE, 'wasser.npy')))[:lvl.size].reshape(lvl.shape).astype(bool)

    def im_wasser(name, cx, fy, opt, sp=False, rand=6):
        sp_ = Image.open(pfad(name))
        bb_ = sp_.getbbox()
        x_ = int(round(cx - (bb_[0] + bb_[2]) / 2.0)); y_ = int(fy - (bb_[3] - 1))
        r_ = (x_ + bb_[0] - rand, y_ + bb_[1] - rand, x_ + bb_[2] - 1 + rand, y_ + bb_[3] - 1 + rand)
        if r_[0] < 0 or r_[1] < 0 or r_[2] >= cols * T or r_[3] >= rows * T:
            return None
        if not xmask[r_[1]:r_[3] + 1, r_[0]:r_[2] + 1].all():
            return None                                                    # ganz im Wasser (nicht am Steg/Ufer)
        if any(schnitt(r_, tuple(rr), 4) for (*rr, _a) in rects):
            return None
        return setze(name, cx, fy, opt, sp, pruefen=False, art='wasser')
    dist = np.full((rows, cols), 99)
    land = np.array([[c in 'gwh' for c in z] for z in cls])
    for y in range(rows):
        for x in range(cols):
            if not land[y, x]:
                ys_, xs_ = np.nonzero(land[max(0, y - 6):y + 7, max(0, x - 6):x + 7])
                if len(ys_):
                    dist[y, x] = int(np.min(np.maximum(abs(ys_ + max(0, y - 6) - y), abs(xs_ + max(0, x - 6) - x))))
    nah = [(x, y) for y in range(rows) for x in range(cols) if 1 <= dist[y, x] <= 3 and cls[y][x] == 'x']
    rnd.shuffle(nah)
    pflanzen = ['rose', 'kolben', 'lotus', 'rose2', 'kolben', 'wfels', 'rose', 'kolben', 'rose2', 'lotus', 'kolben',
                'rose', 'wfels', 'kolben']
    n_wp = 0
    for (x, y) in nah:
        if n_wp >= len(pflanzen):
            break
        if any(o_.get('wasserdeko') and abs(o_['kachel'][0] - x) < 5 and abs(o_['kachel'][1] - y) < 5 for o_ in objekte):
            continue
        n_ = pflanzen[n_wp]
        if im_wasser(n_, x * T + 8, y * T + 12, dict({'wasserdeko': True, 'ebene': 0, 'schattenlos': True,
                                                      'ohne_wall': True}, **({'anim': 'wehen'} if n_ == 'kolben' else {})),
                     rnd.random() < 0.5, rand=3):
            n_wp += 1
    weit = [(x, y) for y in range(rows) for x in range(cols) if 3 <= dist[y, x] <= 6 and cls[y][x] == 'x']
    rnd.shuffle(weit)
    n_tr = 0
    for (x, y) in weit:
        if n_tr >= 3:
            break
        if any(o_.get('treibend') and (o_['kachel'][0] - x) ** 2 + (o_['kachel'][1] - y) ** 2 < 15 ** 2 for o_ in objekte) or x > 44 or y < 3:
            continue
        if im_wasser('treib%d' % (n_tr % 2), x * T + 8, y * T + 10, {'treibend': True, 'schattenlos': True,
                                                                      'ohne_wall': True, 'phase': n_tr}, n_tr == 2):
            n_tr += 1
    print('  Faesser zwischen Baeumen %d, Wasserpflanzen %d, treibende Faesser %d' % (n_fass, n_wp, n_tr))
    # ---------------- Wald fuellen (Guertel und Bloecke): dichte Laub-/Nadelbaeume, Luecken mit Bueschen
    hk = [(x, y) for y in range(rows) for x in range(cols) if cls[y][x] == 'h']
    rnd.shuffle(hk)
    n_w = 0
    for (x, y) in hk:
        if setze(rnd.choice(WALD), x * T + rnd.randint(2, 14), y * T + T - 5, {'anim': 'baum', 'nur_kontakt': True},
                 rnd.random() < 0.5, art='wald'):
            n_w += 1
            rects[-1][4] = 'wald'
    for (x, y) in hk + [(x, y) for y in range(rows) for x in range(cols) if cls[y][x] == 'h' and y > rows - 4]:   # Luecken: Buesche
        r_ = (x * T, y * T, x * T + T, y * T + T)
        if not any(art2 == 'wald' and schnitt(r_, tuple(rr), -6) for (*rr, art2) in rects):
            if setze(rnd.choice(BUSCH), x * T + 8, y * T + T - 5, {'anim': 'baum', 'nur_kontakt': True}, rnd.random() < 0.5,
                     art='wald'):
                n_w += 1
    # zweiter Durchgang: Waldboden, der noch kahl ist (Guertelraender, Kartenrand), mit Bueschen/Baeumen schliessen
    Hp_, Wp_ = rows * T, cols * T
    deck = np.zeros((Hp_, Wp_), bool)
    for o_ in objekte:
        sp_ = np.array(Image.open(os.path.join(OBJ, o_['datei'])).convert('RGBA'))[..., 3] > 0
        y0_, x0_ = o_['y'], o_['x']
        ys_, xs_ = slice(max(0, y0_), min(Hp_, y0_ + sp_.shape[0])), slice(max(0, x0_), min(Wp_, x0_ + sp_.shape[1]))
        deck[ys_, xs_] |= sp_[ys_.start - y0_:ys_.stop - y0_, xs_.start - x0_:xs_.stop - x0_]
    for (x, y) in sorted(hk, key=lambda p_: (p_[1], p_[0])):
        if deck[y * T:(y + 1) * T, x * T:(x + 1) * T].mean() > 0.75:
            continue
        for n_ in (rnd.choice(WALD), rnd.choice(BUSCH)):        # erst Baeume (Busch-Reihen wirken als Hecke)
            o_ = None
            for cx_, fy_ in ((x * T + 8, y * T + T - 3), (x * T + 2, y * T + T - 3), (x * T + 14, y * T + T - 3),
                             (x * T + 8, y * T + 6), (x * T + 2, y * T + 6), (x * T + 14, y * T + 6)):
                cx_ = min(max(cx_, 17), cols * T - 17)                   # am Kartenrand ganz im Bild
                o_ = setze(n_, cx_, min(fy_, rows * T - 1), {'anim': 'baum', 'nur_kontakt': True},
                           rnd.random() < 0.5, art='wald')
                if o_:
                    break
            if o_:
                n_w += 1
                sp_ = np.array(Image.open(os.path.join(OBJ, o_['datei'])).convert('RGBA'))[..., 3] > 0
                y0_, x0_ = o_['y'], o_['x']
                ys_, xs_ = slice(max(0, y0_), min(Hp_, y0_ + sp_.shape[0])), slice(max(0, x0_), min(Wp_, x0_ + sp_.shape[1]))
                deck[ys_, xs_] |= sp_[ys_.start - y0_:ys_.stop - y0_, xs_.start - x0_:xs_.stop - x0_]
                break
    # ---------------- sparsame Streudeko (begehbar), keine Reihen, keine Wiederholung
    streu = ['gras', 'gras2', 'gras3', 'pilz', 'kiesel', 'zweig', 'blume']
    kand = [(x, y) for y in range(3, rows - 3) for x in range(3, cols - 3) if cls[y][x] == 'g']
    rnd.shuffle(kand)
    n_s, letzte = 0, None
    for (x, y) in kand:
        if n_s >= 45:
            break
        if any(o.get('streu') and abs(o['kachel'][0] - x) < 4 and abs(o['kachel'][1] - y) < 4 for o in objekte):
            continue
        if any(abs(o['kachel'][1] - y) <= 1 and abs(o['kachel'][0] - x) < 15 for o in objekte if not o.get('gebaeude')
               and 'wald' not in o.get('datei', '')):
            continue
        wahl = [s for s in streu if s != letzte and not any(o.get('basis') == s and abs(o['kachel'][0] - x) < 12
                                                            and abs(o['kachel'][1] - y) < 12 for o in objekte)]
        if not wahl:
            continue
        n_ = rnd.choice(wahl)
        if setze(n_, x * T + rnd.randint(4, 12), y * T + rnd.randint(10, 15),
                 {'ebene': 0, 'streu': True, 'liegend': n_ in ('zweig',)}, rnd.random() < 0.5):
            n_s += 1; letzte = n_
    json.dump(objekte, open(os.path.join(OBJ, 'platzierung.json'), 'w'), indent=0)
    lay['klassen'] = [''.join(z) for z in cls]                          # Trampelpfade der Huetten
    json.dump(lay, open(os.path.join(KARTE, 'layout.json'), 'w'), indent=0)
    print('Karte 45: %d Objekte (Wald %d, Streudeko %d)' % (len(objekte), n_w, n_s))


if __name__ == '__main__':
    main()
    import regeln_a02
    regeln_a02.objekte_pruefen('karte45', 'w')
