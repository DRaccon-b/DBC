"""Objekte fuer Karte 10 (Toy Town) - am 16x16-Raster, nach den Regeln aus CLAUDE.md.

  python3 tools/karte10_bauen.py   (einmal ohne Objekte -> pixelhoehe.npy, wandflaeche.npy)
  python3 tools/karte10_objekte.py && python3 tools/regeln_v11.py karte10 && python3 tools/karte10_objekte.py symmetrie
  python3 tools/karte10_bauen.py

Neu (PixelLab, assets/objekte/karte10): haeuser, haeuser2, burg, bahnhof, spielplatz, baeume, klein.
Die Ecktuerme der Burg sind aus der Burgfront ausgeschnitten (gleicher Stil, kein Neu-Generieren noetig).
Grosse Objekte zuerst (Burg, Bahnhof, Haeuser, Uhrturm, Brunnen), dann Baeume mit Begleitern, dann Kleinkram.
Paare auf Plaetzen stehen spiegelsymmetrisch zur Achse ihres Bauwerks.
"""
import json, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageFilter
from karte04_objekte import saeubern
from karte09_objekte import raster_x, groesstes_teil, bewerten

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte10')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte10')
T = 16
ACHSE_BURG = 76 * T              # Burg, Torweg, Hofrahmen
ACHSE_BAHNHOF = 76 * T           # Bahnsteig x 69-82
ACHSE_BRUNNEN = 10 * T           # Brunnenplatz (Mitte x 10.0)
ACHSE_UHR = 54 * T               # Uhrenplatz (Mitte x 54.0)
WAND_FUSS = 34 * T + 15          # Unterkante der Burg-Wandflaeche (Reihen 32-34)

LAMPE, BANK, BRIEF, HYDRANT, ZAUN = 'spielplatz/04', 'spielplatz/03', 'spielplatz/05', 'spielplatz/06', 'spielplatz/07'
SOLDAT = 'spielplatz/09'
BAEUME = ['baeume/00', 'baeume/01', 'baeume/02', 'klein/49', 'klein/48']
BUESCHE = ['baeume/03', 'klein/35', 'klein/09', 'klein/10', 'klein/12']
LIEGEND = {'klein/58', 'klein/63', 'klein/15', 'klein/30', 'klein/25'}
FLACH = LIEGEND | {'klein/09', 'klein/10', 'klein/11', 'klein/12', 'baeume/14'}
WIND = {'klein/09', 'klein/10', 'klein/12', 'klein/35', 'baeume/03'}
SPIELZEUG = ['klein/02', 'klein/03', 'klein/06', 'klein/07', 'klein/22', 'klein/32', 'klein/41', 'klein/42',
             'klein/43', 'klein/45', 'klein/46', 'klein/53', 'klein/54', 'klein/59', 'klein/14', 'klein/52']

