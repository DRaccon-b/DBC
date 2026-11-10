"""Objekte fuer Karte 23 (Harvest Hills, A02) - Platzierungslogik wie Karte 20 / 21.

  python3 tools/karte23_bauen.py   (einmal -> wand.npy)
  python3 tools/karte23_objekte.py && python3 tools/karte23_bauen.py

Schritt 1: Baeume. Waldrand ringsum (Baeume von Karte 01), Obstwiese oben links (Apfelbaeume aus PixelLab k23_mauer),
einzelne Wiesenbaeume nach der Vorlage; Begleiter nach Regel 5d (Fels vor dem Stumpf / hinter den Blaettern, Blumen).
"""
import json, math, os, random, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
import bauwerke

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte23')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte23')
T = 16
FREMD = {}
for i in range(16):
    FREMD['k01/baum%02d' % i] = 'karte01/baeume/%02d.png' % i
for i in range(64):
    FREMD['k01/deko%02d' % i] = 'karte01/deko/%02d.png' % i
FREMD['obst/apfel'] = 'karte23/mauer/48.png'
FREMD['turm/00_rand'] = 'karte20/turm/00_rand.png'            # Windmuehle von Karte 20 (Fluegel werden je Bild gezeichnet)
SCHEUNE, SILO, MUEHLE = 'scheune/00', 'scheune/01', 'turm/00_rand'
GEBAEUDE = [                                                    # grosse Objekte zuerst (Positionen nach der Vorlage)
    (SCHEUNE, 6, 33, {}), (SILO, 10.5, 33, {}),                 # Hof links
    (SCHEUNE, 47, 51, {}),                                      # Mitte bei den Feldern
    (SCHEUNE, 88, 7, {}), (SILO, 93.5, 7, {}),                  # obere Terrasse rechts
    (MUEHLE, 41.5, 11, {'anim': 'muehle20'}), (MUEHLE, 58.5, 11, {'anim': 'muehle20'}),   # Plateau, symmetrisch zur Mitte
]                  # Apfelbaum (PixelLab k23_mauer)
WALD = ['k01/baum%02d' % i for i in (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 12, 13, 14)]
FELS_KLEIN = ['k01/deko08', 'k01/deko10']
FELS_GROSS = ['k01/deko09', 'k01/deko11']
BLUMEN = ['k01/deko%02d' % i for i in (0, 1, 2, 3, 4, 27, 30)]
HOCH_FELS = ['k01/deko09', 'k01/deko11']                       # Regel 5d: vor dem Stumpf nur 2 Kacheln hohe Objekte
HOCH_BLUME = ['k01/deko04', 'k01/deko27', 'k01/deko30']
OBST = 'obst/apfel'
# Obstwiese oben links (Reihen wie in der Vorlage, einzelne Luecken)
OBSTWIESE = [(x, y) for y in (8, 16, 24) for x in (4, 8, 12, 24, 28, 32)]   # groessere Baeume -> 4 Kacheln Abstand
WIESE = [(38.5, 15), (38.5, 21), (65, 8), (64, 20), (42, 30), (27, 34), (36, 33), (49, 32), (61, 31),
         (68, 30), (71, 28), (87, 28), (91, 31), (53, 41), (49, 42), (5, 50), (8, 52), (53.5, 68), (4, 74), (9, 76),
         (15, 76), (37, 78), (52, 78), (62, 78), (23, 78)]
SORTEN = {'apfel': 'obst_gross/00', 'birne': 'obst_gross/01', 'orange': 'obst_gross/02', 'pflaume': 'obst_gross/03',
          'kirsche': 'obst_gross/04'}                            # groessere Obstbaeume (Nutzer), PixelLab k23_obst_gross
def sorte(x, y):                                               # je Reihe eine Sorte (wie gepflanzt), links/rechts verschieden
    links = x < 20
    reihe = {8: 0, 16: 1, 24: 2}[y]
    return SORTEN[(('apfel', 'birne', 'kirsche') if links else ('orange', 'pflaume', 'apfel'))[reihe]]
