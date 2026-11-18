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
BL_FUGE = np.array((96, 10, 28), np.float32)   # Luecken zwischen den Schlammflecken (Ton der Flecken)


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
FEIN_DICHTE = 2                                                        # 1 = jede Kachel ein Haufen, 2 = jede zweite


def _ohne_spritzer(im):
    """Nur die groesste zusammenhaengende Flaeche behalten (lose Tropfen am Rand des Schlammflecks entfernen)."""
    a = np.array(im)
    m = a[..., 3] > 0
    lab = np.zeros(m.shape, int); n = 0; groesse = {}
    for y0, x0 in zip(*np.nonzero(m)):
        if lab[y0, x0]:
            continue
        n += 1; st = [(y0, x0)]; lab[y0, x0] = n; c = 0
        while st:
            y, x = st.pop(); c += 1
            for yy, xx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                if 0 <= yy < m.shape[0] and 0 <= xx < m.shape[1] and m[yy, xx] and not lab[yy, xx]:
                    lab[yy, xx] = n; st.append((yy, xx))
        groesse[n] = c
    if groesse:
        a[lab != max(groesse, key=groesse.get)] = 0
    return Image.fromarray(a)


def stempel_laden():
    """PixelLab-Blasenhaufen (Gruppen k52_masse / k52_masse_klein, Draufsicht) als Stempel fuer die Masse."""
    global _STEMPEL
    if _STEMPEL is None:
        import os
        basis = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets', 'objekte', 'karte52')
        gross = [Image.open(os.path.join(basis, 'masse', '%02d.png' % i)).convert('RGBA') for i in (0, 1, 3)]
        # Nutzer: durchgehender dunkelroter Schlamm (PixelLab k52_schlamm) statt Blasenhaufen; lose Spritzer entfernt
        variante = os.environ.get('DREAPER_SCHLAMM')               # Vorschau der Schlamm-Varianten (k52_sv01..10)
        if variante:
            klein = [_ohne_spritzer(Image.open(os.path.join(basis, variante, '%02d.png' % i)).convert('RGBA'))
                     for i in (0, 1, 2, 3)]
        else:
            klein = [_ohne_spritzer(Image.open(os.path.join(basis, 'schlamm', '%02d.png' % i)).convert('RGBA'))
                     for i in (0, 1, 2, 3)] + [_ohne_spritzer(Image.open(os.path.join(basis, 'schlamm_gross', '01.png')).convert('RGBA'))]
        fein = [Image.open(os.path.join(basis, 'masse_fein', '%02d.png' % i)).convert('RGBA') for i in (0, 1, 2, 3)]
        _STEMPEL = ([g.crop(g.getbbox()) for g in gross], [k.crop(k.getbbox()) for k in klein],
                    [k.crop(k.getbbox()) for k in fein])
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


