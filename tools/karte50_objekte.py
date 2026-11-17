# Grundgeruest aus karte47 (tools/neue_karte.py) - an die Vorlage von karte50 "Zhuqiaomon's Sanctuary" anpassen!
# Grundgeruest aus karte46 (tools/neue_karte.py) - an die Vorlage von karte50 "Deva Mountain" anpassen!
# Grundgeruest aus karte45 (tools/neue_karte.py) - an die Vorlage von karte50 "Gekomon Marsh" anpassen!
# Grundgeruest aus karte44 (tools/neue_karte.py) - an die Vorlage von karte50 "Orochimon's Marsh" anpassen!
"""Objekte fuer Karte 50 - Deva Mountain (A03 Nr. 14), Platzierung nach der Vorlage (verbessert).

  python3 tools/karte50_bauen.py   (einmal -> pixelhoehe.npy, wand.npy)
  python3 tools/karte50_objekte.py && python3 tools/karte50_bauen.py

Neu (PixelLab k50_deko): rote Deva-Banner mit Sonnenemblem (Tuch weht, Stange fest), Steinsaeulen und abgebrochene
Saeulen (Ruinen-Logik: gemischt), graublaue Felsbrocken. Wiederverwendet: Baeume (Karte 01) auf den Grasflecken mit
Begleitern, Felsen der Karte 01 auf dem Felsrand, Streudeko (Karte 04) sparsam auf dem Felsboden.
"""
import json, math, os, random, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte50')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte50')
T = 16
FREMD = {'gras': 'karte04/klein/00.png', 'gras2': 'karte04/klein/01.png',
         'kiesel': 'karte04/klein/02.png', 'zweig': 'karte04/klein/09.png', 'gras3': 'karte04/klein/27.png',
         'banner': 'karte50/deko/00.png', 'saeule': 'karte50/deko/01.png', 'stumpf_s': 'karte50/deko/02.png',
         'brocken': 'karte50/deko/03.png'}
for _n, _i in (('rf1', 8), ('rf2', 9), ('rf3', 10), ('rf4', 11)):
    FREMD[_n] = 'karte01/deko/%02d.png' % _i                          # Felsen auf dem Felsrand
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
S_ = 0.8                                                     # Vorlage 1,25-fach: px / 20 = Kachel
BAEUME = [('b00', 30, 6), ('b03', 32, 7), ('b02', 54, 16), ('b03', 56, 15), ('b00', 20, 27), ('b03', 23, 28),
          ('b02', 24, 47), ('b03', 27, 48), ('b00', 31, 48), ('b03', 34, 49), ('b07', 15, 56), ('b03', 79, 27)]
BANNER = [(1250, 835), (1330, 915)]                      # Nutzer: nur 1-2 Flaggen (am Eingang der Arena)
SAEULEN = [(835, 140), (790, 405), (880, 405), (210, 590), (365, 580), (1130, 795), (460, 1090), (1180, 1045),
           (1270, 1045), (900, 1200), (1305, 1140), (1900, 765), (1900, 1250), (1505, 1390)]


