"""Erzeugt die Klippentreppen von Karte 01 per PixelLab-Inpainting im Kartenkontext.

  python3 tools/pixellab_treppen.py [x ...]   # ohne Argument: alle Treppen

Liest maps/karte01/terrain.png + hoehenplan.json, schneidet um jede Treppe einen
Ausschnitt aus, maskiert die Wandkacheln und laesst PixelLab dort eine Steintreppe
malen. Ergebnis: assets/objekte/karte01/treppe_<x>.png (transparent, auf die
Wandkacheln zugeschnitten) + treppen.json mit Position. Danach karte_bauen.py
erneut ausfuehren, es setzt die Treppen ein.

Stand Karte 01: Alle drei Uebergaenge haben dieselbe Geometrie (3 breit, 2 hoch),
daher nutzt treppen.json fuer alle das gelungenste Ergebnis treppe_stein.png
(Seed-Versatz SEED_OFFSET=100 bei x=49).
"""
import base64, io, json, os, sys, time, urllib.error, urllib.request
from PIL import Image, ImageDraw

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte01')
OUT = os.path.join(ROOT, 'assets', 'objekte', 'karte01')
API = 'https://api.pixellab.ai/v2'
T = 16
RAND_X, RAND_Y = 2, 2   # Kontext-Kacheln um die Treppe


def call(method, path, body=None):
    req = urllib.request.Request(API + path, method=method,
                                 data=json.dumps(body).encode() if body is not None else None,
                                 headers={'Authorization': 'Bearer ' + os.environ['PIXELLAB_API_KEY'],
                                          'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.load(r)


def b64(im):
    buf = io.BytesIO(); im.save(buf, 'PNG')
    return {'type': 'base64', 'base64': base64.b64encode(buf.getvalue()).decode(), 'format': 'png'}


def treppe(tr, tcol, terrain):
    x0, w = tr['x'], tr['breite']
    t = tcol[x0]
    y0 = t - 1                                   # Wand = Kachelzeilen t-1, t
    box = ((x0 - RAND_X) * T, (y0 - RAND_Y) * T, (x0 + w + RAND_X) * T, (y0 + 2 + RAND_Y) * T)
    bg = terrain.crop(box).convert('RGB')
    mask = Image.new('RGB', bg.size, (0, 0, 0))
    # Treppenkacheln + 4px Rand, damit die Treppe in die Wege uebergeht
    m = (RAND_X * T - 4, RAND_Y * T - 4, (RAND_X + w) * T + 4, (RAND_Y + 2) * T + 4)
    ImageDraw.Draw(mask).rectangle((m[0], m[1], m[2] - 1, m[3] - 1), fill=(255, 255, 255))
    req = {
        'description': 'stone stairs carved into a grey-blue rock cliff, steps going down from the grassy plateau to a sandy path, top-down view',
        'image_size': {'width': bg.width, 'height': bg.height},
        'view': 'high top-down', 'outline': 'selective outline', 'shading': 'medium shading', 'detail': 'medium detail',
        'background_image': b64(bg),
        'inpainting': {'type': 'mask', 'mask_image': b64(mask)},
        'seed': 7700 + x0 + int(os.environ.get('SEED_OFFSET', 0)),
    }
    d = call('POST', '/map-objects', req)
    oid = d.get('object_id') or d.get('id')
    print('Treppe x=%d: Job %s' % (x0, oid))
    for _ in range(60):
        time.sleep(5)
        try:
            d = call('GET', f'/map-objects/{oid}')
        except urllib.error.HTTPError:
            continue
        if d['status'] == 'completed':
            break
        if d['status'] == 'failed':
            raise SystemExit('fehlgeschlagen: %s' % d)
    raw = urllib.request.urlopen(d['download_url'], timeout=120).read()
    im = Image.open(io.BytesIO(raw)).convert('RGBA')
    if im.size != bg.size:
        im = im.resize(bg.size, Image.NEAREST)
    # nur den maskierten Bereich behalten
    sprite = im.crop(m)
    name = 'treppe_%d.png' % x0
    sprite.save(os.path.join(OUT, name))
    im.save(os.path.join(OUT, 'roh_' + name))
    return {'datei': name, 'px': box[0] + m[0], 'py': box[1] + m[1], 'object_id': oid}


def main():
    plan = json.load(open(os.path.join(KARTE, 'hoehenplan.json')))
    tcol = {}
    for s in plan['segmente']:
        for vx in range(s['von'], s['bis'] + 1):
            tcol[vx] = s['t']
    terrain = Image.open(os.path.join(KARTE, 'terrain_basis.png'))
    os.makedirs(OUT, exist_ok=True)
    idx_f = os.path.join(OUT, 'treppen.json')
    idx = json.load(open(idx_f)) if os.path.exists(idx_f) else {}
    wahl = {int(a) for a in sys.argv[1:]}
    for tr in plan['treppen']:
        if wahl and tr['x'] not in wahl:
            continue
        idx[str(tr['x'])] = treppe(tr, tcol, terrain)
        json.dump(idx, open(idx_f, 'w'), indent=1)


if __name__ == '__main__':
    main()
