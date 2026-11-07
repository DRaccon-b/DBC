# Karte 12 – Spiral Mountain: Puppet Woods v1.0

80 × 70 Kacheln à 16 px (1280 × 1120), Vorlage `assets/vorlagen/karte12_vorlage.png`.
Schlammiger, düsterer Puppenwald am Spiral Mountain. Anspielungen auf den Puppenmeister nur über Holz, Fäden,
Marionetten und Farben – keine Figur nachgebaut.

## Inhalt der Karte
- **Rand:** dieselbe Bergwand wie Dark Ocean, Machine City und Summit; Pflanzenrand aus 16 Farn- und
  Buschvarianten, vom Kartenrand angeschnitten, Tiefe wellenförmig, starr.
- **Boden:** Schlamm, Moosboden unter den Waldstücken, Moorpfützen, Kürbisäcker, vier Moos-Plateaus mit Treppen.
- **Fluss:** entspringt einem Wasserspeier (geschnitzte Puppenmaske) in der Bergwand, verbindet die Moore,
  verlässt die Karte durch eine Felsschlucht; zwei Holzstege, Wege gerade auf die Brückenköpfe.
- **Pfad:** Trampelpfad vom Platz zum oberen Ausgang, mit Unterbrechungen, frei von Objekten.
- **Baumhaus:** großes Baumhaus mit Wendeltreppe, Marionettengestell, Holzhammer.
- **Arena:** Holzpodest eine Etage höher mit Dielen, Rissen und hochgeklappten Brettern, Bohlenfront, Holztreppe,
  Bannkreis mit Spirale, Puppentheater, Zielscheiben und Kürbislaternen spiegelgleich.
- **Wald und Felder:** dichte Waldstücke mit düsteren Bäumen, Obstbaum-Plantagen, Vogelscheuchen, Kürbisse,
  tote Bäume mit Begleitern, Pilze, Rohrkolben, Frösche, Puppenteile; gepflasterter Platz am unteren Ausgang.

## Animation (16 Bilder, 170 ms)
Fluss (Strömung), Moor (Entengrütze, Blasen), Quelle (Strahl, Gischt), Kürbislaternen und Laterne (Flammen),
Baumhaus-Fenster, Bannkreis (Spirale), Teleporter, Farne/Rohrkolben/Gras im Wind, etwa jeder dritte Baum (Stamm fest),
Marionette (pendelt), Vogelscheuchen (nur die Lumpen), Theatervorhang (nur der Stoff), Frosch (blinzelt).

## Dateien
- `Spiral_Mountain_Puppet_Woods_v1.0.png` – Standbild, `Spiral_Mountain_Puppet_Woods_v1.0_discord.gif` – Animation.
- `kollision/` – Kollisionsraster (`kollision.json`, `.txt`, `ebene2_kollision.png`, `kollision_overlay.png`).

Erzeugt mit `tools/karte12_layout.py`, `karte12_kacheln.py`, `karte12_bauen.py`, `karte12_objekte.py`,
`regeln_v11.py karte12`, `karte12_animation.py`, `kollision.py karte12`, `tileset_export.py karte12`.