def main():
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cls = [list(z) for z in lay['klassen']]
    cols, rows = lay['groesse']
    lvl = np.load(os.path.join(KARTE, 'pixelhoehe.npy'))
    wand = np.unpackbits(np.load(os.path.join(KARTE, 'wand.npy')))[:lvl.size].reshape(lvl.shape).astype(bool)
    xmask_ = np.unpackbits(np.load(os.path.join(KARTE, 'wasser.npy')))[:lvl.size].reshape(lvl.shape).astype(bool)
    os.makedirs(os.path.join(OBJ, 'fremd'), exist_ok=True)
    os.makedirs(os.path.join(OBJ, 'varianten'), exist_ok=True)
    _alt_copy = shutil.copy

    def _copy_umfaerben(q_, z_):                                     # rote Kontur (Karte 27) -> kuehles Blaugrau
        _alt_copy(q_, z_)
        if 'fels_klein' in q_:
            a_ = np.array(Image.open(z_).convert('RGBA')).astype(int)
            m_ = (a_[..., 3] > 0) & (a_[..., 0] > a_[..., 1] + 20) & (a_[..., :3].mean(-1) < 80)
            a_[m_, :3] = (34, 38, 50)
            Image.fromarray(a_.astype(np.uint8)).save(z_)
    shutil.copy = _copy_umfaerben
    for n, q in FREMD.items():
        if not q.startswith('karte50/'):
            shutil.copy(os.path.join(ROOT, 'assets', 'objekte', q), os.path.join(OBJ, 'fremd', n + '.png'))
    pfad = lambda n: os.path.join(ROOT, 'assets', 'objekte', FREMD[n]) if FREMD[n].startswith('karte50/') \
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
            if (lvl[r[3] - 2:min(r[3] + 3, lvl.shape[0]), cxw - 9:cxw + 10] != 2).any():
                return None                                          # Fuss auf dem Waldboden (nicht auf der Mauer)
            for yy in range(max(0, r[1] // T), r[3] // T + 1):
                for xx in range(r[0] // T, r[2] // T + 1):
                    if k(xx, yy) in 'kT' or (k(xx, yy) == 'w' and yy >= r[3] // T - 1):
                        return None                                  # Krone darf etwas ueber den Weg ragen (Rand natuerlich)
            if any(art2 != 'wald' and schnitt(r, tuple(rr), 3) for (*rr, art2) in rects):
                return None
        elif pruefen:
            gap = 10 if opt.get('streu') else 4                       # Streudeko nie an grossen Objekten
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
                                             abs(o_['y'] + o_['fuss'] - (y + bb[3] - 1)) < 12 and abs(o_['x'] - x) < 220
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

    # ---------------- Deva-Banner (Tuch weht, Stange fest) und Saeulen - an den Plaetzen der Vorlage
    bx0_, by0_, bx1_, by1_ = lay['bruecken'][1]                     # Flaggenpaar am Eingang: Westende der Hauptbruecke,
    ok_ = False                                                        # gespiegelt zur Brueckenachse
    for xb_ in [bx1_ + d_ for d_ in range(3, 7)] + [bx0_ - d_ for d_ in range(3, 8)]:   # zuerst auf der Arenaseite
        for (ya_, yb_) in ((by0_ - 1, by1_ + 2), (by0_ - 2, by1_ + 3), (by0_, by1_ + 1)):
            n0_ = len(objekte)
            ok_ = setze('banner', xb_ * T + 8, ya_ * T - 1, {'anim': 'standarte'}, False, 'gkd')   # Nutzer: nur eine Flagge
            if ok_:
                break
            del objekte[n0_:]; del rects[n0_:]
        if ok_:
            break
    if not ok_:
        print('  Flaggenpaar nicht gesetzt')
    paare = {}
    for i_, (px_, py_) in enumerate(SAEULEN):
        paare.setdefault(py_, []).append((i_, px_))
    for py_, liste in paare.items():                                 # Paare der Vorlage (gleiche Hoehe) gemeinsam setzen
        if len(liste) == 2:
            ok_ = False
            for dy_ in (0, -1, 1, -2, 2, -3, 3):
                for dx_ in (0, -1, 1, -2, 2):
                    n0_ = len(objekte)
                    ok_ = all(setze('saeule', (int(px_ / 20) + dx_ * (1 if j_ == 0 else -1)) * T + 8,
                                    (int(py_ / 20) + dy_) * T + T - 1, {}, j_ == 1, 'gkd') for j_, (i_, px_) in enumerate(liste))
                    if ok_:
                        break
                    del objekte[n0_:]; del rects[n0_:]
                if ok_:
                    break
            if not ok_:
                print('  Saeulenpaar nicht gesetzt', py_)
        else:
            for (i_, px_) in liste:                                   # Ruinen-Logik: einzelne Saeulen teils abgebrochen
                kachel('saeule' if i_ % 3 else 'stumpf_s', int(px_ / 20), int(py_ / 20), {}, i_ % 2 == 1, 'gkd', suche=4)
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
        o = kachel(n, tx, ty, {'anim': 'baum', '_reihe': True}, i % 2 == 1, 'ng')
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
        if n in ('b03', 'b07', 'b08'):                                            # kleiner Baum: kein Begleiter vor dem Stumpf (verdeckt sonst
            plan = [lambda: hinter(seite), lambda: seitlich(-seite)]   # Stamm und Krone)
        hat = 0
        for f_ in plan + [lambda: seitlich(seite), lambda: seitlich(-seite)] + ([] if n in ('b03', 'b07', 'b08') else [vor]):
            if hat >= soll and f_ not in plan:
                break
            if f_():
                hat += 1
        if hat < soll:                                            # Ersatz: Begleiter weiter weg (Regel 5b)
            for dx_, dy_ in ((-40, T), (40, T), (-56, T), (56, T), (0, 2 * T), (-72, T), (72, T)):
                if hat >= soll:
                    break
                if setze(naechster('k'), sx + dx_, sy + dy_, {'begleiter': True, 'ebene': 0}, dx_ > 0, 'g'):
                    hat += 1
        if hat < soll:
            print('  Baum mit zu wenig Begleitern:', n, hat)
    n_fass = 0
    # ---------------- Felsrand: Felsbrocken locker verteilt (nicht begehbar, nur Optik), ohne Reihen
    n_w = 0
    hk = [(x, y) for y in range(2, rows - 2) for x in range(2, cols - 2)
          if all(cls[yy][xx] == 'h' for yy in range(y - 2, y + 2) for xx in range(x - 2, x + 3))]
    rnd.shuffle(hk)
    rf = ['rf2', 'rf4', 'brocken', 'rf1', 'rf3']
    for (x, y) in hk:
        if n_w >= 60:
            break
        if any(o_.get('randfels') and abs(o_['kachel'][0] - x) < 5 and abs(o_['kachel'][1] - y) < 4 for o_ in objekte):
            continue
        if any(o_.get('randfels') and o_['kachel'][1] == y and abs(o_['kachel'][0] - x) < 12 for o_ in objekte):
            continue                                                  # keine Reihen (gleiche Fusszeile)
        wahl_ = [r_ for r_ in rf if not any(o_.get('basis') == r_ and abs(o_['kachel'][0] - x) < 10
                                              and abs(o_['kachel'][1] - y) < 10 for o_ in objekte)]
        if not wahl_:
            continue
        n_ = wahl_[n_w % len(wahl_)]
        if setze(n_, x * T + rnd.randint(2, 14), y * T + T - 1, {'randfels': True, 'nur_kontakt': True}, rnd.random() < 0.5,
                 'h', pruefen=False, art='rand'):
            n_w += 1
    # ---------------- sparsame Streudeko (begehbar), keine Reihen, keine Wiederholung
    streu = ['gras', 'gras2', 'gras3', 'pilz', 'kiesel', 'zweig', 'blume']
    streu = ['gras', 'gras2', 'gras3', 'kiesel', 'zweig']
    kand = [(x, y) for y in range(3, rows - 3) for x in range(3, cols - 3) if cls[y][x] in 'gk']
    rnd.shuffle(kand)
    n_s, letzte = 0, None
    for (x, y) in kand:
        if n_s >= 70:
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
    print('Karte 50: %d Objekte (Wald %d, Streudeko %d)' % (len(objekte), n_w, n_s))


if __name__ == '__main__':
    main()
    import regeln_a02
    regeln_a02.objekte_pruefen('karte50', 'w')
