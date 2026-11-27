"""Objekte fuer Karte 67 - Colosseum (A01 Nr. 4).

  python3 tools/karte67_bauen.py   (einmal -> pixelhoehe.npy, wand.npy)
  python3 tools/karte67_objekte.py && python3 tools/karte67_bauen.py

Neu mit PixelLab (k67_rom): Travertinsaeule, Bronze-Feuerschale, Legionsstandarte, Gladiatorenstatue, Waffenstaender,
Amphoren mit Fass, Kaiserthron, Speisetisch, Brunnen. Baeume des Guertels aus Karte 01 (Laubbaeume, Zypressen, Kiefern,
Buesche zum Schliessen der Luecken).
Aufbau (Nutzer): keine Objekte in Arena, Tribuene und auf dem Platz - nur der Palmenguertel am Rand.
"""
import json, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte67')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte67')
T = 16
A = os.path.join(ROOT, 'assets', 'objekte')
D = {'saeule': 'karte67/rom/00.png', 'schale': 'karte67/rom/01.png', 'standarte': 'karte67/rom/02.png',
     'statue': 'karte67/rom/03.png', 'waffen': 'karte67/rom/04.png', 'amphoren': 'karte67/rom/05.png',
     'thron': 'karte67/rom/06.png', 'tisch': 'karte67/rom/07.png', 'ruestung': 'karte67/rom/08.png',
     'schild': 'karte67/rom/09.png', 'brunnen': 'karte67/rom/10.png', 'truhe': 'karte67/rom/11.png',
     'fussballtor': 'karte67/tor/00.png', 'balliste': 'karte67/rom/12.png', 'bogen': 'karte67/rom/13.png', 'rauch': 'karte67/rom/14.png'}
# Nutzer: Palette wie die Server-Wueste (Karte 03) - Palmenguertel auf Duenensand, Felsen und duerre Buesche
for k_, f_ in (('p00', 'palmen/00'), ('p01', 'palmen/01'), ('p02', 'palmen/02'), ('p03', 'palmen/03'), ('p06', 'palmen/06'),
               ('p08', 'palmen/08'), ('m00', 'mittel/00'), ('m01', 'mittel/01'), ('m02', 'mittel/02'), ('fels', 'mittel/07'),
               ('busch', 'klein/55'), ('duerr', 'klein/04'), ('stein', 'klein/52')):
    D[k_] = 'karte03/' + f_ + '.png'
GUERTEL_BAUM = ['p00', 'p01', 'p02', 'p03', 'p06', 'p08', 'm00', 'm01', 'm02', 'fels']
GUERTEL_BUSCH = ['busch', 'duerr', 'stein', 'busch']
SANDSTEIN = [(74, 48, 32), (106, 74, 44), (138, 102, 64), (168, 130, 80), (196, 160, 102), (220, 188, 128), (236, 212, 156),
             (248, 232, 192)]
STEIN = {'saeule', 'statue', 'brunnen', 'thron', 'bogen', 'tisch'}


def sandstein(sp):
    """Generierte Marmor-/Graustein-Teile auf die Sandstein-Palette der Karte umfaerben (Helligkeit -> Palettenfarbe);
    Stoff, Gold, Wasser und Feuer behalten ihre Farbe."""
    a = np.array(sp).astype(int)
    mx, mn = a[..., :3].max(2), a[..., :3].min(2)
    grau = (a[..., 3] > 0) & (mx - mn < 28)
    if not grau.any():
        return sp
    hell = a[..., :3].mean(2)
    lo, hi = np.percentile(hell[grau], 2), np.percentile(hell[grau], 98)
    t = np.clip((hell - lo) / max(1, hi - lo), 0, 1)
    idx = np.clip((t * (len(SANDSTEIN) - 1) + 0.5).astype(int), 0, len(SANDSTEIN) - 1)
    pal = np.array(SANDSTEIN)
    a[grau, :3] = pal[idx[grau]]
    return Image.fromarray(a.astype(np.uint8))
FL = {'anim': 'kerzen', 'flammen_box': [[2, 0, 23, 20]], 'flammen_alle': True, 'flammen_amp': 1.4}
ST = {'anim': 'standarte'}


