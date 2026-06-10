## MuscleMate — Myoelectric Robotic Sterilization Helper

Myoelectric signals from your forearm drive a robot arm that shuttles surgical instruments into an autoclave with deterministic, safe motion primitives.

<div align="center">

https://github.com/user-attachments/assets/dcc49717-62b0-4c19-89aa-dea88fd53750

</div>

---

## Highlights

- **Safety & duty cycles**— interlocks, E-stop, deterministic motion ([safety matrix](docs/SAFETY_INTERLOCK_MATRIX.md))
- **Bench → integration**— modular adapters and technician commissioning ([bench guide](docs/BENCH_COMMISSIONING.md))
- **Motion sequences & handoff**— versioned Python sequences, build steps, partner docs ([build](docs/BUILD_INSTRUCTIONS.md) · [handoff](docs/INTEGRATION_HANDOFF.md))
- **Muscle → intent → motion**— EMG gesture decode + sterilization FSM (`control/`)

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
| Manufacturing sequence | `python scripts/run_sequence.py --sequence manufacturing --adapter bench` |
| Demo + trace | `python -m control.cli --demo --adapter bench --trace traces/demo.jsonl` |
| Integration (after sign-off) | `python -m control.cli --adapter integration --signoff-id <id> --demo` |

Tune thresholds via CLI (`--emg-on`, `--cooldown`, `--loop-rate`, etc.) — defaults live in `control/config.py`.

---

## How it works

**Loop:**EMG → envelope → hysteresis → intent → guarded FSM → arm.

```
IDLE → SELECT_BIN → APPROACH → GRIP → LIFT → TRANSIT
 → OPEN_AUTOCLAVE → PLACE → CLOSE_AUTOCLAVE → HOME
```

Long-press on channel 2 triggers **ABORT**(E-stop latch + home). Details: [safety matrix](docs/SAFETY_INTERLOCK_MATRIX.md).

---

## Signal processing

Full chain, noise margins, and false-trigger budget: **[docs/signal_chain.md](docs/signal_chain.md)**.

Let $x_i[n]$ be raw EMG on channel $i \in \{1,2\}$ at sample rate $f_s$.

**Envelope**(rectify + low-pass):

$$
u_i[n] = (1-\alpha)u_i[n-1] + \alpha |x_i[n]|,\qquad
\alpha = 1 - e^{-2\pi f_c/f_s}.
$$

**Normalize**(rest baseline $\mu_i$, $\sigma_i$):

$$
z_i[n] = \frac{u_i[n] - \mu_i}{\sigma_i}.
$$

**Hysteresis**($\theta_{\text{on}} > \theta_{\text{off}}$):

$$
c_i[n] =
\begin{cases}
1, & z_i[n] \ge \theta_{\text{on}} \text{ or } (c_i[n-1] = 1 \text{ and } z_i[n] > \theta_{\text{off}}),\\
0, & \text{otherwise.}
\end{cases}
$$

**Debounce**$T_d$, **cooldown**$T_c$ after each intent; **long-press**$T_\ell \approx 1.2\,\mathrm{s}$ on ch2 → ABORT.

| Symbol | Typical |
|--------|---------|
| $f_s$ | 200–1000 Hz |
| $f_c$ | 3–6 Hz |
| $\theta_{\text{on}}$ / $\theta_{\text{off}}$ | 0.65–0.9 / 0.30–0.5 |
| $T_d$ / $T_c$ / $T_\ell$ | 0.10–0.20 s / 0.30–0.40 s / ≈1.2 s |

Calibrate from a rest capture: set $\theta_{\text{on}}$ near the 95th percentile plus margin, $\theta_{\text{off}}$ ~ half of that.

---

## Documentation

| Doc | Contents |
|-----|----------|
| [docs/signal_chain.md](docs/signal_chain.md) | Acquisition → intent path, noise, false-trigger budget |
| [docs/power_budget.md](docs/power_budget.md) | 24 V rail draw, duty cycle, loop energy |
| [hardware/front_end_bench.md](hardware/front_end_bench.md) | Differential front-end, scope bring-up |
| [docs/BUILD_INSTRUCTIONS.md](docs/BUILD_INSTRUCTIONS.md) | Install, verify, manufacturing runs |
| [docs/BENCH_COMMISSIONING.md](docs/BENCH_COMMISSIONING.md) | Technician bench steps |
| [docs/INTEGRATION_HANDOFF.md](docs/INTEGRATION_HANDOFF.md) | Cross-functional handoff |
| [docs/SAFETY_INTERLOCK_MATRIX.md](docs/SAFETY_INTERLOCK_MATRIX.md) | Interlocks & duty-cycle policy |
| [commissioning/bench_checklist.yaml](commissioning/bench_checklist.yaml) | Bench sign-off checklist |
| [bench_logs/threshold_sweep_summary.csv](bench_logs/threshold_sweep_summary.csv) | R&D threshold sweep results |

**Layout:** `control/` · `hardware/` · `safety/` · `sequences/` · `scripts/` · `sim/` · `tests/` · `bench_logs/`

Production hardware: swap stubs in `hardware/adapters/integration_rig.py` for QArm / biosignal bindings.

---

## License

MIT — see [LICENSE](LICENSE).
