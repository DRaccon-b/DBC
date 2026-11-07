"""Objekte fuer Karte 18 (The Fog-Bound City) - am 16x16-Raster nach den Regeln aus CLAUDE.md.

  python3 tools/karte18_bauen.py && python3 tools/karte18_objekte.py && python3 tools/karte18_bauen.py

Reihenfolge (grosse Objekte zuerst): Gebaeude -> Hochbahn-Pfeiler und Zug -> Baeume/Pflanzkuebel -> Marktstand,
Container, Spielgeraete, Bushaltestellen -> Laternen, Ampeln -> Stadtmoebel -> Autos -> Kleinkram.
Jedes Objekt steht mittig in seinem kleinsten Kachelblock, der Fuss buendig auf der unteren Kachelkante (Regel 1b).
Geprueft wird: Pixelabstand 2 px zu anderen Objekten (ausser gewollten Begleitern), Fuss auf passendem Boden, nicht
vor Tueren, Zebrastreifen, Treppe oder Teleportern. Paare auf dem Platz stehen spiegelsymmetrisch zur Hallenachse.
Fahrtrichtung: Linksverkehr - Ostwaerts auf der Nordspur, Westwaerts auf der Suedspur; die PixelLab-Autos schauen nach
links und werden fuer Ostwaerts gespiegelt.

Wiederverwendet: Laterne (Karte 02), Ampel/Uhr/Bank/Absperrung/Spielplatz (Karte 10), Muelleimer/Hydrant/Kegel/
Container/Lkw/Gabelstapler/Kisten/Marktstand (Karte 02), Sandsaecke (Karte 03), Baeume/Hecke/Busch (Karte 01, 10).
Neu (PixelLab k18_*): Autos, Bus, Hochbahn-Wagen, Boot, Haltestelle, Automaten, Briefkasten, Telefon, Fahrrad,
Infotafel, Fahnen, Rettungsring, Ginkgo-Baeume.
"""
import json, math, os, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageFilter
from karte04_objekte import saeubern

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte18')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte18')
T = 16
GEHEN = set('gpqctkh')                                   # Gehflaechen fuer Stadtmoebel
LEUCHTEN = {'karte02/abgeleitet/laterne': 'laterne18', 'karte02/klein/15': 'laterne18', 'karte10/banner/13': 'ampel18',
            'k18/strasse/00': 'automat', 'k18/strasse/01': 'automat', 'k18/strasse/06': 'automat',
            'gebaeude/laeden': 'reklame', 'k18/gross/03': 'automat'}


def pfad(name):
    """'karte10/banner/13' -> Fremd-Sprite (wird nach karte18/fremd kopiert); 'k18/autos/00' -> eigenes PixelLab;
    'gebaeude/halle' -> prozedurales Gebaeude."""
    if name.startswith('k18/'):
        return os.path.join(OBJ, name[4:] + '.png')
    if name.startswith('gebaeude/'):
        return os.path.join(OBJ, name + '.png')
    ziel = os.path.join(OBJ, 'fremd', name.replace('/', '-') + '.png')
    if not os.path.exists(ziel):
        os.makedirs(os.path.dirname(ziel), exist_ok=True)
        shutil.copy(os.path.join(ROOT, 'assets', 'objekte', name + '.png'), ziel)
    return ziel


