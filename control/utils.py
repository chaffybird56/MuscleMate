"""Utility helpers for MuscleMate."""

from __future__ import annotations


def clamp(value: float, lo: float, hi: float) -> float:
    """Clamp ``value`` within ``[lo, hi]``."""
    if lo > hi:
        raise ValueError("Lower bound must be <= upper bound.")
    return max(lo, min(hi, value))

