"""Karte 01 in drei Spiel-Ebenen zerlegen.

  python3 tools/karte01_ebenen.py   ->  maps/karte01/ebenen/

Je 16x16-Kachel eine Klasse:
  1 = begehbar          (Gras, Wege, Sand, Bruecken, Steg, Treppen, Gras/Farne/Blumen/Pilze/Kiesel)
  2 = nicht begehbar    (Wasser, Meer, Klippenwaende, Wald, Fuss von Baeumen/Felsen/Laternen/Gebaeuden)
  3 = begehbar, verdeckt den Spieler (Baumkronen, Laternenkoepfe, Daecher ueber begehbarem Boden)

Ausgabe:
  ebene1_boden.png           alles, was UNTER dem Spieler liegt (Boden, Klippen, Bauwerke, Objektfuesse, Schatten)
  ebene2_kollision.png       Maske: rotes 8x8-Feld = nicht begehbar (dieselbe Information wie kollision_fein.json)
  ebene3_ueberlagerung.png   transparent: alles, was UEBER dem Spieler liegt (obere Teile hoher Objekte)
  kollision_fein.json / .txt Raster aus 8x8-Feldern mit 1/2/3 (Zeile = y, Zeichen = x)
  kollision.json / .txt      daraus abgeleitetes 16x16-Kachelraster
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
Z = 8              # Kollisionsraster: 8x8-Felder (2x2 je Kachel)
MIN_FUSS = 3       # ab so vielen Fusspixeln (Stamm, Mast, Sockel) ist ein 8x8-Feld blockiert
MIN_DECKT = 4      # ab so vielen deckenden Pixeln der Ueberlagerung verdeckt ein 8x8-Feld den Spieler
# begehbare Bodendeko (liegt unter dem Spieler): Gras, Farne, Schilf, Blumen, Pilze, Kiesel, Zweige
FLACH = {'deko/05', 'deko/06', 'deko/07', 'deko/08', 'deko/10', 'deko/14', 'deko/26', 'deko/27', 'deko/31',
         'deko/33', 'deko/61'}


KORREKTUREN = os.path.join(OUT, 'kollision_korrekturen.json')
SPIEL_JS = os.path.join(ROOT, 'spiel', 'karte01_kollision.js')


def korrekturen_laden():
    """Handkorrekturen aus dem Editor (spiel/karte01.html): {"x,y": wert}."""
    if not os.path.exists(KORREKTUREN):
        return {}
    return json.load(open(KORREKTUREN)).get('kacheln', {})


def korrekturen_anwenden(fein):
    """Korrekturen gelten fuer 8x8-Felder (Spalte, Zeile im feinen Raster)."""
    rows, cols = fein.shape
    for key, w in korrekturen_laden().items():
        x, y = map(int, key.split(','))
        if 0 <= x < cols and 0 <= y < rows:
            fein[y, x] = int(w)


def grob_aus_fein(fein):
    """16x16-Raster fuer Engines ohne feine Kollision: Kachel gesperrt, wenn mindestens 2 ihrer 4 Felder
    gesperrt sind; sonst verdeckt, wenn eines verdeckt ist; sonst begehbar."""
    rows, cols = fein.shape[0] // 2, fein.shape[1] // 2
    viertel = fein.reshape(rows, 2, cols, 2).transpose(0, 2, 1, 3).reshape(rows, cols, 4)
    grob = np.ones((rows, cols), int)
    grob[(viertel == 3).any(axis=2)] = 3
    grob[(viertel == 2).sum(axis=2) >= 2] = 2
    return grob


def raster_bild(klasse, z, farben, basis=None, gitter=None):
    rows, cols = klasse.shape
    bild = basis.copy() if basis is not None else Image.new('RGBA', (cols * z, rows * z), (0, 0, 0, 0))
    farbe = Image.new('RGBA', bild.size, (0, 0, 0, 0))
    fd = ImageDraw.Draw(farbe)
    for y in range(rows):
        for x in range(cols):
            f = farben.get(int(klasse[y, x]))
            if f:
                fd.rectangle((x * z, y * z, x * z + z - 1, y * z + z - 1), fill=f)
    bild.alpha_composite(farbe)
    for schritt, a in gitter or []:             # Gitter als eigene Schicht, damit es abdunkelt statt Loecher zu stanzen
        linien = Image.new('RGBA', bild.size, (0, 0, 0, 0))
        gd = ImageDraw.Draw(linien)
        for x in range(0, bild.width, schritt):
            gd.line((x, 0, x, bild.height), fill=(0, 0, 0, a))
        for y in range(0, bild.height, schritt):
            gd.line((0, y, bild.width, y), fill=(0, 0, 0, a))
        bild.alpha_composite(linien)
    return bild


def kollision_schreiben(fein):
    """Schreibt das feine Raster (8x8) und das daraus abgeleitete 16x16-Raster:
    kollision_fein.json/.txt, kollision.json/.txt, ebene2_kollision.png (8x8), vorschau.png,
    spiel/karte01_kollision.js."""
    legende = {'1': 'begehbar', '2': 'nicht begehbar', '3': 'begehbar, verdeckt den Spieler'}
    reihenfolge = ['ebene1_boden.png', 'Spieler', 'ebene3_ueberlagerung.png']
    zf = [''.join(str(v) for v in r) for r in fein]
    json.dump({'zelle': Z, 'cols': fein.shape[1], 'rows': fein.shape[0], 'legende': legende,
               'zeichenreihenfolge': reihenfolge, 'raster': zf},
              open(os.path.join(OUT, 'kollision_fein.json'), 'w'), indent=0)
    open(os.path.join(OUT, 'kollision_fein.txt'), 'w').write('\n'.join(zf) + '\n')

    grob = grob_aus_fein(fein)
    zg = [''.join(str(v) for v in r) for r in grob]
    json.dump({'tile_size': T, 'cols': grob.shape[1], 'rows': grob.shape[0], 'legende': legende,
               'zeichenreihenfolge': reihenfolge, 'hinweis': 'aus kollision_fein.json abgeleitet (8x8-Felder)',
               'raster': zg}, open(os.path.join(OUT, 'kollision.json'), 'w'), indent=0)
    open(os.path.join(OUT, 'kollision.txt'), 'w').write('\n'.join(zg) + '\n')

    raster_bild(fein, Z, {2: (255, 0, 0, 255)}).save(os.path.join(OUT, 'ebene2_kollision.png'))
    karte = Image.open(os.path.join(KARTE, 'terrain.png')).convert('RGBA')
    raster_bild(fein, Z, {2: (230, 40, 40, 110), 3: (40, 110, 255, 120)}, karte,
                gitter=[(Z, 18), (T, 40)]).save(os.path.join(OUT, 'vorschau.png'))

    spiel = {'zelle': Z, 'cols': fein.shape[1], 'rows': fein.shape[0], 'raster': zf}
    open(SPIEL_JS, 'w').write('// Erzeugt aus maps/karte01/ebenen/kollision_fein.json (8x8-Felder; 1 begehbar, 2 gesperrt, 3 verdeckt)\n'
                              'window.KARTE01_KOLLISION = ' + json.dumps(spiel, indent=0) + ';\n')

EBENEN_KORREKTUREN = os.path.join(OUT, 'ebenen_korrekturen.json')
SPIEL_OBJEKTE_JS = os.path.join(ROOT, 'spiel', 'karte01_objekte.js')
MODI = ('hinten', 'geteilt', 'vorne')


def objekt_key(o):
    """Stabiler Name eines platzierten Objekts: Datei@x,y (+ ~ wenn gespiegelt)."""
    return '%s@%d,%d%s' % (o['datei'], o['x'], o['y'], '~' if o.get('spiegeln') else '')


def ebenen_korrekturen_laden():
    """Ebenen je Objekt aus dem Editor: {key: 'hinten' | 'geteilt' | 'vorne'}."""
    if not os.path.exists(EBENEN_KORREKTUREN):
        return {}
    return json.load(open(EBENEN_KORREKTUREN)).get('objekte', {})


def objekte_exportieren(export, sprite):
    """Sprite-Atlas + Objektliste fuer spiel/karte01.html (zeichnet jedes Objekt einzeln)."""
    import base64
    eindeutig = {}
    for o, *_ in export:
        k = (o['datei'], bool(o.get('spiegeln')))
        if k not in eindeutig:
            eindeutig[k] = sprite(o)
    # einfache Regal-Packung
    BREITE, x, y, zeile = 1024, 0, 0, 0
    platz = {}
    for k, sp in sorted(eindeutig.items(), key=lambda kv: -kv[1].height):
        if x + sp.width > BREITE:
            x, y, zeile = 0, y + zeile + 1, 0
        platz[k] = (x, y)
        x += sp.width + 1
        zeile = max(zeile, sp.height)
    atlas = Image.new('RGBA', (BREITE, y + zeile), (0, 0, 0, 0))
    sprites = []
    index = {}
    for k, sp in eindeutig.items():
        ax, ay = platz[k]
        atlas.alpha_composite(sp, (ax, ay))
        bits = np.packbits((np.array(sp.getchannel('A')) > 0).ravel())
        index[k] = len(sprites)
        sprites.append({'name': k[0][:-4] + (' (gespiegelt)' if k[1] else ''), 'ax': ax, 'ay': ay,
                        'w': sp.width, 'h': sp.height, 'maske': base64.b64encode(bits.tobytes()).decode()})
    atlas.save(os.path.join(OUT, 'objekte_atlas.png'))
    objekte = []
    for o, trenn, flach, modus in export:
        objekte.append([objekt_key(o), index[(o['datei'], bool(o.get('spiegeln')))], o['x'], o['y'],
                        max(0, trenn), 'hinten' if flach else 'geteilt', modus])
    daten = {'sprites': sprites, 'objekte': objekte,
             'felder': ['key', 'sprite', 'x', 'y', 'trenn', 'standard', 'modus']}
    open(SPIEL_OBJEKTE_JS, 'w').write(
        '// Erzeugt von tools/karte01_ebenen.py: Objekte in Zeichenreihenfolge, Atlas maps/karte01/ebenen/objekte_atlas.png\n'
        'window.KARTE01_OBJEKTE = ' + json.dumps(daten, separators=(',', ':')) + ';\n')


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

    boden.save(os.path.join(OUT, 'ebene0_untergrund.png'))     # Boden ohne Objekte (fuer den Ebenen-Editor)

    modi = ebenen_korrekturen_laden()
    export = []
    blockiert_px = np.zeros((H, W), bool)       # Fuesse hoher Objekte
    for o in objs:
        sp = sprite(o)
        a = np.array(sp.getchannel('A'))
        zeilen = np.nonzero((a > 0).any(axis=1))[0]
        if not len(zeilen):
            continue
        flach = o.get('ebene', 1) == 0 or o.get('basis') in FLACH   # flache Deko: Boden, begehbar
        trenn = int(zeilen.max()) + 1 - FUSS    # Zeile im Sprite: darueber Ueberlagerung, darunter Fuss
        modus = modi.get(objekt_key(o)) or ('hinten' if flach else 'geteilt')
        export.append((o, trenn, flach, modus))
        if modus == 'hinten':                   # ganz unter dem Spieler
            boden.alpha_composite(sp, (o['x'], o['y']))
        elif modus == 'vorne':                  # ganz ueber dem Spieler
            oben.alpha_composite(sp, (o['x'], o['y']))
        else:                                   # geteilt: Fuss unten, Rest oben
            boden.alpha_composite(sp.crop((0, trenn, sp.width, sp.height)), (o['x'], o['y'] + trenn))
            oben.alpha_composite(sp.crop((0, 0, sp.width, trenn)), (o['x'], o['y']))
        if flach:
            continue
        fuss = sp.crop((0, trenn, sp.width, sp.height))
        fa = np.array(fuss.getchannel('A')) >= 128
        ys, xs = np.nonzero(fa)
        ys, xs = ys + o['y'] + trenn, xs + o['x']
        ok = (ys >= 0) & (ys < H) & (xs >= 0) & (xs < W)
        blockiert_px[ys[ok], xs[ok]] = True
    objekte_exportieren(export, sprite)
    boden.save(os.path.join(OUT, 'ebene1_boden.png'))
    oben.save(os.path.join(OUT, 'ebene3_ueberlagerung.png'))

    # ---------------------------------------------------------------- Kollisionsraster
    klasse = np.ones((rows, cols), int)
    for y in range(rows):
        for x in range(cols):
            if grid[y][x] in 'WDhF':                # Wasser, Meer, Flachwasser, Wald
                klasse[y, x] = 2
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
    # Feines Raster: jede Kachel in 2x2 Felder, dann Objektfuesse und Verdeckung je 8x8-Feld
    fein = np.kron(klasse, np.ones((2, 2), int))
    fr, fc = fein.shape
    fuss = blockiert_px.reshape(fr, Z, fc, Z).sum(axis=(1, 3))
    fein[fuss >= MIN_FUSS] = 2
    oa = np.array(oben.getchannel('A')) >= 128
    deckt = oa.reshape(fr, Z, fc, Z).sum(axis=(1, 3))
    fein[(fein == 1) & (deckt >= MIN_DECKT)] = 3

    korrekturen_anwenden(fein)
    kollision_schreiben(fein)
    n = {k: int((fein == k).sum()) for k in (1, 2, 3)}
    print('8x8-Felder: begehbar %d, blockiert %d, verdeckt %d' % (n[1], n[2], n[3]))

if __name__ == '__main__':
    main()
