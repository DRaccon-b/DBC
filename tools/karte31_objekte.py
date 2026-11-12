"""Karte 31 - Highton View Terrace: Objekte setzen -> assets/objekte/karte31/platzierung.json

  python3 tools/karte31_gebaeude.py && python3 tools/karte31_objekte.py && python3 tools/karte31_bauen.py

Gebaeude zuerst (unten buendig auf ihrer Flaeche, waagerecht im kleinsten Kachelblock mittig), Fussgaengerbruecke ueber
der Querstrasse, Ladenzeile aus einzelnen Ladenfronten, Zug auf der Hochbahn; dann Baeume nach der Vorlage (Park: Laub,
Kirsche, Bonsai-Kiefer; Siedlung: Ginkgo-Allee, Rasenbaeume; unten Strassenbaeume) mit Begleitern (Regel 5d), dann
Pavillon, Uhr, Kiosk, Spielplaetze, Strassenmoebel, Portal. Wiederverwendete Sprites -> assets/objekte/karte31/fremd.
"""
import json, math, os, shutil
import numpy as np
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte31')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte31')
T = 16


def kirsche(q, ziel):
    a = np.array(Image.open(q).convert('RGBA')).astype(np.float32)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    laub = (g > r + 8) & (g > b) & (a[..., 3] > 0)
    l = (r * 0.3 + g * 0.55 + b * 0.15) / 255
    rampe = np.array([(122, 58, 90), (180, 90, 130), (224, 138, 170), (244, 180, 200), (252, 220, 230)], np.float32)
    t = np.clip((l - 0.18) / 0.62, 0, 1) * 4
    i0 = np.floor(t).astype(int); i1 = np.minimum(i0 + 1, 4); f = (t - i0)[..., None]
    a[laub, :3] = (rampe[i0] * (1 - f) + rampe[i1] * f)[laub]
    Image.fromarray(a.astype(np.uint8)).save(ziel)


