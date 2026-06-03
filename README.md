## 🦾 MuscleMate — Myoelectric Robotic Sterilization Helper

Myoelectric signals from your forearm drive a robot arm that shuttles surgical instruments into an autoclave with deterministic, safe motion primitives.  

<div align="center">

https://github.com/user-attachments/assets/dcc49717-62b0-4c19-89aa-dea88fd53750

</div>

---

## 🌟 Highlights
- **Robotic arm automation** with **safety interlocks**, E-stop safeguarding, and **deterministic motion** on manufacturing-style **duty cycles** (`safety/`, `SafeguardedArm`).
- **Modular hardware adapters** for **technician-led bench commissioning** before controls integration (`hardware/adapters/`, `docs/BENCH_COMMISSIONING.md`).
- **Versioned Python motion sequences**, **build instructions**, and **cross-functional handoff** docs (`sequences/`, `docs/BUILD_INSTRUCTIONS.md`, `docs/INTEGRATION_HANDOFF.md`).
- Myoelectric **gesture decoding** (hysteresis, debounce, long-press abort) driving a sterilization **finite-state machine**.
- **JSONL digital-twin traces** for cycle analytics (`--trace`); **EMG feature vectors** ready for edge ML classifiers (`control/emg_features.py`).
- CI runs `pytest`, bench commissioning, and manufacturing validation sequences.

---

## 🗂️ Project Overview

```
├── control/                  # CLI, FSM, gesture decode, JSONL trace, EMG features
├── hardware/
│   ├── adapters/             # Bench rig + integration rig (modular I/O)
│   ├── arm.py                # Arm protocol + stub
│   ├── safeguarded_arm.py    # Interlock-gated motion
│   └── emg.py
├── safety/                   # Interlocks + manufacturing duty-cycle policy
├── sequences/                # Python motion sequences (sterilization / validation)
├── commissioning/            # Technician bench checklist (YAML)
├── docs/                     # Bench, handoff, build, safety matrix
├── scripts/                  # bench_commission.py, run_sequence.py
├── sim/                      # Scripted EMG profiles
└── tests/
```

---

## ⚡ Quick Overview

1. Flex a muscle → two EMG channels capture the activity.  
2. Signal cleaning yields a smooth strength value (the envelope).  
3. Dual thresholds with hysteresis decide on/off to avoid chatter.  
4. Debounce, cooldown, and long-press logic produce stable intents.  
5. The robot executes a safe sequence: select bin → approach → grip → lift → autoclave → place → close → home.

That’s the loop: **muscle → intent → motion** until the instrument is safely sterilized.

---

## 🚀 Quick Start

### 1. Setup
```bash
git clone https://github.com/chaffybird56/MuscleMate.git
cd MuscleMate
python -m venv .venv && source .venv/bin/activate  # optional but recommended
pip install .
```

### 2. Bench commissioning (technician-led)
```bash
python scripts/bench_commission.py
python scripts/run_sequence.py --sequence manufacturing --adapter bench
```

### 3. Run sterilization demo (interlocks + duty cycle)
```bash
python -m control.cli --demo --adapter bench --trace traces/demo.jsonl
musclemate --demo --adapter bench
```

### 4. Integration rig (after bench sign-off)
```bash
python -m control.cli --adapter integration --signoff-id BENCH-2026-001 --demo
python scripts/run_sequence.py --adapter integration --signoff-id BENCH-2026-001 --sequence sterilization
```

See `docs/INTEGRATION_HANDOFF.md` for the full handoff package.

### 5. Connect production hardware
Replace stubs inside `hardware/adapters/integration_rig.py` with Quanser QArm / biosignal bindings; keep safety wiring in `safety/interlocks.py`.

---

## ⚙️ Configuration Cheatsheet

| Parameter | Location | Purpose |
| --- | --- | --- |
| `Thresholds` | `control.config` | EMG on/off thresholds, debounce, cooldown, long-press abort |
| `Waypoints` | `control.config` | Bin/autoclave/home coordinates |
| `Speeds` | `control.config` | Motion profile speeds & gripper dwell |
| `Sampling` | `control.config` | Runtime and loop rate defaults |

Override values at runtime with CLI flags, e.g.:
```bash
python -m control.cli --emg-on 0.7 --cooldown 0.4 --loop-rate 60
```

---

## 🧠 From Muscle to Motion

1. **Acquire EMG** from two channels → normalize to `[0, 1]`.
2. **Deadband + hysteresis** debounce the raw signal into stable "pressed" states.
3. **Gesture mapping** converts channel patterns into `Intent` enums (start, grip, toggle door, abort).
4. **Finite-state machine** (`State`) ensures safe, sequential motion primitives:

```
IDLE → SELECT_BIN → APPROACH → GRIP → LIFT → TRANSIT
     → OPEN_AUTOCLAVE → PLACE → CLOSE_AUTOCLAVE → HOME
```

5. **Safety**: Interlocks + duty-cycle policy gate every move; long-press ABORT latches E-stop and homes the arm.