# (sprite, Mitte x in px, Fussreihe, Optionen)  - grosse Objekte zuerst
FEST = [
    # Bahnhof: Gebaeude auf der Bahnsteigachse, Zug auf dem unteren Gleis
    ('bahnhof/00', ACHSE_BAHNHOF, 12, {'achse': ACHSE_BAHNHOF}),
    ('klein/39', ACHSE_BAHNHOF - 96, 13, {'symm': 'bsl', 'anim': 'lampe'}), ('klein/39', ACHSE_BAHNHOF + 96, 13, {'symm': 'bsl', 'anim': 'lampe'}),
    # Uhrenplatz: Uhrturm in der Mitte, Baenke und Laternen symmetrisch
    ('bahnhof/03', ACHSE_UHR, 55, {'achse': ACHSE_UHR}),
    (LAMPE, ACHSE_UHR - 64, 52, {'symm': 'ul', 'anim': 'lampe'}), (LAMPE, ACHSE_UHR + 64, 52, {'symm': 'ul', 'anim': 'lampe'}),
    (BANK, ACHSE_UHR - 56, 57, {'symm': 'ub'}), (BANK, ACHSE_UHR + 56, 57, {'symm': 'ub'}),
    # Brunnenplatz: Brunnen in der Mitte, vier Laternen und zwei Baenke symmetrisch
    ('spielplatz/08', ACHSE_BRUNNEN, 38, {'achse': ACHSE_BRUNNEN, 'anim': 'brunnen'}),
    (LAMPE, ACHSE_BRUNNEN - 96, 33, {'symm': 'bl1', 'anim': 'lampe'}), (LAMPE, ACHSE_BRUNNEN + 96, 33, {'symm': 'bl1', 'anim': 'lampe'}),
    (LAMPE, ACHSE_BRUNNEN - 96, 42, {'symm': 'bl2', 'anim': 'lampe'}), (LAMPE, ACHSE_BRUNNEN + 96, 42, {'symm': 'bl2', 'anim': 'lampe'}),
    (BANK, ACHSE_BRUNNEN - 48, 43, {'symm': 'bb'}), (BANK, ACHSE_BRUNNEN + 48, 43, {'symm': 'bb'}),
    # Burghof: Soldaten am Torweg, Brunnen im Rahmen, Blumenbeete in den Rahmenecken (symmetrisch)
    (SOLDAT, ACHSE_BURG - 56, 38, {'symm': 's1'}), (SOLDAT, ACHSE_BURG + 56, 38, {'symm': 's1'}),
    (SOLDAT, ACHSE_BURG - 56, 43, {'symm': 's2'}), (SOLDAT, ACHSE_BURG + 56, 43, {'symm': 's2'}),
    ('baeume/07', ACHSE_BURG, 53, {'achse': ACHSE_BURG, 'anim': 'brunnen'}),
    ('baeume/15', ACHSE_BURG - 72, 50, {'symm': 'f1'}), ('baeume/15', ACHSE_BURG + 72, 50, {'symm': 'f1'}),
    ('spielplatz/15', ACHSE_BURG - 72, 56, {'symm': 'f2'}), ('spielplatz/15', ACHSE_BURG + 72, 56, {'symm': 'f2'}),
    # Burghof unten: Spielzeugecke (Bausteine, Trommel, Teddy, Roboter, Karussell)
    ('spielplatz/14', 65 * T, 66, {}), ('spielplatz/10', 63 * T, 70, {}), ('spielplatz/11', 68 * T + 8, 70, {}),
    ('spielplatz/12', 72 * T, 70, {}), ('spielplatz/13', 80 * T, 69, {}), ('spielplatz/10', 83 * T, 62, {'spiegeln': True}),
    ('klein/32', 77 * T, 64, {}), ('klein/55', 82 * T + 8, 70, {}), ('klein/60', 64 * T, 41, {}), ('klein/03', 84 * T, 40, {}),
    # Spielplatz
    ('spielplatz/00', 27 * T, 49, {}), ('spielplatz/01', 35 * T, 48, {}), ('spielplatz/02', 38 * T, 54, {}),
    ('baeume/12', 30 * T + 8, 63, {}), ('baeume/14', 25 * T, 60, {}), ('klein/26', 27 * T, 66, {}),
    ('klein/24', 23 * T, 61, {}), ('spielplatz/14', 33 * T, 56, {}),
    ('baeume/04', 47 * T, 66, {}), ('baeume/05', 21 * T + 8, 44, {}),
    # Garten (Beeterde): Beete, Kuebel, Windmuehle
    ('spielplatz/15', 6 * T + 8, 63, {}), ('baeume/15', 12 * T + 8, 63, {}), ('baeume/13', 9 * T + 8, 67, {}),
    ('klein/40', 4 * T + 8, 66, {}), ('klein/37', 14 * T, 66, {}), ('klein/36', 7 * T + 8, 68, {}),
    # Strasse: geparkte Spielzeugautos, Hydranten, Briefkaesten
    ('klein/00', 31 * T, 12, {}), ('klein/01', 45 * T, 28, {}), ('klein/00', 25 * T, 37, {}), ('klein/01', 59 * T, 9, {}),
    (BRIEF, 43 * T + 8, 15, {}), ('baeume/09', 29 * T + 8, 28, {}),          # Hydranten (zu gross) weggelassen
    ('baeume/09', 46 * T + 8, 46, {}), ('baeume/05', 17 * T + 8, 23, {}),
    # Teich: Boot am Ufer
    ('klein/08', 36 * T, 61, {}),
]
# Laternen in festem Rhythmus entlang der Gehwege (alle 6 Kacheln), Wegweiser an den Kreuzungen
for y in (6, 12, 26, 32):
    FEST += [(LAMPE, 29 * T + 8, y, {'anim': 'lampe'}), (LAMPE, 43 * T + 8, y, {'anim': 'lampe'}),
             (LAMPE, 57 * T + 8, y, {'anim': 'lampe'})]
