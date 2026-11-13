# Grundgeruest aus karte35 (tools/neue_karte.py) - an die Vorlage von karte36 "Shinjuku Backstreets" anpassen!
"""Objekte fuer Karte 36 (Shinjuku Backstreets, A03 Nr. 3) -> assets/objekte/karte36/platzierung.json

  python3 tools/karte36_objekte.py && python3 tools/karte36_bauen.py

Grosse Objekte zuerst: Gebaeude (lange beige Bloecke, lila Haus und flacher Bau aus generierten Haelften gespiegelt
auf Vorlagenbreite - PixelLab k36_*; Glasbuero von Karte 35 mit reparierten Kanten; Glasbuero von Karte 30), Ladenzeile
aus Ladenfronten von Karte 31 (Cafe, Mart, Drogerie, Ramen); dann Strassenbaeume mittig auf den Gruenstreifen,
Strassenmoebel sparsam, Autos im Linksverkehr, Kleinkram, zuletzt der Baumguertel am Kartenrand (Nutzer).
Pixelgenaue Pruefung (2 px), kein Bodenwall auf Gehweg/Asphalt.
"""
import json, math, os, random, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
import bauwerke

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte36')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte36')
T = 16
FREMD = {}
for i in (0, 1, 4, 5, 12, 14, 18, 41, 42):
    FREMD['k18s/%02d' % i] = 'karte18/strasse/%02d.png' % i
for i in (0, 1, 5, 6, 7, 11):
    FREMD['k18a/%02d' % i] = 'karte18/autos/%02d.png' % i
FREMD['k18a/bus'] = 'karte18/gebaeude/bus.png'
for i in range(8):
    FREMD['k31/laden_%d' % i] = 'karte31/gebaeude/laden_%d.png' % i
FREMD['k30/buero_glas'] = 'karte30/gebaeude/buero_glas.png'
for i in (0, 1, 2, 25, 26, 27, 30):
    FREMD['k01/deko%02d' % i] = 'karte01/deko/%02d.png' % i
for i in (0, 1, 2, 4, 9, 12, 13, 14, 15):
    FREMD['k01/baum%02d' % i] = 'karte01/baeume/%02d.png' % i
WALD = ['k01/baum%02d' % i for i in (0, 1, 2, 4, 9, 15)]                      # Baumguertel am Kartenrand (Nutzer)
BUSCH = ['k01/baum%02d' % i for i in (12, 13, 14)]                             # Luecken im Guertel schliessen

# Gebaeude: (sprite, Mitte x in px, Fusszeile, spiegeln) - Flaechen der Vorlage, an die Sprite-Hoehen angepasst
GEBAEUDE = [                                   # (sprite, Mitte x in px, Fusszeile, spiegeln) - Vorlagenkacheln
    ('gross/wohn_oben', 304, 14, False),       # langer beiger Block oben links (Haelfte gespiegelt)
    ('gross/lila', 800, 11, False),            # lila Haus oben Mitte
    ('gross/buero_mitte', 1272, 13, False),    # Glasbuero oben rechts (Karte 35, Kanten repariert)
    ('gross/wohn_links', 240, 39, False),      # beiger Block links Mitte
    ('k30/buero_glas', 1216, 54, False),       # Glasbuero rechts Mitte (Karte 30)
    ('gross/flach', 256, 57, False),   # eine Gehwegreihe vor der Front           # flacher Ladenbau links unten
    ('gross/wohn_unten', 864, 77, False),      # langer beiger Block unten
]
LAEDEN = ['k31/laden_2', 'k31/laden_0', 'k31/laden_7', 'k31/laden_1']   # Cafe, Mart, Drogerie, Ramen (Karte 31)
LAEDEN_MITTE, LAEDEN_FUSS = 744, 43
BAEUME = [(41, 16), (50, 16), (72, 16), (84, 16), (90, 17), (47, 33), (6, 41), (24, 41),
          (80, 55), (5, 69), (22, 75), (36, 75), (79, 75), (81, 70)]
