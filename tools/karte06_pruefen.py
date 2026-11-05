"""Prueft Karte 06 auf Ueberlappungen: zwei Objekte (ausser Waldbaeumen untereinander) duerfen sich mit
deckenden Pixeln nicht beruehren (2 px Abstand).  python3 tools/karte06_pruefen.py"""
import json, os
import numpy as np
from PIL import Image, ImageFilter
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte06')


def masken(objs):
    out = []
    for o in objs:
        a = np.array(Image.open(os.path.join(OBJ, o['datei'])).getchannel('A')) >= 160
        out.append(a)
    return out


def ueberlappungen(objs, abstand=2):
    ms = masken(objs)
    belegt = {}
    paare = []
    for i, (o, a) in enumerate(zip(objs, ms)):
        g = np.array(Image.fromarray(a.astype(np.uint8) * 255).filter(ImageFilter.MaxFilter(2 * abstand + 1))) > 0
        ys, xs = np.nonzero(g)
        for y, x in zip(ys + o['y'], xs + o['x']):
            j = belegt.get((y, x))
            if j is not None and j != i:
                wald = 'baum' in objs[j]['basis'] and 'baum' in o['basis']
                gleich = objs[j]['basis'] == o['basis'] and 'front_mittel/05' in o['basis']
                if not wald and not gleich:
                    paare.append((j, i))
                    break
        for y, x in zip(*np.nonzero(a)):
            belegt[(y + o['y'], x + o['x'])] = i
    return sorted(set(paare))


if __name__ == '__main__':
    objs = json.load(open(os.path.join(OBJ, 'platzierung.json')))
    p = ueberlappungen(objs)
    print(len(p), 'Ueberlappungen')
    for i, j in p:
        print(' ', objs[i]['basis'], objs[i]['kachel'], '<->', objs[j]['basis'], objs[j]['kachel'])
