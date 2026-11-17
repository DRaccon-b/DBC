"""Objekte fuer Karte 52 (D-Reaper: Shinjuku, A03 Nr. 19) -> assets/objekte/karte52/platzierung.json

  python3 tools/karte52_objekte.py && python3 tools/karte52_bauen.py

Sechs Buerogebaeude aus vorhandenen generierten Haelften (Karte 35/36/40), auf die Vorlagenbreite gebracht und gespiegelt,
Eingang auf der Achse. Ruinenstadt unter dem D-Reaper (PixelLab k52_reaper/k52_klein): Panzersperren statt der Vorlagen-X,
ausgebrannte Autowracks, Schutt, umgeknickte Laternen; an den Masserandern Ranken, Blasen, Kapseln und Waechter-Wesen.
Der Ziegelplatz unten rechts bleibt ein Bahnhofsvorplatz (Haltestelle, Automat, Bank, Laternen). Kein Baumguertel:
die Masse umschliesst die Karte (bauen).
"""
import json, math, os, random, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte52')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte52')
T = 16
# name -> (Quelle unter assets/objekte, Skalierung)
FREMD = {'k38/bank': ('karte38/klein/09.png', 1), 'k38/taube': ('karte38/bahn_klein/02.png', 1),
         'k35/tuer_quelle': ('karte35/gross_buero_mitte/00.png', 1),
         'halb/buero_links': ('karte39/gross/buero_links.png', 1), 'halb/buero_unten': ('karte39/gross/buero_unten.png', 1),
         'halb/beige_flach': ('karte36/gross_beige_halb_flach/00.png', 1),
         'halb/glas_mitte': ('karte35/gross_buero_oben_halb/00.png', 1),
         'halb/beige': ('karte40/gross_beige_flach_halb/00.png', 1), 'halb/glas': ('karte40/gross_glas_halb/00.png', 1)}
for i in (0, 1, 5, 7, 12, 13, 18, 34, 41, 44):
    FREMD['k18s/%02d' % i] = ('karte18/strasse/%02d.png' % i, 1)
for i in (0, 1, 2, 3, 5, 6, 7, 12):
    FREMD['k18a/%02d' % i] = ('karte18/autos/%02d.png' % i, 1)
for i in (0, 1, 2, 4, 9, 12, 13, 14, 15):
    FREMD['k01/baum%02d' % i] = ('karte01/baeume/%02d.png' % i, 1)
for n_, (i, f) in {'ranke': (0, 0.55), 'kapsel': (1, 0.5), 'waechter': (2, 0.6), 'sperre': (3, 0.5), 'schutt': (4, 0.6),
                   'block': (5, 0.55), 'wrack': (6, 1.0), 'blasen': (7, 0.5), 'fass': (8, 0.5), 'laterne_kaputt': (9, 0.6),
                   'ei': (12, 0.5)}.items():
    FREMD['reaper/' + n_] = ('karte52/reaper/%02d.png' % i, f)
for n_, i in {'pfuetze': 0, 'brocken': 1, 'glas': 2, 'zeitung': 3}.items():
    FREMD['klein/' + n_] = ('karte52/klein/%02d.png' % i, 0.75)
GANZ = ('halb/buero_links', 'halb/buero_unten')                     # fertige Gebaeude in Vorlagenbreite
WALD = ['k01/baum%02d' % i for i in (0, 1, 2, 4, 9, 15)]
BUSCH = ['k01/baum%02d' % i for i in (12, 13, 14)]
LAMPE = {'anim': 'leuchten', 'licht': [4, 7], 'licht_box': [2, 5, 6, 10], 'licht_r': 9}
# Gebaeude: Flaeche aus dem Layout, Haelfte, Fassade
GEB = {'oben_links': 'halb/buero_links', 'beige_links': 'halb/beige', 'glas_mitte': 'halb/glas_mitte',
       'glas_rechts': 'halb/glas', 'beige_rechts': 'halb/beige_flach', 'lila_unten': 'halb/buero_unten'}


def kopieren(name, quelle, f):
    ziel = os.path.join(OBJ, name + '.png')
    os.makedirs(os.path.dirname(ziel), exist_ok=True)
    im = Image.open(os.path.join(ROOT, 'assets', 'objekte', quelle)).convert('RGBA')
    im = im.crop(im.getbbox())
    if f != 1:
        im = im.resize((max(1, round(im.width * f)), max(1, round(im.height * f))), Image.NEAREST)
    im.save(ziel)


