"""GPU search pre-filter: batched BLS (Box Least Squares) with PyTorch/CUDA.

For each star, tests thousands of periods and several durations at once and returns the SNR
of the best box transit and the SDE of the spectrum. Stars with no hint of a signal skip TLS
(expensive, CPU only). TLS still measures the signal: the GPU only decides what is worth it.

Measured per star (sector 107, CPU): cleaning 0.82 s, TLS 1.24 s. The GPU only saves the TLS
part for discarded stars; the expected gain is ~1.5x, not 10x.

Grid (audit 2026-10-10, Tier C): frequencies uniform in f^(1/3) (Ofir 2014, the same rule
TLS uses), P from cfg.period_min_days to min(period_max_fraction_of_span * span,
period_max_days) (the same P_max rule as search_periodic), and per-chunk phase bins so the
shortest trial duration spans >= 2 bins at every period.

Optional: requires `uv sync --extra gpu`. Without torch or CUDA, `available()` returns False.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from planethunter.config import SearchConfig
from planethunter.preprocess.clean import FlatLightCurve, bin_lightcurve

DURATIONS_H = (0.75, 1.5, 2.5, 4.0, 6.0, 9.0)
_G = 6.674e-11  # m^3 kg^-1 s^-2
_R_SUN = 6.957e8  # m
_M_SUN = 1.989e30  # kg
_DAY = 86400.0  # s


def available() -> bool:
    try:
        import torch
    except ImportError:
        return False
    return bool(torch.cuda.is_available())


def resolve_device(setting: str) -> str:
    """'cpu', 'cuda' or 'auto' (cuda if present). 'cuda' without a GPU raises a clear error."""
    if setting == "cpu":
        return "cpu"
    if available():
        return "cuda"
    if setting == "cuda":
        raise RuntimeError(
            "device=cuda requested, but PyTorch with CUDA is not available. "
            "Install with `uv sync --extra gpu` or use --device cpu."
        )
    return "cpu"


@dataclass
class BLSResult:
    best_period: float
    best_snr: float
    sde: float
    top_periods: tuple[float, ...] = ()  # distinct peaks, strongest to weakest


def top_peaks(spec: np.ndarray, periods: np.ndarray, k: int, sep_rel: float = 0.02) -> list[float]:
    """The k strongest peaks of the spectrum, ignoring neighbors closer than sep_rel in period."""
    order = np.argsort(spec)[::-1]
    out: list[float] = []
    for j in order:
        p = float(periods[j])
        if all(abs(p / q - 1) > sep_rel for q in out):
            out.append(p)
            if len(out) == k:
                break
    return out


def ofir_n_periods(span_days: float, pmin: float, pmax: float, oversampling: float) -> int:
    """Optimal number of trial frequencies (Ofir 2014, eqs. 5-7) for a Sun-like star."""
    span = span_days * _DAY
    a = (
        (2 * math.pi) ** (2 / 3)
        / math.pi
        * _R_SUN
        / (_G * _M_SUN) ** (1 / 3)
        / (span * oversampling)
    )
    q_min, q_max = (1 / (pmax * _DAY)) ** (1 / 3), (1 / (pmin * _DAY)) ** (1 / 3)
    return max(2, int(math.ceil((q_max - q_min) * 3 / a)))


def period_grid(span_days: float, cfg: SearchConfig, n: int | None = None) -> np.ndarray:
    """Trial periods (days, ascending), uniform in f^(1/3) (Ofir 2014). n None = Ofir optimum."""
    pmax = min(cfg.period_max_fraction_of_span * span_days, cfg.period_max_days)
    pmin = cfg.period_min_days
    if pmax <= pmin:
        return np.array([])
    n = n or ofir_n_periods(span_days, pmin, pmax, cfg.oversampling_factor)
    q = np.linspace((1 / pmax) ** (1 / 3), (1 / pmin) ** (1 / 3), n)
    return np.sort(1 / q**3)


def n_phase_bins(period_days: float, n_min: int = 300) -> int:
    """Phase bins so the shortest trial duration spans >= 2 bins at this period."""
    d_min = min(DURATIONS_H) / 24.0
    return max(n_min, int(math.ceil(2 * period_days / d_min)))


def bls_batch(
    lcs: list[FlatLightCurve],
    cfg: SearchConfig,
    *,
    n_periods: int | None = None,
    n_bins: int = 300,
    period_chunk: int = 1024,
    device: str = "cuda",
    top_k: int = 5,
) -> list[BLSResult]:
    """BLS of a batch of light curves (all with roughly the same span: one sector or the same
    set of sectors). Light curves binned to cfg.bin_minutes. n_bins is the minimum number of
    phase bins; long periods get more (n_phase_bins), with period chunks shrunk so that
    chunk_size * bins stays at period_chunk * n_bins (constant GPU memory)."""
    import torch

    binned = [bin_lightcurve(lc, cfg.bin_minutes) for lc in lcs]
    if not binned:
        return []
    span = max(b.span_days for b in binned)
    periods = period_grid(span, cfg, n_periods)
    if len(periods) == 0:
        return [BLSResult(float("nan"), 0.0, 0.0) for _ in binned]
    n_max = max(len(b) for b in binned)
    B = len(binned)
    t = np.zeros((B, n_max), np.float64)
    y = np.zeros((B, n_max), np.float32)
    m = np.zeros((B, n_max), np.float32)
    sig = np.ones(B, np.float32)
    for i, b in enumerate(binned):
        n = len(b)
        if n == 0:
            continue
        f = b.flux.astype(np.float64)
        med = np.median(f)
        t[i, :n] = b.time - b.time[0]
        y[i, :n] = (f - med).astype(np.float32)
        m[i, :n] = 1.0
        s = 1.4826 * np.median(np.abs(f - med))
        sig[i] = s if s > 0 else 1e-6
    dev = torch.device(device)
    tt = torch.as_tensor(t, device=dev)  # float64 so the phase does not lose precision
    yy = torch.as_tensor(y, device=dev)
    mm = torch.as_tensor(m, device=dev)
    ss = torch.as_tensor(sig, device=dev)
    spectrum = torch.zeros((B, len(periods)), device=dev)
    durs = torch.as_tensor(np.array(DURATIONS_H) / 24.0, device=dev, dtype=torch.float64)
    budget = period_chunk * n_bins
    c0 = 0
    while c0 < len(periods):
        size = max(1, budget // n_phase_bins(float(periods[c0]), n_bins))
        nb = n_phase_bins(float(periods[min(c0 + size, len(periods)) - 1]), n_bins)
        size = max(1, min(size, budget // nb))
        nb = n_phase_bins(float(periods[min(c0 + size, len(periods)) - 1]), n_bins)
        P = torch.as_tensor(periods[c0 : c0 + size], device=dev, dtype=torch.float64)
        Pc = len(P)
        bins_ar = torch.arange(nb, device=dev)
        phase = torch.remainder(tt[:, None, :] / P[None, :, None], 1.0)
        idx = (phase * nb).long().clamp_(0, nb - 1)
        del phase
        sums = torch.zeros((B, Pc, nb), device=dev)
        cnts = torch.zeros((B, Pc, nb), device=dev)
        sums.scatter_add_(2, idx, yy[:, None, :].expand(B, Pc, -1).contiguous())
        cnts.scatter_add_(2, idx, mm[:, None, :].expand(B, Pc, -1).contiguous())
        del idx
        kmax = nb // 3
        # wrap-around cumsum (the box can cross phase 1 -> 0)
        cs_s = torch.nn.functional.pad(torch.cat([sums, sums[..., :kmax]], -1).cumsum(-1), (1, 0))
        cs_c = torch.nn.functional.pad(torch.cat([cnts, cnts[..., :kmax]], -1).cumsum(-1), (1, 0))
        best = torch.zeros((B, Pc), device=dev)
        for d in durs:
            k = torch.clamp(torch.round(d / (P / nb)).long(), 1, kmax)  # bins in the box
            end = bins_ar[None, :] + k[:, None]  # (Pc, n_bins)
            g_end = end[None].expand(B, -1, -1)
            g_beg = bins_ar[None, None, :].expand(B, Pc, -1)
            s_win = cs_s.gather(2, g_end) - cs_s.gather(2, g_beg)
            c_win = cs_c.gather(2, g_end) - cs_c.gather(2, g_beg)
            snr = torch.where(
                c_win >= 3, -s_win / (ss[:, None, None] * torch.sqrt(c_win.clamp(min=1))), 0.0
            )
            best = torch.maximum(best, snr.amax(-1))
        spectrum[:, c0 : c0 + Pc] = best
        del sums, cnts, cs_s, cs_c
        c0 += Pc
    spec = spectrum.cpu().numpy()
    out = []
    for i in range(B):
        sp = spec[i]
        j = int(np.argmax(sp))
        std = float(np.std(sp))
        sde = (float(sp[j]) - float(np.mean(sp))) / std if std > 0 else 0.0
        out.append(
            BLSResult(float(periods[j]), float(sp[j]), sde, tuple(top_peaks(sp, periods, top_k)))
        )
    return out
