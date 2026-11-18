"""D-Reaper-Masse (Karten 52-54): rote, glaenzende organische Masse, die Boden und Strassen ueberzieht.

  import dreaper; m = dreaper.masse(a, maske, frame, seed)

- Kontur am 45-Grad-Raster (die Maske kommt aus k4.weich(zell_maske(...))), leicht erhoeht: dunkle Kante, an den
  Suedkanten eine 5 px dunkle Stirnseite und ein kurzer Bodenschatten nur auf dem Boden davor (nicht ueber Objekte,
  die Masse wird vor den Objekten gezeichnet).
- Oberflaeche: Beulen (weiches Rauschen) mit Licht von oben links, dunkle Adern, feuchte Glanzpunkte.
- Animation (4 Bilder, nahtlos): die Adern pulsieren (Helligkeitswelle laeuft durch die Masse), Glanzpunkte flackern.
"""
import numpy as np
from PIL import Image, ImageFilter

BASIS = np.array((118, 30, 50), np.float32)
DUNKEL = np.array((58, 10, 26), np.float32)
HELL = np.array((196, 74, 96), np.float32)
ADER = np.array((70, 8, 30), np.float32)
GLANZ = np.array((238, 150, 166), np.float32)


def _rauschen(h, w, skala, seed):
    rs = np.random.RandomState(seed)
    kl = rs.rand(h // skala + 2, w // skala + 2).astype(np.float32)
    im = Image.fromarray((kl * 255).astype(np.uint8)).resize(((w // skala + 2) * skala, (h // skala + 2) * skala),
                                                            Image.BICUBIC)
    return np.array(im, np.float32)[:h, :w] / 255.0


def _blur(m, r):
    return np.array(Image.fromarray((np.clip(m, 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(r)),
                    np.float32) / 255.0


# D-Reaper wie im Anime (Nutzer, Karten 52-54): knallrote, glaenzende Gallertmasse aus dicht gepackten Blasen
BL_ROT = np.array((214, 38, 62), np.float32)
BL_DUNKEL = np.array((112, 10, 36), np.float32)
BL_HELL = np.array((255, 120, 140), np.float32)
BL_GLANZ = np.array((255, 214, 222), np.float32)
BL_FUGE = np.array((86, 6, 28), np.float32)


def blasen(h, w, f, seed, x0=0, y0=0):
    """Dicht gepackte Blasen (Radius 3-9 px) mit dunkler Fuge, Licht von oben links und Glanzpunkt.
    4 Bilder nahtlos: jede Blase pulsiert mit eigener Phase um 1 px, einzelne Blasen blubbern (Glanz wandert)."""
    rs = np.random.RandomState(seed * 7 + 3)
    col = np.zeros((h, w, 3), np.float32) + BL_FUGE
    belegt = np.zeros((h, w), bool)
    yy, xx = np.mgrid[0:h, 0:w]
    n = int(h * w / 40)
    kand = list(zip(rs.randint(0, h, n), rs.randint(0, w, n), rs.randint(3, 10, n), rs.randint(0, 4, n)))
    kand.sort(key=lambda t: -t[2])                                     # grosse Blasen zuerst, kleine in die Luecken
    for (cy, cx, r, ph) in kand:
        rr = r + (1 if (f + ph) % 4 in (1, 2) and r >= 5 else 0)       # Pulsieren (nahtlos ueber 4 Bilder)
        y_0, y_1, x_0, x_1 = max(0, cy - rr), min(h, cy + rr + 1), max(0, cx - rr), min(w, cx + rr + 1)
        if y_1 <= y_0 or x_1 <= x_0:
            continue
        sy, sx = yy[y_0:y_1, x_0:x_1] - cy, xx[y_0:y_1, x_0:x_1] - cx
        d = np.sqrt(sy ** 2 + sx ** 2) / max(rr, 1)
        innen = d <= 1.0
        frei = innen & ~belegt[y_0:y_1, x_0:x_1]
        if frei.sum() < innen.sum() * 0.55:                           # zu stark ueberdeckt: weglassen
            continue
        licht = np.clip(1.0 - np.sqrt((sy + rr * 0.45) ** 2 + (sx + rr * 0.45) ** 2) / (rr * 1.5), 0, 1)
        c = BL_ROT[None, None] * (0.78 + 0.22 * licht[..., None]) + (BL_HELL - BL_ROT)[None, None] * (licht[..., None] ** 2) * 0.7
        rand = (d > 0.78) & innen
        c[rand] = c[rand] * 0.55 + BL_DUNKEL * 0.45                    # dunkler Blasenrand (unten rechts staerker)
        unten_r = rand & ((sy + sx) > 0)
        c[unten_r] = c[unten_r] * 0.6 + BL_DUNKEL * 0.4
        gl = (np.abs(sy + rr * 0.45) <= max(1, rr // 4)) & (np.abs(sx + rr * 0.4) <= max(1, rr // 4))
        if (f + ph) % 4 == 3 and r >= 6:                              # Blubbern: Glanz springt kurz zur Mitte
            gl = (np.abs(sy + rr * 0.15) <= 1) & (np.abs(sx + rr * 0.15) <= 1)
        c[gl & innen] = BL_GLANZ
        sub = col[y_0:y_1, x_0:x_1]
        sub[frei] = c[frei]
        belegt[y_0:y_1, x_0:x_1] |= innen
    return col


_STEMPEL = None


def stempel_laden():
    """PixelLab-Blasenhaufen (Gruppen k52_masse / k52_masse_klein, Draufsicht) als Stempel fuer die Masse."""
    global _STEMPEL
    if _STEMPEL is None:
        import os
        basis = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets', 'objekte', 'karte52')
        gross = [Image.open(os.path.join(basis, 'masse', '%02d.png' % i)).convert('RGBA') for i in (0, 1, 3)]
        klein = [Image.open(os.path.join(basis, 'masse_klein', '%02d.png' % i)).convert('RGBA')
                 for i in (0, 2, 12, 15)]                            # helle, runde Haufen (dunkle wirken am Rand wie Saum)
        _STEMPEL = ([g.crop(g.getbbox()) for g in gross], [k.crop(k.getbbox()) for k in klein])
    return _STEMPEL


def _abstand(mm, schritte=14):
    """Grober Abstand zur Maskenkante in Pixeln (Viertelaufloesung, wiederholtes Erodieren)."""
    m4 = Image.fromarray(mm[::4, ::4].astype(np.uint8) * 255)
    d = np.zeros((m4.height, m4.width), np.float32)
    cur = m4
    for i in range(schritte):
        arr = np.array(cur) > 0
        d += arr
        if not arr.any():
            break
        cur = cur.filter(ImageFilter.MinFilter(3))
    d = np.kron(d, np.ones((4, 4), np.float32))[:mm.shape[0], :mm.shape[1]] * 4
    return d


def stempeln(mm, f, seed, flach=False, ueber=12):
    """Masse aus ganzen PixelLab-Blasenhaufen (nie beschnitten, Nutzer): jeder Haufen wird nur so gross gesetzt, dass er bis
    auf ueber px in die Maske passt; am Rand ein Kranz kleiner Haufen, sodass der Umriss aus echten Blasen besteht.
    Von Norden nach Sueden gezeichnet. Animation: jeder Haufen hebt/senkt sich mit eigener Phase um 1 px (4 Bilder).
    Rueckgabe: RGBA-Ebene (Alpha 0/1) in Groesse der Maske."""
    gross, klein = stempel_laden()
    rs = np.random.RandomState(seed)
    h, w = mm.shape
    dist = _abstand(mm)
    alle = [(g, True) for g in gross] + [(k, False) for k in klein]
    liste = []

    def waehle(cy, cx, R, nur_klein=False):
        for _ in range(6):
            im, ist_gross = alle[rs.randint(len(alle))]
            if nur_klein and ist_gross:
                continue
            if ist_gross and rs.rand() < (0.5 if not flach else 0.8):
                continue
            halb = max(im.width, im.height) / 2.0
            sk = min(rs.uniform(0.6, 0.85) if ist_gross else rs.uniform(0.85, 1.15), R / halb)
            if sk * halb < 6:
                continue
            im2 = im.resize((max(4, int(im.width * sk)), max(4, int(im.height * sk))), Image.NEAREST)
            if rs.rand() < 0.5:
                im2 = im2.transpose(Image.FLIP_LEFT_RIGHT)
            liste.append((cy, cx, im2, rs.randint(0, 4)))
            return

    schritt = (34, 38) if not flach else (40, 44)
    for gy in range(0, h, schritt[0]):
        for gx in range(0, w, schritt[1]):
            cy, cx = gy + rs.randint(-8, 9), gx + rs.randint(-9, 10)
            if 0 <= cy < h and 0 <= cx < w and mm[cy, cx] and dist[cy, cx] >= 4:
                waehle(cy, cx, dist[cy, cx] + ueber)
    if not flach:                                                      # Randkranz aus kleinen Haufen
        rand = mm & (dist <= 4)
        ys, xs = np.nonzero(rand)
        reihen = list(zip(ys, xs))
        rs.shuffle(reihen)
        belegt = np.zeros((h // 13 + 2, w // 13 + 2), bool)            # Abstand ueber ein Belegungsraster (alle, nicht nur die letzten)
        for (cy, cx) in reihen:
            by, bx = cy // 13, cx // 13
            if belegt[max(0, by - 1):by + 2, max(0, bx - 1):bx + 2].any():
                continue
            belegt[by, bx] = True
            waehle(cy, cx, 18 + rs.randint(0, 6), nur_klein=True)
    liste.sort(key=lambda t: t[0])
    ebene = np.zeros((h, w, 4), np.float32)
    for (cy, cx, im, ph) in liste:
        dy = (0, 1, 1, 0)[(f + ph) % 4]
        arr = np.array(im).astype(np.float32)
        ih, iw = arr.shape[:2]
        y0, x0 = cy - ih // 2 + dy, cx - iw // 2
        ya, xa = max(0, y0), max(0, x0)
        yb, xb = min(h, y0 + ih), min(w, x0 + iw)
        if yb <= ya or xb <= xa:
            continue
        teil = arr[ya - y0:yb - y0, xa - x0:xb - x0]
        m_ = teil[..., 3] > 128
        rgb = teil[..., :3] * (0.8 if flach else 1.0)
        sub = ebene[ya:yb, xa:xb]
        sub[m_, :3] = rgb[m_]
        sub[m_, 3] = 1
    return ebene, dist


def masse(a, m, frame=None, seed=52, boden=None, flach=False, stil='stempel'):
    """Zeichnet die Masse in a (H x W x 3 uint8) auf die Pixelmaske m. boden: Maske, auf die der Schatten darf.
    flach: begehbarer Belag (Karte 54) - keine Stirnseite, kein Schatten, flachere Beulen."""
    f = (frame or 0) % 4
    Hh, W = m.shape
    ys, xs = np.nonzero(m)
    if not len(ys):
        return m
    y0, y1 = max(0, ys.min() - 12), min(Hh, ys.max() + 14)
    x0, x1 = max(0, xs.min() - 12), min(W, xs.max() + 14)
    mm = m[y0:y1, x0:x1]
    h, w = mm.shape
    sub = a[y0:y1, x0:x1].astype(np.float32)
    # Bodenschatten vor den Suedkanten (rechts unten versetzt), nur auf dem Boden
    sch = np.zeros((h, w), bool)
    sch[4:, 2:] = mm[:-4, :-2]
    sch &= ~mm
    if flach or stil == 'stempel':                                     # Stempel: Schatten folgt spaeter den Blasen
        sch[:] = False
    if boden is not None:
        sch &= boden[y0:y1, x0:x1]
    sub[sch] *= 0.62
    # Oberflaeche
    n1 = _rauschen(h + 0, w + 0, 9, seed + y0 * 7 + x0)
    n2 = _rauschen(h, w, 4, seed + 11 + x0)
    hoehe = _blur(mm.astype(np.float32), 2.0) * (0.55 + 0.45 * n1) + 0.15 * n2
    gy, gx = np.gradient(hoehe)
    licht = np.clip(0.5 - 6.0 * (gx + gy), 0, 1)                       # Licht von oben links
    col = BASIS[None, None] * (0.72 + 0.5 * licht[..., None]) + (HELL - BASIS)[None, None] * (n1[..., None] > 0.72) * 0.35
    # Adern: schmale Baender im Rauschen, pulsierende Helligkeit (Welle, 4 Bilder nahtlos)
    n3 = _rauschen(h, w, 14, seed + 23 + y0)
    ader = np.abs(n3 - 0.5) < 0.035
    yy, xx = np.mgrid[0:h, 0:w]
    welle = 0.5 + 0.5 * np.sin(2 * np.pi * (f / 4.0) - (xx + yy + x0 + y0) / 38.0)
    col[ader] = ADER * (1 - 0.55 * welle[ader, None]) + np.array((210, 40, 70), np.float32) * 0.55 * welle[ader, None]
    if stil in ('blasen', 'stempel'):                                  # Anime-Stil: Blasenmasse statt Beulen/Adern
        col = blasen(h, w, f, seed + y0 * 3 + x0, x0, y0)
        if stil == 'stempel':                                          # Nutzer: hoeher aufloesend - PixelLab-Blasenhaufen
            col = col * 0.55 + BL_FUGE[None, None] * 0.45
            st_ebene, st_dist = stempeln(mm, f, seed + y0 * 3 + x0, flach)
        if flach:                                                      # begehbarer Belag: dunkler, flacher
            col = col * 0.72 + BL_FUGE[None, None] * 0.28
    # Glanzpunkte (feucht), flackern versetzt
    rs = np.random.RandomState(seed + 5)
    n = int(mm.sum() / 180) if stil not in ('blasen', 'stempel') else 0
    py, px = rs.randint(0, h, n), rs.randint(0, w, n)
    ph = rs.randint(0, 4, n)
    for y_, x_, p_ in zip(py, px, ph):
        if 2 <= y_ < h - 3 and 2 <= x_ < w - 3 and mm[y_ - 2:y_ + 3, x_ - 2:x_ + 3].all() and (f + p_) % 4 != 3:
            col[y_, x_] = GLANZ
            col[y_, x_ + 1] = GLANZ * 0.85 + BASIS * 0.15
            if (f + p_) % 4 == 0:
                col[y_ + 1, x_] = GLANZ * 0.7 + BASIS * 0.3
    # Kanten: Stirnseite unten (5 px dunkel), helle Lippe oben/links, dunkle Kontur
    unten = np.zeros((h, w), bool)
    for d in range(1, 6):
        unten[:-d] |= mm[:-d] & ~mm[d:]
    oben = np.zeros((h, w), bool)
    oben[2:] = mm[2:] & ~mm[:-2]
    oben[:, 2:] |= mm[:, 2:] & ~mm[:, :-2]
    if flach or stil == 'stempel':                                     # Stempel: Blasen bringen eigene Schattierung/Kontur mit
        unten[:] = False
        oben[:] = False
    col[oben & ~unten] = col[oben & ~unten] * 0.6 + HELL * 0.4
    tief = np.zeros((h, w), np.float32)
    for d in (range(1, 6) if not flach and stil != 'stempel' else []):
        r_ = np.zeros((h, w), bool)
        r_[:-d] = mm[:-d] & ~mm[d:]
        tief = np.maximum(tief, r_ * (1.0 - (d - 1) / 6.0))
    col = col * (1 - 0.55 * tief[..., None]) + DUNKEL * 0.55 * tief[..., None]
    p_ = np.pad(mm, 1, mode='edge')                                   # Kartenrand fortsetzen (keine Konturlinie am Bildrand)
    rand = mm & ~(p_[:-2, 1:-1] & p_[2:, 1:-1] & p_[1:-1, :-2] & p_[1:-1, 2:])
    if stil == 'stempel':                                              # ganze Blasenhaufen ueber dunklem Kern, Umriss aus Blasen
        kern = mm & (st_dist >= (4 if flach else 8))
        if flach:
            kern = mm
        sub[kern] = col[kern]
        auf = st_ebene[..., 3] > 0
        if boden is not None:
            auf &= mm | boden[y0:y1, x0:x1]
        if flach:
            auf &= mm
        if not flach:                                                  # Schatten der Blasen-Silhouette, nur auf den Boden
            sil = kern | auf
            sch2 = np.zeros((h, w), bool)
            sch2[3:, 2:] = sil[:-3, :-2]
            sch2 &= ~sil
            if boden is not None:
                sch2 &= boden[y0:y1, x0:x1] & ~mm
            sub[sch2] *= 0.62
        sub[auf] = st_ebene[auf, :3]
    else:
        col[rand] = DUNKEL * 0.8
        sub[mm] = col[mm]
    a[y0:y1, x0:x1] = np.clip(sub, 0, 255).astype(np.uint8)
    return m
