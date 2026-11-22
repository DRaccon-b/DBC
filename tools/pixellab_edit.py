"""PixelLab-Bildbearbeitung (edit-image-pixen): ein vorhandenes Pixelbild nach Textanweisung veraendern, Pixelraster
und Aufbau bleiben erhalten. Bild hoechstens 256 px je Seite; wird auf ein Vielfaches von 4 mit transparenten Pixeln
aufgefuellt (nie skaliert) und danach wieder auf die Originalgroesse zugeschnitten.

  from pixellab_edit import bearbeiten
  neu = bearbeiten(Image, 'add fresh snow on top', hintergrund=False)
"""
import base64, io, os, sys, time, urllib.error
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image
import pixellab_tileset as pt


def _call(method, path, body=None):
    for i in range(12):
        try:
            return pt.call(method, path, body)
        except urllib.error.HTTPError as e:
            if e.code not in (423, 429, 500, 502, 503, 504) or i == 11:
                raise
            time.sleep(min(120, 10 * (i + 1)))


def bearbeiten(im, beschreibung, hintergrund=True, seed=None):
    im = im.convert('RGBA')
    w, h = im.size
    assert w <= 256 and h <= 256, (w, h)
    W, H = max(16, -(-w // 4) * 4), max(16, -(-h // 4) * 4)        # Mindestflaeche 16x16
    pad = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    pad.paste(im, (0, 0))
    b = io.BytesIO()
    pad.save(b, 'PNG')
    req = {'image': {'type': 'base64', 'base64': base64.b64encode(b.getvalue()).decode()},
           'description': beschreibung[:500], 'no_background': not hintergrund}
    if seed is not None:
        req['seed'] = seed
    st, d = _call('POST', '/edit-image-pixen', req)
    jid = d.get('background_job_id')
    for _ in range(120):
        st, r = _call('GET', '/background-jobs/' + jid)
        if r.get('status') == 'completed':
            img = r['last_response']['image']
            out = Image.open(io.BytesIO(base64.b64decode(img['base64']))).convert('RGBA')
            return out.crop((0, 0, w, h))
        if r.get('status') == 'failed':
            raise RuntimeError('PixelLab-Bearbeitung fehlgeschlagen: %s' % str(r)[:300])
        time.sleep(5)
    raise RuntimeError('Timeout PixelLab-Bearbeitung')
