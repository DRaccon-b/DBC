"""Objekte fuer Karte 29 (The Sea of Darkness, A02) - Positionen nach der Vorlage.

  python3 tools/karte29_bauen.py   (einmal -> wand.npy, wasser.npy)
  python3 tools/karte29_objekte.py && python3 tools/karte29_bauen.py

Neu (PixelLab Objekt-Creator k29_gross / k29_mittel): Leuchtturm, Tempeltor, Statue des Meeresgottes, Riss-Portal,
Saeulen, Saeulenstumpf, Kristallportal (Spawn), Strudel. Wiederverwendet: Karte 11 (Dark Ocean) Wrack, Anker,
Laternen, Felsen, Muscheln, Seetang, Treibholz, Fischgraete; Karte 25 Ruderboote/Bootswrack (abgedunkelt).
Grosse Objekte zuerst, dann Kleinkram; keine Ueberlappungen (Fussrechtecke mit Abstand).
"""
import json, math, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
import bauwerke

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte29')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte29')
T = 16
FREMD = {'k11/wrack': ('karte11/gross/01.png', 1.0), 'k11/anker': ('karte11/land/00.png', 0.9),
         'k11/laterne': ('karte11/land/11.png', 1.0), 'k11/fels': ('karte11/meer/08.png', 0.95),
         'k11/fels2': ('karte11/meer/09.png', 0.95), 'k11/muschel': ('karte11/meer/07.png', 0.85),
         'k11/auster': ('karte11/meer/14.png', 0.85), 'k11/tang': ('karte11/meer/04.png', 0.9),
         'k11/holz': ('karte11/land/06.png', 0.75), 'k11/graete': ('karte11/land/08.png', 0.8),
         'k25/boot': ('karte25/strand/01.png', 0.62), 'k25/bootwrack': ('karte25/strand/13.png', 0.62)}


