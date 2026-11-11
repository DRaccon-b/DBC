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
THRON2, KOMMANDO, HOLO, WACHE, FEUERSCHALE, WAFFEN, RADAR = ('thron_gross/00', 'thron_gross/01', 'thron/00', 'thron/02',
                                                            'thron/03', 'thron/05', 'thron/15')
THRON, BANNER, KONSOLE, KRISTALL, LATERNE, TERMINAL = ('k24/thron', 'k24/banner', 'k24/konsole', 'k24/kristall',
                                                      'k24/laterne', 'k16/terminal')
AX = 19 * T                                                      # Achse des Thronsaals (x 4..33 -> Mitte)


def paar(name, dx, reihe, opt=None):
    o = dict(opt or {})
    return [(name, reihe, dict(o, px=AX - dx)), (name, reihe, dict(o, px=AX + dx, spiegeln=True))]


THRONSAAL = (                                                    # Kommandobruecke des Kaisers (eigene PixelLab-Objekte k26_thron)
    [(THRON2, 9, {'px': AX})]                                    # Kaiserthron auf der Achse, Teppich davor
    + paar('digifeuer/00', 60, 9, {'anim': 'lampe'})             # Feuerschalen mit digitalen Flammen (Nutzer)
    + paar(KOMMANDO, 172, 9, {'anim': 'lampe'})                  # grosse Kommandopulte mit vier Monitoren
    + [(HOLO, 18, {'px': AX, 'anim': 'lampe'})]                  # ein Holo-Schiff unten auf der Achse (Nutzer)
    + paar('digifeuer/13', 208, 19, {'anim': 'lampe'})          # Tesla-Turm (digifeuer Nr. 13) statt Radar (Nutzer)
)

KAPSEL, TANK, SERVER, FROST, LABTISCH, CHEMIE, REAKTOR, PULT, FAESSER, KABEL, STEUER = (
    'labor/00', 'tank3/00', 'labor/09', 'labor/02', 'labor/01', 'labor/08', 'tank/02', 'labor/10', 'labor/12',
    'labor/03', 'labor/05')
LABOR = (                                                        # Brutlabor oben rechts, aufgeraeumt (Nutzer: weniger)
    [(TANK, 13, {'px': 64 * T}), (TANK, 24, {'px': 64 * T})]      # zwei grosse Stasis-Tanks wie in der Vorlage
    + [(n, r, {'px': x * T})                                     # Nutzer: kapsel2 Nr. 2 (Brutkapseln oben), 4, 11, 14 (unten)
       for (n, x, r) in (('kapsel2/14', 46, 10), ('kapsel2/02', 50, 10), ('kapsel2/11', 54, 10),
                         ('kapsel2/04', 46, 15), ('kapsel2/11', 50, 15), ('kapsel2/14', 54, 15))]
    + [(SERVER, 9, {'px': 72 * T}), (LABTISCH, 10, {'px': 79 * T})]
)

LABOR2 = (                                                       # Zellentrakt Mitte links (Nutzer: Zellen mit Gittern, Gitter in karte26_bauen)
    [('kammer/00', 46, {'px': int(x * T), 'anim': 'lampe'}) for x in (7.25, 10.75, 27.25, 30.75)]   # Kammern in den Eckzellen
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
    for (name, fy, opt) in THRONSAAL + LABOR + LABOR2:
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
