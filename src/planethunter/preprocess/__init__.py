"""Stage 2: quality mask, outliers, normalization and detrending (plus null-run transforms)."""

from planethunter.preprocess.clean import (
    FlatLightCurve,
    bin_lightcurve,
    flatten_adaptive,
    flatten_for_signal,
    flatten_sector,
    red_noise_ratio,
    signal_windows,
    stitch,
)
from planethunter.preprocess.nulltest import NULL_MODES, apply_null

__all__ = [
    "NULL_MODES",
    "FlatLightCurve",
    "apply_null",
    "bin_lightcurve",
    "flatten_adaptive",
    "flatten_for_signal",
    "flatten_sector",
    "red_noise_ratio",
    "signal_windows",
    "stitch",
]