def main():
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    kl = lay['klassen']
    cols, rows = lay['groesse']
    Hp, Wp = rows * T, cols * T
    wand = np.unpackbits(np.load(os.path.join(KARTE, 'wand.npy')))[:Hp * Wp].reshape(Hp, Wp).astype(bool)
    os.makedirs(os.path.join(OBJ, 'fremd'), exist_ok=True)
    for i in (0, 1):
        kirsche(os.path.join(ROOT, 'assets', 'objekte', 'karte01', 'baeume', '%02d.png' % i), os.path.join(OBJ, 'fremd', 'kirsche%d.png' % i))

    def pfad(name):
        if name.startswith(('gebaeude/', 'fremd/')):
            return name + '.png'
        if name.startswith('karte31/'):
            return name[len('karte31/'):] + '.png'
        ziel = 'fremd/' + name.replace('/', '-') + '.png'
        if not os.path.exists(os.path.join(OBJ, ziel)):
            shutil.copy(os.path.join(ROOT, 'assets', 'objekte', name + '.png'), os.path.join(OBJ, ziel))
        return ziel

    objekte, belegt = [], []

    def frei(x0, y0, x1, y1):
        return all(x1 < a0 or x0 > a1 or y1 < b0 or y0 > b1 for (a0, b0, a1, b1) in belegt)

    def setze(name, cx, fy, opt=None, spiegeln=False, pruefen=True, raster=True):
        datei = pfad(name)
        sp = Image.open(os.path.join(OBJ, datei)).convert('RGBA')
        if spiegeln:
            sp = sp.transpose(Image.FLIP_LEFT_RIGHT)
            datei = datei[:-4] + '_m.png'
            sp.save(os.path.join(OBJ, datei))
        bb = sp.getbbox()
        bw = bb[2] - bb[0]
        cx, fy = int(cx), int(fy)
        if raster:                                                   # Regel 1b: kleinster Kachelblock, mittig, Fuss buendig
            nb = math.ceil(bw / T)
            cx = int(round(cx / T)) * T if nb % 2 == 0 else (cx // T) * T + T // 2
            fy = (fy // T) * T + T - 1
        fuss = (cx - bw // 2 - 2, fy - min(14, bb[3] - bb[1]), cx + bw // 2 + 2, fy + 2)
        if pruefen:
            if not frei(*fuss):
                return None
            unten = (slice(max(0, fy - 4), min(Hp, fy + 1)), slice(max(0, cx - bw // 3), min(Wp, cx + bw // 3 + 1)))
            if wand[unten].any():
                return None
        o = {'datei': datei, 'basis': name, 'x': cx - (bb[0] + bw // 2), 'y': fy - (bb[3] - 1), 'fuss': bb[3] - 1,
             'kachel': [cx // T, fy // T], 'ebene': 1, 'an_wand': True}
        o.update(opt or {})
        objekte.append(o)
        belegt.append(fuss)
        return o

    def gebaeude(art, x0, y1, x1, opt=None):
        sp = Image.open(os.path.join(OBJ, 'gebaeude', art + '.png'))
        w = sp.getbbox()[2] - sp.getbbox()[0]
        nb = math.ceil(w / T)
        bx = x0 + ((x1 - x0 + 1) - nb) // 2                           # Block mittig in der Flaeche
        cx = bx * T + nb * T // 2
        o = setze('gebaeude/' + art, cx, (y1 + 1) * T - 1, dict({'gebaeude': True}, **(opt or {})), pruefen=False)
        belegt[-1] = (o['x'], o['y'], o['x'] + sp.width, o['y'] + sp.height)
        return o

    # ---------------------------------------------------------------- Gebaeude
    for (x0, y0, x1, y1, art) in lay['gebaeude']:
        if art == 'laeden':
            breiten = [Image.open(os.path.join(OBJ, 'gebaeude', 'laden_%d.png' % i)).width for i in range(8)]
            x = min(x0 * T, (x1 + 1) * T - 6 - sum(breiten))          # Ladenzeile luecklos, rechts Abstand zum Baumrand
            for i in range(8):
                sp = Image.open(os.path.join(OBJ, 'gebaeude', 'laden_%d.png' % i))
                setze('gebaeude/laden_%d' % i, x + sp.width // 2, (y1 + 1) * T - 1, {'gebaeude': True}, pruefen=False,
                      raster=False)
                x += sp.width
            continue
        gebaeude(art, x0, y1, x1, {'vor_hochbahn': art == 'bahnhof'})
    setze('gebaeude/bruecke', 60 * T + 8, 81 * T - 1, {'gebaeude': True}, pruefen=False)      # Fussgaengerbruecke
    zug = 'karte18/gebaeude/zug'
    objekte.append({'datei': pfad(zug), 'basis': 'zug', 'x': lay['hochbahn']['zug'][0] * T, 'y': 0, 'fuss': 60,
                    'kachel': [1, 72], 'ebene': 1, 'hochbahn': True})
    # ---------------------------------------------------------------- Park oben
    setze('karte07/gross/02', 33 * T + 8, 7 * T - 1, {})                                         # Pavillon
    setze('karte31/uhr/00', 60 * T + 8, 14 * T - 1, {}, raster=False)                                       # Uhr (Nutzer: oben groesser)
    setze('karte30/klein/01', 75 * T, 17 * T - 1, {})                                            # Kiosk
    setze('karte29/gross/03', 104 * T, 5 * T - 1, {'anim': 'portal', 'schattenlos': True}, pruefen=False)   # Riss
    setze('karte29/mittel/02', 104 * T, 9 * T - 1, {'anim': 'portal'})                           # Portal-Tor
    LAUB = ['karte01/baeume/00', 'karte18/baum2/01', 'karte01/baeume/01', 'karte01/baeume/04', 'karte01/baeume/02',
            'karte01/baeume/15', 'karte01/baeume/13']                                 # mehr Arten (Nutzer: Variation)
    KIRSCH = ['karte01/baeume/10', 'fremd/kirsche0', 'fremd/kirsche1']
    KIEFER = 'karte07/mittel/04'                                               # Bonsai-Kiefer
    baeume = [('L', 2, 3), ('K', 6, 3), ('L', 11, 3), ('L', 17, 3), ('C', 24, 3), ('L', 4, 9), ('L', 6, 17), ('L', 18, 21),
              ('K', 25, 9), ('L', 45, 3), ('K', 49, 3), ('L', 54, 3), ('L', 46, 8), ('C', 30, 21), ('C', 35, 20),
              ('C', 41, 22), ('C', 51, 22), ('L', 67, 3), ('C', 71, 3), ('L', 76, 3), ('K', 81, 3), ('K', 65, 9),
              ('L', 72, 8), ('L', 76, 21), ('L', 68, 21), ('L', 92, 3), ('K', 96, 3), ('C', 110, 3), ('L', 116, 3),
              ('L', 117, 12), ('L', 116, 22), ('C', 92, 13), ('C', 89, 22), ('C', 108, 22)]
    for i, (art, tx, ty) in enumerate(baeume):
        n = LAUB[i % len(LAUB)] if art == 'L' else KIRSCH[i % len(KIRSCH)] if art == 'C' else KIEFER
        if kl[ty][tx] != 'n':
            continue
        if setze(n, tx * T + 8, (ty + 1) * T - 1, {'anim': 'baum'}, i % 2 == 0):
            if kl[ty + 1][tx] == 'n':                                 # Regel 5d: Busch vor dem Stamm / Blume mit Abstand
                setze('karte01/deko/%02d' % (25, 27, 26)[i % 3], tx * T + 8, (ty + 2) * T - 1, {'anim': 'wehen'},
                      pruefen=False)
            if i % 3 == 1 and kl[ty + 1][tx + 2] == 'n':
                setze('karte01/deko/%02d' % (i % 5), (tx + 2) * T + 8, (ty + 2) * T - 1, {'anim': 'blume'})
    for (tx, ty) in ((16, 10), (39, 10), (108, 7), (107, 15), (100, 15), (61, 10)):   # Laternen
        setze('karte18/strasse/18', tx * T + 8, ty * T - 1, {'anim': 'leuchten'})
    for (tx, ty) in ((21, 12), (44, 17), (88, 12), (113, 12), (69, 12)):                         # Baenke
        setze('karte18/strasse/14', tx * T + 8, ty * T - 1, {})
    for i, (x0, x1) in enumerate(lay.get('hecken', [])):                                          # Hecken an der Promenade
        n = ['karte01/baeume/14', 'karte01/baeume/12', 'karte01/baeume/14', 'karte01/baeume/13'][i % 4] \
            if x1 - x0 >= 2 else 'karte01/deko/%02d' % (25, 27)[i % 2]                          # (K01-Buesche, schmal: Busch)
        setze(n, (x0 + x1 + 1) * T // 2, 26 * T - 1, {'anim': 'wehen'}, i % 2 == 0, pruefen=False)
    for x in range(6, 118, 8):                                                                   # Promenade: Baenke,
        setze('karte18/strasse/14' if (x // 8) % 2 else 'karte18/strasse/18', x * T + 8, 27 * T - 1,   # Laternen
              {} if (x // 8) % 2 else {'anim': 'leuchten'})
    # ---------------------------------------------------------------- Siedlung
    GINKGO = ['karte18/gebaeude/gold_00', 'karte18/gebaeude/gold_01', 'karte18/gebaeude/gold_02']
    for i, ty in enumerate(range(40, 72, 6)):                                                     # Ginkgo-Allee
        for tx in (53, 67):
            if kl[ty][tx] in 'eg':
                setze(GINKGO[(i + tx) % 3], tx * T + 8, (ty + 1) * T - 1, {'anim': 'baum'})
    for (art, tx, ty) in (('L', 30, 55), ('L', 37, 61), ('L', 3, 68), ('C', 12, 68), ('L', 73, 56), ('L', 103, 56),
                          ('C', 107, 63), ('G', 98, 63), ('G', 50, 86), ('G', 48, 89)):
        n = LAUB[(tx + ty) % 4] if art == 'L' else KIRSCH[(tx + ty) % 3] if art == 'C' else GINKGO[(tx + ty) % 3]
        if setze(n, tx * T + 8, (ty + 1) * T - 1, {'anim': 'baum'}, tx % 2 == 0) and kl[ty + 1][tx] == 'n':
            setze('karte01/deko/%02d' % (25, 27)[tx % 2], tx * T + 8, (ty + 2) * T - 1, {'anim': 'wehen'}, pruefen=False)
    WALD = ['karte01/baeume/00', 'karte01/baeume/01', 'karte01/baeume/02', 'karte01/baeume/15', 'karte01/baeume/09',
            'karte01/baeume/06', 'karte01/baeume/04', 'karte18/baum2/01', 'karte01/baeume/07', 'karte01/baeume/13',
            'karte01/baeume/08']
    hb = lay['hochbahn']
    for ty in range(rows):                                                                       # Baumrand am Kartenrand
        for tx in range(cols):                                                                   # (Nutzer): dicht, versetzt
            if kl[ty][tx] != 'f' or (tx + ty) % 2:
                continue
            if tx <= hb['x1'] and hb['y0'] <= ty <= hb['y1'] + 1:
                continue
            setze(WALD[(tx * 7 + ty * 3) % len(WALD)], tx * T + 8, (ty + 1) * T - 1,
                  {'anim': 'baum', 'kein_schatten': True}, (tx * 3 + ty) % 4 < 2, pruefen=False)
    # Spielplaetze
    for (n, tx, ty) in (('karte10/spielplatz/01', 21, 56), ('karte10/spielplatz/00', 18, 60), ('karte18/gebaeude/kletterkuppel', 9, 59),
                        ('karte10/spielplatz/01', 83, 57), ('karte10/spielplatz/01', 89, 57), ('karte10/spielplatz/00', 80, 61),
                        ('karte10/spielplatz/02', 86, 61), ('karte18/gebaeude/kletterkuppel', 92, 61)):
        setze(n, tx * T + 8, (ty + 1) * T - 1, {})
    for (tx, ty) in ((8, 53), (30, 53)):                                                         # Fahrradunterstaende
        setze('karte18/strasse/41', tx * T + 8, ty * T - 1, {})
    for (tx, ty) in ((20, 52), (95, 52)):
        setze('karte30/klein/08', tx * T + 8, ty * T - 1, {})                                    # Infotafeln
    for (tx, ty) in ((3, 57), (20, 63), (75, 59), (96, 61)):
        setze('karte18/strasse/14', tx * T + 8, ty * T - 1, {})
    # Bahnhofsvorplatz und Strassen
    setze('karte30/klein/09', 13 * T + 8, 90 * T - 1, {})                                       # Uhr
    setze('karte18/strasse/02', 25 * T + 8, 89 * T - 1, {})                                     # Briefkasten
    setze('karte18/strasse/41', 27 * T + 8, 93 * T - 1, {})                                     # Bushaltestelle
    for (tx, ty) in ((67, 88), (68, 88), (90, 81)):
        setze('karte18/strasse/00' if tx % 2 else 'karte18/strasse/01', tx * T + 8, ty * T - 1, {})   # Automaten
    for x in range(6, 118, 10):
        setze('karte18/strasse/18', x * T + 8, 94 * T - 1, {'anim': 'leuchten'})
        setze('karte18/strasse/18', x * T + 5, 100 * T - 1, {'anim': 'leuchten'})
    for (n, tx, ty, sp) in (('karte18/autos/04', 14, 95, False), ('karte18/autos/03', 37, 97, True),
                            ('karte18/autos/00', 59, 50, False), ('karte18/autos/06', 60, 70, False),
                            ('karte18/autos/03', 88, 83, True), ('karte18/autos/00', 109, 82, False),
                            ('karte18/autos/01', 82, 95, False), ('karte18/autos/04', 99, 97, True),
                            ('karte18/autos/12', 114, 97, True)):
        setze(n, tx * T + 8, (ty + 1) * T - 3, {}, sp)
    # Kleinkram an den Strassen (Nutzer: mit PixelLab statt gezeichnet): Laub, Zeitung, Dose, Flasche, Tueten
    import random
    rnd = random.Random(3131)
    MUELL = ['karte31/muell_klein/01', 'karte31/muell_klein/02', 'karte31/muell_klein/03', 'karte31/muell_klein/18',
             'karte31/muell_klein/39', 'karte31/muell_klein/40', 'karte31/muell_klein/49']   # PixelLab, halbiert (Massstab)
    kand = []
    for ty in range(rows):
        for tx in range(cols):
            if kl[ty][tx] not in 'gs':
                continue
            if any(0 <= ty + dy < rows and 0 <= tx + dx < cols and kl[ty + dy][tx + dx] == 's'
                   for dy in (-2, -1, 0, 1, 2) for dx in (-2, -1, 0, 1, 2)):
                if kl[ty][tx] == 's' and not any(kl[ty + dy][tx] != 's' for dy in (-1, 1) if 0 <= ty + dy < rows):
                    continue                                                                    # nicht mitten auf der Fahrbahn
                kand.append((tx, ty))
    rnd.shuffle(kand)
    gesetzt = []
    for (tx, ty) in kand:
        if len(gesetzt) >= 60:
            break
        if any(abs(tx - x) + abs(ty - y) < 5 for (x, y) in gesetzt):
            continue
        ginkgo = 50 <= tx <= 69 and 36 <= ty <= 75
        n = 'karte31/muell_klein/00' if ginkgo and rnd.random() < 0.7 else rnd.choice(MUELL)
        if setze(n, tx * T + rnd.randint(3, 13), ty * T + rnd.randint(8, 15), {'liegend': True}, rnd.random() < 0.5,
                 raster=False):
            gesetzt.append((tx, ty))
    json.dump(objekte, open(os.path.join(OBJ, 'platzierung.json'), 'w'), indent=0)
    print('Karte 31: %d Objekte' % len(objekte))


if __name__ == '__main__':
    main()
