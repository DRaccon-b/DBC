"""Sauberes, wiederverwendbares Boden-Tileset der Startkarte (Karte 06) im Stil der Karte.

  python3 tools/karte06_autotiles.py   ->  maps/karte06/tileset_boden/ (+ karte06_tileset_boden.zip)

Aufbau (16 Kacheln breit, jede Gruppe ab einer neuen Reihe, wie ein klassisches Handheld-Tileset):
  Wasser (animiert)   3x3-Block (Aussenecken, Kanten, Mitte) | 2x2 Innenecken | 2 Diagonalen | Wasser-Varianten
  Teleporter (anim.)  wie auf der Karte
  Grundflaechen       Gras, Waldboden, Sand, Kopfstein, Platten (je alle Varianten)
  Waldboden / Sand / Kopfsteinplatz / Cyber-Platten: je 3x3 + Innenecken + Diagonalen (Uebergang auf Gras)
  Zaun, Steg          transparente Teile zum Ueberlagern

Die Uebergaenge sind Ecken-Kacheln: jede Kachel ist durch ihre vier Ecken (Material ja/nein) bestimmt; die
Kante liegt an den Kachelraendern immer gleich, dazwischen hat jede Kachel ihre eigene Welle -> alle Kacheln
mit gleichen Ecken sind austauschbar (5x5-Flaeche mit 3 Varianten je Kante, 3x3-Loch, Diagonalen). Gerendert
mit den Zeichenfunktionen der Karte (Saum am Weg, Bordstein + Schatten am Platz, Erdrand + Tiefe am Wasser).

boden_tileset.png            alle Kacheln (Standbild)
boden_tileset_animiert.png   nur die animierten Kacheln (Wasser, Teleporter) am selben Platz, 16 Bilder untereinander
animiert_frames/             die 16 Bilder einzeln
boden_tileset.json           je Kachel: Gruppe, Name, Ecken (TL TR BL BR), animiert
vorschau_beschriftet.png     2x mit Gitter und Gruppennamen
beispiel.png                 kleine Beispielkarte nur aus diesen Kacheln
"""
import json, math, os, random, shutil, sys, zipfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw

import karte06_bauen as k6
import karte04_bauen as k4
import bauwerke
import wasser_vertieft

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte06')
OUT = os.path.join(KARTE, 'tileset_boden')
T = 16
N = k6.N_FRAMES
BREITE = 16
DAUER = 170
H = k6.H


def textur(pfad, n, umf=None, form=(4, 4)):
    """Flaeche aus den Texturkacheln, Variante je Kachel wie auf der Karte."""
    ks = k6.kacheln(pfad, n, umf)
    R, C = form
    t = np.zeros((R * T, C * T, 3), np.uint8)
    for j in range(R):
        for i in range(C):
            t[j * T:(j + 1) * T, i * T:(i + 1) * T] = ks[(i * 7 + j * 13 + i * j) % len(ks)]
    return t, ks


def rollen(m, dy, dx):
    return np.roll(np.roll(m, dy, 0), dx, 1)


