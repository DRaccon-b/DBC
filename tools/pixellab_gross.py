"""Grosse Einzelobjekte (> 256 px) mit dem PixelLab Pro-Generator (generate-image-v2).

AUSNAHME von der Regel "PixelLab nur Objekt-Creator" (Nutzer, Karte 25): nur fuer Objekte, die groesser als 256 px
sein muessen (Schiff in Sunset Bay). Subjekt-Referenz = Ausschnitt der Vorlage (geschuetzte Symbole vorher
uebermalt), Stil-Referenz = ein vorhandenes Objekt der Karte, damit Pixeldichte, Kontur und Licht passen.

  python3 tools/pixellab_gross.py schiff
"""
import base64, io, json, os, sys, time, urllib.request, urllib.error
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw
from pixellab_objekte import call, FR14

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')


def b64(im):
    buf = io.BytesIO(); im.save(buf, 'PNG')
    return base64.b64encode(buf.getvalue()).decode()


def ref(im, beschreibung=None):
    r = {'image': {'type': 'base64', 'base64': b64(im), 'format': 'png'}, 'size': {'width': im.width, 'height': im.height}}
    if beschreibung:
        r['usage_description'] = beschreibung
    return r


AUFTRAEGE = {
    'schiff': {
        'ziel': 'assets/objekte/karte25/schiff',
        'groesse': (480, 304),
        'vorlage': ('assets/vorlagen/karte25_vorlage.png', (1424, 160, 1904, 464)),
        'uebermalen': [(1640, 270, 1720, 330)],                 # Wappen der Vorlage (geschuetztes Design) entfernen
        'stil': 'assets/objekte/karte25/leuchtturm/00.png',
        'text': ('huge dark steel battleship docked in a harbor, seen from the side as a flat 2D profile, bow pointing left '
                 'with a sharp ram, long dark grey riveted steel hull with a thin red stripe along the deck line and a row of '
                 'small glowing purple round portholes, two anchor chains hanging from the bow, on the deck a big double gun '
                 'turret at the front, a tall blocky command tower in the middle with a glowing red visor slit and a pointed '
                 'spire on top, a small golden winged emblem of a simple star with wings on the tower front, a second tower '
                 'at the back with antennas and many small lit windows, ' + FR14),
    },
}


def main(name):
    a = AUFTRAEGE[name]
    w, h = a['groesse']
    pf, box = a['vorlage']
    v = Image.open(os.path.join(ROOT, pf)).convert('RGB').crop(box)
    d = ImageDraw.Draw(v)
    for (x0, y0, x1, y1) in a.get('uebermalen', []):
        d.rectangle((x0 - box[0], y0 - box[1], x1 - box[0], y1 - box[1]), fill=(46, 46, 58))
    stil = Image.open(os.path.join(ROOT, a['stil'])).convert('RGBA')
    req = {'description': a['text'], 'image_size': {'width': w, 'height': h}, 'no_background': True,
           'reference_images': [ref(v, 'subject and layout of the ship: shape, proportions, towers, colours')],
           'style_image': ref(stil), 'style_options': {'color_palette': False, 'outline': True, 'detail': True}}
    r = call('POST', '/v2/generate-image-v2', req)
    jid = r['background_job_id']
    print(name, 'Auftrag', jid)
    for _ in range(90):
        time.sleep(10)
        try:
            j = call('GET', '/v2/background-jobs/%s' % jid)
        except urllib.error.HTTPError:
            continue
        if j.get('status') == 'completed':
            break
        if j.get('status') == 'failed':
            raise SystemExit('fehlgeschlagen: %s' % json.dumps(j)[:500])
    else:
        raise SystemExit('Timeout')
    ziel = os.path.join(ROOT, a['ziel'])
    os.makedirs(ziel, exist_ok=True)
    json.dump(j, open(os.path.join(ziel, 'antwort.json'), 'w'), indent=1, default=str)
    lr = j.get('last_response') or {}
    bilder = lr.get('images') or lr.get('image') or []
    if isinstance(bilder, dict):
        bilder = [bilder]
    n = 0
    for i, b in enumerate(bilder):
        data = b.get('base64') if isinstance(b, dict) else b
        if not data:
            continue
        im = Image.open(io.BytesIO(base64.b64decode(data))).convert('RGBA')
        im.save(os.path.join(ziel, '%02d.png' % i)); n += 1
    v.save(os.path.join(ziel, 'referenz.png'))
    print(name, '%d Bild(er) ->' % n, a['ziel'])


if __name__ == '__main__':
    main(sys.argv[1])
