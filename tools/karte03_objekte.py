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
FUSS = {'baeume': 'baum', 'tor': 'stein', 'klein': 'klein', 'mittel': 'stein', 'gross': 'stein', 'pyramide': 'stein', 'pyramide2': 'stein'}
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
    ('gross/06', 44, 31, {}), ('klein/18', 48, 31, {'anim': 'flagge'}), ('mittel2/00', 49.8, 31, {'anim': 'schall'}),
    # Ruinen-Arena
    ('abgeleitet/arena_tor', 54.5, 28, {'ueber_mauer': True, 'roh': True}),
    ('mittel/03', 74, 8, {}), ('mittel/03', 86, 13, {}), ('mittel/03', 74, 19, {}), ('mittel/03', 78, 25, {}),
    ('mittel/04', 59, 15, {}), ('mittel/05', 77, 9, {}), ('mittel/05', 84.5, 9, {}), ('mittel/05', 71, 23, {}),
    ('klein/20', 70, 11, {}), ('klein/20', 81, 23, {}), ('klein/21', 66, 13, {}), ('klein/21', 47, 13, {}),
    # Garten im Nordosten
    ('gross/10', 95.2, 13, {}), ('klein/31', 92.2, 21, {}), ('klein/31', 98.8, 21, {}),
    # Lautsprechersaeulen an den Wegen
    ('mittel2/00', 66.5, 26, {'anim': 'schall'}), ('mittel2/00', 92.5, 26, {'anim': 'schall'}), ('mittel2/00', 52.3, 40, {'anim': 'schall'}), ('mittel2/00', 25, 56, {'anim': 'schall'}),
    ('mittel2/00', 40.5, 63, {'anim': 'schall'}),
    # Server-Feld mit Antennen (auf den Kabelknoten)
    ('gross2/00', 62.5, 41, {'anim': 'blinken', 'dreh': True}), ('gross2/01', 66.5, 48, {'anim': 'blinken', 'dreh': True}),
    ('gross2/00', 70.5, 37, {'anim': 'blinken', 'dreh': True}), ('gross2/01', 74.5, 45, {'anim': 'blinken', 'dreh': True}),
    ('gross2/00', 78.5, 49, {'anim': 'blinken', 'dreh': True}), ('gross2/01', 82.5, 43, {'anim': 'blinken', 'dreh': True}),
    ('gross/13', 86, 35, {'anim': 'blinken'}),
    # Pyramide, Grabtor, Buehne
    ('PYRAMIDE', 96, 41, {}), ('mittel/10', 86.5, 41, {}),
    ('abgeleitet/buehne', 96, 52, {'roh': True, 'proz': 'buehne', 'anim': 'musik'}),
    ('abgeleitet/box_monitor', 90.5, 56, {'roh': True, 'proz': 'box_monitor', 'anim': 'bass'}),
    ('abgeleitet/box_monitor', 101.5, 56, {'roh': True, 'proz': 'box_monitor', 'anim': 'bass'}),
    ('mittel3/01', 89, 62, {'anim': 'flagge'}), ('mittel3/01', 103, 62, {'anim': 'flagge'}),
    # Mitte / Sueden
    ('mittel3/00', 78, 54, {'anim': 'leuchten'}), ('mittel/06', 44.5, 54, {}),
    ('mittel/07', 37, 44, {}), ('mittel/07', 26, 75, {}), ('mittel/07', 95, 74, {}),
    # grosse Sandfelsen (statt der Lehmflaechen)
    ('gross2/03', 44.5, 49, {}), ('mittel2/02', 33, 53, {}), ('mittel2/03', 27, 63, {}), ('gross2/03', 39.5, 70, {}),
    ('mittel2/02', 48.5, 70, {}), ('gross2/03', 63, 71, {}), ('mittel2/04', 77, 70, {}), ('mittel2/05', 83.5, 73, {}),
    ('mittel2/11', 57, 72, {}), ('mittel2/15', 19, 72, {}),
    # Zeltlager am Fluss
    ('gross/04', 9, 54, {}), ('gross/05', 20.5, 54, {}), ('gross/04', 20.5, 66, {}),
    ('klein/15', 23.5, 49, {'anim': 'feuer'}), ('klein/15', 6.5, 67, {'anim': 'feuer'}), ('klein/16', 12.5, 56, {'anim': 'feuer'}),
    ('klein/13', 10.5, 62, {}), ('klein/14', 11.7, 62, {}), ('klein/13', 22.5, 62, {}), ('klein/28', 8.5, 64, {}),
    ('klein/43', 7.5, 57, {}),
]
ZAUN = [(x, 56) for x in range(58, 85, 3)]   # auf dem Sand oberhalb des Weges
STREU_BLUETEN = {'blueten/00': 3, 'blueten/01': 3, 'blueten/02': 2, 'blueten/03': 2, 'blueten/04': 1, 'blueten/05': 2,
                 'mittel2/06': 1, 'mittel2/07': 1, 'mittel2/08': 1, 'mittel2/12': 1}
