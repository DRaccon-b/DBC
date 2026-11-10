"""Export der Kartenstuecke fuer den JS-Generator (maps/zufall/js/).

  python3 tools/zufall_export.py            (alle Lagen, 4 Prozesse parallel, dauert einige Minuten)

Jede Lage jedes Stuecks wird einmal mit der Karte-01-Technik fertig gerendert. Damit Baeume und
Uebergaenge an den Raendern genauso aussehen wie in einer echten Karte, wird das Stueck mit einem Rand
von PAD Kacheln gebaut (Randkacheln nach aussen fortgesetzt - wegen der genormten Kanten ist das genau
das, was ein passender Nachbar dort haette). Objekte zaehlen nur, wenn ihr Fuss im Stueck steht.

Ausgabe je Lage:
  stuecke/<id>_boden.png    Boden mit Schatten, genau Stueckgroesse            (1. alle Stuecke)
  stuecke/<id>_objekte.png  deckende Objektpixel, um PAD Kacheln groesser     (2. von Nord nach Sued)
  stuecke/<id>_oben.png     obere Teile hoher Objekte (Baumkronen), wie objekte (3. ueber dem Spieler)
  Objekt- und Oben-Bilder sind groesser als das Stueck, damit ueberstehende Kronen erhalten bleiben.
  manifest.json            Kanten, Kollision (1 = gesperrt), Spawn-/Bosspunkt, Gewichte
"""
import json, os, shutil, sys
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


