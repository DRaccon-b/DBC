"""Objekte fuer Karte 39 (West Shinjuku Siege, A03 Nr. 6) -> assets/objekte/karte39/platzierung.json

  python3 tools/karte39_objekte.py && python3 tools/karte39_bauen.py

Grosse Objekte zuerst: Zwillingsturm-Rathaus mitten auf seinem Platz (PixelLab k39_rathaus), Hochhaus rechts (Pro-Generator
k39_turm, groesser als 256 px), Fussgaengerbruecke ueber die linke Hauptstrasse (k39_bruecke), Buerobauten aus
gespiegelten Haelften (zweistoeckig neu k39_beige_flach_halb, vierstoeckig von Karte 36), U-Bahn-Eingaenge (Karte 38);
dann Baeume mittig auf den Gruenflaechen, Laternen, Baenke sparsam, Bushaltestellen, Autos im Linksverkehr, zuletzt
der Baumguertel. Pixelgenaue Pruefung (2 px), Fuss auf einheitlichem Belag, kein Bodenwall auf Pflaster/Asphalt.
"""
import json, math, os, random, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte39')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte39')
T = 16
FREMD = {'k38/kiosk': 'karte38/kiosk/00.png', 'k38/taube': 'karte38/bahn_klein/02.png',
         'k38/zeitung': 'karte38/bahn_klein/03.png', 'k38/treppe': 'karte38/treppe/01.png', 'k38/bank': 'karte38/klein/09.png', 'k36/halb_hoch':
         'karte36/gross_beige_halb_hoch_b/00.png', 'k35/tuer_quelle': 'karte35/gross_buero_mitte/00.png'}
for i in (0, 1, 12, 18, 41, 42):
    FREMD['k18s/%02d' % i] = 'karte18/strasse/%02d.png' % i
for i in (2, 4, 5, 6, 11):
    FREMD['k18a/%02d' % i] = 'karte18/autos/%02d.png' % i
for i in (0, 1, 2, 4, 9, 12, 13, 14, 15):
    FREMD['k01/baum%02d' % i] = 'karte01/baeume/%02d.png' % i
WALD = ['k01/baum%02d' % i for i in (0, 1, 2, 4, 9, 15)]
BUSCH = ['k01/baum%02d' % i for i in (12, 13, 14)]
STADTBAUM = ['k01/baum%02d' % i for i in (0, 2, 4)]
LAMPE = {'anim': 'leuchten', 'licht': [4, 7], 'licht_box': [2, 5, 6, 10], 'licht_r': 9}

# (sprite, Mitte x Vorlagen-px, Fusszeile Vorlage)
GEBAEUDE = [('gross/turm', 1410, 44), ('gross/buero_oben', 1297, 10), ('gross/buero_links', 192, 29),   # Gehwegreihe
            ('gross/buero_unten_links', 222, 75), ('gross/buero_unten', 750, 76)]                    # vor jeder Front
RATHAUS_ACHSE = None                                              # aus der hellen Rathausflaeche berechnet
BRUECKE = (465, 42)                                               # Mitte x, Fusszeile (ueber der linken Hauptstrasse)
UBAHN = [(607, 20), (1073, 43)]
BAEUME = [(39, 13), (64, 14), (65, 23), (39, 30), (63, 30), (8, 33), (15, 31), (20, 30), (9, 38), (11, 59),
          (20, 59), (60, 72), (66, 72)]
LATERNEN = [(5, 5), (21, 5), (65, 7), (34, 7), (70, 36), (5, 43), (11, 43), (6, 57), (71, 57), (90, 57), (93, 43)]
BAENKE = [(10, 20), (17, 20), (46, 35), (63, 38)]          # + Paare an Rathaus und Brunnen (Achsen)   # + Paar am Rathaus (Achse)
MOEBEL = [('k18s/00', 21, 18), ('k18s/41', 52, 45), ('k18s/41', 65, 55)]   # Bushaeuschen nicht im Treppenaustritt
# Autos (Linksverkehr): waagerecht Nordspur nach Osten (gespiegelt), Suedspur nach Westen; senkrecht Ostspur nach Sueden
AUTOS = [('k18a/06', 495, 168, False), ('k18a/06', 1264, 535, False), ('k18a/05', 232, 785, True),
         ('k18a/02', 950, 785, True), ('k18a/11', 1415, 785, True), ('k18a/04', 700, 858, False)]


