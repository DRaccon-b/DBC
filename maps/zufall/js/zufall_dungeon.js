/**
 * Zufalls-Dungeon im Stil von Karte 01 – Zusammenbau aus vorgerenderten Kartenstuecken.
 *
 * Engine-unabhaengig (reines JS, ES-Modul). Die Stuecke kommen aus `manifest.json` + `stuecke/*.png`,
 * erzeugt mit `python3 tools/zufall_export.py`.
 *
 *   import { erzeugeDungeon, ladeBilder, zeichneDungeon } from './zufall_dungeon.js';
 *   const manifest = await (await fetch('manifest.json')).json();
 *   const dungeon  = erzeugeDungeon(manifest, 12345, { breite: 6, hoehe: 5 });   // Millisekunden
 *   const bilder   = await ladeBilder(manifest, dungeon, './');                   // nur benoetigte PNGs
 *   const { unten, oben } = zeichneDungeon(manifest, dungeon, bilder);           // zwei Canvas-Ebenen
 *
 * Zeichnen im Spiel: `unten` → Spieler/Gegner → `oben` (Baumkronen, Portalbogen …).
 * dungeon.kollision: Uint8Array (1 = gesperrt), dungeon.spawn / dungeon.boss: Kachelkoordinaten.
 * Gleicher Seed + gleiche Groesse + gleiches Manifest = gleicher Dungeon.
 */

