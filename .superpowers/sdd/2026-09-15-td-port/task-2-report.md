# Task 2 Report — tracking: blob track + Target logic

## Status
Done.

## Commits
- `7b5195d6728d1329c7f061e4bff619993c8935c5` — `feat(td): tracking COMP — blob track + Target logic`
- (pending) cleanup commit for reviewer fixes.

## Test summary
`uv run --with pytest pytest td/tests/test_tracking.py -v` → 8 passed.

## What changed
- Created `td/project1/tracking/target_logic.py` — pure-Python, TD-free `update_target()` matching the OF `Target` smoothing/influence/quiet/dying behavior.
- Created `td/project1/tracking/targets_exec.py` — Script CHOP glue that:
  - Parses real Blob Track CHOP per-track channels (`blob1:tx`, `blob1:ty`, `blob1:w`, `blob1:h`, `blob1:age`, ...).
  - Derives target label from the per-track prefix (`blob1` → label `1`).
  - Outputs an `error` channel and sets `ui.status` when no `*:tx`/`*:ty` channels are present so failure is not silent.
  - Maintains persistent per-label `Target` state keyed by blob label.
  - Updates `targets` Table DAT (`label, x, y, influence, quiet, dying`).
  - Outputs `bIsIdle` channel after 500 frames with no blobs.
  - Loads `target_logic` as a DAT module via `mod("target_logic")`.
- Created `td/tests/test_tracking.py` plus `td/tests/conftest.py` (adds `td/` to import path).
- Updated `td/README.md` with build instructions that match the real Blob Track CHOP channel naming.

## Verification run
- `uv run --with pytest pytest td/tests/test_tracking.py -v` → 8 passed.
- `uv run --with ruff ruff check --select E,W,F --ignore F821,E722 ...` → all passed.
- `uv run --with mypy --disable-error-code name-defined mypy td/project1/tracking/target_logic.py td/tests/test_tracking.py` → no issues. (`targets_exec.py` uses TD builtins `mod`/`ui`/`op`/`me`; mypy flags `mod` unless `name-defined` is disabled.)

## Concerns
- `targets_exec.py` uses `mod("target_logic")` and TouchDesigner globals (`me`, `op`, `ui`) that will only resolve inside TD; this is expected for Script CHOP glue.
- The Blob Track CHOP prefix format assumption (`blobN:tx`/`blobN:ty`) is based on TouchDesigner documentation and the reviewer finding. If a project uses a different Blob Track CHOP output naming convention, `_parse_blob_tracks` will fall back to the `error` channel.
- I cannot run TouchDesigner, so the Script CHOP wiring has not been exercised live.
