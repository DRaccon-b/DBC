"""Objekte fuer Karte 18 (The Fog-Bound City) - am 16x16-Raster nach den Regeln aus CLAUDE.md (Runde 2 nach Review).

  python3 tools/karte18_bauen.py && python3 tools/karte18_objekte.py && python3 tools/karte18_bauen.py

Reihenfolge (grosse Objekte zuerst): Gebaeude -> Hochbahn (Pfeiler, Zug) -> Baeume (mit Begleitern) -> grosse
Einzelobjekte -> Laternen, Ampeln -> Stadtmoebel -> Autos. Jedes Objekt steht mittig in seinem kleinsten Kachelblock,
der Fuss buendig auf der unteren Kachelkante (Regel 1b); Paare am Platz werden pixelgenau an der Achse x = 102
(1632 px) gespiegelt (Achsen-Regel geht vor 1b). Geprueft wird: 2 px Abstand zu anderen Objekten (ausser gewollten
Begleitern), Fuss auf passendem Boden, nicht vor Tueren, auf Zebrastreifen, Treppe oder Teleportern.
Linksverkehr: ostwaerts Nordspur, westwaerts Suedspur; jedes Auto steht ganz in seiner Spur.
Abend im Nebel: wiederverwendete Sprites mit grellen Farben werden gedaempft (Spielplatz, Uhr, Marktzelt, weisse
Autos, Gras/Blumen); die Laterne verliert ihr Grasbueschel (versiegelter Boden).
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
GEHEN = set('gpqctkhvb')                                 # Gehflaechen fuer Stadtmoebel
RASEN = set('n')
LEUCHTEN = {'karte02/abgeleitet/laterne': 'laterne18', 'gebaeude/doppellaterne': 'laterne18',
            'karte10/banner/13': 'ampel18', 'k18/strasse/17': 'ampel18',
            'k18/strasse/00': 'automat', 'k18/strasse/01': 'automat', 'k18/strasse/40': 'automat',
            'k18/strasse/06': 'automat'}
TONUNG = {'karte10/spielplatz/00': 'gedaempft', 'karte10/spielplatz/01': 'gedaempft', 'karte10/spielplatz/02': 'gedaempft',
          'karte10/banner/06': 'metall', 'k18/autos/00': 'weiss', 'k18/autos/06': 'weiss', 'k18/autos/12': 'weiss',
          'karte02/ortho/09': 'zelt_blau', 'karte01/deko/06': 'abend', 'karte01/deko/00': 'abend',
          'karte01/deko/02': 'abend', 'karte01/deko/25': 'abend', 'karte01/deko/44': 'abend', 'karte01/deko/50': 'abend',
          'karte02/abgeleitet/laterne': 'ohne_gras', 'karte10/banner/13': 'nur_gruen'}


def pfad(name):
    if name.startswith('k18/'):
        return os.path.join(OBJ, name[4:] + '.png')
    if name.startswith('gebaeude/'):
        return os.path.join(OBJ, name + '.png')
    ziel = os.path.join(OBJ, 'fremd', name.replace('/', '-') + '.png')
    if not os.path.exists(ziel):
        os.makedirs(os.path.dirname(ziel), exist_ok=True)
        shutil.copy(os.path.join(ROOT, 'assets', 'objekte', name + '.png'), ziel)
    return ziel


def hsv_tonen(a, sat=1.0, hell=1.0, hue=0.0):
    rgb = a[..., :3].astype(np.float32) / 255
    mx, mn = rgb.max(axis=2), rgb.min(axis=2)
    v = mx
    s = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    d = np.maximum(mx - mn, 1e-6)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    h = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) / 6
    h = (h + hue) % 1.0
    s = np.clip(s * sat, 0, 1)
    v = np.clip(v * hell, 0, 1)
    i = np.floor(h * 6).astype(int) % 6
    f = h * 6 - np.floor(h * 6)
    p, q, t = v * (1 - s), v * (1 - s * f), v * (1 - s * (1 - f))
    out = np.stack([np.choose(i, [v, q, p, p, t, v]), np.choose(i, [t, v, v, q, p, p]),
                    np.choose(i, [p, p, t, v, v, q])], -1)
    a[..., :3] = np.clip(out * 255, 0, 255).astype(np.uint8)
    return a


def tonen(sp, art):
    """Farbanpassung wiederverwendeter Sprites an die Abendstimmung im Nebel."""
    a = np.array(sp).copy()
    ai = a.astype(int)
    sicht = a[..., 3] > 0
    if art == 'gedaempft':                                # Spielgeraete: Saettigung x0.6, Helligkeit x0.85, Richtung Violett
        a = hsv_tonen(a, 0.6, 0.85, -0.025)
    elif art == 'abend':                                  # Gras, Blumen, Laub: dunkler, kuehler
        a = hsv_tonen(a, 0.75, 0.62, 0.02)
    elif art == 'metall':                                 # Uhr: Gold -> dunkles Metall, Zifferblatt gedaempft
        lum = (0.3 * ai[..., 0] + 0.59 * ai[..., 1] + 0.11 * ai[..., 2])
        rampe = np.array([[42, 44, 54], [58, 62, 74], [90, 94, 108], [138, 142, 154], [184, 180, 196]])
        idx = np.clip((lum / 256 * len(rampe)).astype(int), 0, len(rampe) - 1)
        a[sicht, :3] = rampe[idx[sicht]]
    elif art == 'weiss':                                  # weisse Karosserie nicht heller als die Lichtquellen
        mx, mn = ai[..., :3].max(axis=2), ai[..., :3].min(axis=2)
        m = sicht & (mx > 204) & (mx - mn < 40)
        lum = mx[m]
        a[m, :3] = np.where((lum > 235)[:, None], [200, 200, 212],
                            np.where((lum > 215)[:, None], [178, 178, 192], [150, 150, 168]))
    elif art == 'zelt_blau':                              # Marktstand -> gedaempftes dunkelblaues Zeltdach
        r_, g_, b_ = ai[..., 0], ai[..., 1], ai[..., 2]
        orange = sicht & (r_ > 150) & (r_ > b_ + 60)
        weiss_ = sicht & (r_ > 200) & (g_ > 200) & (b_ > 190)
        a[orange, :3] = np.where((r_[orange] > 210)[:, None], [58, 90, 138], [42, 68, 112])
        a[weiss_, :3] = [184, 180, 200]
        holz = sicht & ~orange & ~weiss_ & (r_ > g_) & (g_ > b_)
        a[holz, :3] = (ai[holz, :3] * 0.85).astype(np.uint8)
    elif art == 'ohne_gras':                              # Laterne: gruenes Bueschel am Fuss entfernen
        h = a.shape[0]
        gr = sicht & (ai[..., 1] > ai[..., 0] + 30) & (ai[..., 1] > ai[..., 2] + 10)
        gr[: h - 5] = False
        xs = np.nonzero(sicht[h - 6])[0] if sicht[h - 6].any() else np.array([a.shape[1] // 2])
        innen = np.zeros_like(gr)
        innen[:, max(0, xs.min() - 1):xs.max() + 2] = True
        a[gr & innen, :3] = [74, 78, 90]
        a[gr & ~innen] = 0
    elif art == 'nur_gruen':                              # Ampel: Rot und Gelb aus, nur Gruen leuchtet
        r_, g_, b_ = ai[..., 0], ai[..., 1], ai[..., 2]
        rot = sicht & (r_ > 150) & (g_ < 110)
        gelb = sicht & (r_ > 170) & (g_ > 140) & (b_ < 110)
        a[rot | gelb, :3] = (ai[rot | gelb, :3] * 0.35).astype(np.uint8)
    return Image.fromarray(a)


class Platz:
    def __init__(self, lay, lvl):
        self.lay, self.lvl = lay, lvl
        self.kl = np.array([list(r) for r in lay['klassen']])
        self.R, self.C = self.kl.shape
        self.pixel = np.zeros(lvl.shape, bool)
        self.sperr = np.zeros(self.kl.shape, bool)
        self.objekte, self.cache, self.fehl = [], {}, []
        self.A = lay['achse']
        os.makedirs(os.path.join(OBJ, 'sauber'), exist_ok=True)

    def sprite(self, name, spiegel=False):
        key = (name, spiegel)
        if key not in self.cache:
            sp = Image.open(pfad(name)).convert('RGBA')
            if not name.startswith('gebaeude/'):
                sp = saeubern(sp)
            if name in TONUNG:
                sp = tonen(sp, TONUNG[name])
            if spiegel:
                sp = sp.transpose(Image.FLIP_LEFT_RIGHT)
            datei = 'sauber/%s%s.png' % (name.replace('/', '-'), '_m' if spiegel else '')
            sp.save(os.path.join(OBJ, datei))
            al = np.array(sp.getchannel('A')) >= 128
            zu = int(np.nonzero(al.any(axis=1))[0].max())
            xs = np.nonzero(al.any(axis=0))[0]
            self.cache[key] = (datei, al, zu, xs.min(), xs.max())
        return self.cache[key]

    def eintragen(self, al, x, y):
        d = np.array(Image.fromarray((al * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(5))) > 0
        h_, w_ = al.shape
        y0, x0 = max(0, y), max(0, x)
        y1, x1 = min(self.pixel.shape[0], y + h_), min(self.pixel.shape[1], x + w_)
        if y1 > y0 and x1 > x0:
            self.pixel[y0:y1, x0:x1] |= d[y0 - y:y1 - y, x0 - x:x1 - x]

    def setzen(self, name, bx, reihe, spiegel=False, anim=None, boden=GEHEN, n=None, begleiter=False, extra=None,
               pruefen=True, cx=None, x=None):
        if name.startswith('k18/') and not os.path.exists(pfad(name)):
            self.fehl.append((name, bx, reihe, 'Sprite fehlt'))
            return None
        datei, al, zu, xa, xb = self.sprite(name, spiegel)
        breite = xb - xa + 1
        n = n or max(1, math.ceil(breite / T))
        mitte = cx if cx is not None else bx * T + n * T / 2.0
        if x is None:
            x = int(round(mitte - (xa + xb + 1) / 2.0))
        y = (reihe + 1) * T - 1 - zu
        if pruefen:
            grund = self._pruefen(al, x, y, zu, boden, begleiter)
            if grund:
                self.fehl.append((name, bx, reihe, grund))
                return None
        o = {'datei': datei, 'basis': name, 'x': x, 'y': y, 'fuss': zu,
             'kachel': [int((x + (xa + xb + 1) / 2) // T), reihe], 'ebene': 1}
        if anim or LEUCHTEN.get(name):
            o['anim'] = anim or LEUCHTEN[name]
        if extra:
            o.update(extra)
        # Bodenwall nur fuer Pflanzen auf Rasen/Sand (sonst wuerde Fahrbahn/Pflaster an den Fuss kopiert)
        if not (o.get('baum') or o.get('pflanze')) or not (boden <= set('nd')):
            o['an_wand'] = True
        self.objekte.append(o)
        if not o.get('gebaeude') and not begleiter:
            self.eintragen(al, x, y)
        return o

    def paar(self, name, bx, reihe, **kw):
        """Links normal setzen, rechts pixelgenau an der Achse spiegeln: x_r = 2*A*T - x_l - Breite.
        Passt der Partner nicht, wird auch das linke Objekt wieder entfernt (nie halbe Paare)."""
        pixel_vorher = self.pixel.copy()
        links = self.setzen(name, bx, reihe, **kw)
        if not links:
            return None, None
        sp = kw.get('spiegel', False)
        datei, al, zu, xa, xb = self.sprite(name, not sp)
        kw2 = dict(kw)
        kw2['spiegel'] = not sp
        rechts = self.setzen(name, 2 * self.A - bx - 1, reihe, x=2 * self.A * T - links['x'] - al.shape[1], **kw2)
        if not rechts:
            self.objekte.remove(links)
            self.pixel = pixel_vorher
            self.fehl.append((name, bx, reihe, 'Paar ohne Partner entfernt'))
        return links, rechts

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
    lichter = json.load(open(os.path.join(OBJ, 'gebaeude', 'lichter.json')))
    P = Platz(lay, lvl)
    A = lay['achse']
    # ------------------------------------------------------------------ Sperrfelder
    for (x0, x1, y0, y1, art) in lay['zebra']:
        P.sperren(x0, y0, x1, y1)
        if art == 'v':
            P.sperren(x0, y0 - 1, x1, y0 - 1)
            P.sperren(x0, y1 + 1, x1, y1 + 1)
        else:
            P.sperren(x0 - 1, y0, x0 - 1, y1)
            P.sperren(x1 + 1, y0, x1 + 1, y1)
    for tp in lay['teleporter']:
        P.sperren(tp['x'] - 1, tp['y'] - 1, tp['x'] + tp['b'], tp['y'] + tp['h'])
    tx0, tx1, ty = lay['treppe_terrasse']
    P.sperren(tx0 - 1, ty - 1, tx1 + 1, ty + 3)
    laeden_tueren = [(5 + 4 * i + (2 if i % 2 == 0 else 1), 18) for i in range(10) if i not in (2, 6)]
    TUEREN = laeden_tueren + [(72, 18), (73, 18), (18, 40), (19, 40), (50, 68), (51, 68), (48, 80), (60, 80),
                              (39, 80), (40, 80), (53, 80), (54, 80), (55, 80), (56, 80)] + \
        [(x, 28) for x in range(A - 4, A + 4)]
    for (x, y) in TUEREN:
        P.sperren(x - 1, y, x + 1, y + 1)
    P.sperren(A - 4, 34, A + 3, 79)                           # Mittelweg frei
    P.sperren(37, 32, 40, 35)                                 # Parkplatz-Einfahrt
    # ------------------------------------------------------------------ Gebaeude
    for (x0, y0, x1, y1, art) in lay['gebaeude']:
        o = P.setzen('gebaeude/' + art, x0, y1, pruefen=False, n=x1 - x0 + 1, extra={'gebaeude': [x0, y0, x1, y1]})
        o['x'], o['y'] = x0 * T, y0 * T
        o['kein_schatten'] = True
        rects = lichter.get(art) or lichter.get('lager_' + art.split('_')[-1])
        if rects:
            o['licht_rects'] = rects
            o['anim'] = 'rechtecke'
        P.sperren(x0, y0, x1, y1)
    # ------------------------------------------------------------------ Hochbahn: Pfeiler (Mittelstreifen / Kanal) und Zug
    for px_ in lay['hochbahn']['pfeiler']:
        im_wasser = P.kl[88, px_] == 'w'
        P.setzen('gebaeude/pfeiler_wasser' if im_wasser else 'gebaeude/pfeiler', px_, 88, n=2, pruefen=False,
                 extra={'pfeiler': True, 'im_wasser': bool(im_wasser), 'kein_schatten': bool(im_wasser)})
    z = P.setzen('gebaeude/zug', lay['hochbahn']['zug'][0], 81, pruefen=False, n=21,
                 extra={'hochbahn': True, 'kein_schatten': True})
    z['x'] = lay['hochbahn']['zug'][0] * T
    # ------------------------------------------------------------------ Baeume (gross zuerst) mit Begleitern (Regel 5)
    GRUEN, KLEIN_B, GROSS_B = 'karte01/baeume/00', 'karte01/baeume/03', 'karte10/baeume/01'
    GINKGO, GINKGO2, GINKGO_K = 'gebaeude/ginkgo', 'gebaeude/ginkgo_gross', 'gebaeude/ginkgo_klein'
    BUESCHEL, BLUMEN, BUSCH, LAUB = 'karte01/deko/06', 'karte01/deko/00', 'karte01/deko/25', 'karte01/deko/50'

    def baum(n_, bx, r, bd, cx=None, begleit=True, nn=None):
        t = P.setzen(n_, bx, r, boden=bd, cx=cx, n=nn, extra={'baum': True})
        if t and begleit:                                     # Bueschel/Laub an beiden Sockelecken (Einbettung)
            datei, al, zu, xa, xb = P.sprite(n_)
            fz = np.nonzero(al[zu - 1])[0]
            mitte = t['x'] + (fz.mean() if len(fz) else (xa + xb) / 2)
            zweit = LAUB if 'ginkgo' in n_ else BLUMEN
            for sx, nm in ((mitte - 12, BUESCHEL), (mitte + 12, zweit)):
                P.setzen(nm, 0, r, cx=sx, boden=bd | set('gq'), begleiter=True,
                         extra={'pflanze': True, 'begleiter': True, 'kein_schatten': True})
        return t
    baum(GRUEN, 46, 7, set('gn'), begleit=False)              # Spielplatz: NW-Ecke (wie Vorlage) ...
    baum(GINKGO, 59, 6, RASEN)                                # ... und Ginkgo NO-Ecke
    for (n_, bx, r) in ((GROSS_B, 9, 62), (GRUEN, 11, 66), (GROSS_B, 21, 61), (GRUEN, 24, 65), (GRUEN, 6, 74),
                        (GINKGO2, 9, 76), (GRUEN, 21, 74), (KLEIN_B, 25, 75), (KLEIN_B, 12, 92),
                        (GRUEN, 26, 91), (GINKGO_K, 24, 91), (GRUEN, 4, 80)):
        baum(n_, bx, r, RASEN)
    for (bx, r) in ((19, 62), (8, 72), (14, 93)):             # Buesche vor einem Sockel (Regel 5a)
        P.setzen(BUSCH, bx, r, boden=RASEN, begleiter=True, extra={'pflanze': True})
    for (bx, r) in ((11, 48), (23, 48), (47, 48), (59, 48)):  # Mittelstreifen: Baeume am Ostende der Hecken
        baum(GRUEN, bx, r, set('m'), begleit=False)
    for cx in (71 * T, 87 * T, 119 * T):                      # Uferstrasse: mittig zwischen den Pfeilern
        baum(GRUEN, 0, 88, set('m'), cx=cx, begleit=False)
    for (n_, bx, r) in ((GINKGO, 29, 31), (GINKGO, 29, 58), (GINKGO2, 38, 64), (GINKGO, 29, 72)):
        baum(n_, bx, r, set('g'))                             # Strassenbaeume an der Querstrasse
    for r in (39, 51, 63, 75):                                # Platz: Baum mittig im Heckenbeet, Paare gespiegelt
        P.paar(GRUEN, 0, r, boden=set('e'), cx=83 * T, extra={'baum': True})
    for (n_, cx, r) in ((GINKGO, 69 * T, 29), (GRUEN, 71 * T, 45), (GINKGO2, 69 * T, 68)):
        P.setzen(n_, 0, r, boden=set('e'), cx=cx, extra={'baum': True})
    # ------------------------------------------------------------------ Grosse Einzelobjekte
    P.setzen('karte02/ortho/09', 18, 82, boden=set('q'))     # Zelt (Marktstand, dunkelblau getoent)
    P.setzen('karte03/klein/43', 12, 80, boden=set('q'))     # Sandsaecke, symmetrisch zum Zelt
    P.setzen('karte03/klein/43', 23, 80, boden=set('q'), spiegel=True)
    P.setzen('k18/strasse/32', 20, 84, boden=set('q'))       # Kisten (frontal)
    P.setzen('karte10/spielplatz/00', 50, 9, boden=RASEN)    # Rutsche auf dem linken Rasen
    P.setzen('karte10/spielplatz/01', 57, 10, boden=RASEN)   # Schaukel rechts
    P.setzen('karte10/spielplatz/02', 47, 15, boden=set('g'))   # Wippe auf dem Pflaster
    for (n_, bx, r) in (('karte02/abgeleitet/container_rot_0', 89, 97), ('karte02/abgeleitet/container_blau_0', 65, 97),
                        ('karte02/abgeleitet/container_blau_1', 18, 97)):
        P.setzen(n_, bx, r, boden=set('b'))
    P.setzen('karte02/ortho/14', 42, 81, boden=set('s'))     # Lkw auf der Zufahrt vor dem offenen Rolltor
    P.setzen('k18/frontal/02', 66, 19)                        # Bushaltestellen (frontal)
    P.setzen('k18/frontal/03', 21, 41)
    P.setzen('k18/frontal/00', 111, 103, boden=set('w'), anim='boot', extra={'kein_schatten': True})
    P.setzen('gebaeude/koban', 26, 85, boden=set('q'), anim='rechtecke', extra={'licht_rects': lichter.get('koban', [])})
    # ------------------------------------------------------------------ Laternen
    LAT, DLAT = 'karte02/abgeleitet/laterne', 'gebaeude/doppellaterne'
    for x in (14, 30, 46, 58, 70, 82):                        # Nordseite obere Strasse (zwischen den Ladentueren)
        P.setzen(LAT, x, 19)
    for x in (4, 16, 28, 40, 52, 64, 76):                     # Suedseite obere Strasse
        P.setzen(LAT, x, 26)
    for x in (6, 16, 42, 54):
        P.setzen(LAT, x, 41)
    for x in (12, 24, 40, 48, 60):
        P.setzen(LAT, x, 54)
    for cx in (8, 20, 44, 56):                                # zweiarmige Leuchten auf dem Mittelstreifen
        P.setzen(DLAT, 0, 48, boden=set('m'), cx=cx * T + 8)
    for (bx, r) in ((30, 37), (38, 30), (38, 60), (38, 69), (31, 63), (17, 73), (13, 88), (28, 89), (61, 13)):
        P.setzen(LAT, bx, r, boden=GEHEN | RASEN)
    for x in range(14, 125, 12):
        P.setzen(LAT, x, 95)                                  # Uferpromenade
    P.setzen(LAT, 0, 104, boden=set('h'), cx=107 * T)          # Laterne auf dem Steg (Stegmitte)
    for r in (40, 52, 64, 76):                                # Platz: Paare innen am Mittelweg ...
        P.paar(LAT, 90, r)
    for r in (34, 46, 58, 70):                                # ... und aussen zwischen den Beeten
        P.paar(LAT, 80, r)
    P.paar(LAT, 92, 30, boden=set('t'))                       # Terrasse
    for (bx, r) in ((68, 52), (68, 62), (76, 76), (66, 33), (68, 41)):
        P.setzen(LAT, bx, r, boden=set('p'))
    AMP = 'karte10/banner/13'                                 # Ampeln: alle Gruen fuer die Ost-West-Strassen
    for (bx, r) in ((30, 26), (37, 26), (30, 41), (37, 41), (30, 54), (37, 54)):
        P.setzen(AMP, bx, r)
    P.setzen('k18/strasse/17', 26, 26)
    # ------------------------------------------------------------------ Stadtmoebel
    STR = lambda i: 'k18/strasse/%02d' % i
    for (n_, bx, r, sp) in [(STR(1), 47, 19, False), (STR(2), 49, 19, False), (STR(3), 62, 26, False),
                            (STR(0), 25, 41, False), (STR(4), 9, 41, False), (STR(4), 11, 41, True),
                            (STR(6), 76, 41, False), (STR(6), 120, 47, False), (STR(5), 65, 19, False),
                            (STR(40), 61, 26, False)]:
        P.setzen(n_, bx, r, spiegel=sp)
    for dx in (14, 12, 10):                                   # Fahnen vor der Terrasse (Paare gespiegelt)
        P.paar(STR(10), A - dx, 35, anim='fahne18')
    for bx in (20, 44):
        P.setzen(STR(50), bx, 19, anim='fahne18')             # Nobori vor Ramen-Laden und Izakaya (nur Tuch weht)
    for r in (44, 56, 68):                                    # moderne Baenke am Mittelweg (Paare)
        P.paar(STR(14), 95, r)
    for (bx, r) in ((16, 60), (23, 67), (8, 69), (14, 84), (22, 88), (70, 52), (113, 62)):
        P.setzen('karte10/klein/38', bx, r, boden=set('gpqn'))
    P.paar(STR(7), 88, 29, boden=set('t'))                    # rot-weisse Absperrungen auf der Terrasse
    P.setzen(STR(7), 26, 80, boden=set('q'))
    P.setzen('karte13/klein/12', 60, 41)
    P.setzen('karte13/klein/12', 59, 43, boden=set('s'))
    P.setzen('karte10/banner/06', 56, 17, boden=set('g'))     # Uhr (dunkles Metall)
    P.setzen('karte10/banner/06', 16, 55)
    for (bx, r) in ((37, 19), (57, 26), (28, 55), (60, 69), (13, 41), (64, 95), (106, 95), (77, 26)):
        P.setzen('karte02/klein/16', bx, r)                   # Muelleimer
    for (bx, r) in ((24, 26), (49, 41), (40, 69)):
        P.setzen('karte02/klein/17', bx, r)                   # Hydranten
    P.setzen('karte02/klein/31', 54, 69)                      # Muellcontainer am Vorplatz
    P.setzen('karte10/klein2/02', 63, 44, boden=set('gp'))    # Durchfahrt verboten (Strassenende am Platz)
    for r in range(20, 25):                                   # Poller am Ende der oberen Strasse
        P.setzen('gebaeude/poller', 82, r, boden=set('g'))
    for x in (64, 68, 72, 76):                                # Poller am Platzrand (Reihe 78): West einzeln ...
        P.setzen('gebaeude/poller', x, 78, boden=set('pc'))
    for x in (80, 84, 88, 92, 96):                            # ... achsnah als gespiegelte Paare
        P.paar('gebaeude/poller', x, 78, boden=set('pc'))
    for x in range(14, 124, 16):                              # Festmacher an der Kaikante
        P.setzen(STR(21), x, 99, boden=set('k'))
    for (bx, r) in ((104, 101), (108, 101), (104, 105), (108, 105)):
        P.setzen(STR(21), bx, r, boden=set('h'))
    for bx in (30, 56, 116):
        P.setzen(STR(11), bx, 97, boden=set('b'))             # Rettungsringe an der Promenade
    P.setzen(STR(11), 105, 103, boden=set('h'))
    # ------------------------------------------------------------------ Autos (Linksverkehr, ganz in der Spur)
    AUTO = lambda i: 'k18/autos/%02d' % i
    fahr = set('s')
    for (i, bx, r, ost) in [(0, 7, 21, True), (2, 49, 21, True), (1, 56, 24, False), (3, 6, 43, True), (4, 55, 43, True),
                            (5, 8, 53, False), (1, 44, 50, False), (0, 65, 86, True), (4, 106, 86, True),
                            (5, 76, 93, False), (1, 116, 90, False), (0, 41, 93, False)]:
        P.setzen(AUTO(i), bx, r, spiegel=ost, boden=fahr, extra={'auto': True})
    P.setzen(AUTO(12), 0, 21, spiegel=True, boden=fahr, cx=1080, begleiter=True, extra={'auto': True})   # Bus am Haeuschen
    for (i, cx, r) in ((6, 35.75, 34), (7, 33.25, 66)):
        P.setzen(AUTO(i), 0, r, boden=fahr, cx=cx * T, extra={'auto': True})
    for (i, bx, r) in ((6, 42, 32), (7, 48, 32), (6, 51, 32), (7, 45, 37), (6, 57, 37)):
        P.setzen(AUTO(i), bx, r, boden=fahr, n=3, extra={'auto': True})
    json.dump(P.objekte, open(os.path.join(OBJ, 'platzierung.json'), 'w'), indent=0)
    print('Karte 18: %d Objekte, %d nicht gesetzt' % (len(P.objekte), len(P.fehl)))
    for f in P.fehl:
        print('  -', f)


if __name__ == '__main__':
    main()
