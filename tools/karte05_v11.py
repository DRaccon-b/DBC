"""Karte 05 (Freezeland) v1.1 - Regeln aus CLAUDE.md anwenden.

  python3 tools/karte05_v11.py wege        # Regel 6: Wege in natuerlichen Boegen (layout.json, Original in v1.0)
  python3 tools/karte05_objekte.py          # Objekte wie bisher setzen
  python3 tools/karte05_v11.py objekte     # Regeln 1/1b, 8, 5, Einbettung, Abschlusskontrolle
  python3 tools/karte05_bauen.py

objekte:
  1/1b  jedes Objekt im kleinsten Kachelblock, waagerecht zentriert, Fuss buendig auf der Kachelunterkante
  8     Baeume ueberlappen nur an den aeusseren Spalten (Waldrand = dichter Wald: bis zwei Spalten), Sockel nie
        auf derselben Kachel; Waldrand danach regelkonform dicht neu gepackt
  5     einzelne Baeume im Schneefeld bekommen Begleitung (zweiter Baum + Pflanze vor dem Sockel oder 2-3 Pflanzen)
        aus den Schnee-Sets (Karte 07 deko_schnee, Regel 3)
  Einbettung: Felsen bekommen Frostgras/Schneeblume an den Sockelecken
  Kontrolle: Fuss/Unterteil auf derselben Ebene (karte05_pruefen.bewerten), keine ungewollten Pixel-Ueberlappungen
"""
import json, math, os, random, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageFilter
from karte05_pruefen import bewerten
from karte01_v11_baeume import erlaubt

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte05')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte05')
K7S = os.path.join(ROOT, 'assets', 'objekte', 'karte07', 'deko_schnee')
T = 16
BAEUME = {'baeume/00', 'baeume/01', 'baeume/02', 'baeume/03', 'klein/27', 'klein/49'}
GROSSE_TANNEN = ['baeume/00', 'baeume/01', 'baeume/02', 'baeume/00', 'baeume/01']
DECKER = [0, 1, 2, 12, 15, 21, 23, 29, 35, 39, 50, 53]          # Schnee-Set: Frostgras, Farn, Bueschel ...
BLUMEN = [5, 9, 28, 30, 36, 41, 44, 45, 14]                        # Schneegloeckchen, Winterheide, Eisblume ...
FELSEN = {'gross/01', 'wasserfall/02', 'mittel/00', 'mittel/09', 'mittel/15', 'findling/00', 'natur/04', 'natur/05', 'server/00', 'server/11'}
# v1.1-Ideen (PixelLab k5_server/k5_wasserfall/k5_natur/k5_findling): (sprite, Ankerkachel, Anzahl, Suchradius)
NEU = [('server/00', (62, 52), 1, 10), ('server/11', (95, 32), 1, 10), ('server/00', (20, 47), 1, 8),
       ('findling/00', (12, 28), 1, 10), ('findling/00', (88, 44), 1, 10), ('findling/00', (56, 68), 1, 8),
       ('findling/00', (97, 76), 1, 10), ('findling/00', (40, 30), 1, 10)]
STREU_NEU = {'natur/04': 5, 'natur/05': 5, 'natur/02': 6, 'natur/03': 5, 'natur/00': 14, 'natur/01': 14}


# ---------------------------------------------------------------- Regel 6: Wege
def glatt(feld, sigma):
    im = Image.fromarray((np.clip(feld, 0, 1) * 255).astype(np.uint8))
    return np.array(im.filter(ImageFilter.GaussianBlur(sigma))).astype(np.float32) / 255.0


