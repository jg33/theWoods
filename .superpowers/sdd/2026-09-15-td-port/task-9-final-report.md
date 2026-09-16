# Task 9 — Final review fix report

Branch: `td-port` worktree. Fixes applied from the whole-branch review.

## CRITICAL

1. **control_exec.py DAT lookups** — `control_exec.onCook` now reads the targets and
   tracks Table DATs by path via `op("../tracking/targets")` and `op("../trackUI/tracks")`
   (mirroring the `net_exec.py` `op("../control/lights")` pattern). Script CHOP inlets
   accept CHOP-family only, so wiring Table DATs in was invalid. The existing
   `_parse_targets`/`_parse_tracks` helpers are unchanged. Updated the control COMP build
   step and integration-checklist items that said to connect the DATs as COMP inputs.
   Adapted `test_max_distance_indexed_by_track_id` to mock `op()` instead of
   `scriptOp.inputs`.

2. **Manual-override gate** — added a `Manualoverride` toggle param (default Off) in
   `control_exec.onSetupParameters`. In `onCook`, when Off, `woods_state` is fed
   `None` for `manual_state`, so the automatic machine (`bIsIdle`/all-quiet) drives the
   state and IDLE/QUIET transitions are reachable again. Added a README control-section
   line: bind the tracking COMP's `bIsIdle` channel (from `targetscook` → `null1`) into
   `controlcook`'s `Bisidle` parameter (via an expression reference to
   `op('../tracking/null1')['bIsIdle']`) so IDLE has a driver.

3. **trackUI panelcook** — rewrote README step 6: `panelcook` is a **Script CHOP** with
   Callbacks DAT = `ui_exec`; the **Panel CHOP** (built in step 7) is wired into its
   input. Panel CHOP has no Callbacks DAT param, so the original instruction was wrong.

4. **Unsent control messages** — `net_logic.control_message` was never invoked on the
   wire. Added to `net_exec.py`: a `Light` int selector, `Moveamount` int, and pulse
   params `Identify`, `Calibrate`, `Zero`, `Stop`, `Move`; an `_send_control()` helper
   that unicasts `/light/<n>/<control>` (or `/light/<n>/move <steps>`) to the selected
   node's IP via `oscOut`; and `onPulse(scriptOp, par)` dispatch. README network section
   updated (one paragraph).

## MINOR

5. **tracking step 1** — `inOverhead` is now specified as an **In TOP** (landing for
   `depthIn.outOverhead`), not Video Device In / Movie File In.
6. **light_logic projection note** — added a `# ponytail:` comment on the
   `_closest_point_on_segment` lerp documenting the deliberate deviation from OF (keep
   the carriage on the rail) and the upgrade path (drop the projection for literal OF
   behavior).

## Tests

- `uv run --with pytest pytest td/tests/ -v`: **72 passed** (+2 regression tests vs the
  70 baseline — added in this pass, none removed).
- New: `test_manual_override_gate_reaches_automatic_idle` (override gate), and
  `test_onPulse_sends_control_message` (control-message send path). The old tracks-input
  test was updated for the `op()` lookup, not dropped.

## Concerns

- `net_exec.onPulse` uses the `Light` int param + pulse params; `Move` sends
  `Moveamount`. No heavy TD mocking was needed — the control tests mock `op()`/`par`
  exactly as the existing glue tests did.
