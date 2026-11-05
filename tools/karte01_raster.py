"""Objekte von Karte 01 am 16x16-Raster ausrichten - minimaler Kachelblock je Objekt.

  python3 tools/karte01_raster.py     (danach karte_bauen.py, animation_bauen.py, karte01_ebenen.py)

Fuer jedes Objekt wird der sichtbare Umriss des eigentlichen Sprites gemessen (ohne Grasfuss und weichen
Kontaktschatten der Bodenvariante - die gehoeren zum Boden). Daraus folgt der kleinste Kachelblock
(ceil(Breite/16) x ceil(Hoehe/16)). Der Umriss wird in diesen Block gesetzt: unten buendig auf der
Kachelkante, waagerecht im Block zentriert. Ein 15x58-Sprite belegt so genau 1x4 Kacheln, ein 62x62-Sprite
genau 4x4 - nie eine Spalte oder Zeile mehr, weil es ein paar Pixel verrutscht ist.
Der Block liegt dort, wo der Fuss des Objekts in der freien Platzierung stand (platzierung_frei.json).
Je Fusskachel hoechstens ein hohes und ein flaches Objekt.
"""
import json, math, os, shutil
import numpy as np
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte01')
T = 16


def umriss(o, cache):
    """Umriss (x0, y0, x1, y1) des eigentlichen Sprites in den Koordinaten der gezeichneten Datei."""
    key = (o['basis'], o['datei'], bool(o.get('spiegeln')))
    if key not in cache:
        p = os.path.join(OBJ, o['basis'] + '.png')
        varianten = o['datei'].startswith('varianten/') and os.path.exists(p)
        im = Image.open(p if varianten else os.path.join(OBJ, o['datei'])).convert('RGBA')
        if o.get('spiegeln'):
            im = im.transpose(Image.FLIP_LEFT_RIGHT)
        a = np.array(im.getchannel('A')) > 0
        ys, xs = np.nonzero(a)
        off = 2 if varianten else 0            # Bodenvariante: Sprite um 2 px eingerueckt (bauwerke.bodenfuss)
        cache[key] = (int(xs.min()) + off, int(ys.min()), int(xs.max()) + off, int(ys.max()))
    return cache[key]


def main():
    pf = os.path.join(OBJ, 'platzierung.json')
    frei = os.path.join(OBJ, 'platzierung_frei.json')
    if not os.path.exists(frei):
        shutil.copy(pf, frei)
    objs = json.load(open(frei))
    cache = {}
    belegt = set()
    neu, verworfen = [], 0
    for o in sorted(objs, key=lambda o: -(umriss(o, cache)[3] - umriss(o, cache)[1])):
        x0, y0, x1, y1 = umriss(o, cache)
        bw, bh = x1 - x0 + 1, y1 - y0 + 1
        wt, ht = math.ceil(bw / T), math.ceil(bh / T)
        fx, fy = o['x'] + (x0 + x1) / 2.0, o['y'] + y1          # Fussmitte in der freien Platzierung
        bx = int(round(fx / T - wt / 2.0))                      # linke Blockspalte
        by = int(fy // T)                                       # Fusszeile = unterste Blockzeile
        fuss = (bx + (wt - 1) // 2, by)
        art = 'flach' if o.get('ebene', 1) == 0 else 'hoch'
        if (fuss, art) in belegt:
            verworfen += 1
            continue
        belegt.add((fuss, art))
        o = dict(o)
        o['x'] = bx * T + (wt * T - bw) // 2 - x0
        o['y'] = (by + 1) * T - 1 - y1
        o['kachel'] = list(fuss)
        o['block'] = [bx, by - ht + 1, wt, ht]                  # (x, y, Breite, Hoehe) in Kacheln
        neu.append(o)
    json.dump(neu, open(pf, 'w'), indent=0)
    print('%d Objekte im minimalen Kachelblock, %d doppelt belegte Kacheln verworfen' % (len(neu), verworfen))


if __name__ == '__main__':
    main()
