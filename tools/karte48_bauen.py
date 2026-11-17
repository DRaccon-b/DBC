"""Karte 48 - Water Realm: Outer Currents (A03 Nr. 15), Gelaende nach maps/karte48/layout.json.

Flachwasser (Nutzer: begehbar, knoecheltief) ueber hellem Sandgrund mit wandernden Lichtnetzen (Kaustik) und
Glanzstrichen; tiefes Meer (gesperrt) als Abbruchkante unter Wasser mit Tiefenstufen (wasser_vertieft, laeuft ueber
den Kartenrand); helle Steinplattformen (Hoehe 1) aus Quaderplatten mit Steinfront und Wasserlinie, Treppen nach
Sueden/Norden; offene Wasserbibliothek: dunkler Fliesenboden, massive Rueckwand (Abdeckung + Quaderwand),
Seitenwaende als schmale Mauern mit Stirnseite; zwei Teleporter am Kartenrand.

  python3 tools/karte48_layout.py && python3 tools/karte48_bauen.py
"""
import json, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
import karte_bauen as kb
import karte04_bauen as k4
import karte06_bauen as k6
import karte20_bauen as k20
import wasser_vertieft
import wasser_details
wasser_details.felsen_setzen = lambda *a_, **k_: None   # keine automatischen Felsspitzen

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte48')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte48')
T = 16
N_FRAMES = 4
BILDDAUER = 250
k4.N_FRAMES = N_FRAMES
kb.N_FRAMES = N_FRAMES
H = k4.H
weich, zell_maske, flaeche = k4.weich, k4.zell_maske, k20.flaeche
k4.SCHATTEN = {'farbe': (18, 58, 66), 'dx': 0.3, 'dy': 0.15, 'kern': 100, 'wurf': (66, 52)}   # kuehl, auf Wasser
k4.RASTER45 = True
k4.FELS['stein48'] = ['#283240', '#3a4656', '#4e5c6c', '#647282', '#7c8a98', '#96a2ae', '#b4bec6']
LIPPE = ['#6a7684', '#808c98', '#96a2ac', '#aab4bc', '#bcc4ca', '#ccd2d6']
FRONT = 16
SEITE = 6
RAND_FLACH = ['#3c8a8e', '#56a0a0', '#72b4b0', '#8cc4bc']   # helle Sandbank-Kante zum tiefen Wasser


def faerben(lo, hi, a0=0.35, a1=0.5):
    def f(a):
        l = a.mean(axis=2, keepdims=True) / 255.0
        return np.array(lo, np.float32) + (np.array(hi, np.float32) - np.array(lo, np.float32)) * np.clip((l - a0) / a1, 0, 1)
    return f


def platten(cols, rows, basis=(150, 160, 166), fuge=(96, 104, 114), hoehe=16, laenge=(32, 48), seed=48):
    """Helle Quaderplatten wie in der Vorlage: Reihen 16 px hoch, versetzte Fugen, Licht oben links."""
    t = np.zeros((rows * T, cols * T, 3), np.uint8)
    rng = np.random.RandomState(seed)
    b = np.array(basis, float)
    for y in range(0, rows * T, hoehe):
        x = -rng.randint(0, laenge[1])
        while x < cols * T:
            l_ = rng.choice(laenge)
            x0, x1 = max(0, x), min(cols * T, x + l_)
            if x1 > x0:
                c = b + rng.randint(-6, 7)
                t[y:y + hoehe, x0:x1] = np.clip(c, 0, 255)
                t[y + 1, x0:x1] = np.clip(c + 14, 0, 255)
                t[y:y + hoehe, x0] = np.clip(c + 8, 0, 255)
                t[y + hoehe - 2, x0:x1] = np.clip(c - 12, 0, 255)
                t[y + hoehe - 1, x0:x1] = fuge
                t[y:y + hoehe, x1 - 1] = fuge
                for _ in range(rng.randint(0, 3)):                    # feine Poren/Abplatzer
                    py, px = y + rng.randint(3, hoehe - 3), rng.randint(x0, x1)
                    t[py, min(px, cols * T - 1)] = np.clip(c - 16, 0, 255)
            x += l_
    return t


