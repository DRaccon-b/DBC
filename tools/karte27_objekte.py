"""Objekte fuer Karte 27 (Destiny Lake, A02).

  python3 tools/karte27_bauen.py   (einmal -> wand.npy)
  python3 tools/karte27_objekte.py && python3 tools/karte27_bauen.py

Schritt 1: Baum-Umrandung (Waldrand wie Karte 06/23: Baeume von Karte 01 dicht auf den Waldkacheln, jede zweite
Kachel im Schachbrett) und das Wrack des Kaiser-Flaggschiffs (Karte 25) unten links.
"""
import json, math, os, random, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
import bauwerke

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte27')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte27')
T = 16
FREMD = {}
for i in range(16):
    FREMD['k01/baum%02d' % i] = 'karte01/baeume/%02d.png' % i
WALD = ['k01/baum%02d' % i for i in (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 12, 13, 14)]
WRACK = 'wrack/00_sauber'
WRACK_POS = (242, 1126)                         # Fussmitte x, Fusslinie y (px) - vor der Mauer des Plateaus unten links

# Einzelne Baeume nach der Vorlage: Stammfuss (px) und Art, aus der Vorlage gelesen (Stammfarbe, Kronenfarbe)
VORLAGE_BAEUME = [
    (462, 189, 'eiche'), (1102, 221, 'eiche'), (478, 237, 'eiche'), (1470, 253, 'eiche'),
    (1518, 349, 'eiche'), (798, 365, 'eiche'), (142, 381, 'eiche'), (1390, 429, 'eiche'),
    (1054, 477, 'eiche'), (62, 493, 'eiche'), (446, 573, 'eiche'), (494, 621, 'eiche'),
    (270, 669, 'eiche'), (1406, 669, 'eiche'), (990, 733, 'eiche'), (1390, 765, 'eiche'),
    (1006, 813, 'eiche'), (926, 861, 'eiche'), (990, 893, 'eiche'), (1022, 893, 'kirsche'),
    (910, 909, 'eiche'), (510, 925, 'eiche'), (542, 925, 'eiche'), (942, 925, 'eiche'),
    (1102, 925, 'kirsche'), (574, 941, 'eiche'), (1454, 941, 'kirsche'), (1070, 957, 'kirsche'),
    (526, 973, 'eiche'), (1438, 989, 'eiche'), (974, 1005, 'eiche'), (878, 1053, 'kirsche'),
    (1246, 1053, 'kirsche'), (1326, 1053, 'kirsche'), (830, 1069, 'kirsche'), (1038, 1085, 'kirsche'),
    (734, 1101, 'kirsche'), (990, 1101, 'eiche'), (1134, 1101, 'eiche'), (1294, 1101, 'kirsche'),
    (702, 1117, 'eiche'), (831, 1117, 'eiche'), (862, 1117, 'eiche'), (894, 1117, 'eiche'),
    (1102, 1133, 'kirsche'), (1150, 1133, 'eiche'), (814, 1149, 'eiche')]
EICHEN = ['k01/baum00', 'k01/baum01', 'k01/baum02', 'k01/baum04', 'k01/baum15']
KIRSCHE = 'k01/baum10'
FELS_GROSS = ['k01/deko09', 'k01/deko11']                       # bemooste Felsen (2 Kacheln hoch, Regel 5d)
HOCH_BLUME = ['k01/deko04', 'k01/deko27', 'k01/deko30']


