"""Baut das Terrain von Karte 01 aus PixelLab-Wang-Tilesets.

  python3 tools/karte_bauen.py

Eingaben:  maps/karte01/terrain_grid.json   (Gelaendetyp je 16x16-Kachel)
           maps/karte01/hoehenplan.json     (Klippenverlauf, Treppen)
           assets/tilesets/pixellab/weg_gras.json      (Weg <-> Gras, 16 Tiles)
           assets/tilesets/pixellab/klippe_stein.json  (Gras <-> Gras mit Steinwand, 25 Tiles)
Ausgaben:  maps/karte01/terrain_basis.png    (Gras, Wege, Klippen ohne Treppen)
           maps/karte01/terrain.png          (dazu Treppen aus assets/objekte/karte01)
           maps/karte01/terrain_vorschau.png (dazu Platzhalter fuer Wasser/Strand/Wald)
           maps/karte01/tilemap.json         (Tile-Zuordnung je Kachel)

Beide Tilesets arbeiten mit Wang-Ecken: jede Kachel liest ihre 4 Eck-Vertices.
Das Gras ist in beiden Sets identisch (Klippen-Set wurde mit dem Gras-Tile des
Weg-Sets als Referenz erzeugt), deshalb lassen sie sich Kachel fuer Kachel mischen.
"""
import base64, io, json, os
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte01')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte01')
TS_DIR = os.path.join(ROOT, 'assets', 'tilesets', 'pixellab')
LOWER, UPPER, TRANS, ANY = 0, 1, 2, 255

WEG = set('RPBp')            # dunkler/heller Weg, Bruecke, Teichsand -> Weg
MIN_WEG = 8                  # kleinere zusammenhaengende Wegflecken werden Gras
PLATZHALTER = {              # noch nicht umgesetzt: flache Farbe in der Vorschau
    'W': (40, 110, 200, 255), 'S': (250, 238, 205, 255), 's': (205, 180, 125, 255),
    'h': (60, 190, 170, 255), 'D': (25, 35, 100, 255),
}
WALD = (20, 70, 30, 110)     # Wald nur als halbtransparente Markierung


def lade_set(name):
    d = json.load(open(os.path.join(TS_DIR, name + '.json')))
    tiles = []
    for t in d['tileset']['tiles']:
        p = t['pattern_4x4']
        tiles.append({
            'id': t['id'], 'name': t['name'],
            'pat': [p['row_%d' % i] for i in range(4)],
            'img': Image.open(io.BytesIO(base64.b64decode(t['image']['base64']))).convert('RGBA'),
        })
    return d['id'], tiles


def waehle(tiles, pat):
    """Tile, dessen pattern_4x4 am besten passt (255 = egal). Rueckgabe (tile, fehler)."""
    best = None
    for t in tiles:
        err, spec = 0, 0
        for r in range(4):
            for c in range(4):
                want, have = t['pat'][r][c], pat[r][c]
                if want == ANY:
                    continue
                spec += 1
                if have == ANY or want != have:
                    err += 1
        # Kernecken (Zeile 1/2) wiegen schwerer als Ober-/Unterkante
        core = sum(t['pat'][r][c] != pat[r][c] for r in (1, 2) for c in (1, 2))
        score = (core, err, -spec)
        if best is None or score < best[0]:
            best = (score, t)
    return best[1], best[0][0]


