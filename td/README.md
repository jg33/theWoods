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

## tracking COMP

Inside `/project1/tracking` (a Base COMP), build this network to replicate the OF `CvManager`/`Target` behavior:

1. `inOverhead` Video Device In / Movie File In / other video source TOP (luminance: viewers as bright blobs on dark bg).
2. `inOverhead` output → `threshold1` **Threshold TOP**:
   - Threshold `0.5`
   - Pre-shrink `0`
   - Pre-dilate `1`
   - Blur `1` or small radius
   - Output RGBA so blobs remain bright
3. `threshold1` output → `blobtrack1` **Blob Track TOP** (NOT Blob Track CHOP; it emits `blobid`, `u`, `v`, etc. channels via a CHOP-out style TOP) and then wire the TOP's CHOP output into a **CHOP to DAT** named `blobtable`, OR use a **Blob Track CHOP** after converting to `tx`/`ty` points.

   Simpler path using a **Blob Track CHOP**:
   - Add a `noise1` or `pattern1` generating `tx`/`ty` is not needed for real blobs.
   - Better: use **Blob Track TOP** → **CHOP to DAT** `blobtable` (columns: `id`, `u`, `v`, `width`, `height`, `age`).
   - Then a **DAT to CHOP** `blobchop` selecting `id` as first column, rename `id`→`blobid`, `u`→`tx`, `v`→`ty` and feed that into `targetscook`.

   For the most direct construction, place a **Blob Track CHOP** named `blobtrack1` that expects `tx`/`ty` input. If using the Blob Track TOP path, map its CHOP channels to `tx`/`ty` before this step.
4. `blobtrack1` → `targetscook` **Script CHOP**:
   - Parameter: **Callbacks DAT** → the sibling Text DAT `targets_exec.py`
   - Parameter: **Cook Type** → `Python`
5. Inside `/project1/tracking`, add a **Text DAT** named `target_logic` and point its `file` parameter to `td/project1/tracking/target_logic.py`, **Sync to File** On.
6. Add another **Text DAT** named `targets_exec` and point its `file` parameter to `td/project1/tracking/targets_exec.py`, **Sync to File** On. In the `targetscook` Script CHOP **Callbacks DAT** field, set it to `targets_exec`.
7. Inside `/project1/tracking`, add a **Table DAT** named `targets` (columns will be set at runtime: `label, x, y, influence, quiet, dying`).
8. `targetscook` → `null1` **Null CHOP** to expose the `bIsIdle` channel.
9. For `debug` visualization: `threshold1` output → `composite1` **Composite TOP** overlaying the `targets` DAT converted via a **DAT to SOP** or simply display `threshold1` as the debug TOP. Set a **Null TOP** named `debug` from `threshold1`.
10. Externalize `/project1/tracking` to `td/project1/tracking.tox` and ensure `target_logic.py`, `targets_exec.py`, and any generated Python DATs are saved as external files in `td/project1/tracking/`.

### Parameter defaults

- Blob Track persistence: `1000` ms
- Max jump: `100` pixels
- Threshold dilate: `5`
- Threshold blur: `10`
- Idle timeout: `500` frames

## Open

Open `td/theWoods.toe` in TouchDesigner. Externalized COMPs restore from `td/project1/`.
