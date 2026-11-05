"""Objekt-Tileset der Startkarte (Karte 06) am 16x16-Raster.

  python3 tools/karte06_tileset_export.py   ->  maps/karte06/tileset/ (+ karte06_tileset.zip)

objekte_tileset.png            ALLE Objekte der Karte (jede Variante einmal), je in ihrem eigenen Kachelblock,
                               so wie sie auf der Karte stehen (ohne Boden, ohne Schatten, ohne Bodenfuss/Grashalme).
objekte_tileset_animiert.png   NUR die animierten Objekte, exakt am selben Platz wie im ersten Tileset.
                               Die 16 Animationsbilder liegen untereinander: Bild n beginnt bei
                               y = n * hoehe_animationsbereich (steht in objekte_tileset.json).
animiert_frames/frame_NN.png   dieselben 16 Bilder einzeln, gleiche Groesse wie der animierte Bereich.
vorschau_animiert.gif          Vorschau der Animation.
objekte_tileset.json           je Objekt: Name, Animation, Platz im Tileset (Kacheln), Fusskachel und
                               alle Fundstellen auf der Karte.

Die animierten Objekte liegen oben im Tileset, deshalb reicht fuer die Animationsbilder der obere Bereich.
Ein Platz (slot) umfasst den Kachelblock des Objekts plus alle Kacheln, in die Bodenfuss oder Animation
hineinreichen (z. B. Rauch ueber dem Schornstein), damit nichts in den Nachbarn ragt.
"""
import json, math, os, shutil, sys, zipfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image

import karte_bauen as kb
import karte04_bauen as k4
import karte06_bauen as k6

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte06')
OUT = os.path.join(ROOT, 'maps', 'karte06', 'tileset')
T = 16
N = k6.N_FRAMES if hasattr(k6, 'N_FRAMES') else 16
PAD = 6 * T                      # Rand fuer die Einzel-Darstellung (Rauch, Glanz ...)
BREITE = 40                      # Tileset-Breite in Kacheln


def darstellen(o, cache, frame):
    """Objekt allein auf transparentem Grund, genau wie auf der Karte gezeichnet (frame None = Standbild)."""
    bx, by, wt, ht = o['block']
    sp = cache[o['datei']]
    x0, y0 = bx * T - PAD, by * T - PAD
    W = wt * T + 2 * PAD
    Hh = max(ht * T, o['y'] + sp.height - by * T) + 2 * PAD
    img = Image.new('RGBA', (W, Hh), (0, 0, 0, 0))
    o2 = dict(o, x=o['x'] - x0, y=o['y'] - y0)
    s = sp
    if frame is not None and o.get('anim') in ('wehen', 'blume'):
        s = kb.wehen(sp, kb.wind(frame, o['x']))
    elif frame is not None and o.get('anim') == 'baum':
        s = k4.baum_wind(sp, frame, o['x'] + o['y'] * 0.3)
    img.alpha_composite(s, (o2['x'], o2['y']))
    if frame is not None and o.get('anim') == 'blume':
        k4.bluete_puls(img, o2, s, frame)
    k4.animieren(img, [o2], cache, frame or 0)
    k6.animieren_k6(img, [o2], cache, frame or 0)
    return img, (x0, y0)


