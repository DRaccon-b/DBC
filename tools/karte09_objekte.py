"""Objekte fuer Karte 09 (Vamdemon's Keep) - am 16x16-Raster, nach den Regeln aus CLAUDE.md.

  python3 tools/karte09_bauen.py   (einmal ohne Objekte -> pixelhoehe.npy, wandflaeche.npy)
  python3 tools/karte09_objekte.py && python3 tools/regeln_v11.py karte09 && python3 tools/karte09_objekte.py symmetrie
  python3 tools/karte09_bauen.py

Neu (PixelLab, assets/objekte/karte09): gross (Orgel, Altar, Portal, Turm), moebel, tor, wand.
Wiederverwendet (Regel 3) aus Karte 08 (Overdell): tote Baeume, Grabsteine, Krypten, Laternen, Kleinkram -> k8/...
Wandobjekte (Fenster, Banner, Bilder, Fackeln) sitzen auf den Wandflaechen ueber der Goldleiste ('an_wand').
Paare in Saelen stehen spiegelsymmetrisch zur Teppichachse (Regel 'Symmetrische Plaetze').
"""
import json, os, random, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
from karte04_objekte import saeubern

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte09')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte09')
OBJ8 = os.path.join(ROOT, 'assets', 'objekte', 'karte08')
T = 16
ACHSE_B = 27 * T + 8 + 8          # Teppichachse Portalhalle / grosser Saal (Teppich x 26-28)
ACHSE_D = 75 * T + 8              # Ritualsaal (Rahmen x 66-84)

# Wandobjekte: (sprite, Kachel-x Mitte, Reihe der Mauer-Oberkante der Wandflaeche)
WAND = []
for x in (14, 18):
    WAND += [('wand/00', x, 2)]
for x in (37, 41):
    WAND += [('wand/01', x, 2)]
WAND += [('wand/05', 22, 2), ('wand/05', 33, 2), ('wand/04', 13, 2), ('wand/04', 42, 2)]
WAND += [('wand/00', 65, 2), ('wand/02', 68, 2), ('wand/05', 71, 2), ('wand/05', 79, 2), ('wand/02', 82, 2), ('wand/00', 85, 2)]
WAND += [('wand/03', 5, 2), ('wand/03', 50, 2), ('wand/03', 55, 2)]
WAND += [('wand/02', 4, 17), ('wand/00', 9, 17), ('wand/01', 14, 17), ('wand/02', 19, 17), ('wand/06', 23, 17),
         ('wand/06', 32, 17), ('wand/02', 36, 17), ('wand/01', 41, 17), ('wand/00', 46, 17), ('wand/02', 51, 17),
         ('wand/05', 12, 17), ('wand/05', 43, 17), ('wand/06', 58, 17)]
