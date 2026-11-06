"""Karte 01 v1.1 - Abschlusskontrolle der Objekte: Ueberlappungen und falscher Untergrund aufloesen.

  python3 tools/karte01_v11_aufraeumen.py     (nach karte01_v11_begleiter.py und karte_bauen.py)

Gleiche Pruefung wie tools/pruefen.py. Erlaubt: Baeume untereinander (dichter Wald) und die Begleitpflanzen
vor einem Baumsockel (Regel 5). Sonst wird bei einer Ueberlappung das kleinere Objekt entfernt, bei falschem
Untergrund das Objekt (feste Sonderobjekte bleiben immer). Wiederholt, bis alles sauber ist.
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
from pruefen import ist_baum

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte01')
FEST = ('dschungel/', 'gross/', 'zelt_strand/')


def fest(o):
    return o['basis'].startswith(FEST)


def pruefen(objs, cache):
    tm = json.load(open(os.path.join(ROOT, 'maps', 'karte01', 'tilemap.json')))
    W, H = tm['cols'] * 16, tm['rows'] * 16
    besitzer = -np.ones((H, W), np.int32)
    weg = set()
    for i, o in enumerate(objs):
        if o['datei'] not in cache:
            cache[o['datei']] = np.array(Image.open(os.path.join(OBJ, o['datei'])).getchannel('A')) >= 200
        a = cache[o['datei']]
        h, w = a.shape
        x0, y0 = o['x'], o['y']
        xs0, ys0, xs1, ys1 = max(0, x0), max(0, y0), min(W, x0 + w), min(H, y0 + h)
        if xs1 <= xs0 or ys1 <= ys0:
            continue
        a = a[ys0 - y0: ys1 - y0, xs0 - x0: xs1 - x0]
        bereich = besitzer[ys0:ys1, xs0:xs1]
        for j in set(np.unique(bereich[a & (bereich >= 0)]).tolist()):
            p = objs[j]
            if ist_baum(o['datei']) and ist_baum(p['datei']):
                continue
            if (o.get('v11') == 'begleiter' and ist_baum(p['datei'])) or \
                    (p.get('v11') == 'begleiter' and ist_baum(o['datei'])):
                continue                                          # Regel 5: Pflanze vor dem Sockel
            kandidaten = [k for k in (i, j) if not fest(objs[k])]
            if kandidaten:
                weg.add(min(kandidaten, key=lambda k: cache[objs[k]['datei']].sum()))
        bereich[a] = i
    b = np.array(Image.open(os.path.join(ROOT, 'maps', 'karte01', 'terrain_basis.png')).convert('RGB')).astype(np.int16)
    gras = (b[..., 1] > b[..., 0] + 25) & (b[..., 1] > b[..., 2] + 25)
    sand = (b[..., 0] >= b[..., 1]) & (b[..., 0] > b[..., 2] + 40)
    for i, o in enumerate(objs):
        art = o.get('untergrund')
        if not art or fest(o):
            continue
        a = cache[o['datei']]
        h, w = a.shape
        x0, y0 = o['x'], o['y']
        xs0, ys0, xs1, ys1 = max(0, x0), max(0, y0), min(W, x0 + w), min(H, y0 + h)
        a = a[ys0 - y0: ys1 - y0, xs0 - x0: xs1 - x0]
        boden = gras
        if art == 'sand':
            z = np.nonzero(a.any(axis=1))[0]
            a = a.copy(); a[: max(0, z[-1] - 3)] = False
            boden = sand
        elif art == 'fuss':
            z = np.nonzero(a.any(axis=1))[0]
            a = a.copy(); a[: max(0, z[-1] - 4)] = False
        else:
            a = a | np.roll(a, 1, 0) | np.roll(a, -1, 0) | np.roll(a, 1, 1) | np.roll(a, -1, 1)
        if not boden[ys0:ys1, xs0:xs1][a].all():
            weg.add(i)
    return weg


def main():
    pf = os.path.join(OBJ, 'platzierung.json')
    objs = json.load(open(pf))
    cache, gesamt = {}, 0
    while True:
        weg = pruefen(objs, cache)
        if not weg:
            break
        gesamt += len(weg)
        objs = [o for i, o in enumerate(objs) if i not in weg]
    json.dump(objs, open(pf, 'w'), indent=0)
    print('%d Objekte entfernt (Ueberlappung/Untergrund), %d bleiben' % (gesamt, len(objs)))


if __name__ == '__main__':
    main()
