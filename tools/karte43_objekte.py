"""Objekte fuer Karte 43 - Haunted Castle Outskirts (A03 Nr. 10), Platzierung nach der Vorlage (verbessert).

  python3 tools/karte43_bauen.py   (einmal -> pixelhoehe.npy, wand.npy)
  python3 tools/karte43_objekte.py && python3 tools/karte43_bauen.py

Neu: Burg (PixelLab Pro, > 256 px, Kandidat A nach der Vorlage), Torbau mit Dach (k43_tor), Wasserspeier, Feuerschalen,
Baenke (k43_deko). Wiederverwendet: Laub- und Nadelbaeume, Buesche (Karte 01), toter Baum, Gras, Pilze (Karte 04),
bemooste Felsen (Karte 27). Reihenfolge: Wald fuellen, Burg/Torbau, Platzpaare symmetrisch zur Burgachse, Baeume der
Vorlage mit Begleitern (Regel 5/5d, Reihen der Vorlage aufgeloest), sparsame Streudeko.
"""
import json, math, os, random, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte43')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte43')
T = 16
FREMD = {'burg': 'karte43/burg_a/00.png', 'tor': 'karte43/tor/00.png', 'speier': 'karte43/deko/00.png',
         'schale': 'karte43/deko/01.png', 'bank': 'karte43/deko/03.png',
         'totbaum': 'karte04/baeume/02.png', 'gras': 'karte04/klein/00.png', 'gras2': 'karte04/klein/01.png',
         'pilz': 'karte04/klein/11.png', 'kiesel': 'karte04/klein/02.png', 'zweig': 'karte04/klein/09.png',
         'blume': 'karte04/klein/07.png', 'gras3': 'karte04/klein/27.png'}
for _i in (0, 1, 2, 3, 5, 6, 9, 12, 13, 14):
    FREMD['b%02d' % _i] = 'karte01/baeume/%02d.png' % _i
for _i in (2, 3, 14):
    FREMD['fels%02d' % _i] = 'karte27/fels/%02d.png' % _i
KLEINFELS = [0, 3, 4, 15, 24, 26, 27, 31, 52, 55]          # bemooste Felsen, Farn, Buesche, Pilze
for _i in KLEINFELS:
    FREMD['kf%02d' % _i] = 'karte27/fels_klein/%02d.png' % _i
WALD = ['b00', 'b01', 'b02', 'b05', 'b06', 'b09']
BUSCH = ['b12', 'b13']                                        # ohne Kastenhecke b14 (wirkt als Reihe)
# Baeume der Vorlage (Sprite, Kachel-x, Fusszeile); Reihen der Vorlage (oben 4, unten 4) auf versetzte Einzelbaeume reduziert
BAEUME = [('b00', 42, 7), ('b02', 55, 10), ('b01', 10, 18), ('b03', 20, 17), ('b05', 18, 21), ('b02', 23, 26),
          ('b00', 30, 19), ('b01', 49, 18), ('b03', 55, 21), ('b02', 55, 29), ('b05', 63, 33), ('b01', 40, 42),
          ('b00', 35, 49), ('b03', 25, 58), ('b02', 31, 61), ('b05', 6, 54), ('b01', 5, 61), ('b03', 42, 55),
          ('b02', 52, 64), ('b00', 40, 71), ('b01', 25, 74), ('b05', 49, 74), ('b03', 63, 66), ('b00', 75, 70), ('b01', 64, 45), ('b03', 70, 44), ('b05', 63, 51), ('b00', 69, 53), ('b02', 82, 57),
          ('b01', 88, 44),
          ('b00', 58, 15), ('b01', 17, 35), ('b05', 48, 59), ('b00', 76, 61),                       # grosse Laubbaeume
          ('totbaum', 42, 36), ('totbaum', 28, 56), ('totbaum', 55, 66)]


