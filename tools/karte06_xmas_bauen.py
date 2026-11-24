"""Bau-Modul der Xmas-Startkarte (Karte 06 Winter) fuer tileset_export.py: karte06_bauen mit den Xmas-Kacheln,
Xmas-Objekten, zugefrorenem Teich und Weihnachtsbaum (siehe karte06_xmas.py).

  python3 tools/tileset_export.py karte06_xmas --kein-zip
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import karte06_xmas as _x

_k6 = _x.bauen_vorbereiten()
KARTE, OBJ = _x.KARTE_NEU, _x.OBJ_NEU
N_FRAMES, BILDDAUER = 16, 170


def bauen(frame=None, speichern=True, **kw):
    return _k6.bauen(frame=frame, speichern=speichern)


def __getattr__(name):
    return getattr(_k6, name)
