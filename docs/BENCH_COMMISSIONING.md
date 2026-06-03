# Bench commissioning (technician-led)

Complete this phase on the **bench rig adapter** before any integration-rig software bring-up.

## Steps

1. Wire interlocks per `docs/SAFETY_INTERLOCK_MATRIX.md`.
2. Run bench probe and validation sequence:

```bash
pip install .
python scripts/bench_commission.py
```

3. Walk through `commissioning/bench_checklist.yaml` and record pass/fail.
4. Copy the generated `signoff_id` into `docs/INTEGRATION_HANDOFF.md`.

## Adapter selection

| Phase | Adapter class | CLI |
|-------|---------------|-----|
| Bench | `BenchRigAdapter` | `--adapter bench` |
| Integration | `IntegrationRigAdapter` | `--adapter integration --signoff-id <id>` |

Bench mode uses technician enable and simulated I/O so mechanics and controls can be validated independently.
