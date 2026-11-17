"""Objekte fuer Karte 50 - Zhuqiaomon's Sanctuary (A03 Nr. 17).

  python3 tools/karte50_bauen.py   (einmal -> pixelhoehe.npy, wand.npy)
  python3 tools/karte50_objekte.py && python3 tools/karte50_bauen.py

Neu mit PixelLab (k50_torii, k50_deko, k50_klein): rote Torii, Steinlaternen, Steinpfosten, Strohunterstand, Opferkasten,
Feuerschalen (orangerote Flammen - Feuervogel), Wasserbecken, kleiner Schrein, Phoenixfedern, rote Spinnenlilien.
Weniger Kleinkram als in der Vorlage (Nutzer bei Karte 49: lieber cleaner): Pfosten und Feuerschalen nur als Paare an den
Treppenachsen und wenige Randpaare (fester Rhythmus, gespiegelt); Torii auf der Achse ihrer Treppe; abgesenkter Hof mit
Funktion (Schrein an der Nordwand, Laternenpaar, Opferkasten, Wasserbecken); Baeume der Vorlage mit Begleitern (Regel 5).
"""
import json, math, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte50')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte50')
T = 16
A = os.path.join(ROOT, 'assets', 'objekte')
D = {'torii': 'karte50/torii_gross/00b.png',   # Nutzer: Pfeiler stehen am Treppenfuss, man geht darunter durch
     'torii_klein': 'karte50/torii/00.png', 'becken': 'karte50/torii/02.png', 'laterne': 'karte50/deko/00.png',
     'pfosten': 'karte50/deko/01.png', 'unterstand': 'karte50/deko/02.png', 'opfer': 'karte50/deko/03.png',
     'schale': 'karte50/deko/04.png', 'schrein': 'karte50/deko/09.png', 'feder': 'karte50/klein/00.png',
     'feder2': 'karte50/klein/01.png', 'lilie': 'karte50/klein/02.png', 'kiesel': 'karte50/klein/03.png',
     'baum': 'karte01/baeume/00.png', 'zypresse': 'karte01/baeume/07.png', 'brocken': 'karte47/deko/03.png',
     'kf00': 'karte27/fels_klein/00.png', 'kf24': 'karte27/fels_klein/24.png', 'kf52': 'karte27/fels_klein/52.png',
     'gras': 'karte04/klein/00.png', 'gras2': 'karte04/klein/01.png', 'zweig': 'karte04/klein/09.png'}
FLACH = {'feder', 'feder2', 'kiesel', 'zweig'}


