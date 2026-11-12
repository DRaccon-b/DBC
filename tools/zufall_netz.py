"""Zufallskarten im Stil von Karte 16 (The Network, Gebiet A01): Plattformen in der Leere des Netzes.

Gleiche Schnittstelle wie tools/zufall_a02.py (Wald), damit Generator und Export beide Typen bauen koennen.
Dieselben Kartenstuecke (tools/zufall_stuecke.py) werden anders gelesen:
  F  Leere (feines Netzraster, blauer Nebel, Datenstraenge, schwebende Datenfragmente)
  G  Plattform aus den Bodenplatten von Karte 16 (assets/karte16/basis)
  P  Leitbahn auf der Plattform (etwas dunkler, cyan glimmende Leitlinie am Rand)
  W  Loch in der Plattform (Blick in die Leere, Metallfront an der Suedkante)
Kanten wie Karte 16: am 16er-Raster gestuft, aussen dunkle Kontur, innen cyan glimmende Kante, unter jeder Suedkante
eine schmale Metallfront mit haengenden Lichtfaeden.

Nahtlos ueber Stueckgrenzen: Nebel und Raster haengen nur von der Lage innerhalb des 14x14-Feldes ab (periodisch,
'ursprung' = Pixellage einer Feldecke), Datenstraenge, Fragmente und Lichtfaeden bleiben im 'bereich' (beim Export:
das Stueck selbst).
Objekte: Karte 16 (Tor, Computer, Netz, Kleinkram) und Karte 17 (Viren-Kokon als Boss).
"""
import math, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageFilter

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
OBJ16 = os.path.join(ROOT, 'assets', 'objekte', 'karte16')
OBJ17 = os.path.join(ROOT, 'assets', 'objekte', 'karte17')
BASIS16 = os.path.join(ROOT, 'assets', 'karte16', 'basis')
T, FELD = 16, 14
LEER = np.array([8, 15, 32], np.float32)
CYAN = np.array([70, 220, 255], np.float32)
BLAU = np.array([60, 130, 255], np.float32)

# feste Objekte der Stuecke: Wald-Sprite -> Netz-Sprite (je Stueck ueberschreibbar)
FEST = {
    'zufall_portal/01': 'tor/10',          # Ankunft: Teleporter-Plattform (dazu cyan Pfeilfelder davor)
    'gross/14': 'computer/00',             # Lagerfeuer -> Computer "Dungeon Records"
    'gross/13': 'netz/01',                 # Wegweiser -> Holo-Anzeige
    'zufall_brunnen/00': 'computer/15',    # Brunnen -> Datentank
    'gross/00': 'tor/08',                  # Runenbaum -> Datenmonolith
    'gross/01': 'computer/08',             # Rosabaum -> Kristallsaeule
    'gross/09': 'tor/07',                  # Findling -> Antenne
    'dschungel/00': 'k17/gross/01',        # Bossarena: Viren-Kokon (Karte 17)
}
KLEIN = ['klein/%02d' % i for i in (0, 4, 5, 8, 10, 11, 13, 17, 19, 22, 27, 31, 33, 35, 38, 53, 56, 58)]
MITTEL = ['netz/%02d' % i for i in (2, 3, 4, 7, 9, 14)]


def quelle(name):
    if name.startswith('k17/'):
        return os.path.join(OBJ17, name[4:] + '.png')
    return os.path.join(OBJ16, name + '.png')


def kachel(n):
    return np.array(Image.open(os.path.join(BASIS16, n)).convert('RGB'))


def mischen(a, m, farbe, s):
    a[m] = np.clip(a[m] * (1 - s) + np.array(farbe, np.float32) * s, 0, 255).astype(np.uint8)


def kontur(m):
    return m & ~(np.roll(m, 1, 0) & np.roll(m, -1, 0) & np.roll(m, 1, 1) & np.roll(m, -1, 1))


def blend(a, Y, X, farbe, s):
    a[Y, X] = np.clip(a[Y, X] * (1 - s) + farbe * s, 0, 255).astype(np.uint8)


