### Task 2: `tracking` — blob track + Target logic (with test TOP input)

Build tracking first against a synthetic TOP (a rendered test pattern or recorded footage), since `depthIn` needs real hardware to validate. `tracking` only cares about `inOverhead` TOP.

**Files:**
- Modify: `td/project1/tracking.tox`
- Create: `td/project1/tracking/targets_exec.py` (Script CHOP logic)
- Create: `td/tests/test_tracking.py`

**Interfaces:**
- Consumes: `inOverhead` TOP (luminance image, viewers as bright blobs on dark bg).
- Produces: `targets` Table DAT — cols `label, x, y, influence, quiet, dying`; `bIsIdle` channel out; `debug` TOP.

- [ ] **Step 1: Build the TOP→CHOP chain**

Inside `tracking`: `inOverhead` → Threshold TOP (params `threshold`, `dilate`, `blur`) → Blob Track CHOP (persistence ~1000ms, max jump 100px equivalents in CHOP params) → Script CHOP `targets_exec.py` → `targets` Table DAT + `bIsIdle` CHOP channel. Wire `debug` TOP = threshold output + blob overlay.

- [ ] **Step 2: Write Target logic test first**

`td/tests/test_tracking.py` — pure-Python test of the Target update function. Extract the per-target math into an importable function so it's testable outside TD:

```python
# target_logic.py — importable by both Script CHOP and tests
def update_target(t, measured_x, measured_y, seen):
    # t: dict(current=[x,y], influence, quiet_timer, dying)
    # returns updated t
    if seen:
        t['current'][0] += (measured_x - t['current'][0]) * 0.05
        t['current'][1] += (measured_y - t['current'][1]) * 0.05
        t['influence'] = min(1.0, t['influence'] + 0.01)
        t['dying'] = False
        moved = abs(measured_x - t['current'][0]) + abs(measured_y - t['current'][1])
        t['quiet_timer'] = 0 if moved > 20 else t['quiet_timer'] + 1
    else:
        t['influence'] -= 0.001
        t['dying'] = True
    t['quiet'] = t['quiet_timer'] > 300
    t['ready_to_die'] = t['influence'] <= 0
    return t
```

```python
def test_influence_ramps_up():
    t = dict(current=[0,0], influence=0.0001, quiet_timer=0, dying=False)
    for _ in range(100): t = update_target(t, 100, 100, True)
    assert t['influence'] == 1.0

def test_dying_drains_influence():
    t = dict(current=[0,0], influence=0.005, quiet_timer=0, dying=False)
    for _ in range(10): t = update_target(t, 0, 0, False)
    assert t['ready_to_die']

def test_quiet_after_threshold():
    t = dict(current=[0,0], influence=1, quiet_timer=0, dying=False)
    for _ in range(301): t = update_target(t, 0, 0, True)
    assert t['quiet']
```

Run: `cd td && uv run pytest tests/test_tracking.py -v` — verify FAIL, then implement `target_logic.py`, verify PASS.

- [ ] **Step 3: Wire Script CHOP to use it**

`targets_exec.py` calls `target_logic.update_target` per blob label per cook; maintains a persistent dict of targets keyed by Blob Track label; writes `targets` DAT; sets `bIsIdle` when no blobs for 500 frames.

- [ ] **Step 4: Commit**

```bash
git add td/
git commit -m "feat(td): tracking COMP — blob track + Target logic"
```

---

