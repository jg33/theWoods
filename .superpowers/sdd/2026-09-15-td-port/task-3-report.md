# Task 3 Report — control COMP

Done.

## Commits
- `8f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0` — `feat(td): control COMP — Light logic + WoodsState`

## Test summary
`uv run --with pytest pytest td/tests/ -v` → 24 passed.

## What changed
- Created `td/project1/control/light_logic.py` — pure-Python, TD-free Light reaction logic:
  - `dist_influence(dist, max_dist, target_influence)` matches the OF `Light::update` dist-to-influence curve: `(maxD-dist)/maxD`, clamped 0..1, zeroed below 0.1, scaled by target influence.
  - `track_percent(current, start, end)` and `_closest_point_on_segment(p, a, b)` for linear track motion and percent reporting.
  - `make_light(id, start, end, max_distance=300)` replicates OF `Light` constructor: light begins at midpoint of track, `move_target` initialized to midpoint, `intensity=0`.
  - `woods_state(b_is_idle, targets, manual_state=None)` — state precedence: manual NIGHT/DARK > IDLE > QUIET > NORMAL. QUIET is only entered when there is at least one target and all are quiet.
  - `update_light(l, targets, state, t=0.0, elapsed=0.0, noise_func=None)` — per-frame update.
    - NORMAL: for each target inside `maxDistance`, compute `distInfluence`, project target onto light track, lerp `move_target` by influence. Nearest target sets `target_intensity` (clamped, scaled by its influence). Current position lerps toward `move_target` at 0.001; intensity lerps at 0.01.
    - IDLE: per-light `bIsIdleHighlight` pulses with noise; otherwise dims to 0.005.
    - QUIET: continuous per-light noise pulse.
    - NIGHT/DARK: parameter-page placeholders; intensity is left untouched.
  - `_default_noise` is a deterministic octaved-sine fallback for tests/standalone use; in TD the build instructions note how to wire a real Noise CHOP.

- Created `td/project1/control/control_exec.py` — Script CHOP/DAT glue:
  - Loads `light_logic` as a sibling DAT module via `mod("light_logic")`.
  - Declares parameters: `Manualstate`, `Bisidle`, per-light `Maxdistance{i}` (0-7), `Idlehighlightmin`, `Idlehighlightmax`.
  - Reads `targets` DAT (input 0, columns `label,x,y,influence,quiet,dying`) and `tracks` DAT (input 1, columns `id,sx,sy,ex,ey,ip`).
  - Maintains persistent per-light state via `scriptOp.fetch/store("lights")` and resyncs when track count changes.
  - Computes `WoodsState` and writes a single `state` channel (0=NORMAL, 1=IDLE, 2=QUIET, 3=NIGHT, 4=DARK).
  - In IDLE, ensures at least one light is highlighted (`bIsIdleHighlight`) for a random duration between `Idlehighlightmin` and `Idlehighlightmax`.
  - Writes `lights` Table DAT (`id, locationPercent, intensity`) via `op("../lights")`.

- Created `td/tests/test_control.py`:
  - `light_logic` unit tests: dist influence edge cases, track percent, light creation, intensity ramp/decay, location lerp, idle/quiet noise, state machine precedence.
  - `control_exec` glue tests: mock DAT parsing for targets/tracks, idle highlight picker.

- Updated `td/README.md` with numbered build instructions for the `control` COMP inside TouchDesigner.

## Verification run
- `uv run --with pytest pytest td/tests/ -v` → 24 passed.
- `uv run --with ruff ruff check --select E,W,F --ignore F821,E722,E741,E501 td/project1/control/control_exec.py td/project1/control/light_logic.py td/tests/test_control.py td/project1/tracking/targets_exec.py td/project1/tracking/target_logic.py td/tests/test_tracking.py` → all passed.
- `uv run --with mypy mypy --disable-error-code name-defined td/project1/control/control_exec.py td/project1/control/light_logic.py td/tests/test_control.py` → no issues.

## Concerns
- `light_logic.py` uses an artificial noise fallback. In TD the build instructions describe wiring a real Noise CHOP to `control_exec.py` for a closer `ofNoise(t+id*6.66)` match.
- `control_exec.py` references TD builtins (`me`, `op`, `mod`, `ui`) that only resolve inside TouchDesigner, as expected for glue code.
- Per-light `Maxdistance` parameters are indexed 0-7 to match the OF GUI; adding more than 8 lights requires updating `onSetupParameters`.
