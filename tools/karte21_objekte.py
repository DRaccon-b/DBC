"""Objekte fuer Karte 21 (Digi-Egg Valley, A02) - Platzierungslogik wie Karte 20 / Karte 06.

  python3 tools/karte21_objekte.py && python3 tools/karte21_bauen.py

Schritt 1: Baeume. Waldrand ringsum mit den Baeumen von Karte 01 (wie Karte 20), auf der Wiese einzelne Baeume und
Baumpaare an den Stellen der Vorlage. Jedes Objekt im kleinsten Kachelblock, unten buendig, waagerecht zentriert.
"""
import json, math, os, random, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
import bauwerke

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte21')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte21')
T = 16
FREMD = {}
for i in range(16):
    FREMD['k01/baum%02d' % i] = 'karte01/baeume/%02d.png' % i
for i in range(64):
    FREMD['k01/deko%02d' % i] = 'karte01/deko/%02d.png' % i
WALD = ['k01/baum%02d' % i for i in (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 12, 13, 14)]
FELS_KLEIN = ['k01/deko08', 'k01/deko10']                    # kleiner Stein, Kiesel
FELS_GROSS = ['k01/deko09', 'k01/deko11']                    # bemooste Felsen
BLUMEN = ['k01/deko%02d' % i for i in (0, 1, 2, 3, 4, 27, 30)]
# vor dem Stumpf nur Objekte, die 2 Kacheln hoch sind (Nutzer): bemooste Felsen, Blumenbusch, Bluetenbusch, Loewenzahn;
# sie stehen eine Kachel tiefer, sodass nur ihre oberste Kachel den Stumpf ueberdeckt
HOCH_FELS = ['k01/deko09', 'k01/deko11']
HOCH_BLUME = ['k01/deko04', 'k01/deko27', 'k01/deko30']

# Baeume auf der Wiese nach der Vorlage: (sprite, Kachel-x der Fussmitte, Fusszeile, Optionen)
FEST = [
    # oberhalb des Flusses
    ('k01/baum01', 27, 14, {}), ('k01/baum01', 59, 14, {'spiegeln': True}),
    ('k01/baum00', 8, 20, {}), ('k01/baum02', 9, 26, {}),
    ('k01/baum00', 74, 18, {'spiegeln': True}), ('k01/baum02', 81, 21, {}), ('k01/baum00', 83, 26, {}),
    ('k01/baum01', 78.5, 29, {}), ('k01/baum03', 81, 29, {'spiegeln': True}),
    # unterhalb des Flusses: Paare
    ('k01/baum00', 9, 37, {}), ('k01/baum01', 26.5, 37, {}), ('k01/baum02', 29, 37, {'spiegeln': True}),
    ('k01/baum02', 60.5, 37, {}), ('k01/baum01', 63, 37, {'spiegeln': True}),
    ('k01/baum00', 79.5, 37, {}), ('k01/baum03', 82, 37, {}),
    # mittlere Ebene vor der Burgmauer
    ('k01/baum01', 9, 53, {}), ('k01/baum00', 64, 50, {'spiegeln': True}), ('k01/baum02', 83, 53, {}),
]


