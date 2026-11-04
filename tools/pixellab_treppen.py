"""Erzeugt die Klippentreppe von Karte 01 ueber den PixelLab-Objekt-Manager.

  python3 tools/pixellab_treppen.py erzeugen      # neues Objekt, Kandidaten herunterladen
  python3 tools/pixellab_treppen.py waehlen <object_id>

'erzeugen' ruft POST /v2/create-1-direction-object mit der Treppe aus der Vorlage
(assets/vorlagen/referenzen/treppe_48.png) als Stilbild auf. Bei 48 px liefert
PixelLab mehrere Kandidaten (Status 'review'). Alle werden im Objekt-Manager als
eigene Objekte uebernommen (Tag 'karte01-treppe'), exportiert und als Uebersicht in
assets/objekte/karte01/kandidaten.png (+ kandidaten.json mit den IDs) abgelegt.
'waehlen' laedt das gewaehlte Objekt, speichert es als treppe.png und traegt die
Treppen aus hoehenplan.json in treppen.json ein. Danach karte_bauen.py ausfuehren.
"""
import base64, io, json, os, sys, time, urllib.error, urllib.request
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte01')
REF = os.path.join(ROOT, 'assets', 'vorlagen', 'referenzen')
OUT = os.path.join(ROOT, 'assets', 'objekte', 'karte01')
API = 'https://api.pixellab.ai/v2'
T = 16


def call(method, path, body=None):
    req = urllib.request.Request(API + path, method=method,
                                 data=json.dumps(body).encode() if body is not None else None,
                                 headers={'Authorization': 'Bearer ' + os.environ['PIXELLAB_API_KEY'],
                                          'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.load(r)


def b64(path):
    buf = io.BytesIO(); Image.open(path).convert('RGB').save(buf, 'PNG')
    return {'type': 'base64', 'base64': base64.b64encode(buf.getvalue()).decode(), 'format': 'png'}


def lade_objekt(oid):
    """Fertiges Objekt als Spritesheet-ZIP ueber api.pixellab.ai holen (die Bild-URLs auf
    backblaze.pixellab.ai sind in der Cloud-Umgebung gesperrt)."""
    import zipfile
    req = urllib.request.Request(f'{API}/objects/{oid}/spritesheet',
                                 headers={'Authorization': 'Bearer ' + os.environ['PIXELLAB_API_KEY']})
    z = zipfile.ZipFile(io.BytesIO(urllib.request.urlopen(req, timeout=120).read()))
    name = [n for n in z.namelist() if n.endswith('.png')][0]
    return Image.open(io.BytesIO(z.read(name))).convert('RGBA')


def warte(oid, ziel=('review', 'completed')):
    for _ in range(90):
        try:
            d = call('GET', f'/objects/{oid}')
            if d.get('status') in ziel:
                return d
            if d.get('status') == 'failed':
                raise SystemExit('fehlgeschlagen: %s' % d)
        except urllib.error.HTTPError:
            pass
        time.sleep(8)
    raise SystemExit('Timeout')


def erzeugen():
    pal = json.load(open(os.path.join(REF, 'palette.json')))['farben']
    req = {
        'description': 'wide stone staircase leading down a cliff, top-down view, grey-blue stone steps '
                       'framed by mossy dark slate side walls with bushy green grass, game map tile object',
        'view': 'top-down',
        'style_images': [b64(os.path.join(REF, 'treppe_48.png'))],
        'target_palette': {'colors': pal, 'name': 'Karte01 Vorlage'},
    }
    d = call('POST', '/create-1-direction-object', req)
    oid = d.get('object_id')
    print('Objekt', oid, d.get('status'))
    d = warte(oid)
    n = len(d.get('frame_urls') or []) or 1
    if d.get('status') == 'review':
        # alle Kandidaten als eigene Objekte uebernehmen, damit sie exportierbar sind
        d = call('POST', f'/objects/{oid}/select-frames', {'indices': list(range(n)), 'common_tag': 'karte01-treppe'})
        ids = d['created_object_ids']
    else:
        ids = [oid]
    os.makedirs(OUT, exist_ok=True)
    ims = [lade_objekt(i) for i in ids]
    w, h = ims[0].size
    sheet = Image.new('RGBA', (len(ims) * (w + 4), h), (255, 0, 255, 255))
    for i, im in enumerate(ims):
        sheet.alpha_composite(im, (i * (w + 4), 0))
    sheet.save(os.path.join(OUT, 'kandidaten.png'))
    json.dump(ids, open(os.path.join(OUT, 'kandidaten.json'), 'w'), indent=1)
    print(len(ids), 'Kandidaten -> kandidaten.png / kandidaten.json')


def waehlen(oid):
    im = lade_objekt(oid)
    im.save(os.path.join(OUT, 'treppe.png'))
    # 48x48 = 3 Kacheln breit; vertikal mittig auf die 2 Kacheln hohe Wand
    plan = json.load(open(os.path.join(KARTE, 'hoehenplan.json')))
    tcol = {vx: s['t'] for s in plan['segmente'] for vx in range(s['von'], s['bis'] + 1)}
    dy = (im.height - 2 * T) // 2
    dx = (im.width - plan['treppen'][0]['breite'] * T) // 2
    idx = {str(tr['x']): {'datei': 'treppe.png', 'px': tr['x'] * T - dx, 'py': (tcol[tr['x']] - 1) * T - dy,
                          'object_id': oid} for tr in plan['treppen']}
    json.dump(idx, open(os.path.join(OUT, 'treppen.json'), 'w'), indent=1)
    print('treppe.png', im.size, 'fuer', len(idx), 'Treppen')


if __name__ == '__main__':
    if sys.argv[1] == 'erzeugen':
        erzeugen()
    else:
        waehlen(sys.argv[2])
