"""Objekte fuer Karte 03 (Server Desert): feste Positionen aus der Vorlage + verstreute Wuestendeko.

  python3 tools/karte03_objekte.py && python3 tools/karte03_bauen.py

Sprites: assets/objekte/karte03/<gruppe>/NN.png (PixelLab-Objekt-Manager, Gruppen k3_*).
Regeln wie Karte 01/02: Bodenfuss nach Untergrund (Sand/Gras/Stein), Pixel-Kollision fuer verstreute
Objekte, nichts auf Wasser, Mauern, Wegen oder dem Buehnenplatz (ausser gezielt gesetzt).
"""
import json, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
import bauwerke

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte03')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte03')
T = 16
FUSS = {'klein': 'klein', 'mittel': 'stein', 'gross': 'stein', 'pyramide': 'stein', 'pyramide2': 'stein'}
PALMEN = ('mittel/00', 'mittel/01', 'mittel/02', 'klein/25')

# (sprite, Anker-x Kachel (Mitte), Anker-y = unterste Kachelzeile, Optionen)
FEST = [
    # Dorf an der Oase
    ('gross/01', 25, 10, {}), ('gross/00', 8.5, 15, {}), ('gross/02', 29, 15, {}), ('gross/03', 8, 34, {}),
    ('mittel/09', 10.5, 40, {}), ('klein/29', 21, 33, {}), ('klein/11', 12, 31, {}), ('klein/10', 31.5, 32, {}),
    ('mittel/00', 14.5, 13, {'anim': 'wehen'}), ('mittel/01', 29.5, 19, {'anim': 'wehen'}),
    ('mittel/00', 31, 23, {'anim': 'wehen'}), ('mittel/02', 10.5, 22, {'anim': 'wehen'}),
    ('mittel/01', 12.5, 29, {'anim': 'wehen'}), ('mittel/00', 26.5, 30, {'anim': 'wehen'}),
    ('klein/05', 22, 16, {}), ('klein/05', 26, 26, {}), ('klein/04', 11, 26, {}),
    # Bus und Haltestelle
    ('gross/06', 44, 31, {}), ('klein/18', 48, 31, {}), ('klein/17', 49.5, 31, {}),
    # Ruinen-Arena
    ('gross/11', 54.5, 27, {}),
    ('mittel/03', 74, 8, {}), ('mittel/03', 86, 13, {}), ('mittel/03', 74, 19, {}), ('mittel/03', 78, 25, {}),
    ('mittel/04', 59, 15, {}), ('mittel/05', 77, 9, {}), ('mittel/05', 89, 9, {}), ('mittel/05', 62.5, 23, {}),
    ('klein/20', 70, 11, {}), ('klein/20', 81, 23, {}), ('klein/21', 66, 13, {}), ('klein/21', 47, 13, {}),
    ('klein/20', 47, 21, {}),
    # Garten im Nordosten
    ('gross/10', 99.5, 10, {}), ('klein/31', 97.5, 16, {}), ('klein/31', 104.5, 16, {}), ('klein/12', 101, 12, {}),
    ('klein/05', 98, 13, {}), ('klein/04', 104, 13, {}),
    # Lautsprechersaeulen an den Wegen
    ('klein/17', 62.5, 26, {}), ('klein/17', 98.5, 26, {}), ('klein/17', 52.5, 40, {}), ('klein/17', 25, 56, {}),
    ('klein/17', 40.5, 63, {}),
    # Server-Feld mit Antennen (auf den Kabelknoten)
    ('gross/08', 62.5, 41, {'anim': 'blinken'}), ('gross/09', 66.5, 48, {'anim': 'blinken'}),
    ('gross/08', 70.5, 37, {'anim': 'blinken'}), ('gross/09', 74.5, 45, {'anim': 'blinken'}),
    ('gross/08', 78.5, 49, {'anim': 'blinken'}), ('gross/09', 82.5, 43, {'anim': 'blinken'}),
    ('mittel/12', 80, 34, {'anim': 'leuchten'}), ('gross/13', 86, 35, {'anim': 'blinken'}),
    # Pyramide, Grabtor, Buehne
    ('PYRAMIDE', 101, 41, {}), ('mittel/10', 89.5, 41, {}),
    ('gross/07', 100.5, 48, {'anim': 'musik'}),
    ('klein/30', 93, 48, {}), ('klein/30', 107, 48, {}), ('klein/30', 88, 52, {}), ('klein/30', 104.5, 52, {}),
    ('klein/18', 92, 57, {}), ('klein/18', 104, 56, {}),
    # Mitte / Sueden
    ('mittel/11', 78, 54, {'anim': 'leuchten'}), ('mittel/06', 44.5, 54, {}), ('mittel/12', 86.5, 69, {'anim': 'leuchten'}),
    ('mittel/07', 37, 44, {}), ('mittel/07', 46.5, 44, {}), ('mittel/07', 26, 75, {}), ('mittel/07', 78, 74, {}),
    # Zeltlager am Fluss
    ('gross/04', 9, 54, {}), ('gross/05', 20.5, 54, {}), ('gross/04', 20.5, 66, {}),
    ('klein/15', 23.5, 49, {'anim': 'feuer'}), ('klein/15', 6.5, 67, {'anim': 'feuer'}), ('klein/16', 12.5, 56, {'anim': 'feuer'}),
    ('klein/13', 10.5, 62, {}), ('klein/14', 11.7, 62, {}), ('klein/13', 22.5, 62, {}), ('klein/28', 8.5, 64, {}),
    ('klein/43', 7.5, 57, {}),
]
ZAUN = [(x, 58) for x in range(55, 87, 3)]
STREU = {'klein/00': 3, 'klein/01': 3, 'klein/02': 2, 'klein/03': 2, 'klein/04': 4, 'klein/05': 5, 'klein/06': 1,
         'klein/07': 2, 'klein/08': 3, 'klein/09': 3, 'klein/26': 2, 'klein/27': 2}


