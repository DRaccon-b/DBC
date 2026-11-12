"""Baut das englische Paket "random_dungeon_kit" (ZIP) aus dem Export in maps/zufall/js/.

  python3 tools/zufall_export.py && python3 tools/zufall_paket.py

Ausgabe: maps/zufall/random_dungeon_kit.zip  (Ordner maps/zufall/_bau/random_dungeon_kit/ als Zwischenstand)
Inhalt: alle fertigen Kartenstuecke einzeln (Boden / Objekte / oben / komplett), alle Objekte in einem
Tileset-Bild, das JS-Script (laeuft ohne Webserver und ohne Repository), Demo und englische README.
Im Paket sind Manifest, Datei-, Stueck- und Sprite-Namen englisch.
"""
import json, os, shutil, sys, zipfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw, ImageFont
import zufall_stuecke as zs

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
QUELLE = os.path.join(ROOT, 'maps', 'zufall', 'js')
KIT = os.path.join(ROOT, 'maps', 'zufall', 'kit')            # JS, Demo, README des Pakets (englisch)
ZIEL = os.path.join(ROOT, 'maps', 'zufall', '_bau', 'random_dungeon_kit')
ZIP = os.path.join(ROOT, 'maps', 'zufall', 'random_dungeon_kit.zip')
FONT = '/usr/share/fonts/opentype/inter/'

STUECK = {'weg_bogen': 'path_bend', 'wiese_teich': 'meadow_pond', 'weg_zu_wiese': 'path_to_meadow',
          'teich_am_weg': 'pond_by_path', 'weg_ecke': 'path_corner', 'wiese_ecke': 'meadow_corner',
          'weg_gabel': 'path_fork', 'wiese_kreuz': 'meadow_cross', 'weg_kreuz': 'path_cross',
          'ecke_weg_wiese': 'corner_path_meadow', 'wiese_gabel': 'meadow_fork', 'wiese_rosabaum': 'meadow_pink_tree',
          'sackgasse_findling': 'deadend_boulder', 'lichtung_runenbaum': 'glade_rune_tree',
          'sackgasse_teich': 'deadend_pond', 'sackgasse_wiese': 'deadend_meadow', 'sackgasse_brunnen': 'deadend_well',
          'start_lager': 'start_camp', 'boss_dschungelbaum': 'boss_jungle_tree', 'wald': 'forest'}
TYP = {'normal': 'normal', 'start': 'start', 'boss': 'boss', 'wald': 'forest'}
KANTE = {'Z': 'C', 'W': 'P', 'O': 'O'}                      # closed / forest path / open meadow
SEITE = {'N': 'N', 'O': 'E', 'S': 'S', 'W': 'W'}
GRUPPE = {'baeume': 'trees', 'gross': 'large', 'dschungel': 'jungle', 'zufall_portal': 'portal',
          'zufall_brunnen': 'well', 'deko': 'decor', 'k7gras': 'grass', 'laterne': 'lantern', 'sonstige': 'other'}
BODEN = {'gras': 'grass', 'sand': 'sand'}
GELAENDE = {'F': 'F', 'G': 'G', 'P': 'P', 'W': 'W'}


def lage_en(lage):                       # '0' -> 'r0', 's90' -> 'm90'
    return ('m' + lage[1:]) if lage.startswith('s') else 'r' + lage


def sprite_en(name):
    """'varianten/k01-baum00_gras_m' -> 'trees_00_grass_m', 'varianten/zufall_portal-01_gras' -> 'portal_01_grass'."""
    gespiegelt = ''
    if name.startswith('varianten/'):
        rest = name[len('varianten/'):]
        if rest.endswith('_m'):
            rest, gespiegelt = rest[:-2], '_m'
        rest, boden = rest.rsplit('_', 1)
        g, nr = rest.split('-', 1)
        if g == 'k01':
            g, nr = ('baeume', nr[4:]) if nr.startswith('baum') else ('deko', nr[4:])
        return '%s_%s_%s%s' % (GRUPPE.get(g, g), nr, BODEN.get(boden, boden), gespiegelt)
    if '/' in name:
        g, nr = name.split('/', 1)
        return '%s_%s' % (GRUPPE.get(g, g), nr)
    return GRUPPE.get(name, name)


