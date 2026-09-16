### Task 6: `depthIn` — camera → merged cloud → overhead TOP

**Files:**
- Modify: `td/project1/depthIn.tox`
- Create: `td/project1/depthIn/cam_exec.py` (if needed for per-cam enable)

**Interfaces:**
- Consumes: `cameras.tsv` calibration (id, enabled, tx..rz, scale).
- Produces: `outOverhead` TOP → `tracking.inOverhead`; `outCloud` POP debug.

- [ ] **Step 1: Per-camera sub-COMP**

`cam1` sub-COMP: camera's native TOP → TOP to POP → Transform POP (params bound to cameras.tsv row). Stub with a Test Pattern/Video Device TOP until hardware is attached — validates the merge/render path.

- [ ] **Step 2: Merge + clip + render**

Merge POP all cams → height-band clip (params `clipMin/clipMax`) → ortho top-down camera → Render TOP → `outOverhead`. Wire to `tracking.inOverhead`.

- [ ] **Step 3: Verify + commit**

With stub input, confirm overhead TOP renders and `tracking` produces target rows. Commit `feat(td): depthIn — POP merge/clip/overhead render`.

---

