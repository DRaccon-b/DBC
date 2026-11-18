"""Karte 56 (Golden Digimentals): drei Raeume mit Baumguertel (wie Karte 55/35), ohne Animation (folgt am Ende).

  1  Blumenwiese mit See: Sommerwiese (Graskacheln, hell), Blumenfelder mit gestempelten PixelLab-Blumen (flach,
     begehbar), vertiefter See mit Grasufer (wasser_vertieft, 45-Grad-Raster).
  2  Verzerrte Landschaft: exakt dieselbe Wiese wie Raum 1 (gleicher See, gleiche Blumenfelder), dann verfaelscht:
     Farben ins Violett gekippt, Glitch-Zeilen (verschobene Pixelstreifen), Risse ins Nichts mit Magenta-Rand.
  3  Cherubimons Inneres: Membranboden aus Karte 54 ins dunkle Violett umgefaerbt (Adern, Zellwaende), vier Abgruende.
Guertel: Raum 1 Wiese dunkel, Raum 2 verfaelscht, Raum 3 dunkle Membran; digitaler Nebel nur ganz aussen.

  python3 tools/karte56_layout.py && python3 tools/karte56_bauen.py
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageFilter
import karte04_bauen as k4
import karte06_bauen as k6
import karte16_bauen as k16
import karte17_bauen as k17
import karte20_bauen as k20
import karte35_bauen as k35
import karte54_bauen as k54
import wasser_vertieft

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte56')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte56')
T = 16
N_FRAMES = 4
H = k4.H
k4.RASTER45 = True
VIOLETT_LO, VIOLETT_HI = np.array((44, 18, 78), np.float32), np.array((214, 138, 236), np.float32)


def faerben(lo, hi, a0=0.35, a1=0.5):
    def f(a):
        l = a.mean(axis=2, keepdims=True) / 255.0
        return np.array(lo, np.float32) + (np.array(hi, np.float32) - np.array(lo, np.float32)) * np.clip((l - a0) / a1, 0, 1)
    return f


def texturen(cols, rows):
    gras = os.path.join(ROOT, 'assets', 'basis', 'gras_%d.png')
    return {
        'wiese': k20.flaeche(k6.kacheln(gras, 5, faerben((76, 140, 52), (138, 196, 84), 0.3, 0.5)), cols, rows),
        'blumen': k20.flaeche(k6.kacheln(gras, 5, faerben((92, 154, 58), (156, 206, 94), 0.3, 0.5)), cols, rows),
        'guertel': k20.flaeche(k6.kacheln(gras, 5, faerben((40, 84, 36), (78, 126, 56), 0.3, 0.5)), cols, rows),
    }


BLUMEN = (0, 1, 2, 3, 5, 14, 18, 39, 48, 50, 52, 62, 33)


def blumen_stempeln(a, maske, seed):
    """Blumenfelder: kleine PixelLab-Blumenbueschel flach in die Wiese gestempelt (kein Objekt, kein Schatten),
    locker gestreut, nie ueber den Feldrand hinaus."""
    d = os.path.join(OBJ, 'blumen')
    if not os.path.isdir(d):
        return
    sp_ = []
    for n in BLUMEN:                                                   # Auswahl: Wiesenblumen, keine Pilze/Farne
        im = Image.open(os.path.join(d, '%02d.png' % n)).convert('RGBA')
        im = im.crop(im.getbbox())
        if im.width <= 28 and im.height <= 28:
            sp_.append(np.array(im).astype(np.float32))
    if not sp_:
        return
    rs = np.random.RandomState(seed)
    Hp, Wp = maske.shape
    ys, xs = np.nonzero(maske[::13, ::13])
    for y, x in zip(ys * 13, xs * 13):
        if rs.rand() > 0.5:
            continue
        sp = sp_[rs.randint(len(sp_))]
        if rs.rand() < 0.5:
            sp = sp[:, ::-1]
        h, w = sp.shape[:2]
        py, px = y + rs.randint(-5, 6) - h // 2, x + rs.randint(-5, 6) - w // 2
        if py < 0 or px < 0 or py + h > Hp or px + w > Wp or not maske[py:py + h, px:px + w].all():
            continue
        al = sp[..., 3:4] / 255.0
        a[py:py + h, px:px + w] = (a[py:py + h, px:px + w] * (1 - al) + sp[..., :3] * al).astype(np.uint8)


def see(a, maske, frame):
    alt = wasser_vertieft.MAUER
    wasser_vertieft.MAUER = [H(c) for c in ('#2e4a2a', '#3e5e34', '#4e7240', '#62884e', '#78a05e', '#8eb46c')]
    try:
        img = wasser_vertieft.vertiefen(Image.fromarray(a), np.ones(maske.shape, bool), frame, maske=maske,
                                        rand=('#3a5a2e', '#4c6e38', '#5e8444', '#729a50'))
    finally:
        wasser_vertieft.MAUER = alt
    return np.array(img.convert('RGB'))


def verfaelschen(a, m, seed):
    """Verzerrte Landschaft: Helligkeit bleibt (Formen erkennbar), Farbe kippt ins Violett mit einem Rest Gruen;
    dazu Glitch-Zeilen (kurze, waagerecht verschobene Pixelstreifen) und einzelne Magenta-Bloecke im 4-px-Raster."""
    sub = a.astype(np.float32)
    l = sub.mean(axis=2, keepdims=True) / 255.0
    viol = VIOLETT_LO + (VIOLETT_HI - VIOLETT_LO) * np.clip((l - 0.12) / 0.7, 0, 1)
    neu = viol * 0.86 + sub * 0.14
    a[m] = np.clip(neu[m], 0, 255).astype(np.uint8)
    rs = np.random.RandomState(seed)
    ys, xs = np.nonzero(m)
    y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    for _ in range((y1 - y0) * (x1 - x0) // 2600):                    # Glitch-Zeilen
        y, x = rs.randint(y0, y1 - 3), rs.randint(x0, x1 - 60)
        h, w, dx = rs.randint(1, 4), rs.randint(16, 60), rs.choice((-6, -4, 4, 6))
        if not m[y:y + h, x:x + w].all() or not m[y:y + h, max(0, x + dx):x + w + dx].all():
            continue
        a[y:y + h, x:x + w] = a[y:y + h, x - dx:x + w - dx].copy()
        a[y:y + h, x:x + w] = (a[y:y + h, x:x + w] * 0.85 + np.array((60, 10, 70)) * 0.15).astype(np.uint8)
    for _ in range((y1 - y0) * (x1 - x0) // 6000):                    # Magenta-Pixelbloecke
        y, x = (rs.randint(y0, y1 - 4) // 4) * 4, (rs.randint(x0, x1 - 4) // 4) * 4
        if m[y:y + 4, x:x + 4].all():
            a[y:y + 4, x:x + 4] = (a[y:y + 4, x:x + 4] * 0.4 + np.array((230, 60, 200)) * 0.6).astype(np.uint8)


def risse(a, m, seed):
    """Risse ins Nichts: dunkle Leere mit Datensternen, innen eine Magenta-Glutkante, aussen dunkle Kontur; an der
    Nordseite eine schmale Bruchwand (der Boden hat Dicke), Licht von oben links."""
    Hp, Wp = m.shape
    rs = np.random.RandomState(seed)
    a[m] = (10, 4, 22)
    yy, xx = np.nonzero(m)
    for y, x in zip(yy, xx):
        if rs.rand() < 0.012:
            a[y, x] = (150, 110, 220) if rs.rand() < 0.5 else (230, 120, 220)
    oben = m & ~np.roll(m, 1, 0)
    for d, c in enumerate([(88, 60, 96), (66, 42, 76), (46, 28, 58), (30, 16, 42)]):
        w = np.roll(oben, d, 0) & m
        a[w] = c
    rand = m & ~(np.roll(m, 1, 0) & np.roll(m, -1, 0) & np.roll(m, 1, 1) & np.roll(m, -1, 1))
    a[rand] = (a[rand] * 0.3 + np.array((240, 80, 210)) * 0.7).astype(np.uint8)
    aussen = ~m & (np.roll(m, 1, 0) | np.roll(m, -1, 0) | np.roll(m, 1, 1) | np.roll(m, -1, 1))
    a[aussen] = (24, 10, 34)


def abgrund(a, m):
    """Abgruende in Cherubimons Innerem: Schwaerze mit violettem Schein von unten, Bruchwand oben."""
    a[m] = (6, 2, 12)
    Hp, Wp = m.shape
    oben = m & ~np.roll(m, 1, 0)
    for d, c in enumerate([(70, 30, 80), (52, 20, 62), (36, 12, 46), (22, 6, 30), (14, 4, 20)]):
        a[np.roll(oben, d, 0) & m] = c
    unten = m & ~np.roll(m, -1, 0)
    for d in range(6):
        w = np.roll(unten, -d, 0) & m
        a[w] = (a[w] * (0.6 + d * 0.06) + np.array((120, 40, 160)) * (0.4 - d * 0.06)).astype(np.uint8)
    aussen = ~m & (np.roll(m, 1, 0) | np.roll(m, -1, 0) | np.roll(m, 1, 1) | np.roll(m, -1, 1))
    a[aussen] = (20, 8, 26)


def innen_boden(Hp, Wp, mitte, radius):
    a = k54.membran(Hp, Wp, mitte, radius, None).astype(np.float32)
    l = a.mean(axis=2, keepdims=True) / 255.0
    lo, hi = np.array((22, 10, 34), np.float32), np.array((150, 70, 170), np.float32)
    return np.clip(lo + (hi - lo) * np.clip((l - 0.18) / 0.6, 0, 1), 0, 255).astype(np.uint8)


def bauen(frame=None, speichern=True):
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cols, rows = lay['groesse']
    Wp, Hp = cols * T, rows * T
    cls = lay['klassen']
    kl = np.array([list(r) for r in cls])
    gross = lambda m: np.kron(m, np.ones((T, T), int)).astype(bool)
    RW, RH = lay['raum']
    g1, g2 = lay['grenzen']
    sp1 = np.zeros((Hp, Wp), bool); sp1[:, :g1 * T] = True
    sp2 = np.zeros((Hp, Wp), bool); sp2[:, g1 * T:g2 * T] = True
    sp3 = np.zeros((Hp, Wp), bool); sp3[:, g2 * T:] = True
    tex = texturen(cols, rows)
    # ------------------------------------------------------------------ Raum 1 Wiese (und Vorlage fuer Raum 2)
    a = tex['wiese'].copy()                                             # Guertelboden = Wiese (keine harte Raumkante)
    bl = k4.weich(k4.zell_maske(cls, 'bB', cols, rows), 5, 0, 56)
    a[bl] = tex['blumen'][bl]
    innen_bl = bl.copy()
    for _ in range(4):
        innen_bl &= np.roll(innen_bl, 1, 0) & np.roll(innen_bl, -1, 0) & np.roll(innen_bl, 1, 1) & np.roll(innen_bl, -1, 1)
    blumen_stempeln(a, innen_bl & sp1, 5601)
    blumen_stempeln(a, innen_bl & sp2, 5601)
    seem = k4.weich(k4.zell_maske(cls, 'SD', cols, rows), 5, 0, 57)
    a = see(a, seem, frame)
    # ------------------------------------------------------------------ Raum 2: dieselbe Wiese, verfaelscht
    verfaelschen(a, sp2, 5602)
    rm = k4.weich(k4.zell_maske(cls, 'R', cols, rows), 5, 0, 58)
    risse(a, rm, 5603)
    # ------------------------------------------------------------------ Raum 3: Cherubimons Inneres
    x3, y3 = lay['raeume'][2]
    mx, my = lay['ringmarken'][2]
    ib = innen_boden(Hp, Wp, ((x3 + mx) * T + 8, (y3 + my) * T + 8), 15 * T)
    raum3 = gross(np.isin(kl, list('iPfzgo'))) & sp3
    gurt3 = sp3 & ~raum3
    a[sp3] = ib[sp3]
    pm = k4.weich(k4.zell_maske(cls, 'P', cols, rows), 5, 0, 59)
    abgrund(a, pm)
    # ------------------------------------------------------------------ Marken
    for i, (x0, y0) in enumerate(lay['raeume']):
        fy, fx = np.nonzero(kl[y0:y0 + RH, x0:x0 + RW] == 'f')
        k17.feld_marken(a, x0 + fx.min(), y0 + fy.min(), fx.max() - fx.min() + 1, fy.max() - fy.min() + 1, frame)
        mx, my = lay['ringmarken'][i]
        k17.ringmarke(a, x0 + mx, y0 + my, frame)
    n = 0
    for y in range(rows):
        for x in range(cols):
            if kl[y, x] in 'zg':
                k16.pfeil_marke(a, x, y, (110, 225, 250) if kl[y, x] == 'z' else (250, 200, 90), frame, n * 0.25)
                n += 1
    guertel = gross(np.isin(kl, list('huk')))
    gesperrt = guertel | seem | rm | pm
    lvl = np.full((Hp, Wp), 2, np.uint8)
    if speichern and frame is None:
        np.save(os.path.join(KARTE, 'pixelhoehe.npy'), lvl)
        np.save(os.path.join(KARTE, 'wasser.npy'), np.packbits(seem))
        np.save(os.path.join(KARTE, 'leere.npy'), np.packbits(guertel | rm | pm))
    img = Image.fromarray(a).convert('RGBA')
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain_basis.png'))
    pf_ = os.path.join(OBJ, 'platzierung.json')
    if os.path.exists(pf_):
        objs = sorted((o for o in json.load(open(pf_)) if os.path.exists(os.path.join(OBJ, o['datei']))),
                      key=lambda o: o.get('sortier', o['y'] + o['fuss']))
        if objs:
            cache = {o['datei']: Image.open(os.path.join(OBJ, o['datei'])).convert('RGBA') for o in objs}
            ebenen = lvl.astype(np.int16)
            ebenen[seem | rm | pm] = 7
            k4.objekte_zeichnen(img, objs, cache, ~(seem | rm | pm), frame, ebenen=ebenen)
    a = np.array(img.convert('RGB'))
    innen_n = np.zeros((Hp, Wp), bool)
    innen_n[T:-T, T:-T] = True
    k35.nebel_digital(a, innen_n, frame)
    img = Image.fromarray(a).convert('RGBA')
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain.png'))
    print('Karte 56 %dx%d gebaut' % (cols, rows))
    return img


if __name__ == '__main__':
    bauen()
