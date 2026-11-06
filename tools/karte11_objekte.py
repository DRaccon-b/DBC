"""Objekte fuer Karte 11 (Spiral Mountain: Dark Ocean) - am 16x16-Raster, nach den Regeln aus CLAUDE.md.

  python3 tools/karte11_bauen.py   (einmal ohne Objekte -> pixelhoehe.npy)
  python3 tools/karte11_objekte.py && python3 tools/regeln_v11.py karte11 && python3 tools/karte11_objekte.py symmetrie
  python3 tools/karte11_bauen.py

Neu (PixelLab, assets/objekte/karte11): gross (Walskelett, Wracks, Felsnadel), meer (Korallen, Seetang, Seesterne ...),
land (Anker, Kohlenbecken, Obelisk, Runensaeule, Ketten, Treibholz, Schaedel ...).
Wiederverwendet (Regel 3) aus Karte 08 (Overdell): tote Baeume, schwarze Felsen, Skelett, Kristalle -> k8/...
Grosse Objekte zuerst, Paare an Bruecke und Plattform spiegelsymmetrisch, Kleinkram unregelmaessig und sparsam.
"""
import json, os, random, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageFilter
from karte04_objekte import saeubern
from karte09_objekte import raster_x, bewerten

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte11')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte11')
OBJ8 = os.path.join(ROOT, 'assets', 'objekte', 'karte08')
T = 16
ACHSE_P = int(69.5 * T)          # Plattform (Achteck) und Bannkreis
ACHSE_BR = 38 * T + 8            # Bruecke (Mitte der Reihen 37-39) - fuer die Kohlenbecken oben/unten

TOTE_BAEUME = ['k8/baeume/00', 'k8/baeume/01', 'k8/baeume/02', 'k8/baeume/03', 'k8/baeume/14']
FELSEN = ['k8/fels/00', 'k8/fels/02', 'k8/fels/03', 'k8/fels/06', 'k8/fels/11', 'k8/fels/12', 'k8/fels/13']
BEGLEITER = ['land/10', 'land/15', 'k8/fels/03', 'k8/fels/10']
LAND_STREU = {'land/08': 3, 'land/09': 2, 'land/04': 2, 'land/15': 4, 'land/10': 4, 'k8/fels/04': 2, 'k8/fels/10': 2,
              'land/06': 2, 'land/05': 1}
STRAND_STREU = {'land/06': 3, 'land/08': 2, 'meer/07': 3, 'meer/09': 2, 'meer/08': 2, 'land/04': 1}
MEER_STREU = {'meer/00': 5, 'meer/01': 4, 'meer/02': 2, 'meer/10': 2, 'meer/12': 3, 'meer/05': 3, 'meer/06': 1,
              'meer/14': 2, 'meer/08': 2, 'meer/09': 2, 'meer/11': 2, 'meer/13': 2}
SEETANG_STREU = {'meer/03': 5, 'meer/04': 4, 'meer/15': 3}
WIND = {'meer/03', 'meer/04', 'meer/15', 'land/10'}
FLACH = {'meer/07', 'meer/05', 'meer/09', 'meer/12', 'meer/14', 'land/04', 'land/06', 'land/08', 'land/09', 'land/15',
         'k8/fels/04', 'k8/fels/11'}
LIEGEND = {'land/04', 'land/06', 'land/08', 'k8/fels/04', 'land/07'}
LEUCHTEN = {'land/01': 'feuer', 'land/11': 'geisterlicht', 'land/03': 'glimmen', 'meer/11': 'geisterlicht',
            'k8/fels/10': 'glimmen'}
SPITZEN = [(57, 5), (62, 8), (78, 21), (59, 56), (67, 62), (75, 58), (37, 63), (15, 63), (29, 64), (45, 66)]

