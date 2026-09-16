# Task 6 Report: `depthIn` — camera → merged cloud → overhead TOP

## Status
**COMPLETE**

## Summary
Built the `depthIn` COMP (camera-agnostic depth acquisition → merged point cloud → ortho overhead TOP) for the OF→TD port. Deliverable is precise numbered TD build instructions in `td/README.md` under "## depthIn COMP", plus a pure-Python `depth_logic.py` module with tests.

## Files
- **Added** `td/project1/depthIn/__init__.py`
- **Added** `td/project1/depthIn/depth_logic.py` — `parse_cameras` (TSV→dict keyed by id, skips blank/#/short/bad rows), `enabled_cameras`, `in_height_band` (inclusive predicate; `None` bound = unclipped).
- **Added** `td/tests/test_depthin.py` — 9 tests covering parse (header-only → `{}`, comment/blank, short/malformed rows, `true/1/yes/on` enabled variants, numeric params+roundtrips), enabled-cam filtering, and height-band edge cases (incl. unconfigured `None` bounds).
- **Modified** `td/README.md` — appended "## depthIn COMP" section with numbered build steps.

## Build instructions delivered (td/README.md)
1. **Per-camera sub-COMP** (`cam1`, `cam2`, ...): one Base COMP per TSV row. Camera-agnostic input swap point = named `input` TOP (Test Pattern stub now / Kinect TOP / Orbbec TOP). `input` → **TOP to POP** → **Transform POP** `calib` with params bound to the `cam{id}` row of `td/data/cameras.tsv` (`tx,ty,tz,rx,ry,rz,scale`); `enabled` is the per-cam master toggle. → Null POP `outcloudN` → sub-COMP output.
2. **Merge + clip + render**: **Merge POP** `merge1` (only enabled cams, `enabled_cameras` order) → height-band clip using custom params `clipMin`/`clipMax` → **Ortho Camera COMP** `camOverhead` (`rx=-90`, orthographic, width matched to the floor grid) → **Render TOP** `renderO` → Null TOP `outOverhead` → wired to `../tracking/inOverhead`. Debug Null POP `outCloud` exposed pre-render.
3. **Parameter defaults**: `clipMin 0.0`, `clipMax 2.0` (m), per-cam scale `1.0`, ortho `rx -90`.

## Verification (no hardware / no TD available)
- Pure-Python logic fully unit-tested and passing: `uv run --with pytest pytest td/tests/ -v` → **67 passed**.
- TD-side verification steps written in the README using a Test Pattern stub on every cam so the merge/render/clip/top-down path validates before any depth hardware is attached: confirm `renderO` fills, `outOverhead` non-black, `outCloud` merges all active cams, `tracking` emits target rows, and a disabled-cam row drops that cloud from the merge.
- **Build requirement noted**: the point-cloud TOPs (Top to POP, Merge, Ortho Camera + Render) need TouchDesigner **2023.10k+ / 2025** builds.

## Notes / concerns
- `cameras.tsv` currently contains only the header (no data rows yet) — `parse_cameras` correctly returns `{}` until cams are added; the merge/clip/render steps document wiring once rows exist. This is expected: calibration happens against real hardware.
- Kept lazy: Transform/Merge POPs and the ortho camera do all geometry/clip math natively in TD; `depth_logic.py` only covers what must live outside TD (TSV parsing, enabled filtering, band-predicate sanity check). No reimplementation of TD-native math.
