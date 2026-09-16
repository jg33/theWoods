### Task 3: `control` — Light logic + WoodsState

**Files:**
- Modify: `td/project1/control.tox`
- Create: `td/project1/control/control_exec.py`, `td/project1/control/light_logic.py`
- Create: `td/tests/test_control.py`

**Interfaces:**
- Consumes: `targets` DAT (Task 2 schema), `tracks` DAT (`id, sx, sy, ex, ey, ip`).
- Produces: `lights` Table DAT — `id, locationPercent, intensity`; `state` channel (0=NORMAL,1=IDLE,2=QUIET,3=NIGHT,4=DARK).

- [ ] **Step 1: Write light logic test first**

```python
# light_logic.py
import math

def dist_influence(dist, max_dist, target_influence):
    di = (max_dist - dist) / max_dist
    di = max(0.0, min(1.0, di))
    if di < 0.1: di = 0.0
    return di * target_influence

def track_percent(current, start, end):
    total = math.dist(start, end)
    return math.dist(start, current) / total if total else 0.0

def update_light(l, targets, max_dist):
    # l: dict(current=[x,y], move_target=[x,y], intensity, start, end)
    nearest = min(targets, key=lambda t: math.dist(l['current'], t['current']), default=None)
    for t in targets:
        d = math.dist(l['current'], t['current'])
        if d < max_dist:
            di = dist_influence(d, max_dist, t['influence'])
            l['move_target'][0] += (t['current'][0] - l['move_target'][0]) * di
            l['move_target'][1] += (t['current'][1] - l['move_target'][1]) * di
    if nearest:
        nd = math.dist(l['current'], nearest['current'])
        l['target_intensity'] = ((max_dist - nd) / max_dist) * nearest['influence']
    l['intensity'] += (l.get('target_intensity', 0) - l['intensity']) * 0.01
    l['current'][0] += (l['move_target'][0] - l['current'][0]) * 0.001
    l['current'][1] += (l['move_target'][1] - l['current'][1]) * 0.001
    l['locationPercent'] = track_percent(l['current'], l['start'], l['end'])
    return l
```

Tests: intensity rises as target approaches; locationPercent 0 at start, 1 at end; no targets → intensity decays via lerp toward 0 target.

- [ ] **Step 2: Implement + WoodsState**

`control_exec.py`: per cook, read targets/tracks DATs, run `update_light` per light, write `lights` DAT. State machine: `bIsIdle`→IDLE; all targets quiet→QUIET; else NORMAL. IDLE: per-light Noise CHOP intensity pulse + timed highlight param. NIGHT/DARK: param pages only for now.

- [ ] **Step 3: Verify + commit**

`uv run pytest tests/test_control.py -v` PASS; commit `feat(td): control COMP — Light logic + WoodsState`.

---

