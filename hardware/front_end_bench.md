# Bench biosignal front-end — integration reference

MuscleMate’s control stack reads two EMG channels through `EMGReader`. On the **bench rig**, commissioning uses scripted or static sources. Before switching to **`--adapter integration`**, complete the checks below on the physical front-end (Quanser biosignal bindings or equivalent differential EMG pickup).

## Reference signal path

```
Ag/AgCl electrodes (differential pair ×2)
  → instrumentation amplifier (high Z_in, CMRR ≥ 80 dB typ.)
  → 2nd-order anti-alias (fc ≈ 40 Hz)
  → 12–16 bit SAR ADC
  → USB / MCU host → EMGReader.read()
```

Design goals aligned with compact, low-power sensing:

- **Single-ended noise** at ADC input: target < 50 µV RMS during rest (scope + RMS math)  
- **Input bandwidth:** 20–450 Hz usable; envelope chain uses 3–6 Hz effective  
- **Isolation:** motor 24 V return separated from analog ground until single stitch near ADC  

## Bring-up checklist (hardware)

Complete before recording `signoff_id` for integration:

1. **Continuity** — electrode leads, DIN connectors, strain relief  
2. **Bias** — mid-rail bias present with electrodes disconnected (no rail saturation)  
3. **Oscilloscope** — rest capture 10 s: no clipping; 60 Hz hum < 10% of full-scale after diff amp  
4. **Oscilloscope** — intentional contraction: envelope visible on both channels; crosstalk < 15% peak-to-peak  
5. **Impulse test** — tap cable; debounce + hysteresis must not latch intent (software trace)  
6. **Drive power interlock** — verify `drive_power_ok` false blocks motion with live EMG  

Record scope screen captures under `bench_logs/scope/` (optional) with date and build id.

## Adapter wiring map

| Signal | BenchRigAdapter | IntegrationRigAdapter |
|--------|-----------------|------------------------|
| EMG ch1/ch2 | `StaticEMGSource` / `--demo` script | Vendor `EMGReader` binding |
| Interlocks | Simulated inputs in `bench_rig.py` | Production map in `integration_rig.py` |
| Arm | `QArmStub` motion | QArm or production arm driver |

Swap only in `hardware/adapters/integration_rig.py` — do not fork gesture or safety logic.

## Troubleshooting

| Symptom | Likely cause | Action |
|---------|--------------|--------|
| Saturated rest trace | Bad bias / loose electrode | Re-seat gel electrodes; check bias divider |
| False START intents | `emg_on` too low or noisy lead | Run threshold sweep; shorten leads |
| Missed GRIP | `emg_off` too high | Lower off threshold; check envelope α |
| 60 Hz comb on scope | Poor ground | Move analog ground stitch; ferrite on USB |

See [docs/signal_chain.md](../docs/signal_chain.md) for decode math and [docs/BENCH_COMMISSIONING.md](../docs/BENCH_COMMISSIONING.md) for sign-off.
