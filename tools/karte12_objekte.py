"""Objekte fuer Karte 12 (Spiral Mountain: Puppet Woods) - am 16x16-Raster, nach den Regeln aus CLAUDE.md.

  python3 tools/karte12_bauen.py   (einmal ohne Objekte -> pixelhoehe.npy)
  python3 tools/karte12_objekte.py && python3 tools/regeln_v11.py karte12 && python3 tools/karte12_objekte.py symmetrie
  python3 tools/karte12_bauen.py

Neu (PixelLab, assets/objekte/karte12): gross (Baumhaus, Riesen-Eiche, Puppentheater, Trauerbaum), wald (duestere
Waldbaeume, Apfel-/Birnbaum, Buesche, Pilze, Stumpf, Farn, Stamm), puppen (Marionetten, Kuerbislaterne, Wagen, Truhe,
Zielscheibe, Holzhammer, Vogelscheuche ...), klein (Pilze, Laub, Wurzeln, Rohrkolben, Frosch ...).
Wiederverwendet (Regel 3): tote Baeume aus Karte 08 (k8/...), Kuerbisse und Feldpflanzen aus Karte 07 (k7/...).
Anspielung auf den Puppenmeister des Waldes nur ueber Holz, Faeden, Marionetten, Rot/Blau - keine Figur nachgebaut.
Grosse Objekte zuerst, dichte Waldstuecke (Regel 8 Ausnahme dichter Wald), Paare spiegelsymmetrisch, Kleinkram sparsam.
"""
import json, os, random, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageFilter
from karte04_objekte import saeubern
from karte09_objekte import raster_x, bewerten

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte12')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte12')
QUELLEN = {'k8/': os.path.join(ROOT, 'assets', 'objekte', 'karte08'), 'k7/': os.path.join(ROOT, 'assets', 'objekte', 'karte07')}
T = 16
ACHSE_A = int(60.5 * T)          # Arena (senkrechte Achse)
ACHSE_AY = 17 * T                # Arena (waagerechte Achse, Mitte der Reihe 16/17)
ACHSE_PL = 40 * T                # Platz am unteren Ausgang

WALDBAEUME = ['wald/00', 'wald/01', 'wald/02', 'wald/03', 'wald/04', 'wald/05', 'wald/08', 'wald/09']
OBSTBAEUME = ['wald/06', 'wald/07']
EINZELBAEUME = ['k8/baeume/00', 'k8/baeume/01', 'k8/baeume/02', 'wald/09', 'wald/03', 'k8/baeume/14']
BEGLEITER = ['wald/12', 'wald/13', 'wald/10', 'wald/11', 'puppen/13', 'wald/14']
KUERBIS = ['klein/08']
BERG_OBJ = ['wald/04', 'wald/05', 'wald/11', 'wald/10', 'k8/baeume/03', 'k8/fels/00', 'k8/fels/02', 'k8/fels/03',
            'k8/fels/06', 'wald/13', 'wald/09', 'klein/16', 'klein/02', 'wald/14', 'k8/baeume/00']
LAND_STREU = {'klein/00': 3, 'klein/01': 3, 'klein/41': 2, 'klein/03': 3, 'klein/04': 2, 'klein/05': 2, 'klein/10': 2,
              'klein/17': 1, 'klein/24': 1, 'klein/32': 2, 'klein/57': 2, 'klein/62': 1, 'klein/58': 1, 'klein/35': 1,
              'klein/02': 3, 'klein/20': 2, 'klein/29': 1, 'klein/15': 1, 'klein/06': 1, 'klein/11': 1}
WALD_STREU = {'klein/09': 3, 'klein/36': 2, 'klein/53': 2, 'klein/00': 2, 'klein/56': 2, 'klein/19': 2, 'klein/02': 2}
MOOR_RAND = {'klein/48': 4, 'klein/54': 1, 'klein/02': 2}
PUPPEN_STREU = {'puppen/02': 1, 'puppen/15': 1, 'puppen/14': 1, 'puppen/13': 1, 'puppen/09': 2, 'klein/46': 1,
                'klein/37': 1, 'klein/44': 1, 'klein/26': 1, 'klein/49': 1, 'klein/55': 1, 'klein/31': 1}
WIND = {'klein/48', 'klein/09', 'klein/36', 'wald/14', 'klein/02'}
FLACH = {'klein/03', 'klein/04', 'klein/05', 'klein/06', 'klein/11', 'klein/14', 'klein/15', 'klein/19', 'klein/56',
         'klein/57', 'klein/58', 'klein/26', 'klein/35', 'klein/37', 'klein/02', 'klein/10'}
