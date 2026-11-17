"""Objekte fuer Karte 48 - Water Realm: Outer Currents (A03 Nr. 15), Platzierung nach der Vorlage.

  python3 tools/karte48_bauen.py   (einmal -> pixelhoehe.npy, wand.npy, wasser.npy)
  python3 tools/karte48_objekte.py && python3 tools/karte48_bauen.py

Neu mit PixelLab (k48_deko, k48_wasser): Tempelsaeulen, Buecherregale, Lesetisch, umgestuerzte Saeulen, Baenke,
Laternen, Wasserpflanzen, Korallen, Muscheln, Steine. Bibliothek: Regale im festen Rhythmus an der Rueckwand
(symmetrisch zur Raumachse), Lesetisch auf der Achse, Saeulenpaar und Laternenpaar gespiegelt vor der Halle.
Plattformen wie in der Vorlage (Baenke, Saeulen, Saeulenreste - Ruinen-Logik: kaputt am Boden), Wasserpflanzen locker
im Flachwasser (keine Reihen, keine Wiederholung), Kleinkram dezent; nichts auf Treppen und vor Teleportern.
"""
import json, math, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte48')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte48')
T = 16
D = {'saeule': 'deko/00.png', 'regal': 'deko/01.png', 'tisch': 'deko/02.png', 'saeule_kaputt': 'deko/03.png',
     'bank': 'deko/04.png', 'lampe': 'deko/05.png'}
W = {'seegras': 0, 'halme_gelb': 1, 'geroell': 2, 'koralle': 3, 'kiesel': 4, 'seerose': 5, 'koralle_blau': 6,
     'schnecke': 7, 'farn': 10, 'kolben': 12, 'amphore': 13, 'schwamm': 14, 'muschel': 16, 'koralle_lila': 18,
     'mauerrest': 20, 'stumpf': 22, 'sterne': 23, 'steine': 25, 'koralle_rot': 26, 'hirnkoralle': 29,
     'seegras2': 30, 'tafel': 37, 'koralle_orange': 38, 'gras_dicht': 35, 'kraut': 48, 'gelbalge': 50, 'ammonit': 44,
     'muscheln': 62, 'steinbrocken': 46}
for _n, _i in W.items():
    D[_n] = 'wasser/%02d.png' % _i
PFLANZEN = ['seegras', 'halme_gelb', 'farn', 'kolben', 'seegras2', 'gras_dicht', 'kraut', 'gelbalge', 'seerose']
KLEIN = ['koralle', 'koralle_blau', 'schnecke', 'muschel', 'koralle_lila', 'sterne', 'koralle_rot', 'hirnkoralle',
         'koralle_orange', 'schwamm', 'kiesel', 'ammonit', 'muscheln', 'steine']
FLACH = {'seerose', 'sterne', 'kiesel', 'muscheln', 'steine', 'muschel'}