def feld(Vg, seed):
    """Materialwert je Pixel fuer ein Eckenraster Vg ((R+1) x (C+1), 1 = Material).
    Jedes Kachelviertel gehoert zu seiner Ecke; die Ecken werden je Kachel weich gerundet (Radius ~5 px) und die
    Kante bekommt eine sanfte Welle, die an den Kachelraendern auf 0 auslaeuft. Dadurch liegt die Kante an jedem
    Kachelrand an derselben Stelle (Mitte) -> alle Kacheln mit gleichen Ecken passen ueberall hin."""
    from PIL import ImageFilter
    Vg = np.array(Vg, np.float32)
    R, C = Vg.shape[0] - 1, Vg.shape[1] - 1
    a = np.zeros((R * T, C * T), np.float32)
    u = (np.arange(T) + 0.5) / T
    U, W = np.meshgrid(u, u)
    h = T // 2
    for j in range(R):
        for i in range(C):
            q = np.zeros((T, T), np.float32)
            q[:h, :h], q[:h, h:] = Vg[j, i], Vg[j, i + 1]
            q[h:, :h], q[h:, h:] = Vg[j + 1, i], Vg[j + 1, i + 1]
            gross = np.pad(q, T, mode='edge')
            weich = np.array(Image.fromarray((gross * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2.6)),
                             np.float32)[T:2 * T, T:2 * T] / 255.0
            rs = np.random.RandomState(seed * 1000 + j * 37 + i)
            p1, p2 = rs.rand() * 6.28, rs.rand() * 6.28
            welle = 0.10 * np.sin(math.pi * U) * np.sin(2 * math.pi * U * rs.choice((1, 2)) + p1) \
                + 0.10 * np.sin(math.pi * W) * np.sin(2 * math.pi * W * rs.choice((1, 2)) + p2)
            rand = (weich > 0.02) & (weich < 0.98)
            a[j * T:(j + 1) * T, i * T:(i + 1) * T] = weich + np.where(rand, welle, 0)
    return a


def uebergang(art, v, frame=None):
    """Rendert ein Materialfeld v (Werte 0..1, Rand der Flaeche = Gras) mit den Zeichenregeln der Karte."""
    R, C = v.shape[0] // T, v.shape[1] // T
    basis = os.path.join(ROOT, 'assets', 'basis')
    gras, _ = textur(os.path.join(basis, 'gras_%d.png'), 5, form=(R, C))
    a = gras.copy()
    m = v > 0.5
    if art == 'wald':
        a[m] = (gras[m] * np.array([0.62, 0.7, 0.66])).astype(np.uint8)
        kante = m & ~(rollen(m, 1, 0) & rollen(m, -1, 0) & rollen(m, 0, 1) & rollen(m, 0, -1))
        a[kante] = (gras[kante] * np.array([0.5, 0.58, 0.55])).astype(np.uint8)
    elif art == 'sand':
        sand, _ = textur(os.path.join(basis, 'sand_%d.png'), 5, form=(R, C))
        a[m] = sand[m]
        saum = ~m & (rollen(m, 1, 0) | rollen(m, -1, 0) | rollen(m, 0, 1) | rollen(m, 0, -1))
        a[saum] = (a[saum] * 0.78).astype(np.uint8)                  # dunkle Graskante am Weg
        hell = m & ~rollen(m, 1, 0)                                   # Lichtkante oben am Sand
        a[hell] = np.minimum(255, a[hell].astype(np.int16) + 18).astype(np.uint8)
    elif art == 'platz':
        kies, _ = textur(os.path.join(ROOT, 'assets', 'karte03', 'basis', 'kies_%d.png'), 5, k6.beige, form=(R, C))
        a[m] = kies[m]
        rand = m & ~(rollen(m, 1, 0) & rollen(m, -1, 0) & rollen(m, 0, 1) & rollen(m, 0, -1))
        a[rand] = H('#8a6a48')
        unten = m & ~rollen(m, -1, 0)
        for d in (1, 2):
            s_ = rollen(unten, d, 0) & ~m
            a[s_] = (a[s_] * 0.8).astype(np.uint8)
    elif art == 'cyber':
        k2 = os.path.join(ROOT, 'assets', 'karte02', 'basis')
        pl, _ = textur(os.path.join(k2, 'platz_%d.png'), 3,
                       lambda a_: a_ * np.array([0.82, 0.88, 1.0]) + np.array([20, 24, 30]), form=(R, C))
        a[m] = pl[m]
        rand = m & ~(rollen(m, 1, 0) & rollen(m, -1, 0) & rollen(m, 0, 1) & rollen(m, 0, -1))
        a[rand] = H('#3a4252')
    elif art == 'wasser':
        # fuer kombinierbare Kacheln: keine Tiefenstufen im Inneren, niedrigere Ufermauer -> alles, was vom Ufer
        # abhaengt, bleibt in den Randkacheln; jede Wassermitte passt neben jede Kante
        alt = (wasser_vertieft.STUFEN, wasser_vertieft.MAUER_H)
        wasser_vertieft.STUFEN, wasser_vertieft.MAUER_H = [], 5
        try:
            img = wasser_vertieft.vertiefen(Image.fromarray(a), np.ones_like(m), frame, maske=m)
        finally:
            wasser_vertieft.STUFEN, wasser_vertieft.MAUER_H = alt
        a = np.array(img.convert('RGB'))
    return a


