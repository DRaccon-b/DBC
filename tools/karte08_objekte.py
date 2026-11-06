"""Objekte fuer Karte 08 (Overdell) - alle am 16x16-Raster.

  python3 tools/karte08_bauen.py   (einmal ohne Objekte -> pixelhoehe.npy)
  python3 tools/karte08_objekte.py && python3 tools/regeln_v11.py karte08 && python3 tools/karte08_bauen.py

Objekte: PixelLab (assets/objekte/karte08: schloss, gross, baeume, mittel, klein); graeber/ = Grabsteine,
Statuen, Zaun usw. aus der Baum-Gruppe (eigener Ordner, damit sie nicht als Baeume ueberlappen duerfen).
Grosse Objekte zuerst (Schloss, Mausoleum, Gruften, grosse Baeume), dann Grabreihen, Laternen, Banner,
tote Baumgruppen, Felsbrocken auf dem schwarzen Fels, zuletzt Streudeko in die Luecken.
Jedes Objekt: Fuss auf seiner Ebene, unterer Teil vollstaendig auf derselben Ebene (Wandregel),
nie auf Treppen, Bruecke, Teleporter oder direkt an einer Kante.
"""
import json, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
from karte04_objekte import saeubern

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte08')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte08')
T = 16
TOTE_BAEUME = ['baeume/00', 'baeume/01', 'baeume/02', 'baeume/00', 'baeume/01', 'baeume/02', 'baeume/03',
               'baeume/14']
GRAEBER = ['mittel/00', 'mittel/01', 'mittel/02', 'mittel/03', 'mittel/04', 'graeber/04', 'klein/50',
           'klein/51', 'klein/21', 'klein/24', 'mittel/00', 'mittel/01', 'graeber/15']