def verbreitern(quelle, ziel, breite_halb):
    """Haelfte auf breite_halb verbreitern: ein Fassadenfeld (Periode der Fensterachsen) innen wiederholen."""
    im = Image.open(os.path.join(OBJ, quelle)).convert('RGBA')
    im = im.crop(im.getbbox())
    a = np.array(im).astype(int)
    h, w = a.shape[:2]
    if w >= breite_halb + 4:
        im.save(os.path.join(OBJ, ziel)); return
    fass = a[int(h * 0.3):int(h * 0.85), :, :3]
    rosa = (a[..., 3] > 0) & (a[..., 0] > 170) & (a[..., 1] < 120) & (a[..., 2] > 100)   # Tueren nie zerschneiden
    tuer = rosa[h - 40:].any(0)
    tuer = np.convolve(tuer.astype(int), np.ones(9), 'same') > 0
    best, bp, x0 = 1e9, 16, int(w * 0.35)
    for x0_ in range(int(w * 0.25), int(w * 0.8)):
        for p in range(10, min(80, (w - x0_) // 2)):
            if tuer[x0_:x0_ + 2 * p].any():
                continue
            e = np.abs(fass[:, x0_:x0_ + p] - fass[:, x0_ + p:x0_ + 2 * p]).mean() + 0.01 * p
            if e < best - 0.5:
                best, bp, x0 = e, p, x0_
    seg = a[:, x0:x0 + bp]
    n = math.ceil((breite_halb + 4 - w) / bp)
    neu = np.concatenate([a[:, :x0]] + [seg] * (n + 1) + [a[:, x0 + bp:]], 1)
    Image.fromarray(neu.astype(np.uint8)).save(os.path.join(OBJ, ziel))


def tuer_einsetzen(ziel):
    """Glastuer mit Vordach mittig am Boden einsetzen (Tuer reicht bis zur Fusskante), fehlenden Sockel ergaenzen."""
    im = Image.open(os.path.join(OBJ, ziel)).convert('RGBA')
    a = np.array(im)
    h, w = a.shape[:2]
    if a[-1, :, :3].astype(int).sum(-1)[a[-1, :, 3] > 0].mean() > 150:     # unten beschnitten: Sockel + Kontur anfuegen
        neu = np.zeros((h + 3, w, 4), np.uint8); neu[:h] = a
        deck = a[-1, :, 3] > 0
        neu[h:h + 2, deck] = (120, 120, 128, 255)
        neu[h + 2, deck] = (36, 36, 44, 255)
        a, h = neu, h + 3
    ai = a.astype(int)                                                    # lila Freistell-Saum im Sockel -> Sockelgrau
    saum = (ai[..., 3] > 0) & (ai[..., 2] > ai[..., 0]) & (ai[..., 0] - ai[..., 1] > 35)
    saum[:h - 10] = False
    a[saum, :3] = (120, 120, 128)
    if (a[0, :, 3] > 0).mean() > 0.3 and a[0, :, :3].astype(int).sum(-1)[a[0, :, 3] > 0].mean() > 200:   # Dach oben beschnitten
        neu = np.zeros((h + 2, w, 4), np.uint8); neu[2:] = a
        deck = a[0, :, 3] > 0
        neu[0, deck] = (40, 40, 48, 255); neu[1, deck] = (150, 146, 140, 255)
        a, h = neu, h + 2
    im = Image.fromarray(a)
    t = Image.open(os.path.join(OBJ, 'gross_buero_mitte/00.png')).convert('RGBA').crop((170, 136, 248, 180))
    t = t.crop(t.getbbox())
    im.alpha_composite(t, (w // 2 - t.width // 2, h - t.height))
    im.save(os.path.join(OBJ, ziel))


def main():
    rnd = random.Random(53)
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cls = lay['klassen']
    cols, rows = lay['groesse']
    P = lay['versatz']
    OFF = P * T

    def k(tx, ty):
        return cls[min(rows - 1, max(0, ty))][min(cols - 1, max(0, tx))]

    for name, (quelle, f) in FREMD.items():
        kopieren(name, quelle, f)
    os.makedirs(os.path.join(OBJ, 'gross_buero_mitte'), exist_ok=True)
    shutil.copy(os.path.join(OBJ, 'k35/tuer_quelle.png'), os.path.join(OBJ, 'gross_buero_mitte/00.png'))
    import karte36_objekte as k36o
    k36o.OBJ = OBJ
    for n_, (x0, y0, x1, y1) in lay['gebaeude_flaechen'].items():
        bh = (x1 - x0 + 1) * T // 2
        if GEB[n_] in GANZ:
            os.makedirs(os.path.join(OBJ, 'geb'), exist_ok=True)
            shutil.copy(os.path.join(OBJ, GEB[n_] + '.png'), os.path.join(OBJ, 'geb/%s.png' % n_))
            continue
        verbreitern(GEB[n_] + '.png', 'halb/%s_breit.png' % n_, bh)
        k36o.halb_gespiegelt('halb/%s_breit.png' % n_, 'geb/%s.png' % n_, bh, False)
        tuer_einsetzen('geb/%s.png' % n_)
        im = Image.open(os.path.join(OBJ, 'geb/%s.png' % n_)).convert('RGBA')
        im.crop(im.getbbox()).save(os.path.join(OBJ, 'geb/%s.png' % n_))
    tps = [(t['x'] * T - 2 * T, t['y'] * T - 2 * T, (t['x'] + t['b'] + 2) * T, (t['y'] + t['h'] + 2) * T)
           for t in lay['teleporter']]
    tps_eng = [(t['x'] * T, t['y'] * T, (t['x'] + t['b']) * T - 1, (t['y'] + t['h']) * T - 1) for t in lay['teleporter']]
    objekte, rects = [], []

    def schnitt(a, b, rand=0):
        return not (a[2] + rand < b[0] or b[2] + rand < a[0] or a[3] + rand < b[1] or b[3] + rand < a[1])

    def setze(name, cx, fy, opt=None, spiegeln=False, art='objekt', pruefen=True, klassen='k'):
        if not os.path.exists(os.path.join(OBJ, name + '.png')):
            print('fehlt:', name); return None
        sp = Image.open(os.path.join(OBJ, name + '.png')).convert('RGBA')
        if spiegeln:
            sp = sp.transpose(Image.FLIP_LEFT_RIGHT)
        datei = 'varianten/%s%s.png' % (name.replace('/', '-'), '_m' if spiegeln else '')
        os.makedirs(os.path.join(OBJ, 'varianten'), exist_ok=True)
        sp.save(os.path.join(OBJ, datei))
        bb = sp.getbbox()
        x = int(round(cx - (bb[0] + bb[2]) / 2.0))
        y = int(fy - (bb[3] - 1))
        r = (x + bb[0], y + bb[1], x + bb[2] - 1, y + bb[3] - 1)
        if art == 'wald':
            if any(schnitt(r, t_, 3) for t_ in tps_eng):
                return None
            for yy in range(max(0, r[1] // T), min(rows - 1, r[3] // T) + 1):
                for xx in range(max(0, r[0] // T), min(cols - 1, r[2] // T) + 1):
                    if cls[yy][xx] != 'h':
                        ov_y = min(r[3], yy * T + T - 1) - max(r[1], yy * T) + 1
                        ov_x = min(r[2], xx * T + T - 1) - max(r[0], xx * T) + 1
                        if ov_y > 4 and ov_x > 4 and not (yy * T >= r[1] and r[3] - yy * T > 40 and False):
                            return None
            if any(art2 not in ('wald',) and schnitt(r, tuple(rr), 2) for (*rr, art2) in rects):
                return None
        elif pruefen:
            if art not in ('gebaeude', 'auto') and any(abs(o2['y'] + o2['fuss'] - r[3]) <= 6 and
                                                       o2['x'] - 40 < r[2] and r[0] < o2['x'] + 72 for o2 in objekte
                                                       if not o2.get('gebaeude') and not o2.get('liegend')):
                return None                                                # keine Reihe auf derselben Fusszeile
            fuss_r = (r[0], max(r[1], r[3] - T + 1), r[2], r[3])           # vor Gebaeuden zaehlt nur der Fuss
            if any(schnitt(fuss_r, tuple(rr), -1) if (art2 == 'gebaeude' and klassen == 'n') else schnitt(r, tuple(rr), 2) for (*rr, art2) in rects) or \
                    any(schnitt(r, t_, 0) for t_ in tps):
                return None
            # ganzes Bildrechteck auf erlaubtem Boden (untere zwei Reihen; liegende ganz) - Pruefliste K44
            ry0 = r[1] // T if (opt or {}).get('liegend') else max(r[1] // T, r[3] // T - 1)
            belag = {k(xx, yy) for yy in range(ry0, r[3] // T + 1) for xx in range(r[0] // T, r[2] // T + 1)}
            if not belag <= set(klassen) or (len(belag) > 1 and art not in ('gebaeude', 'auto')):
                return None                                                # nie halb auf Gehweg/Platzkante
        o = {'datei': datei, 'basis': name, 'x': x, 'y': y, 'fuss': bb[3] - 1, 'kachel': [int(cx) // T, int(fy) // T],
             'ebene': 1, 'ohne_wall': True}
        if art != 'wald' and not (opt or {}).get('liegend'):
            o['nur_kontakt'] = True
        o.update(opt or {})
        objekte.append(o)
        rects.append(list(r) + [art])
        return o

    def kachel(name, tx, fy_tile, opt=None, spiegeln=False, klassen='k', weit=3):
        sp = Image.open(os.path.join(OBJ, name + '.png'))
        bw = sp.getbbox()[2] - sp.getbbox()[0]
        wt = max(1, math.ceil(bw / T))
        for d in range(weit + 1):
            for dy in range(-d, d + 1):
                for dx in range(-d, d + 1):
                    if max(abs(dx), abs(dy)) != d:
                        continue
                    x0, y = tx + dx - (wt - 1) // 2, fy_tile + dy
                    o = setze(name, x0 * T + wt * T / 2.0, y * T + T - 1, opt, spiegeln, klassen=klassen)
                    if o:
                        return o
        print('nicht gesetzt:', name, tx - P, fy_tile - P)
        return None

    # ---------------------------------------------------------------- Gebaeude (zuerst)
    for n_, (x0, y0, x1, y1) in lay['gebaeude_flaechen'].items():
        if not setze('geb/' + n_, (x0 + x1 + 1) * T / 2.0, (y1 + 1) * T - 1, {'gebaeude': True, 'vorplatz': True},
                     art='gebaeude', pruefen=False):
            print('Gebaeude nicht gesetzt:', n_)
    G = 'kqb'                                                          # begehbarer Belag fuer Deko
    # ---------------------------------------------------------------- Wracks und Sperren (Vorlage: Autos, X-Sperren)
    for (n_, tx, ty, sp) in (('k18a/03', 13, 29, False), ('k18a/01', 47, 39, True), ('k18a/03', 77, 40, True),
                             ('k18a/01', 28, 74, False), ('k18a/02', 60, 38, False), ('k18a/05', 14, 68, True)):   # verlassene Autos (Seitenansicht)
        kachel(n_, tx + P, ty + P, {}, sp, klassen='a', weit=2)
    for (n_, tx, ty, sp) in (('reaper/sperre', 21, 28, False), ('reaper/sperre', 31, 23, True), ('reaper/sperre', 55, 46, False),
                             ('reaper/sperre', 59, 58, True), ('reaper/block', 14, 20, False), ('reaper/block', 66, 63, True),
                             ('reaper/schutt', 36, 20, False), ('reaper/schutt', 13, 55, True), ('reaper/schutt', 70, 25, False),
                             ('reaper/fass', 25, 16, False), ('reaper/laterne_kaputt', 33, 66, False),
                             ('reaper/laterne_kaputt', 80, 52, True)):
        kachel(n_, tx + P, ty + P, {'anim': 'lampe', 'lampe_box': [8, 0, 29, 9], 'licht_farbe': [255, 210, 120]} if 'laterne_kaputt' in n_ else {}, sp, klassen='a' + G, weit=2)
    # ---------------------------------------------------------------- Bahnhofsvorplatz (Ziegelplatz unten rechts)
    gk_ = np.array([list(z) for z in cls])                              # Laternen an den Platzecken, exakt gespiegelt
    ys_b, xs_b = np.nonzero(gk_ == 'b')
    bx0, bx1, by0, by1 = xs_b.min(), xs_b.max(), ys_b.min(), ys_b.max()
    lw = Image.open(os.path.join(OBJ, 'k18s/18.png')).getbbox()
    lw = lw[2] - lw[0]
    xl = bx0 * T + 20
    for fy_ in ((by0 + 1) * T + 15, by1 * T + 11):
        setze('k18s/18', xl + lw / 2.0, fy_, dict(LAMPE), klassen='b')
        setze('k18s/18', (bx1 + 1) * T - 20 - lw / 2.0, fy_, dict(LAMPE), klassen='b')
    for (n_, tx, ty, sp) in (('k18s/13', 80, 62, False), ('k18s/01', 88, 61, False), ('k18s/12', 84, 70, False)):
        kachel(n_, tx + P, ty + P, {}, sp, klassen='b', weit=2)
    kachel('k18s/41', 80 + P, 74 + P, {}, klassen='b', weit=3)             # Haltestelle (Vorlage) auf dem Vorplatz
    for (tx, ty) in ((18, 12), (40, 46), (60, 45), (22, 76 - 1)):
        kachel('k18s/18', tx + P, ty + P, dict(LAMPE), klassen='k', weit=2)
    # ---------------------------------------------------------------- D-Reaper: Auslaeufer an den Masseraendern
    gk = np.array([list(z) for z in cls])
    masse = np.isin(gk, ['r', 'h'])
    rand_k = []
    for ty in range(P + 3, rows - P - 3):
        for tx in range(P + 3, cols - P - 3):
            if gk[ty, tx] in 'akqb' and masse[ty - 1:ty + 2, tx - 1:tx + 2].any() and gk[ty, tx] != 'e' \
                    and not masse[ty, tx]:
                rand_k.append((tx, ty))
    rnd.shuffle(rand_k)
    motive = ['reaper/ranke', 'reaper/blasen', 'reaper/kapsel', 'reaper/ei', 'reaper/ranke', 'reaper/blasen']
    gesetzt_r = []
    for (tx, ty) in rand_k:
        if len(gesetzt_r) >= 26:
            break
        if any(abs(tx - x_) + abs(ty - y_) < 7 for (x_, y_) in gesetzt_r):
            continue
        n_ = motive[len(gesetzt_r) % len(motive)]
        bw_ = (lambda b: b[2] - b[0])(Image.open(os.path.join(OBJ, n_ + '.png')).getbbox())
        wt_ = max(1, math.ceil(bw_ / T))                                   # Regel 1b: mittig im Kachelblock
        if setze(n_, (tx - (wt_ - 1) // 2) * T + wt_ * T / 2.0, ty * T + T - 1, {}, rnd.random() < 0.5, klassen='a' + G):
            gesetzt_r.append((tx, ty))
    for (tx, ty) in ((30, 20), (62, 44), (52, 30 + 10), (12, 22), (86, 48)):   # Waechter-Wesen patrouillieren
        kachel('reaper/waechter', tx + P, ty + P, {}, (tx // 2) % 2 == 0, klassen='a' + G, weit=3)
    # ---------------------------------------------------------------- flacher Kleinkram (begehbar)
    klein = ['klein/pfuetze', 'klein/brocken', 'klein/glas', 'klein/zeitung']
    for i in range(40):
        tx, ty = rnd.randint(P + 3, cols - P - 4), rnd.randint(P + 3, rows - P - 4)
        if gk[ty, tx] in 'akq':
            setze(klein[i % 4], tx * T + rnd.randint(3, 13), ty * T + rnd.randint(8, 15), {'ebene': 0, 'liegend': True,
                  'schattenlos': True}, rnd.random() < 0.5, klassen='akqb')
    for o in objekte:
        if o['basis'].startswith('k01/'):
            o['nur_kontakt'] = True
    json.dump(objekte, open(os.path.join(OBJ, 'platzierung.json'), 'w'), indent=0)
    print(len(objekte), 'Objekte')


if __name__ == '__main__':
    main()
    import regeln_a02
    regeln_a02.objekte_pruefen('karte52', '')
