"""Prueft die Objektplatzierung von Karte 01 auf Ueberlappungen (sichtbare Pixel).

  python3 tools/pruefen.py

Meldet jedes Objektpaar, dessen nicht-transparente Pixel sich beruehren. Erlaubt sind nur
Baeume untereinander (dichter Wald). Ausgabe: Anzahl + Liste, Exit-Code 1 bei Fehlern.
"""
import json, os, sys
import numpy as np
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte01')


def ist_baum(datei):
    n = datei[:-4]
    return n.startswith('baeume/') or n in ('gross/00', 'gross/01', 'gross/02', 'gross/10', 'gross/11')


def main():
    objs = json.load(open(os.path.join(OBJ, 'platzierung.json')))
    tm = json.load(open(os.path.join(ROOT, 'maps', 'karte01', 'tilemap.json')))
    W, H = tm['cols'] * 16, tm['rows'] * 16
    besitzer = -np.ones((H, W), np.int32)
    cache, fehler = {}, []
    for i, o in enumerate(objs):
        if o['datei'] not in cache:
            cache[o['datei']] = np.array(Image.open(os.path.join(OBJ, o['datei'])).getchannel('A')) > 0
        a = cache[o['datei']]
        h, w = a.shape
        x0, y0 = o['x'], o['y']
        xs0, ys0, xs1, ys1 = max(0, x0), max(0, y0), min(W, x0 + w), min(H, y0 + h)
        if xs1 <= xs0 or ys1 <= ys0:
            continue
        a = a[ys0 - y0: ys1 - y0, xs0 - x0: xs1 - x0]
        bereich = besitzer[ys0:ys1, xs0:xs1]
        andere = set(np.unique(bereich[a & (bereich >= 0)]).tolist())
        for j in andere:
            if not (ist_baum(o['datei']) and ist_baum(objs[j]['datei'])):
                fehler.append((objs[j]['datei'], (objs[j]['x'], objs[j]['y']), o['datei'], (x0, y0)))
        bereich[a] = i
    print('%d Objekte geprueft, %d Ueberlappungen' % (len(objs), len(fehler)))
    for f in fehler[:30]:
        print('  ', f)
    return 1 if fehler else 0


if __name__ == '__main__':
    sys.exit(main())
