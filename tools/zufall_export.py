"""Export der Kartenstuecke fuer den JS-Generator (maps/zufall/js/).

  python3 tools/zufall_export.py --typ wald        (alle Lagen im Wald-Stil, 4 Prozesse parallel)
  python3 tools/zufall_export.py --typ netz        (dieselben Stuecke im Stil von Karte 16 - The Network)

Jede Lage jedes Stuecks wird einmal mit der Karte-01-Technik fertig gerendert. Damit Baeume und
Uebergaenge an den Raendern genauso aussehen wie in einer echten Karte, wird das Stueck mit einem Rand
von PAD Kacheln gebaut (Randkacheln nach aussen fortgesetzt - wegen der genormten Kanten ist das genau
das, was ein passender Nachbar dort haette). Objekte zaehlen nur, wenn ihr Fuss im Stueck steht.

Gelaende und Objekte je Kartentyp: wald = tools/zufall_a02.py (A02, Karte 20, 45-Grad-Kanten), netz = tools/zufall_netz.py
(Karte 16, The Network).
Ausgabe je Lage:
  stuecke/<id>_boden.png    reiner Boden, genau Stueckgroesse                  (1. alle Stuecke)
  stuecke/<id>_schatten.png Kontakt- und Schlagschatten, um PAD Kacheln groesser (2. alle Stuecke)
  stuecke/<id>_objekte.png  deckende Objektpixel + Bodenwall, wie schatten      (3. von Nord nach Sued)
  stuecke/<id>_oben.png     obere Teile hoher Objekte (Baumkronen), wie schatten (4. ueber dem Spieler)
  Objekt- und Oben-Bilder sind groesser als das Stueck, damit ueberstehende Kronen erhalten bleiben.
  manifest.json            Kanten, Kollision (1 = gesperrt), Spawn-/Bosspunkt, Gewichte
"""
import json, os, shutil, sys, zlib
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
import zufall_stuecke as zs, zufall_karte as zk

ROOT = zk.ROOT
ZIEL = os.path.join(ROOT, 'maps', 'zufall', 'js')
N, T, PAD = zs.N, 16, 4
SPRITES = os.path.join(ROOT, 'maps', 'zufall', '_bau', 'sprites')   # gesammelte Sprites (Zwischenablage)


def lage_id(l):
    return '%s_%s' % (l['name'], l['lage'])


def gepolstert(raster):
    h, w = len(raster), len(raster[0])
    return [''.join(raster[min(max(y - PAD, 0), h - 1)][min(max(x - PAD, 0), w - 1)] for x in range(w + 2 * PAD))
            for y in range(h + 2 * PAD)]


MODUL = {'wald': 'zufall_a02', 'netz': 'zufall_netz'}
VARIANTEN = {'wald': 4}                                      # Lagen-Varianten je Stueck (verschiedene Deko)        # Kartentypen: Wald (A02, Karte 20) und Netz (Karte 16)


