"""Objekte fuer Karte 05 (Freezeland) - ALLE am 16x16-Raster.

  python3 tools/karte05_objekte.py && python3 tools/karte05_bauen.py

Jedes Objekt steht mit der Fussmitte auf der Mitte einer Kachel, unterste deckende Zeile 2 px ueber der
Kachelunterkante. Je Kachel hoechstens ein hohes und ein flaches Objekt. Feste Objekte in Kachelkoordinaten
aus der Vorlage, Baumgruppen und Deko als Zonen. Waldrand (Klasse h) dicht mit Tannen, ohne Animation.
"""
import json, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
from karte04_objekte import saeubern
from karte05_pruefen import bewerten

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte05')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte05')
T = 16
TANNEN = ['baeume/00', 'baeume/01', 'baeume/02', 'baeume/00', 'baeume/01']
KLEINE_TANNEN = ['klein/27', 'klein/49', 'klein/27', 'klein/49', 'baeume/01']

# (sprite, Kachel-x, Kachel-y [Fusskachel], Optionen)
FEST = [
    # Eishoehle in der Klippe, Mammut-Stosszaehne
    ('gross/01', 63, 10, {}), ('gross/02', 86, 47, {}),
    # Dorf: Iglus, Laternen, Lager, Feuer, Fahne
    ('gross/00', 21, 66, {}), ('gross/00', 39, 66, {}), ('gross/00', 21, 77, {}),
    ('mittel/08', 24, 70, {'anim': 'leuchten'}), ('mittel/08', 37, 70, {'anim': 'leuchten'}),
    ('mittel/08', 27, 78, {'anim': 'leuchten'}), ('mittel/08', 36, 78, {'anim': 'leuchten'}),
    ('mittel/07', 30, 73, {'anim': 'feuer'}), ('mittel/14', 35, 67, {'anim': 'fahne'}),
    ('mittel/05', 23, 70, {}), ('mittel/06', 40, 69, {}), ('mittel/06', 40, 77, {}), ('mittel/12', 26, 73, {}),
    ('mittel/13', 33, 76, {}), ('mittel/04', 38, 72, {}), ('klein/63', 28, 70, {}),
    # Wegweiser
    ('mittel/04', 38, 55, {}), ('mittel/04', 99, 7, {}), ('mittel/04', 93, 52, {}),
    # Eisbloecke und Eisspitzen
    
    
    
    ('mittel/02', 92, 55, {'anim': 'glitzern'}), ('mittel/02', 96, 57, {'anim': 'glitzern'}),
    ('mittel/02', 99, 58, {'anim': 'glitzern'}), ('mittel/02', 75, 24, {'anim': 'glitzern'}),
    ('mittel/02', 102, 68, {'anim': 'glitzern'}), ('mittel/02', 48, 78, {'anim': 'glitzern'}),
    ('mittel/02', 41, 82, {'anim': 'glitzern'}), ('mittel/02', 69, 16, {'anim': 'glitzern'}),
    # Schneemaenner
    ('mittel/03', 70, 57, {}), ('mittel/03', 62, 61, {}), ('mittel/03', 64, 68, {}), ('mittel/03', 86, 65, {}),
    ('mittel/03', 92, 58, {}),
    # Eisangeln am See
    
    # Felsbrocken
    ('mittel/00', 14, 11, {}), ('mittel/00', 30, 11, {}), ('mittel/00', 56, 13, {}), ('mittel/00', 42, 56, {}),
    ('mittel/00', 84, 25, {}), ('mittel/00', 94, 47, {}),
    ('mittel/00', 13, 65, {}), ('mittel/00', 43, 73, {}), ('mittel/00', 82, 74, {}), ('mittel/00', 98, 74, {}),
    ('mittel/00', 59, 14, {}), ('mittel/09', 75, 74, {}), ('mittel/15', 102, 63, {}),
    # Holzhuette am rechten Weg
    ('gross/03', 100, 11, {}),
    # Schlitten und Feuerholz am Lager rechts unten
    ('mittel/13', 94, 70, {}), ('mittel/12', 97, 70, {}),
]
# Baumgruppen (x0, y0, x1, y1, Dichte) - Tannen nur auf Schnee/Eisboden, nicht auf Wegen
HAINE = [
    (14, 21, 28, 31, 0.30), (27, 17, 34, 22, 0.30), (5, 33, 14, 58, 0.22), (27, 43, 36, 48, 0.35),
    (45, 52, 52, 58, 0.22), (73, 54, 80, 66, 0.18), (80, 55, 103, 67, 0.08), (66, 66, 103, 80, 0.12),
    (36, 78, 66, 80, 0.25), (5, 59, 18, 80, 0.12), (90, 8, 103, 20, 0.06), (6, 9, 15, 18, 0.15),
    
]
STREU = {'klein/00': 6, 'klein/01': 4, 'klein/02': 2, 'klein/03': 3, 'klein/04': 2, 'klein/05': 3, 'klein/06': 2,
         'klein/07': 2, 'klein/13': 2, 'klein/17': 3, 'klein/18': 2, 'klein/11': 1, 'klein/10': 1, 'klein/55': 2,
         'klein/45': 1, 'klein/39': 1}
