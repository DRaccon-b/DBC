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
# Nutzer: Ranken so gross wie Baeume (PixelLab k54_ranke96, 4 Varianten) und liegende Ranken, die von der Wand waagerecht
# bzw. senkrecht zur Mitte kriechen (k54_ranke_quer); kleine Blasen aus Karte 52 als Begleiter
D = {'ranke_a': 'karte54/ranke96/00.png', 'ranke_b': 'karte54/ranke96/01.png', 'ranke_c': 'karte54/ranke96/02.png',
     'ranke_d': 'karte54/ranke96/03.png',
     'quer_a': 'karte54/ranke_quer/00.png', 'quer_b': 'karte54/ranke_quer/01.png',
     'senk_a': 'karte54/ranke_quer/02.png', 'senk_b': 'karte54/ranke_quer/03.png',
     'saeule': 'karte52/n48/05.png', 'cluster': 'karte52/n48b/06.png', 'huegel': 'karte52/n48b/02.png'}
RV = os.environ.get('K54_RANKEN')                                       # Nutzer: Rankenvarianten rv1..rv5 (PixelLab k54_rvN)
if RV:
    for i_, n_ in enumerate(('ranke_a', 'ranke_b', 'ranke_c', 'ranke_d')):
        D[n_] = 'karte54/%s/%02d.png' % (RV, i_)
    for i_, n_ in enumerate(('quer_a', 'quer_b', 'senk_a', 'senk_b')):
        D[n_] = 'karte54/%sq/%02d.png' % (RV, i_)
# liegende Ranken: (Motiv, Seite, Lage) - Wurzel steckt in der Kugelwand; 'w' = Westwand bei Zeile y (px relativ zur
# Mitte, Spiegelbild an der Ostwand), 'n' = Nordwand bei Spalte x (px relativ zur Achse, je eine links und rechts)
LIEGEND = [('quer_a', 'w', -56), ('quer_b', 'w', 84), ('senk_a', 'n', -88), ('senk_b', 'n', 70)]
# stehende Ranken und Begleiter: (Motiv, Winkel in Grad; 0 = Osten, 90 = Sueden, 270 = Norden), Spiegelbild (180 - w)
RANKEN = [('ranke_a', 214), ('ranke_d', (240, 236, 246, 232)), ('ranke_b', 142), ('ranke_c', (118, 122, 114))]
CLUSTER = [('huegel', 226), ('saeule', (256, 250, 262, 200)), ('cluster', (160, 132, 128, 105))]


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
        if name.startswith(('quer', 'senk')):                           # Pruefung: Sprite-Fehler der liegenden Ranken
            a = np.array(im).astype(int)
            kuehl = (a[..., 3] > 0) & (a[..., 1] > a[..., 0]) & (a[..., 2] > a[..., 0])
            a[kuehl, :3] = (62, 14, 30)                                  # petrolfarbener Saum -> dunkle Rotkontur
            if a[0, :, 3].any() and (a[0, :, :3][a[0, :, 3] > 0].sum(-1) > 200).any():   # oben angeschnitten
                neu = np.zeros((a.shape[0] + 1, a.shape[1], 4), int); neu[1:] = a
                neu[0] = np.where(a[0, :, 3:4] > 0, [62, 14, 30, 255], 0)  # Kontur oben ergaenzen (rund abschliessen)
                xs_ = np.nonzero(a[0, :, 3])[0]
                if len(xs_) > 2:
                    neu[0, xs_[0]] = 0; neu[0, xs_[-1]] = 0
                a = neu
            im = Image.fromarray(a.astype(np.uint8))
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
        if isinstance(w, tuple):                                             # Ausweichwinkel der Reihe nach
            return any(paar(name, w_) for w_ in w)
        """Paar exakt gespiegelt zur Kugelachse: von der Wand aus nach innen suchen, Fuss auf der Kachelunterkante."""
        im, datei = sprite(name, False)
        im_m, datei_m = sprite(name, True)
        for tiefe in range(14, 7 * T, 4):
            rr_ = rad - tiefe
            cx = mx + rr_ * math.cos(math.radians(w))
            wt_ = -(-im.width // T)                                      # Regel 1b: mittig im kleinsten Kachelblock
            off_ = 0 if wt_ % 2 == 0 else T / 2.0                        # (Achse liegt auf der Kachelkante -> Paare bleiben exakt)
            cx = round((cx - off_) / T) * T + off_
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
        return False

    wand = lvl == 9

    def liegend(name, seite, lage):
        """Liegende Ranke: Wurzel 10 px in der Kugelwand, Koerper flach auf der Membran zur Mitte (begehbar, flacher
        Schatten). Westwand + gespiegelt an der Ostwand; an der Nordwand einzeln (kein senkrechtes Spiegeln: Licht)."""
        im, datei = sprite(name, False)
        if seite == 'w':
            y = int(my + lage - im.height / 2)
            zeile = boden[min(rows * T - 1, max(0, y + im.height // 2))]
            x = int(np.argmax(zeile)) - 10                               # erste Membranspalte von links
            setz = [(im, datei, x, y), (sprite(name, True)[0], sprite(name, True)[1], 2 * mx - x - im.width, y)]
        else:
            x = int(mx + lage - im.width / 2)
            spalte = boden[:, min(cols * T - 1, max(0, x + im.width // 2))]
            y = int(np.argmax(spalte)) - 10
            setz = [(im, datei, x, y)]
        for (im_, d_, x, y) in setz:
            r = (x, y, x + im_.width - 1, y + im_.height - 1)
            if any(schnitt(r, f_) for f_ in frei) or any(schnitt(r, rr, 2) for rr in rects):
                print('  liegend nicht gesetzt:', name); continue
            rects.append(r)
            objekte.append({'datei': d_, 'basis': name, 'x': x, 'y': y, 'fuss': im_.height - 1,
                            'kachel': [(x + im_.width // 2) // T, (y + im_.height - 1) // T], 'ebene': 0, 'ohne_wall': True,
                            'liegend': True, 'sortier': y})            # flach: vor allen stehenden Objekten gezeichnet

    for n_, s_, l_ in LIEGEND:                                              # liegende Ranken zuerst (laengste Objekte)
        liegend(n_, s_, l_)
    for n_, w in RANKEN + CLUSTER:                                          # grosse zuerst, dann Begleiter
        if not paar(n_, w):
            print('  Paar nicht gesetzt:', n_, w)
    import dreaper                                                     # Nutzer: Objekte passend zum Schlamm (Version 8)
    dreaper.objekte_faerben(OBJ, objekte, None)
    json.dump(objekte, open(os.path.join(OBJ, 'platzierung.json'), 'w'), indent=0)
    print(len(objekte), 'Objekte')


if __name__ == '__main__':
    main()
