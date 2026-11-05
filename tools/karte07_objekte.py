"""Objekte fuer Karte 07 (The Holy Peaks) - am 16x16-Raster, ohne Ueberlappungen.

  python3 tools/karte07_objekte.py && python3 tools/karte07_bauen.py

Jedes Objekt im kleinsten Kachelblock (Fuss unten buendig, waagerecht zentriert). Bodenfuss nach Untergrund.
Freie Deko/Baeume nur, wenn sie mit 2 px Abstand nichts beruehren. Wiederverwendet: Deko aus Karte 01,
verschneite Tannen aus Karte 05.
"""
import json, math, os, random, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageFilter
import bauwerke

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte07')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte07')
T = 16
FREMD = {'k05/tanne%d' % i: 'karte05/baeume/0%d.png' % i for i in range(3)}
for i in (5, 6, 8, 10, 26, 27, 31):
    FREMD['k01/deko%02d' % i] = 'karte01/deko/%02d.png' % i
DEKO_GRAS = ['k01/deko05', 'k01/deko06', 'k01/deko26', 'k01/deko27', 'k01/deko08', 'k01/deko10']
WIND = {'k01/deko05', 'k01/deko06', 'k01/deko26', 'k01/deko27'}
SL, PL, BONSAI, BAMBUS = 'mittel/00', 'mittel/01', 'mittel/04', 'mittel/05'

FEST = [
    # Gipfel: Wirbelportal, Drachenschrein, Obelisk, Laternen
    ('mittel/12', 6.5, 7, {'anim': 'portal'}),
    ('gross/00', 89.5, 11, {}), ('mittel/02', 93, 21, {'anim': 'leuchten'}), ('mittel/09', 84, 21, {}),
    (SL, 80, 9, {}), (SL, 83, 9, {}), (SL, 80, 18, {}), (SL, 87, 18, {}), (SL, 80, 23, {}), (SL, 89, 23, {}),
    (PL, 76, 11, {'anim': 'leuchten'}), (PL, 76, 16, {'anim': 'leuchten'}), (PL, 66, 22, {'anim': 'leuchten'}),
    (PL, 59, 25, {'anim': 'leuchten'}), (PL, 21, 23, {'anim': 'leuchten'}), (PL, 27, 23, {'anim': 'leuchten'}),
    (BONSAI, 64, 6, {'anim': 'baum'}),
    ('mittel/13', 59, 39, {}), ('mittel/13', 61, 49, {}),
    # Pagodenhof
    ('pagode/00', 80, 45, {}), (BAMBUS, 73, 39, {'anim': 'wehen'}), (BAMBUS, 87, 39, {'anim': 'wehen'}),
    (SL, 73, 45, {}), (SL, 87, 45, {}), (PL, 72, 32, {'anim': 'leuchten'}), (PL, 88, 32, {'anim': 'leuchten'}),
    ('mittel/03', 87, 53, {'anim': 'glitzern'}), (PL, 76, 55, {'anim': 'leuchten'}), (PL, 82, 55, {'anim': 'leuchten'}),
    (PL, 16, 54, {'anim': 'leuchten'}), (PL, 23, 54, {'anim': 'leuchten'}),
    # untere Terrasse
    ('gross/02', 8.5, 66, {}), ('gross/02', 13.5, 79, {}), ('gross/01', 9.5, 85, {}),
    ('mittel/11', 6, 80, {}), ('mittel/15', 18, 80, {}), (SL, 5, 85, {}), (PL, 4, 78, {'anim': 'leuchten'}),
    (PL, 20, 76, {'anim': 'leuchten'}),
    ('mittel/02', 90.5, 70, {'anim': 'leuchten'}), ('gross/01', 90.5, 80, {}), ('mittel/10', 90.5, 73, {}),
    (SL, 86, 67, {}), (SL, 95, 67, {}), (BAMBUS, 86, 77, {'anim': 'wehen'}), (BAMBUS, 95, 77, {'anim': 'wehen'}),
    (PL, 86, 63, {'anim': 'leuchten'}), (PL, 95, 63, {'anim': 'leuchten'}),
    (BAMBUS, 45, 66, {'anim': 'wehen'}), (BAMBUS, 22, 70, {'anim': 'wehen'}), (BAMBUS, 6, 72, {'anim': 'wehen'}),
    (BAMBUS, 9, 72, {'anim': 'wehen'}), (BAMBUS, 12, 72, {'anim': 'wehen'}), (BAMBUS, 70, 73, {'anim': 'wehen'}),
    (PL, 48, 76, {'anim': 'leuchten'}), (PL, 44, 80, {'anim': 'leuchten'}), (PL, 67, 81, {'anim': 'leuchten'}),
    (PL, 21, 87, {'anim': 'leuchten'}),
    # Felsnadeln in den Wolken
    ('gross/03', 1.5, 30, {}), ('gross/03', 1.5, 46, {}), ('gross/03', 98.5, 22, {}), ('gross/03', 98.5, 56, {}),
    ('gross/03', 70.5, 26, {}), ('gross/03', 30.5, 89, {}), ('gross/03', 46.5, 89, {}), ('gross/03', 60.5, 89, {}),
    ('gross/03', 92.5, 89, {}), ('gross/03', 98.5, 85, {}),
]
BONSAI_PLAETZE = [(52, 35), (58, 35), (40, 40), (47, 50), (53, 51), (66, 39), (92, 34), (93, 49), (14, 68),
                  (25, 75), (89, 59), (42, 55), (35, 34)]


