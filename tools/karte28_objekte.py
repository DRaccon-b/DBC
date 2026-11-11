"""Objekte fuer Karte 28 (Tower Forest, A02).

  python3 tools/karte28_bauen.py   (einmal -> wand.npy)
  python3 tools/karte28_objekte.py && python3 tools/karte28_bauen.py

Schritt 1: Waldrand (Nutzer) - dunkle Waldbaeume (tools/karte28_baeume.py, umgefaerbt aus Karte 01) dicht im
Schachbrett auf den Waldkacheln wie Karte 06 / 23 / 27; Fuss nie auf einer Wand.
"""
import json, math, os, random, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
import bauwerke

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte28')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte28')
T = 16
# Schwarze Obelisken (Karte 24 obelisk2, ohne Leuchten): Mitte x (px, Kachelgrenze) und Schaftende y aus der Vorlage
OBELISKEN = [(816, 218), (1392, 218), (384, 506), (672, 506), (960, 506), (1248, 506),
             (240, 794), (816, 794), (1104, 794), (1392, 794), (640, 1146), (960, 1146)]
OBELISK = 'k24/obelisk'
WALD = ['wald_dunkel/%02d' % i for i in (0, 1, 2, 3, 4, 5, 6, 7, 0, 1, 2, 4, 7, 8, 9, 10)]   # Laub-/Nadelbaeume, wenige Buesche