LIEGEND = {'klein/04', 'klein/03', 'klein/57', 'klein/26', 'klein/37', 'puppen/15', 'wald/15', 'klein/42', 'klein/10',
           'klein/58', 'klein/44'}
LEUCHTEN = {'puppen/03': 'kerzen', 'klein/31': 'kerzen', 'baumhaus/00': 'lampe'}


def quelle(name):
    for pre, pfad in QUELLEN.items():
        if name.startswith(pre):
            ziel = os.path.join(OBJ, name + '.png')
            if not os.path.exists(ziel):
                os.makedirs(os.path.dirname(ziel), exist_ok=True)
                shutil.copy(os.path.join(pfad, name[3:] + '.png'), ziel)
            return ziel
    return os.path.join(OBJ, name + '.png')


def main():
    rnd = random.Random(12)
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cls = lay['klassen']
    cols, rows = lay['groesse']
    lvl = np.load(os.path.join(KARTE, 'pixelhoehe.npy'))
    os.makedirs(os.path.join(OBJ, 'sauber'), exist_ok=True)
    cache, alpha = {}, {}
    objekte, belegt = [], set()
    pixel = np.zeros(lvl.shape, bool)
    gesperrt = set()
    for tp in lay.get('teleporter', []):
        for y in range(tp['y'] - 1, tp['y'] + tp['h'] + 2):
            for x in range(tp['x'] - 1, tp['x'] + tp['b'] + 2):
                gesperrt.add((x, y))
    for (x0, x1, e, yb) in lay.get('treppen_sued', []):          # Treppen und ihr Vorplatz bleiben frei
        for y in range(yb - 1, yb + 5):
            for x in range(x0 - 1, x1 + 2):
                gesperrt.add((x, y))
    pfad = {(x, y) for y in range(rows) for x in range(cols) if cls[y][x] == 'q'}
    for (x0, y0, x1, y1, _) in lay.get('bruecken', []):         # Bruecken und Arena-Treppe frei
        for y in range(y0 - 1, y1 + 2):
            for x in range(x0 - 1, x1 + 2):
                gesperrt.add((x, y))
    tr = lay.get('arena_treppe')
    if tr:
        for y in range(tr[2] - 1, tr[2] + 5):
            for x in range(tr[0] - 1, tr[1] + 2):
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

    def baum_ok(datei, x, y):
        """Begleiter (Regel 5) verdeckt hoechstens den Sockel eines Baums an der Ecke - nie Stamm oder Krone."""
        a = alpha[datei]
        for t in objekte:
            if not t.get('baum'):
                continue
            at = alpha[t['datei']]
            x0, y0 = max(t['x'], x), max(t['y'], y)
            x1, y1 = min(t['x'] + at.shape[1], x + a.shape[1]), min(t['y'] + at.shape[0], y + a.shape[0])
            if x1 <= x0 or y1 <= y0:
                continue
            ov = at[y0 - t['y']:y1 - t['y'], x0 - t['x']:x1 - t['x']] & a[y0 - y:y1 - y, x0 - x:x1 - x]
            if not ov.any():
                continue
            fuss_t = t['y'] + int(np.nonzero(at.any(axis=1))[0].max())
            ys_ = np.nonzero(ov.any(axis=1))[0] + y0
            if ys_.min() < fuss_t - 18 or ov.sum() > 0.2 * a.sum():   # nur unten am Sockel, nur ein kleiner Teil
                return False
            xs_t = np.nonzero(at[-20:].any(axis=0))[0]                 # Stammfuss: mittlere Spalten des Sockels
            mt = t['x'] + (xs_t.min() + xs_t.max() + 1) / 2.0
            xs_b = np.nonzero(a.any(axis=0))[0]
            if abs(x + (xs_b.min() + xs_b.max() + 1) / 2.0 - mt) < 0.45 * (xs_b.max() - xs_b.min() + 1) + 6:
                return False                                            # seitlich an der Ecke, nicht mittig vor dem Stamm
        return True

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
            if bewerten(lvl, alpha[datei], x, y) and (frei_px(datei, x, y) if not opt.get('begleiter') else baum_ok(datei, x, y)):
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

    # 0) Rand der Karte: Farne auf der Bergkuppe, vom Kartenrand angeschnitten (wie der Baumrand auf Karte 01),
    #    starr; frei bleiben die Teleporter und die Felsschlucht, durch die der Fluss die Karte verlaesst
    Hp, Wp = lvl.shape
    frei_x = [(12 * T - 8, 16 * T + 8), (38 * T - 8, 42 * T + 8), (51 * T, 57 * T)]
    rr = random.Random(5)
    stellen = []
    for X in range(-6, Wp + 20, 30):
        stellen.append((X + rr.randint(-5, 5), 20 + rr.randint(-4, 4), 'oben'))
        stellen.append((X + rr.randint(-5, 5), Hp + 16 + rr.randint(-4, 4), 'unten'))
    for Y in range(40, Hp + 10, 28):
        stellen.append((2 + rr.randint(-4, 4), Y + rr.randint(-4, 4), 'seite'))
        stellen.append((Wp - 2 + rr.randint(-4, 4), Y + rr.randint(-4, 4), 'seite'))
    for i_, (X, fussy, seite) in enumerate(stellen):
        if seite != 'seite' and any(a_ <= X <= b_ for a_, b_ in frei_x if (seite == 'unten' or a_ < 300)):
            continue
        datei, h, zu, mitte = sprite('wald/14', i_ % 2 == 1)
        x, y = int(round(X - mitte)), fussy - zu
        objekte.append({'datei': datei, 'basis': 'wald/14', 'x': x, 'y': y, 'fuss': h, 'kachel': [max(0, min(cols - 1, X // T)),
                        max(0, min(rows - 1, fussy // T))], 'ebene': 1, 'fest_pos': True, 'rand': True, 'kein_schatten': True,
                        'baum': True})
        belegen(datei, x, y)
    # 1) grosse Objekte zuerst: Baumhaus, Puppentheater an der Arena, Riesen-Eiche, Trauerbaum
    bh = lay['baumhaus']
    FEST = [
        ('baumhaus/00', bh[0] * T + 8, bh[1] + 1, {'baum': True}),
        ('gross/02', ACHSE_A, 9, {'achse': ACHSE_A}),                       # Theater am Nordrand der Arena, auf der Achse
        ('gross/01', 8 * T, 22, {'baum': True}), ('gross/03', 29 * T, 64, {'baum': True}), ('gross/01', 70 * T, 62, {'baum': True}),
        # Arena: Kuerbislaternen an beiden Eingaengen, Zielscheiben links und rechts - spiegelgleich zur Achse
        ('puppen/03', ACHSE_A - 72, 30, {'symm': 'a1'}), ('puppen/03', ACHSE_A + 72, 30, {'symm': 'a1'}),
        ('puppen/10', ACHSE_A - 104, 17, {'symm': 'a2'}), ('puppen/10', ACHSE_A + 104, 17, {'symm': 'a2'}),
        ('puppen/01', ACHSE_A - 120, 11, {'symm': 'a3'}), ('puppen/01', ACHSE_A + 120, 11, {'symm': 'a3'}),
        # Platz am unteren Ausgang: Laternen, Truhe, Wagen, Wegweiser am Pfadbeginn
        ('puppen/03', ACHSE_PL - 88, 58, {'symm': 'p1'}), ('puppen/03', ACHSE_PL + 88, 58, {'symm': 'p1'}),
        ('puppen/05', 35 * T, 62, {}), ('puppen/04', 46 * T, 63, {}), ('puppen/06', 42 * T, 54, {}),
        # Baumhaus: Truhe und Marionette davor, Wegweiser am Pfad oben
        ('puppen/00', 37 * T, 14, {}), ('puppen/06', 17 * T, 12, {}), ('puppen/11', 48 * T, 13, {}),
        # Felder: Vogelscheuchen
        ('puppen/12', 49 * T, 34, {}), ('puppen/12', 67 * T, 33, {}), ('puppen/12', 55 * T, 52, {}),
        # Plateaus: je ein Blickfang
        ('puppen/02', 30 * T, 18, {}), ('wald/12', 11 * T, 41, {}), ('wald/13', 54 * T, 45, {}),
        ('wald/12', 19 * T, 5, {}), ('klein/46', 24 * T, 6, {}),
    ]
    for (name, X, fy, opt) in FEST:
        setzen(name, X, fy, opt, suchen=not (opt.get('symm') or opt.get('achse')), melden=True)
    # 2) dichte Waldstuecke (Ausnahme dichter Wald: Kronen ueberlappen aussen, Sockel nie)
    for (x0, y0, x1, y1) in lay['wald']:
        for ty in range(y0, y1 + 2, 2):
            versatz = (ty // 2) % 2
            for tx in range(x0 + versatz, x1 + 1, 2):
                if cls[ty][tx] != 'g' or (tx, ty) in belegt or rnd.random() < 0.12:
                    continue
                datei, h, zu, mitte = sprite(rnd.choice(WALDBAEUME), rnd.random() < 0.5)
                x, y = raster_x(alpha[datei], tx * T + 8), (ty + 1) * T - 1 - zu
                if not bewerten(lvl, alpha[datei], x, y):
                    continue
                if any(abs(o['kachel'][0] - tx) < 2 and o['kachel'][1] == ty for o in objekte):
                    continue
                o = {'datei': datei, 'basis': datei.split('sauber/')[1].replace('-', '/').replace('_m.png', '').replace('.png', ''),
                     'x': x, 'y': y, 'fuss': h, 'kachel': [tx, ty], 'ebene': 1, 'baum': True}
                objekte.append(o)
                belegt.add((tx, ty))
                belegen(datei, x, y)
    # 3) Obstbaumreihen (Plantage) und Kuerbisfelder
    for (ty, x0, x1, schritt) in ((30, 46, 75, 4), (39, 44, 72, 4), (56, 51, 75, 4), (47, 49, 51, 4)):
        for tx in range(x0, x1 + 1, schritt):
            setzen(OBSTBAEUME[(tx // schritt + ty) % 2], tx * T + 8, ty, {'baum': True}, arten='dq')
    for ty in range(rows):
        for tx in range(cols):
            if cls[ty][tx] == 'a' and rnd.random() < 0.85:
                setzen(rnd.choice(KUERBIS), tx * T + 8, ty, {'spiegeln': rnd.random() < 0.5}, arten='a')
    # 4) einzelne duestere Baeume auf dem Schlamm, mit Begleitern (Regel 5)
    baeume = []
    for ty in range(4, rows - 4):
        for tx in range(3, 76):
            if cls[ty][tx] == 'd' and rnd.random() < 0.012 and (tx, ty) not in pfad:
                o = setzen(rnd.choice(EINZELBAEUME), tx * T + 8, ty, {'spiegeln': rnd.random() < 0.5, 'baum': True}, arten='d')
                if o:
                    baeume.append(o)
    for o in baeume:
        kx, ky = o['kachel']
        if not [p for p in objekte if p is not o and p.get('baum') and abs(p['kachel'][0] - kx) <= 4 and abs(p['kachel'][1] - ky) <= 3]:
            setzen(rnd.choice(BEGLEITER), (kx + rnd.choice((-1, 1))) * T + 8, ky, {'begleiter': True}, suchen=True, arten='dg')
            setzen(rnd.choice(BEGLEITER[:3]), (kx + rnd.choice((-2, 2))) * T + 8, ky + 1, {}, arten='d')
    # 4b) Bergwand oben, links, rechts, unten: duestere Baeume, Buesche, Felsen auf der Bergkuppe (nicht leer)
    oben5 = [(tx, ty) for ty in range(rows) for tx in range(cols)
             if lvl[min(lvl.shape[0] - 1, ty * T + 15), tx * T + 8] == 5 and lvl[ty * T + 4, tx * T + 8] == 5]
    rnd.shuffle(oben5)
    n5 = 0
    for (tx, ty) in oben5:
        if n5 >= 70:
            break
        name_ = rnd.choice(BERG_OBJ)
        if any(o['basis'] == name_ and abs(o['kachel'][0] - tx) <= 3 and abs(o['kachel'][1] - ty) <= 3 for o in objekte):
            continue
        if setzen(name_, tx * T + 8, ty, {'spiegeln': rnd.random() < 0.5, 'baum': 'wald/0' in name_ or 'baeume' in name_}):
            n5 += 1
    # 5) Kleinkram: Moorrand, Waldboden, Schlamm, Puppen-Reste (unregelmaessig, sparsam, nie auf dem Pfad)
    moor_nah = lambda tx, ty: any(cls[yy][xx] == 'x' for yy in range(max(0, ty - 1), min(rows, ty + 2))
                                  for xx in range(max(0, tx - 1), min(cols, tx + 2)))
    for (streu, arten, anzahl, bed) in ((MOOR_RAND, 'd', 14, moor_nah), (WALD_STREU, 'g', 18, None),
                                        (LAND_STREU, 'd', 46, None), (PUPPEN_STREU, 'd', 14, None)):
        namen, gew = list(streu), list(streu.values())
        n = 0
        for _ in range(9000):
            if n >= anzahl:
                break
            tx, ty = rnd.randrange(3, 76), rnd.randrange(4, rows - 4)
            if cls[ty][tx] not in arten or (tx, ty) in pfad or (bed and not bed(tx, ty)):
                continue
            name_ = rnd.choices(namen, weights=gew)[0]
            if any(o['basis'] == name_ and abs(o['kachel'][0] - tx) <= 5 and abs(o['kachel'][1] - ty) <= 5 for o in objekte):
                continue                                        # keine gleichen Objekte nebeneinander (keine Reihen)
            if setzen(name_, tx * T + 8, ty, {'spiegeln': rnd.random() < 0.4}, arten=arten):
                n += 1
    # 5) Nachlauf: jeder Begleiter gegen alle Baeume (auch spaeter gesetzte) - sonst seitlich umsetzen oder weglassen
    for o in [o for o in objekte if o.get('begleiter')]:
        objekte.remove(o)
        if baum_ok(o['datei'], o['x'], o['y']):
            objekte.append(o)
            continue
        kx, ky = o['kachel']
        for (dx, dy) in sorted(((dx, dy) for dx in range(-3, 4) for dy in range(-1, 3) if dx or dy),
                               key=lambda d: abs(d[0]) + abs(d[1])):
            tx, ty = kx + dx, ky + dy
            if not (0 <= tx < cols and 0 <= ty < rows) or cls[ty][tx] not in 'dgqv' or (tx, ty) in gesperrt:
                continue
            x = raster_x(alpha[o['datei']], tx * T + 8)
            y = (ty + 1) * T - 1 - int(np.nonzero(alpha[o['datei']].any(axis=1))[0].max())
            if bewerten(lvl, alpha[o['datei']], x, y) and frei_px(o['datei'], x, y) and baum_ok(o['datei'], x, y):
                o.update(x=x, y=y, kachel=[tx, ty])
                objekte.append(o)
                break
        else:
            print('  Begleiter weggelassen (laege auf Baum):', o['basis'], (kx, ky))
    json.dump(objekte, open(os.path.join(OBJ, 'platzierung.json'), 'w'), indent=0)
    print(len(objekte), 'Objekte gesetzt')


def symmetrie():
    """Paare exakt spiegelsymmetrisch: 'symm' zur senkrechten Achse (Plattform bzw. Platz), 'symm_y' zur
    waagerechten Brueckenachse; 'achse' genau auf die Achse."""
    pf = os.path.join(OBJ, 'platzierung.json')
    objs = json.load(open(pf))
    achsen = {'a1': ACHSE_A, 'a2': ACHSE_A, 'a3': ACHSE_A, 'p1': ACHSE_PL, 'p2': ACHSE_PL}
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
            neu['x'] = ps[0]['x'] + (1 if ps[0]['x'] < achsen.get(name, ACHSE_A) else -1)
        if len(ps) != 2:
            print('  Paar unvollstaendig:', name, len(ps))
            continue
        l, r = sorted(ps, key=lambda o: o['x'])
        achse = achsen.get(name, ACHSE_A)
        a_ = np.array(Image.open(os.path.join(OBJ, l['datei'])).getchannel('A')) > 128
        xs_ = np.nonzero(a_.any(axis=0))[0]
        m_ = (xs_.min() + xs_.max() + 1) / 2.0
        r['x'] = int(round(2 * achse - (l['x'] + m_) - m_))
        r['y'] = l['y']
        if l['datei'] == r['datei']:                         # spiegelverkehrt: rechter Partner ist das Spiegelbild
            d_ = l['datei'].replace('.png', '_m.png') if not l['datei'].endswith('_m.png') else l['datei'].replace('_m.png', '.png')
            if not os.path.exists(os.path.join(OBJ, d_)):
                Image.open(os.path.join(OBJ, l['datei'])).transpose(Image.FLIP_LEFT_RIGHT).save(os.path.join(OBJ, d_))
            r['datei'] = d_
            a2 = np.array(Image.open(os.path.join(OBJ, d_)).getchannel('A')) > 128
            xs2 = np.nonzero(a2.any(axis=0))[0]
            r['x'] = int(round(2 * achse - (l['x'] + m_) - (xs2.min() + xs2.max() + 1) / 2.0))
    for name, ps in paare_y.items():
        if len(ps) == 1:                                     # fehlender Partner: an der Brueckenachse gespiegelt
            o0 = ps[0]
            neu = dict(o0)
            a_ = np.array(Image.open(os.path.join(OBJ, o0['datei'])).getchannel('A')) > 128
            zu_ = int(np.nonzero(a_.any(axis=1))[0].max())
            fuss = o0['y'] + zu_
            neu['y'] = int(2 * ACHSE_AY - fuss) - zu_ + (T if fuss < ACHSE_AY else -T)
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