def main():
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cls = lay['klassen']
    cols, rows = lay['groesse']
    lvl = np.load(os.path.join(KARTE, 'pixelhoehe.npy'))
    wand = np.unpackbits(np.load(os.path.join(KARTE, 'wand.npy')))[:lvl.size].reshape(lvl.shape).astype(bool)
    os.makedirs(os.path.join(OBJ, 'varianten'), exist_ok=True)
    sperr = [(t['x'] * T - 2 * T, t['y'] * T - 2 * T, (t['x'] + t['b'] + 2) * T, (t['y'] + t['h'] + 2) * T)
             for t in lay['teleporter']]
    for (x0, x1, ry, r_) in lay['treppen']:                          # Treppen und Austritt (2 Reihen) frei
        y0_, y1_ = ((ry - 2) * T, (ry + 3) * T) if r_ == 's' else ((ry - 2) * T, (ry + 5) * T)
        sperr.append((x0 * T - 2, y0_, (x1 + 1) * T + 2, y1_))
    objekte, rects = [], []
    rnd = random.Random(50)

    def schnitt(a, b, d):
        return not (a[2] + d < b[0] or b[2] + d < a[0] or a[3] + d < b[1] or b[3] + d < a[1])

    def setze(name, cx, fy, opt=None, spiegeln=False, gap=2, pruefen=True, klassen='gwknd'):
        opt = dict(opt or {})
        sp = Image.open(os.path.join(A, D[name])).convert('RGBA')
        if spiegeln:
            sp = sp.transpose(Image.FLIP_LEFT_RIGHT)
        if name.startswith('kf'):                                    # rote Kontur (Karte 27) -> kuehles Blaugrau
            ar = np.array(sp).astype(int)
            rot = (ar[..., 3] > 0) & (ar[..., 0] > ar[..., 2] + 40) & (ar[..., 1] < 90)
            ar[rot, :3] = (34, 38, 50)
            sp = Image.fromarray(ar.astype(np.uint8))
        datei = 'varianten/%s%s.png' % (name, '_m' if spiegeln else '')
        sp.save(os.path.join(OBJ, datei))
        bb = sp.getbbox()
        if not (opt.get('liegend') or opt.get('ebene') == 0):
            fy = int(fy) // T * T + T - 1                            # Regel 1b: Fuss auf der Kachelunterkante
        x = int(round(cx - (bb[0] + bb[2]) / 2.0))
        y = int(fy - (bb[3] - 1))
        r = (x + bb[0], y + bb[1], x + bb[2] - 1, y + bb[3] - 1)
        if r[0] < 2 or r[1] < 2 or r[2] >= cols * T - 2 or r[3] >= rows * T - 2:
            return None
        if pruefen:
            if any(schnitt(r, tuple(rr[:4]), gap) for rr in rects):
                return None
            if any(schnitt(r, s_, 0) for s_ in sperr):
                return None
            y_ab = r[1] if opt.get('liegend') else max(r[1], r[3] - 2 * T + 1)
            reg = lvl[y_ab:r[3] + 4, max(0, r[0] - 3):r[2] + 4]
            if len(np.unique(reg)) != 1 or reg[0, 0] == 9 or reg[0, 0] >= 5:
                return None                                          # untere zwei Reihen ganz auf einer Ebene, nicht am Rand
            if wand[max(0, r[1]):r[3] + 1, r[0]:r[2] + 1].any():
                return None
            if any(cls[yy // T][xx // T] not in klassen for yy in range(y_ab, r[3] + 1, 4) for xx in range(r[0], r[2] + 1, 4)):
                return None
            hoch = lvl[max(0, r[1]):r[3] - T, r[0]:r[2] + 1]          # Verdeckung: nicht vor eine hoehere Terrasse daneben
            if ((hoch > lvl[r[3], (r[0] + r[2]) // 2]) & (hoch != 9)).any() and not opt.get('vor_wand'):
                return None
        o = {'datei': datei, 'basis': name, 'x': x, 'y': y, 'fuss': bb[3] - 1, 'kachel': [int(cx) // T, int(fy) // T],
             'ebene': 1, 'ohne_wall': name not in ('baum', 'zypresse', 'kf00', 'kf24', 'kf52', 'lilie', 'gras', 'gras2')}
        o.update(opt)
        objekte.append(o)
        rects.append(list(r))
        return o

    def suche(name, cx, fy, opt=None, spiegeln=False, r=3, klassen='gwknd'):
        for d in range(r + 1):
            for dy in range(-d, d + 1):
                for dx in range(-d, d + 1):
                    if max(abs(dx), abs(dy)) == d:
                        o = setze(name, cx + dx * T, fy + dy * T, opt, spiegeln, klassen=klassen)
                        if o:
                            return o
        print('  nicht gesetzt:', name, int(cx) // T, int(fy) // T)
        return None

    def paar(name, achse, abstand, fy, opt=None):
        """Gespiegeltes Paar auf gemeinsamer Fusszeile; bei Konflikt die Fusszeile gemeinsam verschieben."""
        for dab in (0, 16, -16, 32, 48, 64, 80, 96, 112):         # Saeulen/Schalen nie auf Pflaster (Karte 47)
            for dfy in (0, -T, T, -2 * T, 2 * T, -3 * T, 3 * T):
                a_ = setze(name, achse - abstand - dab, fy + dfy, opt, False, klassen='gd')
                if not a_:
                    continue
                b_ = setze(name, achse + abstand + dab, fy + dfy, opt, True, klassen='gd')
                if b_:
                    return True
                objekte.pop(); rects.pop()
        print('  Paar nicht gesetzt:', name, int(achse) // T, int(fy) // T)
        return False

    # ---------------- Torii auf der Achse ihrer Treppe (auf der Terrasse ueber der Treppe), Paare an den Achsen
    for (x0, x1, ry, r_) in lay['treppen']:
        if r_ != 's':
            continue
        achse = (x0 * T + (x1 + 1) * T) / 2.0
        if ry < 60:                                                  # die beiden Torii (untere Treppe ohne Tor)
            setze('torii', achse, (ry + 1) * T + T - 1, {'fest_pos': True, 'vor_wand': True, 'nur_kontakt': True,
                                                         'sortier': (ry + 1) * T + T - 1}, pruefen=False)
        paar('schale', achse, (x1 - x0 + 1) * T / 2.0 + 24, (ry - 1) * T + 12, {'anim': 'kerzen', 'flammen_box': [[4, 0, 24, 20]],
                                                                              'flammen_alle': True, 'flammen_amp': 1.4})
        paar('pfosten', achse, (x1 - x0 + 1) * T / 2.0 + 24, (ry + 4) * T + 12)
    # Vorlage: Pfosten-/Schalenpaare auf den Terrassen (Achse der Torii-Plaetze), sparsam
    ax_ = [(x0 * T + (x1 + 1) * T) / 2.0 for (x0, x1, ry, r_) in lay['treppen'] if r_ == 's' and ry < 60]
    ax_.sort()                                                       # [unteres Torii, oberes Torii] nach x
    a_oben = [(x0 * T + (x1 + 1) * T) / 2.0 for (x0, x1, ry, r_) in lay['treppen'] if r_ == 's' and ry < 30][0]
    a_mitte = [(x0 * T + (x1 + 1) * T) / 2.0 for (x0, x1, ry, r_) in lay['treppen'] if r_ == 's' and 30 < ry < 60][0]
    for (n, achse, ab, fy) in [('pfosten', a_oben, 96, 222), ('schale', a_oben, 64, 228), ('pfosten', a_mitte, 96, 672),
                               ('schale', a_mitte, 64, 690)]:   # exakt auf den Torii-Achsen
        paar(n, achse, ab, fy, {'anim': 'kerzen', 'flammen_box': [[4, 0, 24, 20]], 'flammen_alle': True, 'flammen_amp': 1.4}
             if n == 'schale' else {})
    # ---------------- Abgesenkter Hof (Nutzer): Schrein an der Nordwand, Laternenpaar, Opferkasten, Wasserbecken
    hx0, hy0, hx1, hy1 = lay['hof']
    hachse = (hx0 * T + (hx1 + 1) * T) / 2.0
    setze('schrein', hachse, (hy0 + 3) * T + 15, {'fest_pos': True}, pruefen=False)
    paar('laterne', hachse, 56, (hy0 + 3) * T + 15, {'anim': 'lampe', 'lampe_box': [8, 18, 20, 30], 'licht_farbe': [255, 200, 120]})
    setze('opfer', hachse, (hy0 + 6) * T - 1, {'fest_pos': True}, pruefen=False)   # gewollt direkt vor dem Schrein
    o_ = setze('becken', (hx1 - 2) * T + 4, (hy1 - 1) * T + 10, {}, True) or setze('becken', (hx0 + 3) * T, (hy1 - 1) * T + 10, {})
    if not o_:
        print('  Wasserbecken im Hof nicht gesetzt')
    # ---------------- Vorlage: Baeume (mit Begleitern), Laternen, Felsbrocken, Unterstand
    baeume = [('baum', 608, 528), ('baum', 655, 528), ('baum', 330, 690), ('baum', 1300, 400),
              ('baum', 1248, 912), ('baum', 1296, 912), ('baum', 360, 1060), ('baum', 420, 1084), ('zypresse', 1080, 552)]   # nur auf Wiese
    gesetzt = []
    for i, (n, px, py) in enumerate(baeume):
        o = suche(n, px, py, {'anim': 'baum', 'nur_kontakt': True}, i % 2 == 1, r=3, klassen='n')
        if o:
            gesetzt.append(o)
    vorne = ['kf00', 'kf24', 'kf52']
    for j, o in enumerate(gesetzt):                                  # Regel 5d: Begleiter vor dem Stumpf + seitlich tiefer
        sx = o['x'] + 22 if o['basis'] == 'baum' else o['x'] + 13
        sy = o['y'] + o['fuss']
        hat = 0
        if o['basis'] == 'baum' and j % 3 != 2:
            hat += any(setze(vorne[j % 3], sx + d, sy + T - 2, {'begleiter': True}, d < 0, gap=-30, klassen='gn')
                       for d in (12, -12, 16, -16))
        for (d, s_, dy) in ((36, -1, T + 6), (36, 1, T + 6), (44, -1, 2 * T), (44, 1, 2 * T)):   # nie in der Stammreihe
            if hat >= 2:
                break
            if setze(vorne[(j + 1 + hat) % 3], sx + s_ * d, sy + dy, {'begleiter': True}, s_ > 0, klassen='gn'):
                hat += 1
        if hat < 2:
            for (d, s_) in ((24, 1), (24, -1)):                      # kleine Blumen/Bueschel an den Sockelecken
                if hat < 2 and setze('lilie' if j % 2 else 'gras', sx + s_ * d, sy + 4, {'begleiter': True, 'ebene': 0},
                                     s_ > 0, gap=-4, klassen='gn'):
                    hat += 1
        if hat < 2:
            print('  Baum mit wenig Begleitern', o['basis'], o['kachel'], hat)
    for (n, px, py) in [('laterne', 568, 552), ('laterne', 455, 888), ('laterne', 1224, 968), ('brocken', 384, 568),
                        ('brocken', 290, 680), ('brocken', 1328, 345), ('unterstand', 1390, 800)]:
        suche(n, px, py, {'anim': 'lampe', 'lampe_box': [8, 18, 20, 30], 'licht_farbe': [255, 200, 120]} if n == 'laterne' else {},
              px > 800, r=3, klassen='gn')                          # nicht auf Pflaster
    # ---------------- Feuervogel: wenige Federn, rote Spinnenlilien auf den Wiesen, Grasbueschel - dezent
    for (n, px, py) in [('feder', 760, 300), ('feder2', 330, 470), ('feder', 1020, 640), ('feder2', 560, 1010),
                        ('lilie', 260, 640), ('lilie', 250, 770), ('lilie', 1270, 880),
                        ('gras', 640, 560), ('gras2', 400, 1160)]:
        suche(n, px, py, {'liegend': n in FLACH, 'ebene': 0, 'nur_kontakt': n not in FLACH}, rnd.random() < 0.5, r=3,
              klassen='gn' if n in ('lilie', 'gras', 'gras2') else 'gwkn')
    for o in objekte:
        if o['basis'] in ('brocken', 'kf00', 'kf24', 'kf52', 'unterstand', 'pfosten', 'opfer'):
            o['nur_kontakt'] = True
    json.dump(objekte, open(os.path.join(OBJ, 'platzierung.json'), 'w'), indent=0)
    print('Karte 50: %d Objekte' % len(objekte))


if __name__ == '__main__':
    main()
    import regeln_a02
    regeln_a02.objekte_pruefen('karte50', 't')
