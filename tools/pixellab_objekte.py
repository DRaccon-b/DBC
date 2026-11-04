"""Objektgruppen fuer Karte 01 ueber den PixelLab-Objekt-Manager erzeugen.

  python3 tools/pixellab_objekte.py <gruppe>        # Gruppe aus OBJEKTGRUPPEN erzeugen
  python3 tools/pixellab_objekte.py <gruppe> holen <object_id>   # nur herunterladen

Ruft POST /v2/create-1-direction-object mit `size` und `item_descriptions` auf. Bei kleinen
Groessen liefert PixelLab viele Kandidaten auf einmal (<=42 px: bis 64, <=85 px: bis 16).
Die Kandidaten werden ueber api.pixellab.ai heruntergeladen (backblaze ist in der
Cloud-Umgebung gesperrt) und unter assets/objekte/karte01/<gruppe>/NN.png abgelegt,
zugeschnitten auf den sichtbaren Inhalt; dazu uebersicht.png mit Nummern.
"""
import base64, io, json, os, sys, time, urllib.error, urllib.request, zipfile
from PIL import Image, ImageDraw

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
OUT = os.path.join(ROOT, 'assets', 'objekte', 'karte01')
OUT_K2 = os.path.join(ROOT, 'assets', 'objekte', 'karte02')
API = 'https://api.pixellab.ai'

STIL = ("Top-down RPG map object in polished handheld monster-collecting RPG pixel art: colored dark outline "
        "(darkest shade of the object's own hue, never pure black), light from the upper left, hue-shifted "
        "shading (shadows toward blue/teal, highlights toward warm yellow), round clumped shapes, bright and "
        "clean, no noise, no dithering, transparent background, no ground, no cast shadow.")

PALETTE = [
    # Laub / Gras
    '#173f3a', '#1f5a46', '#2e7a4c', '#45a052', '#5fbb58', '#78cc60', '#93db70', '#b6eb8a', '#dff5a8',
    # Nadelbaum (kuehler)
    '#12333a', '#1b4d4f', '#24686a', '#3a8a7e',
    # Holz / Stamm / Erde
    '#3a2420', '#5a3a2c', '#7a5236', '#9c6c44', '#c08c58', '#e0b47a',
    # Stein / Schiefer
    '#24304a', '#33466a', '#465e88', '#5e78a2', '#7c95bb', '#a2b6d4', '#c8d6ea',
    # Rune / Kristall
    '#2fc7d8', '#7ff0f5',
    # Bluete pink / blau
    '#7a2a5a', '#b23c82', '#e060a8', '#f59acb', '#ffd2e8', '#2a4fb0', '#3f7fe0', '#7fb8f8',
    # Blumen / Akzente
    '#ffffff', '#fff2a0', '#f5c842', '#e8702a', '#c83a3a', '#ff8a8a',
    # Sand / Zeltstoff
    '#f2dba6', '#1f7a7a', '#2fa39a',
]