def wege():
    pf = os.path.join(KARTE, 'layout.json')
    alt = os.path.join(KARTE, 'v1.0', 'layout_v1.0.json')
    os.makedirs(os.path.dirname(alt), exist_ok=True)
    if not os.path.exists(alt):
        shutil.copy(pf, alt)
    lay = json.load(open(alt))
    lay['treppen'] = [t for t in lay['treppen'] if t[0] != 49]          # mittlere Treppe entfernt (Nutzer)
    g = np.array([list(r) for r in lay['klassen']])
    hoehe = np.array([[int(c) for c in r] for r in lay['hoehe']])
    rows, cols = g.shape
    weg = g == 'w'
    darf = np.isin(g, ['s', 'l', 'w'])                       # Wege nur auf Schnee/Eisboden verschieben
    anker = np.zeros((rows, cols), bool)
    for (x0, x1, y0, y1, _r) in lay['treppen']:
        anker[max(0, y0 - 3):y1 + 4, max(0, x0 - 2):x1 + 3] = True
    for tp in lay['teleporter']:
        anker[max(0, tp['y'] - 3):tp['y'] + tp['h'] + 3, max(0, tp['x'] - 3):tp['x'] + tp['b'] + 3] = True
    anker[:, :6] = anker[:, -6:] = True
    anker[:3, :] = anker[-3:, :] = True
    # Hoehenkanten (Klippen) und alles, was kein Schnee/Eisboden/Weg ist, bleiben fest
    kante = np.zeros_like(anker)
    kante[:-1] |= hoehe[:-1] != hoehe[1:]
    kante[1:] |= hoehe[:-1] != hoehe[1:]
    kante[:, :-1] |= hoehe[:, :-1] != hoehe[:, 1:]
    kante[:, 1:] |= hoehe[:, :-1] != hoehe[:, 1:]
    anker |= kante | ~darf
    dist = np.where(anker, 0.0, 99.0)
    for _ in range(8):
        dist = np.minimum.reduce([dist, np.roll(dist, 1, 0) + 1, np.roll(dist, -1, 0) + 1,
                                  np.roll(dist, 1, 1) + 1, np.roll(dist, -1, 1) + 1])
    SUB = 4
    gew = glatt(np.kron(np.clip((dist - 1) / 4.0, 0, 1), np.ones((SUB, SUB))), SUB * 1.5)

    def rauschen(zelle, seed):
        rs = np.random.RandomState(seed)
        n = rs.rand(rows // zelle + 3, cols // zelle + 3).astype(np.float32) * 2 - 1
        im = Image.fromarray(n, mode='F').resize(((cols // zelle + 3) * zelle * SUB, (rows // zelle + 3) * zelle * SUB),
                                                 Image.BICUBIC)
        return np.array(im)[:rows * SUB, :cols * SUB]
    A = 2.6
    dx = rauschen(10, 3) * A * gew
    dy = rauschen(10, 7) * A * gew
    m = np.kron(weg, np.ones((SUB, SUB))).astype(np.float32)
    Hs, Ws = m.shape
    yy, xx = np.mgrid[0:Hs, 0:Ws].astype(np.float32)
    sy = np.clip(np.round(yy + dy * SUB), 0, Hs - 1).astype(int)
    sx = np.clip(np.round(xx + dx * SUB), 0, Ws - 1).astype(int)
    verbogen = glatt(m[sy, sx], SUB * 0.9) > 0.42
    neu = verbogen.reshape(rows, SUB, cols, SUB).mean(axis=(1, 3)) > 0.4
    neu[anker] = weg[anker]
    n = 0
    for y in range(rows):
        for x in range(cols):
            if not darf[y, x]:
                continue
            if neu[y, x] and not weg[y, x] and hoehe[y, x] == 1:
                g[y, x] = 'w'; n += 1
            elif not neu[y, x] and weg[y, x]:
                g[y, x] = 's'; n += 1
    # Regel 2: unter und ueber jeder Treppe ein Wegstueck in voller Treppenbreite (+1 je Seite)
    for (x0, x1, y0, y1, _r) in lay['treppen']:
        for (ya, yb) in ((y1 + 1, y1 + 4), (y0 - 3, y0)):
            for y in range(ya, yb):
                for x in range(x0 - 1, x1 + 2):
                    if 0 <= y < rows and 0 <= x < cols and g[y, x] in ('s', 'l', 'w'):
                        g[y, x] = 'w'
    # Teich auf dem Mittelplateau -> Bach -> Wasserfall (ueber die Klippe bei x 49-51) -> Bach -> zugefrorener See
    q = np.zeros((rows, cols), bool)
    yy_, xx_ = np.mgrid[0:rows, 0:cols]
    q |= ((xx_ - 49.5) / 5.5) ** 2 + ((yy_ - 6.5) / 3.3) ** 2 <= 1           # Teich
    for y in range(9, 17):                                                   # Bach oben (leicht geschwungen)
        x0 = 49 + (1 if 11 <= y <= 13 else 0)
        q[y, x0:x0 + 3] = True
    q[16, 49:52] = True
    for y in range(21, rows):                                                # Bach unten bis zum See
        if (g[y, 49:52] == 'i').all():
            break
        x0 = 49 + (1 if 24 <= y <= 25 else 0)
        q[y, x0:x0 + 3] = True
    for y in range(rows):
        for x in range(cols):
            if q[y, x] and g[y, x] in ('s', 'l', 'w', 'i'):
                if not (17 <= y <= 20):                                      # Wandzeilen: dort faellt der Wasserfall
                    g[y, x] = 'q'
    lay['wasserfaelle'] = [[49, 51]]
    # Bruecke, wo der untere Bach den Weg kreuzt
    wegzeilen = [y for y in range(21, rows) if q[y, 49:52].any() and (g[y, 46:49] == 'w').any() | (g[y, 52:55] == 'w').any()]
    lay['bruecken'] = [[48, min(wegzeilen), 52, max(wegzeilen)]] if wegzeilen else []
    # Waldrand oben (Kartenrand Zeilen 0-2), Teleporter oben rechts bleibt frei
    for y in range(0, 3):
        for x in range(cols):
            if x >= 103 or g[y, x] == 'q':
                continue
            g[y, x] = 'h'
    lay['klassen'] = [''.join(r) for r in g]
    json.dump(lay, open(pf, 'w'))
    farbe = {'s': (236, 240, 244), 'w': (150, 170, 190), 'l': (157, 210, 231), 'i': (114, 185, 211),
             'c': (138, 176, 198), 'h': (40, 90, 80), 'e': (150, 122, 86), 'd': (10, 25, 60), 'r': (120, 120, 120)}
    alt_g = np.array([list(r) for r in json.load(open(alt))['klassen']])
    bild = np.zeros((rows, cols * 2 + 2, 3), np.uint8)
    for y in range(rows):
        for x in range(cols):
            bild[y, x] = farbe.get(alt_g[y, x], (255, 0, 255))
            bild[y, cols + 2 + x] = farbe.get(g[y, x], (255, 0, 255))
    os.makedirs(os.path.join(KARTE, 'v1.1'), exist_ok=True)
    Image.fromarray(bild).resize(((cols * 2 + 2) * 4, rows * 4), Image.NEAREST).save(
        os.path.join(KARTE, 'v1.1', 'wege_vorher_nachher.png'))
    print('Regel 6: %d Wegzellen geaendert' % n)


# ---------------------------------------------------------------- Objekte
def objekte():
    rnd = random.Random(17)
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cls = lay['klassen']
    cols, rows = lay['groesse']
    lvl = np.load(os.path.join(KARTE, 'pixelhoehe.npy'))
    pf = os.path.join(OBJ, 'platzierung.json')
    objs = json.load(open(pf))
    gesperrt = set()
    for (x0, x1, y0, y1, _r) in lay.get('treppen', []):
        gesperrt |= {(x, y) for y in range(y0 - 4, y1 + 5) for x in range(x0 - 2, x1 + 3)}
    for tp in lay.get('teleporter', []):
        gesperrt |= {(x, y) for y in range(tp['y'] - 1, tp['y'] + tp['h'] + 1) for x in range(tp['x'] - 1, tp['x'] + tp['b'] + 1)}
    alpha, info = {}, {}

    def lade(datei):
        if datei not in info:
            sp = Image.open(os.path.join(OBJ, datei)).convert('RGBA')
            a = np.array(sp.getchannel('A')) >= 128
            ys, xs = np.nonzero(a)
            alpha[datei] = a
            info[datei] = (sp.height, int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()))
        return info[datei]

    def einrasten(o, kx, ky):
        h, x0, y0, x1, y1 = lade(o['datei'])
        bw, bh = x1 - x0 + 1, y1 - y0 + 1
        wt, ht = math.ceil(bw / T), math.ceil(bh / T)
        bx = kx - (wt - 1) // 2
        o.update(x=bx * T + (wt * T - bw) // 2 - x0, y=(ky + 1) * T - 1 - y1, fuss=h, kachel=[kx, ky],
                 block=[bx, ky - ht + 1, wt, ht])
        return o

    def ok_ebene(o):
        g, _ = bewerten(lvl, alpha[o['datei']], o['x'], o['y'])
        return g or o['basis'] in BAEUME and cls[o['kachel'][1]][o['kachel'][0]] == 'h'
    # --- Regel 1/1b
    n_fest = 0
    neu = []
    for o in objs:
        einrasten(o, *o['kachel'])
        if not ok_ebene(o) and not o['basis'].startswith(('gross/', 'baeume/')) and o['basis'] not in BAEUME:
            n_fest += 1
            continue
        bx, by, wt, ht = o['block']
        if not o['basis'].startswith('gross/') and any((x, by + ht - 1) in gesperrt for x in range(bx, bx + wt)):
            n_fest += 1                                   # Regel 2: Treppenzugang frei (Sockel nie im Treppenbereich)
            continue
        neu.append(o)
    objs = neu
    print('Regel 1/1b: %d Objekte im kleinsten Block, Fuss buendig; %d passten danach nicht mehr auf ihre Ebene'
          % (len(objs), n_fest))
    # --- Regel 8
    def wald(o):
        x, y = o['kachel']
        x, y = min(cols - 1, max(0, x)), min(rows - 1, max(0, y))
        return cls[y][x] == 'h'
    baeume = [o for o in objs if o['basis'] in BAEUME]
    rest = [o for o in objs if o['basis'] not in BAEUME]
    vorher = len(baeume)
    behalten = []
    eimer = {}

    def eintragen(b):
        eimer.setdefault((b['kachel'][0] // 8, b['kachel'][1] // 8), []).append(b)

    def nachbarn(x, y):
        for ex in range(x // 8 - 1, x // 8 + 2):
            for ey in range(y // 8 - 1, y // 8 + 2):
                yield from eimer.get((ex, ey), ())
    REGEL8 = False                                  # Nutzer: Baum-Aenderungen (Regel 8) verworfen -> Baeume wie v1.0
    if not REGEL8:
        behalten = list(baeume)
        for o in behalten:
            eintragen(o)
        baeume_sortiert = []
    else:
        baeume_sortiert = sorted(baeume, key=lambda o: (-o['block'][2] * o['block'][3], o['kachel'][1]))
    for o in baeume_sortiert:
        if all(erlaubt(o['block'], p['block'], wald(o) and wald(p)) for p in nachbarn(*o['kachel'])):
            behalten.append(o); eintragen(o)
    entfernt = vorher - len(behalten)
    rest_k = set()
    for o in rest:
        bx, by, wt, ht = o['block']
        rest_k |= {(x, y) for x in range(bx, bx + wt) for y in range(by, by + ht)}
    datei_von = {o['basis']: o['datei'] for o in baeume}
    gepackt = 0
    for durchgang in (range(2) if REGEL8 else ()):
        for y in range(rows):
            for x in range(cols):
                if cls[y][x] != 'h' or (x, y) in gesperrt:
                    continue
                namen = rnd.sample(GROSSE_TANNEN, len(GROSSE_TANNEN)) + ['klein/27', 'klein/49']
                for name in namen:
                    if name not in datei_von:
                        continue
                    o = einrasten({'datei': datei_von[name], 'basis': name, 'ebene': 1,
                                   'spiegeln_': False}, x + (0 if not durchgang else rnd.choice((-1, 1))), y)
                    o.pop('spiegeln_')
                    bx, by, wt, ht = o['block']
                    sockel = [(xx, y) for xx in range(bx, bx + wt)]
                    # Sockel im Wald; am Kartenrand darf der Baum seitlich ueber den Rand ragen
                    if any(0 <= xx < cols and cls[y][xx] != 'h' for xx, _ in sockel):
                        continue
                    if any((xx, yy) in rest_k for xx in range(bx, bx + wt) for yy in range(by, by + ht)):
                        continue
                    if o['block'][2] < 3:                         # kleine Tanne: Block darf nichts beruehren
                        frei = all(not (set(range(o['block'][0], o['block'][0] + o['block'][2])) &
                                        set(range(p['block'][0], p['block'][0] + p['block'][2])) and
                                        set(range(o['block'][1], o['block'][1] + o['block'][3])) &
                                        set(range(p['block'][1], p['block'][1] + p['block'][3])))
                                   for p in nachbarn(x, y))
                        if frei:
                            behalten.append(o); eintragen(o); gepackt += 1
                            break
                        continue
                    if all(erlaubt(o['block'], p['block'], True if wald(p) else False) for p in nachbarn(x, y)):
                        behalten.append(o); eintragen(o); gepackt += 1
                        break
    print('Regel 8: %d Baeume vorher, %d regelwidrige entfernt, %d am Waldrand neu gepackt, %d jetzt'
          % (vorher, entfernt, gepackt, len(behalten)))
    objs = rest + behalten
    # --- Regel 5 + Einbettung
    belegt = {}
    for i, o in enumerate(objs):
        bx, by, wt, ht = o['block']
        for x in range(bx, bx + wt):
            for y in range(by, by + ht):
                belegt[(x, y)] = i
    os.makedirs(os.path.join(OBJ, 'k7schnee'), exist_ok=True)

    def k7(i):
        d = 'k7schnee/%02d.png' % i
        if not os.path.exists(os.path.join(OBJ, d)):
            shutil.copy(os.path.join(K7S, '%02d.png' % i), os.path.join(OBJ, d))
        return d

    def setzen(datei, basis, kx, ky, frei_ok=(), anim=None):
        o = einrasten({'datei': datei, 'basis': basis, 'ebene': 1, 'v11': 'begleiter'}, kx, ky)
        bx, by, wt, ht = o['block']
        for x in range(bx, bx + wt):
            for y in range(by, by + ht):
                if not (0 <= x < cols and 0 <= y < rows) or (x, y) in gesperrt or cls[y][x] not in 'sl':
                    return None
                if (x, y) in belegt and (x, y) not in frei_ok:
                    return None
        if not bewerten(lvl, alpha[datei], o['x'], o['y'])[0]:
            return None
        if anim:
            o['anim'] = anim
        objs.append(o)
        for x in range(bx, bx + wt):
            for y in range(by, by + ht):
                belegt[(x, y)] = len(objs) - 1
        return o

    # --- neue Objekte (Server, Findlinge, Wasserfall, Streu: Eisblumen, Beerenstraeucher, halb eingeschneite Felsen)
    def neu_setzen(name, kx, ky, anim=None, pruefen=True, datei=None, art='neu'):
        d = datei or name + '.png'
        lade(d)
        o = einrasten({'datei': d, 'basis': name, 'ebene': 1, 'v11': art}, kx, ky)
        bx, by, wt, ht = o['block']
        if pruefen:
            for x in range(bx, bx + wt):
                for y in range(by, by + ht):
                    if not (0 <= x < cols and 0 <= y < rows) or (x, y) in gesperrt or cls[y][x] not in 'sl' \
                            or (x, y) in belegt:
                        return None
            if not bewerten(lvl, alpha[d], o['x'], o['y'])[0]:
                return None
        if anim:
            o['anim'] = anim
        objs.append(o)
        for x in range(bx, bx + wt):
            for y in range(by, by + ht):
                belegt[(x, y)] = len(objs) - 1
        return o
    weg_idx = set()
    n_neu = 0
    for (name, (ax, ay), anzahl, r) in NEU:
        orte = sorted(((ax + dx, ay + dy) for dx in range(-r, r + 1) for dy in range(-r, r + 1)),
                      key=lambda k: abs(k[0] - ax) + abs(k[1] - ay))
        gesetzt = 0
        for (kx, ky) in orte:
            if gesetzt >= anzahl:
                break
            if neu_setzen(name, kx, ky):
                gesetzt += 1; n_neu += 1
    namen_s, gew_s = list(STREU_NEU), list(STREU_NEU.values())
    ziel_s = sum(gew_s)
    gesetzt = 0
    for _ in range(8000):
        if gesetzt >= ziel_s:
            break
        name = rnd.choices(namen_s, gew_s)[0]
        kx, ky = rnd.randrange(4, cols - 6), rnd.randrange(6, rows - 6)
        anim = 'wehen' if name in ('natur/00', 'natur/01', 'natur/02', 'natur/03') else None
        if neu_setzen(name, kx, ky, anim=anim):
            gesetzt += 1; n_neu += 1
    hoehe_t = [[int(c) for c in r] for r in lay['hoehe']]
    # Eishoehle (bisheriges Sprite, Kanten gesaeubert in karte05_objekte): Tannen links/rechts als Uebergang
    for o in objs:
        if o['basis'] == 'gross/01':
            o['kein_schatten'] = True
    neu_setzen('baeume/00', 59, 13, anim='baum', pruefen=False, datei='sauber/baeume-00.png', art='begleiter')
    neu_setzen('baeume/01', 69, 13, anim='baum', pruefen=False, datei='sauber/baeume-01.png', art='begleiter')
    # Variation oben: zwei Server, zwei grosse Eiszapfen, ein paar grosse Tannen (mit Begleitung, Regel 5)
    OBEN = [('server/00', None, None, 1), ('server/11', None, None, 1),
            ('mittel/02', 'sauber/mittel-02.png', 'glitzern', 2), ('natur/25', None, 'glitzern', 1),
            ('baeume/00', 'sauber/baeume-00.png', 'baum', 2), ('baeume/01', 'sauber/baeume-01.png', 'baum', 2),
            ('baeume/02', 'sauber/baeume-02.png', 'baum', 2), ('baeume/03', 'sauber/baeume-03.png', 'baum', 2),
            ('natur/24', None, None, 4), ('baeume/01', 'sauber/baeume-01.png', 'baum', 1)]
    n_ob = 0
    grosse_oben = []
    for (name, datei, anim, anzahl) in OBEN:
        gesetzt = 0
        for _ in range(3000):
            if gesetzt >= anzahl:
                break
            kx, ky = rnd.randrange(3, cols - 4), rnd.randrange(4, 16)
            if hoehe_t[ky][kx] != 2:
                continue
            o = neu_setzen(name, kx, ky, anim=anim, datei=datei)
            if o:
                gesetzt += 1; n_ob += 1
                if name.startswith('baeume/'):
                    grosse_oben.append(o)
    print('Oben: %d groessere Objekte (Server, Eiszapfen, Tannen); Hoehle ersetzt' % n_ob)
    # mehr Deko oben auf den Plateaus (Hoehe 2): kleine Tannen, verschneite Buesche, Eiskristalle, Beeren,
    # Eisblumen, halb eingeschneite Felsen, Schnee-Deko aus Karte 07
    hoehe_t = [[int(c) for c in r] for r in lay['hoehe']]
    PLATEAU = {'natur/07': 6, 'natur/17': 6, 'natur/24': 5, 'natur/02': 4, 'natur/03': 3, 'natur/00': 6,
               'natur/01': 6, 'natur/04': 4, 'natur/05': 4, 'natur/06': 3, 'natur/21': 2, 'natur/50': 3}
    namen_p, gew_p = list(PLATEAU), list(PLATEAU.values())
    n_pl = 0
    deko_orte = []
    for _ in range(9000):
        if n_pl >= 40:
            break
        kx, ky = rnd.randrange(2, cols - 2), rnd.randrange(3, rows - 4)
        if hoehe_t[ky][kx] != 2:
            continue
        if any(abs(px - kx) <= 3 and abs(py - ky) <= 0 or abs(px - kx) <= 1 and abs(py - ky) <= 1
               for (px, py) in deko_orte):
            continue                                          # keine Reihen: Abstand in derselben Zeile
        name = rnd.choices(namen_p, gew_p)[0]
        anim = 'baum' if name in ('natur/07', 'natur/17') else 'glitzern' if name in ('natur/06', 'natur/21') else \
            'wehen' if name in ('natur/00', 'natur/01', 'natur/02', 'natur/03', 'natur/50') else None
        if neu_setzen(name, kx, ky, anim=anim):
            n_pl += 1
            deko_orte.append((kx, ky))
    print('Plateaus: %d Deko-Objekte oben' % n_pl)
    print('Neu: Wasserfall, Server, Findlinge + %d Streuobjekte (Eisblumen, Beeren, halb eingeschneite Felsen); '
          '%d alte Objekte am Wasserfall entfernt' % (gesetzt, len(weg_idx)))

    # schmaler Streifen ganz oben (Zeilen 3-7 unter dem Waldrand): keine Reihe aus Deko - je 4 Spalten hoechstens
    # ein kleines Objekt, unregelmaessig ausgeduennt (grosse Objekte wie Server, Tannen, Kristalle bleiben)
    gross_oben = ('server/', 'baeume/', 'mittel/02', 'natur/25', 'findling/')
    behalten_x = []
    for o in sorted([o for o in objs if o.get('v11') == 'neu' and o['kachel'][1] <= 7
                     and not o['basis'].startswith(gross_oben)], key=lambda o: rnd.random()):
        kx = o['kachel'][0]
        if any(abs(kx - x) <= 5 for x in behalten_x) or rnd.random() < 0.3:
            o['_weg'] = True
        else:
            behalten_x.append(kx)
    objs[:] = [o for o in objs if not o.get('_weg')]
    belegt.clear()
    for i, o in enumerate(objs):
        bx, by, wt, ht = o['block']
        for x in range(bx, bx + wt):
            for y in range(by, by + ht):
                belegt[(x, y)] = i

    def vor_sockel(o, anzahl, mit_blume=True):
        bx, by, wt, ht = o['block']
        ty = by + ht - 1
        sockel = {(x, ty) for x in range(bx, bx + wt)}
        n = 0
        seiten = [bx, bx + wt - 1] if rnd.random() < 0.5 else [bx + wt - 1, bx]
        for k, sx in enumerate(seiten * 2):
            if n >= anzahl:
                break
            liste = DECKER if (k % 2 == 0 or not mit_blume) else BLUMEN
            kandidaten = [(k7(i), 'k7schnee/%02d' % i) for i in rnd.sample(liste, len(liste))]
            if liste is BLUMEN:
                kandidaten = [('natur/00.png', 'natur/00'), ('natur/01.png', 'natur/01')] + kandidaten
            for d, b_ in kandidaten:
                lade(d)
                if setzen(d, b_, sx, ty + 1 if k < 2 else ty, frei_ok=sockel, anim='wehen'):
                    n += 1
                    break
        return n

    def nah(o, r=4):
        kx, ky = o['kachel']
        return [p for p in objs if p is not o and p['basis'] in BAEUME and abs(p['kachel'][0] - kx) <= r
                and abs(p['kachel'][1] - ky) <= 3]
    n5a = n5b = n5weg = 0
    einzel = [o for o in objs if o['basis'] in BAEUME and not wald(o) and len(nah(o)) < 2 and not o.get('v11')]
    for o in einzel:
        bx, by, wt, ht = o['block']
        ty = by + ht - 1
        zweiter = None
        if not nah(o):
            for name in ('klein/27', 'klein/49'):
                d = next((p['datei'] for p in objs if p['basis'] == name), None)
                if not d:
                    continue
                for sx in (bx + wt + 1, bx - 2, bx + wt + 1, bx - 2):
                    zweiter = setzen(d, name, sx, ty - 1, anim='baum')
                    if zweiter:
                        break
                if zweiter:
                    break
        if zweiter and vor_sockel(o, 1):
            n5a += 1
        elif vor_sockel(o, rnd.choice((2, 3))) >= 2:
            n5b += 1
        elif not nah(o):
            o['_weg'] = True; n5weg += 1
    for o in [o for o in objs if o['basis'] in FELSEN and o['basis'] != 'wasserfall/02']:
        vor_sockel(o, 2)
    for o in grosse_oben:                              # Regel 5: grosse Tannen oben mit Pflanzen vor dem Sockel
        vor_sockel(o, 2)
    objs = [o for o in objs if not o.get('_weg')]
    print('Regel 5: %d Einzelbaeume -> %d mit Baum + Pflanze, %d mit 2-3 Pflanzen, %d ohne Platz entfernt'
          % (len(einzel), n5a, n5b, n5weg))
    # --- Abschlusskontrolle: ungewollte Pixel-Ueberlappungen
    W, Hh = cols * T, rows * T
    besitzer = -np.ones((Hh, W), np.int32)
    weg = set()
    for i, o in enumerate(sorted(range(len(objs)), key=lambda i: -alpha[objs[i]['datei']].sum())):
        p = objs[o]
        a = alpha[p['datei']]
        h, w = a.shape
        x0, y0 = p['x'], p['y']
        xs0, ys0, xs1, ys1 = max(0, x0), max(0, y0), min(W, x0 + w), min(Hh, y0 + h)
        if xs1 <= xs0 or ys1 <= ys0:
            continue
        aa = a[ys0 - y0:ys1 - y0, xs0 - x0:xs1 - x0]
        ber = besitzer[ys0:ys1, xs0:xs1]
        konflikt = False
        for j in set(np.unique(ber[aa & (ber >= 0)]).tolist()):
            q = objs[j]
            if p['basis'] in BAEUME and q['basis'] in BAEUME:
                continue
            if p.get('v11') == 'begleiter' and q['basis'] in BAEUME | FELSEN:
                continue
            if q.get('v11') == 'begleiter' and p['basis'] in BAEUME | FELSEN:
                continue
            konflikt = True
        if konflikt and not p['basis'].startswith(('gross/', 'mittel/0', 'mittel/1')):
            weg.add(o)
            continue
        ber[aa] = o
    objs = [o for i, o in enumerate(objs) if i not in weg]
    json.dump(objs, open(pf, 'w'), indent=0)
    print('Kontrolle: %d Objekte wegen Ueberlappung entfernt, %d Objekte gesamt' % (len(weg), len(objs)))


if __name__ == '__main__':
    {'wege': wege, 'objekte': objekte}[sys.argv[1]]()
