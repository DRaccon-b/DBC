"""Objekte fuer Karte 14 (Spiral Mountain: Summit) - am 16x16-Raster, nach den Regeln aus CLAUDE.md.

  python3 tools/karte14_bauen.py   (einmal ohne Objekte -> pixelhoehe.npy)
  python3 tools/karte14_objekte.py && python3 tools/regeln_v11.py karte14 && python3 tools/karte14_objekte.py symmetrie
  python3 tools/karte14_bauen.py

Neu (PixelLab, assets/objekte/karte14, frontal): schloss2 (Gauklerschloss mit Harlekin-Tuermen), bau (Burgmauer,
Turm, dunkles Portal, Narrenthron), statue (Ritter mit Schwert, Gaukler, Dame mit Fledermausfluegeln, Pik-Monolith),
mittel (Spielkarten, Kristalle, Feuerschalen, Banner, Schwerter, Masken, Wasserspeier, Kandelaber ...), klein (64),
wolken (Wolken fuer den Gipfelrand und Extras: Stacheltruhe, Dornenbaum, Wasserspeier ...).
Anspielungen auf die Herren des Gipfels (Gaukler, Ritter, dunkle Dame) nur ueber Motive - keine Figur nachgebaut.
Paare stehen spiegelsymmetrisch zur Schlossachse, Banner und Statuen im festen Rhythmus am Schachbrettweg.
"""
import json, os, random, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageFilter
from karte04_objekte import saeubern
from karte09_objekte import raster_x, bewerten

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte14')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte14')
QUELLEN = {}
T = 16
ACHSE_S = int(40.5 * T)          # Schloss, Boss-Feld und Schachbrettweg
ACHSE_P = 62 * T                 # Portalplatz

FLACH = {'klein/%02d' % i for i in (0, 1, 2, 4, 5, 6, 7, 9, 10, 11, 13, 15, 19, 20, 21, 30, 58)} | {'leere/08', 'leere/14'}
LIEGEND = {'mittel/08', 'klein/02', 'klein/04', 'klein/10', 'klein/13', 'klein/19', 'klein/21', 'klein/58'}
LEUCHTEN = {'mittel/06': 'banner', 'bau/02': 'portalwirbel', 'leere/05': 'auge', 'leere/02': 'glimmen', 'leere/07': 'glimmen', 'leere/08': 'glimmen',
            'leere/00': 'glimmen', 'leere/04': 'glimmen', 'mittel/05': 'feuer_lila', 'mittel/12': 'kerzen', 'mittel/04': 'glimmen', 'klein/12': 'kerzen',
            'klein/14': 'glimmen', 'klein/08': 'glimmen', 'wolken/10': 'feuer_lila', 'klein/55': 'glimmen'}
WIND = {'klein/09'}
STREU = {'mittel/00': 2, 'mittel/01': 2, 'mittel/02': 2, 'mittel/03': 2, 'mittel/07': 2, 'mittel/08': 1, 'mittel/09': 1,
         'mittel/11': 1, 'mittel/13': 1, 'mittel/14': 2, 'mittel/15': 1, 'wolken/08': 2, 'wolken/14': 2, 'klein/44': 1}
KLEIN = {'klein/00': 4, 'klein/01': 3, 'klein/02': 3, 'klein/03': 2, 'klein/04': 2, 'klein/05': 2, 'klein/06': 1,
         'klein/07': 1, 'klein/09': 3, 'klein/10': 1, 'klein/11': 2, 'klein/13': 1, 'klein/19': 1, 'klein/21': 1,
         'klein/30': 1, 'klein/39': 1, 'klein/53': 1, 'klein/58': 2, 'klein/12': 1}
KRISTALL = {'mittel/04': 3, 'klein/08': 3, 'klein/55': 2, 'klein/14': 1}
WOLKEN = ['wolken/%02d' % i for i in range(8)]


