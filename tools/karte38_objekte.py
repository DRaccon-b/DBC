"""Objekte fuer Karte 38 (Deva Transit, A03 Nr. 5) -> assets/objekte/karte38/platzierung.json

  python3 tools/karte38_objekte.py && python3 tools/karte38_bauen.py

Grosse Objekte zuerst: drei Bahnhofsgebaeude (neu mit PixelLab: k38_bahnhof_glas, _glas_b, _beige - Nutzer: grosse
Gebaeude gern neu erzeugen), Wartehaeuschen auf den Bahnsteigen (k38_unterstand), Treppenabgaenge (k38_treppe); dann
Automaten, Baenke (unter den Daechern und frei), Muelleimer, Laternen, Infostaender, Verbotsschilder, Poller und
Bodengitter nach der Vorlage (Karte 18 + k38_klein), sparsam und ohne Reihen; zuletzt der Baumguertel am Rand.
Pixelgenaue Pruefung (2 px), kein Bodenwall, Teleporter frei, nichts auf Gleisen und Bahnsteigkanten.
"""
import json, math, os, random, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte38')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte38')
T = 16
FREMD = {}
for i in (0, 1, 12, 18, 40, 42):
    FREMD['k18s/%02d' % i] = 'karte18/strasse/%02d.png' % i
for i in (0, 1, 2, 4, 9, 12, 13, 14, 15):
    FREMD['k01/baum%02d' % i] = 'karte01/baeume/%02d.png' % i
WALD = ['k01/baum%02d' % i for i in (0, 1, 2, 4, 9, 15)]
BUSCH = ['k01/baum%02d' % i for i in (12, 13, 14)]
LAMPE = {'anim': 'leuchten', 'licht': [4, 7], 'licht_box': [2, 5, 6, 10], 'licht_r': 9}
AUTOMAT = {'anim': 'leuchten', 'licht_box': [3, 3, 17, 18], 'licht_r': 7}

# Gebaeude (sprite, Mitte x in Vorlagen-px, Fusszeile Vorlage)
GEBAEUDE = [('bahnhof_glas/00', 152, 14), ('bahnhof_glas_b/01', 160, 42), ('bahnhof_beige/00', 1376, 70)]
# Wartehaeuschen (Mitte x Vorlagen-px, Fusszeile) - Bahnsteige oben und Mitte wie in der Vorlage
UNTERSTAENDE = [(560, 23), (1055, 23), (575, 47), (1100, 47)]
TREPPEN = [('treppe/01', 76 * 16 + 8, 13), ('treppe_breit/00', 87 * 16 + 8, 22), ('treppe/01', 12 * 16 + 8, 61),
           ('treppe_schmal/01', 17 * 16 + 16, 13)]   # breite offene Treppe oben rechts (vor dem mittleren Bahnhof: Eingang frei)   # (sprite, Mitte x px, Fusszeile)
# Poller-Paare mit Verbotsschild genau auf ihrer Achse (Vorlage): (Kachel links, Kachel rechts, Fusszeile)
POLLER = [(43, 47, 13), (54, 58, 73), (33, 37, 73)]
# (sprite, Kachel x, Fusszeile, Optionen) - Vorlagenkacheln
KLEIN = [
    ('k18s/00', 28, 6, {}), ('k18s/42', 69, 6, {}), ('k18s/01', 69, 16, {}), ('k18s/00', 20, 19, {}),
    ('k18s/42', 12, 20, {}), ('klein/09', 19, 9, {}), ('klein/09', 28, 9, {}), ('k18s/12', 30, 9, {}),
    ('klein/09', 58, 21, {}), ('klein/09', 80, 18, {}), ('k18s/12', 82, 18, {}),
    ('klein/02', 47, 17, {}), ('klein/02', 74, 17, {}), ('klein/01', 79, 21, {}),
    ('k18s/18', 41, 21, LAMPE), ('k18s/18', 72, 21, LAMPE), ('klein/03', 17, 6, {'liegend': True, 'schattenlos': True}),
    ('klein/03', 78, 6, {'liegend': True, 'schattenlos': True}), 
    ('k18s/12', 8, 47, {}), ('k18s/00', 28, 35, {}), ('k18s/01', 17, 36, {}), ('k18s/42', 82, 45, {}),
    ('klein/09', 19, 38, {}), ('klein/09', 77, 36, {}), ('k18s/12', 22, 38, {}), ('k18s/12', 80, 36, {}),
    ('klein/02', 24, 42, {}), ('klein/02', 47, 42, {}), ('klein/02', 75, 42, {}),
    ('k18s/18', 26, 45, LAMPE), ('k18s/18', 57, 45, LAMPE), ('klein/01', 16, 33, {}),
    ('klein/03', 17, 41, {'liegend': True, 'schattenlos': True}), ('klein/03', 78, 34, {'liegend': True, 'schattenlos': True}),
    ('k18s/42', 51, 62, {}), ('k18s/00', 79, 58, {}), ('k18s/01', 77, 68, {}), ('k18s/40', 74, 71, {}),
    ('klein/09', 21, 62, {}), ('klein/09', 45, 70, {}), ('klein/09', 65, 64, {}), ('klein/09', 26, 72, {}),
    ('k18s/12', 24, 62, {}), ('k18s/12', 73, 64, {}), ('klein/01', 19, 59, {}), ('klein/01', 65, 59, {}),
    ('klein/01', 88, 57, {}), ('klein/02', 27, 65, {}), ('klein/02', 69, 65, {}),
    ('k18s/18', 30, 69, LAMPE), ('k18s/18', 71, 70, LAMPE), ('klein/03', 17, 69, {'liegend': True, 'schattenlos': True}),
]


