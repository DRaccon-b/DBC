# Karte 01 – Spiel-Ebenen

Erzeugt mit `python3 tools/karte01_ebenen.py` aus derselben Platzierung wie `terrain.png`
(110 × 120 Kacheln à 16 px).

| Datei | Inhalt |
|---|---|
| `ebene1_boden.png` | alles **unter** dem Spieler: Boden, Wasser, Klippen, Treppen, Brücken, Steg, Bodenschatten, Gras/Farne/Blumen, Füße von Bäumen, Laternen, Felsen, Gebäuden |
| `ebene2_kollision.png` | Maske: rotes 8×8-Feld = nicht begehbar |
| `ebene3_ueberlagerung.png` | transparent, alles **über** dem Spieler: Baumkronen, Laternenköpfe, Dächer, obere Teile von Felsen/Büschen |
| `kollision_fein.json` / `kollision_fein.txt` | Kollision in 8×8-Feldern (220 × 240, 2×2 je Kachel): `1` begehbar, `2` nicht begehbar, `3` begehbar + verdeckt den Spieler |
| `kollision.json` / `kollision.txt` | daraus abgeleitet je 16×16-Kachel (gesperrt, wenn ≥ 2 der 4 Felder gesperrt sind) für Engines ohne feines Raster |
| `vorschau.png` | Kontrollbild: rot = 2, blau = 3, Gitter 8 px (fein) und 16 px |

Zeichenreihenfolge im Spiel: `ebene1_boden` → Spieler/NPCs → `ebene3_ueberlagerung`.

Regeln: Wasser, Meer, Flachwasser, Wald und Klippenwände sind gesperrt, Treppen, Brücken und der Steg sind begehbar.
Hohe Objekte werden am Fuß geteilt: Die untersten 10 px (Stamm, Mast, Sockel) liegen auf Ebene 1 und
sperren die 8×8-Felder, in denen sie stehen; alles darüber liegt auf Ebene 3.

Der Spieler (16 × 16) stößt nur mit einer Fuß-Hitbox von 12 × 8 px an (unten mittig), so kommt er
durch schmale Lücken und kann mit dem Kopf vor Wänden und Bäumen stehen.

Alle Objekte stehen am 16×16-Raster (`tools/karte01_raster.py`): Fußmitte auf der Kachelmitte, unterste
Pixelzeile 2 px über der Kachelunterkante, höchstens ein hohes und ein flaches Objekt je Kachel. Die
Kachel jedes Objekts steht in `assets/objekte/karte01/platzierung.json` als `kachel: [x, y]`.

## Im Browser bearbeiten (Kollision und Ebenen)

`spiel/karte01.html` öffnen und mit `E` den Editor einschalten. `Tab` wechselt zwischen den Modi:

- **Kollision:** 8×8-Felder anklicken oder überziehen (`1` frei, `2` gesperrt, `3` verdeckt, `G` wechselt
  den Pinsel zwischen 8×8-Feld und ganzer 16×16-Kachel).
- **Ebenen:** Objekte anklicken (`1` hinter dem Spieler, `2` geteilt = Fuß unten und Rest oben (Standard
  für hohe Objekte), `3` vor dem Spieler).

`Strg+Z` macht rückgängig. „Änderungen kopieren“ liefert Zeilen der Form `spalte,zeile=wert` (8×8-Felder) bzw.
`datei.png@x,y=modus`. Übernehmen:

```bash
python3 tools/editor_uebernehmen.py aenderungen.txt
```

Die Korrekturen stehen dauerhaft in `kollision_korrekturen.json` und `ebenen_korrekturen.json` und werden
von `tools/karte01_ebenen.py` beim Neubauen angewendet. Für den Editor schreibt das Skript zusätzlich
`ebene0_untergrund.png` (Boden ohne Objekte), `objekte_atlas.png` und `spiel/karte01_objekte.js`.
Die Verdeckung (Wert 3) im Kollisionsraster wird beim Übernehmen von Ebenen neu berechnet.