LATERNEN = [(25, 20), (57, 20), (68, 21), (25, 41), (36, 42), (68, 41), (25, 57), (84, 65)]
BAENKE = [(19, 20), (72, 31), (15, 44), (85, 57), (12, 73), (73, 73)]
MOEBEL = [('k18s/41', 47, 22), ('k18s/00', 76, 65), ('k18s/12', 9, 44), ('k18s/12', 15, 73),
          ('k18s/04', 23, 46), ('k18s/04', 79, 31)]
# Fahrzeuge (Linksverkehr): waagerecht Nordspur nach Osten (Van gespiegelt), senkrecht Ostspur nach Sueden (k18a/06)
AUTOS = [('k18a/06', 1024, 270, False), ('k18a/11', 792, 408, True), ('k18a/06', 512, 588, False),
         ('k18a/06', 1464, 600, False), ('k18a/11', 1144, 975, True), ('k18a/06', 1464, 1120, False)]


def kanten_ergaenzen(quelle, ziel, breite=2):
    """Generiertes Gebaeude mit links/rechts abgeschnittener Kante reparieren (Nutzer, Regel 'Sprites auf Schnittkanten
    pruefen'): je Seite `breite` px Eckpfeiler in der Farbe der Randspalte ergaenzen und 1 px dunkle Aussenkontur."""
    a = np.array(Image.open(os.path.join(OBJ, quelle)).convert('RGBA'))
    h, w = a.shape[:2]
    n = breite + 1
    out = np.zeros((h, w + 2 * n, 4), np.uint8)
    out[:, n:n + w] = a
    for y in range(h):
        for seite, x_rand, x_neu in ((-1, 0, range(1, n)), (1, w - 1, range(n + w, n + w + breite))):
            if a[y, x_rand, 3] < 200:
                continue
            for x in x_neu:
                out[y, x] = a[y, x_rand]
            k = 0 if seite < 0 else n + w + breite
            out[y, k, :3] = (a[y, x_rand, :3].astype(int) * 0.4).astype(np.uint8)
            out[y, k, 3] = 255
    Image.fromarray(out).save(os.path.join(OBJ, ziel))


