# Grundgeruest aus karte43 (tools/neue_karte.py) - an die Vorlage von karte44 "Chuchidarumon Village" anpassen!
"""Karte 44 - Chuchidarumon Village (A03 Nr. 11), Gelaende nach maps/karte44/layout.json.

Wiese aus den Graskacheln (assets/basis, Toene der Vorlage), breite Erdwege, Bach von Nord nach Sued als vertieftes
Wasser (wie Karte 20) mit Holzbruecken (bauwerke), Wald (Guertel und Bloecke) erhoeht auf dunklem Waldboden mit
niedriger Steinmauer an allen Suedkanten, flache Grashalm-Bueschel als Bodenstruktur, Teleporter an den Ausgaengen.
Alle Bodenkanten am 16er-Raster mit 45-Grad-Schraegen (Regel 6b).

  python3 tools/karte44_layout.py && python3 tools/karte44_bauen.py
"""
import json, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
import karte_bauen as kb
import karte04_bauen as k4
import karte06_bauen as k6
import karte20_bauen as k20
import bauwerke
import wasser_vertieft

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte44')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte44')
T = 16
N_FRAMES = 4
BILDDAUER = 250
k4.N_FRAMES = N_FRAMES
kb.N_FRAMES = N_FRAMES
H = k4.H
weich, zell_maske, flaeche = k4.weich, k4.zell_maske, k20.flaeche
k4.SCHATTEN = {'farbe': (18, 42, 34), 'dx': 0.3, 'dy': 0.15, 'kern': 100, 'wurf': (66, 52)}   # kuehler, kompakter (Nutzer)
k4.RASTER45 = True                       # Regel 6b: alle Bodenkanten am 16er-Raster mit 45 Grad
# niedrige Steinmauer der Waldbloecke (grauer Bruchstein wie in der Vorlage), Kante oben mit Waldboden
k4.FELS['mauer43'] = ['#2c2f38', '#3e434e', '#545a66', '#6a717e', '#828a96', '#9aa2ac', '#b6bcc4']
LIPPE = ['#1e3a1a', '#284a22', '#33592a', '#3e6a32', '#4a7a3a', '#588a44']   # Waldkante (dunkles Gras)
FRONT = 16
SEITE = 6                                # seitliche Plateaukanten nur schmal (Regel)


def faerben(lo, hi, a0=0.35, a1=0.5):
    def f(a):
        l = a.mean(axis=2, keepdims=True) / 255.0
        return np.array(lo, np.float32) + (np.array(hi, np.float32) - np.array(lo, np.float32)) * np.clip((l - a0) / a1, 0, 1)
    return f


def texturen(cols, rows):
    basis = os.path.join(ROOT, 'assets', 'basis')
    sand = os.path.join(basis, 'sand_%d.png')
    gras = os.path.join(basis, 'gras_%d.png')
    kies = os.path.join(ROOT, 'assets', 'karte03', 'basis', 'kies_%d.png')
    return {
        'g': flaeche(k6.kacheln(gras, 5, faerben((66, 118, 46), (116, 166, 78), 0.3, 0.5)), cols, rows),
        'w': flaeche(k6.kacheln(sand, 5, faerben((168, 138, 92), (218, 190, 136))), cols, rows),
        'k': flaeche(k6.kacheln(kies, 5, faerben((96, 100, 108), (168, 172, 178), 0.25, 0.6)), cols, rows),
        'h': flaeche(k6.kacheln(gras, 5, faerben((30, 70, 30), (64, 110, 50), 0.3, 0.5)), cols, rows),
    }


BODEN = set(os.environ.get('K44_BODEN', '').split(',')) - {''}   # Nutzer: Bodenschattierung (Relief/vertiefte Wege) wieder raus


