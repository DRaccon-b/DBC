# Random Dungeon Kit

Random forest dungeons for a top-down pixel-art RPG (16 × 16 px tiles), assembled from **hand-made,
pre-rendered map pieces** – the same idea as the maps in *Path of Exile*: the pieces are designed by hand,
only their arrangement is random. A dungeon is generated while a short loading screen is shown and is then
fully available.

- **145 finished map pieces** (20 hand-made chunks in up to 8 orientations), each as separate images
- **All objects in one tileset image** (`objects_tileset.png`) with coordinates
- **One JavaScript file**, no dependencies, no build step, **no web server needed**
- **Tiled map files**: every piece as `.tmx`, generated dungeons as `.tmj` (`toTiled()`), shared tilesets
- Same seed → same dungeon

![all pieces](preview/all_pieces.png)

## Contents

```
random_dungeon_kit/
├── random_dungeon.js          the generator (browser <script>, Node require, or bundler import)
├── pieces.js                  piece manifest as a script (works from file://)
├── pieces.json                the same manifest as JSON (for fetch / engines / tools)
├── objects_tileset.png        every object sprite once, aligned to the 16 px grid, grouped
├── objects_tileset.json       sprite rectangles in the tileset (also inside the manifest)
├── demo.html                  playable demo – just double-click it
├── pieces/
│   ├── <id>_ground.png        ground incl. contact shadows, exact piece size (224 × 224, arena 448 × 448)
│   ├── <id>_objects.png       trees, decoration, portal … (+4 tiles padding for overhanging crowns)
│   ├── <id>_above.png         upper parts of tall objects – draw ABOVE characters (same size as _objects)
│   └── <id>_preview.png       the finished piece in one image (ground + objects + above)
├── tiled/                     Tiled map editor files (Tiled 1.10+)
│   ├── ground_tiles.png/.tsx  all ground tiles of all pieces, 16 × 16, duplicates merged
│   ├── objects.tsx            image-collection tileset, one PNG per sprite in sprites/
│   ├── collision.png/.tsx     one "blocked" tile (property blocked = true)
│   ├── pieces/<id>.tmx        every piece as a Tiled map
│   └── examples/              two complete dungeons (seed 7 and 42) as .tmj
├── chunks/
│   ├── chunks.json            the 20 hand-made chunks as tile grids, edges, fixed objects
│   └── chunks_overview.png
└── preview/                   all_pieces.png, objects_tileset_2x.png, system_explained.png, demo screenshots
```

## Try it

Open `demo.html` in a browser (double-click). Arrow keys / WASD move the placeholder character, **M** toggles
the whole map, **O** switches between the two drawing modes, `?seed=42` in the address loads a specific dungeon.

## How it works

1. **Layout** – on a coarse grid (default 6 × 5 cells, one cell = one 14 × 14 tile piece) the boss arena
   (2 × 2 cells) and the start camp are placed far apart. A winding main path connects them, side branches end
   in dead ends, sometimes there is a loop. Unused cells become dense forest.
2. **Fit pieces** – every piece side has an edge type, read from its outer two tile rows:

   | type | outer tile rows   | meaning              |
   |------|-------------------|----------------------|
   | `C`  | `FFFFFFFFFFFFFF`  | closed (forest)      |
   | `P`  | `FFFFGGPPGGFFFF`  | narrow forest path   |
   | `O`  | `FFGGGGPPGGGGFF`  | open meadow with path|

   (`F` forest, `G` meadow, `P` sand path.) For every cell a random piece is chosen whose edges match the
   layout (closed where there is no connection) and the neighbours (same type on both sides). If nothing fits,
   the solver steps back (backtracking). Pieces used often are picked less often.
3. **Assemble** – the pre-rendered images are put together; collision, spawn and boss position come from
   the manifest. Generation takes ~15–70 ms, loading the images and assembling ~100 ms.

