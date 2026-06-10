# Power budget — bench rig (24 V class)

Estimates for duty-cycle planning and **power constraint** reviews on the sterilization helper bench. Values are measured or bounded from commissioning runs on `BenchRigAdapter`; integration rig should re-measure with production arm loads.

## Rail summary

| Subsystem | Rail | Idle (typ.) | Active peak | Notes |
|-----------|------|-------------|-------------|-------|
| Arm + gripper | 24 V | 0.4 A | 2.8 A | Traverse + close peaks; duty-cycle capped |
| Control PC / SBC | 12 V → 5 V | 0.6 A @ 5 V | 0.9 A @ 5 V | 50 Hz control loop + logging |
| EMG front-end | 5 V / 3.3 V | 35 mA | 55 mA | Dual channel + ADC active conversion |
| Interlock IO | 24 V isolated | 10 mA | 40 mA | E-stop chain, pressure OK sense |

## Duty-cycle policy (links safety)

From `safety/interlocks.py` → `DutyCyclePolicy`:

| Mode | Max continuous motion | Cooldown enforced |
|------|----------------------|-------------------|
| Manufacturing validation | 45 s on / 15 s off | Yes (`cooldown_s` in gesture decoder) |
| Demo shift | 60 s on / 30 s off | Yes |
| E-stop latched | 0 (drive disabled) | Until reset + technician enable |

## Control-loop energy (software)

| Parameter | Value | Source |
|-----------|-------|--------|
| Loop rate | 50 Hz | `Sampling.loop_hz` |
| Typical shift | 180 s | `Sampling.runtime_s` |
| EMG reads per shift | 9 000 | \(50 \times 180\) |
| JSONL trace overhead | ~2% CPU | `--trace` enabled |

## Size / packaging notes

- Bench adapter uses modular DIN-rail interlock breakout — target enclosure footprint 200 mm × 150 mm × 80 mm for technician access  
- Electrode lead length ≤ 1.2 m to limit motion-artifact pickup (see signal chain doc)  

## Re-measure procedure

1. Bench PSU on 24 V rail; DMM in series for idle and peak traverse  
2. Run `python scripts/bench_commission.py` + manufacturing sequence  
3. Log peaks in commissioning report JSON; compare to table above  

Related: [SAFETY_INTERLOCK_MATRIX.md](SAFETY_INTERLOCK_MATRIX.md), [BENCH_COMMISSIONING.md](BENCH_COMMISSIONING.md).
