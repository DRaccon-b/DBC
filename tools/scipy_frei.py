"""Kleine Bildhilfen ohne scipy: zusammenhaengende Teile einer booleschen Maske (8er-Nachbarschaft)."""
from collections import deque
import numpy as np


def teile(m):
    """Liefert fuer jede zusammenhaengende Flaeche (ys, xs) als numpy-Arrays."""
    m = np.asarray(m, bool)
    Hh, W = m.shape
    gesehen = np.zeros_like(m)
    for y0, x0 in zip(*np.nonzero(m)):
        if gesehen[y0, x0]:
            continue
        q = deque([(y0, x0)]); gesehen[y0, x0] = True; ys, xs = [], []
        while q:
            y, x = q.popleft(); ys.append(y); xs.append(x)
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    yy, xx = y + dy, x + dx
                    if 0 <= yy < Hh and 0 <= xx < W and m[yy, xx] and not gesehen[yy, xx]:
                        gesehen[yy, xx] = True; q.append((yy, xx))
        yield np.array(ys), np.array(xs)
