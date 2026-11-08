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
            'k18/strasse/01': 'automat', 'k18/strasse/40': 'automat'}
PAD = {'k18/frontal/00': 1}                              # Boot: 1 px Luft oben/unten fuer das Schaukeln
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
            if name in PAD:
                p_ = PAD[name]
                neu = Image.new('RGBA', (sp.width, sp.height + 2 * p_))
                neu.paste(sp, (0, p_))
                sp = neu
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
               pruefen=True, cx=None, x=None, dy=0):
        if name.startswith('k18/') and not os.path.exists(pfad(name)):
            self.fehl.append((name, bx, reihe, 'Sprite fehlt'))
            return None
        datei, al, zu, xa, xb = self.sprite(name, spiegel)
        breite = xb - xa + 1
        n = n or max(1, math.ceil(breite / T))
        mitte = cx if cx is not None else bx * T + n * T / 2.0
        if x is None:
            x = int(round(mitte - (xa + xb + 1) / 2.0))
        y = (reihe + 1) * T - 1 - zu + dy
        if pruefen:
            grund = self._pruefen(al, x, y, zu, boden, begleiter)
            if grund:
                self.fehl.append((name, bx, reihe, grund))
                return None
        o = {'datei': datei, 'basis': name, 'x': x, 'y': y, 'fuss': zu,
             'kachel': [int((x + (xa + xb + 1) / 2) // T), reihe], 'ebene': 1, '_key': (name, spiegel)}
        if anim or LEUCHTEN.get(name):
            o['anim'] = anim or LEUCHTEN[name]
        if extra:
            o.update(extra)
        # Bodenwall nur fuer Pflanzen auf Rasen/Sand (sonst wuerde Fahrbahn/Pflaster an den Fuss kopiert)
        fx_ = min(self.C - 1, max(0, int((x + (xa + xb + 1) / 2) // T)))
        unten = self.kl[min(self.R - 1, reihe + 1), fx_]
        if not (o.get('baum') or o.get('pflanze')) or not (boden <= set('nd')) or unten not in 'nd':
            o['an_wand'] = True                               # kein Bodenwall (sonst wird Pflaster an den Stamm kopiert)
        self.objekte.append(o)
        if not o.get('gebaeude') and not begleiter:
            self.eintragen(al, x, y)
        return o

    def paar(self, name, bx, reihe, sprite_spiegeln=False, anker=None, **kw):
        """Links normal setzen, rechts pixelgenau an der Achse spiegeln. Gespiegeltes Sprite: x_r = 2*A*T - x_l - Breite.
        Ungespiegeltes Sprite: der Ankerpunkt (Standard Mitte der sichtbaren Pixel, bei Bannern die Mastmitte) wird
        gespiegelt, x_r = 2*A*T - x_l - 2*anker. Passt der Partner nicht, wird auch das linke Objekt wieder entfernt."""
        pixel_vorher = self.pixel.copy()
        links = self.setzen(name, bx, reihe, **kw)
        if not links:
            return None, None
        sp = kw.get('spiegel', False)
        sp2 = (not sp) if sprite_spiegeln else sp                 # Licht bleibt oben links: Sprite nur wenn gewollt spiegeln
        datei, al, zu, xa, xb = self.sprite(name, sp2)
        kw2 = dict(kw)
        kw2['spiegel'] = sp2
        if sp2 != sp:
            xr = 2 * self.A * T - links['x'] - al.shape[1]
        else:
            a_ = anker if anker is not None else (xa + xb + 1) / 2.0
            xr = int(round(2 * self.A * T - links['x'] - 2 * a_))
        rechts = self.setzen(name, 2 * self.A - bx - 1, reihe, x=xr, **kw2)
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


def begleiter_nachpruefen(P):
    """Begleiter (Bueschel, Blumen, Laub) duerfen nur ihren eigenen Baum ueberdecken. Zu allen anderen Objekten (auch
    fremden Baumkronen und anderen Begleitern) halten sie 2 px Abstand; sonst werden sie um bis zu 10 px seitlich
    verschoben (Boden wird dabei neu geprueft) oder entfernt."""
    Hh, W = P.pixel.shape
    zahl = np.zeros((Hh, W), np.int16)

    def maske(o, dil=True):
        al = P.cache[o['_key']][1]
        if dil:
            al = np.array(Image.fromarray((al * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(5))) > 0
        return al

    def addieren(o, w_):
        m = maske(o)
        h_, w2 = m.shape
        y0, x0 = max(0, o['y']), max(0, o['x'])
        y1, x1 = min(Hh, o['y'] + h_), min(W, o['x'] + w2)
        zahl[y0:y1, x0:x1] += w_ * m[y0 - o['y']:y1 - o['y'], x0 - o['x']:x1 - o['x']]

    for o in P.objekte:
        if not (o.get('gebaeude') or o.get('hochbahn') or o.get('begleiter')):
            addieren(o, 1)
    for c in [o for o in P.objekte if o.get('begleiter')]:
        t = c.get('_eltern')
        if t is not None:
            addieren(t, -1)
            ka = P.cache[t['_key']][1].copy()                      # Sockel = unterste Kachelreihe: dort darf der
            rgb = np.array(Image.open(os.path.join(OBJ, t['datei'])).convert('RGB')).astype(int)   # Begleiter Stamm
            r_, g_, b_ = rgb[..., 0], rgb[..., 1], rgb[..., 2]                                       # und Wurzeln
            laub = ((g_ > r_ + 10) & (g_ > b_ + 10)) | ((r_ > 150) & (g_ > 110) & (b_ < 100))       # decken, nie Laub
            unten = np.zeros_like(ka); unten[max(0, t['fuss'] - 15):] = True
            ka &= ~(unten & ~laub)
            hk, wk = ka.shape
            y0k, x0k = max(0, t['y']), max(0, t['x'])
            y1k, x1k = min(Hh, t['y'] + hk), min(W, t['x'] + wk)
            krone = np.zeros((Hh, W), bool)
            krone[y0k:y1k, x0k:x1k] = ka[y0k - t['y']:y1k - t['y'], x0k - t['x']:x1k - t['x']]
            zahl[krone] += 100
        al = maske(c, False)
        datei, _, zu, xa, xb = P.cache[c['_key']]
        h_, w2 = al.shape

        def frei(x):
            y0, x0 = max(0, c['y']), max(0, x)
            y1, x1 = min(Hh, c['y'] + h_), min(W, x + w2)
            return not (zahl[y0:y1, x0:x1] > 0)[al[y0 - c['y']:y1 - c['y'], x0 - x:x1 - x]].any()

        ziel = None
        breite_ = (xa + xb + 1) / 2.0
        x_m = int(round(2 * c.get('_mitte', c['x'] + breite_) - (c['x'] + breite_) - breite_))   # andere Stammseite
        weg = 1 if c['x'] + (xa + xb + 1) / 2.0 >= c.get('_mitte', 0) else -1   # vom Stamm weg rutschen
        for x in [c['x'] + weg * dx for dx in range(0, 31, 2)] + [x_m - weg * dx for dx in range(0, 31, 2)]:
            if not frei(x):
                continue
            fy, fx = np.nonzero(al[max(0, zu - 3):zu + 1])
            boden = set(P.kl[np.clip((fy + max(0, zu - 3) + c['y']) // T, 0, P.R - 1),
                             np.clip((fx + x) // T, 0, P.C - 1)].tolist())
            if c['basis'] != 'karte01/deko/50' and not boden <= set('nem'):
                continue
            if not boden <= set('ngqpem'):
                continue
            ziel = x
            break
        if t is not None:
            zahl[krone] -= 100
            addieren(t, 1)
        if ziel is None:
            P.objekte.remove(c)
            P.fehl.append((c['basis'], c['kachel'][0], c['kachel'][1], 'Begleiter entfernt (Abstand)',
                           'frei' if frei(c['x']) else 'belegt'))
            continue
        c['x'] = ziel
        addieren(c, 1)


def main():
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    lvl = np.load(os.path.join(KARTE, 'pixelhoehe.npy'))
    lichter = json.load(open(os.path.join(OBJ, 'gebaeude', 'lichter.json')))
    P = Platz(lay, lvl)
    A = lay['achse']
    # ------------------------------------------------------------------ Sperrfelder
    for (x0, x1, y0, y1, art) in lay['zebra']:
        P.sperren(x0, y0, x1, y1)
        if art == 'v':                                        # zwei Reihen vor beiden Enden frei
            P.sperren(x0, y0 - 2, x1, y0 - 1)
            P.sperren(x0, y1 + 1, x1, y1 + 2)
        else:
            P.sperren(x0 - 2, y0, x0 - 1, y1)
            P.sperren(x1 + 1, y0, x1 + 2, y1)
    for tp in lay['teleporter']:
        P.sperren(tp['x'] - 1, tp['y'] - 1, tp['x'] + tp['b'], tp['y'] + tp['h'])
    tx0, tx1, ty = lay['treppe_terrasse']
    P.sperren(tx0 - 1, ty - 1, tx1 + 1, ty + 3)
    laeden_tueren = [(5 + 4 * i + (2 if i % 2 == 0 else 1), 18) for i in range(10) if i not in (2, 6)]
    TUEREN = laeden_tueren + [(72, 18), (73, 18), (14, 40), (15, 40), (50, 68), (51, 68), (49, 80), (60, 80),
                              (40, 80), (41, 80), (53, 80), (54, 80), (55, 80), (56, 80)] + \
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
    GRUEN, KLEIN_B, GROSS_B = 'k18/baum2/01', 'karte01/baeume/03', 'k18/baum2/00'   # PixelLab-Stadtbaeume
    GINKGO, GINKGO2, GINKGO_K = 'gebaeude/ginkgo', 'gebaeude/ginkgo_gross', 'gebaeude/ginkgo_klein'
    BUESCHEL, BLUMEN, BUSCH, LAUB = 'karte01/deko/06', 'karte01/deko/00', 'karte01/deko/25', 'karte01/deko/50'

    def begleiter_versuch(nm, sx, rr, rasen, t, spiegel=False, mitte=None):
        """Ein Begleiter an der Stelle sx (Mitte) mit Fuss in Reihe rr. Bueschel/Blumen (rasen) liegen ganz auf dem
        Rasen des Baums (2 px innerhalb, nie auf Pflaster/Randstein), Laub darf auf Gehweg/Pflaster liegen. Nie im
        Nebel und nie naeher als 2 px an einer Nebelkachel."""
        if not (0 <= rr < P.R):
            return None
        datei, al, zu, xa, xb = P.sprite(nm, spiegel)
        breite = xb - xa + 1
        if rasen:
            tx_ = int(sx // T)
            if not (0 <= tx_ < P.C) or P.kl[rr, tx_] not in rasen:
                tx_ = int(mitte // T) if mitte is not None else -1   # sonst in den Rasen des Stamms ruecken
                if not (0 <= tx_ < P.C) or P.kl[rr, tx_] not in rasen:
                    return None
            a_ = tx_
            while a_ - 1 >= 0 and P.kl[rr, a_ - 1] in rasen:
                a_ -= 1
            b_ = tx_
            while b_ + 1 < P.C and P.kl[rr, b_ + 1] in rasen:
                b_ += 1
            lo, hi = a_ * T + 2, (b_ + 1) * T - 3
            if hi - lo + 1 < breite:
                return None
            x0 = min(max(sx - breite / 2.0, lo), hi - breite + 1)
            sx = x0 + breite / 2.0
        x0, x1 = int(sx - breite / 2.0) - 2, int(sx + breite / 2.0) + 2
        if '.' in ''.join(P.kl[max(0, rr - 1):rr + 1, max(0, x0 // T):min(P.C, x1 // T + 1)].ravel()):
            return None
        n_fehl = len(P.fehl)
        o = P.setzen(nm, 0, rr, cx=sx, spiegel=spiegel, boden=rasen if rasen else (t['_boden'] | set('gqn')),
                     begleiter=True, extra={'pflanze': True, 'begleiter': True, 'kein_schatten': True})
        del P.fehl[n_fehl:]                                   # Fehlversuche nicht melden (naechster Kandidat folgt)
        if o:
            o['_eltern'] = t
            o['_mitte'] = mitte if mitte is not None else sx
        return o

    def baum(n_, bx, r, bd, cx=None, begleit=True, nn=None):
        t = P.setzen(n_, bx, r, boden=bd, cx=cx, n=nn, extra={'baum': True})
        if t and begleit:                                     # Begleiter an beiden Sockelecken (Einbettung, Regel 5b)
            t['_boden'] = set(bd)
            datei, al, zu, xa, xb = P.sprite(n_)
            fz = np.nonzero(al[zu - 1])[0]
            mitte = t['x'] + (fz.mean() if len(fz) else (xa + xb) / 2)
            rasen = set(bd) & set('nem')
            if rasen:
                paar_ = ((BUESCHEL, rasen), (LAUB if 'ginkgo' in n_ else BLUMEN, None if 'ginkgo' in n_ else rasen))
            else:                                             # Strassenbaum auf dem Gehweg: herabgefallenes Laub
                paar_ = ((LAUB, None), (LAUB, None))
            for seite, (nm, rs_) in zip((-1, 1), paar_):
                if nm == LAUB:                                # Laub ist breit (28 px): weiter aussen, sonst vor
                    kand = ((mitte + 18 * seite, r), (mitte + 26 * seite, r), (mitte + 4 * seite, r + 1),
                            (mitte - 50 * seite, r))          # den Stamm auf den Gehweg
                else:                                         # Nebelseite: andere Seite oder vor den Stamm
                    kand = ((mitte + 12 * seite, r), (mitte + 20 * seite, r), (mitte - 28 * seite, r),
                            (mitte + 6 * seite, r + 1))
                for (sx, rr) in kand:
                    if begleiter_versuch(nm, sx, rr, rs_, t, spiegel=(nm == LAUB and seite > 0), mitte=mitte):
                        break
                else:
                    P.fehl.append((nm, int(mitte // T), r, 'Begleiter ohne Platz'))
        return t
    # Spielplatz: gruener Baum NW, Ginkgo NO (Vorlage)
    baum('karte01/baeume/00', 47, 8, RASEN)
    baum('k18/baum2/02', 59, 7, RASEN)
    # Park SW: je Rasen zwei Baeume versetzt (nie in einer Reihe), dazu Begleiter
    # Park SW (jetzt unten, Reihen 73-93; unter der Hochbahn 80-83 nichts Hohes)
    for (n_, bx, r) in ((GROSS_B, 9, 78), (GRUEN, 20, 76), (KLEIN_B, 25, 78),
                        (GROSS_B, 8, 91), (KLEIN_B, 11, 93), (GRUEN, 21, 90), (GROSS_B, 24, 93)):
        baum(n_, bx, r, RASEN)
    baum(GINKGO, 0, 93, RASEN, cx=17 * T)                     # Ginkgo auf dem kleinen Rasen
    # Mittelstreifen: Baum am Ostende jeder Hecke (Vorlage), Uferstrasse: vier Baeume auf der Hecke
    SB = ('k18/baum2/00', 'k18/baum2/01')        # Stadtbaeume wie Vorlage: Wurzeln in der Hecke
    for i, (bx, r) in enumerate(((11, 48), (23, 48), (47, 48), (59, 48))):
        baum(SB[i % 2], bx, r, set('m'), nn=3)                # Rasen-Mittelstreifen: Baum mit Bueschel/Blumen
    for i, cx in enumerate((71 * T, 87 * T, 104 * T, 117 * T)):
        baum(SB[i % 2], 0, 88, set('m'), cx=cx)
    # Ginkgos an der Querstrasse: Westseite auf dem Gehweg, Ostseite in Baumscheiben (Allee)
    for r in (31, 58, 72):
        baum('k18/baum2/02', 29, r, set('gq'))
    for r in (72, 76):
        baum(GINKGO, 0, r, RASEN, cx=601)
    # Platz: je ein Baum mittig im Rasenbeet, dazu Bueschel am Stamm und ein paar Blumen im Gras
    BL = ('karte01/deko/00', 'karte01/deko/02')
    for i, (x0, y0, x1, y1) in enumerate(lay['beete']):
        n_ = 'k18/baum2/02' if (x0, y0) in ((65, 27), (117, 57)) else SB[i % 2]
        cx_ = (x0 + x1 + 1) / 2.0 * T
        baum(n_, 0, y1 - 1 if y1 - y0 >= 3 else y1, set('e'), cx=cx_)
        for (fx, fy) in ((x0 + 1.2, y1), (x1 - 0.2, y0 + 1)) if y1 - y0 >= 3 else ():
            P.setzen(BL[(i + int(fx)) % 2], 0, int(fy), cx=fx * T, boden=set('e'), begleiter=True,
                     extra={'pflanze': True, 'begleiter': True, 'kein_schatten': True})
    # ------------------------------------------------------------------ Grosse Einzelobjekte
    P.setzen('k18/platz/00', 18, 61, boden=set('q'), n=4)        # Notlager (jetzt oben): Spitzzelt, Sandsaecke symmetrisch
    P.setzen('karte03/klein/43', 0, 61, boden=set('q'), cx=16.5 * T)
    P.setzen('karte03/klein/43', 0, 61, boden=set('q'), cx=23.5 * T, spiegel=True)
    P.setzen('gebaeude/feuerschale', 17, 64, boden=set('q'), anim='flammen18')
    P.setzen('k18/strasse/32', 24, 64, boden=set('q'))       # Kisten
    P.setzen('k18/strasse/01', 11, 57, boden=set('q'))       # Getraenkeautomat
    P.setzen('gebaeude/koban', 26, 65, boden=set('q'), anim='rechtecke', extra={'licht_rects': lichter.get('koban', [])})
    P.setzen('karte10/spielplatz/00', 50, 9, boden=RASEN)    # Spielplatz (Vorlage)
    P.setzen('karte10/spielplatz/01', 57, 11, boden=RASEN)
    P.setzen('gebaeude/kletterkuppel', 57, 13, boden=RASEN)
    P.setzen('karte10/spielplatz/02', 47, 15, boden=set('g'))
    P.setzen('k18/platz/05', 52, 17, boden=set('g'))
    P.setzen('karte10/banner/06', 56, 17, boden=set('g'))     # Uhr
    P.setzen('karte10/klein/38', 54, 17, boden=set('g'))     # Bank
    P.setzen('k18/platz/06', 60, 15, boden=set('gn'))
    for (n_, bx, sp) in (('k18/platz/02', 65, False), ('k18/platz/01', 87, False), ('k18/platz/02', 91, True)):
        P.setzen(n_, bx, 96, boden=set('b'), n=4, spiegel=sp)
    P.setzen('k18/platz/13', 44, 97, boden=set('b'))           # Fischkisten am Kai
    P.setzen('k18/platz/03', 54, 36, boden=set('s'), n=4)     # Lieferwagen auf dem Parkplatz
    LAT_YATAI = [[0, 14, 9, 26, 0], [50, 14, 59, 26, 2]]
    P.setzen('k18/platz/11', 21, 71, boden=set('q'), n=4, anim='rechtecke', extra={'licht_rects': LAT_YATAI})   # Imbissstand (Laternen leuchten)
    P.setzen('k18/frontal/02', 66, 19)                        # Bushaltestellen
    P.setzen('k18/frontal/03', 21, 41)
    P.setzen('k18/frontal/00', 111, 102, boden=set('w'), anim='boot', extra={'kein_schatten': True})
    # ------------------------------------------------------------------ Laternen (fester Rhythmus, Vorlage)
    LAT, DLAT = 'karte02/abgeleitet/laterne', 'gebaeude/doppellaterne'
    for x in (5, 13, 31, 37, 51, 60, 78):                     # Nordseite obere Strasse, zwischen den Ladentueren
        P.setzen(LAT, x, 19)
    for x in (10, 19, 46, 55, 64, 73):                        # Suedseite obere Strasse
        P.setzen(LAT, x, 26)
    for x in (7, 17, 46, 54, 61):                             # Gehweg vor dem Wohnblock / Parkplatz
        P.setzen(LAT, x, 41)
    for x in (12, 24, 44, 58):                                # Suedseite mittlere Strasse
        P.setzen(LAT, x, 54)
    for cx in (8, 20, 44, 56):                                # zweiarmige Leuchten auf dem Mittelstreifen
        P.setzen(DLAT, 0, 48, boden=set('m'), cx=cx * T + 8)   # Mittelstreifen jetzt Rasen
    for r in (36, 64, 76):                                    # Querstrasse Westseite / Ostseite
        P.setzen(LAT, 31, r)
    for r in (31, 61, 69):
        P.setzen(LAT, 37, r)
    for (bx, r) in ((17, 73), (16, 89), (29, 90), (10, 59), (13, 67), (26, 70), (61, 13)):
        P.setzen(LAT, bx, r, boden=GEHEN | RASEN)
    for x in (14, 28, 38, 50, 62, 74, 86, 96, 110, 122):      # Uferpromenade (Zebra 98-101 frei)
        P.setzen(LAT, x, 95)
    P.setzen(LAT, 0, 103, boden=set('h'), cx=107 * T)          # Steglaterne (Reihe 104 bleibt frei)
    for r in (40, 48, 64, 72):                                # Platz: Paare am Mittelweg (gespiegelt an der Achse)
        P.paar(LAT, 88, r)
    for r in (34, 56):
        P.paar(LAT, 79, r)
    P.paar(LAT, 92, 30, boden=set('t'))                       # Terrasse
    AMP = 'karte10/banner/13'                                 # Ampeln an den Kreuzungen
    for (bx, r) in ((30, 26), (37, 26), (30, 41), (37, 41), (30, 54), (37, 54)):
        P.setzen(AMP, bx, r)
    P.setzen('k18/strasse/17', 26, 26, anim='rechtecke', extra={'licht_rects': [[7, 6, 10, 9, 0]]})
    # ------------------------------------------------------------------ Stadtmoebel (sparsam, nie in Reihen)
    STR = lambda i: 'k18/strasse/%02d' % i
    for (n_, bx, r) in ((STR(1), 47, 19), (STR(2), 54, 19), (STR(40), 61, 26), (STR(5), 64, 19)):
        P.setzen(n_, bx, r)
    P.setzen(STR(0), 25, 40, anim='rechtecke', extra={'licht_rects': [[2, 5, 17, 16, 0]]})
    for xb in (128, 162):                                     # Fahrraeder
        P.setzen(STR(4), 0, 41, x=xb, dy=-3)
    P.paar(STR(6), 82, 52)                                    # Infotafeln (Paar)
    for bx in (84, 86, 88, 90):                               # hohe Banner vor der Terrasse, Masten gespiegelt
        P.paar('k18/platz/07', bx, 36, anim='fahne18', anker=3.5)
    for bx in (20, 44):
        P.setzen(STR(50), bx, 19, anim='fahne18')             # Nobori vor Ramen-Laden und Izakaya
    for r in (44, 56, 68):                                    # Baenke am Mittelweg (Paare)
        P.paar(STR(14), 95, r)
    for (bx, r) in ((14, 64), (9, 71), (16, 78), (73, 52), (116, 52)):
        P.setzen('karte10/klein/38', bx, r, boden=set('gpqn'))
    BAKE = {'anim': 'rechtecke', 'extra': {'licht_rects': [[4, 1, 5, 2, 0], [22, 1, 23, 2, 2]]}}
    for bx in (87, 89, 93):                                   # Absperrungen an der Terrassenkante (Paare)
        P.paar(STR(7), bx, 31, boden=set('t'), **BAKE)
    P.setzen(STR(7), 26, 59, boden=set('q'), **BAKE)
    P.setzen('karte13/klein/12', 58, 41)                      # Pylone
    for (bx, r) in ((58, 26), (22, 55), (60, 69), (19, 41), (60, 95), (106, 95)):
        P.setzen('karte02/klein/16', bx, r)                   # Muelleimer
    for (bx, r) in ((24, 26), (47, 41), (40, 69)):
        P.setzen('karte02/klein/17', bx, r)                   # Hydranten
    P.setzen('karte02/klein/31', 54, 69)                      # Muellcontainer
    P.setzen('karte10/klein2/02', 63, 41, boden=set('gp'))    # Durchfahrt verboten
    for r in range(20, 25):                                   # Poller am Strassenende
        P.setzen('gebaeude/poller', 82, r, boden=set('g'))
    for x in (64, 68, 72, 76):                                # Poller am Platzrand (Reihe 78)
        P.setzen('gebaeude/poller', x, 78, boden=set('pc'))
    for x in (80, 84, 88, 92, 96):
        P.paar('gebaeude/poller', x, 78, boden=set('pc'))
    for x in range(14, 124, 16):                              # Festmacher an der Kaikante
        P.setzen(STR(21), x, 99, boden=set('k'))
    for (bx, r) in ((104, 101), (108, 101), (104, 105), (108, 105)):
        P.setzen(STR(21), bx, r, boden=set('h'))
    for bx in (30, 56, 116):
        P.setzen(STR(11), bx, 97, boden=set('b'))             # Rettungsringe
    P.setzen(STR(11), 108, 103, boden=set('h'))
    # ------------------------------------------------------------------ Autos (Linksverkehr, ganz in der Spur)
    AUTO = lambda i: 'k18/autos/%02d' % i
    fahr = set('s')
    for (i, bx, r, ost) in [(0, 7, 21, True), (2, 45, 21, True), (1, 58, 24, False), (3, 6, 43, True),
                            (5, 8, 53, False), (1, 46, 50, False), (0, 65, 86, True), (4, 120, 86, True),
                            (5, 76, 93, False), (1, 118, 90, False), (0, 41, 93, False)]:
        P.setzen(AUTO(i), bx, r, spiegel=ost, boden=fahr, extra={'auto': True})
    P.setzen('gebaeude/bus', 0, 21, boden=fahr, cx=1080, dy=4, anim='rechtecke',
             extra={'auto': True, 'licht_rects': lichter.get('bus', [])})
    for (i, cx, r) in ((6, 35.75, 34), (7, 33.25, 66)):
        P.setzen(AUTO(i), 0, r, boden=fahr, cx=cx * T, extra={'auto': True})
    for (i, bx, r) in ((6, 42, 32), (7, 48, 32), (6, 54, 32)):   # Parkplatz: Nordbuchten, mit Luecken
        P.setzen(AUTO(i), bx, r, boden=fahr, n=3, extra={'auto': True})
    begleiter_nachpruefen(P)
    for o in P.objekte:
        for k in [k for k in o if k.startswith('_')]:
            del o[k]
    json.dump(P.objekte, open(os.path.join(OBJ, 'platzierung.json'), 'w'), indent=0)
    print('Karte 18: %d Objekte, %d nicht gesetzt' % (len(P.objekte), len(P.fehl)))
    for f in P.fehl:
        print('  -', f)


if __name__ == '__main__':
    main()
