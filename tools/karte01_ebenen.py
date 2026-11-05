"""Karte 01 in drei Spiel-Ebenen zerlegen.

  python3 tools/karte01_ebenen.py   ->  maps/karte01/ebenen/

Je 16x16-Kachel eine Klasse:
  1 = begehbar          (Gras, Wege, Sand, Bruecken, Steg, Treppen, Gras/Farne/Blumen/Pilze/Kiesel)
  2 = nicht begehbar    (Wasser, Meer, Klippenwaende, Wald, Fuss von Baeumen/Felsen/Laternen/Gebaeuden)
  3 = begehbar, verdeckt den Spieler (Baumkronen, Laternenkoepfe, Daecher ueber begehbarem Boden)

Ausgabe:
  ebene1_boden.png           alles, was UNTER dem Spieler liegt (Boden, Klippen, Bauwerke, Objektfuesse, Schatten)
  ebene2_kollision.png       Maske: rote Kachel = nicht begehbar (dieselbe Information wie kollision.json)
  ebene3_ueberlagerung.png   transparent: alles, was UEBER dem Spieler liegt (obere Teile hoher Objekte)
  kollision.json / .txt      Kachelraster mit 1/2/3 (Zeile = y, Zeichen = x)
  vorschau.png               Karte mit eingefaerbten Klassen (rot = 2, blau = 3)
Zeichenreihenfolge im Spiel: ebene1_boden -> Spieler/NPCs -> ebene3_ueberlagerung.
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte01')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte01')
OUT = os.path.join(KARTE, 'ebenen')
T = 16
FUSS = 10          # unterste Pixelzeilen eines hohen Objekts: Fuss (blockiert, liegt unter dem Spieler)
BODENOBJEKTE = {'gross/14'}   # Feuerstelle mit Holzscheiten: liegt ganz am Boden
MIN_FUSS = 4       # ab so vielen Fusspixeln (Stamm, Mast, Sockel) ist eine Kachel blockiert
MIN_DECKT = 12     # ab so vielen deckenden Pixeln der Ueberlagerung verdeckt eine Kachel den Spieler
# begehbare Bodendeko (liegt unter dem Spieler): Gras, Farne, Schilf, Blumen, Pilze, Kiesel, Zweige
FLACH = {'deko/05', 'deko/06', 'deko/07', 'deko/08', 'deko/10', 'deko/14', 'deko/26', 'deko/27', 'deko/31',
         'deko/33', 'deko/61'}


PFLANZEN = ('baeume/', 'dschungel/', 'gross/00', 'gross/01', 'gross/02')


def ist_pflanze(o):
    return o.get('basis', '').startswith(PFLANZEN)


def stamm_maske(sp, o):
    """Stamm eines Baums: braune Pixel in den untersten 8 Zeilen des eigentlichen Sprites. Busch ohne
    sichtbaren Stamm: schmaler Ansatz (6 px) mittig in den untersten 5 Zeilen."""
    a = np.array(sp).astype(int)
    h = a.shape[0]
    deckend = a[..., 3] >= 128
    if 'block' in o:
        yb = (o['block'][1] + o['block'][3]) * T - 1 - o['y']
    else:
        yb = int(np.nonzero(deckend.any(axis=1))[0].max())
    yb = min(h - 1, yb)
    m = np.zeros(deckend.shape, bool)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    braun = deckend & (r > g + 8) & (r > b + 18)
    m[max(0, yb - 7):yb + 1] = braun[max(0, yb - 7):yb + 1]
    if m.sum() < 6:                              # Busch: Ansatz in der Mitte
        xs = np.nonzero(deckend[yb])[0]
        if len(xs):
            cx = (xs.min() + xs.max()) // 2
            m[max(0, yb - 4):yb + 1, max(0, cx - 3):cx + 3] = deckend[max(0, yb - 4):yb + 1, max(0, cx - 3):cx + 3]
    return m


def main():
    os.makedirs(OUT, exist_ok=True)
    g = json.load(open(os.path.join(KARTE, 'terrain_grid.json')))
    plan = json.load(open(os.path.join(KARTE, 'hoehenplan.json')))
    grid, cols, rows = g['grid'], g['cols'], g['rows']
    W, H = cols * T, rows * T

    # ---------------------------------------------------------------- Bildebenen
    boden = Image.open(os.path.join(KARTE, 'terrain_basis.png')).convert('RGBA')
    oben = Image.new('RGBA', boden.size, (0, 0, 0, 0))
    objs = sorted(json.load(open(os.path.join(OBJ, 'platzierung.json'))),
                  key=lambda o: (o.get('ebene', 1), o['y'] + o.get('fuss', 0)))
    cache = {}

    def sprite(o):
        if o['datei'] not in cache:
            cache[o['datei']] = Image.open(os.path.join(OBJ, o['datei'])).convert('RGBA')
        sp = cache[o['datei']]
        return sp.transpose(Image.FLIP_LEFT_RIGHT) if o.get('spiegeln') else sp

    # Bodenschatten wie in karte_bauen (gehoeren zum Boden)
    schatten = Image.new('L', boden.size, 0)
    sd = ImageDraw.Draw(schatten)
    for o in objs:
        if 'schatten' in o:
            w, h = o['schatten']
            cx, cy = o['x'] + sprite(o).width // 2, o['y'] + o['fuss'] - 2
            sd.ellipse((cx - w // 2, cy - h // 2, cx + w // 2, cy + h // 2), fill=95)
    dunkel = Image.new('RGBA', boden.size, (18, 52, 48, 255))
    dunkel.putalpha(schatten.filter(ImageFilter.GaussianBlur(1.2)))
    boden.alpha_composite(dunkel)

    blockiert_px = np.zeros((H, W), bool)       # Fuesse hoher Objekte
    for o in objs:
        sp = sprite(o)
        a = np.array(sp.getchannel('A'))
        zeilen = np.nonzero((a > 0).any(axis=1))[0]
        if not len(zeilen):
            continue
        if o.get('ebene', 1) == 0 or o.get('basis') in FLACH:      # flache Deko: Boden, begehbar
            boden.alpha_composite(sp, (o['x'], o['y']))
            continue
        if ist_pflanze(o):                       # Baum/Busch: nur der Stamm ist Boden + gesperrt, Rest ueber dem Spieler
            stamm = stamm_maske(sp, o)
            arr = np.array(sp)
            unten_ = arr.copy(); unten_[~stamm] = 0
            rest = arr.copy(); rest[stamm] = 0
            if 'block' in o:                     # Grasfuss/Schatten unter dem Block bleiben am Boden
                y_basis = (o['block'][1] + o['block'][3]) * T - 1 - o['y']
                unten_[y_basis + 1:] = arr[y_basis + 1:]
                rest[y_basis + 1:] = 0
            boden.alpha_composite(Image.fromarray(unten_), (o['x'], o['y']))
            oben.alpha_composite(Image.fromarray(rest), (o['x'], o['y']))
            ys, xs = np.nonzero(stamm)
            ys, xs = ys + o['y'], xs + o['x']
            ok = (ys >= 0) & (ys < H) & (xs >= 0) & (xs < W)
            blockiert_px[ys[ok], xs[ok]] = True
            continue
        # Fusstiefe: schmale Objekte (Stamm, Mast) 10 px, breite (Zelt, Staender) bis 2 Kacheln tief
        zu_ = int(zeilen.max())
        fussbreite = int((a[max(0, zu_ - 3):zu_ + 1] > 0).any(axis=0).sum())
        tiefe = int(min(32, max(FUSS, fussbreite * 0.4)))
        if zu_ - int(zeilen.min()) + 1 <= 28 or o.get('basis') in BODENOBJEKTE:   # flach: ganz Boden + gesperrt
            tiefe = zu_ - int(zeilen.min()) + 1
        trenn = zu_ + 1 - tiefe                # Zeile im Sprite: darueber Ueberlagerung, darunter Fuss
        fuss = sp.crop((0, trenn, sp.width, sp.height))
        kopf = sp.crop((0, 0, sp.width, trenn))
        boden.alpha_composite(fuss, (o['x'], o['y'] + trenn))
        oben.alpha_composite(kopf, (o['x'], o['y']))
        fa = np.array(fuss.getchannel('A')) >= 128
        ys, xs = np.nonzero(fa)
        ys, xs = ys + o['y'] + trenn, xs + o['x']
        ok = (ys >= 0) & (ys < H) & (xs >= 0) & (xs < W)
        if 'block' in o:                         # nur im eigenen Kachelblock sperren (Grasfuss ragt 2-3 px hinaus)
            bx, by, bw, bh = o['block']
            ok &= (xs >= bx * T) & (xs < (bx + bw) * T) & (ys >= by * T) & (ys < (by + bh) * T)
        blockiert_px[ys[ok], xs[ok]] = True
    # Felsspitzen im Wasser, die ueber begehbaren Boden ragen, gehoeren in die Ueberlagerung
    sp_pfad = os.path.join(KARTE, 'felsspitzen.npy')
    if os.path.exists(sp_pfad):
        sp_m = np.unpackbits(np.load(sp_pfad))[:H * W].reshape(H, W).astype(bool)
        ba = np.array(boden)
        oa_ = np.array(oben)
        oa_[sp_m] = ba[sp_m]
        oben = Image.fromarray(oa_)
    boden.save(os.path.join(OUT, 'ebene1_boden.png'))
    oben.save(os.path.join(OUT, 'ebene3_ueberlagerung.png'))

    # ---------------------------------------------------------------- Kollisionsraster
    klasse = np.ones((rows, cols), int)
    for y in range(rows):
        for x in range(cols):
            if grid[y][x] in 'WDh':                 # Wasser, Meer, Flachwasser (Wald: nur die Staemme)
                klasse[y, x] = 2
            if grid[y][x] == 'F' and (x == 0 or y == 0 or x == cols - 1 or y == rows - 1):
                klasse[y, x] = 2                     # Kartenrand im Wald bleibt zu
    # Klippenwaende aus dem Hoehenplan (Wand belegt Zeilen t-h+1..t; Zeile t-h ist die Graskante oben)
    tcol, hcol = [None] * (cols + 1), [3] * (cols + 1)
    for s in plan['segmente']:
        for vx in range(s['von'], min(s['bis'], cols) + 1):
            tcol[vx], hcol[vx] = s['t'], s.get('h', 3)
    for x in range(cols):
        t, h = tcol[x], hcol[x]
        if t is None:
            continue
        for y in range(t - h + 1, t + 1):
            if 0 <= y < rows:
                klasse[y, x] = 2
    # Kueste nach dem Bild: Meeres-/Flachwasser-/Strandkacheln sind gesperrt, wenn sie zu mehr als der
    # Haelfte Meer zeigen (das terrassierte Meer folgt der echten Wasserlinie, nicht dem Vorlagenraster)
    meer_pfad = os.path.join(KARTE, 'meer.npy')
    if os.path.exists(meer_pfad):
        meer = np.unpackbits(np.load(meer_pfad))[:H * W].reshape(H, W).astype(bool)
        for y in range(rows):
            for x in range(cols):
                if grid[y][x] in 'DhSs':
                    anteil = meer[y * T:(y + 1) * T, x * T:(x + 1) * T].mean()
                    klasse[y, x] = 2 if anteil > 0.5 else (1 if grid[y][x] in 'hSs' else klasse[y, x])
    # begehbare Bauwerke ueberschreiben: Treppen, Bruecken, Steg
    for tr in plan.get('treppen', []):
        t, h = tcol[tr['x']], hcol[tr['x']]
        for x in range(tr['x'], tr['x'] + tr['breite']):
            for y in range(t - h, t + 1):
                klasse[y, x] = 1
    for br in plan.get('bruecken', []) + plan.get('stege', []):
        for y in range(br['y'], br['y'] + br['hoehe']):
            for x in range(br['x'], br['x'] + br['breite']):
                klasse[y, x] = 1
    # Objektfuesse
    for y in range(rows):
        for x in range(cols):
            if blockiert_px[y * T:(y + 1) * T, x * T:(x + 1) * T].sum() >= MIN_FUSS:
                klasse[y, x] = 2
    # Verdeckung: begehbare Kacheln unter deckenden Objektteilen
    oa = np.array(oben.getchannel('A')) >= 128
    for y in range(rows):
        for x in range(cols):
            if klasse[y, x] == 1 and oa[y * T:(y + 1) * T, x * T:(x + 1) * T].sum() >= MIN_DECKT:
                klasse[y, x] = 3

    zeilen = [''.join(str(v) for v in r) for r in klasse]
    json.dump({'tile_size': T, 'cols': cols, 'rows': rows,
               'legende': {'1': 'begehbar', '2': 'nicht begehbar', '3': 'begehbar, verdeckt den Spieler'},
               'zeichenreihenfolge': ['ebene1_boden.png', 'Spieler', 'ebene3_ueberlagerung.png'],
               'raster': zeilen}, open(os.path.join(OUT, 'kollision.json'), 'w'), indent=0)
    open(os.path.join(OUT, 'kollision.txt'), 'w').write('\n'.join(zeilen) + '\n')

    # Ebene 2 als Bild: halbtransparente Maske der nicht begehbaren Kacheln (fuer Editor/Engine-Import)
    maske = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    md = ImageDraw.Draw(maske)
    for y in range(rows):
        for x in range(cols):
            if klasse[y, x] == 2:
                md.rectangle((x * T, y * T, x * T + T - 1, y * T + T - 1), fill=(255, 0, 0, 255))
    maske.save(os.path.join(OUT, 'ebene2_kollision.png'))

    # ---------------------------------------------------------------- Vorschau
    karte = Image.open(os.path.join(KARTE, 'terrain.png')).convert('RGBA')
    farbe = Image.new('RGBA', karte.size, (0, 0, 0, 0))
    fd = ImageDraw.Draw(farbe)
    for y in range(rows):
        for x in range(cols):
            k = klasse[y, x]
            if k == 2:
                fd.rectangle((x * T, y * T, x * T + T - 1, y * T + T - 1), fill=(230, 40, 40, 110))
            elif k == 3:
                fd.rectangle((x * T, y * T, x * T + T - 1, y * T + T - 1), fill=(40, 110, 255, 120))
    karte.alpha_composite(farbe)
    gd = ImageDraw.Draw(karte)
    for x in range(0, W, T):
        gd.line((x, 0, x, H), fill=(0, 0, 0, 40))
    for y in range(0, H, T):
        gd.line((0, y, W, y), fill=(0, 0, 0, 40))
    karte.save(os.path.join(OUT, 'vorschau.png'))
    n = {k: int((klasse == k).sum()) for k in (1, 2, 3)}
    print('Kacheln: begehbar %d, blockiert %d, verdeckt %d' % (n[1], n[2], n[3]))


if __name__ == '__main__':
    main()