for x in (24, 38, 52):
    FEST += [(LAMPE, x * T + 8, 19, {'anim': 'lampe'}), (LAMPE, x * T + 8, 35, {'anim': 'lampe'})]
# Haine (x0, y0, x1, y1, Dichte): Baeume nur auf Gras
HAINE = [(2, 4, 28, 10, 0.05), (2, 14, 15, 18, 0.06), (2, 39, 28, 58, 0.06), (11, 23, 17, 34, 0.06),
         (33, 4, 42, 18, 0.04), (47, 4, 56, 18, 0.04), (33, 23, 42, 34, 0.04), (47, 23, 56, 34, 0.04),
         (47, 39, 58, 48, 0.08), (30, 64, 58, 70, 0.07), (46, 58, 58, 66, 0.06), (14, 60, 22, 70, 0.06),
         (2, 70, 10, 71, 0.1)]
STREU = {'klein/09': 6, 'klein/10': 6, 'klein/12': 8, 'klein/11': 3, 'klein/05': 2, 'klein/56': 2, 'klein/58': 1,
         'klein/15': 1, 'klein/02': 1, 'klein/43': 1, 'klein/30': 1, 'klein/04': 1}


def main():
    rnd = random.Random(10)
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cls = lay['klassen']
    cols, rows = lay['groesse']
    lvl = np.load(os.path.join(KARTE, 'pixelhoehe.npy'))
    os.makedirs(os.path.join(OBJ, 'sauber'), exist_ok=True)
    gesperrt = set()
    for (x0, y0, x1, y1) in lay.get('bruecken', []):
        for y in range(y0 - 1, y1 + 2):
            for x in range(x0 - 1, x1 + 2):
                gesperrt.add((x, y))
    for tp in lay.get('teleporter', []):
        for y in range(tp['y'] - 1, tp['y'] + tp['h'] + 1):
            for x in range(tp['x'], tp['x'] + tp['b'] + 2):
                gesperrt.add((x, y))
    cache, alpha = {}, {}
    objekte, belegt = [], set()
    pixel = np.zeros(lvl.shape, bool)

    def sprite(name, spiegeln=False):
        key = (name, spiegeln)
        if key not in cache:
            if name == 'turm':                                   # Eckturm aus der Burgfront ausgeschnitten
                a = np.array(Image.open(os.path.join(OBJ, 'burg/00.png')).convert('RGBA'))
                a[:, 46:, 3] = 0
                a[80:, 27:, 3] = 0
                sp = Image.fromarray(a)
                sp = sp.crop(sp.getbbox())
            else:
                sp = saeubern(Image.open(os.path.join(OBJ, name + '.png')).convert('RGBA'))
                if name.startswith(('bahnhof/', 'haeuser', 'spielplatz/', 'baeume/')):
                    sp = groesstes_teil(sp)                          # PixelLab-Reste (z. B. Glocke unter der Lok)
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
        return not (pixel[y0:y1, x0:x1] & a[y0 - y:y1 - y, x0 - x:x1 - x]).any()

    def belegen(datei, x, y):
        a = np.array(Image.fromarray((alpha[datei] * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(5))) > 0
        h_, w_ = a.shape
        y0, x0 = max(0, y), max(0, x)
        y1, x1 = min(pixel.shape[0], y + h_), min(pixel.shape[1], x + w_)
        pixel[y0:y1, x0:x1] |= a[y0 - y:y1 - y, x0 - x:x1 - x]

    def auf_land(datei, x, y):
        """Regel 'Gebaeude stehen ganz auf Land': jede Spalte des Sprites ueber Boden (nicht Wasser/Mauer/Hecke)."""
        a = alpha[datei]
        ys, xs = np.nonzero(a)
        ys, xs = ys + y, xs + x
        ok = (ys >= 0) & (ys < lvl.shape[0]) & (xs >= 0) & (xs < lvl.shape[1])
        if not ok.all():
            return False
        return (lvl[ys, xs] == 1).mean() > 0.97

    def fest_setzen(name, X, fy, opt, spiegeln=False, suchen=False, an_wand=False, pruefen=True, melden=False):
        opt = dict(opt)
        datei, h, zu, mitte = sprite(name, spiegeln or opt.pop('spiegeln', False))
        kand = [(X, fy)]
        if suchen:
            kand += sorted(((X + dx * T, fy + dy) for dx in range(-2, 3) for dy in range(-2, 3) if dx or dy),
                           key=lambda k: abs(k[0] - X) / T + abs(k[1] - fy))
        for (kx, ky) in kand:
            tx = int(kx // T)
            if (tx, ky) in gesperrt:
                continue
            x = raster_x(alpha[datei], kx) if not opt.get('achse') else int(round(kx - mitte))
            y = (ky + 1) * T - 1 - zu
            if not pruefen:
                break
            gross = name.startswith(('haeuser', 'bahnhof/00'))
            if bewerten(lvl, alpha[datei], x, y) and frei_px(datei, x, y) and (not gross or auf_land(datei, x, y)) \
                    and lvl[min(lvl.shape[0] - 1, ky * T + 15), min(lvl.shape[1] - 1, int(kx))] == 1:
                break
        else:
            if melden:
                print('  keine passende Stelle:', name, (X // T, fy))
            return None
        o = {'datei': datei, 'basis': name, 'x': x, 'y': y, 'fuss': h, 'kachel': [int(kx // T), ky],
             'ebene': 0 if name in FLACH else 1}
        if name in LIEGEND:
            o['liegend'] = True
        if name in WIND:
            o['anim'] = 'wehen'
        if an_wand:
            o.update({'an_wand': True, 'kein_schatten': True, 'keine_verdeckung': True, 'vorrang': True, 'fest_pos': True})
        o.update(opt)
        objekte.append(o)
        belegt.add((int(kx // T), ky))
        if name not in FLACH:
            belegen(datei, x, y)
        return o

    # 1) Burg: Front auf der Achse (Wandhoehe passt genau zur rosa Mauer), Ecktuerme in gleichem Abstand
    datei, h, zu, mitte = sprite('burg/00')
    objekte.append({'datei': datei, 'basis': 'burg/00', 'x': int(ACHSE_BURG - mitte), 'y': WAND_FUSS - zu, 'fuss': h,
                    'kachel': [76, 34], 'ebene': 1, 'an_wand': True, 'kein_schatten': True, 'keine_verdeckung': True,
                    'vorrang': True, 'fest_pos': True, 'anim': 'fahne'})
    belegen(datei, int(ACHSE_BURG - mitte), WAND_FUSS - zu)
    td, th, tzu, tm = sprite('turm')
    for x_l in (62 * T,):
        for xx in (x_l, 2 * ACHSE_BURG - x_l - alpha[td].shape[1]):
            objekte.append({'datei': td, 'basis': 'turm', 'x': int(xx), 'y': WAND_FUSS - tzu, 'fuss': th,
                            'kachel': [int(xx // T), 34], 'ebene': 1, 'an_wand': True, 'kein_schatten': True,
                            'keine_verdeckung': True, 'vorrang': True, 'fest_pos': True, 'anim': 'fahne'})
            belegen(td, int(xx), WAND_FUSS - tzu)
    for xx in (60 * T, 84 * T):                              # Ecktuerme an der Suedmauer (stehen im Hof davor)
        objekte.append({'datei': td, 'basis': 'turm', 'x': int(xx), 'y': 71 * T + 15 - tzu, 'fuss': th,
                        'kachel': [xx // T, 71], 'ebene': 1, 'vorrang': True, 'fest_pos': True, 'anim': 'fahne'})
        belegen(td, int(xx), 71 * T + 15 - tzu)
    # 2) Zug auf dem unteren Gleis (Raeder auf der Schiene), Lok vorne links (Schienenraeumer zeigt nach links)
    gy = lay['gleise'][1]['y'] * T + 13
    x = 66 * T
    for name in ('bahnhof/01', 'bahnhof/02', 'bahnhof/02'):
        datei, h, zu, mitte = sprite(name)
        objekte.append({'datei': datei, 'basis': name, 'x': x, 'y': gy - zu, 'fuss': h, 'kachel': [x // T, gy // T],
                        'ebene': 1, 'fest_pos': True, 'vorrang': True, **({'anim': 'rauch'} if name == 'bahnhof/01' else {})})
        belegen(datei, x, gy - zu)
        x += alpha[datei].shape[1] + 1
    # 3) Haeuser (Layout: Mitte, Fussreihe)
    for (name, X, fy, _, _) in lay['haeuser']:
        fest_setzen(name, X, fy, {'vorrang': True}, melden=True)
    # 4) feste Objekte
    for (name, X, fy, opt) in FEST:
        fest_setzen(name, X, fy, opt, suchen=not opt.get('symm') and not opt.get('achse'), melden=True)
    # 5) Baeume in Hainen, Regel 5: Einzelbaeume bekommen Begleiter
    baeume = []
    for (x0, y0, x1, y1, d) in HAINE:
        for ty in range(y0, y1 + 1):
            for tx in range(x0, x1 + 1):
                if cls[ty][tx] == 'g' and rnd.random() < d and (tx, ty) not in belegt:
                    o = fest_setzen(rnd.choice(BAEUME), tx * T + 8, ty, {'spiegeln': rnd.random() < 0.5})
                    if o:
                        o['anim'] = 'baum'
                        baeume.append(o)
    for o in baeume:
        kx, ky = o['kachel']
        if not [p for p in baeume if p is not o and abs(p['kachel'][0] - kx) <= 3 and abs(p['kachel'][1] - ky) <= 3]:
            for dx in (rnd.choice((-1, 1)), ):
                b = fest_setzen(rnd.choice(BUESCHE[:2]), (kx + dx * 2) * T + 8, ky, {})
                if b:
                    b['begleiter'] = True
            fest_setzen(rnd.choice(BUESCHE[2:]), (kx + rnd.choice((-1, 1))) * T + 8, ky + 1, {'begleiter': True})
    # 6) Kleinkram auf Gras (unregelmaessig, eher wenig), nie auf/neben Strassen und Plaetzen
    namen, gew = list(STREU), list(STREU.values())
    n = 0
    for _ in range(6000):
        if n >= 70:
            break
        tx, ty = rnd.randrange(2, 60), rnd.randrange(3, 72)
        if any(cls[yy][xx] != 'g' for yy in range(ty - 1, ty + 2) for xx in range(tx - 1, tx + 2)):
            continue
        name = rnd.choices(namen, weights=gew)[0]
        if fest_setzen(name, tx * T + 8, ty, {}):
            n += 1
    # Spielzeug im Burghof (nicht auf Weg/Rahmen)
    n = 0
    for _ in range(3000):
        if n >= 6:
            break
        tx, ty = rnd.randrange(61, 85), rnd.randrange(37, 71)
        if any(cls[yy][xx] != 'k' for yy in range(ty - 1, ty + 2) for xx in range(tx - 1, tx + 2)):
            continue
        if fest_setzen(rnd.choice(SPIELZEUG), tx * T + 8, ty, {}):
            n += 1
    json.dump(objekte, open(os.path.join(OBJ, 'platzierung.json'), 'w'), indent=0)
    print(len(objekte), 'Objekte gesetzt')


def symmetrie():
    """Paare exakt spiegelsymmetrisch zur Achse ihres Platzes; Objekte mit 'achse' genau auf die Achse."""
    pf = os.path.join(OBJ, 'platzierung.json')
    objs = json.load(open(pf))
    for o in objs:
        if o.get('achse'):
            a_ = np.array(Image.open(os.path.join(OBJ, o['datei'])).getchannel('A')) > 128
            xs_ = np.nonzero(a_.any(axis=0))[0]
            o['x'] = int(round(o['achse'] - (xs_.min() + xs_.max() + 1) / 2.0))
    paare = {}
    for o in objs:
        if o.get('symm'):
            paare.setdefault(o['symm'], []).append(o)
    achsen = {'bsl': ACHSE_BAHNHOF, 'bsb': ACHSE_BAHNHOF, 'ul': ACHSE_UHR, 'ub': ACHSE_UHR, 'bl1': ACHSE_BRUNNEN,
              'bl2': ACHSE_BRUNNEN, 'bb': ACHSE_BRUNNEN}
    for name, ps in paare.items():
        if len(ps) != 2:
            print('  Paar unvollstaendig:', name, len(ps))
            continue
        l, r = sorted(ps, key=lambda o: o['x'])
        achse = achsen.get(name, ACHSE_BURG)
        a_ = np.array(Image.open(os.path.join(OBJ, l['datei'])).getchannel('A')) > 128
        xs_ = np.nonzero(a_.any(axis=0))[0]
        # sichtbare Mitte des linken Objekts spiegeln
        ml = l['x'] + (xs_.min() + xs_.max() + 1) / 2.0
        r['x'] = int(round(2 * achse - ml - (xs_.min() + xs_.max() + 1) / 2.0))
        r['y'] = l['y']
    json.dump(objs, open(pf, 'w'), indent=0)
    print('Symmetrie: %d Paare' % len(paare))


if __name__ == '__main__':
    symmetrie() if sys.argv[1:] == ['symmetrie'] else main()
