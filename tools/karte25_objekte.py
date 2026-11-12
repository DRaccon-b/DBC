"""Objekte fuer Karte 25 (Sunset Bay, A02) - Platzierung am 16x16-Raster nach der Vorlage, Logik wie Karte 23/24.

  python3 tools/karte25_bauen.py   (einmal -> wand.npy)
  python3 tools/karte25_objekte.py && python3 tools/karte25_bauen.py

Schritt 1: Grasplateau oben. Leuchtturm (PixelLab k25_leuchtturm), Obelisk (Karte 24), graue Felsen, Steine,
Grasbueschel und Blumen (Karte 01), kleine Nadelbaeume (Karte 01) in Gruppen mit Begleitern (Regel 5).
"""
import json, math, os, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
import bauwerke
from karte04_objekte import saeubern

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte25')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte25')
T = 16
FREMD = {'k24/obelisk': 'karte24/obelisk2/00.png'}
for i in range(64):
    FREMD['k01/deko%02d' % i] = 'karte01/deko/%02d.png' % i
for i in range(16):
    FREMD['k01/baum%02d' % i] = 'karte01/baeume/%02d.png' % i
for i in (0, 1, 2, 7, 9):
    FREMD['k03/palme%02d' % i] = 'karte03/palmen/%02d.png' % i
FREMD['k03/fackel'] = 'karte03/klein/15.png'
FREMD['k03/fass'] = 'karte03/klein/14.png'
LEUCHTTURM, OBELISK = 'leuchtturm/00', 'k24/obelisk'
HUETTE, BOOT, BECKEN, BANK = 'huette_gross/00', 'strand/01', 'strand/02', 'strand/03'
FACKEL, FASS, SEESTERN, MUSCHEL, MUSCHEL2 = 'k03/fackel', 'k03/fass', 'k01/deko20', 'k01/deko21', 'k01/deko21'
P1, P2, P3, P4, P5 = 'k03/palme00', 'k03/palme01', 'k03/palme02', 'k03/palme07', 'k03/palme09'
FELS_G, FELS_G2, STEIN, STEIN2 = 'k01/deko09', 'k01/deko11', 'k01/deko08', 'k01/deko10'
GRAS, GRAS2, BLUME, BLUME2, BLUME3, PINK = 'k01/deko05', 'k01/deko06', 'k01/deko00', 'k01/deko03', 'k01/deko01', 'k01/deko02'
TANNE, TANNE2 = 'k01/baum07', 'k01/baum08'

# (sprite, Kachel-x der Fussmitte, Fusszeile, Optionen) - nach der Vorlage, grosse Objekte zuerst
PLATEAU = [
    (LEUCHTTURM, 53, 12, {'anim': 'lampe'}),                     # Leuchtturm rechts neben dem Sandplatz
    (OBELISK, 7, 15, {}),                                        # dunkler Obelisk links
    # kleine Nadelbaeume in Gruppen (Vorlage: links und rechts vom Leuchtturm)
    (TANNE, 42, 5, {}), (TANNE2, 42.5, 9, {}), (TANNE2, 45.5, 7, {'spiegeln': True}),
    (TANNE, 58, 8, {}), (TANNE2, 60.5, 10, {'spiegeln': True}),
    # graue Felsen
    (FELS_G, 5, 7, {}), (FELS_G2, 19, 5, {}), (FELS_G, 17, 12, {'spiegeln': True}), (FELS_G2, 34, 16, {}),
    (FELS_G, 56, 17, {}), (FELS_G2, 24, 18, {'spiegeln': True}), (FELS_G, 4, 18, {}), (FELS_G2, 49, 4, {}),
    # Begleiter der Nadelbaeume (Regel 5): Fels / Blumen am Sockel
    (STEIN, 40.5, 6, {}), (BLUME2, 47.5, 7, {'anim': 'wehen'}), (STEIN2, 56.5, 9, {}), (PINK, 63, 9, {'anim': 'wehen'}),
    (GRAS, 51, 12, {'anim': 'wehen'}), (GRAS2, 55, 12, {'anim': 'wehen'}),        # Bueschel am Sockel des Leuchtturms
    (GRAS2, 6, 15, {'anim': 'wehen'}),                                             # und am Obelisken
    # Kleinkram: Steine, Bueschel, Blumen (unregelmaessig, eher wenig)
    (STEIN, 9, 5, {}), (STEIN2, 28, 7, {}), (STEIN, 12, 16, {}), (STEIN2, 38, 13, {}), (STEIN, 61, 15, {}),
    (STEIN2, 2, 11, {}), (STEIN, 30, 14, {}),
    (GRAS, 7, 4, {'anim': 'wehen'}), (GRAS2, 14, 8, {'anim': 'wehen'}), (GRAS, 23, 6, {'anim': 'wehen'}),
    (GRAS2, 33, 5, {'anim': 'wehen'}), (GRAS, 10, 12, {'anim': 'wehen'}), (GRAS2, 3, 15, {'anim': 'wehen'}),
    (GRAS, 27, 17, {'anim': 'wehen'}), (GRAS2, 40, 17, {'anim': 'wehen'}), (GRAS, 50, 15, {'anim': 'wehen'}),
    (GRAS2, 57, 13, {'anim': 'wehen'}), (GRAS, 62, 18, {'anim': 'wehen'}), (GRAS2, 20, 15, {'anim': 'wehen'}),
    (BLUME, 12, 6, {'anim': 'wehen'}), (BLUME3, 26, 11, {'anim': 'wehen'}), (BLUME, 36, 10, {'anim': 'wehen'}),
    (BLUME3, 4, 9, {'anim': 'wehen'}), (BLUME2, 31, 19, {'anim': 'wehen'}), (BLUME, 48, 18, {'anim': 'wehen'}),
]

