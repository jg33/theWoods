### Task 4: `trackUI` — performable track editor

**Files:**
- Modify: `td/project1/trackUI.tox`
- Create: `td/project1/trackUI/ui_exec.py`

**Interfaces:**
- Consumes: `tracking.debug` TOP (background).
- Produces: `tracks` Table DAT (`id, sx, sy, ex, ey, ip`) synced to `td/data/tracks.tsv`; `edit` toggle param.

- [ ] **Step 1: Build panel + drag handles**

Container COMP, background = Select TOP (`tracking/debug`). Per light (8): two handle COMPs (start/end) draggable via Panel CHOP; line drawn between (Line MAT or overlay SOP→TOP).

- [ ] **Step 2: TSV sync**

Table DAT `tracks` with file=`../data/tracks.tsv`, sync on write. `ui_exec.py`: on handle drop (debounced 0.5s), write row; on init, load TSV → place handles. IP column editable via a table page. `edit` toggle locks handles when off.

- [ ] **Step 3: Manual verify + commit**

Drag a handle, confirm TSV updates and survives project reload. Commit `feat(td): trackUI — drag-handle track editor with TSV sync`.

---

