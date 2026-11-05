"""Objekte fuer Karte 06 (Startkarte) - alle am 16x16-Raster.

  python3 tools/karte06_objekte.py && python3 tools/karte06_bauen.py

Jedes Objekt belegt den kleinsten Kachelblock, in den sein Umriss passt: unten buendig auf der Kachelkante,
waagerecht zentriert, Fussmitte auf der angegebenen Kachel. Bodenfuss (Halme/Sandwall/Schmutz) nach Untergrund.
Wiederverwendet: Baeume, Laternen, Deko aus Karte 01; Zahnraeder und Schrott aus Karte 04; Server/Antenne aus
Karte 03.
"""
import json, math, os, random, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
import bauwerke

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte06')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte06')
T = 16
FREMD = {  # Sprites aus anderen Karten
    'k01/laterne': 'karte01/laterne.png', 'k01/kirsche': 'karte01/gross/01.png',
    'k04/zahnrad': 'karte04/gross/00.png', 'k04/zahnrad_klein': 'karte04/mittel/06.png',
    'k04/schrott': 'karte04/mittel/14.png', 'k03/server': 'karte03/gross/13.png',
    'k03/antenne': 'karte03/gross2/00.png',
}
for i in range(16):
    FREMD['k01/baum%02d' % i] = 'karte01/baeume/%02d.png' % i
for i in range(4, 62):
    FREMD['k01/deko%02d' % i] = 'karte01/deko/%02d.png' % i
WALD = ['k01/baum%02d' % i for i in (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 12, 13, 14)]
DEKO = ['k01/deko%02d' % i for i in (5, 6, 8, 10, 14, 26, 27, 31, 33)]

# (sprite, Kachel-x der Fussmitte, Fusszeile, Optionen)
FEST = [
    # obere Reihe
    ('front_gebaeude/00', 9.5, 14, {'anim': 'portal'}), ('front_gebaeude/01', 21.5, 12, {}), ('front_gebaeude/02', 33.5, 12, {}),
    ('front_gebaeude/03', 44.5, 13, {}), ('portal/00', 58.5, 18, {'anim': 'portal'}),
    ('k04/zahnrad', 39, 12, {}), ('front_mittel/13', 37, 14, {}), ('front_mittel/12', 30, 14, {}),
    # Brunnenplatz mit Laternenkranz
    ('brunnen/00', 35.5, 37, {'anim': 'brunnen'}),
    ('k01/laterne', 28, 26, {'anim': 'laterne'}), ('k01/laterne', 43, 26, {'anim': 'laterne'}),
    ('k01/laterne', 28, 35, {'anim': 'laterne'}), ('k01/laterne', 43, 35, {'anim': 'laterne'}),
    ('k01/laterne', 31, 25, {'anim': 'laterne'}), ('k01/laterne', 40, 25, {'anim': 'laterne'}),
    ('k01/laterne', 31, 36, {'anim': 'laterne'}), ('k01/laterne', 40, 36, {'anim': 'laterne'}),
    # Laternen an den Wegen
    ('k01/laterne', 12, 20, {'anim': 'laterne'}), ('k01/laterne', 24, 20, {'anim': 'laterne'}),
    ('k01/laterne', 36, 20, {'anim': 'laterne'}), ('k01/laterne', 47, 20, {'anim': 'laterne'}),
    ('k01/laterne', 56, 18, {'anim': 'laterne'}), ('k01/laterne', 61, 18, {'anim': 'laterne'}),
    ('k01/laterne', 61, 28, {'anim': 'laterne'}), ('k01/laterne', 66, 28, {'anim': 'laterne'}),
    ('k01/laterne', 48, 40, {'anim': 'laterne'}), ('k01/laterne', 17, 39, {'anim': 'laterne'}),
    # Marktstand, Wegweiser
    ('stand/00', 34.5, 42, {}), ('front_mittel/08', 67, 28, {}), ('front_mittel/08', 22, 40, {}),
    # Pension
    ('front_gross/00', 10.5, 46, {}), ('datenbaum/klein', 18.5, 51, {'anim': 'daten'}),
    ('front_mittel/09', 14, 53, {}), ('front_mittel/10', 23, 53, {}), ('front_mittel/11', 18.5, 53, {}),
    ('front_mittel/04', 24.5, 45, {}), ('front_mittel/00', 24.5, 50, {}), ('front_mittel/01', 9, 53, {}),
    # Cyber-Datenplatz
    ('front_mittel/05', 53, 43, {'anim': 'leuchten'}), ('front_mittel/05', 55, 43, {'anim': 'leuchten'}),
    ('front_mittel/05', 57, 43, {'anim': 'leuchten'}), ('k03/server', 61, 44, {'anim': 'leuchten'}),
    ('k03/antenne', 64.5, 44, {}), ('front_mittel/06', 53, 48, {'anim': 'leuchten'}),
    ('front_mittel/07', 54, 52, {'anim': 'glitzern'}), ('front_mittel/03', 64, 52, {}), ('front_mittel/02', 64, 48, {}),
    # Kirschbaeume
    ('k01/kirsche', 15, 10, {'anim': 'wehen'}), ('k01/kirsche', 28, 18, {'anim': 'wehen'}),
    ('k01/kirsche', 51, 17, {'anim': 'wehen'}), ('k01/kirsche', 66, 18, {'anim': 'wehen'}),
    ('k01/kirsche', 30, 45, {'anim': 'wehen'}), ('k01/kirsche', 49, 55, {'anim': 'wehen'}),
    ('k01/kirsche', 13, 28, {'anim': 'wehen'}),
]