Because the path always crosses an edge in the middle (tiles 6–7) and the edge rows are standardised, rotated
and mirrored pieces connect seamlessly.

## Using it in your game

```html
<script src="pieces.js"></script>
<script src="random_dungeon.js"></script>
<script>
  const manifest = window.RANDOM_DUNGEON_PIECES;
  async function enterDungeon(seed) {
    // --- loading screen ---
    const dungeon = RandomDungeon.generate(manifest, seed, { width: 6, height: 5 });
    const images  = await RandomDungeon.loadImages(manifest, dungeon, 'path/to/random_dungeon_kit/');
    const layers  = RandomDungeon.render(manifest, dungeon, images);   // { below, above } canvases
    // --- game loop: draw layers.below → characters → layers.above ---
  }
</script>
```

Node / bundler: `const RandomDungeon = require('./random_dungeon.js')` and `fetch('pieces.json')` (or `require`).
`generate()` needs no DOM – you can create dungeons on a server, e.g. to share the seed between players.

### API

| function | returns |
|---|---|
| `generate(manifest, seed, { width, height })` | dungeon data (below) – synchronous, no DOM |
| `loadImages(manifest, dungeon, baseUrl)` | `Promise<{ pieces: Map<id,{ground,objects,above}>, tileset }>` – only the pieces this dungeon uses |
| `render(manifest, dungeon, images, createCanvas?)` | `{ below, above }` – two canvases of map size |
| `renderGround(manifest, dungeon, images, createCanvas?)` | ground canvas only (for sprite mode) |
| `objects(manifest, dungeon)` | every object as its own sprite, sorted by `layer`, then `footY` |
| `drawObject(ctx, tileset, object, part)` | draws one object; `part` = `'all'`, `'top'` (above its base row) or `'bottom'` |
| `toTiled(manifest, dungeon, { imageBase })` | the whole dungeon as a Tiled map object (TMJ), tilesets embedded |
| `createRandom(seed)` | the seeded random generator used internally (mulberry32) |

`createCanvas(w, h)` is optional, e.g. `(w, h) => new OffscreenCanvas(w, h)`.

**Dungeon data**

| field | meaning |
|---|---|
| `cols`, `rows`, `tileSize` | map size in tiles (6 × 5 cells = 84 × 70 tiles = 1344 × 1120 px) |
| `collision` | `Uint8Array(cols * rows)`, `1` = blocked (forest, water, base row of objects) |
| `isWalkable(x, y)` | tile test, `false` outside the map |
| `spawn`, `boss` | `{x, y}` in tiles: in front of the portal / in the arena |
| `cells` | `[{x, y, id, chunk, piece}]` – which piece lies on which cell |

### Two ways to draw

1. **Baked layers** (`render`) – simplest: `below` under the characters, `above` (tree crowns, portal arch)
   over them. Characters walking behind a tree are hidden by its crown.
2. **Single sprites** (`renderGround` + `objects` + `drawObject`) – draw the ground canvas, then all objects
   from the tileset sorted together with your characters by their foot y (`footY`). Gives exact depth order and
   lets you animate single objects (`anim`: `sway` grass/flowers, `bob` lily pads, `lantern`).
   Object `x`/`y` are the top-left corner in map pixels; `sx`/`sy`/`w`/`h` the rectangle in the tileset;
   `blockTiles` the occupied tile block. Only the bottom row of a block is solid (already in `collision`).

## Tiled