# Bloecke je Uebergang (Eckenraster inkl. 1 Kachel Rand, der Rand wird nicht ausgeschnitten)
def bloecke():
    blob = np.zeros((8, 8), int)
    blob[2:6, 2:6] = 1                    # 5x5-Flaeche: Kacheln 1..5
    loch = np.ones((6, 6), int)
    loch[2:4, 2:4] = 0                    # 3x3-Loch: Kacheln 1..3
    diag1 = np.array([[1, 1, 0, 0], [1, 1, 0, 0], [0, 0, 1, 1], [0, 0, 1, 1]])
    diag2 = np.array([[0, 0, 1, 1], [0, 0, 1, 1], [1, 1, 0, 0], [1, 1, 0, 0]])
    #        Raster, Seed, Ausschnitt (Kacheln x0,y0,x1,y1), Ziel (Spalte, Reihe), Name
    return [(blob, 1, (1, 1, 6, 6), (0, 0), 'Flaeche 5x5'),
            (loch, 2, (1, 1, 4, 4), (6, 0), 'Loch 3x3'),
            (diag1, 3, (1, 1, 2, 2), (6, 4), 'Diagonale'),
            (diag2, 4, (1, 1, 2, 2), (7, 4), 'Diagonale')]


NAMEN = {(0, 0, 0, 1): 'Aussenecke oben links', (0, 0, 1, 1): 'Kante oben', (0, 0, 1, 0): 'Aussenecke oben rechts',
         (0, 1, 0, 1): 'Kante links', (1, 1, 1, 1): 'Mitte', (1, 0, 1, 0): 'Kante rechts',
         (0, 1, 0, 0): 'Aussenecke unten links', (1, 1, 0, 0): 'Kante unten', (1, 0, 0, 0): 'Aussenecke unten rechts',
         (1, 1, 1, 0): 'Innenecke oben links', (1, 1, 0, 1): 'Innenecke oben rechts',
         (1, 0, 1, 1): 'Innenecke unten links', (0, 1, 1, 1): 'Innenecke unten rechts',
         (1, 0, 0, 1): 'Diagonale \\', (0, 1, 1, 0): 'Diagonale /', (0, 0, 0, 0): 'Gras'}


def set_kacheln(art, neu, gname, animiert):
    """Rendert alle Bloecke eines Uebergangs und traegt die Kacheln ein (5 Reihen hoch)."""
    for (Vg, seed, (x0, y0, x1, y1), (zs, zr), _) in bloecke():
        v = feld(Vg, seed + {'wasser': 10, 'wald': 20, 'sand': 30, 'platz': 40, 'cyber': 50}[art])
        st = uebergang(art, v, None)
        frs = [uebergang(art, v, f) for f in range(N)] if animiert else None
        for jj, y in enumerate(range(y0, y1)):
            for ii, x in enumerate(range(x0, x1)):
                e = (int(Vg[y][x]), int(Vg[y][x + 1]), int(Vg[y + 1][x]), int(Vg[y + 1][x + 1]))
                sl = (slice(y * T, (y + 1) * T), slice(x * T, (x + 1) * T))
                neu(gname, NAMEN[e], zs + ii, zr + jj, st[sl], [f[sl] for f in frs] if frs else None, e)