FEST = [(sorte(x, y), x + 0.5, y, {'spiegeln': (x + y) % 2 == 0}) for (x, y) in OBSTWIESE] + \
       [('k01/baum0%d' % (i % 3), x, y, {'spiegeln': i % 2 == 0}) for i, (x, y) in enumerate(WIESE)]


def main():
    rnd = random.Random(23)
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
    wand = np.unpackbits(np.load(os.path.join(KARTE, 'wand.npy')))[:rows * T * cols * T].reshape(rows * T, cols * T).astype(bool)
    for ty in range(rows):                                         # keine Fuesse auf Wasser, Aeckern, Hecken, Mauern, Treppen,
        for tx in range(cols):                                     # Waenden, in der Senke oder direkt daneben
            if cls[ty][tx] in 'xaenttock' or wand[ty * T:(ty + 1) * T, tx * T:(tx + 1) * T].any():
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        gesperrt.add((tx + dx, ty + dy))
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
        b = opt.pop('boden', None) or boden(tx, ty)
        key = (name, b, spiegeln)
        if key not in cache:
            sp = Image.open(os.path.join(OBJ, name + '.png')).convert('RGBA')
            if spiegeln:
                sp = sp.transpose(Image.FLIP_LEFT_RIGHT)
            aa = np.array(sp.getchannel('A')) > 0
            ys, xs = np.nonzero(aa)
            ux0, uy0, ux1, uy1 = int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())
            art = 'baum' if 'baum' in name or 'kirsche' in name else 'klein' if flach else 'stein'
            ohne_fuss = name in ('k01/laterne', 'k06/tv_treppe', 'k03/teppich', 'teppich/00') or name.startswith(('k07/gemuese', 'beet/'))
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

    for (name, fx, fy, opt) in GEBAEUDE:
        setze(name, fx, fy, opt)
    for (name, fx, fy, opt) in FEST:
        setze(name, fx, fy, opt, frei=True)                      # nur wo frei (Vorlagenpositionen am Raster pruefen)
    # Begleiter der Wiesenbaeume (Regel 5, nur Baeume in der Karte, nicht am Waldrand):
    # Fels vor dem Stamm (ueberdeckt den Sockel), Fels hinter den Blaettern (eine Reihe hoeher, die Krone verdeckt
    # ihn teilweise), Blumen an den Sockelecken
    BEGLEITET = ('k01/baum',)                                 # Obstwiese: gepflanzte Reihen, keine Begleiter                              # Regel 5d gilt fuer Wiesenbaeume und Fernseher
    baeume = [o for o in objekte if o['basis'].startswith(BEGLEITET)]
    for i, b in enumerate(baeume):
        bx, by, wt, ht = b['block']
        cx, fy = bx * T + wt * T // 2, (by + ht) * T - 1
        seite = -1 if i % 2 else 1
        art = i % 3
        if b.get('nur_blume'):                                   # nur eine Blume vor dem Stumpf, kein Fels (Nutzer)
            setze(rnd.choice(HOCH_BLUME), cx / T, fy // T + 1, {'px': cx - seite * 5, 'py': fy + T, 'anim': 'wehen'})
            continue
        if b['basis'].startswith('tv'):                          # Fernseher: Begleiter nur an der Ecke (der Bildschirm bleibt frei)
            w2 = wt * T // 2
            if art == 0:
                setze(rnd.choice(HOCH_FELS), cx / T, fy // T + 1, {'px': cx + seite * (w2 + 6), 'py': fy + T})
            elif art == 1:
                setze(rnd.choice(FELS_GROSS), cx / T, fy // T - 1, {'px': cx + seite * (w2 + 2), 'py': fy - 7})
            else:
                setze(rnd.choice(HOCH_BLUME), cx / T, fy // T + 1, {'px': cx - seite * (w2 + 6), 'py': fy + T, 'anim': 'wehen'})
            continue
        if art == 0:                                             # ueber dem Stumpf: hoher Fels
            setze(rnd.choice(HOCH_FELS), cx / T, fy // T + 1, {'px': cx + seite * 5, 'py': fy + T})
            continue                                             # keine zweite Pflanze daneben (keine Ueberlappung)
        elif art == 1:                                           # hinter den Blaettern
            setze(rnd.choice(FELS_GROSS), cx / T, fy // T - 1, {'px': cx + seite * 8, 'py': fy - 7})
        else:                                                    # hinter den Blaettern + hohe Blume ueber dem Stumpf
            setze(rnd.choice(FELS_GROSS), cx / T, fy // T - 1, {'px': cx + seite * 9, 'py': fy - 7})
            setze(rnd.choice(HOCH_BLUME), cx / T, fy // T + 1, {'px': cx - seite * 5, 'py': fy + T, 'anim': 'wehen'})
            continue
        setze(rnd.choice(HOCH_BLUME), cx / T, fy // T + 1, {'px': cx - seite * 13, 'py': fy + T, 'anim': 'wehen'})
    # Neben den Baeumen (Stammreihe und Reihe darueber) nichts Freies setzen, sonst liegt es auf dem Stumpf
    for o in objekte:
        if o['basis'].startswith(BEGLEITET):
            bx, by, wt, ht = o['block']
            for x in range(bx - 1, bx + wt + 1):
                for y in (by + ht - 2, by + ht - 1, by + ht):
                    gesperrt.add((x, y))
    # Felsen und Blumen frei auf der Wiese (nicht an Wegen, Wasser, Platz oder Mauer)
    def frei_gras(tx, ty):
        return all(cls[min(rows - 1, max(0, ty + dy))][min(cols - 1, max(0, tx + dx))] == 'g'
                   for dx in (-1, 0, 1) for dy in (-1, 0, 1))
    # Obstwiese oben links: Deko auf der Wiese (Nutzer) - nichts direkt an den Obstbaeumen (Stammreihe +-1)
    for o in objekte:
        if o['basis'].startswith(('obst/', 'obst_gross/')):
            bx, by, wt, ht = o['block']
            for x in range(bx - 1, bx + wt + 1):
                for y in (by + ht - 2, by + ht - 1, by + ht):
                    gesperrt.add((x, y))
    OBST_DEKO_GROSS = [('hecke/16', 7, 12), ('hecke/08', 13, 20), ('hecke/11', 27, 12), ('mauer/28', 33, 20),
                       ('obst/61', 3, 19), ('hecke/34', 36, 4), ('obst/41', 24, 20), ('mauer/36', 10, 5)]
    for (name, x, y) in OBST_DEKO_GROSS:                       # groessere Stuecke zuerst (Kisten, Heu, Karren, Bienenstock)
        setze(name, x + 0.5, y, {'spiegeln': (x * 7 + y) % 3 == 0}, frei=True)
    KLEIN = ['k01/deko05', 'k01/deko06'] + ['k01/deko%02d' % i for i in (0, 1, 2, 3, 30)]   # ohne Buesche (Nutzer)
    n_d = 0
    for _ in range(4000):
        if n_d >= 34:
            break
        tx, ty = rnd.randrange(3, 37), rnd.randrange(3, 27)
        if 16 <= tx <= 22 or not all(cls[ty + dy][tx + dx] == 'g' for dx in (-1, 0, 1) for dy in (-1, 0, 1)):
            continue
        n_ = rnd.choice(KLEIN)
        if setze(n_, tx, ty, {'anim': 'wehen'} if n_.startswith('k01/deko0') or n_ in BLUMEN else {}, frei=True):
            n_d += 1
    for ty in range(rows):                                       # Waldrand wie Karte 06
        for tx in range(cols):
            if cls[ty][tx] == 'h' and (tx + ty) % 2 == 0:
                setze(rnd.choice(WALD), tx, ty, {'spiegeln': rnd.random() < 0.5}, frei=True, wald=True)
    json.dump(objekte, open(os.path.join(OBJ, 'platzierung.json'), 'w'), indent=0)
    print(len(objekte), 'Objekte am Raster')


if __name__ == '__main__':
    main()
