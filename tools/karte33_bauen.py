"""Karte 33 (The World of Dreams, A02): Gelaende.

Runde Traumplattform in der Sternenleere (Leere und Fundamentrand wie Karte 32): lavendelfarbene Platten, heller
Randstein, Rautenring und Mittelquadrat aus dunkleren Ringplatten, drei lila glimmende Runen auf dem Ring, Steg nach
Sueden mit Ankunftsfeldern (Pfeilfelder wie Karte 16). Schwebende Traumobjekte bewegen sich 1 px auf und ab.

  python3 tools/karte33_layout.py && python3 tools/karte33_kacheln.py && python3 tools/karte33_bauen.py
  python3 tools/karte33_objekte.py && python3 tools/karte33_bauen.py
"""
import json, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
import karte_bauen as kb
import karte04_bauen as k4
import karte08_bauen as k8
import karte16_bauen as k16
import karte32_bauen as k32

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte33')
BASIS = os.path.join(ROOT, 'assets', 'karte33', 'basis')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte33')
T = 16
N_FRAMES = 4                     # Regel: hoechstens 4 Animationsbilder
BILDDAUER = 250
k4.N_FRAMES = kb.N_FRAMES = k32.N_FRAMES = N_FRAMES
H = k4.H
gross = k32.gross


def textur(art, cols, rows):
    t = np.zeros((rows * T, cols * T, 3), np.uint8)
    ks = [np.array(Image.open(os.path.join(BASIS, '%s_%d.png' % (art, v))).convert('RGB')) for v in range(5)]
    for y in range(rows):
        for x in range(cols):
            t[y * T:(y + 1) * T, x * T:(x + 1) * T] = ks[kb.variante(x, y)]
    return t


def ring_kante(a, m):
    """Ringplatten liegen leicht vertieft: oben/links dunkle Kante, unten/rechts helle Kante (Licht oben links)."""
    oben = m & ~np.roll(m, 1, 0); links = m & ~np.roll(m, 1, 1)
    unten = m & ~np.roll(m, -1, 0); rechts = m & ~np.roll(m, -1, 1)
    a[oben | links] = (a[oben | links] * 0.7).astype(np.uint8)
    a[unten | rechts] = np.clip(a[unten | rechts].astype(int) + 26, 0, 255).astype(np.uint8)


def rune(a, cx, cy, frame):
    """Lila Rune: ovales Glyphenfeld mit innerem Kreis, glimmt im Takt (4 Bilder). cx, cy in Pixeln."""
    f = 0.6 + 0.4 * math.sin(2 * math.pi * ((frame or 0) / N_FRAMES))
    Hp, Wp = a.shape[:2]
    for y in range(cy - 12, cy + 13):
        for x in range(cx - 14, cx + 15):
            if not (0 <= y < Hp and 0 <= x < Wp):
                continue
            d = ((x - cx) / 7.0) ** 2 + ((y - cy) / 4.5) ** 2
            if d <= 1.0:
                c = np.array([70, 30, 120]) if d > 0.55 else np.array([120, 60, 200])
                if 0.25 < d < 0.4:
                    c = np.array([200, 150, 255])
                a[y, x] = np.clip(c * (0.75 + 0.35 * f), 0, 255).astype(np.uint8)
            elif d <= 2.6:                                           # weicher Schein auf den Platten
                t_ = (1 - (d - 1) / 1.6) * 0.35 * f
                a[y, x] = np.clip(a[y, x] * (1 - t_) + np.array([170, 110, 255]) * t_, 0, 255).astype(np.uint8)