def transparent_teile(zeichnen, x0, y0, x1, y1):
    """Zeichnet etwas auf transparentem Grund und liefert den Kachelausschnitt (Reihen x Spalten)."""
    img = Image.new('RGBA', (k6.COLS * T, k6.ROWS * T), (0, 0, 0, 0))
    zeichnen(img)
    return np.array(img)[y0 * T:y1 * T, x0 * T:x1 * T]


def main():
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    eintraege = []                        # dict(gruppe, name, ecken, reihe, spalte, bild, frames)
    reihe = 0

    def neu(gruppe, name, sp, rh, bild, frames=None, ecken=None):
        eintraege.append({'gruppe': gruppe, 'name': name, 'spalte': sp, 'reihe': reihe + rh, 'bild': bild,
                          'frames': frames, 'ecken': ecken})
    # --- Wasser (animiert) ---
    set_kacheln('wasser', neu, 'Wasser', True)
    reihe += 5
    # --- Teleporter (animiert) aus der Karte ---
    import karte06_boden_export as be
    tp = lay['teleporter'][0]
    tx0, ty0, tx1, ty1 = tp['x'] - 1, tp['y'] - 1, tp['x'] + tp['b'] + 1, tp['y'] + tp['h'] + 1
    tx1 = min(tx1, k6.COLS)
    kb_stand = be.boden(None)
    kb_fr = [be.boden(f) for f in range(N)]
    for jj, y in enumerate(range(ty0, ty1)):
        for ii, x in enumerate(range(tx0, tx1)):
            sl = (slice(y * T, (y + 1) * T), slice(x * T, (x + 1) * T))
            neu('Teleporter', 'Teleporter %d,%d' % (ii, jj), ii, jj, kb_stand[sl][..., :3],
                [f[sl][..., :3] for f in kb_fr])
    reihe += ty1 - ty0
    anim_reihen = reihe
    # --- Grundflaechen ---
    basis = os.path.join(ROOT, 'assets', 'basis')
    gras = k6.kacheln(os.path.join(basis, 'gras_%d.png'), 5)
    gruppen = [('Gras', gras), ('Waldboden', [(g * np.array([0.62, 0.7, 0.66])).astype(np.uint8) for g in gras]),
               ('Sand', k6.kacheln(os.path.join(basis, 'sand_%d.png'), 5)),
               ('Kopfstein', k6.kacheln(os.path.join(ROOT, 'assets', 'karte03', 'basis', 'kies_%d.png'), 5, k6.beige)),
               ('Platten', k6.kacheln(os.path.join(ROOT, 'assets', 'karte02', 'basis', 'platz_%d.png'), 3,
                                      lambda a_: a_ * np.array([0.82, 0.88, 1.0]) + np.array([20, 24, 30])))]
    sp = 0
    for name, ks in gruppen:
        for v, t in enumerate(ks):
            neu('Grundflaechen', '%s %d' % (name, v + 1), sp % BREITE, sp // BREITE, t)
            sp += 1
    reihe += (sp + BREITE - 1) // BREITE
    # --- Uebergaenge auf Gras (je 5 Reihen: Flaeche 5x5 | Loch 3x3 | Diagonalen) ---
    for art, gname in (('wald', 'Waldboden'), ('sand', 'Sand (Weg, Spielplatz)'), ('platz', 'Kopfsteinplatz'),
                       ('cyber', 'Cyber-Platten')):
        set_kacheln(art, neu, gname, False)
        reihe += 5
    # --- Zaun (transparent): kompletter kleiner Zaun mit Tor als Block (alle Teile in ihrer Lage) ---
    z = transparent_teile(lambda im: k6.zaun(im, [1, 2, 9, 6], [4, 5]), 0, 0, 12, 9)
    ys, xs = np.nonzero(z[..., 3])
    zx0, zx1, zy0, zy1 = xs.min() // T, xs.max() // T + 1, ys.min() // T, ys.max() // T + 1
    for jj, y in enumerate(range(zy0, zy1)):
        for ii, x in enumerate(range(zx0, zx1)):
            neu('Zaun (transparent)', 'Zaun %d,%d' % (ii, jj), ii, jj, z[y * T:(y + 1) * T, x * T:(x + 1) * T])
    reihe += int(zy1 - zy0)
    # --- Steg (transparent, als zusammenhaengender Block) ---
    sx0, sy0, sx1, sy1 = lay['steg']
    st = transparent_teile(lambda im: bauwerke.zeichne_steg(im, sx0 * T, (sx1 + 1) * T, sy0 * T, (sy1 + 1) * T - 5,
                                                            frame=0), 0, 0, k6.COLS, k6.ROWS)
    ys, xs = np.nonzero(st[..., 3])
    bx0, bx1, by0, by1 = xs.min() // T, xs.max() // T + 1, ys.min() // T, ys.max() // T + 1
    for jj, y in enumerate(range(by0, by1)):
        for ii, x in enumerate(range(bx0, bx1)):
            neu('Steg (transparent)', 'Steg %d,%d' % (ii, jj), ii, jj, st[y * T:(y + 1) * T, x * T:(x + 1) * T])
    reihe += int(by1 - by0)
    gesamt = reihe
    # --- Bilder zusammensetzen ---
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(os.path.join(OUT, 'animiert_frames'))
    ts = np.zeros((gesamt * T, BREITE * T, 4), np.uint8)

    def rgba(t):
        return t if t.shape[2] == 4 else np.dstack([t, np.full(t.shape[:2], 255, np.uint8)])
    for e in eintraege:
        ts[e['reihe'] * T:(e['reihe'] + 1) * T, e['spalte'] * T:(e['spalte'] + 1) * T] = rgba(e['bild'])
    Image.fromarray(ts).save(os.path.join(OUT, 'boden_tileset.png'))
    ah = anim_reihen * T
    sheet = np.zeros((ah * N, BREITE * T, 4), np.uint8)
    gif = []
    for f in range(N):
        fr_ = np.zeros((ah, BREITE * T, 4), np.uint8)
        for e in eintraege:
            if e['frames'] is not None:
                fr_[e['reihe'] * T:(e['reihe'] + 1) * T, e['spalte'] * T:(e['spalte'] + 1) * T] = rgba(e['frames'][f])
        Image.fromarray(fr_).save(os.path.join(OUT, 'animiert_frames', 'frame_%02d.png' % f))
        sheet[f * ah:(f + 1) * ah] = fr_
        g = Image.new('RGBA', (BREITE * T, ah), (40, 44, 52, 255))
        g.alpha_composite(Image.fromarray(fr_))
        gif.append(g.resize((g.width * 3, g.height * 3), Image.NEAREST).convert('RGB')
                   .quantize(colors=255, method=Image.Quantize.MAXCOVERAGE))
    Image.fromarray(sheet).save(os.path.join(OUT, 'boden_tileset_animiert.png'))
    gif[0].save(os.path.join(OUT, 'vorschau_animiert.gif'), save_all=True, append_images=gif[1:], duration=DAUER,
                loop=0)
    # beschriftete Vorschau
    S = 3
    links = 190
    v = Image.new('RGBA', (links + BREITE * T * S, gesamt * T * S), (40, 44, 52, 255))
    v.alpha_composite(Image.fromarray(ts).resize((BREITE * T * S, gesamt * T * S), Image.NEAREST), (links, 0))
    va = np.array(v)
    for y in range(0, gesamt * T * S, T * S):
        va[y, links:] = (va[y, links:] * 0.55).astype(np.uint8)
    for x in range(links, v.width, T * S):
        va[:, x] = (va[:, x] * 0.55).astype(np.uint8)
    v = Image.fromarray(va)
    dr = ImageDraw.Draw(v)
    gesehen = set()
    for e in eintraege:
        if e['gruppe'] not in gesehen:
            gesehen.add(e['gruppe'])
            y = e['reihe'] * T * S
            dr.line((0, y, v.width, y), fill=(255, 210, 90, 255))
            dr.text((8, y + 6), e['gruppe'], fill=(255, 255, 255, 255))
            if e['frames'] is not None:
                dr.text((8, y + 20), '(animiert)', fill=(140, 220, 255, 255))
    v.save(os.path.join(OUT, 'vorschau_beschriftet.png'))
    # Beispielkarte aus den Kacheln: Eckenraster mit Wald, Sand, Platz, Wasser
    beispiel(eintraege)
    json.dump({'kachel': T, 'breite_kacheln': BREITE, 'reihen': gesamt, 'animationsbereich_reihen': anim_reihen,
               'animationsbilder': N, 'bilddauer_ms': DAUER,
               'ecken_hinweis': 'Ecken = (oben links, oben rechts, unten links, unten rechts), 1 = Material',
               'kacheln': [{'gruppe': e['gruppe'], 'name': e['name'], 'spalte': int(e['spalte']),
                            'reihe': int(e['reihe']), 'index': int(e['reihe'] * BREITE + e['spalte']),
                            'ecken': e['ecken'],
                            'animiert': e['frames'] is not None} for e in eintraege]},
              open(os.path.join(OUT, 'boden_tileset.json'), 'w'), indent=1, ensure_ascii=False)
    with zipfile.ZipFile(os.path.join(KARTE, 'karte06_tileset_boden.zip'), 'w', zipfile.ZIP_DEFLATED) as z:
        for wurzel, _, dateien in os.walk(OUT):
            for d in dateien:
                p = os.path.join(wurzel, d)
                z.write(p, os.path.relpath(p, KARTE))
    print('%d Kacheln, %d Reihen (davon %d animiert)' % (len(eintraege), gesamt, anim_reihen))


def beispiel(eintraege):
    """Kleine Beispielkarte (24x14) nur aus Tileset-Kacheln, zur Kontrolle der Nahtlosigkeit."""
    W, Hh = 24, 14
    nach = {}
    for e in eintraege:
        if e['ecken'] is not None:
            nach.setdefault((e['gruppe'], tuple(e['ecken'])), []).append(e['bild'])
    gras = next(e['bild'] for e in eintraege if e['name'] == 'Gras 1')
    bild = np.zeros((Hh * T, W * T, 3), np.uint8)
    for y in range(Hh):
        for x in range(W):
            bild[y * T:(y + 1) * T, x * T:(x + 1) * T] = gras
    rs = random.Random(2)

    def flaeche(gruppe, ecken_fn):
        for y in range(Hh):
            for x in range(W):
                e = tuple(int(ecken_fn(x + dx, y + dy)) for (dx, dy) in ((0, 0), (1, 0), (0, 1), (1, 1)))
                if any(e):
                    bild[y * T:(y + 1) * T, x * T:(x + 1) * T] = rs.choice(nach[(gruppe, e)])[..., :3]
    flaeche('Waldboden', lambda x, y: x <= 3 or y <= 1 or (x <= 5 and y >= 10))
    flaeche('Sand (Weg, Spielplatz)', lambda x, y: (8 <= x <= 10 and y >= 3) or (8 <= x <= 22 and 6 <= y <= 7))
    flaeche('Kopfsteinplatz', lambda x, y: 13 <= x <= 18 and 1 <= y <= 4)
    flaeche('Wasser', lambda x, y: (14 <= x <= 19 and 9 <= y <= 12) or (17 <= x <= 21 and 10 <= y <= 13))
    flaeche('Cyber-Platten', lambda x, y: 2 <= x <= 5 and 3 <= y <= 7)
    Image.fromarray(bild).resize((W * T * 2, Hh * T * 2), Image.NEAREST).save(os.path.join(OUT, 'beispiel.png'))


if __name__ == '__main__':
    main()
