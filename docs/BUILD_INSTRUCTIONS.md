# Build instructions

## Environment

- Python 3.9+
- Optional: Quanser QArm / biosignal bindings (integration adapter)

```bash
git clone https://github.com/chaffybird56/MuscleMate.git
cd MuscleMate
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

## Verification

```bash
pytest
python scripts/bench_commission.py
python scripts/run_sequence.py --sequence manufacturing
python -m control.cli --demo
```

## Manufacturing duty-cycle run

```bash
python -m control.cli --demo --adapter bench --trace traces/shift.jsonl
```

Review trace with any JSONL viewer; each row includes FSM state, intent, and safety snapshot events.