OBJEKTGRUPPEN = {
    'baeume': {'size': 48, 'items': [
        'round leafy deciduous tree, big clumped canopy of rounded leaf puffs, short brown trunk with roots',
        'round leafy deciduous tree, slightly wider canopy, visible brown trunk',
        'round leafy deciduous tree, darker green canopy, three big leaf clumps',
        'small round leafy tree, compact canopy',
        'leafy tree with a few red fruits in the canopy',
        'round leafy tree with a faint glowing cyan rune carved in the trunk',
        'tall pine tree, layered teal-green needle tiers, small trunk',
        'tall pine tree, slightly narrower, layered needle tiers',
        'small young pine tree',
        'pine tree, wide base, layered tiers',
        'tree with a big round pink blossom canopy, brown trunk',
        'tree with a big round light blue crystal-leaf canopy, brown trunk',
        'large round green bush, clumped leaves',
        'round green bush with small white flowers',
        'dense dark green hedge bush',
        'leafy tree, light spring green canopy',
    ]},
    'deko': {'size': 32, 'items': [
        'small patch of white flowers with yellow centers on a few leaves',
        'small patch of yellow flowers',
        'small patch of pink flowers',
        'small patch of light blue flowers',
        'cluster of red and white flowers',
        'tall grass tuft, three blades',
        'small grass tuft',
        'tall reed grass tuft',
        'small grey round rock',
        'mossy grey boulder',
        'two small stacked grey rocks',
        'grey rock with green moss on top',
        'small standing rune stone, grey slate with a glowing cyan rune',
        'tall slim rune stone monolith, slate blue with glowing cyan runes',
        'small red mushroom pair',
        'small brown tree stump',
        'fallen log with moss',
        'green lily pad',
        'green lily pad with a pink lotus flower',
        'two small lily pads',
        'orange starfish',
        'small spiral seashell',
        'small grey sea rock with white foam ring, in water',
        'pink branching coral',
        'beach grass tuft',
        'small round bush',
        'small fern',
        'cluster of tiny white flowers in grass',
    ]},
    'dschungel': {'size': 128, 'items': [
        'gigantic ancient jungle tree seen from above at an angle: huge layered dome canopy of rounded leaf clumps in several greens, '
        'thick twisted trunk with large buttress roots spreading on the ground, hanging liana vines and moss, a few glowing cyan runes on the trunk',
        'colossal jungle tree, very wide multi-layered canopy with lighter leaf highlights on top, massive trunk with sprawling buttress roots, '
        'long hanging vines with small flowers, moss patches',
        'giant tropical rainforest tree, broad umbrella canopy made of many round leaf clusters, thick trunk, big snake-like roots, hanging lianas',
        'enormous mystical jungle tree with a huge rounded canopy, glowing cyan rune carvings in the bark, buttress roots, hanging vines and ferns at its base',
    ]},
    'gross': {'size': 64, 'items': [
        'huge ancient tree with a massive round green canopy and thick trunk with glowing cyan runes and roots',
        'huge round pink blossom tree with thick trunk',
        'huge round light blue crystal-leaf tree with thick trunk',
        'teal camping tent with an open flap, a wooden lantern post with a glowing lantern and a small wooden crate beside it',
        'wooden plank bridge seen from above, horizontal, planks running vertically, with rope rails and posts at both ends',
        'stone staircase seen from above going down a cliff, slate blue stone steps between dark slate side walls with small grass tufts on top, front view of steps',
        'narrow vertical waterfall seen from above, white and light blue foaming water falling down a cliff face, splash foam at the bottom',
        'large mossy grey sea rock cluster in water with white foam ring',
        'wooden pier jetty seen from above, vertical planks, short',
        'big grey boulder with moss and a small glowing rune',
        'group of three tall pine trees',
        'large dark green bush cluster',
    ]},
}


# ---------------------------------------------------------------- Karte 02 (Factorial Town)
STIL_K2 = ("Top-down RPG map object for an industrial factory town in polished handheld monster-collecting RPG "
           "pixel art: colored dark outline (darkest shade of the object's own hue, never pure black), light from "
           "the upper left, hue-shifted shading (shadows toward blue, highlights slightly warm), clean readable "
           "shapes, bright and clean, no noise, no dithering, transparent background, no ground, no cast shadow.")