def main():
    rnd = random.Random(38)
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cls = lay['klassen']
    cols, rows = lay['groesse']
    P = lay['versatz']
    OFF = P * T

    def k(tx, ty):
        return cls[min(rows - 1, max(0, ty))][min(cols - 1, max(0, tx))]

    for name, quelle in FREMD.items():
        ziel = os.path.join(OBJ, name + '.png')
        os.makedirs(os.path.dirname(ziel), exist_ok=True)
        shutil.copy(os.path.join(ROOT, 'assets', 'objekte', quelle), ziel)
    tps = [(t['x'] * T - 2 * T, t['y'] * T - 2 * T, (t['x'] + t['b'] + 2) * T, (t['y'] + t['h'] + 2) * T)
           for t in lay['teleporter']]
    tps_eng = [(t['x'] * T, t['y'] * T, (t['x'] + t['b']) * T - 1, (t['y'] + t['h']) * T - 1) for t in lay['teleporter']]
    leit_r = [((x0 + 0) * T, y * T + 3, (x1 + 1) * T - 1, y * T + 12) for (x0, x1, y) in lay['leitstreifen']]
    kanten = set()                                               # Bahnsteigkanten-Zeilen (nichts darauf)
    for (y0, y1) in lay['gleisbaender']:
        kanten |= {y0 - 1, y1 + 1}
    objekte, rects = [], []

    def schnitt(a, b, rand=0):
        return not (a[2] + rand < b[0] or b[2] + rand < a[0] or a[3] + rand < b[1] or b[3] + rand < a[1])

    def setze(name, cx, fy, opt=None, spiegeln=False, art='objekt', pruefen=True, sortier=None):
        sp = Image.open(os.path.join(OBJ, name + '.png')).convert('RGBA')
        if spiegeln:
            sp = sp.transpose(Image.FLIP_LEFT_RIGHT)
        datei = 'varianten/%s%s.png' % (name.replace('/', '-'), '_m' if spiegeln else '')
        os.makedirs(os.path.join(OBJ, 'varianten'), exist_ok=True)
        sp.save(os.path.join(OBJ, datei))
        bb = sp.getbbox()
        x = int(round(cx - (bb[0] + bb[2]) / 2.0))
        y = int(fy - (bb[3] - 1))
        r = (x + bb[0], y + bb[1], x + bb[2] - 1, y + bb[3] - 1)
        if art == 'wald':
            if any(schnitt(r, t_, 3) for t_ in tps_eng):              # Guertel: nur der Teleporter selbst frei
                return None
            for yy in range(max(0, r[1] // T), min(rows - 1, r[3] // T) + 1):
                for xx in range(max(0, r[0] // T), min(cols - 1, r[2] // T) + 1):
                    if cls[yy][xx] != 'h':
                        ov_y = min(r[3], yy * T + T - 1) - max(r[1], yy * T) + 1
                        ov_x = min(r[2], xx * T + T - 1) - max(r[0], xx * T) + 1
                        if ov_y > 4 and ov_x > 4:
                            return None
            if any(art2 != 'wald' and schnitt(r, rr, 2) for (*rr, art2) in rects):
                return None
        elif pruefen:
            if any(schnitt(r, tuple(rr), 2) for (*rr, art2) in rects) or any(schnitt(r, t_, 0) for t_ in tps):
                return None
            if not (opt or {}).get('liegend') and any(schnitt(r, l_, 1) for l_ in leit_r):
                return None                                       # nie auf/vor Leitstreifen
            if any(r[1] <= kz * T + T - 1 and r[3] >= kz * T for kz in kanten):
                return None                                       # nie auf/ueber der Bahnsteigkante
            for xx in range(r[0] // T, r[2] // T + 1):            # Fuss auf Bahnsteig, nie auf Gleis/Kante/Guertel
                ty_ = r[3] // T
                if k(xx, ty_) not in 'kpd' or ty_ in kanten:
                    return None
        o = {'datei': datei, 'basis': name, 'x': x, 'y': y, 'fuss': bb[3] - 1, 'kachel': [int(cx) // T, int(fy) // T],
             'ebene': 1, 'ohne_wall': True}
        if art not in ('wald',) and not (opt or {}).get('liegend'):
            o['nur_kontakt'] = True                               # helles Pflaster: nur Kontaktschatten (Pruefliste K36)
        o.update(opt or {})
        if sortier is not None:
            o['sortier'] = sortier
        objekte.append(o)
        rects.append(list(r) + [art])
        return o

    def kachel(name, tx, fy_tile, opt=None, spiegeln=False):
        """Am Raster: kleinster Kachelblock, waagerecht mittig, Fuss buendig (Regel 1b); naechste freie Stelle bis 2."""
        sp = Image.open(os.path.join(OBJ, name + '.png'))
        bw = sp.getbbox()[2] - sp.getbbox()[0]
        wt = max(1, math.ceil(bw / T))
        for d in range(3):
            for dy in range(-d, d + 1):
                for dx in range(-d, d + 1):
                    if max(abs(dx), abs(dy)) != d:
                        continue
                    x0, y = tx + dx - (wt - 1) // 2, fy_tile + dy
                    cx = x0 * T + wt * T / 2.0
                    if setze(name, cx, y * T + T - 1, opt, spiegeln):
                        return True
        print('nicht gesetzt:', name, tx - P, fy_tile - P)
        return False

    for (name, cx, fy) in GEBAEUDE:
        if not setze(name, cx + OFF, (fy + P) * T + T - 1, {'gebaeude': True, 'nur_kontakt': True}, art='gebaeude',
                     pruefen=False):
            print('Gebaeude nicht gesetzt:', name)
    for i, (cx, fy) in enumerate(UNTERSTAENDE):
        cx = int(cx // T) * T + 8                                   # 144 px = 9 Kacheln: linke Kante auf dem Raster
        o = setze('unterstand/00', cx + OFF, (fy + P) * T + T - 1, {'gebaeude': True, 'schattenlos': True}, art='gebaeude')
        if not o:
            print('Unterstand nicht gesetzt:', cx, fy); continue
        # Bank unter dem Dach vor der Glaswand (gewollt im Unterstand, nach ihm gezeichnet)
        setze('klein/09', cx + OFF - 8 + (-16 if i % 2 else 16), (fy + P) * T + T - 4, {'nur_kontakt': True}, pruefen=False,
              sortier=o['y'] + o['fuss'] + 1)
    for (name, cx, fy) in TREPPEN:
        if not os.path.exists(os.path.join(OBJ, name + '.png')):
            print('fehlt:', name); continue
        if not any(setze(name, cx + OFF, (fy + P + d) * T + T - 1, {'liegend': True, 'schattenlos': True}, art='gebaeude')
                   for d in (0, 1, 2, -1)):
            print('Treppe nicht gesetzt:', name, cx, fy)
    for (xa, xb, fy) in POLLER:                                    # Paar + Schild exakt auf der Achse
        ca, cb = (xa + P) * T + T / 2.0, (xb + P) * T + T / 2.0
        fyp = (fy + P) * T + T - 1
        if setze('klein/00', ca, fyp, {}) and setze('klein/00', cb, fyp, {}):
            setze('klein/01', (ca + cb) / 2.0, fyp, {})
    for i, (name, tx, fy, opt) in enumerate(KLEIN):
        kachel(name, tx + P, fy + P, dict(opt), spiegeln=(name == 'klein/09' and i % 3 == 0))
    # ---------------------------------------------------------------- Baumguertel am Kartenrand (Nutzer)
    n_w = 0
    for ty in range(rows):
        for tx in range(cols):
            if cls[ty][tx] == 'h' and (tx + ty) % 2 == 0:
                if setze(rnd.choice(WALD), tx * T + T / 2.0, ty * T + T - 1, {'anim': 'baum'}, rnd.random() < 0.5, 'wald'):
                    n_w += 1
    deck = np.zeros((rows * T, cols * T), bool)                  # echte Sprite-Pixel (nicht Bildrechtecke)

    def decken(o):
        al = np.array(Image.open(os.path.join(OBJ, o['datei'])).convert('RGBA'))[..., 3] > 0
        y0, x0 = o['y'], o['x']
        ys, xs = np.nonzero(al)
        ys, xs = ys + y0, xs + x0
        ok = (ys >= 0) & (ys < rows * T) & (xs >= 0) & (xs < cols * T)
        deck[ys[ok], xs[ok]] = True
    for o in objekte:
        decken(o)
    luecken = 0
    for durchgang in range(2):                                   # Luecken mit Bueschen schliessen (kein nackter Rasen)
        for ty in range(rows):
            for tx in range(cols):
                if cls[ty][tx] == 'h' and deck[ty * T:(ty + 1) * T, tx * T:(tx + 1) * T].mean() < 0.75:
                    for dx in ((0, -5, 5) if durchgang else (0,)):
                        o = setze(rnd.choice(BUSCH + WALD[:2] if durchgang == 0 else BUSCH), tx * T + T / 2.0 + dx,
                                  ty * T + T - 1, {'anim': 'wehen'}, rnd.random() < 0.5, 'wald')
                        if o:
                            decken(o); luecken += 1
                            break
    for o in objekte:
        if o['basis'].startswith('k01/'):
            o['nur_kontakt'] = True
    print('Baumguertel:', n_w, 'Baeume,', luecken, 'Buesche')
    json.dump(objekte, open(os.path.join(OBJ, 'platzierung.json'), 'w'), indent=0)
    print(len(objekte), 'Objekte')


if __name__ == '__main__':
    main()
    import regeln_a02
    regeln_a02.objekte_pruefen('karte38', '')