def stempeln(mm, f, seed, flach=False, x0=0, y0=0, T=16, ueber=3):
    """Masse wie ein Baumguertel (Nutzer): ganze grosse PixelLab-Blasenhaufen auf dem Kachelraster, versetzt nebeneinander
    (jede zweite Kachel, Reihen um eine Kachel verschoben), leicht ueberlappend, von Norden nach Sueden gezeichnet - keine
    kleinen Fuellblasen, nichts beschnitten. Animation: jeder Haufen hebt/senkt sich mit eigener Phase um 1 px (4 Bilder).
    Rueckgabe: RGBA-Ebene (Alpha 0/1) in Groesse der Maske und der Abstand zur Kante."""
    gross = stempel_laden()[2 if flach else 1]                         # Nutzer: Originalgroesse, nie herunterskalieren
                                                                       # (Belag Karte 54: kleinere 48er-Haufen)
    h, w = mm.shape
    dist = _abstand(mm)
    mm_d = np.array(Image.fromarray(mm.astype(np.uint8) * 255).filter(ImageFilter.MaxFilter(2 * ueber + 1))) > 0
    PAD = 48                                                           # am Kartenrand geht die Masse ueber den Bildrand weiter
    mm_p = np.pad(mm_d, PAD, mode='edge')
    breite = 40 if flach else 42                                       # Haufenbreite (ueberlappt die Nachbarn leicht)
    liste = []
    ty0, tx0 = -((y0 + 1) // T) - 1, -((x0 + 1) // T) - 1
    for ty in range(y0 // T - 1, (y0 + h) // T + 2):
        for tx in range(x0 // T - 1, (x0 + w) // T + 2):
            if FEIN_DICHTE == 2 and (tx + ty) % 2:
                continue
            cy, cx = ty * T + T // 2 - y0, tx * T + T // 2 - x0       # Kachelmitte (global am Raster)
            if not (0 <= cy < h and 0 <= cx < w) or not mm[cy, cx]:
                continue
            if flach and dist[cy, cx] < breite // 2:                   # begehbarer Belag: ganz innerhalb der Flaeche
                continue
            rs = np.random.RandomState((seed * 131 + tx * 7919 + ty * 104729) % (2 ** 31))
            im = gross[rs.randint(len(gross))]
            if rs.rand() < 0.5:
                im = im.transpose(Image.FLIP_LEFT_RIGHT)
            if not flach:                                              # exakt pruefen: Blasenpixel hoechstens 'ueber' px ausserhalb
                kand_ = sorted(gross, key=lambda g: -g.width * g.height)
                kand_ = [im] + [g for g in kand_ if g is not im]
                gefunden = None
                gy_, gx_ = np.gradient(dist[max(0, cy - 8):cy + 9, max(0, cx - 8):cx + 9])
                vy, vx = gy_.mean(), gx_.mean()
                n_ = (vy ** 2 + vx ** 2) ** 0.5 or 1.0
                for im_ in kand_:
                    al_ = np.array(im_)[..., 3] > 128
                    ih_, iw_ = al_.shape
                    for schritt_ in range(0, 25, 2):
                        ny_, nx_ = int(round(cy + vy / n_ * schritt_)), int(round(cx + vx / n_ * schritt_))
                        ya_, xa_ = ny_ - ih_ // 2, nx_ - iw_ // 2
                        if ya_ < -PAD or xa_ < -PAD or ya_ + ih_ > h + PAD or xa_ + iw_ > w + PAD:
                            continue
                        if not (al_ & ~mm_p[ya_ + PAD:ya_ + PAD + ih_, xa_ + PAD:xa_ + PAD + iw_]).any():
                            gefunden = (ny_, nx_, im_)
                            break
                    if gefunden:
                        break
                if not gefunden:
                    continue
                cy, cx, im = gefunden
            liste.append((cy + im.height // 2, cx, im, rs.randint(0, 4)))   # mittig auf der Kachel (quillt gleichmaessig ueber)
    liste.sort(key=lambda t: t[0])
    ebene = np.zeros((h, w, 4), np.float32)
    for (fy, cx, im, ph) in liste:
        dy = (0, 1, 1, 0)[(f + ph) % 4]
        arr = np.array(im).astype(np.float32)
        ih, iw = arr.shape[:2]
        ya0, xa0 = fy - ih + dy, cx - iw // 2
        ya, xa = max(0, ya0), max(0, xa0)
        yb, xb = min(h, ya0 + ih), min(w, xa0 + iw)
        if yb <= ya or xb <= xa:
            continue
        teil = arr[ya - ya0:yb - ya0, xa - xa0:xb - xa0]
        m_ = teil[..., 3] > 128
        rgb = teil[..., :3] * (0.8 if flach else 1.0)
        sub = ebene[ya:yb, xa:xb]
        sub[m_, :3] = rgb[m_]
        sub[m_, 3] = 1
    return ebene, dist


SCHLAMM = np.array([(26, 3, 9), (44, 6, 14), (66, 9, 20), (92, 14, 28), (122, 22, 36), (156, 36, 48),
                    (190, 62, 70)], np.float32)                      # dunkelrote Schlamm-Rampe (Pixelart-Stufen)


def schlamm(mm, h, w, f, seed, x0, y0):
    """Durchgehende, zaehe, dunkelrote Schlammmasse (Nutzer, Karten 52-54): grosse weiche Wuelste und kleinere Beulen,
    Licht von oben links in 7 Stufen, feuchte Glanzlichter, langsam ueber die Oberflaeche wandernde Glanzwellen und dunkle
    Adern, die im Takt pulsieren (4 Bilder, nahtlos)."""
    nb = _rauschen(h, w, 30, seed + 31 + y0)
    nm = _rauschen(h, w, 12, seed + 37 + x0)
    ns = _rauschen(h, w, 3, seed + 41 + y0 + x0)
    dist = _blur(mm.astype(np.float32), 5.0)
    hoehe = dist * (0.55 + 0.45 * nb) + 0.07 * nm + 0.015 * ns
    gy, gx = np.gradient(_blur(np.clip(hoehe, 0, 1), 1.5) * 40.0)
    licht = np.clip(0.5 - 1.1 * (gx + gy), 0, 1)
    t = np.clip(0.02 + 0.62 * licht + 0.2 * (hoehe - 0.5), 0, 0.86)
    yy, xx = np.mgrid[0:h, 0:w]
    welle = 0.5 + 0.5 * np.sin(2 * np.pi * (f / 4.0) - ((xx + x0) * 0.6 + (yy + y0)) / 26.0 + nm * 5.0)
    t = np.clip(t + 0.07 * (welle - 0.5) * (licht > 0.5), 0, 0.9)       # Glanzwelle wandert langsam
    stufe = np.clip((t * (len(SCHLAMM) - 1)).round().astype(int), 0, len(SCHLAMM) - 1)
    col = SCHLAMM[stufe]
    glanz = (licht > 0.86) & (ns > 0.7) & (dist > 0.7)                # feuchte Glanzlichter auf den Wuelsten (sparsam)
    col[glanz] = col[glanz] * 0.35 + np.array((236, 132, 132), np.float32) * 0.65
    n3 = _rauschen(h, w, 14, seed + 23 + y0)
    ader = (np.abs(n3 - 0.5) < 0.022) & (dist > 0.45)
    puls = 0.5 + 0.5 * np.sin(2 * np.pi * (f / 4.0) - (xx + yy + x0 + y0) / 40.0)
    col[ader] = np.array((34, 3, 10), np.float32) * (1 - puls[ader, None]) + np.array((150, 22, 40), np.float32) * puls[ader, None]
    return col


_TEXTUR = None


def textur_laden():
    """PixelLab-Texturfelder (k52_masse_tex2, voll deckend, Nutzer: Masse ohne Rand wie im Anime) - Innenteil ohne Rahmen."""
    global _TEXTUR
    if _TEXTUR is None:
        import os
        basis = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets', 'objekte', 'karte52', 'masse_tex2')
        _TEXTUR = []
        for i, ein in ((3, 5), (0, 9)):
            a = np.array(Image.open(os.path.join(basis, '%02d.png' % i)).convert('RGBA'))
            ys, xs = np.nonzero(a[..., 3] > 0)
            a = a[ys.min() + ein:ys.max() - ein + 1, xs.min() + ein:xs.max() - ein + 1, :3].astype(np.float32)
            _TEXTUR += [a, a[:, ::-1]]
    return _TEXTUR


def textur(h, w, f, seed, x0, y0, zelle=52):
    """Randlose Masse: Texturfelder ueberlappend aneinandergesetzt, Naehte als unregelmaessige Rauschgrenze (Pixel werden
    gewaehlt, nicht gemischt - Palette bleibt). Adern (gelbe Pixel) pulsieren als Welle (4 Bilder, nahtlos)."""
    tex = textur_laden()
    rs = np.random.RandomState(seed)
    t0 = tex[0]                                                        # Grundflaeche gekachelt (keine Luecken)
    out = np.tile(t0, (h // t0.shape[0] + 1, w // t0.shape[1] + 1, 1))[:h, :w].copy()
    ueber = 16
    nz = _rauschen(h + 200, w + 200, 6, seed + 3)
    for gy in range(-ueber, h, zelle):
        for gx in range(-ueber, w, zelle):
            t = tex[rs.randint(len(tex))]
            th, tw = t.shape[:2]
            gr = zelle + 2 * ueber
            oy, ox = rs.randint(0, th - gr + 1), rs.randint(0, tw - gr + 1)
            stueck = t[oy:oy + gr, ox:ox + gr]
            ya, xa = gy - ueber, gx - ueber
            yy, xx = np.mgrid[0:gr, 0:gr]
            # Rampe 1 in der Zellmitte, 0 am Ueberlappungsrand, plus Rauschen -> unregelmaessige Naht
            rand = np.minimum(np.minimum(yy, gr - 1 - yy), np.minimum(xx, gr - 1 - xx)) / float(2 * ueber)
            sy0, sx0 = max(0, ya), max(0, xa)
            sy1, sx1 = min(h, ya + gr), min(w, xa + gr)
            if sy1 <= sy0 or sx1 <= sx0:
                continue
            r_ = rand[sy0 - ya:sy1 - ya, sx0 - xa:sx1 - xa]
            n_ = nz[sy0 + 100:sy1 + 100, sx0 + 100:sx1 + 100]
            neu_ = (r_ + 0.6 * (n_ - 0.5)) > 0.35
            if gy == -ueber or gx == -ueber:
                neu_ |= r_ >= 0
            ziel = out[sy0:sy1, sx0:sx1]
            ziel[neu_] = stueck[sy0 - ya:sy1 - ya, sx0 - xa:sx1 - xa][neu_]
    gelb = (out[..., 0] > 170) & (out[..., 1] > 110) & (out[..., 1] > out[..., 2] + 20)
    yy, xx = np.mgrid[0:h, 0:w]
    welle = 0.5 + 0.5 * np.sin(2 * np.pi * (f / 4.0) - (xx + yy + x0 + y0) / 40.0)
    out[gelb] = out[gelb] * (0.82 + 0.3 * welle[gelb, None])
    return np.clip(out, 0, 255)


def masse(a, m, frame=None, seed=52, boden=None, flach=False, stil='stempel'):
    """Zeichnet die Masse in a (H x W x 3 uint8) auf die Pixelmaske m. boden: Maske, auf die der Schatten darf.
    flach: begehbarer Belag (Karte 54) - keine Stirnseite, kein Schatten, flachere Beulen."""
    import os
    stil = os.environ.get('DREAPER_STIL', stil)                         # Vorschau anderer Stile
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
            col = col * 0.15 + BL_FUGE[None, None] * 0.85                # Schlamm: Fugen im Ton der Flecken
            st_ebene, st_dist = stempeln(mm, f, seed, flach, x0, y0)
        if flach:                                                      # begehbarer Belag: dunkler, flacher
            col = col * 0.72 + BL_FUGE[None, None] * 0.28
    if stil == 'schlamm':                                              # Nutzer: durchgehender dunkelroter Schlamm
        col = schlamm(mm, h, w, f, seed, x0, y0)
    if stil == 'textur':                                               # Nutzer: Masse ohne Rand/Abgrenzung (Anime-Bild)
        col = textur(h, w, f, seed + x0 * 3 + y0, x0, y0)
        if flach:
            col = col * 0.8
    # Glanzpunkte (feucht), flackern versetzt
    rs = np.random.RandomState(seed + 5)
    n = int(mm.sum() / (900 if stil == 'schlamm' else 180)) if stil not in ('blasen', 'stempel', 'textur') else 0   # Schlamm: wenige Glanzpunkte
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
    if stil == 'textur':
        oben[:] = False
    col[oben & ~unten] = col[oben & ~unten] * 0.6 + (SCHLAMM[4] if stil == 'schlamm' else HELL) * 0.4
    tief = np.zeros((h, w), np.float32)
    for d in (range(1, 6) if not flach and stil != 'stempel' else []):
        r_ = np.zeros((h, w), bool)
        r_[:-d] = mm[:-d] & ~mm[d:]
        tief = np.maximum(tief, r_ * (1.0 - (d - 1) / 6.0))
    k_ = 0.3 if stil == 'textur' else 0.55                             # Textur: nur weiche Stirnseite, kein dunkles Band
    col = col * (1 - k_ * tief[..., None]) + DUNKEL * k_ * tief[..., None]
    p_ = np.pad(mm, 1, mode='edge')                                   # Kartenrand fortsetzen (keine Konturlinie am Bildrand)
    rand = mm & ~(p_[:-2, 1:-1] & p_[2:, 1:-1] & p_[1:-1, :-2] & p_[1:-1, 2:])
    if stil == 'stempel':                                              # ganze Blasenhaufen ueber dunklem Kern, Umriss aus Blasen
        auf0 = st_ebene[..., 3] > 0                                    # Grundflaeche nur in Luecken zwischen Haufen (Schliessung)
        zu = Image.fromarray(np.pad(auf0, 8, mode='edge').astype(np.uint8) * 255).filter(ImageFilter.MaxFilter(9)).filter(
            ImageFilter.MinFilter(9))
        kern = mm & (np.array(zu)[8:-8, 8:-8] > 0)
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
        if stil != 'textur':                                           # Textur: keine Konturlinie (Nutzer)
            col[rand] = DUNKEL * 0.8
        sub[mm] = col[mm]
    a[y0:y1, x0:x1] = np.clip(sub, 0, 255).astype(np.uint8)
    return m
