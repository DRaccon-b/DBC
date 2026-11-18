"""Objekte fuer Karte 42 - Digital World: Wind Valley (A03 Nr. 9), Platzierung nach der Vorlage (verbessert).

  python3 tools/karte42_bauen.py   (einmal -> pixelhoehe.npy, wand.npy)
  python3 tools/karte42_objekte.py && python3 tools/karte42_bauen.py

Wiederverwendet (Regel 3): Akazien, tote Baeume, Felsen, Knochen, Schaedel, Gras, Kiesel, Zweige (Karte 04), Skelett,
Sandsteinfels (Karte 03), Unterstand, Begleiter und Plateau-Deko (PixelLab, Karte 41). Neu (PixelLab k42_dorf): Huette mit
Strohkuppel, Holzbank, Tonkruege. Verbesserungen gegenueber der Vorlage: nichts auf den Wegen (die Huette stand mitten auf
der Windbahn), Baeume mit Begleitern (Regel 5/5d), weniger Kleinkram ohne Reihen/Raster, Deko auch auf dem Felsrand.
"""
import json, math, os, random, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte42')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte42')
T = 16
FREMD = {
    'akazie': 'karte04/baeume/00.png', 'akazie_klein': 'karte04/baeume/03.png', 'totbaum': 'karte04/baeume/02.png',
    'felsen': 'karte42/begleiter/58.png',   # K04-Fels schwebte (Halme unter dem Fuss) -> PixelLab-Fels
    'fels_sand': 'karte03/mittel/07.png', 'fels_grau': 'karte04/mittel/00.png',
    'skelett': 'karte03/mittel/06.png', 'knochen': 'karte04/mittel/08.png', 'schaedel': 'karte04/mittel/09.png',
    'busch_tot': 'karte04/mittel/10.png', 'steinhaufen': 'karte04/mittel/15.png',
    'banner': 'karte03/mittel3/01.png', 'laubbaum': 'karte01/baeume/00.png',
    'gras': 'karte04/klein/14.png', 'gras2': 'karte04/klein/33.png', 'gras3': 'karte04/klein/38.png',   # Nutzer: kein Gras
    'kiesel': 'karte04/klein/02.png', 'zweig': 'karte04/klein/09.png', 'knochen_k': 'karte04/klein/03.png',
    'kristall': 'karte04/klein/05.png', 'pilz': 'karte04/klein/11.png', 'stein': 'karte04/klein/08.png',
    'automat': 'karte42/wueste/00.png', 'saeule': 'karte42/gross/00.png', 'unterstand': 'karte42/gross/02.png',   # groesser (Nutzer)
    'saeule_kaputt': 'karte42/gross/01.png',
    'huette': 'karte42/haus/00.png',   # Nutzer-Vorlage: bemoostes Kuppelhaus
    'bank': 'karte42/dorf/01.png', 'kruege': 'karte42/dorf/02.png',
}
# (Sprite, Kachel-x der Fussmitte, Fusszeile, Ebene) nach der Vorlage; Ebene 1 Talboden, 2 Hochplateau
BAEUME = [('totbaum', 11, 16, 2), ('totbaum', 59, 13, 2), ('totbaum', 79, 18, 2), ('totbaum', 40, 22, 1),
          ('totbaum', 54, 44, 1), ('akazie', 12, 50, 1), ('akazie', 26, 47, 1), ('akazie', 36, 53, 1),
          ('akazie', 74, 42, 1), ('akazie_klein', 81, 57, 1), ('akazie', 57, 64, 1)]
GROSS = [('huette', 17, 35, 1), ('kruege', 21, 36, 1), ('unterstand', 9, 56, 1), ('bank', 13, 57, 1),
         ('skelett', 28, 12, 2), ('skelett', 70, 24, 2), ('skelett', 59, 50, 1), ('skelett', 33, 61, 1),
         ('schaedel', 30, 18, 2), ('schaedel', 70, 54, 1),
         ('fels_sand', 12, 14, 2), ('felsen', 19, 24, 2), ('fels_sand', 61, 12, 2), ('felsen', 77, 21, 2),
         ('fels_sand', 38, 24, 1), ('felsen', 59, 39, 1), ('fels_sand', 36, 56, 1), ('felsen', 68, 58, 1)]