def main():
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cls = lay['klassen']
    cols, rows = lay['groesse']
    lvl = np.load(os.path.join(KARTE, 'pixelhoehe.npy'))
    wand = np.unpackbits(np.load(os.path.join(KARTE, 'wand.npy')))[:lvl.size].reshape(lvl.shape).astype(bool)
    os.makedirs(os.path.join(OBJ, 'fremd'), exist_ok=True)
    os.makedirs(os.path.join(OBJ, 'varianten'), exist_ok=True)
    for n, q in FREMD.items():
        if not q.startswith('karte43/'):
            shutil.copy(os.path.join(ROOT, 'assets', 'objekte', q), os.path.join(OBJ, 'fremd', n + '.png'))
    pfad = lambda n: os.path.join(ROOT, 'assets', 'objekte', FREMD[n]) if FREMD[n].startswith('karte43/') \
        else os.path.join(OBJ, 'fremd', n + '.png')
    tps = [(t['x'] * T - 2 * T, t['y'] * T - 2 * T, (t['x'] + t['b'] + 2) * T, (t['y'] + t['h'] + 2) * T)
           for t in lay['teleporter']]
    objekte, rects, stumpf = [], [], []
    k = lambda tx, ty: cls[ty][tx] if 0 <= tx < cols and 0 <= ty < rows else 'h'
    rnd = random.Random(43)

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
            if (lvl[r[3] - 2:min(r[3] + 3, lvl.shape[0]), r[0] + 6:r[2] - 5] != 2).any():
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
            if not opt.get('begleiter') and any(schnitt(r, z, 0) for z in stumpf):
                return None
            if any(schnitt(r, t_, 0) for t_ in tps):
                return None
            if any(k(xx // T, yy // T) not in klassen for yy in (r[3] - 6, r[3] + 6) for xx in range(r[0] - 3, r[2] + 4, 4)):
                return None                                          # Fuss und Schatten mit Abstand zu Weg/Platz/Wald
            if (lvl[r[3] - 3:r[3] + 9, r[0]:r[2] + 1] != 1).any() or wand[r[3] - 3:r[3] + 2, r[0]:r[2] + 1].any():
                return None
            hoch = lvl[max(0, r[1]):r[3] - T, r[0]:r[2] + 1] > 1     # Verdeckung durch Hoehen: Wald seitlich davor
            if hoch.any() and hoch[-T:].any():
                return None
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

    # ---------------- Burg auf dem Vorplatz, Torbau am Waldblock
    bx0, by0, bx1, by1 = lay['burg']
    ax = (bx0 + bx1 + 1) * T / 2.0                                    # Burgachse
    setze('burg', ax, (by1 + 1) * T - 1, {'gebaeude': True, 'nur_kontakt': True}, False, 'k', pruefen=False)   # kein Balkenschatten
    tx0, ty0, tx1, ty1 = lay['tor']
    setze('tor', 37.5 * T, (ty1 + 1) * T - 1, {'nur_kontakt': True}, False, 'g', pruefen=False)   # offener Bogen: nur Sockel sperrt
    # Platzpaare exakt gespiegelt zur Burgachse (gemeinsame Fusszeile)
    for (n, dxs, reihen, opt) in (('schale', (104, 96, 112, 88), (33, 34, 32), {'anim': 'feuer_kamin', 'flammen_box': [[5, 4, 23, 24]]}),
                                  ('speier', (152, 144, 136, 160, 128, 120), (36, 35, 37, 34, 38), {}),
                                  ('bank', (64, 72, 80, 56, 88, 96), (39, 38, 40, 37, 36), {})):
        ok = False
        for dx in dxs:
            for ry in reihen:
                n0 = len(objekte)
                o_ = {k_: v_ for k_, v_ in opt.items() if v_ is not None}
                ok = setze(n, ax - dx, ry * T + T - 1, o_, False, 'k') and setze(n, ax + dx, ry * T + T - 1, o_, True, 'k')
                if ok:
                    break
                del objekte[n0:]; del rects[n0:]
            if ok:
                break
        if not ok:
            print('  Paar nicht gesetzt:', n)
    # Uebergang Torbau -> Waldmauer: Busch links und rechts (Regel), gewollt dicht am Torbau (ohne Abstandspruefung)
    for sd in (-1, 1):
        for d in (88, 92, 96, 100, 104, 108, 112):
            if setze('b13' if sd < 0 else 'b12', 37.5 * T + sd * d, (ty1 + 1) * T - 1, {'anim': 'baum'}, sd > 0, 'g',
                     ohne=(1,), pruefen=True) or setze('b13' if sd < 0 else 'b12', 37.5 * T + sd * d, (ty1 + 1) * T - 1,
                                                       {'anim': 'baum'}, sd > 0, 'g', ohne=(1,), pruefen=False) \
                    if (lambda xx: all(cls[yy][xx] == 'g' for yy in (ty1 - 1, ty1)))(int(37.5 + sd * d / T)) else False:
                break
        else:
            print('  Uebergangsbusch fehlt', sd)
    # ---------------- Baeume der Vorlage mit Begleitern
    felsen = ['fels02', 'fels03', 'fels14']
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
        o = kachel(n, tx, ty, {'anim': 'baum'} if n != 'totbaum' else {}, i % 2 == 1)
        if not o:
            continue
        tsp = np.array(Image.open(os.path.join(OBJ, o['datei'])).convert('RGBA'))[..., 3] > 0
        zl = np.nonzero(tsp.any(1))[0][-1]
        sx = o['x'] + int(np.nonzero(tsp[zl - 3:zl + 1].any(0))[0].mean()); sy = o['y'] + int(zl)
        stumpf.append((sx - 32, sy - 28, sx + 32, sy + 30))
        gesetzt.append((i, n, len(rects) - 1, sx, sy))
    for (i, n, ti, sx, sy) in gesetzt:
        seite = 1 if i % 2 == 0 else -1
        vor = lambda: any(setze(naechster('k'), sx + d, sy + T, {'begleiter': True}, seite < 0, 'g', ohne=(ti,))
                          for d in (0, 3, -3, 6, -6))
        hinter = lambda sd: (n != 'totbaum') and any(setze(naechster('f'), sx + sd * d, sy - T, {'begleiter': True}, sd < 0,
                                                           'g', ohne=(ti,)) for d in (24, 32))
        seitlich = lambda sd: any(setze(naechster('k'), sx + sd * d, sy + dy, {'begleiter': True, 'ebene': 0}, sd > 0, 'g')
                                  for d in (48, 56, 64, 72) for dy in (-T, 2 * T, -2 * T)
                                  if not any(abs(o_['y'] + o_['fuss'] - (sy + dy)) < 10 and abs(o_['x'] - (sx + sd * d)) < 140
                                             for o_ in objekte if o_.get('begleiter')))
        nah = sum(1 for (_, _, _, x2, y2) in gesetzt if (x2, y2) != (sx, sy) and abs(x2 - sx) < 6 * T and abs(y2 - sy) < 5 * T)
        soll = 1 if nah else 2
        plan = [[vor, lambda: seitlich(-seite)], [vor, lambda: hinter(seite)], [lambda: hinter(-seite), lambda: seitlich(seite)]][i % 3]
        hat = 0
        for f_ in plan + [lambda: seitlich(seite), lambda: seitlich(-seite), vor]:
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
    print('Karte 43: %d Objekte (Wald %d, Streudeko %d)' % (len(objekte), n_w, n_s))


if __name__ == '__main__':
    main()
    import regeln_a02
    regeln_a02.objekte_pruefen('karte43', 'w')
