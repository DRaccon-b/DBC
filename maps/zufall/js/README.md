# Zufalls-Dungeon in JavaScript

Der Dungeon wird beim Betreten im Ladebildschirm aus **vorgerenderten Kartenstücken** zusammengesetzt.
Python rendert die Stücke einmal vorab, JavaScript würfelt im Spiel nur Grundriss und Stückwahl und setzt
die Bilder zusammen (Generator ~15–60 ms, Bilder + Zusammenbau ~80 ms).

| Datei | Inhalt |
|---|---|
| `zufall_dungeon.js` | ES-Modul, engine-unabhängig: Seed → Grundriss → Stücke → Ebenen + Kollision |
| `manifest_<typ>.json` / `.js` | je Kartentyp (`wald`, `netz`) alle 148 Lagen: Kanten, Kollision, Spawn-/Bosspunkt, Gewichte, Bildpfade |
| `stuecke/<typ>/<lage>_boden.png` | reiner Boden (224×224 px, Bossarena 448×448) |
| `stuecke/<typ>/<lage>_schatten.png` | Kontakt- und Schlagschatten (je 4 Kacheln Rand, reichen über die Naht) |
| `stuecke/<typ>/<lage>_objekte.png` | Bäume, Deko, Portal … (je 4 Kacheln Rand für überstehende Kronen) |
| `stuecke/<typ>/<lage>_oben.png` | obere Teile hoher Objekte – wird **über** dem Spieler gezeichnet |
| `demo.html` | Testseite mit **Reitern für den Kartentyp** (Wald / The Network): Ladebildschirm, Spielfigur, Kollision, Kamera |

## Demo starten

Module brauchen einen Webserver (nicht per Doppelklick öffnen):

```bash
cd maps/zufall/js && python3 -m http.server 8000
```

Dann `http://localhost:8000/demo.html` öffnen. Pfeiltasten/WASD laufen, **M** zeigt die ganze Karte,
`?seed=42` in der Adresse lädt einen bestimmten Dungeon.

## Im eigenen Spiel

```js
import { erzeugeDungeon, ladeBilder, zeichneDungeon } from './zufall_dungeon.js';

const manifest = await (await fetch('manifest_netz.json')).json(); // Kartentyp: manifest_wald.json oder manifest_netz.json
// --- Ladebildschirm ---
const dungeon = erzeugeDungeon(manifest, seed, { breite: 6, hoehe: 5 });
const bilder  = await ladeBilder(manifest, dungeon, './');           // lädt nur benutzte Stücke
const { unten, oben } = zeichneDungeon(manifest, dungeon, bilder);   // zwei Canvas in Kartengröße
// --- Spiel ---
// zeichnen: unten → Figuren (nach y sortiert) → oben
// dungeon.istFrei(kx, ky)      begehbar? (Kachelkoordinaten)
// dungeon.kollision            Uint8Array cols*rows: 1 begehbar, 2 gesperrt, 3 begehbar + verdeckt (wie kollision.py)
// dungeon.spawn / dungeon.boss  {x, y} in Kacheln (vor dem Portal / in der Arena)
// dungeon.felder               welches Stück in welcher Lage wo liegt
```

- Gleicher **Seed** + gleiche Größe + gleiches Manifest = gleicher Dungeon (eigener Zufallsgenerator
  `mulberry32`, unabhängig von `Math.random`). Hinweis: Die JS-Seeds ergeben andere Karten als die
  Python-Seeds in `tools/zufall_karte.py`.
- `zeichneDungeon` nimmt optional eine eigene Canvas-Fabrik `(w, h) => canvas` (z. B. `OffscreenCanvas`).
- Für Engines wie Phaser/Pixi: die beiden Canvas als Textur verwenden, oder `dungeon.felder` direkt mit den
  Stückbildern als Sprites setzen (Boden zuerst, dann Objekte von Nord nach Süd, dann oben).

## Stücke neu exportieren

Nach Änderungen an `tools/zufall_stuecke.py` oder an den Objekten:

```bash
python3 tools/zufall_export.py --typ wald
python3 tools/zufall_export.py --typ netz
```

Rendert alle Lagen eines Typs (Wald: aktueller Kachel-Standard A02, Stil Karte 20, 45-Grad-Kanten, `tools/zufall_a02.py`;
Netz: Stil Karte 16, `tools/zufall_netz.py`; je 4 Prozesse, ~15 s). Zeichenreihenfolge: alle Böden → alle Schatten → Objekte von Nord nach Süd → oben. Jede Lage wird mit 4 Kacheln Rand gebaut
(Randkacheln fortgesetzt = genau das, was ein passender Nachbar dort hat); Objekte zählen nur, wenn ihr Fuß im
Stück steht.

## Noch offen

- Animation (Portalwirbel, Lagerfeuer, Wasser, Gras) – kommt mit den Animationsbildern je Stück
- Gegner-/Schatzpunkte je Stück im Manifest
