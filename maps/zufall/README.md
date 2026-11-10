# Zufallskarten im Stil von Karte 01 (Kartenstück-Generator)

Zufällig erzeugte Wald-Dungeons aus **vorgefertigten Kartenstücken** – Prinzip wie bei den Karten in
Path of Exile: Die Stücke sind von Hand gebaut, nur ihre Anordnung ist zufällig.

```bash
python3 tools/zufall_stuecke.py           # Stücke prüfen + stuecke_uebersicht.png
python3 tools/zufall_karte.py 7           # Karte mit Startwert 7 (5×4 Felder)
python3 tools/zufall_karte.py 7 6 5       # Startwert 7, 6×5 Felder
```

Gleicher Startwert = gleiche Karte.

| Datei | Inhalt |
|---|---|
| `karte_<n>.png` | fertige Karte (Felder × 14 Kacheln à 16 px, z. B. 84×70 Kacheln) |
| `grundriss_<n>.png` | welches Stück in welcher Lage auf welchem Feld liegt |
| `karte_<n>.json` | dasselbe als Liste (Startwert, Felder, Stücke) |
| `stuecke_uebersicht.png` | alle Kartenstücke (rot = feste Objekte) |
| `assets/objekte/karte01/zufall_portal`, `zufall_brunnen` | kleines Portal und Waldbrunnen (PixelLab-Objekt-Creator, `tools/pixellab_objekte.py`) |
| `random_dungeon_kit.zip` | fertiges Paket (englisch): alle Kartenstuecke einzeln, Objekt-Tileset, JS ohne Server, Demo, README |
| `js/` | deutsches JS-Modul + Export der Stuecke (`tools/zufall_export.py`) |
| `kit/` | Quellen des englischen Pakets (JS, Demo, README); bauen mit `python3 tools/zufall_paket.py` |
| `_bau/` | Zwischendateien (nicht im Repo) |

## Kartenstücke (`tools/zufall_stuecke.py`)

Ein Stück ist ein Geländeraster aus **14×14 Kacheln** (Bossarena 2×2 Felder = 28×28):
`F` Wald, `G` Wiese, `P` Sandweg, `W` Teich. Jede Seite hat einen **Kantentyp**, der aus den äußeren zwei
Kachelreihen gelesen wird:

| Typ | Kante | Bedeutung |
|---|---|---|
| `Z` | `FFFFFFFFFFFFFF` | zu (Wald) |
| `W` | `FFFFGGPPGGFFFF` | schmaler Waldweg |
| `O` | `FFGGGGPPGGGGFF` | offene Wiese mit Weg |

Zwei Stücke passen zusammen, wenn ihre Kantentypen gleich sind. Der Weg liegt an jeder offenen Kante mittig
(Spalte 6–7), deshalb funktionieren auch gedrehte und gespiegelte Stücke. Jedes Stück wird in bis zu 8 Lagen
verwendet (die Bossarena nur 0°/180° + gespiegelt, damit die Runensteine symmetrisch zum Baum stehen).

Stückarten: Wege (Bogen, Ecke, Gabel, Kreuzung), Wiesen (mit Teich, Rosabaum, Übergang Waldweg ↔ Wiese),
Sackgassen (Teich, Wiese, Waldbrunnen, Findling, Runenbaum-Lichtung), Startlager (Portal, Lagerfeuer,
Wegweiser), Bossarena (Dschungelbaum + Runensteinpaar), Füllwald.

**Neues Stück:** Raster in `STUECKE` eintragen und `python3 tools/zufall_stuecke.py` laufen lassen. Die Prüfung
meldet falsche Kanten, Objekte nicht auf Wiese, Objekte, die sich in einer Lage berühren, Objekte, deren Fuß
in einer Lage am Waldrand steht (Stamm verdeckt), und 1 Kachel schmale Grasinseln zwischen Weg und Wasser.

## Ablauf des Generators (`tools/zufall_karte.py`)

1. **Grundriss:** Bossarena und Startlager möglichst weit auseinander, dazwischen ein verschlungener Hauptweg,
   Abzweigungen in Sackgassen, selten eine Schleife. Leere Felder werden dichter Wald. Die Arena wird von Nord
   oder Süd betreten.
2. **Stücke einsetzen:** Je Feld ein zufälliges Stück in passender Lage (Kanten passen zum Grundriss und zu den
   Nachbarn), sonst Backtracking. Häufig benutzte Stücke werden seltener gewählt.
3. **Bauen mit der Karte-01-Technik:** `karte_bauen.py` (Boden, Übergänge, vertiefte Teiche, Waldboden),
   `objekte_setzen.py` (Wald, Waldrand, Wiese, Laternen, feste Objekte), `karte01_raster.py` (Regel 1/1b),
   Symmetrie der Objektpaare, `karte01_v11_begleiter.py` (Regel 5 und 7), `karte01_v11_aufraeumen.py`
   (keine Überlappungen, richtiger Untergrund). Karte 01 selbst wird dabei nicht verändert.

## Noch nicht enthalten (nächste Schritte)

- Klippen mit Treppen und Bäche mit Brücken als Stücke
- Kollisions-/Überlagerungsebenen und Tiled-Export für die Engine
- Animation (GIF) – erst, wenn die Standbilder passen
