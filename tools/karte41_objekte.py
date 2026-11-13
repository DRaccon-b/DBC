"""Objekte fuer Karte 41 - Digital World: Wind Desert (A03 Nr. 8), Platzierung nach der Vorlage.

  python3 tools/karte41_bauen.py   (einmal -> pixelhoehe.npy, wand.npy)
  python3 tools/karte41_objekte.py && python3 tools/karte41_bauen.py

Wiederverwendet (Regel 3): Akazien, toter Baum, Felsen, Knochen, Schaedel, Gras, Kiesel, Zweige, Pilze (Karte 04),
Skelett, Sandsteinfels, Banner mit Sonnenwappen (Karte 03), runder Laubbaum (Karte 01). Neu (PixelLab k41_wueste):
roter Getraenkeautomat, dunkle Steinsaeulen (ganz/abgebrochen), Fell-Unterstand auf Felsen.
Grosse Objekte zuerst (Positionen der Vorlage), dann Begleiter an den Baeumen (Regel 5/5d), dann sparsame Streudeko.
"""
import json, math, os, random, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte41')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte41')
T = 16
FREMD = {
    'akazie': 'karte04/baeume/00.png', 'akazie_klein': 'karte04/baeume/03.png', 'totbaum': 'karte04/baeume/02.png',
    'felsen': 'karte04/baeume/08.png', 'fels_sand': 'karte03/mittel/07.png', 'fels_grau': 'karte04/mittel/00.png',
    'skelett': 'karte03/mittel/06.png', 'knochen': 'karte04/mittel/08.png', 'schaedel': 'karte04/mittel/09.png',
    'busch_tot': 'karte04/mittel/10.png', 'steinhaufen': 'karte04/mittel/15.png',
    'banner': 'karte03/mittel3/01.png', 'laubbaum': 'karte01/baeume/00.png',
    'gras': 'karte04/klein/00.png', 'gras2': 'karte04/klein/01.png', 'gras3': 'karte04/klein/27.png',
    'kiesel': 'karte04/klein/02.png', 'zweig': 'karte04/klein/09.png', 'knochen_k': 'karte04/klein/03.png',
    'kristall': 'karte04/klein/05.png', 'pilz': 'karte04/klein/11.png', 'stein': 'karte04/klein/08.png',
    'automat': 'karte41/wueste/00.png', 'saeule': 'karte41/wueste/01.png', 'unterstand': 'karte41/wueste/02.png',
    'saeule_kaputt': 'karte41/wueste/03.png',
}
# (Sprite, Kachel-x der Fussmitte, Fusszeile) nach der Vorlage
BAEUME = [('totbaum', 29, 11), ('totbaum', 36, 27), ('totbaum', 72, 28), ('totbaum', 48, 43), ('totbaum', 83, 55),
          ('totbaum', 53, 69), ('akazie', 37, 35), ('akazie', 75, 55), ('akazie', 40, 62), ('akazie_klein', 38, 68),
          ('akazie', 28, 72), ('laubbaum', 24, 72), ('laubbaum', 40, 73)]
GROSS = [('unterstand', 13, 56), ('skelett', 80, 44), ('skelett', 59, 72),
         ('automat', 82, 28), ('automat', 13, 61), ('automat', 20, 72),
         ('banner', 75, 29), ('banner', 56, 74),
         ('saeule', 57, 8), ('saeule', 28, 31), ('saeule_kaputt', 34, 31), ('saeule', 73, 24), ('saeule_kaputt', 74, 77),
         ('fels_sand', 30, 7), ('felsen', 31, 31), ('fels_sand', 52, 33), ('felsen', 78, 19), ('fels_sand', 84, 34),
         ('felsen', 12, 48), ('fels_sand', 77, 48), ('felsen', 57, 58), ('fels_sand', 44, 72), ('felsen', 72, 72)]
STREU = ['gras', 'gras2', 'gras3', 'kiesel', 'zweig', 'knochen_k', 'kristall', 'stein']
BODEN = 'sbdk'                       # begehbarer Wuestenboden (kein Gras/Teich/Teleporter/Plateau)


