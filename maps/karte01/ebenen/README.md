# Karte 01 – Spiel-Ebenen

Erzeugt mit `python3 tools/karte01_ebenen.py` aus derselben Platzierung wie `terrain.png`
(110 × 120 Kacheln à 16 px).

| Datei | Inhalt |
|---|---|
| `ebene1_boden.png` | alles **unter** dem Spieler: Boden, Wasser, Klippen, Treppen, Brücken, Steg, Bodenschatten, Gras/Farne/Blumen, Füße von Bäumen, Laternen, Felsen, Gebäuden |
| `ebene2_kollision.png` | Maske: rote Kachel = nicht begehbar |
| `ebene3_ueberlagerung.png` | transparent, alles **über** dem Spieler: Baumkronen, Laternenköpfe, Dächer, obere Teile von Felsen/Büschen |
| `kollision.json` / `kollision.txt` | Raster je Kachel: `1` begehbar, `2` nicht begehbar, `3` begehbar + verdeckt den Spieler |
| `vorschau.png` | Kontrollbild: rot = 2, blau = 3 |

Zeichenreihenfolge im Spiel: `ebene1_boden` → Spieler/NPCs → `ebene3_ueberlagerung`.

Regeln: Wasser, Meer, Flachwasser, Wald und Klippenwände sind gesperrt, Treppen, Brücken und der Steg sind begehbar.
Hohe Objekte werden am Fuß geteilt: Die untersten 10 px (Stamm, Mast, Sockel) liegen auf Ebene 1 und
sperren ihre Kachel, alles darüber liegt auf Ebene 3.

Alle Objekte stehen am 16×16-Raster (`tools/karte01_raster.py`): Fußmitte auf der Kachelmitte, unterste
Pixelzeile 2 px über der Kachelunterkante, höchstens ein hohes und ein flaches Objekt je Kachel. Die
Kachel jedes Objekts steht in `assets/objekte/karte01/platzierung.json` als `kachel: [x, y]`.

Bäume und Büsche: Nur der Stamm (braune Pixel in den untersten 8 Zeilen, bei Büschen ein 6 px breiter Ansatz
in der Mitte) liegt auf Ebene 1 und sperrt seine Kachel. Die ganze Krone liegt auf Ebene 3, die Kacheln
darunter sind begehbar und verdecken den Spieler. Der Wald ist zwischen den Stämmen begehbar, nur der äußere
Kartenrand bleibt zu.