def weiss_freistellen(quelle, ziel):
    """Pro-Generator lieferte weissen statt magentafarbenen Hintergrund: vom Rand her erreichbares Weiss transparent."""
    from collections import deque
    ar = np.array(Image.open(os.path.join(OBJ, quelle)).convert('RGBA')).astype(int)
    w_ = (ar[..., :3].min(-1) > 236)
    hh, ww = w_.shape
    weg = np.zeros_like(w_); q = deque()
    for yy in range(hh):
        for xx in (0, ww - 1):
            if w_[yy, xx]: weg[yy, xx] = True; q.append((yy, xx))
    for xx in range(ww):
        for yy in (0, hh - 1):
            if w_[yy, xx] and not weg[yy, xx]: weg[yy, xx] = True; q.append((yy, xx))
    while q:
        yy, xx = q.popleft()
        for y2, x2 in ((yy - 1, xx), (yy + 1, xx), (yy, xx - 1), (yy, xx + 1)):
            if 0 <= y2 < hh and 0 <= x2 < ww and w_[y2, x2] and not weg[y2, x2]:
                weg[y2, x2] = True; q.append((y2, x2))
    ar[weg, 3] = 0
    im = Image.fromarray(ar.astype(np.uint8))
    im.crop(im.getbbox()).save(os.path.join(OBJ, ziel))


def stockwerke_entfernen(quelle, ziel, y0, n, periode):
    """Hochhaus hoeher als in der Vorlage: n gleiche Stockwerke (Periode in px) aus dem Fensterraster nehmen (Regel:
    Gebaeude hoeher als die Vorlage -> anpassen); die Fuge liegt genau auf einer Stockwerksgrenze."""
    a = np.array(Image.open(os.path.join(OBJ, quelle)).convert('RGBA'))
    b = np.concatenate([a[:y0], a[y0 + n * periode:]], 0)
    im = Image.fromarray(b)
    im.crop(im.getbbox()).save(os.path.join(OBJ, ziel))


def halb_gespiegelt(quelle, ziel, breite_halb, eingang=True):
    import karte36_objekte as k36o
    k36o.OBJ = OBJ
    k36o.halb_gespiegelt(quelle, ziel, breite_halb, eingang)
    a = np.array(Image.open(os.path.join(OBJ, ziel)).convert('RGBA')).astype(int)   # lila/magenta Freistellsaum unten weg
    r_, g_, b_ = a[..., 0], a[..., 1], a[..., 2]
    mg = (a[..., 3] > 0) & (b_ > g_ + 8) & (r_ > g_ + 6)
    for yy in range(a.shape[0] - 1, a.shape[0] - 6, -1):
        if mg[yy].mean() > 0.3:
            a[yy, :, 3] = 0
    im = Image.fromarray(a.astype(np.uint8))
    im.crop(im.getbbox()).save(os.path.join(OBJ, ziel))


