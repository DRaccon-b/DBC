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
    ('spiel/schaukel', 45.5, 46, {}), ('spiel/rutsche', 50.5, 47, {}), ('spiel/kuppel', 47, 48, {}),
]
# Wiesenbaeume nach der Vorlage (Fussmitte, Fusszeile); werden bei Bedarf auf die naechste freie Graskachel geschoben
BAEUME = [
    (LAUB[0], 51, 6), (LAUB[1], 6, 11), (LAUB[2], 14, 10), (LAUB[0], 17, 10), (GROSS, 20, 11), (LAUB[1], 26, 12),
    (LAUB[2], 28, 21), (LAUB[0], 29, 25), (LAUB[1], 17, 25), (LAUB[2], 17, 32), (GROSS, 7, 28), (LAUB[0], 3, 28),
    (LAUB[1], 3, 31), (LAUB[2], 3, 46), (LAUB[0], 27, 45), (GROSS, 36, 48), (LAUB[1], 58, 47), (LAUB[2], 60, 44),
]
ZYPRESSEN = [(2, 10), (8, 13), (2, 17), (26, 27), (20, 28), (4, 35), (23, 47), (25, 46), (19, 50), (24, 49)]
BAENKE = [(18.5, 21), (23.5, 31), (22.5, 36), (23.5, 40), (12.5, 40), (6.5, 38), (33.5, 32), (33.5, 38), (37.5, 40),
          (38.5, 30), (50.5, 25)]
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
    rects = []                                                   # (x0, y0, x1, y1, wald) sichtbare Pixelflaeche je Objekt
    for ty in range(rows):                                       # Teich und Steg: keine Fuesse im Wasser
        for tx in range(cols):
            if cls[ty][tx] in 'xb':
                gesperrt.add((tx, ty))
    for tp in lay['teleporter']:                                 # Teleporter frei (inkl. Umkreis, 2-Kachel-Sprites)
        for y in range(tp['y'] - 3, tp['y'] + tp['h'] + 3):
            for x in range(tp['x'] - 3, tp['x'] + tp['b'] + 3):
                gesperrt.add((x, y))
    cache = {}

    def boden(tx, ty):
        kk = k(tx, ty)
        return 'sand' if kk in 'wsem' else 'beton' if kk == 'p' else 'gras'

    def schnitt(a, b, rand=0):
        return not (a[2] + rand < b[0] or b[2] + rand < a[0] or a[3] + rand < b[1] or b[3] + rand < a[1])

    def setze(name, fx, fy, opt, frei=False, wald=False):
        """frei: nur wenn Kachel frei und keine Pixelueberlappung (2 px Abstand) mit vorhandenen Objekten.
        wald: Waldrand - darf Kronen anderer Waldbaeume ueberlappen, aber nie den Fuss (untere 20 px) anderer Objekte."""
        opt = dict(opt)
        spiegeln = opt.pop('spiegeln', False)
        flach = name.startswith('k01/deko')
        tx, ty = int(math.floor(fx)), int(fy)
        if frei:
            if (tx, ty) in gesperrt or (tx, ty, flach) in belegt:
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
        r = (o['x'] + ux0, o['y'] + uy0, o['x'] + ux1, o['y'] + uy1)
        if wald and not all(k(x, ty) in 'hg' for x in range(bx, bx + wt)):
            return False                                         # Waldrand/Hecke nie mit dem Fuss auf Pflaster oder Weg
        if opt.pop('begleiter', False):                          # Begleiter: Fuss auf Rasen, nicht in Gebaeuden/Moebeln
            if not all(k(x // T, r[3] // T) == 'g' for x in range(r[0], r[2] + 1, 4)):
                return False
            if any(schnitt(r, (a0, a1, a2, a3), 2) for (a0, a1, a2, a3, w), oo in zip(rects, objekte)
                   if not w and 'baum' not in oo['basis']):
                return False
        if wald:
            if any(schnitt(r, ((tp['x'] * T), (tp['y'] * T), (tp['x'] + tp['b']) * T - 1, (tp['y'] + tp['h']) * T - 1), 2)
                   for tp in lay['teleporter']):
                return False                                     # Waldbaeume nie ueber Teleportern
            if any(not w and schnitt(r, (a0, max(a1, a3 - 20), a2, a3), 1) for (a0, a1, a2, a3, w) in rects):
                return False
        elif frei and any(schnitt(r, rr[:4], 2) for rr in rects):
            return False
        o.update(opt)
        objekte.append(o)
        rects.append(r + (wald,))
        belegt[(tx, ty, flach)] = True
        if not flach:
            for x in range(bx, bx + wt):                         # Sockel/Block gesperrt
                for y in range(ty - (ht - 1 if not wald else 0), ty + 1):
                    gesperrt.add((x, y))
        return True

    def versuche(name, fx, fy, opt, klassen='g', r=2, breite=1):
        """Vorlagenlage einrasten: naechste Fusskachel(n) auf passendem Boden, frei und ohne Pixelueberlappung."""
        for d in range(r + 1):
            for dy in range(-d, d + 1):
                for dx in range(-d, d + 1):
                    if max(abs(dx), abs(dy)) != d:
                        continue
                    x, y = fx + dx, fy + dy
                    bx = int(math.floor(x + 0.5 - breite / 2.0 + 0.5))
                    if not all(k(bx + i, y) in klassen and k(bx + i, y + 1) in klassen + 'hp' for i in range(breite)):
                        continue
                    if setze(name, x, y, opt, frei=True):
                        return True
        print('nicht gesetzt:', name, fx, fy)
        return False

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
        if versuche(name, fx, fy, {'spiegeln': i % 2 == 1}, 'g', 2, 3):
            gesetzt_b.append(objekte[-1])
    for i, b in enumerate(gesetzt_b):
        bx, by, wt, ht = b['block']
        cx, fy = bx * T + wt * T // 2, (by + ht) * T - 1
        seite = -1 if i % 2 else 1
        art = i % 3
        mx = bx + wt // 2
        vorne_frei = all(k(mx + d, by + ht) == 'g' and (mx + d, by + ht) not in gesperrt for d in (-1, 0, 1))
        hinten_frei = all(k(x, by + ht - 2) == 'g' for x in range(bx, bx + wt))
        if art == 0 and vorne_frei:                              # Fels vor dem Stumpf (2 Kacheln hoch, eine Reihe tiefer)
            setze(rnd.choice(HOCH_FELS), cx / T, fy // T + 1, {'px': cx + seite * 5, 'py': fy + T, 'begleiter': True})
        elif (art == 1 or not vorne_frei) and hinten_frei:       # Fels hinter den Blaettern: eine Reihe hoeher, ragt
            setze(rnd.choice(FELS_GROSS), cx / T, fy // T - 1, {'px': cx + seite * 17, 'py': fy - T, 'begleiter': True})   # seitlich heraus
        elif vorne_frei:                                         # hohe Blume vor dem Stumpf
            setze(rnd.choice(HOCH_BLUME), cx / T, fy // T + 1, {'px': cx - seite * 5, 'py': fy + T, 'anim': 'wehen', 'begleiter': True})
    for o in gesetzt_b:                                          # Stammreihe +-1 und Begleiterreihe: keine freie Deko
        bx, by, wt, ht = o['block']
        for x in range(bx - 1, bx + wt + 1):
            for y in (by + ht - 2, by + ht - 1, by + ht, by + ht + 1):
                gesperrt.add((x, y))
    for i, (fx, fy) in enumerate(ZYPRESSEN):                     # schlanke Zypressen (Vorlage)
        if versuche(ZYPRESSE[i % 2], fx, fy, {'spiegeln': i % 3 == 0}, 'g', 2, 2):
            bx, by, wt, ht = objekte[-1]['block']
            for x in range(bx - 1, bx + wt + 1):
                for y in (by + ht - 1, by + ht, by + ht + 1):
                    gesperrt.add((x, y))
    # ---------------------------------------------------------------- Parkmoebel (nie auf dem Weg, beide Fusskacheln)
    for (fx, fy) in BAENKE:
        if not versuche('moebel/bank', fx, fy, {}, 'g', 2, 2):          # beide Fuesse auf demselben Boden
            versuche('moebel/bank', fx, fy, {}, 'p', 2, 2)
    for (fx, fy) in LATERNEN:
        versuche('moebel/laterne', fx, fy, {'anim': 'lampe'}, 'gp', 2, 1)
    # ---------------------------------------------------------------- Waldrand / Hecken auf allen 'h'-Kacheln
    for ty in range(rows):
        for tx in range(cols):
            if cls[ty][tx] == 'h' and (tx + ty) % 2 == 0:
                setze(rnd.choice(WALD), tx, ty, {'spiegeln': rnd.random() < 0.5}, frei=True, wald=True)
    deck = np.zeros((rows * T, cols * T), bool)                  # Luecken im Waldrand schliessen (kein nackter Waldboden)
    for (x0, y0, x1, y1, w) in rects:
        deck[max(0, y0):max(0, y1 + 1), max(0, x0):max(0, x1 + 1)] = True
    luecken = 0
    for ty in range(rows):
        for tx in range(cols):
            if cls[ty][tx] == 'h' and deck[ty * T:(ty + 1) * T, tx * T:(tx + 1) * T].mean() < 0.6:
                if setze(rnd.choice(['k01/baum12', 'k01/baum13', 'k01/baum14']), tx, ty,
                         {'spiegeln': rnd.random() < 0.5}, wald=True):
                    x0, y0, x1, y1, _ = rects[-1]
                    deck[max(0, y0):y1 + 1, max(0, x0):x1 + 1] = True
                    luecken += 1
    print('Waldrand-Luecken gefuellt:', luecken)
    # ---------------------------------------------------------------- Teich: Uferfelsen und Seerosen
    ufer = [(tx, ty) for ty in range(rows) for tx in range(cols) if cls[ty][tx] == 'm'
            and any(k(tx + dx, ty + dy) == 'x' for dx in (-1, 0, 1) for dy in (-1, 0, 1))
            and not any(k(tx + dx, ty + dy) == 'p' for dx in (-2, -1, 0, 1, 2) for dy in (-1, 0, 1))
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
        return all(k(tx + dx, ty + dy) == 'g' for dx in (-1, 0, 1) for dy in (-1, 0, 1, 2))
    gesetzt = []                                                 # Abstand ueber alle Listen (kein Klumpen)
    for liste, ziel, opt in ((FELS_KLEIN + FELS_GROSS, 8, {}), (PILZE, 7, {}), (BLUMEN, 26, {'anim': 'wehen'})):
        n = 0
        for _ in range(6000):
            if n >= ziel:
                break
            tx, ty = rnd.randrange(3, cols - 3), rnd.randrange(3, rows - 3)
            if not frei_gras(tx, ty) or any(abs(tx - x) + abs(ty - y) < 4 for (x, y) in gesetzt):
                continue
            if setze(rnd.choice(liste), tx, ty, opt, frei=True):
                n += 1
                gesetzt.append((tx, ty))
    json.dump(objekte, open(os.path.join(OBJ, 'platzierung.json'), 'w'), indent=0)
    print(len(objekte), 'Objekte am Raster')


if __name__ == '__main__':
    main()
    import regeln_a02                                                 # Regeln: nichts auf Wegen, Teleporter frei
    regeln_a02.objekte_pruefen('karte34', 'w')
