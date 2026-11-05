"""Objekte fuer Karte 07 (The Holy Peaks) - am 16x16-Raster, ohne Ueberlappungen.

  python3 tools/karte07_objekte.py && python3 tools/karte07_bauen.py

Jedes Objekt im kleinsten Kachelblock (Fuss unten buendig, waagerecht zentriert). Bodenfuss nach Untergrund.
Freie Deko/Baeume nur, wenn sie mit 2 px Abstand nichts beruehren. Wiederverwendet: Deko aus Karte 01,
verschneite Tannen aus Karte 05.
"""
import json, math, os, random, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageFilter
import bauwerke

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte07')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte07')
T = 16
FREMD = {'k05/tanne%d' % i: 'karte05/baeume/0%d.png' % i for i in range(3)}
for i in (5, 6, 8, 10, 26, 27, 31):
    FREMD['k01/deko%02d' % i] = 'karte01/deko/%02d.png' % i
DEKO_GRAS = ['k01/deko05', 'k01/deko06', 'k01/deko26', 'k01/deko27']
WIND = {'k01/deko05', 'k01/deko06', 'k01/deko26', 'k01/deko27'}
SL, PL, BAMBUS = 'mittel/00', 'mittel/01', 'mittel/05'
KIEFER, TANNE, GROSSKIEFER = 'neu/00', 'neu/01', 'turm/03'      # neue Baeume (statt Bonsai / alter Schneekiefer)
BUSCH, AZALEE = 'neu/02', 'neu/03'
OBELISK, KRISTALL = 'mittel/02', 'mittel/03'
NADEL, NADEL_BODEN = 'gross/03', 'gross/03_ohne'                # Felsnadel mit / ohne Wolkensockel
BAEUME = {KIEFER, TANNE, GROSSKIEFER}
FRUECHTE = ['kuerbis', 'kohl', 'tomate', 'mais', 'karotte', 'erdbeere', 'aubergine', 'melone', 'zwiebel',
            'heidelbeere', 'weizen', 'kartoffel', 'ruebe', 'rote_bete', 'paprika', 'blumenkohl']
OBSTBAEUME = ['frucht/apfelbaum', 'frucht/apfelbaum', 'frucht/kirschbusch', 'frucht/trauben']
TURM_G, TURM_K, TURM_F, TURM_S = 'turm/schwarz_gross', 'turm/schwarz_klein', 'turm/schwarz_gefallen', 'turm/schwarz_stumpf'
LILA = 'mittel/13'
FELDER = [(26, 43), (49, 67)]                                   # Beetfelder (Spalten), Zeilen 64..81
OBSTGARTEN = (72, 83, 64, 80)
RING = (30, 62, 4, 26)                                          # Steinkreis oben: keine Felsen

