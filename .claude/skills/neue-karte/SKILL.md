---
name: neue-karte
description: Neue 16x16-RPG-Karte aus einer Vorlage selbststaendig bauen - Layout, Gelaende, Objekte, Animation, Agenten-Pruefschleife bis fehlerfrei, Kollision, Tileset, ZIP, GIF. Verwenden, sobald der Nutzer eine neue Karte (Vorlagenbild + Name, z. B. "naechste Map A03 Name ...") schickt.
---

# Neue Karte bauen (ohne Zwischenfragen bis zur Abnahme)

Ziel: Der Nutzer schickt Vorlage + Name, bekommt erst das **fertige, gepruefte** Ergebnis (Standbild, GIF mit 16
Bildern, ZIP) mit kurzer Zusammenfassung. Rueckfragen nur bei echten Mehrdeutigkeiten der Vorlage (Regel "Unklares
erst fragen") - dann gesammelt in EINER Frage am Anfang.

Alle Regeln in `CLAUDE.md` gelten, besonders **"Pruefliste: haeufige Fehler"** - sie ist die Summe aller bisherigen
Nutzer-Korrekturen und wird bei jedem Schritt mitgedacht, nicht erst am Ende.

## 1. Anlegen
1. Vorlage vermessen: Groesse in Kacheln (Bild / 16 bzw. passend skaliert), Flaechen, Hoehen, Wege, Wasser, Bauwerke,
   Ausgaenge. Kurz notieren, was die Vorlage zeigt (wird spaeter mit dem Ergebnis verglichen).
2. Passendste Vorbild-Karte waehlen (Katalog in `tools/neue_karte.py`) und anlegen:
   `python3 tools/neue_karte.py NN "Name" --vorbild karteXX --gebiet A03 --nr N --vorlage <pfad> --beschreibung "..."`
   (naechste freie Nummer: hoechste `tools/karteNN_bauen.py` + 1).
3. In den kopierten Skripten alles Vorbild-Spezifische ersetzen: Groesse `C, R`, Klassen-Farben `REF` (aus der Vorlage
   messen: Median je Kachel), Sonderflaechen (Treppen, Bruecken, Tore, Teleporter), Docstrings mit der neuen Karte.

## 2. Bauen (Reihenfolge)
`python3 tools/karteNN_layout.py` -> `karteNN_bauen.py` -> `karteNN_objekte.py` -> `karteNN_bauen.py`
- Gelaende: `k4.RASTER45 = True`, Wege mit `regeln_a02.wege_schwingen`, Meer mit `wasser_details.RASTER45 = True`,
  `raster45`/`abstand45`; Kollisionsdaten speichern (`pixelhoehe.npy`, `wasser.npy`, bei Leere `leere.npy`).
- Objekte: grosse zuerst, **erst wiederverwenden** (`assets/objekte/karteXX/`), fehlende mit PixelLab Objekt-Creator
  (`tools/pixellab_objekte.py`, Frontal-Zusatz), umfaerben auf die Kartenpalette. `regeln_a02.objekte_pruefen` laeuft
  automatisch (nichts auf Wegen, Teleporter frei) und wendet `anim_a02` und `korrektur_a02` an.
- Animation: `anim_a02.ANIM['karteNN']` fuer Fahnen (`standarte`/`wimpel`), Bildschirme, LEDs, Maschinen, Feuer
  (`flammen_box`), Portale, Lampen (`lampe_box`) - immer mit Box auf das bewegliche Teil.
  `python3 tools/animation_a02.py karteNN 16` und `python3 tools/animation_a02.py karteNN`.

## 3. Selbstkontrolle (Pflicht, Schleife)
1. Selbst ansehen: Gesamtbild + vergroesserte Ausschnitte aller Treppen, Bruecken, Wegenden, Ufer, Kartenraender,
   Tore, Teleporter; Vergleich mit der Vorlage.
2. Agenten-Pruefung: Workflow `karte_pruefen` mit `args: {karte: "karteNN"}` (4 Pruefer + Gegenpruefung).
3. Alle bestaetigten Befunde (hoch/mittel) beheben - Ursache im Code/Layout, nicht nur das Symptom; Objekt-Einzelfaelle
   in `tools/korrektur_a02.py`. Geringe Befunde beheben, wenn schnell.
4. Neu bauen (bauen + Animationen) und Schritt 2-3 wiederholen, bis keine hohen/mittleren Befunde mehr bestaetigt werden
   (hoechstens 3 Runden; Rest in der Zusammenfassung nennen).
5. Neue Fehlerarten, die die Pruefung findet, als Zeile in `CLAUDE.md` -> "Pruefliste: haeufige Fehler" ergaenzen.

## 4. Abgabe
- `python3 tools/paket_a02.py karteNN` (Kollision mit Overlay ansehen!, Tileset, README, ZIP mit GIF 4+16).
- `maps/GEBIETE.md` Stand aktualisieren; committen und pushen.
- An den Nutzer (SendUserFile): Standbild, `..._discord_16.gif`, ZIP; auf Deutsch kurz: was die Karte enthaelt, welche
  Objekte neu erzeugt wurden, was die Pruefung gefunden und behoben hat, was offen ist.
- Ab dann Nutzer-Feedback umsetzen; jede Korrektur, die eine Regel betrifft, in `CLAUDE.md` festhalten.