def main():
    rnd = random.Random(39)
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
    shutil.copy(os.path.join(OBJ, 'k35/tuer_quelle.png'), os.path.join(OBJ, 'gross_buero_mitte_00.png'))
    os.makedirs(os.path.join(OBJ, 'gross_buero_mitte'), exist_ok=True)
    shutil.copy(os.path.join(OBJ, 'k35/tuer_quelle.png'), os.path.join(OBJ, 'gross_buero_mitte/00.png'))
    flach = 'gross_beige_flach_halb/00.png'                         # _b ist oben angeschnitten
    os.makedirs(os.path.join(OBJ, 'gross'), exist_ok=True)
    if os.path.exists(os.path.join(OBJ, flach)):
        halb_gespiegelt(flach, 'gross/buero_oben.png', 148)
        halb_gespiegelt(flach, 'gross/buero_links.png', 112)
        halb_gespiegelt(flach, 'gross/buero_unten.png', 176)
    halb_gespiegelt('k36/halb_hoch.png', 'gross/buero_unten_links.png', 142)
    if os.path.exists(os.path.join(OBJ, 'gross_turm/00.png')):
        stockwerke_entfernen('gross_turm/00.png', 'gross/turm.png', 150, 2, 34)
    if os.path.exists(os.path.join(OBJ, 'gross_bruecke/00.png')):
        weiss_freistellen('gross_bruecke/00.png', 'gross/bruecke.png')
    tps = [(t['x'] * T - 2 * T, t['y'] * T - 2 * T, (t['x'] + t['b'] + 2) * T, (t['y'] + t['h'] + 2) * T)
           for t in lay['teleporter']]
    tps_eng = [(t['x'] * T, t['y'] * T, (t['x'] + t['b']) * T - 1, (t['y'] + t['h']) * T - 1) for t in lay['teleporter']]
    objekte, rects = [], []

    def schnitt(a, b, rand=0):
        return not (a[2] + rand < b[0] or b[2] + rand < a[0] or a[3] + rand < b[1] or b[3] + rand < a[1])

    def setze(name, cx, fy, opt=None, spiegeln=False, art='objekt', pruefen=True, klassen='gkqbn'):
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
            if any(art2 != 'wald' and schnitt(r, tuple(rr), 2) for (*rr, art2) in rects):
                return None
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
            o['nur_kontakt'] = True                               # helles Pflaster: nur Kontaktschatten (Pruefliste K36)
        o.update(opt or {})
        objekte.append(o)
        rects.append(list(r) + [art])
        return o

    def kachel(name, tx, fy_tile, opt=None, spiegeln=False, klassen='gkqbn', art='objekt'):
        if not os.path.exists(os.path.join(OBJ, name + '.png')):
            print('fehlt:', name); return False
        sp = Image.open(os.path.join(OBJ, name + '.png'))
        bw = sp.getbbox()[2] - sp.getbbox()[0]
        wt = max(1, math.ceil(bw / T))
        for d in range(3):
            for dy in range(-d, d + 1):
                for dx in range(-d, d + 1):
                    if max(abs(dx), abs(dy)) != d:
                        continue
                    x0, y = tx + dx - (wt - 1) // 2, fy_tile + dy
                    if setze(name, x0 * T + wt * T / 2.0, y * T + T - 1, opt, spiegeln, art, klassen=klassen):
                        return True
        print('nicht gesetzt:', name, tx - P, fy_tile - P)
        return False

    # ---------------------------------------------------------------- grosse Bauwerke
    rf = lay['gebaeude_flaechen']
    for (name, cx, fy) in GEBAEUDE:
        if not setze(name, cx + OFF, (fy + P) * T + T - 1, {'gebaeude': True}, art='gebaeude', pruefen=False):
            print('Gebaeude nicht gesetzt:', name)
    gk = np.array([list(z) for z in cls])                          # Rathaus: exakt auf der Mitte seiner hellen Flaeche
    x0, y0, x1, y1 = 42 + P, 8 + P, 56 + P, 23 + P
    rat = 'rathaus/00' if not os.path.exists(os.path.join(OBJ, 'rathaus_wahl.txt')) else \
        open(os.path.join(OBJ, 'rathaus_wahl.txt')).read().strip()
    setze(rat, (x0 + x1 + 1) * T / 2.0, y1 * T + T - 1, {'gebaeude': True}, art='gebaeude', pruefen=False)
    ra = objekte[-1]                                              # Bankpaar exakt gespiegelt an der Rathausachse
    achse = (x0 + x1 + 1) * T / 2.0
    for d_ in (80, 96, 112):
        if all(setze('k38/bank', achse + s_ * d_, (26 + P) * T + T - 1, {}, s_ > 0) for s_ in (-1, 1)):
            break
    setze('gross/bruecke', BRUECKE[0] + OFF, (BRUECKE[1] + P) * T + T - 1, {'schattenlos': True}, art='gebaeude',
          pruefen=False)
    for (cx, fy) in UBAHN:
        setze('ubahn/00', cx + OFF, (fy + P) * T + T - 1, {}, art='gebaeude')   # ueberdachter Eingang, vorne offen
    # ---------------------------------------------------------------- Baeume mittig auf Gruenflaechen, Moebel sparsam
    for i, (tx, ty) in enumerate(BAEUME):
        kachel(STADTBAUM[i % len(STADTBAUM)], tx + P, ty + P, {'anim': 'baum'}, i % 2 == 1, klassen='gkqbn')
    for (tx, ty) in LATERNEN:
        kachel('k18s/18', tx + P, ty + P, dict(LAMPE))
    for i, (tx, ty) in enumerate(BAENKE):
        kachel('k38/bank', tx + P, ty + P, {}, i % 2 == 1)
    for (n_, tx, ty) in MOEBEL:
        kachel(n_, tx + P, ty + P, {})
    for (n_, cx, fy, sp) in AUTOS:                                 # Autos auf der Fahrbahn (Linksverkehr)
        setze(n_, cx + OFF, fy + OFF, {'nur_kontakt': True}, sp, art='auto', klassen='a')
    # ---------------------------------------------------------------- Plaetze beleben (Nutzer: Karte etwas leer)
    gk = np.array([list(z) for z in cls])

    def mitte(maske):
        ys, xs = np.nonzero(maske)
        return (xs.min() + xs.max() + 1) * T / 2.0, (ys.min() + ys.max() + 1) * T / 2.0
    sued = np.zeros_like(gk, bool); sued[60 + P:68 + P, 34 + P:84 + P] = True   # offene Platzflaeche ueber dem Buerobau
    bx, by = mitte((gk == 'q') & sued)                           # grosser Platz unten: Mitte aus der Flaeche
    fb = int(by + 40)
    if setze('brunnen/00', bx, fb, {'anim': 'maschine', 'fluessig': [[12, 0, 95, 68, 'cyan']]}, art='gebaeude'):
        for d_ in (80, 96, 112):                                  # Bankpaar gespiegelt an der Brunnenachse
            if all(setze('k38/bank', bx + s_ * d_, fb, {}, s_ > 0) for s_ in (-1, 1)):
                break
    for (tx, ty, sp) in ((72, 66, False), (75, 69, True)):        # Cafe-Ecke rechts vom Brunnen (locker, keine Reihe)
        kachel('platz/03', tx + P, ty + P, {}, sp, klassen='q')
    kachel('platz/12', 70 + P, 70 + P, {}, klassen='q')
    kachel('k38/kiosk', 40 + P, 62 + P, {}, klassen='q')
    nord = np.zeros_like(gk, bool); nord[:30 + P, :24 + P] = True
    sx, sy = mitte((gk == 'b') & nord)                           # Ziegelplatz oben links: Skulptur auf der Mitte
    fs = int(sy + 15)
    if setze('platz/02', sx, fs, {}, art='gebaeude', klassen='b'):
        for d_ in (64, 80):
            if all(setze('platz/01', sx + s_ * d_, fs, {}, klassen='b') for s_ in (-1, 1)):
                break
    achse_r = (x0 + x1 + 1) * T / 2.0                             # Fahnenpaar am Rathaus, gespiegelt
    fertig = False
    for zeile in (26, 27, 25, 28):                                # vordere Ecken der Rathausflaeche
        for d_ in (136, 144, 152):
            n0 = len(objekte)
            a_ = setze('platz/00', achse_r - d_, (zeile + P) * T + T - 1, {'anim': 'wimpel', 'wimpel': [[12, 1, 31, 16]]},
                       False, klassen='gq')
            b_ = setze('platz/00', achse_r + d_, (zeile + P) * T + T - 1, {'anim': 'wimpel', 'wimpel': [[0, 1, 19, 16]]},
                       True, klassen='gq') if a_ else None
            if a_ and b_:
                fertig = True; break
            while len(objekte) > n0:
                objekte.pop(); rects.pop()
        if fertig:
            break
    if not fertig:
        print('Fahnenpaar nicht gesetzt')
    for i, (tx, ty) in enumerate(((48, 32), (57, 64), (14, 12), (80, 30))):   # flach und begehbar
        kachel('k38/taube', tx + P, ty + P, {'ebene': 0}, i % 2 == 1)
    for (tx, ty) in ((60, 13), (50, 70)):
        kachel('k38/zeitung', tx + P, ty + P, {'ebene': 0, 'liegend': True})
    # ---------------------------------------------------------------- Baumguertel am Kartenrand (Nutzer)
    n_w = 0
    for ty in range(rows):
        for tx in range(cols):
            if cls[ty][tx] == 'h' and (tx + ty) % 2 == 0:
                if setze(rnd.choice(WALD), tx * T + T / 2.0, ty * T + T - 1, {'anim': 'baum'}, rnd.random() < 0.5, 'wald'):
                    n_w += 1
    deck = np.zeros((rows * T, cols * T), bool)

    def decken(o):
        al = np.array(Image.open(os.path.join(OBJ, o['datei'])).convert('RGBA'))[..., 3] > 0
        ys, xs = np.nonzero(al)
        ys, xs = ys + o['y'], xs + o['x']
        ok = (ys >= 0) & (ys < rows * T) & (xs >= 0) & (xs < cols * T)
        deck[ys[ok], xs[ok]] = True
    for o in objekte:
        decken(o)
    luecken = 0
    for durchgang in range(2):
        for ty in range(rows):
            for tx in range(cols):
                if cls[ty][tx] == 'h' and deck[ty * T:(ty + 1) * T, tx * T:(tx + 1) * T].mean() < 0.75:
                    for dx in ((0, -5, 5) if durchgang else (0,)):
                        o = setze(rnd.choice(BUSCH + WALD[:2] if durchgang == 0 else BUSCH), tx * T + T / 2.0 + dx,
                                  ty * T + T - 1, {'anim': 'wehen'}, rnd.random() < 0.5, 'wald')
                        if o:
                            decken(o); luecken += 1
                            break
    for o in objekte:
        if o['basis'].startswith('k01/'):
            o['nur_kontakt'] = True
    print('Baumguertel:', n_w, 'Baeume,', luecken, 'Buesche')
    json.dump(objekte, open(os.path.join(OBJ, 'platzierung.json'), 'w'), indent=0)
    print(len(objekte), 'Objekte')


if __name__ == '__main__':
    main()
    import regeln_a02
    regeln_a02.objekte_pruefen('karte39', '')
