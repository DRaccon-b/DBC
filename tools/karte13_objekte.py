"""Objekte fuer Karte 13 (Spiral Mountain: Machine City) - am 16x16-Raster, nach den Regeln aus CLAUDE.md.

  python3 tools/karte13_bauen.py   (einmal ohne Objekte -> pixelhoehe.npy)
  python3 tools/karte13_objekte.py && python3 tools/regeln_v11.py karte13 && python3 tools/karte13_objekte.py symmetrie
  python3 tools/karte13_bauen.py

Neu (PixelLab, assets/objekte/karte13, alles frontal): gross (Funkturm, Gittermast, Mech-Drachen-Wrack, Buswrack),
gross2 (Bahnhofshalle, Kranwrack, Festungstor mit Auge), haus/haus2/turm (alle Gebaeude mit sichtbarem Dach - Regel
'Gebaeude mit Dach': Lagerhalle, Fabrik mit Sheddach, Ladenzeilen, Wohnbloecke, Buero, Glastuerme),
festung (Reaktor, Panzertuer, Konsole, Strommast), mittel (Schornstein, Ofen, Tank, Autowrack, Ampel, Laterne, Zahnrad,
Statue, Telefonzelle, Schutt, Roboterwrack, Fass, Kisten, Generator, Rohr, Bank), klein (64 Stueck Kleinkram).
Wiederverwendet (Regel 3, frontal): Karte 02 Schrott, Kabeltrommel (k2/...). Anspielungen nur ueber Stil und Farben.
Grosse Objekte zuerst (Gebaeude in den Bloecken wie in der Vorlage), Paare spiegelsymmetrisch zur Festungsachse.
"""
import json, os, random, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageFilter
from karte04_objekte import saeubern
from karte09_objekte import raster_x, bewerten

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte13')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte13')
QUELLEN = {'k2/': os.path.join(ROOT, 'assets', 'objekte', 'karte02')}
T = 16
ACHSE_F = 40 * T                 # Festung (senkrechte Achse)

FLACH = {'klein/%02d' % i for i in (1, 2, 3, 4, 5, 6, 13, 14, 15, 23, 32, 35, 41, 48, 57, 59, 63)}
LIEGEND = {'eigen/dragondead', 'klein/03', 'klein/13', 'klein/41', 'klein/32', 'klein/57', 'klein/59', 'gross2/02', 'gross/02', 'mittel/14'}
LEUCHTEN = {'mittel/05': 'lampe', 'mittel/01': 'feuer', 'festung/00': 'glimmen', 'gross/00': 'rotlicht', 'gross2/03': 'rotlicht',
            'festung/01': 'rotlicht', 'festung/03': 'rotlicht', 'mittel/13': 'rotlicht', 'festung/02': 'konsole', 'gross/02': 'funken', 'eigen/dragondead': 'funken',
            'mittel/04': 'ampel_blinken', 'klein/09': 'glimmen', 'klein/36': 'glimmen'}
RAUCH = {'mittel/00', 'mittel/01'}
WIND = {'klein/15'}
BLOCK_STREU = {'klein/00': 3, 'klein/01': 4, 'klein/02': 3, 'klein/04': 2, 'klein/05': 2, 'klein/06': 2, 'klein/11': 2,
               'klein/12': 1, 'klein/13': 2, 'klein/14': 2, 'klein/15': 2, 'klein/23': 1, 'klein/32': 1, 'klein/35': 1,
               'klein/41': 1, 'klein/46': 1, 'klein/48': 1, 'klein/57': 1, 'klein/63': 2, 'klein/08': 1, 'klein/30': 1}
VERSEUCHT = {'klein/09': 3, 'klein/36': 2, 'klein/00': 1, 'klein/13': 1}
HOF_STREU = {'klein/01': 3, 'klein/02': 2, 'klein/05': 2, 'klein/08': 2, 'klein/16': 1, 'klein/21': 1, 'klein/28': 1,
             'klein/29': 1, 'klein/33': 1, 'klein/40': 1, 'klein/43': 1, 'klein/52': 1, 'klein/53': 1, 'klein/59': 1}
