"""Objekte fuer Karte 04 (Gear Savanna): feste Positionen aus der Vorlage + verstreute Deko je Boden.

  python3 tools/karte04_objekte.py && python3 tools/karte04_bauen.py

Sprites: assets/objekte/karte04/<gruppe>/NN.png (PixelLab, Gruppen k4_*). Positionen der festen Objekte
sind Pixelkoordinaten der Vorlage (Fussmitte), die 1:1 auf die Karte passen (beide 16-px-Raster).
Bodenfuss wie in Karte 03 (bauwerke.bodenfuss), die Halme werden auf Savannen-/Plateaugras umgefaerbt.
"""
import json, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
import bauwerke
from basis_kacheln import RGB

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte04')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte04')
T = 16
H = lambda h: tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))
GRASRAMPE = {'c': ['#5e4630', '#7a5c40', '#977c58', '#b09470', '#c4ac88', '#d6c4a2'],
             's': ['#7a6430', '#957c3e', '#ad944e', '#c4aa60', '#d6bc70', '#e8d08a'],
             'g': ['#66783e', '#82924e', '#9aa95e', '#afbd70', '#c2ce82', '#d6df9a'],
             'a': ['#55554c', '#69695e', '#7c7c70', '#8e8e80', '#a4a496', '#b8b8aa']}

AKAZIE = ['baeume/00', 'rand/01', 'baeume/03', 'rand/02']
# Waldrand wie in Karte 01: viele verschiedene Savannenbaeume (Baobab, Akazien, Marula, Drachenbaum, Buesche)
RAND = ['rand/00', 'rand/01', 'rand/02', 'rand/03', 'rand/03', 'rand/04', 'rand/04', 'rand/05', 'rand/06', 'rand/07',
        'baeume/00', 'baeume/03', 'rand/03', 'rand/05']