# (sprite, Kachel-x, Kachel-y [Fusskachel], Optionen)
FEST = [
    ('schloss/00', 55, 11, {'keine_verdeckung': True}),
    # Schlossplatz: Paare exakt spiegelsymmetrisch zur Schlossachse (symmetrie() nach regeln_v11)
    ('graeber/09', 47, 15, {'symm': 'garg'}), ('graeber/09', 63, 15, {'spiegeln': True, 'symm': 'garg'}),
    ('mittel/06', 49, 17, {'anim': 'fahne', 'symm': 'banner'}),
    ('mittel/06', 61, 17, {'anim': 'fahne', 'spiegeln': True, 'symm': 'banner'}),
    ('mittel/07', 45, 17, {'symm': 'saeule'}), ('mittel/07', 65, 17, {'spiegeln': True, 'symm': 'saeule'}),
    ('mittel/05', 52, 15, {'anim': 'geisterlicht', 'symm': 'laterne'}),
    ('mittel/05', 58, 15, {'anim': 'geisterlicht', 'spiegeln': True, 'symm': 'laterne'}),
    # Mausoleum mit Laternen, Gruften
    ('krypta/02', 54, 67, {}),
    ('mittel/05', 49, 68, {'anim': 'geisterlicht'}), ('mittel/05', 59, 68, {'anim': 'geisterlicht'}),
    ('krypta/00', 44, 63, {}), ('krypta/03', 88, 60, {}), ('krypta/01', 82, 63, {}),
    ('mittel/07', 92, 64, {}), ('mittel/07', 79, 59, {'spiegeln': True}),
    # grosser toter Baum oben links, Baum am Sumpf
    ('gross/03', 9, 14, {}), ('gross/03', 66, 66, {'spiegeln': True}),
    # Lagerplatz unten links: Banner, Laternen, Kerzen, Kessel, Truhe
    ('mittel/06', 4, 77, {'anim': 'fahne'}), ('mittel/06', 17, 77, {'anim': 'fahne', 'spiegeln': True}),
    ('mittel/06', 7, 82, {'anim': 'fahne'}),
    ('mittel/05', 5, 74, {'anim': 'geisterlicht'}), ('mittel/05', 17, 73, {'anim': 'geisterlicht'}),
    ('mittel/05', 6, 85, {'anim': 'geisterlicht'}), ('mittel/05', 16, 85, {'anim': 'geisterlicht'}),
    ('mittel/13', 11, 79, {'anim': 'kerzen'}), ('klein/37', 13, 80, {}), ('klein/32', 13, 83, {}),
    ('klein/62', 14, 78, {}), ('klein/38', 9, 77, {}),
    # Laternen an den Wegen
    ('mittel/05', 37, 61, {'anim': 'geisterlicht'}), ('mittel/05', 44, 77, {'anim': 'geisterlicht'}),
    ('mittel/05', 57, 77, {'anim': 'geisterlicht'}), ('mittel/05', 21, 71, {'anim': 'geisterlicht'}),
    ('mittel/05', 70, 70, {'anim': 'geisterlicht'}), ('mittel/05', 89, 70, {'anim': 'geisterlicht'}),
    ('mittel/05', 73, 85, {'anim': 'geisterlicht'}),
    # Wegweiser, Saerge, Knochenhaufen, offenes Grab
    ('mittel/15', 21, 60, {}), ('mittel/15', 61, 79, {}), ('mittel/11', 36, 66, {}), ('mittel/09', 92, 41, {}),
    ('mittel/09', 33, 52, {}), ('graeber/08', 19, 66, {}), ('mittel/12', 85, 57, {}),
    # rechter Friedhof auf dem Berg
    ('graeber/05', 88, 37, {}), ('graeber/12', 84, 41, {}), ('graeber/13', 91, 40, {}), ('mittel/02', 86, 36, {}),
    ('mittel/00', 82, 38, {}), ('mittel/01', 90, 37, {}), ('mittel/04', 93, 37, {}), ('mittel/03', 80, 41, {}),
    ('graeber/10', 87, 42, {}),
    # Terrassen: Saeulen, Knochen, Statue
    ('graeber/09', 74, 26, {'spiegeln': True}), ('mittel/07', 33, 34, {}), ('graeber/07', 60, 41, {}),
    ('mittel/09', 66, 33, {}), ('graeber/06', 55, 50, {}),
]
# Haine toter Baeume (x0, y0, x1, y1, Dichte)
HAINE = [
    (4, 8, 14, 15, 0.22), (14, 9, 22, 12, 0.12), (6, 18, 13, 28, 0.10), (19, 25, 25, 32, 0.12),
    (5, 34, 12, 46, 0.10), (13, 40, 24, 48, 0.12), (3, 50, 12, 58, 0.14), (17, 52, 25, 60, 0.12),
    (62, 55, 72, 60, 0.12), (88, 64, 95, 79, 0.10), (30, 19, 40, 27, 0.08), (70, 20, 78, 26, 0.08),
    (31, 38, 37, 43, 0.12), (54, 37, 64, 42, 0.08), (31, 46, 36, 56, 0.10), (64, 28, 78, 33, 0.06),
]
STREU_BODEN = {'klein/04': 8, 'klein/12': 6, 'klein/02': 4, 'klein/03': 3, 'klein/00': 4, 'klein/01': 2,
               'klein/05': 3, 'klein/07': 3, 'klein/09': 2, 'klein/10': 2, 'klein/14': 1, 'klein/27': 2,
               'klein/47': 2, 'klein/48': 3, 'klein/59': 1, 'klein/40': 1, 'klein/26': 1, 'klein/49': 2,
               'mittel/14': 2, 'klein/36': 1}
STREU_TERRASSE = {'klein/00': 4, 'klein/01': 2, 'klein/05': 5, 'klein/11': 3, 'klein/10': 2, 'klein/49': 2,
                  'klein/15': 1, 'klein/04': 3, 'klein/12': 2, 'klein/07': 2, 'mittel/14': 1, 'klein/35': 1}
STREU_FELS = {'mittel/08': 2, 'fels/00': 3, 'fels/01': 2, 'fels/02': 3, 'fels/03': 3, 'fels/04': 1, 'fels/05': 2,
              'fels/06': 2, 'fels/08': 1, 'fels/09': 1, 'fels/10': 2, 'fels/11': 2, 'fels/12': 2, 'fels/13': 1,
              'fels/14': 1, 'fels/15': 1, 'fels_klein/00': 4, 'fels_klein/01': 4, 'fels_klein/02': 2,
              'fels_klein/03': 1, 'fels_klein/04': 3, 'fels_klein/05': 3, 'fels_klein/06': 2, 'fels_klein/08': 1,
              'fels_klein/09': 3, 'fels_klein/10': 1, 'fels_klein/11': 2, 'fels_klein/32': 1, 'fels_klein/36': 1,
              'fels_klein/60': 1, 'klein/48': 1}
