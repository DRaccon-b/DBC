"""Objekte fuer Karte 16 (The Network), Neuaufbau Schritt 3 - nach den Regeln aus CLAUDE.md.

  python3 tools/karte16_bauen.py   (einmal ohne Objekte -> pixelhoehe.npy)
  python3 tools/karte16_objekte.py && python3 tools/karte16_bauen.py

- Firewall-Tor (wiederverwendet, PixelLab k16_tor/00 - entspricht dem Tor der Vorlage) oben auf der Plattform,
  exakt auf der Achse (x = 512 px), 4 Kacheln breit wie das Pfeilfeld.
- Computer 'Dungeon Records' (neu, PixelLab Objekt-Creator k16_computer/00, nach dem Bild des Nutzers) links vom Tor,
  tiefer gesetzt (Nutzerwunsch): Fuss auf halber Hoehe der runden Plattform (Reihe 15).
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
from karte04_objekte import saeubern

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte16')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte16')
T = 16
ACHSE = 32 * T
FUSS = 9                                   # Fussreihe von Tor und Computer
# (Quelle, Mitte x in px, Fussreihe, Animation)
OBJEKTE = [
    ('tor/00', ACHSE, FUSS, 'tor16'),
    ('computer/00', ACHSE - 40, 15, 'bildschirm16'),   # Nutzerwunsch: tiefer, auf halber Hoehe der Plattform
]


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
        fuss = a.copy(); fuss[:max(0, zu + 1 - 2 * T)] = False     # untere zwei Kachelreihen
        assert (lvl[y:y + h_, x:x + w_][fuss] == 2).all(), name + ': Fuss nicht ganz auf der Plattform'
        assert not (belegt[y:y + h_, x:x + w_] & a).any(), name + ': ueberlappt'
        g = np.zeros_like(belegt); g[y:y + h_, x:x + w_] = a
        from PIL import ImageFilter
        belegt |= np.array(Image.fromarray((g * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(5))) > 0
        objekte.append({'datei': datei, 'basis': name, 'x': x, 'y': y, 'fuss': zu, 'kachel': [int(mitte // T), reihe],
                        'ebene': 2, 'anim': anim, 'an_wand': True})   # an_wand: kein Erd-Bodenwall auf Metall
        print('  %s: x %d-%d, y %d-%d' % (name, x, x + w_, y, y + h_))
    json.dump(objekte, open(os.path.join(OBJ, 'platzierung.json'), 'w'), indent=0)
    print('Karte 16: %d Objekte' % len(objekte))


if __name__ == '__main__':
    main()