def _nebel_kachel(seed, gross, P):
    """Periodischer Nebel (P x P px): Zufallsgitter gross x gross, umlaufend bikubisch vergroessert."""
    n = np.random.RandomState(seed).rand(gross, gross)
    n3 = np.tile(n, (3, 3))
    m = np.array(Image.fromarray((n3 * 255).astype(np.uint8)).resize((3 * P, 3 * P), Image.BICUBIC)).astype(np.float32) / 255
    return m[P:2 * P, P:2 * P]


def leere(a, leer, ursprung):
    """Nebel und Netzraster - nur abhaengig von der Lage im Feld (periodisch je 224 px) -> nahtlos an Stueckgrenzen."""
    Hh, W = leer.shape
    P = FELD * T
    oy, ox = ursprung
    yy = (np.arange(Hh) - oy) % P
    xx = (np.arange(W) - ox) % P
    for farbe, staerke, sd, gross in (((14, 40, 90), 0.55, 160, 6), ((10, 60, 110), 0.3, 161, 7)):
        k = _nebel_kachel(sd, gross, P)
        m = k[yy][:, xx]
        m = np.clip((m - 0.45) / 0.55, 0, 1) ** 1.6 * staerke
        m = np.where(leer, m, 0)[..., None]
        a[:] = np.clip(a * (1 - m) + np.array(farbe, np.float32) * m, 0, 255).astype(np.uint8)
    ry, rx = np.meshgrid((np.arange(Hh) - oy) % 32 == 0, (np.arange(W) - ox) % 4 == 0, indexing='ij')
    sy, sx = np.meshgrid((np.arange(Hh) - oy) % 4 == 0, (np.arange(W) - ox) % 32 == 0, indexing='ij')
    mischen(a, ((ry & rx) | (sy & sx)) & leer, (40, 80, 140), 0.25)


