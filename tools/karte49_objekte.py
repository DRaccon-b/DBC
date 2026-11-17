"""Objekte fuer Karte 49 - The Broken Promise (A03 Nr. 16), Bossarena von Beelzemon.

  python3 tools/karte49_bauen.py   (einmal -> pixelhoehe.npy, wand.npy)
  python3 tools/karte49_objekte.py && python3 tools/karte49_bauen.py

Vorlage: Felsbrocken auf den Pflasterflecken, zwei tote Baeume (mit Begleitern, Regel 5), sparsam Zweige/Kiesel.
Beelzemon-Anspielungen (Nutzer: Gimmicks, PixelLab k49_deko/k49_spur, ohne Originalsymbole): Motorradspuren
(Burnout-Kreis, Boegen, Profilspur - flach, halbtransparent, zuerst gezeichnet), das abgestellte schwarze Motorrad auf der
Buehne, gespiegelt Feuerschalen mit violetten Flammen und schwarze Banner mit drei Krallenhieben, zerrissene Ketten
("gebrochenes Versprechen"), Brandflecken, Patronenhuelsen, Krallen-Steinplatte, Reifenstapel und Oelfass.
"""
import json, math, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte49')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte49')
T = 16
A = os.path.join(ROOT, 'assets', 'objekte')
D = {'motorrad': 'karte49/deko/00.png', 'schale': 'karte49/deko/01v.png', 'kette': 'karte49/deko/02.png',
     'brand': 'karte49/deko/03r.png', 'huelsen': 'karte49/deko/04.png', 'banner': 'karte49/deko/05.png',
     'kralle': 'karte49/deko/06.png', 'schutt': 'karte49/deko/07.png', 'fass': 'karte49/deko/08.png',
     'reifen': 'karte49/deko/10.png', 'knochen': 'karte49/deko/11.png', 'sperre': 'karte49/deko/12.png',
     'burnout': 'karte49/spur/01a.png', 'spirale': 'karte49/spur/07a.png', 'bogen': 'karte49/spur/00a.png',
     'bogen2': 'karte49/spur/05a.png', 'profil': 'karte49/spur/02a.png', 'schlange': 'karte49/spur/03a.png',
     'totbaum': 'karte04/baeume/02.png', 'brocken': 'karte47/deko/03.png', 'rf1': 'karte01/deko/08.png',
     'rf2': 'karte01/deko/09.png', 'rf3': 'karte01/deko/10.png', 'rf4': 'karte01/deko/11.png',
     'zweig': 'karte04/klein/09.png', 'kiesel': 'karte04/klein/02.png'}
SPUR = {'burnout', 'spirale', 'bogen', 'bogen2', 'profil', 'schlange'}
FLACH = {'kette', 'brand', 'huelsen', 'kralle', 'knochen', 'zweig', 'kiesel'}