def rendern(l):
    import karte_bauen, objekte_setzen, karte01_raster, karte01_v11_begleiter, karte01_v11_aufraeumen
    lid = lage_id(l)
    raster = gepolstert(l['raster'])
    rows, cols = len(raster), len(raster[0])
    h, w = len(l['raster']), len(l['raster'][0])
    fest = [(n, x + PAD, y + PAD) for n, x, y in l.get('objekte', [])]
    symmetrie = [tuple(fest[i] for i in s) for s in l.get('symmetrie', [])]
    bau, obj = zk.bauordner('export_' + lid)
    json.dump({'tile_size': T, 'cols': cols, 'rows': rows, 'grid': raster},
              open(os.path.join(bau, 'terrain_grid.json'), 'w'))
    json.dump({'segmente': [], 'treppen': [], 'wasserfaelle': [], 'bruecken': [], 'stege': []},
              open(os.path.join(bau, 'hoehenplan.json'), 'w'))
    for m in (karte_bauen, objekte_setzen, karte01_raster, karte01_v11_begleiter, karte01_v11_aufraeumen):
        if hasattr(m, 'KARTE'):
            m.KARTE = bau
        m.OBJ = obj
    objekte_setzen.FEST = fest
    objekte_setzen.TEICH_AB_ZEILE = 0
    for n in ('zufall_portal/01', 'zufall_brunnen/00'):
        objekte_setzen.FUSS_ART[n] = 'stein'
    objekte_setzen.SCHATTEN = tuple(objekte_setzen.SCHATTEN) + ('zufall_portal/', 'zufall_brunnen/')
    objekte_setzen.DSCHUNGEL_SPERRE = (5, 7, 2)
    stumm = open(os.devnull, 'w')
    alt, sys.stdout = sys.stdout, stumm
    try:
        karte_bauen.bauen(objekte=False)
        objekte_setzen.main()
        karte01_raster.main()
        zk.symmetrisch(obj, symmetrie)
        karte01_v11_begleiter.main()
        # nur Objekte, deren Fuss im Stueck steht (die anderen gehoeren zum Nachbarn)
        pf = os.path.join(obj, 'platzierung.json')
        objs = [o for o in json.load(open(pf))
                if PAD <= o['kachel'][0] < PAD + w and PAD <= o['kachel'][1] < PAD + h]
        # Laternen nur an Startlager, Arena und Gabelungen - sonst haette jedes Stueck seine eigene
        if l['typ'] not in ('start', 'boss') and 'gabel' not in l['name'] and 'kreuz' not in l['name']:
            objs = [o for o in objs if o.get('basis') != 'laterne']
        json.dump(objs, open(pf, 'w'))
        karte_bauen.bauen()
        karte01_v11_aufraeumen.main()
        voll = karte_bauen.bauen().convert('RGBA')
        boden = karte_bauen.bauen(objekte=False, speichern=False).convert('RGBA')
    finally:
        sys.stdout = alt
    objs = json.load(open(os.path.join(obj, 'platzierung.json')))
    tm = json.load(open(os.path.join(bau, 'tilemap.json')))

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
    v, b = np.array(voll), np.array(boden)
    # boden: nur das Stueck, ohne Objekte (unter Sprites der reine Boden)
    bo = v.copy()
    bo[maske] = b[maske]
    boden_bild = Image.fromarray(bo).crop((PAD * T, PAD * T, (PAD + w) * T, (PAD + h) * T))
    # objekte: deckende Sprite-Pixel, auch ueber den Rand hinaus
    ob = v.copy()
    ob[~maske] = 0
    objekte_bild = Image.fromarray(ob)

    # --- Kollision im Stueck: Wald, Wasser, Sockelreihe stehender Objekte
    koll = [[0] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            if l['raster'][y][x] in 'FW' or tm['klassen'][y + PAD][x + PAD] == 'w':
                koll[y][x] = 1
    for o in objs:
        if o.get('ebene', 1) != 1 or o.get('anim') == 'wehen':
            continue
        bx, by, bw, bh = o['block']
        for x in range(bx, bx + bw):
            yy, xx = by + bh - 1 - PAD, x - PAD
            if 0 <= yy < h and 0 <= xx < w:
                koll[yy][xx] = 1

    def frei_nahe(x, y):
        best = min(((abs(xx - x) + abs(yy - y), xx, yy) for yy in range(h) for xx in range(w) if not koll[yy][xx]))
        return [best[1], best[2]]
    punkte = {}
    for n, x, y in l.get('objekte', []):
        if n.startswith('zufall_portal/'):
            punkte['spawn'] = frei_nahe(x, y + 2)
        if n.startswith('dschungel/'):
            punkte['boss'] = frei_nahe(x, y + 4)
    boden_bild.save(os.path.join(ZIEL, 'stuecke', lid + '_boden.png'), optimize=True)
    objekte_bild.save(os.path.join(ZIEL, 'stuecke', lid + '_objekte.png'), optimize=True)
    oben.save(os.path.join(ZIEL, 'stuecke', lid + '_oben.png'), optimize=True)
    # Komplettbild des Stuecks (Boden + Objekte + oben), genau Stueckgroesse
    ganz = Image.new('RGBA', voll.size)
    ganz.alpha_composite(Image.fromarray(bo)); ganz.alpha_composite(objekte_bild); ganz.alpha_composite(oben)
    ganz.crop((PAD * T, PAD * T, (PAD + w) * T, (PAD + h) * T)).save(
        os.path.join(ZIEL, 'stuecke', lid + '_komplett.png'), optimize=True)
    # Sprites fuer das Objekt-Tileset sammeln, Objektliste relativ zur linken oberen Stueckecke (Pixel)
    liste = []
    for o in sorted(objs, key=lambda o: (o.get('ebene', 1), o['y'] + o.get('fuss', 0))):
        name = o['datei'][:-4]
        ziel = os.path.join(SPRITES, o['datei'])
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
    shutil.rmtree(bau)
    print('  ', lid, len(objs), 'Objekte', flush=True)
    return {'id': lid, 'name': l['name'], 'lage': l['lage'], 'typ': l['typ'], 'gewicht': l['gewicht'],
            'felder': list(l['felder']),
            'kanten': {'%d,%d,%s' % k: t for k, t in l['kanten'].items()},
            'boden': 'stuecke/%s_boden.png' % lid, 'objekte': 'stuecke/%s_objekte.png' % lid, 'oben': 'stuecke/%s_oben.png' % lid,
            'komplett': 'stuecke/%s_komplett.png' % lid,
            'kollision': [''.join(map(str, z)) for z in koll], 'punkte': punkte, 'objektliste': liste}


GRUPPEN = ['baeume', 'gross', 'dschungel', 'zufall_portal', 'zufall_brunnen', 'deko', 'k7gras', 'laterne']


def gruppe(name):
    if name.startswith('varianten/'):
        name = name[len('varianten/'):].rsplit('_', 1)[0].replace('-', '/', 1)
    g = name.split('/')[0]
    return g if g in GRUPPEN else 'sonstige'


def objekt_tileset(namen, breite=32):
    """Alle Objekt-Sprites in ein Tileset-Bild: jedes Sprite im kleinsten 16er-Kachelblock, waagerecht
    zentriert, Fuss buendig unten (Regel 1/1b); nach Gruppen geordnet, jede Gruppe beginnt eine neue Reihe."""
    bilder = {n: Image.open(os.path.join(SPRITES, n + '.png')).convert('RGBA') for n in namen}
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
    atlas.save(os.path.join(ZIEL, 'objekte_tileset.png'), optimize=True)
    # Vorschau 2x auf dunklem Grund mit 16er-Raster
    v = Image.new('RGBA', atlas.size, (30, 32, 37, 255))
    from PIL import ImageDraw
    d = ImageDraw.Draw(v)
    for x in range(0, atlas.width, T):
        d.line((x, 0, x, atlas.height), fill=(44, 47, 54, 255))
    for y in range(0, atlas.height, T):
        d.line((0, y, atlas.width, y), fill=(44, 47, 54, 255))
    v.alpha_composite(atlas)
    v.resize((v.width * 2, v.height * 2), Image.NEAREST).save(os.path.join(ZIEL, 'objekte_tileset_vorschau.png'))
    print('Objekt-Tileset:', len(info), 'Sprites,', atlas.size)
    return info


def main():
    for d in (os.path.join(ZIEL, 'stuecke'), SPRITES):
        if os.path.exists(d):
            shutil.rmtree(d)
    os.makedirs(os.path.join(ZIEL, 'stuecke'))
    lagen = zs.alle_lagen()
    nur = sys.argv[1:]                                   # optional: nur bestimmte Stuecke (zum Testen)
    if nur:
        lagen = [l for l in lagen if l['name'] in nur]
    print(len(lagen), 'Lagen werden gerendert')
    with Pool(4) as p:
        eintraege = p.map(rendern, lagen, chunksize=1)
    anzahl = {}
    for e in eintraege:
        anzahl[e['name']] = anzahl.get(e['name'], 0) + 1
    for e in eintraege:
        e['lagenDesStuecks'] = anzahl[e['name']]
    tileset = objekt_tileset(sorted({o['s'] for e in eintraege for o in e['objektliste']}))
    manifest = {'kachel': T, 'feld': N, 'rand': PAD,
                'kantentypen': {'Z': 'closed (forest)', 'W': 'forest path', 'O': 'open meadow'},
                'tileset': {'bild': 'objekte_tileset.png', 'sprites': tileset},
                'lagen': eintraege}
    json.dump(manifest, open(os.path.join(ZIEL, 'manifest.json'), 'w'), separators=(',', ':'))
    # dasselbe als Script: funktioniert auch ohne Webserver (demo.html per Doppelklick)
    with open(os.path.join(ZIEL, 'manifest.js'), 'w') as fh:
        fh.write('/* generated by tools/zufall_export.py */\nwindow.ZUFALL_MANIFEST = ')
        json.dump(manifest, fh, separators=(',', ':'))
        fh.write(';\n')
    print('fertig:', len(eintraege), 'Lagen -> maps/zufall/js/manifest.json')


if __name__ == '__main__':
    main()
