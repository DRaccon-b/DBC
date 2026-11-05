# Karte 06 – Startkarte

72 × 60 Kacheln à 16 px, Vorlage `assets/vorlagen/karte06_vorlage.png`.

```
python3 tools/karte06_bauen.py layout   # Raster (von Hand definiert) -> layout.json
python3 tools/karte06_objekte.py        # Objekte, alle am 16x16-Raster
python3 tools/karte06_bauen.py          # terrain.png
python3 tools/karte06_animation.py      # animation/ (webp, Discord-GIF, Detail-GIFs)
```

- Wald ringsum (rundlicher Rand, nur grüne Bäume aus Karte 01, unbewegt), Ausgang rechts mit Teleporter.
- Oben: Fernseher-Portal, Blockhütte, Schrott-Werkstatt mit Zahnrädern (Karte 04), Meeres-Schmiede, Ring-Portal-Platz.
- Mitte: Riesenbrunnen auf Kopfsteinplatz (Kiesel aus Karte 03, umgefärbt) mit Laternenkranz.
- Unten links: umzäunte Pension mit Spielplatz, Datenbaum (Datenfragmente animiert) und Eiern.
- Unten Mitte: Teich im vertieften Wasserstil mit Steg. Unten rechts: Cyber-Datenplatz (Platten aus Karte 02,
  blaue/rote Kabel mit Lichtpulsen, Server und Antenne aus Karte 03).
- Neue Objekte: PixelLab (`assets/objekte/karte06/`), übernommene Sprites unter `k01/`, `k03/`, `k04/`.
