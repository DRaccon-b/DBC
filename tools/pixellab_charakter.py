"""Spielfigur fuer die Karten ueber PixelLab erzeugen (16x16, 4 Richtungen, Lauf-Animation).

  python3 tools/pixellab_charakter.py                 # neu erzeugen (Charakter + Laufanimation)
  python3 tools/pixellab_charakter.py holen <id>      # vorhandenen Charakter nur herunterladen
  python3 tools/pixellab_charakter.py animieren <id>  # Laufanimation zu vorhandenem Charakter

Ablauf: POST /v2/create-character-with-4-directions (image_size 16x16; PixelLab legt die Figur auf
eine etwas groessere Leinwand), dann POST /v2/animate-character mit Vorlage `walking-4-frames`,
dann GET /v2/characters/<id>/zip. Ausgabe unter assets/charaktere/spieler/:
  rohdaten/                     ZIP-Inhalt von PixelLab (rotations/, animations/, metadata.json)
  spieler.png                   Spritesheet 16x16: Zeilen = unten, links, rechts, oben;
                                Spalten = Stehen + 4 Lauf-Frames
  spieler.json                  Aufbau des Spritesheets
  vorschau.png                  8x vergroessert
  spiel/spieler.js              dasselbe fuer die Spielseite (laeuft auch per file://)
Braucht PIXELLAB_API_KEY.
"""
import io, json, os, sys, time, urllib.error, urllib.request, zipfile
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
OUT = os.path.join(ROOT, 'assets', 'charaktere', 'spieler')
API = 'https://api.pixellab.ai/v2'
RICHTUNGEN = ['south', 'west', 'east', 'north']          # Zeilen im Spritesheet
GROESSE = 16
BESCHREIBUNG = ("young adventurer kid for a top-down monster-collecting RPG overworld: short messy brown hair, "
                "teal headband, red jacket over white shirt, dark blue shorts, small yellow backpack, brown boots, "
                "cheerful, bright clean colors, readable at 16 pixels")


