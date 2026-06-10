# EMG signal chain — acquisition through intent

End-to-end path from forearm myoelectric pickup to guarded robot intents. This document is the reference for threshold calibration, noise margin, and false-trigger tradeoffs on the bench and integration rigs.

## Chain overview

```
Skin electrodes → diff amp / conditioning → anti-alias filter → ADC → normalize → envelope → hysteresis → debounce → intent → SafetySupervisor → arm
```

Implementation split:

| Stage | Module | Notes |
|-------|--------|-------|
| Acquisition API | `hardware/emg.py` (`EMGReader`) | Two-channel normalized samples in \([0,1]\) |
| Envelope + features | `control/emg_features.py`, README math | Rectify + LPF, z-score vs rest baseline |
| Hysteresis + timing | `control/gesture.py`, `control/config.py` | `emg_on` / `emg_off`, debounce, cooldown, long-press ABORT |
| Safety gating | `safety/interlocks.py` | Motion blocked unless interlocks + duty cycle OK |

Bench adapter uses `StaticEMGSource` / scripted profiles (`sim/emg_profiles.py`). Production integration swaps `hardware/adapters/integration_rig.py` bindings for Quanser / biosignal hardware — see [hardware/front_end_bench.md](../hardware/front_end_bench.md).

## Sampling and filter assumptions

| Parameter | Default / range | Effect |
|-----------|-----------------|--------|
| Control loop \(f_\text{loop}\) | 50 Hz (`Sampling.loop_hz`) | Intent update rate; must exceed envelope bandwidth |
| EMG sample rate \(f_s\) | 200–1000 Hz (front-end) | Nyquist for 3–6 Hz envelope corner |
| Envelope corner \(f_c\) | 3–6 Hz | Separates contraction burst from high-frequency noise |
| `emg_on` / `emg_off` | 0.65 / 0.35 default | Hysteresis band — see [threshold sweeps](../bench_logs/threshold_sweep_summary.csv) |
| Debounce \(T_d\) | 0.15 s | Suppresses contact bounce / motion artifact glitches |
| Cooldown \(T_c\) | 0.35 s | Limits intent repetition rate (duty-cycle partner) |

## Noise and non-ideal interfaces

Real bench captures include:

- **Motion artifact** — cable flex and connector microphonics during arm traverse  
- **Power-line hum** — 60 Hz pickup on long electrode leads  
- **Baseline drift** — sweat / impedance change over a shift  
- **Crosstalk** — channel correlation when both forearm groups co-contract  

Mitigations used in software (always) and recommended on hardware (integration):

1. Differential electrode pair per channel; single-point analog ground near ADC  
2. Rest capture for \(\mu_i, \sigma_i\) before each shift; re-calibrate if false triggers rise  
3. Set \(\theta_\text{on}\) at ~95th percentile of rest envelope + margin; \(\theta_\text{off} \approx 0.5\,\theta_\text{on}\)  
4. Increase debounce when mechanical vibration is present on the bench rig  
5. Log JSONL traces (`--trace`) and compare envelope margin vs interlock events  

## False-trigger budget

Target for manufacturing validation sequence (`sequences/motion_sequences.py`):

| Metric | Acceptance (bench) |
|--------|---------------------|
| Uncommanded intents during 60 s rest | 0 |
| Missed START on scripted contraction | ≤ 1 per 10 trials |
| ABORT long-press latency | 1.2 s ± 0.15 s |

Run `python scripts/threshold_sweep.py` to regenerate sweep data after changing defaults in `control/config.py`.

## Related docs

- [hardware/front_end_bench.md](../hardware/front_end_bench.md) — conditioning, grounding, scope checks  
- [docs/power_budget.md](power_budget.md) — rail draw vs duty cycle  
- [docs/BENCH_COMMISSIONING.md](BENCH_COMMISSIONING.md) — technician sign-off flow  
