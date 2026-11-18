"""Objekte fuer Karte 53 (Shinjuku Evacuation District, A03 Nr. 20) -> assets/objekte/karte53/platzierung.json

  python3 tools/karte53_objekte.py && python3 tools/karte53_bauen.py

Sechs Buerobloecke aus vorhandenen generierten Haelften (Karte 35/36/40), auf die Vorlagenbreite verbreitert (Fassadenfeld
wiederholt) und gespiegelt, Eingang auf der Achse. Baeume mittig auf den Beeten (Tuerluecken frei), verlassene Busse und
Autos im Linksverkehr, Bushaltestellen. Evakuierung (PixelLab, Gruppe k53_evak/k53_gross): Hilfslager mit Zelt, Feldbetten,
Vorraeten und Wasserspender, Sanitaetsposten mit Generator und Flutlicht, Sandsack- und Barrierensperren, liegengebliebenes
Gepaeck; D-Reaper-Auslaeufer (Ranken, Blasen) nur direkt an den roten Flecken. Ringsum Baumguertel.
"""
import json, math, os, random, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageFilter

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte53')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte53')
T = 16
# name -> (Quelle unter assets/objekte, Skalierung)
FREMD = {'k38/bank': ('karte38/klein/09.png', 1), 'k38/taube': ('karte38/bahn_klein/02.png', 1),
         'k35/tuer_quelle': ('karte35/gross_buero_mitte/00.png', 1),
         'halb/glas_gross': ('karte35/gross_buero_unten_halb/00.png', 1),
         'halb/glas_mitte': ('karte35/gross_buero_oben_halb/00.png', 1),
         'halb/beige': ('karte36/gross_beige_halb_hoch/00.png', 1),
         'halb/lila': ('karte40/gross_lila_halb/00.png', 1), 'halb/glas': ('karte40/gross_glas_halb/00.png', 1)}
for i in (0, 1, 5, 7, 12, 13, 18, 34, 41, 44):
    FREMD['k18s/%02d' % i] = ('karte18/strasse/%02d.png' % i, 1)
for i in (0, 2, 5, 6, 7, 12):
    FREMD['k18a/%02d' % i] = ('karte18/autos/%02d.png' % i, 1)
for i in (0, 1, 2, 4, 9, 12, 13, 14, 15):
    FREMD['k01/baum%02d' % i] = ('karte01/baeume/%02d.png' % i, 1)
EVAK = {'bett': (0, 0.5), 'sandsack': (1, 0.6), 'gepaeck': (2, 0.5), 'schild': (3, 0.55), 'kisten': (4, 0.5),
        'flutlicht': (5, 0.65), 'kegel': (6, 0.5), 'tisch': (7, 0.5), 'generator': (8, 0.55), 'wasser': (9, 0.5),
        'sperre': (12, 0.5), 'kocher': (14, 0.5), 'rucksack': (15, 0.45)}
for n_, (i, f) in EVAK.items():
    FREMD['evak/' + n_] = ('karte53/evak/%02d.png' % i, f)
FREMD['evak/bett'] = ('karte53/bett/00.png', 0.7)                       # Feldbett in Draufsicht (Pruefung: frontal)
FREMD['evak/kanister'] = ('karte53/bett/12.png', 0.5)
FREMD['evak/kuehlbox'] = ('karte53/bett/07.png', 0.5)
FREMD['evak/schlafsack'] = ('karte53/bett/09.png', 0.6)
for n_, (i, f) in {'zelt': (0, 0.75), 'lkw': (1, 0.75), 'vorrat': (2, 0.6)}.items():
    FREMD['evak/' + n_] = ('karte53/gross/%02d.png' % i, f)
for n_, (i, f) in {'ranke': ('07', 0.6), 'blasen': ('04b', 0.7), 'kapsel': ('11', 0.55)}.items():   # D-Reaper wie im Anime
    FREMD['reaper/' + n_] = ('karte52/anime/%s.png' % i, f)