FLACH = {'klein/00', 'klein/01', 'klein/02', 'klein/03', 'klein/04', 'klein/05', 'klein/07', 'klein/13',
         'klein/17', 'klein/18', 'klein/11', 'klein/10', 'klein/55', 'klein/45', 'klein/15', 'klein/19'}


def main():
    rnd = random.Random(5)
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cls = lay['klassen']
    hoehe = [[int(c) for c in r] for r in lay['hoehe']]
    cols, rows = lay['groesse']
    os.makedirs(os.path.join(OBJ, 'sauber'), exist_ok=True)
    belegt = set()
    gesperrt = set()
    for (x0, x1, y0, y1, _r) in lay.get('treppen', []):
        for y in range(y0, y1 + 3):
            for x in range(x0 - 1, x1 + 2):
                gesperrt.add((x, y))
    for (x0, y0, x1, y1) in lay.get('bruecken', []) + lay.get('stege', []):
        for y in range(y0 - 1, y1 + 2):
            for x in range(x0 - 1, x1 + 2):
                gesperrt.add((x, y))
    for tp in lay.get('teleporter', []):
        for y in range(tp['y'] - 1, tp['y'] + tp['h'] + 1):
            for x in range(tp['x'] - 1, tp['x'] + tp['b'] + 1):
                gesperrt.add((x, y))
    # Kacheln unter Klippenfronten (Hoehe 2 -> 1): 4 Zeilen unter der Plateaukante gesperrt
    for x in range(cols):
        for y in range(rows - 1):
            if hoehe[y][x] == 2 and hoehe[y + 1][x] < 2:
                for k in range(1, 5):
                    gesperrt.add((x, y + k))
            for dx in (-1, 1):
                if 0 <= x + dx < cols and hoehe[y][x] == 2 and hoehe[y][x + dx] < 2:
                    gesperrt.add((x + dx, y))
    cache = {}
    objekte = []

    def sprite(name, spiegeln):
        key = (name, spiegeln)
        if key not in cache:
            sp = saeubern(Image.open(os.path.join(OBJ, name + '.png')).convert('RGBA'))
            if name == 'gross/01':                       # Hoehle: rechteckigen Hintergrund als Bogen freistellen
                a = np.array(sp)
                h_, w_ = a.shape[:2]
                yy, xx = np.mgrid[0:h_, 0:w_]
                # Bogen etwas schmaler als das Bild (keine senkrechte Schnittkante unten), Rand unregelmaessig wie Fels
                rs_ = np.random.RandomState(4)
                zacke = np.repeat(rs_.randint(0, 4, size=h_ // 3 + 2), 3)[:h_][:, None]
                rx_ = w_ * 0.47 - zacke
                bogen = ((xx - w_ / 2) / rx_) ** 2 + ((yy - h_) / (h_ * 0.96)) ** 2 <= 1
                a[~bogen, 3] = 0
                # Kontur an der Schnittkante: dunkler Eisrand innen, damit die Kante sauber wie Fels wirkt
                innen = bogen & ~(np.roll(bogen, 1, 1) & np.roll(bogen, -1, 1) & np.roll(bogen, 1, 0))
                innen[-1] = False
                a[innen, :3] = (36, 52, 84)
                innen2 = bogen & ~innen & ~(np.roll(bogen, 2, 1) & np.roll(bogen, -2, 1))
                a[innen2, :3] = (a[innen2, :3] * 0.75).astype(np.uint8)
                sp = Image.fromarray(a)
            if spiegeln:
                sp = sp.transpose(Image.FLIP_LEFT_RIGHT)
            datei = 'sauber/%s%s.png' % (name.replace('/', '-'), '_m' if spiegeln else '')
            sp.save(os.path.join(OBJ, datei))
            a = np.array(sp.getchannel('A')) >= 128
            zu = int(np.nonzero(a.any(axis=1))[0].max())
            sp_ = np.nonzero(a[max(0, zu - 2):zu + 1].any(axis=0))[0]
            cache[key] = (datei, sp.height, zu, (sp_.min() + sp_.max() + 1) / 2.0)
        return cache[key]

    lvl = np.load(os.path.join(KARTE, 'pixelhoehe.npy')) if os.path.exists(os.path.join(KARTE, 'pixelhoehe.npy')) else None
    alpha = {}
    verschoben, weggelassen = [], 0

    def passt(datei, x, y, rand_ok):
        if lvl is None:
            return True
        if datei not in alpha:
            alpha[datei] = np.array(Image.open(os.path.join(OBJ, datei)).getchannel('A')) >= 128
        ok, grund = bewerten(lvl, alpha[datei], x, y)
        return ok or (rand_ok and grund == 'ragt aus der Karte')

    def setze(name, tx, ty, opt, pruefen=False, fest=False, rand_ok=False):
        nonlocal weggelassen
        opt = dict(opt)
        spiegeln = opt.pop('spiegeln', False)
        art = 'flach' if name in FLACH else 'hoch'
        datei, h, zu, mitte = sprite(name, spiegeln)
        kandidaten = [(tx, ty)]
        if fest:                                  # feste Objekte: naechste passende Kachel suchen
            kandidaten += sorted(((tx + dx, ty + dy) for dx in range(-4, 5) for dy in range(-4, 5) if dx or dy),
                                 key=lambda k: (abs(k[0] - tx) + abs(k[1] - ty), -k[1]))
        for (kx, ky) in kandidaten:
            if (kx, ky, art) in belegt:
                continue
            if pruefen or (fest and (kx, ky) != (tx, ty)):
                if not (0 <= kx < cols and 0 <= ky < rows) or (kx, ky) in gesperrt:
                    continue
                if art == 'hoch' and any((kx + dx, ky, 'hoch') in belegt for dx in (-1, 1)):
                    continue
            x, y = int(round(kx * T + T / 2 - mitte)), int(ky * T + T - 2 - zu)
            if passt(datei, x, y, rand_ok):
                break
        else:
            weggelassen += 1
            if fest:
                print('  keine passende Stelle:', name, (tx, ty))
            return False
        if (kx, ky) != (tx, ty):
            verschoben.append((name, (tx, ty), (kx, ky)))
        tx, ty = kx, ky
        o = {'datei': datei, 'basis': name, 'x': x, 'y': y,
             'fuss': h, 'kachel': [tx, ty], 'ebene': 0 if art == 'flach' else 1}
        o.update(opt)
        objekte.append(o)
        belegt.add((tx, ty, art))
        return True

    for (name, tx, ty, opt) in FEST:
        setze(name, tx, ty, opt, fest=True)
    # Waldrand: jede zweite Kachel eine Tanne (versetzt), keine Animation
    for ty in range(rows):
        for tx in range(cols):
            if cls[ty][tx] == 'h' and (tx + ty) % 2 == 0 and (tx, ty) not in gesperrt:
                setze(rnd.choice(TANNEN), tx, ty, {'spiegeln': rnd.random() < 0.5}, rand_ok=True)
    # Haine im Schneefeld (Wind)
    for (x0, y0, x1, y1, dichte) in HAINE:
        for ty in range(y0, y1 + 1):
            for tx in range(x0, x1 + 1):
                if cls[ty][tx] in 'sl' and rnd.random() < dichte:
                    n = 'baeume/03' if rnd.random() < 0.05 else rnd.choice(KLEINE_TANNEN)
                    setze(n, tx, ty, {'anim': 'baum', 'spiegeln': rnd.random() < 0.5}, pruefen=True)
    # Streudeko
    namen, gew = list(STREU), list(STREU.values())
    gesetzt = 0
    for _ in range(6000):
        if gesetzt >= 230:
            break
        tx, ty = rnd.randrange(3, cols - 6), rnd.randrange(6, rows - 4)
        if cls[ty][tx] not in 'slr' or hoehe[ty][tx] != 1:
            continue
        n = rnd.choices(namen, weights=gew)[0]
        if setze(n, tx, ty, {'anim': 'wehen'} if n in ('klein/00', 'klein/55', 'klein/13') else
                 {'anim': 'glitzern'} if n in ('klein/02', 'klein/39', 'klein/45') else {}, pruefen=True):
            gesetzt += 1
    json.dump(objekte, open(os.path.join(OBJ, 'platzierung.json'), 'w'), indent=0)
    for v in verschoben:
        print('  verschoben:', v[0], v[1], '->', v[2])
    print(len(objekte), 'Objekte am Raster gesetzt,', weggelassen, 'unpassende Stellen ausgelassen')


if __name__ == '__main__':
    main()
