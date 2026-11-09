"""Objekte fuer Karte 21 (Digi-Egg Valley, A02) - Platzierungslogik wie Karte 20 / Karte 06.

  python3 tools/karte21_objekte.py && python3 tools/karte21_bauen.py

Schritt 1: Baeume. Waldrand ringsum mit den Baeumen von Karte 01 (wie Karte 20), auf der Wiese einzelne Baeume und
Baumpaare an den Stellen der Vorlage. Jedes Objekt im kleinsten Kachelblock, unten buendig, waagerecht zentriert.
"""
import json, math, os, random, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
import bauwerke

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte21')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte21')
T = 16
FREMD = {}
for i in range(16):
    FREMD['k01/baum%02d' % i] = 'karte01/baeume/%02d.png' % i
for i in range(64):
    FREMD['k01/deko%02d' % i] = 'karte01/deko/%02d.png' % i
WALD = ['k01/baum%02d' % i for i in (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 12, 13, 14)]
FELS_KLEIN = ['k01/deko08', 'k01/deko10']                    # kleiner Stein, Kiesel
FELS_GROSS = ['k01/deko09', 'k01/deko11']                    # bemooste Felsen
BLUMEN = ['k01/deko%02d' % i for i in (0, 1, 2, 3, 4, 27, 30)]
# vor dem Stumpf nur Objekte, die 2 Kacheln hoch sind (Nutzer): bemooste Felsen, Blumenbusch, Bluetenbusch, Loewenzahn;
# sie stehen eine Kachel tiefer, sodass nur ihre oberste Kachel den Stumpf ueberdeckt
HOCH_FELS = ['k01/deko09', 'k01/deko11']
HOCH_BLUME = ['k01/deko04', 'k01/deko27', 'k01/deko30']

FREMD.update({
    'k03/feuer': 'karte03/klein/16.png', 'k03/sack': 'karte03/klein/12.png', 'k03/sack2': 'karte03/klein/47.png',
    'k03/fass': 'karte03/klein/14.png', 'k03/kiste': 'karte03/klein/13.png', 'k03/teppich': 'karte03/klein/34.png',
    'k03/holz': 'karte03/klein/63.png', 'k04/wegweiser': 'karte04/mittel/13.png', 'k04/feuerring': 'karte04/mittel/04.png',
    'k01/laterne': 'karte01/laterne.png',
})
LILA = {'lager/segel': 'karte03/mittel/09.png',   # grosses Zelt (Nutzer: groesser)
         'lager/banner': 'karte03/klein/18.png'}   # rot -> lila umgefaerbt (Vorlage)
ACHSE_TOR = 45.5                                               # Achse des Tors: Paare an der Mauer spiegeln (Spalte x <-> 90 - x)
LAGER_OBEN = [
    ('lager/segel', 50.5, 7, {}), ('k03/sack', 54, 7, {}), ('k03/sack2', 55, 6, {}), ('k03/fass', 56, 5, {}),
    ('k03/feuer', 47.5, 11, {'anim': 'feuer'}), ('k01/deko16', 49.5, 12, {'liegend': True}), ('k04/wegweiser', 46, 14, {}),
    ('k04/feuerring', 35, 10, {}), ('teppich/00', 38.5, 11, {'liegend': True}), ('k03/holz', 52, 11, {}),   # ein Feuerring weniger (Nutzer)
]
MAUER_DEKO = [                                                 # exakt spiegelsymmetrisch zur Torachse
    ('k01/baum01', 43, 60, {'px': 45 * 16 - 23, 'py': 60 * 16 + 15, 'nur_blume': True}),  # links ein Baum statt Busch, ohne Fels (Nutzer)
    ('k01/deko25', 47, 60, {'an_wand': True, 'spiegeln': True}),
    ('k01/laterne', 27, 61, {'anim': 'laterne'}), ('k01/laterne', 63, 61, {'anim': 'laterne'}),
    ('lager/banner', 34, 62, {'anim': 'fahne'}), ('lager/banner', 56, 62, {'anim': 'fahne', 'spiegeln': True}),
]
# Lager unten auf dem Sand (Positionen nach der Vorlage, eher etwas weniger Kleinkram)
FREMD.update({'k03/schild': 'karte03/klein/19.png'})
LAGER_UNTEN_FEST = [                                           # Laternen paarweise spiegelsymmetrisch zur Torachse
    ('k01/laterne', 14, 75, {'anim': 'laterne'}), ('k01/laterne', 76, 75, {'anim': 'laterne'}),
    ('k01/laterne', 33, 70, {'anim': 'laterne'}), ('k01/laterne', 57, 70, {'anim': 'laterne'}),
]
LAGER_UNTEN = [
    ('lager/zelt', 11.5, 65, {}),
    ('k01/deko16', 23, 63, {'liegend': True}), 
    ('k01/deko41', 61, 71, {'liegend': True, 'spiegeln': True}),
    ('k01/deko16', 77, 66, {'liegend': True}),
    ('k03/sack', 16, 63, {}), ('saeule/14', 27, 67, {}), ('saeule/14', 81, 68, {'spiegeln': True}),
    ('saeule/11', 16, 68, {}), ('saeule/11', 59, 67, {'spiegeln': True}),
    ('k03/holz', 23, 69, {}), ('k03/holz', 67, 69, {}), 
    ('k03/schild', 29, 62, {}), ('k03/schild', 61, 62, {}), 
    ('k03/fass', 18, 73, {}), ('k03/fass', 75, 69, {}), ('k03/kiste', 12, 72, {}),
]
ZELT_QUELLE = 'karte04/mittel/02.png'                          # Zelt von Karte 04, lila eingefaerbt (Vorlage)