# Nutzer (Karte 52): nie herunterskalieren -> Evakuierungs-Kleinkram neu in Zielgroesse (PixelLab k53_n32/n48/n48b),
# grosse Objekte (Zelt, LKW, Vorraete) frontal in Originalgroesse, D-Reaper-Auslaeufer und Stadtmobiliar wie Karte 52
NEU = {'evak/bett': 'karte53/n48/00.png', 'evak/sandsack': 'karte53/n48/01.png', 'evak/gepaeck': 'karte53/n48/02.png',
       'evak/schild': 'karte53/n48/03.png', 'evak/kisten': 'karte53/n48/04.png', 'evak/flutlicht': 'karte53/n48/05.png',
       'evak/tisch': 'karte53/n48/06.png', 'evak/generator': 'karte53/n32/40.png', 'evak/kegel': 'karte53/n48b/02.png',
       'evak/wasser': 'karte53/n48b/00.png', 'evak/sperre': 'karte53/n48b/01.png', 'evak/kocher': 'karte53/n32/04.png',
       'evak/rucksack': 'karte53/n32/03.png', 'evak/kanister': 'karte53/n32/00.png', 'evak/kuehlbox': 'karte53/n32/01.png',
       'evak/schlafsack': 'karte53/n32/02.png', 'evak/zelt': 'karte53/gross/00.png', 'evak/lkw': 'karte53/gross/01.png',
       'evak/vorrat': 'karte53/gross/02.png',
       'reaper/ranke': 'karte52/n48/06.png', 'reaper/blasen': 'karte52/n48b/06.png', 'reaper/kapsel': 'karte52/n48b/02.png',
       'k18s/18': 'karte52/n48/00.png', 'k18s/13': 'karte52/n32/06.png', 'k18s/01': 'karte53/fix/automat.png',   # roter Fleck am Fuss entfernt (Pruefung)
       'k18s/12': 'karte52/n32/05.png', 'k18s/41': 'karte52/n48b/05.png',
       'k18a/02': 'karte52/n64/02.png', 'k18a/05': 'karte52/n64/03.png'}
for n_, q in NEU.items():
    FREMD[n_] = (q, 1)
assert all(f == 1 for (_, f) in FREMD.values())                         # nie herunterskalieren
WALD = ['k01/baum%02d' % i for i in (0, 1, 2, 4, 9, 15)]
BUSCH = ['k01/baum%02d' % i for i in (12, 13, 14)]
LAMPE = {'anim': 'lampe'}                                       # grosse PixelLab-Laterne (Karte 52): Glaskopf leuchtet
# Gebaeude: Flaeche aus dem Layout, Haelfte, Fassade
GEB = {'glas_gross': 'halb/glas_gross', 'glas_mitte': 'halb/glas_mitte', 'beige': 'halb/beige',
       'lila_rechts': 'halb/lila', 'lila_links': 'halb/lila', 'glas_zentrum': 'halb/glas'}


def kopieren(name, quelle, f):
    ziel = os.path.join(OBJ, name + '.png')
    os.makedirs(os.path.dirname(ziel), exist_ok=True)
    im = Image.open(os.path.join(ROOT, 'assets', 'objekte', quelle)).convert('RGBA')
    im = im.crop(im.getbbox())
    if f != 1:
        raise ValueError('nie herunterskalieren: %s' % name)
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


