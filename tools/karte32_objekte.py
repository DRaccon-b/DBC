"""Karte 32 - Dream Ruins: Objekte setzen -> assets/objekte/karte32/platzierung.json

  python3 tools/karte32_bauen.py && python3 tools/karte32_objekte.py && python3 tools/karte32_bauen.py

Wiederverwendet (Regel 3): Schlossausstattung von Karte 09 (Buntglasfenster, Banner, Kandelaber, Saeulen, Throne,
Kronleuchter, Tuerme, Tor, Spiegel, Grabmale, Zaeune, Gruefte, Brunnen, tote Baeume) und Friedhofskleinkram von
Karte 08/09. Neu (PixelLab k32_traum): schwebende Traumobjekte in der Sternenleere (Taschenuhren, Fernseher,
Spielkarte, Spiegel, Sanduhren, Kristallkugeln, Saeckchen, Kristalle ...).
Paare stehen spiegelsymmetrisch zur Teppich- bzw. Raumachse; Tuerme im festen Rhythmus symmetrisch zum Tor.
"""
import json, math, os, random, shutil
import numpy as np
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte32')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte32')
T = 16
ACHSE = 36.5 * T                 # roter Teppich (Spalten 35-37): Achse von Thron, Saal, Halle und Tor
K9 = 'karte09/'