class Platz:
    def __init__(self, lay, lvl):
        self.lay, self.lvl = lay, lvl
        self.kl = np.array([list(r) for r in lay['klassen']])
        self.R, self.C = self.kl.shape
        self.pixel = np.zeros(lvl.shape, bool)
        self.sperr = np.zeros(self.kl.shape, bool)
        self.objekte, self.cache, self.fehl = [], {}, []
        os.makedirs(os.path.join(OBJ, 'sauber'), exist_ok=True)

    def sprite(self, name, spiegel=False):
        key = (name, spiegel)
        if key not in self.cache:
            p = pfad(name)
            sp = Image.open(p).convert('RGBA')
            if not name.startswith('gebaeude/'):
                sp = saeubern(sp)
            if spiegel:
                sp = sp.transpose(Image.FLIP_LEFT_RIGHT)
            datei = 'sauber/%s%s.png' % (name.replace('/', '-'), '_m' if spiegel else '')
            sp.save(os.path.join(OBJ, datei))
            al = np.array(sp.getchannel('A')) >= 128
            zu = int(np.nonzero(al.any(axis=1))[0].max())
            xs = np.nonzero(al.any(axis=0))[0]
            self.cache[key] = (datei, al, zu, xs.min(), xs.max())
        return self.cache[key]

    def setzen(self, name, bx, reihe, spiegel=False, anim=None, boden=GEHEN, n=None, begleiter=False, extra=None,
               pruefen=True, cx=None):
        if not os.path.exists(pfad(name)) if name.startswith('k18/') else False:
            self.fehl.append((name, bx, reihe, 'Sprite fehlt'))
            return None
        datei, al, zu, xa, xb = self.sprite(name, spiegel)
        breite = xb - xa + 1
        n = n or max(1, math.ceil(breite / T))
        mitte = cx if cx is not None else bx * T + n * T / 2.0
        x = int(round(mitte - (xa + xb + 1) / 2.0))
        y = (reihe + 1) * T - 1 - zu
        h_, w_ = al.shape
        if pruefen:
            grund = self._pruefen(al, x, y, zu, boden, begleiter)
            if grund:
                self.fehl.append((name, bx, reihe, grund))
                return None
        o = {'datei': datei, 'basis': name, 'x': x, 'y': y, 'fuss': zu, 'kachel': [int(mitte // T), reihe], 'ebene': 1}
        if anim or LEUCHTEN.get(name):
            o['anim'] = anim or LEUCHTEN[name]
        if extra:
            o.update(extra)
        self.objekte.append(o)
        d = np.array(Image.fromarray((al * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(5))) > 0
        y0, x0 = max(0, y), max(0, x)
        y1, x1 = min(self.pixel.shape[0], y + h_), min(self.pixel.shape[1], x + w_)
        if not begleiter and not (extra or {}).get('gebaeude'):
            self.pixel[y0:y1, x0:x1] |= d[y0 - y:y1 - y, x0 - x:x1 - x]
        return o

    def _pruefen(self, al, x, y, zu, boden, begleiter):
        h_, w_ = al.shape
        if x < 0 or y < -64 or x + w_ > self.pixel.shape[1] or y + h_ > self.pixel.shape[0]:
            return 'ausserhalb'
        fuss = np.zeros_like(al)
        fuss[max(0, zu - 3):zu + 1] = al[max(0, zu - 3):zu + 1]
        ys, xs = np.nonzero(fuss)
        tx, ty = (xs + x) // T, (ys + y) // T
        for (a_, b_) in set(zip(ty.tolist(), tx.tolist())):
            if not (0 <= a_ < self.R and 0 <= b_ < self.C):
                return 'ausserhalb'
            if self.kl[a_, b_] not in boden:
                return 'Boden %s an %d,%d' % (self.kl[a_, b_], b_, a_)
            if self.sperr[a_, b_]:
                return 'Sperrfeld %d,%d' % (b_, a_)
        if not begleiter:
            y0, x0 = max(0, y), max(0, x)
            y1, x1 = min(self.pixel.shape[0], y + h_), min(self.pixel.shape[1], x + w_)
            if (self.pixel[y0:y1, x0:x1] & al[y0 - y:y1 - y, x0 - x:x1 - x]).any():
                return 'Ueberlappung'
        return None

    def sperren(self, x0, y0, x1, y1):
        self.sperr[max(0, y0):y1 + 1, max(0, x0):x1 + 1] = True


def main():
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    lvl = np.load(os.path.join(KARTE, 'pixelhoehe.npy'))
    P = Platz(lay, lvl)
    A = lay['achse']
    # ------------------------------------------------------------------ Sperrfelder
    for (x0, x1, y0, y1, art) in lay['zebra']:
        P.sperren(x0, y0, x1, y1)
        if art == 'v':                                        # Enden der Zebrastreifen auf dem Gehweg frei
            P.sperren(x0, y0 - 1, x1, y0 - 1); P.sperren(x0, y1 + 1, x1, y1 + 1)
        else:
            P.sperren(x0 - 1, y0, x0 - 1, y1); P.sperren(x1 + 1, y0, x1 + 1, y1)
    for tp in lay['teleporter']:
        P.sperren(tp['x'] - 1, tp['y'] - 1, tp['x'] + tp['b'], tp['y'] + tp['h'])
    tx0, tx1, ty = lay['treppe_terrasse']
    P.sperren(tx0 - 1, ty - 1, tx1 + 1, ty + 2)
    TUEREN = [(7, 18), (13, 18), (19, 18), (25, 18), (32, 18), (37, 18), (43, 18), (72, 18), (73, 18), (18, 40), (19, 40),
              (50, 68), (51, 68), (48, 80), (39, 80), (40, 80), (41, 80), (44, 80), (45, 80), (46, 80), (60, 80),
              (53, 80), (54, 80), (55, 80), (56, 80)] + [(x, 28) for x in range(A - 4, A + 4)]
    for (x, y) in TUEREN:
        P.sperren(x - 1, y, x + 1, y + 1)
    P.sperren(A - 4, 34, A + 3, 79)                           # Mittelweg frei
    P.sperren(37, 32, 40, 35)                                 # Parkplatz-Einfahrt
    # ------------------------------------------------------------------ Gebaeude
    for (x0, y0, x1, y1, art) in lay['gebaeude']:
        o = P.setzen('gebaeude/' + art, x0, y1, pruefen=False, n=x1 - x0 + 1, extra={'gebaeude': [x0, y0, x1, y1]})
        o['x'], o['y'] = x0 * T, y0 * T
        o['kein_schatten'] = True                             # Gebaeudeschatten zeichnet karte18_bauen selbst
        P.sperren(x0, y0, x1, y1)                             # Grundflaeche: hier steht nichts anderes
    # ------------------------------------------------------------------ Hochbahn: Pfeiler (Fuss auf dem Mittelstreifen) und Zug
    for px_ in lay['hochbahn']['pfeiler']:
        P.setzen('gebaeude/pfeiler', px_, 88, boden=set('mwsg'), n=2, pruefen=False, extra={'pfeiler': True})
    z = P.setzen('gebaeude/zug', lay['hochbahn']['zug'][0], 81, pruefen=False, n=21,
                 extra={'hochbahn': True, 'kein_schatten': True})
    z['x'] = lay['hochbahn']['zug'][0] * T
    # ------------------------------------------------------------------ Baeume (gross zuerst)
    GRUEN, KLEIN_B, GROSS_B = 'karte01/baeume/00', 'karte01/baeume/03', 'karte10/baeume/01'
    GINKGO = 'k18/baum/00' if os.path.exists(pfad('k18/baum/00')) else 'karte01/baeume/15'
    GINKGO2 = 'k18/baum/01' if os.path.exists(pfad('k18/baum/01')) else GINKGO
    RASEN = set('n')
    baeume = [  # Parks und Spielplatz (Rasen)
        (GRUEN, 47, 8, RASEN), (GINKGO, 50, 8, RASEN), (GROSS_B, 9, 62, RASEN), (GRUEN, 11, 66, RASEN),
        (GROSS_B, 21, 61, RASEN), (GRUEN, 24, 65, RASEN), (GRUEN, 7, 74, RASEN), (GINKGO2, 10, 76, RASEN),
        (GRUEN, 22, 74, RASEN), (KLEIN_B, 12, 92, RASEN), (GRUEN, 25, 92, RASEN), (GINKGO, 15, 76, set('qn')),
        # Mittelstreifen
        (GRUEN, 8, 48, set('m')), (GRUEN, 20, 48, set('m')), (GRUEN, 44, 48, set('m')), (GRUEN, 56, 48, set('m')),
        (GRUEN, 69, 88, set('m')), (GRUEN, 85, 88, set('m')), (GRUEN, 117, 88, set('m')),
        # Ginkgos an der Querstrasse
        (GINKGO, 29, 31, set('g')), (GINKGO2, 38, 39, set('g')),
        (GINKGO, 29, 58, set('g')), (GINKGO2, 37, 64, set('g')), (GINKGO, 29, 72, set('g')), (GINKGO2, 37, 76, set('g')),
    ]
    for (n, bx, r, bd) in baeume:
        P.setzen(n, bx, r, boden=bd, extra={'baum': True})
    # Platz: Pflanzkuebel (Hecke) mit Baum, Paare spiegelsymmetrisch zur Achse (A -/+ 18)
    KUEBEL = 'gebaeude/kuebel'
    def kuebel_baum(bx, r, baum):
        # Kuebel (4x2) zuerst, der Baum steht auf der Heckenflaeche im Kuebel (Fuss 6 px ueber der Steinfront) und
        # wird nach dem Kuebel gezeichnet ('sortier'), damit der Stamm aus der Hecke waechst
        k_ = P.setzen(KUEBEL, bx, r, boden=set('p'), n=4, extra={'kuebel': True})
        if k_:
            t = P.setzen(baum, bx, r, boden=set('p'), n=4, begleiter=True, pruefen=False, extra={'baum': True, 'im_kuebel': True})
            t['y'] -= 10
            t['sortier'] = k_['y'] + k_['fuss'] + 1
    for r in (40, 52, 64, 76):                                # Paare spiegelsymmetrisch zur Achse (A-20..A-17 / A+16..A+19)
        kuebel_baum(A - 20, r, GRUEN)
        kuebel_baum(A + 16, r, GRUEN)
    for (bx, r, bm) in ((67, 32, GRUEN), (74, 46, GINKGO), (66, 58, GRUEN), (73, 70, GINKGO2)):   # linke Platzseite
        kuebel_baum(bx, r, bm)
    # ------------------------------------------------------------------ Grosse Einzelobjekte
    P.setzen('karte02/ortho/09', 16, 82, boden=set('q'))     # Marktstand
    P.setzen('karte03/klein/43', 12, 80, boden=set('q'))     # Sandsaecke
    P.setzen('karte03/klein/43', 24, 80, boden=set('q'), spiegel=True)
    P.setzen('karte02/klein/61', 21, 83, boden=set('q'))     # Kisten am Stand
    P.setzen('karte10/spielplatz/01', 56, 10, boden=RASEN)   # Schaukel
    P.setzen('karte10/spielplatz/00', 60, 12, boden=RASEN)   # Rutsche
    P.setzen('karte10/spielplatz/02', 48, 16, boden=RASEN)   # Wippe
    for (n, bx, r) in (('karte02/abgeleitet/container_rot_0', 86, 99), ('karte02/abgeleitet/container_blau_0', 92, 99),
                       ('karte02/abgeleitet/container_blau_1', 20, 99)):
        P.setzen(n, bx, r, boden=set('k'))
    P.setzen('karte02/ortho/14', 42, 82, boden=set('g'))     # Lkw vor dem offenen Rolltor
    P.setzen('karte02/ortho/10', 50, 81, boden=set('g')) if os.path.exists(os.path.join(ROOT, 'assets/objekte/karte02/ortho/10.png')) else None
    if os.path.exists(pfad('k18/gross/03')):                 # Bushaltestellen
        P.setzen('k18/gross/03', 66, 19)
        P.setzen('k18/gross/03', 20, 41)
    if os.path.exists(pfad('k18/gross/02')):                 # Boot am Steg (schwebt im Wasser, wippt)
        P.setzen('k18/gross/02', 111, 103, boden=set('w'), anim='boot', extra={'kein_schatten': True})
    # ------------------------------------------------------------------ Laternen (fester Rhythmus, je Strassenseite)
    LAT = 'karte02/abgeleitet/laterne'
    for x in (10, 22, 34, 46, 58, 70, 82):                    # Nordseite obere Strasse (zwischen den Ladentueren)
        P.setzen(LAT, x, 19)
    for x in (4, 16, 28, 40, 52, 64, 76):                     # Suedseite obere Strasse (versetzt)
        P.setzen(LAT, x, 26)
    for x in range(6, 62, 12):
        P.setzen(LAT, x, 41)
        P.setzen(LAT, x + 6, 55)
    for y in range(30, 80, 10):
        P.setzen(LAT, 30, y)
        P.setzen(LAT, 38, y + 5)
    for x in range(14, 126, 12):
        P.setzen(LAT, x, 95)                                  # Uferpromenade
    for r in (40, 52, 64, 76):                                # Platz: Paare symmetrisch zur Achse
        for dx in (-8, 7, -16, 15):
            P.setzen(LAT, A + dx, r - 4)
    # Ampeln an den Kreuzungen der Querstrasse
    AMP = 'karte10/banner/13'
    for (bx, r) in ((30, 26), (37, 26), (30, 41), (37, 41), (30, 54), (38, 54)):
        P.setzen(AMP, bx, r)
    # ------------------------------------------------------------------ Stadtmoebel
    STR = lambda i: 'k18/strasse/%02d' % i
    for (n, bx, r, sp) in [(STR(0), 44, 19, False), (STR(1), 45, 19, False), (STR(2), 47, 19, False), (STR(3), 63, 26, False),
                           (STR(0), 25, 41, False), (STR(1), 26, 41, False), (STR(4), 22, 41, False), (STR(4), 23, 41, True),
                           (STR(6), 76, 41, False), (STR(6), 120, 49, False), (STR(5), 70, 19, False),
                           (STR(11), 24, 99, False), (STR(11), 56, 99, False), (STR(11), 116, 99, False),
                           (STR(11), 106, 106, False)]:
        if os.path.exists(pfad(n)):
            P.setzen(n, bx, r, spiegel=sp)
    # Fahnen an der Terrasse: drei je Seite, spiegelsymmetrisch (A-14/-12/-10 <-> A+13/+11/+9)
    if os.path.exists(pfad(STR(10))):
        for dx in (-14, -12, -10):
            P.setzen(STR(10), A + dx, 35, anim='fahne18')
            P.setzen(STR(10), A - dx - 1, 35, spiegel=True, anim='fahne18')
    BANK = 'karte10/klein/38'
    for r in (46, 58, 70):                                    # Baenke am Mittelweg (Paare)
        P.setzen(BANK, A - 7, r)
        P.setzen(BANK, A + 5, r)
    for (bx, r) in ((16, 60), (23, 67), (8, 69), (26, 86), (70, 52), (118, 62)):
        P.setzen(BANK, bx, r, boden=set('gpqn'))
    for (bx, r) in ((A - 12, 31), (A + 9, 31)):              # Absperrungen auf der Terrasse (Paar)
        P.setzen('karte10/banner/04', bx, r, boden=set('t'))
    P.setzen('karte10/banner/04', 27, 85, boden=set('q'))
    for (bx, r) in ((60, 41), (61, 41)):
        P.setzen('karte13/klein/12', bx, r)
    P.setzen('karte13/klein/12', 59, 43, boden=set('s'))
    P.setzen('karte10/banner/06', 56, 17, boden=set('g'))     # Uhr am Spielplatz
    P.setzen('karte10/banner/06', 16, 55)
    for (bx, r) in ((35, 19), (57, 26), (28, 55), (60, 70), (13, 41), (64, 95), (100, 95), (77, 26)):
        P.setzen('karte02/klein/16', bx, r)                   # Muelleimer
    for (bx, r) in ((27, 26), (52, 41), (40, 70)):
        P.setzen('karte02/klein/17', bx, r)                   # Hydranten
    P.setzen('karte02/klein/31', 51, 70)                      # Container (Muell) neben der Lagerhalle
    P.setzen('karte10/klein2/02', 63, 44, boden=set('gp'))    # Durchfahrt verboten (Strassenende am Platz)
    for x in range(64, 126, 4):                               # Poller am Rand des Platzes (Rhythmus)
        if not (A - 4 <= x <= A + 3):
            P.setzen('gebaeude/poller', x, 79, boden=set('pc'))
    # ------------------------------------------------------------------ Autos (Linksverkehr)
    AUTO = lambda i: 'k18/autos/%02d' % i
    fahr = set('s')
    for (i, bx, r, ost) in [(0, 5, 21, True), (2, 49, 21, True), (1, 56, 24, False), (3, 4, 44, True), (4, 55, 44, True),
                            (5, 8, 52, False), (1, 47, 52, False), (0, 69, 85, True), (4, 106, 85, True),
                            (5, 76, 92, False), (1, 116, 92, False), (0, 41, 92, False)]:
        if os.path.exists(pfad(AUTO(i))):
            P.setzen(AUTO(i), bx, r, spiegel=ost, boden=fahr, extra={'auto': True})
    if os.path.exists(pfad('k18/gross/00')):                 # Bus an der Haltestelle (ostwaerts)
        P.setzen('k18/gross/00', 64, 22, spiegel=True, boden=fahr, extra={'auto': True})
    for (i, cx, r) in ((6, 35.5, 34), (7, 33.5, 66)):         # Querstrasse von oben (Sued auf Ostspur, Nord auf Westspur)
        if os.path.exists(pfad(AUTO(i))):
            P.setzen(AUTO(i), 0, r, boden=fahr, cx=cx * T, extra={'auto': True})
    for (i, bx, r) in ((6, 42, 32), (7, 48, 32), (6, 51, 32), (7, 45, 37), (6, 57, 37)):   # Parkplatz (unregelmaessig)
        if os.path.exists(pfad(AUTO(i))):
            P.setzen(AUTO(i), bx, r, boden=fahr, n=3, extra={'auto': True})
    json.dump(P.objekte, open(os.path.join(OBJ, 'platzierung.json'), 'w'), indent=0)
    print('Karte 18: %d Objekte, %d nicht gesetzt' % (len(P.objekte), len(P.fehl)))
    for f in P.fehl:
        print('  -', f)


if __name__ == '__main__':
    main()
