"""Tileset-Export fuer jede Karte (wie Karte 06): Boden- und Objekt-Tilesets am 16x16-Raster.

  python3 tools/tileset_export.py karte09            ->  maps/karte09/tileset/ und neues ZIP mit Kartennamen
  python3 tools/tileset_export.py karte09 --kein-zip

Inhalt von maps/karteXX/tileset/ (Aufbau identisch zu Karte 06):
  boden_tileset.png              jede Bodenkachel genau einmal; oben die animierten, darunter die unbewegten
  boden_tileset_animiert.png     NUR die animierten Bodenkacheln am exakt selben Platz, 16 Bilder untereinander
  boden_animiert_frames/         dieselben 16 Bilder einzeln
  boden_raster.json              Karte als Raster mit Kachelindex je Feld
  karteXX_boden.tmx              Tiled-Karte (Bodenebene, Animationen eingetragen)
  vorschau_boden.png             aus den Kacheln zusammengesetzt (Kontrolle: identisch zum Boden)
  vorschau_boden_animiert.gif
  objekte_tileset.png            ALLE Objekte (jede Variante einmal) in ihrem eigenen Kachelblock
  objekte_tileset_animiert.png   NUR die animierten Objekte am exakt selben Platz, 16 Bilder untereinander
  animiert_frames/               dieselben 16 Bilder einzeln
  objekte_tileset.json           je Objekt: Name, Animation, Platz im Tileset, Objektblock, Fundstellen auf der Karte
  vorschau_raster.png, vorschau_animiert.gif

Der Boden wird ohne Objekte gebaut (Objektliste ausgeblendet). Objekte werden einzeln auf transparentem Grund
gezeichnet, mit derselben Animation wie auf der Karte (ohne Schatten und Bodenfuss).
"""
import importlib, json, math, os, shutil, sys, zipfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image

import karte_bauen as kb
import karte04_bauen as k4

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
T = 16
N = 16
DAUER = 170
PAD = 6 * T
BREITE_OBJ = 40
BREITE_BODEN = 32
# Karte -> (Bau-Modul, Kartenname fuer das ZIP, Version)
KARTEN = {
    'karte02': ('karte02_bauen', 'Factorial_Town', 'v1.1'),
    'karte03': ('karte03_bauen', 'Server_Desert', 'v1.1'),
    'karte04': ('karte04_bauen', 'Gear_Savanna', 'v1.1'),
    'karte05': ('karte05_bauen', 'Freezeland', 'v1.1'),
    'karte07': ('karte07_bauen', 'The_Holy_Peaks', 'v1.0'),
    'karte08': ('karte08_bauen', 'Overdell', 'v1.0'),
    'karte09': ('karte09_bauen', 'Vamdemons_Keep', 'v1.0'),
    'karte10': ('karte10_bauen', 'Toy_Town', 'v1.0'),
    'karte11': ('karte11_bauen', 'Spiral_Mountain_Dark_Ocean', 'v1.0'),
    'karte12': ('karte12_bauen', 'Spiral_Mountain_Puppet_Woods', 'v1.0'),
    'karte13': ('karte13_bauen', 'Spiral_Mountain_Machine_City', 'v1.0'),
    'karte14': ('karte14_bauen', 'Spiral_Mountain_Summit', 'v1.0'),
    'karte15': ('karte15_bauen', 'Apocalymons_Realm', 'v1.0'),
    'karte16': ('karte16_bauen', 'The_Network', 'v1.0'),
    'karte17': ('karte17_bauen', 'Our_War_Game', 'v1.0'),
    'karte18': ('karte18_bauen', 'The_Fog_Bound_City', 'v1.0'),
    'karte19': ('karte19_bauen', 'Revenge', 'v1.0'),
    'karte20': ('karte20_bauen', 'Startdorf', 'v1.0'),
    'karte28': ('karte28_bauen', 'Tower_Forest', 'v1.0'),
}


