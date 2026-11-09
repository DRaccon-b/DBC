# Zufalls-Dungeon in JavaScript

Der Dungeon wird beim Betreten im Ladebildschirm aus **vorgerenderten Kartenstücken** zusammengesetzt.
Python rendert die Stücke einmal vorab, JavaScript würfelt im Spiel nur Grundriss und Stückwahl und setzt
die Bilder zusammen (Generator ~15–60 ms, Bilder + Zusammenbau ~80 ms).

| Datei | Inhalt |
|---|---|
| `zufall_dungeon.js` | ES-Modul, engine-unabhängig: Seed → Grundriss → Stücke → Ebenen + Kollision |
| `manifest.json` | alle 145 Lagen: Kanten, Kollision, Spawn-/Bosspunkt, Gewichte, Bildpfade |
| `stuecke/<lage>_boden.png` | Boden mit Schatten (224×224 px, Bossarena 448×448) |
| `stuecke/<lage>_objekte.png` | Bäume, Deko, Portal … (je 4 Kacheln Rand für überstehende Kronen) |
| `stuecke/<lage>_oben.png` | obere Teile hoher Objekte – wird **über** dem Spieler gezeichnet |
| `demo.html` | Testseite: Ladebildschirm, Spielfigur, Kollision, Kamera |

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

const manifest = await (await fetch('manifest.json')).json();      // einmal beim Spielstart
// --- Ladebildschirm ---
const dungeon = erzeugeDungeon(manifest, seed, { breite: 6, hoehe: 5 });
const bilder  = await ladeBilder(manifest, dungeon, './');           // lädt nur benutzte Stücke
const { unten, oben } = zeichneDungeon(manifest, dungeon, bilder);   // zwei Canvas in Kartengröße
// --- Spiel ---
// zeichnen: unten → Figuren (nach y sortiert) → oben
// dungeon.istFrei(kx, ky)      begehbar? (Kachelkoordinaten)
// dungeon.kollision            Uint8Array cols*rows, 1 = gesperrt (Wald, Wasser, Sockel von Objekten)
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
python3 tools/zufall_export.py
```

Rendert alle Lagen mit der Karte-01-Technik (4 Prozesse, ~25 s). Jede Lage wird mit 4 Kacheln Rand gebaut
(Randkacheln fortgesetzt = genau das, was ein passender Nachbar dort hat); Objekte zählen nur, wenn ihr Fuß im
Stück steht. Laternen gibt es nur an Startlager, Arena und Gabelungen.

## Noch offen

- Animation (Portalwirbel, Lagerfeuer, Wasser, Gras) – kommt mit den Animationsbildern je Stück
- Gegner-/Schatzpunkte je Stück im Manifest
