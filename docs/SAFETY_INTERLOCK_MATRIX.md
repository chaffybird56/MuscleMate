# Safety interlock matrix

| Interlock | Input | Blocks motion when | Reset |
|-----------|-------|-------------------|-------|
| E-stop | `estop_latched` | True | Technician key + `clear_estop()` |
| Door guard | `door_closed` | False (door open) | Close autoclave door |
| Gripper pressure | `gripper_pressure_ok` | False | Fix air line / sensor |
| Light curtain | `light_curtain_clear` | False | Clear zone |
| Technician enable | `technician_enable` | False | Hold enable on bench rig |
| Drive power | `drive_power_ok` | False | Restore 24V supply |

## Duty-cycle policy (manufacturing)

Configured in `safety/interlocks.py` → `DutyCyclePolicy`:

- `max_cycles_per_hour` — default 120
- `min_cycle_gap_s` — default 2.0 s between completed cycles
- `max_continuous_runtime_s` — default 1 h session cap

## Deterministic motion

- Speed clamped in `SafeguardedArm` (`max_speed`)
- Motion log records every commanded pose for audit
- FSM transitions gated by `SafetySupervisor.require_motion()`