def quelle(name):
    return os.path.join(OBJ, name + '.png')


def main():
    rnd = random.Random(14)
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cls = lay['klassen']
    cols, rows = lay['groesse']
    lvl = np.load(os.path.join(KARTE, 'pixelhoehe.npy'))
    os.makedirs(os.path.join(OBJ, 'sauber'), exist_ok=True)
    cache, alpha = {}, {}
    objekte, belegt = [], set()
    pixel = np.zeros(lvl.shape, bool)
    gesperrt = set()
    for tp in lay.get('teleporter', []):
        for y in range(tp['y'] - 1, tp['y'] + tp['h'] + 2):
            for x in range(tp['x'] - 1, tp['x'] + tp['b'] + 2):
                gesperrt.add((x, y))
    for (x0, x1, e, yb) in lay.get('treppen_sued', []):
        for y in range(yb - 1, yb + 5):
            for x in range(x0 - 1, x1 + 2):
                gesperrt.add((x, y))
    pfad = {(x, y) for y in range(rows) for x in range(cols) if cls[y][x] == 'z' and y >= 29}   # Schachbrettweg frei

    def sprite(name, spiegeln=False):
        key = (name, spiegeln)
        if key not in cache:
            sp = saeubern(Image.open(quelle(name)).convert('RGBA'))
            if spiegeln:
                sp = sp.transpose(Image.FLIP_LEFT_RIGHT)
            datei = 'sauber/%s%s.png' % (name.replace('/', '-'), '_m' if spiegeln else '')
            sp.save(os.path.join(OBJ, datei))
            a = np.array(sp.getchannel('A')) >= 128
            zu = int(np.nonzero(a.any(axis=1))[0].max())
            xs = np.nonzero(a.any(axis=0))[0]
            cache[key] = (datei, sp.height, zu, (xs.min() + xs.max() + 1) / 2.0)
            alpha[datei] = a
        return cache[key]

    def frei_px(datei, x, y):
        a = alpha[datei]
        h_, w_ = a.shape
        y0, x0 = max(0, y), max(0, x)
        y1, x1 = min(pixel.shape[0], y + h_), min(pixel.shape[1], x + w_)
        if y1 <= y0 or x1 <= x0:
            return True
        return not (pixel[y0:y1, x0:x1] & a[y0 - y:y1 - y, x0 - x:x1 - x]).any()

    def belegen(datei, x, y):
        a = np.array(Image.fromarray((alpha[datei] * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(5))) > 0
        h_, w_ = a.shape
        y0, x0 = max(0, y), max(0, x)
        y1, x1 = min(pixel.shape[0], y + h_), min(pixel.shape[1], x + w_)
        if y1 > y0 and x1 > x0:
            pixel[y0:y1, x0:x1] |= a[y0 - y:y1 - y, x0 - x:x1 - x]

    def baum_ok(datei, x, y):
        """Begleiter (Regel 5) verdeckt hoechstens den Sockel eines Baums an der Ecke - nie Stamm oder Krone."""
        a = alpha[datei]
        for t in objekte:
            if not t.get('baum'):
                continue
            at = alpha[t['datei']]
            x0, y0 = max(t['x'], x), max(t['y'], y)
            x1, y1 = min(t['x'] + at.shape[1], x + a.shape[1]), min(t['y'] + at.shape[0], y + a.shape[0])
            if x1 <= x0 or y1 <= y0:
                continue
            ov = at[y0 - t['y']:y1 - t['y'], x0 - t['x']:x1 - t['x']] & a[y0 - y:y1 - y, x0 - x:x1 - x]
            if not ov.any():
                continue
            fuss_t = t['y'] + int(np.nonzero(at.any(axis=1))[0].max())
            ys_ = np.nonzero(ov.any(axis=1))[0] + y0
            if ys_.min() < fuss_t - 18 or ov.sum() > 0.2 * a.sum():   # nur unten am Sockel, nur ein kleiner Teil
                return False
            xs_t = np.nonzero(at[-20:].any(axis=0))[0]                 # Stammfuss: mittlere Spalten des Sockels
            mt = t['x'] + (xs_t.min() + xs_t.max() + 1) / 2.0
            xs_b = np.nonzero(a.any(axis=0))[0]
            if abs(x + (xs_b.min() + xs_b.max() + 1) / 2.0 - mt) < 0.45 * (xs_b.max() - xs_b.min() + 1) + 6:
                return False                                            # seitlich an der Ecke, nicht mittig vor dem Stamm
        return True

    pfad_px = np.zeros(lvl.shape, bool)                       # Weg bleibt frei: kein Objektfuss auf dem Pfad
    for (px_, py_) in pfad:
        pfad_px[py_ * T:(py_ + 1) * T, px_ * T:(px_ + 1) * T] = True

    def weg_belegt(datei, x, y):
        a = alpha[datei]
        zeilen = np.nonzero(a.any(axis=1))[0]
        unten = int(zeilen.max() - (zeilen.max() - zeilen.min()) * 0.4)
        ys, xs = np.nonzero(a[unten:])
        ys, xs = ys + y + unten, xs + x
        ok = (ys >= 0) & (ys < pfad_px.shape[0]) & (xs >= 0) & (xs < pfad_px.shape[1])
        return pfad_px[ys[ok], xs[ok]].any()

    def setzen(name, X, fy, opt, suchen=False, arten=None, melden=False):
        opt = dict(opt)
        datei, h, zu, mitte = sprite(name, opt.pop('spiegeln', False))
        kand = [(X, fy)]
        if suchen:
            kand += sorted(((X + dx * T, fy + dy) for dx in range(-2, 3) for dy in range(-2, 3) if dx or dy),
                           key=lambda k: abs(k[0] - X) / T + abs(k[1] - fy))
        for (kx, ky) in kand:
            tx = int(kx // T)
            if not (0 <= tx < cols and 0 <= ky < rows) or (tx, ky) in gesperrt:
                continue
            if arten and cls[ky][tx] not in arten:
                continue
            x = raster_x(alpha[datei], kx) if not opt.get('achse') else int(round(kx - mitte))
            y = (ky + 1) * T - 1 - zu
            if weg_belegt(datei, x, y):
                continue
            if opt.get('an_wand') or (bewerten(lvl, alpha[datei], x, y) and (frei_px(datei, x, y) if not opt.get('begleiter') else baum_ok(datei, x, y))):
                break
        else:
            if melden:
                print('  keine passende Stelle:', name, (X // T, fy))
            return None
        o = {'datei': datei, 'basis': name, 'x': x, 'y': y, 'fuss': h, 'kachel': [tx, ky],
             'ebene': 0 if name in FLACH else 1}
        if name in LIEGEND:
            o['liegend'] = True
        if name in WIND:
            o['anim'] = 'wehen'
        if name in LEUCHTEN:
            o['anim'] = LEUCHTEN[name]
        o.update(opt)
        objekte.append(o)
        belegt.add((tx, ky))
        if name not in FLACH and not o.get('begleiter'):
            belegen(datei, x, y)
        return o

    Hp, Wp = lvl.shape
    rr = random.Random(9)
    # 0) Gipfelrand: Wolken auf der Bergkuppe, vom Kartenrand angeschnitten, Tiefe wellenfoermig (wie Karte 12/13);
    #    sie treiben langsam (echte Bewegung), der Teleporter bleibt frei
    def kante(laenge):
        pos, tiefe, out = -10, 0.0, []
        while pos < laenge + 24:
            tiefe = max(-8, min(12, tiefe * 0.7 + rr.uniform(-6, 6)))
            out.append((pos, tiefe + rr.uniform(-4, 4)))
            pos += rr.randint(26, 44)
        return out
    stellen = [(X, 22 + t, 'oben') for X, t in kante(Wp)] + [(X, Hp + 10 - t, 'unten') for X, t in kante(Wp)]
    stellen += [(t, Y + 20, 'seite') for Y, t in kante(Hp)] + [(Wp - t, Y + 20, 'seite') for Y, t in kante(Hp)]
    for (X, fussy, seite) in stellen:
        X, fussy = int(round(X)), int(round(fussy))
        if seite == 'unten' and 38 * T - 16 <= X <= 43 * T + 16:
            continue
        if seite == 'oben' and 18 * T <= X <= 54 * T:
            continue                                              # hinter dem Schloss keine Wolken vor den Daechern
        name_ = rr.choice(WOLKEN)
        datei, h, zu, mitte = sprite(name_, rr.random() < 0.5)
        x, y = int(round(X - mitte)), fussy - zu
        objekte.append({'datei': datei, 'basis': name_, 'x': x, 'y': y, 'fuss': h, 'kachel': [max(0, min(cols - 1, X // T)),
                        max(0, min(rows - 1, fussy // T))], 'ebene': 1, 'fest_pos': True, 'rand': True, 'kein_schatten': True,
                        'anim': 'treiben', 'an_wand': True})
    # 1) Schloss, Mauern und Tuerme spiegelgleich zur Achse, Thron vor dem Tor, Portalplatz
    FEST = [
        ('schloss2/01', ACHSE_S, 6, {'achse': ACHSE_S, 'an_wand': True, 'hinter_feld': True}),
        ('bau/00', ACHSE_S - 104, 6, {'symm': 's1', 'an_wand': True, 'hinter_feld': True}), ('bau/00', ACHSE_S + 104, 6, {'symm': 's1', 'an_wand': True, 'hinter_feld': True}),
        ('bau/01', ACHSE_S - 176, 8, {'symm': 's2', 'an_wand': True, 'hinter_feld': True}), ('bau/01', ACHSE_S + 176, 8, {'symm': 's2', 'an_wand': True, 'hinter_feld': True}),   # aeussere Tuerme 2 Kacheln vor der Mauer
        ('bau/03', ACHSE_S, 13, {'achse': ACHSE_S, 'vorrang': True}),
        # Boss-Feld: Feuerschalen in den vier Ecken, Kandelaber am Rahmen
        ('mittel/05', ACHSE_S - 120, 12, {'symm': 'b1'}), ('mittel/05', ACHSE_S + 120, 12, {'symm': 'b1'}),
        ('mittel/05', ACHSE_S - 152, 22, {'symm': 'b2'}), ('mittel/05', ACHSE_S + 152, 22, {'symm': 'b2'}),
        ('mittel/12', ACHSE_S - 96, 26, {'symm': 'b3'}), ('mittel/12', ACHSE_S + 96, 26, {'symm': 'b3'}),
        # Portalplatz: Portal, Wasserspeier-Paar, Kandelaber
        ('bau/02', ACHSE_P, 10, {'achse': ACHSE_P}),
        ('leere/01', ACHSE_P - 104, 8, {'symm': 'p1'}), ('leere/01', ACHSE_P + 104, 8, {'symm': 'p1'}),   # schwarze Kristallsplitter am Portal
        ('leere/12', 72 * T, 7, {}), ('leere/10', 74 * T + 8, 8, {}), ('leere/11', 70 * T, 8, {}),          # rechte Schulter
        ('leere/05', ACHSE_P - 48, 18, {'symm': 'q2'}), ('leere/05', ACHSE_P + 48, 18, {'symm': 'q2'}),   # Obelisken mit Leere-Auge
        ('leere/13', ACHSE_P - 44, 11, {'symm': 'p3'}), ('leere/13', ACHSE_P + 44, 11, {'symm': 'p3'}),   # Kettendorne vor dem Portal
        ('leere/02', ACHSE_P - 56, 10, {}), 
        # rund um den Eingang: Schattenklauen, Skelettklaue, Risse, Eierschalen, Saeulenrest, Steinkreis, Leere-Kugel
        ('leere/00', 56 * T, 17, {}), ('leere/06', 67 * T, 16, {}), ('leere/14', 58 * T, 19, {}),
        ('leere/04', 69 * T, 18, {}), ('leere/15', 73 * T, 20, {}), ('leere/07', 54 * T, 21, {}),
        ('leere/09', 71 * T, 16, {}), ('leere/03', 66 * T, 20, {}),
        # Treppenplatz unten: Feuerschalen, Stacheltruhe, Zylinder
        ('mittel/05', ACHSE_S - 104, 58, {'symm': 'u1'}), ('mittel/05', ACHSE_S + 104, 58, {'symm': 'u1'}),
        ('wolken/11', 34 * T, 62, {}), ('mittel/15', 46 * T, 62, {}),
        # einzelne Blickfaenge auf dem Gipfel
        ('statue/03', 12 * T, 22, {}), ('statue/03', 70 * T, 37, {'spiegeln': True}), ('wolken/12', 20 * T, 6, {}),
        ('wolken/13', 54 * T, 18, {}), ('mittel/07', 24 * T, 33, {}), ('mittel/07', 60 * T, 56, {}),
    ]
    # Schachbrettweg: Gauklerstatuen oben, Ritterstatuen, Fluegeldamen unten - Banner dazwischen im festen Rhythmus
    for (y, name_) in ((33, 'statue/01'), (41, 'statue/00'), (49, 'statue/02')):
        FEST += [(name_, ACHSE_S - 72, y, {'symm': 'w%d' % y}), (name_, ACHSE_S + 72, y, {'symm': 'w%d' % y})]
    for y in (37, 45):                                            # Banner aussen neben den Statuen, gleicher Takt
        FEST += [('mittel/06', ACHSE_S - 128, y, {'symm': 'f%d' % y}), ('mittel/06', ACHSE_S + 128, y, {'symm': 'f%d' % y})]
    FEST += [('mittel/06', ACHSE_S - 60, 53, {'symm': 'f53'}), ('mittel/06', ACHSE_S + 60, 53, {'symm': 'f53'})]
    for (name, X, fy, opt) in FEST:
        setzen(name, X, fy, opt, suchen=not (opt.get('symm') or opt.get('achse')) or str(opt.get('symm', '')).startswith(('p', 'q', 'w', 'f')),
               melden=True)
    for o in objekte:                                             # Schloss ganz im Bild (Turmspitze nicht am Rand
        if o['basis'] == 'schloss2/01':                           # abgeschnitten) und vor der Mauer gezeichnet
            o['y'] = max(o['y'], 0)
    # 2) Kristalle auf dem Kristallboden, Spielkarten und Deko auf dem Gipfel, Kleinkram (sparsam, unregelmaessig)
    for (streu, arten, anzahl) in ((KRISTALL, 'p', 14), (STREU, 'dk', 22), (KLEIN, 'dkv', 52)):
        namen, gew = list(streu), list(streu.values())
        n = 0
        for _ in range(9000):
            if n >= anzahl:
                break
            tx, ty = rnd.randrange(3, 77), rnd.randrange(4, rows - 4)
            if cls[ty][tx] not in arten or (tx, ty) in pfad:
                continue
            name_ = rnd.choices(namen, weights=gew)[0]
            if any(o['basis'] == name_ and abs(o['kachel'][0] - tx) <= 6 and abs(o['kachel'][1] - ty) <= 6 for o in objekte):
                continue
            if setzen(name_, tx * T + 8, ty, {'spiegeln': rnd.random() < 0.4}, arten=arten):
                n += 1
    json.dump(objekte, open(os.path.join(OBJ, 'platzierung.json'), 'w'), indent=0)
    print(len(objekte), 'Objekte gesetzt')


def symmetrie():
    """Paare exakt spiegelsymmetrisch: 'symm' zur senkrechten Achse (Plattform bzw. Platz), 'symm_y' zur
    waagerechten Brueckenachse; 'achse' genau auf die Achse."""
    pf = os.path.join(OBJ, 'platzierung.json')
    objs = json.load(open(pf))
    achsen = {'p1': ACHSE_P, 'p2': ACHSE_P, 'p3': ACHSE_P, 'q2': ACHSE_P}      # Portalplatz-Paare an der Portalachse
    paare, paare_y = {}, {}
    for o in objs:
        if o.get('achse'):
            a_ = np.array(Image.open(os.path.join(OBJ, o['datei'])).getchannel('A')) > 128
            xs_ = np.nonzero(a_.any(axis=0))[0]
            o['x'] = int(round(o['achse'] - (xs_.min() + xs_.max() + 1) / 2.0))
        if o.get('symm'):
            paare.setdefault(o['symm'], []).append(o)
        if o.get('symm_y'):
            paare_y.setdefault(o['symm_y'], []).append(o)
    for name, ps in paare.items():
        if len(ps) == 1:                                     # fehlender Partner: gespiegelt ergaenzen
            neu = dict(ps[0]); objs.append(neu); ps.append(neu)
            neu['x'] = ps[0]['x'] + (1 if ps[0]['x'] < achsen.get(name, ACHSE_S) else -1)
        if len(ps) != 2:
            print('  Paar unvollstaendig:', name, len(ps))
            continue
        l, r = sorted(ps, key=lambda o: o['x'])
        achse = achsen.get(name, ACHSE_S)
        a_ = np.array(Image.open(os.path.join(OBJ, l['datei'])).getchannel('A')) > 128
        xs_ = np.nonzero(a_.any(axis=0))[0]
        m_ = (xs_.min() + xs_.max() + 1) / 2.0
        r['x'] = int(round(2 * achse - (l['x'] + m_) - m_))
        r['y'] = l['y']
        if l['datei'] == r['datei']:                         # spiegelverkehrt: rechter Partner ist das Spiegelbild
            d_ = l['datei'].replace('.png', '_m.png') if not l['datei'].endswith('_m.png') else l['datei'].replace('_m.png', '.png')
            if not os.path.exists(os.path.join(OBJ, d_)):
                Image.open(os.path.join(OBJ, l['datei'])).transpose(Image.FLIP_LEFT_RIGHT).save(os.path.join(OBJ, d_))
            r['datei'] = d_
            a2 = np.array(Image.open(os.path.join(OBJ, d_)).getchannel('A')) > 128
            xs2 = np.nonzero(a2.any(axis=0))[0]
            r['x'] = int(round(2 * achse - (l['x'] + m_) - (xs2.min() + xs2.max() + 1) / 2.0))
    for name, ps in paare_y.items():
        if len(ps) == 1:                                     # fehlender Partner: an der Brueckenachse gespiegelt
            o0 = ps[0]
            neu = dict(o0)
            a_ = np.array(Image.open(os.path.join(OBJ, o0['datei'])).getchannel('A')) > 128
            zu_ = int(np.nonzero(a_.any(axis=1))[0].max())
            fuss = o0['y'] + zu_
            neu['y'] = int(2 * ACHSE_SY - fuss) - zu_ + (T if fuss < ACHSE_SY else -T)
            objs.append(neu); ps.append(neu)
        if len(ps) != 2:
            print('  Paar unvollstaendig:', name, len(ps))
            continue
        o_, u_ = sorted(ps, key=lambda o: o['y'])
        u_['x'] = o_['x']
    json.dump(objs, open(pf, 'w'), indent=0)
    print('Symmetrie: %d + %d Paare' % (len(paare), len(paare_y)))


if __name__ == '__main__':
    symmetrie() if sys.argv[1:] == ['symmetrie'] else main()