WAND += [('wand/05', x, 35) for x in (7, 18, 37, 48, 59, 70, 82)]
WAND += [('wand/04', x, 35) for x in (24, 31)]
# (sprite, Kachel-x, Fusskachel-y, Optionen)
FEST = [
    # ---- Portalhalle: Portal in der Achse, je Seite Statue, Saeule, Feuerschale, Gargoyle, Kandelaber (symmetrisch)
    ('gross/02', 27.5, 9, {'symm': None}),
    ('einrichtung/13', 16, 9, {'symm': 'statue'}), ('einrichtung/13', 39, 9, {'symm': 'statue', 'spiegeln': True}),
    ('moebel/00', 19, 8, {'symm': 'saeule1'}), ('moebel/00', 36, 8, {'symm': 'saeule1'}),
    ('moebel/06', 22, 9, {'symm': 'schale', 'anim': 'glimmen'}), ('moebel/06', 33, 9, {'symm': 'schale', 'anim': 'glimmen'}),
    ('moebel/13', 23, 13, {'symm': 'garg'}), ('moebel/13', 32, 13, {'symm': 'garg', 'spiegeln': True}),
    ('moebel/01', 14, 13, {'symm': 'kand1', 'anim': 'kerzen'}), ('moebel/01', 41, 13, {'symm': 'kand1', 'anim': 'kerzen'}),
    # ---- Kreuzung: vier Saeulen um die Teppichkreuzung, Ruestungen am Tor (symmetrisch)
    ('moebel/00', 24, 25, {'symm': 'saeuleK1'}), ('moebel/00', 31, 25, {'symm': 'saeuleK1'}),
    ('moebel/09', 24, 33, {'symm': 'ruestung'}), ('moebel/09', 31, 33, {'symm': 'ruestung', 'spiegeln': True}),
    # ---- grosser Saal West: Thron am Teppichende, Bibliothek mit Kamin, Sitzecke, Weinkeller-Ecke
    ('moebel/07', 4, 26, {}), ('moebel/01', 3, 30, {'anim': 'kerzen'}),
    ('einrichtung/02', 7, 21, {}), ('einrichtung/08', 14, 21, {'anim': 'feuer_kamin'}), ('einrichtung/02', 21, 21, {}),
    ('einrichtung/03', 10, 24, {}), ('einrichtung/07', 18, 24, {}),
    ('einrichtung/11', 11, 32, {}), ('einrichtung/15', 7, 32, {'anim': 'kerzen'}), ('einrichtung/15', 15, 32, {'anim': 'kerzen'}),
    ('einrichtung/10', 19, 31, {}), ('einrichtung/09', 22, 33, {}),
    # ---- grosser Saal Ost: Speisesaal mit zwei Tafeln, Stuehle an den Kopfenden, Kandelaber, Kamin
    ('einrichtung/00', 41, 23, {}), ('einrichtung/01', 38, 23, {}), ('einrichtung/01', 44, 23, {'spiegeln': True}),
    ('einrichtung/00', 41, 32, {}), ('einrichtung/01', 38, 32, {}), ('einrichtung/01', 44, 32, {'spiegeln': True}),
    ('moebel/01', 34, 21, {'anim': 'kerzen'}), ('moebel/01', 51, 21, {'anim': 'kerzen'}),
    ('moebel/11', 51, 33, {}), ('moebel/05', 50, 25, {}),
    # ---- Gang zum Ritualsaal
    ('moebel/13', 58, 22, {}), ('moebel/09', 58, 33, {}),
    # ---- Ritualsaal: Orgel, Altar, Saerge an den Waenden, Statuen, Baenke, Fledermaus-Teppich im Kreis
    ('gross/00', 75, 6, {}), ('gross/01', 75, 10, {}),
    ('moebel/01', 71, 10, {'symm': 'kandD', 'anim': 'kerzen'}), ('moebel/01', 79, 10, {'symm': 'kandD', 'anim': 'kerzen'}),
    ('einrichtung/04', 75, 22, {'boden': True}),
    ('einrichtung/13', 69, 17, {'symm': 'statD'}), ('einrichtung/13', 81, 17, {'symm': 'statD', 'spiegeln': True}),
    ('moebel/03', 70, 30, {'symm': 'bank1'}), ('moebel/03', 80, 30, {'symm': 'bank1'}),
    ('moebel/03', 70, 33, {'symm': 'bank2'}), ('moebel/03', 80, 33, {'symm': 'bank2'}),
    ('moebel/14', 65, 33, {'anim': 'kerzen'}), ('moebel/14', 86, 33, {'anim': 'kerzen'}),
] + [('moebel/02', 64, y, {}) for y in (9, 14, 19, 24)] + [('moebel/02', 86, y, {}) for y in (9, 14, 19, 24)] + [
    # Garten links: Grabstaetten im Beet, toter Baum
    ('k8/baeume/02', 6, 7, {}), ('k8/graeber/13', 4, 9, {}), ('k8/mittel/00', 7, 10, {}), ('wand/31', 5, 12, {}),
    ('k8/klein/02', 8, 13, {'anim': 'glimmen'}),
    # Gartenhof: Gruft, toter Baum, Grab
    ('k8/krypta/00', 57, 7, {}), ('k8/baeume/00', 49, 7, {}), ('k8/mittel/02', 53, 12, {}), ('wand/38', 59, 12, {}),
    # Friedhof: Mausoleum, Gruften, Steinkreis, Lager, Statue, grosser toter Baum
    ('k8/krypta/02', 11, 48, {}), ('k8/krypta/00', 21, 48, {}), ('k8/krypta/00', 4, 62, {}), ('k8/krypta/03', 85, 68, {}),
    ('k8/gross/03', 77, 50, {}), ('wand/32', 38, 76, {}), ('k8/graeber/09', 23, 45, {}), ('k8/graeber/09', 32, 45, {'spiegeln': True}),
    ('wand/34', 66, 57, {}),
] + [('k8/mittel/04', x, y, {}) for (x, y) in ((61, 54), (63, 51), (68, 51), (71, 54), (71, 59), (68, 61), (63, 61), (61, 58))] + [
    ('wand/35', 45, 76, {'anim': 'glimmen'}), ('k8/mittel/13', 47, 78, {'anim': 'kerzen'}), ('wand/60', 49, 75, {}),
    ('k8/mittel/05', 35, 78, {'anim': 'geisterlicht'}), ('k8/mittel/05', 52, 80, {'anim': 'geisterlicht'}),
    ('k8/mittel/05', 24, 50, {'anim': 'geisterlicht'}), ('k8/mittel/05', 34, 50, {'anim': 'geisterlicht'}),
    ('k8/mittel/05', 57, 75, {'anim': 'geisterlicht'}), ('k8/mittel/05', 14, 74, {'anim': 'geisterlicht'}),
    ('wand/26', 62, 46, {}), ('wand/53', 6, 75, {}), ('k8/mittel/11', 18, 58, {}), ('wand/28', 80, 69, {}),
]
GROSS2 = {'wand/00', 'wand/01', 'wand/02', 'wand/05', 'wand/06', 'wand/03'}
GRAEBER = ['k8/mittel/00', 'k8/mittel/01', 'k8/mittel/02', 'k8/mittel/03', 'k8/klein/50', 'k8/klein/51', 'wand/21',
           'wand/22', 'wand/31', 'wand/55', 'wand/59', 'k8/graeber/04']