// ------------------------------------------------------------------ Zufall mit Seed
export function zufall(seed) {
  let a = seed >>> 0;
  const random = () => {                       // mulberry32
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
  return {
    random,
    int: (n) => Math.floor(random() * n),
    wahl: (liste) => liste[Math.floor(random() * liste.length)],
  };
}

const RICHT = { N: [0, -1], S: [0, 1], O: [1, 0], W: [-1, 0] };
const GEGEN = { N: 'S', S: 'N', O: 'W', W: 'O' };
const k = (x, y) => x + ',' + y;
const kante = (a, b) => (a < b ? a + '|' + b : b + '|' + a);     // ungerichtete Verbindung zweier Felder

// ------------------------------------------------------------------ 1. Grundriss
function grundriss(rnd, gw, gh) {
  for (let versuch = 0; versuch < 500; versuch++) {
    const bx = rnd.int(gw - 1), by = rnd.int(gh - 1);
    const boss = new Set([k(bx, by), k(bx + 1, by), k(bx, by + 1), k(bx + 1, by + 1)]);
    const bossFelder = [[bx, by], [bx + 1, by], [bx, by + 1], [bx + 1, by + 1]];
    const frei = [];
    for (let x = 0; x < gw; x++) for (let y = 0; y < gh; y++) if (!boss.has(k(x, y))) frei.push([x, y]);
    const dist = ([x, y]) => Math.min(...bossFelder.map(([a, b]) => Math.abs(a - x) + Math.abs(b - y)));
    const weit = Math.max(...frei.map(dist));
    const start = rnd.wahl(frei.filter((c) => dist(c) >= weit - 1));
    const zielLaenge = Math.floor(frei.length * 0.45);
    const nachbarn = ([x, y]) => Object.values(RICHT).map(([dx, dy]) => [x + dx, y + dy])
      .filter(([a, b]) => a >= 0 && a < gw && b >= 0 && b < gh && !boss.has(k(a, b)));
    // Arena nur von Nord/Sued betreten
    const amBoss = ([x, y]) => bossFelder.filter(([a, b]) => a === x && Math.abs(b - y) === 1);

    let bester = null;
    for (let i = 0; i < 3000; i++) {             // zufaellige, selbstvermeidende Wege
      let pfad = [start];
      const drin = new Set([k(...start)]);
      for (;;) {
        const letzt = pfad[pfad.length - 1];
        if (amBoss(letzt).length && pfad.length >= zielLaenge) break;
        const nb = nachbarn(letzt).filter((c) => !drin.has(k(...c)));
        if (!nb.length) { pfad = null; break; }
        const n = rnd.wahl(nb);
        pfad.push(n); drin.add(k(...n));
      }
      if (pfad && (!bester || Math.abs(pfad.length - zielLaenge) < Math.abs(bester.length - zielLaenge))) {
        bester = pfad;
        if (pfad.length === zielLaenge) break;
      }
    }
    if (!bester || bester.length < 3) continue;
    const pfad = bester;
    const verb = new Set();
    for (let i = 0; i + 1 < pfad.length; i++) verb.add(kante(k(...pfad[i]), k(...pfad[i + 1])));
    const eingang = rnd.wahl(amBoss(pfad[pfad.length - 1]));
    verb.add(kante(k(...pfad[pfad.length - 1]), k(...eingang)));
    const belegt = new Set(pfad.map((c) => k(...c)));

    // Abzweigungen in Sackgassen (nie am Startlager)
    const zielBelegt = Math.floor(frei.length * 0.8);
    for (let v = 0; belegt.size < zielBelegt && v < 400; v++) {
      const kand = [...belegt].filter((c) => c !== k(...start)).map((c) => c.split(',').map(Number));
      const ast = [rnd.wahl(kand)];
      const laenge = rnd.wahl([1, 1, 2, 2, 3]);
      for (let j = 0; j < laenge; j++) {
        const nb = nachbarn(ast[ast.length - 1])
          .filter((c) => !belegt.has(k(...c)) && !ast.some((a) => a[0] === c[0] && a[1] === c[1]));
        if (!nb.length) break;
        ast.push(rnd.wahl(nb));
      }
      if (ast.length < 2) continue;
      for (let j = 0; j + 1 < ast.length; j++) verb.add(kante(k(...ast[j]), k(...ast[j + 1])));
      ast.forEach((c) => belegt.add(k(...c)));
    }
    // selten eine Schleife
    const schleifen = [];
    for (const c of belegt) {
      const [x, y] = c.split(',').map(Number);
      for (const [dx, dy] of [[1, 0], [0, 1]]) {
        const d = k(x + dx, y + dy);
        if (belegt.has(d) && c !== k(...start) && d !== k(...start) && !verb.has(kante(c, d))) schleifen.push(kante(c, d));
      }
    }
    if (schleifen.length && rnd.random() < 0.6) verb.add(rnd.wahl(schleifen));
    return { boss: [bx, by], bossFelder: boss, start, belegt, verb };
  }
  throw new Error('kein Grundriss gefunden');
}

// ------------------------------------------------------------------ 2. Stuecke einsetzen (Backtracking)
function einsetzen(rnd, gw, gh, g, lagen) {
  const [bx, by] = g.boss;
  const startK = k(...g.start);
  const einheiten = [{ art: 'boss', x: bx, y: by, gr: 2 }];
  // Startlager zuerst, dann in Wegrichtung (Breitensuche), dann Boss, dann Wald
  const reihe = [startK], gesehen = new Set([startK]);
  for (let i = 0; i < reihe.length; i++) {
    const [x, y] = reihe[i].split(',').map(Number);
    for (const [dx, dy] of Object.values(RICHT)) {
      const d = k(x + dx, y + dy);
      if (g.belegt.has(d) && !gesehen.has(d) && g.verb.has(kante(reihe[i], d))) { gesehen.add(d); reihe.push(d); }
    }
  }
  for (const c of g.belegt) if (!gesehen.has(c)) reihe.push(c);
  const geordnet = reihe.map((c) => {
    const [x, y] = c.split(',').map(Number);
    return { art: c === startK ? 'start' : 'normal', x, y, gr: 1 };
  });
  geordnet.push(einheiten[0]);
  for (let x = 0; x < gw; x++) for (let y = 0; y < gh; y++) {
    if (!g.belegt.has(k(x, y)) && !g.bossFelder.has(k(x, y))) geordnet.push({ art: 'wald', x, y, gr: 1 });
  }

  const gesetzt = new Map();                     // "x,y,S" -> Kantentyp
  const benutzt = {};
  const wahl = [];
  const soll = (fx, fy, s) => {
    const nx = fx + RICHT[s][0], ny = fy + RICHT[s][1];
    return { offen: g.verb.has(kante(k(fx, fy), k(nx, ny))), nachbar: gesetzt.get(k(nx, ny) + ',' + GEGEN[s]) };
  };
  const kandidaten = (e) => {
    const out = [];
    for (const l of lagen) {
      if (l.typ !== e.art || l.felder[0] !== e.gr || l.felder[1] !== e.gr) continue;
      let ok = true;
      for (const [schl, t] of Object.entries(l.kanten)) {
        const [fx, fy, s] = schl.split(',');
        const { offen, nachbar } = soll(e.x + +fx, e.y + +fy, s);
        if ((t !== 'Z') !== offen || (nachbar !== undefined && nachbar !== t)) { ok = false; break; }
      }
      if (!ok) continue;
      const gew = l.gewicht / l.lagenDesStuecks / (1 + 3 * (benutzt[l.name] || 0)) ** 2;
      out.push([rnd.random() ** (1 / gew), l]);   // gewichtetes Mischen
    }
    return out.sort((a, b) => b[0] - a[0]).map((t) => t[1]);
  };
  let schritte = 0;                              // Schrittlimit: schlechte Grundrisse aufgeben
  const setzen = (i) => {
    if (i === geordnet.length) return true;
    if (++schritte > 3000) throw new Error('Schrittlimit');
    const e = geordnet[i];
    for (const l of kandidaten(e)) {
      const neu = Object.entries(l.kanten).map(([schl, t]) => {
        const [fx, fy, s] = schl.split(',');
        const key = k(e.x + +fx, e.y + +fy) + ',' + s;
        gesetzt.set(key, t);
        return key;
      });
      benutzt[l.name] = (benutzt[l.name] || 0) + 1;
      wahl.push({ x: e.x, y: e.y, lage: l });
      if (setzen(i + 1)) return true;
      wahl.pop();
      benutzt[l.name]--;
      neu.forEach((key) => gesetzt.delete(key));
    }
    return false;
  };
  if (!setzen(0)) throw new Error('Stuecke passen nicht zum Grundriss');
  return wahl;
}

// ------------------------------------------------------------------ Oeffentliche API
export function erzeugeDungeon(manifest, seed, { breite = 6, hoehe = 5 } = {}) {
  const rnd = zufall(seed);
  let felder = null;
  for (let i = 0; i < 50 && !felder; i++) {
    const g = grundriss(rnd, breite, hoehe);
    try { felder = einsetzen(rnd, breite, hoehe, g, manifest.lagen); } catch (e) { /* neuer Grundriss */ }
  }
  if (!felder) throw new Error('kein passender Dungeon fuer Seed ' + seed);
  const N = manifest.feld;
  const cols = breite * N, rows = hoehe * N;
  const kollision = new Uint8Array(cols * rows);
  let spawn = null, boss = null;
  for (const f of felder) {
    const l = f.lage;
    l.kollision.forEach((zeile, y) => {
      for (let x = 0; x < zeile.length; x++) kollision[(f.y * N + y) * cols + f.x * N + x] = zeile.charCodeAt(x) - 48;
    });
    if (l.punkte.spawn) spawn = { x: f.x * N + l.punkte.spawn[0], y: f.y * N + l.punkte.spawn[1] };
    if (l.punkte.boss) boss = { x: f.x * N + l.punkte.boss[0], y: f.y * N + l.punkte.boss[1] };
  }
  return {
    seed, breite, hoehe, cols, rows, kachel: manifest.kachel, kollision, spawn, boss,
    felder: felder.map((f) => ({ x: f.x, y: f.y, id: f.lage.id, name: f.lage.name, lage: f.lage })),
    istFrei: (x, y) => x >= 0 && y >= 0 && x < cols && y < rows && kollision[y * cols + x] === 0,
  };
}

/** Laedt nur die Bilder der benutzten Lagen. basisUrl: Ordner mit manifest.json. */
export async function ladeBilder(manifest, dungeon, basisUrl = './') {
  const lade = (src) => new Promise((ok, fehler) => {
    const im = new Image();
    im.onload = () => ok(im);
    im.onerror = () => fehler(new Error('Bild fehlt: ' + src));
    im.src = basisUrl + src;
  });
  const bilder = new Map();
  await Promise.all([...new Set(dungeon.felder.map((f) => f.lage))].map(async (l) => {
    const [boden, objekte, oben] = await Promise.all([lade(l.boden), lade(l.objekte), lade(l.oben)]);
    bilder.set(l.id, { boden, objekte, oben });
  }));
  return bilder;
}

/** Setzt die Stueckbilder zu zwei Ebenen zusammen (Canvas in Kartengroesse). */
export function zeichneDungeon(manifest, dungeon, bilder, erzeugeCanvas) {
  const T = manifest.kachel, N = manifest.feld, R = manifest.rand;
  const neu = erzeugeCanvas || ((w, h) => Object.assign(document.createElement('canvas'), { width: w, height: h }));
  const unten = neu(dungeon.cols * T, dungeon.rows * T);
  const oben = neu(dungeon.cols * T, dungeon.rows * T);
  const cu = unten.getContext('2d'), co = oben.getContext('2d');
  cu.imageSmoothingEnabled = co.imageSmoothingEnabled = false;
  // 1. Boden aller Stuecke, 2. Objekte von Nord nach Sued (ueberstehende Kronen suedlicher Stuecke liegen
  //    vor dem noerdlichen Stueck), 3. obere Ebene genauso
  for (const f of dungeon.felder) cu.drawImage(bilder.get(f.id).boden, f.x * N * T, f.y * N * T);
  const reihe = [...dungeon.felder].sort((a, b) => (a.y + a.lage.felder[1]) - (b.y + b.lage.felder[1]) || a.x - b.x);
  for (const f of reihe) {
    const b = bilder.get(f.id);
    const px = (f.x * N - R) * T, py = (f.y * N - R) * T;
    cu.drawImage(b.objekte, px, py);
    co.drawImage(b.oben, px, py);
  }
  return { unten, oben };
}
