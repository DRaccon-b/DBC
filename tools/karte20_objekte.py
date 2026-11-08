"""Objekte fuer Karte 20 (A02-Startdorf) - Stil und Platzierungslogik wie Karte 06 (Primary Village).

  python3 tools/karte20_objekte.py && python3 tools/karte20_bauen.py

Jedes Objekt belegt den kleinsten Kachelblock, in den sein Umriss passt: unten buendig auf der Kachelkante,
waagerecht zentriert, Fussmitte auf der angegebenen Kachel (Positionen nach der Vorlage). Bodenfuss nach Untergrund.
Wiederverwendet: Fernseher mit Treppe (Karte 06, exakt derselbe), Baeume/Kirschbaum/Laternen/Deko (Karte 01),
Marktstand (Karte 06), Gemuese (Karte 07), Fass/Bank/Saecke (Karte 10).
Neu (PixelLab Objekt-Creator k20_*): Strohdachhaus, Windmuehle, Heuballen, Vogelscheuche, Anschlagbrett, Brunnen,
Schubkarre, Holzstapel, Fasser.
"""
import json, math, os, random, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
import bauwerke

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte20')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte20')
T = 16
FREMD = {
    'k06/tv_treppe': 'karte06/front_gebaeude/tv_treppe.png', 'k06/stand': 'karte06/stand/00.png', 'k03/stand': 'karte03/mittel/09.png',
    'k06/schild': 'karte06/front_mittel/08.png', 'k06/kiste': 'karte06/front_mittel/15.png',
    'k01/laterne': 'karte01/laterne.png', 'k01/kirsche': 'karte01/gross/01.png',
    'k10/bank': 'karte10/spielplatz/03.png', 'k10/faesser': 'karte10/bahn2/09.png', 'k10/saecke': 'karte10/bahn2/03.png',
    'k10/milch': 'karte10/bahn2/02.png',
}
for i in range(16):
    FREMD['k01/baum%02d' % i] = 'karte01/baeume/%02d.png' % i
    FREMD['k07/gemuese%02d' % i] = 'karte07/obst2/%02d.png' % i
for i in range(4, 62):
    FREMD['k01/deko%02d' % i] = 'karte01/deko/%02d.png' % i
WALD = ['k01/baum%02d' % i for i in (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 12, 13, 14)]
DEKO = ['k01/deko%02d' % i for i in (5, 6, 8, 10, 14, 26, 27, 31, 33)]
DEKO_PFLANZE = {'k01/deko05', 'k01/deko06', 'k01/deko26', 'k01/deko27'}
HAUS, MUEHLE = 'haus/00', 'muehle/00'
HEU, VOGEL, BRETT, BRUNNEN = 'klein/00', 'klein/01', 'klein/02', 'klein/03'
SCHUBKARRE, HOLZ, FASS2 = 'klein/06', 'klein/05', 'klein/13'
ACHSE = 28.0                                   # Achse des Dorfplatzes (Kacheln)