STRAND = [                                                       # Sandstrand nach der Vorlage, grosse Objekte zuerst
    (HUETTE, 26, 37, {}), (HUETTE, 11, 43, {}), (HUETTE, 22, 43, {'spiegeln': True}), (HUETTE, 47, 43, {}),
    (OBELISK, 58, 44, {}), (OBELISK, 87, 28, {}),
    # Palmen locker verteilt (Nutzer: weiter auseinander); zwei direkt unter der Felsfront ragen vor die Klippe
    (P1, 29, 25, {'anim': 'wehen'}), (P4, 49, 26, {'anim': 'wehen'}),
    (P2, 35, 29, {'anim': 'wehen'}), (P3, 33, 41, {'anim': 'wehen'}),        # vier Palmen in der Mitte entfernt (Nutzer)
    (P1, 41.5, 43, {'anim': 'wehen', 'spiegeln': True}), (P2, 51, 39, {'anim': 'wehen'}),
    (P2, 59, 28, {'anim': 'wehen'}), (P3, 65, 27, {'anim': 'wehen'}), (P1, 62, 32, {'anim': 'wehen', 'spiegeln': True}),
    (P4, 70, 25, {'anim': 'wehen'}), (P5, 68, 31, {'anim': 'wehen'}),
    # Boote am Wasser
    (BOOT, 20, 45, {}), (BOOT, 27, 44, {'spiegeln': True}), (BOOT, 54, 42, {}),
    # Fackeln, Baenke, Faesser am Dorfplatz links
    (FACKEL, 13, 31, {'anim': 'feuer'}), (FACKEL, 9, 34, {'anim': 'feuer'}), (FACKEL, 19, 34, {'anim': 'feuer'}),
    (FACKEL, 9, 38, {'anim': 'feuer'}), (FACKEL, 16, 38, {'anim': 'feuer'}),
    (BANK, 15.5, 42, {}), (BANK, 19.5, 31, {}),
    (FASS, 17, 44, {}), (FASS, 30, 38, {}), (FASS, 5, 43, {}),
    # Kleinkram (sparsam): Seesterne, Muscheln, Steine
    (SEESTERN, 27, 31, {}), (SEESTERN, 44, 29, {}), (SEESTERN, 56, 37, {}), (SEESTERN, 66, 37, {}), (SEESTERN, 15, 35, {}),
    (MUSCHEL, 31, 44, {}), (MUSCHEL2, 48, 38, {}), (MUSCHEL, 72, 33, {}), (MUSCHEL2, 11, 28, {}), (MUSCHEL, 60, 41, {}),
    (STEIN, 11, 26, {}), (STEIN, 16, 26, {}), (STEIN, 33, 25, {}), (STEIN, 49, 27, {}), (STEIN, 57, 25, {}),
]


