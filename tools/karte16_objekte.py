"""Objekte fuer Karte 16 (The Network) - am 16x16-Raster, Paare exakt gespiegelt zur Achse (x = 256 px).

  python3 tools/karte16_bauen.py && python3 tools/karte16_objekte.py && python3 tools/karte16_bauen.py

Neu (PixelLab k16_tor, k16_klein): Firewall-Tor mit rotem Schirm (nach der Vorlage), Server-Schrank, Antennenknoten,
Datentank; gelber Datenchip wie in der Vorlage. Die Server stehen genau auf den Endknoten der Leiterbahnen.
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
from karte04_objekte import saeubern

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
T = 16


def platzieren(karte, eintraege, achse):
    """eintraege: (Quelle, Mitte x px, Fuss-Kachelreihe, Animation, gespiegelt-Paar?)"""
    OBJ = os.path.join(ROOT, 'assets', 'objekte', karte)
    os.makedirs(os.path.join(OBJ, 'sauber'), exist_ok=True)
    objekte = []
    for name, mx, reihe, anim, paar in eintraege:
        for spiegel in ((False, True) if paar else (False,)):
            sp = saeubern(Image.open(os.path.join(OBJ, name + '.png')).convert('RGBA'))
            if spiegel:
                sp = sp.transpose(Image.FLIP_LEFT_RIGHT)
            datei = 'sauber/%s%s.png' % (name.replace('/', '-'), '_m' if spiegel else '')
            sp.save(os.path.join(OBJ, datei))
            al = np.array(sp.getchannel('A')) >= 128
            zu = int(np.nonzero(al.any(axis=1))[0].max())
            xs = np.nonzero(al.any(axis=0))[0]
            m = (xs.min() + xs.max() + 1) / 2.0
            cx = 2 * achse - mx if spiegel else mx
            o = {'datei': datei, 'basis': name, 'x': int(round(cx - m)), 'y': (reihe + 1) * T - 1 - zu, 'fuss': zu,
                 'kachel': [int(cx // T), reihe], 'ebene': 1}
            if anim:
                o['anim'] = anim
            if paar:
                o['symm'] = name
            objekte.append(o)
    json.dump(objekte, open(os.path.join(OBJ, 'platzierung.json'), 'w'), indent=0)
    print('%s: %d Objekte' % (karte, len(objekte)))


ACHSE = 256
EINTRAEGE = [
    ('tor/00', ACHSE, 5, 'netzlicht', False),            # Firewall-Tor oben auf der Achse
    ('tor/04', 5.5 * T, 12, 'netzlicht', True),          # Server auf den Endknoten der Leiterbahnen
    ('tor/07', 4.5 * T, 4, 'netzlicht', True),           # Antennenknoten
    ('tor/03', 7.5 * T, 16, 'netzlicht', True),          # Datentank
]

if __name__ == '__main__':
    eintraege = list(EINTRAEGE)
    if os.path.exists(os.path.join(ROOT, 'assets', 'objekte', 'karte16', 'klein', '00.png')):
        eintraege.append(('klein/00', 19.5 * T, 7, 'netzlicht', False))   # gelber Datenchip (wie die Vorlage)
    platzieren('karte16', eintraege, ACHSE)
