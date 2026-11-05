"""Schwarze Tuerme fuer Karte 07: schlanke, facettierte Obsidian-Tuerme (frontal, Licht oben links).

  python3 tools/karte07_tuerme.py

Erzeugt assets/objekte/karte07/turm/schwarz_{gross,klein,gefallen,stumpf}.png
Stehend: drei sichtbare Facetten (links im Licht, Mitte, rechts im Schatten) mit hellen Graten,
Pyramidenspitze, ausgestellter Fuss und Sockelplatte, Glanzreflexe.
Umgestuerzt: liegendes Prisma (Oberseite im Licht, Seitenflaeche dunkel), Bruchflaeche links,
Spitze rechts, Truemmer und Risse.
"""
import math, os, random
import numpy as np
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
ZIEL = os.path.join(ROOT, 'assets', 'objekte', 'karte07', 'turm')


def H(c):
    return np.array([int(c[i:i + 2], 16) for i in (1, 3, 5)], np.float32)


UMRISS = H('#08090d')
LICHT = (H('#3c4356'), H('#5a6480'))       # linke Facette unten -> oben
MITTE = (H('#20242f'), H('#323848'))
SCHATTEN = (H('#121419'), H('#1b1e27'))
GRAT_L = H('#8c96b2')
GRAT_R = H('#3a4052')
GLANZ = H('#a8b2cc')
FUGE = H('#0d0f14')
BRUCH = (H('#4a5064'), H('#6a7290'), H('#2a2e3a'))


def mix(a, b, t):
    return a * (1 - t) + b * t


def stehend(hoehe, breite, spitze=30, fuss=22, sockel=6, risse=(), seed=1, bruch_oben=0):
    rs = random.Random(seed)
    W = int(breite * 1.6) + 4
    img = np.zeros((hoehe, W, 4), np.float32)
    cx = W / 2.0
    schaft_oben, schaft_unten = breite * 0.30, breite * 0.42
    for y in range(hoehe):
        if y < spitze:
            hw = schaft_oben * y / spitze
        elif y < hoehe - fuss - sockel:
            t = (y - spitze) / max(1, hoehe - fuss - sockel - spitze)
            hw = schaft_oben + (schaft_unten - schaft_oben) * t
        elif y < hoehe - sockel:
            t = (y - (hoehe - fuss - sockel)) / fuss
            hw = schaft_unten + breite * 0.28 * t ** 1.4
        else:
            hw = schaft_unten + breite * 0.28 + 2
        if hw < 0.5:
            hw = 0.5
        hoehe_t = 1 - y / hoehe                                   # oben heller
        g1, g2 = cx - 0.42 * hw, cx + 0.48 * hw                   # Grate
        for x in range(int(cx - hw), int(math.ceil(cx + hw)) + 1):
            if not 0 <= x < W:
                continue
            px = x + 0.5
            if px < cx - hw - 0.5 or px > cx + hw + 0.5:
                continue
            if y >= hoehe - sockel:                               # Sockelplatte
                c = mix(MITTE[0], LICHT[0], 0.6) if y == hoehe - sockel else MITTE[0] if px < cx else SCHATTEN[0]
                if y == hoehe - sockel + 1:
                    c = GRAT_L
            elif px < g1:
                c = mix(LICHT[0], LICHT[1], hoehe_t)
            elif px < g2:
                c = mix(MITTE[0], MITTE[1], hoehe_t)
                # weicher Reflex auf der Mittelfacette
                r = max(0.0, 1 - abs((px - (g1 + (g2 - g1) * 0.3)) / max(1.0, (g2 - g1) * 0.25)))
                c = mix(c, LICHT[0], 0.35 * r * hoehe_t)
            else:
                c = mix(SCHATTEN[0], SCHATTEN[1], hoehe_t)
            if abs(px - g1) < 0.75 and y < hoehe - sockel:
                c = GRAT_L if y < hoehe - fuss - sockel else mix(GRAT_L, LICHT[0], 0.4)
            elif abs(px - g2) < 0.75 and y < hoehe - sockel:
                c = GRAT_R
            img[y, x, :3] = c
            img[y, x, 3] = 255
    # Umriss
    a = img[..., 3] > 0
    rand = a & ~(np.roll(a, 1, 0) & np.roll(a, -1, 0) & np.roll(a, 1, 1) & np.roll(a, -1, 1))
    img[rand, :3] = UMRISS
    # Glanzlicht an der Spitze, schraege Glanzstreifen auf der Lichtfacette
    for y in range(3, spitze):
        x = int(cx - 0.42 * schaft_oben * y / spitze) - 1
        if 0 <= x < W and img[y, x, 3]:
            img[y, x, :3] = GLANZ
    for y0 in range(spitze + 12, hoehe - fuss - sockel - 8, 34):
        for i in range(7):
            y = y0 + i
            hw = schaft_oben + (schaft_unten - schaft_oben) * (y - spitze) / max(1, hoehe - fuss - sockel - spitze)
            x = int(cx - hw + 2 + i * 0.5)
            if img[y, x, 3] and x < cx - 0.42 * hw:
                img[y, x, :3] = mix(img[y, x, :3], GLANZ, 0.6)
    # Segmentfugen
    for yf in range(spitze + 28, hoehe - fuss - sockel - 4, 38):
        for x in range(W):
            if img[yf, x, 3] and not rand[yf, x]:
                img[yf, x, :3] = FUGE
                if yf + 1 < hoehe and img[yf + 1, x, 3] and x < cx:
                    img[yf + 1, x, :3] = mix(img[yf + 1, x, :3], GRAT_L, 0.4)
    for (y0, dx, n) in risse:
        x, y = cx + dx, y0
        for i in range(n):
            xi = int(x)
            if 0 <= y < hoehe and img[y, xi, 3]:
                img[y, xi, :3] = FUGE
            y += 1
            x += rs.choice((-0.6, 0, 0.6))
    if bruch_oben:                                                # abgebrochener Stumpf
        for x in range(W):
            z = int(bruch_oben + 3 * math.sin(x * 0.33) + 2 * abs(math.sin(x * 0.9)))
            img[:z, x, 3] = 0
            ys = np.nonzero(img[:, x, 3])[0]
            if len(ys):
                for k, c in enumerate((BRUCH[1], BRUCH[0], BRUCH[2])):
                    if ys.min() + k < hoehe:
                        img[ys.min() + k, x, :3] = c
        a = img[..., 3] > 0
        rand = a & ~(np.roll(a, 1, 1) & np.roll(a, -1, 1))
        img[rand, :3] = UMRISS
    out = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), 'RGBA')
    return out.crop(out.getbbox())