def main():
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cls = lay['klassen']
    cols, rows = lay['groesse']
    lvl = np.load(os.path.join(KARTE, 'pixelhoehe.npy'))
    wand = np.unpackbits(np.load(os.path.join(KARTE, 'wand.npy')))[:lvl.size].reshape(lvl.shape).astype(bool)
    wasser = np.unpackbits(np.load(os.path.join(KARTE, 'wasser.npy')))[:lvl.size].reshape(lvl.shape).astype(bool)
    from PIL import ImageFilter
    wasser = np.array(Image.fromarray((wasser * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(15))) > 0   # mit Ufer
    os.makedirs(os.path.join(OBJ, 'fremd'), exist_ok=True)
    os.makedirs(os.path.join(OBJ, 'varianten'), exist_ok=True)
    for n, q in FREMD.items():
        if not q.startswith('karte41/'):
            shutil.copy(os.path.join(ROOT, 'assets', 'objekte', q), os.path.join(OBJ, 'fremd', n + '.png'))
    pfad = lambda n: os.path.join(ROOT, 'assets', 'objekte', FREMD[n]) if FREMD[n].startswith('karte41/') \
        else os.path.join(OBJ, 'fremd', n + '.png')
    tps = [(t['x'] * T - 2 * T, t['y'] * T - 2 * T, (t['x'] + t['b'] + 2) * T, (t['y'] + t['h'] + 2) * T)
           for t in lay['teleporter']]
    objekte, rects = [], []
    k = lambda tx, ty: cls[ty][tx] if 0 <= tx < cols and 0 <= ty < rows else 'r'

    def schnitt(a, b, d):
        return not (a[2] + d < b[0] or b[2] + d < a[0] or a[3] + d < b[1] or b[3] + d < a[1])

    def setze(name, cx, fy, opt=None, spiegeln=False, klassen=BODEN, pruefen=True, ohne=()):
        sp = Image.open(pfad(name)).convert('RGBA')
        if spiegeln:
            sp = sp.transpose(Image.FLIP_LEFT_RIGHT)
        datei = 'varianten/%s%s.png' % (name, '_m' if spiegeln else '')
        sp.save(os.path.join(OBJ, datei))
        bb = sp.getbbox()
        x = int(round(cx - (bb[0] + bb[2]) / 2.0))
        y = int(fy - (bb[3] - 1))
        r = (x + bb[0], y + bb[1], x + bb[2] - 1, y + bb[3] - 1)
        if r[0] < 0 or r[1] < 0 or r[2] >= cols * T or r[3] >= rows * T:
            return None
        if pruefen:
            if any(schnitt(r, tuple(rr[:4]), 2) for i_, rr in enumerate(rects) if i_ not in ohne):
                return None
            if any(schnitt(r, t_, 0) for t_ in tps):
                return None
            ty_ = r[3] // T
            if any(k(xx, ty_) not in klassen for xx in range(r[0] // T, r[2] // T + 1)):
                return None
            if (lvl[r[3] - 3:r[3] + 2, r[0]:r[2] + 1] != 1).any() or wand[r[3] - 3:r[3] + 2, r[0]:r[2] + 1].any():
                return None                                          # Fuss ganz auf dem Wuestenboden, nie an der Wand
            if wasser[max(0, r[1]):r[3] + 1, r[0]:r[2] + 1].any():
                return None                                          # nichts auf Teich oder Ufer
            if (lvl[max(0, r[1]):r[3], r[0]:r[2] + 1] > 1).any() and not (opt or {}).get('vor_fels'):
                hoch = lvl[max(0, r[1]):r[3], r[0]:r[2] + 1] > 1     # Verdeckung durch Hoehen: nur Plateau im Norden
                if hoch[:, :].any(axis=0).sum() and hoch[-T:].any():
                    return None
        o = {'datei': datei, 'basis': name, 'x': x, 'y': y, 'fuss': bb[3] - 1, 'kachel': [int(cx) // T, int(fy) // T],
             'ebene': 1}
        o.update(opt or {})
        objekte.append(o)
        rects.append(list(r) + [name])
        return o

    def kachel(name, tx, ty, opt=None, spiegeln=False, klassen=BODEN, suche=4):
        sp = Image.open(pfad(name))
        bw = sp.getbbox()[2] - sp.getbbox()[0]
        wt = max(1, math.ceil(bw / T))
        for d in range(suche + 1):
            for dy in range(-d, d + 1):
                for dx in range(-d, d + 1):
                    if max(abs(dx), abs(dy)) != d:
                        continue
                    x0 = tx + dx - (wt - 1) // 2
                    o = setze(name, x0 * T + wt * T / 2.0, (ty + dy) * T + T - 1, opt, spiegeln, klassen)
                    if o:
                        return o
        print('  nicht gesetzt:', name, tx, ty)
        return None

    rnd = random.Random(41)
    # ---------------- Baeume (gross zuerst), Begleiter nach Regel 5/5d
    for i, (n, tx, ty) in enumerate(BAEUME):
        kl = BODEN + ('n' if n in ('laubbaum', 'akazie', 'akazie_klein') else '')
        o = kachel(n, tx, ty, {'anim': 'baum'} if n != 'totbaum' else {}, i % 2 == 1, kl)
        if not o:
            continue
        idx = len(rects) - 1
        fx, fy = o['kachel']
        seite = 1 if i % 2 == 0 else -1
        art = i % 3                                                   # abwechseln: Fels hinter den Blaettern / Busch / beides
        if art in (0, 2):                                             # Fels eine Reihe hoeher, seitlich hinter der Krone
            for dx in (3, 4):
                if setze(rnd.choice(['fels_grau', 'steinhaufen']), (fx + seite * dx) * T + 8, (fy - 1) * T + T - 1,
                         {}, seite < 0, kl):
                    break
        if art in (1, 2):                                             # trockener Busch / Gras schraeg vor dem Baum
            for dx in (3, 4, 5):
                if setze('busch_tot' if n == 'totbaum' else 'gras3', (fx - seite * dx) * T + 8, (fy + 1) * T + T - 1,
                         {'ebene': 0}, seite > 0, kl):
                    break
    # ---------------- grosse Einzelobjekte
    for i, (n, tx, ty) in enumerate(GROSS):
        opt = {}
        if n == 'banner':
            opt = {'anim': 'standarte'}
        if n == 'skelett':
            opt = {'liegend': True}
        kachel(n, tx, ty, opt, n in ('skelett',) and i % 2 == 1)
    # Pilze am Teich (Gras)
    for (tx, ty) in ((23, 67), (37, 71)):
        kachel('pilz', tx, ty, {'ebene': 0}, klassen='n')
    # ---------------- sparsame Streudeko (Kleinkram dezent, keine Wiederholung nebeneinander)
    kand = [(x, y) for y in range(2, rows - 2) for x in range(2, cols - 2) if cls[y][x] in BODEN]
    rnd.shuffle(kand)
    n_soll, gesetzt, letzte = 70, 0, None
    for (x, y) in kand:
        if gesetzt >= n_soll:
            break
        nb = [o for o in objekte if abs(o['kachel'][0] - x) < 4 and abs(o['kachel'][1] - y) < 4 and o.get('streu')]
        if nb:
            continue
        wahl = [s for s in STREU if s != letzte]
        n = rnd.choice(wahl)
        lieg = n in ('zweig', 'knochen_k')
        if setze(n, x * T + rnd.randint(4, 12), y * T + rnd.randint(10, 15), {'ebene': 0, 'streu': True, 'liegend': lieg},
                 rnd.random() < 0.5):
            gesetzt += 1; letzte = n
    json.dump(objekte, open(os.path.join(OBJ, 'platzierung.json'), 'w'), indent=0)
    print('Karte 41: %d Objekte (%d Streudeko)' % (len(objekte), gesetzt))


if __name__ == '__main__':
    main()
    import regeln_a02                                                 # Regeln: Teleporter frei
    regeln_a02.objekte_pruefen('karte41', '')