# ---------------------------------------------------------------------------------------------- Boden
def boden_bild(mod, frame, leer):
    alt = mod.OBJ
    mod.OBJ = leer                                    # keine platzierung.json -> nur Boden
    try:
        return np.array(mod.bauen(frame=frame, speichern=False).convert('RGBA'))
    finally:
        mod.OBJ = alt


def schneefall_export(mod, out):
    """Karte 05: Schneefall als eigene, kachelbare Wetter-Ebene (1408x64 px = 88x4 Kacheln, wiederholt sich
    nahtlos ueber die ganze Karte) - der Boden bleibt dadurch unbewegt."""
    import math as _m, random as _r
    W, Hh = 1408, 64
    fd = os.path.join(out, 'wetter_schneefall_frames')
    os.makedirs(fd)
    sheet = Image.new('RGBA', (W, Hh * N), (0, 0, 0, 0))
    for frame in range(N):
        img = Image.new('RGBA', (W, Hh), (0, 0, 0, 0))
        for (kw, kh, n, groesse, seed, al) in ((176, 64, 9, 2, 3, 210), (128, 32, 7, 1, 8, 150)):
            rs = _r.Random(seed)
            flocken = [(rs.randrange(kw), rs.randrange(kh), rs.random() * 6.28) for _ in range(n)]
            dy = frame * kh // N
            lage = Image.new('RGBA', (W, Hh), (0, 0, 0, 0))
            px = lage.load()
            for oy in range(-kh, Hh + kh, kh):
                for ox in range(-kw, W + kw, kw):
                    for (fx, fy, ph) in flocken:
                        x = ox + fx + int(round(2 * _m.sin(2 * _m.pi * frame / N + ph)))
                        y = oy + (fy + dy) % kh
                        for ddx in range(groesse):
                            for ddy in range(groesse):
                                X, Y = (x + ddx) % W, y + ddy
                                if 0 <= Y < Hh:
                                    px[X, Y] = (255, 255, 255, al)
            img.alpha_composite(lage)
        img.save(os.path.join(fd, 'frame_%02d.png' % frame))
        sheet.alpha_composite(img, (0, frame * Hh))
    sheet.save(os.path.join(out, 'wetter_schneefall.png'))
    print('  Schneefall als Wetter-Ebene (88x4 Kacheln, kachelbar)')


