"""Objekte fuer Karte 34 (Shinjuku Central Park, A03 Nr. 1) -> assets/objekte/karte34/platzierung.json

  python3 tools/karte34_objekte.py && python3 tools/karte34_bauen.py

Reihenfolge (Regel "Grosse Objekte zuerst"): Gebaeude (Doppelturm-Rathaus, glaesernes Buerohaus, Steinpavillon -
PixelLab k34_*), Brunnen, Spielplatz, Wiesenbaeume nach der Vorlage mit Begleitern (Regel 5d), Zypressen, Baenke,
Laternen, Uferfelsen und Seerosen, Streudeko (Blumen, Pilze, Steine), zuletzt der Waldrand auf allen 'h'-Kacheln.
Wiederverwendet: Baeume/Deko von Karte 01, Spielgeraete und Brunnen von Karte 10, Klettergeruest/Bank von Karte 18,
Laterne von Karte 31. Jedes Objekt im kleinsten Kachelblock, unten buendig, waagerecht zentriert (Regel 1b).
"""
import json, math, os, random, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
import bauwerke

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte34')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte34')
T = 16
FREMD = {}
for i in range(16):
    FREMD['k01/baum%02d' % i] = 'karte01/baeume/%02d.png' % i
for i in range(64):
    FREMD['k01/deko%02d' % i] = 'karte01/deko/%02d.png' % i
FREMD.update({
    'spiel/schaukel': 'karte10/spielplatz/01.png', 'spiel/rutsche': 'karte10/spielplatz/00.png',
    'spiel/brunnen': 'karte10/spielplatz/08.png', 'spiel/kuppel': 'karte18/gebaeude/kletterkuppel.png',
    'moebel/bank': 'karte18/strasse/14.png', 'moebel/laterne': 'karte31/laterne/00.png',
})
WALD = ['k01/baum%02d' % i for i in (0, 1, 2, 4, 5, 9, 12, 13, 14, 15)]
LAUB = ['k01/baum00', 'k01/baum01', 'k01/baum02', 'k01/baum15']
GROSS = 'k01/baum05'                                         # knorriger Grossbaum (Vorlage: drei alte Baeume)
ZYPRESSE = ['k01/baum07', 'k01/baum08']
FELS_KLEIN = ['k01/deko08', 'k01/deko10']
FELS_GROSS = ['k01/deko09', 'k01/deko11']
BLUMEN = ['k01/deko%02d' % i for i in (0, 1, 2, 3, 4, 27, 30)]
PILZE = ['k01/deko14', 'k01/deko31']
SEEROSEN = ['k01/deko17', 'k01/deko18', 'k01/deko19']
HOCH_FELS = ['k01/deko09', 'k01/deko11']
HOCH_BLUME = ['k01/deko04', 'k01/deko27', 'k01/deko30']
OHNE_FUSS = ('rathaus/', 'buero/', 'pavillon/', 'moebel/laterne', 'k01/deko17', 'k01/deko18', 'k01/deko19')

# Gebaeude und grosse Objekte: (sprite, Kachel-x der Mitte, Fusszeile, Optionen) - Lage nach der Vorlage
GEBAEUDE = [
    ('rathaus/00', 46.5, 21, {'gebaeude': True}),             # Doppelturm-Rathaus auf dem Platz oben rechts
    ('buero/00', 10, 36, {'gebaeude': True}),                 # glaesernes Buerohaus links
    ('pavillon/00', 14.5, 17, {'gebaeude': True}),            # kleiner Steinpavillon oben links
    ('spiel/brunnen', 29, 31, {'anim': 'brunnen'}),           # Brunnen auf dem mittleren Platz
    ('spiel/schaukel', 45.5, 46, {}), ('spiel/rutsche', 50.5, 47, {}), ('spiel/kuppel', 47, 49, {}),
]
# Wiesenbaeume nach der Vorlage (Fussmitte, Fusszeile); werden bei Bedarf auf die naechste freie Graskachel geschoben
BAEUME = [
    (LAUB[0], 51, 6), (LAUB[1], 6, 11), (LAUB[2], 14, 10), (LAUB[0], 17, 10), (GROSS, 20, 11), (LAUB[1], 26, 12),
    (LAUB[2], 28, 21), (LAUB[0], 29, 25), (LAUB[1], 17, 25), (LAUB[2], 17, 32), (GROSS, 7, 28), (LAUB[0], 3, 28),
    (LAUB[1], 3, 31), (LAUB[2], 3, 46), (LAUB[0], 27, 47), (GROSS, 36, 48), (LAUB[1], 58, 48), (LAUB[2], 61, 47),
]
ZYPRESSEN = [(2, 10), (8, 13), (2, 17), (26, 27), (20, 28), (4, 35), (23, 47), (25, 46), (19, 52), (24, 49)]
BAENKE = [(18.5, 21), (23.5, 31), (22.5, 36), (23.5, 40), (12.5, 40), (6.5, 38), (33.5, 32), (33.5, 38), (37.5, 40),
          (38.5, 30), (51.5, 25)]
