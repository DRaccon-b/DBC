"""Karte 05 (Freezeland): Schneefeld, Nordplateau mit Eisklippen, Eissee mit Loechern, Gletscherspalten,
Eismeer, Waldrand, Dorfplatz. Baut auf den Bausteinen von Karte 04 auf (Waende, Treppen, Schatten, Objekte).

  python3 tools/karte05_layout.py && python3 tools/karte05_kacheln.py
  python3 tools/karte05_objekte.py && python3 tools/karte05_bauen.py   -> maps/karte05/terrain.png

Licht oben links, Schatten nur auf dem Boden, alle Objekte am 16x16-Raster (karte05_objekte.py).
"""
import json, math, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
import karte_bauen as kb
import karte04_bauen as k4
import bauwerke

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte05')
BASIS5 = os.path.join(ROOT, 'assets', 'karte05', 'basis')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte05')
T = 16
N_FRAMES = 16
H = k4.H
weich, zell_maske = k4.weich, k4.zell_maske

k4.FELS['eis'] = ['#3e5274', '#566e92', '#7088ac', '#8ca4c4', '#aac0d8', '#c8d8e8', '#e6eff7']
LIPPE_SCHNEE = ['#90a6bc', '#b0c4d6', '#cad9e6', '#dfe9f2', '#f0f6fb', '#ffffff']


def textur(cls, art, cols, rows):
    t = np.zeros((rows * T, cols * T, 3), np.uint8)
    ks = [np.array(Image.open(os.path.join(BASIS5, '%s_%d.png' % (art, v))).convert('RGB')) for v in range(5)]
    for y in range(rows):
        for x in range(cols):
            t[y * T:(y + 1) * T, x * T:(x + 1) * T] = ks[kb.variante(x, y)]
    return t


def spalten_zeichnen(a, km):
    """Gletscherspalte: dunkler, nach unten tiefer werdender Grund, oben eine helle Eiskante mit Ueberhang,
    an der Suedkante eine schmale beleuchtete Eiswand, ringsum Schneewechte."""
    Hh, W = km.shape
    F = [np.array(H(c)) for c in k4.FELS['eis']]
    for y, x in zip(*np.nonzero(km)):
        tiefe = 0
        while tiefe < 6 and y - tiefe - 1 >= 0 and km[y - tiefe - 1, x]:
            tiefe += 1
        a[y, x] = H('#0e1428') if tiefe >= 4 else H('#16203a') if tiefe >= 2 else F[0]
    oben = km & ~np.roll(km, 1, 0)
    unten = km & ~np.roll(km, -1, 0)
    for y, x in zip(*np.nonzero(oben)):            # Nordkante: Wechte, die ueberhaengt
        a[y, x] = H('#ffffff')
        if y + 1 < Hh and km[y + 1, x]:
            a[y + 1, x] = H('#c2d6e6')
        if y - 1 >= 0:
            a[y - 1, x] = H('#e2ecf4')
    for y, x in zip(*np.nonzero(unten)):            # Suedkante: Eiswand im Licht (nach Norden zeigend)
        for k in range(3):
            if y - k >= 0 and km[y - k, x]:
                a[y - k, x] = F[5 - k]
        if y + 1 < Hh:
            a[y + 1, x] = (a[y + 1, x] * 0.86).astype(np.uint8)
    seite = km & ~(np.roll(km, 1, 1) & np.roll(km, -1, 1))
    for y, x in zip(*np.nonzero(seite)):
        a[y, x] = F[2]