FEST = [
    # Gipfel: Wirbelportal, Drachenschrein, Obelisk, Laternen (max. 4 Steinlaternen im Schrein)
    ('mittel/12', 6.5, 7, {'anim': 'portal'}),
    ('gross/00', 89.5, 11, {}), (KRISTALL, 93, 21, {'anim': 'glitzern'}), (BUSCH, 92, 22, {}),
    ('mittel/09', 84, 21, {}),
    (SL, 80, 9, {}), (SL, 83, 9, {}), (SL, 80, 18, {}), (SL, 87, 18, {}),
    (PL, 76, 11, {'anim': 'leuchten', 'spiegeln': True}), (PL, 66, 22, {'anim': 'leuchten'}),
    (PL, 27, 23, {'anim': 'leuchten', 'spiegeln': True}),
    (KIEFER, 64, 6, {'anim': 'baum'}),
    ('mittel/13', 59, 39, {}), ('mittel/13', 61, 49, {}),
    # Pagodenhof
    ('pagode/00', 80, 45, {}), (BAMBUS, 73, 39, {'anim': 'wehen'}), (BAMBUS, 87, 39, {'anim': 'wehen'}),
    (SL, 73, 45, {}), (SL, 87, 45, {}), (PL, 72, 32, {'anim': 'leuchten'}),
    (PL, 88, 32, {'anim': 'leuchten', 'spiegeln': True}),
    (KRISTALL, 87, 53, {'anim': 'glitzern'}), (AZALEE, 86, 54, {}),
    (PL, 82, 55, {'anim': 'leuchten', 'spiegeln': True}), (PL, 16, 54, {'anim': 'leuchten'}),
    # untere Terrasse
    ('gross/02', 8.5, 66, {}), ('gross/02', 13.5, 79, {}), ('gross/01', 9.5, 85, {}),
    ('mittel/11', 6, 80, {}), ('mittel/15', 18, 80, {}), (SL, 5, 85, {}), (PL, 4, 78, {'anim': 'leuchten'}),
    (KRISTALL, 90.5, 70, {'anim': 'glitzern'}), (BUSCH, 91.5, 71, {}),
    ('gross/01', 90.5, 80, {}), ('mittel/10', 90.5, 73, {}),
    (SL, 86, 67, {}), (SL, 95, 67, {}), (BAMBUS, 86, 77, {'anim': 'wehen'}), (BAMBUS, 95, 77, {'anim': 'wehen'}),
    (PL, 95, 63, {'anim': 'leuchten', 'spiegeln': True}),
    (BAMBUS, 45, 66, {'anim': 'wehen'}), (BAMBUS, 22, 70, {'anim': 'wehen'}), (BAMBUS, 6, 72, {'anim': 'wehen'}),
    (BAMBUS, 9, 72, {'anim': 'wehen'}), (BAMBUS, 12, 72, {'anim': 'wehen'}), (BAMBUS, 70, 73, {'anim': 'wehen'}),
    (PL, 46.5, 76, {'anim': 'leuchten', 'spiegeln': True}), (PL, 69.5, 81, {'anim': 'leuchten'}),
    # umgekippte schwarze Tuerme
    (TURM_G, 48, 40, {}), (TURM_K, 33, 57, {}), (TURM_F, 13, 58, {}), (TURM_S, 5, 58, {}),
    (TURM_F, 57, 57, {'spiegeln': True}), (TURM_G, 92, 46, {}),
    # Kristallsaeulen verteilt, jeweils mit Baum/Strauch halb davor
    (LILA, 12, 30, {}), (TANNE, 13.5, 31, {'anim': 'baum'}),
    (KRISTALL, 45, 31, {'anim': 'glitzern'}), (AZALEE, 46.5, 32, {}),
    (KRISTALL, 64, 48, {'anim': 'glitzern'}), (KIEFER, 65.5, 49, {'anim': 'baum', 'spiegeln': True}),
    (LILA, 24, 67, {}), (BUSCH, 24.5, 68, {}),
    (KRISTALL, 80, 27, {'anim': 'glitzern'}), (TANNE, 81.5, 28, {'anim': 'baum'}),
    (LILA, 93, 40, {}), (AZALEE, 94, 41, {}),
    (LILA, 5, 49, {}), (TANNE, 6.5, 50, {'anim': 'baum', 'spiegeln': True}),
    # Felsnadeln ohne Wolken auf der Insel
    (NADEL_BODEN, 17, 35, {}), (NADEL_BODEN, 13, 45, {}), (NADEL_BODEN, 41, 58, {}),
    # grosse Kiefern
    (GROSSKIEFER, 93, 58, {'anim': 'baum'}), (GROSSKIEFER, 66.5, 58, {'anim': 'baum', 'spiegeln': True}),
    # Felsnadeln in den Wolkenbergen
    (NADEL, 1.5, 30, {}), (NADEL, 1.5, 46, {}), (NADEL, 98.5, 22, {}), (NADEL, 98.5, 56, {}),
    (NADEL, 70.5, 26, {}), (NADEL, 30.5, 89, {}), (NADEL, 46.5, 89, {}), (NADEL, 60.5, 89, {}),
    (NADEL, 92.5, 89, {}), (NADEL, 98.5, 85, {}),
    (NADEL, -3, 12, {}), (NADEL, -3, 66, {}), (NADEL, 103, 8, {}), (NADEL, 103, 70, {}), (NADEL, 14, 92, {}),
    (NADEL, 78, 92, {}),
]
BAUM_PLAETZE = [(52, 35), (58, 35), (40, 40), (47, 50), (53, 51), (66, 39), (92, 34), (14, 68),
                (89, 59), (42, 55), (35, 34)]


