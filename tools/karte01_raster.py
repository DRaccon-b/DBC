"""Objekte von Karte 01 am 16x16-Raster ausrichten.

  python3 tools/karte01_raster.py     (danach karte_bauen.py, animation_bauen.py, karte01_ebenen.py)

Jedes Objekt steht danach mit seinem Fuss mittig in genau einer Kachel: Fussmitte (Mitte der untersten
deckenden Spalten) auf der Kachelmitte, unterste deckende Zeile 2 px ueber der Kachelunterkante.
Landen zwei Objekte derselben Art (hoch/flach) in einer Kachel, bleibt nur das erste.
Die freie Platzierung wird einmalig als platzierung_frei.json gesichert und dient als Quelle.
"""
import json, os, shutil
import numpy as np
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte01')
T = 16


def main():
    pf = os.path.join(OBJ, 'platzierung.json')
    frei = os.path.join(OBJ, 'platzierung_frei.json')
    if not os.path.exists(frei):
        shutil.copy(pf, frei)
    objs = json.load(open(frei))
    cache = {}
    belegt = set()
    neu = []
    verworfen = 0
    for o in sorted(objs, key=lambda o: -(Image.open(os.path.join(OBJ, o['datei'])).height)):
        if o['datei'] not in cache:
            a = np.array(Image.open(os.path.join(OBJ, o['datei'])).getchannel('A')) >= 128
            zeilen = np.nonzero(a.any(axis=1))[0]
            zu = int(zeilen.max())
            spalten = np.nonzero(a[max(0, zu - 2):zu + 1].any(axis=0))[0]
            cache[o['datei']] = (zu, (spalten.min() + spalten.max() + 1) / 2.0)
        zu, mitte = cache[o['datei']]
        if o.get('spiegeln'):
            w = Image.open(os.path.join(OBJ, o['datei'])).width
            mitte = w - mitte
        fx, fy = o['x'] + mitte, o['y'] + zu
        tx, ty = int(fx // T), int(fy // T)
        art = 'flach' if o.get('ebene', 1) == 0 else 'hoch'
        if (tx, ty, art) in belegt:
            verworfen += 1
            continue
        belegt.add((tx, ty, art))
        o = dict(o)
        o['x'] = int(round(tx * T + T / 2 - mitte))
        o['y'] = int(ty * T + T - 2 - zu)
        o['kachel'] = [tx, ty]
        neu.append(o)
    json.dump(neu, open(pf, 'w'), indent=0)
    print('%d Objekte am Raster, %d doppelt belegte Kacheln verworfen' % (len(neu), verworfen))


if __name__ == '__main__':
    main()