STREU = {'klein/00': 3, 'klein/01': 3, 'klein/02': 2, 'klein/03': 2, 'klein/04': 4, 'klein/05': 5, 'klein/06': 1,
         'klein/07': 2, 'klein/08': 3, 'klein/09': 3, 'klein/26': 2, 'klein/27': 2}


BLUETEN = ['blueten/00', 'blueten/01', 'blueten/02', 'blueten/03', 'blueten/04', 'blueten/05',
           'mittel2/06', 'mittel2/07', 'mittel2/08', 'mittel2/09', 'mittel2/12', 'mittel2/13']
ROSA = [(0x7a, 0x2a, 0x5a), (0xb2, 0x3c, 0x82), (0xe0, 0x60, 0xa8), (0xf5, 0x9a, 0xcb), (0xff, 0xd2, 0xe8)]


KAKTEEN = ('klein/00', 'klein/01', 'klein/02', 'klein/03', 'mittel2/06', 'mittel2/07', 'mittel2/08', 'mittel2/12',
           'mittel2/13', 'mittel/07', 'baeume/04', 'baeume/05')


def anim_fuer(name):
    """Kakteen wiegen sich leicht und ihre Blueten leuchten, Buesche/Steppenlaeufer wehen, Steine ruhen."""
    if name.startswith('rosa/') or name.startswith('blueten/') or name in KAKTEEN:
        return {'anim': 'kaktus'}
    if name in ('klein/04', 'klein/05', 'klein/26'):
        return {'anim': 'wehen'}
    return {}


def garten_ring():
    """Ring aus Palmen, Kakteen und Wuestenbaeumen um den Garten (statt Ziegelmauer), offen nach Sueden."""
    import math
    pflanzen = ['mittel/00', 'baeume/00', 'mittel2/12', 'baeume/02', 'mittel/01', 'baeume/01', 'mittel2/07',
                'baeume/03', 'mittel/02', 'baeume/05', 'mittel2/06', 'baeume/00']
    cx, cy, rx, ry = 95.5, 12.6, 6.9, 7.2
    out = []
    winkel = [w for w in range(-90 + 18, 270 - 18, 26) if not (60 < w < 120)]   # Sueden (90 Grad) offen
    for i, w in enumerate(winkel):
        n = pflanzen[i % len(pflanzen)]
        if n.startswith('baeume/') and not os.path.exists(os.path.join(OBJ, n + '.png')):
            n = 'mittel/0%d' % (i % 3)
        x = cx + rx * math.cos(math.radians(w)); y = cy + ry * math.sin(math.radians(w))
        opt = anim_fuer(n) if n in KAKTEEN else {'anim': 'wehen'}
        out.append((n, round(x, 1), round(y, 1), opt))
    return out


def rosa_machen(name):
    """Rote/orange Bluetenpixel eines Kaktus nach Helligkeit auf Rosatoene umfaerben -> rosa/<name>.png"""
    import colorsys
    im = Image.open(os.path.join(OBJ, name + '.png')).convert('RGBA')
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            r_, g_, b_, a_ = px[x, y]
            if not a_:
                continue
            h, s_, v = colorsys.rgb_to_hsv(r_ / 255, g_ / 255, b_ / 255)
            if (h < 0.11 or h > 0.93) and s_ > 0.45 and v > 0.35 and r_ > g_ + 40:
                i = min(4, int(v * 5.2) - 1)
                px[x, y] = ROSA[max(0, i)] + (a_,)
    ziel = os.path.join(OBJ, 'rosa', name.replace('/', '-') + '.png')
    os.makedirs(os.path.dirname(ziel), exist_ok=True)
    im.save(ziel)
    return 'rosa/' + name.replace('/', '-')


