"""Objekte fuer Karte 22 (Digicasino) - am 16x16-Raster, nach den Regeln aus CLAUDE.md.

  python3 tools/karte22_bauen.py   (einmal -> pixelhoehe.npy)
  python3 tools/karte22_objekte.py && python3 tools/karte22_bauen.py

Alle Objekte neu mit dem PixelLab Objekt-Creator (k22_casino, k22_gross) im Netz-Stil von Karte 16.
Paare stehen exakt spiegelsymmetrisch zur Mittelachse des Casinos (x = 416 px; gespiegelt: x' = 832 - x).
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageFilter
from karte04_objekte import saeubern

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte22')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte22')
T = 16
MITTE = 416
AUTOMAT, ROULETTE, KARTEN, CRAPS, BLACKJACK = 'casino/00', 'casino/01', 'casino/02', 'casino/06', 'casino/07'
KORDEL, ATM, JACKPOT, THEKE, KRISTALL, LAMPE = 'casino/04', 'casino/12', 'gross/00', 'gross/01', 'gross/02', 'gross/10'


def paar(name, dx, reihe, anim=None, spiegeln_rechts=False):
    """Links/rechts gespiegelt zur Achse: Mitte bei MITTE -/+ dx."""
    return [(name, MITTE - dx, reihe, anim, False), (name, MITTE + dx, reihe, anim, spiegeln_rechts)]


# (Quelle, Mitte x in px, Fussreihe, Animation, gespiegelt)
OBJEKTE = (
    # Buehne: zwei Preistheken links/rechts der VIP-Tuer (Ausgang bleibt frei)
    paar(THEKE, 96, 6)
    # Automatenreihen (je 4 Automaten untereinander)
    + sum((paar(AUTOMAT, 224, r, 'automat') for r in (8, 11, 14, 17)), [])
    # Spieltische: links Roulette/Karten, rechts Blackjack/Craps (gleiche Plaetze gespiegelt)
    + [(ROULETTE, MITTE - 112, 12, None, False), (BLACKJACK, MITTE + 112, 12, None, False),
       (KARTEN, MITTE - 112, 16, None, False), (CRAPS, MITTE + 112, 16, None, False)]
    # Samtkordeln am Teppich, Neonlaternen am Eingang, Geldautomaten
    + paar(KORDEL, 46, 10, None, True) + paar(KORDEL, 46, 15, None, True)
    + paar(LAMPE, 56, 20, 'lampe')
    + paar(ATM, 120, 20, 'lampe')
    # Jackpot-Inseln: je ein grosser Jackpot-Automat
    + paar(JACKPOT, 360, 12, 'automat')
    # Ankunft: zwei Datenkristalle neben den Pfeilen
    + paar(KRISTALL, 48, 25, 'lampe')
)


def main():
    lvl = np.load(os.path.join(KARTE, 'pixelhoehe.npy'))
    Hp, Wp = lvl.shape
    os.makedirs(os.path.join(OBJ, 'sauber'), exist_ok=True)
    objekte, belegt = [], np.zeros((Hp, Wp), bool)
    for name, mitte, reihe, anim, spiegeln in OBJEKTE:
        sp = saeubern(Image.open(os.path.join(OBJ, name + '.png')).convert('RGBA'))
        if spiegeln:
            sp = sp.transpose(Image.FLIP_LEFT_RIGHT)
        datei = 'sauber/%s%s.png' % (name.replace('/', '-'), '_m' if spiegeln else '')
        sp.save(os.path.join(OBJ, datei))
        a = np.array(sp.getchannel('A')) >= 128
        zu = int(np.nonzero(a.any(axis=1))[0].max())
        xs = np.nonzero(a.any(axis=0))[0]
        x = int(round(mitte - (xs.min() + xs.max() + 1) / 2.0))
        y = (reihe + 1) * T - 1 - zu
        h_, w_ = a.shape
        fuss = a.copy(); fuss[:max(0, zu + 1 - 6)] = False
        assert (lvl[y:y + h_, x:x + w_][fuss] == 2).all(), name + ': Fuss nicht auf der Plattform'
        if (belegt[y:y + h_, x:x + w_] & a).any():
            print('  WARNUNG ueberlappt:', name, mitte, reihe)
        g = np.zeros_like(belegt); g[y:y + h_, x:x + w_] = a
        belegt |= np.array(Image.fromarray((g * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(5))) > 0
        o = {'datei': datei, 'basis': name, 'x': x, 'y': y, 'fuss': zu, 'kachel': [int(mitte // T), reihe], 'ebene': 2,
             'an_wand': True}
        if anim:
            o['anim'] = anim
        objekte.append(o)
    json.dump(objekte, open(os.path.join(OBJ, 'platzierung.json'), 'w'), indent=0)
    print('Karte 22: %d Objekte' % len(objekte))


if __name__ == '__main__':
    main()
