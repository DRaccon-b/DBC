"""Sauberes, wiederverwendbares Boden-Tileset der Startkarte (Karte 06) im Stil der Karte.

  python3 tools/karte06_autotiles.py   ->  maps/karte06/tileset_boden/ (+ karte06_tileset_boden.zip)

Aufbau (16 Kacheln breit, jede Gruppe ab einer neuen Reihe, wie ein klassisches Handheld-Tileset):
  Wasser (animiert)   3x3-Block (Aussenecken, Kanten, Mitte) | 2x2 Innenecken | 2 Diagonalen | Wasser-Varianten
  Teleporter (anim.)  wie auf der Karte
  Grundflaechen       Gras, Waldboden, Sand, Kopfstein, Platten (je alle Varianten)
  Waldboden / Sand / Kopfsteinplatz / Cyber-Platten: je 3x3 + Innenecken + Diagonalen (Uebergang auf Gras)
  Zaun, Steg          transparente Teile zum Ueberlagern

Die Uebergaenge sind Ecken-Wang-Kacheln: jede Kachel ist durch ihre vier Ecken (Material ja/nein) bestimmt,
alle passen nahtlos aneinander. Sie werden auf einem nahtlosen 4x4-Torus aller 16 Eckkombinationen mit den
Zeichenfunktionen der Karte gerendert (Saum am Weg, Bordstein + Schatten am Platz, Erdrand + Tiefe am Wasser).

boden_tileset.png            alle Kacheln (Standbild)
boden_tileset_animiert.png   nur die animierten Kacheln (Wasser, Teleporter) am selben Platz, 16 Bilder untereinander
animiert_frames/             die 16 Bilder einzeln
boden_tileset.json           je Kachel: Gruppe, Name, Ecken (TL TR BL BR), animiert
vorschau_beschriftet.png     2x mit Gitter und Gruppennamen
beispiel.png                 kleine Beispielkarte nur aus diesen Kacheln
"""
import itertools, json, math, os, random, shutil, sys, zipfile
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


# ---------------------------------------------------------------- Ecken-Wang: nahtloser 4x4-Torus
def torus():
    for bits in range(1 << 16):
        V = [[(bits >> (j * 4 + i)) & 1 for i in range(4)] for j in range(4)]
        combos = set()
        for j in range(4):
            for i in range(4):
                combos.add((V[j][i], V[j][(i + 1) % 4], V[(j + 1) % 4][i], V[(j + 1) % 4][(i + 1) % 4]))
        if len(combos) == 16:
            return V
    raise SystemExit('kein Torus')


V = torus()
ECKEN = {}                                     # (TL,TR,BL,BR) -> (i, j) im Torus
for j in range(4):
    for i in range(4):
        ECKEN[(V[j][i], V[j][(i + 1) % 4], V[(j + 1) % 4][i], V[(j + 1) % 4][(i + 1) % 4])] = (i, j)
RAUSCH = np.random.RandomState(4).rand(T, T)


def wert_feld():
    """Materialwert 0..1 je Pixel auf dem 64x64-Torus (bilinear aus den Ecken + kachelperiodische Welle)."""
    a = np.zeros((4 * T, 4 * T), np.float32)
    u = (np.arange(T) + 0.5) / T
    U, Vv = np.meshgrid(u, u)
    welle = 0.07 * np.sin(2 * math.pi * U) + 0.04 * np.sin(4 * math.pi * U + 1.0) \
        + 0.07 * np.sin(2 * math.pi * Vv + 0.5) + 0.04 * np.sin(4 * math.pi * Vv + 2.0)
    for (tl, tr, bl, br), (i, j) in ECKEN.items():
        b = tl * (1 - U) * (1 - Vv) + tr * U * (1 - Vv) + bl * (1 - U) * Vv + br * U * Vv
        rand = (b > 0.05) & (b < 0.95)
        v = b + np.where(rand, welle + 0.08 * (RAUSCH - 0.5), 0)
        a[j * T:(j + 1) * T, i * T:(i + 1) * T] = v
    return a


