"""Objekte fuer Karte 40 (Shinjuku Siege, A03 Nr. 7) -> assets/objekte/karte40/platzierung.json

  python3 tools/karte40_objekte.py && python3 tools/karte40_bauen.py

Drei Buerobloecke neu mit PixelLab (Pro-Generator, linke Haelften k40_*_halb, gespiegelt auf Vorlagenbreite), Baeume mittig
auf den Beeten, Bus und Autos im Linksverkehr, sparsame Strassenmoebel (keine Pollerreihen: wenig Kollision, Nutzer),
Bankpaar mit Pflanzkuebel auf dem Platz unten links, Baumguertel. Boden unter den Objekten (Vorplaetze an den Tueren,
Sockel am Kuebel) zeichnet karte40_bauen.plaetze_boden aus den echten Positionen (Nutzer K39: nicht nur draufsetzen).
"""
import json, math, os, random, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageFilter

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte40')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte40')
T = 16
FREMD = {'k38/bank': 'karte38/klein/09.png', 'k39/kuebel': 'karte39/platz/01.png', 'k38/taube': 'karte38/bahn_klein/02.png',
         'k35/tuer_quelle': 'karte35/gross_buero_mitte/00.png'}
for i in (12, 18):
    FREMD['k18s/%02d' % i] = 'karte18/strasse/%02d.png' % i
for i in (5, 11, 12):
    FREMD['k18a/%02d' % i] = 'karte18/autos/%02d.png' % i
for i in (0, 1, 2, 4, 9, 12, 13, 14, 15):
    FREMD['k01/baum%02d' % i] = 'karte01/baeume/%02d.png' % i
WALD = ['k01/baum%02d' % i for i in (0, 1, 2, 4, 9, 15)]
BUSCH = ['k01/baum%02d' % i for i in (12, 13, 14)]
LAMPE = {'anim': 'leuchten', 'licht': [4, 7], 'licht_box': [2, 5, 6, 10], 'licht_r': 9}
# Gebaeude: (sprite, Mitte x Vorlagen-px, Fusszeile Vorlage, Haelfte, halbe Breite)
GEBAEUDE = [('gross/beige', 127, 10, 'gross_beige_halb/00.png', 112), ('gross/glas', 671, 11, 'gross_glas_halb/00.png', 81),
            ('gross/lila', 447, 35, 'gross_lila_halb/00.png', 142)]
BAEUME = [((0, 3, 12, 13), (0.5,)), ((39, 44, 25, 26), (0.25, 0.75))]   # Beet (x0,x1,y0,y1), Anteile in x; links Tuerachsen frei
LATERNEN = [(16, 8), (35, 8), (15, 24)]
MUELL = [(9, 13), (36, 4)]
KRATER_X = 25                                            # Achse der Nordstrasse (Spalten 18-31), Vorlagenkacheln
KRATER_FUSS = 255                                        # unteres Ende (Kartenpixel): ueber dem Zebrastreifen hinaus                               # nicht vor Tueren
# Fahrzeuge (Linksverkehr): Suedspur nach Westen (Seitenansicht schaut nach links)
AUTOS = [('k18a/12', 135, 318, False), ('k18a/05', 695, 318, False), ('k18a/11', 665, 382, False)]


def halb(quelle, ziel, breite_halb):
    import karte36_objekte as k36o
    k36o.OBJ = OBJ
    k36o.halb_gespiegelt(quelle, ziel, breite_halb, True)
    a = np.array(Image.open(os.path.join(OBJ, ziel)).convert('RGBA')).astype(int)   # lila/magenta Saum unten weg
    mg = (a[..., 3] > 0) & (a[..., 2] > a[..., 1] + 8) & (a[..., 0] > a[..., 1] + 6)
    for yy in range(a.shape[0] - 1, a.shape[0] - 6, -1):
        if mg[yy].mean() > 0.3:
            a[yy, :, 3] = 0
    im = Image.fromarray(a.astype(np.uint8))
    im.crop(im.getbbox()).save(os.path.join(OBJ, ziel))


