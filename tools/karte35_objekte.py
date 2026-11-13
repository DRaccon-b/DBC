"""Objekte fuer Karte 35 (Shinjuku Digital Fog, A03 Nr. 2) -> assets/objekte/karte35/platzierung.json

  python3 tools/karte35_objekte.py && python3 tools/karte35_bauen.py

Grosse Objekte zuerst: neun Gebaeude (PixelLab k35_*, die langen Glasbueros aus einer generierten Haelfte gespiegelt,
Breite wie die Vorlage), Fussgaengerbruecke ueber der mittleren Strasse; dann Strassenbaeume auf den Gruenstreifen,
Strassenmoebel sparsam an den Stellen der Vorlage (Laternen, Baenke, Haltestellen, Automaten, Raeder, Muelleimer),
Autos und Bus im Linksverkehr in ihrer Spur, zuletzt etwas Kleinkram. Wiederverwendet: Strassenmoebel und Autos von
Karte 18, Baeume/Buesche von Karte 01, Kleinkram von Karte 31.
Pixelgenaue Pruefung: kein Objekt ueberlappt ein anderes (2 px), nur Strassenbaeume duerfen vor einer Fassade stehen.
"""
import json, math, os, random, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
import bauwerke

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte35')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte35')
T = 16
FREMD = {}
for i in (0, 1, 4, 5, 12, 14, 18, 41, 42):
    FREMD['k18s/%02d' % i] = 'karte18/strasse/%02d.png' % i
for i in (0, 1, 5, 6, 7, 11):
    FREMD['k18a/%02d' % i] = 'karte18/autos/%02d.png' % i
FREMD['k18a/bus'] = 'karte18/gebaeude/bus.png'
for i in (0, 1, 2, 25, 26, 27, 30):
    FREMD['k01/deko%02d' % i] = 'karte01/deko/%02d.png' % i
for i in (0, 1, 2):
    FREMD['k01/baum%02d' % i] = 'karte01/baeume/%02d.png' % i

# Gebaeude: (sprite, Mitte x in px, Fusszeile, spiegeln) - Flaechen der Vorlage, an die Sprite-Hoehen angepasst
GEBAEUDE = [
    ('gross/turm_a', 144, 22, False), ('gross/turm_b', 352, 22, False),          # zwei Glastuerme oben links
    ('gross/buero_oben', 848, 11, False),                                       # langes Glasbuero oben
    ('wohnblock_b/00', 176, 34, False),                                          # Wohnblock links
    ('gross_buero_mitte/00', 936, 34, False),   # 24 px rechts: Platz fuer die Bruecke                                    # Glasbuero Mitte
    ('schmal_a/00', 1424, 32, False), ('schmal_b/00', 1424, 54, False),          # schmale Wohnhaeuser rechts
    ('wohnblock_b/00', 440, 54, True),                                           # Wohnblock Mitte links (gespiegelt)
    ('gross/buero_unten', 952, 76, False),                                       # Glasbuero unten
]
BRUECKE = ('fussgaengerbruecke/00', 632, 31)                                    # Achse der Strasse (Spalten 36-42)
BAEUME = [(49, 13), (60, 13), (47, 23), (63, 23), (70, 23), (7, 48), (18, 48), (50, 48), (70, 48)]
LATERNEN = [(29, 12), (44, 12), (74, 12), (29, 33), (73, 33), (19, 53), (44, 53), (74, 53), (23, 70),
            (74, 73)]
BAENKE = [(6, 55), (28, 65), (90, 73)]
MOEBEL = [('k18s/41', 23, 34), ('k18s/12', 26, 34), ('k18s/41', 69, 54), ('k18s/00', 72, 29), ('k18s/01', 17, 65),
          ('k18s/42', 19, 65), ('k18s/12', 31, 65), ('k18s/04', 72, 31), ('k18s/04', 11, 52), ('k18s/04', 12, 72),
          ('k18s/05', 66, 54)]
# Fahrzeuge (Linksverkehr): (sprite, Mitte x px, Fuss y px, spiegeln). Waagerecht: Nordspur nach Osten (gespiegelt),
# Suedspur nach Westen; senkrecht: Ostspur nach Sueden.
AUTOS = [('k18a/05', 312, 622, True), ('k18a/bus', 1096, 620, False), ('k18a/00', 824, 942, True),
         ('k18a/11', 380, 990, False), ('k18a/06', 1288, 494, False), ('k18a/07', 600, 812, False),
         ('k18a/06', 1288, 846, False), ('k18a/01', 560, 334, False)]