def main():
    rnd = random.Random(21)
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cls = lay['klassen']
    cols, rows = lay['groesse']
    for name, quelle in FREMD.items():
        ziel = os.path.join(OBJ, name + '.png')
        q = os.path.join(ROOT, 'assets', 'objekte', quelle)
        if os.path.exists(q):
            os.makedirs(os.path.dirname(ziel), exist_ok=True)
            shutil.copy(q, ziel)
    belegt, objekte, gesperrt = {}, [], set()
    for ty in range(rows):                                         # Fluss: keine Baumfuesse im oder direkt am Wasser
        for tx in range(cols):
            if cls[ty][tx] in 'xb':
                for dy in (-2, -1, 0, 1):
                    gesperrt.add((tx, ty + dy))
    mk = lay['mauer_kante']                                       # Burgmauer, Treppen und Tor frei halten
    for x in range(cols):
        for y in range(mk, mk + 5):
            if cls[y][x] != 'h':
                gesperrt.add((x, y))
    for tp in lay['teleporter']:
        for y in range(tp['y'] - 1, tp['y'] + tp['h'] + 1):
            for x in range(tp['x'] - 1, tp['x'] + tp['b'] + 1):
                gesperrt.add((x, y))
    cache = {}

    def boden(tx, ty):
        k = cls[min(rows - 1, max(0, ty))][min(cols - 1, max(0, tx))]
        return 'sand' if k in 'wfe' else 'beton' if k in 'pqmto' else 'gras'

    def setze(name, fx, fy, opt, frei=False, wald=False):
        opt = dict(opt)
        spiegeln = opt.pop('spiegeln', False)
        flach = name.startswith('k01/deko')
        tx, ty = int(math.floor(fx)), int(fy)
        if frei:
            if (tx, ty) in gesperrt or (tx, ty, flach) in belegt:
                return False
            if not flach and not wald and any((tx + dx, ty + dy, False) in belegt for dx in (-1, 0, 1) for dy in (-1, 0, 1)):
                return False
        b = boden(tx, ty)
        key = (name, b, spiegeln)
        if key not in cache:
            sp = Image.open(os.path.join(OBJ, name + '.png')).convert('RGBA')
            if spiegeln:
                sp = sp.transpose(Image.FLIP_LEFT_RIGHT)
            aa = np.array(sp.getchannel('A')) > 0
            ys, xs = np.nonzero(aa)
            ux0, uy0, ux1, uy1 = int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())
            art = 'baum' if 'baum' in name or 'kirsche' in name else 'klein' if flach else 'stein'
            ohne_fuss = name in ('k01/laterne', 'k06/tv_treppe') or name.startswith(('k07/gemuese', 'beet/'))
            v = sp if ohne_fuss else bauwerke.bodenfuss(sp, b, art)
            off = 0 if ohne_fuss else 2
            datei = 'varianten/%s_%s%s.png' % (name.replace('/', '-'), b, '_m' if spiegeln else '')
            os.makedirs(os.path.join(OBJ, 'varianten'), exist_ok=True)
            v.save(os.path.join(OBJ, datei))
            cache[key] = (datei, v.height, ux0 + off, uy0, ux1 + off, uy1)
        datei, h, ux0, uy0, ux1, uy1 = cache[key]
        bw, bh = ux1 - ux0 + 1, uy1 - uy0 + 1
        wt, ht = math.ceil(bw / T), math.ceil(bh / T)
        bx = int(round(fx + 0.5 - wt / 2.0))
        o = {'datei': datei, 'basis': name, 'x': bx * T + (wt * T - bw) // 2 - ux0, 'y': (ty + 1) * T - 1 - uy1,
             'fuss': h, 'kachel': [tx, ty], 'block': [bx, ty - ht + 1, wt, ht], 'ebene': 0 if flach else 1}
        px_, py_ = opt.pop('px', None), opt.pop('py', None)
        if px_ is not None:                                      # pixelgenaue Lage (Beetpflanzen)
            o['x'] = px_ - (ux0 + bw // 2)
            o['y'] = py_ - uy1
        o.update(opt)
        objekte.append(o)
        belegt[(tx, ty, flach)] = True
        for x in range(bx, bx + wt):
            for y in range(ty - ht + 1, ty + 1):
                gesperrt.add((x, y))
        return True

    for (name, fx, fy, opt) in FEST:
        setze(name, fx, fy, opt)
    # Begleiter der Wiesenbaeume (Regel 5, nur Baeume in der Karte, nicht am Waldrand):
    # Fels vor dem Stamm (ueberdeckt den Sockel), Fels hinter den Blaettern (eine Reihe hoeher, die Krone verdeckt
    # ihn teilweise), Blumen an den Sockelecken
    baeume = [o for o in objekte if o['basis'].startswith('k01/baum')]
    for i, b in enumerate(baeume):
        bx, by, wt, ht = b['block']
        cx, fy = bx * T + wt * T // 2, (by + ht) * T - 1
        seite = -1 if i % 2 else 1
        art = i % 3
        if art == 0:                                             # ueber dem Stumpf: hoher Fels
            setze(rnd.choice(HOCH_FELS), cx / T, fy // T + 1, {'px': cx + seite * 5, 'py': fy + T})
        elif art == 1:                                           # hinter den Blaettern
            setze(rnd.choice(FELS_GROSS), cx / T, fy // T - 1, {'px': cx + seite * 8, 'py': fy - 7})
        else:                                                    # hinter den Blaettern + hohe Blume ueber dem Stumpf
            setze(rnd.choice(FELS_GROSS), cx / T, fy // T - 1, {'px': cx + seite * 9, 'py': fy - 7})
            setze(rnd.choice(HOCH_BLUME), cx / T, fy // T + 1, {'px': cx - seite * 5, 'py': fy + T, 'anim': 'wehen'})
            continue
        setze(rnd.choice(HOCH_BLUME), cx / T, fy // T, {'px': cx - seite * 17, 'py': fy + 3, 'anim': 'wehen'})
    # Felsen und Blumen frei auf der Wiese (nicht an Wegen, Wasser, Platz oder Mauer)
    def frei_gras(tx, ty):
        return all(cls[min(rows - 1, max(0, ty + dy))][min(cols - 1, max(0, tx + dx))] == 'g'
                   for dx in (-1, 0, 1) for dy in (-1, 0, 1))
    for liste, ziel in ((FELS_KLEIN + FELS_GROSS, 16), (BLUMEN, 40)):
        n = 0
        for _ in range(5000):
            if n >= ziel:
                break
            tx, ty = rnd.randrange(3, cols - 3), rnd.randrange(3, rows - 3)
            if not frei_gras(tx, ty):
                continue
            n_ = rnd.choice(liste)
            if setze(n_, tx, ty, {'anim': 'wehen'} if n_ in BLUMEN else {}, frei=True):
                n += 1
    for ty in range(rows):                                       # Waldrand wie Karte 06
        for tx in range(cols):
            if cls[ty][tx] == 'h' and (tx + ty) % 2 == 0:
                setze(rnd.choice(WALD), tx, ty, {'spiegeln': rnd.random() < 0.5}, frei=True, wald=True)
    json.dump(objekte, open(os.path.join(OBJ, 'platzierung.json'), 'w'), indent=0)
    print(len(objekte), 'Objekte am Raster')


if __name__ == '__main__':
    main()