Open any file in `tiled/pieces/` or `tiled/examples/` with the [Tiled map editor](https://www.mapeditor.org/)
(1.10 or newer). Every map has the same layers:

| layer | type | content |
|---|---|---|
| `ground` | tile layer | ground incl. baked contact shadows (tileset `ground`) |
| `objects` | object layer | one tile object per tree / decoration / portal … (tileset `objects`), properties `sprite`, `layer` (0 = flat, 1 = standing), `anim` |
| `collision` | tile layer, hidden | `blocked` tile where the player cannot walk |
| `points` | object layer | point objects `spawn` (in front of the portal) and `boss` |

Piece maps also carry map properties `chunk`, `pieceOrientation`, `pieceType` and `edges` (JSON).
Tile objects use Tiled's usual bottom-left anchor; sort them by `y` to get the correct depth order with
characters. Tile ids in `ground_tiles.png` are shared by all pieces, so pieces placed next to each other in
Tiled form one map with one tileset.

**Your own dungeon as a Tiled map:** in the demo press **Download .tmj** and save the file into the kit folder
(next to `demo.html`), or in code:

```js
const map = RandomDungeon.toTiled(manifest, dungeon, { imageBase: '' });   // path from the .tmj to the kit
const json = JSON.stringify(map);                                         // save as dungeon.tmj
```

The tilesets are embedded in the `.tmj` (image paths relative to the file), so loaders that need embedded
tilesets (e.g. Phaser) work as well. The `.tmx` piece files reference the shared `.tsx` tilesets.

## Manifest (`pieces.json` / `pieces.js`)

```js
{
  tileSize: 16, chunkSize: 14, padding: 4,          // padding: extra tiles around _objects/_above images
  edgeTypes: { C, P, O },
  tileset: { image: 'objects_tileset.png', sprites: { '<name>': { x, y, w, h, block: [tx, ty, tw, th], group } } },
  pieces: [{
    id: 'path_corner_m90',                          // <chunk>_<orientation>
    chunk: 'path_corner', orientation: 'm90',       // r = rotated clockwise, m = mirrored first, then rotated
    type: 'normal',                                 // start | boss | normal | forest
    weight: 3, orientationsOfChunk: 4,
    cells: [1, 1],                                  // size in cells (boss arena: [2, 2])
    edges: { '0,0,N': 'P', '0,0,E': 'P', '0,0,S': 'C', '0,0,W': 'C' },   // cellX,cellY,side
    ground, objects, above, preview,                // image paths
    collision: ['11110000001111', …],               // 14 rows per cell, '1' = blocked
    points: { spawn: [x, y] } | { boss: [x, y] },   // tile inside the piece
    objectList: [{ sprite, x, y, block: [tx, ty, tw, th], layer, anim?, flip? }],  // px / tiles inside the piece
    groundTiles: [ … ]                              // ids in tiled/ground_tiles.png, row by row
  }],
  tiled: { ground, objects, collision }             // tileset info used by toTiled()
}
```

Image placement: `ground` at `(cellX * 14) * 16`, `objects`/`above` at `(cellX * 14 - padding) * 16`
(same for y). Draw all grounds first, then objects north to south.

## Chunks

| chunk | edges | notes |
|---|---|---|
| `path_bend`, `pond_by_path` | path – path | winding forest path, pond beside the path |
| `meadow_pond`, `meadow_pink_tree` | open – open | meadow with pond / pink blossom tree |
| `path_to_meadow` | path – open | transition forest path ↔ meadow |
| `path_corner`, `meadow_corner`, `corner_path_meadow` | corner | |
| `path_fork`, `meadow_fork` | T junction | |
| `path_cross`, `meadow_cross` | crossing | |
| `deadend_pond`, `deadend_well`, `deadend_meadow`, `deadend_boulder`, `glade_rune_tree` | dead end | |
| `start_camp` | dead end | rune portal (spawn), campfire, signpost |
| `boss_jungle_tree` | 2 × 2 cells | giant jungle tree with a symmetric pair of rune stones; rotates 180° only |
| `forest` | closed | filler |

## Notes

- The seed generator is `mulberry32`, independent of `Math.random`, so a seed gives the same dungeon on every
  device and in Node.
- Not animated yet: portal vortex, campfire, water and grass are static in the images. The objects that should
  move are marked with `anim` in `objectList`.
- Art style: polished handheld monster-RPG look, light from the upper left, frontal view.
