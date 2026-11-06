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
FUSS = {'palmen': 'baum', 'baeume': 'baum', 'tor': 'stein', 'klein': 'klein', 'mittel': 'stein', 'gross': 'stein', 'pyramide': 'stein', 'pyramide2': 'stein'}
PALMEN_NEU = ['palmen/%02d' % i for i in range(12)]          # v1.1: neue Palmen (PixelLab k3_palmen_a/b/c)
PALMEN = ('mittel/00', 'mittel/01', 'mittel/02', 'klein/25') + tuple(PALMEN_NEU)
BEGLEITER = ['klein/02', 'klein/04', 'klein/05', 'klein/08', 'klein/09', 'klein/10', 'klein/11', 'klein/28', 'klein/03']

# (sprite, Anker-x Kachel (Mitte), Anker-y = unterste Kachelzeile, Optionen)
FEST = [
    # Dorf an der Oase
    ('gross/01', 25, 10, {}), ('gross/00', 10.5, 15, {}), ('gross/02', 29, 15, {}), ('gross/03', 10.5, 34, {}),
    ('mittel/09', 11.5, 40, {}), ('klein/29', 21, 33, {}), ('klein/11', 12, 31, {}), ('klein/10', 31.5, 32, {}),
    ('palmen/05', 14.5, 13, {'anim': 'wehen'}), ('palmen/10', 29.5, 19, {'anim': 'wehen'}),
    ('palmen/03', 31, 23, {'anim': 'wehen'}), ('palmen/08', 11.5, 22, {'anim': 'wehen'}),
    ('palmen/01', 12.5, 29, {'anim': 'wehen'}), ('palmen/06', 26.5, 30, {'anim': 'wehen'}),
    ('klein/05', 22, 16, {}), ('klein/05', 26, 26, {}), ('klein/04', 11, 26, {}),
    # Bus und Haltestelle
    ('gross/06', 44, 31, {}), ('klein/18', 48, 31, {'anim': 'flagge'}), ('mittel2/00', 49.8, 31, {'anim': 'schall'}),
    # Ruinen-Arena
    ('abgeleitet/arena_tor', 54.5, 28, {'ueber_mauer': True, 'roh': True}),
    ('mittel/03', 74, 8, {}), ('mittel/03', 79, 14, {}), ('mittel/03', 74, 19, {}), ('mittel/03', 78, 25, {}),
    ('mittel/04', 59, 15, {}), ('mittel/05', 77, 9, {}), ('mittel/05', 79.5, 8, {}), ('mittel/05', 71, 23, {}),
    ('klein/20', 70, 11, {}), ('klein/20', 81, 23, {}), ('klein/21', 66, 13, {}), ('klein/21', 47, 13, {}),
    # Garten im Nordosten
    ('gross/10', 95.2, 12, {}), ('klein/31', 92.2, 25, {}), ('klein/31', 98.8, 25, {}),
    # Lautsprechersaeulen an den Wegen
    ('mittel2/00', 66.5, 26, {'anim': 'schall'}), ('mittel2/00', 89.5, 26, {'anim': 'schall'}), ('mittel2/00', 52.3, 40, {'anim': 'schall'}), ('mittel2/00', 25, 56, {'anim': 'schall'}),
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
    ('gross/04', 11, 54, {}), ('gross/05', 20.5, 54, {}), ('gross/04', 20.5, 66, {}),
    ('klein/15', 23.5, 49, {'anim': 'feuer'}), ('klein/15', 9.5, 67, {'anim': 'feuer'}), ('klein/16', 12.5, 56, {'anim': 'feuer'}),
    ('klein/13', 10.5, 62, {}), ('klein/14', 11.7, 62, {}), ('klein/13', 22.5, 62, {}), ('klein/28', 9.5, 64, {}),
    ('klein/43', 9.5, 58, {}),
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
    pflanzen = ['palmen/00', 'baeume/00', 'mittel2/12', 'palmen/06', 'palmen/09', 'baeume/01', 'mittel2/07',
                'palmen/03', 'palmen/10', 'baeume/05', 'mittel2/06', 'palmen/01']
    cx, cy, rx, ry = 95.3, 12.2, 6.2, 4.9           # v1.1: auf dem Sandstrand der Insel
    out = []
    winkel = [w for w in range(-90 + 18, 270 - 18, 30) if not (55 < w < 125)]   # Sueden (90 Grad) offen
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
            if cls[y][x] in 'xmwpd':
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
        fy_, fx_ = min(rows - 1, int(ay) // T), min(cols - 1, max(0, int(ax) // T))
        if cls[fy_][fx_] in 'xm':                          # nie im Wasser (Meer, Teich)
            print('  im Wasser, uebersprungen:', name, int(ax) // T, int(ay) // T)
            return None
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
    # --- v1.1: Palmen als Baeume der Karte (Regel 5: Gruppen + Begleiter; Objekte vor Palmen)
    prnd = random.Random(31)

    def begleiter(o_palme, vorher, pflicht=False):
        """kleines Objekt vor den Stamm: darf nur die eigene Palme ueberdecken (vorher = belegt ohne Palme)"""
        if not pflicht and prnd.random() < 0.3:
            return
        a_ = np.array(Image.open(os.path.join(OBJ, o_palme['datei'])).getchannel('A')) >= 200
        ys_, xs_ = np.nonzero(a_)
        fx = o_palme['x'] + int(xs_[ys_ >= ys_.max() - 2].mean())
        fy = o_palme['y'] + int(ys_.max())
        for _ in range(30 if pflicht else 6):
            bx_ = fx + prnd.choice((-1, 1)) * prnd.randint(6, 18)
            by_ = fy + prnd.randint(3, 10)
            n_ = prnd.choice(BEGLEITER)
            im_ = lade('varianten/%s_%s' % (n_.replace('/', '-'), boden_bei(bx_, by_))) if os.path.exists(os.path.join(OBJ, 'varianten/%s_%s.png' % (n_.replace('/', '-'), boden_bei(bx_, by_)))) else lade(n_)
            x_, y_ = int(bx_ - im_.width // 2), int(by_ + 3 - im_.height)
            m_ = np.array(im_.getchannel('A')) >= 200
            y0_, x0_ = max(0, y_), max(0, x_)
            teil = m_[y0_ - y_:min(MH, y_ + im_.height) - y_, x0_ - x_:min(MW, x_ + im_.width) - x_]
            if ((vorher[y0_:y0_ + teil.shape[0], x0_:x0_ + teil.shape[1]] | gesperrt[y0_:y0_ + teil.shape[0], x0_:x0_ + teil.shape[1]]) & teil).any():
                continue
            o_ = setze(n_, bx_, by_, True, dict(anim_fuer(n_), begleiter=True))
            if o_:
                return

    def palme(tx, ty, fest=False, name=None):
        name = name or prnd.choice(PALMEN_NEU)
        vorher = belegt.copy()
        o_ = setze(name, tx * T + 8, ty * T + 15, fest, {'anim': 'wehen'})
        if o_:
            begleiter(o_, vorher)
        return o_

    # Objekte vor Palmen: hinter Haeusern, Marktstand und Brunnen je eine Palme (Gebaeude ueberdeckt den Stamm)
    for o in list(objekte):
        if o['basis'] in ('gross/00', 'gross/01', 'gross/02', 'gross/03', 'mittel/09') or o['basis'].startswith('klein/29'):
            fx_ = (o['x'] + Image.open(os.path.join(OBJ, o['datei'])).width // 2) // T
            fy_ = (o['y'] + o['fuss']) // T
            seite = prnd.choice((-1, 1))
            # nur die Ueberdeckung mit genau diesem Gebaeude erlauben (Gebaeude steht davor)
            im_h = Image.open(os.path.join(OBJ, o['datei']))
            hm = np.zeros_like(belegt)
            ah = np.array(im_h.getchannel('A')) >= 200
            y0h, x0h = max(0, o['y']), max(0, o['x'])
            teil_h = ah[y0h - o['y']:min(MH, o['y'] + im_h.height) - o['y'], x0h - o['x']:min(MW, o['x'] + im_h.width) - o['x']]
            hm[y0h:y0h + teil_h.shape[0], x0h:x0h + teil_h.shape[1]] = teil_h
            frei_vorher = belegt & hm
            belegt[hm] = False
            for dx_ in (seite * 2, -seite * 2, seite, -seite):
                if palme(fx_ + dx_, fy_ - 1, fest=False):
                    break
            belegt |= frei_vorher
    # Palmenhaine (x0, y0, x1, y1, Anzahl): Oase, Landzungen, Lagune, Pyramide, Sueden
    HAINE_P = [(9, 15, 30, 28, 7), (9, 17, 12, 24, 2), (9, 33, 12, 41, 2), (9, 62, 12, 70, 2), (78, 20, 90, 26, 3),
               (99, 30, 104, 42, 2), (24, 66, 50, 73, 3), (60, 64, 100, 73, 3), (30, 5, 40, 12, 2)]
    for (x0, y0, x1, y1, n) in HAINE_P:
        gesetzt_ = 0
        for _ in range(80):
            if gesetzt_ >= n:
                break
            if palme(prnd.randint(x0, x1), prnd.randint(y0, y1)):
                gesetzt_ += 1
    # Regel 5: jede Palme ohne Nachbarpalme (3 Kacheln) bekommt sicher einen Begleiter
    palmen_ = [o for o in objekte if o['basis'] in PALMEN_NEU]
    for o in palmen_:
        fx_, fy_ = o['x'] + 30, o['y'] + o['fuss']
        nachbar = any(q is not o and abs(q['x'] - o['x']) <= 48 and abs(q['y'] + q['fuss'] - fy_) <= 48 for q in palmen_)
        hat = any(q.get('begleiter') and abs(q['x'] - o['x']) <= 40 and abs(q['y'] + q['fuss'] - fy_) <= 24 for q in objekte)
        if not nachbar and not hat:
            vorher = belegt.copy()
            n_vor = len(objekte)
            begleiter(o, vorher, pflicht=True)
            if len(objekte) > n_vor:
                continue
            kx_, ky_ = (o['x'] + 30) // T, (o['y'] + o['fuss']) // T
            if any(palme(kx_ + dx_, ky_ + dy_) for dx_, dy_ in ((2, 0), (-2, 0), (2, 1), (-2, 1), (3, -1), (-3, -1))):
                continue                                   # Regel 5a: zweiter Baum daneben
            objekte.remove(o)                              # sonst lieber keine einzelne Palme
            print('  einzelne Palme ohne Begleitung entfernt:', o['basis'], kx_, ky_)
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


# Paare exakt symmetrisch zur Achse ihres Bauwerks (Regel 'Symmetrische Plaetze'): (Basis, Achse in px)
PAARE = [('klein/31', 96 * T), ('abgeleitet/box_monitor', 96 * T), ('mittel3/01', 96 * T)]


def symmetrie():
    pf = os.path.join(OBJ, 'platzierung.json')
    objs = json.load(open(pf))
    for basis, achse in PAARE:
        ps = sorted((o for o in objs if o['basis'] == basis), key=lambda o: o['x'])
        if len(ps) != 2:
            print('  Paar unvollstaendig:', basis, len(ps))
            continue
        l, r = ps
        im = Image.open(os.path.join(OBJ, l['datei']))
        a = np.array(im.getchannel('A')) > 128
        xs = np.nonzero(a.any(axis=0))[0]
        ml = (xs.min() + xs.max()) / 2.0                 # Mitte des sichtbaren Sprites
        l['x'] = int(round(achse - (achse - (l['x'] + ml)) - ml))
        dist = achse - (l['x'] + ml)
        im_r = Image.open(os.path.join(OBJ, r['datei']))
        ar = np.array(im_r.getchannel('A')) > 128
        xr = np.nonzero(ar.any(axis=0))[0]
        mr = (xr.min() + xr.max()) / 2.0
        r['x'] = int(round(achse + dist - mr))
        r['y'] = l['y'] + l['fuss'] - r['fuss']
    json.dump(objs, open(pf, 'w'), indent=0)
    print('Symmetrie: %d Paare' % len(PAARE))


if __name__ == '__main__':
    symmetrie() if sys.argv[1:] == ['symmetrie'] else main()