LIEGEND = {'fels/03', 'fels/04', 'fels/11', 'fels_klein/00', 'fels_klein/03', 'fels_klein/05', 'fels_klein/06',
           'fels_klein/09', 'fels_klein/11', 'fels_klein/32', 'fels_klein/60', 'klein/00', 'klein/07', 'klein/10', 'klein/14', 'klein/15', 'klein/29', 'klein/49', 'klein/61',
           'klein/26', 'klein/05'}
FLACH = LIEGEND | {'fels_klein/01', 'fels_klein/02', 'fels_klein/04', 'fels_klein/08', 'fels_klein/10',
                   'fels_klein/36', 'klein/02', 'klein/03', 'klein/04', 'klein/09', 'klein/11', 'klein/12', 'klein/27', 'klein/47',
                   'klein/48', 'klein/59', 'klein/36', 'klein/01', 'klein/35'}
AUF_WEG = {'klein/37', 'klein/38', 'klein/32', 'klein/62', 'mittel/05', 'mittel/15', 'mittel/06', 'mittel/07', 'mittel/13', 'schloss/00', 'graeber/09'}
WIND = {'klein/04', 'klein/12', 'klein/09', 'klein/47', 'klein/48', 'klein/59', 'mittel/14'}


def bewerten(lvl, a, x, y):
    """Fuss auf einer begehbaren Ebene (1-7), unterer Teil (35 %) und 6 px unter dem Fuss auf derselben Ebene."""
    Hh, W = lvl.shape
    zeilen = np.nonzero(a.any(axis=1))[0]
    zu = int(zeilen.max())
    fuss = np.nonzero(a[max(0, zu - 2):zu + 1].any(axis=0))[0]
    fx = x + int((fuss.min() + fuss.max()) // 2); fy = y + zu + 1
    if not (0 <= fx < W and 0 <= fy < Hh):
        return False
    ebene = lvl[fy, fx]
    if not 1 <= ebene <= 7:
        return False
    unten = int(zu - (zu - zeilen.min()) * 0.35)
    ys, xs = np.nonzero(a[unten:zu + 1])
    ys, xs = ys + y + unten, xs + x
    if ((ys < 0) | (ys >= Hh) | (xs < 0) | (xs >= W)).any():
        return False
    if (lvl[ys, xs] != ebene).mean() > 0.03:
        return False
    xs_ = np.arange(x + fuss.min(), x + fuss.max() + 1)
    xs_ = xs_[(xs_ >= 0) & (xs_ < W)]
    for dy in range(1, 7):
        if fy + dy < Hh and (lvl[fy + dy, xs_] != ebene).mean() > 0.2:
            return False
    return True


def main():
    rnd = random.Random(8)
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cls = lay['klassen']
    hoehe = [[int(c) for c in r] for r in lay['hoehe']]
    cols, rows = lay['groesse']
    lvl = np.load(os.path.join(KARTE, 'pixelhoehe.npy'))
    os.makedirs(os.path.join(OBJ, 'sauber'), exist_ok=True)
    gesperrt = set()
    for (x0, x1, e) in lay.get('treppen', []):
        for y in range(rows - 1):
            if hoehe[y][x0] >= e > hoehe[y + 1][x0] and y < 60:
                for yy in range(y - 2, y + 5):
                    for x in range(x0 - 1, x1 + 2):
                        gesperrt.add((x, yy))
    for (x0, y0, x1, y1) in lay.get('bruecken', []):
        for y in range(y0 - 1, y1 + 2):
            for x in range(x0 - 2, x1 + 3):
                gesperrt.add((x, y))
    for tp in lay.get('teleporter', []):
        for y in range(tp['y'] - 2, tp['y'] + tp['h'] + 1):
            for x in range(tp['x'] - 2, tp['x'] + tp['b'] + 1):
                gesperrt.add((x, y))
    cache, alpha = {}, {}
    objekte, belegt = [], set()
    pixel = np.zeros(lvl.shape, bool)                     # deckende Pixel aller hohen Objekte (+2 px Abstand)

    def frei_px(datei, x, y):
        a = alpha[datei]
        h_, w_ = a.shape
        y0, x0 = max(0, y), max(0, x)
        y1, x1 = min(pixel.shape[0], y + h_), min(pixel.shape[1], x + w_)
        return not (pixel[y0:y1, x0:x1] & a[y0 - y:y1 - y, x0 - x:x1 - x]).any()

    def belegen(datei, x, y):
        from PIL import ImageFilter
        a = np.array(Image.fromarray((alpha[datei] * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(5))) > 0
        h_, w_ = a.shape
        y0, x0 = max(0, y), max(0, x)
        y1, x1 = min(pixel.shape[0], y + h_), min(pixel.shape[1], x + w_)
        pixel[y0:y1, x0:x1] |= a[y0 - y:y1 - y, x0 - x:x1 - x]

    def sprite(name, spiegeln):
        key = (name, spiegeln)
        if key not in cache:
            sp = saeubern(Image.open(os.path.join(OBJ, name + '.png')).convert('RGBA'))
            if spiegeln:
                sp = sp.transpose(Image.FLIP_LEFT_RIGHT)
            datei = 'sauber/%s%s.png' % (name.replace('/', '-'), '_m' if spiegeln else '')
            sp.save(os.path.join(OBJ, datei))
            a = np.array(sp.getchannel('A')) >= 128
            zu = int(np.nonzero(a.any(axis=1))[0].max())
            f = np.nonzero(a[max(0, zu - 2):zu + 1].any(axis=0))[0]
            cache[key] = (datei, sp.height, zu, (f.min() + f.max() + 1) / 2.0)
            alpha[datei] = a
        return cache[key]

    def setze(name, tx, ty, opt, suchen=False):
        opt = dict(opt)
        spiegeln = opt.pop('spiegeln', False)
        art = 'flach' if name in FLACH else 'hoch'
        datei, h, zu, mitte = sprite(name, spiegeln)
        kand = [(tx, ty)]
        if suchen:
            kand += sorted(((tx + dx, ty + dy) for dx in range(-3, 4) for dy in range(-3, 4) if dx or dy),
                           key=lambda k: abs(k[0] - tx) + abs(k[1] - ty))
        for (kx, ky) in kand:
            if not (0 <= kx < cols and 0 <= ky < rows) or (kx, ky) in gesperrt or (kx, ky, art) in belegt:
                continue
            if art == 'hoch' and any((kx + dx, ky, 'hoch') in belegt for dx in (-1, 1)):
                continue
            if art == 'hoch' and name not in AUF_WEG and (cls[ky][kx] in 'wq' and name != 'krypta/02'
                                                          or ky > 0 and cls[ky - 1][kx] == 'w'):
                continue                                          # keine Grabsteine/Baeume auf Wegen
            x, y = int(round(kx * T + T / 2 - mitte)), int((ky + 1) * T - 1 - zu)
            if bewerten(lvl, alpha[datei], x, y) and (art == 'flach' or name.startswith('baeume/') or frei_px(datei, x, y)):
                break
        else:
            if suchen:
                print('  keine passende Stelle:', name, (tx, ty))
            return None
        o = {'datei': datei, 'basis': name, 'x': x, 'y': y, 'fuss': h, 'kachel': [kx, ky],
             'ebene': 0 if art == 'flach' else 1}
        if name in LIEGEND:
            o['liegend'] = True
        o.update(opt)
        objekte.append(o)
        belegt.add((kx, ky, art))
        if art == 'hoch' and not name.startswith('baeume/'):
            belegen(datei, x, y)
        return o

    # 1) grosse und feste Objekte
    for (name, tx, ty, opt) in FEST:
        if setze(name, tx, ty, opt, suchen='symm' not in opt) is None and 'symm' in opt:
            print('  Symmetrie-Paar passt nicht:', name, (tx, ty))
    # 2) Grabreihen auf der Graberde: Fuss in der obersten Erdzeile jedes Feldes, unregelmaessige Abstaende
    for ty in range(1, rows):
        for tx in range(cols):
            if cls[ty][tx] != 'e':
                continue
            oben = ty
            while oben > 0 and cls[oben - 1][tx] == 'e':
                oben -= 1
            links = tx
            while links > 0 and cls[ty][links - 1] == 'e':
                links -= 1
            # Grabsteine am Kopfende jeder Reihe (alle 3 Zeilen eine Reihe), jede 2. Spalte, mit Luecken
            if (ty - oben) % 3 == 0 and (tx - links) % 2 == 0 and rnd.random() < 0.85:
                setze(rnd.choice(GRAEBER), tx, ty, {'spiegeln': rnd.random() < 0.3})
    # 3) Haine toter Baeume (Wind nur an Zweigen: keine Animation, tote Baeume sind steif)
    baeume = []
    for (x0, y0, x1, y1, d) in HAINE:
        for ty in range(y0, y1 + 1):
            for tx in range(x0, x1 + 1):
                if cls[ty][tx] in 'ghfa' and rnd.random() < d:
                    o = setze(rnd.choice(TOTE_BAEUME), tx, ty, {'spiegeln': rnd.random() < 0.5})
                    if o:
                        baeume.append(o)
    # Regel 5: einzeln stehende Baeume bekommen Begleitung (Busch/Gras am Sockel, Stein daneben)
    for o in baeume:
        kx, ky = o['kachel']
        nachbarn = [p for p in baeume if p is not o and abs(p['kachel'][0] - kx) <= 3 and abs(p['kachel'][1] - ky) <= 3]
        if not nachbarn:
            setze(rnd.choice(['mittel/14', 'klein/48']), kx + rnd.choice((-1, 1)), ky, {'anim': 'wehen'}, suchen=False)
            setze(rnd.choice(['klein/04', 'klein/12', 'klein/05', 'klein/02']), kx, ky + 1, {})
    # 4) Felsbrocken und Geroell auf dem schwarzen Fels (nicht an der Felskante)
    namen, gew = list(STREU_FELS), list(STREU_FELS.values())
    for ty in range(1, rows - 3):
        for tx in range(1, cols - 1):
            if hoehe[ty][tx] == 7 and all(hoehe[ty + k][tx] == 7 for k in range(1, 4)) and rnd.random() < 0.11:
                name = rnd.choices(namen, weights=gew)[0]
                opt = {'spiegeln': rnd.random() < 0.5}
                if name in ('fels/01', 'fels/10', 'fels_klein/02', 'fels_klein/10', 'fels/14'):
                    opt['anim'] = 'glimmen'
                setze(name, tx, ty, opt)
    # 5) Streudeko in die Luecken
    for (streu, arten, ebenen, anzahl) in ((STREU_BODEN, 'gh', (1,), 260), (STREU_TERRASSE, 'fa', (2, 3, 4, 5, 6), 120)):
        namen, gew = list(streu), list(streu.values())
        n = 0
        for _ in range(8000):
            if n >= anzahl:
                break
            tx, ty = rnd.randrange(2, cols - 2), rnd.randrange(3, rows - 3)
            if cls[ty][tx] not in arten or hoehe[ty][tx] not in ebenen:
                continue
            name = rnd.choices(namen, weights=gew)[0]
            opt = {'anim': 'wehen'} if name in WIND else {'anim': 'glimmen'} if name == 'klein/02' else {}
            if setze(name, tx, ty, opt):
                n += 1
    json.dump(objekte, open(os.path.join(OBJ, 'platzierung.json'), 'w'), indent=0)
    print(len(objekte), 'Objekte am Raster gesetzt')


ACHSE = 888                      # Schlossachse in px (Mitte des Schlossplatzes, Kacheln 47-63)


def symmetrie():
    """Gleiche Objekte buendig/symmetrisch: das rechte Objekt jedes Paars wird exakt an der Schlossachse
    gespiegelt zum linken gesetzt (gleiche Hoehe, gleicher Abstand zur Achse)."""
    pf = os.path.join(OBJ, 'platzierung.json')
    objs = json.load(open(pf))
    paare = {}
    for o in objs:
        if o.get('symm'):
            paare.setdefault(o['symm'], []).append(o)
    for name, ps in paare.items():
        if len(ps) != 2:
            print('  Paar unvollstaendig:', name, len(ps))
            continue
        l, r = sorted(ps, key=lambda o: o['x'])
        w = Image.open(os.path.join(OBJ, l['datei'])).width
        r['x'], r['y'] = 2 * ACHSE - l['x'] - w, l['y']
        if 'block' in l:
            bx, by, wt, ht = l['block']
            r['block'] = [2 * ACHSE // T - bx - wt, by, wt, ht]
            r['kachel'] = [2 * ACHSE // T - 1 - l['kachel'][0], l['kachel'][1]]
    json.dump(objs, open(pf, 'w'), indent=0)
    print('Symmetrie: %d Paare gespiegelt' % len(paare))


if __name__ == '__main__':
    symmetrie() if sys.argv[1:] == ['symmetrie'] else main()
