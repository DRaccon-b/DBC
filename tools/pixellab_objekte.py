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
    if gruppe.startswith('k7_'):
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