def main():
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cls = lay['klassen']
    cols, rows = lay['groesse']
    lvl = np.load(os.path.join(KARTE, 'pixelhoehe.npy'))
    wand = np.unpackbits(np.load(os.path.join(KARTE, 'wand.npy')))[:lvl.size].reshape(lvl.shape).astype(bool)
    xm = np.unpackbits(np.load(os.path.join(KARTE, 'wasser.npy')))[:lvl.size].reshape(lvl.shape).astype(bool)
    os.makedirs(os.path.join(OBJ, 'varianten'), exist_ok=True)
    k = lambda tx, ty: cls[ty][tx] if 0 <= tx < cols and 0 <= ty < rows else 'x'
    sperr = [(t['x'] * T - 2 * T, t['y'] * T - 2 * T, (t['x'] + t['b'] + 2) * T, (t['y'] + t['h'] + 2) * T)
             for t in lay['teleporter']]
    for (x0, x1, ry, r_) in lay['treppen']:                          # Treppen und ihr Austritt (2 Reihen) frei
        sperr.append((x0 * T - 2, (ry - 2) * T, (x1 + 1) * T + 2, (ry + 3) * T))   # Saeulen duerfen flankieren
    objekte, rects = [], []
    rnd = random.Random(48)

    def schnitt(a, b, d):
        return not (a[2] + d < b[0] or b[2] + d < a[0] or a[3] + d < b[1] or b[3] + d < a[1])

    def setze(name, cx, fy, opt=None, spiegeln=False, ebene_lvl=2, pruefen=True, gap=2):
        """cx: Mitte, fy: unterste Pixelzeile. ebene_lvl: 2 = Plattform/Halle, 1 = Flachwasser."""
        opt = dict(opt or {})
        sp = Image.open(os.path.join(OBJ, D[name])).convert('RGBA')
        if spiegeln:
            sp = sp.transpose(Image.FLIP_LEFT_RIGHT)
        datei = 'varianten/%s%s.png' % (name, '_m' if spiegeln else '')
        sp.save(os.path.join(OBJ, datei))
        bb = sp.getbbox()
        x = int(round(cx - (bb[0] + bb[2]) / 2.0))
        y = int(fy - (bb[3] - 1))
        r = (x + bb[0], y + bb[1], x + bb[2] - 1, y + bb[3] - 1)
        if r[0] < 2 or r[1] < 2 or r[2] >= cols * T - 2 or r[3] >= rows * T - 2:
            return None
        if pruefen:
            if any(schnitt(r, tuple(rr), gap) for rr in rects):
                return None
            if any(schnitt(r, s_, 0) for s_ in sperr):
                return None
            y_ab = r[1] if opt.get('liegend') else max(r[1], r[3] - 2 * T + 1)
            reg = lvl[y_ab:r[3] + 4, max(0, r[0] - 3):r[2] + 4]
            if (reg != ebene_lvl).any() or xm[y_ab:r[3] + 4, max(0, r[0] - 3):r[2] + 4].any():
                return None                                          # untere zwei Reihen ganz auf ihrer Ebene, mit Abstand
            if wand[max(0, r[1]):r[3] + 1, r[0]:r[2] + 1].any() and not opt.get('an_wand'):
                return None
            if ebene_lvl == 1 and (lvl[max(0, r[1]):r[3] - T, r[0]:r[2] + 1] > 1).any():
                return None                                          # Verdeckung: nichts im Wasser vor einer Plattform
        o = {'datei': datei, 'basis': name, 'x': x, 'y': y, 'fuss': bb[3] - 1, 'kachel': [int(cx) // T, int(fy) // T],
             'ebene': 1, 'ohne_wall': True}                          # Steinplatten/Wasser: kein Bodenwall (harte Kanten)
        o.update(opt)
        objekte.append(o)
        rects.append(r)
        return o

    def suche(name, cx, fy, opt=None, spiegeln=False, ebene_lvl=2, r=3, gap=2):
        bb_ = Image.open(os.path.join(OBJ, D[name])).getbbox()       # Regel 1/1b: am 16er-Raster, im Kachelblock zentriert
        wt = max(1, math.ceil((bb_[2] - bb_[0]) / T))
        cx = round((cx - wt * T / 2.0) / T) * T + wt * T / 2.0
        fy = int(fy) // T * T + T - 1
        for d in range(r + 1):
            for dy in range(-d, d + 1):
                for dx in range(-d, d + 1):
                    if max(abs(dx), abs(dy)) != d:
                        continue
                    o = setze(name, cx + dx * T, fy + dy * T, opt, spiegeln, ebene_lvl, gap=gap)
                    if o:
                        return o
        print('  nicht gesetzt:', name, cx // T, fy // T)
        return None

    # ---------------- Bibliothek: Regale im festen Rhythmus an der Rueckwand, Lesetisch auf der Achse
    rx0, ry0, rx1, ry1 = lay['raum']
    achse = (rx0 * T + (rx1 + 1) * T) / 2.0
    fuss_regal = (ry0 + 4) * T + 12                                  # vor der Wandflaeche, Oberkante unter der Mauerabdeckung
    for dx in (-108, -36, 36, 108):
        setze('regal', achse + dx, fuss_regal, {'an_wand': True, 'fest_pos': True}, pruefen=False)
        rects[-1] = (rects[-1][0], rects[-1][1], rects[-1][2], rects[-1][3])
    setze('tisch', achse, (ry0 + 7) * T + 10, {'fest_pos': True}, pruefen=False)
    # Saeulenpaar vor der offenen Halle (wie Vorlage: Saeulen tragen die Front), Laternen an den Plattformecken
    fy_s = (ry1 + 1) * T + 10
    for sx in (-1, 1):
        setze('saeule', achse + sx * 72, fy_s, {'fest_pos': True}, sx > 0, pruefen=False)
    hx0, hy0, hx1, hy1 = lay['halle']
    for sx in (-1, 1):
        cx_ = achse + sx * ((hx1 - hx0 + 1) * T / 2.0 - 22)
        setze('lampe', cx_, (hy1 - 2) * T + 12, {'fest_pos': True}, sx > 0, pruefen=False)
    for sx in (-1, 1):                                               # Baenke unter den Aussenfeldern (gespiegelt)
        setze('bank', achse + sx * 120, (ry1 + 3) * T + 6, {'fest_pos': True}, sx > 0, pruefen=False)
    # ---------------- Plattformen (Positionen der Vorlage, Pixel)
    PLATZ = [('bank', 256, 557), ('bank', 368, 657), ('geroell', 222, 668),            # linke Plattform
             ('saeule', 498, 575), ('saeule_kaputt', 541, 575),                         # kleine Plattform mit Saeule
             ('bank', 704, 543), ('bank', 768, 622), ('steinbrocken', 656, 621),         # mittlere Plattform
             ('saeule_kaputt', 856, 900),                                               # unten Mitte (Ruine)
             ('saeule', 1298, 1040), ('stumpf', 1372, 1040),    # unten rechts
             ('tafel', 1400, 200), ('stumpf', 1440, 120),                                # Teleporter-Plattform oben rechts
             ('saeule_kaputt', 200, 1030), ('mauerrest', 300, 1140), ('amphore', 180, 1180), ('stumpf', 120, 1100), ('tafel', 250, 1190)]  # unten links
    for i, (n, px, py) in enumerate(PLATZ):
        if n == 'saeule' and 1200 < px:                                # Saeulenpaar unten rechts: gemeinsame Fusszeile, ohne Suche
            setze(n, px, py, {}, px > 1340, 2)
            continue
        if n == 'saeule' and px < 600 and setze(n, px, py, {}, False, 2):
            continue                                                   # enge Plattform: Saeule genau an der Westkante
        if n == 'saeule_kaputt' and setze(n, px, py, {'liegend': True}, i % 2 == 1, 2):
            continue                                                   # liegende Saeule: genau zwischen Saeule und Rand
        if not suche(n, px, py, {'liegend': n in ('saeule_kaputt', 'steinbrocken')}, i % 2 == 1, 2, r=4) and n == 'saeule_kaputt':
            suche(n, px, py + 24, {'liegend': True, 'ebene': 0, 'ohne_wall': True}, i % 2 == 1, 1, r=4)   # liegt im Flachwasser
    # ---------------- Flachwasser: Pflanzen an den Plattformecken (Vorlage) und locker verteilt, Kleinkram dezent
    wpos = [(583, 393), (551, 457), (487, 489), (471, 553), (455, 585), (599, 585), (791, 650), (871, 682), (167, 698),
            (775, 919), (919, 919), (1255, 1062), (1223, 1079), (1399, 1030)]
    zug = [0]

    def pflanze(cx, fy, r=3):
        for _ in range(len(PFLANZEN)):
            n = PFLANZEN[zug[0] % len(PFLANZEN)]; zug[0] += 1
            if any(o_['basis'] == n and abs(o_['x'] - cx) < 12 * T and abs(o_['y'] - fy) < 12 * T for o_ in objekte):
                continue
            o = None
            for d in range(r + 1):
                for dy in range(-d, d + 1):
                    for dx in range(-d, d + 1):
                        if max(abs(dx), abs(dy)) == d and not o:
                            o = setze(n, cx + dx * 8, fy + dy * 8, {'ebene': 0, 'wasserdeko': True, 'ohne_wall': True,
                                                                    'nur_kontakt': True, 'anim': 'wehen'}, rnd.random() < 0.5, 1, gap=6)
            if o:
                return o
        return None
    n_p = sum(1 for (px, py) in wpos if pflanze(px, py))
    flach = [(x, y) for y in range(2, rows - 2) for x in range(2, cols - 2) if cls[y][x] == 's']
    rnd.shuffle(flach)
    n_s = 0
    for (x, y) in flach:
        if n_s >= 34:
            break
        if any(o_.get('wasserdeko') and abs(o_['kachel'][0] - x) < 5 and abs(o_['kachel'][1] - y) < 5 for o_ in objekte):
            continue
        if any(abs(o_['kachel'][1] - y) <= 1 and abs(o_['kachel'][0] - x) < 8 for o_ in objekte if o_.get('wasserdeko')):
            continue                                                 # keine Reihen
        if n_s % 3 == 0:
            ok = pflanze(x * T + 8, y * T + 12, r=0)
        else:
            wahl = [n for n in KLEIN if not any(o_['basis'] == n and abs(o_['kachel'][0] - x) < 14 and abs(o_['kachel'][1] - y) < 14
                                                for o_ in objekte)]
            if not wahl:
                continue
            n = rnd.choice(wahl)
            ok = setze(n, x * T + rnd.randint(5, 11), y * T + rnd.randint(9, 14),
                       {'ebene': 0, 'wasserdeko': True, 'ohne_wall': True, 'nur_kontakt': True, 'streu': True,
                        'liegend': n in FLACH}, rnd.random() < 0.5, 1, gap=6)
        if ok:
            n_s += 1
    json.dump(objekte, open(os.path.join(OBJ, 'platzierung.json'), 'w'), indent=0)
    print('Karte 48: %d Objekte (Wasserpflanzen Vorlage %d, Streudeko %d)' % (len(objekte), n_p, n_s))


if __name__ == '__main__':
    main()
    import regeln_a02
    regeln_a02.objekte_pruefen('karte48', 't')