def ringmauer(a, wm):
    """Massive Ringmauer, ueberall 1 Kachel breit (Nutzer): oben eine Abdeckung (Decke) aus glatten, hellen
    Deckplatten mit Fugen, Lichtkante oben/links und dunkler Kante rechts; unter jeder Suedkante die Mauerwand aus
    Ziegellagen (13 px), direkt unter der Abdeckung eine Schattenfuge (die Platte steht ueber), unten die Fusskante und
    3 px Schatten auf dem Boden davor. Seitlich nur Kontur. -> Maske der Wand."""
    Hp, Wp = wm.shape
    yy, xx = np.mgrid[0:Hp, 0:Wp]
    WH = 13
    # Abdeckung: Platten 16x8 versetzt, sehr ruhig
    platte = ((yy // 8) % 2 == 0)
    a[wm] = np.where(platte[wm][:, None], H('#bcb6dc'), H('#b4aed6'))
    fuge = wm & ((yy % 8 == 7) | (((xx + 8 * ((yy // 8) % 2)) % 16) == 15))
    a[fuge] = H('#9a94c2')
    a[wm & ~np.roll(wm, 1, 0)] = H('#e4e0f6')                         # Lichtkante oben
    a[wm & ~np.roll(wm, 1, 1)] = H('#d4d0ee')                         # Lichtkante links
    a[wm & ~np.roll(wm, -1, 1)] = H('#5a5486')                        # Schattenkante rechts
    a[wm & ~np.roll(wm, 1, 1) & ~np.roll(wm, 1, 0)] = H('#eeeaf9')
    unterkante = wm & ~np.roll(wm, -1, 0)
    a[unterkante] = H('#7a74a6')                                      # Plattenkante vorn
    # Mauerwand unter den Suedkanten
    wand = np.zeros_like(wm)
    dist = np.zeros((Hp, Wp), np.int16)
    for y, x in zip(*np.nonzero(unterkante)):
        for d in range(1, WH + 1):
            if y + d < Hp and not wm[y + d, x]:
                wand[y + d, x] = True
                dist[y + d, x] = d
    reihe = (dist - 1) // 4
    ziegel = (xx + np.where(reihe % 2 == 1, 6, 0)) % 12
    basis = np.where(((xx // 12 + reihe) % 3 == 0)[..., None], H('#625c8e'), H('#6a6496'))
    a[wand] = basis[wand]
    a[wand & (((dist - 1) % 4 == 3) | (ziegel == 11))] = H('#4a4474')          # Fugen
    a[wand & ((dist - 1) % 4 == 0) & (ziegel != 11)] = H('#7a74a8')            # Lichtkante je Lage
    a[wand & (dist <= 2)] = H('#3a345e')                                       # Schattenfuge unter der Abdeckung
    a[wand & (dist == WH)] = H('#2e2a4c')                                      # Fusskante
    links = wand & ~np.roll(wand, 1, 1)
    rechts = wand & ~np.roll(wand, -1, 1)
    a[links] = H('#8680b0'); a[rechts] = H('#2e2a4c')
    for k_, fa in ((1, 0.58), (2, 0.72), (3, 0.86)):                  # Schatten auf den Boden vor der Wand
        m_ = np.roll(wand & ~np.roll(wand, -1, 0), k_, 0) & ~wm & ~wand
        a[m_] = (a[m_] * fa).astype(np.uint8)
    return wand


_QUELLEN = {}


def quellbild(karte, frame):
    """Bild der Quellkarte fuer den Riss: im Standbild terrain.png, in der Animation das passende Bild aus der
    fertigen Animation der Karte (Wasser, Fernseher-Wirbel, Wind bewegen sich auch im Riss)."""
    schluessel = (karte, None if frame is None else frame % N_FRAMES)
    if schluessel not in _QUELLEN:
        anim = os.path.join(ROOT, 'maps', karte, 'animation', '%s_animiert%s.webp' % (karte, '_16' if N_FRAMES == 16 else ''))
        if frame is not None and os.path.exists(anim):
            im = Image.open(anim)                                     # Quelle mit gleicher Bildzahl (4 bzw. 16)
            im.seek(frame * getattr(im, 'n_frames', 1) // N_FRAMES % getattr(im, 'n_frames', 1))
            _QUELLEN[schluessel] = np.array(im.convert('RGB'))
        else:
            _QUELLEN[schluessel] = np.array(Image.open(os.path.join(ROOT, 'maps', karte, 'terrain.png')).convert('RGB'))
    return _QUELLEN[schluessel]


def risse(a, lay, frame, land):
    """Raum-Zeit-Risse (Nutzer): die Ecken der Karte reissen entlang einer Kante auf (Nutzer-Skizze), dahinter ist ein
    Ausschnitt einer anderen A02-Karte im selben Massstab zu sehen (animiert aus deren Animation). Die Risskante liegt
    am 45-Grad-Raster (Kachelmaske, Gauss 5 px, Schwelle 50 % wie Regel 6b) und haelt 1 Kachel Abstand zur Plattform.
    Innen eine dunkle Tiefenkante, aussen eine leuchtende, flackernde Kante (weiss -> violett -> cyan) mit Funken.
    -> Maske aller Risse (fuer Objekte: frei halten)."""
    import random
    from PIL import ImageDraw, ImageFilter
    Hp, Wp = a.shape[:2]
    rows, cols = Hp // T, Wp // T
    gesamt = np.zeros((Hp, Wp), bool)
    f = frame or 0
    sperre = np.array(Image.fromarray((land * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(2 * T + 1))) > 0
    for i, r in enumerate(lay.get('risse', [])):
        poly = [tuple(p) for p in r['kante']]
        ex, ey = r['ecke']
        poly += [(ex, ey if ey == 0 else rows)] if False else []
        ecken = {(0, 0): [(0, 0)], (44, 0): [(cols, 0)], (0, 44): [(0, rows)], (44, 44): [(cols, rows)]}[(ex, ey)]
        flaeche = Image.new('L', (cols, rows), 0)
        ImageDraw.Draw(flaeche).polygon([(x - 0.5, y - 0.5) for (x, y) in poly + ecken], fill=255)
        kach = np.array(flaeche) > 0
        m = np.kron(kach, np.ones((T, T), np.uint8)).astype(np.uint8) * 255
        m = np.pad(m, T, mode='edge')                                   # Kartenrand: keine Kante dort
        m = np.array(Image.fromarray(m).filter(ImageFilter.GaussianBlur(5)))[T:-T, T:-T] > 127
        m &= ~sperre
        quelle = quellbild(r['karte'], frame)
        ys, xs = np.nonzero(m)
        bx0, by0 = xs.min(), ys.min()
        qx, qy = r['quelle']
        sy = np.clip(qy + ys - by0, 0, quelle.shape[0] - 1)
        sx = np.clip(qx + xs - bx0, 0, quelle.shape[1] - 1)
        a[ys, xs] = quelle[sy, sx]
        # Abstand zur Risskante innen/aussen (Pixel), ueber wiederholtes Erodieren/Dilatieren
        def ring(maske, n, wachsen):
            out = []
            cur = maske.copy()
            for _ in range(n):
                nb = np.roll(cur, 1, 0) | np.roll(cur, -1, 0) | np.roll(cur, 1, 1) | np.roll(cur, -1, 1) if wachsen \
                    else np.roll(cur, 1, 0) & np.roll(cur, -1, 0) & np.roll(cur, 1, 1) & np.roll(cur, -1, 1)
                neu = (nb & ~cur) if wachsen else (cur & ~nb)
                rand_ = np.zeros_like(neu); rand_[10:-10, 10:-10] = True  # am Kartenrand keine Kante
                out.append(neu & rand_)
                cur = nb if wachsen else (cur & nb)
            return out
        for k_, ringm in enumerate(ring(m, 5, False)):                 # dunkle Tiefenkante innen
            fa = 0.45 + 0.11 * k_
            a[ringm] = (a[ringm] * fa).astype(np.uint8)
        puls = 0.75 + 0.25 * math.sin(2 * math.pi * f / N_FRAMES + i * 1.3)
        aussen = ring(m, 7, True)
        for k_, ringm in enumerate(aussen):
            farbe, st = ((255, 250, 255), 1.0) if k_ < 1 else (((200, 140, 255), 0.85) if k_ < 3 else ((110, 200, 255), 0.5 - 0.08 * (k_ - 3)))
            al = st * puls
            ringm = ringm & ~land
            a[ringm] = np.clip(a[ringm] * (1 - al) + np.array(farbe) * al, 0, 255).astype(np.uint8)
        kante = aussen[2]
        ky, kx = np.nonzero(kante)
        rs = random.Random(3400 + i * 7 + f)                            # Funken an der Kante (wandern je Bild)
        for _ in range(min(26, len(ky))):
            j = rs.randrange(len(ky))
            py, px = ky[j] + rs.randint(-6, 6), kx[j] + rs.randint(-6, 6)
            if 1 <= px < Wp - 1 and 1 <= py < Hp - 1 and not m[py, px] and not land[py, px]:
                a[py, px] = (240, 220, 255)
                if rs.random() < 0.5:
                    a[py, px + 1] = a[py + 1, px] = (170, 120, 240)
        gesamt |= m
        for ringm in aussen:
            gesamt |= ringm
    return gesamt


def traumschein(img, objs, cache, frame):
    """Surreale Schwebeobjekte: weicher, pulsierender lila/cyan Schimmer hinter jedem Objekt und ein schwaches,
    verschobenes Nachbild (Geisterbild) darunter - vor dem eigentlichen Objekt gezeichnet."""
    from PIL import ImageDraw, ImageFilter
    f = frame or 0
    glow = Image.new('RGBA', img.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for i, o in enumerate(objs):
        if not o.get('schwebend'):
            continue
        sp = cache[o['datei']]
        bb = sp.getbbox()
        cx, cy = o['x'] + (bb[0] + bb[2]) / 2, o['y'] + (bb[1] + bb[3]) / 2
        r = max(bb[2] - bb[0], bb[3] - bb[1]) * 0.75
        p = 0.6 + 0.4 * math.sin(2 * math.pi * (f + o.get('phase', 0)) / N_FRAMES)
        farbe = (190, 120, 255) if i % 2 else (120, 210, 255)
        for k_, al in ((1.05, 52), (0.7, 72)):
            gd.ellipse((cx - r * k_, cy - r * k_, cx + r * k_, cy + r * k_), fill=farbe + (int(al * p),))
        geist = sp.copy()
        a_ = np.array(geist).astype(np.float32)
        a_[..., :3] = a_[..., :3] * 0.4 + np.array(farbe, np.float32) * 0.6
        a_[..., 3] *= 0.28
        img.alpha_composite(Image.fromarray(a_.astype(np.uint8)), (int(o['x']), int(o['y']) - 3))   # Nachbild darueber, im Gleichtakt (kein Schatten)
    img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(4)))


def bauen(frame=None, speichern=True):
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cols, rows = lay['groesse']
    kl = np.array([list(r) for r in lay['klassen']])
    Wp, Hp = cols * T, rows * T
    leer = gross(kl == '.')
    land = ~leer
    a = k32.leere(Hp, Wp, frame)
    rissmaske = risse(a, lay, frame, land)                            # Raum-Zeit-Risse in den Ecken
    for art in 'irmp':
        m = gross(kl == art)
        a[m] = textur(art, cols, rows)[m]
    am = gross(kl == 'a')
    a[am] = textur('p', cols, rows)[am]
    ring_kante(a, gross(kl == 'm'))
    stegkante = gross(kl == 'p') | am                                 # Steg: dunkle Seitenkanten
    sk = stegkante & (~np.roll(stegkante, 1, 1) | ~np.roll(stegkante, -1, 1))
    a[sk] = (a[sk] * 0.62).astype(np.uint8)
    for (cx, cy) in lay.get('runen_px', []):
        rune(a, cx, cy, frame)
    wm = gross(kl == 'w')
    fund = k32.fundament(a, land, leer, tiefe=12, seed=3333)
    front = ringmauer(a, wm)                                          # nach dem Fundament: Front liegt davor
    for i, x in enumerate(range(20, 24)):                             # Ankunftsfelder (wie Karte 16)
        for y in (42, 43):
            k16.pfeil_marke(a, x, y, np.array([110, 220, 255], np.float32), frame, i + y)
    lvl = np.ones((Hp, Wp), np.uint8)
    lvl[leer] = 0
    lvl[fund] = 9
    lvl[gross(kl == 'w')] = 2
    lvl[front] = 9
    if speichern and frame is None:
        np.save(os.path.join(KARTE, 'pixelhoehe.npy'), lvl)
    img = Image.fromarray(a).convert('RGBA')
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain_basis.png'))
    pf = os.path.join(OBJ, 'platzierung.json')
    if os.path.exists(pf):
        objs = sorted((o for o in json.load(open(pf)) if os.path.exists(os.path.join(OBJ, o['datei']))),
                      key=lambda o: o['y'] + o['fuss'])
        if frame is not None:
            for o in objs:
                if o.get('schwebend'):
                    o['y'] += (0, -1, -1, 0)[(frame * 4 // N_FRAMES + o.get('phase', 0)) % 4]   # ruhiges Schweben, eine Welle pro Schleife
        cache = {o['datei']: Image.open(os.path.join(OBJ, o['datei'])).convert('RGBA') for o in objs}
        k8.schatten_ebene(img, [o for o in objs if not o.get('schwebend') and not o.get('kein_schatten')], cache, lvl)
        traumschein(img, objs, cache, frame)
        k4.objekte_zeichnen(img, objs, cache, np.zeros((Hp, Wp), bool), frame)
        k4.animieren(img, objs, cache, frame or 0, ruhig=frame is None)
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain.png'))
    print('Karte 33 %dx%d gebaut' % (cols, rows))
    return img


if __name__ == '__main__':
    bauen()