def call(method, path, body=None, raw=False):
    req = urllib.request.Request(API + path, method=method,
                                 data=json.dumps(body).encode() if body is not None else None,
                                 headers={'Authorization': 'Bearer ' + os.environ['PIXELLAB_API_KEY'],
                                          'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            data = r.read()
    except urllib.error.HTTPError as e:
        sys.exit('%s %s -> %s %s' % (method, path, e.code, e.read().decode()[:800]))
    return data if raw else json.loads(data)


def warte_job(jid, was):
    for _ in range(240):
        d = call('GET', '/background-jobs/' + jid)
        st = d.get('status')
        if st == 'completed':
            return d
        if st == 'failed':
            sys.exit('%s fehlgeschlagen: %s' % (was, json.dumps(d)[:800]))
        time.sleep(5)
    sys.exit('%s: Zeitueberschreitung' % was)


def erzeugen():
    d = call('POST', '/create-character-with-4-directions', {
        'description': BESCHREIBUNG,
        'image_size': {'width': GROESSE, 'height': GROESSE},
        'view': 'low top-down',
        'outline': 'single color outline',
        'shading': 'basic shading',
        'detail': 'low detail',
        'proportions': {'type': 'preset', 'name': 'chibi'},
    })
    cid = d['character_id']
    print('Charakter', cid, '- warte auf Rotationen ...')
    warte_job(d['background_job_id'], 'Charakter')
    return cid


def animieren(cid):
    d = call('POST', '/animate-character', {
        'character_id': cid, 'mode': 'template', 'template_animation_id': 'walking-4-frames',
        'animation_name': 'gehen', 'directions': RICHTUNGEN,
    })
    print('Animation laeuft:', d.get('directions'))
    for jid in d['background_job_ids']:
        warte_job(jid, 'Animation')


def holen(cid):
    z = zipfile.ZipFile(io.BytesIO(call('GET', '/characters/%s/zip' % cid, raw=True)))
    roh = os.path.join(OUT, 'rohdaten')
    os.makedirs(roh, exist_ok=True)
    for n in z.namelist():
        if n.endswith('/'):
            continue
        ziel = os.path.normpath(os.path.join(roh, n))
        if not ziel.startswith(os.path.normpath(roh) + os.sep):
            continue                                        # keine Pfade ausserhalb
        os.makedirs(os.path.dirname(ziel), exist_ok=True)
        open(ziel, 'wb').write(z.read(n))
    json.dump({'character_id': cid}, open(os.path.join(roh, 'pixellab_id.json'), 'w'))
    spritesheet(roh)


def finde(roh, teil, richtung):
    """Alle PNGs unter roh, deren Pfad `teil` und die Richtung enthaelt, sortiert."""
    treffer = []
    for wurzel, _, dateien in os.walk(roh):
        for f in dateien:
            p = os.path.join(wurzel, f)
            rel = os.path.relpath(p, roh).replace(os.sep, '/')
            if f.endswith('.png') and teil in rel and '/%s/' % richtung in '/' + rel:
                treffer.append(p)
    return sorted(treffer)


def spritesheet(roh):
    stehen = {r: Image.open(os.path.join(roh, 'rotations', r + '.png')).convert('RGBA') for r in RICHTUNGEN}
    gehen = {r: [Image.open(p).convert('RGBA') for p in finde(roh, 'animations/', r)] for r in RICHTUNGEN}
    alle = list(stehen.values()) + [f for fs in gehen.values() for f in fs]
    # gemeinsamer Ausschnitt ueber alle Frames, damit die Figur nicht springt
    boxen = [im.getbbox() for im in alle if im.getbbox()]
    x0 = min(b[0] for b in boxen); y0 = min(b[1] for b in boxen)
    x1 = max(b[2] for b in boxen); y1 = max(b[3] for b in boxen)
    w, h = x1 - x0, y1 - y0
    zelle_w, zelle_h = max(GROESSE, w), max(GROESSE, h)
    n = 1 + max(len(f) for f in gehen.values())
    blatt = Image.new('RGBA', (zelle_w * n, zelle_h * len(RICHTUNGEN)), (0, 0, 0, 0))
    for zi, r in enumerate(RICHTUNGEN):
        for si, im in enumerate([stehen[r]] + gehen[r]):
            teil = im.crop((x0, y0, x1, y1))
            # unten mittig in die Zelle (Fuesse auf der Zellunterkante)
            blatt.alpha_composite(teil, (si * zelle_w + (zelle_w - w) // 2, zi * zelle_h + zelle_h - h))
    blatt.save(os.path.join(OUT, 'spieler.png'))
    blatt.resize((blatt.width * 8, blatt.height * 8), Image.NEAREST).save(os.path.join(OUT, 'vorschau.png'))
    info = {'zelle': [zelle_w, zelle_h], 'zeilen': ['unten', 'links', 'rechts', 'oben'],
            'spalten': ['stehen'] + ['gehen%d' % i for i in range(1, n)],
            'gehen_frames': {r: len(gehen[r]) for r in RICHTUNGEN},
            'hinweis': 'Fuesse auf der Zellunterkante; im Spiel unten mittig auf die 16x16-Spielerbox setzen.'}
    json.dump(info, open(os.path.join(OUT, 'spieler.json'), 'w'), indent=1)
    open(os.path.join(ROOT, 'spiel', 'spieler.js'), 'w').write(
        '// Erzeugt von tools/pixellab_charakter.py: Aufbau von assets/charaktere/spieler/spieler.png\n'
        'window.SPIELER_SPRITE = ' + json.dumps(info) + ';\n')
    print('Spritesheet', blatt.size, 'Zelle', (zelle_w, zelle_h), 'Frames', info['gehen_frames'])


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    if len(sys.argv) > 2 and sys.argv[1] == 'holen':
        holen(sys.argv[2])
    elif len(sys.argv) > 2 and sys.argv[1] == 'animieren':
        animieren(sys.argv[2]); holen(sys.argv[2])
    else:
        cid = erzeugen()
        animieren(cid)
        holen(cid)
