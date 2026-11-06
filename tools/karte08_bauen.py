"""Karte 08 (Overdell): Friedhof links und unten, Terrassenberg in der Mitte (Treppen abwechselnd links/rechts),
Schloss oben, Sumpf mit Bruecke, ringsum schwarzer Fels. Baut auf den Bausteinen von Karte 04/05 auf.

  python3 tools/karte08_layout.py && python3 tools/karte08_kacheln.py
  python3 tools/karte08_objekte.py && python3 tools/karte08_bauen.py   -> maps/karte08/terrain.png

Ebenen: 1 Friedhof, 2-5 Terrassen, 6 Schlossplateau, 7 schwarzer Fels. Licht oben links, Schatten nur auf der
eigenen Ebene, Objekte auf tieferem Boden werden vom seitlich hoeheren Fels abgeschnitten.
"""
import json, math, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageFilter
import karte_bauen as kb
import karte04_bauen as k4
import bauwerke

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte08')
BASIS8 = os.path.join(ROOT, 'assets', 'karte08', 'basis')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte08')
T = 16
N_FRAMES = 16
H = k4.H
weich, zell_maske = k4.weich, k4.zell_maske

k4.FELS['nacht'] = ['#08080e', '#101018', '#181824', '#222232', '#2e2e42', '#3c3c54', '#4e4e6a']
k4.FELS['terrasse'] = ['#16161f', '#22222e', '#30303e', '#40404f', '#525264', '#66667a', '#7e7e94']
LIPPE_TERRASSE = ['#3a3e4a', '#4a4f5c', '#5a606e', '#6a707e', '#7c8290', '#8e94a2']
LIPPE_FELS = ['#14141e', '#1c1c28', '#262634', '#30303f', '#3c3c4e', '#4a4a5e']
FRONT = {2: 32, 3: 32, 4: 32, 5: 32, 6: 32, 7: 44}


def textur(cls, art, cols, rows):
    t = np.zeros((rows * T, cols * T, 3), np.uint8)
    ks = [np.array(Image.open(os.path.join(BASIS8, '%s_%d.png' % (art, v))).convert('RGB')) for v in range(5)]
    for y in range(rows):
        for x in range(cols):
            t[y * T:(y + 1) * T, x * T:(x + 1) * T] = ks[kb.variante(x, y)]
    return t


def stufe(hoehe, n, cols, rows):
    return zell_maske([''.join('1' if v >= n else '0' for v in r) for r in hoehe], '1', cols, rows)


def ebenen_masken(hoehe, cols, rows):
    """Pixelmasken je Ebene (>= n), weich und ineinander geschachtelt."""
    m = {}
    for n in range(7, 1, -1):
        r = (0.18, 22 + n) if n < 7 else (0.34, 40)
        mn = weich(stufe(hoehe, n, cols, rows), 5 if n < 7 else 6, r[0], r[1])
        if n + 1 in m:
            mn |= m[n + 1]
        m[n] = mn
    return m


