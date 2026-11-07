# Karte 13 – Spiral Mountain: Machine City v1.0

80 × 70 Kacheln à 16 px (1280 × 1120), Vorlage `assets/vorlagen/karte13_vorlage.png`.
Zerstörte Maschinenstadt am Spiral Mountain. Anspielungen auf den Herrn der Stadt nur über Stil und Farben.

## Inhalt der Karte
- **Rand:** dieselbe Bergwand wie Dark Ocean, Puppet Woods und Summit; Schrottrand vom Kartenrand angeschnitten,
  versunkene Maschinenteile (Zahnrad, Panzerkette, Roboterarm, Mech-Kopf), Kabel und Rohre über die Kuppe,
  Warnleuchten, Funkmasten, Kamera, Zäune, Stacheldraht, Warnschilder, Kristalladern und Ölflecken.
  Festungstor, Panzertüren und Teleporter bleiben frei.
- **Maschinenfestung:** eine Etage höher, Metallboden, Front mit Warnstreifen und roten Leuchten, Metalltreppe,
  Festungstor mit rotem Auge, Panzertüren, Reaktoren und Konsolen spiegelgleich, Boss-Kreis im Maschinenstil.
- **Höfe:** Industriehof (Lagerhalle, Fabrik, Schornsteine, Ofen, Strommast, Generator) und Hof mit Funkturm, Tanks,
  Rohren; Giftwasser-Becken auf Laborboden mit Warnstreifen-Rand.
- **Stadt:** Straßenraster mit Bordsteinen, Mittellinie und Zebrastreifen, Häuserblöcke mit sichtbaren Dächern
  (Wohnblöcke, Ladenzeilen, Büros, Glastürme), Kran-, Bus- und Autowracks, Drachen-Wrack (eigenes Objekt
  „dragondead“), Laternen, Ampeln, Statue, Telefonzelle, Schutt, verseuchter Boden; Bahnhof mit Gitterrost.

## Animation (16 Bilder, 170 ms)
Boss-Kreis, Teleporter, Giftwasser (Lichtnetz, Blasen), rote Lichter (Warnleuchten, Funkmasten, Funkturm,
Festungstor, Panzertüren, Strommast, Generator, Mech-Kopf, Kamera, Schaltkasten), Reaktoren, Laternen, Kristalle,
Konsolen, Funken am Drachen-Wrack, Rauch aus Schornsteinen, Ofenfeuer, Gras.

## Dateien
- `Spiral_Mountain_Machine_City_v1.0.png` – Standbild, `Spiral_Mountain_Machine_City_v1.0_discord.gif` – Animation.
- `kollision/` – Kollisionsraster (`kollision.json`, `.txt`, `ebene2_kollision.png`, `kollision_overlay.png`).

Erzeugt mit `tools/karte13_layout.py`, `karte13_kacheln.py`, `karte13_bauen.py`, `karte13_objekte.py`,
`regeln_v11.py karte13`, `karte13_animation.py`, `kollision.py karte13`, `tileset_export.py karte13`.
