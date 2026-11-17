"""Objekte fuer Karte 50 - Zhuqiaomon's Sanctuary (A03 Nr. 17).

  python3 tools/karte50_bauen.py   (einmal -> pixelhoehe.npy, wand.npy)
  python3 tools/karte50_objekte.py && python3 tools/karte50_bauen.py

Neu mit PixelLab (k50_torii, k50_deko, k50_klein): rote Torii, Steinlaternen, Steinpfosten, Strohunterstand, Opferkasten,
Feuerschalen (orangerote Flammen - Feuervogel), Wasserbecken, kleiner Schrein, Phoenixfedern, rote Spinnenlilien.
Weniger Kleinkram als in der Vorlage (Nutzer bei Karte 49: lieber cleaner): Pfosten und Feuerschalen nur als Paare an den
Treppenachsen und wenige Randpaare (fester Rhythmus, gespiegelt); Torii auf der Achse ihrer Treppe; abgesenkter Hof mit
Funktion (Schrein an der Nordwand, Laternenpaar, Opferkasten, Wasserbecken); Baeume der Vorlage mit Begleitern (Regel 5).
"""
import json, math, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte51')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte51')
T = 16
A = os.path.join(ROOT, 'assets', 'objekte')
D = {'torii': 'karte50/torii_gross/00b.png',   # Nutzer: Pfeiler stehen am Treppenfuss, man geht darunter durch
     'torii_klein': 'karte50/torii/00.png', 'becken': 'karte50/torii/02.png', 'laterne': 'karte50/deko/00.png',
     'pfosten': 'karte50/deko/01.png', 'unterstand': 'karte50/deko/02.png', 'opfer': 'karte50/deko/03.png',
     'schale': 'karte50/deko/04.png', 'schrein': 'karte50/deko/09.png', 'feder': 'karte50/klein/00.png',
     'feder2': 'karte50/klein/01.png', 'lilie': 'karte50/klein/02.png', 'kiesel': 'karte50/klein/03.png',
     'baum': 'karte01/baeume/00.png', 'zypresse': 'karte01/baeume/07.png', 'brocken': 'karte47/deko/03.png',
     'kf00': 'karte27/fels_klein/00.png', 'kf24': 'karte27/fels_klein/24.png', 'kf52': 'karte27/fels_klein/52.png',
     'gras': 'karte04/klein/00.png', 'gras2': 'karte04/klein/01.png', 'zweig': 'karte04/klein/09.png'}
D.update({'baum_b': 'karte50/brand/00.png', 'busch_b': 'karte50/brand/01.png', 'brocken_b': 'karte50/brand/02.png',
          'stamm_b': 'karte50/brand/03.png', 'asche_b': 'karte50/brand_klein/01.png', 'glut_b': 'karte50/brand_klein/11.png',
          'rauch_b': 'karte50/brand_klein/29.png'})
VERBRANNT = {'baum': 'baum_b', 'zypresse': 'baum_b', 'kf00': 'busch_b', 'kf24': 'busch_b', 'kf52': 'busch_b',
             'brocken': 'brocken_b', 'lilie': None, 'gras': None, 'gras2': None}
FLACH = {'feder', 'feder2', 'kiesel', 'zweig'}


