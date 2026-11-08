"""Objekte fuer Karte 19 (Revenge) - am 16x16-Raster, nach den Regeln aus CLAUDE.md.

  python3 tools/karte19_bauen.py   (einmal -> pixelhoehe.npy)
  python3 tools/karte19_objekte.py && python3 tools/karte19_bauen.py

Hafen (rechter Raum): vier Poller mit Tau (wiederverwendet: Karte 18, PixelLab k18_boot/05) auf der Kaikante, kurz
bevor das Wasser beginnt - gleichmaessig verteilt und spiegelsymmetrisch zur Raummitte, Fuesse buendig in einer Reihe.
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageFilter
from karte04_objekte import saeubern

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte19')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte19')
T = 16
RX, RY = 42, 6                                   # linke obere Ecke des Hafenraums
MITTE = (RX + 14) * T                            # Raumachse (x = 896 px)
KAI = RY + 8                                     # Fussreihe: erste Pflasterreihe hinter der Kaikante (Sockel ganz auf Stein)
# (Quelle, Mitte x in px, Fussreihe, Animation)
OBJEKTE = [('hafen/poller', MITTE + dx, KAI, None) for dx in (-152, -56, 56, 152)]


def main():
    lvl = np.load(os.path.join(KARTE, 'pixelhoehe.npy'))
    Hp, Wp = lvl.shape
    os.makedirs(os.path.join(OBJ, 'sauber'), exist_ok=True)
    objekte, belegt = [], np.zeros((Hp, Wp), bool)
    for name, mitte, reihe, anim in OBJEKTE:
        sp = saeubern(Image.open(os.path.join(OBJ, name + '.png')).convert('RGBA'))
        datei = 'sauber/%s.png' % name.replace('/', '-')
        sp.save(os.path.join(OBJ, datei))
        a = np.array(sp.getchannel('A')) >= 128
        zu = int(np.nonzero(a.any(axis=1))[0].max())
        xs = np.nonzero(a.any(axis=0))[0]
        x = int(round(mitte - (xs.min() + xs.max() + 1) / 2.0))
        y = (reihe + 1) * T - 1 - zu
        h_, w_ = a.shape
        fuss = a.copy(); fuss[:max(0, zu + 1 - 6)] = False          # Fuss (unterste Pixelreihen) auf festem Boden
        assert (lvl[y:y + h_, x:x + w_][fuss] == 2).all(), name + ': Fuss nicht auf dem Kai'
        assert not (belegt[y:y + h_, x:x + w_] & a).any(), name + ': ueberlappt'
        g = np.zeros_like(belegt); g[y:y + h_, x:x + w_] = a
        belegt |= np.array(Image.fromarray((g * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(5))) > 0
        o = {'datei': datei, 'basis': name, 'x': x, 'y': y, 'fuss': zu, 'kachel': [int(mitte // T), reihe], 'ebene': 2,
             'an_wand': True}                                         # kein Erd-Bodenwall auf Stein
        if anim:
            o['anim'] = anim
        objekte.append(o)
        print('  %s: x %d-%d, y %d-%d' % (name, x, x + w_, y, y + h_))
    json.dump(objekte, open(os.path.join(OBJ, 'platzierung.json'), 'w'), indent=0)
    print('Karte 19: %d Objekte' % len(objekte))


if __name__ == '__main__':
    main()
