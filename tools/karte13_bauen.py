"""Karte 13 (Spiral Mountain: Machine City): zerstoerte Maschinenstadt. Ringsum dieselbe Bergwand wie Karte 11/12
(dunkelberg, 44 px Front), Strassenraster mit Mittellinie, Zebrastreifen und Bordsteinen, Gehwege und Hoefe aus
Betonplatten, verseuchter Boden, die Maschinenfestung eine Etage hoeher (Metallboden, Front aus Metallpaneelen mit
Warnstreifen und Leuchten, Metalltreppe) mit Gitterring und Boss-Kreis, Bahnhof mit Gitterrost.

  python3 tools/karte13_layout.py && python3 tools/karte13_kacheln.py
  python3 tools/karte13_bauen.py && python3 tools/karte13_objekte.py && python3 tools/regeln_v11.py karte13 \\
    && python3 tools/karte13_objekte.py symmetrie && python3 tools/karte13_bauen.py
"""
import json, math, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageFilter
import karte_bauen as kb
import karte04_bauen as k4
import karte08_bauen as k8
import bauwerke

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte13')
BASIS = os.path.join(ROOT, 'assets', 'karte13', 'basis')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte13')
T = 16
N_FRAMES = 16
H = k4.H
weich, zell_maske = k4.weich, k4.zell_maske
k4.FELS['dunkelberg'] = ['#12141c', '#1a1d28', '#242836', '#303546', '#3e4458', '#50586e', '#666e86']
k4.FELS['metall'] = ['#10161c', '#18222a', '#203038', '#2a3c46', '#364c58', '#46606e', '#5a7684']
LIPPE_BERG = ['#3c4050', '#4a4e60', '#585e70', '#686e80', '#7a8092', '#8c92a4']
FRONT = {2: 32, 5: 44}


def textur(art, cols, rows):
    t = np.zeros((rows * T, cols * T, 3), np.uint8)
    ks = [np.array(Image.open(os.path.join(BASIS, '%s_%d.png' % (art, v))).convert('RGB')) for v in range(5)]
    for y in range(rows):
        for x in range(cols):
            t[y * T:(y + 1) * T, x * T:(x + 1) * T] = ks[kb.variante(x, y)]
    return t


def kontur(m):
    return m & ~(np.roll(m, 1, 0) & np.roll(m, -1, 0) & np.roll(m, 1, 1) & np.roll(m, -1, 1))