def wasser_kalt(a, m, frame, dunkel=False):
    """Wasser aus Karte 01, kuehler getoent; offene Eisloecher deutlich dunkler und tiefer."""
    k4.wasser_zeichnen(a, m, frame, np.zeros_like(m))
    if dunkel:
        a[m] = np.clip(a[m] * np.array([0.22, 0.3, 0.48]) + np.array([4, 10, 30]), 0, 255).astype(np.uint8)
    else:
        a[m] = np.clip(a[m] * np.array([0.42, 0.55, 0.55]) + np.array([92, 118, 128]), 0, 255).astype(np.uint8)
        rs = random.Random(5)                                         # Eisschollen
        ys, xs = np.nonzero(m)
        for _ in range(len(ys) // 900):
            i = rs.randrange(len(ys)); cy, cx = ys[i], xs[i]
            rx, ry = rs.randint(4, 10), rs.randint(2, 5)
            for y in range(cy - ry, cy + ry + 1):
                for x in range(cx - rx, cx + rx + 1):
                    if 0 <= y < m.shape[0] and 0 <= x < m.shape[1] and m[y, x] and ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1:
                        a[y, x] = H('#f2f9fc') if y < cy else H('#d6ebf4')


def eis_zeichnen(a, m, frame):
    """Zugefrorene Flaeche ueber vertieftem Wasser: der Grund (Steine, Stufen, Felsen, Algen) bleibt sichtbar,
    darueber eine helle, leicht blaue Eisschicht mit feinen Rissen, Lichtreflexen und Schneeflocken am Rand."""
    if not m.any():
        return
    Hh, W = m.shape
    eis = np.array(H('#dcf1fa'), np.float32)
    a[m] = np.clip(a[m] * 0.5 + eis * 0.5, 0, 255).astype(np.uint8)
    rs = random.Random(17)
    ys, xs = np.nonzero(m)
    for _ in range(len(ys) // 4500):                      # Risse: wenige, laengere Linien
        i = rs.randrange(len(ys)); y, x = float(ys[i]), float(xs[i])
        w = rs.uniform(0, 6.28)
        for k in range(rs.randint(18, 40)):
            w += rs.uniform(-0.5, 0.5)
            y += math.sin(w); x += math.cos(w)
            yi, xi = int(y), int(x)
            if not (0 <= yi < Hh and 0 <= xi < W) or not m[yi, xi]:
                break
            a[yi, xi] = H('#f6fcff')
            if 0 <= yi + 1 < Hh and m[yi + 1, xi]:
                a[yi + 1, xi] = (a[yi + 1, xi] * 0.8).astype(np.uint8)
    for _ in range(len(ys) // 900):                       # Reflexe: kurze helle Diagonalen (oben links Licht)
        i = rs.randrange(len(ys)); y, x = ys[i], xs[i]
        for k in range(4):
            if 0 <= y - k < Hh and 0 <= x + k < W and m[y - k, x + k]:
                a[y - k, x + k] = H('#ffffff') if k in (1, 2) else H('#eaf7fd')
    rand = m & ~(np.roll(m, 1, 0) & np.roll(m, -1, 0) & np.roll(m, 1, 1) & np.roll(m, -1, 1))
    a[rand] = H('#ffffff')


def schneefall(img, frame):
    """Zwei Schichten Flocken, die in 16 Frames nahtlos weiterfallen (Muster wiederholt sich senkrecht)."""
    px = img.load()
    W, Hh = img.size
    for (kw, kh, n, groesse, seed, al) in ((176, 64, 9, 2, 3, 210), (128, 32, 7, 1, 8, 150)):
        rs = random.Random(seed)
        flocken = [(rs.randrange(kw), rs.randrange(kh), rs.random() * 6.28) for _ in range(n)]
        dy = frame * kh // N_FRAMES
        for oy in range(-kh, Hh + kh, kh):
            for ox in range(0, W, kw):
                for (fx, fy, ph) in flocken:
                    x = ox + fx + int(round(2 * math.sin(2 * math.pi * frame / N_FRAMES + ph)))
                    y = oy + (fy + dy) % kh
                    for ddx in range(groesse):
                        for ddy in range(groesse):
                            X, Y = x + ddx, y + ddy
                            if 0 <= X < W and 0 <= Y < Hh:
                                r_, g_, b_, _ = px[X, Y]
                                t = al / 255.0
                                px[X, Y] = (int(r_ + (255 - r_) * t), int(g_ + (255 - g_) * t), int(b_ + (255 - b_) * t), 255)


def schatten_k5(img, objs, cache, lvl):
    """Kontakt- und Schlagschatten (Licht oben links) wie Karte 04, aber je Objekt nur auf der Hoehenebene,
    auf der sein Fuss steht: nie auf Klippenwaende, Wasser, Spalten oder ueber eine Kante auf eine andere Ebene.
    Gerechnet wird je Objekt nur in seinem Ausschnitt (schnell genug fuer die Animation)."""
    from PIL import ImageFilter
    Hh, W = lvl.shape
    sch = np.zeros((Hh, W), np.uint8)
    for o in objs:
        if o.get('kein_schatten'):                 # z. B. Hoehle in der Klippe: kein Schlagschatten
            continue
        sp = cache[o['datei']]
        a = np.array(sp.getchannel('A')) >= 200
        if o.get('ebene', 1) == 0 and a.any():   # liegende Objekte (Ast, Knochen ...): Schatten der ganzen Form
            ys_, xs_ = np.nonzero(a)
            for dx_, dy_, wert in ((2, 2, 60), (1, 1, 72)):
                Y = o['y'] + ys_ + dy_; X = o['x'] + xs_ + dx_
                ok = (Y >= 0) & (Y < Hh) & (X >= 0) & (X < W)
                Y, X = Y[ok], X[ok]
                if not len(Y):
                    continue
                fy_ = min(Hh - 1, max(0, o['y'] + int(ys_.max()) + 1)); fx_ = min(W - 1, max(0, o['x'] + int(xs_.mean())))
                eb = lvl[fy_, fx_]
                gut = lvl[Y, X] == eb
                sch[Y[gut], X[gut]] = np.maximum(sch[Y[gut], X[gut]], wert)
            continue
        zeilen = np.nonzero(a.any(axis=1))[0]
        if len(zeilen) < 4:
            continue
        zu = int(zeilen.max())
        hoehe_ = max(1, zu - int(zeilen.min()))
        fuss = np.nonzero(a[max(0, zu - 3):zu + 1].any(axis=0))[0]
        if not len(fuss):
            continue
        fx = min(W - 1, max(0, o['x'] + int(fuss.min() + fuss.max()) // 2))
        fy = min(Hh - 1, max(0, o['y'] + zu + 1))
        ebene = lvl[fy, fx]
        if ebene not in (1, 2):
            continue
        # Ausschnitt in Kartenkoordinaten
        X0 = o['x'] - 2
        Y0 = o['y']
        bw = sp.width + int(hoehe_ * 0.5) + 8
        bh = zu + int(hoehe_ * 0.3) + 8
        teil = np.zeros((bh, bw), np.float32)
        wurf = np.zeros((bh, bw), np.float32)
        fx0, fx1 = int(fuss.min()) + 2, int(fuss.max()) + 2
        for yy in range(zu - 1, zu + 3):
            ein = (yy - zu + 1) if yy > zu else 0
            teil[yy, max(0, fx0 - 1 + ein):max(0, fx1 + 3 - ein)] = 92
        for zi in zeilen:
            k = zu - zi
            ty = int(zu + k * 0.24)
            dx = int(1 + k * 0.45)
            xs = np.nonzero(a[zi])[0] + 2 + dx
            xs = xs[xs < bw]
            if ty < bh:
                wurf[ty, xs] = np.maximum(wurf[ty, xs], 1.0 - 0.35 * k / hoehe_)
        w = np.array(Image.fromarray((wurf * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3))) / 255.0
        teil = np.maximum(teil, np.where(w > 0.82, 64, np.where(w > 0, 50, 0)))
        # auf die Karte zuschneiden und nur auf der eigenen Ebene
        y0, y1 = max(0, Y0), min(Hh, Y0 + bh)
        x0, x1 = max(0, X0), min(W, X0 + bw)
        if y1 <= y0 or x1 <= x0:
            continue
        t = teil[y0 - Y0:y1 - Y0, x0 - X0:x1 - X0]
        t[lvl[y0:y1, x0:x1] != ebene] = 0
        sch[y0:y1, x0:x1] = np.maximum(sch[y0:y1, x0:x1], t.astype(np.uint8))
    dunkel = Image.new('RGBA', img.size, (40, 52, 84, 255))       # kuehler Schnee-Schatten
    dunkel.putalpha(Image.fromarray(sch))
    img.alpha_composite(dunkel)


def bauen(frame=None, speichern=True):
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cols, rows = lay['groesse']
    cls = lay['klassen']
    hoehe = np.array([[int(c) for c in r] for r in lay['hoehe']])
    Wp, Hp = cols * T, rows * T
    a = textur(cls, 's', cols, rows)
    # --- weiche Bodenarten
    for art, blur, rausch, seed in (('l', 6.0, 0.5, 3), ('w', 4.0, 0.42, 4), ('e', 5.0, 0.45, 5), ('r', 3.5, 0.4, 6)):
        roh = zell_maske(cls, art, cols, rows)
        m = weich(roh, blur, rausch, seed)
        tx = textur(cls, art, cols, rows)
        a[m] = tx[m]
        saum = weich(roh, blur, rausch, seed, 0.38) & ~m
        k4.dunkeln(a, saum, 0.95)
    # Eissee: klarere Kante mit hellem Eisrand
    sroh = zell_maske(cls, 'id', cols, rows)
    see = weich(sroh, 4.5, 0.25, 7)
    tx = textur(cls, 'i', cols, rows)
    a[see] = tx[see]
    rand = see & ~(np.roll(see, 1, 0) & np.roll(see, -1, 0) & np.roll(see, 1, 1) & np.roll(see, -1, 1))
    a[rand] = H('#e8f6fc')
    # Waldboden unter dem Waldrand
    hroh = zell_maske(cls, 'h', cols, rows)
    hm = weich(hroh, 5, 0.4, 8)
    tx = textur(cls, 'h', cols, rows)
    a[hm] = tx[hm]
    # --- Hoehen
    stufe = lambda n: zell_maske([''.join('1' if v >= n else '0' for v in r) for r in hoehe], '1', cols, rows)
    spalte = zell_maske(cls, 'k', cols, rows) > 0
    m1 = weich(np.maximum(stufe(1), spalte.astype(np.float32)), 6, 0, 21)
    m2 = weich(stufe(2), 6, 0.32, 22)
    tx = textur(cls, 'g', cols, rows)
    plateau_boden = m2 & ~weich(zell_maske(cls, 'xlhq', cols, rows), 5, 0.3, 9)
    a[plateau_boden] = tx[plateau_boden]
    # --- Wasser: Meer (rechts, oben) und Loecher im Eissee
    meer = weich(zell_maske(cls, 'x', cols, rows), 5, 0.15, 24, 0.45) | weich(zell_maske(cls, 'q', cols, rows), 4.5, 0.3, 27, 0.45)
    loch = weich(zell_maske(cls, 'd', cols, rows), 3.0, 0.3, 25, 0.5) & see
    wasser_kalt(a, meer, frame)
    wasser_kalt(a, loch, frame, dunkel=True)
    import wasser_vertieft                                  # Stil von Karte 01: vertieftes Wasser, Schneerand
    a = np.array(wasser_vertieft.vertiefen(Image.fromarray(a), np.ones_like(meer), frame, maske=meer | see,
                                           rand=('#7e96ae', '#a2b8cc', '#c6d6e4', '#e2ecf4')).convert('RGB'))
    eis_zeichnen(a, see & ~loch, frame)
    for y, x in zip(*np.nonzero(loch & ~np.roll(loch, -1, 0))):        # Eiskante am Lochrand (Dicke)
        for k in range(1, 3):
            if y - k >= 0 and loch[y - k, x]:
                pass
    lr = loch & ~(np.roll(loch, 1, 0) & np.roll(loch, -1, 0) & np.roll(loch, 1, 1) & np.roll(loch, -1, 1))
    a[lr] = H('#ffffff')
    oben_loch = loch & ~np.roll(loch, 1, 0)
    for y, x in zip(*np.nonzero(oben_loch)):
        for k in range(1, 4):
            if y + k < Hp and loch[y + k, x]:
                a[y + k, x] = H('#3e7aa6') if k == 1 else H('#2c5c86') if k == 2 else a[y + k, x]
    # --- Treppen (Plateau -> Schneefeld)
    treppen_info = []
    frei_pl = np.zeros((Hp, Wp), bool)
    for (x0, x1, y0, y1, r) in lay.get('treppen', []):
        px0, px1 = x0 * T + 1, (x1 + 1) * T - 1
        ye = max((max(np.nonzero(m2[y0 * T:(y1 + 1) * T, xc])[0]) + y0 * T
                  for xc in range(px0, px1) if m2[y0 * T:(y1 + 1) * T, xc].any()
                  and not m2[y0 * T:(y1 + 1) * T, xc].all()), default=None)
        if ye is None:
            continue
        frei_pl[ye - 14:ye + 70, px0 - 6:px1 + 6] = True
        treppen_info.append((px0, px1, ye))
    # --- Waende: Meer/Feld (Eisklippe 24 px), Plateau/Feld (Eisklippe 40 px), Fronten + Seiten
    # Seiten (senkrechte Kanten): nur eine schmale Abgrenzung (Kontur + leichter Schatten), keine sichtbare
    # Seitenwand aus Kacheln (berg=False); Fronten bleiben Eisklippen
    waende = k4.hoehenkanten(a, m1, 'eis', 40, 14, LIPPE_SCHNEE, np.zeros((Hp, Wp), bool), 11, berg=False)
    waende |= k4.hoehenkanten(a, m2, 'eis', 64, 14, LIPPE_SCHNEE, frei_pl, 13, (), berg=False)
    km = spalte & (np.array(Image.fromarray((spalte * 255).astype(np.uint8)).resize((Wp, Hp))) > 0)
    km = weich(spalte.astype(np.float32), 3.0, 0.3, 26, 0.42)
    spalten_zeichnen(a, km)
    if speichern and frame is None:
        np.save(os.path.join(KARTE, 'waende.npy'), np.packbits(waende | km))
        lvl = np.ones((Hp, Wp), np.uint8)
        lvl[m2] = 2
        lvl[meer | loch] = 0
        lvl[waende] = 9
        lvl[km] = 8
        np.save(os.path.join(KARTE, 'pixelhoehe.npy'), lvl)
    wegtex = textur(cls, 'w', cols, rows)
    img = Image.fromarray(a).convert('RGBA')
    # Wasserfall (Stil Karte 01) ueber die Plateaufront, wo der Bach ueber die Kante faellt
    import klippen
    for (x0, x1) in lay.get('wasserfaelle', []):
        px0, px1 = x0 * T - 3, (x1 + 1) * T + 3
        ye = max(int(np.nonzero(m2[:, xc])[0].max()) for xc in range(px0 + 4, px1 - 4) if m2[:, xc].any())
        klippen.zeichne_wasserfall(img, px0, px1, ye - 4, ye + 70, frame=frame or 0)
    alt_S = bauwerke.S
    bauwerke.S = [H(c) + (255,) for c in k4.FELS['eis']]
    for (px0, px1, ye) in treppen_info:
        for y in range(ye - 12, ye + 1):
            for x in range(px0 + 4, px1 - 4):
                if (y - (ye - 12)) + min(x - px0 - 4, px1 - 5 - x) > 2:
                    img.putpixel((x, y), tuple(wegtex[y, x]) + (255,))
        bauwerke.zeichne_treppe(img, px0 - 6, px1 + 6, ye + 2, ye + 66)
    bauwerke.S = alt_S
    # --- Bruecken ueber die Spalten, Steg auf dem Eissee
    for (x0, y0, x1, y1) in lay.get('bruecken', []) + lay.get('stege', []):
        bauwerke.zeichne_bruecke(img, x0 * T - 4, (x1 + 1) * T + 4, y0 * T + 1, (y1 + 1) * T - 1,
                                 frame=frame or 0, seed=x0 * 7 + y0, wasser=False)
    a = np.array(img.convert('RGB'))
    for tp in lay.get('teleporter', []):
        k4.teleporter_zeichnen(a, tp['x'], tp['y'], tp['b'], tp['h'], frame)
    img = Image.fromarray(a).convert('RGBA')
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain_basis.png'))
    # --- Objekte
    pf = os.path.join(OBJ, 'platzierung.json')
    objs = []
    if os.path.exists(pf):
        objs = sorted((o for o in json.load(open(pf)) if os.path.exists(os.path.join(OBJ, o['datei']))),
                      key=lambda o: o['y'] + o['fuss'])
        cache = {o['datei']: Image.open(os.path.join(OBJ, o['datei'])).convert('RGBA') for o in objs}
        lvl = np.ones((Hp, Wp), np.uint8)
        lvl[m2] = 2
        lvl[meer | loch] = 0
        lvl[waende] = 9
        lvl[km] = 8
        schatten_k5(img, objs, cache, lvl)
        k4.objekte_zeichnen(img, objs, cache, np.zeros((Hp, Wp), bool), frame)
        k4.animieren(img, objs, cache, frame or 0)
    if frame is not None:
        schneefall(img, frame)
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain.png'))
    print('Karte 05 %dx%d gebaut' % (cols, rows))
    return img


if __name__ == '__main__':
    bauen()