def main():
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cls, hoehe = lay['klassen'], lay['hoehe']
    cols, rows = lay['groesse']
    for name, quelle in FREMD.items():
        ziel = os.path.join(OBJ, name + '.png')
        os.makedirs(os.path.dirname(ziel), exist_ok=True)
        shutil.copy(os.path.join(ROOT, 'assets', 'objekte', quelle), ziel)
    wand = np.unpackbits(np.load(os.path.join(KARTE, 'wand.npy')))[:rows * T * cols * T].reshape(rows * T, cols * T).astype(bool)
    objekte, cache, belegt = [], {}, set()
    import karte04_bauen as k4                                   # Wege/Sand auf dem Plateau genau wie im Gelaende
    hp = np.kron(np.array([[int(c) for c in z] for z in hoehe]), np.ones((T, T), int))
    weg = k4.weich(k4.zell_maske(cls, 'wst', cols, rows), 7.0, 0.5, 4) & (hp >= 2)
    for (name, fx, fy, opt, ebene) in [e + ('2',) for e in PLATEAU] + [e + ('1',) for e in STRAND]:
        opt = dict(opt)
        spiegeln = opt.pop('spiegeln', False)
        flach = name in (STEIN, STEIN2, GRAS, GRAS2, BLUME, BLUME2, BLUME3, PINK, SEESTERN, MUSCHEL, MUSCHEL2, BECKEN)
        tx, ty = int(math.floor(fx)), int(fy)
        k = cls[ty][tx]
        b = 'sand' if k in 'wsn' else 'gras'
        key = (name, b, spiegeln)
        if key not in cache:
            sp = Image.open(os.path.join(OBJ, name + '.png')).convert('RGBA')
            if not name.startswith('k01/'):
                sp = saeubern(sp)
            if spiegeln:
                sp = sp.transpose(Image.FLIP_LEFT_RIGHT)
            aa = np.array(sp.getchannel('A')) > 0
            ys, xs = np.nonzero(aa)
            ux0, uy0, ux1, uy1 = int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())
            art = 'baum' if 'baum' in name or 'palme' in name else 'klein' if flach else 'stein'
            ohne_fuss = flach or name in (OBELISK, BOOT, FACKEL, BANK, FASS)
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
        x, y = bx * T + (wt * T - bw) // 2 - ux0, (ty + 1) * T - 1 - uy1
        fuss = range(bx, bx + wt)
        unten = [(xx, yy) for xx in fuss for yy in (ty, ty - 1)]
        if any(hoehe[ty][xx] != ebene or cls[ty][xx] not in 'gwsn' for xx in fuss) or wand[max(0, (ty - 1) * T):(ty + 1) * T, bx * T:(bx + wt) * T].any() \
                or any(p in belegt for p in unten) \
                or (flach and ebene == '2' and any(cls[yy][xx] != 'g' for xx in range(tx - 1, tx + 2) for yy in (ty - 1, ty, ty + 1))) \
                or (ebene == '1' and name != BOOT and any(cls[yy][xx] not in 'sn' for xx in range(bx - 1, bx + wt + 1) for yy in (ty, ty + 1))) \
                or (name == BOOT and any(cls[ty][xx] not in 'sn' for xx in fuss)):         # Boote liegen am Wasser
            print('  uebersprungen:', name, fx, fy)
            continue
        al = np.array(Image.open(os.path.join(OBJ, datei)))[..., 3] > 0   # nichts auf dem Weg (Nutzer)
        ys_, xs_ = np.nonzero(al)
        Y_, X_ = ys_ + y, xs_ + x
        ok = (Y_ >= 0) & (Y_ < weg.shape[0]) & (X_ >= 0) & (X_ < weg.shape[1])
        if ebene == '2' and weg[Y_[ok], X_[ok]].any():              # nur Objekte auf dem Plateau (Palmen vom Strand duerfen vor die Klippe ragen)
            print('  auf dem Weg, entfernt:', name, fx, fy)
            continue
        if not flach:
            for p in unten:
                belegt.add(p)
        o = {'datei': datei, 'basis': name, 'x': x, 'y': y, 'fuss': h, 'kachel': [tx, ty],
             'block': [bx, ty - ht + 1, wt, ht], 'ebene': 0 if flach else 1}
        o.update(opt)
        objekte.append(o)
    json.dump(objekte, open(os.path.join(OBJ, 'platzierung.json'), 'w'), indent=0)
    print('Karte 25: %d Objekte' % len(objekte))


if __name__ == '__main__':
    main()
    import regeln_a02                                                 # Regeln: nichts auf Wegen, Teleporter frei
    regeln_a02.objekte_pruefen('karte25', 'w')