def fliesen(cols, rows):
    """Dunkler Fliesenboden der Bibliothek (16er-Raster, Kanten hell oben links, Fuge dunkel)."""
    t = np.zeros((rows * T, cols * T, 3), np.uint8)
    rng = np.random.RandomState(481)
    for y in range(0, rows * T, T):
        for x in range(0, cols * T, T):
            c = np.array((96, 108, 126)) + rng.randint(-5, 6)
            t[y:y + T, x:x + T] = c
            t[y, x:x + T] = np.clip(c + 16, 0, 255)
            t[y:y + T, x] = np.clip(c + 8, 0, 255)
            t[y + T - 1, x:x + T] = (62, 70, 86)
            t[y:y + T, x + T - 1] = (68, 76, 92)
    return t


def kaustik(a, m, frame):
    """Lichtnetz auf dem Sandgrund unter dem Flachwasser (wandert in einer geschlossenen Schleife)."""
    Hh, W = m.shape
    n = max(1, N_FRAMES)
    ph = 2 * math.pi * ((frame or 0) % n) / n
    yy, xx = np.mgrid[0:Hh, 0:W].astype(np.float32)
    v = np.sin(xx / 9.0 + np.sin(yy / 13.0) * 1.6 + ph) + np.sin(yy / 8.0 + np.sin(xx / 11.0) * 1.4 - ph)
    netz = (np.abs(v) < 0.16) & m
    hell = netz & ((xx.astype(int) + yy.astype(int)) % 3 != 0)
    a[hell] = np.minimum(a[hell].astype(int) + np.array([22, 30, 26]), 255).astype(np.uint8)