def kanten_en(k):
    out = {}
    for schl, t in k.items():
        fx, fy, s = schl.split(',')
        out['%s,%s,%s' % (fx, fy, SEITE[s])] = KANTE[t]
    return out


def main():
    if os.path.exists(ZIEL):
        shutil.rmtree(ZIEL)
    for d in ('pieces', 'chunks', 'preview'):
        os.makedirs(os.path.join(ZIEL, d))
    m = json.load(open(os.path.join(QUELLE, 'manifest.json')))
    sprites = {sprite_en(n): dict(v, group=GRUPPE.get(v.pop('gruppe'), 'other')) for n, v in m['tileset']['sprites'].items()}
    for v in sprites.values():
        v['block'] = v['block']
    shutil.copy(os.path.join(QUELLE, 'objekte_tileset.png'), os.path.join(ZIEL, 'objects_tileset.png'))
    shutil.copy(os.path.join(QUELLE, 'objekte_tileset_vorschau.png'), os.path.join(ZIEL, 'preview', 'objects_tileset_2x.png'))
    pieces = []
    for l in m['lagen']:
        pid = '%s_%s' % (STUECK[l['name']], lage_en(l['lage']))
        dateien = {}
        for alt, neu in (('boden', 'ground'), ('schatten', 'shadows'), ('objekte', 'objects'), ('oben', 'above'),
                         ('komplett', 'preview')):
            ziel = 'pieces/%s_%s.png' % (pid, neu)
            shutil.copy(os.path.join(QUELLE, l[alt]), os.path.join(ZIEL, ziel))
            dateien[neu] = ziel
        objs = []
        for o in l['objektliste']:
            e = {'sprite': sprite_en(o['s']), 'x': o['x'], 'y': o['y'], 'block': o['block'], 'layer': o['ebene']}
            if 'anim' in o:
                e['anim'] = {'wehen': 'sway', 'wippen': 'bob', 'laterne': 'lantern'}.get(o['anim'], o['anim'])
            if o.get('spiegeln'):
                e['flip'] = True
            objs.append(e)
        punkte = l['punkte']
        pieces.append({'id': pid, 'chunk': STUECK[l['name']], 'orientation': lage_en(l['lage']),
                       'type': TYP[l['typ']], 'weight': l['gewicht'], 'orientationsOfChunk': l['lagenDesStuecks'],
                       'cells': l['felder'], 'edges': kanten_en(l['kanten']), **dateien,
                       'collision': l['kollision'], 'points': punkte, 'objectList': objs})
    manifest = {'tileSize': m['kachel'], 'chunkSize': m['feld'], 'padding': m['rand'],
                'edgeTypes': {'C': 'closed (forest)', 'P': 'forest path', 'O': 'open meadow'},
                'tileset': {'image': 'objects_tileset.png', 'sprites': sprites}, 'pieces': pieces}
    tiled(manifest)                                      # Tiled-Tilesets + eine .tmx je Stueck, ergaenzt das Manifest
    json.dump(manifest, open(os.path.join(ZIEL, 'pieces.json'), 'w'), separators=(',', ':'))
    with open(os.path.join(ZIEL, 'pieces.js'), 'w') as fh:
        fh.write('/* Random Dungeon Kit - piece manifest (same content as pieces.json). Loaded with a plain\n'
                 '   <script> tag so the kit also works from the file system without a web server. */\n'
                 'window.RANDOM_DUNGEON_PIECES = ')
        json.dump(manifest, fh, separators=(',', ':'))
        fh.write(';\n')
    json.dump({'image': 'objects_tileset.png', 'tileSize': m['kachel'], 'sprites': sprites},
              open(os.path.join(ZIEL, 'objects_tileset.json'), 'w'), indent=1)

    # Stueck-Definitionen (Raster)
    defs = []
    for st in zs.STUECKE:
        defs.append({'chunk': STUECK[st['name']], 'type': TYP[st['typ']], 'weight': st['gewicht'],
                     'cells': [len(st['raster'][0]) // zs.N, len(st['raster']) // zs.N],
                     'rotation': '180 only' if st.get('drehen') == 180 else 'all',
                     'edges': kanten_en({'%d,%d,%s' % k: t for k, t in zs.kanten(st['raster']).items()}),
                     'fixedObjects': [{'sprite': sprite_en(n), 'tileX': x, 'tileY': y} for n, x, y in st.get('objekte', [])],
                     'grid': st['raster']})
    json.dump({'chunkSize': zs.N, 'legend': {'F': 'forest', 'G': 'meadow', 'P': 'sand path', 'W': 'pond'},
               'edgePatterns': {KANTE[t]: p for t, p in zs.KANTE.items()}, 'chunks': defs},
              open(os.path.join(ZIEL, 'chunks', 'chunks.json'), 'w'), indent=1)
    uebersicht(os.path.join(ZIEL, 'chunks', 'chunks_overview.png'))
    alle_lagen(manifest, os.path.join(ZIEL, 'preview', 'all_pieces.png'))
    for f, n in (('system_explained.png', 'system_explained.png'),):
        shutil.copy(os.path.join(ROOT, 'maps', 'zufall', f), os.path.join(ZIEL, 'preview', n))
    for f in ('random_dungeon.js', 'demo.html', 'README.md'):
        shutil.copy(os.path.join(KIT, f), os.path.join(ZIEL, f))
    for f in os.listdir(KIT):
        if f.startswith('demo_') and f.endswith('.png'):
            shutil.copy(os.path.join(KIT, f), os.path.join(ZIEL, 'preview', f))
    beispiele()                                          # ganze Zufalls-Dungeons als .tmj (ueber das JS in Node)
    if os.path.exists(ZIP):
        os.remove(ZIP)
    with zipfile.ZipFile(ZIP, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for wurzel, _, dateien in os.walk(ZIEL):
            for f in sorted(dateien):
                p = os.path.join(wurzel, f)
                z.write(p, os.path.join('random_dungeon_kit', os.path.relpath(p, ZIEL)))
    print('->', os.path.relpath(ZIP, ROOT), '%.1f MB' % (os.path.getsize(ZIP) / 1e6), len(pieces), 'pieces,',
          len(sprites), 'sprites')


# ---------------------------------------------------------------- Tiled
TILED_VERSION, TILED_FORMAT = '1.10.2', '1.10'


def xml(s):
    return str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')


def tiled(manifest):
    """Schreibt tiled/: ground_tiles.png/.tsx (Bodenkacheln aller Stuecke, doppelte zusammengefasst),
    objects.tsx (Bildsammlung, je Sprite ein PNG in tiled/sprites/), collision.tsx und pieces/<id>.tmx.
    Ergaenzt das Manifest um manifest['tiled'] und je Stueck 'groundTiles' (Tile-IDs ab 0)."""
    T = manifest['tileSize']
    td = os.path.join(ZIEL, 'tiled')
    for d in ('pieces', 'sprites'):
        os.makedirs(os.path.join(td, d))
    # Bodenkacheln
    kacheln, index = [], {}
    for p in manifest['pieces']:
        im = Image.open(os.path.join(ZIEL, p['ground'])).convert('RGBA')
        ids = []
        for ty in range(im.height // T):
            for tx in range(im.width // T):
                k = im.crop((tx * T, ty * T, (tx + 1) * T, (ty + 1) * T))
                b = k.tobytes()
                if b not in index:
                    index[b] = len(kacheln)
                    kacheln.append(k)
                ids.append(index[b])
        p['groundTiles'] = ids
    spalten = 64
    zeilen = -(-len(kacheln) // spalten)
    atlas = Image.new('RGBA', (spalten * T, zeilen * T))
    for i, k in enumerate(kacheln):
        atlas.paste(k, ((i % spalten) * T, (i // spalten) * T))
    atlas.save(os.path.join(td, 'ground_tiles.png'), optimize=True)
    with open(os.path.join(td, 'ground_tiles.tsx'), 'w') as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<tileset version="%s" tiledversion="%s" name="ground" '
                'tilewidth="%d" tileheight="%d" tilecount="%d" columns="%d">\n <image source="ground_tiles.png" '
                'width="%d" height="%d"/>\n</tileset>\n' % (TILED_FORMAT, TILED_VERSION, T, T, len(kacheln), spalten,
                                                          atlas.width, atlas.height))
    # Objekte: Bildsammlung
    tsatlas = Image.open(os.path.join(ZIEL, 'objects_tileset.png')).convert('RGBA')
    namen = sorted(manifest['tileset']['sprites'])
    objtiles = []
    for i, n in enumerate(namen):
        s = manifest['tileset']['sprites'][n]
        tsatlas.crop((s['x'], s['y'], s['x'] + s['w'], s['y'] + s['h'])).save(os.path.join(td, 'sprites', n + '.png'))
        objtiles.append({'id': i, 'name': n, 'image': 'sprites/%s.png' % n, 'w': s['w'], 'h': s['h'], 'group': s['group']})
    mw, mh = max(t['w'] for t in objtiles), max(t['h'] for t in objtiles)
    with open(os.path.join(td, 'objects.tsx'), 'w') as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<tileset version="%s" tiledversion="%s" name="objects" '
                'tilewidth="%d" tileheight="%d" tilecount="%d" columns="0">\n <grid orientation="orthogonal" width="1" height="1"/>\n'
                % (TILED_FORMAT, TILED_VERSION, mw, mh, len(objtiles)))
        for t in objtiles:
            f.write(' <tile id="%d">\n  <properties>\n   <property name="sprite" value="%s"/>\n   <property name="group" value="%s"/>\n'
                    '  </properties>\n  <image source="%s" width="%d" height="%d"/>\n </tile>\n'
                    % (t['id'], xml(t['name']), xml(t['group']), t['image'], t['w'], t['h']))
        f.write('</tileset>\n')
    # Kollision (Format wie tools/kollision.py): Kachel 0 = gesperrt (2), Kachel 1 = begehbar + verdeckt (3)
    kim = Image.new('RGBA', (2 * T, T), (220, 60, 60, 150))
    kim.paste(Image.new('RGBA', (T, T), (60, 200, 255, 120)), (T, 0))
    kim.save(os.path.join(td, 'collision.png'))
    with open(os.path.join(td, 'collision.tsx'), 'w') as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<tileset version="%s" tiledversion="%s" name="collision" '
                'tilewidth="%d" tileheight="%d" tilecount="2" columns="2">\n <image source="collision.png" width="%d" height="%d"/>\n'
                ' <tile id="0">\n  <properties>\n   <property name="blocked" type="bool" value="true"/>\n  </properties>\n </tile>\n'
                ' <tile id="1">\n  <properties>\n   <property name="covered" type="bool" value="true"/>\n  </properties>\n </tile>\n'
                '</tileset>\n' % (TILED_FORMAT, TILED_VERSION, T, T, 2 * T, T))
    g_obj = 1 + len(kacheln)
    g_koll = g_obj + len(objtiles)
    sprite_id = {t['name']: t['id'] for t in objtiles}
    manifest['tiled'] = {
        'ground': {'name': 'ground', 'source': 'tiled/ground_tiles.tsx', 'image': 'tiled/ground_tiles.png',
                   'columns': spalten, 'tilecount': len(kacheln), 'imagewidth': atlas.width, 'imageheight': atlas.height},
        'objects': {'name': 'objects', 'source': 'tiled/objects.tsx', 'tilewidth': mw, 'tileheight': mh,
                    'tiles': [{'id': t['id'], 'sprite': t['name'], 'image': 'tiled/' + t['image'], 'w': t['w'], 'h': t['h']}
                              for t in objtiles]},
        'collision': {'name': 'collision', 'source': 'tiled/collision.tsx', 'image': 'tiled/collision.png'}}
    # eine .tmx je Stueck
    P = manifest['padding']
    for p in manifest['pieces']:
        W, H = p['cells'][0] * manifest['chunkSize'], p['cells'][1] * manifest['chunkSize']
        boden = ','.join(str(i + 1) for i in p['groundTiles'])
        koll = ','.join(str(g_koll) if c == '2' else str(g_koll + 1) if c == '3' else '0' for z in p['collision'] for c in z)
        oid = 1
        objs = []
        for o in p['objectList']:
            s = manifest['tileset']['sprites'][o['sprite']]
            gid = g_obj + sprite_id[o['sprite']] + (0x80000000 if o.get('flip') else 0)
            props = '<property name="layer" type="int" value="%d"/>' % o['layer']
            if o.get('anim'):
                props += '<property name="anim" value="%s"/>' % o['anim']
            objs.append('  <object id="%d" gid="%d" x="%d" y="%d" width="%d" height="%d"><properties>%s</properties></object>'
                        % (oid, gid, o['x'], o['y'] + s['h'], s['w'], s['h'], props))
            oid += 1
        punkte = []
        for name, (px, py) in p['points'].items():
            punkte.append('  <object id="%d" name="%s" x="%d" y="%d"><point/></object>' % (oid, name, px * T + T // 2, py * T + T // 2))
            oid += 1
        eig = ''.join('  <property name="%s" value="%s"/>\n' % (k, xml(v)) for k, v in (
            ('chunk', p['chunk']), ('pieceOrientation', p['orientation']), ('pieceType', p['type']),
            ('edges', json.dumps(p['edges'], separators=(',', ':')))))
        with open(os.path.join(td, 'pieces', p['id'] + '.tmx'), 'w') as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n'
                    '<map version="%s" tiledversion="%s" orientation="orthogonal" renderorder="right-down" width="%d" '
                    'height="%d" tilewidth="%d" tileheight="%d" infinite="0" nextlayerid="6" nextobjectid="%d">\n'
                    ' <properties>\n%s </properties>\n'
                    ' <tileset firstgid="1" source="../ground_tiles.tsx"/>\n'
                    ' <tileset firstgid="%d" source="../objects.tsx"/>\n'
                    ' <tileset firstgid="%d" source="../collision.tsx"/>\n'
                    ' <layer id="1" name="ground" width="%d" height="%d">\n  <data encoding="csv">\n%s\n</data>\n </layer>\n'
                    ' <imagelayer id="5" name="shadows" offsetx="%d" offsety="%d">\n  <image source="../../%s" width="%d" height="%d"/>\n </imagelayer>\n'
                    ' <objectgroup id="2" name="objects">\n%s\n </objectgroup>\n'
                    ' <layer id="3" name="collision" width="%d" height="%d" visible="0" opacity="0.6">\n  <data encoding="csv">\n%s\n</data>\n </layer>\n'
                    ' <objectgroup id="4" name="points">\n%s\n </objectgroup>\n'
                    '</map>\n' % (TILED_FORMAT, TILED_VERSION, W, H, T, T, oid, eig, g_obj, g_koll,
                                   W, H, boden, -P * T, -P * T, p['shadows'], (W + 2 * P) * T, (H + 2 * P) * T,
                                   '\n'.join(objs), W, H, koll, '\n'.join(punkte)))
    print('Tiled:', len(kacheln), 'Bodenkacheln,', len(objtiles), 'Objekt-Sprites,', len(manifest['pieces']), '.tmx')


def beispiele():
    """Zwei ganze Dungeons als .tmj, erzeugt mit RandomDungeon.toTiled() in Node (prueft das JS mit)."""
    import subprocess
    ex = os.path.join(ZIEL, 'tiled', 'examples')
    os.makedirs(ex, exist_ok=True)
    skript = ("const RD=require(process.argv[1]+'/random_dungeon.js');const m=require(process.argv[1]+'/pieces.json');"
              "const fs=require('fs');for(const s of [7,42]){const d=RD.generate(m,s,{width:6,height:5});"
              "fs.writeFileSync(process.argv[1]+'/tiled/examples/dungeon_seed_'+s+'.tmj',"
              "JSON.stringify(RD.toTiled(m,d,{imageBase:'../../'}),null,1));}")
    subprocess.run(['node', '-e', skript, ZIEL], check=True)


def uebersicht(pfad):
    px, rand = 6, 24
    f = ImageFont.truetype(FONT + 'Inter-Medium.otf', 12)
    plaetze, x, y, hmax = [], rand, rand, 0
    for s in zs.STUECKE:
        w, h = len(s['raster'][0]) * px, len(s['raster']) * px
        if x + w > 1100:
            x, y, hmax = rand, y + hmax + rand + 16, 0
        plaetze.append((s, x, y)); x += w + rand + 40; hmax = max(hmax, h)
    im = Image.new('RGB', (1100 + rand, y + hmax + rand + 16), (18, 19, 22))
    d = ImageDraw.Draw(im)
    for s, x, y in plaetze:
        im.paste(zs.bild(s['raster'], px), (x, y + 16))
        d.text((x, y), STUECK[s['name']], font=f, fill=(230, 230, 230))
        for n, ox, oy in s.get('objekte', []):
            d.rectangle((x + ox * px, y + 16 + oy * px, x + ox * px + px - 1, y + 16 + oy * px + px - 1), fill=(232, 92, 92))
    im.save(pfad)


def alle_lagen(m, pfad):
    T, N = m['tileSize'], m['chunkSize']
    font = ImageFont.truetype(FONT + 'Inter-Medium.otf', 11)
    zelle, sp, gap = 128, 8, 34
    klein = [p for p in m['pieces'] if p['cells'] == [1, 1]]
    gross = [p for p in m['pieces'] if p['cells'] != [1, 1]]
    zeilen = (len(klein) + sp - 1) // sp
    W = sp * (zelle + gap) + gap
    out = Image.new('RGB', (W, 50 + zeilen * (zelle + 24) + 10 + 256 + 40), (18, 19, 22))
    d = ImageDraw.Draw(out)
    d.text((gap, 14), 'Random Dungeon Kit – all %d pieces (half size)' % len(m['pieces']),
           font=ImageFont.truetype(FONT + 'Inter-Bold.otf', 20), fill=(236, 238, 242))
    for i, p in enumerate(klein):
        x, y = gap + (i % sp) * (zelle + gap), 50 + (i // sp) * (zelle + 24)
        out.paste(Image.open(os.path.join(ZIEL, p['preview'])).resize((zelle, zelle), Image.LANCZOS).convert('RGB'), (x, y))
        d.text((x + zelle // 2, y + zelle + 4), p['id'], font=font, fill=(150, 156, 166), anchor='mt')
    y = 50 + zeilen * (zelle + 24) + 10
    for i, p in enumerate(gross):
        x = gap + i * (256 + 64)
        out.paste(Image.open(os.path.join(ZIEL, p['preview'])).resize((256, 256), Image.LANCZOS).convert('RGB'), (x, y))
        d.text((x + 128, y + 260), p['id'], font=font, fill=(150, 156, 166), anchor='mt')
    out.save(pfad, optimize=True)


if __name__ == '__main__':
    main()
