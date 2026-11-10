/*!
 * Random Dungeon Kit – assembles a random forest dungeon from pre-rendered map pieces.
 *
 * No dependencies, no build step, no web server required.
 *   Browser:  <script src="pieces.js"></script> <script src="random_dungeon.js"></script>
 *             → window.RandomDungeon, manifest in window.RANDOM_DUNGEON_PIECES
 *   Node:     const RandomDungeon = require('./random_dungeon.js');   (generate() works without a DOM)
 *   Bundlers: import RandomDungeon from './random_dungeon.js';
 *
 * Quick start (see README.md):
 *   const dungeon = RandomDungeon.generate(manifest, seed, { width: 6, height: 5 });
 *   const images  = await RandomDungeon.loadImages(manifest, dungeon, './');
 *   const layers  = RandomDungeon.render(manifest, dungeon, images);      // { below, above } canvases
 *   draw: layers.below → characters → layers.above
 *
 * Same seed + same size + same manifest = same dungeon.
 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.RandomDungeon = factory();
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  // ---------------------------------------------------------------- seeded random numbers (mulberry32)
  function createRandom(seed) {
    let a = seed >>> 0;
    const random = () => {
      a = (a + 0x6d2b79f5) >>> 0;
      let t = a;
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
    return { random, int: (n) => Math.floor(random() * n), pick: (list) => list[Math.floor(random() * list.length)] };
  }

  const DIR = { N: [0, -1], S: [0, 1], E: [1, 0], W: [-1, 0] };
  const OPPOSITE = { N: 'S', S: 'N', E: 'W', W: 'E' };
  const key = (x, y) => x + ',' + y;
  const link = (a, b) => (a < b ? a + '|' + b : b + '|' + a);       // undirected connection of two cells
  const parse = (k) => k.split(',').map(Number);

  // ---------------------------------------------------------------- 1. layout on the coarse cell grid
  function makeLayout(rnd, gw, gh) {
    for (let attempt = 0; attempt < 500; attempt++) {
      const bx = rnd.int(gw - 1), by = rnd.int(gh - 1);                // boss arena: 2 x 2 cells
      const bossCells = [[bx, by], [bx + 1, by], [bx, by + 1], [bx + 1, by + 1]];
      const boss = new Set(bossCells.map((c) => key(...c)));
      const free = [];
      for (let x = 0; x < gw; x++) for (let y = 0; y < gh; y++) if (!boss.has(key(x, y))) free.push([x, y]);
      const dist = ([x, y]) => Math.min(...bossCells.map(([a, b]) => Math.abs(a - x) + Math.abs(b - y)));
      const far = Math.max(...free.map(dist));
      const start = rnd.pick(free.filter((c) => dist(c) >= far - 1));   // start camp far from the boss
      const targetLength = Math.floor(free.length * 0.45);
      const neighbours = ([x, y]) => Object.values(DIR).map(([dx, dy]) => [x + dx, y + dy])
        .filter(([a, b]) => a >= 0 && a < gw && b >= 0 && b < gh && !boss.has(key(a, b)));
      const nextToBoss = ([x, y]) => bossCells.filter(([a, b]) => a === x && Math.abs(b - y) === 1);  // N/S entry only

      let best = null;
      for (let i = 0; i < 3000; i++) {                                 // random self-avoiding walks
        let path = [start];
        const inPath = new Set([key(...start)]);
        for (;;) {
          const last = path[path.length - 1];
          if (nextToBoss(last).length && path.length >= targetLength) break;
          const options = neighbours(last).filter((c) => !inPath.has(key(...c)));
          if (!options.length) { path = null; break; }
          const n = rnd.pick(options);
          path.push(n); inPath.add(key(...n));
        }
        if (path && (!best || Math.abs(path.length - targetLength) < Math.abs(best.length - targetLength))) {
          best = path;
          if (path.length === targetLength) break;
        }
      }
      if (!best || best.length < 3) continue;
      const path = best;
      const links = new Set();
      for (let i = 0; i + 1 < path.length; i++) links.add(link(key(...path[i]), key(...path[i + 1])));
      links.add(link(key(...path[path.length - 1]), key(...rnd.pick(nextToBoss(path[path.length - 1])))));
      const used = new Set(path.map((c) => key(...c)));

      // side branches ending in dead ends (never at the start camp)
      const targetUsed = Math.floor(free.length * 0.8);
      for (let t = 0; used.size < targetUsed && t < 400; t++) {
        const branch = [rnd.pick([...used].filter((c) => c !== key(...start)).map(parse))];
        const length = rnd.pick([1, 1, 2, 2, 3]);
        for (let j = 0; j < length; j++) {
          const options = neighbours(branch[branch.length - 1])
            .filter((c) => !used.has(key(...c)) && !branch.some((b) => b[0] === c[0] && b[1] === c[1]));
          if (!options.length) break;
          branch.push(rnd.pick(options));
        }
        if (branch.length < 2) continue;
        for (let j = 0; j + 1 < branch.length; j++) links.add(link(key(...branch[j]), key(...branch[j + 1])));
        branch.forEach((c) => used.add(key(...c)));
      }
      // sometimes one loop
      const loops = [];
      for (const c of used) {
        const [x, y] = parse(c);
        for (const [dx, dy] of [[1, 0], [0, 1]]) {
          const d = key(x + dx, y + dy);
          if (used.has(d) && c !== key(...start) && d !== key(...start) && !links.has(link(c, d))) loops.push(link(c, d));
        }
      }
      if (loops.length && rnd.random() < 0.6) links.add(rnd.pick(loops));
      return { boss: [bx, by], bossCells: boss, start, used, links };
    }
    throw new Error('no layout found');
  }

  // ---------------------------------------------------------------- 2. fit pieces (backtracking)
  function fitPieces(rnd, gw, gh, layout, pieces) {
    const startKey = key(...layout.start);
    const order = [startKey], seen = new Set([startKey]);              // start, then along the paths (BFS)
    for (let i = 0; i < order.length; i++) {
      const [x, y] = parse(order[i]);
      for (const [dx, dy] of Object.values(DIR)) {
        const d = key(x + dx, y + dy);
        if (layout.used.has(d) && !seen.has(d) && layout.links.has(link(order[i], d))) { seen.add(d); order.push(d); }
      }
    }
    for (const c of layout.used) if (!seen.has(c)) order.push(c);
    // boss arena first (most constrained), then start camp and the cells along the paths, then forest
    const units = [{ type: 'boss', x: layout.boss[0], y: layout.boss[1], size: 2 }].concat(order.map((c) => {
      const [x, y] = parse(c);
      return { type: c === startKey ? 'start' : 'normal', x, y, size: 1 };
    }));
    for (let x = 0; x < gw; x++) for (let y = 0; y < gh; y++) {
      if (!layout.used.has(key(x, y)) && !layout.bossCells.has(key(x, y))) units.push({ type: 'forest', x, y, size: 1 });
    }

    const placedEdges = new Map();                                      // "x,y,side" -> edge type
    const useCount = {};
    const result = [];
    const expect = (cx, cy, side) => {
      const nx = cx + DIR[side][0], ny = cy + DIR[side][1];
      return { open: layout.links.has(link(key(cx, cy), key(nx, ny))), neighbour: placedEdges.get(key(nx, ny) + ',' + OPPOSITE[side]) };
    };
    const candidates = (u) => {
      const out = [];
      for (const p of pieces) {
        if (p.type !== u.type || p.cells[0] !== u.size || p.cells[1] !== u.size) continue;
        let ok = true;
        for (const [k, t] of Object.entries(p.edges)) {
          const [fx, fy, side] = k.split(',');
          const { open, neighbour } = expect(u.x + +fx, u.y + +fy, side);
          if ((t !== 'C') !== open || (neighbour !== undefined && neighbour !== t)) { ok = false; break; }
        }
        if (!ok) continue;
        const weight = p.weight / p.orientationsOfChunk / (1 + 3 * (useCount[p.chunk] || 0)) ** 2;  // repeats get rarer
        out.push([rnd.random() ** (1 / weight), p]);                    // weighted shuffle
      }
      return out.sort((a, b) => b[0] - a[0]).map((t) => t[1]);
    };
    let steps = 0;                                                      // step budget: give up on bad layouts
    const place = (i) => {
      if (i === units.length) return true;
      if (++steps > 3000) throw new Error('step budget exceeded');
      const u = units[i];
      for (const p of candidates(u)) {
        const added = Object.entries(p.edges).map(([k, t]) => {
          const [fx, fy, side] = k.split(',');
          const ek = key(u.x + +fx, u.y + +fy) + ',' + side;
          placedEdges.set(ek, t);
          return ek;
        });
        useCount[p.chunk] = (useCount[p.chunk] || 0) + 1;
        result.push({ x: u.x, y: u.y, piece: p });
        if (place(i + 1)) return true;
        result.pop();
        useCount[p.chunk]--;
        added.forEach((ek) => placedEdges.delete(ek));
      }
      return false;
    };
    if (!place(0)) throw new Error('pieces do not fit the layout');
    return result;
  }

  // ---------------------------------------------------------------- public API
  /** Builds the dungeon data (layout, pieces, collision, spawn/boss). Fast (a few ms), no DOM needed. */
  function generate(manifest, seed, options) {
    const width = (options && options.width) || 6, height = (options && options.height) || 5;
    const rnd = createRandom(seed);
    let cells = null;
    for (let i = 0; i < 50 && !cells; i++) {
      const layout = makeLayout(rnd, width, height);
      try { cells = fitPieces(rnd, width, height, layout, manifest.pieces); } catch (e) { /* try another layout */ }
    }
    if (!cells) throw new Error('no dungeon found for seed ' + seed);
    const N = manifest.chunkSize, cols = width * N, rows = height * N;
    const collision = new Uint8Array(cols * rows);
    let spawn = null, boss = null;
    for (const c of cells) {
      const p = c.piece;
      p.collision.forEach((line, y) => {
        for (let x = 0; x < line.length; x++) collision[(c.y * N + y) * cols + c.x * N + x] = line.charCodeAt(x) - 48;
      });
      if (p.points.spawn) spawn = { x: c.x * N + p.points.spawn[0], y: c.y * N + p.points.spawn[1] };
      if (p.points.boss) boss = { x: c.x * N + p.points.boss[0], y: c.y * N + p.points.boss[1] };
    }
    return {
      seed, width, height, cols, rows, tileSize: manifest.tileSize, collision, spawn, boss,
      cells: cells.map((c) => ({ x: c.x, y: c.y, id: c.piece.id, chunk: c.piece.chunk, piece: c.piece })),
      isWalkable: (x, y) => x >= 0 && y >= 0 && x < cols && y < rows && collision[y * cols + x] === 0,
    };
  }

  function loadImage(src) {
    return new Promise((resolve, reject) => {
      const img = new Image();
      img.onload = () => resolve(img);
      img.onerror = () => reject(new Error('missing image: ' + src));
      img.src = src;
    });
  }

  /** Loads only the images of the pieces used by this dungeon, plus the object tileset. */
  async function loadImages(manifest, dungeon, baseUrl) {
    const base = baseUrl || '';
    const pieces = new Map();
    const used = [...new Map(dungeon.cells.map((c) => [c.id, c.piece])).values()];
    await Promise.all(used.map(async (p) => {
      const [ground, objects, above] = await Promise.all([p.ground, p.objects, p.above].map((f) => loadImage(base + f)));
      pieces.set(p.id, { ground, objects, above });
    }));
    const tileset = await loadImage(base + manifest.tileset.image);
    return { pieces, tileset };
  }

  const defaultCanvas = (w, h) => Object.assign(document.createElement('canvas'), { width: w, height: h });

  /** Ground only (with baked contact shadows) – use with objects() when you draw objects yourself. */
  function renderGround(manifest, dungeon, images, createCanvas) {
    const T = manifest.tileSize, N = manifest.chunkSize;
    const canvas = (createCanvas || defaultCanvas)(dungeon.cols * T, dungeon.rows * T);
    const ctx = canvas.getContext('2d');
    ctx.imageSmoothingEnabled = false;
    for (const c of dungeon.cells) ctx.drawImage(images.pieces.get(c.id).ground, c.x * N * T, c.y * N * T);
    return canvas;
  }

  /** Two ready layers: below (ground + all objects) and above (upper parts of tall objects). */
  function render(manifest, dungeon, images, createCanvas) {
    const T = manifest.tileSize, N = manifest.chunkSize, P = manifest.padding;
    const below = renderGround(manifest, dungeon, images, createCanvas);
    const above = (createCanvas || defaultCanvas)(dungeon.cols * T, dungeon.rows * T);
    const cb = below.getContext('2d'), ca = above.getContext('2d');
    ca.imageSmoothingEnabled = false;
    // north to south: crowns of southern pieces reaching north are drawn in front of the northern piece
    const order = [...dungeon.cells].sort((a, b) => (a.y + a.piece.cells[1]) - (b.y + b.piece.cells[1]) || a.x - b.x);
    for (const c of order) {
      const img = images.pieces.get(c.id);
      const px = (c.x * N - P) * T, py = (c.y * N - P) * T;
      cb.drawImage(img.objects, px, py);
      ca.drawImage(img.above, px, py);
    }
    return { below, above };
  }

  /**
   * Every object of the dungeon as its own sprite (from the object tileset), sorted by foot position.
   * x/y: top-left in map pixels; footY: bottom edge (sort characters against this);
   * splitY: top of the base tile row – the part above it covers characters walking behind the object;
   * sx/sy/w/h: rectangle in objects_tileset.png; blockTiles: occupied tile block [x, y, w, h] in map tiles.
   */
  function objects(manifest, dungeon) {
    const T = manifest.tileSize, N = manifest.chunkSize, sprites = manifest.tileset.sprites;
    const out = [];
    for (const c of dungeon.cells) {
      const ox = c.x * N * T, oy = c.y * N * T;
      for (const o of c.piece.objectList) {
        const s = sprites[o.sprite];
        const [bx, by, bw, bh] = o.block;
        out.push({
          sprite: o.sprite, x: ox + o.x, y: oy + o.y, w: s.w, h: s.h, sx: s.x, sy: s.y,
          footY: oy + (by + bh) * T, splitY: oy + (by + bh - 1) * T, layer: o.layer,
          blockTiles: [c.x * N + bx, c.y * N + by, bw, bh], anim: o.anim || null, flip: !!o.flip,
        });
      }
    }
    return out.sort((a, b) => a.layer - b.layer || a.footY - b.footY);
  }

  /** Draws one object from objects(); part = 'all' | 'top' (above splitY) | 'bottom'. */
  function drawObject(ctx, tileset, o, part) {
    let sy = o.sy, y = o.y, h = o.h;
    if (part === 'top') h = Math.max(0, Math.min(o.h, o.splitY - o.y));
    if (part === 'bottom') { const cut = Math.max(0, Math.min(o.h, o.splitY - o.y)); sy += cut; y += cut; h -= cut; }
    if (h <= 0) return;
    if (o.flip) {
      ctx.save(); ctx.translate(o.x + o.w, 0); ctx.scale(-1, 1);
      ctx.drawImage(tileset, o.sx, sy, o.w, h, 0, y, o.w, h);
      ctx.restore();
    } else ctx.drawImage(tileset, o.sx, sy, o.w, h, o.x, y, o.w, h);
  }

  return { generate, loadImages, render, renderGround, objects, drawObject, createRandom, version: '1.0.0' };
});
