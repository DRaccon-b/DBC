"""Objekte fuer Karte 07 (The Holy Peaks) - am 16x16-Raster, ohne Ueberlappungen.

  python3 tools/karte07_objekte.py && python3 tools/karte07_bauen.py

Jedes Objekt im kleinsten Kachelblock (Fuss unten buendig, waagerecht zentriert). Bodenfuss nach Untergrund.
Freie Deko/Baeume nur, wenn sie mit 2 px Abstand nichts beruehren. Wiederverwendet: Deko aus Karte 01,
verschneite Tannen aus Karte 05.
"""
import json, math, os, random, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageFilter
import bauwerke

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte07')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte07')
T = 16
FREMD = {'k05/tanne%d' % i: 'karte05/baeume/0%d.png' % i for i in range(3)}
for i in (1, 2, 3, 4, 5, 6, 8, 9, 10, 11, 26, 27, 31):
    FREMD['k01/deko%02d' % i] = 'karte01/deko/%02d.png' % i
for i in (0, 4, 13, 36):
    FREMD['k05/klein%02d' % i] = 'karte05/klein/%02d.png' % i
# Einbettung: Bueschel und Blumen vor dem Sockel von Felsen, Baeumen, Kristallen, Stuempfen
# neue Deko-Sets (PixelLab k7_deko_*) + bewaehrte aus Karte 01/05
G_, S_, ST_ = 'deko_gras/%02d', 'deko_schnee/%02d', 'deko_stein/%02d'
BUESCHEL_GRAS = ['k01/deko06', 'k01/deko05', 'k01/deko26'] + [G_ % i for i in (0, 1, 2, 3, 11, 12, 15, 40, 43, 50, 52, 54, 58, 59, 63)]
BLUMEN_GRAS = ['k01/deko01', 'k01/deko02', 'k01/deko03', 'k01/deko27'] + [G_ % i for i in (4, 5, 6, 7, 8, 9, 13, 14, 29, 32, 39, 42, 48, 55, 57, 62)]
KLEINKRAM_GRAS = [G_ % i for i in (10, 16, 17, 38, 56, 19, 27)]
BUESCHEL_SCHNEE = ['k05/klein00', 'k05/klein13'] + [S_ % i for i in (0, 1, 2, 12, 15, 21, 23, 29, 34, 35, 39, 50, 53)]
BLUMEN_SCHNEE = ['k05/klein04'] + [S_ % i for i in (5, 6, 9, 14, 28, 30, 31, 36, 41, 44, 45)]
KLEINKRAM_SCHNEE = [S_ % i for i in (8, 18, 19, 47, 52, 58, 59)]
DEKO_FELS = [ST_ % i for i in (0, 1, 3, 6, 10, 14, 19, 34, 36, 43, 47, 54)]
BAMBUS_GRAS, BAMBUS_SCHNEE = ['bambus/00', 'bambus/02'], ['bambus/01', 'bambus/03']
BAUM_BAMBUS = {'neu/00', 'neu/01', 'turm/03'}
DEKO_GRAS = ['k01/deko05', 'k01/deko06', 'k01/deko26', 'k01/deko27']
WIND = {'k01/deko05', 'k01/deko06', 'k01/deko26', 'k01/deko27'}
SL, PL, BAMBUS = 'mittel/00', 'mittel/01', 'mittel/05'
KIEFER, TANNE, GROSSKIEFER = 'neu/00', 'neu/01', 'turm/03'      # neue Baeume (statt Bonsai / alter Schneekiefer)
BUSCH, AZALEE = 'neu/02', 'neu/03'
OBELISK, KRISTALL = 'mittel/02', 'mittel/03'
NADEL, NADEL_BODEN = 'gross/03', 'gross/03_land'                # Felsnadel mit / ohne Wolkensockel
BAEUME = {KIEFER, TANNE, GROSSKIEFER}
FRUECHTE = ['kuerbis', 'kohl', 'tomate', 'mais', 'karotte', 'erdbeere', 'aubergine', 'melone', 'zwiebel',
            'heidelbeere', 'weizen', 'kartoffel', 'ruebe', 'rote_bete', 'paprika', 'blumenkohl']