def main():
    rnd = random.Random(27)
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cls = lay['klassen']
    cols, rows = lay['groesse']
    for name, quelle in FREMD.items():
        ziel = os.path.join(OBJ, name + '.png')
        os.makedirs(os.path.dirname(ziel), exist_ok=True)
        shutil.copy(os.path.join(ROOT, 'assets', 'objekte', quelle), ziel)
    wand = np.unpackbits(np.load(os.path.join(KARTE, 'wand.npy')))[:rows * T * cols * T].reshape(rows * T, cols * T).astype(bool)
    objekte, cache = [], {}

    def variante(name, spiegeln, mit_fuss=True):
        key = (name, spiegeln, mit_fuss)
        if key not in cache:
            sp = Image.open(os.path.join(OBJ, name + '.png')).convert('RGBA')
            if spiegeln:
                sp = sp.transpose(Image.FLIP_LEFT_RIGHT)
            aa = np.array(sp.getchannel('A')) > 0
            ys, xs = np.nonzero(aa)
            ux0, uy0, ux1, uy1 = int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())
            art = 'baum' if 'baum' in name else 'stein' if name in ('k01/deko09', 'k01/deko11') else 'klein'
            v = bauwerke.bodenfuss(sp, 'gras', art) if mit_fuss else sp
            off = 2 if mit_fuss else 0
            datei = 'varianten/%s%s%s.png' % (name.replace('/', '-'), '_m' if spiegeln else '', '' if mit_fuss else '_ohne')
            os.makedirs(os.path.join(OBJ, 'varianten'), exist_ok=True)
            v.save(os.path.join(OBJ, datei))
            cache[key] = (datei, v.height, ux0 + off, uy0, ux1 + off, uy1)
        return cache[key]

    # Waldrand: Baeume dicht im Schachbrett auf den Waldkacheln (Fuss auf Wald, nicht auf einer Mauerfront)
    for ty in range(rows):
        for tx in range(cols):
            if cls[ty][tx] != 'h' or (tx + ty) % 2:
                continue
            if wand[ty * T:(ty + 1) * T, tx * T:(tx + 1) * T].any():
                continue
            name = rnd.choice(WALD)
            datei, h, ux0, uy0, ux1, uy1 = variante(name, rnd.random() < 0.5)
            bw = ux1 - ux0 + 1
            wt, ht = math.ceil(bw / T), math.ceil((uy1 - uy0 + 1) / T)
            bx = int(round(tx + 0.5 - wt / 2.0))
            objekte.append({'datei': datei, 'basis': name, 'x': bx * T + (wt * T - bw) // 2 - ux0,
                            'y': (ty + 1) * T - 1 - uy1, 'fuss': h, 'kachel': [tx, ty],
                            'block': [bx, ty - ht + 1, wt, ht], 'ebene': 1, 'anim': 'baum'})
    # Wrack des Kaiser-Flaggschiffs (PixelLab Pro-Generator, Ausnahme > 256 px, Vorbild: Schiff aus Karte 25)
    if os.path.exists(os.path.join(OBJ, WRACK + '.png')):
        datei, h, ux0, uy0, ux1, uy1 = variante(WRACK, False, mit_fuss=False)
        cx, fy = WRACK_POS
        bw, bh = ux1 - ux0 + 1, uy1 - uy0 + 1
        x = cx - (ux0 + bw // 2)
        objekte.append({'datei': datei, 'basis': WRACK, 'x': x, 'y': fy - uy1, 'fuss': h, 'kachel': [cx // T, fy // T],
                        'block': [(x + ux0) // T, (fy - bh) // T, math.ceil(bw / T), math.ceil(bh / T)], 'ebene': 1})
    # Einzelne Baeume (Eichen, Kirschbaeume) nach der Vorlage, mit Begleitern nach Regel 5d
    for n in (9, 11, 4, 27, 30):
        q = os.path.join(ROOT, 'assets', 'objekte', 'karte01', 'deko', '%02d.png' % n)
        os.makedirs(os.path.join(OBJ, 'k01'), exist_ok=True)
        shutil.copy(q, os.path.join(OBJ, 'k01', 'deko%02d.png' % n))
    gesperrt = set()
    for ty in range(rows):
        for tx in range(cols):
            if cls[ty][tx] in 'xpbwTqh' or wand[ty * T:(ty + 1) * T, tx * T:(tx + 1) * T].any():
                gesperrt.add((tx, ty))
    for o in objekte:                                               # Wrack und Waldrand
        bx, by, wt, ht = o['block']
        for x in range(bx, bx + wt):
            for y in range(by, by + ht):
                gesperrt.add((x, y))

    def setze_px(name, cx, fy, opt, spiegeln=False, mit_fuss=True):
        datei, h, ux0, uy0, ux1, uy1 = variante(name, spiegeln, mit_fuss)
        bw, bh = ux1 - ux0 + 1, uy1 - uy0 + 1
        o = {'datei': datei, 'basis': name, 'x': cx - (ux0 + bw // 2), 'y': fy - uy1, 'fuss': h,
             'kachel': [cx // T, fy // T], 'block': [(cx - bw // 2) // T, (fy - bh + 1) // T, math.ceil(bw / T), math.ceil(bh / T)],
             'ebene': 1}
        o.update(opt)
        objekte.append(o)
        return o

    baeume = []
    for (cx, cy, art) in VORLAGE_BAEUME:
        tx, ty = cx // T, cy // T
        for dx, dy in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, -1)):
            ok = all((tx + dx + ex, ty + dy + ey) not in gesperrt for ex in (-1, 0, 1) for ey in (-1, 0))
            if ok:
                tx, ty = tx + dx, ty + dy
                break
        else:
            continue
        if any((abs(b['kachel'][0] - tx) < 3 and abs(b['kachel'][1] - ty) < 2) or
               (abs(b['kachel'][0] - tx) < 2 and abs(b['kachel'][1] - ty) < 4) for b in baeume):
            continue                                                # Sockel zweier Baeume ueberlappen nie (Regel 4)
        name = KIRSCHE if art == 'kirsche' else rnd.choice(EICHEN)
        b = setze_px(name, tx * T + 8, (ty + 1) * T - 1, {'anim': 'baum'}, rnd.random() < 0.5)
        b['kachel'] = [tx, ty]
        baeume.append(b)
        bx, by, wt, ht = b['block']
        for x in range(bx - 1, bx + wt + 1):                        # Stammreihe +-1 frei von anderer Deko
            for y in range(ty - 2, ty + 2):
                gesperrt.add((x, y))
    # Begleiter (Regel 5d): abwechselnd Fels vor dem Stumpf (eine Kachel tiefer), Fels hinter den Blaettern
    # (eine Reihe hoeher, wird vor dem Baum gezeichnet), oder Fels hinter den Blaettern + hohe Blume vor dem Stumpf
    for i, b in enumerate(baeume):
        tx, ty = b['kachel']
        cx, fy = tx * T + 8, (ty + 1) * T - 1
        seite = -1 if i % 2 else 1
        art = i % 3
        unten_frei = cls[min(rows - 1, ty + 1)][tx] in 'gfs' and not wand[min(rows * T - 1, fy + T), cx]
        andere = [c['kachel'] for c in baeume if c is not b]
        nah = [ax for ax, ay in andere if abs(ax - tx) <= 5 and abs(ay - ty) <= 3]
        if nah:                                                     # Begleiter auf die vom Nachbarbaum abgewandte Seite
            n0 = min(nah, key=lambda ax: abs(ax - tx))
            seite = 1 if tx >= n0 else -1
        oben_frei = not any(abs(ax - tx) <= 2 and 0 < ty - ay <= 3 for ax, ay in andere)   # kein Stamm hinter den Blaettern
        if not oben_frei:
            art = 0 if unten_frei else 3
        if art == 3:
            continue
        if art == 0 and unten_frei:
            setze_px(rnd.choice(FELS_GROSS), cx + seite * 5, fy + T, {'kachel': [tx, ty + 1]}, rnd.random() < 0.5)
        elif art == 1 or not unten_frei:
            setze_px(rnd.choice(FELS_GROSS), cx + seite * max(9, b['block'][2] * T // 2 - 2), fy - 7, {'kachel': [tx, ty - 1], 'hinter': True}, rnd.random() < 0.5)
        else:
            setze_px(rnd.choice(FELS_GROSS), cx + seite * max(9, b['block'][2] * T // 2 - 2), fy - 7, {'kachel': [tx, ty - 1], 'hinter': True}, rnd.random() < 0.5)
            setze_px(rnd.choice(HOCH_BLUME), cx - seite * 5, fy + T, {'kachel': [tx, ty + 1], 'anim': 'wehen'})
    # Uebergaenge (Nutzer, PixelLab k27_rand + Grasbueschel Karte 01): am Rand des Pflasters Bueschel und lose
    # Pflastersteine im Gras, rund um das Wrack Truemmer und angesengte Erde
    for n in (5, 6):
        q = os.path.join(ROOT, 'assets', 'objekte', 'karte01', 'deko', '%02d.png' % n)
        os.makedirs(os.path.join(OBJ, 'k01'), exist_ok=True)
        shutil.copy(q, os.path.join(OBJ, 'k01', 'deko%02d.png' % n))
    flach = []
    for ty in range(1, rows - 1):
        for tx in range(1, cols - 1):
            if cls[ty][tx] != 'p':
                continue
            nb = [cls[ty + dy][tx + dx] for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1))]
            if 'g' in nb and rnd.random() < 0.12:
                gy, gx = [(ty + dy, tx + dx) for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)) if cls[ty + dy][tx + dx] == 'g'][0]
                flach.append((rnd.choice(['k01/deko05', 'k01/deko06', 'rand/01']), gx, gy))
    wx, wy = WRACK_POS
    for (dx, dy, n) in ((-110, 22, 'rand/02'), (150, 4, 'rand/47'), (-128, 8, 'rand/03'), (60, 24, 'rand/02'),
                        (175, -10, 'rand/03')):
        flach.append((n, (wx + dx) // T, (wy + dy) // T))
    belegt = set()
    for (n, tx, ty) in flach:
        if (tx, ty) in belegt or not (0 <= ty < rows and 0 <= tx < cols):
            continue
        belegt.add((tx, ty))
        datei, h, ux0, uy0, ux1, uy1 = variante(n, rnd.random() < 0.5, mit_fuss=False)
        bw = ux1 - ux0 + 1
        objekte.append({'datei': datei, 'basis': n, 'x': tx * T + 8 - (ux0 + bw // 2), 'y': (ty + 1) * T - 1 - uy1,
                        'fuss': h, 'kachel': [tx, ty], 'block': [tx, ty, 1, 1], 'ebene': 0,
                        'liegend': n.startswith('rand/'), 'anim': 'wehen' if n.startswith('k01') else None})
    json.dump(objekte, open(os.path.join(OBJ, 'platzierung.json'), 'w'), indent=0)
    print('Karte 27: %d Objekte' % len(objekte))


if __name__ == '__main__':
    main()
