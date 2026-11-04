# Karte 02 – Factorial Town

Fertige Karte: `terrain.png` (1520×1200 px, 95×75 Kacheln à 16×16), ohne Objekte: `terrain_basis.png`.
Animation: `animation/karte02_animiert.webp`, Discord: `animation/karte02_discord.gif` (volle Auflösung,
16 Frames, unter 10 MB), Ausschnitte `animation/detail_*.gif`. Vorlage: `assets/vorlagen/karte02_vorlage.png`.

## Neu bauen

```bash
python3 tools/karte02_kacheln.py    # Grundkacheln (Beton, Asphalt, Gehweg, Platz, Metallboden)
python3 tools/karte02_bauen.py      # Boden, Mauern, Gebaeude, Schienen, Baender, Rohre, Markierungen
python3 tools/karte02_objekte.py    # Objekte setzen (feste Positionen + Kleinteile)
python3 tools/karte02_bauen.py      # fertige Karte
python3 tools/karte02_animation.py  # Animation und Discord-GIF
```

## Aufbau (gleiche Prinzipien wie Karte 01)

| Ebene | Quelle | Datei |
|---|---|---|
| Layout (Zonen, Gebaeude, Schienen …) | aus der Vorlage vermessen, Kacheln | `maps/karte02/layout.json` |
| Grundkacheln | handgezeichnet (Skript) | `tools/karte02_kacheln.py` → `assets/karte02/basis/` |
| Gras | aus Karte 01 | `assets/basis/gras_*` |
| Beton↔Gras | PixelLab-Pro-Tileset, Grundkacheln als Referenz | `assets/tilesets/pixellab/k2_beton_gras.json` |
| Mauern, Hallen, Backsteinhaeuser, Reaktorhaus, Schienen, Foerderbaender, Rohre, Markierungen, Container, Portalkran | prozedural | `tools/industrie.py` |
| Maschinen, Fahrzeuge, Tanks, Reaktor, Oefen, Kleinteile | PixelLab-Objekt-Manager (Gruppen `k2_*`) | `assets/objekte/karte02/<gruppe>/` |
| Laternen, Bodenfuss, Lichtschein | aus Karte 01 | `tools/bauwerke.py`, `tools/karte_bauen.py` |

Massstab: Leinwandgroesse je Objektgruppe passend zur Zielgroesse aus der Vorlage (Objekte fuellen
~90 % der Leinwand): Kleinteile 18 px (Fass ≈ 12×16), Kleingeraete 32 px, Maschinen 64 px,
Fahrzeuge/Tanks 84 px, Silos/Schornsteine 100 px, Hochoefen/Pylone 140 px, Reaktor 256 px.
Objekte, die gerade (frontal) zur Karte passen muessen, wurden ausdruecklich orthografisch erzeugt
(`k2_ortho`); Container und Kran sind prozedural, damit sie exakt achsparallel sind.

Animation: Foerderbaender laufen, Reaktor/Pylone/Generatoren pulsieren, Feuer flackert, Rauch steigt
aus den Schornsteinen, Signalsaeulen blinken, Laternen flackern.
