### Task 1: TD project skeleton + Embody externalization

**Files:**
- Create: `td/theWoods.toe`
- Create: `td/externalizations.tsv`
- Create: `td/data/tracks.tsv`, `td/data/cameras.tsv`
- Create: `td/README.md`

**Interfaces:**
- Produces: project root `/theWoods` in the .toe; `project1/` folder convention for externalized COMPs; empty TSVs with headers.

- [ ] **Step 1: Create project + dirs**

```bash
mkdir -p td/data td/project1
printf 'id\tsx\tsy\tex\tey\tip\n' > td/data/tracks.tsv
printf 'id\tenabled\ttx\tty\ttz\trx\try\trz\tscale\n' > td/data/cameras.tsv
```

- [ ] **Step 2: Create the .toe in TD**

Open TouchDesigner, new project at `td/theWoods.toe`. Set cook rate 60fps (project settings). Create base COMPs named `depthIn`, `tracking`, `trackUI`, `control`, `network` at root.

- [ ] **Step 3: Externalize each COMP**

Per Embody workflow: set each COMP's `externaltox` to `project1/<name>.tox`, enable "Save Backup of External" off, add rows to `td/externalizations.tsv`. Save and commit.

- [ ] **Step 4: Commit**

```bash
git add td/
git commit -m "feat(td): project skeleton with externalized COMPs"
```

---

