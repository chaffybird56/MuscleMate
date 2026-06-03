# Integration handoff (controls ↔ design partners)

## Purpose

Cross-functional handoff package for software, controls, and hardware design after bench sign-off.

## Deliverables

| Artifact | Location |
|----------|----------|
| Motion sequences (versioned Python) | `sequences/motion_sequences.py` |
| Build / run instructions | `docs/BUILD_INSTRUCTIONS.md` |
| Safety interlock matrix | `docs/SAFETY_INTERLOCK_MATRIX.md` |
| Bench checklist | `commissioning/bench_checklist.yaml` |
| JSONL cycle trace (optional) | `--trace traces/run.jsonl` |

## Bench sign-off

| Field | Value |
|-------|-------|
| signoff_id | _fill after bench_commission.py_ |
| Date | |
| Technician | |

## Integration rig bring-up

```bash
python scripts/run_sequence.py --adapter integration --signoff-id <signoff_id> --sequence sterilization
python -m control.cli --adapter integration --signoff-id <signoff_id> --demo --trace traces/demo.jsonl
```

## Contact points

- **Hardware**: adapter modules in `hardware/adapters/`
- **Safety**: `safety/interlocks.py` — do not bypass in production
- **Application FSM**: `control/state_machine.py`
- **EMG / gestures**: `control/gesture.py`