def boden_export(karte, mod, out):
    if karte == 'karte05':                              # Schneefall ist Wetter, nicht Boden
        mod.schneefall = lambda img, frame: None
        schneefall_export(mod, out)
    leer = os.path.join(out, '_keine_objekte')
    os.makedirs(leer, exist_ok=True)
    stand = boden_bild(mod, None, leer)
    frames = [boden_bild(mod, f, leer) for f in range(N)]
    shutil.rmtree(leer)
    Hh, W = stand.shape[:2]
    rows, cols = Hh // T, W // T

    def kachel(a, x, y):
        return a[y * T:(y + 1) * T, x * T:(x + 1) * T]
    felder, anim_keys, stat_keys = {}, {}, {}
    for y in range(rows):
        for x in range(cols):
            s = kachel(stand, x, y)
            folge = [kachel(fr, x, y) for fr in frames]
            animiert = any(not np.array_equal(f, folge[0]) for f in folge[1:])
            if animiert:
                key = b''.join(f.tobytes() for f in folge)
                anim_keys.setdefault(key, (folge[0], folge))
            else:
                key = s.tobytes()
                stat_keys.setdefault(key, s)
            felder[(x, y)] = (animiert, key)
    anim_liste, stat_liste = list(anim_keys), list(stat_keys)
    B = BREITE_BODEN
    anim_reihen = (len(anim_liste) + B - 1) // B
    stat_reihen = (len(stat_liste) + B - 1) // B
    index = {}
    for i, k in enumerate(anim_liste):
        index[(True, k)] = i
    for i, k in enumerate(stat_liste):
        index[(False, k)] = anim_reihen * B + i
    gesamt = anim_reihen + stat_reihen
    ts = np.zeros((gesamt * T, B * T, 4), np.uint8)

    def setze(ziel, i, t):
        r, c = divmod(i, B)
        ziel[r * T:(r + 1) * T, c * T:(c + 1) * T] = t
    for k in anim_liste:
        setze(ts, index[(True, k)], anim_keys[k][0])
    for k in stat_liste:
        setze(ts, index[(False, k)], stat_keys[k])
    Image.fromarray(ts).save(os.path.join(out, 'boden_tileset.png'))
    fd = os.path.join(out, 'boden_animiert_frames')
    os.makedirs(fd)
    ah = max(1, anim_reihen) * T
    sheet = np.zeros((ah * N, B * T, 4), np.uint8)
    vor = []
    for f in range(N):
        fr = np.zeros((ah, B * T, 4), np.uint8)
        for k in anim_liste:
            setze(fr, index[(True, k)], anim_keys[k][1][f])
        Image.fromarray(fr).save(os.path.join(fd, 'frame_%02d.png' % f))
        sheet[f * ah:(f + 1) * ah] = fr
        g = Image.new('RGBA', (B * T, ah), (40, 44, 52, 255))
        g.alpha_composite(Image.fromarray(fr))
        vor.append(g.resize((g.width * 2, g.height * 2), Image.NEAREST).convert('RGB')
                   .quantize(colors=255, method=Image.Quantize.MAXCOVERAGE))
    Image.fromarray(sheet).save(os.path.join(out, 'boden_tileset_animiert.png'))
    vor[0].save(os.path.join(out, 'vorschau_boden_animiert.gif'), save_all=True, append_images=vor[1:],
                duration=DAUER, loop=0)
    # Standbild der Karte: animierte Felder zeigen Bild 0 (wie im Tileset)
    raster = [[index[felder[(x, y)]] for x in range(cols)] for y in range(rows)]
    probe = np.zeros_like(stand)
    for y in range(rows):
        for x in range(cols):
            r, c = divmod(raster[y][x], B)
            probe[y * T:(y + 1) * T, x * T:(x + 1) * T] = ts[r * T:(r + 1) * T, c * T:(c + 1) * T]
    Image.fromarray(probe).save(os.path.join(out, 'vorschau_boden.png'))
    json.dump({'kachel': T, 'breite_kacheln': B, 'tileset_reihen': gesamt,
               'animierte_kacheln': len(anim_liste), 'animationsbereich_hoehe_kacheln': anim_reihen,
               'animationsbilder': N, 'bilddauer_ms': DAUER, 'unbewegte_kacheln': len(stat_liste),
               'karte_spalten': cols, 'karte_zeilen': rows, 'raster': raster},
              open(os.path.join(out, 'boden_raster.json'), 'w'))
    anim_tsx = ''.join(
        '   <tile id="%d"><animation>%s</animation></tile>\n'
        % (i, ''.join('<frame tileid="%d" duration="%d"/>' % (gesamt * B + f * anim_reihen * B + i, DAUER)
                      for f in range(N)))
        for i in range(len(anim_liste)))
    daten = '\n'.join(','.join(str(v + 1) for v in reihe) for reihe in raster)
    tmx = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<map version="1.10" orientation="orthogonal" renderorder="right-down" width="%d" height="%d" '
           'tilewidth="16" tileheight="16" infinite="0">\n'
           ' <tileset firstgid="1" name="boden" tilewidth="16" tileheight="16" tilecount="%d" columns="%d">\n'
           '  <image source="boden_tileset.png" width="%d" height="%d"/>\n%s </tileset>\n'
           ' <tileset firstgid="%d" name="boden_animiert" tilewidth="16" tileheight="16" tilecount="%d" columns="%d">\n'
           '  <image source="boden_tileset_animiert.png" width="%d" height="%d"/>\n </tileset>\n'
           ' <layer id="1" name="Boden" width="%d" height="%d">\n  <data encoding="csv">\n%s\n  </data>\n </layer>\n'
           '</map>\n') % (cols, rows, gesamt * B, B, B * T, gesamt * T, anim_tsx,
                          gesamt * B + 1, anim_reihen * B * N, B, B * T, ah * N, cols, rows, daten)
    open(os.path.join(out, '%s_boden.tmx' % karte), 'w').write(tmx)
    print('  Boden %dx%d: %d unbewegte + %d animierte Kacheln' % (cols, rows, len(stat_liste), len(anim_liste)))


