"""Objekte fuer Karte 54 - D-Reaper Kernel (A03 Nr. 21), Inneres der Kernkugel -> assets/objekte/karte54/platzierung.json

  python3 tools/karte54_layout.py && python3 tools/karte54_bauen.py && python3 tools/karte54_objekte.py && python3 tools/karte54_bauen.py

Nutzer: Ranken wachsen aus der Kugelwand in die Arena, kleine Blasencluster liegen am Rand der Membran; die Mitte und der
Zugang im Sueden bleiben frei (der Boss ist beim Betreten schon da). Alle Sprites aus Karte 52 in Originalgroesse
(PixelLab, nie herunterskaliert). Paare exakt gespiegelt zur Kugelachse, Fuss auf der Kachelunterkante, Fuss ganz auf der
Membran (nicht auf den Blasen), 2 px Abstand untereinander, Motive ohne gleiches Motiv daneben.
"""
import json, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte54')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte54')
T = 16
D = {'ranke': 'karte52/n48/06.png', 'ranke2': 'karte52/anime/07.png',              # Ranken mit Blasenspitze
     'saeule': 'karte52/n48/05.png', 'cluster': 'karte52/n48b/06.png', 'huegel': 'karte52/n48b/02.png'}
# (Motiv, Winkel in Grad; 0 = Osten, 90 = Sueden, 270 = Norden) - je Eintrag wird das Spiegelbild (180 - w) mitgesetzt
# In Gruppen statt gleichmaessig im Kreis (keine Reihe): je Gruppe eine Ranke an der Wand, daneben Blasen etwas tiefer
RANKEN = [('ranke2', 226), ('ranke', 170), ('ranke2', 132)]
CLUSTER = [('huegel', 233), ('saeule', 249), ('cluster', 178), ('huegel', 140)]


def main():
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cols, rows = lay['groesse']
    lvl = np.load(os.path.join(KARTE, 'pixelhoehe.npy'))
    boden = lvl == 1
    mx, my = lay['mitte'][0] * T, lay['mitte'][1] * T
    rad = lay['radius'] * T
    tp = lay['teleporter'][0]
    frei = [(mx - 7 * T, my - 7 * T, mx + 7 * T, my + 7 * T),                        # Mitte frei (Boss)
            ((tp['x'] - 3) * T, (tp['y'] - 8) * T, (tp['x'] + tp['b'] + 3) * T, rows * T)]   # Zugang frei
    os.makedirs(os.path.join(OBJ, 'varianten'), exist_ok=True)
    objekte, rects = [], []

    def schnitt(a, b, d=0):
        return not (a[2] + d < b[0] or b[2] + d < a[0] or a[3] + d < b[1] or b[3] + d < a[1])

    def sprite(name, sp_):
        im = Image.open(os.path.join(ROOT, 'assets', 'objekte', D[name])).convert('RGBA')
        im = im.crop(im.getbbox())
        if sp_:
            im = im.transpose(Image.FLIP_LEFT_RIGHT)
        datei = 'varianten/%s%s.png' % (name, '_m' if sp_ else '')
        im.save(os.path.join(OBJ, datei))
        return im, datei

    def pruefe(im, cx, fy):
        x = int(round(cx - im.width / 2.0))
        y = fy - im.height + 1
        r = (x, y, x + im.width - 1, fy)
        if r[0] < 0 or r[1] < 0 or r[2] >= cols * T or r[3] >= rows * T:
            return None
        if any(schnitt(r, f_) for f_ in frei) or any(schnitt(r, rr, 2) for rr in rects):
            return None
        al = np.array(im)[..., 3] > 0                                       # untere zwei Reihen ganz auf der Membran
        unten = al.copy(); unten[:max(0, im.height - 2 * T)] = False
        ys, xs = np.nonzero(unten)
        yy, xx = ys + y, xs + x
        if not boden[np.clip(yy + 2, 0, rows * T - 1), np.clip(xx, 0, cols * T - 1)].all():
            return None
        return x, y, r

    def paar(name, w):
        """Paar exakt gespiegelt zur Kugelachse: von der Wand aus nach innen suchen, Fuss auf der Kachelunterkante."""
        im, datei = sprite(name, False)
        im_m, datei_m = sprite(name, True)
        for tiefe in range(14, 7 * T, 4):
            rr_ = rad - tiefe
            cx = mx + rr_ * math.cos(math.radians(w))
            fy = int(my + rr_ * math.sin(math.radians(w))) // T * T + T - 1
            a_ = pruefe(im, cx, fy)
            if not a_:
                continue
            rects.append(a_[2])
            b_ = pruefe(im_m, 2 * mx - cx, fy)
            if not b_:
                rects.pop()
                continue
            rects.append(b_[2])
            for (x, y, r), d_, n_ in ((a_, datei, name), (b_, datei_m, name)):
                objekte.append({'datei': d_, 'basis': n_, 'x': x, 'y': y, 'fuss': r[3] - y, 'kachel': [int(r[0] + r[2]) // 2 // T, r[3] // T],
                                'ebene': 1, 'ohne_wall': True, 'nur_kontakt': True})
            return True
        print('  Paar nicht gesetzt:', name, w)
        return False

    for n_, w in RANKEN:                                                     # grosse Begleiter zuerst
        paar(n_, w)
    for n_, w in CLUSTER:
        paar(n_, w)
    json.dump(objekte, open(os.path.join(OBJ, 'platzierung.json'), 'w'), indent=0)
    print(len(objekte), 'Objekte')


if __name__ == '__main__':
    main()
