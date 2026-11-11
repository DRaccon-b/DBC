"""Objekte fuer Karte 28 (Tower Forest, A02).

  python3 tools/karte28_bauen.py   (einmal -> wand.npy)
  python3 tools/karte28_objekte.py && python3 tools/karte28_bauen.py

Schritt 1: Waldrand (Nutzer) - dunkle Waldbaeume (tools/karte28_baeume.py, umgefaerbt aus Karte 01) dicht im
Schachbrett auf den Waldkacheln wie Karte 06 / 23 / 27; Fuss nie auf einer Wand.
"""
import json, math, os, random, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
import bauwerke

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte28')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte28')
T = 16
# Schwarze Obelisken (Karte 24 obelisk2, ohne Leuchten): Mitte x (px, Kachelgrenze) und Schaftende y aus der Vorlage
OBELISKEN = [(816, 218), (1392, 218), (384, 506), (672, 506), (960, 506), (1248, 506),
             (240, 794), (816, 794), (1104, 794), (1392, 794), (640, 1146), (960, 1146)]
OBELISK = 'k24/obelisk'
WALD = ['wald_dunkel/%02d' % i for i in (0, 1, 2, 3, 4, 5, 6, 7, 0, 1, 2, 4, 7, 8, 9, 10)]   # Laub-/Nadelbaeume, wenige Buesche


def main():
    rnd = random.Random(28)
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cls = lay['klassen']
    cols, rows = lay['groesse']
    wand = np.unpackbits(np.load(os.path.join(KARTE, 'wand.npy')))[:rows * T * cols * T].reshape(rows * T, cols * T).astype(bool)
    objekte, cache = [], {}

    def variante(name, spiegeln, boden='gras'):
        key = (name, spiegeln, boden)
        if key not in cache:
            sp = Image.open(os.path.join(OBJ, name + '.png')).convert('RGBA')
            if spiegeln:
                sp = sp.transpose(Image.FLIP_LEFT_RIGHT)
            aa = np.array(sp.getchannel('A')) > 0
            ys, xs = np.nonzero(aa)
            ux0, uy0, ux1, uy1 = int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())
            v = bauwerke.bodenfuss(sp, boden, 'baum' if 'wald' in name else 'stein')
            fa = np.array(v).astype(np.float32)                      # Bodenfuss an den dunklen Waldboden anpassen
            off = Image.new('RGBA', v.size, (0, 0, 0, 0)); off.paste(sp, (2, 0))
            sel = (np.array(off.getchannel('A')) == 0) & (fa[..., 3] > 0)
            fa[sel, :3] *= np.array([0.5, 0.56, 0.62])
            v = Image.fromarray(np.clip(fa, 0, 255).astype(np.uint8))
            datei = 'varianten/%s_%s%s.png' % (name.replace('/', '-'), boden, '_m' if spiegeln else '')
            os.makedirs(os.path.join(OBJ, 'varianten'), exist_ok=True)
            v.save(os.path.join(OBJ, datei))
            cache[key] = (datei, v.height, ux0 + 2, uy0, ux1 + 2, uy1)
        return cache[key]

    # Grosse Objekte zuerst: schwarze Obelisken (Fuss buendig auf der Kachelkante, waagerecht auf der Kachelgrenze
    # wie in der Vorlage = mittig im 2-Kachel-Block)
    os.makedirs(os.path.join(OBJ, 'k24'), exist_ok=True)
    ob = np.array(Image.open(os.path.join(ROOT, 'assets', 'objekte', 'karte24', 'obelisk2', '00.png')).convert('RGBA')).astype(int)
    warm = (ob[..., 3] > 0) & (ob[..., 0] > ob[..., 2] + 20)           # orange Lichtkante am Sockel -> schwarzblau
    ob[warm, :3] = (52, 58, 78)
    Image.fromarray(ob.astype(np.uint8)).save(os.path.join(OBJ, OBELISK + '.png'))
    for (cx, yb) in OBELISKEN:
        ty = (yb + 20) // T
        tx = cx // T
        k_ = cls[ty][tx]
        boden = 'sand' if k_ in 'fewt' else 'beton' if k_ == 'k' else 'gras'
        datei, h, ux0, uy0, ux1, uy1 = variante(OBELISK, False, boden)
        bw = ux1 - ux0 + 1
        objekte.append({'datei': datei, 'basis': OBELISK, 'x': cx - bw // 2 - ux0, 'y': (ty + 1) * T - 1 - uy1, 'fuss': h,
                        'kachel': [tx, ty], 'block': [tx - 1, ty - math.ceil((uy1 - uy0 + 1) / T) + 1, 2,
                                                      math.ceil((uy1 - uy0 + 1) / T)], 'ebene': 1})
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
    # Spinnweben (Nutzer, PixelLab k28_netz): flach auf dem Boden, ohne Schatten - Steinplatz ausserhalb des Rings und
    # Arena (vor allem die oberen Ecken, wie die Vorlage); Kokons (4, 6) dazwischen
    NETZE = ['netz/00', 'netz/01', 'netz/02', 'netz/03', 'netz/00', 'netz/02']
    NETZ_STELLEN = [(67, 12), (72, 12), (77, 12), (63, 13), (79, 13),             # Mauer der Spinnen-Arena: innere Front,
                    (61, 17), (62, 22), (80, 16), (80, 22), (66, 9), (74, 9),      # Ecken, Krone, aeussere Front
                    (63, 27), (67, 27), (77, 27),
                    (87, 12), (88, 20), (87, 27), (59, 27), (59, 16),              # Steinplatz aussen
                    (8, 21), (10, 23), (12, 20), (9, 25), (13, 23), (24, 21), (27, 20), (30, 19), (29, 23), (34, 18),
                    (42, 21), (45, 22), (46, 25), (41, 19), (6, 28), (19, 34), (38, 31)]
    KOKONS = [(66, 15), (85, 14), (11, 22), (44, 21), (28, 21)]
    belegt = set((o['kachel'][0], o['kachel'][1]) for o in objekte if not o['basis'].startswith('wald'))
    for i, (tx, ty) in enumerate(NETZ_STELLEN + KOKONS):
        if (tx, ty) in belegt or cls[ty][tx] in 'hwT' or any(
                o['basis'] == OBELISK and abs(o['kachel'][0] - tx) <= 2 and -6 <= ty - o['kachel'][1] <= 1 for o in objekte):
            continue
        name = ('netz/04' if i % 2 else 'netz/06') if i >= len(NETZ_STELLEN) else NETZE[(tx * 7 + ty * 3) % len(NETZE)]
        sp = Image.open(os.path.join(OBJ, name + '.png')).convert('RGBA')
        if (tx + ty) % 2:
            sp = sp.transpose(Image.FLIP_LEFT_RIGHT)
        datei = 'varianten/%s%s.png' % (name.replace('/', '-'), '_m' if (tx + ty) % 2 else '')
        sp.save(os.path.join(OBJ, datei))
        bb = sp.getbbox()
        kokon = i >= len(NETZ_STELLEN)
        objekte.append({'datei': datei, 'basis': name, 'x': tx * T + 8 - (bb[0] + bb[2]) // 2, 'y': (ty + 1) * T - 1 - (bb[3] - 1),
                        'fuss': sp.height, 'kachel': [tx, ty], 'block': [tx, ty, 1, 1], 'ebene': 1 if kokon else 0,
                        'schattenlos': not kokon})
        belegt.add((tx, ty))
    json.dump(objekte, open(os.path.join(OBJ, 'platzierung.json'), 'w'), indent=0)
    print('Karte 28: %d Objekte' % len(objekte))


if __name__ == '__main__':
    main()
