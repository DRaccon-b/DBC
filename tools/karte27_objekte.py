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
WRACK_POS = (178, 1126)                         # Fussmitte x, Fusslinie y (px) - vor der Mauer des Plateaus unten links


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
        key = (name, spiegeln)
        if key not in cache:
            sp = Image.open(os.path.join(OBJ, name + '.png')).convert('RGBA')
            if spiegeln:
                sp = sp.transpose(Image.FLIP_LEFT_RIGHT)
            aa = np.array(sp.getchannel('A')) > 0
            ys, xs = np.nonzero(aa)
            ux0, uy0, ux1, uy1 = int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())
            v = bauwerke.bodenfuss(sp, 'gras', 'baum') if mit_fuss else sp
            off = 2 if mit_fuss else 0
            datei = 'varianten/%s%s.png' % (name.replace('/', '-'), '_m' if spiegeln else '')
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
    json.dump(objekte, open(os.path.join(OBJ, 'platzierung.json'), 'w'), indent=0)
    print('Karte 27: %d Objekte' % len(objekte))


if __name__ == '__main__':
    main()