def boden_tiefe(a, cls, cols, rows, frame):
    """Boden nicht platt (Nutzer): ohne neue Objekte/Texturen.
    relief: sanfte Huegel der Wiese - Hoehenfeld aus grobem Rauschen, Licht von oben links, in 3 Stufen (Pixel-Look)
    wege:   Erdwege liegen etwas tiefer - Schattenkante unter der Wiese im Norden/Westen, Lichtkante im Sueden/Osten
    wind:   Windboeen ziehen als helle Wellen ueber die Wiese (animiert, 4 Bilder)"""
    def gauss(m, sig):                                                 # separabler Gauss (Rand fortgesetzt)
        r_ = int(3 * sig) + 1
        k_ = np.exp(-0.5 * (np.arange(-r_, r_ + 1) / sig) ** 2); k_ /= k_.sum()
        p_ = np.pad(m, r_, mode='edge')
        p_ = np.apply_along_axis(lambda v: np.convolve(v, k_, 'valid'), 0, p_)
        return np.apply_along_axis(lambda v: np.convolve(v, k_, 'valid'), 1, p_)
    Hp, Wp = rows * T, cols * T
    g = weich(zell_maske(cls, 'g', cols, rows), 5.0, 0, 3)
    w = weich(zell_maske(cls, 'wT', cols, rows), 5.0, 0, 3)
    af = a.astype(np.float32)
    if 'relief' in BODEN:
        rs = np.random.RandomState(4401)
        hf = gauss(rs.rand(Hp // 16 + 2, Wp // 16 + 2).astype(np.float32), 2.0)
        hf = np.array(Image.fromarray(hf.astype(np.float32), 'F').resize((Wp + 32, Hp + 32), Image.BICUBIC))[16:Hp + 16, 16:Wp + 16]
        hf = (hf - hf.min()) / (hf.max() - hf.min() + 1e-6) * 160.0
        gy, gx = np.gradient(hf)
        licht = -(gx + gy)                                           # Hang nach oben links -> hell
        licht = licht / (np.abs(licht).max() + 1e-6)
        stufe = np.where(licht > 0.18, 1.07, np.where(licht < -0.18, 0.91, 1.0))
        stufe = np.where(licht > 0.5, 1.13, np.where(licht < -0.5, 0.85, stufe))
        f_ = np.where(g, stufe, np.where(w, 1 + (stufe - 1) * 0.5, 1.0))
        af *= f_[..., None]
    if 'wege' in BODEN:
        tief = w.copy()
        gras_ob = np.zeros_like(tief); gras_li = np.zeros_like(tief)
        for d in (1, 2, 3):
            gras_ob[d:] |= ~w[:-d] & g[:-d]
            gras_li[:, d:] |= ~w[:, :-d] & g[:, :-d]
        schatten = tief & (gras_ob | gras_li)
        nah = np.zeros_like(tief)
        for d in (1, 2):
            nah[d:] |= ~w[:-d] & g[:-d]
        af[schatten] *= 0.86
        af[tief & nah] *= 0.92
        licht_ = np.zeros_like(tief)                                  # Lichtkante: Boeschung im Sueden/Osten
        licht_[:-1] |= tief[:-1] & ~w[1:] & g[1:]
        licht_[:, :-1] |= tief[:, :-1] & ~w[:, 1:] & g[:, 1:]
        af[licht_] = np.minimum(af[licht_] * 1.12, 255)
        kante = np.zeros_like(tief)                                   # Grasrand ueber dem Weg: dunkle Kante (Abbruch)
        kante[:-1] |= g[:-1] & ~w[:-1] & w[1:]
        af[kante] *= 0.8
    if 'wind' in BODEN and frame is not None:
        yy, xx = np.mgrid[0:Hp, 0:Wp].astype(np.float32)
        ph = 2 * np.pi * (frame % N_FRAMES) / N_FRAMES
        welle = np.sin((xx * 0.8 + yy) / 46.0 - ph) + 0.6 * np.sin((xx - yy * 0.4) / 23.0 - 2 * ph + 1.3)
        rs2 = np.random.RandomState(4402)
        korn = gauss(rs2.rand(Hp // 2 + 1, Wp // 2 + 1).astype(np.float32), 0.8) > 0.5
        korn = np.kron(korn, np.ones((2, 2), bool))[:Hp, :Wp]
        hell = (welle > 1.05) & korn & g
        af[hell] = np.minimum(af[hell] * np.array([1.06, 1.1, 1.02]), 255)
    a[:] = np.clip(af, 0, 255).astype(np.uint8)


def bauen(frame=None, speichern=True):
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cls = lay['klassen']
    cols, rows = lay['groesse']
    Wp, Hp = cols * T, rows * T
    hp = np.kron(np.array([[int(c) for c in z] for z in lay['hoehe']]), np.ones((T, T), int))
    tex = texturen(cols, rows)
    a = tex['g'].copy()
    for art, blur, seed in (('w', 5.0, 3),):
        m = weich(zell_maske(cls, art + ('T' if art == 'w' else ''), cols, rows), blur, 0, seed)
        if art == 'w':                                               # Wegrand: leichter dunkler Saum im Gras
            saum = weich(zell_maske(cls, 'wT', cols, rows), blur, 0, seed, 0.36) & ~m
            a[saum] = (a[saum] * 0.9).astype(np.uint8)
        a[m] = tex[art][m]
    # Bodenstruktur (Nutzer): flache Grashalm-Bueschel (PixelLab k44_halme) direkt in die Wiese gestempelt - kein Objekt,
    # kein Schatten, begehbar; locker in Gruppen, nur innerhalb der Wiese (Abstand zu Weg/Platz/Wald)
    halme = []
    for n_ in ('00', '02', '03', '06'):              # ohne 01 (zu dunkel auf der hellen Wiese)
        sp = np.array(Image.open(os.path.join(OBJ, 'halme', n_ + '.png')).convert('RGBA')).astype(float)
        bb = Image.fromarray(sp.astype(np.uint8)).getbbox()
        sp = sp[bb[1]:bb[3], bb[0]:bb[2]]
        gruen = (sp[..., 1] > sp[..., 0] + 10) & (sp[..., 3] > 0)          # Halme auf die Grastoene der Karte abdunkeln
        sp[gruen, :3] = sp[gruen, :3] * np.array([0.9, 0.93, 0.86])
        halme.append(sp)
    kl = np.array([list(z) for z in cls])
    innen = kl == 'g'
    rs_rand = np.pad(kl == 'g', 1, mode='edge')
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            innen &= rs_rand[1 + dy:1 + dy + rows, 1 + dx:1 + dx + cols]      # Rand fortsetzen (kein np.roll)
    belegt = np.zeros((Hp, Wp), bool)                                 # keine Halme unter/an Objekten
    pf_ = os.path.join(OBJ, 'platzierung.json')
    if os.path.exists(pf_):
        for o in json.load(open(pf_)):
            if 'wald' in o['datei'] or not os.path.exists(os.path.join(OBJ, o['datei'])):
                continue
            bb_ = Image.open(os.path.join(OBJ, o['datei'])).getbbox()
            if bb_:
                belegt[max(0, o['y'] + bb_[1] - 4):o['y'] + bb_[3] + 6, max(0, o['x'] + bb_[0] - 6):o['x'] + bb_[2] + 6] = True
    rs = np.random.RandomState(4444)
    zentren = [(y, x) for y in range(rows) for x in range(cols) if innen[y, x] and rs.rand() < 0.045]
    for (cy, cx) in zentren:
        for _ in range(rs.randint(2, 5)):                                    # Gruppe aus 2-4 Bueschelchen
            yy, xx = cy + rs.randint(-1, 2), cx + rs.randint(-1, 2)
            if not (0 <= yy < rows and 0 <= xx < cols and innen[yy, xx]):
                continue
            sp = halme[rs.randint(0, 3) if rs.rand() < 0.9 else 3]
            if rs.rand() < 0.5:
                sp = sp[:, ::-1]
            h_, w_ = sp.shape[:2]
            py, px = yy * T + rs.randint(0, T - min(h_, T) + 1), xx * T + rs.randint(0, T - min(w_, T) + 1)
            if py + h_ > Hp or px + w_ > Wp or belegt[py:py + h_, px:px + w_].any():
                continue
            belegt[py - 2:py + h_ + 2, px - 2:px + w_ + 2] = True       # Bueschel ueberlappen sich nicht
            al = sp[..., 3:4] / 255.0
            a[py:py + h_, px:px + w_] = (a[py:py + h_, px:px + w_] * (1 - al) + sp[..., :3] * al).astype(np.uint8)
    boden_tiefe(a, cls, cols, rows, frame)
    hoch = weich((hp >= 1).astype(np.float32), 5, 0.0, 7, 0.5)       # Wald erhoeht
    a[hoch] = tex['h'][hoch]
    frei = np.zeros((Hp, Wp), bool)
    wand = k4.hoehenkanten(a, hoch, 'mauer43', FRONT, SEITE, LIPPE, frei, 44, berg=False)
    vor_bach = a.copy()
    # Bach: vertieftes Wasser (Karte 20); laeuft oben und unten aus der Karte -> Bild dort erweitern, kein Ufer am Rand
    xm = weich(zell_maske(cls, 'xb', cols, rows), 4, 0.15, 8, 0.45)
    P = 24
    ag = np.pad(a, ((P, P), (P, P), (0, 0)), mode='edge')
    mg = np.pad(xm, ((P, P), (P, P)), mode='edge')
    ag = np.array(wasser_vertieft.vertiefen(Image.fromarray(ag), np.ones_like(mg), frame, maske=mg, stufen=[]).convert('RGB'))   # schmaler Bach: keine Tiefenstufen (sonst Loecher)
    a = ag[P:-P, P:-P].copy()
    a[wand] = vor_bach[wand]                                         # Mauerfronten bleiben (Bach laeuft im Guertel davor)
    img_b = Image.fromarray(a).convert('RGBA')
    for (bx0, by0, bx1, by1) in lay['bruecken']:
        bauwerke.zeichne_bruecke(img_b, bx0 * T - 6, (bx1 + 1) * T + 6, by0 * T, (by1 + 1) * T - 4, frame=frame or 0)
    a = np.array(img_b.convert('RGB'))
    bm = np.zeros((Hp, Wp), bool)
    for (bx0, by0, bx1, by1) in lay['bruecken']:
        bm[by0 * T:(by1 + 1) * T, bx0 * T:(bx1 + 1) * T] = True
    xm &= ~bm                                                        # Bruecken begehbar
    for tp in lay['teleporter']:
        k4.teleporter_zeichnen(a, tp['x'], tp['y'], tp['b'], tp['h'], frame)
    img = Image.fromarray(a).convert('RGBA')
    lvl = hp.astype(np.uint8) + 1
    lvl[wand] = 9                                                    # Felsfront = Wand (Kollision, Schatten)
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain_basis.png'))
        np.save(os.path.join(KARTE, 'pixelhoehe.npy'), lvl)
        np.save(os.path.join(KARTE, 'wand.npy'), np.packbits(wand))
        np.save(os.path.join(KARTE, 'wasser.npy'), np.packbits(xm))

    pf = os.path.join(OBJ, 'platzierung.json')
    if os.path.exists(pf):
        objs = sorted((o for o in json.load(open(pf)) if os.path.exists(os.path.join(OBJ, o['datei']))),
                      key=lambda o: o.get('sortier', o['y'] + o['fuss']))
        if objs:
            cache = {o['datei']: Image.open(os.path.join(OBJ, o['datei'])).convert('RGBA') for o in objs}
            ebenen = lvl.copy().astype(np.int16)
            ebenen[wand] = 9
            ebenen[xm] = 7
            k4.objekte_zeichnen(img, objs, cache, ~xm & ~wand, frame, ebenen=ebenen)
            k4.animieren(img, objs, cache, frame or 0)
            # Einbettung (Regel): Grasbueschel an den Sockelecken der Huetten, damit sie im Boden sitzen
            for o in objs:
                if not (o['basis'].startswith('h') and len(o['basis']) == 3):
                    continue
                al_ = np.array(cache[o['datei']].getchannel('A')) > 0
                zl_ = np.nonzero(al_.any(1))[0].max()
                xs_ = np.nonzero(al_[zl_ - 2:zl_ + 1].any(0))[0]
                ar_ = np.array(cache[o['datei']]).astype(int)
                b_ = ar_[ar_.shape[0] * 2 // 3:]
                md_ = (b_[..., 3] > 0) & (b_[..., 0] > 30) & (b_[..., 0] < 150) & (b_[..., 1] < 100) & \
                      (b_[..., 2] < 80) & (b_[..., 0] > b_[..., 2] + 10)
                tuer_ = np.nonzero(md_.sum(0) >= 6)[0] + o['x'] if md_.sum() > 10 else np.array([-999])   # Tuer: hohe braune Spalten
                for j_ in (0, 1):
                    sp_ = halme[0][:, ::-1] if j_ == 0 else halme[0]               # kurzes Bueschel, nicht vor der Tuer
                    hh_, ww_ = sp_.shape[:2]
                    bx_ = o['x'] + xs_.min() - ww_ + 5 if j_ == 0 else o['x'] + xs_.max() - 4   # aussen an den Ecken
                    py_ = o['y'] + zl_ - hh_ + 3
                    if ((tuer_ >= bx_ - 2) & (tuer_ <= bx_ + ww_ + 2)).any():
                        continue                                                     # nie vor der Tuer
                    st_ = Image.fromarray(sp_.astype(np.uint8))
                    img.alpha_composite(st_, (int(bx_), int(py_)))
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain.png'))
    print('Karte 44 %dx%d gebaut' % (cols, rows))
    return img


if __name__ == '__main__':
    bauen()
