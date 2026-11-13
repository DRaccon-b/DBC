"""Objekte fuer Karte 37 (Hypnos Rooftop, A03 Nr. 4) -> assets/objekte/karte37/platzierung.json

  python3 tools/karte37_objekte.py && python3 tools/karte37_bauen.py

Nach der Vorlage: Faesser paarweise in den oberen Ziegelflaechen (Karte 02), Generatoren/Tanks und Terminal unten
(Karte 26), Laternen an den Kanten (Karte 18, Schein nur am Kopf), Lueftungsgitter, Kabel und Dachluke (PixelLab k37_dach).
Pixelgenaue Pruefung (2 px), kein Bodenwall auf dem Ziegelboden, Teleporter frei.
"""
import json, math, os, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte37')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte37')
T = 16
FREMD = {'fass/blau': 'karte02/klein/00.png', 'fass/grau': 'karte02/klein/01.png', 'gen/00': 'karte26/labor/04.png',
         'terminal/00': 'karte26/labor/01.png', 'k18s/18': 'karte18/strasse/18.png'}
# (sprite, Kachel-x, Fusszeile) der Vorlage
FAESSER = [('fass/blau', 6, 7), ('fass/grau', 8, 7), ('fass/grau', 6, 11), ('fass/blau', 8, 11),
           ('fass/grau', 41, 7), ('fass/blau', 43, 7), ('fass/blau', 41, 12), ('fass/grau', 43, 12)]
GITTER = [(5, 9), (7, 9), (5, 14), (42, 9), (40, 14), (42, 14), (18, 27), (20, 27), (36, 27), (38, 27)]
GITTERREIHEN = [(12, 37, 5), (17, 38, 25), (17, 38, 31)]          # Lueftungsreihen der Vorlage (jede 2. Kachel)
LATERNEN = [(4, 19), (43, 19),               # Bucht-Laternen eine Reihe hoeher: Schatten bleibt auf der Flaeche
            (16, 29), (38, 29)]
GROSS = [('gen/00', 5, 28), ('gen/00', 41, 28), ('terminal/00', 7, 31)]
# Generator laeuft: Tanks blubbern, Anzeigen blinken (Regel Maschinen-Animation)
GEN_ANIM = {'anim': 'maschine', 'ruetteln': True, 'leds': True, 'led_box': [[34, 18, 48, 30], [9, 41, 15, 47]],
            'fluessig': [[27, 2, 36, 15, 'gruen'], [0, 20, 9, 42, 'cyan'], [53, 14, 62, 40, 'cyan']]}
# Rohre der Vorlage unter der Ziegelkante der Seitenbuchten (PixelLab k37_rohr, Mittelstueck gekuerzt): (sprite, cx, Fuss-y)
ROHRE = [('rohr/lang', 120, 273), ('rohr/kurz', 664, 289)]
KABEL = [(6, 12), (13, 9), (29, 8), (11, 15), (6, 18), (14, 26), (36, 30), (40, 15)]