def main():
    rnd = random.Random(29)
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cls = lay['klassen']
    cols, rows = lay['groesse']
    Hp, Wp = rows * T, cols * T
    wand = np.unpackbits(np.load(os.path.join(KARTE, 'wand.npy')))[:Hp * Wp].reshape(Hp, Wp).astype(bool)
    wasser = np.unpackbits(np.load(os.path.join(KARTE, 'wasser.npy')))[:Hp * Wp].reshape(Hp, Wp).astype(bool)
    for name, (q, f) in FREMD.items():
        im = np.array(Image.open(os.path.join(ROOT, 'assets', 'objekte', q)).convert('RGBA')).astype(np.float32)
        l = im[..., :3].mean(2, keepdims=True)
        im[..., :3] = (im[..., :3] * 0.55 + l * 0.45) * f            # entsaettigt + dunkler (dunkles Meer)
        os.makedirs(os.path.dirname(os.path.join(OBJ, name + '.png')), exist_ok=True)
        Image.fromarray(np.clip(im, 0, 255).astype(np.uint8)).save(os.path.join(OBJ, name + '.png'))
    objekte, fuesse = [], []
    os.makedirs(os.path.join(OBJ, 'varianten'), exist_ok=True)

    def setze(name, cx, fy, opt=None, spiegeln=False, mit_fuss=True, auf='land', frei=True):
        sp = Image.open(os.path.join(OBJ, name + '.png')).convert('RGBA')
        if spiegeln:
            sp = sp.transpose(Image.FLIP_LEFT_RIGHT)
        bb = sp.getbbox()
        bw = bb[2] - bb[0]
        cx, fy = int(cx), int(fy)
        x0, x1, y0, y1 = cx - bw // 2 - 2, cx + bw // 2 + 2, fy - min(T, bb[3] - bb[1]) - 2, fy + 2
        unten = (slice(max(0, fy - 6), min(Hp, fy + 1)), slice(max(0, cx - bw // 3), min(Wp, cx + bw // 3 + 1)))
        if auf == 'land' and (wasser[unten].any() or wand[unten].any()):
            return None
        if auf == 'wasser' and not wasser[unten].all():
            return None
        if frei and any(not (x1 < a0 or x0 > a1 or y1 < b0 or y0 > b1) for (a0, b0, a1, b1) in fuesse):
            return None
        tx, ty = cx // T, fy // T
        if mit_fuss and auf == 'land':
            k_ = cls[min(rows - 1, ty)][min(cols - 1, tx)]
            v = bauwerke.bodenfuss(sp, 'beton' if k_ in 'pq' else 'sand', 'stein')
            fa = np.array(v).astype(np.float32)
            off = Image.new('RGBA', v.size, (0, 0, 0, 0)); off.paste(sp, (2, 0))
            sel = (np.array(off.getchannel('A')) == 0) & (fa[..., 3] > 0)
            fa[sel, :3] = fa[sel, :3].mean(axis=1, keepdims=True) * np.array([0.7, 0.76, 0.8])   # Bodenfuss graublau
            sp = Image.fromarray(np.clip(fa, 0, 255).astype(np.uint8))
            bb = (bb[0] + 2, bb[1], bb[2] + 2, bb[3])
        datei = 'varianten/%s_%d_%d.png' % (name.replace('/', '-'), int(spiegeln), int(mit_fuss and auf == 'land'))
        sp.save(os.path.join(OBJ, datei))
        o = {'datei': datei, 'basis': name, 'x': cx - (bb[0] + bw // 2), 'y': fy - (bb[3] - 1), 'fuss': sp.height,
             'kachel': [tx, ty], 'block': [(cx - bw // 2) // T, ty - math.ceil((bb[3] - bb[1]) / T) + 1,
                                           math.ceil(bw / T), math.ceil((bb[3] - bb[1]) / T)], 'ebene': 1}
        if name.startswith(('gross/', 'mittel/0')) or name == 'k11/laterne':
            o['an_wand'] = True                                      # Bauwerke auf Pflaster: kein Erdwall ueber den Fuessen
        o.update(opt or {})
        objekte.append(o)
        fuesse.append((x0, y0, x1, y1))
        return o

    # ---- grosse Objekte zuerst
    setze('gross/00', 1264, 254, {'anim': 'lampe'})                          # Leuchtturm am Ende der langen Bruecke
    bx0, by0, bx1, by1 = lay['bruecken'][0]
    achse_tor = (bx0 + bx1 + 1) * T // 2                                     # Tempeltor genau auf der Brueckenachse
    py0 = lay['platz'][1]
    setze('gross/01', achse_tor, py0 * T + 30, {}, mit_fuss=False, frei=False)
    setze('gross/02', 864, py0 * T + 94, {})                                 # Statue des Meeresgottes (links oben im Tempel)
    px0, _, px1, py1 = lay['platz']
    achse = (px0 + px1 + 1) * T // 2                                         # Saeulenpaare spiegelsymmetrisch zur Platzachse
    for fy in (py0 * T + 120, py0 * T + 218, py0 * T + 312):
        for sd in (-1, 1):
            setze('mittel/00', achse + sd * 168, fy, {})
    for (cx, fy) in ((940, py0 * T + 70), (1086, py0 * T + 124), (872, py0 * T + 292), (990, py0 * T + 274)):
        setze('mittel/01', cx, fy, {}, rnd.random() < 0.5)                  # Saeulenstuempfe
    setze('k11/wrack', 365, 652, {'liegend': False}, frei=True)              # grosses Schiffswrack am Strand
    # ---- Portale / Teleporter (animiert)
    setze('mittel/02', 88, 104, {'anim': 'portal'}, mit_fuss=False, frei=False)          # Spawn: Kristallportal
    setze('gross/03', 1360, 120, {'anim': 'leuchten'}, mit_fuss=False, auf='egal', frei=False)   # Riss ueber dem Meer
    setze('mittel/03', 1352, 1200, {'anim': 'portal', 'schattenlos': True}, mit_fuss=False, auf='egal', frei=False)
    # ---- Spawnplatz: vier Laternen symmetrisch
    lx0, ly0, lx1, ly1 = 4, 7, 15, 17
    mx, my = (lx0 + lx1 + 1) * T // 2, (ly0 + ly1 + 1) * T // 2
    for sx in (-1, 1):
        for sy in (-1, 1):
            setze('k11/laterne', mx + sx * 64, my + sy * 52 + 14, {'anim': 'leuchten'}, mit_fuss=False, frei=False)
    # ---- Strand: Boote, Bootswrack, Anker, Felsbrocken
    for (cx, fy, n, sp_) in ((180, 446, 'k25/boot', False), (660, 222, 'k25/boot', True), (885, 286, 'k25/boot', False),
                             (150, 944, 'k25/boot', True), (545, 420, 'k25/bootwrack', False)):
        setze(n, cx, fy, {'liegend': True}, sp_)
    for (cx, fy) in ((110, 588), (1135, 238)):
        setze('k11/anker', cx, fy, {}, rnd.random() < 0.5)
    for (cx, fy) in ((670, 124), (1135, 158), (255, 556), (287, 874)):
        setze('k11/fels' if rnd.random() < 0.6 else 'k11/fels2', cx, fy, {}, rnd.random() < 0.5)
    # ---- Kleinkram am Strand (unregelmaessig, eher wenig): Muscheln, Austern, Treibholz, Graeten, Seetang
    n_ = 0
    for _ in range(6000):
        if n_ >= 5:                                                   # deutlich weniger Kleinkram (Nutzer)
            break
        tx, ty = rnd.randrange(2, cols - 2), rnd.randrange(2, rows - 2)
        if not all(cls[ty + dy][tx + dx] in 'gl' for dx in (-1, 0, 1) for dy in (-1, 0, 1)):
            continue
        nm = rnd.choice(['k11/muschel', 'k11/auster', 'k11/holz', 'k11/graete', 'k11/tang'])
        if any(o['basis'] == nm and abs(o['kachel'][0] - tx) < 6 and abs(o['kachel'][1] - ty) < 4 for o in objekte):
            continue                                                 # keine Reihen gleicher Deko
        if setze(nm, tx * T + rnd.randrange(4, 12), ty * T + 13, {'liegend': nm in ('k11/holz', 'k11/graete'),
                 'anim': 'wehen' if nm == 'k11/tang' else None}, rnd.random() < 0.5, mit_fuss=False):
            n_ += 1
    json.dump(objekte, open(os.path.join(OBJ, 'platzierung.json'), 'w'), indent=0)
    print('Karte 29: %d Objekte' % len(objekte))


if __name__ == '__main__':
    main()