GRABFELDER = [(7, 51, 16, 51), (6, 56, 9, 56), (13, 56, 17, 56), (7, 60, 12, 60), (60, 47, 68, 47), (76, 61, 84, 66)]
TOTE_BAEUME = ['k8/baeume/00', 'k8/baeume/01', 'k8/baeume/02', 'k8/baeume/03', 'k8/baeume/14', 'wand/38']
HAINE = [(3, 44, 10, 47, 0.12), (36, 44, 48, 52, 0.08), (40, 54, 60, 68, 0.06), (62, 64, 84, 80, 0.07),
         (8, 76, 30, 82, 0.1), (70, 44, 84, 48, 0.08), (26, 60, 40, 70, 0.06)]
STREU = {'k8/klein/04': 6, 'k8/klein/12': 5, 'k8/klein/02': 4, 'k8/klein/03': 2, 'k8/klein/00': 3, 'k8/klein/01': 2,
         'k8/klein/05': 3, 'k8/klein/07': 2, 'k8/klein/09': 2, 'k8/klein/10': 2, 'k8/klein/48': 3, 'k8/klein/47': 2,
         'k8/klein/49': 1, 'k8/klein/40': 1, 'k8/fels_klein/02': 1, 'k8/mittel/14': 1}
STREU_SCHLOSS = {'k8/fels_klein/11': 2, 'k8/klein/05': 1}
LIEGEND = {'k8/klein/00', 'k8/klein/07', 'k8/klein/10', 'k8/klein/49', 'k8/klein/05', 'k8/fels_klein/11'}
FLACH = LIEGEND | {'k8/klein/02', 'k8/klein/03', 'k8/klein/04', 'k8/klein/09', 'k8/klein/12', 'k8/klein/47',
                   'k8/klein/48', 'k8/klein/40', 'k8/klein/01', 'k8/fels_klein/02', 'wand/12'}
WIND = {'k8/klein/04', 'k8/klein/12', 'k8/klein/09', 'k8/klein/47', 'k8/klein/48', 'k8/mittel/14'}


def groesstes_teil(sp, rechts=False):
    """Nur die groesste zusammenhaengende Flaeche behalten (PixelLab-Reste vom Nachbarobjekt)."""
    from collections import deque
    a = np.array(sp)
    m = a[..., 3] > 0
    h, w = m.shape
    lab = np.zeros((h, w), int); n = 0; gr = {}
    for y in range(h):
        for x in range(w):
            if m[y, x] and not lab[y, x]:
                n += 1; q = deque([(y, x)]); lab[y, x] = n; c = 0
                while q:
                    yy, xx = q.popleft(); c += 1
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            y2, x2 = yy + dy, xx + dx
                            if 0 <= y2 < h and 0 <= x2 < w and m[y2, x2] and not lab[y2, x2]:
                                lab[y2, x2] = n; q.append((y2, x2))
                gr[n] = c
    if gr:
        if rechts:                                       # Teil mit der rechtesten Mitte (ab 15 % der Flaeche)
            gross_ = [n_ for n_ in gr if gr[n_] >= 0.15 * max(gr.values())]
            k = max(gross_, key=lambda n_: np.nonzero(lab == n_)[1].mean())
        else:
            k = max(gr, key=gr.get)
        a[lab != k, 3] = 0
    out = Image.fromarray(a)
    return out.crop(out.getbbox())


