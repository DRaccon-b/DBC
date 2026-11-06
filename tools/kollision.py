"""Kollisionsraster und Overlay fuer die Karten 11/12 (gleiches Format wie Karte 01, karte01_ebenen.py).

  python3 tools/kollision.py karte11      ->  maps/karte11/ebenen/kollision.json, .txt, ebene2_kollision.png,
                                             kollision_overlay.png (Karte mit Markierungen und Legende)

Je 16x16-Kachel:  1 = begehbar   2 = nicht begehbar   3 = begehbar, verdeckt den Spieler (Baumkronen u. a.)
Gruende fuer 2 (nur im Overlay unterschieden): Bergwand/Klippenfront, Wasser, Plateaukante, Objektfuss, Bruestung.
Begehbar trotz Hoehenwechsel: Treppen, Bruecken, Arena-Treppe. Teleporter sind markiert.
Regeln (CLAUDE.md, Regel 4): hohe Objekte blockieren nur am Fuss (unterste Pixelzeilen), der obere Teil verdeckt
den Spieler; flache Bodendeko (Gras, Blumen, Pilze, Laub) ist begehbar.
"""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
T = 16
FUSS = 10          # unterste Pixelzeilen eines hohen Objekts blockieren
MIN_FUSS = 4       # ab so vielen Fusspixeln ist eine Kachel blockiert
MIN_DECKT = 12     # ab so vielen deckenden Pixeln verdeckt eine Kachel den Spieler
LIEGEND_GROSS = {'karte11': {'gross/00', 'gross/01'}}    # liegen breit am Boden (Walskelett, gestrandetes Wrack)
FARBEN = {'wand': (230, 40, 40), 'wasser': (40, 90, 230), 'kante': (250, 200, 40), 'objekt': (255, 120, 20),
          'bruestung': (200, 60, 200), 'verdeckt': (60, 200, 255), 'durchgang': (60, 220, 90), 'teleporter': (255, 60, 255)}
NAMEN = {'wand': 'Bergwand / Klippe / Front', 'wasser': 'Wasser', 'kante': 'Plateaukante', 'objekt': 'Objektfuss (Sockel)',
         'bruestung': 'Bruestung', 'verdeckt': 'begehbar, verdeckt Spieler', 'durchgang': 'Treppe / Bruecke',
         'teleporter': 'Teleporter'}


