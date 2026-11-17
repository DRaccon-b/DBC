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


def masse(a, m, frame=None, seed=52, boden=None, flach=False):
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
    if flach:
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
    # Glanzpunkte (feucht), flackern versetzt
    rs = np.random.RandomState(seed + 5)
    n = int(mm.sum() / 180)
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
    if flach:
        unten[:] = False
    col[oben & ~unten] = col[oben & ~unten] * 0.6 + HELL * 0.4
    tief = np.zeros((h, w), np.float32)
    for d in (range(1, 6) if not flach else []):
        r_ = np.zeros((h, w), bool)
        r_[:-d] = mm[:-d] & ~mm[d:]
        tief = np.maximum(tief, r_ * (1.0 - (d - 1) / 6.0))
    col = col * (1 - 0.55 * tief[..., None]) + DUNKEL * 0.55 * tief[..., None]
    p_ = np.pad(mm, 1, mode='edge')                                   # Kartenrand fortsetzen (keine Konturlinie am Bildrand)
    rand = mm & ~(p_[:-2, 1:-1] & p_[2:, 1:-1] & p_[1:-1, :-2] & p_[1:-1, 2:])
    col[rand] = DUNKEL * 0.8
    sub[mm] = col[mm]
    a[y0:y1, x0:x1] = np.clip(sub, 0, 255).astype(np.uint8)
    return m