def textur(pfad, n, umf=None, var=0):
    ks = k6.kacheln(pfad, n, umf)
    return np.tile(ks[var % len(ks)], (4, 4, 1)), ks


def rollen(m, dy, dx):
    return np.roll(np.roll(m, dy, 0), dx, 1)


def uebergang(art, frame=None):
    """Rendert den 64x64-Torus fuer ein Material auf Gras."""
    basis = os.path.join(ROOT, 'assets', 'basis')
    gras, _ = textur(os.path.join(basis, 'gras_%d.png'), 5)
    a = gras.copy()
    v = wert_feld()
    m = v > 0.5
    if art == 'wald':
        a[m] = (gras[m] * np.array([0.62, 0.7, 0.66])).astype(np.uint8)
    elif art == 'sand':
        sand, _ = textur(os.path.join(basis, 'sand_%d.png'), 5)
        a[m] = sand[m]
        saum = (v > 0.36) & ~m
        a[saum] = (a[saum] * 0.9).astype(np.uint8)
    elif art == 'platz':
        kies, _ = textur(os.path.join(ROOT, 'assets', 'karte03', 'basis', 'kies_%d.png'), 5, k6.beige)
        a[m] = kies[m]
        rand = m & ~(rollen(m, 1, 0) & rollen(m, -1, 0) & rollen(m, 0, 1) & rollen(m, 0, -1))
        a[rand] = H('#8a6a48')
        unten = m & ~rollen(m, -1, 0)
        for d in (1, 2):
            s = rollen(unten, d, 0) & ~m
            a[s] = (a[s] * 0.8).astype(np.uint8)
    elif art == 'cyber':
        k2 = os.path.join(ROOT, 'assets', 'karte02', 'basis')
        pl, _ = textur(os.path.join(k2, 'platz_%d.png'), 3,
                       lambda a_: a_ * np.array([0.82, 0.88, 1.0]) + np.array([20, 24, 30]))
        a[m] = pl[m]
        rand = m & ~(rollen(m, 1, 0) & rollen(m, -1, 0) & rollen(m, 0, 1) & rollen(m, 0, -1))
        a[rand] = H('#3a4252')
    elif art == 'wasser':
        # 3x3 gekachelt rendern (Umgebung stimmt an jedem Rand), Mitte ausschneiden
        g3 = np.tile(a, (3, 3, 1))
        m3 = np.tile(m, (3, 3))
        img = wasser_vertieft.vertiefen(Image.fromarray(g3), np.ones_like(m3), frame, maske=m3)
        a = np.array(img.convert('RGB'))[4 * T:8 * T, 4 * T:8 * T]
    return a


def kachel(tor, ecken):
    i, j = ECKEN[ecken]
    return tor[j * T:(j + 1) * T, i * T:(i + 1) * T]