# (sprite, Mitte x in px, Fussreihe, Optionen)
FEST = [
    # grosse Objekte zuerst
    ('gross/00', 26 * T, 27, {}), ('gross/01', 23 * T, 47, {}), ('gross/02', 45 * T + 8, 33, {}),
    # Bruecke: Kohlenbecken an beiden Seiten des Brueckenkopfs (spiegelgleich zur Brueckenachse)
    ('land/01', 61 * T + 8, 36, {'symm_y': 'kb'}), ('land/01', 61 * T + 8, 42, {'symm_y': 'kb'}),
    # Plattform: Runensaeulen am Rand, spiegelgleich zur Achse; Kohlenbecken am Bannkreis
    ('land/03', ACHSE_P - 80, 32, {'symm': 'p1'}), ('land/03', ACHSE_P + 80, 32, {'symm': 'p1'}),
    ('land/03', ACHSE_P - 72, 47, {'symm': 'p4'}), ('land/03', ACHSE_P + 72, 47, {'symm': 'p4'}),
    # Brueckenkopf am Strand: zwei Laternen spiegelgleich zur Brueckenachse
    ('land/11', 40 * T + 8, 36, {'symm_y': 'bk'}), ('land/11', 40 * T + 8, 41, {'symm_y': 'bk'}),
    # Ruinen-Platz: Kohlenbecken, Laternen, Schild, Kisten
    ('land/01', 3 * T + 8, 27, {'symm': 'r1'}), ('land/01', 12 * T + 8, 27, {'symm': 'r1'}),
    ('land/11', 3 * T + 8, 35, {}), ('land/12', 12 * T, 34, {}), ('land/13', 8 * T, 33, {}), ('land/05', 10 * T, 31, {}),
    # Weg zum Teleporter oben: Laternen beidseitig
    ('land/11', 28 * T + 8, 7, {'symm': 't1'}), ('land/11', 36 * T + 8, 7, {'symm': 't1'}),
    # Strand: Anker, Mastbruch, Treibholz
    ('land/00', 30 * T, 55, {}), ('land/07', 33 * T, 45, {}), ('land/06', 38 * T, 52, {}),
    # Felsblock: schwarze Felsen davor
    ('k8/fels/00', 15 * T, 22, {}), ('k8/fels/12', 22 * T + 8, 22, {}),
    # Plateaus: tote Baeume in Gruppen mit Begleitern (Regel 5)
    ('k8/baeume/00', 4 * T, 8, {}), ('k8/baeume/02', 7 * T + 8, 10, {}), ('land/10', 5 * T + 8, 11, {'begleiter': True}),
    ('k8/baeume/14', 4 * T, 15, {}), ('k8/baeume/03', 8 * T, 17, {}), ('k8/fels/10', 6 * T, 18, {}),
    ('k8/baeume/01', 4 * T, 43, {}), ('k8/baeume/02', 7 * T + 8, 45, {}), ('land/15', 5 * T + 8, 46, {'begleiter': True}),
    ('k8/baeume/00', 4 * T, 50, {}), ('k8/baeume/03', 8 * T, 51, {}), ('k8/fels/10', 6 * T, 52, {}),
]
# Haine auf dem verseuchten Land (tote Baeume)
HAINE = [(11, 6, 28, 14, 0.035), (11, 38, 30, 56, 0.03), (28, 14, 40, 40, 0.02)]


def quelle(name):
    if name.startswith('k8/'):
        ziel = os.path.join(OBJ, name + '.png')
        if not os.path.exists(ziel):
            os.makedirs(os.path.dirname(ziel), exist_ok=True)
            shutil.copy(os.path.join(OBJ8, name[3:] + '.png'), ziel)
        return ziel
    return os.path.join(OBJ, name + '.png')