def rendern(arg):
    l, typ = arg
    mod = __import__(MODUL[typ])
    lid = lage_id(l)
    raster = gepolstert(l['raster'])
    h, w = len(l['raster']), len(l['raster'][0])
    fest = [(n, x + PAD, y + PAD) for n, x, y in l.get('objekte', [])]
    symmetrie = [tuple(fest[i] for i in s) for s in l.get('symmetrie', [])]
    obj = os.path.join(ROOT, 'maps', 'zufall', '_bau', 'export_%s_%s' % (typ, lid))
    if os.path.exists(obj):
        shutil.rmtree(obj)
    os.makedirs(obj)
    # Gelaende und Objekte des Typs. Der Rand (PAD Kacheln, Randkacheln fortgesetzt) bekommt ebenfalls Objekte - so
    # verhalten sich Platzierung und Kanten am Rand wie mit einem echten Nachbarn; behalten werden nur Objekte mit dem
    # Fuss im Stueck. Netz: Nebel/Raster periodisch je Feld (ursprung), Straenge/Fragmente nur im Stueck (bereich).
    bereich = np.zeros((len(raster) * T, len(raster[0]) * T), bool)
    bereich[PAD * T:(PAD + h) * T, PAD * T:(PAD + w) * T] = True
    seed = zlib.crc32(lid.encode())                                     # je Stueck eigene Deko / Leere
    boden_rgb, wasser = mod.boden_bauen(raster, None, fest=fest, ursprung=(PAD * T, PAD * T), bereich=bereich, seed=seed)
    objs = mod.objekte_setzen(raster, fest, symmetrie, obj, seed=seed, innen=(PAD, PAD, PAD + w, PAD + h))
    objs = [o for o in objs if PAD <= o['kachel'][0] < PAD + w and PAD <= o['kachel'][1] < PAD + h]
    if typ == 'wald' and l['typ'] not in ('start', 'boss') and 'gabel' not in l['name'] and 'kreuz' not in l['name']:
        objs = [o for o in objs if o.get('basis') != 'laterne']
    boden_rgb = mod.waldboden(boden_rgb, objs, obj)                     # Wurzeln des Dschungelbaums gehoeren zum Boden
    voll, cache = mod.zeichnen(boden_rgb, wasser, objs, obj)
    boden = Image.fromarray(boden_rgb).convert('RGBA')

    # --- Sprite-Maske: deckende Objektpixel (Kontaktschatten/Lichtschein zaehlen zum Boden)
    maske = np.zeros(voll.size[::-1], bool)
    oben = Image.new('RGBA', voll.size)
    for o in sorted(objs, key=lambda o: (o.get('ebene', 1), o['y'] + o.get('fuss', 0))):
        sp = Image.open(os.path.join(obj, o['datei'])).convert('RGBA')
        if o.get('spiegeln'):
            sp = sp.transpose(Image.FLIP_LEFT_RIGHT)
        a = np.array(sp.getchannel('A')) >= 200
        x0, y0 = o['x'], o['y']
        xs0, ys0 = max(0, x0), max(0, y0)
        xs1, ys1 = min(voll.width, x0 + sp.width), min(voll.height, y0 + sp.height)
        if xs1 > xs0 and ys1 > ys0:
            maske[ys0:ys1, xs0:xs1] |= a[ys0 - y0:ys1 - y0, xs0 - x0:xs1 - x0]
        # oben: Teile hoher Objekte oberhalb ihrer Sockelreihe (Spieler laeuft dahinter)
        if o.get('ebene', 1) == 1 and o['block'][3] >= 2:
            sockel_y = (o['block'][1] + o['block'][3] - 1) * T - o['y']
            if sockel_y > 0:
                oben.alpha_composite(sp.crop((0, 0, sp.width, min(sockel_y, sp.height))), (x0, y0))
    # --- Schatten als eigene Ebene (reicht wie die Kronen ueber den Rand - sonst enden Schlagschatten an der Naht):
    # dieselben Objekte auf rein weissem und rein schwarzem Boden zeichnen. Schatten = Farbe S mit Deckkraft a:
    # weiss -> 255 (1 - a) + S a, schwarz -> S a  =>  a = 1 - (weiss - schwarz) / 255, S = schwarz / a
    def auf(wert):
        grund = np.full(boden_rgb.shape, wert, np.uint8)
        return np.array(mod.zeichnen(grund, wasser, objs, obj)[0].convert('RGB')).astype(np.float32)
    rw, rb = auf(255), auf(0)
    alpha = np.clip(1 - (rw - rb).mean(-1) / 255.0, 0, 1)
    alpha[maske] = 0                                             # unter den Sprites egal (Sprites decken)
    alpha[alpha < 0.02] = 0
    farbe = np.clip(rb / np.maximum(alpha, 1e-3)[..., None], 0, 255)
    sch = np.zeros(rw.shape[:2] + (4,), np.uint8)
    sch[..., :3] = farbe.astype(np.uint8)
    sch[..., 3] = np.round(alpha * 255).astype(np.uint8)
    schatten_bild = Image.fromarray(sch)
    v, b = np.array(voll), np.array(boden)
    # boden: nur das Stueck, reiner Boden ohne Schatten und Objekte
    boden_bild = boden.crop((PAD * T, PAD * T, (PAD + w) * T, (PAD + h) * T))
    # objekte: deckende Sprite-Pixel + Bodenwall an den Fuessen (was nach Boden+Schatten noch anders ist)
    ref = Image.fromarray(b); ref.alpha_composite(schatten_bild)
    anders = np.abs(v[..., :3].astype(int) - np.array(ref)[..., :3]).sum(-1) > 6
    ob = v.copy()
    ob[~(maske | anders)] = 0
    objekte_bild = Image.fromarray(ob)

    # --- Kollision im Stueck wie tools/kollision.py: 1 begehbar, 2 gesperrt, 3 begehbar + verdeckt
    koll = mod.kollision(raster, objs, cache, wasser, PAD, PAD, w, h)

    def frei_nahe(x, y):
        best = min(((abs(xx - x) + abs(yy - y), xx, yy) for yy in range(h) for xx in range(w) if koll[yy][xx] == '1'))
        return [best[1], best[2]]
    punkte = {}
    for n, x, y in l.get('objekte', []):
        if n.startswith('zufall_portal/'):
            punkte['spawn'] = frei_nahe(x, y + 1)                  # direkt vor der Ankunft (Netz: auf den Pfeilfeldern)
        if n.startswith('dschungel/'):
            punkte['boss'] = frei_nahe(x, y + 4)
    boden_bild.save(os.path.join(ZIEL, 'stuecke', typ, lid + '_boden.png'), optimize=True)
    schatten_bild.save(os.path.join(ZIEL, 'stuecke', typ, lid + '_schatten.png'), optimize=True)
    objekte_bild.save(os.path.join(ZIEL, 'stuecke', typ, lid + '_objekte.png'), optimize=True)
    oben.save(os.path.join(ZIEL, 'stuecke', typ, lid + '_oben.png'), optimize=True)
    # Komplettbild des Stuecks (Boden + Schatten + Objekte + oben), genau Stueckgroesse
    ganz = voll.copy(); ganz.alpha_composite(oben)
    ganz.crop((PAD * T, PAD * T, (PAD + w) * T, (PAD + h) * T)).save(
        os.path.join(ZIEL, 'stuecke', typ, lid + '_komplett.png'), optimize=True)
    # Sprites fuer das Objekt-Tileset sammeln, Objektliste relativ zur linken oberen Stueckecke (Pixel)
    liste = []
    for o in sorted(objs, key=lambda o: (o.get('ebene', 1), o['y'] + o.get('fuss', 0))):
        name = o['datei'][:-4]
        ziel = os.path.join(SPRITES, typ, o['datei'])
        if not os.path.exists(ziel):
            os.makedirs(os.path.dirname(ziel), exist_ok=True)
            tmp = ziel + '.%d.tmp' % os.getpid()
            shutil.copy(os.path.join(obj, o['datei']), tmp)
            os.replace(tmp, ziel)
        bx, by, bw, bh = o['block']
        e = {'s': name, 'x': o['x'] - PAD * T, 'y': o['y'] - PAD * T,
             'block': [bx - PAD, by - PAD, bw, bh], 'ebene': o.get('ebene', 1)}
        if o.get('anim'):
            e['anim'] = o['anim']
        if o.get('spiegeln'):
            e['spiegeln'] = True
        liste.append(e)
    shutil.rmtree(obj)
    print('  ', lid, len(objs), 'Objekte', flush=True)
    return {'id': lid, 'name': l['name'], 'lage': l['lage'], 'typ': l['typ'], 'gewicht': l['gewicht'],
            'felder': list(l['felder']),
            'kanten': {'%d,%d,%s' % k: t for k, t in l['kanten'].items()},
            'boden': 'stuecke/%s/%s_boden.png' % (typ, lid), 'schatten': 'stuecke/%s/%s_schatten.png' % (typ, lid), 'objekte': 'stuecke/%s/%s_objekte.png' % (typ, lid), 'oben': 'stuecke/%s/%s_oben.png' % (typ, lid),
            'komplett': 'stuecke/%s/%s_komplett.png' % (typ, lid),
            'kollision': koll, 'punkte': punkte, 'objektliste': liste}