LATERNEN = [(42, 22), (51, 22), (19, 35), (21, 46), (32, 29), (8, 41)]   # Paar 42/51 symmetrisch zum Rathaus


def main():
    rnd = random.Random(34)
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cls = lay['klassen']
    cols, rows = lay['groesse']

    def k(tx, ty):
        return cls[min(rows - 1, max(0, ty))][min(cols - 1, max(0, tx))]

    for name, quelle in FREMD.items():
        ziel = os.path.join(OBJ, name + '.png')
        q = os.path.join(ROOT, 'assets', 'objekte', quelle)
        if os.path.exists(q) and not os.path.exists(ziel):
            os.makedirs(os.path.dirname(ziel), exist_ok=True)
            shutil.copy(q, ziel)
    belegt, objekte, gesperrt = {}, [], set()
    for ty in range(rows):                                       # Teich und Steg: keine Fuesse im Wasser
        for tx in range(cols):
            if cls[ty][tx] in 'xb':
                gesperrt.add((tx, ty))
    for tp in lay['teleporter']:                                 # Teleporter frei (inkl. Umkreis)
        for y in range(tp['y'] - 2, tp['y'] + tp['h'] + 2):
            for x in range(tp['x'] - 2, tp['x'] + tp['b'] + 2):
                gesperrt.add((x, y))
    cache = {}

    def boden(tx, ty):
        kk = k(tx, ty)
        return 'sand' if kk in 'wsem' else 'beton' if kk == 'p' else 'gras'

    def setze(name, fx, fy, opt, frei=False, wald=False):
        opt = dict(opt)
        spiegeln = opt.pop('spiegeln', False)
        flach = name.startswith('k01/deko')
        tx, ty = int(math.floor(fx)), int(fy)
        if frei:
            if (tx, ty) in gesperrt or (tx, ty, flach) in belegt:
                return False
            if not flach and not wald and any((tx + dx, ty + dy, False) in belegt for dx in (-1, 0, 1) for dy in (-1, 0, 1)):
                return False
        b = opt.pop('boden', None) or boden(tx, ty)
        key = (name, b, spiegeln)
        if key not in cache:
            sp = Image.open(os.path.join(OBJ, name + '.png')).convert('RGBA')
            if spiegeln:
                sp = sp.transpose(Image.FLIP_LEFT_RIGHT)
            aa = np.array(sp.getchannel('A')) > 0
            ys, xs = np.nonzero(aa)
            ux0, uy0, ux1, uy1 = int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())
            art = 'baum' if 'baum' in name else 'klein' if flach else 'stein'
            ohne_fuss = name.startswith(OHNE_FUSS)
            v = sp if ohne_fuss else bauwerke.bodenfuss(sp, b, art)
            off = 0 if ohne_fuss else 2
            datei = 'varianten/%s_%s%s.png' % (name.replace('/', '-'), b, '_m' if spiegeln else '')
            os.makedirs(os.path.join(OBJ, 'varianten'), exist_ok=True)
            v.save(os.path.join(OBJ, datei))
            cache[key] = (datei, v.height, ux0 + off, uy0, ux1 + off, uy1)
        datei, h, ux0, uy0, ux1, uy1 = cache[key]
        bw, bh = ux1 - ux0 + 1, uy1 - uy0 + 1
        wt, ht = math.ceil(bw / T), math.ceil(bh / T)
        bx = int(math.floor(fx + 0.5 - wt / 2.0 + 0.5))
        o = {'datei': datei, 'basis': name, 'x': bx * T + (wt * T - bw) // 2 - ux0, 'y': (ty + 1) * T - 1 - uy1,
             'fuss': h, 'kachel': [tx, ty], 'block': [bx, ty - ht + 1, wt, ht], 'ebene': 0 if flach else 1}
        px_, py_ = opt.pop('px', None), opt.pop('py', None)
        if px_ is not None:                                      # pixelgenaue Lage (Begleiter am Stumpf)
            o['x'] = px_ - (ux0 + bw // 2)
            o['y'] = py_ - uy1
        o.update(opt)
        objekte.append(o)
        belegt[(tx, ty, flach)] = True
        if not flach:
            for x in range(bx, bx + wt):                         # Sockel/Block gesperrt
                for y in range(ty - (ht - 1 if not wald else 0), ty + 1):
                    gesperrt.add((x, y))
        return True

    def naechste(fx, fy, klassen='g', r=2):
        """Naechste Fusskachel auf passendem Boden (Vorlagenlage auf das Layout einrasten)."""
        for d in range(r + 1):
            for dy in range(-d, d + 1):
                for dx in range(-d, d + 1):
                    if max(abs(dx), abs(dy)) != d:
                        continue
                    tx, ty = int(math.floor(fx)) + dx, fy + dy
                    if k(tx, ty) in klassen and k(tx, ty + 1) in klassen + 'hp' and (tx, ty) not in gesperrt:
                        return fx + dx, ty
        return None

    # ---------------------------------------------------------------- grosse Objekte
    for (name, fx, fy, opt) in GEBAEUDE:
        setze(name, fx, fy, opt)
    for o in objekte:                                            # vor und neben Gebaeuden frei (Eingang, keine Deko)
        bx, by, wt, ht = o['block']
        for x in range(bx - 1, bx + wt + 1):
            for y in range(by, by + ht + 2):
                gesperrt.add((x, y))
    # ---------------------------------------------------------------- Wiesenbaeume mit Begleitern (Regel 5d)
    gesetzt_b = []
    for i, (name, fx, fy) in enumerate(BAEUME):
        p = naechste(fx, fy)
        if p and setze(name, p[0], p[1], {'spiegeln': i % 2 == 1}, frei=True):
            gesetzt_b.append(objekte[-1])
        else:
            print('Baum nicht gesetzt:', name, fx, fy)
    for i, b in enumerate(gesetzt_b):
        bx, by, wt, ht = b['block']
        cx, fy = bx * T + wt * T // 2, (by + ht) * T - 1
        seite = -1 if i % 2 else 1
        art = i % 3
        vorne_frei = k(bx + wt // 2, by + ht) == 'g' and (bx + wt // 2, by + ht) not in gesperrt
        if art == 0 and vorne_frei:                              # Fels vor dem Stumpf (2 Kacheln hoch, eine Reihe tiefer)
            setze(rnd.choice(HOCH_FELS), cx / T, fy // T + 1, {'px': cx + seite * 5, 'py': fy + T})
        elif art == 1 or not vorne_frei:                         # Fels hinter den Blaettern
            if k(bx, by + ht - 2) == 'g':
                setze(rnd.choice(FELS_GROSS), cx / T, fy // T - 1, {'px': cx + seite * 8, 'py': fy - 7})
        else:                                                    # hohe Blume vor dem Stumpf
            setze(rnd.choice(HOCH_BLUME), cx / T, fy // T + 1, {'px': cx - seite * 5, 'py': fy + T, 'anim': 'wehen'})
    for o in gesetzt_b:                                          # Stammreihe +-1: keine freie Deko
        bx, by, wt, ht = o['block']
        for x in range(bx - 1, bx + wt + 1):
            for y in (by + ht - 2, by + ht - 1, by + ht):
                gesperrt.add((x, y))
    for i, (fx, fy) in enumerate(ZYPRESSEN):                     # schlanke Zypressen (Vorlage), ohne Begleitpflicht
        p = naechste(fx, fy)
        if p:
            setze(ZYPRESSE[i % 2], p[0], p[1], {'spiegeln': i % 3 == 0}, frei=True)
    # ---------------------------------------------------------------- Parkmoebel
    for (fx, fy) in BAENKE:                                      # Baenke am Wegrand (Rasen/Platz, nicht auf dem Weg)
        p = naechste(fx, fy, 'gp', 2)
        if p:
            setze('moebel/bank', p[0], p[1], {}, frei=True)
    for (fx, fy) in LATERNEN:
        if not setze('moebel/laterne', fx, fy, {'anim': 'lampe'}, frei=True):
            p = naechste(fx, fy, 'gp', 2)
            if not (p and setze('moebel/laterne', p[0], p[1], {'anim': 'lampe'}, frei=True)):
                print('Laterne nicht gesetzt:', fx, fy)
    # ---------------------------------------------------------------- Teich: Uferfelsen und Seerosen
    ufer = [(tx, ty) for ty in range(rows) for tx in range(cols) if cls[ty][tx] == 'm'
            and any(k(tx + dx, ty + dy) == 'x' for dx in (-1, 0, 1) for dy in (-1, 0, 1))
            and not any(k(tx + dx, ty + dy) == 'b' for dx in range(-3, 4) for dy in range(-2, 3))]
    rnd.shuffle(ufer)
    fels = []
    for (tx, ty) in ufer:
        if len(fels) >= 4:
            break
        if any(abs(tx - x) + abs(ty - y) < 7 for (x, y) in fels):
            continue
        if setze(rnd.choice(FELS_KLEIN + FELS_GROSS), tx, ty, {}, frei=True):
            fels.append((tx, ty))
    rosen = []
    wasser = [(tx, ty) for ty in range(rows) for tx in range(cols) if cls[ty][tx] == 'x'
              and all(k(tx + dx, ty + dy) == 'x' for dx in (-1, 0, 1) for dy in (-1, 0, 1))]
    rnd.shuffle(wasser)
    for (tx, ty) in wasser:
        if len(rosen) >= 7:
            break
        if any(abs(tx - x) + abs(ty - y) < 4 for (x, y) in rosen):
            continue
        if any(k(tx + dx, ty + dy) == 'b' for dx in range(-2, 3) for dy in range(-2, 3)):
            continue
        objekte.append({'datei': 'k01/%s.png' % rnd.choice(SEEROSEN).split('/')[1], 'basis': 'seerose',
                        'x': tx * T + rnd.randint(-2, 3), 'y': ty * T + rnd.randint(0, 4), 'fuss': 12,
                        'kachel': [tx, ty], 'ebene': 0, 'liegend': True, 'schattenlos': True, 'wasser': True})
        rosen.append((tx, ty))
    # ---------------------------------------------------------------- Streudeko auf dem Rasen (wenig, unregelmaessig)
    def frei_gras(tx, ty):
        return all(k(tx + dx, ty + dy) == 'g' for dx in (-1, 0, 1) for dy in (-1, 0, 1))
    for liste, ziel, opt in ((FELS_KLEIN + FELS_GROSS, 8, {}), (PILZE, 7, {}), (BLUMEN, 26, {'anim': 'wehen'})):
        n, gesetzt = 0, []
        for _ in range(6000):
            if n >= ziel:
                break
            tx, ty = rnd.randrange(3, cols - 3), rnd.randrange(3, rows - 3)
            if not frei_gras(tx, ty) or any(abs(tx - x) + abs(ty - y) < 4 for (x, y) in gesetzt):
                continue
            if setze(rnd.choice(liste), tx, ty, opt, frei=True):
                n += 1
                gesetzt.append((tx, ty))
    # ---------------------------------------------------------------- Waldrand / Hecken auf allen 'h'-Kacheln
    for ty in range(rows):
        for tx in range(cols):
            if cls[ty][tx] == 'h' and (tx + ty) % 2 == 0:
                setze(rnd.choice(WALD), tx, ty, {'spiegeln': rnd.random() < 0.5}, frei=True, wald=True)
    json.dump(objekte, open(os.path.join(OBJ, 'platzierung.json'), 'w'), indent=0)
    print(len(objekte), 'Objekte am Raster')


if __name__ == '__main__':
    main()
    import regeln_a02                                                 # Regeln: nichts auf Wegen, Teleporter frei
    regeln_a02.objekte_pruefen('karte34', 'w')
