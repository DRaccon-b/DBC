"""Karte 30 - Odaiba: Objekte setzen -> assets/objekte/karte30/platzierung.json

  python3 tools/karte30_gebaeude.py && python3 tools/karte30_objekte.py && python3 tools/karte30_bauen.py

Grosse Objekte zuerst (Gebaeude genau auf ihren Rechtecken, Riesenrad, Brueckentuerme, Zug), dann Baeume nach der
Vorlage (Parkbaeume Karte 01, Kirschbaeume = Baum von Karte 01 rosa umgefaerbt, Palmen Karte 25, Waldrand rechts),
dann Strassenmoebel (Karte 18) und Kleinkram. Wiederverwendete Sprites werden nach assets/objekte/karte30/fremd kopiert.
"""
import json, math, os, random, shutil
import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte30')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte30')
T = 16
H = lambda h: tuple(int(h[i:i + 2], 16) for i in (1, 3, 5)) + (255,)


def kirsche(q, ziel):
    """Kirschbaum: Laub eines Karte-01-Baums auf eine Rosa-Rampe gelegt (Helligkeit bleibt), Stamm unveraendert."""
    a = np.array(Image.open(q).convert('RGBA')).astype(np.float32)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    laub = (g > r + 8) & (g > b) & (a[..., 3] > 0)
    l = (r * 0.3 + g * 0.55 + b * 0.15) / 255
    rampe = np.array([H(c)[:3] for c in ('#7a3a5a', '#b45a82', '#e08aaa', '#f4b4c8', '#fcdce6')], np.float32)
    t = np.clip((l - 0.18) / 0.62, 0, 1) * (len(rampe) - 1)
    i0 = np.floor(t).astype(int); i1 = np.minimum(i0 + 1, len(rampe) - 1); f = (t - i0)[..., None]
    a[laub, :3] = (rampe[i0] * (1 - f) + rampe[i1] * f)[laub]
    Image.fromarray(a.astype(np.uint8)).save(ziel)


def brueckenturm(w=128, h=336):
    """Pylon der Bruecke (Vorlage): zwei weisse Stahlpfosten an den Gelaendern, drei Querriegel ueber der Fahrbahn,
    Nietreihen, Licht von links. Fuss = Brueckendeck."""
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    hell, mittel, dunkel, kontur = H('#f2f4f8'), H('#c8ced8'), H('#8a929e'), H('#3a4252')
    for x0 in (0, w - 18):
        d.rectangle((x0, 6, x0 + 17, h - 1), fill=mittel, outline=kontur)
        d.rectangle((x0 + 2, 7, x0 + 6, h - 2), fill=hell)
        d.rectangle((x0 + 13, 7, x0 + 16, h - 2), fill=dunkel)
        d.rectangle((x0 - 2, 0, x0 + 19, 8), fill=mittel, outline=kontur)        # Kappe
        d.rectangle((x0 - 1, 1, x0 + 18, 2), fill=hell)
        d.rectangle((x0 - 3, h - 10, x0 + 20, h - 1), fill=dunkel, outline=kontur)   # Fuss
        for y in range(16, h - 12, 10):
            d.point((x0 + 9, y), fill=dunkel)
    for yq in (36, 110, 196):                                      # Querriegel
        d.rectangle((14, yq, w - 15, yq + 11), fill=mittel, outline=kontur)
        d.rectangle((15, yq + 1, w - 16, yq + 3), fill=hell)
        d.rectangle((15, yq + 9, w - 16, yq + 10), fill=dunkel)
        for x in range(24, w - 20, 12):
            d.point((x, yq + 6), fill=dunkel)
    return im