def main():
    rnd = random.Random(6)
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cls = lay['klassen']
    cols, rows = lay['groesse']
    for name, quelle in FREMD.items():
        ziel = os.path.join(OBJ, name + '.png')
        q = os.path.join(ROOT, 'assets', 'objekte', quelle)
        if os.path.exists(q) and not os.path.exists(ziel):
            os.makedirs(os.path.dirname(ziel), exist_ok=True)
            shutil.copy(q, ziel)
    belegt = {}
    objekte = []
    gesperrt = set()
    x0, y0, x1, y1 = lay['pension']
    for x in range(x0, x1 + 1):
        gesperrt |= {(x, y0), (x, y1)}
    for y in range(y0, y1 + 1):
        gesperrt |= {(x0, y), (x1, y)}
    sx0, sy0, sx1, sy1 = lay['steg']
    for y in range(sy0 - 1, sy1 + 2):
        for x in range(sx0 - 1, sx1 + 2):
            gesperrt.add((x, y))
    for tp in lay['teleporter']:
        for y in range(tp['y'] - 1, tp['y'] + tp['h'] + 1):
            for x in range(tp['x'] - 1, tp['x'] + tp['b'] + 1):
                gesperrt.add((x, y))
    cache = {}

    def boden(tx, ty):
        k = cls[min(rows - 1, max(0, ty))][min(cols - 1, max(0, tx))]
        return 'sand' if k in 'ws' else 'beton' if k in 'pc' else 'gras'

    def setze(name, fx, fy, opt, frei=False, wald=False):
        """fx: Kachel-x der Fussmitte (x.5 = Fuss zwischen zwei Spalten fuer gerade Blockbreiten), fy: Fusszeile."""
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
            v = bauwerke.bodenfuss(sp, b, art) if name != 'k01/laterne' else sp
            off = 2 if name != 'k01/laterne' else 0
            datei = 'varianten/%s_%s%s.png' % (name.replace('/', '-'), b, '_m' if spiegeln else '')
            os.makedirs(os.path.join(OBJ, 'varianten'), exist_ok=True)
            v.save(os.path.join(OBJ, datei))
            cache[key] = (datei, v.height, ux0 + off, uy0, ux1 + off, uy1)
        datei, h, ux0, uy0, ux1, uy1 = cache[key]
        bw, bh = ux1 - ux0 + 1, uy1 - uy0 + 1
        wt, ht = math.ceil(bw / T), math.ceil(bh / T)
        bx = int(round(fx + 0.5 - wt / 2.0))                     # linke Blockspalte (fx = Fussmitte in Kacheln)
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
    # Waldrand: Baeume auf jeder zweiten Waldkachel (versetzt), ohne Animation
    for ty in range(rows):
        for tx in range(cols):
            if cls[ty][tx] == 'h' and (tx + ty) % 2 == 0:
                setze(rnd.choice(WALD), tx, ty, {'spiegeln': rnd.random() < 0.5}, frei=True, wald=True)
    # Deko auf Gras
    n = 0
    for _ in range(4000):
        if n >= 110:
            break
        tx, ty = rnd.randrange(4, cols - 4), rnd.randrange(4, rows - 4)
        if cls[ty][tx] != 'g':
            continue
        if setze(rnd.choice(DEKO), tx, ty, {'anim': 'wehen'} if rnd.random() < 0.4 else {}, frei=True):
            n += 1
    json.dump(objekte, open(os.path.join(OBJ, 'platzierung.json'), 'w'), indent=0)
    print(len(objekte), 'Objekte am Raster')


if __name__ == '__main__':
    main()