def halb_gespiegelt(quelle, ziel, breite_halb):
    """Langes symmetrisches Gebaeude aus der generierten linken Haelfte: Haelfte auf die halbe Vorlagenbreite
    (gleichfoermige Glasfront in der Mitte), dann gespiegelt angesetzt."""
    h = Image.open(os.path.join(OBJ, quelle)).convert('RGBA')
    ar = np.array(h)
    ar[ar[..., 3] < 200] = 0                                     # halbtransparente Rauschpixel (Saum) weg
    import karte04_bauen as k4
    ar[~k4.splitter_weg(ar[..., 3] > 0, 40)] = 0                 # lose Splitter weg
    h = Image.fromarray(ar)
    bb = h.getbbox()
    h = h.crop((bb[0], bb[1], bb[0] + breite_halb, bb[3]))
    voll = Image.new('RGBA', (2 * breite_halb, h.height), (0, 0, 0, 0))
    voll.paste(h, (0, 0))
    voll.paste(h.transpose(Image.FLIP_LEFT_RIGHT), (breite_halb, 0))
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
    halb_gespiegelt('gross_buero_oben_halb/00.png', 'gross/buero_oben.png', 336)
    halb_gespiegelt('gross_buero_unten_halb/00.png', 'gross/buero_unten.png', 248)
    for v, q in (('a', 'gross_turm_c/00.png'), ('b', 'gross_turm_c/00.png')):   # Variante c: vollstaendig, mit Rand
        if not os.path.exists(os.path.join(OBJ, q)):
            q = 'gross_turm_b/00.png'
        sp = Image.open(os.path.join(OBJ, q)).convert('RGBA')
        os.makedirs(os.path.join(OBJ, 'gross'), exist_ok=True)
        sp.crop(sp.getbbox()).save(os.path.join(OBJ, 'gross', 'turm_%s.png' % v))
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
        if pruefen:
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
        if not setze(name, cx, fy * T + T - 1, {'gebaeude': True}, sp, 'gebaeude'):
            print('Gebaeude ueberlappt:', name)
    n_, cx, fy = BRUECKE
    if not setze(n_, cx, fy * T + T - 1, {'gebaeude': True}, False, 'gebaeude'):
        print('Bruecke nicht gesetzt')
    # ---------------------------------------------------------------- Strassenbaeume mit Bueschen an den Stammecken
    for i, (tx, ty) in enumerate(BAEUME):
        if kachel('k01/baum%02d' % (i % 3), tx, ty, {'anim': 'baum'}, i % 2 == 1, 'baum', 'n', 'gras'):
            b = objekte[-1]
            seite = 1 if i % 2 else -1
            bb_ = Image.open(os.path.join(OBJ, b['datei'])).getbbox()
            mitte = b['x'] + (bb_[0] + bb_[2]) / 2.0
            bx = int(mitte + seite * 17)                          # Busch an der Stammecke (gewollte Ueberdeckung)
            fy_b = b['y'] + bb_[3] - 1
            if all(k(xx // T, fy_b // T) == 'n' for xx in (bx - 12, bx + 12)):
                setze('k01/deko%02d' % (25, 26)[i % 2], bx, fy_b + 2, {'anim': 'wehen'}, i % 3 == 0, 'klein',
                      pruefen=False, boden='gras')
    # ---------------------------------------------------------------- Strassenmoebel (sparsam, Vorlage)
    for (tx, ty) in LATERNEN:
        kachel('k18s/18', tx, ty, {'anim': 'leuchten'}, klassen='g')
    for (tx, ty) in BAENKE:
        kachel('k18s/14', tx, ty, {}, klassen='g')
    for (n_, tx, ty) in MOEBEL:
        kachel(n_, tx, ty, {'anim': 'leuchten'} if n_ in ('k18s/00', 'k18s/01', 'k18s/42') else {}, klassen='g')
    # ---------------------------------------------------------------- Fahrzeuge in ihrer Spur
    for (n_, cx, fy, sp) in AUTOS:
        if not setze(n_, cx, fy, {'auto': True, 'fest_pos': True}, sp, 'auto'):
            print('Auto nicht gesetzt:', n_, cx, fy)
    # ---------------------------------------------------------------- Kleinkram: Blumen auf den Streifen, Muell am Rand
    gesetzt = []
    kand = [(tx, ty) for ty in range(rows) for tx in range(cols) if cls[ty][tx] == 'n']
    rnd.shuffle(kand)
    for (tx, ty) in kand:
        if len(gesetzt) >= 10:
            break
        if any(abs(tx - x) + abs(ty - y) < 5 or (y == ty and abs(tx - x) < 8) for (x, y) in gesetzt):
            continue
        if not all(k(tx + d, ty) == 'n' for d in (-1, 0, 1)):
            continue
        if setze('k01/deko%02d' % (0, 1, 2, 27, 30)[len(gesetzt) % 5], tx * T + rnd.randint(5, 11), ty * T + 13,
                 {'anim': 'wehen'}, rnd.random() < 0.5, 'klein'):
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
    json.dump(objekte, open(os.path.join(OBJ, 'platzierung.json'), 'w'), indent=0)
    print(len(objekte), 'Objekte')


if __name__ == '__main__':
    main()
    import regeln_a02                                                 # Teleporter frei, Animationen, Korrekturen
    regeln_a02.objekte_pruefen('karte35', '')
