"""Karte 16 (The Network), Neuaufbau: Gelaende.

Ankunft unten auf den Pfeilfeldern, ein schmaler Pfad nach Norden zu einer kreisrunden Plattform (wie Apocalymon's
Realm, am 16er-Raster gestuft). Boden aus den Plattenkacheln der Vorlage, Randring dunkler mit cyan glimmender
Kante, unter der Suedkante eine schmale Metallfront, von der Lichtstraenge in die Leere haengen. Ringsum die Leere
des Netzes: feines Raster, blauer Nebel, links und rechts blaue Datenstraenge (Datenpakete laufen nach unten) und
schwebende Datenfragmente (losgerissene Bodenplatten und kleine Datenwuerfel, 1 px auf und ab).

  python3 tools/karte16_layout.py && python3 tools/karte16_bauen.py
"""
import json, math, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
import karte_bauen as kb
import karte04_bauen as k4
import karte08_bauen as k8
import karte15_bauen as k15

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte16')
BASIS = os.path.join(ROOT, 'assets', 'karte16', 'basis')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte16')
T = 16
N_FRAMES = 4                     # Regel: hoechstens 4 Animationsbilder
BILDDAUER = 250
k4.N_FRAMES = k15.N_FRAMES = N_FRAMES
H = k4.H
CYAN = np.array([70, 220, 255], np.float32)
BLAU = np.array([60, 130, 255], np.float32)
LEER = np.array([8, 15, 32], np.float32)          # Hintergrund der Vorlage
kontur, mischen, puls = k15.kontur, k15.mischen, k15.puls


def fadenkreuz_drehen(a, f):
    """Das rote Fadenkreuz auf dem Tor dreht sich (Nutzerwunsch): der Kreis bleibt, die vier Striche werden je Bild
    um 22,5 Grad weitergedreht neu gezeichnet (nach 4 Bildern 90 Grad = nahtlos, da das Kreuz 4-fach symmetrisch
    ist). Nur diese Pixel aendern sich, der Bildschirm drumherum bleibt."""
    h, w = a.shape[:2]
    r_, g_, b_, al = a[..., 0], a[..., 1], a[..., 2], a[..., 3]
    yy, xx = np.mgrid[0:h, 0:w]
    box = (np.abs(yy - h / 2) < 13) & (np.abs(xx - w / 2) < 13)
    kreuz = box & (al > 0) & (r_ > 150) & (g_ < 120) & (b_ < 110)
    if kreuz.sum() < 10:
        return
    ys, xs = np.nonzero(kreuz)
    cy, cx = (ys.min() + ys.max()) / 2.0, (xs.min() + xs.max()) / 2.0
    d = np.hypot(yy - cy, xx - cx)
    ring_d = np.median(d[kreuz & (np.abs(yy - cy) > 2) & (np.abs(xx - cx) > 2)])
    kreis = kreuz & (np.abs(d - ring_d) <= 1.0)
    striche = kreuz & ~kreis
    hinter = np.array((74, 20, 24), np.float32)               # Bildschirmgrund
    a[striche, :3] = hinter
    r_max = d[striche].max()
    winkel = math.radians(22.5 * (f % 4))
    for k in range(4):
        w_ = winkel + k * math.pi / 2
        for t in np.arange(1.5, r_max + 0.5, 0.5):
            X, Y = int(round(cx + math.cos(w_) * t)), int(round(cy + math.sin(w_) * t))
            if 0 <= X < w and 0 <= Y < h:
                a[Y, X, :3] = (224, 74, 60) if abs(t - ring_d) > 1.2 else a[Y, X, :3]
    a[int(round(cy)), int(round(cx)), :3] = (224, 74, 60)