def lade(name, cache={}):
    if name not in cache:
        cache[name] = Image.open(os.path.join(OBJ, name + '.png')).convert('RGBA')
    return cache[name]


def main():
    rnd = random.Random(5)
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    tm = json.load(open(os.path.join(KARTE, 'tilemap.json')))
    cls = tm['klassen']
    cols, rows = lay['groesse']
    MW, MH = cols * T, rows * T
    b = np.array(Image.open(os.path.join(KARTE, 'terrain_basis.png')).convert('RGB')).astype(np.int16)
    gras = (b[..., 1] > b[..., 0] + 25) & (b[..., 1] > b[..., 2] + 25)
    pyr = 'pyramide2/00' if os.path.exists(os.path.join(OBJ, 'pyramide2', '00.png')) else 'pyramide/00'

    gesperrt = np.zeros((MH, MW), bool)
    for y in range(rows):
        for x in range(cols):
            if cls[y][x] in 'xwpd':
                gesperrt[y * T:(y + 1) * T, x * T:(x + 1) * T] = True
    for (x, y) in tm.get('arena', []) + tm.get('garten', []):
        gesperrt[max(0, y * T - 26):(y + 1) * T + 4, x * T:(x + 1) * T + 4] = True
    for (a, c) in lay.get('kabel', []):
        (ax, ay), (bx, by) = a, c
        gesperrt[min(ay, by) * T:(max(ay, by) + 1) * T, min(ax, bx) * T:(max(ax, bx) + 1) * T] = True
    belegt = np.zeros((MH, MW), bool)
    objekte = []

    def boden_bei(ax, ay):
        x, y = min(max(int(ax), 0), MW - 1), min(max(int(ay) - 1, 0), MH - 1)
        if gras[y, x]:
            return 'gras'
        return 'beton' if cls[y // T][x // T] in 'kp' else 'sand'

    def setze(name, ax, ay, fest=True, opt=None):
        opt = dict(opt or {})
        basis = pyr if name == 'PYRAMIDE' else name
        gruppe = basis.split('/')[0]
        boden = boden_bei(ax, ay)
        art = 'pflanze' if basis in PALMEN or basis in ('klein/00', 'klein/01', 'klein/02', 'klein/03', 'klein/04', 'klein/05') else FUSS.get(gruppe, 'stein')
        vname = 'varianten/%s_%s' % (basis.replace('/', '-'), boden)
        pfad = os.path.join(OBJ, vname + '.png')
        if not os.path.exists(pfad):
            os.makedirs(os.path.join(OBJ, 'varianten'), exist_ok=True)
            bauwerke.bodenfuss(lade(basis), boden, art).save(pfad)
        im = lade(vname)
        x, y = int(ax - im.width // 2), int(ay + 3 - im.height)
        a = np.array(im.getchannel('A')) >= 200
        xs0, ys0, xs1, ys1 = max(0, x), max(0, y), min(MW, x + im.width), min(MH, y + im.height)
        a = a[ys0 - y:ys1 - y, xs0 - x:xs1 - x]
        if not fest:
            if ((belegt[ys0:ys1, xs0:xs1] | gesperrt[ys0:ys1, xs0:xs1]) & a).any():
                return None
            fy = min(MH - 1, int(ay))
            if gras[fy, min(MW - 1, int(ax))]:
                return None
        belegt[ys0:ys1, xs0:xs1] |= a
        o = {'datei': vname + '.png', 'basis': basis, 'x': x, 'y': y, 'fuss': im.height, 'ebene': 1}
        o.update(opt)
        objekte.append(o)
        return o

    for name, tx, ty, opt in FEST:
        setze(name, tx * T, ty * T + 15, True, opt)
    for (tx, ty) in ZAUN:
        setze('klein/22', tx * T + 8, ty * T + 12, True)
    namen, gew = list(STREU), list(STREU.values())
    gesetzt = 0
    for _ in range(9000):
        if gesetzt >= 105:
            break
        cx, cy = rnd.randrange(5, cols - 6), rnd.randrange(4, rows - 4)
        if cls[cy][cx] not in 'sk' or rnd.random() < 0.4:
            continue
        if setze(rnd.choices(namen, weights=gew)[0], cx * T + rnd.randint(3, 13), cy * T + rnd.randint(8, 15), False,
                 {'anim': 'wehen'} if rnd.random() < 0.5 else {}):
            gesetzt += 1
    json.dump(objekte, open(os.path.join(OBJ, 'platzierung.json'), 'w'), indent=0)
    print(len(objekte), 'Objekte gesetzt')


if __name__ == '__main__':
    main()