TUEREN_BLAU = {'geb/beige': [(106, 136), (215, 245)]}                 # Spritespalten der Seitentueren


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
    for xr in (0, a.shape[1] - 1):                                       # helle Dachkanten am Bildrand: Kontur
        hell = (a[:, xr, 3] > 0) & (a[:, xr, :3].astype(int).sum(-1) > 450)
        a[hell, xr, :3] = (40, 40, 48)
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

    # D-Reaper-Masse (Klasse 'r'): Blasen ragen bis 3 px ueber ihre Kacheln -> Objekte halten 6 px Abstand (Pruefung)
    masse = np.kron(np.array([[c_ == 'r' for c_ in z] for z in cls]), np.ones((T, T), bool))
    masse_d = np.array(Image.fromarray(masse.astype(np.uint8) * 255).filter(ImageFilter.MaxFilter(13))) > 0

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
            fuss_r = (r[0], max(r[1], r[3] - T + 1), r[2], r[3])           # vor Gebaeuden zaehlt nur der Fuss
            if any(schnitt(fuss_r, tuple(rr), 1) if (art2 == 'gebaeude' and klassen == 'n') else schnitt(r, tuple(rr), 2) for (*rr, art2) in rects) or \
                    any(schnitt(r, t_, 0) for t_ in tps):
                return None
            if not name.startswith('reaper/') and masse_d[max(0, r[1]):r[3] + 1, max(0, r[0]):r[2] + 1].any():
                return None
            # ganzes Bildrechteck auf erlaubtem Boden (untere zwei Reihen; liegende ganz) - Pruefliste K44
            ry0 = r[1] // T if (opt or {}).get('liegend') else max(r[1] // T, r[3] // T - 1)
            belag = {k(xx, yy) for yy in range(ry0, r[3] // T + 1) for xx in range(r[0] // T, r[2] // T + 1)}
            if not belag <= set(klassen):
                return None
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
    # Seitentueren (rosa Ladentueren) der gesetzten Gebaeude: Beet davor wird Gehweg (Eingaenge frei, Pruefliste K35)
    zeilen = [list(z) for z in cls]
    for o in [o for o in objekte if o['basis'].startswith('geb/')]:
        sp_ = np.array(Image.open(os.path.join(OBJ, o['datei'])).convert('RGBA')).astype(int)
        u = sp_[-24:]
        rosa = (u[..., 3] > 0) & (u[..., 0] > 170) & (u[..., 1] < 120) & (u[..., 2] > 100)
        spalten = list(np.nonzero(rosa.sum(0) >= 3)[0])
        for (a0, a1) in TUEREN_BLAU.get(o['basis'], []):                  # blaue Ladentueren (beige Block)
            spalten += list(range(a0, a1 + 1))
        if not len(spalten):
            continue
        fy_ = (o['y'] + o['fuss']) // T
        tx_ = sorted({(o['x'] + c) // T for c in spalten})
        for tx in tx_:
            for ty in range(fy_ + 1, fy_ + 5):
                if 0 <= ty < rows and zeilen[ty][tx] == 'n':
                    zeilen[ty][tx] = 'k'
    import karte43_layout as k43_
    k43_.R, k43_.C = rows, cols
    zz = np.array(zeilen)
    for teil in k43_.flaechen(zz == 'n'):                                   # Beetreste unter 6 Kacheln -> Gehweg
        if len(teil) < 6:
            for (y, x) in teil:
                zeilen[y][x] = 'k'
    cls = [''.join(z) for z in zeilen]
    lay['klassen'] = cls
    json.dump(lay, open(os.path.join(KARTE, 'layout.json'), 'w'), indent=0)
    # ---------------------------------------------------------------- Baeume auf den Beeten (Stamm auf der Beetmitte)
    gk = np.array([list(z) for z in cls])
    import karte43_layout as k43
    k43.R, k43.C = rows, cols
    beete = [t_ for t_ in k43.flaechen(gk == 'n')]
    arten = ['k01/baum00', 'k01/baum02', 'k01/baum01', 'k01/baum04']
    hw_ = {a_: (lambda b: (b[2] - b[0]) / 2.0 + 1)(Image.open(os.path.join(OBJ, a_ + '.png')).getbbox()) for a_ in arten}
    gebs = [rr for rr in rects if rr[4] == 'gebaeude']
    info = []
    for teil in beete:
        ys_ = [p_[0] for p_ in teil]; xs_ = [p_[1] for p_ in teil]
        y0, y1, x0, x1 = min(ys_), max(ys_), min(xs_), max(xs_)
        if y0 < P or y1 >= rows - P:
            continue
        gi = next((i for i, g in enumerate(gebs) if g[0] <= (x0 + x1 + 1) * T / 2.0 <= g[2]
                   and 0 <= y0 * T - g[3] <= 3 * T), None)              # Beetmitte vor der Fassade
        info.append((y0, y1, x0, x1, gi))
    nb = 0
    erledigt = set()
    # Beete vor einem Gebaeude: Baumpaare exakt gespiegelt zur Gebaeude-/Tuerachse, Stammfuss auf der Beetmitte (Pruefung)
    for gi, g in enumerate(gebs):
        teile = [t_ for t_ in info if t_[4] == gi]
        achse = (g[0] + g[2] + 1) / 2.0
        li = [t_ for t_ in teile if (t_[2] + t_[3] + 1) * T / 2.0 < achse]
        re = [t_ for t_ in teile if (t_[2] + t_[3] + 1) * T / 2.0 > achse]
        if not li or not re:
            continue
        L = max(li, key=lambda t_: t_[3] - t_[2]); R = max(re, key=lambda t_: t_[3] - t_[2])
        art_ = arten[nb % len(arten)]; hw = hw_[art_]
        d0 = max(achse - ((L[3] + 1) * T - hw), (R[2] * T + hw) - achse)       # beide Fuesse im Beet
        d1 = min(achse - (L[2] * T + hw), ((R[3] + 1) * T - hw) - achse)
        if d1 < d0:
            continue
        fy = L[0] * T + (L[1] - L[0] + 1) * T // 2 + 3
        ds = [(d0 + d1) / 2.0] if d1 - d0 < 6 * T else [d0 + (d1 - d0) * 0.2, d0 + (d1 - d0) * 0.8]
        for j, d in enumerate(ds):
            a_ = arten[(nb + j) % len(arten)]
            for dd in (0, 8, -8, 16, -16):
                n0 = len(objekte)
                if setze(a_, achse - d - dd, fy, {'anim': 'baum'}, False, klassen='n') and \
                        setze(a_, achse + d + dd, fy, {'anim': 'baum'}, True, klassen='n'):
                    break
                del objekte[n0:]; del rects[n0:]
        nb += len(ds)
        erledigt.update([L, R])
    for (y0, y1, x0, x1, gi) in info:
        if (y0, y1, x0, x1, gi) in erledigt:
            continue
        fy = y0 * T + (y1 - y0 + 1) * T // 2 + 3
        breite = x1 - x0 + 1
        anteile = (0.5,) if breite < 9 else (0.2, 0.8) if breite < 18 else (0.12, 0.45, 0.88)
        for j, f in enumerate(anteile):
            art_ = arten[(nb + j) % len(arten)]
            hw = hw_[art_]
            cx = min(max(x0 * T + f * breite * T, x0 * T + hw), (x1 + 1) * T - hw)
            for dx in (0, -16, 16, -32, 32):
                if setze(art_, cx + dx, fy, {'anim': 'baum'}, (nb + j) % 2 == 1, klassen='n'):
                    break
        nb += len(anteile)
    # ---------------------------------------------------------------- Fahrzeuge (verlassen, Linksverkehr)
    oben_y, unten_y = (56 + P) * T + 4, (59 + P) * T + 6                  # Hauptstrasse: Nordspur nach Osten, Suedspur nach Westen
    for (n_, x_, y_, sp) in (('k18a/12', 14, oben_y, True), ('k18a/12', 79, oben_y, True), ('k18a/02', 22, unten_y, False),
                             ('k18a/05', 48, oben_y, True), ('k18a/00', 58, unten_y, False)):
        setze(n_, (x_ + P) * T, y_, {}, sp, art='auto', klassen='a')
    setze('k18a/06', (32 + P) * T + 24, (43 + P) * T, {}, False, art='auto', klassen='a')   # Nord-Sued: Ostspur nach Sueden (Front unten)
    setze('k18a/06', (89 + P) * T + 24, (70 + P) * T, {}, False, art='auto', klassen='a')
    setze('evak/lkw', (46 + P) * T, (28 + P) * T + 8, {}, False, art='auto', klassen='a')  # Militaer-LKW an der Querstrasse
    # ---------------------------------------------------------------- Strassenmoebel
    for (tx, ty) in ((5, 51), (73, 51)):                                 # Bushaltestellen an der Hauptstrasse
        kachel('k18s/41', tx + P, ty + P, {}, weit=2)
    for (tx, ty) in ((27, 44), (37, 36), (62, 60 + 2), (71, 37), (36, 76), (85, 64), (5, 24 - 2), (58, 20)):
        kachel('k18s/18', tx + P, ty + P, dict(LAMPE), weit=2)
    for (n_, tx, ty) in (('k18s/12', 26, 49), ('k18s/00', 92, 29), ('k18s/12', 60, 31), ('k18s/01', 24, 31)):
        kachel(n_, tx + P, ty + P, {}, weit=4)
    # ---------------------------------------------------------------- Evakuierung
    # Hilfslager (Block unten links): Zelt, Feldbetten, Vorraete, Wasserspender, Tisch
    for (n_, tx, ty, sp) in (('evak/zelt', 11, 68, False), ('evak/vorrat', 21, 67, False), ('evak/bett', 7, 74, False),
                             ('evak/schlafsack', 12, 75, False), ('evak/wasser', 17, 72, False), ('evak/kuehlbox', 16, 64, False),
                             ('evak/kocher', 25, 71, False), ('evak/schild', 26, 63, False)):
        kachel(n_, tx + P, ty + P, {}, sp)
    # Sanitaetsposten (Block unten rechts): Generator, Flutlicht, Betten
    for (n_, tx, ty, sp) in (('evak/generator', 78, 64, False), ('evak/flutlicht', 82, 66, False),
                             ('evak/bett', 75, 70, False), ('evak/kanister', 80, 71, False), ('evak/kisten', 82, 73, False)):
        kachel(n_, tx + P, ty + P, {'anim': 'leuchten', 'licht': [18, 8], 'licht_box': [7, 1, 35, 17], 'licht_r': 18}
               if n_ == 'evak/flutlicht' else {'anim': 'maschine', 'leds': True, 'ruetteln': True, 'led_box': [[15, 15, 23, 19]]} if n_ == 'evak/generator' else {}, sp)
    # Sperren und Zurueckgelassenes
    for (n_, tx, ty, sp) in (('evak/sandsack', 33, 22, False), ('evak/sperre', 9, 46, False), ('evak/kegel', 44, 66, False),
                             ('evak/sperre', 58, 69, True), ('evak/gepaeck', 19, 47, False), ('evak/rucksack', 48, 74, False),
                             ('evak/sandsack', 78, 48, True), ('evak/kegel', 88, 40, False), ('evak/gepaeck', 50, 35, True),
                             ('evak/schild', 39, 61, False), ('evak/kisten', 90, 22, True), ('evak/rucksack', 76, 37, True),
                             ('k18s/44', 61, 74, False), ('k18s/07', 13, 33, False)):
        kachel(n_, tx + P, ty + P, {}, sp, weit=5)
    for i, (tx, ty) in enumerate(((44, 37), (13, 56 + 8), (84, 31))):
        kachel('k38/taube', tx + P, ty + P, {'ebene': 0}, i % 2 == 1)
    # D-Reaper-Auslaeufer: Ranken und Blasen direkt an den roten Flecken
    for (n_, tx, ty, sp) in (('reaper/ranke', 41, 12, False), ('reaper/blasen', 37, 13, True), ('reaper/ranke', 11, 22, True),
                             ('reaper/kapsel', 12, 19, False)):
        kachel(n_, tx + P, ty + P, {}, sp, klassen='kn', weit=6)
    # ---------------------------------------------------------------- Baumguertel
    for ty in range(rows):
        for tx in range(cols):
            if cls[ty][tx] == 'h' and (tx + ty) % 2 == 0:
                setze(rnd.choice(WALD), tx * T + T / 2.0, ty * T + T - 1, {'anim': 'baum'}, rnd.random() < 0.5, 'wald')
    deck = np.zeros((rows * T, cols * T), bool)

    def decken(o):
        al = np.array(Image.open(os.path.join(OBJ, o['datei'])).convert('RGBA'))[..., 3] > 0
        yy, xx = np.nonzero(al)
        yy, xx = yy + o['y'], xx + o['x']
        ok = (yy >= 0) & (yy < rows * T) & (xx >= 0) & (xx < cols * T)
        deck[yy[ok], xx[ok]] = True
    for o in objekte:
        decken(o)
    for durchgang in range(2):
        for ty in range(rows):
            for tx in range(cols):
                if cls[ty][tx] == 'h' and deck[ty * T:(ty + 1) * T, tx * T:(tx + 1) * T].mean() < 0.75:
                    for dx in ((0, -5, 5) if durchgang else (0,)):
                        o = setze(rnd.choice(BUSCH + WALD[:2] if durchgang == 0 else BUSCH), tx * T + T / 2.0 + dx,
                                  ty * T + T - 1, {'anim': 'wehen'}, rnd.random() < 0.5, 'wald')
                        if o:
                            decken(o); break
    for o in objekte:
        if o['basis'].startswith('k01/'):
            o['nur_kontakt'] = True
            fx, fy_ = (o['x'] + 24) // T, (o['y'] + o['fuss']) // T     # Guertelbaeume am Weg: kein Schatten aufs Pflaster
            if cls[min(rows - 1, fy_ + 1)][min(cols - 1, fx)] not in 'hn' and cls[fy_][min(cols - 1, fx)] == 'h':
                o['schattenlos'] = True
    json.dump(objekte, open(os.path.join(OBJ, 'platzierung.json'), 'w'), indent=0)
    print(len(objekte), 'Objekte')


if __name__ == '__main__':
    main()
    import regeln_a02
    regeln_a02.objekte_pruefen('karte53', '')
