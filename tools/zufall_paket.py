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
    if name.startswith('varianten/'):
        rest, boden = name[len('varianten/'):].rsplit('_', 1)
        g, nr = rest.split('-', 1)
        return '%s_%s_%s' % (GRUPPE.get(g, g), nr, BODEN.get(boden, boden))
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
        for alt, neu in (('boden', 'ground'), ('objekte', 'objects'), ('oben', 'above'), ('komplett', 'preview')):
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
    if os.path.exists(ZIP):
        os.remove(ZIP)
    with zipfile.ZipFile(ZIP, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for wurzel, _, dateien in os.walk(ZIEL):
            for f in sorted(dateien):
                p = os.path.join(wurzel, f)
                z.write(p, os.path.join('random_dungeon_kit', os.path.relpath(p, ZIEL)))
    print('->', os.path.relpath(ZIP, ROOT), '%.1f MB' % (os.path.getsize(ZIP) / 1e6), len(pieces), 'pieces,',
          len(sprites), 'sprites')


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