def gefallen(laenge=168, dicke=42, seed=4, ganz=False):
    """Liegender Turm von schraeg oben/frontal: Oberseite (Licht) und Seitenflaeche (Schatten) als zwei Baender,
    nach rechts verjuengt mit Spitze, links gezackte Bruchflaeche, Truemmer davor."""
    rs = random.Random(seed)
    top_h, seite_h = int(dicke * 0.45), int(dicke * 0.55)
    Hh = int((top_h + seite_h) * 1.6) + 14
    W = laenge + 30
    img = np.zeros((Hh, W, 4), np.float32)
    x0 = 18                                                      # Bruchkante
    spitze_l = 34
    mitte_y = 4 + int(top_h * 1.6)                                          # Grat zwischen Ober- und Seitenflaeche
    for x in range(x0, x0 + laenge):
        t = (x - x0) / laenge
        s = 1.0 - 0.22 * t                                       # leichte Verjuengung
        if ganz and x - x0 < 26:                                 # ausgestellter Fuss links
            s *= 1 + 0.55 * (1 - (x - x0) / 26) ** 1.4
        if x > x0 + laenge - spitze_l:
            s *= (x0 + laenge - x) / spitze_l
        th, sh = top_h * s, seite_h * s
        for y in range(Hh):
            d = y - mitte_y
            if -th <= d < 0:
                u = -d / max(1, th)                              # 0 am Grat .. 1 oben
                c = mix(LICHT[1], LICHT[0], u * 0.8)
                if d >= -1.2:
                    c = GRAT_L
            elif 0 <= d < sh:
                u = d / max(1, sh)
                c = mix(MITTE[1], SCHATTEN[0], u)
                if abs(d - sh * 0.5) < 0.6:
                    c = GRAT_R                                   # zweiter Grat der Seitenflaeche
            else:
                continue
            img[y, x, :3] = c
            img[y, x, 3] = 255
    # Segmentfugen (senkrecht) und Glanz auf der Oberseite
    for xf in range(x0 + 30, x0 + laenge - spitze_l, 36):
        for y in range(Hh):
            if img[y, xf, 3]:
                img[y, xf, :3] = FUGE
                if xf + 1 < W and img[y, xf + 1, 3] and y < mitte_y:
                    img[y, xf + 1, :3] = mix(img[y, xf + 1, :3], GRAT_L, 0.5)
    for x in range(x0 + 6, x0 + laenge - spitze_l):
        y = mitte_y - int(top_h * 0.6)
        if img[y, x, 3] and (x // 14) % 3 != 2:
            img[y, x, :3] = mix(img[y, x, :3], GLANZ, 0.45)
    if ganz:                                                     # Sockelplatte senkrecht links
        for y in range(Hh):
            if img[y, x0, 3]:
                for x in range(x0 - 5, x0 + 1):
                    img[y, x, :3] = LICHT[1] if x == x0 - 5 else MITTE[0] if y < mitte_y else SCHATTEN[0]
                    img[y, x, 3] = 255
    # Bruchkante links: grob gezackt in den Koerper geschnitten, heller rauer Saum an der Bruchflaeche
    if not ganz:
        ys = [y for y in range(Hh) if img[y, x0:x0 + 40, 3].any()]
        zacken = [rs.randint(0, 14) for _ in range(len(ys) // 4 + 2)]
        for i, y in enumerate(ys):
            k = i / 4.0
            j = int(k)
            z = int(zacken[j] + (zacken[j + 1] - zacken[j]) * (k - j))
            img[y, :x0 + z, 3] = 0
            for d in range(4):
                x = x0 + z + d
                img[y, x, :3] = (BRUCH[1] if d == 1 else BRUCH[0] if d in (0, 2) else BRUCH[2]) if rs.random() > 0.15 else BRUCH[2]
                img[y, x, 3] = 255
    # Abplatzer an Ober- und Unterkante
    for _ in range(5):
        cx_ = rs.randint(x0 + 25, x0 + laenge - spitze_l - 5)
        oben = rs.random() < 0.6
        r = rs.randint(2, 4)
        col = img[:, cx_, 3] > 0
        yy = np.nonzero(col)[0]
        if not len(yy):
            continue
        ye = yy.min() if oben else yy.max()
        for dx in range(-r, r + 1):
            for dy in range(r - abs(dx)):
                y = ye + dy if oben else ye - dy
                img[y, cx_ + dx, 3] = 0
    # Risse
    for _ in range(3):
        x, y = rs.randint(x0 + 20, x0 + laenge - 50), mitte_y - rs.randint(1, top_h - 1)
        for i in range(rs.randint(5, 9)):
            if 0 <= y < Hh and img[y, x, 3]:
                img[y, x, :3] = FUGE
            x += 1
            y += rs.choice((-1, 0, 1))
    a = img[..., 3] > 0
    rand = a & ~(np.roll(a, 1, 0) & np.roll(a, -1, 0) & np.roll(a, 1, 1) & np.roll(a, -1, 1))
    img[rand, :3] = UMRISS
    # Truemmer: kleine Obsidianbrocken (Oberseite hell, Unterseite dunkel) vor der Bruchkante und unten
    for _ in range(9):
        bx = rs.randint(0, x0 + 16) if rs.random() < 0.7 else rs.randint(x0 + 20, x0 + laenge - 40)
        by = rs.randint(mitte_y + seite_h - 6, mitte_y + seite_h + 2)
        s = rs.randint(2, 4)
        for yy in range(by, by + s):
            for xx in range(bx, bx + s + 1):
                if 0 <= yy < Hh and 0 <= xx < W and not img[yy, xx, 3]:
                    img[yy, xx, :3] = LICHT[1] if yy == by else UMRISS if yy == by + s - 1 else MITTE[0]
                    img[yy, xx, 3] = 255
    # in den Boden gedrueckt: Erdschollen entlang der Unterkante
    ERDE = (H('#4a3624'), H('#6a4e32'), H('#8a6a44'))
    for x in range(0, W):
        col = np.nonzero(img[:, x, 3])[0]
        if not len(col) or x % 3 == 2 and rs.random() < 0.5:
            continue
        yb = col.max()
        h = rs.choice((1, 2, 2, 3))
        for d in range(h):
            y = yb - d
            if y >= 0:
                img[y, x, :3] = ERDE[2] if d == h - 1 else ERDE[1] if d else ERDE[0]
    # grosse Obsidianbrocken an der Bruchstelle
    for (bx, by, s) in ((rs.randint(0, 6), mitte_y + rs.randint(0, 6), 7), (rs.randint(4, 12), mitte_y + seite_h - 2, 5)):
        for yy in range(by, by + s):
            for xx in range(bx + (yy - by) // 2, bx + s + 2 - (yy - by) // 3):
                if 0 <= yy < Hh and 0 <= xx < W:
                    img[yy, xx, :3] = LICHT[1] if yy == by else GRAT_L if xx == bx + (yy - by) // 2 else UMRISS if yy == by + s - 1 else MITTE[1]
                    img[yy, xx, 3] = 255
    out = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), 'RGBA')
    return out.crop(out.getbbox())


if __name__ == '__main__':
    os.makedirs(ZIEL, exist_ok=True)
    stehend(190, 40).save(os.path.join(ZIEL, 'schwarz_gross.png'))
    stehend(140, 32, spitze=24, fuss=18, seed=2).save(os.path.join(ZIEL, 'schwarz_klein.png'))
    gefallen().save(os.path.join(ZIEL, 'schwarz_gefallen.png'))
    gefallen(ganz=True, seed=6).save(os.path.join(ZIEL, 'schwarz_gefallen_ganz.png'))
    s = stehend(190, 40, seed=3)
    s.crop((0, s.height - 50, s.width, s.height)).save(os.path.join(ZIEL, '_tmp.png'))
    st = stehend(190, 40, seed=3, bruch_oben=140)
    st.save(os.path.join(ZIEL, 'schwarz_stumpf.png'))
    os.remove(os.path.join(ZIEL, '_tmp.png'))
    for n in ('gross', 'klein', 'gefallen', 'gefallen_ganz', 'stumpf'):
        print(n, Image.open(os.path.join(ZIEL, 'schwarz_%s.png' % n)).size)