def main():
    objs = json.load(open(os.path.join(OBJ, 'platzierung.json')))
    # Originalsprites ohne Bodenfuss (keine Gras-/Sandpixel vor dem Objekt): die Variante ist 4 px breiter und
    # 3 px hoeher, das Original sitzt darin bei x = 2 -> gleiche Position auf dem Raster
    cache, ohne_fuss = {}, 0
    for o in objs:
        var = Image.open(os.path.join(OBJ, o['datei'])).convert('RGBA')
        basis = os.path.join(OBJ, o['basis'] + '.png')
        spiegel = o['datei'].endswith('_m.png')
        if o['datei'].startswith('varianten/') and os.path.exists(basis):
            orig = Image.open(basis).convert('RGBA')
            if spiegel:
                orig = orig.transpose(Image.FLIP_LEFT_RIGHT)
            gleich = var.size == orig.size and var.tobytes() == orig.tobytes()
            if var.size == (orig.width + 4, orig.height + 3) or gleich:
                o['datei'] = o['basis'] + ('_m' if spiegel else '')
                o['x'] += 0 if gleich else 2
                cache[o['datei']] = orig
                ohne_fuss += 1
                continue
        cache[o['datei']] = var
    print(ohne_fuss, 'Platzierungen ohne Bodenfuss')
    # jede Variante (Datei + Animation) einmal; Fundstellen sammeln
    eintraege = {}
    for o in objs:
        key = (o['datei'], o.get('anim'))
        if key not in eintraege:
            eintraege[key] = {'o': o, 'fundstellen': []}
        eintraege[key]['fundstellen'].append({'block': o['block'], 'fusskachel': o['kachel']})
    animierte = {key for key in eintraege if key[1]}
    # Bilder je Eintrag: Standbild + 16 Animationsbilder (nur bei Animation); Ausdehnung in Kacheln
    for key, e in eintraege.items():
        o = e['o']
        bx, by, wt, ht = o['block']
        stand, (x0, y0) = darstellen(o, cache, None)
        bilder = [stand]
        if key in animierte:
            bilder += [darstellen(o, cache, f)[0] for f in range(N)]
        alpha = np.zeros((stand.height, stand.width), bool)
        for b in bilder:
            alpha |= np.array(b.getchannel('A')) > 0
        ys, xs = np.nonzero(alpha)
        # Blockgrenzen im Einzelbild: Block beginnt bei PAD; nach aussen auf ganze Kacheln erweitern
        links = max(0, math.ceil((PAD - xs.min()) / T))
        oben = max(0, math.ceil((PAD - ys.min()) / T))
        rechts = max(0, math.ceil((xs.max() + 1 - (PAD + wt * T)) / T))
        unten = max(0, math.ceil((ys.max() + 1 - (PAD + ht * T)) / T))
        e.update(bilder=bilder, rand=(links, oben, rechts, unten), groesse=(links + wt + rechts, oben + ht + unten))
    # Packen: animierte zuerst (oben), dann der Rest; Regal-Verfahren, groesste Hoehe zuerst
    def packen(keys, y_start):
        keys = sorted(keys, key=lambda k: (-eintraege[k]['groesse'][1], -eintraege[k]['groesse'][0], k[0]))
        x = y = 0
        y += y_start
        reihe_h = 0
        for k in keys:
            w, h = eintraege[k]['groesse']
            if x + w > BREITE:
                x, y, reihe_h = 0, y + reihe_h, 0
            eintraege[k]['platz'] = (x, y)
            x += w
            reihe_h = max(reihe_h, h)
        return y + reihe_h
    anim_h = packen(animierte, 0)
    gesamt_h = packen(set(eintraege) - animierte, anim_h)
    os.makedirs(OUT, exist_ok=True)
    if os.path.isdir(os.path.join(OUT, 'animiert_frames')):
        shutil.rmtree(os.path.join(OUT, 'animiert_frames'))
    os.makedirs(os.path.join(OUT, 'animiert_frames'))

    def einsetzen(ziel, e, bild, dy=0):
        px, py = e['platz']
        links, oben = e['rand'][0], e['rand'][1]
        # Einzelbild-Ausschnitt = Slot; Slot beginnt (links, oben) Kacheln vor dem Block (Block bei PAD)
        sx, sy = PAD - links * T, PAD - oben * T
        w, h = e['groesse']
        ziel.alpha_composite(bild.crop((sx, sy, sx + w * T, sy + h * T)), (px * T, py * T + dy))

    tileset = Image.new('RGBA', (BREITE * T, gesamt_h * T), (0, 0, 0, 0))
    for e in eintraege.values():
        einsetzen(tileset, e, e['bilder'][0])
    tileset.save(os.path.join(OUT, 'objekte_tileset.png'))
    frames = []
    for f in range(N):
        fr = Image.new('RGBA', (BREITE * T, anim_h * T), (0, 0, 0, 0))
        for k in animierte:
            einsetzen(fr, eintraege[k], eintraege[k]['bilder'][1 + f])
        fr.save(os.path.join(OUT, 'animiert_frames', 'frame_%02d.png' % f))
        frames.append(fr)
    sheet = Image.new('RGBA', (BREITE * T, anim_h * T * N), (0, 0, 0, 0))
    for f, fr in enumerate(frames):
        sheet.alpha_composite(fr, (0, f * anim_h * T))
    sheet.save(os.path.join(OUT, 'objekte_tileset_animiert.png'))
    # Vorschau-GIF (auf dunklem Grund, 2x)
    vorschau = []
    for fr in frames:
        g = Image.new('RGBA', fr.size, (40, 44, 52, 255))
        g.alpha_composite(fr)
        vorschau.append(g.resize((fr.width * 2, fr.height * 2), Image.NEAREST).convert('RGB')
                        .quantize(colors=255, method=Image.Quantize.MAXCOVERAGE))
    vorschau[0].save(os.path.join(OUT, 'vorschau_animiert.gif'), save_all=True, append_images=vorschau[1:],
                     duration=170, loop=0, disposal=2)
    # Raster-Vorschau des statischen Tilesets (2x, Kachelgitter)
    g = Image.new('RGBA', tileset.size, (40, 44, 52, 255))
    g.alpha_composite(tileset)
    a = np.array(g)
    a[::T, :, :3] = (a[::T, :, :3] * 0.6 + 40).astype(np.uint8)
    a[:, ::T, :3] = (a[:, ::T, :3] * 0.6 + 40).astype(np.uint8)
    Image.fromarray(a).resize((g.width * 2, g.height * 2), Image.NEAREST).save(os.path.join(OUT, 'vorschau_raster.png'))
    # Index
    liste = []
    for (datei, anim), e in sorted(eintraege.items(), key=lambda kv: (kv[1]['platz'][1], kv[1]['platz'][0])):
        px, py = e['platz']
        w, h = e['groesse']
        links, oben, _, _ = e['rand']
        bx, by, wt, ht = e['o']['block']
        liste.append({'name': e['o']['basis'], 'datei': datei, 'animation': anim,
                      'slot_kacheln': {'x': px, 'y': py, 'breite': w, 'hoehe': h},
                      'objektblock_im_slot': {'x': links, 'y': oben, 'breite': wt, 'hoehe': ht},
                      'fundstellen_karte': e['fundstellen']})
    json.dump({'kachel': T, 'breite_kacheln': BREITE, 'hoehe_kacheln': gesamt_h,
               'animationsbereich_hoehe_kacheln': anim_h, 'animationsbilder': N, 'bilddauer_ms': 170,
               'objekte': liste}, open(os.path.join(OUT, 'objekte_tileset.json'), 'w'), indent=1, ensure_ascii=False)
    with zipfile.ZipFile(os.path.join(ROOT, 'maps', 'karte06', 'karte06_tileset.zip'), 'w', zipfile.ZIP_DEFLATED) as z:
        for wurzel, _, dateien in os.walk(OUT):
            for d in dateien:
                p = os.path.join(wurzel, d)
                z.write(p, os.path.relpath(p, os.path.join(ROOT, 'maps', 'karte06')))
    print('%d Objektvarianten, davon %d animiert; Tileset %dx%d Kacheln, Animationsbereich %d Kachelreihen'
          % (len(eintraege), len(animierte), BREITE, gesamt_h, anim_h))


if __name__ == '__main__':
    main()
