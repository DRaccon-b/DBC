"""Objekte fuer Karte 26 (The Kaiser's Fortress, A02) - Raum fuer Raum, Platzierung wie Karte 24/25.

  python3 tools/karte26_bauen.py   (einmal -> wand.npy)
  python3 tools/karte26_objekte.py && python3 tools/karte26_bauen.py

Schritt 1: Thronsaal. Obsidian-Thron, Kriegsbanner, Konsolen, Obsidian-Saeulen (Karte 24), Terminals (Karte 16),
Laternen (Karte 24). Paare exakt spiegelsymmetrisch zur Achse des Throns (Mitte des Saals).
"""
import json, math, os, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
from karte04_objekte import saeubern

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte26')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte26')
T = 16
FREMD = {'k24/thron': 'karte24/schrein/00.png', 'k24/banner': 'karte24/schrein/01.png',
         'k24/konsole': 'karte24/schrein/02.png', 'k24/kristall': 'karte24/schrein/04.png',
         'k24/laterne': 'karte24/lager/04.png', 'k16/terminal': 'karte16/netz/13.png',
         'k16/saeule': 'karte16/netz/03.png'}
THRON, BANNER, KONSOLE, KRISTALL, LATERNE, TERMINAL = ('k24/thron', 'k24/banner', 'k24/konsole', 'k24/kristall',
                                                      'k24/laterne', 'k16/terminal')
AX = 19 * T                                                      # Achse des Thronsaals (x 4..33 -> Mitte)


def paar(name, dx, reihe, opt=None):
    o = dict(opt or {})
    return [(name, reihe, dict(o, px=AX - dx)), (name, reihe, dict(o, px=AX + dx, spiegeln=True))]


THRONSAAL = (
    [(THRON, 7, {'px': AX})]                                     # Thron auf dem Podest, auf der Achse
    + paar(KRISTALL, 48, 7, {'anim': 'lampe'})                   # Obsidian-Kristallsaeulen neben dem Thron (leuchten)
    + paar(BANNER, 88, 7, {'anim': 'fahne'})
    + paar(KONSOLE, 136, 7) + paar(KONSOLE, 196, 7)              # Konsolenreihen wie Vorlage, mit Abstand
    + paar(TERMINAL, 152, 14) + paar(TERMINAL, 208, 16)          # Terminals locker, keine Reihe
    + paar(LATERNE, 232, 12, {'anim': 'lampe'}) + paar(LATERNE, 232, 19, {'anim': 'lampe'})
)


def main():
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cls = lay['klassen']
    cols, rows = lay['groesse']
    for name, quelle in FREMD.items():
        ziel = os.path.join(OBJ, name + '.png')
        os.makedirs(os.path.dirname(ziel), exist_ok=True)
        shutil.copy(os.path.join(ROOT, 'assets', 'objekte', quelle), ziel)
    objekte, cache = [], {}
    for (name, fy, opt) in THRONSAAL:
        opt = dict(opt)
        spiegeln = opt.pop('spiegeln', False)
        key = (name, spiegeln)
        if key not in cache:
            sp = saeubern(Image.open(os.path.join(OBJ, name + '.png')).convert('RGBA'))
            if spiegeln:
                sp = sp.transpose(Image.FLIP_LEFT_RIGHT)
            datei = 'varianten/%s%s.png' % (name.replace('/', '-'), '_m' if spiegeln else '')
            os.makedirs(os.path.join(OBJ, 'varianten'), exist_ok=True)
            sp.save(os.path.join(OBJ, datei))
            a = np.array(sp.getchannel('A')) > 0
            ys, xs = np.nonzero(a)
            cache[key] = (datei, sp.height, int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()))
        datei, h, ux0, uy0, ux1, uy1 = cache[key]
        bw = ux1 - ux0 + 1
        px = opt.pop('px')
        x = px - (ux0 + bw // 2)
        y = (fy + 1) * T - 1 - uy1
        tx0, tx1 = (x + ux0) // T, (x + ux1) // T
        if any(cls[r][c] not in '.pgr' for c in range(tx0, tx1 + 1) for r in (fy, fy - 1)):
            print('  uebersprungen (Wand/Huelle):', name, px, fy)
            continue
        wt, ht = math.ceil(bw / T), math.ceil((uy1 - uy0 + 1) / T)
        o = {'datei': datei, 'basis': name, 'x': x, 'y': y, 'fuss': h, 'kachel': [px // T, fy],
             'block': [tx0, fy - ht + 1, wt, ht], 'ebene': 1}
        o.update(opt)
        objekte.append(o)
    json.dump(objekte, open(os.path.join(OBJ, 'platzierung.json'), 'w'), indent=0)
    print('Karte 26: %d Objekte' % len(objekte))


if __name__ == '__main__':
    main()