# Schreinhof: alles exakt spiegelsymmetrisch zur Torachse (Spalte x <-> 90 - x); PixelLab k21_schrein
def _sym(name, tx, fy, opt=None):
    """Pixelgenau mittig auf Kachel tx (Mitte tx + 0.5) -> Paare tx / 90 - tx liegen exakt gespiegelt zur Torachse."""
    o = dict(opt or {}); o['px'] = int((tx + 0.5) * 16); o['py'] = fy * 16 + 15
    return (name, tx, fy, o)


SCHREIN = [
    _sym('saeule/00', 36, 51), _sym('saeule/00', 54, 51),                           # Saeulen (grau, groesser - Nutzer)
    _sym('eier_nutzer/00', 38, 51), _sym('eier_nutzer/03', 41, 51),               # Digi-Eier des Nutzers (PixelLab)
    _sym('eier_nutzer/07', 49, 51), _sym('eier_nutzer/10', 52, 51),
    ('schrein/05', 45, 51, {'px': int(ACHSE_TOR * 16), 'py': 51 * 16 + 15}),         # Steintisch genau auf der Achse
    _sym('schrein/06', 37, 54), _sym('schrein/06', 53, 54),                         # Steinlaternen
]
TV_A, TV_B, TV_C, TV_D, TV_KAPUTT, TV_GROSS = 'tv/00', 'tv/01', 'tv/03', 'tv/04', 'tv/02', 'tv_gross/00'   # PixelLab k21_tv / k21_tv_gross
# Baeume auf der Wiese nach der Vorlage: (sprite, Kachel-x der Fussmitte, Fusszeile, Optionen)
FEST = [
    # oberhalb des Flusses
    ('k01/baum01', 27, 14, {}), ('k01/baum01', 59, 14, {'spiegeln': True}),
    ('k01/baum00', 8, 20, {}), ('k01/baum02', 9, 26, {}),
    ('k01/baum00', 74, 18, {'spiegeln': True}), ('k01/baum02', 81, 21, {}), ('k01/baum00', 83, 26, {}),
    ('k01/baum01', 78.5, 29, {}), ('k01/baum03', 81, 29, {'spiegeln': True}),
    # unterhalb des Flusses: Paare
    ('k01/baum00', 9, 37, {}), ('k01/baum01', 26.5, 37, {}), ('k01/baum02', 29, 37, {'spiegeln': True}),
    ('k01/baum02', 60.5, 37, {}), ('k01/baum01', 63, 37, {'spiegeln': True}),
    ('k01/baum00', 79.5, 37, {}), ('k01/baum03', 82, 37, {}),
    # mittlere Ebene vor der Burgmauer (unten weiter)
    ('k01/baum01', 9, 53, {}), ('k01/baum00', 64, 50, {'spiegeln': True}), ('k01/baum02', 83, 53, {}),
    # Fernseher auf der oberen Ebene: 70 % der Vorlage (7 kleine, 2 grosse Holzfernseher, 1 umgekippter)
    (TV_A, 15, 8, {}), (TV_B, 39, 6, {}), (TV_C, 11, 15, {}), (TV_A, 31, 16, {}),
    (TV_D, 54, 16, {}), (TV_B, 65, 18, {}), (TV_A, 77, 15, {}),
    (TV_GROSS, 20.5, 17, {}), (TV_GROSS, 67.5, 22, {'spiegeln': True}),
    (TV_KAPUTT, 24, 20, {}),
]
FEST += LAGER_OBEN + MAUER_DEKO + SCHREIN + LAGER_UNTEN_FEST