MITTEL_STREU = {'mittel/09': 3, 'mittel/11': 2, 'mittel/12': 1, 'mittel/13': 1, 'mittel/15': 2, 'mittel/10': 1,
                'k2/mittel/05': 1, 'k2/mittel/06': 1, 'k2/mittel/11': 1}


def quelle(name):
    for pre, pfad in QUELLEN.items():
        if name.startswith(pre):
            ziel = os.path.join(OBJ, name + '.png')
            if not os.path.exists(ziel):
                os.makedirs(os.path.dirname(ziel), exist_ok=True)
                shutil.copy(os.path.join(pfad, name[3:] + '.png'), ziel)
            return ziel
    return os.path.join(OBJ, name + '.png')


def main():
    rnd = random.Random(13)
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cls = lay['klassen']
    cols, rows = lay['groesse']
    lvl = np.load(os.path.join(KARTE, 'pixelhoehe.npy'))
    os.makedirs(os.path.join(OBJ, 'sauber'), exist_ok=True)
    cache, alpha = {}, {}
    objekte, belegt = [], set()
    pixel = np.zeros(lvl.shape, bool)
    gesperrt = set()
    for tp in lay.get('teleporter', []):
        for y in range(tp['y'] - 1, tp['y'] + tp['h'] + 2):
            for x in range(tp['x'] - 1, tp['x'] + tp['b'] + 2):
                gesperrt.add((x, y))
    for (x0, x1, e, yb) in lay.get('treppen_sued', []):
        for y in range(yb - 1, yb + 5):
            for x in range(x0 - 1, x1 + 2):
                gesperrt.add((x, y))
    pfad = {(x, y) for y in range(rows) for x in range(cols) if cls[y][x] == 's'}     # Fahrbahn bleibt frei
    for y in range(rows):                                         # Giftbecken und Laborrand frei
        for x in range(cols):
            if cls[y][x] == 'n':
                for dy in range(-2, 3):
                    for dx in range(-2, 3):
                        gesperrt.add((x + dx, y + dy))

    def sprite(name, spiegeln=False):
        key = (name, spiegeln)
        if key not in cache:
            sp = saeubern(Image.open(quelle(name)).convert('RGBA'))
            if spiegeln:
                sp = sp.transpose(Image.FLIP_LEFT_RIGHT)
            datei = 'sauber/%s%s.png' % (name.replace('/', '-'), '_m' if spiegeln else '')
            sp.save(os.path.join(OBJ, datei))
            a = np.array(sp.getchannel('A')) >= 128
            zu = int(np.nonzero(a.any(axis=1))[0].max())
            xs = np.nonzero(a.any(axis=0))[0]
            cache[key] = (datei, sp.height, zu, (xs.min() + xs.max() + 1) / 2.0)
            alpha[datei] = a
        return cache[key]

    def frei_px(datei, x, y):
        a = alpha[datei]
        h_, w_ = a.shape
        y0, x0 = max(0, y), max(0, x)
        y1, x1 = min(pixel.shape[0], y + h_), min(pixel.shape[1], x + w_)
        if y1 <= y0 or x1 <= x0:
            return True
        return not (pixel[y0:y1, x0:x1] & a[y0 - y:y1 - y, x0 - x:x1 - x]).any()

    def belegen(datei, x, y):
        a = np.array(Image.fromarray((alpha[datei] * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(5))) > 0
        h_, w_ = a.shape
        y0, x0 = max(0, y), max(0, x)
        y1, x1 = min(pixel.shape[0], y + h_), min(pixel.shape[1], x + w_)
        if y1 > y0 and x1 > x0:
            pixel[y0:y1, x0:x1] |= a[y0 - y:y1 - y, x0 - x:x1 - x]

    def baum_ok(datei, x, y):
        """Begleiter (Regel 5) verdeckt hoechstens den Sockel eines Baums an der Ecke - nie Stamm oder Krone."""
        a = alpha[datei]
        for t in objekte:
            if not t.get('baum'):
                continue
            at = alpha[t['datei']]
            x0, y0 = max(t['x'], x), max(t['y'], y)
            x1, y1 = min(t['x'] + at.shape[1], x + a.shape[1]), min(t['y'] + at.shape[0], y + a.shape[0])
            if x1 <= x0 or y1 <= y0:
                continue
            ov = at[y0 - t['y']:y1 - t['y'], x0 - t['x']:x1 - t['x']] & a[y0 - y:y1 - y, x0 - x:x1 - x]
            if not ov.any():
                continue
            fuss_t = t['y'] + int(np.nonzero(at.any(axis=1))[0].max())
            ys_ = np.nonzero(ov.any(axis=1))[0] + y0
            if ys_.min() < fuss_t - 18 or ov.sum() > 0.2 * a.sum():   # nur unten am Sockel, nur ein kleiner Teil
                return False
            xs_t = np.nonzero(at[-20:].any(axis=0))[0]                 # Stammfuss: mittlere Spalten des Sockels
            mt = t['x'] + (xs_t.min() + xs_t.max() + 1) / 2.0
            xs_b = np.nonzero(a.any(axis=0))[0]
            if abs(x + (xs_b.min() + xs_b.max() + 1) / 2.0 - mt) < 0.45 * (xs_b.max() - xs_b.min() + 1) + 6:
                return False                                            # seitlich an der Ecke, nicht mittig vor dem Stamm
        return True

    pfad_px = np.zeros(lvl.shape, bool)                       # Weg bleibt frei: kein Objektfuss auf dem Pfad
    for (px_, py_) in pfad:
        pfad_px[py_ * T:(py_ + 1) * T, px_ * T:(px_ + 1) * T] = True

    def weg_belegt(datei, x, y):
        a = alpha[datei]
        zeilen = np.nonzero(a.any(axis=1))[0]
        unten = int(zeilen.max() - (zeilen.max() - zeilen.min()) * 0.4)
        ys, xs = np.nonzero(a[unten:])
        ys, xs = ys + y + unten, xs + x
        ok = (ys >= 0) & (ys < pfad_px.shape[0]) & (xs >= 0) & (xs < pfad_px.shape[1])
        return pfad_px[ys[ok], xs[ok]].any()

    def setzen(name, X, fy, opt, suchen=False, arten=None, melden=False):
        opt = dict(opt)
        datei, h, zu, mitte = sprite(name, opt.pop('spiegeln', False))
        kand = [(X, fy)]
        if suchen:
            kand += sorted(((X + dx * T, fy + dy) for dx in range(-2, 3) for dy in range(-2, 3) if dx or dy),
                           key=lambda k: abs(k[0] - X) / T + abs(k[1] - fy))
        for (kx, ky) in kand:
            tx = int(kx // T)
            if not (0 <= tx < cols and 0 <= ky < rows) or (tx, ky) in gesperrt:
                continue
            if arten and cls[ky][tx] not in arten:
                continue
            x = raster_x(alpha[datei], kx) if not opt.get('achse') else int(round(kx - mitte))
            y = (ky + 1) * T - 1 - zu
            if weg_belegt(datei, x, y):
                continue
            if opt.get('an_wand') or (bewerten(lvl, alpha[datei], x, y) and (frei_px(datei, x, y) if not opt.get('begleiter') else baum_ok(datei, x, y))):
                break
        else:
            if melden:
                print('  keine passende Stelle:', name, (X // T, fy))
            return None
        o = {'datei': datei, 'basis': name, 'x': x, 'y': y, 'fuss': h, 'kachel': [tx, ky],
             'ebene': 0 if name in FLACH else 1}
        if name in LIEGEND:
            o['liegend'] = True
        if name in WIND:
            o['anim'] = 'wehen'
        if name in LEUCHTEN:
            o['anim'] = LEUCHTEN[name]
        o.update(opt)
        objekte.append(o)
        belegt.add((tx, ky))
        if name not in FLACH and not o.get('begleiter'):
            belegen(datei, x, y)
        return o

    # 0) Bergwand ringsum (Regel 3b: neue Teile, alle starr ausser echten Lichtern):
    #    a) halb im Fels versunkene Maschinenteile, vom Kartenrand angeschnitten
    Hp, Wp = lvl.shape
    rr = random.Random(7)
    def fest_setzen(name, X, fussy, spiegeln=False, **extra):
        datei, h, zu, mitte = sprite(name, spiegeln)
        x, y = int(round(X - mitte)), int(fussy) - zu
        o = {'datei': datei, 'basis': name, 'x': x, 'y': y, 'fuss': h, 'kachel': [max(0, min(cols - 1, int(X) // T)),
             max(0, min(rows - 1, int(fussy) // T))], 'ebene': 1, 'fest_pos': True, 'rand': True}
        o.update(extra)
        objekte.append(o)
        belegen(datei, x, y)
        return o
    KUPPE = 44                                                    # Breite der Bergkuppe innerhalb der Karte (px)
    def versunken(name, seite, pos, spiegeln=False, **extra):
        """Maschinenteil im Fels: nur so weit sichtbar, wie die Bergkuppe reicht - ragt nie ueber die Kante."""
        datei, h, zu, mitte = sprite(name, spiegeln)
        hh, ww = alpha[datei].shape
        if seite == 'links':
            X, fuss = KUPPE - ww + mitte, pos
        elif seite == 'rechts':
            X, fuss = Wp - KUPPE + mitte, pos
        else:                                                     # unten: Oberkante auf der Bergkuppe
            X, fuss = pos, Hp - KUPPE + zu
        return fest_setzen(name, X, fuss, spiegeln, **extra)
    versunken('berg/00', 'links', 26 * T, kein_schatten=True)                    # Zahnrad links
    versunken('berg/01', 'unten', 17 * T, kein_schatten=True)                    # Panzerkette unten
    versunken('berg/02', 'rechts', 47 * T, spiegeln=True, kein_schatten=True)    # Roboterarm rechts
    versunken('berg/03', 'unten', 72 * T, kein_schatten=True, anim='rotlicht')   # Mech-Kopf unten rechts, rotes Auge
    #    c) Wachtechnik auf der Bergkuppe: Funkmasten an den Ecken, Warnleuchten im festen Abstand, Kameras und
    #       Scheinwerfer zur Stadt, Zaun mit Luecken, Stacheldraht, Warnschilder, Kristalle, Kabel- und Rohrenden
    WACHE = [('wache/00', 1, 4), ('wache/00', 78, 4), ('wache/00', 1, 66), ('wache/00', 78, 66),
             ('wache/04', 25, 2), ('wache/04', 55, 2), ('wache/11', 9, 2), ('wache/15', 47, 68), ('wache/13', 30, 68),
             ('wache/12', 1, 27), ('wache/12', 78, 33), ('wache/08', 1, 38), ('wache/08', 78, 57), ('wache/08', 26, 68),
             ('wache/09', 1, 51), ('wache/10', 78, 21), ('wache/09', 23, 68), ('wache/10', 69, 68), ('wache/07', 1, 15),
             ('wache/07', 78, 44), ('wache/07', 12, 68)]
    for y in range(8, 66, 12):                                    # Warnleuchten links/rechts im festen Rhythmus
        WACHE += [('wache/02', 1, y), ('wache/02', 78, y)]
    for y in (20, 44):                                            # Kameras zur Stadt hin (rechts gespiegelt)
        WACHE += [('wache/03', 1, y), ('wache/03', 78, y + 1)]
    for x in range(6, 76, 9):                                     # Zaun entlang der unteren Bergkante, mit Luecken
        if rr.random() < 0.7 and not (36 <= x <= 43):
            WACHE.append(('wache/05' if rr.random() < 0.75 else 'wache/06', x, 68))
    for (name_, tx, ty) in WACHE:
        o = None
        for d in (0, 1, -1, 2, -2, 3, -3):                        # nur entlang der Bergkuppe ausweichen, nie in die Stadt
            tx_, ty_ = (tx, ty + d) if tx in (1, 78) else (tx + d, ty)
            if tx in (1, 78) and not 3 <= ty_ <= 66:
                continue
            o = setzen(name_, tx_ * T + 8, ty_, {'spiegeln': tx > 40 and name_ in ('wache/03', 'wache/02', 'wache/04')})
            if o:
                break
        if o and name_ in ('wache/00', 'wache/02', 'wache/03', 'wache/14', 'wache/15'):
            o['anim'] = 'rotlicht'
        elif o and name_ == 'wache/09':
            o['anim'] = 'glimmen'
        elif o and name_ == 'wache/04':
            o['anim'] = 'lampe'
    #    b) Schrottrand: vom Kartenrand angeschnitten, Tiefe wellenfoermig, ungleiche Abstaende (wie Karte 12)
    RAND = ['rand/%02d' % i for i in range(16)]
    GEW = [2, 3, 2, 3, 2, 2, 1, 3, 2, 2, 1, 3, 1, 1, 2, 1]
    frei_x = [(66 * T - 8, 69 * T + 8), (38 * T - 8, 42 * T + 8)]
    def kante(laenge):
        pos, tiefe, out = -8, 0.0, []
        while pos < laenge + 24:
            tiefe = max(-8, min(12, tiefe * 0.7 + rr.uniform(-6, 6)))
            out.append((pos, tiefe + rr.uniform(-4, 4)))
            pos += rr.randint(22, 38)
        return out
    stellen = [(X, 18 + t, 'oben') for X, t in kante(Wp)] + [(X, Hp + 12 - t, 'unten') for X, t in kante(Wp)]
    stellen += [(t, Y + 20, 'seite') for Y, t in kante(Hp)] + [(Wp - t, Y + 20, 'seite') for Y, t in kante(Hp)]
    for (X, fussy, seite) in stellen:
        X, fussy = int(round(X)), int(round(fussy))
        if seite != 'seite' and any(a_ <= X <= b_ for a_, b_ in frei_x if (seite == 'unten') == (a_ < 700)):
            continue
        name_ = rr.choices(RAND, weights=GEW)[0]
        datei, h, zu, mitte = sprite(name_, rr.random() < 0.5)
        x, y = int(round(X - mitte)), fussy - zu
        if not frei_px(datei, x, y):
            continue
        objekte.append({'datei': datei, 'basis': name_, 'x': x, 'y': y, 'fuss': h, 'kachel': [max(0, min(cols - 1, X // T)),
                        max(0, min(rows - 1, fussy // T))], 'ebene': 1, 'fest_pos': True, 'rand': True, 'kein_schatten': True})
        belegen(datei, x, y)
    # 1) Festung: Tor mit Auge und Panzertueren in der Bergwand, Reaktoren und Konsolen spiegelgleich zur Achse
    FEST = [
        ('gross2/03', ACHSE_F, 5, {'achse': ACHSE_F, 'an_wand': True}),
        ('festung/01', ACHSE_F - 136, 5, {'symm': 'f1', 'an_wand': True}), ('festung/01', ACHSE_F + 136, 5, {'symm': 'f1', 'an_wand': True}),
        ('festung/00', ACHSE_F - 144, 11, {'symm': 'f2'}), ('festung/00', ACHSE_F + 144, 11, {'symm': 'f2'}),
        ('festung/00', ACHSE_F - 144, 22, {'symm': 'f3'}), ('festung/00', ACHSE_F + 144, 22, {'symm': 'f3'}),
        ('festung/02', ACHSE_F - 96, 16, {'symm': 'f4'}), ('festung/02', ACHSE_F + 96, 16, {'symm': 'f4'}),
        # Industriehof links oben: zwei Lagerhallen, Schornsteine, Ofen, Strommast
        ('haus/00', 8 * T + 8, 8, {}), ('haus2/03', 22 * T, 8, {}),
        ('mittel/00', 13 * T + 8, 25, {}), ('mittel/00', 15 * T + 8, 25, {}), ('mittel/01', 6 * T, 26, {}),
        ('festung/03', 22 * T, 20, {}), ('mittel/13', 13 * T, 20, {}),
        # Hof rechts oben: Funkturm, Tanks, Rohr, Schornstein, Kisten
        ('gross/00', 57 * T + 8, 14, {}), ('mittel/02', 61 * T, 7, {}), ('mittel/02', 64 * T, 8, {}), ('mittel/02', 61 * T + 8, 11, {}),
        ('mittel/14', 62 * T, 15, {}), ('mittel/00', 55 * T + 8, 26, {}), ('mittel/12', 57 * T, 27, {}),
        # rechte Spalte oben
        ('haus/03', 72 * T + 8, 9, {}), ('mittel/03', 71 * T, 27, {}), ('mittel/10', 74 * T, 21, {}),
        # Bloecke Reihe 1 (31-38)
        ('haus/02', 6 * T + 8, 37, {}), ('mittel/08', 9 * T + 8, 37, {}), ('haus/01', 18 * T + 8, 37, {}),
        ('gross2/02', 32 * T, 37, {}), ('haus/03', 47 * T, 37, {}), ('gross/03', 60 * T, 36, {}), ('haus2/02', 72 * T + 8, 37, {}),
        # Reihe 2 (41-48)
        ('mittel/10', 6 * T, 46, {}), ('mittel/09', 18 * T, 46, {}), ('mittel/07', 32 * T, 46, {}), ('eigen/dragondead', 47 * T, 47, {}),
        ('mittel/06', 72 * T, 47, {}), ('mittel/03', 60 * T, 46, {}),
        # Reihe 3 (51-58)
        ('haus2/01', 6 * T + 8, 57, {}), ('haus2/02', 18 * T + 8, 57, {'spiegeln': True}), ('gross/01', 32 * T, 57, {}),
        ('turm/02', 47 * T, 57, {}), ('turm/00', 60 * T, 58, {}), ('mittel/08', 74 * T, 57, {}),
        # Reihe 4 (61-66) mit Bahnhof
        ('haus/02', 6 * T + 8, 66, {'spiegeln': True}), ('mittel/03', 17 * T, 64, {}), ('mittel/03', 21 * T, 66, {}),
        ('gross2/01', 47 * T + 8, 66, {}), ('festung/02', 31 * T + 8, 64, {}), ('haus/01', 60 * T, 66, {'spiegeln': True}),
        ('mittel/09', 72 * T, 66, {}),
    ]
    for (name, X, fy, opt) in FEST:
        setzen(name, X, fy, opt, suchen=not (opt.get('symm') or opt.get('achse')), melden=True)
    # 2) Strassenmoebel: Ampeln an Kreuzungsecken, Laternen in festem Abstand an der Hauptstrasse
    for (x, y) in ((37, 31), (42, 41), (24, 41), (55, 51), (13, 61), (52, 31)):
        setzen('mittel/04', x * T + 8, y, {'spiegeln': x > 40}, suchen=True)
    for y in (34, 44, 54, 64):
        setzen('mittel/05', 37 * T + 8, y, {'symm_y': None} if False else {}, suchen=True)
        setzen('mittel/05', 42 * T + 8, y, {'spiegeln': True}, suchen=True)
    # 3) Kleinkram und Schrott (unregelmaessig, sparsam, nie auf der Fahrbahn)
    for (streu, arten, anzahl) in ((MITTEL_STREU, 'gp', 14), (VERSEUCHT, 'p', 16), (BLOCK_STREU, 'g', 46),
                                   (HOF_STREU, 'h', 22)):
        namen, gew = list(streu), list(streu.values())
        n = 0
        for _ in range(9000):
            if n >= anzahl:
                break
            tx, ty = rnd.randrange(3, 77), rnd.randrange(3, rows - 3)
            if cls[ty][tx] not in arten or (tx, ty) in pfad:
                continue
            name_ = rnd.choices(namen, weights=gew)[0]
            if any(o['basis'] == name_ and abs(o['kachel'][0] - tx) <= 5 and abs(o['kachel'][1] - ty) <= 5 for o in objekte):
                continue
            if setzen(name_, tx * T + 8, ty, {'spiegeln': rnd.random() < 0.4}, arten=arten):
                n += 1
    for o in objekte:
        if o['basis'] in RAUCH:
            o['rauch'] = True
    json.dump(objekte, open(os.path.join(OBJ, 'platzierung.json'), 'w'), indent=0)
    print(len(objekte), 'Objekte gesetzt')


def symmetrie():
    """Paare exakt spiegelsymmetrisch: 'symm' zur senkrechten Achse (Plattform bzw. Platz), 'symm_y' zur
    waagerechten Brueckenachse; 'achse' genau auf die Achse."""
    pf = os.path.join(OBJ, 'platzierung.json')
    objs = json.load(open(pf))
    achsen = {}
    paare, paare_y = {}, {}
    for o in objs:
        if o.get('achse'):
            a_ = np.array(Image.open(os.path.join(OBJ, o['datei'])).getchannel('A')) > 128
            xs_ = np.nonzero(a_.any(axis=0))[0]
            o['x'] = int(round(o['achse'] - (xs_.min() + xs_.max() + 1) / 2.0))
        if o.get('symm'):
            paare.setdefault(o['symm'], []).append(o)
        if o.get('symm_y'):
            paare_y.setdefault(o['symm_y'], []).append(o)
    for name, ps in paare.items():
        if len(ps) == 1:                                     # fehlender Partner: gespiegelt ergaenzen
            neu = dict(ps[0]); objs.append(neu); ps.append(neu)
            neu['x'] = ps[0]['x'] + (1 if ps[0]['x'] < achsen.get(name, ACHSE_F) else -1)
        if len(ps) != 2:
            print('  Paar unvollstaendig:', name, len(ps))
            continue
        l, r = sorted(ps, key=lambda o: o['x'])
        achse = achsen.get(name, ACHSE_F)
        a_ = np.array(Image.open(os.path.join(OBJ, l['datei'])).getchannel('A')) > 128
        xs_ = np.nonzero(a_.any(axis=0))[0]
        m_ = (xs_.min() + xs_.max() + 1) / 2.0
        r['x'] = int(round(2 * achse - (l['x'] + m_) - m_))
        r['y'] = l['y']
        if l['datei'] == r['datei']:                         # spiegelverkehrt: rechter Partner ist das Spiegelbild
            d_ = l['datei'].replace('.png', '_m.png') if not l['datei'].endswith('_m.png') else l['datei'].replace('_m.png', '.png')
            if not os.path.exists(os.path.join(OBJ, d_)):
                Image.open(os.path.join(OBJ, l['datei'])).transpose(Image.FLIP_LEFT_RIGHT).save(os.path.join(OBJ, d_))
            r['datei'] = d_
            a2 = np.array(Image.open(os.path.join(OBJ, d_)).getchannel('A')) > 128
            xs2 = np.nonzero(a2.any(axis=0))[0]
            r['x'] = int(round(2 * achse - (l['x'] + m_) - (xs2.min() + xs2.max() + 1) / 2.0))
    for name, ps in paare_y.items():
        if len(ps) == 1:                                     # fehlender Partner: an der Brueckenachse gespiegelt
            o0 = ps[0]
            neu = dict(o0)
            a_ = np.array(Image.open(os.path.join(OBJ, o0['datei'])).getchannel('A')) > 128
            zu_ = int(np.nonzero(a_.any(axis=1))[0].max())
            fuss = o0['y'] + zu_
            neu['y'] = int(2 * ACHSE_FY - fuss) - zu_ + (T if fuss < ACHSE_FY else -T)
            objs.append(neu); ps.append(neu)
        if len(ps) != 2:
            print('  Paar unvollstaendig:', name, len(ps))
            continue
        o_, u_ = sorted(ps, key=lambda o: o['y'])
        u_['x'] = o_['x']
    json.dump(objs, open(pf, 'w'), indent=0)
    print('Symmetrie: %d + %d Paare' % (len(paare), len(paare_y)))


if __name__ == '__main__':
    symmetrie() if sys.argv[1:] == ['symmetrie'] else main()