def main():
    rnd = random.Random(28)
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cls = lay['klassen']
    cols, rows = lay['groesse']
    wand = np.unpackbits(np.load(os.path.join(KARTE, 'wand.npy')))[:rows * T * cols * T].reshape(rows * T, cols * T).astype(bool)
    objekte, cache = [], {}

    def variante(name, spiegeln, boden='gras'):
        key = (name, spiegeln, boden)
        if key not in cache:
            sp = Image.open(os.path.join(OBJ, name + '.png')).convert('RGBA')
            if spiegeln:
                sp = sp.transpose(Image.FLIP_LEFT_RIGHT)
            aa = np.array(sp.getchannel('A')) > 0
            ys, xs = np.nonzero(aa)
            ux0, uy0, ux1, uy1 = int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())
            v = bauwerke.bodenfuss(sp, boden, 'baum' if 'wald' in name else 'stein')
            fa = np.array(v).astype(np.float32)                      # Bodenfuss an den dunklen Waldboden anpassen
            off = Image.new('RGBA', v.size, (0, 0, 0, 0)); off.paste(sp, (2, 0))
            sel = (np.array(off.getchannel('A')) == 0) & (fa[..., 3] > 0)
            fa[sel, :3] *= np.array([0.5, 0.56, 0.62])
            v = Image.fromarray(np.clip(fa, 0, 255).astype(np.uint8))
            datei = 'varianten/%s_%s%s.png' % (name.replace('/', '-'), boden, '_m' if spiegeln else '')
            os.makedirs(os.path.join(OBJ, 'varianten'), exist_ok=True)
            v.save(os.path.join(OBJ, datei))
            cache[key] = (datei, v.height, ux0 + 2, uy0, ux1 + 2, uy1)
        return cache[key]

    # Grosse Objekte zuerst: schwarze Obelisken (Fuss buendig auf der Kachelkante, waagerecht auf der Kachelgrenze
    # wie in der Vorlage = mittig im 2-Kachel-Block)
    os.makedirs(os.path.join(OBJ, 'k24'), exist_ok=True)
    ob = np.array(Image.open(os.path.join(ROOT, 'assets', 'objekte', 'karte24', 'obelisk2', '00.png')).convert('RGBA')).astype(int)
    warm = (ob[..., 3] > 0) & (ob[..., 0] > ob[..., 2] + 20)           # orange Lichtkante am Sockel -> schwarzblau
    ob[warm, :3] = (52, 58, 78)
    Image.fromarray(ob.astype(np.uint8)).save(os.path.join(OBJ, OBELISK + '.png'))
    for (cx, yb) in OBELISKEN:
        ty = (yb + 20) // T
        tx = cx // T
        k_ = cls[ty][tx]
        boden = 'sand' if k_ in 'fewt' else 'beton' if k_ == 'k' else 'gras'
        datei, h, ux0, uy0, ux1, uy1 = variante(OBELISK, False, boden)
        bw = ux1 - ux0 + 1
        objekte.append({'datei': datei, 'basis': OBELISK, 'x': cx - bw // 2 - ux0, 'y': (ty + 1) * T - 1 - uy1, 'fuss': h,
                        'kachel': [tx, ty], 'block': [tx - 1, ty - math.ceil((uy1 - uy0 + 1) / T) + 1, 2,
                                                      math.ceil((uy1 - uy0 + 1) / T)], 'ebene': 1})
    for ty in range(rows):
        for tx in range(cols):
            if cls[ty][tx] != 'h' or (tx + ty) % 2:
                continue
            if wand[ty * T:(ty + 1) * T, tx * T:(tx + 1) * T].any():
                continue
            name = rnd.choice(WALD)
            datei, h, ux0, uy0, ux1, uy1 = variante(name, rnd.random() < 0.5)
            bw = ux1 - ux0 + 1
            wt, ht = math.ceil(bw / T), math.ceil((uy1 - uy0 + 1) / T)
            bx = int(round(tx + 0.5 - wt / 2.0))
            objekte.append({'datei': datei, 'basis': name, 'x': bx * T + (wt * T - bw) // 2 - ux0,
                            'y': (ty + 1) * T - 1 - uy1, 'fuss': h, 'kachel': [tx, ty],
                            'block': [bx, ty - ht + 1, wt, ht], 'ebene': 1, 'anim': 'baum'})
    # Spinnweben (Nutzer, PixelLab k28_netz): flach auf dem Boden, ohne Schatten - Steinplatz ausserhalb des Rings und
    # Arena (vor allem die oberen Ecken, wie die Vorlage); Kokons (4, 6) dazwischen
    NETZE = ['netz/00', 'netz/01', 'netz/02', 'netz/03', 'netz/00', 'netz/02']
    import karte28_bauen as k28
    cx_, cy_, rx_, ry_ = k28.MAUER_MITTE
    mauer_netze = []
    for k in range(10):                                              # Netze an der Mauer (Mittellinie, unregelmaessig)
        t = k * 2 * math.pi / 10 + (0.18 if k % 2 else -0.1)
        e = k28.mauer_rand(t)
        x = cx_ + math.cos(t) * (rx_ - k28.MAUER_DICKE / 2) * e
        y = cy_ + math.sin(t) * (ry_ - k28.MAUER_DICKE / 2) * e
        if k28.MAUER_TOR[0] - 12 <= x <= k28.MAUER_TOR[1] + 12 and y > cy_:
            continue
        ring_px = k28.mauer_maske(rows * T, cols * T)
        cand = [(abs(xx * T + 8 - x) + abs(yy * T + 8 - y), xx, yy) for yy in range(int(y) // T - 2, int(y) // T + 3)
                for xx in range(int(x) // T - 2, int(x) // T + 3) if ring_px[yy * T + 8, xx * T + 8]]
        if cand:
            _, xx, yy = min(cand)
            mauer_netze.append((xx, yy))
    NETZ_STELLEN = mauer_netze + [
                    (87, 12), (88, 20), (87, 27), (59, 27),            # Steinplatz aussen
                    (72, 19), (65, 21), (76, 17), (70, 23), (74, 13),         # Arenaboden innen (Nutzer: mehr Netze)
                    (8, 21), (10, 23), (12, 20), (9, 25), (13, 23), (24, 21), (27, 20), (30, 19), (29, 23), (34, 18),
                    (42, 21), (45, 22), (46, 25), (41, 19), (6, 28), (19, 34), (38, 31)]
    KOKONS = [(68, 15), (85, 14), (11, 22), (44, 21), (28, 21)]
    belegt = set((o['kachel'][0], o['kachel'][1]) for o in objekte if not o['basis'].startswith('wald'))
    for i, (tx, ty) in enumerate(NETZ_STELLEN + KOKONS):
        if (tx, ty) in belegt or cls[ty][tx] in 'hwT' or any(
                o['basis'] == OBELISK and abs(o['kachel'][0] - tx) <= 2 and -6 <= ty - o['kachel'][1] <= 1 for o in objekte):
            continue
        name = ('netz/02' if i % 2 else 'netz/00') if i >= len(NETZ_STELLEN) else NETZE[(tx * 7 + ty * 3) % len(NETZE)]   # Spinnweben statt Ei/Kokon/Knochen (Nutzer)
        sp = Image.open(os.path.join(OBJ, name + '.png')).convert('RGBA')
        if (tx + ty) % 2:
            sp = sp.transpose(Image.FLIP_LEFT_RIGHT)
        datei = 'varianten/%s%s.png' % (name.replace('/', '-'), '_m' if (tx + ty) % 2 else '')
        sp.save(os.path.join(OBJ, datei))
        bb = sp.getbbox()
        kokon = False                                                # alles flache Netze
        objekte.append({'datei': datei, 'basis': name, 'x': tx * T + 8 - (bb[0] + bb[2]) // 2, 'y': (ty + 1) * T - 1 - (bb[3] - 1),
                        'fuss': sp.height, 'kachel': [tx, ty], 'block': [tx, ty, 1, 1], 'ebene': 1 if kokon else 0,
                        'schattenlos': not kokon, 'liegend': kokon})
        belegt.add((tx, ty))
    # ---------------- Restliche Objekte (Nutzer: "alles") - Positionen nach der Vorlage ----------------
    def dunkel_kopie(q, ziel, f=(0.72, 0.76, 0.8)):                 # Deko von anderen Karten an den dunklen Wald anpassen
        im = np.array(Image.open(os.path.join(ROOT, 'assets', 'objekte', q)).convert('RGBA')).astype(np.float32)
        im[..., :3] *= np.array(f)
        os.makedirs(os.path.dirname(os.path.join(OBJ, ziel + '.png')), exist_ok=True)
        Image.fromarray(np.clip(im, 0, 255).astype(np.uint8)).save(os.path.join(OBJ, ziel + '.png'))
    for n in (4, 5, 6, 7, 9, 11, 14, 16, 27, 30, 31, 41, 53):
        dunkel_kopie('karte01/deko/%02d.png' % n, 'k01/deko%02d' % n)
    dunkel_kopie('karte01/laterne.png', 'k01/laterne', (0.9, 0.9, 0.9))
    dunkel_kopie('karte03/klein/16.png', 'k03/feuer', (1, 1, 1))
    dunkel_kopie('karte04/mittel/13.png', 'k04/wegweiser', (0.78, 0.78, 0.8))
    dunkel_kopie('karte24/obelisk_liegend/00.png', 'k24/obelisk_liegend', (1, 1, 1))
    for n in (35, 36):
        dunkel_kopie('karte28/netz/%02d.png' % n, 'deko/wurzel%02d' % n, (0.85, 0.85, 0.85))
    dunkel_kopie('karte28/netz/51.png', 'deko/pfuetze', (0.9, 0.9, 0.9))
    for n in range(4):
        dunkel_kopie('karte27/fels_klein/%02d.png' % [0, 1, 3, 51][n], 'deko/fels%d' % n, (0.78, 0.8, 0.86))
    kr = np.array(Image.open(os.path.join(ROOT, 'assets', 'objekte', 'karte24', 'lager', '03.png')).convert('RGBA')).astype(np.float32)
    l = kr[..., :3].mean(2, keepdims=True)                          # Erzkristall (Karte 24) -> dunkle, matte Kristalle
    kr[..., :3] = np.clip(l * np.array([0.42, 0.4, 0.58]) + np.array([6, 6, 14]), 0, 255)
    Image.fromarray(kr.astype(np.uint8)).save(os.path.join(OBJ, 'deko', 'kristall.png'))

    fuesse = []
    for o in objekte:
        if o['basis'] == OBELISK:
            fuesse.append((o['x'] + 4, o['y'] + o['fuss'] - 20, o['x'] + 40, o['y'] + o['fuss'] + 2))

    def setze(name, cx, fy, opt=None, spiegeln=False, mit_fuss=True, boden_ok='gfekwt', frei=True):
        sp = Image.open(os.path.join(OBJ, name + '.png')).convert('RGBA')
        if spiegeln:
            sp = sp.transpose(Image.FLIP_LEFT_RIGHT)
        bb = sp.getbbox()
        bw = bb[2] - bb[0]
        tx, ty = int(cx) // T, int(fy) // T
        if not (0 <= tx < cols and 0 <= ty < rows) or cls[ty][tx] not in boden_ok:
            return None
        x0, x1, y0, y1 = cx - bw // 2 - 2, cx + bw // 2 + 2, fy - min(16, bb[3] - bb[1]) - 2, fy + 2
        if wand[max(0, fy - 10):fy + 2, max(0, cx - bw // 2):cx + bw // 2 + 1].any():
            return None
        if frei and any(not (x1 < a0 or x0 > a1 or y1 < b0 or y0 > b1) for (a0, b0, a1, b1) in fuesse):
            return None
        if mit_fuss:
            k_ = cls[ty][tx]
            b_ = 'sand' if k_ in 'fewt' else 'beton' if k_ == 'k' else 'gras'
            v = bauwerke.bodenfuss(sp, b_, 'baum' if 'wald' in name else 'stein')
            fa = np.array(v).astype(np.float32)
            off = Image.new('RGBA', v.size, (0, 0, 0, 0)); off.paste(sp, (2, 0))
            sel = (np.array(off.getchannel('A')) == 0) & (fa[..., 3] > 0)
            fa[sel, :3] *= np.array([0.5, 0.56, 0.62])                 # Bodenfuss dunkel wie der Waldboden
            sp = Image.fromarray(np.clip(fa, 0, 255).astype(np.uint8))
            bb = (bb[0] + 2, bb[1], bb[2] + 2, bb[3])
        datei = 'varianten/%s_%d_%d.png' % (name.replace('/', '-'), int(spiegeln), int(mit_fuss))
        sp.save(os.path.join(OBJ, datei))
        o = {'datei': datei, 'basis': name, 'x': int(cx) - (bb[0] + bw // 2), 'y': int(fy) - (bb[3] - 1), 'fuss': sp.height,
             'kachel': [tx, ty], 'block': [(int(cx) - bw // 2) // T, ty - math.ceil((bb[3] - bb[1]) / T) + 1,
                                           math.ceil(bw / T), math.ceil((bb[3] - bb[1]) / T)], 'ebene': 1}
        o.update(opt or {})
        objekte.append(o)
        fuesse.append((x0, y0, x1, y1))
        return o

    # Grosses zuerst: umgestuerzter Turm oben rechts am Weg, dunkle Kristallbrocken an den Ecken des Steinplatzes
    setze('k24/obelisk_liegend', 1484, 200, {'liegend': True}, mit_fuss=False, boden_ok='gkew')
    for (cx, fy, sp_) in ((990, 104, False), (1348, 470, True), (896, 580, False), (1314, 582, True)):
        setze('deko/kristall', cx, fy, {}, sp_, boden_ok='gkew')
    # Wiesenbaeume nach der Vorlage: grosse knorrige Eichen und kleine Baeume (dunkel), Begleiter nach Regel 5d
    GROSS = [(943, 845), (1455, 829), (543, 941), (1183, 1005)]
    KLEIN = [(974, 605), (1245, 767), (1534, 781), (590, 829), (622, 829), (1214, 829), (1246, 845), (1278, 845),
             (286, 861), (1454, 957), (462, 1021), (670, 1021), (1006, 1021), (926, 1069), (910, 1277)]
    baeume = []
    for i, (cx, fy) in enumerate(GROSS + KLEIN):
        name = 'wald_dunkel/01' if i < len(GROSS) else rnd.choice(['wald_dunkel/02', 'wald_dunkel/03', 'wald_dunkel/05', 'wald_dunkel/00'])
        cx = (cx // T) * T + 8
        fy = (fy // T + 1) * T - 1
        if any(abs(b['kachel'][0] - cx // T) < 2 and abs(b['kachel'][1] - fy // T) < 3 for b in baeume):
            continue
        b = setze(name, cx, fy, {'anim': 'baum'}, rnd.random() < 0.5, boden_ok='gw')
        if b:
            baeume.append(b)
    for i, b in enumerate(baeume):                                   # Begleiter: abwechselnd vor dem Stumpf / hinter den Blaettern
        cx, fy = b['kachel'][0] * T + 8, (b['kachel'][1] + 1) * T - 1
        sd = -1 if i % 2 else 1
        hw = max(9, b['block'][2] * T // 2 - 2)
        if i % 3 == 0:
            setze('k01/deko%02d' % rnd.choice([9, 11]), cx + sd * 5, fy + T, {}, rnd.random() < 0.5, boden_ok='g', frei=False)
        elif i % 3 == 1:
            setze('k01/deko%02d' % rnd.choice([9, 11]), cx + sd * hw, fy - 7, {'hinter': True}, rnd.random() < 0.5, boden_ok='g', frei=False)
        else:
            setze('k01/deko%02d' % rnd.choice([9, 11]), cx + sd * hw, fy - 7, {'hinter': True}, rnd.random() < 0.5, boden_ok='g', frei=False)
            setze('k01/deko%02d' % rnd.choice([4, 27, 30]), cx - sd * 5, fy + T, {'anim': 'wehen'}, boden_ok='g', frei=False)
        bx, by, wt, ht = b['block']
        fuesse.append((bx * T - 16, fy - 2 * T, (bx + wt) * T + 16, fy + 4))   # Stammreihe frei von anderer Deko
    # Lagerfeuer am unteren Weg (Vorlage) mit Sitzstaemmen, Wegweiser, Laterne
    setze('k03/feuer', 792, 1150, {'anim': 'feuer'}, boden_ok='gwt')
    setze('k01/deko16', 748, 1160, {'liegend': True}, boden_ok='gwt')
    setze('k01/deko41', 830, 1166, {'liegend': True}, True, boden_ok='gwt')
    setze('k04/wegweiser', 790, 1020, {}, boden_ok='gw')
    setze('k01/laterne', 872, 1176, {'anim': 'laterne'}, mit_fuss=False, boden_ok='gw')
    # Kleine Nadelbaeume auf den Wiesen (Vorlage)
    for (cx, fy) in ((183, 722), (312, 850), (697, 1100), (583, 1170), (695, 1265), (838, 1280), (950, 1195), (1530, 742),
                     (1100, 930), (420, 1100)):
        setze('wald_dunkel/06', (cx // T) * T + 8, (fy // T + 1) * T - 1, {'anim': 'baum'}, rnd.random() < 0.5, boden_ok='g')
    # Schlamm-Arena: Wurzeln/Totholz, Findlinge, liegende Staemme, Pilze, Pfuetzen auf den Erdflecken
    for (cx, fy) in ((140, 463), (443, 333), (263, 540), (527, 437)):
        setze('deko/wurzel%02d' % rnd.choice([35, 36]), cx, fy, {'liegend': True}, rnd.random() < 0.5, mit_fuss=False, boden_ok='fe')
    for (cx, fy) in ((97, 497), (623, 463), (430, 623)):
        setze('deko/fels%d' % rnd.randrange(3), cx, fy, {}, rnd.random() < 0.5, boden_ok='fe')
    for (cx, fy) in ((310, 360), (177, 537), (430, 567), (640, 553), (593, 632)):
        setze('k01/deko%s' % rnd.choice(['16', '41']), cx, fy, {'liegend': True}, rnd.random() < 0.5, boden_ok='fe')
    for (cx, fy) in ((327, 377), (183, 520), (200, 553), (407, 551), (440, 583), (600, 617)):
        setze('k01/deko%s' % rnd.choice(['14', '31']), cx, fy, {}, rnd.random() < 0.5, mit_fuss=False, boden_ok='fe')
    for (cx, fy) in ((183, 423), (583, 392), (343, 470), (470, 600)):
        setze('deko/pfuetze', cx, fy, {'schattenlos': True}, mit_fuss=False, boden_ok='fe')
    # Wiesen und Plateaurand: Pilze, Gras- und Blumenbueschel (unregelmaessig, eher wenig) und ein paar Steine
    n_ = 0
    for _ in range(6000):
        if n_ >= 55:
            break
        tx, ty = rnd.randrange(1, cols - 1), rnd.randrange(1, rows - 1)
        if not all(cls[ty + dy][tx + dx] == 'g' for dx in (-1, 0, 1) for dy in (-1, 0, 1)):
            continue
        nm = rnd.choice(['k01/deko05', 'k01/deko06', 'k01/deko07', 'k01/deko14', 'k01/deko31', 'k01/deko05', 'k01/deko06'])
        if setze(nm, tx * T + rnd.randrange(4, 12), ty * T + 13, {'anim': 'wehen'} if nm[-2:] in ('05', '06', '07') else {},
                 rnd.random() < 0.5, mit_fuss=False, boden_ok='g'):
            n_ += 1
    n_ = 0
    for _ in range(3000):
        if n_ >= 6:
            break
        tx, ty = rnd.randrange(1, cols - 1), rnd.randrange(40, rows - 1)
        if not all(cls[ty + dy][tx + dx] == 'g' for dx in (-1, 0, 1) for dy in (-1, 0, 1)):
            continue
        if setze('deko/fels%d' % rnd.randrange(4), tx * T + 8, ty * T + 14, {}, rnd.random() < 0.5, boden_ok='g'):
            n_ += 1
    json.dump(objekte, open(os.path.join(OBJ, 'platzierung.json'), 'w'), indent=0)
    print('Karte 28: %d Objekte' % len(objekte))


if __name__ == '__main__':
    main()
