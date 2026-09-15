# theWoods — TouchDesigner Port

TD control app for the installation.

## Layout

```
td/
├── theWoods.toe        # project file (create in TD)
├── externalizations.tsv # Embody externalization ledger
├── project1/           # externalized COMPs
│   ├── depthIn.tox
│   ├── tracking.tox
│   ├── trackUI.tox
│   ├── control.tox
│   └── network.tox
└── data/
    ├── tracks.tsv      # light track endpoints
    └── cameras.tsv     # camera calibration
```

## Manual setup steps (TouchDesigner GUI)

1. Open TouchDesigner.
2. File → New Project → Save As `td/theWoods.toe`.
3. File → Project Settings → FPS: set **60**.
4. In the root (`/theWoods`), create five **Base COMPs**:
   - `depthIn`
   - `tracking`
   - `trackUI`
   - `control`
   - `network`
5. Externalize each COMP to `td/project1/<name>.tox`:
   - Select the COMP.
   - In the parameter dialog, set **External Tox** to `project1/<name>.tox` (e.g. `project1/depthIn.tox`).
   - Set **Enable External Tox** to **On**.
   - Set **Save Backup of External** to **Off**.
6. Save the project.

The `externalizations.tsv` ledger is managed by Embody as you externalize; stubs for the five COMPs can be added manually if needed before Embody is running.

## Open

Open `td/theWoods.toe` in TouchDesigner. Externalized COMPs restore from `td/project1/`.