# Anordnung eines Uebergangs-Sets: (Spalte, Reihe, Name, Ecken)
SET = [(0, 0, 'Aussenecke oben links', (0, 0, 0, 1)), (1, 0, 'Kante oben', (0, 0, 1, 1)),
       (2, 0, 'Aussenecke oben rechts', (0, 0, 1, 0)),
       (0, 1, 'Kante links', (0, 1, 0, 1)), (1, 1, 'Mitte', (1, 1, 1, 1)), (2, 1, 'Kante rechts', (1, 0, 1, 0)),
       (0, 2, 'Aussenecke unten links', (0, 1, 0, 0)), (1, 2, 'Kante unten', (1, 1, 0, 0)),
       (2, 2, 'Aussenecke unten rechts', (1, 0, 0, 0)),
       (3, 0, 'Innenecke oben links', (1, 1, 1, 0)), (4, 0, 'Innenecke oben rechts', (1, 1, 0, 1)),
       (3, 1, 'Innenecke unten links', (1, 0, 1, 1)), (4, 1, 'Innenecke unten rechts', (0, 1, 1, 1)),
       (3, 2, 'Diagonale \\', (1, 0, 0, 1)), (4, 2, 'Diagonale /', (0, 1, 1, 0))]


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
    stand = uebergang('wasser', None)
    fr = [uebergang('wasser', f) for f in range(N)]
    for (sp, rh, name, e) in SET:
        neu('Wasser', name, sp, rh, kachel(stand, e), [kachel(f, e) for f in fr], e)
    # Wasser-Varianten: die reine Wassermitte gibt es nur einmal (Torus), dazu Ufer-Varianten nicht noetig
    reihe += 3
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
    # --- Uebergaenge auf Gras ---
    for art, gname in (('wald', 'Waldboden'), ('sand', 'Sand (Weg, Spielplatz)'), ('platz', 'Kopfsteinplatz'),
                       ('cyber', 'Cyber-Platten')):
        tor = uebergang(art)
        for (sp, rh, name, e) in SET:
            neu(gname, name, sp, rh, kachel(tor, e), ecken=e)
        reihe += 3
    # --- Zaun (transparent): Ausschnitt um die linke obere Ecke, das Tor und die rechte untere Ecke ---
    px0, py0, px1, py1 = lay['pension']
    tor_ = lay['pension_tor']
    zaun = transparent_teile(lambda im: k6.zaun(im, lay['pension'], tor_), 0, 0, k6.COLS, k6.ROWS)

    def teil(x, y):
        return zaun[y * T:(y + 1) * T, x * T:(x + 1) * T]
    zaun_teile = [('Ecke oben links', px0, py0 - 1), ('Ecke oben links unten', px0, py0),
                  ('Latte oben', px0 + 1, py0 - 1), ('Latte', px0 + 1, py0),
                  ('Torende links oben', tor_[0] - 1, py0 - 1), ('Torende links', tor_[0] - 1, py0),
                  ('Torende rechts oben', tor_[1] + 1, py0 - 1), ('Torende rechts', tor_[1] + 1, py0),
                  ('Ecke oben rechts', px1, py0 - 1), ('Ecke oben rechts unten', px1, py0),
                  ('Seite links', px0, py0 + 2), ('Seite rechts', px1, py0 + 2),
                  ('Ecke unten links oben', px0, py1 - 1), ('Ecke unten links', px0, py1),
                  ('Latte unten oben', px0 + 2, py1 - 1), ('Latte unten', px0 + 2, py1),
                  ('Ecke unten rechts oben', px1, py1 - 1), ('Ecke unten rechts', px1, py1)]
    sp = 0
    for name, x, y in zaun_teile:
        t = teil(x, y)
        if t[..., 3].any():
            neu('Zaun (transparent)', name, sp % BREITE, sp // BREITE, t)
            sp += 1
    reihe += (sp + BREITE - 1) // BREITE
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
            nach[(e['gruppe'], e['ecken'])] = e['bild']
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
                    bild[y * T:(y + 1) * T, x * T:(x + 1) * T] = nach[(gruppe, e)][..., :3]
    flaeche('Waldboden', lambda x, y: x <= 3 or y <= 1 or (x <= 5 and y >= 10))
    flaeche('Sand (Weg, Spielplatz)', lambda x, y: (8 <= x <= 10 and y >= 3) or (8 <= x <= 22 and 6 <= y <= 7))
    flaeche('Kopfsteinplatz', lambda x, y: 13 <= x <= 18 and 1 <= y <= 4)
    flaeche('Wasser', lambda x, y: (14 <= x <= 19 and 9 <= y <= 12) or (17 <= x <= 21 and 10 <= y <= 13))
    flaeche('Cyber-Platten', lambda x, y: 2 <= x <= 5 and 3 <= y <= 7)
    Image.fromarray(bild).resize((W * T * 2, Hh * T * 2), Image.NEAREST).save(os.path.join(OUT, 'beispiel.png'))


if __name__ == '__main__':
    main()