PALETTE_K2 = [
    # Stahl / Beton
    '#1c2128', '#2a313a', '#3e4850', '#56626b', '#717e87', '#8e9ba3', '#aab6bd', '#c8d1d6', '#e8ecee',
    # Container rot / blau / orange / gruen
    '#5e2a26', '#8c3a30', '#b5503e', '#d47258', '#24395c', '#335888', '#4a78ad', '#7aa2cc',
    '#7a4a1e', '#b06e2a', '#d99440', '#f0bc6c', '#2a4a30', '#3e6a44', '#5a8c5c', '#86b080',
    # Gelb (Maschinen, Warnfarbe)
    '#6e5410', '#a8801c', '#d6a828', '#f2d050', '#fff0a0',
    # Reaktor / Leuchten
    '#141c3a', '#22306a', '#34489c', '#4c66c8', '#2f8f5a', '#4fd07a', '#9af5b0', '#2fc7d8', '#7ff0f5',
    # Feuer / Glut / Ziegel / Holz
    '#c83a1e', '#e8702a', '#f5b042', '#fff2a0', '#5e2f26', '#8f4737', '#b8664b', '#5a4030', '#94704e',
]
OBJEKTGRUPPEN_K2 = {
    'k2_klein': {'size': 32, 'items': [
        'blue steel oil barrel', 'grey steel barrel with hazard stripe', 'rusty brown barrel', 'two stacked grey steel barrels',
        'wooden pallet with two small crates', 'small wooden crate', 'orange traffic cone', 'two orange traffic cones',
        'yellow triangle warning sign on a short post', 'yellow industrial robot arm, standing, side view from above',
        'yellow robot arm with gripper, raised', 'small yellow forklift seen from above', 'wooden cable reel with dark cable',
        'grey gas cylinder', 'green electrical box on a pole', 'short street light post with warm lamp',
        'small grey trash bin', 'red fire hydrant', 'metal toolbox', 'stack of steel pipes', 'pile of bolts and nuts',
        'small scrap metal pieces', 'park bench, wooden seat on metal legs', 'small metal vent box',
        'stack of four grey metal canisters', 'small concrete barrier block', 'yellow and black hazard barrier',
        'metal sewer manhole cover', 'small control terminal with screen', 'wall mounted fan unit',
    ]},
    'k2_mittel': {'size': 64, 'items': [
        'compact industrial power generator with a glowing cyan core in a glass cylinder, steel housing',
        'industrial power generator with cyan glowing capsule, pipes and bolts',
        'small iron furnace with glowing orange fire inside the grated front, dark steel',
        'small blacksmith furnace with burning coals visible, steel hood',
        'big steel gear cog lying on the ground', 'pile of rusty scrap metal, pipes and plates',
        'pile of broken machine parts and scrap', 'broken rusty red robot lying on the ground',
        'broken orange spherical robot, damaged', 'yellow hydraulic press gantry frame over a conveyor belt',
        'yellow industrial gantry with clamp, seen from above', 'large wooden cable reel with thick cable',
        'industrial control panel console with screens', 'stack of metal crates',
        'yellow forklift carrying a pallet', 'steel water tank on legs',
    ]},
    'k2_gross': {'size': 84, 'items': [
        'red shipping container, horizontal, corrugated sides, seen from above at an angle',
        'blue shipping container, horizontal, corrugated sides',
        'orange shipping container, horizontal, corrugated sides',
        'green shipping container, horizontal, corrugated sides',
        'red shipping container with white label, horizontal', 'blue shipping container with doors on the side',
        'orange shipping container, weathered', 'green shipping container, weathered',
        'red flatbed truck carrying wooden crates, side view from above, facing right',
        'red cargo truck with two crates on the flatbed',
        'yellow industrial scrap crusher press machine with scrap inside',
        'two stacked horizontal grey pressure gas tanks on a steel frame',
        'two stacked horizontal steel tanks with pipes and valves',
        'market stall with an orange and white striped awning', 'heavy hydraulic press machine, yellow frame',
        'large steel generator housing with vents',
    ]},
    'k2_mini': {'size': 18, 'items': [
        'blue steel oil barrel', 'grey steel barrel', 'rusty brown barrel', 'grey barrel with yellow hazard band',
        'orange traffic cone', 'grey gas cylinder', 'small grey trash bin', 'red fire hydrant', 'red metal toolbox',
        'small wooden crate', 'grey metal jerry can', 'pile of bolts', 'small scrap metal pieces', 'red fire extinguisher',
        'small cardboard box', 'blue plastic barrel', 'metal bucket', 'small concrete block', 'yellow hard hat',
        'coiled cable', 'small pipe valve', 'pressure gauge on a short pipe', 'oil can', 'small green crate',
    ]},
    'k2_ortho': {'size': 84, 'items': [
        'red flatbed truck carrying two wooden crates, flat orthographic side view facing right, not isometric',
        'red cargo truck with wooden crates on the flatbed, flat side view facing right, orthographic, axis aligned',
        'red flatbed truck, orthographic side view facing right, top slightly visible',
        'two horizontal grey pressure tanks stacked on a steel frame with pipes and a valve, flat front view, orthographic, not isometric',
        'two stacked horizontal steel gas tanks with brass valves, straight front view, orthographic',
        'two horizontal grey tanks on a rack, front view, orthographic, axis aligned',
        'yellow industrial scrap crusher press with scrap metal inside, straight front view, orthographic, not isometric',
        'yellow hydraulic scrap compactor machine, front view, orthographic',
        'grey diesel generator housing with vents, straight front view, orthographic, not isometric',
        'market stall with an orange and white striped awning and a wooden counter, straight front view, orthographic',
        'yellow forklift, flat side view facing right, orthographic',
        'industrial control console with screens, straight front view, orthographic',
        'stack of wooden and metal crates, straight front view, orthographic',
        'steel water tank on four legs, front view, orthographic',
        'red flatbed truck with a covered load, side view facing left, orthographic',
        'two stacked horizontal pressure tanks, rusty, front view, orthographic',
    ]},
    'k2_hoch': {'size': 100, 'items': [
        'tall white vertical gas silo on four steel legs with a gear logo, seen from above at an angle',
        'tall cylindrical industrial brick chimney stack with a metal ring top',
        'tall dark signal pillar obelisk with a red light on top and a glowing blue core',
        'tall white storage silo with ladder and legs',
    ]},
    'k2_turm': {'size': 140, 'items': [
        'tall blast furnace tower with brick body, steel frame, glowing fire at the bottom and a chimney top',
        'industrial smelting tower with orange glowing furnace opening, pipes and a tall metal chimney',
        'tall dark metal tesla coil pylon with stacked rings and a cyan light on top',
        'tall reactor cooling pylon of stacked dark discs with a glowing cap',
    ]},
    'k2_kran': {'size': 192, 'items': [
        'large yellow gantry crane on rail wheels, two legs and a top beam with a trolley, holding a red container, seen from above at an angle',
    ]},
    'k2_reaktor': {'size': 256, 'items': [
        'huge futuristic nuclear reactor: large dark blue cylindrical dome with glowing green rings and a big round green glowing core window, '
        'antenna on top, standing on a wide dark metal base with control screens and a central secure door with hazard stripes, seen from above at an angle',
    ]},
}