def main():
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cls = lay['klassen']
    cols, rows = lay['groesse']
    lvl = np.load(os.path.join(KARTE, 'pixelhoehe.npy'))
    wand = np.unpackbits(np.load(os.path.join(KARTE, 'wand.npy')))[:lvl.size].reshape(lvl.shape).astype(bool)
    os.makedirs(os.path.join(OBJ, 'varianten'), exist_ok=True)
    sperr = [(t['x'] * T - 2 * T, t['y'] * T - 2 * T, (t['x'] + t['b'] + 2) * T, (t['y'] + t['h'] + 2) * T)
             for t in lay['teleporter']]
    for (x0, x1, ry) in lay['treppen']:                              # Treppe und Austritt (2 Reihen) frei
        sperr.append((x0 * T - 2, (ry - 2) * T, (x1 + 1) * T + 2, (ry + 3) * T))
    objekte, rects = [], []
    rnd = random.Random(49)

    def schnitt(a, b, d):
        return not (a[2] + d < b[0] or b[2] + d < a[0] or a[3] + d < b[1] or b[3] + d < a[1])

    def setze(name, cx, fy, opt=None, spiegeln=False, ebene_lvl=1, gap=2, pruefen=True):
        opt = dict(opt or {})
        sp = Image.open(os.path.join(A, D[name])).convert('RGBA')
        if spiegeln:
            sp = sp.transpose(Image.FLIP_LEFT_RIGHT)
        if name.startswith('rf'):                                    # bemooste Felsen (Karte 01) auf die kuehle Felspalette
            ar = np.array(sp).astype(float)
            l_ = ar[..., :3].mean(-1, keepdims=True) / 255.0
            ar[..., :3] = np.array((34, 38, 50)) + (np.array((170, 182, 198)) - np.array((34, 38, 50))) * l_ ** 0.9
            sp = Image.fromarray(np.clip(ar, 0, 255).astype(np.uint8))
        datei = 'varianten/%s%s.png' % (name, '_m' if spiegeln else '')
        sp.save(os.path.join(OBJ, datei))
        bb = sp.getbbox()
        if not (opt.get('liegend') or opt.get('ebene') == 0 or name in SPUR):
            fy = int(fy) // T * T + T - 1                            # Regel 1b: Fuss buendig auf der Kachelunterkante
        x = int(round(cx - (bb[0] + bb[2]) / 2.0))
        y = int(fy - (bb[3] - 1))
        r = (x + bb[0], y + bb[1], x + bb[2] - 1, y + bb[3] - 1)
        if r[0] < 2 or r[1] < 2 or r[2] >= cols * T - 2 or r[3] >= rows * T - 2:
            return None
        spur = name in SPUR
        if pruefen:
            if any(schnitt(r, tuple(rr[:4]), gap) for rr in rects):
                return None
            if any(schnitt(r, s_, 0) for s_ in sperr):
                return None
            y_ab = r[1] if (opt.get('liegend') or spur) else max(r[1], r[3] - 2 * T + 1)
            if (lvl[y_ab:r[3] + 4, max(0, r[0] - 3):r[2] + 4] != ebene_lvl).any():
                return None
            if wand[max(0, r[1]):r[3] + 1, r[0]:r[2] + 1].any():
                return None
        o = {'datei': datei, 'basis': name, 'x': x, 'y': y, 'fuss': bb[3] - 1, 'kachel': [int(cx) // T, int(fy) // T],
             'ebene': 1}
        if spur:                                                     # Reifenspuren: Bodendetail, zuerst gezeichnet
            o.update({'ebene': 0, 'schattenlos': True, 'ohne_wall': True, 'liegend': True, 'sortier': -1000 + len(objekte)})
        o.update(opt)
        objekte.append(o)
        rects.append(list(r) + [spur])
        return o

    def suche(name, cx, fy, opt=None, spiegeln=False, ebene_lvl=1, r=3, schritt=T):
        for d in range(r + 1):
            for dy in range(-d, d + 1):
                for dx in range(-d, d + 1):
                    if max(abs(dx), abs(dy)) == d:
                        o = setze(name, cx + dx * schritt, fy + dy * schritt, opt, spiegeln, ebene_lvl)
                        if o:
                            return o
        print('  nicht gesetzt:', name, int(cx) // T, int(fy) // T)
        return None

    # ---------------- Buehne des Bosses (Plateau): alles gespiegelt zur Treppenachse
    (tx0, tx1, ry) = lay['treppen'][0]
    achse = (tx0 * T + (tx1 + 1) * T) / 2.0
    p0, py0, p1, py1 = lay['plateau']
    setze('motorrad', achse, (py0 + 1) * T + 13, {}, False, 2, pruefen=False)       # abgestellt mitten auf der Buehne
    for s_ in (-1, 1):
        setze('schale', achse + s_ * 72, (py1 - 1) * T + 12, {'fest_pos': True}, s_ > 0, 2, pruefen=False)
        setze('banner', achse + s_ * 150, (py1 - 1) * T + 12, {'fest_pos': True, 'anim': 'standarte'}, s_ > 0, 2,
              pruefen=False)
    suche('reifen', 600, 110, {}, False, 1, r=3, schritt=8)          # Werkstattecke oben rechts am Rand
    suche('fass', 555, 110, {}, False, 1, r=3, schritt=8)
    # ---------------- Motorradspuren (Nutzer): Burnout in der Arenamitte, Boegen und Profilspur Richtung Buehne
    for (n, px, py, sp_) in [('burnout', 360, 270, False), ('bogen', 250, 150, False), ('schlange', 470, 360, True)]:   # Nutzer: cleaner
        suche(n, px, py, {}, sp_, 1, r=3, schritt=8)
    # ---------------- Vorlage: Felsbrocken auf den Pflasterflecken, tote Baeume mit Begleitern
    for (px, py) in [(190, 125), (655, 280), (590, 360), (255, 472)]:
        o = suche('brocken', px, py, {}, px > 400, 1, r=2, schritt=8)
        if o:                                                        # Einbettung: Kiesel an einer Sockelecke
            bx0, bx1 = o['x'], o['x'] + 43
            fy_ = o['y'] + o['fuss'] + 3
            for (cx_, sp_) in ((bx1 + 2, False), (bx0 + 2, True)):   # direkt an der Sockelecke (ueberlappt den Fels gewollt)
                r_ = (int(cx_) - 11, fy_ - 18, int(cx_) + 11, fy_)
                if (lvl[r_[1]:r_[3] + 3, r_[0]:r_[2] + 1] == 1).all() and not any(
                        schnitt(r_, tuple(rr[:4]), 2) for rr in rects[:-1]):
                    setze('kiesel', cx_, fy_, {'ebene': 0, 'liegend': True, 'einbettung': True, 'schattenlos': True},
                          sp_, 1, pruefen=False)
                    break
            else:
                print('  Fels ohne Einbettung', o['x'], o['y'])
    for i, (px, py) in enumerate([(176, 236), (656, 364)]):
        o = suche('totbaum', px, py, {}, i == 1, 1, r=2, schritt=8)
        if not o:
            continue
        sx = o['x'] + 31; sy = o['y'] + o['fuss']
        if i == 0:                                                   # 5d abwechseln: Baum 1 Fels vor dem Stumpf + links tiefer
            ok = any(setze('rf2', sx + d, sy + T - 2, {'begleiter': True}, False, 1, gap=-30) for d in (14, -14, 20, -20))
            any(setze('rf3', sx - d, sy + T + 10, {'begleiter': True}, False, 1) for d in (40, 48, 56))
        else:                                                        # Baum 2: seitlich, rechts tiefer und links hoeher
            ok = any(setze('rf4', sx + d, sy + dy, {'begleiter': True}, True, 1) for dy in (T + 8, 2 * T) for d in (40, 48, 32, 56))
            ok = ok or any(setze('rf4', sx + d, sy + dy, {'begleiter': True}, True, 1)
                           for dy in (-T, -2 * T, T) for d in (48, 40, 56, -48, -56, -64))
            any(setze('rf1', sx - d, sy - T + 2, {'begleiter': True}, False, 1) for d in (36, 44, 52))
        if not ok:
            print('  Baum ohne Begleiter vor dem Stumpf', i)
    # ---------------- Gebrochenes Versprechen: zerrissene Ketten, Brandflecken, Kampfspuren (dezent, keine Reihen)
    for (n, px, py) in [('kette', 300, 330), ('brand', 200, 380), ('huelsen', 480, 230), ('kralle', 130, 300)]:   # Nutzer: cleaner
        suche(n, px, py, {'liegend': n in FLACH, 'ebene': 0 if n in FLACH else 1}, rnd.random() < 0.5, 1, r=3, schritt=8)
    # ---------------- sparsame Streudeko wie in der Vorlage (Zweige, Kiesel)
    kand = [(x, y) for y in range(4, rows - 3) for x in range(3, cols - 3) if cls[y][x] in 'gw']
    rnd.shuffle(kand)
    n_s = 0
    for (x, y) in kand:
        if n_s >= 3:
            break
        if any(abs(o['kachel'][0] - x) < 5 and abs(o['kachel'][1] - y) < 4 for o in objekte if o.get('streu')):
            continue
        n_ = 'zweig' if n_s % 2 else 'kiesel'
        if setze(n_, x * T + rnd.randint(4, 12), y * T + rnd.randint(10, 15),
                 {'ebene': 0, 'streu': True, 'liegend': True}, rnd.random() < 0.5, 1, gap=6):
            n_s += 1
    for o in objekte:                                                # Fels auf Fels: kein Bodenwall; Felsen nur Kontaktschatten
        o.setdefault('ohne_wall', True)
        if o['basis'] == 'brand':                                    # nur das Bodenmal ohne Schatten; liegende Teile: flacher Schatten
            o['schattenlos'] = True
        if o['basis'] in ('brocken', 'rf1', 'rf2', 'rf3', 'rf4', 'schutt', 'sperre', 'totbaum'):
            o['nur_kontakt'] = True
    json.dump(objekte, open(os.path.join(OBJ, 'platzierung.json'), 'w'), indent=0)
    print('Karte 49: %d Objekte (Streudeko %d)' % (len(objekte), n_s))


if __name__ == '__main__':
    main()
    import regeln_a02
    regeln_a02.objekte_pruefen('karte49', 't')