def lila(src, ziel):
    """Rote Stoffpixel (Segel, Banner) in das Lila der Vorlage umfaerben, Helligkeit bleibt."""
    a = np.array(Image.open(src).convert('RGBA')).astype(np.float32)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    rot = (a[..., 3] > 0) & (r > g + 70) & (r > b + 60) & (r > 130)        # nur kraeftiges Rot (Stoff), kein Holz
    l = (r * 0.5 + g * 0.3 + b * 0.2)[rot]
    ton = np.array([0.62, 0.36, 0.95], np.float32)
    a[rot, :3] = np.clip(l[:, None] * ton[None, :] * 1.55, 0, 255)
    os.makedirs(os.path.dirname(ziel), exist_ok=True)
    Image.fromarray(a.astype(np.uint8)).save(ziel)


def lila_zelt(src, ziel):
    """Ganzes Zeltstoff-Sprite (Beige/Braun) ins dunkle Lila der Vorlage einfaerben; Helligkeit bleibt, Konturen bleiben dunkel."""
    a = np.array(Image.open(src).convert('RGBA')).astype(np.float32)
    l = a[..., 0] * 0.4 + a[..., 1] * 0.45 + a[..., 2] * 0.15
    m = a[..., 3] > 0
    ton = np.array([0.66, 0.44, 0.98], np.float32)
    a[m, :3] = np.clip(l[m][:, None] * ton[None, :] * 1.05, 0, 255)
    Image.fromarray(a.astype(np.uint8)).save(ziel)