def main():
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cls = lay['klassen']
    cols, rows = lay['groesse']
    lvl = np.load(os.path.join(KARTE, 'pixelhoehe.npy'))
    wand = np.unpackbits(np.load(os.path.join(KARTE, 'wand.npy')))[:lvl.size].reshape(lvl.shape).astype(bool)
    os.makedirs(os.path.join(OBJ, 'varianten'), exist_ok=True)
    sperr = [(t['x'] * T - 2 * T, t['y'] * T - 2 * T, (t['x'] + t['b'] + 2) * T, (t['y'] + t['h'] + 2) * T)
             for t in lay['teleporter']]
    for (x0, x1, ry, r_) in lay['treppen']:                          # Treppen und Austritt (2 Reihen) frei
        y0_, y1_ = ((ry - 2) * T, (ry + 3) * T) if r_ == 's' else ((ry - 2) * T, (ry + 5) * T)
        sperr.append((x0 * T - 2, y0_, (x1 + 1) * T + 2, y1_))
    objekte, rects = [], []
    rnd = random.Random(50)

    def schnitt(a, b, d):
        return not (a[2] + d < b[0] or b[2] + d < a[0] or a[3] + d < b[1] or b[3] + d < a[1])

    brand_k = [[c == '1' for c in z] for z in lay.get('brand', ['0' * cols] * rows)]

    def _dbg(k_, name, cx, fy):
        if os.environ.get('K51_DEBUG') and name in os.environ.get('K51_DEBUG'):
            print('    abgelehnt', name, int(cx), int(fy), 'Grund', k_)
        return None

    def setze(name, cx, fy, opt=None, spiegeln=False, gap=2, pruefen=True, klassen='gwknd'):
        opt = dict(opt or {})
        if 0 <= int(fy) // T < rows and 0 <= int(cx) // T < cols and brand_k[int(fy) // T][int(cx) // T] and name in VERBRANNT:
            name = VERBRANNT[name]                                   # Nutzer: im Brandbereich verkohlte Varianten
            if name is None:
                return _dbg(1, name, cx, fy)
            if name == 'baum_b':
                opt['anim'] = 'kerzen'                               # Glut in der Rinde glimmt
        sp = Image.open(os.path.join(A, D[name])).convert('RGBA')
        if spiegeln:
            sp = sp.transpose(Image.FLIP_LEFT_RIGHT)
        if name.startswith('kf'):                                    # rote Kontur (Karte 27) -> kuehles Blaugrau
            ar = np.array(sp).astype(int)
            rot = (ar[..., 3] > 0) & (ar[..., 0] > ar[..., 2] + 40) & (ar[..., 1] < 90)
            ar[rot, :3] = (34, 38, 50)
            sp = Image.fromarray(ar.astype(np.uint8))
        datei = 'varianten/%s%s.png' % (name, '_m' if spiegeln else '')
        sp.save(os.path.join(OBJ, datei))
        bb = sp.getbbox()
        if not (opt.get('liegend') or opt.get('ebene') == 0):
            fy = int(fy) // T * T + T - 1                            # Regel 1b: Fuss auf der Kachelunterkante
        x = int(round(cx - (bb[0] + bb[2]) / 2.0))
        y = int(fy - (bb[3] - 1))
        r = (x + bb[0], y + bb[1], x + bb[2] - 1, y + bb[3] - 1)
        if r[0] < 2 or r[1] < 2 or r[2] >= cols * T - 2 or r[3] >= rows * T - 2:
            return _dbg(2, name, cx, fy)
        if pruefen:
            if any(schnitt(r, tuple(rr[:4]), gap) for rr in rects):
                return _dbg(3, name, cx, fy)
            if any(schnitt(r, s_, 0) for s_ in sperr):
                return _dbg(4, name, cx, fy)
            y_ab = r[1] if opt.get('liegend') else max(r[1], r[3] - 2 * T + 1)
            reg = lvl[y_ab:r[3] + 4, max(0, r[0] - 3):r[2] + 4]
            if len(np.unique(reg)) != 1 or reg[0, 0] == 9 or reg[0, 0] >= 5:
                return _dbg(5, name, cx, fy)                                          # untere zwei Reihen ganz auf einer Ebene, nicht am Rand
            if wand[max(0, r[1]):r[3] + 1, r[0]:r[2] + 1].any():
                return _dbg(6, name, cx, fy)
            if any(cls[yy // T][xx // T] not in klassen for yy in range(y_ab, r[3] + 1, 4) for xx in range(r[0], r[2] + 1, 4)):
                return _dbg(7, name, cx, fy)
            hoch = lvl[max(0, r[1]):r[3] - T, r[0]:r[2] + 1]          # Verdeckung: nicht vor eine hoehere Terrasse daneben
            if ((hoch > lvl[r[3], (r[0] + r[2]) // 2]) & (hoch != 9)).any() and not opt.get('vor_wand'):
                return _dbg(8, name, cx, fy)
        o = {'datei': datei, 'basis': name, 'x': x, 'y': y, 'fuss': bb[3] - 1, 'kachel': [int(cx) // T, int(fy) // T],
             'ebene': 1, 'ohne_wall': name not in ('baum', 'zypresse', 'kf00', 'kf24', 'kf52', 'lilie', 'gras', 'gras2')}
        o.update(opt)
        objekte.append(o)
        rects.append(list(r))
        return o

    def suche(name, cx, fy, opt=None, spiegeln=False, r=3, klassen='gwknd'):
        for d in range(r + 1):
            for dy in range(-d, d + 1):
                for dx in range(-d, d + 1):
                    if max(abs(dx), abs(dy)) == d:
                        o = setze(name, cx + dx * T, fy + dy * T, opt, spiegeln, klassen=klassen)
                        if o:
                            return o
        print('  nicht gesetzt:', name, int(cx) // T, int(fy) // T)
        return None

    def paar(name, achse, abstand, fy, opt=None):
        """Gespiegeltes Paar auf gemeinsamer Fusszeile; bei Konflikt die Fusszeile gemeinsam verschieben."""
        for dab in sorted(range(-120, 121, 8), key=abs):         # Saeulen/Schalen nie auf Pflaster (Karte 47)
            for dfy in (0, -T, T, -2 * T, 2 * T, -3 * T, 3 * T):
                a_ = setze(name, achse - abstand - dab, fy + dfy, opt, False, klassen='gd')
                if not a_:
                    continue
                b_ = setze(name, achse + abstand + dab, fy + dfy, opt, True, klassen='gd')
                if b_:
                    return True
                objekte.pop(); rects.pop()
        print('  Paar nicht gesetzt:', name, int(achse) // T, int(fy) // T)
        return False

    # ---------------- Suzaku Gate: grosses Torii ueber der Treppe (wie Karte 50), Paare symmetrisch zur Arena
    (tx0, tx1, ry, r_) = lay['treppen'][0]
    t_achse = (tx0 * T + (tx1 + 1) * T) / 2.0
    setze('torii', t_achse, (ry + 2) * T + T - 1, {'fest_pos': True, 'vor_wand': True, 'nur_kontakt': True,
                                                    'sortier': (ry + 2) * T + T - 1}, pruefen=False)
    ax0, ay0, ax1, ay1 = lay['arena']
    achse = (ax0 + ax1 + 1) * T / 2.0
    fl = {'vor_wand': True, 'anim': 'kerzen', 'flammen_box': [[4, 0, 24, 20]], 'flammen_alle': True, 'flammen_amp': 1.4}
    la = {'vor_wand': True, 'anim': 'lampe', 'lampe_box': [8, 18, 20, 30], 'licht_farbe': [255, 200, 120]}
    paar('laterne', achse, 232, 11 * T + 12, la)                      # Boden links/rechts des Platzes (nicht auf Pflaster)
    paar('schale', achse, 280, 21 * T + 12, fl)
    paar('pfosten', achse, 272, 19 * T + 12)
    paar('schale', t_achse, 112, 31 * T + 12, fl)                    # Boden vor der Treppe, neben dem Torii
    # Vorlage: Fels und Zypresse, Wiesen mit Bueschel (verbrannte Stellen: verkohlte Varianten)
    for (n, px, py) in [('brocken', 145, 215), ('lilie', 263, 488), ('gras2', 272, 456), ('baum', 650, 285), ('brocken', 520, 470),
                        ('stamm_b', 560, 490), ('glut_b', 400, 236), ('asche_b', 110, 420), ('feder', 300, 120), ('feder2', 640, 400),
                        ('lilie', 140, 200), ('lilie', 660, 270)]:
        o_ = suche(n, px, py, {'liegend': n in FLACH or n in ('stamm_b', 'glut_b', 'asche_b'),
                          'ebene': 0 if n in FLACH or n in ('glut_b', 'asche_b', 'lilie') else 1,
                          **({'anim': 'kerzen'} if n in ('stamm_b', 'glut_b', 'asche_b') else {})}, px > 400, r=3, klassen='gnwz')
        if o_ and o_['basis'] in ('baum_b', 'zypresse', 'baum'):      # Regel 5: Begleiter vor dem Stumpf + seitlich tiefer
            brn = o_['basis'] == 'baum_b'
            sx = o_['x'] + (31 if brn else 13); sy = o_['y'] + o_['fuss']
            hat = any(setze('brocken_b' if brn else 'kf52', sx + d, sy + T - 2, {'begleiter': True}, d < 0, gap=-30,
                            klassen='gnwz') for d in (14, -14, 18, -18))
            hat += any(setze('busch_b' if brn else 'kf24', sx + s_ * d, sy + T + 6, {'begleiter': True}, s_ > 0, klassen='gnwz')
                       for d in (36, 44, 28) for s_ in (-1, 1))
            if hat < 2:                                                  # Ersatz: Asche/Glut an der Stammecke (flach)
                hat += any(setze('asche_b', sx + s_ * d, sy + 4, {'begleiter': True, 'ebene': 0, 'liegend': True, 'anim': 'kerzen'},
                                 s_ > 0, gap=-4, klassen='gnwz') for d in (24, 30) for s_ in (-1, 1))
            if hat < 2:
                print('  Baum mit wenig Begleitern', o_['basis'], hat)
    for o in objekte:
        if o['basis'] in ('brocken_b', 'busch_b', 'stamm_b', 'baum_b'):
            o['nur_kontakt'] = True
        if o['basis'] in ('brocken', 'kf00', 'kf24', 'kf52', 'unterstand', 'pfosten', 'opfer'):
            o['nur_kontakt'] = True
    json.dump(objekte, open(os.path.join(OBJ, 'platzierung.json'), 'w'), indent=0)
    print('Karte 51: %d Objekte' % len(objekte))


if __name__ == '__main__':
    main()
    import regeln_a02
    regeln_a02.objekte_pruefen('karte51', 't')