# (sprite, x_px, y_px [Fussmitte in der Vorlage], Optionen)
FEST = [
    # Plateaus mit Zahnraedern
    ('gross/00', 543, 104, {}), ('gross/01', 417, 252, {'spiegeln': True}), ('gross/01', 1232, 96, {}),
    ('gross/00', 1520, 218, {'spiegeln': True}), ('gross/01', 1567, 364, {}),
    ('mittel/06', 1312, 380, {}), ('mittel/07', 1288, 190, {'anim': 'glitzern'}), ('klein/05', 1192, 317, {'anim': 'glitzern'}),
    ('klein/05', 1177, 380, {'anim': 'glitzern'}), ('mittel/07', 1575, 286, {'anim': 'glitzern'}),
    ('mittel/00', 1168, 204, {}), ('mittel/00', 440, 60, {}), ('mittel/15', 639, 46, {}), ('mittel/00', 319, 78, {}),
    ('mittel/00', 700, 302, {}),
    # Termitenhuegel
    ('baeume/01', 168, 72, {}), ('mittel/11', 360, 128, {}), ('mittel/11', 280, 254, {}), ('baeume/01', 265, 368, {}),
    ('mittel/11', 372, 440, {}), ('mittel/11', 267, 494, {}), ('baeume/01', 368, 752, {}), ('mittel/11', 392, 766, {}),
    ('baeume/01', 464, 1008, {}), ('mittel/11', 488, 1020, {}), ('mittel/11', 568, 1248, {}), ('baeume/01', 1640, 64, {}),
    ('mittel/11', 1468, 120, {}), ('baeume/01', 720, 560, {}),
    # Akazien
    ('A', 193, 330, {}), ('A', 225, 393, {}), ('A', 145, 408, {}), ('A', 128, 459, {}), ('A', 497, 380, {}),
    ('A', 462, 478, {}), ('A', 303, 557, {}), ('A', 337, 237, {}), ('A', 400, 620, {}), ('A', 432, 776, {}),
    ('A', 528, 812, {}), ('A', 640, 828, {}), ('A', 448, 856, {}), ('A', 48, 844, {}), ('A', 128, 924, {}),
    ('A', 224, 924, {}), ('A', 224, 1020, {}), ('A', 496, 1116, {}), ('A', 592, 1116, {}), ('A', 672, 1100, {}),
    ('A', 512, 1180, {}), ('A', 432, 1212, {}), ('A', 304, 1228, {}), ('A', 224, 1244, {}), ('A', 696, 744, {}),
    ('A', 780, 66, {}), ('A', 1090, 706, {}), ('A', 1150, 726, {}), ('A', 1075, 1040, {}), ('A', 1060, 1150, {}),
    ('A', 1150, 1150, {}), ('A', 1610, 756, {}), ('A', 1568, 843, {}), ('A', 1073, 1053, {}), ('A', 1080, 1273, {}),
    ('A', 1153, 1273, {}),
    # Canyon: Riesenschaedel, Brustkorb, Felsen, Knochen
    ('gross/02', 800, 522, {}), ('gross/03', 1000, 842, {}), ('mittel/15', 1022, 556, {}), ('mittel/08', 890, 772, {}),
    ('mittel/09', 830, 300, {}), ('klein/04', 905, 600, {}), ('klein/34', 860, 180, {}), ('klein/04', 950, 960, {}),
    # Lager
    ('zelte/00', 112, 612, {}), ('zelte2/00', 236, 596, {}), ('zelte2/00', 252, 790, {'spiegeln': True}),
    ('mittel/04', 166, 734, {'anim': 'feuer'}), ('mittel/12', 300, 744, {}), ('mittel/05', 318, 708, {}),
    ('mittel/13', 186, 684, {}), ('mittel/03', 280, 682, {}), ('baeume/07', 112, 700, {}), ('klein/25', 196, 770, {}),
    ('klein/31', 120, 660, {'anim': 'leuchten'}), ('klein/28', 26, 720, {}),
    # Teerfeld: Monument, tote Baeume, Kristalle, dunkle Felsen
    ('monument/00', 1380, 958, {'anim': 'juwel'}),
    ('baeume/02', 1196, 900, {}), ('baeume/02', 1377, 1262, {'spiegeln': True}), ('baeume/02', 1567, 1164, {}),
    ('baeume/02', 1280, 1150, {'spiegeln': True}), ('baeume/02', 1519, 1294, {}),
    ('mittel/07', 1512, 912, {'anim': 'glitzern'}), ('klein/05', 1288, 1102, {'anim': 'glitzern'}),
    ('klein/05', 1440, 1186, {'anim': 'glitzern'}), ('mittel/07', 1353, 1196, {'anim': 'glitzern'}),
    ('klein/05', 1350, 1178, {'anim': 'glitzern'}), ('klein/05', 1527, 1148, {'anim': 'glitzern'}),
    ('klein/05', 1480, 1178, {'anim': 'glitzern'}), ('klein/10', 1310, 1034, {}), ('klein/10', 1577, 970, {}),
    ('klein/10', 1495, 1194, {}),
    # Schrott am Wegesrand (Zahnrad-Thema)
    ('baeume/09', 600, 900, {}), ('baeume/06', 1180, 560, {}), ('mittel/14', 1660, 600, {}), ('baeume/05', 1650, 920, {}),
    ('mittel/00', 272, 862, {}), ('mittel/00', 648, 1222, {}),
]
STREU = {
    's': {'klein/00': 8, 'klein/27': 4, 'klein/02': 3, 'klein/08': 2, 'klein/07': 2, 'klein/03': 1,
          'klein/59': 1, 'klein/09': 1, 'klein/14': 2, 'klein/50': 1, 'klein/06': 0.4, 'klein/18': 0.3, 'klein/55': 0.3},
    'g': {'klein/01': 6, 'klein/07': 3, 'klein/02': 2, 'klein/08': 2, 'klein/05': 0.6, 'klein/06': 1, 'klein/18': 0.6,
          'klein/55': 0.6, 'klein/12': 0.4, 'klein/17': 0.4},
    'c': {'klein/02': 4, 'klein/08': 2, 'klein/03': 2, 'klein/59': 1, 'klein/04': 0.6, 'klein/34': 0.6},
    'a': {'klein/10': 1, 'klein/09': 2, 'klein/14': 2, 'klein/05': 1, 'klein/43': 1, 'klein/02': 2},
}
STREU_ANZAHL = {'s': 140, 'g': 40, 'c': 30, 'a': 16}
ANIM_STREU = {'klein/00': 'wehen', 'klein/27': 'wehen', 'klein/01': 'wehen', 'klein/14': 'wehen', 'klein/07': 'wehen',
              'klein/05': 'glitzern'}