def straenge(a, leer, bereich, rs, frame=None):
    """Blaue Datenstraenge: senkrechte Lichtfaeden mit nach unten laufenden Datenpaketen, nur in langen senkrechten
    Leere-Abschnitten innerhalb des Bereichs, Enden blenden aus."""
    f = frame or 0
    Hh, W = leer.shape
    frei = leer & bereich
    n = int(frei.sum() / (FELD * T) ** 2 * 1.2 + 0.5)
    for _ in range(n * 6):
        if n <= 0:
            break
        x = rs.randrange(W)
        spalte = frei[:, x]
        ys = np.nonzero(spalte)[0]
        if len(ys) < 90:
            continue
        # laengster zusammenhaengender Abschnitt
        brueche = np.nonzero(np.diff(ys) > 1)[0]
        teile = np.split(ys, brueche + 1)
        t = max(teile, key=len)
        if len(t) < 90:
            continue
        y0 = int(t[0]) + rs.randint(4, 30)
        y1 = int(t[-1]) - rs.randint(4, 30)
        if y1 - y0 < 60:
            continue
        hell = rs.uniform(0.25, 0.45)
        abstand = rs.choice((32, 48, 64))
        lang = rs.randint(4, 9)
        ph = rs.randrange(abstand)
        farbe = CYAN if rs.random() < 0.5 else BLAU
        L = y1 - y0
        for j, Y in enumerate(range(y0, y1)):
            rand = min(j, L - j) / 40.0
            blend(a, Y, x, BLAU * 0.7, hell * min(1, rand))
            q = (j - ph - f * abstand // 4) % abstand
            if q < lang:
                s_ = (0.95 - 0.5 * q / lang) * min(1, rand + 0.2)
                blend(a, Y, x, farbe, s_)
        frei[:, max(0, x - 28):x + 29] = False                       # Abstand zwischen den Straengen
        n -= 1


def fragmente(a, leer, bereich, rs, boden_tex, frame=None):
    """Schwebende Datenfragmente (losgerissene Bodenplatten mit Front und cyan Bruchkante, kleine Datenwuerfel)."""
    f = frame or 0
    Hh, W = leer.shape
    frei = leer & bereich
    # Abstand zum Land und zum Bereichsrand
    zu = ~frei
    zu = np.array(Image.fromarray((zu * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(25))) > 0
    belegt = zu.copy()
    n = int(frei.sum() / (FELD * T) ** 2 * 1.6) + 1
    for i in range(n * 8):
        if n <= 0:
            break
        x, y = rs.randrange(8, W - 60), rs.randrange(8, Hh - 60)
        d = (0, -1, 0, 1)[(f + i) % 4]
        if rs.random() < 0.35:                                       # kleiner Datenwuerfel
            s = rs.choice((6, 7, 8))
            if belegt[y - 6:y + s + 8, x - 4:x + s + 6].any():
                continue
            Y0 = y + d
            a[Y0 - 1:Y0 + s + 3, x - 1:x + s + 1] = (6, 10, 22)
            a[Y0:Y0 + s, x:x + s] = (34, 100, 180)
            a[Y0, x:x + s] = (130, 235, 255); a[Y0:Y0 + s, x] = (100, 210, 250)
            a[Y0 + s - 1, x + 1:x + s] = (20, 60, 120); a[Y0 + 1:Y0 + s, x + s - 1] = (20, 60, 120)
            a[Y0 + s:Y0 + s + 2, x:x + s] = (16, 34, 70)
            blend(a, Y0 + s // 2, x + s // 2, np.array((230, 255, 255), np.float32), 0.7)
            belegt[y - 10:y + s + 12, x - 8:x + s + 8] = True
            n -= 1
            continue
        bw, bh = rs.choice(((2, 1), (1, 1), (2, 2), (3, 1), (1, 2)))
        w, h = bw * T, bh * T
        if belegt[y - 6:y + h + 12, x - 4:x + w + 4].any() or y + h + 12 > Hh or x + w + 4 > W:
            continue
        Y0 = y + d
        m = np.ones((h, w), bool)                                    # stufig ausgebrochene Ecken (4-px-Raster)
        for ecke in rs.sample([(0, 0), (0, 1), (1, 0), (1, 1)], rs.randint(1, 3)):
            for st in range(rs.randint(1, 3)):
                ew, eh = 4 * rs.randint(1, 3), 4 * (st + 1)
                ys_ = slice(0, eh) if ecke[0] == 0 else slice(h - eh, h)
                xs_ = slice(0, max(4, ew - 4 * st)) if ecke[1] == 0 else slice(w - max(4, ew - 4 * st), w)
                m[ys_, xs_] = False
        fl = np.zeros((Hh, W), bool)
        fl[Y0:Y0 + h, x:x + w] = m
        ox, oy = rs.randrange(0, 16), rs.randrange(0, 16)
        a[fl] = boden_tex[oy:oy + h, ox:ox + w][m]
        front = np.zeros((Hh, W), bool)
        tiefe = np.zeros((Hh, W), np.int8)
        for X in range(x, x + w):
            col = np.nonzero(fl[:, X])[0]
            if len(col):
                yb = col.max()
                for dd in range(1, 6):
                    if yb + dd < Hh and not fl[yb + dd, X]:
                        front[yb + dd, X] = True; tiefe[yb + dd, X] = dd
        a[front] = (34, 48, 82)
        a[front & (tiefe == 1)] = (70, 92, 132)
        a[front & (tiefe == 3)] = (40, 110, 170)
        a[front & (tiefe == 5)] = (18, 26, 48)
        aussen = kontur(np.array(Image.fromarray(((fl | front) * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3))) > 0) \
            & ~(fl | front)
        a[aussen] = (5, 9, 20)
        mischen(a, kontur(fl) & ~np.roll(front, -1, 0), CYAN, 0.6)
        belegt[y - 14:y + h + 18, x - 10:x + w + 10] = True
        n -= 1


def front_und_faeden(a, land, bereich, rs, frame=None, tiefe=10):
    """Schmale Metallfront unter jeder Suedkante, darunter haengende Lichtfaeden (enden im Bereich)."""
    f = frame or 0
    Hh, W = land.shape
    front = np.zeros_like(land)
    unten = []
    for x in range(W):
        for y in np.nonzero(land[:-1, x] & ~land[1:, x])[0]:
            unten.append((x, int(y)))
            for dd in range(1, tiefe + 1):
                if y + dd < Hh and not land[y + dd, x]:
                    front[y + dd, x] = True
    for (x, y) in unten:
        for dd in range(1, tiefe + 1):
            Y = y + dd
            if Y >= Hh or not front[Y, x]:
                break
            c = np.array((30, 44, 76), np.float32) * (1.1 - 0.35 * dd / tiefe)
            if dd == 1:
                c = np.array((66, 90, 130), np.float32)
            if dd == 5 and x % 16 not in (0, 15):
                c = c * 0.6 + np.array((40, 120, 200), np.float32) * 0.4
            if dd == tiefe:
                c = np.array((12, 18, 36), np.float32)
            a[Y, x] = np.clip(c, 0, 255).astype(np.uint8)
        if x % 16 == 0:
            for dd in range(2, tiefe):
                if y + dd < Hh and front[y + dd, x]:
                    a[y + dd, x] = (18, 26, 48)
    kandidaten = [(x, y) for (x, y) in unten if bereich[min(Hh - 1, y + tiefe + 1), x]]
    for i in range(min(len(kandidaten) // 40 + 1, 12) if kandidaten else 0):
        x, y0 = rs.choice(kandidaten)
        y = y0 + tiefe + 1
        lang = rs.randint(14, 54)
        ph = rs.random()
        for t in range(lang):
            Y = y + t
            if Y >= Hh or land[Y, x] or front[Y, x] or not bereich[Y, x]:
                break
            s_ = 0.55 * (1 - t / lang)
            blend(a, Y, x, BLAU, s_)
            q = (t - (f * lang // 4) - int(ph * lang)) % lang
            if q < 3:
                blend(a, Y, x, CYAN, 0.8 * (1 - t / lang) + 0.1)
    return front


def pfeil_marke(a, tx, ty, farbe):
    """Pfeilfeld wie Karte 16/17: vier Eckklammern und ein Doppel-Chevron nach Norden, cyan = Ankunft."""
    farbe = np.array(farbe, np.float32)
    X, Y = tx * T, ty * T
    pix = []
    for (ex, ey, sx, sy) in ((2, 2, 1, 1), (13, 2, -1, 1), (2, 13, 1, -1), (13, 13, -1, -1)):
        for d in range(3):
            pix += [(Y + ey, X + ex + sx * d), (Y + ey + sy * d, X + ex)]
    for oy in (4, 8):
        for d in range(4):
            pix += [(Y + oy + d, X + 7 - d), (Y + oy + d, X + 8 + d)]
    for (yy, xx) in pix:
        a[yy + 1, xx + 1] = (a[yy + 1, xx + 1] * 0.75).astype(np.uint8)
    for (yy, xx) in pix:
        a[yy, xx] = np.clip(a[yy, xx] * 0.2 + farbe * 0.8, 0, 255).astype(np.uint8)


def ankunft_felder(raster, fest):
    """Kacheln der cyan Pfeilfelder direkt unter der Teleporter-Plattform (Ankunft) - nur wenn alle drei auf der
    Plattform liegen und kein anderes festes Objekt (Block ca. 4x4 ueber seinem Fuss) dort steht."""
    rows, cols = len(raster), len(raster[0])
    for (name, cx, cy) in fest:
        if name != 'zufall_portal/01':
            continue
        andere = [(n, x, y) for (n, x, y) in fest if n != name]
        for dy in (1, 2):
            felder = [(cx + dx, cy + dy) for dx in (-1, 0, 1)]
            if all(0 <= tx < cols and 0 <= ty < rows and raster[ty][tx] == 'G' for tx, ty in felder) and \
                    not any(abs(tx - x) <= 2 and y - 3 <= ty <= y for tx, ty in felder for (_, x, y) in andere):
                return felder
    return []


def boden_bauen(raster, frame=None, fest=(), ursprung=(0, 0), bereich=None, seed=16, **_):
    """-> (RGB-Array, Leere-Maske). ursprung: Pixellage einer Feldecke (fuer periodischen Nebel/Raster),
    bereich: Pixelmaske, in der Straenge/Fragmente/Lichtfaeden liegen duerfen (Standard: ganze Flaeche)."""
    rows, cols = len(raster), len(raster[0])
    Hp, Wp = rows * T, cols * T
    gross = lambda m: np.kron(np.array(m), np.ones((T, T), int)).astype(bool)
    kl = [list(z) for z in raster]
    land = gross([[c in 'GP' for c in z] for z in kl])
    pfad = gross([[c == 'P' for c in z] for z in kl])
    leer = ~land
    if bereich is None:
        bereich = np.ones((Hp, Wp), bool)
    rs = random.Random(seed)
    a = np.zeros((Hp, Wp, 3), np.uint8)
    a[:] = LEER
    leere(a, leer, ursprung)
    import karte_bauen as kb
    b0, b1 = kachel('boden_0.png'), kachel('boden_1.png')
    bt = np.zeros((Hp, Wp, 3), np.uint8)
    for y in range(rows):
        for x in range(cols):
            bt[y * T:(y + 1) * T, x * T:(x + 1) * T] = b1 if kb.variante(x, y) == 0 else b0
    a[land] = bt[land]
    a[pfad] = (bt[pfad] * 0.86).astype(np.uint8)                       # Leitbahn etwas dunkler
    mischen(a, kontur(pfad) & land & ~kontur(land), CYAN, 0.32)          # cyan Leitlinie am Bahnrand
    for (tx, ty) in ankunft_felder(raster, fest):
        pfeil_marke(a, tx, ty, (110, 225, 250))
    front = front_und_faeden(a, land, bereich, rs, frame)
    ak = kontur(land)
    a[ak] = (8, 14, 30)
    mischen(a, kontur(land & ~ak), CYAN, 0.55)
    rest = leer & ~front
    straenge(a, rest, bereich, rs, frame)
    tex = np.zeros((3 * T, 4 * T, 3), np.uint8)
    for y in range(3):
        for x in range(4):
            tex[y * T:(y + 1) * T, x * T:(x + 1) * T] = b1 if (x + y) % 3 == 0 else b0
    fragmente(a, rest, bereich, rs, tex, frame)
    return a, leer | front


def waldboden(boden_rgb, objekte, obj_dir):
    return boden_rgb                                                     # (kein Waldboden im Netz)


def objekte_setzen(raster, fest, symmetrie, obj_dir, seed=1, innen=None):
    """Objekte am Raster (kleinster Kachelblock, Fuss buendig, mittig), nur auf Plattformboden mit Abstand zur Kante."""
    from karte04_objekte import saeubern
    rows, cols = len(raster), len(raster[0])
    rnd = random.Random(seed)
    objekte, belegt, gesperrt, cache = [], set(), set(), {}

    def k(tx, ty):
        return raster[min(rows - 1, max(0, ty))][min(cols - 1, max(0, tx))]

    def setze(name, fx, fy, opt=None, frei=False):
        opt = dict(opt or {})
        tx, ty = int(math.floor(fx)), int(fy)
        if frei and ((tx, ty) in gesperrt or any((tx + dx, ty + dy) in belegt for dx in (-1, 0, 1) for dy in (-1, 0, 1))):
            return None
        if name not in cache:
            sp = saeubern(Image.open(quelle(name)).convert('RGBA'))
            aa = np.array(sp.getchannel('A')) > 0
            ys, xs = np.nonzero(aa)
            ux0, uy0, ux1, uy1 = int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())
            datei = 'netz/%s.png' % name.replace('/', '-')
            os.makedirs(os.path.join(obj_dir, 'netz'), exist_ok=True)
            sp.save(os.path.join(obj_dir, datei))
            cache[name] = (datei, sp.height, ux0, uy0, ux1, uy1)
        datei, h, ux0, uy0, ux1, uy1 = cache[name]
        bw, bh = ux1 - ux0 + 1, uy1 - uy0 + 1
        wt, ht = math.ceil(bw / T), math.ceil(bh / T)
        bx = int(round(fx + 0.5 - wt / 2.0))
        if frei:                                                     # ganzer Fuss (unterste Reihe) auf Plattform, nicht am Rand
            for x in range(bx - 1, bx + wt + 1):
                for y in (ty - 1, ty, ty + 1):
                    if k(x, y) != 'G':
                        return None
        o = {'datei': datei, 'basis': name, 'x': bx * T + (wt * T - bw) // 2 - ux0, 'y': (ty + 1) * T - 1 - uy1,
             'fuss': h, 'kachel': [tx, ty], 'block': [bx, ty - ht + 1, wt, ht], 'ebene': 1, 'an_wand': True}
        o.update(opt)
        objekte.append(o)
        belegt.add((tx, ty))
        for x in range(bx, bx + wt):
            for y in range(ty - ht + 1, ty + 1):
                gesperrt.add((x, y))
        return o

    fest_objs = {}
    paare = {f for _, a_, b_ in symmetrie for f in (a_, b_)}
    for (name, cx, cy) in fest:
        neu = 'tor/09' if (name, cx, cy) in paare else FEST.get(name, name)     # Arena: Energiesaeulen-Paar
        fest_objs[(name, cx, cy)] = setze(neu, cx, cy, {'fest': True})
    for achse, a_, b_ in symmetrie:                                   # Paare exakt spiegelgleich zur Achse
        oa, o1, o2 = fest_objs.get(achse), fest_objs.get(a_), fest_objs.get(b_)
        if not (oa and o1 and o2):
            continue
        mitte = lambda o: (o['block'][0] + o['block'][2] / 2.0) * T
        m = mitte(oa)
        links, rechts = sorted((o1, o2), key=mitte)
        d = round((m - mitte(links) + mitte(rechts) - m) / 2.0)
        links['x'] += int(round(m - d - mitte(links)))
        rechts['x'] += int(round(m + d - mitte(rechts)))
    for (name, cx, cy) in fest:                                      # Bossarena bleibt freie Kampfflaeche
        if name == 'dschungel/00':
            for x in range(cx - 10, cx + 11):
                for y in range(cy - 8, cy + 12):
                    gesperrt.add((x, y))
    for (tx, ty) in ankunft_felder(raster, fest):                     # Ankunft und Umgebung frei
        for x in range(tx - 2, tx + 3):
            for y in range(ty - 4, ty + 3):
                gesperrt.add((x, y))
    plattform = [(tx, ty) for ty in range(rows) for tx in range(cols) if raster[ty][tx] == 'G']
    if innen:                                                    # Export: 2 Kacheln Abstand zum Stueckrand (Nachbar unbekannt)
        x0, y0, x1, y1 = innen
        plattform = [(tx, ty) for (tx, ty) in plattform if x0 + 2 <= tx <= x1 - 3 and y0 + 2 <= ty <= y1 - 3]
    ziel = len(plattform) // 60                                     # Kleinkram dezent
    vorrat, n = [], 0
    for _ in range(ziel * 40):
        if n >= ziel or not plattform:
            break
        tx, ty = rnd.choice(plattform)
        if not vorrat:
            vorrat = KLEIN[:] + MITTEL[:]
            rnd.shuffle(vorrat)
        name = vorrat[-1]
        if any(o['basis'] == name and abs(o['kachel'][0] - tx) <= 4 and abs(o['kachel'][1] - ty) <= 4 for o in objekte):
            continue                                                  # gleiche Motive nie nebeneinander
        if setze(name, tx, ty, {}, frei=True):
            vorrat.pop()
            n += 1
    return objekte


def zeichnen(boden_rgb, leer, objekte, obj_dir, frame=None):
    """Schatten wie Karte 16 (karte08_bauen.schatten_ebene, nur auf der Plattform), dann die Sprites."""
    import karte04_bauen as k4
    import karte08_bauen as k8
    img = Image.fromarray(boden_rgb).convert('RGBA')
    objs = sorted(objekte, key=lambda o: o['y'] + o['fuss'])
    cache = {o['datei']: Image.open(os.path.join(obj_dir, o['datei'])).convert('RGBA') for o in objs}
    lvl = np.where(leer, 0, 2).astype(np.uint8)
    k8.schatten_ebene(img, objs, cache, lvl)
    k4.objekte_zeichnen(img, objs, cache, np.zeros(leer.shape, bool), frame)
    return img, cache


def bauen(raster, fest, symmetrie, obj_dir, seed=1, frame=None):
    boden, leer = boden_bauen(raster, frame, fest)
    objekte = objekte_setzen(raster, fest, symmetrie, obj_dir, seed)
    bild, cache = zeichnen(boden, leer, objekte, obj_dir, frame)
    return {'bild': bild, 'boden': boden, 'objekte': objekte, 'cache': cache, 'wasser': leer}


def kollision(raster, objekte, cache, leer, x0=0, y0=0, w=None, h=None):
    import zufall_a02
    return zufall_a02.kollision(raster, objekte, cache, leer, x0, y0, w, h)