def main():
    rnd = random.Random(40)
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cls = lay['klassen']
    cols, rows = lay['groesse']
    P = lay['versatz']
    OFF = P * T

    def k(tx, ty):
        return cls[min(rows - 1, max(0, ty))][min(cols - 1, max(0, tx))]

    for name, quelle in FREMD.items():
        ziel = os.path.join(OBJ, name + '.png')
        os.makedirs(os.path.dirname(ziel), exist_ok=True)
        shutil.copy(os.path.join(ROOT, 'assets', 'objekte', quelle), ziel)
    os.makedirs(os.path.join(OBJ, 'gross_buero_mitte'), exist_ok=True)
    shutil.copy(os.path.join(OBJ, 'k35/tuer_quelle.png'), os.path.join(OBJ, 'gross_buero_mitte/00.png'))
    os.makedirs(os.path.join(OBJ, 'gross'), exist_ok=True)
    for (name, cx, fy, h_, bh) in GEBAEUDE:
        if os.path.exists(os.path.join(OBJ, h_)):
            halb(h_, name + '.png', bh)
    tps = [(t['x'] * T - 2 * T, t['y'] * T - 2 * T, (t['x'] + t['b'] + 2) * T, (t['y'] + t['h'] + 2) * T)
           for t in lay['teleporter']]
    tps_eng = [(t['x'] * T, t['y'] * T, (t['x'] + t['b']) * T - 1, (t['y'] + t['h']) * T - 1) for t in lay['teleporter']]
    objekte, rects = [], []

    def schnitt(a, b, rand=0):
        return not (a[2] + rand < b[0] or b[2] + rand < a[0] or a[3] + rand < b[1] or b[3] + rand < a[1])

    krater_maske = None

    def setze(name, cx, fy, opt=None, spiegeln=False, art='objekt', pruefen=True, klassen='kqn'):
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
                        if ov_y > 4 and ov_x > 4:
                            return None
            if any(art2 not in ('wald', 'krater') and schnitt(r, tuple(rr), 2) for (*rr, art2) in rects):
                return None
            if krater_maske is not None and krater_maske[max(0, r[3] - 12):r[3] + 1, max(0, r[0] + 6):r[2] - 5].any():
                return None                                          # Guertel dicht an die Furche (echte Pixel statt Rechteck)
        elif pruefen:
            if any(schnitt(r, tuple(rr), 2) for (*rr, art2) in rects) or any(schnitt(r, t_, 0) for t_ in tps):
                return None
            ty_ = r[3] // T
            belag = {k(xx, ty_) for xx in range(r[0] // T, r[2] // T + 1)}
            if not belag <= set(klassen) or (len(belag) > 1 and art not in ('gebaeude', 'auto')):
                return None
        o = {'datei': datei, 'basis': name, 'x': x, 'y': y, 'fuss': bb[3] - 1, 'kachel': [int(cx) // T, int(fy) // T],
             'ebene': 1, 'ohne_wall': True}
        if art != 'wald' and not (opt or {}).get('liegend'):
            o['nur_kontakt'] = True
        o.update(opt or {})
        objekte.append(o)
        rects.append(list(r) + [art])
        return o

    def kachel(name, tx, fy_tile, opt=None, spiegeln=False, klassen='kq'):
        sp = Image.open(os.path.join(OBJ, name + '.png'))
        bw = sp.getbbox()[2] - sp.getbbox()[0]
        wt = max(1, math.ceil(bw / T))
        for d in range(3):
            for dy in range(-d, d + 1):
                for dx in range(-d, d + 1):
                    if max(abs(dx), abs(dy)) != d:
                        continue
                    x0, y = tx + dx - (wt - 1) // 2, fy_tile + dy
                    if setze(name, x0 * T + wt * T / 2.0, y * T + T - 1, opt, spiegeln, klassen=klassen):
                        return True
        print('nicht gesetzt:', name, tx - P, fy_tile - P)
        return False

    for (name, cx, fy, h_, bh) in GEBAEUDE:
        if not setze(name, cx + OFF, (fy + P) * T + T - 1, {'gebaeude': True, 'vorplatz': True}, art='gebaeude',
                     pruefen=False):
            print('Gebaeude nicht gesetzt:', name)
    # Meteor-Furche (Nutzer): laeuft auf der Nordstrasse vom Zebrastreifen bis an den Kartenrand durch den Guertel,
    # Erde/Asphalt nach links und rechts weggedrueckt, Meteor selbst unsichtbar. Bodenobjekt: zuerst gezeichnet, ohne Schatten.
    kx = (KRATER_X + P) * T
    setze('krater/lang', kx, KRATER_FUSS, {'gebaeude': True, 'schattenlos': True, 'sortier': -1, 'krater': True},
          art='krater', pruefen=False)
    ko = objekte[-1]
    ka = np.array(Image.open(os.path.join(OBJ, ko['datei'])).convert('RGBA'))[:, :, 3] > 0
    krater_maske = np.zeros((rows * T, cols * T), bool)
    h_, w_ = ka.shape
    krater_maske[max(0, ko['y']):ko['y'] + h_, ko['x']:ko['x'] + w_] = ka[max(0, -ko['y']):, :]
    krater_maske = np.array(Image.fromarray(krater_maske.astype(np.uint8) * 255).filter(ImageFilter.MaxFilter(7))) > 0
    for i, ((x0, x1, y0, y1), anteile) in enumerate(BAEUME):      # Stammfuss auf der senkrechten Beetmitte (Pruefliste)
        fy = (y0 + P) * T + (y1 - y0 + 1) * T // 2 + 3
        arten = ['k01/baum14', 'k01/baum13'] if i == 0 else ['k01/baum00', 'k01/baum02']   # links Bueche: Block steht dicht davor
        for j, f in enumerate(anteile):
            hw = (lambda b: (b[2] - b[0]) / 2.0 + 1)(Image.open(os.path.join(OBJ, arten[j % 2] + '.png')).getbbox())
            cx = min(max((x0 + P) * T + f * (x1 - x0 + 1) * T, (x0 + P) * T + hw), (x1 + P + 1) * T - hw)   # ganz im Beet
            setze(arten[j % 2], cx, fy, {'anim': 'baum'}, (i + j) % 2 == 1, klassen='n')
    for (tx, ty) in LATERNEN:
        kachel('k18s/18', tx + P, ty + P, dict(LAMPE))
    for (tx, ty) in MUELL:
        kachel('k18s/12', tx + P, ty + P, {})
    for (n_, cx, fy, sp) in AUTOS:
        setze(n_, cx + OFF, fy + OFF, {'nur_kontakt': True}, sp, art='auto', klassen='a')
    # Platz unten links: Pflanzkuebel auf der Platzmitte, Bankpaar gespiegelt daneben
    gk = np.array([list(z) for z in cls])
    ys, xs = np.nonzero(gk[:, :] == 'q')
    ys, xs = ys[ys < 36 + P], xs[ys < 36 + P]
    mx, my = (xs.min() + xs.max() + 1) * T / 2.0, (ys.min() + ys.max() + 1) * T / 2.0
    if setze('k39/kuebel', mx, my + 18, {'sockel': True}, art='gebaeude', klassen='q'):
        for d_ in (56, 64, 72):
            if all(setze('k38/bank', mx + s_ * d_, my + 18, {}, s_ > 0, klassen='q') for s_ in (-1, 1)):
                break
    for i, (tx, ty) in enumerate(((10, 28), (40, 31))):
        kachel('k38/taube', tx + P, ty + P, {'ebene': 0}, i % 2 == 1)
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
    json.dump(objekte, open(os.path.join(OBJ, 'platzierung.json'), 'w'), indent=0)
    print(len(objekte), 'Objekte')


if __name__ == '__main__':
    main()
    import regeln_a02
    regeln_a02.objekte_pruefen('karte40', '')