OBSTBAEUME = ['frucht/apfelbaum', 'frucht/apfelbaum', 'frucht/kirschbusch', 'frucht/trauben']
TURM_G, TURM_K, TURM_F, TURM_S = 'turm/schwarz_gross', 'turm/schwarz_klein', 'turm/schwarz_gefallen', 'turm/schwarz_stumpf'
LILA = 'mittel/13'
FELDER = [(26, 43), (49, 67)]                                   # Beetfelder (Spalten), Zeilen 64..81
OBSTGARTEN = (72, 83, 64, 80)
EINBETTEN = {'gross/03_land', 'mittel/stumpf', 'mittel/runenstein', 'neu/00', 'neu/01', 'turm/03', 'mittel/13',
             'mittel/03', 'mittel/07', 'frucht/apfelbaum', 'frucht/kirschbusch'}
RING = (30, 62, 4, 26)                                          # Steinkreis oben: keine Felsen

FEST = [
    # Gipfel: Wirbelportal, Drachenschrein, Obelisk, Laternen (max. 4 Steinlaternen im Schrein)
    ('mittel/12', 6.5, 7, {'anim': 'portal'}),
    # Reich des azurblauen Drachen (Schreinhof): Drachenstatue um Jadesaeule, Marmorweg, Kugelsockel, Banner
    ('azul_gross/00', 87, 12, {'anim': 'leuchten'}),
    ('azul/07', 79, 12, {}), ('azul/07', 79, 19, {'spiegeln': True}),
    ('azul/00', 82, 12, {'anim': 'leuchten'}), ('azul/00', 82, 19, {'anim': 'leuchten'}),
    ('azul/02', 94, 11, {'anim': 'leuchten'}), ('azul/02', 94, 21, {'anim': 'leuchten'}),
    ('azul/01', 79, 6, {'anim': 'wehen'}), ('azul/01', 82, 6, {'anim': 'wehen'}),
    ('azul/01', 92, 6, {'anim': 'wehen'}), ('azul/01', 95, 6, {'anim': 'wehen'}),
    ('azul/04', 86.5, 21, {}), ('azul/09', 91, 22, {'anim': 'glitzern'}),
    ('azul/03', 79, 23, {'anim': 'glitzern'}), ('azul/05', 82, 23, {}), ('azul/03', 95, 16, {'anim': 'glitzern'}),
    (PL, 66, 22, {'anim': 'leuchten'}),
    (PL, 27, 23, {'anim': 'leuchten', 'spiegeln': True}),
    ('mittel/13', 59, 39, {}), ('mittel/13', 61, 49, {}),
    # Pagodenhof
    ('pagode/00', 80, 45, {}), (BAMBUS, 73, 39, {'anim': 'wehen'}), (BAMBUS, 87, 39, {'anim': 'wehen'}),
    (SL, 73, 45, {}), (SL, 87, 45, {}), (PL, 72, 32, {'anim': 'leuchten'}),
    (PL, 88, 32, {'anim': 'leuchten', 'spiegeln': True}),
    (KRISTALL, 87, 53, {'anim': 'glitzern'}), (AZALEE, 86, 54, {}),
    (PL, 82, 55, {'anim': 'leuchten', 'spiegeln': True}), (PL, 16, 54, {'anim': 'leuchten'}),
    # untere Terrasse
    ('gross/02', 8.5, 66, {}), ('gross/02', 13.5, 79, {}), ('gross/01', 9.5, 85, {}),
    ('mittel/11', 6, 80, {}), ('mittel/15', 18, 80, {}), (SL, 5, 85, {}), (PL, 4, 78, {'anim': 'leuchten'}),
    (KRISTALL, 90.5, 70, {'anim': 'glitzern'}), (BUSCH, 91.5, 71, {}),
    ('gross/01', 90.5, 80, {}), ('mittel/10', 90.5, 73, {}),
    (SL, 86, 67, {}), (SL, 95, 67, {}), (BAMBUS, 86, 77, {'anim': 'wehen'}), (BAMBUS, 95, 77, {'anim': 'wehen'}),
    (PL, 95, 64, {'anim': 'leuchten', 'spiegeln': True}),
    (BAMBUS, 45, 66, {'anim': 'wehen'}), (BAMBUS, 22, 70, {'anim': 'wehen'}), (BAMBUS, 6, 72, {'anim': 'wehen'}),
    (BAMBUS, 9, 72, {'anim': 'wehen'}), (BAMBUS, 12, 72, {'anim': 'wehen'}), (BAMBUS, 70, 73, {'anim': 'wehen'}),
    (PL, 46.5, 76, {'anim': 'leuchten', 'spiegeln': True}), (PL, 69.5, 81, {'anim': 'leuchten'}),
    # umgekippte schwarze Tuerme
    # fuenf schwarze Tuerme wie die Spitzen eines Pentagramms um die Arena (Steinkreis, Mitte 47/15)
    (TURM_G, 47, 4, {}), (TURM_G, 62, 11, {}), (TURM_G, 57, 24, {}), (TURM_G, 37, 24, {}), (TURM_G, 32, 11, {}),
    # Kristallsaeulen verteilt, jeweils mit Baum/Strauch halb davor
    (LILA, 12, 30, {}), (TANNE, 13.5, 31, {'anim': 'baum'}),
    (KRISTALL, 45, 33, {'anim': 'glitzern'}), (AZALEE, 46.5, 34, {}),
    (KRISTALL, 64, 48, {'anim': 'glitzern'}), (KIEFER, 65.5, 49, {'anim': 'baum', 'spiegeln': True}),
    (LILA, 24, 67, {}), (BUSCH, 24.5, 68, {}),
    
    (LILA, 92, 38, {}), (AZALEE, 93, 39, {}),
    (LILA, 5, 49, {}), (TANNE, 6.5, 50, {'anim': 'baum', 'spiegeln': True}),
    # Felsnadeln ohne Wolken auf der Insel
    (NADEL_BODEN, 17, 35, {}), (NADEL_BODEN, 13, 45, {}), (NADEL_BODEN, 41, 58, {}),
    # grosse Kiefern
    (GROSSKIEFER, 90, 58, {'anim': 'baum'}), (GROSSKIEFER, 66.5, 58, {'anim': 'baum', 'spiegeln': True}),
    # Felsnadeln in den Wolkenbergen
    # (nur im Wolkenmeer, Sockel nie auf einer Felswand)
    (NADEL, -2, 30, {}), (NADEL, -2, 48, {}), (NADEL, -3, 12, {}), (NADEL, -3, 68, {}), (NADEL, -2, 84, {}),
    (NADEL, 102, 22, {}), (NADEL, 102, 56, {}), (NADEL, 103, 8, {}), (NADEL, 103, 72, {}), (NADEL, 102, 88, {}),
    (NADEL, 14, 95, {}), (NADEL, 31, 95, {}), (NADEL, 47, 95, {}), (NADEL, 61, 95, {}),
    (NADEL, 78, 95, {}), (NADEL, 2, 32, {}), (NADEL, 63, 90, {}), (NADEL, 92, 95, {}),
]
STUMPF_PLAETZE = [(49, 57), (54, 38)]
RUNEN_PLAETZE = [(40, 37), (57, 31), (89, 51), (27, 58), (65, 54)]
BAUM_PLAETZE = [(52, 35), (40, 40), (53, 51), (66, 39), (92, 34), (14, 68), (89, 59)]   # weniger Baeume (Nutzer)