def call(method, path, body=None, raw=False):
    req = urllib.request.Request(API + path, method=method,
                                 data=json.dumps(body).encode() if body is not None else None,
                                 headers={'Authorization': 'Bearer ' + os.environ['PIXELLAB_API_KEY'],
                                          'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=300) as r:
        data = r.read()
        return data if raw else json.loads(data)


def warte(oid):
    for _ in range(120):
        try:
            d = call('GET', f'/v2/objects/{oid}')
            if d.get('status') in ('review', 'completed'):
                return d
            if d.get('status') == 'failed':
                raise SystemExit('fehlgeschlagen: %s' % d)
        except urllib.error.HTTPError:
            pass
        time.sleep(10)
    raise SystemExit('Timeout')


def bilder_aus_zip(data):
    z = zipfile.ZipFile(io.BytesIO(data))
    namen = sorted((n for n in z.namelist() if n.lower().endswith('.png')),
                   key=lambda n: [int(t) if t.isdigit() else t for t in __import__('re').split(r'(\d+)', n)])
    return [Image.open(io.BytesIO(z.read(n))).convert('RGBA') for n in namen]


def herunterladen(oid, d):
    if d.get('status') == 'completed':          # nur ein Kandidat: direkt als Spritesheet exportieren
        return [bilder_aus_zip(call('GET', f'/v2/objects/{oid}/spritesheet', raw=True))[0]], [oid]
    # 1) direkter ZIP-Download (funktioniert auch fuer Objekte im Review-Status?)
    try:
        ims = bilder_aus_zip(call('GET', f'/mcp/objects/{oid}/download', raw=True))
        if len(ims) > 1 or d.get('status') == 'completed':
            return ims, [oid]
    except (urllib.error.HTTPError, zipfile.BadZipFile):
        pass
    # 2) alle Kandidaten uebernehmen und einzeln exportieren
    n = len(d.get('frame_urls') or [])
    sel = call('POST', f'/v2/objects/{oid}/select-frames', {'indices': list(range(n)), 'common_tag': 'karte01'})
    ims = []
    for i in sel['created_object_ids']:
        z = call('GET', f'/v2/objects/{i}/spritesheet', raw=True)
        ims.append(bilder_aus_zip(z)[0])
    return ims, sel['created_object_ids']


def speichern(gruppe, ims, ids):
    ziel = os.path.join(OUT_K2, gruppe[3:]) if gruppe.startswith('k2_') else os.path.join(OUT, gruppe)
    os.makedirs(ziel, exist_ok=True)
    for i, im in enumerate(ims):
        bb = im.getbbox()
        (im.crop(bb) if bb else im).save(os.path.join(ziel, '%02d.png' % i))
    json.dump({'object_ids': ids}, open(os.path.join(ziel, 'ids.json'), 'w'), indent=1)
    # Uebersicht mit Nummern auf Grasgrund, 3x
    w = max(im.width for im in ims); h = max(im.height for im in ims)
    spalten = min(8, len(ims)); zeilen = (len(ims) + spalten - 1) // spalten
    sheet = Image.new('RGBA', (spalten * (w + 8), zeilen * (h + 18)), (120, 204, 96, 255))
    dr = ImageDraw.Draw(sheet)
    for i, im in enumerate(ims):
        x, y = (i % spalten) * (w + 8), (i // spalten) * (h + 18)
        sheet.alpha_composite(im, (x + 4, y + 14))
        dr.text((x + 2, y + 1), str(i), fill=(0, 0, 0, 255))
    sheet = sheet.resize((sheet.width * 3, sheet.height * 3), Image.NEAREST)
    sheet.save(os.path.join(ziel, 'uebersicht.png'))
    print(gruppe, len(ims), 'Kandidaten ->', os.path.relpath(ziel, ROOT))


def erzeugen(gruppe):
    k2 = gruppe.startswith('k2_')
    g = (OBJEKTGRUPPEN_K2 if k2 else OBJEKTGRUPPEN)[gruppe]
    stil, palette = (STIL_K2, PALETTE_K2) if k2 else (STIL, PALETTE)
    req = {'description': stil, 'size': g['size'], 'view': 'top-down',
           'item_descriptions': [it + '. ' + stil for it in g['items']],
           'target_palette': {'colors': palette, 'name': 'Karte02 Industrie' if k2 else 'Karte01 handheld'}}
    d = call('POST', '/v2/create-1-direction-object', req)
    oid = d['object_id']
    print(gruppe, 'Objekt', oid)
    d = warte(oid)
    ims, ids = herunterladen(oid, d)
    speichern(gruppe, ims, ids)


if __name__ == '__main__':
    if len(sys.argv) > 3 and sys.argv[2] == 'holen':
        oid = sys.argv[3]
        d = call('GET', f'/v2/objects/{oid}')
        speichern(sys.argv[1], *herunterladen(oid, d))
    else:
        erzeugen(sys.argv[1])