def tor16(sp, frame, o):
    """Firewall-Tor: nur der rote Bildschirm mit Fadenkreuz pulsiert, die orangen Leiterbahnen laufen als Lichtwelle
    um den Rahmen. Rahmen und Hoerner bleiben unveraendert."""
    a = np.array(sp).astype(np.float32)
    fadenkreuz_drehen(a, frame or 0)
    r_, g_, b_, al = a[..., 0], a[..., 1], a[..., 2], a[..., 3]
    p = puls(frame)
    rot = (al > 0) & (r_ > 90) & (g_ < 70) & (b_ < 70)
    a[rot, :3] *= 0.82 + 0.3 * p
    orange = (al > 0) & (r_ > 180) & (g_ > 70) & (g_ < 190) & (b_ < 110)
    ys, xs = np.nonzero(orange)
    if len(ys):
        cy, cx = a.shape[0] / 2, a.shape[1] / 2
        w = (np.arctan2(ys - cy, xs - cx) / (2 * math.pi) + 0.5 - (frame or 0) / N_FRAMES) % 1.0
        k = 0.8 + 0.4 * (w < 0.25)
        a[ys, xs, :3] *= k[:, None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def bildschirm16(sp, frame, o):
    """Computer 'Dungeon Records': nur der Bildschirm lebt - die cyan Balken flackern leicht nacheinander, die gelben
    Punkte und das Gehaeuse-Laempchen blinken. Gehaeuse und Sockel bleiben ruhig."""
    a = np.array(sp).astype(np.float32)
    r_, g_, b_, al = a[..., 0], a[..., 1], a[..., 2], a[..., 3]
    f = frame or 0
    cyan = (al > 0) & (b_ > 170) & (g_ > 150) & (r_ < 140)
    ys, xs = np.nonzero(cyan)
    if len(ys):
        zeile = (ys // 4) % 4
        k = np.where(zeile == f % 4, 1.18, 0.95)
        a[ys, xs, :3] *= k[:, None]
    gelb = (al > 0) & (r_ > 190) & (g_ > 150) & (b_ < 110)
    a[gelb, :3] *= (1.12, 0.85, 1.0, 0.9)[f % 4]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


k4.TEILANIM['tor16'] = tor16
k4.TEILANIM['bildschirm16'] = bildschirm16


def pfeil_marke(a, tx, ty, farbe, frame, ph):
    """Pfeilfeld passend zum Aufstellfeld: vier Eckklammern (wie feld_marken) und ein Doppel-Chevron nach Norden,
    beides direkt auf dem Boden, 1 px dunkler Schlagschatten rechts unten, Leuchten pulsiert."""
    p = 0.55 + 0.45 * puls(frame, ph)
    farbe = np.array(farbe, np.float32)
    X, Y = tx * T, ty * T
    pix = []
    for (ex, ey, sx, sy) in ((2, 2, 1, 1), (13, 2, -1, 1), (2, 13, 1, -1), (13, 13, -1, -1)):
        for d in range(3):
            pix += [(Y + ey, X + ex + sx * d), (Y + ey + sy * d, X + ex)]
    for oy in (4, 8):                                           # zwei Chevrons uebereinander
        for d in range(4):
            pix += [(Y + oy + d, X + 7 - d), (Y + oy + d, X + 8 + d)]
    for (yy, xx) in pix:                                        # Schatten zuerst
        a[yy + 1, xx + 1] = (a[yy + 1, xx + 1] * 0.75).astype(np.uint8)
    for (yy, xx) in pix:
        a[yy, xx] = np.clip(a[yy, xx] * (1 - 0.8 * p) + farbe * 0.8 * p, 0, 255).astype(np.uint8)


def kachel(n):
    return np.array(Image.open(os.path.join(BASIS, n)).convert('RGB'))


def boden_textur(cols, rows):
    b0, b1 = kachel('boden_0.png'), kachel('boden_1.png')
    t = np.zeros((rows * T, cols * T, 3), np.uint8)
    for y in range(rows):
        for x in range(cols):
            t[y * T:(y + 1) * T, x * T:(x + 1) * T] = b1 if kb.variante(x, y) == 0 else b0
    return t


def blend(a, Y, X, farbe, s):
    a[Y, X] = np.clip(a[Y, X] * (1 - s) + farbe * s, 0, 255).astype(np.uint8)


# ---------------------------------------------------------------------------------------------- Leere
def leere(a, leer, frame):
    Hh, W = leer.shape
    for farbe, staerke, sd, gross in (((14, 40, 90), 0.55, 160, 6), ((10, 60, 110), 0.3, 161, 9)):
        rs = np.random.RandomState(sd)
        n = rs.rand(gross, gross)
        m = np.array(Image.fromarray((n * 255).astype(np.uint8)).resize((W, Hh), Image.BICUBIC)).astype(np.float32) / 255
        m = np.clip((m - 0.45) / 0.55, 0, 1) ** 1.6 * staerke
        m = np.where(leer, m, 0)[..., None]
        a[:] = np.clip(a * (1 - m) + np.array(farbe, np.float32) * m, 0, 255).astype(np.uint8)
    raster = np.zeros_like(leer)                                  # feines Netzraster alle 32 px (nur Punkte/Kreuze)
    raster[::32, ::4] = True
    raster[::4, ::32] = True
    mischen(a, raster & leer, (40, 80, 140), 0.25)


def straenge(a, leer, frame, seed=1616, zonen=((16, 300), (720, 1008)), n=9, y_bereich=None):
    """Blaue Datenstraenge in der Leere: senkrechte Lichtfaeden (teils mit einem Knick), auf denen Datenpakete nach
    unten laufen. 4 Bilder: jedes Paket wandert je Bild 1/4 seines Abstands weiter -> nahtlose Schleife."""
    f = frame or 0
    Hh, W = leer.shape
    rs = random.Random(seed)
    for zi, (xa, xb) in enumerate(zonen):
        for i in range(n):
            x = rs.randint(xa, xb)
            y0, y1 = (rs.randint(0, 200), rs.randint(380, Hh)) if y_bereich is None else \
                (rs.randint(0, y_bereich[0]), rs.randint(y_bereich[1], Hh))
            knick = rs.random() < 0.5
            ky, kd = rs.randint(y0 + 40, y1 - 40), rs.choice((-24, -16, 16, 24))
            pfad = []
            for y in range(y0, y1):
                xx = x + (kd if knick and y > ky else 0)
                pfad.append((xx, y))
                if knick and y == ky:                             # waagerechtes Stueck am Knick
                    for t in range(1, abs(kd)):
                        pfad.append((x + t * (1 if kd > 0 else -1), y))
            hell = rs.uniform(0.25, 0.45)
            abstand = rs.choice((32, 48, 64))
            lang = rs.randint(4, 9)
            ph = rs.randrange(abstand)
            farbe = CYAN if rs.random() < 0.5 else BLAU
            for j, (X, Y) in enumerate(pfad):
                if not (0 <= X < W and 0 <= Y < Hh and leer[Y, X]):
                    continue
                rand = min(j, len(pfad) - j) / 60.0                 # Enden blenden aus
                blend(a, Y, X, BLAU * 0.7, hell * min(1, rand))
                q = (j - ph - f * abstand // N_FRAMES) % abstand
                if q < lang:
                    s_ = (0.95 - 0.5 * q / lang) * min(1, rand + 0.2)
                    blend(a, Y, X, farbe, s_)
                    if q == 0 and X + 1 < W:
                        blend(a, Y, X + 1, farbe, 0.35 * s_)
                        blend(a, Y, X - 1, farbe, 0.35 * s_)


def fragmente(a, leer, frame, seed=1617, stellen=None):
    """Schwebende Datenfragmente: losgerissene Bodenplatten (1-3 Kacheln, an den Ecken stufig ausgebrochen, am
    4-px-Raster) mit schmaler Front und cyan glimmender Bruchkante, dazu kleine Datenwuerfel. Jedes schwebt 1 px
    auf und ab (eigener Takt)."""
    f = frame or 0
    Hh, W = leer.shape
    rs = random.Random(seed)
    tex = boden_textur(4, 3)
    belegt = ~leer.copy()
    stellen = stellen or [(56, 64), (190, 36), (120, 190), (236, 292), (48, 404), (196, 500), (100, 580),
               (790, 56), (912, 150), (816, 262), (950, 340), (770, 430), (900, 500), (968, 584)]
    for i, (x, y) in enumerate(stellen):
        x += rs.randint(-8, 8); y += rs.randint(-8, 8)
        d = (0, -1, 0, 1)[(f + i) % 4]
        if i % 3 == 2:                                            # kleiner Datenwuerfel
            s = rs.choice((6, 7, 8))
            Y0 = y + d
            if belegt[max(0, y - 6):y + s + 8, max(0, x - 4):x + s + 6].any():
                continue
            a[Y0 - 1:Y0 + s + 3, x - 1:x + s + 1] = (6, 10, 22)  # Kontur
            a[Y0:Y0 + s, x:x + s] = (34, 100, 180)
            a[Y0, x:x + s] = (130, 235, 255); a[Y0:Y0 + s, x] = (100, 210, 250)
            a[Y0 + s - 1, x + 1:x + s] = (20, 60, 120); a[Y0 + 1:Y0 + s, x + s - 1] = (20, 60, 120)
            a[Y0 + s:Y0 + s + 2, x:x + s] = (16, 34, 70)          # Unterseite
            pl = 0.5 + 0.5 * math.sin(2 * math.pi * (f / N_FRAMES + i * 0.3))
            blend(a, Y0 + s // 2, x + s // 2, np.array((230, 255, 255), np.float32), 0.45 + 0.5 * pl)
            belegt[y - 4:y + s + 6, x - 3:x + s + 3] = True
            continue
        bw, bh = rs.choice(((2, 1), (1, 1), (2, 2), (3, 1), (3, 2), (1, 2)))
        w, h = bw * T, bh * T
        Y0 = y + d
        if y < 6 or y + h + 12 > Hh or x + w + 4 > W or belegt[max(0, y - 6):y + h + 12, max(0, x - 4):x + w + 4].any():
            continue
        m = np.ones((h, w), bool)                                 # stufig ausgebrochene Ecken (4-px-Raster)
        for ecke in rs.sample([(0, 0), (0, 1), (1, 0), (1, 1)], rs.randint(1, 3)):
            for st in range(rs.randint(1, 3)):
                ew, eh = 4 * rs.randint(1, 3), 4 * (st + 1)
                ys_ = slice(0, eh) if ecke[0] == 0 else slice(h - eh, h)
                xs_ = slice(0, max(4, ew - 4 * st)) if ecke[1] == 0 else slice(w - max(4, ew - 4 * st), w)
                m[ys_, xs_] = False
        ox, oy = rs.randrange(0, 16), rs.randrange(0, 16)
        fl = np.zeros((Hh, W), bool)
        fl[Y0:Y0 + h, x:x + w] = m
        sub = np.zeros((h, w, 3), np.uint8)
        sub[:] = tex[oy:oy + h, ox:ox + w] if oy + h <= tex.shape[0] and ox + w <= tex.shape[1] else tex[:h, :w]
        a[fl] = sub[m]
        front = np.zeros((Hh, W), bool)                           # Front (5 px) unter der Platte
        tiefe = np.zeros((Hh, W), np.int8)
        for X in range(x, x + w):
            col = np.nonzero(fl[:, X])[0]
            if len(col):
                yb = col.max()
                for dd in range(1, 6):
                    if not fl[yb + dd, X]:
                        front[yb + dd, X] = True; tiefe[yb + dd, X] = dd
        a[front] = (34, 48, 82)
        a[front & (tiefe == 1)] = (70, 92, 132)
        a[front & (tiefe == 3)] = (40, 110, 170)
        a[front & (tiefe == 5)] = (18, 26, 48)
        aussen = kontur(np.array(Image.fromarray(((fl | front) * 255).astype(np.uint8)).filter(
            __import__('PIL.ImageFilter', fromlist=['x']).MaxFilter(3))) > 0) & ~(fl | front)
        a[aussen] = (5, 9, 20)
        pl = 0.5 + 0.5 * math.sin(2 * math.pi * (f / N_FRAMES + i * 0.21))
        kante = kontur(fl) & ~np.roll(front, -1, 0)
        mischen(a, kante, CYAN, 0.45 + 0.4 * pl)                  # glimmende Bruchkante
        belegt[y - 6:y + h + 12, x - 4:x + w + 4] = True


# ---------------------------------------------------------------------------------------------- Plattform
def front_und_faeden(a, land, frame, tiefe=10):
    """Schmale Metallfront unter den Suedkanten (Plattform, Ankunft), darunter haengende Lichtfaeden."""
    f = frame or 0
    Hh, W = land.shape
    front = np.zeros_like(land)
    unten = {}
    for x in range(W):                                               # jede Suedkante der Spalte (nicht nur die unterste)
        for y in np.nonzero(land[:-1, x] & ~land[1:, x])[0]:
            unten[(x, int(y))] = int(y)
            for dd in range(1, tiefe + 1):
                if y + dd < Hh and not land[y + dd, x]:
                    front[y + dd, x] = True
    for (x, _y), y in unten.items():
        for dd in range(1, tiefe + 1):
            Y = y + dd
            if Y >= Hh or not front[Y, x]:
                break
            c = np.array((30, 44, 76), np.float32) * (1.1 - 0.35 * dd / tiefe)
            if dd == 1:
                c = np.array((66, 90, 130), np.float32)               # Kante oben (Licht)
            if dd == 5 and x % 16 not in (0, 15):
                c = c * 0.6 + np.array((40, 120, 200), np.float32) * 0.4   # Leitungsrille
            if dd == tiefe:
                c = np.array((12, 18, 36), np.float32)
            a[Y, x] = np.clip(c, 0, 255).astype(np.uint8)
        if x % 16 == 0 and (x - 1, _y) in unten:                  # Plattenfugen in der Front
            for dd in range(2, tiefe):
                if y + dd < Hh and front[y + dd, x]:
                    a[y + dd, x] = (18, 26, 48)
    # haengende Lichtfaeden
    rs = random.Random(1618)
    xs = sorted(unten)
    for i in range(22):
        x, y0_ = rs.choice(xs)
        y = unten[(x, y0_)] + tiefe + 1
        lang = rs.randint(14, 54)
        ph = rs.random()
        for t in range(lang):
            Y = y + t
            if Y >= Hh or land[Y, x] or front[Y, x]:
                break
            s_ = 0.55 * (1 - t / lang)
            blend(a, Y, x, BLAU, s_)
            q = (t - (f * lang // N_FRAMES) - int(ph * lang)) % lang
            if q < 3:
                blend(a, Y, x, CYAN, 0.8 * (1 - t / lang) + 0.1)
    return front


def bauen(frame=None, speichern=True):
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cols, rows = lay['groesse']
    Wp, Hp = cols * T, rows * T
    kl = np.array([list(r) for r in lay['klassen']])
    gross = lambda m: np.kron(m, np.ones((T, T), int)).astype(bool)
    a = np.zeros((Hp, Wp, 3), np.uint8)
    a[:] = LEER
    land = gross(kl != '.')
    platt = gross(np.isin(kl, list('pr')))
    ring = gross(kl == 'r')
    pfad = gross(kl == 's')
    ank = gross(np.isin(kl, list('az')))
    leer = ~land
    leere(a, leer, frame)
    # ------------------------------------------------------------------ Boden
    bt = boden_textur(cols, rows)
    a[land] = bt[land]
    a[ring] = (bt[ring] * 0.72).astype(np.uint8)
    innen = platt & ~ring
    a[innen & np.roll(ring, -1, 0)] = (18, 26, 46)                # Stufe Ring -> Boden
    a[innen & np.roll(ring, 1, 0)] = (78, 104, 140)
    # Kreis der Plattform: zwei feine Ringlinien und Achsen-Markierung (Bodenzeichen)
    cx, cy = lay['platte'][0] * T, lay['platte'][1] * T
    yy, xx = np.mgrid[0:Hp, 0:Wp]
    d = np.hypot(xx + 0.5 - cx, yy + 0.5 - cy)
    p = puls(frame, 0.2)
    for rr, s_ in ((112, 0.28), (104, 0.18)):
        mischen(a, innen & (np.abs(d - rr) <= 0.7), CYAN, s_ + 0.12 * p)
    # Pfad: Lichtschienen an beiden Seiten (Leitlinie zur Plattform)
    x0, x1 = lay['pfad'][0] * T, (lay['pfad'][1] + 1) * T
    for X in (x0 + 2, x1 - 3):
        m = np.zeros_like(pfad); m[:, X] = True
        mischen(a, m & pfad, CYAN, 0.35 + 0.3 * p)
    # Pfeilmarken (Ankunft/Teleporter) im Stil des Sammelplatzes wie auf Karte 17/19: Eckklammern + Doppelpfeil
    # direkt auf dem Boden, cyan, leuchten nacheinander
    px0, px1, py = lay['pfeile']
    for i, X in enumerate(range(px0, px1 + 1)):
        pfeil_marke(a, X, py, (110, 225, 250), frame, i * 0.25)
    # Kanten: aussen dunkle Kontur, innen cyan glimmende Kante (wie Apocalymon's Realm, nur blau)
    front = front_und_faeden(a, land, frame)
    ak = kontur(land)
    a[ak] = (8, 14, 30)
    mischen(a, kontur(land & ~ak), CYAN, 0.4 + 0.3 * puls(frame, 0.6))
    rest = leer & ~front
    straenge(a, rest & (np.abs(xx - cx) > 190), frame)
    fragmente(a, rest & (np.abs(xx - cx) > 200), frame)
    lvl = np.zeros((Hp, Wp), np.uint8)
    lvl[land] = 2
    lvl[front] = 9
    if speichern and frame is None:
        np.save(os.path.join(KARTE, 'pixelhoehe.npy'), lvl)
        np.save(os.path.join(KARTE, 'wasser.npy'), np.packbits(np.zeros((Hp, Wp), bool)))
        np.save(os.path.join(KARTE, 'leere.npy'), np.packbits(rest))
    img = Image.fromarray(a).convert('RGBA')
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain_basis.png'))
    pf_ = os.path.join(OBJ, 'platzierung.json')
    if os.path.exists(pf_):
        objs = sorted((o for o in json.load(open(pf_)) if os.path.exists(os.path.join(OBJ, o['datei']))),
                      key=lambda o: o['y'] + o['fuss'])
        cache = {o['datei']: Image.open(os.path.join(OBJ, o['datei'])).convert('RGBA') for o in objs}
        k8.schatten_ebene(img, objs, cache, lvl)
        vor = np.array(img)
        k4.objekte_zeichnen(img, objs, cache, np.zeros((Hp, Wp), bool), frame)
        img = img.copy()
        k4.animieren(img, objs, cache, frame or 0, ruhig=frame is None)
        k8.verdeckung(img, objs, cache, lvl, vor)
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain.png'))
    print('Karte 16 %dx%d gebaut' % (cols, rows))
    return img


if __name__ == '__main__':
    bauen()
