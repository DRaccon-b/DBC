# Karte 02 (Factorial Town) – v1.1

Regeln aus `CLAUDE.md` angewendet; v1.0 in `maps/karte02/v1.0/`.

- **Regel 1/1b – Raster:** alle Objekte im kleinsten Kachelblock, waagerecht zentriert, Fuß bündig.
- **Keine Überlappungen:** nach dem Einrasten überlappende Kleinobjekte entfernt.
- Nicht angewendet, weil auf dieser Karte nicht vorhanden bzw. nicht passend: Wege in Bögen (Industriestraßen
  bleiben gerade), Plateaus/Klippen (Verdeckung, Seitenkanten), Bäume, Wasserfälle.

Neu bauen: `python3 tools/karte02_objekte.py && python3 tools/regeln_v11.py karte02 && python3 tools/karte02_bauen.py && python3 tools/karte02_animation.py`