def main(karte):
    K = os.path.join(ROOT, 'maps', karte)
    OBJ = os.path.join(ROOT, 'assets', 'objekte', karte)
    OUT = os.path.join(K, 'ebenen')
    os.makedirs(OUT, exist_ok=True)
    lay = json.load(open(os.path.join(K, 'layout.json')))
    cols, rows = lay['groesse']
    lvl = np.load(os.path.join(K, 'pixelhoehe.npy'))
    Hh, W = lvl.shape
    wasser = np.unpackbits(np.load(os.path.join(K, 'wasser.npy')))[:Hh * W].reshape(Hh, W).astype(bool)
    grund = np.full((rows, cols), '', object)                 # Grund je Kachel (leer = begehbar)
    ebene = np.zeros((rows, cols), int)
    kach = lambda m, x, y: m[y * T:(y + 1) * T, x * T:(x + 1) * T]
    for y in range(rows):
        for x in range(cols):
            l_ = kach(lvl, x, y)
            if ((l_ == 9) | (l_ == 5)).mean() >= 0.5:
                grund[y, x] = 'wand'
            elif kach(wasser, x, y).mean() > 0.5:
                grund[y, x] = 'wasser'
            ebene[y, x] = int(np.bincount(l_.ravel()).argmax())
    # Durchgaenge: Treppen (Front 32 px = 2 Kacheln unter der Kante), Bruecken, Arena-Treppe
    durch = np.zeros((rows, cols), bool)
    for (x0, x1, e, yb) in lay.get('treppen_sued', []):
        durch[yb:yb + 3, x0:x1 + 1] = True
    if lay.get('arena_treppe'):
        x0, x1, yb = lay['arena_treppe']
        durch[yb:yb + 3, x0:x1 + 1] = True
    for b in lay.get('bruecken', []):                        # Holzstege (Karte 12): ganze Flaeche begehbar
        durch[b[1]:b[3] + 1, b[0]:b[2] + 1] = True
    bru = lay.get('bruecke')                                 # Steinbruecke (Karte 11): Deck mittig, Bruestungen zu
    if bru:
        y0p, y1p = bru[1] * T + 4 + 7, (bru[3] + 1) * T - 4 - 5
        for y in range(bru[1], bru[3] + 1):
            deck = max(0, min((y + 1) * T, y1p) - max(y * T, y0p)) / T
            for x in range(bru[0], bru[2] + 1):
                if deck >= 0.5:
                    durch[y, x] = True
                else:
                    grund[y, x] = 'bruestung'
    grund[durch] = ''
    # Plateaukanten: begehbare hoehere Kachel neben begehbarer tieferer (ausser an Treppe/Bruecke)
    for y in range(rows):
        for x in range(cols):
            if grund[y, x] or durch[y, x] or ebene[y, x] not in (2, 3, 4):
                continue
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                yy, xx = y + dy, x + dx
                if 0 <= yy < rows and 0 <= xx < cols and not grund[yy, xx] and not durch[yy, xx] \
                        and ebene[yy, xx] < ebene[y, x]:
                    grund[y, x] = 'kante'
                    break
    # Objekte: Fuss blockiert, oberer Teil verdeckt
    fuss_px = np.zeros((Hh, W), bool)
    deckt_px = np.zeros((Hh, W), bool)
    flach_namen = set()
    for o in json.load(open(os.path.join(OBJ, 'platzierung.json'))):
        a = np.array(Image.open(os.path.join(OBJ, o['datei'])).getchannel('A')) >= 128
        zeilen = np.nonzero(a.any(axis=1))[0]
        if not len(zeilen):
            continue
        zu, oben = int(zeilen.max()), int(zeilen.min())
        hoch, breit = zu - oben + 1, int(np.ptp(np.nonzero(a.any(axis=0))[0])) + 1
        flach = o.get('ebene') == 0 or (hoch <= 16 and breit <= 16)
        if flach:
            continue
        f = np.zeros_like(a)
        if o.get('liegend') or o.get('basis') in LIEGEND_GROSS.get(karte, ()):   # liegende Objekte: untere Haelfte
            f[(oben + zu) // 2:zu + 1] = a[(oben + zu) // 2:zu + 1]
        else:
            f[max(0, zu - FUSS + 1):zu + 1] = a[max(0, zu - FUSS + 1):zu + 1]
        d = a & ~f
        x, y = o['x'], o['y']
        for m, ziel in ((f, fuss_px), (d, deckt_px)):
            ys, xs = np.nonzero(m)
            ys, xs = ys + y, xs + x
            ok = (ys >= 0) & (ys < Hh) & (xs >= 0) & (xs < W)
            ziel[ys[ok], xs[ok]] = True
    klasse = np.ones((rows, cols), int)
    for y in range(rows):
        for x in range(cols):
            if not grund[y, x] and not durch[y, x] and kach(fuss_px, x, y).sum() >= MIN_FUSS:
                grund[y, x] = 'objekt'
            if grund[y, x]:
                klasse[y, x] = 2
            elif kach(deckt_px, x, y).sum() >= MIN_DECKT:
                klasse[y, x] = 3
    zeilen = [''.join(str(v) for v in r) for r in klasse]
    json.dump({'tile_size': T, 'cols': cols, 'rows': rows,
               'legende': {'1': 'begehbar', '2': 'nicht begehbar', '3': 'begehbar, verdeckt den Spieler'},
               'grund': {'%d,%d' % (x, y): grund[y, x] for y in range(rows) for x in range(cols) if grund[y, x]},
               'teleporter': lay.get('teleporter', []),
               'raster': zeilen}, open(os.path.join(OUT, 'kollision.json'), 'w'), indent=0)
    open(os.path.join(OUT, 'kollision.txt'), 'w').write('\n'.join(zeilen) + '\n')
    maske = Image.new('RGBA', (W, Hh), (0, 0, 0, 0))
    md = ImageDraw.Draw(maske)
    for y in range(rows):
        for x in range(cols):
            if klasse[y, x] == 2:
                md.rectangle((x * T, y * T, x * T + T - 1, y * T + T - 1), fill=(255, 0, 0, 255))
    maske.save(os.path.join(OUT, 'ebene2_kollision.png'))
    # Overlay: Karte, Markierungen je Grund, Durchgaenge und Teleporter umrandet, Raster, Legende
    bild = Image.open(os.path.join(K, 'terrain.png')).convert('RGBA')
    lage = Image.new('RGBA', bild.size, (0, 0, 0, 0))
    ld = ImageDraw.Draw(lage)
    for y in range(rows):
        for x in range(cols):
            r_ = (x * T, y * T, x * T + T - 1, y * T + T - 1)
            g = grund[y, x] or ('verdeckt' if klasse[y, x] == 3 else '')
            if g:
                ld.rectangle(r_, fill=FARBEN[g] + (120 if g != 'verdeckt' else 70,))
            if durch[y, x]:
                ld.rectangle(r_, outline=FARBEN['durchgang'] + (255,), width=2)
    for tp in lay.get('teleporter', []):
        ld.rectangle((tp['x'] * T, tp['y'] * T, (tp['x'] + tp['b']) * T - 1, (tp['y'] + tp['h']) * T - 1),
                     outline=FARBEN['teleporter'] + (255,), width=3)
    bild.alpha_composite(lage)
    gd = ImageDraw.Draw(bild)
    for x in range(0, W, T):
        gd.line((x, 0, x, Hh), fill=(0, 0, 0, 50))
    for y in range(0, Hh, T):
        gd.line((0, y, W, y), fill=(0, 0, 0, 50))
    lx, ly = W - 250, Hh - 20 * len(FARBEN) - 16
    gd.rectangle((lx - 8, ly - 8, W - 8, Hh - 8), fill=(10, 10, 14, 220))
    for i, (k_, c) in enumerate(FARBEN.items()):
        yy = ly + i * 20
        if k_ in ('durchgang', 'teleporter'):
            gd.rectangle((lx, yy, lx + 14, yy + 14), outline=c + (255,), width=2)
        else:
            gd.rectangle((lx, yy, lx + 14, yy + 14), fill=c + (200,))
        gd.text((lx + 22, yy + 2), NAMEN[k_], fill=(240, 240, 240, 255))
    bild.save(os.path.join(OUT, 'kollision_overlay.png'))
    print('%s: %d begehbar, %d blockiert, %d verdeckt' % (karte, (klasse == 1).sum(), (klasse == 2).sum(), (klasse == 3).sum()))


if __name__ == '__main__':
    main(sys.argv[1])