def main():
    rnd = random.Random(21)
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cls = lay['klassen']
    cols, rows = lay['groesse']
    for name, quelle in FREMD.items():
        ziel = os.path.join(OBJ, name + '.png')
        q = os.path.join(ROOT, 'assets', 'objekte', quelle)
        if os.path.exists(q):
            os.makedirs(os.path.dirname(ziel), exist_ok=True)
            shutil.copy(q, ziel)
    for name, quelle in LILA.items():
        lila(os.path.join(ROOT, 'assets', 'objekte', quelle), os.path.join(OBJ, name + '.png'))
    lila_zelt(os.path.join(ROOT, 'assets', 'objekte', ZELT_QUELLE), os.path.join(OBJ, 'lager', 'zelt.png'))
    belegt, objekte, gesperrt = {}, [], set()
    for ty in range(rows):                                         # Fluss: keine Baumfuesse im oder direkt am Wasser
        for tx in range(cols):
            if cls[ty][tx] in 'xb':
                for dy in (-2, -1, 0, 1):
                    gesperrt.add((tx, ty + dy))
    mk = lay['mauer_kante']                                       # Burgmauer, Treppen und Tor frei halten
    for x in range(cols):
        for y in range(mk, mk + 5):
            if cls[y][x] != 'h':
                gesperrt.add((x, y))
    for tp in lay['teleporter']:
        for y in range(tp['y'] - 1, tp['y'] + tp['h'] + 1):
            for x in range(tp['x'] - 1, tp['x'] + tp['b'] + 1):
                gesperrt.add((x, y))
    cache = {}

    def boden(tx, ty):
        k = cls[min(rows - 1, max(0, ty))][min(cols - 1, max(0, tx))]
        return 'sand' if k in 'wfe' else 'beton' if k in 'pqmto' else 'gras'

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
        b = boden(tx, ty)
        key = (name, b, spiegeln)
        if key not in cache:
            sp = Image.open(os.path.join(OBJ, name + '.png')).convert('RGBA')
            if spiegeln:
                sp = sp.transpose(Image.FLIP_LEFT_RIGHT)
            aa = np.array(sp.getchannel('A')) > 0
            ys, xs = np.nonzero(aa)
            ux0, uy0, ux1, uy1 = int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())
            art = 'baum' if 'baum' in name or 'kirsche' in name else 'klein' if flach else 'stein'
            ohne_fuss = name in ('k01/laterne', 'k06/tv_treppe', 'k03/teppich', 'teppich/00') or name.startswith(('k07/gemuese', 'beet/'))
            v = sp if ohne_fuss else bauwerke.bodenfuss(sp, b, art)
            off = 0 if ohne_fuss else 2
            datei = 'varianten/%s_%s%s.png' % (name.replace('/', '-'), b, '_m' if spiegeln else '')
            os.makedirs(os.path.join(OBJ, 'varianten'), exist_ok=True)
            v.save(os.path.join(OBJ, datei))
            cache[key] = (datei, v.height, ux0 + off, uy0, ux1 + off, uy1)
        datei, h, ux0, uy0, ux1, uy1 = cache[key]
        bw, bh = ux1 - ux0 + 1, uy1 - uy0 + 1
        wt, ht = math.ceil(bw / T), math.ceil(bh / T)
        bx = int(round(fx + 0.5 - wt / 2.0))
        o = {'datei': datei, 'basis': name, 'x': bx * T + (wt * T - bw) // 2 - ux0, 'y': (ty + 1) * T - 1 - uy1,
             'fuss': h, 'kachel': [tx, ty], 'block': [bx, ty - ht + 1, wt, ht], 'ebene': 0 if flach else 1}
        px_, py_ = opt.pop('px', None), opt.pop('py', None)
        if px_ is not None:                                      # pixelgenaue Lage (Beetpflanzen)
            o['x'] = px_ - (ux0 + bw // 2)
            o['y'] = py_ - uy1
        o.update(opt)
        objekte.append(o)
        belegt[(tx, ty, flach)] = True
        for x in range(bx, bx + wt):
            for y in range(ty - ht + 1, ty + 1):
                gesperrt.add((x, y))
        return True

    for (name, fx, fy, opt) in FEST:
        setze(name, fx, fy, opt)
    for (name, fx, fy, opt) in LAGER_UNTEN:                     # Lager unten: nur wo frei (keine Ueberlappung)
        setze(name, fx, fy, opt, frei=True)
    for o in objekte:                                            # vor Lagerobjekten keine freie Deko (sonst Ueberlappung)
        if o['kachel'][1] >= 60 and not o['basis'].startswith('k01/deko'):
            bx, by, wt, ht = o['block']
            for x in range(bx - 1, bx + wt + 1):
                gesperrt.add((x, by + ht))
    # Begleiter der Wiesenbaeume (Regel 5, nur Baeume in der Karte, nicht am Waldrand):
    # Fels vor dem Stamm (ueberdeckt den Sockel), Fels hinter den Blaettern (eine Reihe hoeher, die Krone verdeckt
    # ihn teilweise), Blumen an den Sockelecken
    BEGLEITET = ('k01/baum', 'tv')                              # Regel 5d gilt fuer Wiesenbaeume und Fernseher
    baeume = [o for o in objekte if o['basis'].startswith(BEGLEITET)]
    for i, b in enumerate(baeume):
        bx, by, wt, ht = b['block']
        cx, fy = bx * T + wt * T // 2, (by + ht) * T - 1
        seite = -1 if i % 2 else 1
        art = i % 3
        if b.get('nur_blume'):                                   # nur eine Blume vor dem Stumpf, kein Fels (Nutzer)
            setze(rnd.choice(HOCH_BLUME), cx / T, fy // T + 1, {'px': cx - seite * 5, 'py': fy + T, 'anim': 'wehen'})
            continue
        if b['basis'].startswith('tv'):                          # Fernseher: Begleiter nur an der Ecke (der Bildschirm bleibt frei)
            w2 = wt * T // 2
            if art == 0:
                setze(rnd.choice(HOCH_FELS), cx / T, fy // T + 1, {'px': cx + seite * (w2 + 6), 'py': fy + T})
            elif art == 1:
                setze(rnd.choice(FELS_GROSS), cx / T, fy // T - 1, {'px': cx + seite * (w2 + 2), 'py': fy - 7})
            else:
                setze(rnd.choice(HOCH_BLUME), cx / T, fy // T + 1, {'px': cx - seite * (w2 + 6), 'py': fy + T, 'anim': 'wehen'})
            continue
        if art == 0:                                             # ueber dem Stumpf: hoher Fels
            setze(rnd.choice(HOCH_FELS), cx / T, fy // T + 1, {'px': cx + seite * 5, 'py': fy + T})
            continue                                             # keine zweite Pflanze daneben (keine Ueberlappung)
        elif art == 1:                                           # hinter den Blaettern
            setze(rnd.choice(FELS_GROSS), cx / T, fy // T - 1, {'px': cx + seite * 8, 'py': fy - 7})
        else:                                                    # hinter den Blaettern + hohe Blume ueber dem Stumpf
            setze(rnd.choice(FELS_GROSS), cx / T, fy // T - 1, {'px': cx + seite * 9, 'py': fy - 7})
            setze(rnd.choice(HOCH_BLUME), cx / T, fy // T + 1, {'px': cx - seite * 5, 'py': fy + T, 'anim': 'wehen'})
            continue
        setze(rnd.choice(HOCH_BLUME), cx / T, fy // T + 1, {'px': cx - seite * 13, 'py': fy + T, 'anim': 'wehen'})
    # Neben den Baeumen (Stammreihe und Reihe darueber) nichts Freies setzen, sonst liegt es auf dem Stumpf
    for o in objekte:
        if o['basis'].startswith(BEGLEITET):
            bx, by, wt, ht = o['block']
            for x in range(bx - 1, bx + wt + 1):
                for y in (by + ht - 2, by + ht - 1, by + ht):
                    gesperrt.add((x, y))
    # Felsen und Blumen frei auf der Wiese (nicht an Wegen, Wasser, Platz oder Mauer)
    def frei_gras(tx, ty):
        return all(cls[min(rows - 1, max(0, ty + dy))][min(cols - 1, max(0, tx + dx))] == 'g'
                   for dx in (-1, 0, 1) for dy in (-1, 0, 1))
    lampen = []                                                     # Laternen am Weg entlang (eher wenige, Nutzer)
    for (lx, ly) in [(o['kachel'][0], o['kachel'][1]) for o in objekte if o['basis'] == 'k01/laterne']:
        lampen.append((lx, ly))
    kand = []
    for ty in range(4, 56):
        for tx in range(5, cols - 5):
            if cls[ty][tx] != 'g' or not any(cls[ty][tx + d] == 'w' for d in (-1, 1)):
                continue
            if any(cls[ty + dy][tx + dx] in 'xbpqe' for dx in range(-2, 3) for dy in range(-2, 3)):
                continue
            kand.append((tx, ty))
    rnd.shuffle(kand)
    n_l = 0
    for (tx, ty) in kand:
        if n_l >= 9:
            break
        if any(abs(tx - lx) + abs(ty - ly) < 14 for (lx, ly) in lampen):
            continue
        if setze('k01/laterne', tx, ty, {'anim': 'laterne'}, frei=True):
            lampen.append((tx, ty)); n_l += 1
    steine = 0                                                      # ein paar kleine Steine auf dem Platz (nicht im Hof)
    for _ in range(3000):
        if steine >= 7:
            break
        tx, ty = rnd.randrange(20, 70), rnd.randrange(42, 57)
        if not all(cls[ty + dy][tx + dx] == 'p' for dx in (-1, 0, 1) for dy in (-1, 0, 1)):
            continue
        if setze(rnd.choice(FELS_KLEIN), tx, ty, {}, frei=True):
            steine += 1
    pilze = 0                                                       # Pilze am Flussufer (Gras direkt neben dem Ufersand)
    for _ in range(3000):
        if pilze >= 10:
            break
        tx, ty = rnd.randrange(4, cols - 4), rnd.randrange(24, 40)
        if any(cls[ty + dy][min(cols - 1, max(0, tx + dx))] == 'b' for dx in range(-3, 4) for dy in range(-3, 4)):
            continue                                                # nicht an den Brueckenkoepfen
        if cls[ty][tx] != 'g' or not any(cls[ty + dy][tx] == 'w' and any(cls[ty + dy + e][tx] == 'x' for e in (-2, -1, 1, 2))
                                         for dy in (-1, 1)):
            continue
        if setze(rnd.choice(['k01/deko14', 'k01/deko14', 'k01/deko31']), tx, ty, {}, frei=True):
            pilze += 1
    for liste, ziel in ((FELS_KLEIN + FELS_GROSS, 16), (BLUMEN, 40)):
        n = 0
        for _ in range(5000):
            if n >= ziel:
                break
            tx, ty = rnd.randrange(3, cols - 3), rnd.randrange(3, rows - 3)
            if not frei_gras(tx, ty):
                continue
            n_ = rnd.choice(liste)
            if setze(n_, tx, ty, {'anim': 'wehen'} if n_ in BLUMEN else {}, frei=True):
                n += 1
    for ty in range(rows):                                       # Waldrand wie Karte 06
        for tx in range(cols):
            if cls[ty][tx] == 'h' and (tx + ty) % 2 == 0:
                setze(rnd.choice(WALD), tx, ty, {'spiegeln': rnd.random() < 0.5}, frei=True, wald=True)
    json.dump(objekte, open(os.path.join(OBJ, 'platzierung.json'), 'w'), indent=0)
    print(len(objekte), 'Objekte am Raster')


if __name__ == '__main__':
    main()