BG_FELS = ['00', '02', '08', '16', '18', '24', '26', '32', '34', '40', '48', '58']   # PixelLab k42_begleiter, 2 Kacheln
BG_BUSCH = ['01', '03', '09', '11', '19', '33', '41', '49', '57']
for _n in BG_FELS + BG_BUSCH:
    FREMD['bg' + _n] = 'karte42/begleiter/%s.png' % _n
PLATEAU_GROSS = ['00', '01', '02', '03', '09', '13', '15']   # ohne toten Baum (pl05: einzeln ohne Begleiter)   # PixelLab k42_plateau (Nutzer: Plateaus zu leer)
for _n in PLATEAU_GROSS:
    FREMD['pl' + _n] = 'karte42/plateau/%s.png' % _n
BERG = ['00', '01', '02', '03', '06', '08', '12', '13', '14']          # PixelLab k42_berg (Bergkette)
RAND = ['00', '01', '02', '03', '05', '09', '13', '15']            # ohne 14 (Schmierfleck im Sprite)          # PixelLab k42_rand (Felsrand)
for _n in BERG:
    FREMD['be' + _n] = 'karte42/berg/%s.png' % _n
for _n in RAND:
    FREMD['ra' + _n] = 'karte42/rand/%s.png' % _n
STREU = ['gras', 'gras2', 'gras3', 'kiesel', 'zweig', 'knochen_k', 'kristall', 'stein']
BODEN = 's'                          # heller Sand: nichts auf Windbahn-Wegen (b) und Pflaster (k)
KL = {1: 's', 2: 'p'}


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
        if not q.startswith('karte42/'):
            shutil.copy(os.path.join(ROOT, 'assets', 'objekte', q), os.path.join(OBJ, 'fremd', n + '.png'))
    pfad = lambda n: os.path.join(ROOT, 'assets', 'objekte', FREMD[n]) if FREMD[n].startswith('karte42/') \
        else os.path.join(OBJ, 'fremd', n + '.png')
    tps = [(t['x'] * T - 2 * T, t['y'] * T - 2 * T, (t['x'] + t['b'] + 2) * T, (t['y'] + t['h'] + 2) * T)
           for t in lay['teleporter']]
    objekte, rects, stumpf = [], [], []
    k = lambda tx, ty: cls[ty][tx] if 0 <= tx < cols and 0 <= ty < rows else 'r'

    def schnitt(a, b, d):
        return not (a[2] + d < b[0] or b[2] + d < a[0] or a[3] + d < b[1] or b[3] + d < a[1])

    def setze(name, cx, fy, opt=None, spiegeln=False, klassen=BODEN, pruefen=True, ohne=(), ebene_soll=1, rand=2 * T):
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
            gap = 2 if (opt or {}).get('streu') else 4                 # Grosses mit etwas mehr Luft (nicht gestapelt)
            if any(schnitt(r, tuple(rr[:4]), gap) for i_, rr in enumerate(rects) if i_ not in ohne):
                return None
            if not (opt or {}).get('begleiter') and any(schnitt(r, z, 0) for z in stumpf):
                return None                                          # Regel 5d: nichts auf Stammhoehe (Sperrzone)
            if any(schnitt(r, t_, 0) for t_ in tps):
                return None
            ty_ = r[3] // T
            if any(k(xx, ty_) not in klassen for xx in range(r[0] // T, r[2] // T + 1)):
                return None
            if any(k(xx // T, yy // T) not in klassen for yy in (r[3] - 6, r[3] + 6) for xx in range(r[0] - 3, r[2] + 4, 4)):
                return None                                          # Fuss und Schatten mit Abstand zu Weg/Pflaster
            if ebene_soll != 1:                                      # Plateau: ganzes Bild mit Rand auf dem Plateau
                y0_, x0_ = max(0, r[1] - 6), max(0, r[0] - 6)
                if (lvl[max(y0_, r[3] - 8):r[3] + rand, x0_:r[2] + 7] != ebene_soll).any():
                    return None                                      # Fuss 2 Reihen von der Kante (Wandregel)
            elif (lvl[r[3] - 3:r[3] + 9, r[0]:r[2] + 1] != 1).any() or wand[r[3] - 3:r[3] + 2, r[0]:r[2] + 1].any():
                return None                                          # Fuss ganz auf dem Wuestenboden, nie an der Wand
            if wasser[max(0, r[1]):r[3] + 1, r[0]:r[2] + 1].any():
                return None                                          # nichts auf Teich oder Ufer
            if ebene_soll == 1 and (lvl[max(0, r[1]):r[3], r[0]:r[2] + 1] > 1).any() and not (opt or {}).get('vor_fels'):
                hoch = lvl[max(0, r[1]):r[3], r[0]:r[2] + 1] > 1     # Verdeckung durch Hoehen: nur Plateau im Norden
                if hoch[:, :].any(axis=0).sum() and hoch[-T:].any():
                    return None
        o = {'datei': datei, 'basis': name, 'x': x, 'y': y, 'fuss': bb[3] - 1, 'kachel': [int(cx) // T, int(fy) // T],
             'ebene': 1}
        o.update(opt or {})
        objekte.append(o)
        rects.append(list(r) + [name])
        return o

    def kachel(name, tx, ty, opt=None, spiegeln=False, klassen=BODEN, suche=4, ebene_soll=1):
        sp = Image.open(pfad(name))
        bw = sp.getbbox()[2] - sp.getbbox()[0]
        wt = max(1, math.ceil(bw / T))
        for d in range(suche + 1):
            for dy in range(-d, d + 1):
                for dx in range(-d, d + 1):
                    if max(abs(dx), abs(dy)) != d:
                        continue
                    x0 = tx + dx - (wt - 1) // 2
                    o = setze(name, x0 * T + wt * T / 2.0, (ty + dy) * T + T - 1, opt, spiegeln, klassen, ebene_soll=ebene_soll)
                    if o:
                        return o
        print('  nicht gesetzt:', name, tx, ty)
        return None

    rnd = random.Random(41)
    # ---------------- Baeume (gross zuerst), Begleiter nach Regel 5/5d
    # Lagerplaetze zuerst (gross, feste Orte: Huette, Unterstand) - sonst sperrt die Stumpfzone der Baeume ihren Platz
    for (n, tx, ty, eb) in [g for g in GROSS if g[0] in ('huette', 'kruege', 'unterstand', 'bank')]:
        kachel(n, tx, ty, {'fuss_dy': 7} if n == 'unterstand' else {}, False, klassen=KL[eb], ebene_soll=eb, suche=8)
    gesetzte_baeume = []
    for i, (n, tx, ty, eb) in enumerate(BAEUME):
        kl = KL[eb]
        o = kachel(n, tx, ty, {'anim': 'baum'} if n != 'totbaum' else {}, i % 2 == 1, kl, ebene_soll=eb)
        if not o:
            continue
        tsp = np.array(Image.open(os.path.join(OBJ, o['datei'])).convert('RGBA'))[..., 3] > 0
        zl = np.nonzero(tsp.any(1))[0][-1]
        sx = o['x'] + int(np.nonzero(tsp[zl - 3:zl + 1].any(0))[0].mean())   # Stammmitte am Fuss
        sy = o['y'] + int(zl)
        stumpf.append((sx - 40, sy - 28, sx + 40, sy + 30))
        gesetzte_baeume.append((i, n, o, kl, len(rects) - 1, sx, sy, eb))
    # ---------------- grosse Einzelobjekte (vor den Begleitern: Grosses zuerst)
    for i, (n, tx, ty, eb) in enumerate(GROSS):
        if n in ('huette', 'kruege', 'unterstand', 'bank'):
            continue
        opt = {}
        if n == 'banner':
            opt = {'anim': 'standarte'}
        if n == 'skelett':
            opt = {'liegend': True}
        if n == 'unterstand':
            opt = {'fuss_dy': 7}                                      # Schatten an der Felsunterkante, nicht an der Stangenspitze
        if n == 'schaedel':
            opt = {'liegend': True}
        kachel(n, tx, ty, opt, n in ('skelett', 'schaedel') and i % 2 == 1, klassen=KL[eb], ebene_soll=eb, suche=8)
    # Begleiter (Regel 5/5d): vor dem Stumpf nur 2 Kacheln hohe Objekte eine Reihe tiefer (oberste Kachel deckt den
    # Stumpf), Fels hinter den Blaettern eine Reihe hoeher, Busch seitlich ausserhalb der Stammzone; abwechselnd, Motive
    # ohne Wiederholung, mind. 2 Begleiter bei einzeln stehenden Baeumen
    felsen_ = BG_FELS[:]; buesche_ = BG_BUSCH[:]
    rnd.shuffle(felsen_); rnd.shuffle(buesche_)
    zug = {'f': 0, 'b': 0}
    def naechster(art):
        liste = felsen_ if art == 'f' else buesche_
        zug[art] += 1
        return 'bg' + liste[zug[art] % len(liste)]
    for (i, n, o, kl, ti, sx, sy, eb) in gesetzte_baeume:
        seite = 1 if i % 2 == 0 else -1
        def vor():
            return any(setze(naechster('f' if i % 2 else 'b'), sx + d, sy + T, {'begleiter': True}, seite < 0, kl,
                             ohne=(ti,), ebene_soll=eb) for d in (0, 3, -3, 6, -6))
        def hinter(sd):
            return any(setze(naechster('f'), sx + sd * d, sy - T, {'begleiter': True}, sd < 0, kl, ohne=(ti,), ebene_soll=eb)
                       for d in (24, 32))
        def seitlich(sd):
            return any(setze(naechster('b'), sx + sd * d, sy + dy, {'begleiter': True, 'ebene': 0}, sd > 0, kl, ebene_soll=eb)
                       for d in (48, 56, 64, 72, 80) for dy in (-T, 2 * T, -2 * T))   # nie in der Stammreihe (keine Reihe Busch-Baum-Busch)
        nah = sum(1 for (_, _, _, _, _, x2, y2, _) in gesetzte_baeume if (x2, y2) != (sx, sy)
                  and abs(x2 - sx) < 6 * T and abs(y2 - sy) < 5 * T)
        soll = 1 if nah else 2
        if n == 'totbaum':                                            # ohne Krone: kein Fels 'hinter den Blaettern'
            plan = [[vor, lambda: seitlich(-seite)], [lambda: seitlich(seite), vor]][i % 2]
            ersatz = [lambda: seitlich(seite), vor]                   # abwechseln (Pruefung: alle gleich aufgebaut)
        else:
            plan = [[vor, lambda: seitlich(-seite)], [vor, lambda: hinter(seite)],
                    [vor, lambda: hinter(-seite)]][i % 3]                 # immer etwas vor dem Stumpf (Einbettung)
            ersatz = [lambda: seitlich(seite), lambda: seitlich(-seite), vor]   # nie zwei 'hinter' (gespiegeltes Paar)
        hat = 0
        for f_ in plan + ersatz:
            if hat >= soll and f_ not in plan:
                break
            if f_():
                hat += 1
        if hat < soll:
            print('  Baum mit zu wenig Begleitern:', n, o['kachel'], hat)
    # Lagerplatz an der Huette und am Unterstand: wenige Dinge, nicht in Reihen (bereits in GROSS)
    # ---------------- Deko auf den Plateaus (Nutzer: zu leer): Felsgruppen, Felsnadeln, Bueschel; locker, ohne Reihen
    pk = [(x, y) for y in range(1, rows - 1) for x in range(1, cols - 1) if cls[y][x] == 'r']
    rnd.shuffle(pk)
    gross_ = ['ra' + n_ for n_ in RAND] + ['pl' + n_ for n_ in ('01', '03')]; rnd.shuffle(gross_)   # Felsrand: neue Motive
    klein_ = [('bg' + n_) for n_ in BG_FELS + BG_BUSCH] + ['gras', 'gras2', 'gras3']
    rnd.shuffle(klein_)
    pl_g, pl_k, gpos, pmotiv = 0, 0, [], []
    breit_ok = lambda x, y: sum(1 for xx in range(x - 5, x + 6) if 0 <= xx < cols and cls[y][xx] == 'r') >= 10 and \
        sum(1 for yy in range(y - 5, y + 6) if 0 <= yy < rows and cls[yy][x] == 'r') >= 8   # keine Reihen auf schmalen Streifen
    for (x, y) in pk:
        if pl_g >= 16:
            break
        if any(abs(x - a_) < 7 and abs(y - b_) < 6 for (a_, b_) in gpos):
            continue
        if not (sum(1 for xx in range(x - 6, x + 7) if 0 <= xx < cols and cls[y][xx] == 'r') >= 11 and
                sum(1 for yy in range(y - 5, y + 6) if 0 <= yy < rows and cls[yy][x] == 'r') >= 9):
            continue                                                  # nur auf breiten Randflaechen (keine Reihen)
        nahe = {m_ for (a_, b_, m_) in pmotiv if abs(x - a_) < 14 and abs(y - b_) < 14}
        frei_ = [m_ for m_ in gross_ if m_ not in nahe]
        if not frei_:
            continue
        n_ = frei_[pl_g % len(frei_)]
        if setze(n_, x * T + 8, y * T + T - 1, {}, rnd.random() < 0.5, 'r', ebene_soll=3):
            pl_g += 1; gpos.append((x, y)); pmotiv.append((x, y, n_))
    for (x, y) in pk[::-1]:
        if pl_k >= 20:
            break
        if any(abs(x - a_) < 4 and abs(y - b_) < 4 for (a_, b_) in gpos):
            continue
        if not breit_ok(x, y):
            continue
        n_ = klein_[pl_k % len(klein_)]
        if setze(n_, x * T + rnd.randint(4, 12), y * T + T - 1, {'streu': True}, rnd.random() < 0.5, 'r', ebene_soll=3):
            pl_k += 1; gpos.append((x, y))
    # Bergkette (Nutzer): Felsnadeln, Felsgruppen und Platten auf dem Kamm, locker verteilt
    mk = [(x, y) for y in range(0, rows - 1) for x in range(1, cols - 1) if cls[y][x] == 'm']
    rnd.shuffle(mk)
    berg_ = ['be' + n_ for n_ in BERG]                       # Bergkette: neue PixelLab-Motive (k42_berg)
    pl_m, mpos = 0, []
    for (x, y) in mk:
        if pl_m >= 13:
            break
        if any(max(abs(x - a_), abs(y - b_)) < 6 or (abs(y - b_) < 2 and abs(x - a_) < 13) for (a_, b_, _) in mpos):
            continue
        if sum(1 for xx in range(x - 4, x + 5) if 0 <= xx < cols and cls[y][xx] == 'm') < 8:
            continue                                                  # schmaler Kettenarm: keine senkrechte Reihe
        frei_ = [m_ for m_ in berg_ if not any(m2 == m_ and abs(x - a_) < 20 and abs(y - b_) < 20 for (a_, b_, m2) in mpos)]
        if not frei_:
            continue
        m_ = frei_[(x * 7 + y * 3) % len(frei_)]
        if setze(m_, x * T + rnd.randint(2, 14), y * T + T - 1, {}, rnd.random() < 0.5, 'm', ebene_soll=4, rand=8):
            pl_m += 1; mpos.append((x, y, m_))
    print('  Plateau: %d grosse, %d kleine Objekte, Bergkette %d' % (pl_g, pl_k, pl_m))
    # ---------------- sparsame Streudeko (Kleinkram dezent, keine Wiederholung, nicht auf Wegen) - Tal und Hochplateaus
    kand = [(x, y, 1 if cls[y][x] == 's' else 2) for y in range(2, rows - 2) for x in range(2, cols - 2) if cls[y][x] in 'sp']
    rnd.shuffle(kand)
    n_soll, gesetzt, letzte = 40, 0, None   # Nutzer: weniger kleine begehbare Objekte
    for (x, y, eb) in kand:
        if gesetzt >= n_soll:
            break
        nb = [o for o in objekte if abs(o['kachel'][0] - x) < 4 and abs(o['kachel'][1] - y) < 4 and o.get('streu')]
        if nb or any(abs(o['kachel'][1] - y) < 1 and abs(o['kachel'][0] - x) < 15 for o in objekte if o.get('streu')) \
                or any(o['kachel'][1] == y and abs(o['kachel'][0] - x) < 6 for o in objekte):
            continue                                                  # keine Reihe mit Begleitern auf derselben Fusszeile
        wahl = [s for s in STREU if s != letzte and not any(o.get('basis') == s and abs(o['kachel'][0] - x) < 13
                                                           and abs(o['kachel'][1] - y) < 13 for o in objekte)]
        if not wahl:
            continue
        n = rnd.choice(wahl)
        lieg = n in ('zweig', 'knochen_k')
        opt_ = {'ebene': 0, 'streu': True, 'liegend': lieg}
        if n == 'kristall':
            opt_['anim'] = 'glitzern'; opt_['glitzer'] = 'cyan'      # Kristalle glitzern selbst (Flaechen schimmern)
        if setze(n, x * T + rnd.randint(4, 12), y * T + rnd.randint(10, 15), opt_,
                 rnd.random() < 0.5, KL[eb], ebene_soll=eb):
            gesetzt += 1; letzte = n
    json.dump(objekte, open(os.path.join(OBJ, 'platzierung.json'), 'w'), indent=0)
    print('Karte 42: %d Objekte (%d Streudeko)' % (len(objekte), gesetzt))


if __name__ == '__main__':
    main()
    import regeln_a02                                                 # Regeln: Teleporter frei
    regeln_a02.objekte_pruefen('karte42', '')