def fels_variation(a, m, cls, cols, rows):
    """Schwarzer Fels lebendiger: helle Geroellfelder, dunkle Moosflecken, Risse mit Lichtkante (Licht oben links)."""
    Hh, W = m.shape
    for art, seed, schwelle in (('R', 51, 0.62), ('M', 52, 0.68)):
        n = np.random.RandomState(seed).rand(Hh // 40 + 2, W // 40 + 2)
        n = np.array(Image.fromarray((n * 255).astype(np.uint8)).resize((W + 80, Hh + 80), Image.BICUBIC))[:Hh, :W] / 255.0
        f = np.random.RandomState(seed + 9).rand(Hh // 10 + 2, W // 10 + 2)
        f = np.array(Image.fromarray((f * 255).astype(np.uint8)).resize((W + 20, Hh + 20), Image.BICUBIC))[:Hh, :W] / 255.0
        fleck = m & (n * 0.8 + f * 0.2 > schwelle)
        fleck = np.array(Image.fromarray((fleck * 255).astype(np.uint8)).filter(ImageFilter.ModeFilter(5))) > 0
        fleck &= m
        tx = textur(cls, art, cols, rows)
        a[fleck] = tx[fleck]
        rand = fleck & ~(np.roll(fleck, 1, 0) & np.roll(fleck, -1, 0) & np.roll(fleck, 1, 1) & np.roll(fleck, -1, 1))
        a[rand] = (a[rand] * 0.82).astype(np.uint8)
    rs = random.Random(53)
    ys, xs = np.nonzero(m)
    for _ in range(len(ys) // 2600):                       # Risse
        i = rs.randrange(len(ys)); y, x = float(ys[i]), float(xs[i])
        w = rs.uniform(0, 6.28)
        for _k in range(rs.randint(8, 22)):
            w += rs.uniform(-0.7, 0.7)
            y += math.sin(w); x += math.cos(w)
            yi, xi = int(y), int(x)
            if not (1 <= yi < Hh - 1 and 1 <= xi < W - 1) or not m[yi, xi]:
                break
            a[yi, xi] = H('#0a0a10')
            if m[yi + 1, xi + 1]:
                a[yi + 1, xi + 1] = H('#3c3c52')


def sumpf_zeichnen(a, m, frame):
    """Sumpfwasser: Wasser aus Karte 01, trueb dunkelgruen getoent, mit Entengruetze-Flecken."""
    k4.wasser_zeichnen(a, m, frame, np.zeros_like(m))
    a[m] = np.clip(a[m] * np.array([0.3, 0.42, 0.32]) + np.array([14, 30, 26]), 0, 255).astype(np.uint8)


def entengruetze(a, m, frame):
    """Kleine Gruenflecken auf der Oberflaeche (treiben langsam)."""
    rs = random.Random(9)
    ys, xs = np.nonzero(m)
    if not len(ys):
        return
    for _ in range(len(ys) // 700):
        i = rs.randrange(len(ys)); cy, cx = ys[i], xs[i] + ((frame or 0) // 4) % 2
        for dy in range(-1, 2):
            for dx in range(-2, 3):
                y, x = cy + dy, cx + dx
                if 0 <= y < m.shape[0] and 0 <= x < m.shape[1] and m[y, x] and abs(dx) + abs(dy) < 3 and rs.random() < 0.8:
                    a[y, x] = H('#5a7a3a') if dy < 0 else H('#465f2e')


def schatten_ebene(img, objs, cache, lvl, farbe=(26, 20, 40)):
    """Kontakt- und Schlagschatten wie Karte 05, je Objekt nur auf seiner eigenen Ebene (Regel 7);
    liegende Objekte werfen einen flachen Schatten ihrer ganzen Form."""
    Hh, W = lvl.shape
    sch = np.zeros((Hh, W), np.uint8)
    for o in objs:
        if o.get('kein_schatten'):
            continue
        sp = cache[o['datei']]
        a = np.array(sp.getchannel('A')) >= 200
        if not a.any():
            continue
        if o.get('liegend'):
            ys_, xs_ = np.nonzero(a)
            fy_ = min(Hh - 1, max(0, o['y'] + int(ys_.max()) + 1)); fx_ = min(W - 1, max(0, o['x'] + int(xs_.mean())))
            eb = lvl[fy_, fx_]
            for dx_, dy_, wert in ((2, 2, 60), (1, 1, 72)):
                Y = o['y'] + ys_ + dy_; X = o['x'] + xs_ + dx_
                ok = (Y >= 0) & (Y < Hh) & (X >= 0) & (X < W)
                Y, X = Y[ok], X[ok]
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
        if ebene < 1 or ebene > 7:
            continue
        X0, Y0 = o['x'] - 2, o['y']
        bw = sp.width + int(hoehe_ * 0.5) + 8
        bh = zu + int(hoehe_ * 0.3) + 8
        teil = np.zeros((bh, bw), np.float32)
        wurf = np.zeros((bh, bw), np.float32)
        fx0, fx1 = int(fuss.min()) + 2, int(fuss.max()) + 2
        for yy in range(zu - 1, min(bh, zu + 3)):
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
        y0, y1 = max(0, Y0), min(Hh, Y0 + bh)
        x0, x1 = max(0, X0), min(W, X0 + bw)
        if y1 <= y0 or x1 <= x0:
            continue
        t = teil[y0 - Y0:y1 - Y0, x0 - X0:x1 - X0]
        t[lvl[y0:y1, x0:x1] != ebene] = 0
        sch[y0:y1, x0:x1] = np.maximum(sch[y0:y1, x0:x1], t.astype(np.uint8))
    dunkel = Image.new('RGBA', img.size, farbe + (255,))
    dunkel.putalpha(Image.fromarray(sch))
    img.alpha_composite(dunkel)


def verdeckung(img, objs, cache, lvl, grund):
    """Verdeckung durch Hoehen: steht ein Objekt neben hoeherem Gelaende (oder dessen Wand), das in dieser
    Spalte bis auf Fusshoehe herunterreicht, schneidet der Fels das Objekt ab. Liegt die Klippe hinter dem
    Objekt (Norden), bleibt es davor sichtbar."""
    Hh, W = lvl.shape
    a = np.array(img)
    for o in objs:
        if o.get('keine_verdeckung'):
            continue
        sp = cache[o['datei']]
        al = np.array(sp.getchannel('A')) > 0
        ys, xs = np.nonzero(al)
        if not len(ys):
            continue
        fy = min(Hh - 1, max(0, o['y'] + int(ys.max())))
        fx = min(W - 1, max(0, o['x'] + int(xs.mean())))
        eb = lvl[min(Hh - 1, fy + 1), fx]
        if eb > 7:
            continue
        hoch = (lvl > eb) & (lvl <= 7) | (lvl == 9)
        Y, X = ys + o['y'], xs + o['x']
        ok = (Y >= 0) & (Y < Hh) & (X >= 0) & (X < W)
        Y, X = Y[ok], X[ok]
        seitlich = hoch[np.clip(fy - 2, 0, Hh - 1), X]
        m = seitlich & hoch[Y, X]
        if m.any():
            a[Y[m], X[m]] = grund[Y[m], X[m]]
    img.paste(Image.fromarray(a))


def bauen(frame=None, speichern=True):
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cols, rows = lay['groesse']
    cls = lay['klassen']
    hoehe = np.array([[int(c) for c in r] for r in lay['hoehe']])
    Wp, Hp = cols * T, rows * T
    a = textur(cls, 'g', cols, rows)
    # --- weiche Bodenarten auf dem Friedhof
    for art, blur, rausch, seed in (('h', 6.0, 0.45, 3), ('e', 3.0, 0.2, 4), ('m', 5.0, 0.45, 5),
                                    ('w', 4.0, 0.42, 6), ('q', 3.5, 0.3, 7)):
        roh = zell_maske(cls, art, cols, rows)
        m = weich(roh, blur, rausch, seed)
        tx = textur(cls, art, cols, rows)
        a[m] = tx[m]
        saum = weich(roh, blur, rausch, seed, 0.38) & ~m
        k4.dunkeln(a, saum, 0.9)
    # --- Ebenen
    em = ebenen_masken(hoehe, cols, rows)
    berg = em[2] & ~em[7]
    tx = textur(cls, 'f', cols, rows)
    a[berg] = tx[berg]
    am = weich(zell_maske(cls, 'a', cols, rows), 4.5, 0.4, 11) & berg
    tx = textur(cls, 'a', cols, rows)
    a[am] = tx[am]
    km = zell_maske(cls, 'k', cols, rows) > 0
    km &= berg
    tx = textur(cls, 'k', cols, rows)
    a[km] = tx[km]
    tx = textur(cls, 'r', cols, rows)
    a[em[7]] = tx[em[7]]
    fels_variation(a, em[7], cls, cols, rows)
    # --- Sumpf (vertieft wie Karte 01, Schlammrand)
    sumpf = weich(zell_maske(cls, 'x', cols, rows), 9, 0.2, 24, 0.45) & ~em[2]
    sumpf = k4.splitter_weg(sumpf, 200)
    sumpf_zeichnen(a, sumpf, frame)
    import wasser_vertieft, wasser_details
    wasser_details.FELSEN_PROTOKOLL.clear()
    wasser_details.SPITZEN.clear()
    meiden = np.zeros((Hp, Wp), bool)
    for (x0, y0, x1, y1) in lay.get('bruecken', []):
        meiden[y0 * T - 14:(y1 + 1) * T + 14, x0 * T - 8:(x1 + 1) * T + 8] = True
    a = np.array(wasser_vertieft.vertiefen(Image.fromarray(a), np.ones_like(sumpf), frame, maske=sumpf, meiden=meiden,
                                           rand=('#241e16', '#30281c', '#3c3224', '#4a3e2e'),
                                           stufen=[(22, 0.78, 7), (46, 0.6, 6)]).convert('RGB'))
    # Sumpf: alles (Grund, Stufen, Ufermauer, Felsen) trueb dunkelgruen einfaerben
    lum = (a[sumpf].astype(np.float32) @ np.array([0.3, 0.59, 0.11], np.float32))[:, None]
    a[sumpf] = np.clip(lum * np.array([0.62, 0.86, 0.7]) + np.array([4, 12, 10]), 0, 255).astype(np.uint8)
    entengruetze(a, sumpf, frame)
    # --- Treppen: Front der oberen Ebene bleibt dort offen
    treppen_info = []
    frei = np.zeros((Hp, Wp), bool)
    for (x0, x1, e) in lay.get('treppen', []):
        px0, px1 = x0 * T + 1, (x1 + 1) * T - 1
        oben = em[e][:60 * T]                                     # nur der Berg, nicht der Fels am Kartenrand
        ye = max(int(np.nonzero(oben[:, xc])[0].max()) for xc in range(px0, px1) if oben[:, xc].any())
        f = FRONT[e]
        frei[ye - 14:ye + f + 8, px0 - 6:px1 + 6] = True
        treppen_info.append((px0, px1, ye, f, e))
    # --- Waende: jede Ebene zeichnet ihre Front (Sueden) und schmale Seitenkanten in die tiefere Flaeche
    waende = np.zeros((Hp, Wp), bool)
    for e in range(2, 8):
        fels, lippe = ('nacht', LIPPE_FELS) if e == 7 else ('terrasse', LIPPE_TERRASSE)
        waende |= k4.hoehenkanten(a, em[e], fels, FRONT[e], 12, lippe, frei, 30 + e, berg=False)
    lvl = np.ones((Hp, Wp), np.uint8)
    for e in range(2, 8):
        lvl[em[e]] = e
    lvl[sumpf] = 0
    lvl[waende] = 9
    if speichern and frame is None:
        np.save(os.path.join(KARTE, 'pixelhoehe.npy'), lvl)
    img = Image.fromarray(a).convert('RGBA')
    wegtex = textur(cls, 'a', cols, rows)
    alt_S = bauwerke.S
    bauwerke.S = [H(c) + (255,) for c in k4.FELS['terrasse']]
    for (px0, px1, ye, f, e) in treppen_info:
        for y in range(ye - 12, ye + 1):                         # Wegstueck oben auf der Terrasse
            for x in range(px0 + 4, px1 - 4):
                if (y - (ye - 12)) + min(x - px0 - 4, px1 - 5 - x) > 2:
                    img.putpixel((x, y), tuple(wegtex[y, x]) + (255,))
        bauwerke.zeichne_treppe(img, px0 - 6, px1 + 6, ye + 2, ye + f + 2)
        for y in range(ye + 1, ye + f + 3):
            for x in range(px0 - 6, px1 + 6):
                lvl[min(Hp - 1, y), x] = 9
    bauwerke.S = alt_S
    for (x0, y0, x1, y1) in lay.get('bruecken', []):
        vorher = np.array(img)
        bauwerke.zeichne_bruecke(img, x0 * T - 6, (x1 + 1) * T + 6, y0 * T + 1, (y1 + 1) * T - 1,
                                 frame=frame or 0, seed=x0 * 7 + y0, wasser=True)
        nachher = np.array(img)
        neu_ = (nachher != vorher).any(axis=2)                 # altes, verwittertes Holz: dunkler, entsaettigt
        p_ = nachher[neu_][:, :3].astype(np.float32)
        grau = p_.mean(axis=1, keepdims=True)
        nachher[neu_, :3] = np.clip((p_ * 0.55 + grau * 0.45) * np.array([0.72, 0.66, 0.66]), 0, 255).astype(np.uint8)
        img = Image.fromarray(nachher)
    a = np.array(img.convert('RGB'))
    for tp in lay.get('teleporter', []):
        k4.teleporter_zeichnen(a, tp['x'], tp['y'], tp['b'], tp['h'], frame)
    img = Image.fromarray(a).convert('RGBA')
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain_basis.png'))
    # --- Objekte
    pf = os.path.join(OBJ, 'platzierung.json')
    if os.path.exists(pf):
        objs = sorted((o for o in json.load(open(pf)) if os.path.exists(os.path.join(OBJ, o['datei']))),
                      key=lambda o: o['y'] + o['fuss'])
        cache = {o['datei']: Image.open(os.path.join(OBJ, o['datei'])).convert('RGBA') for o in objs}
        schatten_ebene(img, objs, cache, lvl)
        vor_objekten = np.array(img)
        k4.objekte_zeichnen(img, objs, cache, np.zeros((Hp, Wp), bool), frame)
        k4.animieren(img, objs, cache, frame or 0, ruhig=frame is None)
        verdeckung(img, objs, cache, lvl, vor_objekten)
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain.png'))
    print('Karte 08 %dx%d gebaut' % (cols, rows))
    return img


if __name__ == '__main__':
    bauen()