def quelle(name):
    """Pfad eines Sprites; 'k8/...' kommt aus Karte 08 und wird nach karte09/k8 kopiert (Wiederverwendung)."""
    if name.startswith('k8/'):
        ziel = os.path.join(OBJ, name + '.png')
        if not os.path.exists(ziel):
            os.makedirs(os.path.dirname(ziel), exist_ok=True)
            shutil.copy(os.path.join(OBJ8, name[3:] + '.png'), ziel)
        return ziel
    return os.path.join(OBJ, name + '.png')


def bewerten(lvl, a, x, y):
    Hh, W = lvl.shape
    zeilen = np.nonzero(a.any(axis=1))[0]
    zu = int(zeilen.max())
    fuss = np.nonzero(a[max(0, zu - 2):zu + 1].any(axis=0))[0]
    fx = x + int((fuss.min() + fuss.max()) // 2); fy = y + zu + 1
    if not (0 <= fx < W and 0 <= fy < Hh):
        return False
    ebene = lvl[fy, fx]
    if not 1 <= ebene <= 7:
        return False
    unten = int(zu - (zu - zeilen.min()) * 0.35)
    ys, xs = np.nonzero(a[unten:zu + 1])
    ys, xs = ys + y + unten, xs + x
    if ((ys < 0) | (ys >= Hh) | (xs < 0) | (xs >= W)).any():
        return False
    if (lvl[ys, xs] != ebene).mean() > 0.03:
        return False
    xs_ = np.arange(x + fuss.min(), x + fuss.max() + 1)
    xs_ = xs_[(xs_ >= 0) & (xs_ < W)]
    for dy in range(1, 7):
        if fy + dy < Hh and (lvl[fy + dy, xs_] != ebene).mean() > 0.2:
            return False
    return True


def main():
    rnd = random.Random(9)
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cls = lay['klassen']
    hoehe = [[int(c) for c in r] for r in lay['hoehe']]
    cols, rows = lay['groesse']
    lvl = np.load(os.path.join(KARTE, 'pixelhoehe.npy'))
    flaeche = np.unpackbits(np.load(os.path.join(KARTE, 'wandflaeche.npy')))[:rows * T * cols * T].reshape(rows * T, cols * T).astype(bool)
    os.makedirs(os.path.join(OBJ, 'sauber'), exist_ok=True)
    gesperrt = set()
    for (x0, y0, x1, y1) in lay.get('bruecken', []) + lay.get('stege', []) + [lay['zugbruecke']]:
        for y in range(y0 - 1, y1 + 2):
            for x in range(x0 - 2, x1 + 3):
                gesperrt.add((x, y))
    for tp in lay.get('teleporter', []):
        for y in range(tp['y'] - 2, tp['y'] + tp['h'] + 1):
            for x in range(tp['x'], tp['x'] + tp['b'] + 2):
                gesperrt.add((x, y))
    cache, alpha = {}, {}
    objekte, belegt = [], set()
    pixel = np.zeros(lvl.shape, bool)

    def sprite(name, spiegeln):
        key = (name, spiegeln)
        if key not in cache:
            sp = saeubern(Image.open(quelle(name)).convert('RGBA'))
            if name == 'einrichtung/03':
                sp = groesstes_teil(sp)
            if name == 'einrichtung/01':
                sp = groesstes_teil(sp, rechts=True)        # Stuhl steht rechts, links haengt ein Tischrest
            if name in GROSS2:                                   # Wandfenster/Bilder passend zur 3 Kacheln hohen Wand
                sp = sp.crop(sp.getbbox()).resize((sp.crop(sp.getbbox()).width * 2, sp.crop(sp.getbbox()).height * 2), Image.NEAREST)
            if spiegeln:
                sp = sp.transpose(Image.FLIP_LEFT_RIGHT)
            datei = 'sauber/%s%s.png' % (name.replace('/', '-'), '_m' if spiegeln else '')
            sp.save(os.path.join(OBJ, datei))
            a = np.array(sp.getchannel('A')) >= 128
            zu = int(np.nonzero(a.any(axis=1))[0].max())
            f = np.nonzero(a[max(0, zu - 2):zu + 1].any(axis=0))[0]
            cache[key] = (datei, sp.height, zu, (f.min() + f.max() + 1) / 2.0)
            alpha[datei] = a
        return cache[key]

    def frei_px(datei, x, y):
        a = alpha[datei]
        h_, w_ = a.shape
        y0, x0 = max(0, y), max(0, x)
        y1, x1 = min(pixel.shape[0], y + h_), min(pixel.shape[1], x + w_)
        return not (pixel[y0:y1, x0:x1] & a[y0 - y:y1 - y, x0 - x:x1 - x]).any()

    def belegen(datei, x, y):
        from PIL import ImageFilter
        a = np.array(Image.fromarray((alpha[datei] * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(5))) > 0
        h_, w_ = a.shape
        y0, x0 = max(0, y), max(0, x)
        y1, x1 = min(pixel.shape[0], y + h_), min(pixel.shape[1], x + w_)
        pixel[y0:y1, x0:x1] |= a[y0 - y:y1 - y, x0 - x:x1 - x]

    def setze(name, tx, ty, opt, suchen=False):
        opt = dict(opt)
        opt.pop('symm', None) if opt.get('symm') is None else None
        spiegeln = opt.pop('spiegeln', False)
        boden_ = opt.pop('boden', False)
        art = 'flach' if name in FLACH or boden_ else 'hoch'
        datei, h, zu, mitte = sprite(name, spiegeln)
        kand = [(tx, ty)]
        if suchen:
            kand += sorted(((tx + dx, ty + dy) for dx in range(-3, 4) for dy in range(-3, 4) if dx or dy),
                           key=lambda k: abs(k[0] - tx) + abs(k[1] - ty))
        for (kx, ky) in kand:
            kxi = int(kx)
            if not (0 <= kxi < cols and 0 <= ky < rows) or (kxi, ky) in gesperrt or (kx, ky, art) in belegt:
                continue
            if art == 'hoch' and cls[ky][kxi] == 'w' and not name.startswith(('k8/mittel/05', 'wand/26')):
                continue
            x, y = int(round(kx * T + T / 2 - mitte)), int((ky + 1) * T - 1 - zu)
            if bewerten(lvl, alpha[datei], x, y) and (art == 'flach' or frei_px(datei, x, y)):
                break
        else:
            if suchen or opt.get('symm'):
                print('  keine passende Stelle:', name, (tx, ty))
            return None
        o = {'datei': datei, 'basis': name, 'x': x, 'y': y, 'fuss': h, 'kachel': [int(kx), ky],
             'ebene': 0 if art == 'flach' else 1}
        if not suchen:
            o['fest_pos'] = True                         # feste Objekte nicht mehr verschieben (Saeulen, Baenke ...)
        if name in LIEGEND:
            o['liegend'] = True
        if boden_:
            o.update({'an_wand': True, 'kein_schatten': True, 'keine_verdeckung': True})   # liegt flach auf dem Boden
        o.update(opt)
        objekte.append(o)
        belegt.add((kx, ky, art))
        if art == 'hoch':
            belegen(datei, x, y)
        return o

    # 1) Wandobjekte auf den Wandflaechen (ueber der Goldleiste)
    for (name, tx, reihe) in WAND:
        datei, h, zu, mitte = sprite(name, False)
        X = int(tx * T + T // 2)
        spalte = flaeche[reihe * T:(reihe + 6) * T, X]
        if not spalte.any():
            print('  keine Wandflaeche:', name, tx, reihe)
            continue
        oben = reihe * T + int(np.nonzero(spalte)[0].min())
        x, y = int(round(X - mitte)), oben + 38 - zu if name not in GROSS2 else oben + 39 - zu
        objekte.append({'datei': datei, 'basis': name, 'x': x, 'y': y, 'fuss': h, 'kachel': [tx, oben // T + 2],
                        'ebene': 1, 'an_wand': True, 'kein_schatten': True, 'keine_verdeckung': True,
                        **({'anim': 'kerzen'} if name == 'wand/04' else {})})
    # Tuerme auf der Aussenmauer und Tore (stehen auf/vor der Mauer, eigene Platzierung)
    for (name, tx, fuss_px) in [('einrichtung/05', x, 39 * T + 13) for x in (1.5, 12, 22.5, 32.5, 43, 53.5, 64, 75, 86)] + \
                               [('tor/01', 27.5, 39 * T + 15), ('tor/00', 27.5, 19 * T + 15)]:
        datei, h, zu, mitte = sprite(name, False)
        x, y = int(round(tx * T + T / 2 - mitte)), fuss_px - zu
        objekte.append({'datei': datei, 'basis': name, 'x': x, 'y': y, 'fuss': h, 'kachel': [int(tx), fuss_px // T],
                        'ebene': 1, 'an_wand': True, 'kein_schatten': True, 'keine_verdeckung': True,
                        'vorrang': True})
        if name == 'einrichtung/05':
            belegen(datei, x, y)
        objekte[-1]['fest_pos'] = True
    # 2) feste Objekte
    for (name, tx, ty, opt) in FEST:
        setze(name, tx, ty, opt, suchen='symm' not in opt or opt.get('symm') is None)
    # 3) Grabfelder
    for (x0, y0, x1, y1) in GRABFELDER:
        for ty in range(y0, y1 + 1):
            for tx in range(x0, x1 + 1, 2):
                if rnd.random() < 0.85:
                    setze(rnd.choice(GRAEBER), tx, ty, {'spiegeln': rnd.random() < 0.3})
    # 4) tote Baeume (Regel 5: Begleiter)
    baeume = []
    for (x0, y0, x1, y1, d) in HAINE:
        for ty in range(y0, y1 + 1):
            for tx in range(x0, x1 + 1):
                if cls[ty][tx] in 'gh' and hoehe[ty][tx] == 1 and rnd.random() < d:
                    o = setze(rnd.choice(TOTE_BAEUME), tx, ty, {'spiegeln': rnd.random() < 0.5})
                    if o:
                        baeume.append(o)
    for o in baeume:
        kx, ky = o['kachel']
        if not [p for p in baeume if p is not o and abs(p['kachel'][0] - kx) <= 3 and abs(p['kachel'][1] - ky) <= 3]:
            setze(rnd.choice(['k8/mittel/14', 'k8/klein/48', 'k8/klein/04']), kx + rnd.choice((-1, 1)), ky + 1,
                  {'begleiter': True, 'anim': 'wehen'})
    # 5) Streudeko: Friedhof und (sparsam) Schlossboden
    for (streu, arten, anzahl, y0, y1) in ((STREU, 'gh', 230, 43, rows), (STREU_SCHLOSS, 'i', 14, 2, 40)):
        namen, gew = list(streu), list(streu.values())
        n = 0
        for _ in range(8000):
            if n >= anzahl:
                break
            tx, ty = rnd.randrange(2, cols - 2), rnd.randrange(y0, y1 - 1)
            if cls[ty][tx] not in arten or hoehe[ty][tx] != 1:
                continue
            if arten == 'i' and any(cls[yy][xx] in 'cv' for yy in range(ty - 1, ty + 2) for xx in range(tx - 1, tx + 2)):
                continue
            name = rnd.choices(namen, weights=gew)[0]
            opt = {'anim': 'wehen'} if name in WIND else {'anim': 'glimmen'} if name in ('k8/klein/02', 'k8/fels_klein/02') else {}
            if setze(name, tx, ty, opt):
                n += 1
    json.dump(objekte, open(os.path.join(OBJ, 'platzierung.json'), 'w'), indent=0)
    print(len(objekte), 'Objekte gesetzt')


def symmetrie():
    """Paare exakt spiegelsymmetrisch zur Achse ihres Saals."""
    pf = os.path.join(OBJ, 'platzierung.json')
    objs = json.load(open(pf))
    paare = {}
    for o in objs:
        if o.get('symm'):
            paare.setdefault(o['symm'], []).append(o)
    for name, ps in paare.items():
        if len(ps) != 2:
            print('  Paar unvollstaendig:', name, len(ps))
            continue
        l, r = sorted(ps, key=lambda o: o['x'])
        achse = ACHSE_D if l['x'] > 62 * T else ACHSE_B
        w = Image.open(os.path.join(OBJ, l['datei'])).width
        r['x'], r['y'] = 2 * achse - l['x'] - w, l['y']
    json.dump(objs, open(pf, 'w'), indent=0)
    print('Symmetrie: %d Paare' % len(paare))


if __name__ == '__main__':
    symmetrie() if sys.argv[1:] == ['symmetrie'] else main()