def lade(name, cache={}):
    if name not in cache:
        cache[name] = Image.open(os.path.join(OBJ, name + '.png')).convert('RGBA')
    return cache[name]


def main():
    import karte03_bauen as k3
    import karte03_prozedural as kp
    kp.statisch_speichern()
    os.makedirs(os.path.join(OBJ, 'abgeleitet'), exist_ok=True)
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
    mauer = np.zeros((MH, MW), bool)
    for (x, y) in tm.get('arena', []) + tm.get('garten', []):
        gesperrt[max(0, y * T - 26):(y + 1) * T + 4, x * T:(x + 1) * T + 4] = True
    for (x, y) in tm.get('arena', []):
        mauer[max(0, y * T - 22):(y + 1) * T, x * T:(x + 1) * T] = True
    for (x, y) in tm.get('garten', []):
        mauer[max(0, y * T - 12):(y + 1) * T, x * T + 2:(x + 1) * T - 2] = True
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
        art = 'pflanze' if basis in PALMEN or basis in KAKTEEN or gruppe == 'rosa' or basis in ('klein/00', 'klein/01', 'klein/02', 'klein/03', 'klein/04', 'klein/05') else FUSS.get(gruppe, 'stein')
        vname = 'varianten/%s_%s' % (basis.replace('/', '-'), boden)
        pfad = os.path.join(OBJ, vname + '.png')
        if not os.path.exists(pfad):
            os.makedirs(os.path.join(OBJ, 'varianten'), exist_ok=True)
            bauwerke.bodenfuss(lade(basis), boden, art).save(pfad)
        if opt.pop('roh', False):                      # Sprite ohne Bodenfuss (steht auf dem Weg)
            vname = basis
        im = lade(vname)
        x, y = int(ax - im.width // 2), int(ay + 3 - im.height)
        a = np.array(im.getchannel('A')) >= 200
        xs0, ys0, xs1, ys1 = max(0, x), max(0, y), min(MW, x + im.width), min(MH, y + im.height)
        a = a[ys0 - y:ys1 - y, xs0 - x:xs1 - x]
        if fest and not opt.pop('ueber_mauer', False) and (mauer[ys0:ys1, xs0:xs1] & a).any():
            print('  auf Mauer, uebersprungen:', name, ax // T, ay // T)
            return None
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

    for name, tx, ty, opt in FEST + garten_ring():
        if 'anim' not in opt:
            opt = dict(opt, **anim_fuer(name))
        setze(name, tx * T, ty * T + 15, True, opt)
    for (tx, ty) in ZAUN:
        setze('klein/22', tx * T + 8, ty * T + 12, True)
    rosa = {n: rosa_machen(n) for n in BLUETEN}
    streu = dict(STREU)
    for n, w in STREU_BLUETEN.items():
        streu[rosa[n]] = w
    namen, gew = list(streu), list(streu.values())
    gesetzt = 0
    for _ in range(9000):
        if gesetzt >= 125:
            break
        cx, cy = rnd.randrange(5, cols - 6), rnd.randrange(4, rows - 4)
        if cy <= 5 or cy >= 73 or cx >= 104:            # Abstand zu den Sandwaenden
            continue
        if cls[cy][cx] != 's' or rnd.random() < 0.4:   # nur auf Sand, nicht auf Pflaster
            continue
        n = rnd.choices(namen, weights=gew)[0]
        if setze(n, cx * T + rnd.randint(3, 13), cy * T + rnd.randint(8, 15), False, anim_fuer(n)):
            gesetzt += 1
    json.dump(objekte, open(os.path.join(OBJ, 'platzierung.json'), 'w'), indent=0)
    print(len(objekte), 'Objekte gesetzt')


if __name__ == '__main__':
    main()
