"""Signal composition helpers."""

from __future__ import annotations

import numpy as np


def mix_signals(clean: np.ndarray, rfi_signals: list[np.ndarray]) -> tuple[np.ndarray, np.ndarray]:
    if not rfi_signals:
        rfi = np.zeros_like(clean)
    else:
        rfi = np.sum(np.stack(rfi_signals, axis=0), axis=0)
    return clean + rfi, rfi