def main():
    rnd = random.Random(7)
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cls = lay['klassen']
    hoehe = [[int(c) for c in r] for r in lay['hoehe']]
    cols, rows = lay['groesse']
    R = lay.get('rand', 0)
    for name, quelle in FREMD.items():
        ziel = os.path.join(OBJ, name + '.png')
        if not os.path.exists(ziel):
            os.makedirs(os.path.dirname(ziel), exist_ok=True)
            shutil.copy(os.path.join(ROOT, 'assets', 'objekte', quelle), ziel)
    W_, H_ = cols * T, rows * T
    pix = np.zeros((H_, W_), bool)
    gesperrt = set()
    for (x0, x1, y0, y1) in lay['treppen']:
        for y in range(y0 - 1, y1 + 2):
            for x in range(x0 - 1, x1 + 2):
                gesperrt.add((x, y))
    bx0, by0, bx1, by1 = lay['bruecke']
    for y in range(by0 - 3, by1 + 5):
        for x in range(bx0 - 2, bx1 + 3):
            gesperrt.add((x, y))
    for tp in lay['teleporter']:
        for y in range(tp['y'] - 1, tp['y'] + tp['h'] + 1):
            for x in range(tp['x'] - 1, tp['x'] + tp['b'] + 1):
                gesperrt.add((x, y))
    # Kanten: 3 Zeilen unter jeder Hochkante (Felsfront) und die Kante selbst freihalten
    for y in range(rows - 1):
        for x in range(cols):
            if hoehe[y][x] > hoehe[y + 1][x]:
                for k in range(0, 4):
                    gesperrt.add((x, y + k))
            for dx in (-1, 1):
                if 0 <= x + dx < cols and hoehe[y][x] != hoehe[y][x + dx]:
                    gesperrt.add((x, y))
    cache, alpha, objekte = {}, {}, []
    rnd2 = random.Random(23)
    # Wandkacheln: Kante der hoeheren Ebene + Felsfront darunter (3 Kacheln, zur Wolke 4), Seitenwaende
    wand = set()
    for y in range(rows - 1):
        for x in range(cols):
            if hoehe[y][x] > hoehe[y + 1][x]:
                for k in range(0, (4 if hoehe[y + 1][x] == 0 else 3) + 1):
                    wand.add((x, y + k))
            for dx in (-1, 1):
                if 0 <= x + dx < cols and hoehe[y][x] < hoehe[y][x + dx]:
                    wand.add((x, y))

    def boden(tx, ty):
        k = cls[min(rows - 1, max(0, ty))][min(cols - 1, max(0, tx))]
        return 'sand' if k in 'nw' else 'beton' if k in 'prf' else 'gras'

    def setze(name, fx, fy, opt, frei=False, nur=None, abs_=False, _versuch=False):
        opt0 = dict(opt)
        opt = dict(opt)
        spiegeln = opt.pop('spiegeln', False)
        hoch = opt.pop('hoch', 0)
        if not abs_:
            fx, fy = fx + R, fy + R
        tx, ty = int(math.floor(fx)), int(fy)
        if frei and (tx, ty) in gesperrt:
            return False
        if nur:                                                # ganzer Block muss auf dieser Klasse liegen
            sp0 = Image.open(os.path.join(OBJ, name + '.png'))
            wt0 = math.ceil(sp0.width / T) + 2
            bx0 = int(round(fx + 0.5 - wt0 / 2.0))
            for xx in range(bx0, bx0 + wt0):
                for yy in range(ty - 2, ty + 2):
                    if not (0 <= xx < cols and 0 <= yy < rows) or cls[yy][xx] not in nur:
                        return False
        b = boden(tx, ty) if hoehe[min(rows - 1, ty)][min(cols - 1, tx)] > 0 else None
        key = (name, b, spiegeln)
        if key not in cache:
            sp = Image.open(os.path.join(OBJ, name + '.png')).convert('RGBA')
            if spiegeln:
                sp = sp.transpose(Image.FLIP_LEFT_RIGHT)
            aa = np.array(sp.getchannel('A')) > 0
            ys, xs = np.nonzero(aa)
            ux0, uy0, ux1, uy1 = int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())
            if b is None or (name.startswith('frucht/') and name not in OBSTBAEUME):   # Wolken / Beete: kein Fuss
                v, off = sp, 0
            else:
                art = 'baum' if name in BAEUME or name == 'mittel/stumpf' or name.startswith('bambus/') or name in OBSTBAEUME or 'tanne' in name else 'klein' if name.startswith(('k01/', 'neu/0', 'deko_', 'k05/')) else 'stein'
                v, off = bauwerke.bodenfuss(sp, b, art), 2
            datei = 'varianten/%s_%s%s.png' % (name.replace('/', '-'), b or 'wolke', '_m' if spiegeln else '')
            os.makedirs(os.path.join(OBJ, 'varianten'), exist_ok=True)
            v.save(os.path.join(OBJ, datei))
            cache[key] = (datei, v.height, ux0 + off, uy0, ux1 + off, uy1)
            alpha[key] = np.array(v.getchannel('A')) >= 160
        datei, h, ux0, uy0, ux1, uy1 = cache[key]
        bw, bh = ux1 - ux0 + 1, uy1 - uy0 + 1
        wt, ht = math.ceil(bw / T), math.ceil(bh / T)
        bx = int(round(fx + 0.5 - wt / 2.0))
        # Wandregel: die unteren zwei Kachelreihen (Sockel) duerfen nie auf einer Felswand/Kante liegen
        if any((x, y) in wand for x in range(bx, bx + wt) for y in (ty - 1, ty)):
            if frei or _versuch:
                return False
            for (dx, dy) in ((0, 1), (0, -1), (0, 2), (0, -2), (0, 3), (0, -3), (1, 0), (-1, 0), (0, 4), (0, -4),
                             (2, 0), (-2, 0), (0, 5), (0, -5)):
                if setze(name, fx + dx, fy + dy, opt0, nur=nur, abs_=True, _versuch=True):
                    print('  Wandregel: %s (%g,%g) -> (%g,%g)' % (name, fx - R, fy - R, fx + dx - R, fy + dy - R))
                    return True
            print('  WARNUNG Wand:', name, fx - R, fy - R)
        ox, oy = bx * T + (wt * T - bw) // 2 - ux0, (ty + 1) * T - 1 - uy1 - hoch
        ys_, xs_ = np.nonzero(alpha[key])
        ys_, xs_ = ys_ + oy, xs_ + ox
        ok = (ys_ >= 0) & (ys_ < H_) & (xs_ >= 0) & (xs_ < W_)
        ys_, xs_ = ys_[ok], xs_[ok]
        if frei and len(ys_):
            y0, y1, x0, x1 = max(0, ys_.min() - 2), ys_.max() + 3, max(0, xs_.min() - 2), xs_.max() + 3
            f = np.zeros((y1 - y0, x1 - x0), bool)
            f[ys_ - y0, xs_ - x0] = True
            f = np.array(Image.fromarray(f.astype(np.uint8) * 255).filter(ImageFilter.MaxFilter(5))) > 0
            hind = pix[y0:y1, x0:x1]
            if (f[:hind.shape[0], :hind.shape[1]] & hind).any():
                return False
        pix[ys_, xs_] = True
        o = {'datei': datei, 'basis': name, 'x': ox, 'y': oy, 'fuss': h, 'kachel': [tx, ty],
             'block': [bx, ty - ht + 1, wt, ht], 'ebene': 0 if name.startswith(('k01/', 'k05/', 'deko_')) else 1}
        o.update(opt)
        objekte.append(o)
        for x in range(bx, bx + wt):
            for y in range(ty - ht + 1, ty + 1):
                gesperrt.add((x, y))
        if name in EINBETTEN and name not in BAEUME:           # Baeume bekommen Begleiter nach Regel 5d (unten)
            einbetten(bx, wt, ty)
        return True

    def einbetten(bx, wt, ty):
        """Ein Bueschel an einer Sockelecke und eine Blume an der anderen, im Sockelbereich (vorne gezeichnet)."""
        ecken = [bx, bx + wt - 1] if wt > 1 else [bx]
        rnd2.shuffle(ecken)
        for i, x in enumerate(ecken):
            if not (0 <= x < cols and 0 <= ty < rows) or (x, ty) in wand:
                continue
            k = cls[ty][x]
            if k in 'gf':
                n = rnd2.choice(BUESCHEL_GRAS if i == 0 else BLUMEN_GRAS)
            elif k == 'n':
                n = rnd2.choice(BUESCHEL_SCHNEE if i == 0 else BLUMEN_SCHNEE)
            else:
                continue
            dx = 0.25 if x == bx else -0.25
            setze(n, x + dx, ty, {'anim': 'wehen', 'spiegeln': rnd2.random() < 0.5}, abs_=True, _versuch=True)

    def bambus_dazu(bx, wt, ty):
        """Ab und zu ein Bambusbusch neben einem Baum (im Schnee die verschneite Variante)."""
        for x in (bx - 1, bx + wt) if rnd2.random() < 0.5 else (bx + wt, bx - 1):
            if not (0 <= x < cols) or (x, ty) in wand or (x, ty) in gesperrt or (x, ty - 1) in gesperrt:
                continue
            k = cls[ty][x]
            if k not in 'gn':
                continue
            n = rnd2.choice(BAMBUS_SCHNEE if k == 'n' else BAMBUS_GRAS)
            if setze(n, x + (0.0 if x < bx else 1.0), ty, {'anim': 'wehen', 'spiegeln': rnd2.random() < 0.5},
                     abs_=True, _versuch=True):
                return

    for (name, fx, fy, opt) in FEST:
        setze(name, fx, fy, opt)
    for (x, y) in STUMPF_PLAETZE:                                # alte Baumstuempfe auf der Wiese
        setze('mittel/stumpf', x, y, {'spiegeln': rnd.random() < 0.5}, frei=True)
    for (x, y) in RUNEN_PLAETZE:                                 # Runensteine mit leuchtenden Runen
        setze('mittel/runenstein', x, y, {'anim': 'leuchten'}, frei=True)
    for (x, y) in BAUM_PLAETZE:
        setze(KIEFER, x, y, {'anim': 'baum', 'spiegeln': rnd.random() < 0.5}, frei=True)
    # Beete: Hochbeete mit Holzrahmen in unregelmaessigen Reihen, je Beet eine Fruchtsorte (digital)
    beete = []
    for (fx0, fx1) in FELDER:
        y = 64 + rnd.randint(0, 1)
        while y + 2 <= 81:
            x = fx0 + rnd.randint(1, 2)
            while x <= fx1 - 3:
                ende = x + 4 * min(rnd.randint(2, 4), (fx1 + 1 - x) // 4)
                if ende - x >= 4:
                    beete.append([(x + R) * T + 2, (ende + R) * T - 2, (y + R) * T + 2, (y + 3 + R) * T - 2])
                    frucht = 'frucht/' + rnd.choice(FRUECHTE)
                    anim = {'anim': 'wehen'}
                    px = x
                    while px + 4 <= ende:
                        setze(frucht, px + 1.5, y + 2, dict(anim, hoch=6, spiegeln=rnd.random() < 0.5))
                        px += 4
                x = ende + 1
            y += 4
    json.dump(beete, open(os.path.join(KARTE, 'beete.json'), 'w'))
    # Obstgarten: lockere Baumreihen
    ox0, ox1, oy0, oy1 = OBSTGARTEN
    y = oy0 + 3
    while y <= oy1:
        x = ox0 + 1.5 + rnd.random() * 1.5
        while x <= ox1 - 1:
            setze(rnd.choice(OBSTBAEUME), x, y, {'anim': 'baum', 'spiegeln': rnd.random() < 0.5}, frei=True)
            x += 6 + rnd.random() * 2                                # weniger Obstbaeume, versetzt
        y += 6 + rnd.randint(0, 1)
    # verschneite Tannen und Schneefelsen nur auf Schnee (nie auf Wegen), keine Felsen im Steinkreis
    n_s = n_r = 0
    for _ in range(5000):
        tx, ty = rnd.randrange(3, cols - 3), rnd.randrange(3, rows - 3)
        if cls[ty][tx] != 'n' or n_s >= 14 or rnd.random() > 0.5:   # weniger Tannen (Nutzer)
            continue
        if RING[0] <= tx - R <= RING[1] and RING[2] <= ty - R <= RING[3]:   # Steinkreis bleibt frei
            continue
        if n_r < 6 and rnd.random() < 0.15:
            if setze('mittel/07', tx, ty, {'spiegeln': rnd.random() < 0.5}, frei=True, nur='n', abs_=True):
                n_r += 1
        elif setze(TANNE, tx, ty, {'anim': 'baum', 'spiegeln': rnd.random() < 0.5}, frei=True, abs_=True):
            n_s += 1
    # Begleiter nach Regel 5 / 5d fuer alle einzeln stehenden Baeume (nicht Obstgarten, nicht Baeume an Kristallsaeulen):
    # abwechselnd 2 Kacheln hoher Fels vor dem Stumpf (eine Kachel tiefer), Fels hinter den Blaettern, oder beides mit
    # hoher Blume vorne; danach Stammreihe +-1 fuer andere Deko sperren
    kristalle = [o['kachel'] for o in objekte if o['basis'] in (LILA, KRISTALL)]
    baeume_ = [o for o in objekte if o['basis'] in BAEUME
               and not any(abs(o['kachel'][0] - kx) <= 3 and abs(o['kachel'][1] - ky) <= 2 for kx, ky in kristalle)]
    for i, o in enumerate(baeume_):
        bx, by, wt, ht = o['block']
        ty = o['kachel'][1]
        cxm = bx + wt / 2.0 - 0.5
        k = cls[ty][min(cols - 1, int(cxm + 0.5))]
        fels = 'k05/klein36' if k == 'n' else rnd2.choice(['k01/deko09', 'k01/deko11'])
        blume = 'k05/klein04' if k == 'n' else rnd2.choice(['k01/deko04', 'k01/deko27'])
        sd = -1 if i % 2 else 1
        art = i % 3
        if art in (1, 2):                                            # hinter den Blaettern (eine Reihe hoeher, aussen)
            setze(fels, cxm + sd * (wt / 2.0 + 0.2), ty - 1, {'spiegeln': rnd2.random() < 0.5}, abs_=True, _versuch=True)
        if art in (0, 2):                                            # vor dem Stumpf: eine Kachel tiefer
            n_ = fels if art == 0 else blume
            setze(n_, cxm, ty + 1, {'spiegeln': rnd2.random() < 0.5, 'anim': 'wehen' if n_ == blume else None},
                  abs_=True, _versuch=True)
        for x in range(bx - 1, bx + wt + 1):
            for y in (ty - 1, ty, ty + 1):
                gesperrt.add((x, y))
    n = 0
    for _ in range(3000):
        if n >= 70:
            break
        tx, ty = rnd.randrange(3, cols - 3), rnd.randrange(3, rows - 3)
        if cls[ty][tx] != 'g':
            continue
        z = rnd.random()
        d = rnd.choice(BUESCHEL_GRAS if z < 0.55 else BLUMEN_GRAS if z < 0.9 else KLEINKRAM_GRAS)
        if setze(d, tx, ty, {'anim': 'wehen'} if d not in KLEINKRAM_GRAS else {}, frei=True, abs_=True):
            n += 1
    # Schnee- und Felsdeko (abwechslungsreich, nicht im Steinkreis)
    n_sn = n_fe = 0
    for _ in range(6000):
        tx, ty = rnd.randrange(3, cols - 3), rnd.randrange(3, rows - 3)
        k = cls[ty][tx]
        if RING[0] <= tx - R <= RING[1] and RING[2] <= ty - R <= RING[3]:
            continue
        if k == 'n' and n_sn < 40:
            z = rnd.random()
            d = rnd.choice(BUESCHEL_SCHNEE if z < 0.5 else BLUMEN_SCHNEE if z < 0.85 else KLEINKRAM_SCHNEE)
            if setze(d, tx, ty, {'anim': 'wehen'} if d not in KLEINKRAM_SCHNEE else {}, frei=True, abs_=True):
                n_sn += 1
        elif k == 'f' and n_fe < 10 and hoehe[ty][tx] == 2:          # nur Felsflecken im Schnee, nicht am Gipfel
            if setze(rnd.choice(DEKO_FELS), tx, ty, {}, frei=True, abs_=True):
                n_fe += 1
    json.dump(objekte, open(os.path.join(OBJ, 'platzierung.json'), 'w'), indent=0)
    print(len(objekte), 'Objekte am Raster')


if __name__ == '__main__':
    main()
