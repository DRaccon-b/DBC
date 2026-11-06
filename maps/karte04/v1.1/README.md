# Karte 04 (Gear Savanna) – v1.1

Regeln aus `CLAUDE.md` angewendet; v1.0 in `maps/karte04/v1.0/`.

- **Regel 1/1b – Raster:** alle Objekte im kleinsten Kachelblock, waagerecht zentriert, Fuß bündig (gemessen ohne Bodenfuß-Halme).
- **Regel 6 – Wege:** Wege in natürlichen Bögen; Treppen, Brücke, Furten, Teleporter, Höhenkanten und Rand bleiben fest.
- **Seitliche Plateaukanten:** nur noch schmale Abgrenzung statt sichtbarer Seitenwand (Fronten bleiben Klippen).
- **Verdeckung durch Höhen:** Objekte auf tieferem Boden werden vom seitlich daneben liegenden Plateau abgeschnitten.
- **Liegende Objekte:** Knochen, Äste, Ketten, Schrott u. Ä. werfen flachen Schatten der ganzen Form.
- **Keine Überlappungen:** nach dem Einrasten überlappende Kleinobjekte entfernt.
- Bäume unverändert (Regel 8 ausgesetzt).

Neu bauen: `python3 tools/regeln_v11.py karte04 wege && python3 tools/karte04_bauen.py && python3 tools/karte04_objekte.py && python3 tools/regeln_v11.py karte04 && python3 tools/karte04_bauen.py && python3 tools/karte04_animation.py`