GRUPPEN = ['baeume', 'gross', 'dschungel', 'zufall_portal', 'zufall_brunnen', 'deko', 'k7gras', 'laterne',
           'tor', 'computer', 'netz', 'klein', 'k17']


def basis_name(name):
    """'varianten/k01-baum00_gras_m' -> 'k01/baum00' (Bodenfuss-Variante, gespiegelt), 'netz/tor-10' -> 'tor/10'."""
    if name.startswith('varianten/'):
        rest = name[len('varianten/'):]
        if rest.endswith('_m'):
            rest = rest[:-2]
        return rest.rsplit('_', 1)[0].replace('-', '/', 1)
    if name.startswith('netz/'):
        return name[len('netz/'):].replace('-', '/')
    return name


def gruppe(name):
    b = basis_name(name)
    if b.startswith('k01/baum'):
        return 'baeume'
    if b.startswith('k01/deko'):
        return 'deko'
    g = b.split('/')[0]
    return g if g in GRUPPEN else 'sonstige'


def objekt_tileset(namen, typ, breite=32):
    """Alle Objekt-Sprites in ein Tileset-Bild: jedes Sprite im kleinsten 16er-Kachelblock, waagerecht
    zentriert, Fuss buendig unten (Regel 1/1b); nach Gruppen geordnet, jede Gruppe beginnt eine neue Reihe."""
    bilder = {}
    for n in namen:                       # halbtransparente Kontaktschatten liegen schon im Boden -> nicht doppelt
        im = Image.open(os.path.join(SPRITES, typ, n + '.png')).convert('RGBA')
        a = np.array(im)
        a[a[..., 3] < 200] = 0
        bilder[n] = Image.fromarray(a)
    reihen = sorted(namen, key=lambda n: ((GRUPPEN + ['sonstige']).index(gruppe(n)), n))
    plaetze, cx, cy, zh, g_alt = {}, 0, 0, 0, None
    for n in reihen:
        im = bilder[n]
        wt, ht = -(-im.width // T), -(-im.height // T)
        if (g_alt is not None and gruppe(n) != g_alt) or cx + wt > breite:
            cx, cy, zh = 0, cy + zh, 0
        g_alt = gruppe(n)
        plaetze[n] = (cx, cy, wt, ht)
        cx += wt
        zh = max(zh, ht)
    atlas = Image.new('RGBA', (breite * T, (cy + zh) * T))
    info = {}
    for n, (cx, cy, wt, ht) in plaetze.items():
        im = bilder[n]
        x, y = cx * T + (wt * T - im.width) // 2, cy * T + ht * T - im.height
        atlas.alpha_composite(im, (x, y))
        info[n] = {'x': x, 'y': y, 'w': im.width, 'h': im.height, 'block': [cx, cy, wt, ht], 'gruppe': gruppe(n)}
    atlas.save(os.path.join(ZIEL, 'objekte_tileset_%s.png' % typ), optimize=True)
    # Vorschau 2x auf dunklem Grund mit 16er-Raster
    v = Image.new('RGBA', atlas.size, (30, 32, 37, 255))
    from PIL import ImageDraw
    d = ImageDraw.Draw(v)
    for x in range(0, atlas.width, T):
        d.line((x, 0, x, atlas.height), fill=(44, 47, 54, 255))
    for y in range(0, atlas.height, T):
        d.line((0, y, atlas.width, y), fill=(44, 47, 54, 255))
    v.alpha_composite(atlas)
    v.resize((v.width * 2, v.height * 2), Image.NEAREST).save(os.path.join(ZIEL, 'objekte_tileset_%s_vorschau.png' % typ))
    print('Objekt-Tileset:', len(info), 'Sprites,', atlas.size)
    return info


KANTEN = {'wald': {'Z': 'closed (forest)', 'W': 'forest path', 'O': 'open meadow'},
          'netz': {'Z': 'closed (void)', 'W': 'narrow platform bridge', 'O': 'wide platform'}}
NAME = {'wald': 'Forest (map 01 / area A02 style)', 'netz': 'The Network (map 16 style)'}


def main():
    args = sys.argv[1:]
    typ = 'wald'
    if '--typ' in args:
        i = args.index('--typ'); typ = args[i + 1]; del args[i:i + 2]
    assert typ in MODUL, 'Typ: ' + ', '.join(MODUL)
    for d in (os.path.join(ZIEL, 'stuecke', typ), os.path.join(SPRITES, typ)):
        if os.path.exists(d):
            shutil.rmtree(d)
    os.makedirs(os.path.join(ZIEL, 'stuecke', typ))
    lagen = zs.alle_lagen()
    # Fuellstueck (nur eine Lage): mehrere Varianten mit eigener Deko, sonst sehen alle Wald-/Leere-Felder gleich aus
    extra = []
    for l in lagen:
        for v in range(1, VARIANTEN.get(l['name'], 1)):
            extra.append(dict(l, lage='%sv%d' % (l['lage'], v)))
    lagen += extra
    if args:                                             # optional: nur bestimmte Stuecke (zum Testen)
        lagen = [l for l in lagen if l['name'] in args]
    print(len(lagen), 'Lagen werden gerendert (Typ %s)' % typ)
    with Pool(4) as p:
        eintraege = p.map(rendern, [(l, typ) for l in lagen], chunksize=1)
    anzahl = {}
    for e in eintraege:
        anzahl[e['name']] = anzahl.get(e['name'], 0) + 1
    for e in eintraege:
        e['lagenDesStuecks'] = anzahl[e['name']]
    tileset = objekt_tileset(sorted({o['s'] for e in eintraege for o in e['objektliste']}), typ)
    manifest = {'typ': typ, 'name': NAME[typ], 'kachel': T, 'feld': N, 'rand': PAD, 'kantentypen': KANTEN[typ],
                'tileset': {'bild': 'objekte_tileset_%s.png' % typ, 'sprites': tileset},
                'lagen': eintraege}
    json.dump(manifest, open(os.path.join(ZIEL, 'manifest_%s.json' % typ), 'w'), separators=(',', ':'))
    # dasselbe als Script: funktioniert auch ohne Webserver
    with open(os.path.join(ZIEL, 'manifest_%s.js' % typ), 'w') as fh:
        fh.write('/* generated by tools/zufall_export.py */\nwindow.ZUFALL_MANIFESTE = window.ZUFALL_MANIFESTE || {};\n'
                 'window.ZUFALL_MANIFESTE[%s] = ' % json.dumps(typ))
        json.dump(manifest, fh, separators=(',', ':'))
        fh.write(';\n')
    print('fertig:', len(eintraege), 'Lagen -> maps/zufall/js/manifest_%s.json' % typ)


if __name__ == '__main__':
    main()