PFLANZEN = set(AKAZIE) | {'baeume/02', 'klein/00', 'klein/01', 'klein/07', 'klein/14', 'klein/27', 'mittel/10'}


def fuss_variante(name, boden, spiegeln):
    """Sprite mit Bodenfuss; Grashalme des Fusses auf die Bodenfarbe umfaerben."""
    vname = 'varianten/%s_%s%s' % (name.replace('/', '-'), boden, '_m' if spiegeln else '')
    pfad = os.path.join(OBJ, vname + '.png')
    if not os.path.exists(pfad):
        sp = Image.open(os.path.join(OBJ, name + '.png')).convert('RGBA')
        if spiegeln:
            sp = sp.transpose(Image.FLIP_LEFT_RIGHT)
        sp = saeubern(sp)
        art = 'baum' if name in PFLANZEN or name.startswith('baeume/') or name.startswith('rand/') else 'klein' if name.startswith('klein/') else 'stein'
        if not name.startswith('klein/') and not name.startswith('rand/') and name not in AKAZIE:
            sp = einbetten(sp, boden)
        v = bauwerke.bodenfuss(sp, 'gras', art)
        a = np.array(v)
        ramp = [H(c) for c in GRASRAMPE[boden]]
        unten = a.shape[0] - 8
        for i, k in enumerate(('g0', 'g1', 'g2', 'g3', 'g4', 'g5')):
            m = (a[unten:, :, :3] == RGB[k]).all(axis=2) & (a[unten:, :, 3] > 0)
            a[unten:][m, :3] = ramp[i]
        for i, k in enumerate(('g0', 'g1', 'g2', 'g3', 'g4', 'g5')):
            pass
        sch = (a[..., :3] == (24, 70, 50)).all(axis=2)
        a[sch, :3] = (60, 44, 24)                          # Kontaktschatten warm statt gruen
        os.makedirs(os.path.dirname(pfad), exist_ok=True)
        Image.fromarray(a).save(pfad)
    return vname


def einbetten(sp, boden):
    """Eigenes Gras/Erdreich am Fuss des Sprites (untere 35 %) an den Untergrund anpassen: Grashalme nach
    Helligkeit auf die Bodenrampe (Plateau gruen, Savanne gelb, Asche grau); im Canyon wird Gras zu Erde."""
    import colorsys
    a = np.array(sp.convert('RGBA'))
    h = a.shape[0]
    y0 = int(h * 0.65)
    ramp = [np.array(H(c)) for c in GRASRAMPE[boden if boden != 'c' else 's']]
    erde = [np.array(H(c)) for c in ('#5e4630', '#7a5c40', '#977c58', '#b09470', '#c4ac88', '#d6c4a2')]
    for y in range(y0, h):
        for x in range(a.shape[1]):
            if a[y, x, 3] == 0:
                continue
            r, g, b = a[y, x, :3] / 255.0
            hh, ss, vv = colorsys.rgb_to_hsv(r, g, b)
            if ss > 0.28 and 0.10 <= hh <= 0.42 and vv > 0.3:     # Gras (gelb bis gruen)
                i = min(4, max(0, int((vv - 0.3) / 0.7 * 5)))
                a[y, x, :3] = (erde if boden == 'c' else ramp)[i]
    return Image.fromarray(a)


def saeubern(sp):
    """Kleine abgetrennte Splitter (PixelLab-Reste) entfernen: nur Teile >= 4 % der groessten Flaeche."""
    from collections import deque
    a = np.array(sp)
    m = a[..., 3] > 0
    h, w = m.shape
    lab = np.zeros((h, w), int); n = 0; groessen = {}
    for y in range(h):
        for x in range(w):
            if m[y, x] and not lab[y, x]:
                n += 1; q = deque([(y, x)]); lab[y, x] = n; c = 0
                while q:
                    yy, xx = q.popleft(); c += 1
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            y2, x2 = yy + dy, xx + dx
                            if 0 <= y2 < h and 0 <= x2 < w and m[y2, x2] and not lab[y2, x2]:
                                lab[y2, x2] = n; q.append((y2, x2))
                groessen[n] = c
    if len(groessen) <= 1:
        return sp
    gross = max(groessen.values())
    for k, c in groessen.items():
        if c < gross * 0.04:
            a[lab == k, 3] = 0
    return Image.fromarray(a)