def main():
    rnd = random.Random(7)
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cls = lay['klassen']
    hoehe = [[int(c) for c in r] for r in lay['hoehe']]
    cols, rows = lay['groesse']
    for name, quelle in FREMD.items():
        ziel = os.path.join(OBJ, name + '.png')
        if not os.path.exists(ziel):
            os.makedirs(os.path.dirname(ziel), exist_ok=True)
            shutil.copy(os.path.join(ROOT, 'assets', 'objekte', quelle), ziel)
    W_, H_ = cols * T, rows * T
    pix = np.zeros((H_, W_), bool)
    gesperrt = set()
    for (x0, x1, y0, y1) in lay['treppen']:
        for y in range(y0 - 1, y1 + 2):
            for x in range(x0 - 1, x1 + 2):
                gesperrt.add((x, y))
    bx0, by0, bx1, by1 = lay['bruecke']
    for y in range(by0 - 1, by1 + 2):
        for x in range(bx0 - 1, bx1 + 2):
            gesperrt.add((x, y))
    for tp in lay['teleporter']:
        for y in range(tp['y'] - 1, tp['y'] + tp['h'] + 1):
            for x in range(tp['x'] - 1, tp['x'] + tp['b'] + 1):
                gesperrt.add((x, y))
    # Kanten: 3 Zeilen unter jeder Hochkante (Felsfront) und die Kante selbst freihalten
    for y in range(rows - 1):
        for x in range(cols):
            if hoehe[y][x] > hoehe[y + 1][x]:
                for k in range(0, 4):
                    gesperrt.add((x, y + k))
            for dx in (-1, 1):
                if 0 <= x + dx < cols and hoehe[y][x] != hoehe[y][x + dx]:
                    gesperrt.add((x, y))
    cache, alpha, objekte = {}, {}, []

    def boden(tx, ty):
        k = cls[min(rows - 1, max(0, ty))][min(cols - 1, max(0, tx))]
        return 'sand' if k in 'nw' else 'beton' if k in 'prf' else 'gras'

    def setze(name, fx, fy, opt, frei=False):
        opt = dict(opt)
        spiegeln = opt.pop('spiegeln', False)
        tx, ty = int(math.floor(fx)), int(fy)
        if frei and (tx, ty) in gesperrt:
            return False
        b = boden(tx, ty) if hoehe[min(rows - 1, ty)][min(cols - 1, tx)] > 0 else None
        key = (name, b, spiegeln)
        if key not in cache:
            sp = Image.open(os.path.join(OBJ, name + '.png')).convert('RGBA')
            if spiegeln:
                sp = sp.transpose(Image.FLIP_LEFT_RIGHT)
            aa = np.array(sp.getchannel('A')) > 0
            ys, xs = np.nonzero(aa)
            ux0, uy0, ux1, uy1 = int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())
            if b is None:                                      # in den Wolken: kein Bodenfuss
                v, off = sp, 0
            else:
                art = 'baum' if name in (BONSAI,) or 'tanne' in name else 'klein' if name.startswith('k01/') else 'stein'
                v, off = bauwerke.bodenfuss(sp, b, art), 2
            datei = 'varianten/%s_%s%s.png' % (name.replace('/', '-'), b or 'wolke', '_m' if spiegeln else '')
            os.makedirs(os.path.join(OBJ, 'varianten'), exist_ok=True)
            v.save(os.path.join(OBJ, datei))
            cache[key] = (datei, v.height, ux0 + off, uy0, ux1 + off, uy1)
            alpha[key] = np.array(v.getchannel('A')) >= 160
        datei, h, ux0, uy0, ux1, uy1 = cache[key]
        bw, bh = ux1 - ux0 + 1, uy1 - uy0 + 1
        wt, ht = math.ceil(bw / T), math.ceil(bh / T)
        bx = int(round(fx + 0.5 - wt / 2.0))
        ox, oy = bx * T + (wt * T - bw) // 2 - ux0, (ty + 1) * T - 1 - uy1
        ys_, xs_ = np.nonzero(alpha[key])
        ys_, xs_ = ys_ + oy, xs_ + ox
        ok = (ys_ >= 0) & (ys_ < H_) & (xs_ >= 0) & (xs_ < W_)
        ys_, xs_ = ys_[ok], xs_[ok]
        if frei and len(ys_):
            y0, y1, x0, x1 = max(0, ys_.min() - 2), ys_.max() + 3, max(0, xs_.min() - 2), xs_.max() + 3
            f = np.zeros((y1 - y0, x1 - x0), bool)
            f[ys_ - y0, xs_ - x0] = True
            f = np.array(Image.fromarray(f.astype(np.uint8) * 255).filter(ImageFilter.MaxFilter(5))) > 0
            hind = pix[y0:y1, x0:x1]
            if (f[:hind.shape[0], :hind.shape[1]] & hind).any():
                return False
        pix[ys_, xs_] = True
        o = {'datei': datei, 'basis': name, 'x': ox, 'y': oy, 'fuss': h, 'kachel': [tx, ty],
             'block': [bx, ty - ht + 1, wt, ht], 'ebene': 0 if name.startswith('k01/') else 1}
        o.update(opt)
        objekte.append(o)
        for x in range(bx, bx + wt):
            for y in range(ty - ht + 1, ty + 1):
                gesperrt.add((x, y))
        return True

    for (name, fx, fy, opt) in FEST:
        setze(name, fx, fy, opt)
    for (x, y) in BONSAI_PLAETZE:
        setze(BONSAI, x, y, {'anim': 'baum', 'spiegeln': rnd.random() < 0.5}, frei=True)
    # verschneite Tannen und Felsen auf dem Schnee, bemooste Felsen auf dem Fels
    n_s = n_f = 0
    for _ in range(4000):
        tx, ty = rnd.randrange(3, cols - 3), rnd.randrange(3, rows - 3)
        k = cls[ty][tx]
        if k == 'n' and n_s < 46 and rnd.random() < 0.5:
            n = rnd.choice(['mittel/06', 'mittel/06', 'mittel/06', 'mittel/07'])
            if setze(n, tx, ty, {'spiegeln': rnd.random() < 0.5}, frei=True):
                n_s += 1
        elif k == 'f' and n_f < 9 and rnd.random() < 0.1:
            if setze('mittel/08', tx, ty, {}, frei=True):
                n_f += 1
    n = 0
    for _ in range(3000):
        if n >= 90:
            break
        tx, ty = rnd.randrange(3, cols - 3), rnd.randrange(3, rows - 3)
        if cls[ty][tx] != 'g':
            continue
        d = rnd.choice(DEKO_GRAS)
        if setze(d, tx, ty, {'anim': 'wehen'} if d in WIND else {}, frei=True):
            n += 1
    json.dump(objekte, open(os.path.join(OBJ, 'platzierung.json'), 'w'), indent=0)
    print(len(objekte), 'Objekte am Raster')


if __name__ == '__main__':
    main()