def main():
    g = json.load(open(os.path.join(KARTE, 'terrain_grid.json')))
    plan = json.load(open(os.path.join(KARTE, 'hoehenplan.json')))
    grid, cols, rows, T = g['grid'], g['cols'], g['rows'], g['tile_size']
    weg_id, weg_tiles = lade_set('weg_gras')
    kl_id, kl_tiles = lade_set('klippe_stein')

    # Kleine isolierte Wegstuecke (Baumstaemme im Original) entfernen
    grid = [list(r) for r in grid]
    gesehen = set()
    for y0 in range(rows):
        for x0 in range(cols):
            if grid[y0][x0] in WEG and (x0, y0) not in gesehen:
                comp, stack = [], [(x0, y0)]
                gesehen.add((x0, y0))
                while stack:
                    x, y = stack.pop(); comp.append((x, y))
                    for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                        if 0 <= nx < cols and 0 <= ny < rows and (nx, ny) not in gesehen and grid[ny][nx] in WEG:
                            gesehen.add((nx, ny)); stack.append((nx, ny))
                if len(comp) < MIN_WEG:
                    for x, y in comp:
                        grid[y][x] = 'G'
    grid = [''.join(r) for r in grid]

    cell = lambda x, y: grid[min(max(y, 0), rows - 1)][min(max(x, 0), cols - 1)]

    # --- Vertex-Raster Weg/Gras: Weg, wenn >=2 der 4 angrenzenden Kacheln Weg sind
    vweg = [[LOWER if sum(cell(vx + dx, vy + dy) in WEG for dx in (-1, 0) for dy in (-1, 0)) >= 2 else UPPER
             for vx in range(cols + 1)] for vy in range(rows + 1)]

    # --- Vertex-Raster Hoehe aus dem Hoehenplan
    tcol = [None] * (cols + 1)
    for s in plan['segmente']:
        for vx in range(s['von'], min(s['bis'], cols) + 1):
            tcol[vx] = s['t']
    # Treppen: Weg-Vertices durch die Wand fuehren, damit oben und unten anschliessen
    treppen_zellen = set()
    for tr in plan.get('treppen', []):
        t = tcol[tr['x']]
        for vx in range(tr['x'], tr['x'] + tr['breite'] + 1):
            for vy in range(t - 3, t + 3):
                vweg[vy][vx] = LOWER
        for x in range(tr['x'], tr['x'] + tr['breite']):
            treppen_zellen |= {(x, t - 1), (x, t)}

    vh = [[UPPER if vy < tcol[vx] else TRANS if vy == tcol[vx] else LOWER
           for vx in range(cols + 1)] for vy in range(rows + 1)]

    def muster(v, x, y):
        out = []
        for r, vy in enumerate((y - 1, y, y + 1, y + 2)):
            row = [ANY]
            for vx in (x, x + 1):
                row.append(v[vy][vx] if 0 <= vy <= rows else ANY)
            out.append(row + [ANY])
        return out

    img = Image.new('RGBA', (cols * T, rows * T))
    karte = {'tile_size': T, 'cols': cols, 'rows': rows,
             'tilesets': {'weg_gras': weg_id, 'klippe_stein': kl_id}, 'zellen': []}
    warn = 0
    for y in range(rows):
        zeile = []
        for x in range(cols):
            ph = muster(vh, x, y)
            core = {ph[r][c] for r in (1, 2) for c in (1, 2)}
            if (len(core) == 1 and TRANS not in core) or (x, y) in treppen_zellen:
                t, e = waehle(weg_tiles, muster(vweg, x, y))
                zeile.append(['weg_gras', t['name']])
            else:
                t, e = waehle(kl_tiles, ph)
                zeile.append(['klippe_stein', t['name']])
            if e:
                warn += 1
                print("  ungenau:", x, y, t["name"])
            img.paste(t['img'], (x * T, y * T))
        karte['zellen'].append(zeile)
    karte['treppen'] = plan.get('treppen', [])
    karte['wasserfaelle'] = plan.get('wasserfaelle', [])
    karte['hoehe_vertices'] = [''.join('LUT'[v] for v in r) for r in vh]

    img.save(os.path.join(KARTE, 'terrain_basis.png'))   # ohne Objekte, Grundlage fuers Inpainting
    # Treppen-Sprites (tools/pixellab_treppen.py) einsetzen
    idx_f = os.path.join(OBJ, 'treppen.json')
    if os.path.exists(idx_f):
        for tr in json.load(open(idx_f)).values():
            img.alpha_composite(Image.open(os.path.join(OBJ, tr['datei'])).convert('RGBA'), (tr['px'], tr['py']))
    img.save(os.path.join(KARTE, 'terrain.png'))
    json.dump(karte, open(os.path.join(KARTE, 'tilemap.json'), 'w'))

    # Vorschau mit Platzhaltern fuer noch fehlende Gelaendetypen
    vor = img.copy()
    over = Image.new('RGBA', vor.size)
    for y in range(rows):
        for x in range(cols):
            ch = grid[y][x]
            farbe = PLATZHALTER.get(ch) or (WALD if ch == 'F' else None)
            if farbe:
                over.paste(farbe, (x * T, y * T, x * T + T, y * T + T))
    vor.alpha_composite(over)
    vor.save(os.path.join(KARTE, 'terrain_vorschau.png'))
    print('Karte %dx%d Kacheln gebaut, %d Kacheln ohne exakt passendes Tile' % (cols, rows, warn))


if __name__ == '__main__':
    main()