def main():
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cls = lay['klassen']
    cols, rows = lay['groesse']

    def k(tx, ty):
        return cls[min(rows - 1, max(0, ty))][min(cols - 1, max(0, tx))]

    for name, q in FREMD.items():
        ziel = os.path.join(OBJ, name + '.png')
        os.makedirs(os.path.dirname(ziel), exist_ok=True)
        shutil.copy(os.path.join(ROOT, 'assets', 'objekte', q), ziel)
    tps = [(t['x'] * T - 2 * T, t['y'] * T - 2 * T, (t['x'] + t['b'] + 2) * T, (t['y'] + t['h'] + 2) * T)
           for t in lay['teleporter']]
    objekte, rects = [], []

    def schnitt(a, b, rand=0):
        return not (a[2] + rand < b[0] or b[2] + rand < a[0] or a[3] + rand < b[1] or b[3] + rand < a[1])

    def setze(name, tx, fy_tile, opt=None, spiegeln=False, pruefen=True, cx=None, fy=None):
        sp = Image.open(os.path.join(OBJ, name + '.png')).convert('RGBA')
        if spiegeln:
            sp = sp.transpose(Image.FLIP_LEFT_RIGHT)
        datei = 'varianten/%s%s.png' % (name.replace('/', '-'), '_m' if spiegeln else '')
        os.makedirs(os.path.join(OBJ, 'varianten'), exist_ok=True)
        sp.save(os.path.join(OBJ, datei))
        bb = sp.getbbox()
        bw = bb[2] - bb[0]
        wt = max(1, math.ceil(bw / T))
        if cx is None:                                               # Regel 1b: kleinster Kachelblock, mittig, Fuss buendig
            cx = (tx - (wt - 1) // 2) * T + wt * T / 2.0
        if fy is None:
            fy = fy_tile * T + T - 1
        x = int(round(cx - (bb[0] + bb[2]) / 2.0))
        y = int(fy - (bb[3] - 1))
        r = (x + bb[0], y + bb[1], x + bb[2] - 1, y + bb[3] - 1)
        if pruefen:
            if any(schnitt(r, rr, 2) for rr in rects) or any(schnitt(r, t_, 0) for t_ in tps):
                return None
            for xx in range(r[0] // T, r[2] // T + 1):              # Fuss ganz auf dem Dach
                if k(xx, r[3] // T) not in 'ku':
                    return None
        o = {'datei': datei, 'basis': name, 'x': x, 'y': y, 'fuss': bb[3] - 1, 'kachel': [int(cx) // T, int(fy) // T],
             'ebene': 1, 'ohne_wall': True}
        o.update(opt or {})
        objekte.append(o)
        rects.append(r)
        return o

    for (n_, tx, ty) in GROSS:
        if n_.startswith('terminal'):                                   # Terminal neben dem Generator (erste freie Stelle)
            if not any(setze(n_, x_, y_, {'anim': 'maschine', 'schirm': [[7, 2, 28, 13]]})
                       for (x_, y_) in ((tx, ty), (10, 30), (11, 31), (12, 30))):
                print('nicht gesetzt:', n_, tx, ty)
            continue
        if not setze(n_, tx, ty, GEN_ANIM):
            print('nicht gesetzt:', n_, tx, ty)
    for (n_, cx_, fy_) in ROHRE:
        if not setze(n_, 0, 0, {'liegend': True}, cx=cx_, fy=fy_):
            print('Rohr nicht gesetzt:', n_)
    for i, (n_, tx, ty) in enumerate(FAESSER):
        if not setze(n_, tx, ty, {'nur_kontakt': True}, i % 3 == 0):          # dicht an dicht: nur Kontaktschatten
            print('nicht gesetzt:', n_, tx, ty)
    for (tx, ty) in LATERNEN:
        fy_ = 322 if ty == 19 else None                                 # Bucht: Fuss 13 px ueber der Kante (Rohr darueber)
        if not setze('k18s/18', tx, ty, fy=fy_, opt={'anim': 'leuchten', 'licht': [4, 7], 'licht_box': [2, 5, 6, 10], 'licht_r': 9}):
            print('Laterne nicht gesetzt:', tx, ty)
    gitter = 'dach/00' if os.path.exists(os.path.join(OBJ, 'dach/00.png')) else None
    if gitter:
        for (tx, ty) in GITTER:
            setze(gitter, tx, ty, {'liegend': True, 'schattenlos': True})
        for (x0, x1, ty) in GITTERREIHEN:
            for tx in range(x0, x1 + 1, 2):
                setze(gitter, tx, ty, {'liegend': True, 'schattenlos': True})
        for i, (tx, ty) in enumerate(KABEL):
            setze('dach/02', tx, ty, {'liegend': True}, i % 2 == 1)
        setze('dach/03', 24, 22, {'liegend': True, 'schattenlos': True})          # Dachluke
        for (tx, ty) in ((14, 23), (33, 23)):                                     # zwei Klimageraete am Weg
            setze('dach/01', tx, ty, {'anim': 'portal_box', 'wirbel': [11.5, 8.5, 5]})   # Luefterrad dreht sich
        setze('dach/04', 33, 9, {})                                               # Satellitenschuessel (sparsam)
        for (tx, ty) in ((17, 12), (25, 17)):                                     # Lueftungshauben auf der Flaeche
            setze('dach/38', tx, ty, {})
    json.dump(objekte, open(os.path.join(OBJ, 'platzierung.json'), 'w'), indent=0)
    print(len(objekte), 'Objekte')


if __name__ == '__main__':
    main()
    import regeln_a02
    regeln_a02.objekte_pruefen('karte37', '')
