## MuscleMate — Myoelectric Robotic Sterilization Helper

Myoelectric signals from your forearm drive a robot arm that shuttles surgical instruments into an autoclave with deterministic, safe motion primitives.

<div align="center">

https://github.com/user-attachments/assets/dcc49717-62b0-4c19-89aa-dea88fd53750

</div>

---

## At a glance

- **Two-channel EMG acquisition** — envelope, hysteresis, and intent decode on a guarded control loop ([signal chain](docs/signal_chain.md))
- **Bench biosignal front-end** — differential conditioning, grounding, and oscilloscope bring-up before integration ([hardware guide](hardware/front_end_bench.md))
- **Safety-critical interlocks** — E-stop, duty cycles, technician enable ([safety matrix](docs/SAFETY_INTERLOCK_MATRIX.md))
- **Power & duty-cycle budget** — 24 V rail estimates and loop energy for compact bench hardware ([power budget](docs/power_budget.md))
- **R&D threshold sweeps** — logged `emg_on` / `emg_off` tradeoffs vs false triggers ([CSV](bench_logs/threshold_sweep_summary.csv) · [script](scripts/threshold_sweep.py))
- **Bench → integration adapters** — commission on stub rig, then swap bindings for QArm / biosignal hardware ([commissioning](docs/BENCH_COMMISSIONING.md))

---

## How it works

**Loop:** EMG → envelope → hysteresis → intent → guarded FSM → arm.

```
IDLE → SELECT_BIN → APPROACH → GRIP → LIFT → TRANSIT
  → OPEN_AUTOCLAVE → PLACE → CLOSE_AUTOCLAVE → HOME
```

Long-press on channel 2 triggers **ABORT** (E-stop latch + home). Motion is blocked unless interlocks and duty-cycle policy pass (`safety/interlocks.py`).

---

## Subsystems

| Layer | Doc / module | Role |
|-------|----------------|------|
| Signal chain | [docs/signal_chain.md](docs/signal_chain.md) | Sampling, noise margins, false-trigger budget |
| Front-end bench | [hardware/front_end_bench.md](hardware/front_end_bench.md) | Electrode → conditioning → ADC bring-up |
| Power | [docs/power_budget.md](docs/power_budget.md) | Rail draw, duty cycle, packaging notes |
| Control | `control/` | Gesture decode, FSM, CLI |
| Hardware adapters | `hardware/adapters/` | Bench vs integration rig wiring |
| Safety | [docs/SAFETY_INTERLOCK_MATRIX.md](docs/SAFETY_INTERLOCK_MATRIX.md) | Interlock map and motion gating |
| Sequences | `sequences/` | Versioned manufacturing / demo flows |

---

## Quick start

```bash
git clone https://github.com/chaffybird56/MuscleMate.git && cd MuscleMate
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
python -m control.cli --demo --adapter bench
```

| Task | Command |
|------|---------|
| Bench commissioning | `python scripts/bench_commission.py` |
| Threshold R&D sweep | `python scripts/threshold_sweep.py` |
| Manufacturing sequence | `python scripts/run_sequence.py --sequence manufacturing --adapter bench` |
| Demo + trace | `python -m control.cli --demo --adapter bench --trace traces/demo.jsonl` |
| Integration (after sign-off) | `python -m control.cli --adapter integration --signoff-id <id> --demo` |

Tune decode parameters via CLI (`--emg-on`, `--cooldown`, `--loop-rate`, …) — defaults in `control/config.py`.

---

## Documentation

### Electrical / bench design

| Doc | Contents |
|-----|----------|
| [docs/signal_chain.md](docs/signal_chain.md) | Acquisition → intent path, noise, calibration |
| [hardware/front_end_bench.md](hardware/front_end_bench.md) | Differential front-end, scope checks, troubleshooting |
| [hardware/README.md](hardware/README.md) | Hardware layer index |
| [docs/power_budget.md](docs/power_budget.md) | 24 V rails, duty cycle, loop energy |
| [bench_logs/threshold_sweep_summary.csv](bench_logs/threshold_sweep_summary.csv) | Threshold sweep results |
| [bench_logs/README.md](bench_logs/README.md) | Bench artifact index |

### Commissioning & handoff

| Doc | Contents |
|-----|----------|
| [docs/BUILD_INSTRUCTIONS.md](docs/BUILD_INSTRUCTIONS.md) | Install and verification |
| [docs/BENCH_COMMISSIONING.md](docs/BENCH_COMMISSIONING.md) | Technician bench steps |
| [docs/INTEGRATION_HANDOFF.md](docs/INTEGRATION_HANDOFF.md) | Cross-functional handoff |
| [docs/SAFETY_INTERLOCK_MATRIX.md](docs/SAFETY_INTERLOCK_MATRIX.md) | Interlocks and duty-cycle policy |
| [commissioning/bench_checklist.yaml](commissioning/bench_checklist.yaml) | Bench sign-off checklist |

**Repository layout:** `control/` · `hardware/` · `safety/` · `sequences/` · `scripts/` · `sim/` · `tests/` · `bench_logs/`

Production integration: replace stubs in `hardware/adapters/integration_rig.py` with QArm / biosignal bindings after bench sign-off.

---

<details>
<summary><strong>Technical depth — decode equations</strong></summary>

Full narrative and false-trigger acceptance criteria: [docs/signal_chain.md](docs/signal_chain.md).

Let $x_i[n]$ be raw EMG on channel $i \in \{1,2\}$ at sample rate $f_s$.

**Envelope** (rectify + low-pass):

$$
u_i[n] = (1-\alpha)u_i[n-1] + \alpha |x_i[n]|,\qquad
\alpha = 1 - e^{-2\pi f_c/f_s}.
$$

**Normalize** (rest baseline $\mu_i$, $\sigma_i$):

$$
z_i[n] = \frac{u_i[n] - \mu_i}{\sigma_i}.
$$

**Hysteresis** ($\theta_{\text{on}} > \theta_{\text{off}}$):

$$
c_i[n] =
\begin{cases}
1, & z_i[n] \ge \theta_{\text{on}} \text{ or } (c_i[n-1] = 1 \text{ and } z_i[n] > \theta_{\text{off}}),\\
0, & \text{otherwise.}
\end{cases}
$$

Debounce $T_d$, cooldown $T_c$, long-press $T_\ell \approx 1.2\,\mathrm{s}$ on ch2 → ABORT. Typical defaults: $f_s$ 200–1000 Hz, $f_c$ 3–6 Hz, $\theta_{\text{on}}$ / $\theta_{\text{off}}$ 0.65 / 0.35.

</details>

---

## License

MIT — see [LICENSE](LICENSE).