def glanz(a, m, frame):
    """Kurze helle Glanzstriche auf der Oberflaeche des Flachwassers (wandern langsam nach rechts unten)."""
    Hh, W = m.shape
    fr = frame or 0
    for ky in range(0, Hh // T):
        for kx in range(0, W // T):
            h_ = (kx * 73856093 ^ ky * 19349663) & 0xffff
            if h_ % 3:
                continue
            sy = ky * T + (h_ >> 4) % 12 + 2
            sx = kx * T + (h_ >> 8) % 10 + 2 + fr % 4
            if sy < Hh and sx + 3 < W and m[sy, sx:sx + 3].all():
                a[sy, sx:sx + 3] = (170, 222, 220)
                a[sy, sx + 1] = (226, 248, 244)


def hallenwaende(a, lay, wand):
    """Rueckwand (Abdeckung 16 px + Quaderwand 32 px + Schattenfuge) und Seitenwaende (schmale Abdeckung, Stirnseite)."""
    rx0, ry0, rx1, ry1 = lay['raum']
    KR = [np.array(H(c)) for c in ('#2a3040', '#3a4254', '#4c566a', '#5e6a80', '#76849a', '#929eb2')]
    rng = np.random.RandomState(482)

    def abdeckung(y0, y1, x0, x1):
        a[y0:y1, x0:x1] = KR[3]
        a[y0:y0 + 2, x0:x1] = KR[5]
        a[y0:y1, x0:x0 + 1] = KR[4]
        a[y1 - 2:y1, x0:x1] = KR[1]
        a[y0:y1, x1 - 1:x1] = KR[1]
        for x in range(x0 + 16, x1 - 4, 16):                          # Deckplattenfugen
            a[y0 + 2:y1 - 2, x] = KR[2]

    def quader(y0, y1, x0, x1):
        for r, y in enumerate(range(y0, y1, 8)):
            off = 8 if r % 2 else 0
            for bx in range(x0 - off, x1, 16):
                c = KR[1] + rng.randint(-3, 4)
                xa, xb = max(bx, x0), min(bx + 16, x1)
                a[y:y + 8, xa:xb] = np.clip(c, 0, 255)
                a[y, xa:xb] = KR[2]
                a[y:y + 8, xa] = KR[2]
                a[y + 7, xa:xb] = KR[0]
        a[y1 - 1, x0:x1] = KR[0]

    X0, X1 = rx0 * T, (rx1 + 1) * T
    Y0 = ry0 * T
    abdeckung(Y0, Y0 + 16, X0, X1)                                    # Rueckwand
    quader(Y0 + 16, Y0 + 48, X0 + 16, X1 - 16)
    a[Y0 + 16:Y0 + 18, X0 + 16:X1 - 16] = (a[Y0 + 16:Y0 + 18, X0 + 16:X1 - 16] * 0.6).astype(np.uint8)   # Schattenfuge
    wand[Y0:Y0 + 48, X0:X1] = True
    YS = (ry1 + 1) * T                                                # Seitenwaende: Abdeckung bis zur Stirnseite
    for xs in (X0, X1 - 16):
        abdeckung(Y0, YS - 16, xs + 4, xs + 12)
        a[Y0 + 16:YS - 16, xs:xs + 4] = a[Y0 + 16:YS - 16, xs:xs + 4]
        quader(YS - 16, YS, xs + 4, xs + 12)                          # Stirnseite nach Sueden
        wand[Y0:YS, xs + 4:xs + 12] = True
        # Schlagschatten der Wand auf den Boden (rechts unten)
        sx = xs + 12
        a[Y0 + 48:YS + 2, sx:sx + 3] = (a[Y0 + 48:YS + 2, sx:sx + 3] * 0.8).astype(np.uint8)
        a[YS:YS + 2, xs + 4:xs + 12] = (a[YS:YS + 2, xs + 4:xs + 12] * 0.75).astype(np.uint8)
    a[Y0 + 48:Y0 + 51, X0 + 12:X1 - 12] = (a[Y0 + 48:Y0 + 51, X0 + 12:X1 - 12] * 0.78).astype(np.uint8)   # Bodenschatten


def bauen(frame=None, speichern=True):
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cls = lay['klassen']
    cols, rows = lay['groesse']
    Wp, Hp = cols * T, rows * T
    hp = np.kron(np.array([[int(c) for c in z] for z in lay['hoehe']]), np.ones((T, T), int))
    basis = os.path.join(ROOT, 'assets', 'basis')
    sand = flaeche(k6.kacheln(os.path.join(basis, 'sand_%d.png'), 5, faerben((70, 140, 146), (112, 178, 176), 0.3, 0.55)), cols, rows)
    a = sand.copy()
    flach = ~zell_maske(cls, 'x', cols, rows).astype(bool)
    kaustik(a, flach, frame)
    glanz(a, flach, frame)
    # tiefes Meer: Abbruchkante unter Wasser mit Tiefenstufen, laeuft ueber den Kartenrand
    xm = weich(zell_maske(cls, 'x', cols, rows), 4, 0.0, 8, 0.5)
    P = 24
    wasser_vertieft.MIN_FLAECHE, wasser_vertieft.OEFFNEN = 3000, 5   # keine Einzelloecher und duennen Stufen-Finger
    ag = np.pad(a, ((P, P), (P, P), (0, 0)), mode='edge')
    mg = np.pad(xm, ((P, P), (P, P)), mode='edge')
    ag = np.array(wasser_vertieft.vertiefen(Image.fromarray(ag), np.ones_like(mg), frame, maske=mg, rand=RAND_FLACH,
                                            stufen=[(30, 0.82, 8), (64, 0.68, 7)]).convert('RGB'))
    wasser_vertieft.MIN_FLAECHE, wasser_vertieft.OEFFNEN = 0, 3
    a = ag[P:-P, P:-P].copy()
    a[xm] = np.clip(a[xm].astype(float) * np.array([0.82, 0.9, 1.0]), 0, 255).astype(np.uint8)   # tiefer = blauer
    # Steinplattformen (Hoehe 1) mit Front
    tex_p = platten(cols, rows)
    hoch = weich((hp >= 1).astype(np.float32), 5, 0.0, 7, 0.5)
    hoch = hoch | (np.kron(np.array([[c in 'pimT' for c in z] for z in cls]), np.ones((T, T), bool)) & ~xm & False)
    a[hoch] = tex_p[hoch]
    im_ = np.kron(np.array([[c in 'im' for c in z] for z in cls]), np.ones((T, T), bool)) & hoch
    a[im_] = fliesen(cols, rows)[im_]
    frei = np.zeros((Hp, Wp), bool)
    for (x0, x1, ry, r_) in lay['treppen']:
        if r_ == 's':
            frei[ry * T - 4:ry * T + FRONT + 10, x0 * T:(x1 + 1) * T] = True
    wand = k4.hoehenkanten(a, hoch, 'stein48', FRONT, SEITE, LIPPE, frei, 48, berg=False)
    # Wasserlinie am Fuss der Fronten (heller Saum, wandert je Bild)
    unter = np.zeros_like(wand)
    unter[1:] = wand[:-1] & ~wand[1:] & ~hoch[1:]
    xs_ = np.nonzero(unter)
    sel = ((xs_[1] + (frame or 0) * 2) % 6) < 3
    a[xs_[0][sel], xs_[1][sel]] = (150, 210, 208)
    a[xs_[0][~sel], xs_[1][~sel]] = (98, 168, 170)
    for (x0, x1, ry, r_) in lay['treppen']:
        if r_ == 's':
            k4.treppe(a, x0 * T, (x1 + 1) * T, ry * T - 1, 's', FRONT, 'stein48', tex_p)
        else:
            k4.treppe(a, x0 * T, (x1 + 1) * T, (ry + 1) * T - 12, 'n', FRONT, 'stein48', tex_p)
    hallenwaende(a, lay, wand)
    for tp in lay['teleporter']:
        k4.teleporter_zeichnen(a, tp['x'], tp['y'], tp['b'], tp['h'], frame)
    img = Image.fromarray(a).convert('RGBA')
    lvl = hp.astype(np.uint8) + 1
    lvl[wand] = 9                                                    # Fronten und Hallenwaende = Wand
    for (x0, x1, ry, r_) in lay['treppen']:                          # Treppen begehbar
        lvl[ry * T:(ry + 1) * T, x0 * T:(x1 + 1) * T] = 2
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain_basis.png'))
        np.save(os.path.join(KARTE, 'pixelhoehe.npy'), lvl)
        np.save(os.path.join(KARTE, 'wand.npy'), np.packbits(wand))
        np.save(os.path.join(KARTE, 'wasser.npy'), np.packbits(xm))
        np.save(os.path.join(KARTE, 'treppe.npy'), np.packbits(np.kron(np.array([[c == 't' for c in z] for z in cls]),
                                                                       np.ones((T, T), bool))))
    pf = os.path.join(OBJ, 'platzierung.json')
    if os.path.exists(pf):
        objs = sorted((o for o in json.load(open(pf)) if os.path.exists(os.path.join(OBJ, o['datei']))),
                      key=lambda o: o.get('sortier', o['y'] + o['fuss']))
        if objs:
            cache = {o['datei']: Image.open(os.path.join(OBJ, o['datei'])).convert('RGBA') for o in objs}
            ebenen = lvl.copy().astype(np.int16)
            ebenen[wand] = 9
            ebenen[xm] = 7
            if frame is not None:                                          # treibende Objekte: 1 px auf und ab
                objs = [dict(o, y=o['y'] + (1 if math.sin(2 * math.pi * (frame + o.get('phase', 0)) / N_FRAMES) > 0
                                            else 0)) if o.get('treibend') else o for o in objs]
            k4.objekte_zeichnen(img, objs, cache, ~xm & ~wand, frame, ebenen=ebenen)
            k4.animieren(img, objs, cache, frame or 0)
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain.png'))
    print('Karte 48 %dx%d gebaut' % (cols, rows))
    return img


if __name__ == '__main__':
    bauen()
