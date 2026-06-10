# Hardware layer

| Path | Purpose |
|------|---------|
| [front_end_bench.md](front_end_bench.md) | Differential EMG conditioning, grounding, oscilloscope bring-up |
| [emg.py](emg.py) | `EMGReader` protocol + test sources |
| [adapters/](adapters/) | Bench vs integration rig wiring |
| [safeguarded_arm.py](safeguarded_arm.py) | Motion wrapper enforcing interlocks |

Control software is adapter-agnostic: bench commissioning must pass before integration phase (`AdapterPhase.INTEGRATION`).
