"""PixelLab-Tilesets erzeugen bzw. herunterladen.

  python3 tools/pixellab_tileset.py holen <tileset_id> <name>
  python3 tools/pixellab_tileset.py erzeugen <name> <request.json>

Speichert assets/tilesets/pixellab/<name>.json (Tiles + Metadaten) und
<name>.png (Uebersicht). Braucht PIXELLAB_API_KEY.
"""
import base64, io, json, os, sys, time, urllib.error, urllib.request
from PIL import Image

API = 'https://api.pixellab.ai/v2'
OUT = os.path.join(os.path.dirname(__file__), '..', 'assets', 'tilesets', 'pixellab')


def call(method, path, body=None):
    req = urllib.request.Request(API + path, method=method,
                                 data=json.dumps(body).encode() if body is not None else None,
                                 headers={'Authorization': 'Bearer ' + os.environ['PIXELLAB_API_KEY'],
                                          'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=300) as r:
        return r.status, json.load(r)


def warte(tid):
    for _ in range(120):
        try:
            st, d = call('GET', f'/tilesets/{tid}')
        except urllib.error.HTTPError as e:  # API liefert gelegentlich 500/423 waehrend der Erzeugung
            st, d = e.code, {}
        if st == 200 and 'tileset' in d:
            return d
        time.sleep(10)
    raise SystemExit('Timeout fuer ' + tid)


def speichern(d, name, tid):
    os.makedirs(OUT, exist_ok=True)
    d['id'] = tid
    json.dump(d, open(os.path.join(OUT, name + '.json'), 'w'), indent=1)
    tiles = d['tileset']['tiles']
    ts = d['tileset']['tile_size']['width']
    rows = max(t['original_position']['row'] for t in tiles) + 1 if all('original_position' in t for t in tiles) else 1
    cols = max(t['original_position']['col'] for t in tiles) + 1 if rows > 1 else len(tiles)
    sheet = Image.new('RGBA', (cols * ts, rows * ts))
    for i, t in enumerate(tiles):
        im = Image.open(io.BytesIO(base64.b64decode(t['image']['base64'])))
        p = t.get('original_position') or {'row': 0, 'col': i}
        sheet.paste(im, (p['col'] * ts, p['row'] * ts))
    sheet.save(os.path.join(OUT, name + '.png'))
    print('gespeichert', name, len(tiles), 'Tiles')


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'holen':
        tid, name = sys.argv[2], sys.argv[3]
        speichern(warte(tid), name, tid)
    elif cmd == 'erzeugen':
        name, reqf = sys.argv[2], sys.argv[3]
        st, d = call('POST', '/create-tileset', json.load(open(reqf)))
        print(st, {k: v for k, v in d.items() if k != 'tileset'})
        tid = d.get('tileset_id') or d.get('id') or (d.get('tileset') or {}).get('id')
        if 'tileset' in d and d['tileset'].get('tiles'):
            speichern(d, name, tid)
        else:
            speichern(warte(tid), name, tid)