def main():
    rnd = random.Random(30)
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    kl = lay['klassen']
    cols, rows = lay['groesse']
    Hp, Wp = rows * T, cols * T
    wand = np.unpackbits(np.load(os.path.join(KARTE, 'wand.npy')))[:Hp * Wp].reshape(Hp, Wp).astype(bool)
    wasser = np.unpackbits(np.load(os.path.join(KARTE, 'wasser.npy')))[:Hp * Wp].reshape(Hp, Wp).astype(bool)
    os.makedirs(os.path.join(OBJ, 'fremd'), exist_ok=True)
    for i in (0, 1, 2):
        kirsche(os.path.join(ROOT, 'assets', 'objekte', 'karte01', 'baeume', '%02d.png' % i),
                os.path.join(OBJ, 'fremd', 'kirsche%d.png' % i))
    brueckenturm().save(os.path.join(OBJ, 'gebaeude', 'brueckenturm.png'))
    wp = np.array(Image.open(os.path.join(ROOT, 'assets', 'objekte', 'karte29', 'mittel', '03.png')).convert('RGBA')).astype(np.float32)
    l_ = wp[..., :3].mean(2, keepdims=True)                         # Strudel (Karte 29) in Meerblau
    wp[..., :3] = l_ * np.array([0.55, 0.85, 1.15])
    Image.fromarray(np.clip(wp, 0, 255).astype(np.uint8)).save(os.path.join(OBJ, 'fremd', 'strudel.png'))

    def pfad(name):
        if name.startswith(('gebaeude/', 'fremd/', 'klein/', 'statue/')):
            return name + '.png'
        ziel = 'fremd/' + name.replace('/', '-') + '.png'
        if not os.path.exists(os.path.join(OBJ, ziel)):
            shutil.copy(os.path.join(ROOT, 'assets', 'objekte', name + '.png'), os.path.join(OBJ, ziel))
        return ziel

    objekte, belegt = [], []

    def frei(x0, y0, x1, y1):
        return all(x1 < a0 or x0 > a1 or y1 < b0 or y0 > b1 for (a0, b0, a1, b1) in belegt)

    def setze(name, cx, fy, opt=None, spiegeln=False, pruefen=True, auf='land'):
        datei = pfad(name)
        sp = Image.open(os.path.join(OBJ, datei)).convert('RGBA')
        if spiegeln:
            sp = sp.transpose(Image.FLIP_LEFT_RIGHT)
            datei = datei[:-4] + '_m.png'
            sp.save(os.path.join(OBJ, datei))
        bb = sp.getbbox()
        bw = bb[2] - bb[0]
        cx, fy = int(cx), int(fy)
        nb = math.ceil(bw / T)                                       # Regel 1b: kleinster Kachelblock, mittig darin,
        if nb % 2 == 0:                                               # Fuss buendig auf der unteren Kachelkante
            cx = int(round(cx / T)) * T
        else:
            cx = (cx // T) * T + T // 2
        cx -= (nb * T - bw) % 2 and 0
        fy = (fy // T) * T + T - 1
        fuss = (cx - bw // 2 - 2, fy - min(14, bb[3] - bb[1]), cx + bw // 2 + 2, fy + 2)
        if pruefen:
            if not frei(*fuss):
                return None
            unten = (slice(max(0, fy - 4), min(Hp, fy + 1)), slice(max(0, cx - bw // 3), min(Wp, cx + bw // 3 + 1)))
            if auf == 'land' and (wasser[unten].any() or wand[unten].any()):
                return None
        o = {'datei': datei, 'basis': name, 'x': cx - (bb[0] + bw // 2), 'y': fy - (bb[3] - 1), 'fuss': bb[3] - 1,
             'kachel': [cx // T, fy // T], 'ebene': 1, 'an_wand': True}
        o.update(opt or {})
        objekte.append(o)
        belegt.append(fuss)
        return o

    # ---------------------------------------------------------------- Gebaeude (genau auf ihren Rechtecken)
    for (x0, y0, x1, y1, art) in lay['gebaeude']:
        datei = 'gebaeude/%s.png' % art
        sp = Image.open(os.path.join(OBJ, datei))
        objekte.append({'datei': datei, 'basis': 'gebaeude/' + art, 'x': x0 * T, 'y': (y1 + 1) * T - sp.height,
                        'fuss': sp.height - 1, 'kachel': [(x0 + x1) // 2, y1], 'ebene': 1, 'an_wand': True, 'gebaeude': True,
                        'vor_hochbahn': art == 'bahnhof'})
        belegt.append((x0 * T, y0 * T, (x1 + 1) * T, (y1 + 1) * T))
    # Riesenrad (Fuss Reihe 65, Achse Spalte 105), Kiosk darunter, Brueckentuerme, Zug auf der Hochbahn
    setze('gebaeude/riesenrad_0', 105 * T, 66 * T - 2, {'anim': 'riesenrad'}, pruefen=False)
    setze('klein/01', 105 * T, 66 * T - 2, {}, pruefen=False)
    bx0, _, bx1, by1 = lay['bruecke']
    for yt in (by1 + 1,):
        setze('gebaeude/brueckenturm', (bx0 + bx1 + 1) * T // 2, yt * T - 1, {'kein_schatten': True}, pruefen=False)
    zx0, zx1 = lay['hochbahn']['zug']
    zug = Image.open(os.path.join(ROOT, 'assets', 'objekte', 'karte18', 'gebaeude', 'zug.png'))
    shutil.copy(os.path.join(ROOT, 'assets', 'objekte', 'karte18', 'gebaeude', 'zug.png'), os.path.join(OBJ, 'fremd', 'zug.png'))
    objekte.append({'datei': 'fremd/zug.png', 'basis': 'zug', 'x': zx0 * T + (math.ceil(zug.width / T) * T - zug.width) // 2, 'y': 0, 'fuss': zug.height - 1,
                    'kachel': [zx0, 68], 'ebene': 1, 'hochbahn': True})
    setze('fremd/strudel', 6 * T, 102 * T + 10, {'anim': 'portal', 'schattenlos': True}, pruefen=False)
    setze('statue/00', 89 * T, 91 * T - 1, {}, pruefen=False)                       # Freiheitsstatue (gross, Nutzer)
    # ---------------------------------------------------------------- Baeume nach der Vorlage
    BAUM = ['karte01/baeume/00', 'karte01/baeume/01', 'karte01/baeume/02', 'karte01/baeume/04', 'karte01/baeume/15',
            'karte18/baum2/01']                                                       # mehr Arten (Nutzer: Variation)
    KIRSCH = ['karte01/baeume/10', 'fremd/kirsche0', 'fremd/kirsche1', 'fremd/kirsche2']
    WALD = ['karte01/baeume/00', 'karte01/baeume/01', 'karte01/baeume/02', 'karte01/baeume/15', 'karte01/baeume/09',
            'karte01/baeume/06', 'karte18/baum2/01']
    PALME = 'karte25/strand/12'
    gruen = [(3, 3), (6, 5), (9, 11), (29, 9), (33, 10), (37, 8), (44, 2), (81, 3), (45, 32), (49, 36), (45, 39), (49, 44),
             (82, 33), (80, 38), (84, 42), (80, 45), (7, 37), (36, 37), (7, 60), (17, 60), (26, 89), (43, 89), (75, 89),
             (98, 89), (121, 89)]
    kirsch = [(16, 4), (19, 6), (22, 3), (40, 4), (3, 9), (80, 11), (85, 23), (92, 25), (99, 25), (102, 29), (113, 26),
              (122, 23), (29, 90), (93, 90), (111, 90), (106, 90)]
    def auf_rasen(tx, ty):
        return 0 <= ty < rows and 0 <= tx < cols and kl[ty][tx] == 'n'

    def begleiter(tx, ty, i):
        """Regel 5d: Busch (2 Kacheln hoch) eine Reihe tiefer vor dem Stamm ODER Busch hinter der Krone (eine Reihe
        hoeher, seitlich), manchmal beides; Blume nur mit Abstand (nie auf Stammhoehe +-1). Keine Ueberlappung."""
        art = i % 3
        busch = 'karte01/deko/%02d' % (25, 27, 26)[i % 3]
        if art in (0, 2) and auf_rasen(tx, ty + 1):
            setze(busch, tx * T + 8, (ty + 2) * T - 1, {'anim': 'wehen'}, i % 2 == 0, pruefen=False)
        if art in (1, 2):
            sx = 1 if i % 2 else -1
            if auf_rasen(tx + sx, ty - 1):
                setze('karte01/deko/%02d' % (25, 27)[i % 2], (tx + sx) * T + 8, ty * T - 1, {'anim': 'wehen', 'sortier_vor': True},
                      i % 2 == 1, pruefen=False)
        if art == 1:
            bx, by = tx + (2 if i % 4 < 2 else -2), ty + 1
            if auf_rasen(bx, by):
                setze('karte01/deko/%02d' % (i % 5), bx * T + 8, (by + 1) * T - 1, {'anim': 'blume'}, pruefen=False)

    for i, (tx, ty) in enumerate(gruen):
        if auf_rasen(tx, ty) and setze(BAUM[(i * 3) % len(BAUM)], tx * T + 8, (ty + 1) * T - 2, {'anim': 'baum'}, i % 2 == 0):
            begleiter(tx, ty, i)
    for i, (tx, ty) in enumerate(kirsch):
        if auf_rasen(tx, ty) and setze(KIRSCH[i % len(KIRSCH)], tx * T + 8, (ty + 1) * T - 2, {'anim': 'baum'}, i % 2 == 1):
            begleiter(tx, ty, i + 1)
    setze('karte18/strasse/14', 27 * T + 8, 10 * T - 1, {})                   # Bank und Laternen am Weg oben (Vorlage)
    for (tx, ty) in ((13, 10), (39, 11)):
        setze('karte18/strasse/18', tx * T + 8, ty * T - 1, {'anim': 'leuchten'})
    for (tx, ty) in ((3, 44), (9, 44), (15, 44), (21, 44), (27, 44), (33, 44), (39, 44)):   # Baumbeete der Allee
        setze('karte18/baum2/03', tx * T + 8, (ty + 2) * T - 3, {'anim': 'baum'}, tx % 2 == 0)   # Strassenbaum mit Baumscheibe
    for (tx, ty) in ((26, 84), (30, 84), (41, 84), (66, 84), (75, 84), (85, 84), (95, 84), (104, 84), (114, 84),
                     (120, 84), (29, 96), (79, 96), (106, 96), (120, 96)):          # Palmen an der Promenade und am Strand
        setze(PALME, tx * T + 8, (ty + 1) * T - 2, {'anim': 'baum'}, (tx + ty) % 2 == 0)
    for ty in range(21, 92):                                                         # Waldrand rechts: dicht, versetzt,
        for tx in (126, 127, 128, 129):                                              # Kronen ueberlappen (Wald)
            if (tx + ty) % 2 == 0 and kl[min(ty, rows - 1)][tx] == 'f':
                setze(WALD[(tx * 7 + ty * 3) % len(WALD)], tx * T + 8, (ty + 1) * T - 1,
                      {'anim': 'baum', 'kein_schatten': True}, (tx + ty * 5) % 4 < 2, pruefen=False)
    for ty in range(0, rows):                                                       # Waldrand oben links (Nutzer): oberer
        for tx in range(0, cols):                                                    # und linker Kartenrand im Gruen
            if kl[ty][tx] == 'f' and tx < 120 and (tx + ty) % 2 == 0:
                setze(WALD[(tx * 5 + ty * 11) % len(WALD)], tx * T + 8, (ty + 1) * T - 1,
                      {'anim': 'baum', 'kein_schatten': True}, (tx * 3 + ty) % 4 < 2, pruefen=False)
    # ---------------------------------------------------------------- Strassenmoebel
    for x in range(4, 125, 9):                                                       # Laternen an der Hauptstrasse
        for fy in (49 * T - 2, 56 * T + 6):
            if kl[fy // T][x] == 'g':
                setze('karte18/strasse/18', x * T + 8, fy, {'anim': 'leuchten'})
    for x in range(26, 125, 10):                                                     # Laternen an der Uferstrasse
        setze('karte18/strasse/18', x * T + 8, 81 * T - 2, {'anim': 'leuchten'})
    setze('karte18/strasse/41', 26 * T + 8, 49 * T - 2, {})                          # Bushaltestelle
    for (tx, ty) in ((29, 57), (50, 57)):
        setze('klein/02', tx * T + 8, ty * T - 2, {})                                # Telefonzellen
    for (tx, ty) in ((50, 37), (78, 37), (11, 88), (28, 86), (44, 86), (77, 86), (108, 86), (63, 86)):
        setze('karte18/strasse/14', tx * T + 8, ty * T - 2, {})                      # Baenke
    for (tx, ty) in ((53, 27), (76, 27), (53, 47), (76, 47)):
        setze('karte18/strasse/18', tx * T + 8, ty * T - 2, {'anim': 'leuchten'})    # Laternen am Platz (symmetrisch)
    # Autos (stehen auf ihrer Fahrspur), Bus
    for (n, tx, ty, sp) in (('karte18/autos/04', 21, 52, False), ('karte18/autos/00', 37, 52, False),
                            ('karte18/autos/05', 8, 54, True), ('karte18/autos/02', 84, 54, True),
                            ('karte18/autos/12', 75, 52, False), ('karte18/autos/01', 46, 78, True),
                            ('karte18/autos/12', 82, 76, False), ('karte18/autos/00', 117, 78, True)):
        setze(n, tx * T + 8, (ty + 1) * T - 3, {}, sp)
    for o in objekte:
        o.setdefault('fuss', 0)
    json.dump(objekte, open(os.path.join(OBJ, 'platzierung.json'), 'w'), indent=0)
    print('Karte 30: %d Objekte' % len(objekte))


if __name__ == '__main__':
    main()