def main():
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cls = lay['klassen']
    cols, rows = lay['groesse']
    CX, CY = lay['mitte']
    achse = CX * T                                                   # Achse auf der Kachelkante (Treppen 4 breit)
    lvl = np.load(os.path.join(KARTE, 'pixelhoehe.npy'))
    wand = np.unpackbits(np.load(os.path.join(KARTE, 'wand.npy')))[:lvl.size].reshape(lvl.shape).astype(bool)
    os.makedirs(os.path.join(OBJ, 'varianten'), exist_ok=True)
    sperr = [(t['x'] * T - 2 * T, t['y'] * T - 2 * T, (t['x'] + t['b'] + 2) * T, (t['y'] + t['h'] + 2) * T)
             for t in lay['teleporter']]
    for (x0, x1, ry, r_) in lay['treppen']:                          # Treppen und Austritt (2 Reihen) frei
        y0_, y1_ = ((ry - 2) * T, (ry + 3) * T) if r_ == 's' else ((ry - 2) * T, (ry + 5) * T)
        sperr.append((x0 * T - 2, y0_, (x1 + 1) * T + 2, y1_))
    objekte, rects = [], []

    def schnitt(a, b, d):
        return not (a[2] + d < b[0] or b[2] + d < a[0] or a[3] + d < b[1] or b[3] + d < a[1])

    def setze(name, cx, fy, opt=None, spiegeln=False, gap=2, pruefen=True, klassen='z'):
        opt = dict(opt or {})
        sp = Image.open(os.path.join(A, D[name])).convert('RGBA')
        if name in STEIN:
            sp = sandstein(sp)
        if spiegeln:
            sp = sp.transpose(Image.FLIP_LEFT_RIGHT)
        datei = 'varianten/%s%s.png' % (name, '_m' if spiegeln else '')
        sp.save(os.path.join(OBJ, datei))
        bb = sp.getbbox()
        if not (opt.get('liegend') or opt.get('ebene') == 0):
            fy = int(fy) // T * T + T - 1                            # Regel 1b: Fuss auf der Kachelunterkante
        x = int(round(cx - (bb[0] + bb[2]) / 2.0))
        y = int(fy - (bb[3] - 1))
        r = (x + bb[0], y + bb[1], x + bb[2] - 1, y + bb[3] - 1)
        if r[0] < 0 or r[1] < 0 or r[2] >= cols * T or r[3] >= rows * T:
            return None
        if pruefen:
            if any(schnitt(r, tuple(rr[:4]), gap) for rr in rects):
                return None
            if any(schnitt(r, s_, 0) for s_ in sperr):
                return None
            y_ab = max(r[1], r[3] - 2 * T + 1)
            reg = lvl[y_ab:r[3] + 4, max(0, r[0] - 3):r[2] + 4]
            if len(np.unique(reg)) != 1 or reg[0, 0] == 9:
                return None                                          # untere zwei Reihen ganz auf einer Ebene
            if wand[y_ab:r[3] + 4, max(0, r[0] - 3):r[2] + 4].any():
                return None
            if any(cls[yy // T][xx // T] not in klassen for yy in range(y_ab, r[3] + 1, 4)
                   for xx in range(r[0], r[2] + 1, 4)):
                return None
            hoch = lvl[max(0, r[1]):r[3] - T, r[0]:r[2] + 1]         # nicht vor eine hoehere Ebene daneben ragen
            if ((hoch > lvl[r[3], (r[0] + r[2]) // 2]) & (hoch != 9)).any():
                return None
        o = {'datei': datei, 'basis': name, 'x': x, 'y': y, 'fuss': bb[3] - 1, 'kachel': [int(cx) // T, int(fy) // T],
             'ebene': 1, 'ohne_wall': True}
        o.update(opt)
        objekte.append(o)
        rects.append(list(r))
        return o

    def paar(name, abstand, fy, opt=None, klassen='z', ax=None, schritt=T, weit=4):
        """Gespiegeltes Paar zur Achse auf gemeinsamer Fusszeile; bei Konflikt gemeinsam verschieben."""
        ax = achse if ax is None else ax
        for dab in sorted(range(-weit, weit + 1), key=abs):
            for dfy in (0, -T, T, -2 * T, 2 * T):
                a_ = setze(name, ax - abstand - dab * schritt, fy + dfy, opt, False, klassen=klassen)
                if not a_:
                    continue
                b_ = setze(name, ax + abstand + dab * schritt, fy + dfy, opt, True, klassen=klassen)
                if b_:
                    return True
                objekte.pop(); rects.pop()
        print('  Paar nicht gesetzt:', name, abstand, fy // T)
        return False

    def suche(name, cx, fy, opt=None, spiegeln=False, r=3, klassen='z'):
        for d in range(r + 1):
            for dy in range(-d, d + 1):
                for dx in range(-d, d + 1):
                    if max(abs(dx), abs(dy)) == d and setze(name, cx + dx * T, fy + dy * T, opt, spiegeln, klassen=klassen):
                        return True
        print('  nicht gesetzt:', name, int(cx) // T, int(fy) // T)
        return False

    # Nutzer: innen (Arena und Tribuene) keine Objekte - Kampfarena abgeschottet, Tribuene frei begehbar
    # Nutzer: grosses Fussballtor unten (Suedende der Arena), mittig auf der Achse, Fuss in der letzten Arenareihe
    unten = max(y for y in range(rows) if cls[y][CX] == 'a')
    setze('fussballtor', achse, unten * T + T - 1, {'fest_pos': True, 'nur_kontakt': True}, pruefen=False)
    # Nutzer: auch aussen keine Objekte (Fackeln, Saeulen, Brunnen usw. entfernt) - nur der Palmenguertel

    # ---------------- Baumguertel (Wiese 'n' am Rand): dicht, nicht begehbar, Luecken mit Bueschen
    rnd = random.Random(67)
    nk = np.array([[c == 'n' for c in z] for z in cls])
    deck = np.zeros((rows * T, cols * T), bool)
    guertel = []

    def baum(name, cx, fy, sp_):
        im = Image.open(os.path.join(A, D[name])).convert('RGBA')
        if sp_:
            im = im.transpose(Image.FLIP_LEFT_RIGHT)
        w, h = im.size
        x, y = int(cx - w / 2), int(fy - h + 1)
        if x < 0 or y < 0 or x + w > cols * T or y + h > rows * T:
            return False
        ty, tx = int(fy) // T, int(cx) // T
        for dx in (-6, 0, 6):                                        # Fuss ganz auf der Wiese
            if not nk[ty, max(0, min(cols - 1, int(cx + dx) // T))]:
                return False
        if any(abs(g['cx'] - cx) < 18 and abs(g['fy'] - fy) < 10 for g in guertel):
            return False
        if any(schnitt((x, y, x + w - 1, y + h - 1), s_, 0) for s_ in sperr[:1]):
            return False
        datei = 'varianten/%s%s.png' % (name, '_m' if sp_ else '')
        im.save(os.path.join(OBJ, datei))
        guertel.append({'cx': cx, 'fy': fy})
        deck[y:y + h, x:x + w] |= np.array(im)[..., 3] > 0
        objekte.append({'datei': datei, 'basis': name, 'x': x, 'y': y, 'fuss': h - 1, 'kachel': [tx, ty], 'ebene': 1,
                        'ohne_wall': True, 'nur_kontakt': True, 'guertel': True, 'fest_pos': True,
                        'anim': 'wehen' if name[0] in 'pm' else None})
        return True

    kand = []
    for ty in range(rows):
        for tx in range(cols):
            if nk[ty, tx]:
                for _ in range(2):
                    kand.append((tx * T + rnd.randint(2, 14), ty * T + rnd.randint(6, 15)))
    rnd.shuffle(kand)
    for (cx, fy) in kand:
        baum(rnd.choice(GUERTEL_BAUM), cx, fy, rnd.random() < 0.5)
    for runde in range(3):                                           # Luecken schliessen (kahle Wiese)
        rnd.shuffle(kand)
        for (cx, fy) in kand:
            y0, x0 = max(0, int(fy) - 10), max(0, int(cx) - 10)
            if deck[y0:int(fy) + 1, x0:int(cx) + 10].mean() < 0.55:
                baum(rnd.choice(GUERTEL_BUSCH if runde else GUERTEL_BAUM + GUERTEL_BUSCH), cx, fy, rnd.random() < 0.5)
    for o in objekte:
        if o['basis'] in ('saeule', 'statue', 'brunnen', 'thron', 'amphoren', 'tisch', 'truhe', 'balliste', 'waffen'):
            o['nur_kontakt'] = True                                  # Stein/Moebel auf Pflaster: nur Kontaktschatten
        if o.get('anim') is None:
            o.pop('anim', None)
    json.dump(objekte, open(os.path.join(OBJ, 'platzierung.json'), 'w'), indent=0)
    print('Karte 67: %d Objekte (%d im Guertel)' % (len(objekte), len(guertel)))


if __name__ == '__main__':
    main()