def main():
    rnd = random.Random(7)
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cls = lay['klassen']
    hoehe = [[int(c) for c in r] for r in lay['hoehe']]
    cols, rows = lay['groesse']
    R = lay.get('rand', 0)
    for name, quelle in FREMD.items():
        ziel = os.path.join(OBJ, name + '.png')
        if not os.path.exists(ziel):
            os.makedirs(os.path.dirname(ziel), exist_ok=True)
            shutil.copy(os.path.join(ROOT, 'assets', 'objekte', quelle), ziel)
    W_, H_ = cols * T, rows * T
    pix = np.zeros((H_, W_), bool)
    gesperrt = set()
    for (x0, x1, y0, y1) in lay['treppen']:
        for y in range(y0 - 1, y1 + 2):
            for x in range(x0 - 1, x1 + 2):
                gesperrt.add((x, y))
    bx0, by0, bx1, by1 = lay['bruecke']
    for y in range(by0 - 1, by1 + 2):
        for x in range(bx0 - 1, bx1 + 2):
            gesperrt.add((x, y))
    for tp in lay['teleporter']:
        for y in range(tp['y'] - 1, tp['y'] + tp['h'] + 1):
            for x in range(tp['x'] - 1, tp['x'] + tp['b'] + 1):
                gesperrt.add((x, y))
    # Kanten: 3 Zeilen unter jeder Hochkante (Felsfront) und die Kante selbst freihalten
    for y in range(rows - 1):
        for x in range(cols):
            if hoehe[y][x] > hoehe[y + 1][x]:
                for k in range(0, 4):
                    gesperrt.add((x, y + k))
            for dx in (-1, 1):
                if 0 <= x + dx < cols and hoehe[y][x] != hoehe[y][x + dx]:
                    gesperrt.add((x, y))
    cache, alpha, objekte = {}, {}, []

    def boden(tx, ty):
        k = cls[min(rows - 1, max(0, ty))][min(cols - 1, max(0, tx))]
        return 'sand' if k in 'nw' else 'beton' if k in 'prf' else 'gras'

    def setze(name, fx, fy, opt, frei=False, nur=None, abs_=False):
        opt = dict(opt)
        spiegeln = opt.pop('spiegeln', False)
        hoch = opt.pop('hoch', 0)
        if not abs_:
            fx, fy = fx + R, fy + R
        tx, ty = int(math.floor(fx)), int(fy)
        if frei and (tx, ty) in gesperrt:
            return False
        if nur:                                                # ganzer Block muss auf dieser Klasse liegen
            sp0 = Image.open(os.path.join(OBJ, name + '.png'))
            wt0 = math.ceil(sp0.width / T) + 2
            bx0 = int(round(fx + 0.5 - wt0 / 2.0))
            for xx in range(bx0, bx0 + wt0):
                for yy in range(ty - 2, ty + 2):
                    if not (0 <= xx < cols and 0 <= yy < rows) or cls[yy][xx] not in nur:
                        return False
        b = boden(tx, ty) if hoehe[min(rows - 1, ty)][min(cols - 1, tx)] > 0 else None
        key = (name, b, spiegeln)
        if key not in cache:
            sp = Image.open(os.path.join(OBJ, name + '.png')).convert('RGBA')
            if spiegeln:
                sp = sp.transpose(Image.FLIP_LEFT_RIGHT)
            aa = np.array(sp.getchannel('A')) > 0
            ys, xs = np.nonzero(aa)
            ux0, uy0, ux1, uy1 = int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())
            if b is None or (name.startswith('frucht/') and name not in OBSTBAEUME):   # Wolken / Beete: kein Fuss
                v, off = sp, 0
            else:
                art = 'baum' if name in BAEUME or name in OBSTBAEUME or 'tanne' in name else 'klein' if name.startswith(('k01/', 'neu/0')) else 'stein'
                v, off = bauwerke.bodenfuss(sp, b, art), 2
            datei = 'varianten/%s_%s%s.png' % (name.replace('/', '-'), b or 'wolke', '_m' if spiegeln else '')
            os.makedirs(os.path.join(OBJ, 'varianten'), exist_ok=True)
            v.save(os.path.join(OBJ, datei))
            cache[key] = (datei, v.height, ux0 + off, uy0, ux1 + off, uy1)
            alpha[key] = np.array(v.getchannel('A')) >= 160
        datei, h, ux0, uy0, ux1, uy1 = cache[key]
        bw, bh = ux1 - ux0 + 1, uy1 - uy0 + 1
        wt, ht = math.ceil(bw / T), math.ceil(bh / T)
        bx = int(round(fx + 0.5 - wt / 2.0))
        ox, oy = bx * T + (wt * T - bw) // 2 - ux0, (ty + 1) * T - 1 - uy1 - hoch
        ys_, xs_ = np.nonzero(alpha[key])
        ys_, xs_ = ys_ + oy, xs_ + ox
        ok = (ys_ >= 0) & (ys_ < H_) & (xs_ >= 0) & (xs_ < W_)
        ys_, xs_ = ys_[ok], xs_[ok]
        if frei and len(ys_):
            y0, y1, x0, x1 = max(0, ys_.min() - 2), ys_.max() + 3, max(0, xs_.min() - 2), xs_.max() + 3
            f = np.zeros((y1 - y0, x1 - x0), bool)
            f[ys_ - y0, xs_ - x0] = True
            f = np.array(Image.fromarray(f.astype(np.uint8) * 255).filter(ImageFilter.MaxFilter(5))) > 0
            hind = pix[y0:y1, x0:x1]
            if (f[:hind.shape[0], :hind.shape[1]] & hind).any():
                return False
        pix[ys_, xs_] = True
        o = {'datei': datei, 'basis': name, 'x': ox, 'y': oy, 'fuss': h, 'kachel': [tx, ty],
             'block': [bx, ty - ht + 1, wt, ht], 'ebene': 0 if name.startswith('k01/') else 1}
        o.update(opt)
        objekte.append(o)
        for x in range(bx, bx + wt):
            for y in range(ty - ht + 1, ty + 1):
                gesperrt.add((x, y))
        return True

    for (name, fx, fy, opt) in FEST:
        setze(name, fx, fy, opt)
    for (x, y) in BAUM_PLAETZE:
        setze(KIEFER, x, y, {'anim': 'baum', 'spiegeln': rnd.random() < 0.5}, frei=True)
    # Beete: Hochbeete mit Holzrahmen in unregelmaessigen Reihen, je Beet eine Fruchtsorte (digital)
    beete = []
    for (fx0, fx1) in FELDER:
        y = 64 + rnd.randint(0, 1)
        while y + 1 <= 81:
            x = fx0 + rnd.randint(1, 2)
            while x <= fx1 - 3:
                ende = min(x + rnd.randint(4, 9), fx1 + 1 - rnd.randint(0, 1))
                if ende - x >= 3:
                    beete.append([(x + R) * T + 2, (ende + R) * T - 2, (y + R) * T + 2, (y + 2 + R) * T - 2])
                    frucht = 'frucht/' + rnd.choice(FRUECHTE)
                    anim = {'anim': 'wehen'} if frucht.endswith(('mais', 'weizen', 'zwiebel', 'karotte')) else {}
                    px = x
                    while px + 2 <= ende:
                        setze(frucht, px + 0.5, y + 1, dict(anim, hoch=5, spiegeln=rnd.random() < 0.5))
                        px += 2
                x = ende + rnd.randint(1, 2)
            y += 3 + rnd.choice((0, 0, 1))
    json.dump(beete, open(os.path.join(KARTE, 'beete.json'), 'w'))
    # Obstgarten: lockere Baumreihen
    ox0, ox1, oy0, oy1 = OBSTGARTEN
    y = oy0 + 3
    while y <= oy1:
        x = ox0 + 1.5 + rnd.random() * 1.5
        while x <= ox1 - 1:
            setze(rnd.choice(OBSTBAEUME), x, y, {'anim': 'baum', 'spiegeln': rnd.random() < 0.5}, frei=True)
            x += 4 + rnd.random() * 1.5
        y += 5 + rnd.randint(0, 1)
    # verschneite Tannen und Schneefelsen nur auf Schnee (nie auf Wegen), keine Felsen im Steinkreis
    n_s = n_r = 0
    for _ in range(5000):
        tx, ty = rnd.randrange(3, cols - 3), rnd.randrange(3, rows - 3)
        if cls[ty][tx] != 'n' or n_s >= 42 or rnd.random() > 0.5:
            continue
        if RING[0] <= tx - R <= RING[1] and RING[2] <= ty - R <= RING[3]:   # Steinkreis bleibt frei
            continue
        if n_r < 6 and rnd.random() < 0.15:
            if setze('mittel/07', tx, ty, {'spiegeln': rnd.random() < 0.5}, frei=True, nur='n', abs_=True):
                n_r += 1
        elif setze(TANNE, tx, ty, {'anim': 'baum', 'spiegeln': rnd.random() < 0.5}, frei=True, abs_=True):
            n_s += 1
    n = 0
    for _ in range(3000):
        if n >= 70:
            break
        tx, ty = rnd.randrange(3, cols - 3), rnd.randrange(3, rows - 3)
        if cls[ty][tx] != 'g':
            continue
        d = rnd.choice(DEKO_GRAS)
        if setze(d, tx, ty, {'anim': 'wehen'} if d in WIND else {}, frei=True, abs_=True):
            n += 1
    json.dump(objekte, open(os.path.join(OBJ, 'platzierung.json'), 'w'), indent=0)
    print(len(objekte), 'Objekte am Raster')


if __name__ == '__main__':
    main()