---

## 🧮 Signal Processing & Decision Flow 

Let $x_i[n]$ be raw EMG on channel $i \in \{1,2\}$ sampled at $f_s$ Hz.

### 1) Create the envelope

Rectify and low-pass filter to obtain a smooth envelope $u_i[n]$:

$$
u_i[n] = (1-\alpha)u_i[n-1] + \alpha |x_i[n]|,\qquad
\alpha = 1 - e^{-2\pi f_c/f_s}.
$$

- $f_c$: 3–6 Hz cutoff keeps the envelope slow and stable.
- Intuition: a moving average of the absolute EMG suppresses spikes.

### 2) Normalize (z-score)

From a rest segment, compute baseline $\mu_i, \sigma_i$ and normalize:

$$
z_i[n] = \frac{u_i[n] - \mu_i}{\sigma_i}.
$$

- Different electrodes, different baselines—z-scores compare apples to apples.

### 3) Apply hysteresis

Use on/off thresholds $(\theta_{\text{on}}, \theta_{\text{off}})$ with $\theta_{\text{on}} > \theta_{\text{off}}$:

$$
c_i[n] =
\begin{cases}
1, & z_i[n] \ge \theta_{\text{on}} \text{ or } (c_i[n-1] = 1 \text{ and } z_i[n] > \theta_{\text{off}}),\\
0, & \text{otherwise.}
\end{cases}
$$

- Once “on,” the signal must fall below $\theta_{\text{off}}$ to turn off—no flicker at the boundary.

### 4) Debounce and cooldown

- **Debounce:** require $c_i[n] = 1$ for $T_d$ seconds → $N_d = \lceil T_d / (1/f_s) \rceil$ consecutive samples.
- **Cooldown:** ignore new gestures for $T_c$ seconds after accepting an intent.

### 5) Long-press abort

If channel 2 stays active for $T_\ell \approx 1.2$ s, issue an ABORT and send the arm home.

---

## 🔬 Typical Values & Calibration

| Symbol | Meaning | Typical |
| --- | --- | --- |
| $f_s$ | EMG sampling rate | 200–1000 Hz |
| $f_c$ | Envelope cutoff | 3–6 Hz |
| $\theta_{\text{on}}$ | On threshold (z-score) | 0.65–0.9 |
| $\theta_{\text{off}}$ | Off threshold (z-score) | 0.30–0.5 |
| $T_d$ | Debounce time | 0.10–0.20 s |
| $T_c$ | Cooldown | 0.30–0.40 s |
| $T_\ell$ | Long-press (abort) | ≈ 1.2 s |

**Calibration tip:** Take a rest recording, set $\theta_{\text{on}}$ near the 95th percentile + margin, and $\theta_{\text{off}}$ at roughly half that. Adjust until confident contractions trigger reliably without false positives.

---

## 🧪 Testing

```bash
pip install pytest
pytest
```

Unit tests validate gesture decoding (debounce, cooldown, long-press) and deterministic EMG playback. Extend with hardware-in-the-loop tests as you integrate real sensors.

### Hardware-in-the-loop (HIL) smoke test
- Connect your EMG acquisition and arm bindings.
- Run `python -m control.cli --loop-rate 60 --runtime 30` to exercise the loop at control-rate.
- Monitor logs for state transitions; abort safely with a long press.
- Add assertions around `ControllerEvent` streams to automate pass/fail checks.

---

## 🧪 What You Should See

- Reliable pick/place of mock instruments into the autoclave (sim + hardware).  
- Long-press abort always returns to **home**.  
- Stable control thanks to the envelope, hysteresis, and debounce stages.

**Limitations.** EMG varies day-to-day; revisit thresholds periodically. The autoclave door dwell is simulated in the stub implementation. Expanding the gesture set will require additional channels or a classifier.

---

## 🛠️ Extending MuscleMate
- Add new intents by expanding `Intent` and updating the transition logic in `state_machine.py`.
- Integrate real EMG hardware by implementing `EMGReader`.
- Plug in motion planning or collision checking in `SterilizationController.move_to`.
- Log or stream `ControllerEvent` instances via the optional sink in `run_controller`.

---

## 🔧 Customization Checklist
- [ ] Extend the `Intent` enum and FSM transitions for new gestures.
- [ ] Wire up your EMG backend through `EMGReader`.
- [ ] Enhance `SterilizationController.move_to` with planners or collision avoidance.
- [ ] Attach a telemetry sink to `run_controller` for logging or streaming events.

---

## 📚 Glossary
- **EMG** — Electromyography; electrical activity from muscles.
- **Envelope** — Smoothed strength signal after rectification + low-pass filtering.
- **Hysteresis** — Using two thresholds to avoid flicker around the setpoint.
- **Debounce** — Minimum press duration to confirm state changes.
- **Cooldown** — Timeout to prevent rapid re-triggering.
- **Waypoint** — Predefined robot pose used to build motion sequences.

---

## 📜 License
MIT — see `LICENSE`.