def main():
    rnd = random.Random(11)
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cls = lay['klassen']
    cols, rows = lay['groesse']
    lvl = np.load(os.path.join(KARTE, 'pixelhoehe.npy'))
    os.makedirs(os.path.join(OBJ, 'sauber'), exist_ok=True)
    cache, alpha = {}, {}
    objekte, belegt = [], set()
    pixel = np.zeros(lvl.shape, bool)
    gesperrt = set()
    b_ = lay.get('bruecke')
    if b_:
        for y in range(b_[1] - 1, b_[3] + 4):
            for x in range(b_[0], b_[2] + 1):
                gesperrt.add((x, y))
    for tp in lay.get('teleporter', []):
        for y in range(tp['y'] - 1, tp['y'] + tp['h'] + 2):
            for x in range(tp['x'] - 1, tp['x'] + tp['b'] + 2):
                gesperrt.add((x, y))

    def sprite(name, spiegeln=False):
        key = (name, spiegeln)
        if key not in cache:
            sp = saeubern(Image.open(quelle(name)).convert('RGBA'))
            if spiegeln:
                sp = sp.transpose(Image.FLIP_LEFT_RIGHT)
            datei = 'sauber/%s%s.png' % (name.replace('/', '-'), '_m' if spiegeln else '')
            sp.save(os.path.join(OBJ, datei))
            a = np.array(sp.getchannel('A')) >= 128
            zu = int(np.nonzero(a.any(axis=1))[0].max())
            xs = np.nonzero(a.any(axis=0))[0]
            cache[key] = (datei, sp.height, zu, (xs.min() + xs.max() + 1) / 2.0)
            alpha[datei] = a
        return cache[key]

    def frei_px(datei, x, y):
        a = alpha[datei]
        h_, w_ = a.shape
        y0, x0 = max(0, y), max(0, x)
        y1, x1 = min(pixel.shape[0], y + h_), min(pixel.shape[1], x + w_)
        if y1 <= y0 or x1 <= x0:
            return True
        return not (pixel[y0:y1, x0:x1] & a[y0 - y:y1 - y, x0 - x:x1 - x]).any()

    def belegen(datei, x, y):
        a = np.array(Image.fromarray((alpha[datei] * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(5))) > 0
        h_, w_ = a.shape
        y0, x0 = max(0, y), max(0, x)
        y1, x1 = min(pixel.shape[0], y + h_), min(pixel.shape[1], x + w_)
        if y1 > y0 and x1 > x0:
            pixel[y0:y1, x0:x1] |= a[y0 - y:y1 - y, x0 - x:x1 - x]

    def setzen(name, X, fy, opt, suchen=False, arten=None, melden=False):
        opt = dict(opt)
        datei, h, zu, mitte = sprite(name, opt.pop('spiegeln', False))
        kand = [(X, fy)]
        if suchen:
            kand += sorted(((X + dx * T, fy + dy) for dx in range(-2, 3) for dy in range(-2, 3) if dx or dy),
                           key=lambda k: abs(k[0] - X) / T + abs(k[1] - fy))
        for (kx, ky) in kand:
            tx = int(kx // T)
            if not (0 <= tx < cols and 0 <= ky < rows) or (tx, ky) in gesperrt:
                continue
            if arten and cls[ky][tx] not in arten:
                continue
            x = raster_x(alpha[datei], kx) if not opt.get('achse') else int(round(kx - mitte))
            y = (ky + 1) * T - 1 - zu
            if bewerten(lvl, alpha[datei], x, y) and (opt.get('begleiter') or frei_px(datei, x, y)):
                break
        else:
            if melden:
                print('  keine passende Stelle:', name, (X // T, fy))
            return None
        o = {'datei': datei, 'basis': name, 'x': x, 'y': y, 'fuss': h, 'kachel': [tx, ky],
             'ebene': 0 if name in FLACH else 1}
        if name in LIEGEND:
            o['liegend'] = True
        if name in WIND:
            o['anim'] = 'wehen'
        if name in LEUCHTEN:
            o['anim'] = LEUCHTEN[name]
        o.update(opt)
        objekte.append(o)
        belegt.add((tx, ky))
        if name not in FLACH and not o.get('begleiter'):
            belegen(datei, x, y)
        return o

    # 1) Felsnadeln in der Tiefsee (stehen im Wasser, Fuss in der Tiefe)
    stufen = np.load(os.path.join(KARTE, 'meer_stufen.npy'))
    for (tx, ty) in SPITZEN:
        st_ = int(stufen[min(stufen.shape[0] - 1, ty * T + 12), tx * T + 8])
        name = 'gross/03' if st_ <= 2 else 'meer/13'       # tiefe Stufen: nur noch kleine Spitzen ragen heraus
        datei, h, zu, mitte = sprite(name, (tx * 7 + ty) % 2 == 1)
        x, y = raster_x(alpha[datei], tx * T + 8), (ty + 1) * T - 1 - zu
        if not frei_px(datei, x, y):
            continue
        objekte.append({'datei': datei, 'basis': name, 'x': x, 'y': y, 'fuss': h, 'kachel': [tx, ty], 'ebene': 1,
                        'fest_pos': True, 'im_wasser': True, 'kein_schatten': True})
        belegen(datei, x, y)
    # 2) feste Objekte
    for (name, X, fy, opt) in FEST:
        setzen(name, X, fy, opt, suchen=not (opt.get('symm') or opt.get('symm_y') or opt.get('achse')), melden=True)
    # 3) tote Baeume auf dem Land, Begleiter (Regel 5)
    baeume = []
    for (x0, y0, x1, y1, d) in HAINE:
        for ty in range(y0, y1 + 1):
            for tx in range(x0, x1 + 1):
                if cls[ty][tx] in 'dm' and rnd.random() < d:
                    o = setzen(rnd.choice(TOTE_BAEUME), tx * T + 8, ty, {'spiegeln': rnd.random() < 0.5}, arten='dm')
                    if o:
                        baeume.append(o)
    for o in baeume:
        kx, ky = o['kachel']
        if not [p for p in baeume if p is not o and abs(p['kachel'][0] - kx) <= 3 and abs(p['kachel'][1] - ky) <= 3]:
            setzen(rnd.choice(BEGLEITER), (kx + rnd.choice((-1, 1))) * T + 8, ky, {'begleiter': True}, arten='dmn')
            setzen(rnd.choice(BEGLEITER[:2]), (kx + rnd.choice((-2, 2))) * T + 8, ky + 1, {}, arten='dmn')
    # 4) schwarze Felsen und Kleinkram (unregelmaessig, sparsam)
    for (streu, arten, anzahl, x_lim) in ((dict((f, 2) for f in FELSEN), 'dm', 12, (2, 42)), (LAND_STREU, 'dm', 16, (2, 42)),
                                          (STRAND_STREU, 'n', 12, (2, 60)), (MEER_STREU, 'u', 20, (34, 76)),
                                          (SEETANG_STREU, 'h', 18, (34, 76))):
        namen, gew = list(streu), list(streu.values())
        n = 0
        for _ in range(9000):
            if n >= anzahl:
                break
            tx, ty = rnd.randrange(*x_lim), rnd.randrange(4, rows - 4)
            if any(cls[yy][xx] not in arten for yy in range(ty - 1, ty + 2) for xx in range(tx - 1, tx + 2)):
                continue
            if setzen(rnd.choices(namen, weights=gew)[0], tx * T + 8, ty, {'spiegeln': rnd.random() < 0.4}, arten=arten):
                n += 1
    json.dump(objekte, open(os.path.join(OBJ, 'platzierung.json'), 'w'), indent=0)
    print(len(objekte), 'Objekte gesetzt')


def symmetrie():
    """Paare exakt spiegelsymmetrisch: 'symm' zur senkrechten Achse (Plattform bzw. Platz), 'symm_y' zur
    waagerechten Brueckenachse; 'achse' genau auf die Achse."""
    pf = os.path.join(OBJ, 'platzierung.json')
    objs = json.load(open(pf))
    achsen = {'r1': 8 * T, 't1': 32 * T + 8}
    paare, paare_y = {}, {}
    for o in objs:
        if o.get('achse'):
            a_ = np.array(Image.open(os.path.join(OBJ, o['datei'])).getchannel('A')) > 128
            xs_ = np.nonzero(a_.any(axis=0))[0]
            o['x'] = int(round(o['achse'] - (xs_.min() + xs_.max() + 1) / 2.0))
        if o.get('symm'):
            paare.setdefault(o['symm'], []).append(o)
        if o.get('symm_y'):
            paare_y.setdefault(o['symm_y'], []).append(o)
    for name, ps in paare.items():
        if len(ps) == 1:                                     # fehlender Partner: gespiegelt ergaenzen
            neu = dict(ps[0]); objs.append(neu); ps.append(neu)
            neu['x'] = ps[0]['x'] + (1 if ps[0]['x'] < achsen.get(name, ACHSE_P) else -1)
        if len(ps) != 2:
            print('  Paar unvollstaendig:', name, len(ps))
            continue
        l, r = sorted(ps, key=lambda o: o['x'])
        achse = achsen.get(name, ACHSE_P)
        a_ = np.array(Image.open(os.path.join(OBJ, l['datei'])).getchannel('A')) > 128
        xs_ = np.nonzero(a_.any(axis=0))[0]
        m_ = (xs_.min() + xs_.max() + 1) / 2.0
        r['x'] = int(round(2 * achse - (l['x'] + m_) - m_))
        r['y'] = l['y']
    for name, ps in paare_y.items():
        if len(ps) == 1:                                     # fehlender Partner: an der Brueckenachse gespiegelt
            o0 = ps[0]
            neu = dict(o0)
            a_ = np.array(Image.open(os.path.join(OBJ, o0['datei'])).getchannel('A')) > 128
            zu_ = int(np.nonzero(a_.any(axis=1))[0].max())
            fuss = o0['y'] + zu_
            neu['y'] = int(2 * ACHSE_BR - fuss) - zu_ + (T if fuss < ACHSE_BR else -T)
            objs.append(neu); ps.append(neu)
        if len(ps) != 2:
            print('  Paar unvollstaendig:', name, len(ps))
            continue
        o_, u_ = sorted(ps, key=lambda o: o['y'])
        u_['x'] = o_['x']
    json.dump(objs, open(pf, 'w'), indent=0)
    print('Symmetrie: %d + %d Paare' % (len(paare), len(paare_y)))


if __name__ == '__main__':
    symmetrie() if sys.argv[1:] == ['symmetrie'] else main()