# (sprite, Kachel-x der Fussmitte, Fusszeile, Optionen)
FEST = [
    # Fernseher (exakt wie Karte 06) und Haeuser
    ('k06/tv_treppe', 9.0, 17, {'anim': 'portal'}),
    (HAUS, 5.5, 7, {}), (HAUS, 26.0, 10, {}), (HAUS, 34.0, 10, {'spiegeln': True}), (HAUS, 8.5, 29, {'spiegeln': True}),
    # Dorfplatz: Brunnen auf dem Rasen, Laternen und Baenke paarweise zur Achse, Marktstaende unten
    (BRUNNEN, ACHSE - 0.5, 21, {}),
    ('k01/laterne', ACHSE - 6.5, 15, {'anim': 'laterne'}), ('k01/laterne', ACHSE + 5.5, 15, {'anim': 'laterne'}),
    ('k01/laterne', ACHSE - 6.5, 26, {'anim': 'laterne'}), ('k01/laterne', ACHSE + 5.5, 26, {'anim': 'laterne'}),
    ('k10/bank', ACHSE - 3.5, 16, {}), ('k10/bank', ACHSE + 2.5, 16, {}),
    ('k06/stand', ACHSE - 3.5, 28, {}), ('k03/stand', ACHSE + 2.5, 28, {}),
    ('k10/faesser', ACHSE - 7.5, 28, {}), ('k10/saecke', ACHSE + 6.5, 28, {}),
    (BRETT, 19.5, 17, {}),
    # Kirschbaeume (rosa) und gruene Baeume nach der Vorlage
    ('k01/kirsche', 20.5, 23, {'anim': 'wehen'}), ('k01/kirsche', 35.5, 23, {'anim': 'wehen'}),
    ('k01/kirsche', 19.5, 32, {'anim': 'wehen'}), ('k01/kirsche', 35, 39, {'anim': 'wehen'}),
    ('k01/kirsche', 53, 40, {'anim': 'wehen'}), ('k01/kirsche', 41, 9, {'anim': 'wehen'}),
    ('k01/baum01', 13, 9, {}), ('k01/baum00', 5, 21, {}), ('k01/baum02', 11, 26, {}), ('k01/baum01', 4, 27, {}),
    ('k01/baum03', 17, 31, {}), ('k01/baum00', 24, 32, {}), ('k01/baum02', 39, 36, {}), ('k01/baum00', 37, 41, {}),
    ('k01/baum01', 49, 41, {}), ('k01/baum02', 45, 3, {}), ('k01/baum03', 23, 9, {}),
    # Felder: Windmuehle, Heu, Vogelscheuchen, Gemuese
    (MUEHLE, 48, 34, {}),
    (HEU, 44, 31, {}), (HEU, 55, 31, {}), (HEU, 56, 4, {}), (HEU, 8, 37, {}), (HEU, 7, 43, {}),
    (VOGEL, 9, 39, {}), (VOGEL, 13, 39, {}), (VOGEL, 17, 39, {}), (VOGEL, 11, 42, {}), (VOGEL, 15, 42, {}),
    (VOGEL, 19, 42, {}), (VOGEL, 47, 21, {}),
    (SCHUBKARRE, 54, 35, {}), (HOLZ, 56, 26, {}),
    # Plateau oben rechts: Baenke links und rechts vom Weg, Wegweiser
    ('k10/bank', 45.5, 6, {}), ('k10/bank', 54.5, 6, {}), ('k06/schild', 47.5, 8, {}),
    # Wegweiser am Fernseher
    ('k06/schild', 11.5, 23, {}),
]
for x in range(43, 52, 2):                                   # Moehren im oberen Beet
    FEST.append(('k07/gemuese04', x, 18, {}))
for x in (43, 45):                                           # Kohl links unten
    for y in (23, 25):
        FEST.append(('k07/gemuese01', x, y, {}))
for x in (49, 51):                                           # Weizen rechts unten
    for y in (23, 25):
        FEST.append(('k07/gemuese10', x, y, {'anim': 'wehen'}))


def main():
    rnd = random.Random(20)
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
    for rect in (lay['acker_zaun'], lay['feld_zaun']):          # Zaeune frei halten (Kachel innen und aussen)
        x0, y0, x1, y1 = rect
        for x in range(x0 - 1, x1 + 2):
            for d in (-1, 0, 1):
                gesperrt |= {(x, y0 + d), (x, y1 + d)}
        for y in range(y0 - 1, y1 + 2):
            for d in (-1, 0, 1):
                gesperrt |= {(x0 + d, y), (x1 + d, y)}
    for tp in lay['teleporter']:
        for y in range(tp['y'] - 1, tp['y'] + tp['h'] + 1):
            for x in range(tp['x'] - 1, tp['x'] + tp['b'] + 1):
                gesperrt.add((x, y))
    cache = {}

    def boden(tx, ty):
        k = cls[min(rows - 1, max(0, ty))][min(cols - 1, max(0, tx))]
        return 'sand' if k in 'wfe' else 'beton' if k in 'p' else 'gras'

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
            ohne_fuss = name in ('k01/laterne', 'k06/tv_treppe')
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
        o.update(opt)
        objekte.append(o)
        belegt[(tx, ty, flach)] = True
        for x in range(bx, bx + wt):
            for y in range(ty - ht + 1, ty + 1):
                gesperrt.add((x, y))
        return True

    for (name, fx, fy, opt) in FEST:
        setze(name, fx, fy, opt)
    for ty in range(rows):                                       # Waldrand wie Karte 06
        for tx in range(cols):
            if cls[ty][tx] == 'h' and (tx + ty) % 2 == 0:
                setze(rnd.choice(WALD), tx, ty, {'spiegeln': rnd.random() < 0.5}, frei=True, wald=True)
    n = 0
    for _ in range(4000):                                        # Deko auf Gras
        if n >= 90:
            break
        tx, ty = rnd.randrange(3, cols - 3), rnd.randrange(3, rows - 3)
        if cls[ty][tx] not in 'go':
            continue
        n_ = rnd.choice(DEKO)
        if setze(n_, tx, ty, {'anim': 'wehen'} if n_ in DEKO_PFLANZE and rnd.random() < 0.6 else {}, frei=True):
            n += 1
    json.dump(objekte, open(os.path.join(OBJ, 'platzierung.json'), 'w'), indent=0)
    print(len(objekte), 'Objekte am Raster')


if __name__ == '__main__':
    main()