def strasse(a, s, lay):
    """Asphalt: Bordstein an den Gehwegen (helle Kante, Schatten auf die Fahrbahn), gelbe Mittellinie der
    Hauptstrasse (gestrichelt, verblasst), Zebrastreifen an den Kreuzungen."""
    Hh, W = s.shape
    rand = ~s & (np.roll(s, 1, 0) | np.roll(s, -1, 0) | np.roll(s, 1, 1) | np.roll(s, -1, 1))
    a[rand] = H('#8a90a0')                                        # Bordsteinkante
    sch = s & (np.roll(~s, 1, 0) | np.roll(~s, 1, 1))
    a[sch] = (a[sch] * 0.72).astype(np.uint8)
    x0, x1 = lay['hauptstrasse']
    mx = (x0 + x1 + 1) * T // 2
    for y in range(0, Hh):
        if s[y, mx] and (y // 8) % 2 == 0:
            a[y, mx - 1:mx + 1] = H('#b8a040') if (y * 7) % 11 else H('#8a7a3a')
    for (zx0, zx1, zy, art) in lay.get('zebra', []):
        for y in range(zy * T, zy * T + 2 * T if art == 'q' else zy * T + 4 * T):
            for x in range(zx0 * T, (zx1 + 1) * T):
                if not s[y, x]:
                    continue
                if art == 'q' and (y % 6) < 3 and 3 <= (x - zx0 * T) % (4 * T) < 4 * T - 3:
                    a[y, x] = H('#c8ccd4')
                if art == 'l' and (x % 6) < 3 and 3 <= (y - zy * T) < 4 * T - 3:
                    a[y, x] = H('#c8ccd4')


def festung_front(a, fest, lay):
    """Suedfront der Maschinenfestung (32 px): Metallpaneele mit Fugen, Warnstreifen gelb/schwarz oben, rote
    Leuchten in festem Rhythmus, unten Kontaktschatten. Mittig eine Metalltreppe mit Gelaender."""
    Hh, W = fest.shape
    front = np.zeros_like(fest)
    F = 32
    sued = fest & ~np.roll(fest, -1, 0)
    tr = lay['treppen_sued'][0]
    tx0, tx1 = tr[0] * T, (tr[1] + 1) * T
    for y, x in zip(*np.nonzero(sued)):
        for d in range(F + 3):
            Y = y + 1 + d
            if Y >= Hh or fest[Y, x]:
                break
            if d >= F:
                a[Y, x] = (a[Y, x] * (0.6 if d == F else 0.8)).astype(np.uint8)
                continue
            front[Y, x] = True
            if tx0 <= x < tx1:
                continue
            c = np.array((44, 62, 74) if (x // 16) % 2 else (40, 56, 68), np.float32)
            if x % 16 == 15 or d in (12, 13):
                c = np.array((18, 26, 32), np.float32)
            if d < 4:                                           # Warnstreifen
                c = np.array((200, 160, 40), np.float32) if ((x + d) // 4) % 2 else np.array((30, 30, 34), np.float32)
            if d == 4:
                c = np.array((16, 20, 24), np.float32)
            c = c * (1 - 0.3 * d / F)
            a[Y, x] = np.clip(c, 0, 255).astype(np.uint8)
    # rote Leuchten alle 64 px
    xs_s = np.nonzero(sued.any(axis=0))[0]
    ys_s = int(np.nonzero(sued.any(axis=1))[0].max())
    for x in range(xs_s.min() + 24, xs_s.max() - 8, 64):
        if tx0 - 12 <= x <= tx1 + 4:
            continue
        a[ys_s + 18:ys_s + 22, x:x + 6] = H('#7a1c24')
        a[ys_s + 18:ys_s + 20, x + 1:x + 5] = H('#e04050')
    # Metalltreppe
    y0 = (tr[3] + 1) * T
    for d in range(F + 2):
        Y = y0 + d
        for x in range(tx0 - 3, tx1 + 3):
            if x < tx0 or x >= tx1:
                a[Y, x] = H('#1c262e') if x in (tx0 - 3, tx1 + 2) else H('#4a5c68')
            else:
                st = d % 6
                a[Y, x] = H('#7a8c98') if st == 0 else (H('#52626e') if st < 4 else H('#222c34'))
        front[Y, tx0 - 3:tx1 + 3] = False
    return front


def techkreis(a, cx, cy, r, frame):
    """Boss-Feld der Festung: technischer Kreis - Ringe in Cyan, rote Leiterbahnen zum Ring, ein Segmentring dreht
    sich, die Mitte pulsiert (wie der Bannkreis auf Karte 11/12, im Maschinenstil)."""
    f = frame or 0
    Hh, W = a.shape[:2]
    yy, xx = np.mgrid[0:Hh, 0:W]
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    ang = (np.arctan2(yy - cy, xx - cx) + math.pi) / (2 * math.pi)
    puls = 0.6 + 0.4 * math.sin(2 * math.pi * f / N_FRAMES)
    a[d <= r] = (a[d <= r] * 0.55).astype(np.uint8)
    cyan = np.array([60, 200, 220], np.float32)
    for rr, br in ((r - 2, 1.2), (r * 0.72, 1.0), (r * 0.3, 1.0)):
        m = np.abs(d - rr) <= br
        a[m] = np.clip(cyan * (0.7 + 0.3 * puls), 0, 255).astype(np.uint8)
    seg = (np.abs(d - r * 0.86) <= 2.2) & (((ang * 24 + f / N_FRAMES * 3) % 2) < 1)   # Segmentring dreht sich
    a[seg] = H('#2a8ca0')
    for k_ in range(8):                                          # Leiterbahnen
        w = 2 * math.pi * k_ / 8 + math.pi / 8
        for t in np.arange(r * 0.32, r * 0.7, 0.5):
            X, Y = int(cx + math.cos(w) * t), int(cy + math.sin(w) * t)
            a[Y, X] = H('#c03040')
        X, Y = int(cx + math.cos(w) * r * 0.7), int(cy + math.sin(w) * r * 0.7)
        a[Y - 1:Y + 2, X - 1:X + 2] = H('#ff6070')
    kern = d <= r * 0.18
    a[kern] = np.clip(np.array([200, 60, 70], np.float32) * (0.6 + 0.4 * puls), 0, 255).astype(np.uint8)


def bergkuppe(a, kuppe):
    """Bergkuppe: dicke schwarze Stromkabel und rostige Rohre laufen in Boegen ueber den Fels (zur Festung hin),
    dazu violette Kristalladern und oelige Flecken (Verseuchung). Nur auf der begehbaren Kuppe, nie auf Fronten."""
    Hh, W = kuppe.shape
    rs = random.Random(4)
    def linie(pts, breite, farbe, licht, schatten, glied=0):
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            n = int(max(abs(bx - ax), abs(by - ay))) + 1
            for t in range(n):
                x, y = ax + (bx - ax) * t / n, ay + (by - ay) * t / n
                for d in range(-(breite // 2), breite - breite // 2):
                    X, Y = int(x), int(y + d)
                    if 0 <= X < W and 0 <= Y < Hh and kuppe[Y, X]:
                        a[Y, X] = licht if d == -(breite // 2) else (schatten if d == breite - breite // 2 - 1 else farbe)
                    if 0 <= X < W and 0 <= Y + 1 < Hh and d == breite - breite // 2 - 1 and kuppe[Y + 1, X]:
                        a[Y + 1, X] = (a[Y + 1, X] * 0.7).astype(np.uint8)
                if glied and int(t) % glied == 0:
                    for d in range(-(breite // 2) - 1, breite - breite // 2 + 1):
                        X, Y = int(x), int(y + d)
                        if 0 <= X < W and 0 <= Y < Hh and kuppe[Y, X]:
                            a[Y, X] = H('#3a2416')
    def bogen(p0, p1, durchhang, n=24):
        return [(p0[0] + (p1[0] - p0[0]) * t / n, p0[1] + (p1[1] - p0[1]) * t / n + durchhang * math.sin(math.pi * t / n))
                for t in range(n + 1)]
    # Kabel oben entlang zur Festung (links und rechts), Kabel an den Seiten herab
    for (p0, p1, dh) in (((4, 22), (300, 14), 8), ((300, 14), (430, 30), 5), ((1275, 24), (1000, 12), 7), ((1000, 12), (860, 30), 5),
                         ((22, 1110), (22, 600), 0), ((1258, 1105), (1258, 520), 0)):
        pts = bogen(p0, p1, dh) if p0[0] != p1[0] else [(p0[0] + 3 * math.sin(t / 6.0), p0[1] + (p1[1] - p0[1]) * t / 40.0) for t in range(41)]
        linie(pts, 3, H('#1a1c22'), H('#4a4e5c'), H('#0c0d10'))
    # rostige Rohre (mit Muffen)
    for (p0, p1, dh) in (((40, 1090), (560, 1094), 3), ((700, 1094), (1240, 1088), 3), ((38, 300), (38, 60), 0)):
        pts = bogen(p0, p1, dh) if p0[0] != p1[0] else [(p0[0], p0[1] + (p1[1] - p0[1]) * t / 40.0) for t in range(41)]
        linie(pts, 5, H('#6a3e22'), H('#a0643a'), H('#3a2214'), glied=26)
    # Verseuchung: violette Kristalladern (Zickzack) und oelige Flecken
    ys, xs = np.nonzero(kuppe)
    for _ in range(26):
        i = rs.randrange(len(ys)); y, x = int(ys[i]), int(xs[i])
        for d in range(rs.randint(6, 14)):
            if 0 <= x < W and 0 <= y < Hh and kuppe[y, x]:
                a[y, x] = H('#8a5ac0') if d % 4 else H('#c8a0f0')
            x += rs.choice((-1, 1)); y += rs.choice((-1, 0, 1))
    for _ in range(14):
        i = rs.randrange(len(ys)); cy, cx = int(ys[i]), int(xs[i])
        rx, ry = rs.randint(4, 9), rs.randint(2, 4)
        for y in range(cy - ry, cy + ry + 1):
            for x in range(cx - rx, cx + rx + 1):
                if 0 <= x < W and 0 <= y < Hh and kuppe[y, x] and ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1:
                    a[y, x] = (a[y, x] * 0.45 + np.array([20, 16, 30]) * 0.55).astype(np.uint8)
        a[cy - 1, cx - rx // 2:cx] = H('#5a4a78')                  # Oelschimmer


def rotlicht(sp, frame, o):
    """Warnleuchten, Kameralinse, Mech-Auge: nur die roten Lichtpixel blinken langsam (an/ab), sonst nichts."""
    a = np.array(sp)
    ai = a.astype(int)
    rot = (ai[..., 3] > 0) & (ai[..., 0] > 150) & (ai[..., 0] > ai[..., 1] + 70) & (ai[..., 0] > ai[..., 2] + 60)
    an = 0.5 + 0.5 * math.sin(2 * math.pi * frame / N_FRAMES * 2 + o.get('x', 0) * 0.03)
    k_ = 0.55 + 0.6 * an
    a[rot, :3] = np.clip(ai[rot, :3] * k_, 0, 255).astype(np.uint8)
    return Image.fromarray(a)


k4.TEILANIM['rotlicht'] = rotlicht


def konsole(sp, frame, o):
    """Konsole: kleine bunte Lampen und Bildschirmpixel blinken in eigenem Takt; Gehaeuse bleibt ruhig."""
    a = np.array(sp)
    ai = a.astype(int)
    al = ai[..., 3] > 0
    mx = ai[..., :3].max(axis=2); mn = ai[..., :3].min(axis=2)
    bunt = al & (mx > 140) & (mx - mn > 70)
    ys, xs = np.nonzero(bunt)
    out = a.copy()
    for y, x in zip(ys, xs):
        t = (frame * 3 + x * 7 + y * 13) % 16
        if t < 5:
            out[y, x, :3] = (ai[y, x, :3] * 0.35).astype(np.uint8)
        elif t > 13:
            out[y, x, :3] = np.minimum(255, ai[y, x, :3] + 60).astype(np.uint8)
    return Image.fromarray(out)


def funken(sp, frame, o):
    """Wrack: aus gerissenen Kabeln sprueht es - einzelne gelb-weisse Funken flackern an wechselnden Stellen."""
    a = np.array(sp)
    ai = a.astype(int)
    al = ai[..., 3] > 0
    hell = al & (ai[..., 0] > 170) & (ai[..., 1] > 120)
    ys, xs = np.nonzero(hell)
    out = a.copy()
    out[hell, :3] = (ai[hell, :3] * 0.6).astype(np.uint8)
    rs = random.Random(frame * 31 + int(o.get('x', 0)))
    if len(ys):
        for _ in range(3):
            i = rs.randrange(len(ys)); y, x = ys[i], xs[i]
            for dy, dx in ((0, 0), (-1, 0), (0, 1), (-1, -1), (-2, 1)):
                Y, X = y + dy, x + dx
                if 0 <= Y < a.shape[0] and 0 <= X < a.shape[1] and rs.random() < 0.8:
                    out[Y, X] = (255, 240, 150, 255)
    return Image.fromarray(out)


def ampel_blinken(sp, frame, o):
    """Kaputte Ampel: nur die Lampen blinken gelb (halbe Zeit an), Mast und Gehaeuse ruhig."""
    a = np.array(sp)
    ai = a.astype(int)
    al = ai[..., 3] > 0
    lampe = al & (ai[..., 0] > 150) & (ai[..., 0] > ai[..., 2] + 50)
    out = a.copy()
    if (frame // 4) % 2:
        out[lampe, :3] = (ai[lampe, :3] * 0.35).astype(np.uint8)
    else:
        out[lampe, :3] = np.clip(np.array([240, 190, 60]) * 0.6 + ai[lampe, :3] * 0.4, 0, 255).astype(np.uint8)
    return Image.fromarray(out)


k4.TEILANIM.update({'konsole': konsole, 'funken': funken, 'ampel_blinken': ampel_blinken})


def _lichtpixel(ai):
    al = ai[..., 3] > 0
    mx = ai[..., :3].max(axis=2); mn = ai[..., :3].min(axis=2)
    return al & (mx > 150) & ((mx - mn > 55) | (mn > 200))


def pulsieren(sp, frame, o):
    """Echte Lichtquellen (Reaktorkern, Laternenglas, Kristall): die hellen, farbigen Pixel pulsieren weich."""
    a = np.array(sp)
    ai = a.astype(int)
    m = _lichtpixel(ai)
    k_ = 0.72 + 0.4 * (0.5 + 0.5 * math.sin(2 * math.pi * frame / N_FRAMES + o.get('x', 0) * 0.05))
    a[m, :3] = np.clip(ai[m, :3] * k_, 0, 255).astype(np.uint8)
    return Image.fromarray(a)


def blinken(sp, frame, o):
    """Kaputte Ampel / Warnlicht: die Lampenpixel sind abwechselnd an und aus."""
    a = np.array(sp)
    ai = a.astype(int)
    m = _lichtpixel(ai)
    if ((frame + int(o.get('x', 0)) // 16) // 4) % 2:
        a[m, :3] = (ai[m, :3] * 0.3).astype(np.uint8)
    return Image.fromarray(a)


k4.TEILANIM.update({'pulsieren': pulsieren, 'blinken': blinken})


def rauch(img, objs, frame):
    """Schornsteine: graue Woelkchen steigen genau aus der Oeffnung oben, wachsen, treiben nach rechts und verblassen."""
    from PIL import ImageDraw
    f = frame or 0
    lage = Image.new('RGBA', img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lage)
    for o in objs:
        if not o.get('rauch'):
            continue
        al = np.array(Image.open(os.path.join(OBJ, o['datei'])).getchannel('A')) > 0
        top = int(np.nonzero(al.any(axis=1))[0].min())
        xs = np.nonzero(al[top:top + 3].any(axis=0))[0]
        cx, cy = o['x'] + (xs.min() + xs.max()) / 2.0, o['y'] + top
        for k_ in range(5):
            t = ((f / N_FRAMES) + k_ / 5.0) % 1.0
            r = 2 + t * 6
            x, y = cx + t * 14 + math.sin(t * 6 + k_) * 1.5, cy - 3 - t * 34
            al_ = int(150 * (1 - t))
            d.ellipse((x - r, y - r, x + r, y + r), fill=(70, 70, 82, al_))
            d.ellipse((x - r * 0.6, y - r * 0.8, x + r * 0.3, y), fill=(110, 110, 124, int(al_ * 0.8)))
    img.alpha_composite(lage)


def giftbecken(a, m, frame):
    """Giftwasser im Laborbecken: der Laborboden bleibt sichtbar (Wasser halbdurchsichtig giftgruen, am Rand flacher
    und heller), Lichtnetz und Wellenlinien wandern, Blasen steigen auf und platzen; Beckenrand aus Metall mit
    gelb-schwarzem Warnstreifen, innen ein dunkler Wasserrand. Alles Bewegte nur innerhalb des Wassers."""
    f = frame or 0
    Hh, W = m.shape
    yy, xx = np.mgrid[0:Hh, 0:W]
    tief = np.array(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(5))) / 255.0
    boden = a[m].astype(np.float32)
    gruen = np.array([70, 196, 58], np.float32)
    al = (0.38 + 0.3 * tief[m])[:, None]                        # Mitte etwas tiefer -> etwas gruener
    farbe = boden * (1 - al) * np.array([0.5, 0.78, 0.5]) + gruen * al
    ph = 2 * math.pi * f / N_FRAMES
    netz = np.abs(np.sin(xx * 0.16 + np.sin(yy * 0.11 + ph) * 2.0) + np.sin(yy * 0.19 + np.sin(xx * 0.07 - ph) * 2.2))
    linie = (netz < 0.09)[m]
    farbe[linie] = farbe[linie] * 0.7 + np.array([200, 255, 150]) * 0.3
    a[m] = np.clip(farbe, 0, 255).astype(np.uint8)
    rand_in = m & ~(np.array(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(5))) > 0)
    a[rand_in] = (a[rand_in] * 0.75).astype(np.uint8)
    # Beckenrand: Metallkante mit Warnstreifen (2 px) direkt um das Wasser
    aussen = (np.array(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(7))) > 0) & ~m
    streifen = ((xx + yy) // 4) % 2 == 0
    a[aussen & streifen] = H('#d0a830')
    a[aussen & ~streifen] = H('#26282e')
    a[kontur(aussen | m) & aussen] = H('#4a5058')
    # Blasen
    rs = random.Random(13)
    ys, xs = np.nonzero(m & ~rand_in)
    for _ in range(max(3, len(ys) // 350)):
        i = rs.randrange(len(ys)); y, x = int(ys[i]), int(xs[i])
        t = (f / N_FRAMES + rs.random()) % 1.0
        if t < 0.55:
            r = 1 if t < 0.3 else 2
            for dy in range(-r, r + 1):
                for dx in range(-r, r + 1):
                    if abs(dx) + abs(dy) == r and m[y + dy, x + dx]:
                        a[y + dy, x + dx] = (210, 255, 170)
            a[y, x] = (150, 240, 120)
        elif t < 0.65:                                            # platzt: kleiner Spritzring
            for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2)):
                if m[y + dy, x + dx]:
                    a[y + dy, x + dx] = (190, 250, 160)


def bauen(frame=None, speichern=True):
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cols, rows = lay['groesse']
    cls = lay['klassen']
    hoehe = np.array([[int(c) for c in r] for r in lay['hoehe']])
    Wp, Hp = cols * T, rows * T
    a = textur('g', cols, rows)
    gift = weich(zell_maske(cls, 'n', cols, rows), 3.0, 0.4, 3)          # Giftwasser-Becken (aus den gruenen Flecken)
    labor = np.array(Image.fromarray((gift * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(25))) > 0
    for art, bl, rausch, seed in (('p', 4.0, 0.5, 9),):
        roh = zell_maske(cls, art, cols, rows)
        m = weich(roh, bl, rausch, seed)
        a[m] = textur(art, cols, rows)[m]
        k4.dunkeln(a, weich(roh, bl, rausch, seed, 0.36) & ~m, 0.86)
    for art in 'shmz':
        m = zell_maske(cls, art, cols, rows) > 0
        a[m] = textur(art, cols, rows)[m]
    labor &= ~(zell_maske(cls, 's', cols, rows) > 0)
    a[labor] = textur('l', cols, rows)[labor]                      # Laborboden um und unter dem Becken
    a[kontur(labor)] = H('#5a626c')
    giftbecken(a, gift, frame)
    s = zell_maske(cls, 's', cols, rows) > 0
    strasse(a, s, lay)
    # --- Ebenen: Festung (2), Berg (5)
    em = {}
    em[5] = weich(k8.stufe(hoehe, 5, cols, rows), 5, 0.3, 37)
    fest = (k8.stufe(hoehe, 2, cols, rows) > 0) & ~(k8.stufe(hoehe, 5, cols, rows) > 0)
    a[em[5]] = (textur('r', cols, rows)[em[5]] * np.array([0.56, 0.58, 0.66])).astype(np.uint8)
    a[kontur(fest)] = H('#5a7684')
    rand_f = fest & ~(np.array(Image.fromarray((fest * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(9))) > 0)
    a[rand_f & ~kontur(fest)] = (a[rand_f & ~kontur(fest)] * 0.7).astype(np.uint8)
    b = lay['boss']
    techkreis(a, b[0] * T, b[1] * T, 3.6 * T, frame)
    waende = k4.hoehenkanten(a, em[5], 'dunkelberg', FRONT[5], 12, LIPPE_BERG, np.zeros((Hp, Wp), bool), 35, berg=False)
    bergkuppe(a, em[5] & ~waende)
    lvl = np.ones((Hp, Wp), np.uint8)
    lvl[fest] = 2
    lvl[gift] = 0
    lvl[em[5]] = 5
    lvl[waende] = 9
    lvl[festung_front(a, fest, lay)] = 9
    tr = lay['treppen_sued'][0]
    lvl[(tr[3] + 1) * T:(tr[3] + 1) * T + 34, tr[0] * T - 3:(tr[1] + 1) * T + 3] = 9
    if speichern and frame is None:
        np.save(os.path.join(KARTE, 'pixelhoehe.npy'), lvl)
        np.save(os.path.join(KARTE, 'wasser.npy'), np.packbits(gift))
    for tp in lay.get('teleporter', []):
        k4.teleporter_zeichnen(a, tp['x'], tp['y'], tp['b'], tp['h'], frame)
    img = Image.fromarray(a).convert('RGBA')
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain_basis.png'))
    pf = os.path.join(OBJ, 'platzierung.json')
    if os.path.exists(pf):
        objs = sorted((o for o in json.load(open(pf)) if os.path.exists(os.path.join(OBJ, o['datei']))),
                      key=lambda o: (0 if o.get('an_wand') else 1, o['y'] + o['fuss']))
        cache = {o['datei']: Image.open(os.path.join(OBJ, o['datei'])).convert('RGBA') for o in objs}
        k8.schatten_ebene(img, [o for o in objs if not o.get('an_wand')], cache, lvl)
        vor_objekten = np.array(img)
        k4.objekte_zeichnen(img, objs, cache, np.zeros((Hp, Wp), bool), frame)
        k4.animieren(img, objs, cache, frame or 0, ruhig=frame is None)
        if frame is not None:
            rauch(img, objs, frame)
        k8.verdeckung(img, [o for o in objs if not o.get('an_wand')], cache, lvl, vor_objekten)
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain.png'))
    print('Karte 13 %dx%d gebaut' % (cols, rows))
    return img


if __name__ == '__main__':
    bauen()
