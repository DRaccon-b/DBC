# Karte 01

Fertige Karte: `terrain.png` (1760×1920 px, 110×120 Kacheln à 16×16).
Ohne Objekte: `terrain_basis.png`. Kachelzuordnung: `tilemap.json`.

## Neu bauen

```bash
python3 tools/basis_kacheln.py      # Grundkacheln Gras/Sand/Wasser/Meer (je 5 Varianten)
python3 tools/karte_bauen.py        # Boden + Klippen  (schreibt tilemap.json mit Klassen)
python3 tools/objekte_setzen.py     # Wald, Deko, Sonderobjekte -> platzierung.json
python3 tools/karte_bauen.py        # fertige Karte mit Objekten
python3 tools/pruefen.py            # Kontrolle: keine Objekte, die sich ueberlappen
```

Objekte werden nur gesetzt, wenn ihre sichtbaren Pixel kein anderes Objekt und kein Bauwerk
(Klippe, Treppe, Brücke, Steg) berühren; Ausnahme: Bäume untereinander (dichter Wald).
Gras und Blumen, die sich im Wind neigen, halten 1 px Abstand zur Seite. Wiesen-Deko liegt
mit allen Pixeln plus 1 px Rand auf Gras (nie im Sand/Weg/Wasser), bei Bäumen gilt das für
Stamm und Fuß. Pflanzen (Gras, Schilf, Strandgras, Farne) gibt es in zwei Varianten, die
automatisch nach Untergrund gewählt werden: `varianten/NN_gras.png` (kurze Halme und Schatten am
Fuß) und `varianten/NN_sand.png` (wachsen aus einem kleinen Sandhügel); am Ufer und Strand muss der
Fuß ganz auf Sand stehen. Beide Varianten haben einen halbtransparenten Kontaktschatten und einen
leicht abgedunkelten Halmfuß; auf Gras fransen kurze Halme aus, auf Sand dünnt der Hügel zum Rand aus.
Dasselbe Prinzip gilt für alle Objekte an Land (`tools/bauwerke.py`, `bodenfuss`, Art je Objekt in
`FUSS_ART` in `tools/objekte_setzen.py`): Steine, Runensteine, Kristalle, Bäume, Büsche, Stümpfe,
Zelt, Lagerfeuer und kleine Deko bekommen Kontaktschatten, abgedunkelten Fuß und auf Gras kleine
Grasbüschel vor der Unterkante bzw. auf Sand einen Sandwall. Varianten: `varianten/<gruppe>-<nr>_<gras|sand>.png`.
Halbtransparente Schatten zählen bei der Überlappungsprüfung nicht mit.

Riesiger Dschungelbaum (`assets/objekte/karte01/dschungel/00.png`, PixelLab-Objekt-Manager, 118×113 px)
östlich des Weges, mit Kronenschatten und Unterwuchs; kein anderer Baum überlappt ihn.

## Aufbau

| Ebene | Quelle | Datei |
|---|---|---|
| Grundkacheln | handgezeichnet (Skript) | `tools/basis_kacheln.py` → `assets/basis/` |
| Übergänge Gras/Sand/Wasser/Meer | PixelLab Pro-Tilesets, Grundkacheln als exakte Referenz | `assets/tilesets/pixellab/` |
| Klippen (3–4 Kacheln hoch) und Wasserfall | handgezeichnet (Skript) | `tools/klippen.py` |
| Bäume, Deko, Brücken, Treppen, Zelt … | PixelLab-Objekt-Manager | `assets/objekte/karte01/{baeume,deko,gross}/` |

- Geländetypen je Kachel: `terrain_grid.json` (aus dem Original abgeleitet).
- Klippenverlauf, Wandhöhe `h`, Treppen, Brücken, Steg: `hoehenplan.json`.
- Welche Objekt-Kandidaten wo verwendet werden: `AUSWAHL` und `FEST` in `tools/objekte_setzen.py`
  (Nummern siehe `uebersicht.png` der jeweiligen Gruppe).
- Neue Objektgruppen: `tools/pixellab_objekte.py` (braucht `PIXELLAB_API_KEY`).

## Stilregeln (Handheld-Monster-RPG-Look, 16 px)

- Bodenkacheln ohne Outlines, kontrastarme Textur, Hue-Shifting (Schatten → blaugrün, Licht → gelblich).
- Übergänge ohne Linie: dunklerer Rand + Saum.
- Objekte mit farbiger dunkler Kontur (nie Schwarz), Licht von oben links, runde gebündelte Formen,
  weicher Bodenschatten.

## Animation

```bash
python3 tools/animation_bauen.py    # 16 Frames à 110 ms, nahtlose Schleife
```

Ausgabe in `animation/`: `karte01_animiert.webp` (ganze Karte), `karte01_discord.gif` (ganze Karte
in voller Auflösung unter 10 MB, 8 Frames à 220 ms), `detail_*.gif` (Ausschnitte 3×),
`kacheln/*.png` (Wasser-Grundkacheln als 16-Frame-Streifen für eine Engine: `_fluss` = fließt nach
unten, `_schwappen` = pendelt seitlich).

Animiert werden: Fluss (fließt), Teich und Meer (schwappen), Schaum an Ufern und Strand (glitzert),
Wasserfall (fallende Streifen, brodelnde Gischt, Nebel), Runen in Klippen, Steinen und Bäumen
(pulsieren), Lagerfeuer (flackert), Gras/Schilf/Farne/Blumen (wiegen sich in einer Windwelle, die
über die Karte läuft), Seerosen (wippen), Schmetterlinge (flattern über Blumenwiesen),
Laternen am Wegrand (Glas flackert, warmer Lichtschein; Sprite aus `tools/bauwerke.py`).
Animationsart je Objekt steht als `anim` in `assets/objekte/karte01/platzierung.json`
(`wehen`/`wippen`), Flugbahnen der Schmetterlinge in `schmetterlinge.json`. Die Logik steckt in `tools/karte_bauen.py` (`bauen(frame)`,
`wasser_frame`, `leuchten`) und `tools/klippen.py` (`zeichne_wasserfall(..., frame)`).
