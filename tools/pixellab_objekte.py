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
OUT_K3 = os.path.join(ROOT, 'assets', 'objekte', 'karte03')
OUT_K4 = os.path.join(ROOT, 'assets', 'objekte', 'karte04')
OUT_K5 = os.path.join(ROOT, 'assets', 'objekte', 'karte05')
OUT_K6 = os.path.join(ROOT, 'assets', 'objekte', 'karte06')
OUT_K7 = os.path.join(ROOT, 'assets', 'objekte', 'karte07')
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
    # Kaeferpanzer rot (Hirschkaefer-Stil)
    '#3a0e10', '#5e1418', '#8a1f22', '#b8302c', '#e0503c',
]

OBJEKTGRUPPEN = {
    'zelt_strand': {'size': 96, 'items': [
        'large teal canvas beach camping tent with an open front flap showing a cozy sleeping bag inside, wooden poles, guy ropes with pegs, small flag on top, straight front view',
    ]},
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


# ---------------------------------------------------------------- Karte 03 (Server Desert)
STIL_K3 = ("Top-down RPG map object for a sunny desert town in polished handheld monster-collecting RPG pixel art: "
           "colored dark outline (darkest shade of the object's own hue, never pure black), light from the upper left, "
           "hue-shifted shading (shadows toward purple-brown, highlights warm), clean readable shapes, bright and clean, "
           "no noise, no dithering, transparent background, no ground, no cast shadow. Straight front view, orthographic, "
           "not isometric.")
PALETTE_K3 = [
    # Sand / Sandstein
    '#5a3e26', '#7a5636', '#9c7448', '#c09a62', '#d8b87e', '#e8cf98', '#f4e4bc', '#fff4dc',
    # Lehm / Adobe / Ziegel
    '#4a2a1e', '#6e3c28', '#8f5234', '#b06a42', '#c8865a',
    # Gruen (Palmen, Kakteen)
    '#173f3a', '#1f5a46', '#2e7a4c', '#45a052', '#5fbb58', '#93db70',
    # Stoff rot / Holz
    '#5e1e22', '#8c2c2e', '#b5443c', '#d86a52', '#3a2a20', '#5a4030', '#7a5a40',
    # Stahl / Technik / Lila Kabel
    '#1c2128', '#2a313a', '#3e4850', '#56626b', '#8e9ba3', '#c8d1d6', '#2a2050', '#4a3a8a', '#7a6ac8',
    # Leuchten
    '#2fc7d8', '#7ff0f5', '#e6ffff', '#c83a1e', '#e8702a', '#f5b042', '#fff2a0', '#ffffff',
]
STIL_K4 = ("Top-down RPG map object for a sunny savanna with old rusty machinery in polished handheld monster-collecting "
           "RPG pixel art: colored dark outline (darkest shade of the object's own hue, never pure black), light from the "
           "upper left, hue-shifted shading (shadows toward purple-brown, highlights warm), clean readable shapes, "
           "slightly muted warm savanna colors, no noise, no dithering, transparent background, no ground, no cast "
           "shadow. Straight front view, orthographic, not isometric.")
PALETTE_K4 = [
    # Savannengras / Erde
    '#5a4a26', '#7a6430', '#957c3e', '#ad944e', '#c4aa60', '#d6bc70', '#e8d08a',
    '#7e5234', '#9a6844', '#b07c56', '#c08e66', '#d2a47c',
    # Gruen (Akazien, Plateau)
    '#2e3e22', '#3e5a2e', '#557a38', '#6e9a44', '#8cb455', '#afbd70',
    # Stein / Knochen
    '#4a4038', '#6a5e50', '#8a7c68', '#a8987e', '#c8b89a', '#e6dcc4', '#f6f0e0',
    # Rost / Eisen
    '#2e2830', '#4a3e44', '#6a4a3a', '#8a4a2a', '#a85e32', '#c47a44', '#5a5e6a', '#7e8494',
    # Akzente: Rot (Juwel), Blau (Kristall), Stoff
    '#8a1e22', '#c8303a', '#ff6a5a', '#3e5a8a', '#6e8ec4', '#a8c4ea', '#e6c49a',
]
OBJEKTGRUPPEN_K4 = {
    'k4_gross': {'size': 128, 'items': [
        'huge rusty broken iron gear wheel standing upright half buried in the ground, missing teeth, rust stains',
        'huge old rusty cogwheel lying tilted in the grass with broken spokes and orange rust',
        'giant bleached animal skull fossil like a crocodile skull lying on the ground',
        'giant curved ribcage bones of a huge animal skeleton sticking out of the ground',
    ]},
    'k4_baeume': {'size': 80, 'items': [
        'flat-topped umbrella acacia tree with a wide green canopy and a thin crooked trunk',
        'tall termite mound, a pointed reddish clay tower',
        'dead twisted charred black tree without leaves',
        'small young acacia tree with a flat green canopy',
    ]},
    'k4_mittel': {'size': 64, 'items': [
        'large rounded savanna boulder', 'safari canvas tent with an open entrance', 'small canvas tent',
        'carved wooden totem pole', 'campfire with stones around it', 'clay pots and a woven basket',
        'small rusty iron cogwheel lying on the ground', 'cluster of pale blue crystals growing out of rock',
        'pile of old bones', 'horned cow skull', 'dry thorny savanna bush', 'small termite mound',
        'wooden crate and barrel', 'wooden signpost with two arrows', 'stack of rusty pipes and scrap metal',
        'pile of small rocks',
    ]},
    'k4_klein': {'size': 32, 'items': [
        'tuft of dry yellow savanna grass', 'small green grass clump', 'few small pebbles', 'small white bone',
        'tiny animal skull', 'small pale blue crystal', 'tiny rusty cog', 'small orange savanna flower',
        'small grey rock', 'dry twig', 'small dark rock with ash', 'little red mushroom',
    ]},
    'k4_rand': {'size': 80, 'items': [
        'large baobab tree with a very thick bottle shaped trunk and a small green crown',
        'wide flat-topped umbrella acacia tree with a dense green canopy',
        'tall acacia tree with two layered flat green canopies',
        'dense round green savanna bush',
        'marula tree with a round full green crown and a short trunk',
        'thorny acacia shrub with small green leaves',
        'dragon blood tree with an umbrella shaped crown of thick branches',
        'young baobab tree with a few bare branches and small leaves',
    ]},
    'k4_zelte': {'size': 120, 'items': [
        'large safari canvas tent with an open entrance, wooden poles and guy ropes',
        'medium canvas expedition tent with an open flap and ropes',
    ]},
    'k4_zelte2': {'size': 100, 'items': [
        'canvas A-frame tent seen straight from the front, symmetric, open entrance flap in the middle, guy ropes on both sides',
    ]},
    'k4_monument': {'size': 160, 'items': [
        'giant dark iron gear monument standing upright with a glowing red gem in the hub, on a rocky dark stone base',
    ]},
}

STIL_K5 = ("Top-down RPG map object for a snowy arctic land in polished handheld monster-collecting RPG pixel art: "
           "colored dark outline (darkest shade of the object's own hue, never pure black), light from the upper left, "
           "hue-shifted shading (shadows toward blue-violet, highlights toward warm white), clean readable shapes, "
           "snow on top surfaces, no noise, no dithering, transparent background, no ground, no cast shadow. "
           "Straight front view, orthographic, not isometric.")
PALETTE_K5 = [
    # Schnee / Eis
    '#2a3a5a', '#3e5a7e', '#5a7ea2', '#7ea2c2', '#a8c6dc', '#cfe2ee', '#eaf3f8', '#ffffff',
    '#2a6a8e', '#3e8eb4', '#5ab0d2', '#8ad2ea', '#c2ecf8',
    # Tannengruen
    '#14302e', '#1e4a40', '#2a6650', '#3a8462', '#56a276',
    # Holz / Fell / Erde
    '#3a2418', '#5a3a26', '#7a5434', '#9a7046', '#bc9262', '#dcb886',
    # Stein
    '#3e4252', '#5a6072', '#7e8496', '#a6acbc',
    # Akzente: Feuer, Rot, Gold
    '#c8303a', '#ff7a3a', '#ffc85a', '#fff2b0',
]
OBJEKTGRUPPEN_K5 = {
    'k5_baeume': {'size': 80, 'items': [
        'tall snow covered fir tree, dark green with thick snow on every branch layer',
        'small snow covered pine tree',
        'round snow covered spruce tree, dense, white snow caps',
        'bare frozen birch tree with frost and icicles',
    ]},
    'k5_gross': {'size': 128, 'items': [
        'igloo made of snow blocks with a dark arched entrance, front view',
        'ice cave entrance in a frozen cliff, glowing blue ice, icicles hanging over a dark opening, front view',
        'two huge curved mammoth tusks sticking out of a snow drift',
        'frozen wooden fishing hut with snow on the roof',
    ]},
    'k5_mittel': {'size': 64, 'items': [
        'big snow covered boulder', 'clear blue ice block cube', 'tall pointed ice crystal spike',
        'snowman with a carrot nose and a red scarf', 'wooden signpost with snow on top',
        'wooden supply crates covered with snow', 'wooden barrel with snow on the lid', 'campfire with stones in snow',
        'wooden lantern post with a warm glowing lamp and snow cap', 'small snow covered rock pile',
        'frozen dead bush with frost', 'fishing hole in ice with a small wooden sign', 'stack of firewood logs with snow',
        'wooden sled with a fur blanket', 'banner flag on a pole, blue cloth with a snowflake emblem',
        'small ice boulder with frost',
    ]},
    'k5_server': {'size': 64, 'items': [
        'broken old computer server rack half frozen in ice, cracked dark metal case with snow on top, icicles, a few blinking cyan and red status lights, loose cables frozen to the side, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
    ]},
    'k5_wasserfall': {'size': 96, 'items': [
        'tall frozen waterfall of pale blue ice flowing down a cliff face, solid glossy ice columns and icicles, snow on top edge, frozen pool of ice at the bottom, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
    ]},
    'k5_natur': {'size': 32, 'items': [
        'small ice flower with glowing pale blue crystal petals in snow, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'frost flower cluster with white and light blue icy petals, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'small snowy berry bush with red berries and white snow on top, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'snow covered holly shrub with red berries, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'grey rock half buried in snow, only top showing with snow cap, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'small mossy boulder half sunk in snow drift, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
    ]},
    'k5_findling': {'size': 64, 'items': [
        'large grey granite boulder half buried in a snow drift, thick snow cap on top, a little moss, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
    ]},
    'k5_klein': {'size': 32, 'items': [
        'tuft of frosted grass sticking out of snow', 'small snow covered pebble', 'tiny ice crystal',
        'small frozen twig', 'tiny blue frost flower', 'small snow pile', 'small grey rock with snow cap',
        'animal footprints in snow', 'small icicle on the ground', 'frozen fish', 'small white bone in snow',
        'pine cone with frost',
    ]},
}

OBJEKTGRUPPEN_K6 = {
    'k6_brunnen': {'size': 240, 'items': [
        'gigantic ornate three tier stone fountain with water spraying high from the top, wide round basin, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
    ]},
    'k6_portal': {'size': 240, 'items': [
        'giant ancient stone ring portal standing upright on a wide stone base with steps, glowing cyan runes around the ring, swirling blue energy inside, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
    ]},
    'k6_datenbaum': {'size': 240, 'items': [
        'giant digital tree with a huge glowing cyan and green pixelated crown made of data blocks, thick trunk with circuit lines, roots, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
    ]},
    'k6_stand': {'size': 64, 'items': [
        'small wooden market stall with a striped pink awning and fruit baskets on the counter, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
    ]},
    'k6_front_gebaeude': {'size': 128, 'items': [
        'huge old wooden CRT television on a stone pedestal, screen is a glowing swirling cyan portal you can walk through, two antennas on top, perfectly straight front elevation view, symmetric, facade facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, like a classic 2D handheld RPG town building',
        'cozy log cabin with a red tiled roof, chimney, wooden door in the middle, two windows with flowers, perfectly straight front elevation view, symmetric, facade facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, like a classic 2D handheld RPG town building',
        'small workshop house of rusty metal plates with a large rusty cogwheel on the facade, door in the middle, chimney pipe, perfectly straight front elevation view, symmetric, facade facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, like a classic 2D handheld RPG town building',
        'seaside blacksmith forge house with a big blue and white turtle shell shaped roof, stone walls with shells and coral, anchor above the door, glowing furnace window, perfectly straight front elevation view, symmetric, facade facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, like a classic 2D handheld RPG town building',
    ]},
    'k6_front_gross': {'size': 128, 'items': [
        'small cozy nursery house with a pastel pink roof, egg shaped windows, door in the middle, perfectly straight front elevation view, symmetric, facade facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, like a classic 2D handheld RPG town building',
        'giant ancient stone ring portal standing upright on a stone base, glowing cyan runes around the ring, swirling blue energy inside, perfectly straight front elevation view, symmetric, facade facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, like a classic 2D handheld RPG town building',
        'gigantic ornate three tier stone fountain with water spraying from the top, round basin, perfectly straight front elevation view, symmetric, facade facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, like a classic 2D handheld RPG town building',
        'wooden market stall with a striped pink awning, perfectly straight front elevation view, symmetric, facade facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, like a classic 2D handheld RPG town building',
    ]},
    'k6_front_mittel': {'size': 64, 'items': [
        'small wooden children slide, perfectly straight front elevation view, symmetric, facade facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, like a classic 2D handheld RPG town building', 'wooden sandbox with a toy bucket, perfectly straight front elevation view, symmetric, facade facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, like a classic 2D handheld RPG town building', 'satellite dish on a pole, perfectly straight front elevation view, symmetric, facade facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, like a classic 2D handheld RPG town building',
        'big cable spool with blue and red cables, perfectly straight front elevation view, symmetric, facade facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, like a classic 2D handheld RPG town building', 'wooden playground swing, perfectly straight front elevation view, symmetric, facade facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, like a classic 2D handheld RPG town building', 'server rack with blinking blue lights, perfectly straight front elevation view, symmetric, facade facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, like a classic 2D handheld RPG town building',
        'holographic computer terminal, perfectly straight front elevation view, symmetric, facade facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, like a classic 2D handheld RPG town building', 'data pillar emitting floating cyan pixel cubes, perfectly straight front elevation view, symmetric, facade facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, like a classic 2D handheld RPG town building',
        'wooden sign board, perfectly straight front elevation view, symmetric, facade facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, like a classic 2D handheld RPG town building', 'large spotted monster egg, perfectly straight front elevation view, symmetric, facade facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, like a classic 2D handheld RPG town building', 'large striped egg, perfectly straight front elevation view, symmetric, facade facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, like a classic 2D handheld RPG town building', 'egg in a straw nest, perfectly straight front elevation view, symmetric, facade facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, like a classic 2D handheld RPG town building',
        'rusty gear pile with scrap, perfectly straight front elevation view, symmetric, facade facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, like a classic 2D handheld RPG town building', 'small rusty cogwheel, perfectly straight front elevation view, symmetric, facade facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, like a classic 2D handheld RPG town building', 'stack of scrap metal pipes, perfectly straight front elevation view, symmetric, facade facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, like a classic 2D handheld RPG town building', 'wooden crate, perfectly straight front elevation view, symmetric, facade facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, like a classic 2D handheld RPG town building',
    ]},
    'k6_gebaeude': {'size': 128, 'items': [
        'huge old wooden CRT television set standing on a stone pedestal, the screen is a glowing swirling cyan portal you can walk through, two antennas on top, knobs on the side, front view',
        'cozy log cabin with a red tiled roof, small chimney with smoke, wooden door, window with flowers, front view',
        'small workshop house made of rusty metal plates with a large rusty cogwheel on the wall, scrap metal and gears piled beside it, chimney, front view',
        'seaside blacksmith forge house shaped like a big turtle shell roof in blue and white, stone walls with shells and coral, glowing furnace, anvil and giant hammer in front, anchor decoration, front view',
    ]},
    'k6_gross': {'size': 160, 'items': [
        'giant ancient stone ring portal standing upright on a round stone platform, glowing cyan runes around the ring, shimmering blue energy inside the ring, front view',
        'gigantic ornate three tier stone fountain with water spraying from the top, round basin, front view',
        'giant digital tree with a glowing cyan and green pixelated crown, bark with circuit lines, front view',
        'small cozy nursery house with a pastel roof and egg shaped windows, front view',
    ]},
    'k6_mittel': {'size': 64, 'items': [
        'large spotted digital monster egg, white with colorful spots', 'large striped egg, cream with blue stripes',
        'egg in a small straw nest', 'wooden playground swing', 'small wooden slide for children', 'sandbox with a toy bucket',
        'server rack terminal with blinking blue lights', 'holographic computer terminal with a glowing screen',
        'data pillar emitting floating cyan pixel cubes', 'big cable spool with blue and red cables', 'satellite dish on a small pole',
        'wooden market stall with a striped pink awning', 'wooden fence section, horizontal', 'wooden fence post',
        'stack of rusty gears and scrap', 'wooden sign board',
    ]},
}

OBJEKTGRUPPEN_K7 = {
    'k7_turm': {'size': 160, 'items': [
        'huge black stone tower lying fallen on its side on the ground, broken in the middle, cracked dark obsidian blocks, a few glowing purple runes, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'fallen black stone tower segment lying on the ground, round broken end with rubble, dark obsidian, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'tilted half sunken black stone tower ruin leaning to the side, cracked, moss, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'large japanese black pine tree with layered cloud shaped green crowns and a twisted trunk, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
    ]},
    'k7_neu': {'size': 64, 'items': [
        'japanese black pine tree with cloud shaped green crown layers, twisted trunk, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'snow covered fir tree, dark green with white snow layers, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'small round green bush, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style', 'small flowering azalea bush with pink flowers, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'digital plant sprout with glowing cyan pixel leaves, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style', 'digital cabbage made of glowing green pixel cubes, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'digital pumpkin made of glowing orange voxel cubes, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style', 'data crop stalk with glowing blue bulbs, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'digital carrot top with neon green pixel leaves sticking out of soil, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style', 'glowing circuit flower with cyan petals, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'small digital tree sapling with pixel cube leaves, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style', 'cluster of glowing data mushrooms, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'stone japanese lantern toro, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style', 'red paper lantern hanging on a wooden post facing left, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'small grey stone fragment floating, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style', 'broken stone pillar with moss, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
    ]},
    'k7_obst': {'size': 64, 'items': [
        'ripe orange pumpkin growing on green vine leaves, its skin covered with thin glowing cyan circuit lines and tiny pixel squares, digital crop, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'green cabbage head growing from the soil, leaves with glowing cyan circuit vein lines, digital crop, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'tomato plant on a small wooden stake with round red tomatoes that glow like digital pixel cubes, cyan data sparkles, digital crop, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'corn plant with tall green leaves and a golden corn cob made of glowing yellow pixel cubes, digital crop, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'row of carrot greens with an orange carrot top showing glowing cyan circuit pattern, digital crop, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'strawberry bush with red strawberries made of glowing pixel cubes, cyan data sparkles, digital crop, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'eggplant plant with purple eggplants covered in glowing cyan circuit lines, digital crop, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'watermelon on green vine leaves, striped rind with glowing cyan circuit lines, digital crop, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'small apple fruit tree with round leafy green crown and red apples glowing like digital pixel cubes, digital fruit tree, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'small orange fruit tree with round leafy crown and oranges glowing with cyan circuit lines, digital fruit tree, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
    ]},
    'k7_obst2': {'size': 64, 'items': [
        'ripe orange pumpkin on green vine leaves, farm crop, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'green cabbage head growing from the soil, farm crop, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'tomato plant on a small wooden stake with ripe red tomatoes, farm crop, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'corn plant with tall green leaves and yellow corn cobs, farm crop, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'carrot greens with orange carrot tops in the soil, farm crop, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'small strawberry plant with red strawberries, farm crop, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'eggplant plant with purple eggplants, farm crop, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'round green striped watermelon on vine leaves, farm crop, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'white onions with green shoots in the soil, farm crop, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'small blueberry bush with blue berries, farm crop, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'golden ripe wheat bundle growing, farm crop, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
    ]},
    'k7_nadel': {'size': 128, 'items': [
        'tall jagged grey blue rock spire with green moss patches rising directly out of the grass, no platform, no slab, a few small rocks and grass tufts around its foot, no clouds, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
    ]},
    'k7_azul_gross': {'size': 128, 'items': [
        'majestic azure blue eastern dragon statue coiled around a tall white jade pillar, blue scales, white mane, golden horns, a ring of glowing amber orbs around its body, standing on a white stone altar platform with steps, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'blue tiled chinese paifang shrine gate with white stone pillars, golden ornaments and a blue dragon emblem on top, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
    ]},
    'k7_azul': {'size': 64, 'items': [
        'white stone pedestal holding a glowing amber energy orb, golden ring, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'azure blue silk banner on a white pole with a golden dragon emblem, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'blue stone lantern with golden roof cap and glowing amber light inside, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'large pale blue crystal with small lightning bolts inside, on a white rock, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'round bronze incense cauldron with blue dragon handles and gentle smoke, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'small white cloud shaped stone with blue swirl carvings, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
    ]},
    'k7_deko_gras': {'size': 32, 'items': [
        'small tuft of short green grass, front view, flat orthographic, classic 2D handheld RPG style, small ground decoration',
        'tall wild grass tuft, front view, flat orthographic, classic 2D handheld RPG style, small ground decoration',
        'clump of clover leaves, front view, flat orthographic, classic 2D handheld RPG style, small ground decoration',
        'small fern sprout, front view, flat orthographic, classic 2D handheld RPG style, small ground decoration',
        'dandelion with yellow flower, front view, flat orthographic, classic 2D handheld RPG style, small ground decoration',
        'white daisy flowers in grass, front view, flat orthographic, classic 2D handheld RPG style, small ground decoration',
        'purple violets cluster, front view, flat orthographic, classic 2D handheld RPG style, small ground decoration',
        'small red poppy flowers, front view, flat orthographic, classic 2D handheld RPG style, small ground decoration',
        'tiny blue forget-me-not flowers, front view, flat orthographic, classic 2D handheld RPG style, small ground decoration',
        'lavender sprigs, front view, flat orthographic, classic 2D handheld RPG style, small ground decoration',
        'small mushroom pair in grass, front view, flat orthographic, classic 2D handheld RPG style, small ground decoration',
        'leafy weed tuft, front view, flat orthographic, classic 2D handheld RPG style, small ground decoration',
        'small green shrub sprout, front view, flat orthographic, classic 2D handheld RPG style, small ground decoration',
        'yellow buttercup cluster, front view, flat orthographic, classic 2D handheld RPG style, small ground decoration',
        'orange marigold flowers, front view, flat orthographic, classic 2D handheld RPG style, small ground decoration',
        'grass tuft with tiny white flowers, front view, flat orthographic, classic 2D handheld RPG style, small ground decoration',
    ]},
    'k7_deko_stein': {'size': 32, 'items': [
        'small grey pebbles cluster, front view, flat orthographic, classic 2D handheld RPG style, small ground decoration',
        'flat grey stone with moss, front view, flat orthographic, classic 2D handheld RPG style, small ground decoration',
        'cracked rock chunk, front view, flat orthographic, classic 2D handheld RPG style, small ground decoration',
        'small mossy boulder, front view, flat orthographic, classic 2D handheld RPG style, small ground decoration',
        'rock with lichen spots, front view, flat orthographic, classic 2D handheld RPG style, small ground decoration',
        'pile of small rocks, front view, flat orthographic, classic 2D handheld RPG style, small ground decoration',
        'stone with a tuft of grass growing beside, front view, flat orthographic, classic 2D handheld RPG style, small ground decoration',
        'grey gravel patch, front view, flat orthographic, classic 2D handheld RPG style, small ground decoration',
        'small pointed rock, front view, flat orthographic, classic 2D handheld RPG style, small ground decoration',
        'two round stones, front view, flat orthographic, classic 2D handheld RPG style, small ground decoration',
        'rock with small fern, front view, flat orthographic, classic 2D handheld RPG style, small ground decoration',
        'broken stone slab piece, front view, flat orthographic, classic 2D handheld RPG style, small ground decoration',
        'dark slate shard, front view, flat orthographic, classic 2D handheld RPG style, small ground decoration',
        'stone with tiny yellow flowers, front view, flat orthographic, classic 2D handheld RPG style, small ground decoration',
        'mossy pebble trio, front view, flat orthographic, classic 2D handheld RPG style, small ground decoration',
        'rough granite chunk, front view, flat orthographic, classic 2D handheld RPG style, small ground decoration',
    ]},
    'k7_deko_wueste': {'size': 32, 'items': [
        'small dry desert grass tuft, front view, flat orthographic, classic 2D handheld RPG style, small ground decoration',
        'small round cactus, front view, flat orthographic, classic 2D handheld RPG style, small ground decoration',
        'tumbleweed, front view, flat orthographic, classic 2D handheld RPG style, small ground decoration',
        'sun bleached small bone, front view, flat orthographic, classic 2D handheld RPG style, small ground decoration',
        'sandstone pebbles, front view, flat orthographic, classic 2D handheld RPG style, small ground decoration',
        'dry thorny shrub, front view, flat orthographic, classic 2D handheld RPG style, small ground decoration',
        'desert succulent rosette, front view, flat orthographic, classic 2D handheld RPG style, small ground decoration',
        'small barrel cactus with pink flower, front view, flat orthographic, classic 2D handheld RPG style, small ground decoration',
        'cracked sandstone chunk, front view, flat orthographic, classic 2D handheld RPG style, small ground decoration',
        'dry twig, front view, flat orthographic, classic 2D handheld RPG style, small ground decoration',
        'golden dry grass clump, front view, flat orthographic, classic 2D handheld RPG style, small ground decoration',
        'small agave plant, front view, flat orthographic, classic 2D handheld RPG style, small ground decoration',
        'sand ripple stone, front view, flat orthographic, classic 2D handheld RPG style, small ground decoration',
        'desert flower orange, front view, flat orthographic, classic 2D handheld RPG style, small ground decoration',
        'small skull rock, front view, flat orthographic, classic 2D handheld RPG style, small ground decoration',
        'pebble cluster tan, front view, flat orthographic, classic 2D handheld RPG style, small ground decoration',
    ]},
    'k7_deko_schnee': {'size': 32, 'items': [
        'snow covered grass tuft, front view, flat orthographic, classic 2D handheld RPG style, small ground decoration',
        'frosted fern, front view, flat orthographic, classic 2D handheld RPG style, small ground decoration',
        'small snowdrift with grass, front view, flat orthographic, classic 2D handheld RPG style, small ground decoration',
        'snow covered small rock, front view, flat orthographic, classic 2D handheld RPG style, small ground decoration',
        'icy crystal shard in snow, front view, flat orthographic, classic 2D handheld RPG style, small ground decoration',
        'white snowdrop flowers, front view, flat orthographic, classic 2D handheld RPG style, small ground decoration',
        'frozen berry bush sprout, front view, flat orthographic, classic 2D handheld RPG style, small ground decoration',
        'frosty twig, front view, flat orthographic, classic 2D handheld RPG style, small ground decoration',
        'snow covered pebbles, front view, flat orthographic, classic 2D handheld RPG style, small ground decoration',
        'pale blue winter flower, front view, flat orthographic, classic 2D handheld RPG style, small ground decoration',
        'icicle tuft, front view, flat orthographic, classic 2D handheld RPG style, small ground decoration',
        'snow covered tiny pine sapling, front view, flat orthographic, classic 2D handheld RPG style, small ground decoration',
        'frosted clover, front view, flat orthographic, classic 2D handheld RPG style, small ground decoration',
        'small snow mound with stone, front view, flat orthographic, classic 2D handheld RPG style, small ground decoration',
        'winter heather pink flowers in snow, front view, flat orthographic, classic 2D handheld RPG style, small ground decoration',
        'frozen dry grass, front view, flat orthographic, classic 2D handheld RPG style, small ground decoration',
    ]},
    'k7_bambus': {'size': 64, 'items': [
        'cluster of green bamboo stalks with leaves, front view, flat orthographic, classic 2D handheld RPG style, small ground decoration',
        'cluster of bamboo stalks covered with snow on leaves and tops, front view, flat orthographic, classic 2D handheld RPG style, small ground decoration',
        'small bamboo clump of three stalks, front view, flat orthographic, classic 2D handheld RPG style, small ground decoration',
        'small snowy bamboo clump of three stalks with snow caps, front view, flat orthographic, classic 2D handheld RPG style, small ground decoration',
    ]},
    'k7_kuwaga': {'size': 128, 'items': [
        'giant ancient jungle tree with hanging vines, its trunk and big roots covered in glossy dark red stag beetle armor plates, two huge curved red pincer shaped branches rising from the top of the crown like stag beetle mandibles, sharp claw like roots, green leafy crown, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'massive jungle tree with a thick trunk shaped like a red armored stag beetle body with segmented glossy shell plates, crown framed by two giant curved serrated mandible branches, dangling green vines, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
    ]},
    'k7_pagode': {'size': 240, 'items': [
        'three story asian pagoda temple with dark blue curved tiled roofs, red wooden walls and pillars, golden ornaments, stone base with steps, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
    ]},
    'k7_gross': {'size': 128, 'items': [
        'golden dragon shrine altar on a grey stone platform with steps, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'red japanese torii gate, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'small wooden pavilion gazebo with a dark teal curved roof and red pillars, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'tall jagged grey rock spire with moss rising out of clouds, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
    ]},
    'k7_mittel': {'size': 64, 'items': [
        'stone japanese lantern toro, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style', 'red paper lantern hanging on a wooden post, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'tall glowing teal crystal obelisk on a stone pedestal, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style', 'cluster of teal crystals growing from a rock, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'small bonsai pine tree with a flat windswept crown, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style', 'bamboo cluster, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'snow covered pine tree, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style', 'snow covered grey boulder, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style', 'grey mossy boulder, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'small stone incense burner, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style', 'wooden prayer bench, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style', 'small stone buddha statue, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'purple glowing swirling vortex portal, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style', 'broken dark stone pillar rubble with purple crystals, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'red wooden fence segment, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style', 'stone well, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
    ]},
}

OBJEKTGRUPPEN_K3 = {
    'k3_palmen_a': {'size': 96, 'items': [
        'tall date palm tree with a slightly curved ringed trunk and a full crown of long green fronds, clusters of orange dates, perfectly straight front elevation view, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'tall straight coconut palm tree with a lush crown of fronds and a few coconuts, perfectly straight front elevation view, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'leaning palm tree with a curved trunk bending to the right, big drooping fronds, perfectly straight front elevation view, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'group of two palm trees of different heights growing from one base, perfectly straight front elevation view, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
    ]},
    'k3_palmen_b': {'size': 96, 'items': [
        'group of three palm trees, tall middle one, two smaller beside it, perfectly straight front elevation view, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'young short palm tree with a thick trunk and wide fronds, perfectly straight front elevation view, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'fan palm tree with round fan shaped leaves on a straight trunk, perfectly straight front elevation view, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'tall slender palm tree with a small crown of fronds high up, perfectly straight front elevation view, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
    ]},
    'k3_palmen_c': {'size': 96, 'items': [
        'bushy desert palm with fronds down to the ground, no visible trunk, perfectly straight front elevation view, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'old palm tree with some dry brown fronds hanging below the green crown, perfectly straight front elevation view, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'palm tree with a double bent trunk and a dense crown, perfectly straight front elevation view, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'small palm tree cluster with dry grass at its base, perfectly straight front elevation view, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
    ]},
    'k3_grab': {'size': 96, 'items': [
        'small sandstone tomb house with a low pyramid shaped roof, dark arched entrance with an iron gate, hieroglyph carvings, seen from the front and slightly above so the roof surfaces are visible, like a small building in a classic 2D handheld RPG town, facade facing the camera, symmetric, not isometric',
        'small desert crypt house of sandstone bricks with a sloped tiled roof and a barred arched doorway, seen from the front and slightly above so the roof surfaces are visible, like a small building in a classic 2D handheld RPG town, facade facing the camera, symmetric, not isometric',
        'small egyptian style shrine house with a stepped sandstone roof and a dark arched iron gate in front, seen from the front and slightly above so the roof surfaces are visible, like a small building in a classic 2D handheld RPG town, facade facing the camera, symmetric, not isometric',
        'small mud brick tomb house with a domed roof and an arched iron gate, seen from the front and slightly above so the roof surfaces are visible, like a small building in a classic 2D handheld RPG town, facade facing the camera, symmetric, not isometric',
    ]},
    'k3_klein': {'size': 32, 'items': [
        'small green saguaro cactus', 'tall green saguaro cactus with two arms', 'small round barrel cactus', 'prickly pear cactus',
        'dry desert bush', 'small dry grass tuft', 'animal skull', 'scattered bones', 'small sandstone rock', 'two small desert rocks',
        'clay water jar', 'large clay amphora', 'burlap sack', 'wooden crate', 'wooden barrel', 'standing torch with flame',
        'campfire with stones', 'speaker on a pole, dark grey', 'red banner on a pole with a yellow emblem', 'wooden signpost',
        'broken sandstone column stump', 'sandstone rubble', 'wooden fence post', 'small satellite dish on a short pole',
        'dark stone scarab beetle', 'small palm sapling', 'tumbleweed', 'small sand rock with crack', 'clay pot pair',
        'stone well with a wooden roller', 'loudspeaker box', 'oil lamp on a post',
    ]},
    'k3_mittel': {'size': 64, 'items': [
        'tall desert palm tree with a curved trunk and big fronds', 'desert palm tree, straight trunk', 'twin palm trees',
        'tall sandstone column with capital, intact', 'broken sandstone column, half height', 'pile of sandstone ruin blocks',
        'large animal rib cage skeleton half buried', 'big sandstone boulder', 'stone well with wooden roof',
        'market stall with red and white striped awning, front view', 'small stone tomb gate with iron bars',
        'stone obelisk with a glowing cyan crystal on a pedestal', 'dark scarab shaped stone robot',
        'tall loudspeaker stack', 'DJ table with turntables, front view', 'red tent, front view',
    ]},
    'k3_gross': {'size': 84, 'items': [
        'adobe dome hut with arched doorway and a striped awning, front view',
        'adobe dome hut, round clay house with wooden door, front view',
        'flat roof adobe house with wooden beams, two windows and a door, front view',
        'flat roof clay house with a wooden balcony rail, front view',
        'red canvas tent with open flap, front view', 'red canvas tent, closed, front view',
        'red and white tour bus, side view facing right, orthographic',
        'concert stage with a red banner screen, two big speakers and a DJ desk, front view',
        'radio antenna tower: steel lattice mast with a satellite dish and small server box, front view',
        'tall lattice antenna mast with two dishes and antennas, front view',
        'wooden pavilion gazebo with red tiled pyramid roof and a bell, front view',
        'sandstone arch gate with two towers, front view',
        'big dark stone scarab robot with a glowing eye', 'stack of server racks with blinking lights, front view',
        'sandstone ruin wall fragment', 'large desert rock formation',
    ]},
    'k3_gross2': {'size': 128, 'items': [
        'tall steel lattice radio tower with a large satellite dish, antennas and a server box at its base, front view',
        'tall steel lattice communication mast with three dish antennas and a red warning light on top, front view',
        'large concert stage with a big red LED screen, truss frame, two tall speaker stacks and a DJ desk, front view',
        'huge sandy desert rock formation, layered sandstone with sand drifts at its base, front view',
    ]},
    'k3_mittel2': {'size': 64, 'items': [
        'tall loudspeaker pole with two horn speakers on top, front view',
        'tall concert speaker tower, black, front view',
        'large sandy rock formation with layered sandstone and sand piled at the base',
        'big rounded sandstone boulder cluster half buried in sand',
        'wide flat sandstone rock outcrop',
        'tall sandstone rock spire',
        'big saguaro cactus with pink flowers on top',
        'large barrel cactus cluster with pink blossoms',
        'prickly pear cactus with pink flowers',
        'flowering desert shrub with pink blossoms',
        'sandstone rock with a small cactus',
        'two sandstone boulders',
        'tall saguaro cactus with three arms and pink flowers',
        'cholla cactus with pink flowers',
        'medium sandy rock',
        'flat layered sandstone rock',
    ]},
    'k3_blueten': {'size': 32, 'items': [
        'small saguaro cactus with pink flowers', 'barrel cactus with a pink blossom', 'prickly pear cactus with pink flowers',
        'small cactus cluster with pink blossoms', 'tall thin cactus with a pink flower', 'round cactus with three pink flowers',
    ]},
    'k3_tor': {'size': 144, 'items': [
        'grand sandstone colosseum arena entrance gate, wide tall round archway with open dark passage, two massive square towers with crenellations on both sides, red banners hanging from the towers, carved stone details, front view, orthographic',
    ]},
    'k3_mittel3': {'size': 64, 'items': [
        'tall sandstone obelisk with glowing cyan hieroglyphs, on a stepped stone base, front view',
        'tall red banner flag on a wooden pole with a golden emblem, front view',
        'stage monitor speaker stack, two black speaker boxes on top of each other, front view',
        'tall sandstone obelisk with a golden tip, front view',
    ]},
    'k3_baeume': {'size': 64, 'items': [
        'small flat-topped acacia tree with green canopy, desert tree, front view',
        'joshua tree with spiky green leaf clusters, front view',
        'small olive tree with silvery green leaves, front view',
        'bushy desert shrub tree with small green leaves, front view',
    ]},
    'k3_pyramide2': {'size': 240, 'items': [
        'classic egyptian pyramid with four smooth triangular sloped sides made of sandstone blocks, pointed apex, small dark arched entrance at the bottom center, a small glowing cyan eye emblem near the apex, light side on the left, shaded side on the right, front view, orthographic',
    ]},
    'k3_pyramide': {'size': 240, 'items': [
        'large sandstone pyramid with stepped blocks, a dark entrance door at the bottom center and a glowing eye emblem near the top, front view, orthographic',
    ]},
}


OUT_K8 = os.path.join(ROOT, 'assets', 'objekte', 'karte08')
STIL_K8 = ("Top-down RPG map object for a dark gothic graveyard land in polished handheld monster-collecting RPG pixel "
           "art: colored dark outline (darkest shade of the object's own hue, never pure black), light from the upper "
           "left, hue-shifted shading (shadows toward deep violet, highlights toward pale bone), muted gloomy colors, "
           "clean readable shapes, no noise, no dithering, transparent background, no ground, no cast shadow. "
           "Straight front view, orthographic, not isometric.")
PALETTE_K8 = [
    # Stein violett-grau
    '#1c1a26', '#2a2838', '#3a384c', '#4e4c62', '#64627a', '#7e7c94', '#9a98ae', '#bab8cc',
    # Totholz / Erde
    '#2a1e1a', '#3e2c22', '#56402e', '#70563c', '#8c6e4c', '#a88a62',
    # Moos / Gras gedeckt
    '#2a3424', '#3c4a2e', '#52603a', '#6a7848',
    # Knochen
    '#b8ae98', '#d6ceb8', '#efe8d6',
    # Akzente: Violett, Blutrot, Geistergruen, Kerzenlicht
    '#4a2a5e', '#6e3a8a', '#9a5ab8', '#7a1420', '#b82432', '#ff4a4a', '#3a9a6a', '#7af0a8', '#ffb84a', '#fff0a0',
]
OBJEKTGRUPPEN_K8 = {
    'k8_schloss': {'size': 192, 'items': [
        'huge dark gothic castle of black stone with tall pointed spires and towers, narrow glowing red stained glass windows, large pointed arch gate in the middle, wide stone stairs in front, sinister demon lord fortress, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
    ]},
    'k8_gross': {'size': 128, 'items': [
        'gothic stone mausoleum with a pointed roof, a stone cross on top, pillars and a dark arched iron door, pale weathered limestone, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'small dark stone crypt with a slate roof and a small barred door, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'ruined old crypt, cracked grey stone walls, broken roof, moss, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'big twisted dead tree with gnarled bare black branches and a hollow trunk, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
    ]},
    'k8_baeume': {'size': 80, 'items': [
        'bare dead tree with twisted dark grey-violet branches, no leaves, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'withered dead tree with brown bark and crooked bare branches, no leaves, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'spooky leafless tree with long thin claw-like branches, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'small dead sapling, bare crooked twigs, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
    ]},
    'k8_mittel': {'size': 64, 'items': [
        'rounded grey tombstone with a carved cross, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style', 'stone cross gravestone, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'celtic cross gravestone with moss, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style', 'broken cracked tombstone, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'small stone obelisk grave marker, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style', 'iron lantern post with a ghostly green flame, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'tattered purple banner flag on a black pole, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style', 'broken grey stone pillar, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'dark violet boulder, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style', 'pile of skulls and bones, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'wrought iron graveyard fence segment with spikes, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style', 'old wooden coffin standing upright, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'stone gargoyle statue on a pedestal, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style', 'cluster of melting candles, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'dead thorny bush, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style', 'wooden signpost with a skull, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
    ]},
    'k9_portal2': {'size': 128, 'items': [
        'gothic dark stone portal arch with a swirling purple vortex inside, eight glowing gemstone crystals set into the arch frame in these colors: orange, blue, red, purple, green, grey, yellow and pink, no symbols, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'ornate dark stone portal with a swirling violet vortex, eight tall pointed crystals standing around the frame like a crown, colored orange, blue, red, purple, green, grey, yellow and pink, softly glowing, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'gothic dark stone portal arch with a swirling purple vortex, eight small blank rectangular cards in slots along the arch, each card a plain single color: orange, blue, red, purple, green, grey, yellow and pink, no symbols, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'dark stone portal frame with a swirling purple vortex, eight floating colored tag cards hanging on thin chains around the arch, colors orange, blue, red, purple, green, grey, yellow and pink, plain cards without symbols, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
    ]},
    'k9_portal': {'size': 128, 'items': [
        'ornate dark stone portal arch with a swirling purple vortex inside, eight small glowing tag-shaped plaques set into the frame, each with an original simple symbol (sun, heart, star, droplet, flame, leaf, light ray, gem) in different colors, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'tall gothic portal gate with a swirling dark violet vortex, ring of eight colorful glowing emblem stones around the arch, each emblem a simple original rune symbol, crystal keystone on top, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'ancient digital portal frame of dark stone with glowing cyan circuit lines, swirling purple data vortex inside, eight small colored crest plaques along the arch, original symbols, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'round gothic portal with a swirling purple vortex, stone frame with eight round glowing medallions in eight colors (orange, blue, red, purple, yellow, grey, green, pink) each with a simple original symbol, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
    ]},
    'k9_tor3': {'size': 128, 'items': [
        'large inner gothic castle doorway arch in dark grey stone, tall wide open passage with no door (empty, transparent inside), ornate pointed arch with a violet inner arch and a red bat crest above, slim columns on both sides, about as wide as a 3 tile carpet plus columns, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
    ]},
    'k9_tor2': {'size': 96, 'items': [
        'gothic castle gatehouse in a dark blue-grey stone brick wall, tall pointed archway with an OPEN EMPTY passage (nothing inside the arch, transparent), raised iron portcullis at the top of the arch, bat emblem keystone, two small spires, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'gothic castle main gate tower, dark slate-grey stone bricks, wide pointed arch passage completely open and empty, portcullis pulled up, two wall torches, battlements on top with a small bat statue, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'inner gothic castle doorway arch in dark grey stone, open passage with no door, ornate pointed arch with a red bat crest above, thin columns on both sides, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'gothic stone archway gate with dark grey bricks, gold trim, open empty arch passage, iron portcullis spikes visible at the top, small red banner on each side, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
    ]},
    'k9_banner': {'size': 32, 'items': [
        'long hanging gothic castle banner, deep red cloth with a black bat emblem, gold trim, hanging from a short iron rod, pointed swallowtail bottom, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'long hanging gothic castle banner, dark purple cloth with a silver crescent moon, gold trim, iron rod, pointed bottom, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'long hanging gothic castle banner, black cloth with a red bat and gold border, iron rod, swallowtail bottom, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'long hanging gothic castle banner, crimson cloth with a gold crown and bat wings crest, iron rod, pointed bottom, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
    ]},
    'k9_turm': {'size': 64, 'items': [
        'small round castle watchtower on a wall, dark grey stone matching a gothic castle, conical dark slate roof, a small dark red pennant flag on top, narrow window, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'small round castle watchtower, dark blue-grey stone, pointed slate roof with a purple pennant flag, arrow slit window, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'small square gothic castle turret, dark grey stone, battlements, red flag with bat on a pole on top, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'small round castle watchtower with dark grey stone, cone roof, a black and red bat flag waving on top, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
    ]},
    'k9_einrichtung': {'size': 64, 'items': [
        'long gothic banquet table with a red tablecloth, silver plates, goblets and candles, seen slightly from above, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'tall dark wooden gothic dining chair with a red velvet seat, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'wide gothic bookshelf full of old books, skulls and candles, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'wooden reading lectern with a large open spellbook, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'round dark red carpet rug with a gold bat emblem, lying flat on the floor, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'small round castle watchtower on top of a wall, dark stone, conical slate roof, red banner, narrow window, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'stone wall pilaster column with a pointed gothic capital, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'dark wooden writing desk with a candle, quill and papers, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'tall stone fireplace with burning fire and a skull mantel, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'wooden barrel of wine with a tap, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'wine rack with bottles, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'dark velvet sofa with gold trim, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'stone stairs leading up to a throne dais with red carpet, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'tall bat-winged stone statue of a vampire lord, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'hanging iron chandelier with candles seen from below on the floor shadow, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'small side table with a skull and a candle, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
    ]},
    'k9_wand': {'size': 32, 'items': [
        'tall gothic arched stained glass window with a purple moon pattern, dark stone frame',
        'tall gothic arched stained glass window with a cyan pattern, dark stone frame',
        'tall gothic arched stained glass window with a red bat pattern, dark stone frame',
        'narrow castle arrow slit window',
        'iron wall torch sconce with a burning flame',
        'long red hanging wall banner with a black bat emblem',
        'gold framed portrait painting of a pale vampire lord',
        'small gold wall candle sconce with one candle',
        'stone wall shield crest with crossed swords',
        'iron wall chain with shackles',
        'small round stone wall vent',
        'wall mounted bat head trophy',
        'cobweb in a corner',
        'small purple wall lamp glowing',
        'wooden wall shelf with skulls and candles',
        'cracked wall mirror',
    ]},
    'k9_moebel': {'size': 64, 'items': [
        'tall dark gothic stone pillar with a carved capital and base, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'tall gold candelabra with three lit candles, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'upright black coffin with a gold cross, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'dark wooden church pew bench, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'large ornate gothic wall mirror with gold frame, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'tall gothic bookshelf with old books and skulls, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'stone brazier bowl with purple flames, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'blood red velvet throne with tall gothic back, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'stone pedestal with a glowing red crystal ball, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'dark suit of armor with a halberd, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'gothic treasure chest with gold trim, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'tall gothic grandfather clock, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'small round table with a red cloth and a wine goblet, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'stone gargoyle on a pedestal, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'wrought iron candle stand with many candles, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'large dark vase with dead roses, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
    ]},
    'k9_gross': {'size': 128, 'items': [
        'large gothic pipe organ with tall silver pipes and a dark wooden console, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'gothic altar table with a red velvet cloth, a black coffin on top and two candelabras, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'swirling purple portal in an ornate stone frame decorated with colored gems, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'round castle tower with a dark conical slate roof, red banner with bat emblem, stone bricks, seen from the front and slightly above so the roof is visible, classic 2D handheld RPG style, facing the camera, symmetric, not isometric',
    ]},
    'k9_tor': {'size': 96, 'items': [
        'gothic stone archway doorway with an open iron portcullis and a bat emblem keystone, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'castle main gate in a stone wall with a raised iron portcullis and two torches, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'heavy wooden drawbridge with iron chains, seen from above, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'small gothic stone doorway arch, open, dark inside, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
    ]},
    'k8_krypta': {'size': 128, 'items': [
        'small gothic crypt house of dark grey stone with a steep dark slate tiled roof, arched iron barred door in the middle, two narrow gothic windows, small stone cross on the roof ridge, seen from the front and slightly above so both slopes of the roof and the roof ridge are visible, like a house in a classic 2D handheld RPG town, facade facing the camera, symmetric, not isometric',
        'old ruined crypt house, cracked grey stone walls with moss, partly collapsed slate roof with broken beams, dark open doorway, seen from the front and slightly above so both slopes of the roof and the roof ridge are visible, like a house in a classic 2D handheld RPG town, facade facing the camera, symmetric, not isometric',
        'gothic mausoleum house of pale limestone with a steep slate roof, a stone cross on the ridge, two pillars beside a pointed arch iron door, seen from the front and slightly above so both slopes of the roof and the roof ridge are visible, like a house in a classic 2D handheld RPG town, facade facing the camera, symmetric, not isometric',
        'small family crypt house of mossy dark stone with a pointed slate roof, wooden door with iron fittings, lantern hook above the door, seen from the front and slightly above so both slopes of the roof and the roof ridge are visible, like a house in a classic 2D handheld RPG town, facade facing the camera, symmetric, not isometric',
    ]},
    'k8_krypta2': {'size': 128, 'items': [
        'small tomb house of pale weathered limestone with a steep dark slate roof, arched iron double door with two skull door knockers, moss on the walls, seen from the front and slightly above so both slopes of the roof and the roof ridge are visible, like a house in a classic 2D handheld RPG town, facade facing the camera, symmetric, not isometric',
        'ossuary chapel house of grey stone with a slate roof, skulls set into the wall above the arched door, seen from the front and slightly above so both slopes of the roof and the roof ridge are visible, like a house in a classic 2D handheld RPG town, facade facing the camera, symmetric, not isometric',
        'tiny gothic graveyard chapel with a small bell tower on the roof ridge, dark slate roof, pointed wooden door, seen from the front and slightly above so both slopes of the roof and the roof ridge are visible, like a house in a classic 2D handheld RPG town, facade facing the camera, symmetric, not isometric',
        'small crypt house of dark stone with a slate roof and a heavy iron gate, two small gargoyles on the roof corners, seen from the front and slightly above so both slopes of the roof and the roof ridge are visible, like a house in a classic 2D handheld RPG town, facade facing the camera, symmetric, not isometric',
    ]},
    'k8_kristall': {'size': 64, 'items': [
        'cluster of dark purple amethyst crystals growing out of a black rock, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'single tall pointed violet crystal spire on a small black rock base, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'wide cluster of many small purple crystals in black stone, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'two large purple crystals crossing each other on black rock, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'cracked black boulder with purple crystals breaking out of the crack, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'ring of purple crystals around a small dark stone, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'tall purple crystal cluster with a faint violet glow at the tips, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'broken purple crystal stump with shards lying around on black rock, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'dark violet crystal formation shaped like a crown on black rock, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'small purple crystal cluster with a skull half buried beside it, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'black rock pillar with purple crystals growing on its side, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'leaning purple crystal shards in a pile of black gravel, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'deep magenta and violet crystal cluster with dark outline on obsidian, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'three purple crystals of different heights in a row on black rock, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'purple crystal cluster overgrown with dead thorny vines, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'flat black slab with small purple crystals sprouting from it, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
    ]},
    'k8_kristall_klein': {'size': 32, 'items': [
        'tiny purple crystal shard on black rock',
        'small cluster of three purple crystals',
        'small glowing violet crystal in gravel',
        'tiny broken purple crystal pieces',
        'small purple crystal sprouting from a crack',
        'two small violet crystals on a black pebble',
        'small dark amethyst point',
        'tiny magenta crystal cluster',
    ]},
    'k8_fels': {'size': 64, 'items': [
        'jagged black rock spire, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style', 'cluster of dark purple crystals growing out of black rock, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'cracked dark boulder with a little moss, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style', 'heap of grey rock rubble, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'skeleton half buried in gravel, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style', 'dead thorny bush growing from a rock crack, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'tall pointed obsidian stalagmite, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style', 'fallen broken ancient stone pillar lying on the ground, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'old rusty sword stuck in a rock, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style', 'horned ram skull on a flat stone, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'glowing purple crystal shard in black rock, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style', 'flat dark slab rocks, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'pile of rocks with a dead branch, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style', 'black rock with a rusty iron chain, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'ancient dark runestone with carved glowing violet runes, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style', 'weathered stone gargoyle head lying in gravel, perfectly straight front elevation view, symmetric, facing the camera head-on, no side wall visible, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
    ]},
    'k8_fels_klein': {'size': 32, 'items': [
        'small black pebbles', 'small dark rock', 'tiny purple crystal', 'small bone in gravel', 'cracked small stone',
        'small grey rubble', 'dry dead twig on rock', 'tiny dead weed', 'small skull on gravel', 'two small dark stones',
        'tiny glowing violet mushroom', 'small flat stone',
    ]},
    'k8_klein': {'size': 32, 'items': [
        'white bone lying on the ground', 'small skull', 'cluster of small glowing purple mushrooms',
        'small brown toadstool', 'tuft of dry dead grass', 'small grey pebbles', 'single lit candle',
        'small dark twig', 'tiny wooden cross', 'small purple flower', 'crossed bones', 'small dark stone',
        'pale dry grass sprouts', 'broken small gravestone piece', 'black crow feather', 'small rib cage bones',
    ]},
}


STIL_K10 = ("Top-down RPG map object for a cheerful children's toy town in polished handheld monster-collecting RPG pixel "
            "art: colored dark outline (darkest shade of the object's own hue, never pure black), light from the upper left, "
            "soft pastel and bright toy colors, clean readable shapes, no noise, no dithering, transparent background, no "
            "ground, no cast shadow. Straight front view, orthographic, not isometric.")
PALETTE_K10 = ['#2a2a3a', '#4a4a5e', '#7a7a8e', '#b0b0c0', '#e8e8f0', '#ffffff', '#3a2418', '#6a4428', '#9a6a3a', '#c8945a',
               '#f0d8a8', '#fff2d0', '#2e6a2e', '#4a9a3a', '#78c050', '#a8e070', '#a02a2a', '#d84a3a', '#f07a5a', '#ff9a8a',
               '#2a4aa0', '#3a7ad8', '#6aa8f0', '#a8d0ff', '#6a3a9a', '#9a5ad0', '#c890f0', '#d06a9a', '#f09ac8', '#ffd0e8',
               '#e0a020', '#f8d040', '#fff080']
OBJEKTGRUPPEN_K10 = {
    'k10_haeuser': {'size': 128, 'items': [
        'cute toy house with two pointed orange tiled roofs, cream walls, blue shutters, small red door, seen from the front and slightly above so the roof surfaces and ridge are visible, like a house in a classic 2D handheld RPG town, facade facing the camera, symmetric, not isometric',
        'cute toy house with a blue round dome roof, cream walls, blue windows, small porch, seen from the front and slightly above so the roof surfaces and ridge are visible, like a house in a classic 2D handheld RPG town, facade facing the camera, symmetric, not isometric',
        'cute toy house with a big red tiled roof, cream walls, blue shutters, chimney, seen from the front and slightly above so the roof surfaces and ridge are visible, like a house in a classic 2D handheld RPG town, facade facing the camera, symmetric, not isometric',
        'cute toy house with a purple pointed roof and a small chimney, cream walls, blue shutters, seen from the front and slightly above so the roof surfaces and ridge are visible, like a house in a classic 2D handheld RPG town, facade facing the camera, symmetric, not isometric',
    ]},
    'k10_haeuser2': {'size': 128, 'items': [
        'toy apartment building like a small castle, blue-grey walls, purple crenellated roof with a gold star, many windows, seen from the front and slightly above so the roof surfaces and ridge are visible, like a house in a classic 2D handheld RPG town, facade facing the camera, symmetric, not isometric',
        'cute toy bakery with a pink striped awning and a cake sign, seen from the front and slightly above so the roof surfaces and ridge are visible, like a house in a classic 2D handheld RPG town, facade facing the camera, symmetric, not isometric',
        'cute toy shop with a yellow roof and a big teddy bear sign, seen from the front and slightly above so the roof surfaces and ridge are visible, like a house in a classic 2D handheld RPG town, facade facing the camera, symmetric, not isometric',
        'cute toy fire station with a red roof and a big garage door, seen from the front and slightly above so the roof surfaces and ridge are visible, like a house in a classic 2D handheld RPG town, facade facing the camera, symmetric, not isometric',
    ]},
    'k10_burg': {'size': 192, 'items': [
        'big pink toy castle front made of pink bricks, four tall round towers with red cone roofs and gold trim, big wooden arched double door in the middle, heart emblem above the door, small flags, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
    ]},
    'k10_bahnhof': {'size': 128, 'items': [
        'cute toy train station building with a red roof, cream walls, a big clock in the gable, blue doors, seen from the front and slightly above so the roof surfaces and ridge are visible, like a house in a classic 2D handheld RPG town, facade facing the camera, symmetric, not isometric',
        'cute toy steam locomotive, red and blue with gold details, seen from the side, facing right, perfectly straight front elevation view, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'cute toy train wagon carrying big letter blocks, red, seen from the side, perfectly straight front elevation view, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'tall wooden toy clock tower with a red roof and a big round clock, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
    ]},
    'k10_spielplatz': {'size': 64, 'items': [
        'red playground slide with a ladder, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'red playground swing set with two swings, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'playground seesaw, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'wooden park bench, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'round yellow street lamp on a thin post, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'blue mailbox on a post, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'red fire hydrant, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'small wooden fence segment painted white, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'stone fountain with blue water, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'toy soldier guard with a tall black hat and red coat, standing, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'stack of big colorful toy letter blocks, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'red and blue toy drum, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'big brown teddy bear sitting, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'small cute toy robot, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'small merry-go-round carousel, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'flower bed with tulips, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
    ]},
    'k10_baeume': {'size': 80, 'items': [
        'round pink cherry blossom tree, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'round green cartoon tree with a short trunk, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'small pink blossom tree, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'round green bush with small flowers, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
    ]},
    'k10_banner': {'size': 64, 'items': [
        'pink castle wall banner with a gold heart, hanging cloth from a short gold rod, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'light blue castle wall banner with a white star, hanging cloth from a short gold rod, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'tall arched castle window with light blue glass and a gold frame, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'round pink castle wall shield with a red heart, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'railway buffer stop, red and white striped, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'toy railway signal post with a red and a green lamp, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'round station clock on a tall post, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'small ticket booth kiosk with a pink striped roof, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'wooden platform bench with a red backrest, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'stack of wooden crates with toys, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'toy windmill with colorful blades, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'flower planter box with pink flowers, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'small bus stop sign with a little bench, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'toy traffic light on a pole, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'park trash bin painted green, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'small wooden dog house with a red roof, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
    ]},
    'k10_klein2': {'size': 32, 'items': [
        'small red fire hydrant', 'small blue mailbox', 'small round street sign on a pole', 'small flower pot with a red flower',
        'small yellow flowers', 'small blue flowers', 'small lollipop', 'small candy cane',
        'small green toy car', 'small yellow toy truck', 'small green trash bin', 'small tulips',
        'small toy soldier', 'small pink bush', 'small white picket fence piece', 'small stone path tile',
    ]},
    'k10_baeume2': {'size': 80, 'items': [
        'round lollipop tree with a pink and white swirl crown on a striped candy stick trunk, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'round toy tree made of a green ball on a straight brown stick trunk, like a wooden toy tree, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'cone shaped toy pine tree made of stacked green wooden rings, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'round gumdrop bush, glossy green with tiny sugar sparkles, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
    ]},
    'k10_gross1': {'size': 192, 'items': [
        'big tall wooden toy clock tower, red pointed tiled roof on top, big round white clock face with a gold rim and black hands, small balcony with railing below the clock, small red side roofs, cream walls with brown timber frame, small wooden double door at the bottom, stone base, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
    ]},
    'k10_gross2': {'size': 128, 'items': [
        'big merry-go-round carousel with a red and yellow striped round canopy, golden center pole, white and brown carousel horses on gold poles, round wooden base with gold trim, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'big playground tower with a blue pointed roof, yellow and green wooden tower, blue ladder on the left side, red and yellow slide going down on the right side, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
    ]},
    'k10_schloss': {'size': 256, 'items': [
        'big pink toy castle palace main keep made of pink bricks, tall central round tower with a red cone roof and gold trim, two smaller round side towers with red cone roofs, many arched windows with light blue glass, gold balcony, red heart emblem, small pink flags on the roof tips, seen from the front and slightly above so the roof surfaces are visible, like a castle in a classic 2D handheld RPG town, facade facing the camera, symmetric, not isometric',
    ]},
    'k10_schloss2': {'size': 128, 'items': [
        'long pink brick toy castle hall building with a red tiled roof, small arched windows, gold trim, chimney, seen from the front and slightly above so the roof surfaces are visible, like a castle in a classic 2D handheld RPG town, facade facing the camera, symmetric, not isometric',
        'pink brick toy castle chapel building with a red pointed roof and a round rose window with a heart, gold trim, seen from the front and slightly above so the roof surfaces are visible, like a castle in a classic 2D handheld RPG town, facade facing the camera, symmetric, not isometric',
        'tall round pink brick toy castle tower with a red cone roof, gold rings and narrow arched windows, small red flag on top, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'pink brick toy castle stable building with a red roof and wooden doors, gold trim, seen from the front and slightly above so the roof surfaces are visible, like a castle in a classic 2D handheld RPG town, facade facing the camera, symmetric, not isometric',
    ]},
    'k10_bahn': {'size': 128, 'items': [
        'cute toy railway water tower for steam trains, round red wooden tank on tall wooden legs, blue spout pipe, small ladder, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'cute toy railway signal box building with a red roof, cream walls, big windows on the upper floor, small stairs, seen from the front and slightly above so the roof surfaces are visible, like a building in a classic 2D handheld RPG town, facade facing the camera, symmetric, not isometric',
        'cute toy railway goods shed with a red roof, wooden sliding door and a small loading ramp with crates, seen from the front and slightly above so the roof surfaces are visible, like a building in a classic 2D handheld RPG town, facade facing the camera, symmetric, not isometric',
        'cute toy coal bunker for steam trains, wooden bin full of black coal with a small crane, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
    ]},
    'k10_bahn2': {'size': 64, 'items': [
        'red station luggage cart with suitcases, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style', 'stack of colorful toy suitcases, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style', 'two old milk cans, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'pile of mail sacks, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style', 'small red railway handcar on rails, side view, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style', 'railway switch lever with a red and white handle, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'wooden telegraph pole with wires, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style', 'red railway buffer stop, side view, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style', 'station name sign board on two posts, blank, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'two wooden barrels, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style', 'stack of wooden crates with toy letters, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style', 'red and white railway crossing barrier gate post, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'small blue railway worker toy figure with a lantern, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style', 'small pile of coal, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style', 'old station lantern on a post, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'wooden station bench with a red backrest, perfectly straight front elevation view, symmetric, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
    ]},
    'k10_prellbock': {'size': 64, 'items': [
        'small red toy railway buffer stop seen exactly from the side in profile: sturdy red wooden frame standing on the rail end, the round black buffer pads on the LEFT side facing left toward an arriving train, slanted support beams on the right, side view, profile view, flat orthographic, classic 2D handheld RPG style',
        'red and white striped railway buffer stop seen from the side in profile, a vertical bumper beam with two round buffers on the left facing left, triangular support behind it on the right, sitting on short rail ends, side view, flat orthographic, classic 2D handheld RPG style',
        'small toy railway end stop block seen from the side: a red wooden sleeper block with a yellow striped warning board standing upright, buffer facing left, side view, flat orthographic, classic 2D handheld RPG style',
        'cute toy railway buffer stop made of red painted wood, side view profile, upright post with a round black buffer facing left and a diagonal brace to the right, flat orthographic, classic 2D handheld RPG style',
    ]},
    'k10_klein': {'size': 32, 'items': [
        'small red toy car',
        'small blue toy car',
        'colorful beach ball',
        'wrapped gift box with a bow',
        'orange traffic cone',
        'wrapped candy',
        'small toy letter block',
        'spinning top toy',
        'small yellow rubber duck',
        'pink flowers',
        'small white daisy flowers',
        'small stones',
        'small grass tuft',
        'toy sailboat',
        'small toy airplane',
        'crayon',
    ]},
}

STIL_K11 = ("Top-down RPG map object for a dark cursed coast at a sea of darkness, in polished handheld monster-collecting RPG "
            "pixel art: colored dark outline (darkest shade of the object's own hue, never pure black), light from the upper "
            "left, desaturated gloomy colors with cold teal and violet accents, clean shapes, no noise, no dithering, "
            "transparent background, no ground, no cast shadow.")
PALETTE_K11 = ['#14161e', '#1e2230', '#2a3042', '#3a4256', '#4e5870', '#6a7690', '#8c98b0', '#b4bed0',
               '#2a1e2a', '#3e2a3e', '#5a3a5a', '#7a4e7a', '#a06aa0', '#1a3a40', '#245058', '#307078', '#40949a',
               '#5cb8b8', '#8adcd4', '#3a2a1e', '#5a4030', '#7a5a40', '#a07a54', '#c8a070', '#e8d0a0',
               '#7a1e2e', '#b03a4a', '#e06a80', '#f8a0b0', '#e8702a', '#f8b040', '#fff0a0', '#ffffff']
OBJEKTGRUPPEN_K11 = {
    'k11_gross': {'size': 128, 'items': [
        'giant bleached whale skeleton lying on the ground, long ribcage and spine, big skull, side view, perfectly straight front elevation view, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'old broken wooden shipwreck stranded on land, tilted hull, broken mast with a torn pale sail, perfectly straight front elevation view, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'half sunken old wooden shipwreck in shallow water, only the dark hull and a broken mast stump visible, perfectly straight front elevation view, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
        'tall jagged dark sea rock spire rising from the water, teal-black stone with a little moss, perfectly straight front elevation view, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style',
    ]},
    'k11_meer': {'size': 64, 'items': [
        'round pink coral cluster', 'tall pink branching coral', 'red fan coral', 'dark green seaweed tuft',
        'tall dark kelp strands', 'orange starfish', 'black sea urchin', 'pale spiral sea shell',
        'grey rock with barnacles', 'small dark sea rock', 'purple sea anemone', 'teal glowing sea crystal',
        'pale pink coral rubble', 'small dark sea rock spire', 'clam shell with a pearl', 'tangle of dark seaweed',
    ]},
    'k11_land': {'size': 64, 'items': [
        'old rusty ship anchor stuck in the ground', 'black iron brazier with burning orange fire', 'broken dark stone obelisk',
        'tall dark stone pillar with a violet rune', 'pile of rusty chains', 'old broken barrel', 'pale driftwood log',
        'broken ship mast lying on the ground', 'fish skeleton', 'pile of skulls and bones', 'small withered black bush',
        'cursed dark lantern on a post with a teal glow', 'old wooden signpost, blank', 'broken wooden crate',
        'dark stone stairs block', 'small pile of black ooze stones',
    ]},
}


STIL_K12 = ("Top-down RPG map object for a gloomy muddy puppet forest, in polished handheld monster-collecting RPG pixel "
            "art: colored dark outline (darkest shade of the object's own hue, never pure black), light from the upper "
            "left, dark desaturated greens, violet and warm brown wood, clean shapes, no noise, no dithering, "
            "transparent background, no ground, no cast shadow.")
PALETTE_K12 = ['#12161a', '#1c2a22', '#26382c', '#304836', '#3e5a44', '#4e6e52', '#6a8a64', '#8eaa7e',
               '#2a1e34', '#3c2a4a', '#523a66', '#6c4e86', '#8a68a8', '#2a1a10', '#3e2818', '#5a3c24',
               '#7a5434', '#9a6e46', '#c08e5e', '#e0b484', '#4a1a1e', '#7a2228', '#b03a3a', '#e05a4a',
               '#e8702a', '#f8a040', '#ffd870', '#fff4c0', '#2c3242', '#4a5266', '#7a8296', '#b4bccc', '#ffffff']
FR12 = "perfectly straight front elevation view, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style"
OBJEKTGRUPPEN_K12 = {
    'k12_gross': {'size': 128, 'items': [
        'wooden treehouse built into a huge gnarled dark tree with dark blue-violet leaves, red pointed shingle roof, warm lit windows, wooden balcony and a wooden stair down to the ground, ' + FR12,
        'huge old gloomy oak tree with a dense dark green crown and a few violet leaves, thick twisted trunk with roots, ' + FR12,
        'wooden puppet theater booth with a dark red curtain and carved wooden frame, ' + FR12,
        'huge twisted dark tree with drooping dark violet leaves and thick gnarled roots, ' + FR12,
    ]},
    'k12_baumhaus': {'size': 224, 'items': [
        'big wooden treehouse with two floors built into a huge gnarled dark tree with dark blue-violet leaves, red pointed shingle roof with a small spire, warm lit yellow windows, wooden balconies with railings, a wooden stair spiraling down the trunk to the ground, a small wooden door in the trunk, ' + FR12,
    ]},
    'k12_rand': {'size': 64, 'items': [
        'large dark green fern', 'tall dark green fern with long fronds', 'wide low dark fern', 'small cluster of dark ferns',
        'dark fern with curled young fronds', 'bluish dark green fern', 'fern with a few violet flowers', 'dense clump of ferns and grass',
        'dark leafy forest shrub', 'small dark thorny shrub', 'tuft of tall dark grass', 'dark ivy-covered bush',
        'big dark green leaves plant', 'dark fern with drooping fronds', 'mossy rock with small ferns', 'dark wild herb bush',
    ]},
    'k12_bruecke': {'size': 96, 'items': [
        'narrow old wooden plank footbridge seen from above, running vertically from top to bottom, planks laid horizontally, thick wooden side beams, small posts at the four corners with rope railings, mossy weathered dark wood, top-down view',
        'narrow old wooden plank footbridge seen from above, running vertically from top to bottom, slightly arched, planks laid horizontally, wooden railings on both sides, one plank missing, mossy dark wood, top-down view',
        'old wooden plank footbridge over a stream, running horizontally from left to right, planks vertical, wooden railing with posts on the far side, mossy dark wood, 3/4 top-down view',
        'old wooden plank footbridge over a stream, running horizontally from left to right, rope railings, weathered dark wood with moss, 3/4 top-down view',
    ]},
    'k12_bruecke2': {'size': 128, 'items': [
        'narrow old wooden plank footbridge seen from above, running vertically from top to bottom, the whole bridge fully visible with both ends, planks laid horizontally, thick wooden side beams, a small post at each of the four corners with rope railings between them, mossy weathered dark wood, top-down view, small and centered with empty space around it',
        'narrow old wooden plank footbridge seen from above, running vertically, complete with both ends visible, planks laid horizontally, side beams, corner posts with rope railings, a little moss, dark weathered wood, top-down view, small and centered with empty space around it',
        'short old wooden plank footbridge seen from above, vertical, both ends complete with corner posts, rope railings, dark mossy wood, top-down view, small and centered with empty space around it',
        'old wooden footbridge from above, vertical, planks horizontal, wooden side rails with posts at both ends, mossy dark wood, top-down view, small and centered with empty space around it',
    ]},
    'k12_quelle': {'size': 96, 'items': [
        'stone cave mouth with a carved stone arch built into a dark rock cliff wall, a small waterfall pouring out of the cave and splashing into a little foaming pool at the bottom, moss and ferns around the arch, ' + FR12,
        'old carved stone water spout shaped like a gaping monster face set into a dark rock wall, a stream of water pouring from its mouth down into a small foaming pool, moss, ' + FR12,
        'dark rocky crevice in a cliff with a spring gushing out as a thin waterfall over mossy stones into a small pool, ferns at the sides, ' + FR12,
        'mossy stone culvert arch in a cliff wall with water flowing out over stone steps into a small pool, hanging roots and ferns, ' + FR12,
    ]},
    'k12_quelle2': {'size': 48, 'items': [
        'isolated small carved stone water spout shaped like a gaping monster face with moss, water pouring from its mouth straight down, only the spout and the water stream, no wall, no background, ' + FR12,
        'isolated small carved stone arch outlet with a dark opening and water pouring out of it straight down, moss on the stones, only the arch and the water, no wall, no background, ' + FR12,
        'isolated small old stone pipe spout with a mossy rim, water pouring out straight down, no wall, no background, ' + FR12,
        'isolated small carved wooden puppet face spout with a round open mouth, water pouring out straight down, no wall, no background, ' + FR12,
    ]},
    'k12_wald': {'size': 64, 'items': [
        'gloomy dark green round forest tree', 'gloomy dark green tall forest tree', 'dark green forest tree with a twisted trunk',
        'gloomy dark forest tree with blue-violet leaves', 'dark pine tree', 'small gloomy dark green tree',
        'gloomy apple tree with red apples', 'gloomy pear tree with yellow pears', 'gloomy plum tree with dark purple plums',
        'gnarled black tree with violet leaves', 'dark thorny bramble bush', 'dark green round bush',
        'cluster of big red spotted mushrooms', 'old mossy tree stump', 'dark fern', 'fallen mossy log',
    ]},
    'k12_puppen': {'size': 64, 'items': [
        'wooden marionette puppet hanging on strings from a wooden frame', 'wooden marionette control cross on a post with dangling strings',
        'broken wooden puppet sitting slumped on the ground', 'wooden lamp post with a glowing jack-o-lantern',
        'red wooden toy wagon full of toys', 'wooden treasure chest with iron bands', 'old wooden signpost, blank',
        'red wooden toy letter block', 'blue wooden toy letter block', 'wooden fence post with a rope',
        'round wooden archery target on a stand', 'giant wooden toy mallet stuck head-down in the ground',
        'wooden scarecrow puppet with a straw hat', 'old wooden barrel', 'wooden spinning top toy', 'pile of loose wooden puppet limbs',
    ]},
    'k12_klein': {'size': 32, 'items': [
        'small red spotted mushroom', 'two pale mushrooms', 'small dark grass tuft', 'small dead leaves', 'twig',
        'small stones', 'small purple flowers', 'fallen red apple', 'small orange pumpkin', 'small dark fern',
        'small tree root', 'small pink flowers', 'small wooden peg', 'small puddle of mud', 'small yellow flowers', 'acorns',
    ]},
}


STIL_K13 = ("Top-down RPG map object for a ruined dark machine city, in polished handheld monster-collecting RPG pixel "
            "art: colored dark outline (darkest shade of the object's own hue, never pure black), light from the upper "
            "left, dark steel blue-grey and teal metal, rust brown, glowing red lights, clean shapes, no noise, no "
            "dithering, transparent background, no ground, no cast shadow.")
PALETTE_K13 = ['#101418', '#1a222a', '#243038', '#2e3e48', '#3a4e5a', '#4a6270', '#5e7886', '#7890a0', '#98aab8', '#c0ccd6',
               '#2a2e3a', '#3c4250', '#565e6e', '#7a8292', '#a2aab8', '#3a2418', '#5a3622', '#7a4a2c', '#a06438', '#c88a50',
               '#4a1018', '#7a1c24', '#b02c34', '#e04050', '#ff8090', '#c8a040', '#f0d060', '#2a6a7a', '#3c9aaa', '#70d0dc',
               '#3a2a50', '#5a4078', '#8060a8', '#e8eef4', '#ffffff']
FR13 = "perfectly straight front elevation view, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style"
OBJEKTGRUPPEN_K13 = {
    'k13_gross': {'size': 128, 'items': [
        'tall black steel radio antenna tower with glowing red rings and a red eye light on top, sinister machine city landmark, ' + FR13,
        'tall rusty steel lattice transmission tower, ' + FR13,
        'wrecked giant purple mechanical dragon robot lying broken on the ground, torn metal wings, sparking cables, ' + FR13,
        'burnt-out abandoned city bus wreck, rusty and broken windows, side view, ' + FR13,
    ]},
    'k13_gross2': {'size': 128, 'items': [
        'tall ruined glass office tower with many broken blue windows and a glass double door, grey concrete, ' + FR13,
        'small train station entrance hall with a blue pointed metal roof, metal turnstiles in front, ' + FR13,
        'collapsed construction crane jib lying on the ground in rubble, rusty steel lattice, ' + FR13,
        'huge sealed fortress gate machine with a glowing red mechanical eye in the middle, heavy dark steel, ' + FR13,
    ]},
    'k13_gebaeude': {'size': 128, 'items': [
        'abandoned industrial warehouse with a large grey roll-up shutter door with yellow hazard stripes, red warning lights, dark teal metal walls, flat roof with a vent, ' + FR13,
        'ruined two-storey city building with two small shops below with red and yellow awnings and a door, cracked grey walls, ' + FR13,
        'abandoned beige apartment block with rows of small windows and balconies, one door, cracked walls, ' + FR13,
        'small grey office building with blue glass windows, glass double door and a rooftop antenna, ' + FR13,
    ]},
    'k13_rand': {'size': 64, 'items': [
        'bent rusty steel I-beam', 'pile of rusty pipes', 'rusty cogwheel half buried', 'tangled bundle of black cables',
        'stack of old tires', 'crumpled rusty sheet metal', 'broken rusty engine block', 'pile of scrap metal with bolts',
        'cluster of broken rusty gears', 'twisted rusty rebar sticking out', 'broken rusty radiator', 'heap of mixed junk and wires',
        'bent broken metal fence piece', 'rusty barrel lying on its side', 'pile of rusty chains', 'broken rusty robot leg',
    ]},
    'k13_berg': {'size': 128, 'items': [
        'giant rusty cogwheel half buried in dark rock, ' + FR13,
        'segment of a giant rusty tank track half buried in rubble, ' + FR13,
        'broken giant mechanical robot arm with a claw sticking out of rubble, ' + FR13,
        'broken giant mechanical robot head half buried in rubble, one dim red eye, ' + FR13,
    ]},
    'k13_wache': {'size': 64, 'items': [
        'small rusty radio mast with a red warning light on top', 'rusty antenna pole', 'red warning lamp on a metal pole',
        'broken security camera on a pole with a red lens light', 'old searchlight on a metal stand', 'upright chain-link fence segment with posts',
        'fallen chain-link fence segment lying flat', 'coil of barbed wire', 'rusty warning sign with a skull', 'cluster of glowing violet crystals',
        'small violet crystal vein in a dark rock', 'small rusty satellite dish', 'thick black power cable coming out of the ground',
        'rusty pipe elbow sticking out of the ground', 'broken metal post with a red light', 'small rusty control box with a red light',
    ]},
    'k13_haus': {'size': 128, 'items': [
        'abandoned industrial warehouse with a large grey roll-up shutter door with yellow hazard stripes and red warning lights, dark teal metal walls, flat metal roof with a big vent and a skylight, seen from the front and slightly from above so the whole flat roof surface is clearly visible above the facade (roof parapet, vents, pipes), the front facade below, like a classic 2D handheld RPG town building with a visible roof, no isometric',
        'ruined two-storey city building with two small shops below with red and yellow awnings, cracked grey walls, flat roof with a broken parapet, an air-conditioning unit and rubble, seen from the front and slightly from above so the whole flat roof surface is clearly visible above the facade (roof parapet, vents, pipes), the front facade below, like a classic 2D handheld RPG town building with a visible roof, no isometric',
        'abandoned beige apartment block with rows of small windows and balconies, one door, flat roof with a water tank and antennas, seen from the front and slightly from above so the whole flat roof surface is clearly visible above the facade (roof parapet, vents, pipes), the front facade below, like a classic 2D handheld RPG town building with a visible roof, no isometric',
        'small grey office building with blue glass windows and a glass double door, flat roof with an antenna and a vent box, seen from the front and slightly from above so the whole flat roof surface is clearly visible above the facade (roof parapet, vents, pipes), the front facade below, like a classic 2D handheld RPG town building with a visible roof, no isometric',
    ]},
    'k13_turm': {'size': 128, 'items': [
        'ruined glass office tower, four floors, many broken blue windows and a glass double door at the bottom, flat roof with antennas and a satellite dish, the whole building fully visible and centered with empty space around it, seen from the front and slightly from above so the whole flat roof surface is clearly visible above the facade (roof parapet, vents, pipes), the front facade below, like a classic 2D handheld RPG town building with a visible roof, no isometric',
        'ruined glass office building, three floors, broken blue windows, glass double door at the bottom, flat roof with a vent and antennas, the whole building fully visible and centered with empty space around it, seen from the front and slightly from above so the whole flat roof surface is clearly visible above the facade (roof parapet, vents, pipes), the front facade below, like a classic 2D handheld RPG town building with a visible roof, no isometric',
        'damaged teal glass office tower, four floors, flat roof with a helipad, glass door at the bottom, the whole building fully visible and centered with empty space around it, seen from the front and slightly from above so the whole flat roof surface is clearly visible above the facade (roof parapet, vents, pipes), the front facade below, like a classic 2D handheld RPG town building with a visible roof, no isometric',
        'ruined grey concrete office tower with blue windows, four floors, glass door at the bottom, flat roof with antennas, the whole building fully visible and centered with empty space around it, seen from the front and slightly from above so the whole flat roof surface is clearly visible above the facade (roof parapet, vents, pipes), the front facade below, like a classic 2D handheld RPG town building with a visible roof, no isometric',
    ]},
    'k13_haus2': {'size': 128, 'items': [
        'tall ruined glass office tower with many broken blue windows and a glass double door, flat roof with a helipad mark and antennas, seen from the front and slightly from above so the whole flat roof surface is clearly visible above the facade (roof parapet, vents, pipes), the front facade below, like a classic 2D handheld RPG town building with a visible roof, no isometric',
        'abandoned dark red brick apartment block with small windows, fire escape stairs, flat roof with chimneys and a water tank, seen from the front and slightly from above so the whole flat roof surface is clearly visible above the facade (roof parapet, vents, pipes), the front facade below, like a classic 2D handheld RPG town building with a visible roof, no isometric',
        'ruined city shop building with one big shopfront and a torn green awning, grey walls, flat roof with vents, seen from the front and slightly from above so the whole flat roof surface is clearly visible above the facade (roof parapet, vents, pipes), the front facade below, like a classic 2D handheld RPG town building with a visible roof, no isometric',
        'abandoned small factory building with a rusty metal door and high windows, sawtooth roof with skylights, seen from the front and slightly from above so the whole flat roof surface is clearly visible above the facade (roof parapet, vents, pipes), the front facade below, like a classic 2D handheld RPG town building with a visible roof, no isometric',
    ]},
    'k13_festung': {'size': 96, 'items': [
        'cylindrical steel reactor pod with a glowing orange core window and pipes, standing on a base, ' + FR13,
        'heavy steel blast door with yellow and black hazard stripes and red lights, wall mounted, ' + FR13,
        'dark machine control console with red blinking lights and screens, ' + FR13,
        'steel power pylon with thick hanging cables and a red warning light, ' + FR13,
    ]},
    'k13_mittel': {'size': 64, 'items': [
        'tall rusty factory chimney stack with dark holes', 'industrial furnace with glowing fire behind a grate',
        'teal cylindrical storage tank on legs', 'burnt-out wrecked car, side view', 'broken traffic light on a pole',
        'old street lamp with a small light', 'giant rusty cogwheel lying half buried', 'dark monument statue on a pedestal with a red gem',
        'broken glass phone booth', 'pile of concrete rubble and rebar', 'wrecked broken robot slumped on the ground',
        'rusty oil barrel', 'stack of metal crates', 'humming generator box with a red light', 'bent rusty pipe segment',
        'broken bench',
    ]},
    'k13_klein': {'size': 32, 'items': [
        'small skull', 'small concrete rubble stones', 'small scrap metal bits', 'small broken pipe', 'screws and bolts',
        'small black oil puddle', 'tangled wires', 'small warning sign', 'small rusty barrel', 'small purple crystal shard',
        'small cogwheel', 'old tire', 'traffic cone', 'small bones', 'crushed tin can', 'small dead weed',
    ]},
}


STIL_K14 = ("Top-down RPG map object for the dark summit of a cursed spiral mountain ruled by a sinister jester, in polished "
            "handheld monster-collecting RPG pixel art: colored dark outline (darkest shade of the object's own hue, never "
            "pure black), light from the upper left, grey-violet stone, deep red, harlequin black and lavender, gold "
            "accents, clean shapes, no noise, no dithering, transparent background, no ground, no cast shadow.")
PALETTE_K14 = ['#12101a', '#1c1826', '#282236', '#363046', '#464058', '#58526c', '#6c6882', '#86829a', '#a4a0b8', '#c8c4d8',
               '#3a0e16', '#5a1420', '#7a1a28', '#a02232', '#c83446', '#e8606e', '#4a2a6a', '#6a3e92', '#8a5cbc', '#b088e0',
               '#d8b8f8', '#5a4018', '#8a6424', '#b88a34', '#e0b44a', '#f8dc80', '#2a3a4a', '#4a6a80', '#f4f0f8', '#ffffff']
FR14 = "perfectly straight front elevation view, facing the camera head-on, no perspective, no isometric, flat orthographic, classic 2D handheld RPG style"
DACH14 = "seen from the front and slightly from above so the roofs are clearly visible, like a classic 2D handheld RPG castle"
OBJEKTGRUPPEN_K14 = {
    'k14_schloss': {'size': 224, 'items': [
        'sinister jester castle on a mountain summit, dark grey-violet stone with harlequin diamond patterns in red and black, many slender towers with pointed red cone roofs and golden spires, a big arched gate in the middle with a golden playing-card suit emblem above, gothic windows glowing faintly, the whole castle fully visible and centered, ' + DACH14,
    ]},
    'k14_schloss2': {'size': 128, 'items': [
        'sinister jester castle on a mountain summit, dark grey-violet stone with red and black harlequin diamond patterns, slender towers with red jester-cap shaped roofs and pointed red cone roofs with golden spires, a big arched gate in the middle with a golden card-suit emblem above, faintly glowing violet gothic windows, the whole castle fully visible and centered, ' + DACH14 + ', ' + FR14,
        'dark jester castle keep with three towers, red pointed roofs with golden spires, harlequin pattern walls, big arched gate in the middle, the whole castle fully visible and centered, ' + DACH14 + ', ' + FR14,
        'gothic dark violet castle with a central tall tower and two side towers, red cone roofs, gold trim, a grand arched gate, the whole castle fully visible and centered, ' + DACH14 + ', ' + FR14,
        'small sinister circus-like castle with striped red and black roofs, golden spires, an arched gate, the whole castle fully visible and centered, ' + DACH14 + ', ' + FR14,
    ]},
    'k14_leere': {'size': 64, 'items': [
        'dark shadowy claw-like tendrils rising out of a crack in the ground, violet glow at the base', 'cluster of floating black crystal shards with violet light',
        'small floating glitching purple data cubes breaking apart into pixels', 'heavy dark iron chain anchored in the ground with a big ring',
        'broken dark eggshell halves with faint violet glow inside', 'black stone obelisk with a single glowing violet void eye',
        'dark skeletal claw reaching out of the ground', 'small dark void orb floating above a cracked stone base',
        'cracked ground fissure with violet light shining out', 'dark thorny vine twisting out of the ground',
        'tilted broken black stone pillar wrapped in chains', 'pile of dark broken data crystals',
        'floating single black shard with violet glow', 'dark iron spike stuck in the ground with chains', 'small dark void rift crack floating in the air',
        'ring of small dark standing stones',
    ]},
    'k14_bau': {'size': 128, 'items': [
        'straight grey stone castle wall segment with battlements and narrow arrow slits, ' + DACH14 + ', ' + FR14,
        'round grey stone castle tower with a pointed red cone roof and a golden spire, small window and door, ' + DACH14,
        'dark swirling void portal inside a ring of jagged black crystals and stone, violet and cyan sparks, ' + FR14,
        'dark stone throne with tall spiky back and red cushion, harlequin pattern, ' + FR14,
    ]},
    'k14_statue': {'size': 96, 'items': [
        'stone statue of an armored knight holding a huge sword point down, on a stone pedestal, ' + FR14,
        'stone statue of a sinister harlequin jester juggling, on a stone pedestal, ' + FR14,
        'dark stone statue of an elegant winged lady with bat wings, on a stone pedestal, ' + FR14,
        'giant standing stone playing card monolith with a carved spade, ' + FR14,
    ]},
    'k14_mittel': {'size': 64, 'items': [
        'large standing playing card with a red heart, stuck in the ground', 'large standing playing card with a black spade, stuck in the ground',
        'large standing playing card with a red diamond, stuck in the ground', 'large standing playing card with a black club, stuck in the ground',
        'cluster of glowing violet crystals', 'stone brazier with violet flames', 'purple banner with a gold diamond on a pole',
        'big sword stuck in a rock', 'broken giant sword lying', 'harlequin mask on a wooden stake', 'small stone bat gargoyle',
        'pile of skulls', 'gothic iron candle stand with lit candles', 'stone urn', 'broken stone pillar', 'black top hat with playing cards',
    ]},
    'k14_klein': {'size': 32, 'items': [
        'small grey rocks', 'pebbles', 'small bones', 'small skull', 'scattered playing cards', 'few gold coins', 'two dice',
        'broken mask shard', 'small violet crystal', 'dead grass tuft', 'black feather', 'small rubble', 'small lit candle',
        'rusty chain', 'small star shard glowing', 'cracked stone tile piece',
    ]},
    'k14_wolken': {'size': 64, 'items': [
        'soft lavender-white cloud puff', 'big fluffy pale violet cloud', 'flat wispy cloud', 'round small cloud puff',
        'long thin cloud streak', 'cluster of two cloud puffs', 'dense white cloud', 'fading misty cloud',
    ]},
}


STIL_K15 = ("Top-down RPG object floating in a dark starry void, in polished handheld monster-collecting RPG pixel art: "
            "colored dark outline (darkest shade of the object's own hue, never pure black), light from the upper left, "
            "clean shapes, no noise, no dithering, transparent background, no ground, no cast shadow.")
PALETTE_K15 = ['#0a0c18', '#141830', '#1e2440', '#2a3256', '#3a446c', '#505c86', '#6c78a2', '#9aa4c4', '#c8d0e4', '#ffffff',
               '#2a1a3a', '#40265a', '#5c3684', '#7c4cb0', '#a070e0', '#c8a0f8', '#e070c0', '#3a5a2a', '#5a8a3a', '#8ac050',
               '#c8a060', '#e8d090', '#a0d8f0', '#e0f4ff', '#5a3a24', '#8a5a34', '#c03040', '#40c8d8', '#f0d040', '#606878']
OBJEKTGRUPPEN_K15 = {
    'k15_inseln': {'size': 64, 'items': [
        'small floating rock island chunk with green grass and a tiny tree on top, broken rocky bottom with dangling roots',
        'small floating rock chunk with desert sand and a tiny cactus, broken rocky bottom',
        'small floating ice chunk with snow and a tiny pine tree, broken icy bottom',
        'small floating chunk of rusty machine scrap with pipes and gears, cables dangling below',
        'small floating chunk of colorful toy blocks and a tiny toy house',
        'small floating chunk of dark ocean water with coral, water dripping from the broken bottom',
        'small floating chunk of muddy forest ground with a tiny dark tree and mushrooms',
        'small floating chunk of red carpet and checkered floor, broken stone bottom',
        'floating grey asteroid rock', 'small floating grey rock pieces', 'floating dark crystal shard with violet glow',
        'floating broken stone pillar piece', 'floating glitching violet data cube cluster', 'floating broken chain links',
        'floating dark tentacle-like void tendril', 'floating cracked digital egg shell',
    ]},
    'k15_inseln2': {'size': 64, 'items': [   # je zwei Varianten fuer Karte 02, 04, 08, 09
        'small floating chunk of industrial steelworks ground with a tiny smokestack and a shipping container, broken rocky bottom',
        'small floating chunk of rusty steel plates with a tiny yellow crane and oil barrels, broken rocky bottom',
        'small floating chunk of dry golden savanna grass with a tiny acacia tree and a bronze gear half buried, broken orange canyon rock bottom',
        'small floating chunk of savanna ground with big bronze gears and a small rock, broken orange canyon rock bottom',
        'small floating chunk of dark graveyard grass with a tiny tombstone and a dead tree, broken rocky bottom',
        'small floating chunk of foggy grey graveyard ground with a tiny crypt and a crooked cross, broken rocky bottom',
        'small floating chunk of a gothic castle ruin with a tiny dark tower with red windows and a bat flag, broken stone bottom',
        'small floating chunk of dark castle wall with a tiny red-roofed gothic tower and dark moat water, broken stone bottom',
    ]},
}


STIL_K16 = ("Top-down RPG object in a glowing digital cyberspace network world, in polished handheld monster-collecting RPG pixel "
            "art: colored dark outline (darkest shade of the object's own hue, never pure black), light from the upper left, "
            "clean shapes, no noise, no dithering, transparent background, no ground, no cast shadow, " + FR14 + ".")
PALETTE_K16 = ['#080c1c', '#0e1630', '#16223e', '#1e2e50', '#283c64', '#34507a', '#466892', '#6a8cb0', '#a0bcd4', '#e0ecf6',
               '#0a3a48', '#10586a', '#1a8094', '#2cb4c8', '#5ae0ec', '#b0f6fa', '#4a1418', '#7a1c22', '#b02a2c', '#e04a3c',
               '#f08a50', '#f0d060', '#fff0a0', '#c8c0b4', '#f0ece4', '#3a2a5a', '#6a4aa0', '#a070e0', '#3a3a44', '#ffffff']
OBJEKTGRUPPEN_K16 = {
    'k16_tor': {'size': 64, 'items': [
        'digital firewall gate, a thick dark steel frame with orange glowing circuit lines around a deep red glowing screen with a red target crosshair symbol, two curved white horn-like bolts on the upper and lower corners, standing upright',
        'cyber boss gate, square dark blue steel frame with orange neon edges, red glowing data screen in the middle with a glitching red eye-like target mark, white claw-like clamps at the four corners, standing upright',
    ]},
    'k16_netz': {'size': 48, 'items': [
        'tall dark blue server tower with rows of small blinking cyan and green lights and a cable at the bottom',
        'holographic computer terminal on a slim stand with a floating cyan screen showing code',
        'network antenna node, slim metal mast with a glowing cyan orb on top and small blinking lights',
        'cyber data pylon, dark steel pillar with a vertical glowing cyan energy stripe',
        'floating glowing cyan data cube with circuit pattern above a small metal base',
        'small metal cable junction box with glowing cyan ports and cables',
        'glowing cyan data crystal growing from a small metal socket',
        'holographic warning sign floating above a small emitter, orange exclamation mark',
        'big round radar dish on a metal stand with a red blinking light',
        'stack of two small dark server boxes with green blinking lights',
        'glowing orange data mailbox, a small terminal with an envelope icon screen',
        'small cyber tree made of glowing cyan circuit lines on a metal base',
    ]},
    'k17_virus': {'size': 48, 'items': [   # Anspielungen auf die Virus-Linie nur ueber Farben und Motive
        'cracked white digital egg with red and yellow spots, glowing red data leaking from the crack, on a small pile of corrupted pixel blocks',
        'small cluster of round red and white virus bug eggs with tiny dark eyes, glitching pixels around them',
        'grey silken cocoon made of tangled data cables hanging from a broken cable mast, faint red glow inside',
        'tangle of dark cables forming a spider web with a glowing red node in the center, anchored on the floor',
        'black bone-like spike pillar with red glowing markings and jagged white bone tips',
        'big curved red-brown horn shard sticking out of the floor, cracked, red glow in the cracks',
        'corrupted dark server tower with a red glitching screen and black tendrils growing out of it',
        'broken network pylon wrapped in black thorny data tendrils with red glow',
        'pile of corrupted pixel blocks in red, magenta and black',
        'red warning hologram with a glitching virus symbol floating above a small emitter',
        'black cable tentacles bursting out of a floor crack with red light',
        'grey cocoon shell of cables broken open and empty',
    ]},
    'k17_gross': {'size': 96, 'items': [
        'huge black and red corrupted data crystal formation with white bone spikes, red glowing veins',
        'giant broken cocoon made of grey data cables with a red glowing core, cables spreading on the floor',
        'large web of black data cables stretched between two broken network pylons, glowing red nodes',
        'giant red-brown horn pair rising from a corrupted floor crater, black and red glitch blocks around',
    ]},
    'k16_klein': {'size': 32, 'items': [
        'small golden data chip item lying on the floor, glowing softly',
        'small coil of dark cable lying on the floor',
        'small glowing cyan floor vent grate',
        'small broken pixel glitch block, magenta and cyan',
        'tiny blinking cyan sensor lamp on the floor',
        'small dark metal crate with a cyan stripe',
        'small orange warning floor marker',
        'small floating binary code hologram, green digits',
    ]},
}


STIL_K18 = ("Top-down RPG object for a modern Japanese bay-side city at dusk in light fog, in polished handheld monster-collecting "
            "RPG pixel art: colored dark outline (darkest shade of the object's own hue, never pure black), light from the upper "
            "left, slightly muted cool evening colors, clean shapes, no noise, no dithering, transparent background, no ground, "
            "no cast shadow, " + FR14 + ".")
PALETTE_K18 = ['#16182a', '#222638', '#30364a', '#40485e', '#566078', '#727c94', '#98a2b8', '#c4cad8', '#eef0f6', '#ffffff',
               '#5a2a2e', '#8a3a3c', '#c04a44', '#e87a5a', '#f0b070', '#f6d890', '#2a3a2c', '#3e5a40', '#5a8a50', '#8ab868',
               '#c89a2a', '#e8c040', '#f8e070', '#2a3a5a', '#3a5a8a', '#5a86c0', '#8ab6e0', '#6a5a7a', '#9a8aae', '#4a3a2a']
OBJEKTGRUPPEN_K18 = {
    'k18_autos': {'size': 64, 'items': [
        'small white sedan car seen from the side, facing right, slightly from above so the roof is visible, headlights',
        'small silver grey sedan car seen from the side, facing left, slightly from above so the roof is visible',
        'small red compact car seen from the side, facing right, slightly from above so the roof is visible',
        'small orange compact car seen from the side, facing left, slightly from above so the roof is visible',
        'yellow taxi car with a roof sign seen from the side, facing right, slightly from above',
        'light blue small car seen from the side, facing left, slightly from above',
        'small white car seen from directly above, facing down, roof and windshield visible',
        'small grey car seen from directly above, facing up, roof and rear window visible',
    ]},
    'k18_gross': {'size': 128, 'items': [
        'white and green modern city bus seen from the side, facing right, slightly from above so the roof is visible',
        'white monorail train car with a dark blue window band seen from the side, long and sleek, slightly from above',
        'small white motor boat seen from the side, floating, slightly from above',
        'blue bus stop shelter with a glass back wall, a bench inside and a round bus stop sign',
    ]},
    'k18_frontal': {'size': 64, 'items': [   # zweiter Versuch, streng frontal (die ersten waren isometrisch)
        'small white motor boat, pure side view flat 2D profile, camera exactly perpendicular to the hull side, bow pointing right, no perspective, no isometric, floating',
        'small white motor boat with a blue stripe, pure side view flat 2D profile, bow pointing left, no perspective, no isometric',
        'blue bus stop shelter seen exactly from the front, flat 2D front elevation, glass back wall, flat roof, bench inside, symmetric, no perspective, no isometric',
        'grey bus stop shelter seen exactly from the front, flat 2D front elevation, glass back wall, flat roof with a route sign, bench inside, symmetric, no perspective, no isometric',
    ]},
    'k18_strasse': {'size': 32, 'items': [
        'red japanese drink vending machine with glowing display of bottles',
        'blue drink vending machine with glowing display of bottles',
        'red cylindrical japanese post box on a short pillar',
        'small grey public telephone booth with glass and a green phone',
        'parked bicycle seen from the side',
        'round blue bus stop sign on a pole',
        'modern street information map board on two legs with a glowing city map',
        'red and white striped road barrier on two feet',
        'grey metal pedestrian guard rail piece',
        'short grey bollard post',
        'tall flag pole with a light blue banner flag',
        'orange life buoy ring on a small post',
    ]},
    'k18_laeden': {'size': 128, 'items': [
        'small japanese town convenience store building, two stories, red and white awning over a big glowing shop window, sign on the facade, flat roof visible from slightly above, cozy hand painted handheld RPG town style, perfectly straight front view',
        'small japanese ramen restaurant building, two stories, red paper lanterns and a short noren curtain at the door, wooden sign, flat roof visible from slightly above, cozy handheld RPG town style, perfectly straight front view',
        'small cafe building, two stories, pink striped awning, flower boxes under the windows, flat roof visible from slightly above, cozy handheld RPG town style, perfectly straight front view',
        'small pharmacy building, two stories, green cross sign, green awning, flat roof visible from slightly above, cozy handheld RPG town style, perfectly straight front view',
    ]},
    'k18_laeden2': {'size': 128, 'items': [
        'small bakery building, two stories, orange awning, bread in the window, flat roof visible from slightly above, cozy handheld RPG town style, perfectly straight front view',
        'small bookstore building, two stories, dark blue awning, stacks of books in the window, flat roof visible from slightly above, cozy handheld RPG town style, perfectly straight front view',
        'small japanese izakaya bar building, two stories, red lanterns, wooden facade, flat roof visible from slightly above, cozy handheld RPG town style, perfectly straight front view',
        'small closed shop building, two stories, grey metal roller shutter pulled down, flat roof visible from slightly above, cozy handheld RPG town style, perfectly straight front view',
    ]},
    'k18_haeuser': {'size': 128, 'items': [
        'modern office building, four stories, rows of blue glass windows, some windows warmly lit, glass entrance door at the bottom, flat roof with small ac units visible from slightly above, cozy handheld RPG town style, perfectly straight front view',
        'japanese apartment block, five stories, balconies with railings and hanging laundry, some windows warmly lit, entrance at the bottom, flat roof visible from slightly above, cozy handheld RPG town style, perfectly straight front view',
        'harbor warehouse, light grey corrugated walls, red white blue stripe, one big roll-up door half open, small side door with a lamp, flat corrugated roof visible from slightly above, cozy handheld RPG town style, perfectly straight front view',
        'harbor warehouse with a sawtooth roof with skylights, beige walls, orange stripe, roll-up door, small side door with a lamp, cozy handheld RPG town style, perfectly straight front view',
    ]},
    'k18_laeden3': {'size': 128, 'items': [
        'small japanese convenience store building, two stories, red and white awning over a glowing shop window, sign on the facade, flat facade exactly parallel to the camera, absolutely no side wall visible, strict front elevation like a building in a classic handheld town, roof only as a thin strip on top, ground line straight, no perspective, no isometric, no 3/4 view',
        'small japanese ramen restaurant building, two stories, red paper lanterns, noren curtain at the door, wooden sign, flat facade exactly parallel to the camera, absolutely no side wall visible, strict front elevation like a building in a classic handheld town, roof only as a thin strip on top, ground line straight, no perspective, no isometric, no 3/4 view',
        'small cafe building, two stories, pink striped awning, flower boxes under the windows, flat facade exactly parallel to the camera, absolutely no side wall visible, strict front elevation like a building in a classic handheld town, roof only as a thin strip on top, ground line straight, no perspective, no isometric, no 3/4 view',
        'small pharmacy building, two stories, green cross sign, green awning, flat facade exactly parallel to the camera, absolutely no side wall visible, strict front elevation like a building in a classic handheld town, roof only as a thin strip on top, ground line straight, no perspective, no isometric, no 3/4 view',
    ]},
    'k18_laeden4': {'size': 128, 'items': [
        'small bakery building, two stories, orange awning, bread in the window, flat facade exactly parallel to the camera, absolutely no side wall visible, strict front elevation like a building in a classic handheld town, roof only as a thin strip on top, ground line straight, no perspective, no isometric, no 3/4 view',
        'small bookstore building, two stories, dark blue awning, books in the window, flat facade exactly parallel to the camera, absolutely no side wall visible, strict front elevation like a building in a classic handheld town, roof only as a thin strip on top, ground line straight, no perspective, no isometric, no 3/4 view',
        'small japanese izakaya bar building, two stories, red lanterns, wooden facade, flat facade exactly parallel to the camera, absolutely no side wall visible, strict front elevation like a building in a classic handheld town, roof only as a thin strip on top, ground line straight, no perspective, no isometric, no 3/4 view',
        'small closed shop building, two stories, grey metal roller shutter pulled down, flat facade exactly parallel to the camera, absolutely no side wall visible, strict front elevation like a building in a classic handheld town, roof only as a thin strip on top, ground line straight, no perspective, no isometric, no 3/4 view',
    ]},
    'k18_haeuser2': {'size': 128, 'items': [
        'modern office building, four stories, rows of blue glass windows, some warmly lit, glass entrance door at the bottom center, flat facade exactly parallel to the camera, absolutely no side wall visible, strict front elevation like a building in a classic handheld town, roof only as a thin strip on top, ground line straight, no perspective, no isometric, no 3/4 view',
        'japanese apartment block, five stories, balconies with railings and hanging laundry, some windows warmly lit, entrance at the bottom center, flat facade exactly parallel to the camera, absolutely no side wall visible, strict front elevation like a building in a classic handheld town, roof only as a thin strip on top, ground line straight, no perspective, no isometric, no 3/4 view',
        'small grey office building, three stories, square windows, some warmly lit, entrance at the bottom center, flat facade exactly parallel to the camera, absolutely no side wall visible, strict front elevation like a building in a classic handheld town, roof only as a thin strip on top, ground line straight, no perspective, no isometric, no 3/4 view',
        'beige apartment house, four stories, small balconies, warmly lit windows, entrance at the bottom center, flat facade exactly parallel to the camera, absolutely no side wall visible, strict front elevation like a building in a classic handheld town, roof only as a thin strip on top, ground line straight, no perspective, no isometric, no 3/4 view',
    ]},
    'k18_lager2a': {'size': 192, 'items': [
        'large harbor warehouse, light grey corrugated metal walls, red white blue stripe, two big roll-up doors (one half open, dark inside), small side door with a lamp, flat facade exactly parallel to the camera, absolutely no side wall visible, strict front elevation like a building in a classic handheld town, roof only as a thin strip on top, ground line straight, no perspective, no isometric, no 3/4 view',
    ]},
    'k18_lager2b': {'size': 192, 'items': [
        'large harbor warehouse with a sawtooth roof edge, beige corrugated walls, orange stripe, big roll-up door, small side door with a lamp and a window, flat facade exactly parallel to the camera, absolutely no side wall visible, strict front elevation like a building in a classic handheld town, roof only as a thin strip on top, ground line straight, no perspective, no isometric, no 3/4 view',
    ]},
    'k18_zug': {'size': 128, 'items': [
        'front car of a modern white monorail commuter train, dark blue window band, rounded nose with windshield and headlight pointing right, pure side view flat 2D profile, long and low, no perspective, no isometric, cozy handheld RPG style',
        'middle car of a modern white monorail commuter train, dark blue window band with windows, two sliding doors, pure side view flat 2D profile, long and low, no perspective, no isometric, cozy handheld RPG style',
        'rear car of a modern white monorail commuter train, dark blue window band, flat rear end on the left with red tail light, pure side view flat 2D profile, long and low, no perspective, no isometric, cozy handheld RPG style',
        'complete short white monorail train with three cars, dark blue window band, pure side view flat 2D profile, nose pointing right, no perspective, cozy handheld RPG style',
    ]},
    'k18_boot': {'size': 64, 'items': [
        'small white fishing motor boat, pure side view flat 2D profile, bow pointing right, small cabin with windows, blue stripe along the hull, floating, no perspective, cozy handheld RPG style',
        'small wooden rowing boat with oars, pure side view flat 2D profile, floating, no perspective, cozy handheld RPG style',
        'small red and white harbor tug boat, pure side view flat 2D profile, bow pointing right, floating, no perspective, cozy handheld RPG style',
        'small sail boat with a white sail, pure side view flat 2D profile, floating, no perspective, cozy handheld RPG style',
    ]},
    'k18_baum2': {'size': 64, 'items': [
        'lush round city park tree with dense dark green leaf clusters, bright highlights on the upper left of each cluster, short visible brown trunk with spreading roots at the base, full crown fully visible, perfectly straight front view',
        'lush round city park tree with dense mid green leaf clusters, slightly irregular crown, short visible brown trunk with roots, full crown fully visible, perfectly straight front view',
        'lush round ginkgo tree with dense golden yellow autumn leaf clusters, bright highlights upper left, short visible brown trunk with roots, full crown fully visible, perfectly straight front view',
        'small slim street tree with a compact round green crown and a thin brown trunk, full crown fully visible, perfectly straight front view',
    ]},
    'k18_platz': {'size': 64, 'items': [
        'dark navy blue pointed canopy tent pavilion with four thin metal poles, open front, a white cooler box and a wooden chest underneath, perfectly straight front elevation view, symmetric',
        'red steel shipping container, pure side view flat 2D, corrugated side panels, corner posts, perfectly straight front elevation, no perspective',
        'blue steel shipping container, pure side view flat 2D, corrugated side panels, corner posts, perfectly straight front elevation, no perspective',
        'white delivery box truck, pure side view flat 2D profile, red cab on the left, white cargo box with a blue stripe, two wheels, no perspective',
        'stacked burlap sandbags pile, front view',
        'small grey stone drinking fountain on a pillar with a little basin, front view',
        'grey city pigeon standing, side view, tiny',
        'tall thin metal pole with a long vertical light blue cloth banner hanging from a top arm, front view',
    ]},
    'k18_baum': {'size': 64, 'items': [
        'round ginkgo tree with bright golden yellow autumn leaves and a slim brown trunk, full crown fully visible',
        'round ginkgo tree with golden yellow and orange autumn leaves, slim trunk, full crown fully visible',
        'round deciduous street tree with dark green leaves and a slim trunk, full crown fully visible',
        'square stone planter box filled with a trimmed green hedge',
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
    if gruppe.startswith('k18_'):
        ziel = os.path.join(ROOT, 'assets', 'objekte', 'karte18', gruppe[4:])
    elif gruppe.startswith('k17_'):
        ziel = os.path.join(ROOT, 'assets', 'objekte', 'karte17', gruppe[4:])
    elif gruppe.startswith('k16_'):
        ziel = os.path.join(ROOT, 'assets', 'objekte', 'karte16', gruppe[4:])
    elif gruppe.startswith('k15_'):
        ziel = os.path.join(ROOT, 'assets', 'objekte', 'karte15', gruppe[4:])
    elif gruppe.startswith('k14_'):
        ziel = os.path.join(ROOT, 'assets', 'objekte', 'karte14', gruppe[4:])
    elif gruppe.startswith('k13_'):
        ziel = os.path.join(ROOT, 'assets', 'objekte', 'karte13', gruppe[4:])
    elif gruppe.startswith('k12_'):
        ziel = os.path.join(ROOT, 'assets', 'objekte', 'karte12', gruppe[4:])
    elif gruppe.startswith('k11_'):
        ziel = os.path.join(ROOT, 'assets', 'objekte', 'karte11', gruppe[4:])
    elif gruppe.startswith('k10_'):
        ziel = os.path.join(ROOT, 'assets', 'objekte', 'karte10', gruppe[4:])
    elif gruppe.startswith('k9_'):
        ziel = os.path.join(ROOT, 'assets', 'objekte', 'karte09', gruppe[3:])
    elif gruppe.startswith('k8_'):
        ziel = os.path.join(OUT_K8, gruppe[3:])
    elif gruppe.startswith('k7_'):
        ziel = os.path.join(OUT_K7, gruppe[3:])
    elif gruppe.startswith('k6_'):
        ziel = os.path.join(OUT_K6, gruppe[3:])
    elif gruppe.startswith('k5_'):
        ziel = os.path.join(OUT_K5, gruppe[3:])
    elif gruppe.startswith('k4_'):
        ziel = os.path.join(OUT_K4, gruppe[3:])
    elif gruppe.startswith('k3_'):
        ziel = os.path.join(OUT_K3, gruppe[3:])
    else:
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
    k3 = gruppe.startswith('k3_')
    k4 = gruppe.startswith('k4_')
    k5 = gruppe.startswith('k5_')
    k6 = gruppe.startswith('k6_') or gruppe.startswith('k7_')
    if gruppe.startswith(('k11_', 'k12_', 'k13_', 'k14_', 'k15_', 'k16_', 'k17_', 'k18_')):
        g, stil_, pal_, pn_ = ((OBJEKTGRUPPEN_K18[gruppe], STIL_K18, PALETTE_K18, 'Karte18 Fog City') if gruppe.startswith('k18_') else
                               (OBJEKTGRUPPEN_K16[gruppe], STIL_K16, PALETTE_K16, 'Karte16 Network') if gruppe.startswith(('k16_', 'k17_')) else
                               (OBJEKTGRUPPEN_K15[gruppe], STIL_K15, PALETTE_K15, 'Karte15 Realm') if gruppe.startswith('k15_') else
                               (OBJEKTGRUPPEN_K14[gruppe], STIL_K14, PALETTE_K14, 'Karte14 Summit') if gruppe.startswith('k14_') else
                               (OBJEKTGRUPPEN_K13[gruppe], STIL_K13, PALETTE_K13, 'Karte13 Machine City') if gruppe.startswith('k13_') else
                               (OBJEKTGRUPPEN_K12[gruppe], STIL_K12, PALETTE_K12, 'Karte12 Puppet Woods') if gruppe.startswith('k12_')
                               else (OBJEKTGRUPPEN_K11[gruppe], STIL_K11, PALETTE_K11, 'Karte11 Dark Ocean'))
        req = {'description': stil_, 'size': g['size'], 'view': 'top-down',
               'item_descriptions': [it + '. ' + stil_ for it in g['items']],
               'target_palette': {'colors': pal_, 'name': pn_}}
        d = call('POST', '/v2/create-1-direction-object', req)
        oid = d['object_id']
        print(gruppe, 'Objekt', oid)
        d = warte(oid)
        speichern(gruppe, *herunterladen(oid, d))
        return
    if gruppe.startswith('k10_'):
        g = OBJEKTGRUPPEN_K10[gruppe]
        req = {'description': STIL_K10, 'size': g['size'], 'view': 'top-down',
               'item_descriptions': [it + '. ' + STIL_K10 for it in g['items']],
               'target_palette': {'colors': PALETTE_K10, 'name': 'Karte10 Toy Town'}}
        d = call('POST', '/v2/create-1-direction-object', req)
        oid = d['object_id']
        print(gruppe, 'Objekt', oid)
        d = warte(oid)
        speichern(gruppe, *herunterladen(oid, d))
        return
    if gruppe.startswith('k8_') or gruppe.startswith('k9_'):
        g = OBJEKTGRUPPEN_K8[gruppe]
        req = {'description': STIL_K8, 'size': g['size'], 'view': 'top-down',
               'item_descriptions': [it + '. ' + STIL_K8 for it in g['items']],
               'target_palette': {'colors': PALETTE_K8, 'name': 'Karte08 Overdell'}}
        d = call('POST', '/v2/create-1-direction-object', req)
        oid = d['object_id']
        print(gruppe, 'Objekt', oid)
        d = warte(oid)
        speichern(gruppe, *herunterladen(oid, d))
        return
    g = (OBJEKTGRUPPEN_K7 if gruppe.startswith('k7_') else OBJEKTGRUPPEN_K6 if k6 else OBJEKTGRUPPEN_K5 if k5 else OBJEKTGRUPPEN_K4 if k4 else OBJEKTGRUPPEN_K3 if k3 else OBJEKTGRUPPEN_K2 if k2 else OBJEKTGRUPPEN)[gruppe]
    stil, palette = (STIL, PALETTE) if k6 else (STIL_K5, PALETTE_K5) if k5 else (STIL_K4, PALETTE_K4) if k4 else (STIL_K3, PALETTE_K3) if k3 else (STIL_K2, PALETTE_K2) if k2 else (STIL, PALETTE)
    req = {'description': stil, 'size': g['size'], 'view': 'top-down',
           'item_descriptions': [it + '. ' + stil for it in g['items']],
           'target_palette': {'colors': palette, 'name': 'Karte01 handheld' if k6 else 'Karte05 Freezeland' if k5 else 'Karte04 Savanne' if k4 else 'Karte03 Wueste' if k3 else 'Karte02 Industrie' if k2 else 'Karte01 handheld'}}
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
