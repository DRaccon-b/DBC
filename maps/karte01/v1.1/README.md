# Karte 01 (Wald & Strand) – v1.1

Neue Fassung nach den Regeln in `CLAUDE.md`. v1.0 liegt in `maps/karte01/v1.0/`.

| Datei | Inhalt |
|---|---|
| `karte01_v1.1.png` | fertige Karte (1760×1920, 110×120 Kacheln) |
| `karte01_v1.1_discord.gif` | Animation (8 Bilder, 6,8 MB) |
| `karte01_v1.1_tilesets.zip` | Objekte + Boden, je statisch und animiert (Muster wie Startkarte) |
| `karte01_v1.1_ebenen.zip` | Ebenen begehbar / gesperrt / verdeckt |
| `wege_vorher_nachher.png` | Wegnetz v1.0 (links) und v1.1 (rechts) |

## Änderungen gegenüber v1.0
- **Regel 6 – Wege:** natürliche Bögen und Diagonalen statt eckiger, gerader Wege (`tools/karte01_v11_wege.py`);
  an Treppen, Brücken, Steg und Kartenrand bleiben die Anschlüsse exakt; ein Weg setzt kurz aus.
- **Regel 2 – Treppen:** 3× vergrößert geprüft; ober- und unterhalb jeder Treppe ist der Weg mindestens so breit wie die Treppe.
- **Regel 5 – Bäume:** Wiesenbäume bekommen Begleitung (zweiter Baum + Pflanze vor dem Sockel, sonst 2–3 Pflanzen);
  Pflanzen aus Karte 01 und den neuen Gras-Sets (Regel 3); Bäume ohne Platz für Begleitung entfernt
  (`tools/karte01_v11_begleiter.py`).
- **Regel 7 – Schatten:** Schatten über Klippe/Wasser verkleinert.
- **Abschlusskontrolle:** keine Überlappungen, alles auf dem richtigen Untergrund (`tools/karte01_v11_aufraeumen.py`,
  `tools/pruefen.py`: 0/0); Felsen im Wasser nach Tiefe (tiefer = größer, tiefste Stufe nur unter Wasser).

## Neu bauen
```bash
python3 tools/karte01_v11_wege.py && python3 tools/karte_bauen.py && python3 tools/objekte_setzen.py
rm -f assets/objekte/karte01/platzierung_frei.json && python3 tools/karte01_raster.py
python3 tools/karte01_v11_begleiter.py && python3 tools/karte_bauen.py
python3 tools/karte01_v11_aufraeumen.py && python3 tools/karte_bauen.py
python3 tools/animation_bauen.py && python3 tools/karte01_ebenen.py
python3 tools/karte01_tilesets_objekte.py && python3 tools/karte01_tilesets_boden.py
```