# ---------------------------------------------------------------------------------------------- Objekte
def sprite_bild(karte, mod, o, sp, frame):
    """Sprite eines Objekts in einem Animationsbild - dieselben Umformungen wie beim Kartenbau."""
    if frame is None:
        if o.get('anim') == 'muehle20':                      # Karte 20: Muehlenfluegel gehoeren auch ins Standbild
            return k4.TEILANIM['muehle20'](sp, 0, o)
        return sp
    anim = o.get('anim')
    if karte == 'karte03':
        if o.get('proz'):
            sp = mod.kp.PROZ[o['proz']](frame)
        elif anim == 'wehen':
            sp = kb.wehen(sp, kb.wind(frame, o['x']))
        elif anim == 'flagge':
            sp = k4.fahne_wehen(sp, frame, o['x'] * 0.37)
        elif anim == 'kaktus':
            sp = mod.kaktus(sp, frame, o['x'], o['y'])
        if o.get('dreh'):
            sp = mod.schuesseln_drehen(sp, frame, o['x'] + o['y'], o['basis'])
        return sp
    if karte == 'karte02':
        if anim == 'wehen':
            return kb.wehen(sp, kb.wind(frame, o['x']))
        if anim == 'greifarm':
            return mod.greifarm_pose(sp, frame, (o['x'] * 13 + o['y'] * 7) % 16)
        if anim == 'portal':
            return mod.portal_pose(sp, frame, (o['x'] // 16) % 16)
        if anim == 'kran':
            return Image.open(os.path.join(mod.OBJ, o['datei'].replace('abgeleitet-kran_', 'abgeleitet-kran_f%02d_' % frame))).convert('RGBA')
        return sp
    if anim in ('wehen', 'blume'):
        return kb.wehen(sp, kb.wind(frame, o['x']))
    if anim == 'baum':
        return k4.baum_wind(sp, frame, o['x'] + o['y'] * 0.3)
    if anim in ('fahne', 'flagge'):
        return k4.fahne_wehen(sp, frame, o['x'] * 0.37)
    if anim == 'reaktor':
        return k4.reaktor_ruetteln(sp, frame, o['x'])
    if anim in ('kerzen', 'feuer_kamin', 'feuer', 'feuer_lila'):
        return k4.flammen_bewegen(sp, frame, o['x'] + o['y'], lila=anim == 'feuer_lila')
    if anim == 'portal':
        return k4.portal_drehen(sp, frame)
    if anim == 'brunnen':
        return k4.brunnen_fliessen(sp, frame)
    if anim == 'rauch':
        return k4.rauch_steigen(sp, frame)
    if anim in ('ampel', 'signal'):
        return k4.ampel_schalten(sp, frame, anim)
    if anim == 'windrad':
        return k4.windrad_drehen(sp, frame)
    if anim in k4.TEILANIM:
        return k4.TEILANIM[anim](sp, frame, o)
    return sp


def nachher(karte, mod, img, o2, cache, frame):
    """Leuchten, Glut, Lichtschein usw. wie auf der Karte (wirkt nur innerhalb des Objekt-Platzes)."""
    f = frame or 0
    if karte == 'karte02':
        if o2.get('anim') == 'laterne':
            kb.laternen_licht(img, [o2], frame)
        try:
            import karte02_objekte as ko
            ko.animieren(img, [o2], f)
        except ImportError:
            pass
        return
    if karte == 'karte03':
        mod.animieren(img, [o2], f)
        return
    if o2.get('anim') == 'blume' and frame is not None:
        k4.bluete_puls(img, o2, cache[o2['datei']], frame)
    k4.animieren(img, [o2], cache, f)
    if karte == 'karte07':
        import karte06_bauen as k6
        k6.animieren_k6(img, [o2], cache, f)


def block_von(o, sp):
    if o.get('block'):
        return o['block']
    a = np.array(sp.getchannel('A')) > 0
    ys, xs = np.nonzero(a)
    x0, x1 = o['x'] + xs.min(), o['x'] + xs.max()
    y0, y1 = o['y'] + ys.min(), o['y'] + ys.max()
    bx, by = x0 // T, y0 // T
    return [int(bx), int(by), int(x1 // T - bx + 1), int(y1 // T - by + 1)]


def objekte_export(karte, mod, out):
    obj_dir = mod.OBJ
    objs = [o for o in json.load(open(os.path.join(obj_dir, 'platzierung.json')))
            if o.get('basis') not in ('schatten',) and os.path.exists(os.path.join(obj_dir, o['datei']))]
    if not objs:                                         # Karte ohne Objekte (z. B. Karte 17 v1.0): kein Objekt-Tileset
        print('  keine Objekte - Objekt-Tileset entfaellt')
        return
    cache = {}
    for o in objs:
        if o['datei'] not in cache:
            cache[o['datei']] = Image.open(os.path.join(obj_dir, o['datei'])).convert('RGBA')
        o['block'] = block_von(o, cache[o['datei']])
    eintraege = {}
    for o in objs:
        key = (o['datei'], o.get('anim'), o.get('proz'), bool(o.get('dreh')))
        if key not in eintraege:
            eintraege[key] = {'o': o, 'fundstellen': []}
        eintraege[key]['fundstellen'].append({'block': o['block'], 'fusskachel': o.get('kachel')})
    animierte = {k for k in eintraege if k[1] or k[2] or k[3]}

    def darstellen(o, frame):
        bx, by, wt, ht = o['block']
        sp0 = cache[o['datei']]
        x0, y0 = bx * T - PAD, by * T - PAD
        W = max(wt * T, o['x'] + sp0.width - bx * T) + 2 * PAD
        Hh = max(ht * T, o['y'] + sp0.height - by * T) + 2 * PAD
        img = Image.new('RGBA', (W, Hh), (0, 0, 0, 0))
        o2 = dict(o, x=o['x'] - x0, y=o['y'] - y0)
        sp = sprite_bild(karte, mod, o, sp0, frame)
        img.alpha_composite(sp, (o2['x'], o2['y']))
        nachher(karte, mod, img, o2, cache, frame)
        return img
    for key, e in eintraege.items():
        o = e['o']
        bx, by, wt, ht = o['block']
        bilder = [darstellen(o, None)]
        if key in animierte:
            bilder += [darstellen(o, f) for f in range(N)]
        hmax = max(b.height for b in bilder)
        wmax = max(b.width for b in bilder)
        alpha = np.zeros((hmax, wmax), bool)
        for b in bilder:
            a_ = np.array(b.getchannel('A')) > 0
            alpha[:a_.shape[0], :a_.shape[1]] |= a_
        ys, xs = np.nonzero(alpha)
        if not len(ys):
            ys, xs = np.array([PAD]), np.array([PAD])
        links = max(0, math.ceil((PAD - xs.min()) / T))
        oben = max(0, math.ceil((PAD - ys.min()) / T))
        rechts = max(0, math.ceil((xs.max() + 1 - (PAD + wt * T)) / T))
        unten = max(0, math.ceil((ys.max() + 1 - (PAD + ht * T)) / T))
        e.update(bilder=bilder, rand=(links, oben, rechts, unten), groesse=(links + wt + rechts, oben + ht + unten))
    breite = max(BREITE_OBJ, max(e['groesse'][0] for e in eintraege.values()))

    def packen(keys, y_start):
        keys = sorted(keys, key=lambda k: (-eintraege[k]['groesse'][1], -eintraege[k]['groesse'][0], str(k)))
        x, y, reihe_h = 0, y_start, 0
        for k in keys:
            w, h = eintraege[k]['groesse']
            if x + w > breite:
                x, y, reihe_h = 0, y + reihe_h, 0
            eintraege[k]['platz'] = (x, y)
            x += w
            reihe_h = max(reihe_h, h)
        return y + reihe_h
    anim_h = packen(animierte, 0)
    gesamt_h = packen(set(eintraege) - animierte, anim_h)

    def einsetzen(ziel, e, bild):
        px, py = e['platz']
        links, oben = e['rand'][0], e['rand'][1]
        sx, sy = PAD - links * T, PAD - oben * T
        w, h = e['groesse']
        ziel.alpha_composite(bild.crop((sx, sy, sx + w * T, sy + h * T)), (px * T, py * T))
    tileset = Image.new('RGBA', (breite * T, gesamt_h * T), (0, 0, 0, 0))
    for e in eintraege.values():
        einsetzen(tileset, e, e['bilder'][0])
    tileset.save(os.path.join(out, 'objekte_tileset.png'))
    os.makedirs(os.path.join(out, 'animiert_frames'))
    frames = []
    for f in range(N):
        fr = Image.new('RGBA', (breite * T, max(1, anim_h) * T), (0, 0, 0, 0))
        for k in animierte:
            einsetzen(fr, eintraege[k], eintraege[k]['bilder'][1 + f])
        fr.save(os.path.join(out, 'animiert_frames', 'frame_%02d.png' % f))
        frames.append(fr)
    sheet = Image.new('RGBA', (breite * T, max(1, anim_h) * T * N), (0, 0, 0, 0))
    for f, fr in enumerate(frames):
        sheet.alpha_composite(fr, (0, f * max(1, anim_h) * T))
    sheet.save(os.path.join(out, 'objekte_tileset_animiert.png'))
    vorschau = []
    for fr in frames:
        g = Image.new('RGBA', fr.size, (40, 44, 52, 255))
        g.alpha_composite(fr)
        vorschau.append(g.resize((fr.width * 2, fr.height * 2), Image.NEAREST).convert('RGB')
                        .quantize(colors=255, method=Image.Quantize.MAXCOVERAGE))
    vorschau[0].save(os.path.join(out, 'vorschau_animiert.gif'), save_all=True, append_images=vorschau[1:],
                     duration=DAUER, loop=0, disposal=2)
    g = Image.new('RGBA', tileset.size, (40, 44, 52, 255))
    g.alpha_composite(tileset)
    a = np.array(g)
    a[::T, :, :3] = (a[::T, :, :3] * 0.6 + 40).astype(np.uint8)
    a[:, ::T, :3] = (a[:, ::T, :3] * 0.6 + 40).astype(np.uint8)
    Image.fromarray(a).resize((g.width * 2, g.height * 2), Image.NEAREST).save(os.path.join(out, 'vorschau_raster.png'))
    liste = []
    for key, e in sorted(eintraege.items(), key=lambda kv: (kv[1]['platz'][1], kv[1]['platz'][0])):
        px, py = e['platz']
        w, h = e['groesse']
        links, oben, _, _ = e['rand']
        bx, by, wt, ht = e['o']['block']
        liste.append({'name': e['o'].get('basis'), 'datei': key[0], 'animation': key[1] or key[2] or ('dreh' if key[3] else None),
                      'slot_kacheln': {'x': px, 'y': py, 'breite': w, 'hoehe': h},
                      'objektblock_im_slot': {'x': links, 'y': oben, 'breite': wt, 'hoehe': ht},
                      'fundstellen_karte': e['fundstellen']})
    json.dump({'kachel': T, 'breite_kacheln': breite, 'hoehe_kacheln': gesamt_h,
               'animationsbereich_hoehe_kacheln': anim_h, 'animationsbilder': N, 'bilddauer_ms': DAUER,
               'objekte': liste}, open(os.path.join(out, 'objekte_tileset.json'), 'w'), indent=1, ensure_ascii=False)
    print('  Objekte: %d Varianten, davon %d animiert; Tileset %dx%d Kacheln' % (len(eintraege), len(animierte), breite, gesamt_h))


def ueberlagerung_export(karte, mod, out):
    """Karte 10: Ebene UEBER den Objekten (Telegrafenleitungen, Mauerkrone vor den Turmfuessen) als ganzes Bild,
    als Kachel-Tileset (jede Kachel einmal) mit Raster und als zweite Ebene 'Ueberlagerung' in der Tiled-Karte."""
    import re
    lay = json.load(open(os.path.join(mod.KARTE, 'layout.json')))
    leer = os.path.join(out, '_keine_objekte')
    os.makedirs(leer, exist_ok=True)
    grund = boden_bild(mod, None, leer)
    shutil.rmtree(leer)
    objs = json.load(open(os.path.join(mod.OBJ, 'platzierung.json')))
    cache = {o['datei']: Image.open(os.path.join(mod.OBJ, o['datei'])).convert('RGBA') for o in objs}
    ov = np.array(mod.ueberlagerung(objs, cache, mod.mauer_maske(lay), grund))
    Image.fromarray(ov).save(os.path.join(out, 'ueberlagerung_ebene.png'))
    Hh, W = ov.shape[:2]
    rows, cols = Hh // T, W // T
    B = BREITE_BODEN
    kacheln, index, raster = [], {}, []
    for y in range(rows):
        reihe = []
        for x in range(cols):
            k = ov[y * T:(y + 1) * T, x * T:(x + 1) * T]
            if not k[..., 3].any():
                reihe.append(-1)
                continue
            key = k.tobytes()
            if key not in index:
                index[key] = len(kacheln)
                kacheln.append(k)
            reihe.append(index[key])
        raster.append(reihe)
    n_r = max(1, (len(kacheln) + B - 1) // B)
    ts = np.zeros((n_r * T, B * T, 4), np.uint8)
    for i, k in enumerate(kacheln):
        r, c = divmod(i, B)
        ts[r * T:(r + 1) * T, c * T:(c + 1) * T] = k
    Image.fromarray(ts).save(os.path.join(out, 'ueberlagerung_tileset.png'))
    json.dump({'kachel': T, 'breite_kacheln': B, 'kacheln': len(kacheln), 'leer': -1, 'karte_spalten': cols,
               'karte_zeilen': rows, 'raster': raster}, open(os.path.join(out, 'ueberlagerung_raster.json'), 'w'))
    tmx_p = os.path.join(out, '%s_boden.tmx' % karte)
    tmx = open(tmx_p).read()
    gids = [(int(a), int(b)) for a, b in re.findall(r'firstgid="(\d+)"[^>]*tilecount="(\d+)"', tmx)]
    first = max(a + b for a, b in gids)
    daten = '\n'.join(','.join(str(v + first) if v >= 0 else '0' for v in reihe) for reihe in raster)
    zusatz = (' <tileset firstgid="%d" name="ueberlagerung" tilewidth="16" tileheight="16" tilecount="%d" columns="%d">\n'
              '  <image source="ueberlagerung_tileset.png" width="%d" height="%d"/>\n </tileset>\n'
              ' <layer id="2" name="Ueberlagerung (ueber den Objekten)" width="%d" height="%d">\n'
              '  <data encoding="csv">\n%s\n  </data>\n </layer>\n') % (first, n_r * B, B, B * T, n_r * T, cols, rows, daten)
    pos = tmx.index(' <layer id="1"')
    tmx = tmx[:pos] + zusatz.split(' <layer')[0] + tmx[pos:]
    tmx = tmx.replace('</map>', ' <layer' + zusatz.split(' <layer', 1)[1] + '</map>')
    open(tmx_p, 'w').write(tmx)
    print('  Ueberlagerung: %d Kacheln (Telegrafenleitungen, Mauer vor den Turmfuessen)' % len(kacheln))


README_TILESET = """
## Tilesets (Ordner tileset/)

Aufbau wie bei Karte 06, alles am 16x16-Raster:

- `boden_tileset.png` - jede Bodenkachel genau einmal; oben die animierten Kacheln, darunter die unbewegten.
- `boden_tileset_animiert.png` - nur die animierten Bodenkacheln, exakt am selben Platz; 16 Bilder untereinander
  (Bild n beginnt bei y = n x Hoehe des Animationsbereichs, steht in `boden_raster.json`). Einzeln in `boden_animiert_frames/`.
- `boden_raster.json` - die Karte als Raster mit dem Kachelindex je Feld; `%s_boden.tmx` - fertige Tiled-Karte (Bodenebene).
- `objekte_tileset.png` - alle Objekte (jede Variante einmal) in ihrem eigenen Kachelblock, ohne Boden und Schatten.
- `objekte_tileset_animiert.png` - nur die animierten Objekte am exakt selben Platz, 16 Bilder untereinander;
  Einzelbilder in `animiert_frames/`.
- `objekte_tileset.json` - je Objekt: Name, Animation, Platz im Tileset, Objektblock und alle Fundstellen auf der Karte.
- Vorschauen: `vorschau_boden.png`, `vorschau_raster.png`, `vorschau_animiert.gif`, `vorschau_boden_animiert.gif`.%s

Bilddauer 170 ms, 16 Animationsbilder.%s
"""
README_UEBER = """
- `ueberlagerung_ebene.png`, `ueberlagerung_tileset.png`, `ueberlagerung_raster.json` - Ebene UEBER den Objekten
  (Telegrafenleitungen, Mauerkrone vor den Turmfuessen); Raster-Index -1 = leer. In der Tiled-Karte als 2. Ebene."""
README_SCHNEE = """
- `wetter_schneefall.png` - der Schneefall als eigene Wetter-Ebene (ueber Boden und Objekten): 1408x64 px,
  wiederholt sich nahtlos ueber die ganze Karte; 16 Bilder untereinander, einzeln in `wetter_schneefall_frames/`."""


def zip_neu(karte, name, version, out):
    """Bestehendes Karten-ZIP (README, PNG, Discord-GIF) um den Ordner tileset/ ergaenzen."""
    vdir = os.path.join(ROOT, 'maps', karte, version)
    os.makedirs(vdir, exist_ok=True)
    ziel = os.path.join(vdir, '%s_%s.zip' % (name, version))
    alte = [os.path.join(vdir, d) for d in os.listdir(vdir) if d.endswith('.zip')]
    inhalt = {}
    for z_ in alte:
        with zipfile.ZipFile(z_) as z:
            for n in z.namelist():
                if not n.startswith('tileset/'):
                    inhalt[n] = z.read(n)
    readme = inhalt.get('README.md', b'').decode('utf-8')
    if '## Tilesets' not in readme:
        readme += README_TILESET % (karte, README_UEBER if karte == 'karte10' else '',
                                    README_SCHNEE if karte == 'karte05' else '')
    inhalt['README.md'] = readme.encode('utf-8')
    tmp = ziel + '.tmp'
    with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as z:
        for n, d in inhalt.items():
            z.writestr(n, d)
        for wurzel, _, dateien in os.walk(out):
            for d in sorted(dateien):
                p = os.path.join(wurzel, d)
                z.write(p, os.path.relpath(p, os.path.dirname(out)))
    for z_ in alte:
        if os.path.abspath(z_) != os.path.abspath(ziel):
            os.remove(z_)
    os.replace(tmp, ziel)
    print('  ZIP:', os.path.relpath(ziel, ROOT), '%.1f MB' % (os.path.getsize(ziel) / 1e6))


def main():
    karte = sys.argv[1]
    modname, name, version = KARTEN[karte]
    mod = importlib.import_module(modname)
    global N
    N = getattr(mod, 'N_FRAMES', 16)
    global DAUER
    DAUER = getattr(mod, 'BILDDAUER', DAUER)
    out = os.path.join(ROOT, 'maps', karte, 'tileset')
    if os.path.isdir(out):
        shutil.rmtree(out)
    os.makedirs(out)
    print(karte, name)
    objekte_export(karte, mod, out)
    boden_export(karte, mod, out)
    if karte == 'karte10':
        ueberlagerung_export(karte, mod, out)
    if '--kein-zip' not in sys.argv:
        zip_neu(karte, name, version, out)


if __name__ == '__main__':
    main()
