"""
EMG feature vector for edge intent models (ONNX / TFLite handoff).

Provides a fixed-size feature snapshot compatible with future learned
classifiers; current FSM still uses rule-based gesture decoding.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple


@dataclass(frozen=True)
class EmgFeatureVector:
    ch1: float
    ch2: float
    ch1_envelope: float
    ch2_envelope: float
    co_contraction: float

    def as_list(self) -> List[float]:
        return [
            self.ch1,
            self.ch2,
            self.ch1_envelope,
            self.ch2_envelope,
            self.co_contraction,
        ]


def extract_features(raw: Tuple[float, float], prev_env: Tuple[float, float]) -> EmgFeatureVector:
    alpha = 0.2
    e1 = alpha * abs(raw[0]) + (1 - alpha) * prev_env[0]
    e2 = alpha * abs(raw[1]) + (1 - alpha) * prev_env[1]
    co = min(e1, e2) / max(e1, e2, 1e-6)
    return EmgFeatureVector(raw[0], raw[1], e1, e2, co)