def halb_gespiegelt(quelle, ziel, breite_halb, eingang=True):
    """Langes symmetrisches Gebaeude aus der generierten linken Haelfte: Haelfte auf die halbe Vorlagenbreite
    (gleichfoermige Glasfront in der Mitte), dann gespiegelt angesetzt."""
    h = Image.open(os.path.join(OBJ, quelle)).convert('RGBA')
    ar = np.array(h)
    ar[ar[..., 3] < 200] = 0                                     # halbtransparente Rauschpixel (Saum) weg
    r_, g_, b_ = ar[..., 0].astype(int), ar[..., 1].astype(int), ar[..., 2].astype(int)
    mg = (ar[..., 3] > 0) & (r_ - g_ > 60) & (b_ - g_ > 60)          # Magenta-Reste der Freistellung (Pruefung)
    hell = mg & ((r_ + g_ + b_) > 420)
    ar[hell, :3] = (176, 180, 186); ar[mg & ~hell, :3] = (58, 60, 70)
    import karte04_bauen as k4
    ar[~k4.splitter_weg(ar[..., 3] > 0, 40)] = 0                 # lose Splitter weg
    hh_, ww_ = ar.shape[:2]                                       # Schnittkanten am Bildrand reparieren (Pruefliste)
    if (ar[:, 0, 3] > 0).sum() > hh_ * 0.3:                      # linke Kante angeschnitten: Pfeiler + Kontur ergaenzen
        neu = np.zeros((hh_, ww_ + 3, 4), np.uint8); neu[:, 3:] = ar
        for y in range(hh_):
            if ar[y, 0, 3] > 0:
                neu[y, 1:3] = ar[y, 0]
                neu[y, 0, :3] = (ar[y, 0, :3].astype(int) * 0.4).astype(np.uint8); neu[y, 0, 3] = 255
        ar = neu
    hh_, ww_ = ar.shape[:2]
    if (ar[-1, :, 3] > 0).sum() > ww_ * 0.3 and ar[-1, :, :3].astype(int).sum(-1).mean() > 150:   # Sockel angeschnitten
        neu = np.zeros((hh_ + 3, ww_, 4), np.uint8); neu[:hh_] = ar
        for x in range(ww_):
            if ar[-1, x, 3] > 0:
                neu[hh_:hh_ + 2, x] = ar[-1, x]
                neu[hh_ + 2, x, :3] = (ar[-1, x, :3].astype(int) * 0.4).astype(np.uint8); neu[hh_ + 2, x, 3] = 255
        ar = neu
    h = Image.fromarray(ar)
    bb = h.getbbox()
    h = h.crop((bb[0], bb[1], bb[0] + breite_halb, bb[3]))
    voll = Image.new('RGBA', (2 * breite_halb, h.height), (0, 0, 0, 0))
    voll.paste(h, (0, 0))
    voll.paste(h.transpose(Image.FLIP_LEFT_RIGHT), (breite_halb, 0))
    va = np.array(voll)
    hv = va.shape[0]
    wand = (va[max(0, hv - 14):hv - 6, :, 3] > 0).any(0)           # Spalten mit Wand/Sockel kurz ueber dem Fuss
    va[hv - 6:, ~wand] = 0                                       # Saum/Balken seitlich ueber die Wand hinaus weg
    dunkel = (va[..., :3].astype(int).sum(-1) < 90) & (va[..., 3] > 0)
    for yy in range(hv - 1, hv - 7, -1):                         # fast schwarze volle Fusszeilen (Freistell-Rest) weg
        if dunkel[yy].mean() > 0.6:
            va[yy] = 0
        else:
            break
    deck = (va[..., 3] > 0).mean(1)                              # Unterkante: gezackte Saumzeilen (< 90 % deckend) weg
    unten = max(i for i in range(len(deck)) if deck[i] > 0.9)
    va[unten + 1:] = 0
    voll = Image.fromarray(va).crop((0, 0, voll.width, unten + 1))
    if eingang:                                                  # Eingang mittig im Erdgeschoss (wie Glasbuero Mitte)
        tuer = Image.open(os.path.join(OBJ, 'gross_buero_mitte/00.png')).convert('RGBA').crop((170, 136, 248, 180))   # ohne Umrisszeile darunter (lose Pixel)
        voll.alpha_composite(tuer, (voll.width // 2 - tuer.width // 2, voll.height - tuer.height))
    os.makedirs(os.path.dirname(os.path.join(OBJ, ziel)), exist_ok=True)
    voll.save(os.path.join(OBJ, ziel))


def main():
    rnd = random.Random(35)
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cls = lay['klassen']
    cols, rows = lay['groesse']

    def k(tx, ty):
        return cls[min(rows - 1, max(0, ty))][min(cols - 1, max(0, tx))]

    for name, quelle in FREMD.items():
        ziel = os.path.join(OBJ, name + '.png')
        os.makedirs(os.path.dirname(ziel), exist_ok=True)
        shutil.copy(os.path.join(ROOT, 'assets', 'objekte', quelle), ziel)
    kanten_ergaenzen('gross_buero_mitte/00.png', 'gross/buero_mitte.png')   # Kanten waren abgeschnitten (Karte 35)
    halb_gespiegelt('gross_beige_halb_hoch_b/00.png', 'gross/wohn_oben.png', 240, eingang=False)   # Vorlagenbreiten
    halb_gespiegelt('gross_beige_halb_hoch_b/00.png', 'gross/wohn_unten.png', 240, eingang=False)
    halb_gespiegelt('gross_beige_halb_flach_b/00.png', 'gross/wohn_links.png', 176, eingang=False)
    halb_gespiegelt('gross_lila_halb_b/00.png', 'gross/lila.png', 144, eingang=False)
    halb_gespiegelt('gross_flach_halb/00.png', 'gross/flach.png', 144, eingang=False)
    os.makedirs(os.path.join(OBJ, 'gross'), exist_ok=True)
    P = lay.get('versatz', 0)                                    # Karte ringsum erweitert: alle Vorlagenpositionen + P
    OFF = P * T
    tps = [(t['x'] * T, t['y'] * T, (t['x'] + t['b']) * T - 1, (t['y'] + t['h']) * T - 1) for t in lay['teleporter']]
    objekte, rects = [], []                                      # rects: (x0, y0, x1, y1, art, fuss_y)

    def schnitt(a, b, rand=0):
        return not (a[2] + rand < b[0] or b[2] + rand < a[0] or a[3] + rand < b[1] or b[3] + rand < a[1])

    def setze(name, cx, fy, opt=None, spiegeln=False, art='objekt', pruefen=True, boden=None):
        """Pixelgenau: Mitte cx, unterste Sprite-Zeile auf fy. Prueft 2 px Abstand zu allen Objekten; Baeume duerfen vor
        (unterhalb des Fusses) einer Fassade stehen."""
        sp = Image.open(os.path.join(OBJ, name + '.png')).convert('RGBA')
        if spiegeln:
            sp = sp.transpose(Image.FLIP_LEFT_RIGHT)
        if boden:
            sp = bauwerke.bodenfuss(sp, boden, 'baum' if art == 'baum' else 'klein')
        datei = 'varianten/%s%s%s.png' % (name.replace('/', '-'), '_' + boden if boden else '', '_m' if spiegeln else '')
        os.makedirs(os.path.join(OBJ, 'varianten'), exist_ok=True)
        sp.save(os.path.join(OBJ, datei))
        bb = sp.getbbox()
        x = int(round(cx - (bb[0] + bb[2]) / 2.0))
        y = int(fy - (bb[3] - 1))
        r = (x + bb[0], y + bb[1], x + bb[2] - 1, y + bb[3] - 1)
        if art == 'wald':                                        # Baumguertel: nie ueber Teleporter oder andere Objekte
            if any(schnitt(r, t_, 3) for t_ in tps):
                return None
            y_a, y_b = max(0, r[1] // T), min(rows - 1, r[3] // T)
            x_a, x_b = max(0, r[0] // T), min(cols - 1, r[2] // T)
            for yy in range(y_a, y_b + 1):                       # Krone nicht ueber Stadt/Ausgang (max. 4 px)
                for xx in range(x_a, x_b + 1):
                    if cls[yy][xx] != 'h':
                        ov_y = min(r[3], yy * T + T - 1) - max(r[1], yy * T) + 1
                        ov_x = min(r[2], xx * T + T - 1) - max(r[0], xx * T) + 1
                        if ov_y > 4 and ov_x > 4:
                            return None
            if any(art2 != 'wald' and schnitt(r, (a0, a1, a2, a3), 2) for (a0, a1, a2, a3, art2, fy2) in rects):
                return None
        elif pruefen:
            for (a0, a1, a2, a3, art2, fy2) in rects:
                if art == 'baum' and art2 == 'gebaeude' and fy > fy2 + 8:
                    continue                                     # Strassenbaum vor der Fassade (gewollt)
                if art2 == 'baum' and art == 'gebaeude':
                    continue
                if schnitt(r, (a0, a1, a2, a3), 2):
                    return None
        o = {'datei': datei, 'basis': name, 'x': x, 'y': y, 'fuss': bb[3] - 1, 'kachel': [int(cx) // T, int(fy) // T],
             'ebene': 1}
        o.update(opt or {})
        o.setdefault('ohne_wall', True)                          # Stadt: harte Kanten, kein Bodenwall aus Pflaster/Asphalt
        objekte.append(o)
        rects.append(r + (art, fy))
        return o

    def kachel(name, tx, fy_tile, opt=None, spiegeln=False, art='objekt', klassen='gn', boden=None):
        """Am Raster: kleinster Kachelblock, waagerecht mittig, Fuss buendig (Regel 1b); naechste freie Stelle bis 2."""
        sp = Image.open(os.path.join(OBJ, name + '.png'))
        bw = sp.getbbox()[2] - sp.getbbox()[0]
        wt = max(1, math.ceil(bw / T))
        for d in range(3):
            for dy in range(-d, d + 1):
                for dx in range(-d, d + 1):
                    if max(abs(dx), abs(dy)) != d:
                        continue
                    x0, y = tx + dx - (wt - 1) // 2, fy_tile + dy
                    if not all(k(x0 + i, y) in klassen for i in range(wt)):
                        continue
                    cx = x0 * T + wt * T / 2.0
                    if setze(name, cx, y * T + T - 1, opt, spiegeln, art, boden=boden):
                        return True
        print('nicht gesetzt:', name, tx, fy_tile)
        return False

    # ---------------------------------------------------------------- Gebaeude und Bruecke
    for (name, cx, fy, sp) in GEBAEUDE:
        if not setze(name, cx + OFF, (fy + P) * T + T - 1, {'gebaeude': True, 'ohne_wall': True}, sp, 'gebaeude'):
            print('Gebaeude ueberlappt:', name)
    breiten = [Image.open(os.path.join(OBJ, n_ + '.png')).getbbox() for n_ in LAEDEN]     # Ladenzeile lueckenlos
    x = LAEDEN_MITTE + OFF - sum(bb[2] - bb[0] for bb in breiten) // 2
    for n_, bb in zip(LAEDEN, breiten):
        w = bb[2] - bb[0]
        if not setze(n_, x + w / 2.0, (LAEDEN_FUSS + P) * T + T - 1, {'gebaeude': True}, False, 'gebaeude',
                     pruefen=False):                             # Ladenzeile: Fronten stossen gewollt aneinander
            print('Laden ueberlappt:', n_)
        x += w
    # ---------------------------------------------------------------- Strassenbaeume mit Bueschen an den Stammecken
    def baum_mittig(name, tx, ty, opt, spiegeln):
        """Strassenbaum mittig auf dem Gruenstreifen (Nutzer): Stammfuss auf der senkrechten Mitte des Streifens,
        waagerecht auf der Kachelmitte; weicht bei Ueberlappung um bis zu 2 Spalten aus."""
        for dx in (0, 1, -1, 2, -2):
            x = tx + dx
            if k(x, ty) != 'n' or k(x - 1, ty) != 'n' or k(x + 1, ty) != 'n':
                continue
            oben, unten = ty, ty
            while k(x, oben - 1) == 'n':
                oben -= 1
            while k(x, unten + 1) == 'n':
                unten += 1
            fy = (oben * T + (unten + 1) * T) // 2 + 4
            if setze(name, x * T + T / 2.0, fy, opt, spiegeln, 'baum'):
                return True
        print('Baum nicht gesetzt:', tx, ty)
        return False

    for i, (tx, ty) in enumerate(BAEUME):
        tx, ty = tx + P, ty + P
        if baum_mittig('k01/baum%02d' % (i % 3), tx, ty, {'anim': 'baum'}, i % 2 == 1):
            b = objekte[-1]
            seite = 1 if i % 2 else -1
            bb_ = Image.open(os.path.join(OBJ, b['datei'])).getbbox()
            mitte = b['x'] + (bb_[0] + bb_[2]) / 2.0
            bx = int(mitte + seite * 17)                          # Busch an der Stammecke (gewollte Ueberdeckung)
            fy_b = b['y'] + bb_[3] - 1
            for bx in (bx, int(mitte - seite * 17), int(mitte + seite * 13), int(mitte - seite * 13)):  # andere Ecke / naeher
                if all(k(xx // T, fy_b // T) == 'n' for xx in (bx - 9, bx + 9)):
                    break
            else:
                bx = None
            if bx is not None:
                setze('k01/deko%02d' % (25, 26)[i % 2], bx, fy_b - 1, {'anim': 'wehen', 'nur_kontakt': True, 'ohne_wall': True}, i % 3 == 0,
                      'klein', pruefen=False)
    # ---------------------------------------------------------------- Strassenmoebel (sparsam, Vorlage)
    for (tx, ty) in LATERNEN:
        kachel('k18s/18', tx + P, ty + P, {'anim': 'leuchten'}, klassen='g')
    for (tx, ty) in BAENKE:
        kachel('k18s/14', tx + P, ty + P, {}, klassen='g')
    for (n_, tx, ty) in MOEBEL:
        kachel(n_, tx + P, ty + P, {'anim': 'leuchten'} if n_ in ('k18s/00', 'k18s/01', 'k18s/42') else {}, klassen='g')
    # ---------------------------------------------------------------- Fahrzeuge in ihrer Spur
    for (n_, cx, fy, sp) in AUTOS:
        if not setze(n_, cx + OFF, fy + OFF, {'auto': True, 'fest_pos': True, 'nur_kontakt': True}, sp, 'auto'):
            print('Auto nicht gesetzt:', n_, cx, fy)
    # ---------------------------------------------------------------- Kleinkram: Blumen auf den Streifen, Muell am Rand
    gesetzt, gesetzt_m = [], []
    kand = [(tx, ty) for ty in range(rows) for tx in range(cols) if cls[ty][tx] == 'n']
    rnd.shuffle(kand)
    for (tx, ty) in kand:
        if len(gesetzt) >= 10:
            break
        if any(abs(tx - x) + abs(ty - y) < 5 or (y == ty and abs(tx - x) < 8) for (x, y) in gesetzt):
            continue
        if not all(k(tx + d, ty) == 'n' for d in (-1, 0, 1)):
            continue
        if any(o_['basis'].startswith('k01/baum') and abs(o_['kachel'][0] - tx) <= 2 and abs(o_['kachel'][1] - ty) <= 1
               for o_ in objekte):
            continue                                              # Regel 5d: nichts auf Stammhoehe neben dem Baum
        motiv = (0, 1, 2, 27, 30)[len(gesetzt) % 5]
        if any(abs(tx - x) < 12 and abs(ty - y) < 4 and m == motiv for (x, y, m) in gesetzt_m):
            continue                                              # gleiches Motiv nicht auf demselben Streifen
        if setze('k01/deko%02d' % motiv, tx * T + rnd.randint(5, 11), ty * T + 11,
                 {'anim': 'wehen', 'nur_kontakt': True, 'ohne_wall': True}, rnd.random() < 0.5, 'klein'):
            gesetzt_m.append((tx, ty, motiv))
            gesetzt.append((tx, ty))
    MUELL = sorted(f[:-4] for f in os.listdir(os.path.join(OBJ, 'muell_klein')) if f.endswith('.png') and not f.endswith('_m.png'))
    kand = [(tx, ty) for ty in range(rows) for tx in range(cols) if cls[ty][tx] == 'g'
            and any(k(tx + dx, ty + dy) == 'a' for dx in (-2, -1, 0, 1, 2) for dy in (-2, -1, 0, 1, 2))
            and all(k(tx + dx, ty + dy) == 'g' for dx in (-1, 0, 1) for dy in (-1, 0, 1))]   # nicht auf dem Bordstein
    rnd.shuffle(kand)
    gesetzt = []
    for (tx, ty) in kand:
        if len(gesetzt) >= 22:
            break
        if any(abs(tx - x) + abs(ty - y) < 6 for (x, y) in gesetzt):
            continue
        if setze('muell_klein/' + MUELL[len(gesetzt) % len(MUELL)], tx * T + rnd.randint(4, 12), ty * T + rnd.randint(8, 14),
                 {'liegend': True}, rnd.random() < 0.5, 'klein'):
            gesetzt.append((tx, ty))
    # ---------------------------------------------------------------- Baumguertel am Kartenrand (Nutzer)
    n_w = 0
    for ty in range(rows):
        for tx in range(cols):
            if cls[ty][tx] == 'h' and (tx + ty) % 2 == 0:
                if setze(rnd.choice(WALD), tx * T + T / 2.0, ty * T + T - 1, {'anim': 'baum'}, rnd.random() < 0.5, 'wald'):
                    n_w += 1
    deck = np.zeros((rows * T, cols * T), bool)                  # Luecken schliessen (kein leerer Rasen im Guertel)
    for (a0, a1, a2, a3, art2, fy2) in rects:
        deck[max(0, a1):a3 + 1, max(0, a0):a2 + 1] = True
    luecken = 0
    for ty in range(rows):
        for tx in range(cols):
            if cls[ty][tx] == 'h' and deck[ty * T:(ty + 1) * T, tx * T:(tx + 1) * T].mean() < 0.7:
                if setze(rnd.choice(BUSCH), tx * T + T / 2.0, ty * T + T - 1, {'anim': 'wehen'}, rnd.random() < 0.5, 'wald'):
                    a0, a1, a2, a3 = rects[-1][:4]
                    deck[max(0, a1):a3 + 1, max(0, a0):a2 + 1] = True
                    luecken += 1
    print('Baumguertel:', n_w, 'Baeume,', luecken, 'Buesche')
    json.dump(objekte, open(os.path.join(OBJ, 'platzierung.json'), 'w'), indent=0)
    print(len(objekte), 'Objekte')


if __name__ == '__main__':
    main()
    import regeln_a02                                                 # Teleporter frei, Animationen, Korrekturen
    regeln_a02.objekte_pruefen('karte36', '')