def main():
    rnd = random.Random(4)
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cls = lay['klassen']
    cols, rows = lay['groesse']
    MW, MH = cols * T, rows * T
    gesperrt = np.zeros((MH, MW), bool)
    for y in range(rows):
        for x in range(cols):
            if cls[y][x] in 'xwfht':
                gesperrt[y * T:(y + 1) * T, x * T:(x + 1) * T] = True
    # Waende/Fronten nicht bestreuen: Bereich unter jeder Hochkante sperren
    hoehe = [[int(c) for c in r] for r in lay['hoehe']]
    for y in range(rows - 1):
        for x in range(cols):
            if hoehe[y][x] > hoehe[y + 1][x]:
                gesperrt[(y + 1) * T:(y + 4) * T, x * T:(x + 1) * T] = True
            for dx in (-1, 1):
                if 0 <= x + dx < cols and hoehe[y][x] > hoehe[y][x + dx]:
                    gesperrt[y * T:(y + 1) * T, (x + dx) * T:(x + dx + 1) * T] = True
                    gesperrt[y * T:(y + 1) * T, x * T:(x + 1) * T] = True
    for (x0, x1, y0, y1, *_r) in lay.get('treppen', []):
        gesperrt[(y0 - 1) * T:(y1 + 4) * T, (x0 - 2) * T:(x1 + 3) * T] = True
    # unter der hohen Bruecke nichts (Objekte auf dem Canyonboden wuerden sonst ueber ihr liegen)
    br = lay.get('bruecke')
    unter_bruecke = np.zeros((MH, MW), bool)
    if br:
        unter_bruecke[(br[0] - 2) * T:(br[1] + 4) * T, :] = True
        for y in range(rows):
            for x in range(cols):
                if hoehe[y][x] != 0:
                    unter_bruecke[y * T:(y + 1) * T, x * T:(x + 1) * T] = False
        gesperrt |= unter_bruecke
    belegt = np.zeros((MH, MW), bool)
    objekte = []

    def boden_bei(px, py):
        k = cls[min(rows - 1, max(0, int(py - 2) // T))][min(cols - 1, max(0, int(px) // T))]
        return 'g' if k == 'g' else 'a' if k in 'at' else 'c' if k in 'cf' else 's'

    def setze(name, ax, ay, fest, opt):
        opt = dict(opt)
        spiegeln = opt.pop('spiegeln', False)
        vname = fuss_variante(name, boden_bei(ax, ay), spiegeln)
        im = Image.open(os.path.join(OBJ, vname + '.png'))
        x, y = int(ax - im.width // 2), int(ay + 3 - im.height)
        a = np.array(im.getchannel('A')) >= 200
        xs0, ys0, xs1, ys1 = max(0, x), max(0, y), min(MW, x + im.width), min(MH, y + im.height)
        a = a[ys0 - y:ys1 - y, xs0 - x:xs1 - x]
        if not fest:
            fuss = np.zeros_like(a); fuss[-6:] = a[-6:]
            if ((belegt[ys0:ys1, xs0:xs1] & a).any() or (gesperrt[ys0:ys1, xs0:xs1] & fuss).any()):
                return None
        belegt[ys0:ys1, xs0:xs1] |= a
        o = {'datei': vname + '.png', 'basis': name, 'x': x, 'y': y, 'fuss': im.height}
        o.update(opt)
        objekte.append(o)
        return o

    wandpfad = os.path.join(KARTE, 'waende.npy')
    wand = np.unpackbits(np.load(wandpfad))[:MH * MW].reshape(MH, MW).astype(bool) if os.path.exists(wandpfad) else np.zeros((MH, MW), bool)

    def frei_von_wand(name, px, py):
        """Steht der Fuss eines festen Objekts auf einer Wand/Front, wird es zur naechsten freien Stelle
        (bis 48 px) verschoben - nach unten bevorzugt (vor die Wand)."""
        sp = Image.open(os.path.join(OBJ, name + '.png'))
        b = max(6, sp.width // 3)
        def trifft(x, y):
            y0 = max(0, y - 3); x0 = max(0, x - b)
            return wand[y0:y + 2, x0:x + b].any()
        if not trifft(px, py):
            return px, py
        for r in range(4, 49, 4):
            for dx, dy in ((0, r), (0, -r), (r, 0), (-r, 0), (r, r), (-r, r)):
                if 0 <= px + dx < MW and 0 <= py + dy < MH and not trifft(px + dx, py + dy):
                    print('  verschoben (Wand):', name, (px, py), '->', (px + dx, py + dy))
                    return px + dx, py + dy
        return px, py

    # Waldrand: dichte Reihen verschiedener Savannenbaeume auf den Heckenflaechen
    hz = np.array([[c == 'h' for c in r] for r in cls])
    tp = [(t['x'], t['y'], t['b'], t['h']) for t in lay.get('teleporter', [])]
    rw = random.Random(17)
    wald = []
    for gy in range(0, MH + 20, 15):
        for gx in range(-6, MW + 10, 21):
            x = gx + rw.randint(-6, 6) + (10 if (gy // 15) % 2 else 0)
            y = gy + rw.randint(-4, 4)
            cx_, cy_ = min(cols - 1, max(0, x // T)), min(rows - 1, max(0, (y - 4) // T))
            if not hz[cy_, cx_]:
                continue
            if any(tx - 1 <= cx_ <= tx + tb and ty - 1 <= cy_ <= ty + th for (tx, ty, tb, th) in tp):
                continue
            wald.append((rw.choice(RAND), x, y))
    tp_px = [((tx - 1) * T, (ty - 1) * T, (tx + tb + 1) * T, (ty + th + 1) * T) for (tx, ty, tb, th) in tp]
    for (name, x, y) in wald:
        sp = Image.open(os.path.join(OBJ, name + '.png'))
        bx0, by0, bx1, by1 = x - sp.width // 2, y - sp.height, x + sp.width // 2, y
        if any(bx0 < r[2] and bx1 > r[0] and by0 < r[3] and by1 > r[1] for r in tp_px):
            continue
        setze(name, x, y, True, {'spiegeln': rw.random() < 0.5})
    for i, (name, px, py, opt) in enumerate(FEST):
        if name == 'A':
            name = AKAZIE[i % len(AKAZIE)]
            opt = dict(opt, anim='baum', spiegeln=(i * 7) % 3 == 0)
        elif name in ('baeume/02',):
            opt = dict(opt, anim='baum')
        px, py = frei_von_wand(name, px, py)
        if unter_bruecke[min(MH - 1, py), min(MW - 1, px)]:
            print('  unter der Bruecke, weggelassen:', name, (px, py))
            continue
        setze(name, px, py, True, opt)
    for art, anzahl in STREU_ANZAHL.items():
        namen, gew = list(STREU[art]), list(STREU[art].values())
        gesetzt = 0
        for _ in range(anzahl * 40):
            if gesetzt >= anzahl:
                break
            cx, cy = rnd.randrange(1, cols - 1), rnd.randrange(2, rows - 1)
            k = cls[cy][cx]
            ziel = {'s': 'sde', 'g': 'g', 'c': 'c', 'a': 'am'}[art]
            if k not in ziel:
                continue
            n = rnd.choices(namen, weights=gew)[0]
            opt = {'anim': ANIM_STREU[n]} if n in ANIM_STREU else {}
            if rnd.random() < 0.5:
                opt['spiegeln'] = True
            if setze(n, cx * T + rnd.randint(3, 13), cy * T + rnd.randint(8, 15), False, opt):
                gesetzt += 1
    json.dump(objekte, open(os.path.join(OBJ, 'platzierung.json'), 'w'), indent=0)
    print(len(objekte), 'Objekte gesetzt')


if __name__ == '__main__':
    main()