def main():
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    kl = lay['klassen']
    cols, rows = lay['groesse']
    Hp, Wp = rows * T, cols * T
    flaeche = np.unpackbits(np.load(os.path.join(KARTE, 'wandflaeche.npy')))[:Hp * Wp].reshape(Hp, Wp).astype(bool)
    lvl = np.load(os.path.join(KARTE, 'pixelhoehe.npy'))
    os.makedirs(os.path.join(OBJ, 'fremd'), exist_ok=True)

    def pfad(name):
        if name.startswith('karte32/'):
            return name[len('karte32/'):] + '.png'
        ziel = 'fremd/' + name.replace('/', '-') + '.png'
        if not os.path.exists(os.path.join(OBJ, ziel)):
            shutil.copy(os.path.join(ROOT, 'assets', 'objekte', name + '.png'), os.path.join(OBJ, ziel))
        return ziel

    objekte, belegt = [], []

    def frei(x0, y0, x1, y1):
        return all(x1 < a0 or x0 > a1 or y1 < b0 or y0 > b1 for (a0, b0, a1, b1) in belegt)

    def setze(name, cx, fy, opt=None, pruefen=True, raster=True, spiegeln=False):
        datei = pfad(name)
        sp = Image.open(os.path.join(OBJ, datei)).convert('RGBA')
        if spiegeln:
            sp = sp.transpose(Image.FLIP_LEFT_RIGHT)
            datei = datei[:-4] + '_m.png'
            sp.save(os.path.join(OBJ, datei))
        bb = sp.getbbox()
        bw = bb[2] - bb[0]
        cx, fy = int(cx), int(fy)
        if raster:                                                   # Regel 1b
            nb = math.ceil(bw / T)
            cx = int(round(cx / T)) * T if nb % 2 == 0 else (cx // T) * T + T // 2
            fy = (fy // T) * T + T - 1
        fuss = (cx - bw // 2 - 2, fy - min(14, bb[3] - bb[1]), cx + bw // 2 + 2, fy + 2)
        if pruefen:
            if not frei(*fuss):
                return None
            y0_, x0_ = max(0, fy - 3), max(0, cx - bw // 3)
            if (lvl[y0_:fy + 1, x0_:cx + bw // 3 + 1] != 1).any():   # Fuss nur auf Boden (keine Mauer, Leere, Wand)
                return None
            if any(kl[fy // T][xx // T] == 'p' for xx in (cx - bw // 3, cx, cx + bw // 3)):   # nicht auf Wegen
                return None
        o = {'datei': datei, 'basis': name, 'x': cx - (bb[0] + bw // 2), 'y': fy - (bb[3] - 1), 'fuss': bb[3] - 1,
             'kachel': [cx // T, fy // T], 'ebene': 1}
        o.update(opt or {})
        objekte.append(o)
        belegt.append(fuss)
        return o

    def wand(name, cx, reihe, opt=None):
        """Wandobjekt frei auf der Wandflaeche ab Reihe 'reihe' (Abstand zur Krone, ueber der Goldleiste)."""
        datei = pfad(name)
        sp = Image.open(os.path.join(OBJ, datei)).convert('RGBA')
        bb = sp.getbbox()
        spalte = flaeche[reihe * T:(reihe + 4) * T, int(cx)]
        if not spalte.any():
            print('  keine Wandflaeche:', name, cx / T, reihe)
            return
        oben = reihe * T + int(np.nonzero(spalte)[0].min())
        hoehe = bb[3] - bb[1]
        d = max(4, min(7, 37 - hoehe))
        objekte.append({'datei': datei, 'basis': name, 'x': int(cx) - (bb[0] + bb[2]) // 2, 'y': oben + d - bb[1],
                        'fuss': bb[3] - 1, 'kachel': [int(cx) // T, oben // T + 2], 'ebene': 1, 'an_wand': True,
                        'kein_schatten': True, 'keine_verdeckung': True, **(opt or {})})

    def paar(name, dx_px, fy, opt=None, achse=ACHSE, raster=False):
        """Paar exakt spiegelsymmetrisch zur Achse (Regel 'Symmetrische Plaetze' / 'Achsen in Raeumen')."""
        a = setze(name, achse - dx_px, fy, opt, raster=raster)
        b = setze(name, achse + dx_px, fy, opt, raster=raster, spiegeln=True)
        if not (a and b):
            print('  Paar unvollstaendig:', name, dx_px / T, fy / T)

    def fuss(row):
        return (row + 1) * T - 1

    # ------------------------------------------------------------------ Wandflaechen
    for x in (34.5, 38.5):                                            # Thronturm: zwei Banner hinter dem Thron
        wand(K9 + 'banner/03', x * T, 2)
    FENSTER = [K9 + 'wand/02', K9 + 'wand/00', K9 + 'wand/01']
    for i, x in enumerate((14.5, 18.5, 22.5, 26.5)):                   # linker Fluegel
        wand(FENSTER[i % 3], x * T, 12)
    for x in (16.5, 20.5, 24.5):
        wand(K9 + 'banner/02', x * T, 12)
    for i, x in enumerate((46.5, 50.5, 54.5)):                         # rechter Fluegel
        wand(FENSTER[(i + 1) % 3], x * T, 12)
    for x in (48.5, 52.5):
        wand(K9 + 'banner/02', x * T, 12)
    for dx in (4, 10, 16):                                            # Mittelmauer: Banner paarweise zur Achse
        for s in (-1, 1):
            wand(K9 + 'banner/03', ACHSE + s * dx * T, 30)
    for i, x in enumerate((66.5, 70.5, 74.5, 78.5, 82.5)):             # Festsaal: Buntglasfenster (Achse 74.5)
        wand(FENSTER[i % 3], x * T, 33)
    for x in (13, 25, 48, 60, 72, 84):                                 # Aussenmauer: schmale Fenster zwischen Tuermen
        wand(K9 + 'wand/03', (x + 0.5) * T, 54)
    # ------------------------------------------------------------------ Thron, Tor, Tuerme (feste Achsen)
    setze(K9 + 'moebel/07', ACHSE, fuss(8), {'achse': True}, raster=False)          # Thron im Thronturm
    setze(K9 + 'moebel/07', ACHSE, fuss(15), {'achse': True}, raster=False, pruefen=False)   # Nischenthron
    for dx in (5, 17, 29, 41):                                        # Tuerme alle 12 Kacheln, symmetrisch zum Tor
        for s in (-1, 1):
            x = ACHSE + s * dx * T
            if T <= x <= Wp - T:
                o = setze(K9 + 'turm/01', x, fuss(57), {'an_wand': True, 'kein_schatten': True,
                                                        'keine_verdeckung': True}, raster=False, pruefen=False)
    # ------------------------------------------------------------------ Thronturm und grosser Saal
    paar(K9 + 'moebel/01', 6 * T, fuss(6), {'anim': 'kerzen'})                       # Kandelaber neben dem Thron
    paar(K9 + 'moebel/00', 8 * T, fuss(19))                                         # Saeulen (2 Paare x 2 Reihen)
    paar(K9 + 'moebel/00', 16 * T, fuss(19))
    paar(K9 + 'moebel/00', 8 * T, fuss(24))
    paar(K9 + 'moebel/00', 16 * T, fuss(24))
    setze('karte32/leuchter/00', 24 * T + 8, fuss(22), {'liegend': True, 'versatz': 2})   # Nutzer: weniger Kronleuchter, kaputt am Boden
    paar(K9 + 'moebel/01', 7 * T, fuss(16), {'anim': 'kerzen'})                      # Kandelaber am Teppich
    for (x, y) in ((13, 16), (13, 25), (55, 16)):
        setze(K9 + 'moebel/01', x * T + 8, fuss(y), {'anim': 'kerzen'})
    for (x, y) in ((53, 21), (54, 25), (51, 17)):                     # Truemmer an der abgebrochenen Kante
        setze(K9 + 'wand/45', x * T + 8, fuss(y))
    # ------------------------------------------------------------------ Bannerhalle
    for y in (36, 42, 48):
        paar(K9 + 'moebel/00', 10 * T, fuss(y))                                     # Saeulenreihen (mit Luft)
    setze('karte32/leuchter/01', 42 * T + 8, fuss(45), {'liegend': True, 'versatz': 2, 'anim': 'kerzen'}, spiegeln=True)
    paar(K9 + 'moebel/01', 5 * T, fuss(34), {'anim': 'kerzen'})
    for (x, y) in ((13, 35), (13, 40), (13, 49), (57, 35), (57, 40), (57, 49)):
        setze(K9 + 'moebel/01', x * T + 8, fuss(y), {'anim': 'kerzen'})
    for (x, y) in ((20, 44), (13, 46), (16, 49)):                     # Truemmer am Loch
        setze(K9 + 'wand/45', x * T + 8, fuss(y))
    # ------------------------------------------------------------------ Festsaal (Achse 74.5)
    FA = 74.5 * T
    setze('karte32/leuchter/00', 70 * T + 8, fuss(42), {'liegend': True, 'versatz': 2}, spiegeln=True)
    for y in (36, 40, 44, 48):
        paar(K9 + 'moebel/01', 10 * T, fuss(y), {'anim': 'kerzen'}, achse=FA)
    # ------------------------------------------------------------------ Friedhof
    rnd = random.Random(3232)
    GRAEBER = ['k8/mittel/00', 'k8/mittel/01', 'k8/mittel/02', 'k8/mittel/03', 'wand/21', 'wand/22']
    for (x0, x1) in ((24, 33), (43, 50), (57, 67), (73, 78), (81, 86)):   # Grabreihe an der Mauer
        for x in range(x0, x1 + 1, 2):
            setze(K9 + rnd.choice(GRAEBER), x * T + 8, fuss(59), {}, spiegeln=rnd.random() < 0.3)
    for (x0, x1) in ((26, 33), (40, 50), (56, 68), (74, 79), (82, 86)):  # Eisenzaun-Abschnitte (Luecken an Wegen)
        for x in range(x0, x1 + 1, 2):
            setze(K9 + 'wand/19', x * T + 16, fuss(61), {}, raster=False)
    for (x0, x1) in ((26, 34), (56, 68)):                            # eingezaeunte Grabfelder
        for x in range(x0, x1 + 1, 2):
            if any(kl[y][xx] == 'p' for y in range(66, 70) for xx in (x, x + 1)):
                continue                                              # Grabfeld nicht auf dem Weg
            setze(K9 + 'wand/19', x * T + 16, fuss(66), {}, raster=False, pruefen=False)
            setze(K9 + rnd.choice(GRAEBER), x * T + 8, fuss(68), {}, pruefen=False)
            setze(K9 + 'wand/19', x * T + 16, fuss(69), {}, raster=False, pruefen=False)
    for (x, y) in ((34, 61), (38, 61), (51, 61), (55, 61), (69, 61), (73, 61), (25, 68), (35, 68), (55, 68), (69, 68)):
        setze(K9 + 'wand/31', x * T + 8, fuss(y))                    # kleine Wasserspeier-Statuen an den Wegen
    setze(K9 + 'turm/09', 44.5 * T, fuss(70), {}, raster=False, pruefen=False)   # Brunnen mitten auf den Plaetzen
    setze(K9 + 'turm/09', 78.5 * T, fuss(70), {}, raster=False, pruefen=False)
    for (n, x) in (('turm/04', 29), ('turm/08', 47), ('turm/04', 62), ('turm/08', 81)):
        setze(K9 + n, x * T + 8, fuss(77), {})                        # Gruefte unten
    for (x, y) in ((25, 61), (23, 69), (40, 77), (56, 77), (69, 76), (75, 77)):
        o = setze(K9 + 'turm/07', x * T + 8, fuss(y), {'anim': 'wehen'}, spiegeln=rnd.random() < 0.5)
        if o:
            setze(K9 + rnd.choice(['k8/mittel/14', 'k8/klein/48']), (x + 1) * T + 8, fuss(y + 1),
                  {'begleiter': True, 'anim': 'wehen'}, pruefen=False)
    for (x, y) in ((5, 60), (18, 60), (4, 74), (21, 74)):            # Mauerreste
        setze(K9 + 'turm/15', x * T + 8, fuss(y), {})
    for (x, y) in ((5, 66), (20, 66)):
        setze(K9 + 'wand/45', x * T + 8, fuss(y), {})
    setze(K9 + 'moebel/04', 11.5 * T, fuss(75), {}, raster=False)   # Traumspiegel (Portal)
    paar(K9 + 'moebel/01', 3.5 * T, fuss(75), {'anim': 'kerzen'}, achse=11.5 * T)
    STREU = ['k8/klein/04', 'k8/klein/05', 'k8/klein/07', 'k8/klein/12', 'k8/klein/47', 'k8/klein/48', 'k8/klein/06']
    n = 0
    for _ in range(3000):
        if n >= 45:
            break
        tx, ty = rnd.randrange(3, 87), rnd.randrange(58, 77)
        if kl[ty][tx] != 'g':
            continue
        nm = rnd.choice(STREU)
        if setze(K9 + nm, tx * T + 8, fuss(ty), {'anim': 'kerzen'} if nm == 'k8/klein/06' else {'anim': 'wehen'}):
            n += 1
    # ------------------------------------------------------------------ Traumobjekte in der Leere (schwebend)
    TRAUM = ['karte32/traum/%02d' % i for i in (0, 63, 33, 1, 2, 3, 7, 62, 9, 60, 28, 54, 47, 51, 38, 30, 5, 27)]
    leer = np.array([[c == '.' for c in z] for z in kl])
    gesetzt = []
    for _ in range(6000):
        if len(gesetzt) >= 34:
            break
        tx, ty = rnd.randrange(1, cols - 1), rnd.randrange(1, 51)
        if not leer[max(0, ty - 2):ty + 3, max(0, tx - 2):tx + 3].all():
            continue
        if any(abs(tx - x) + abs(ty - y) < 6 for (x, y) in gesetzt):
            continue
        if setze(rnd.choice(TRAUM), tx * T + 8, fuss(ty), {'schwebend': True, 'kein_schatten': True,
                                                          'phase': rnd.randrange(4)}, pruefen=False):
            gesetzt.append((tx, ty))
    json.dump(objekte, open(os.path.join(OBJ, 'platzierung.json'), 'w'), indent=0)
    print('Karte 32: %d Objekte' % len(objekte))


if __name__ == '__main__':
    main()
