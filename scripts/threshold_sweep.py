#!/usr/bin/env python3
"""Sweep emg_on / emg_off thresholds against scripted noise profiles.

Writes bench_logs/threshold_sweep_summary.csv for calibration traceability.
Uses deterministic sample lists — regenerate after changing control/config.py defaults.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from control.config import Thresholds
from control.gesture import GestureDecoder

OUT = ROOT / "bench_logs" / "threshold_sweep_summary.csv"

REST_SAMPLES = [(0.02, 0.02)] * 12
NOISY_SAMPLES = [(0.56, 0.48)] * 12
CONTRACT_SAMPLES = [
    (0.02, 0.02),
    (0.88, 0.05),
    (0.90, 0.05),
    (0.02, 0.02),
    (0.05, 0.85),
    (0.05, 0.88),
    (0.02, 0.02),
] * 3


def count_intents(decoder: GestureDecoder, samples: list[tuple[float, float]], clock: list[float]) -> int:
    count = 0
    for ch1, ch2 in samples:
        clock[0] += 0.20
        decoder.update(ch1, ch2)
        if decoder.intent().name != "NONE":
            count += 1
    return count


def count_missed_starts(decoder: GestureDecoder, samples: list[tuple[float, float]], clock: list[float]) -> int:
    missed = 0
    for ch1, ch2 in samples:
        clock[0] += 0.20
        decoder.update(ch1, ch2)
        if ch1 >= decoder.thresholds.emg_on and decoder.intent().name == "NONE":
            missed += 1
    return missed


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []
    for emg_on in (0.55, 0.60, 0.65, 0.70, 0.75):
        for emg_off in (0.25, 0.30, 0.35, 0.40):
            if emg_off >= emg_on:
                continue
            th = Thresholds(emg_on=emg_on, emg_off=emg_off)
            clock = [0.0]
            with patch("control.gesture.time") as mock_time:
                mock_time.side_effect = lambda: clock[0]
                false_rest = count_intents(GestureDecoder(th), REST_SAMPLES, clock)
                clock[0] = 0.0
                false_noisy = count_intents(GestureDecoder(th), NOISY_SAMPLES, clock)
                clock[0] = 0.0
                missed = count_missed_starts(GestureDecoder(th), CONTRACT_SAMPLES, clock)
            rows.append(
                {
                    "emg_on": emg_on,
                    "emg_off": emg_off,
                    "false_triggers_rest": false_rest,
                    "false_triggers_noisy": false_noisy,
                    "missed_start_ticks": missed,
                    "recommended": emg_on == 0.65 and emg_off == 0.35,
                }
            )

    with OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    print(f"Wrote {len(rows)} rows to {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
