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

1. `inOverhead` an **In TOP** (landing for the `depthIn.outOverhead` wire): luminance is viewers as bright blobs on dark bg.
2. `inOverhead` output → `threshold1` **Threshold TOP**:
   - Threshold `0.5`
   - Pre-shrink `0`
   - Pre-dilate `1`
   - Blur `1` or small radius
   - Output RGBA so blobs remain bright
3. `threshold1` output → `blobtrack1` **Blob Track CHOP**:
   - Input: `threshold1` TOP output (RGBA, bright blobs on dark background).
   - The CHOP will find blobs and output per-blob channels with a *per-track prefix*:
     `blob1:tx`, `blob1:ty`, `blob1:w`, `blob1:h`, `blob1:age`,
     `blob2:tx`, `blob2:ty`, ...
   - `targets_exec.py` reads those per-track `*:tx` and `*:ty` channels and uses the prefix (`blob1`, `blob2`, ...) as the target label.
   - Set **Max Blobs** to `8` (matches `NUM_LIGHTS`/`NUM_TARGETS`).
   - Set **Max Blob Movement** to `100` pixels.
   - Set **Lost Blob Timeout (s)** to `1` (≈ 1000 ms, tune per show).
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

## control COMP

Inside `/project1/control` (a Base COMP), build this network to replicate the OF `Light`/`WoodsState` behavior:

1. Add a **Script CHOP** named `controlcook`:
   - Parameter: **Callbacks DAT** → the sibling Text DAT `control_exec.py`
   - Parameter: **Cook Type** → `Python`
   - Note: `controlcook` reads the targets and tracks Table DATs directly by path (`../tracking/targets`, `../trackUI/tracks`) inside `control_exec.py` — do **not** add COMP inputs or wire DATs into the CHOP (CHOP inlets accept CHOP family only).
2. Inside `/project1/control`, add a **Text DAT** named `light_logic` and point its `file` parameter to `td/project1/control/light_logic.py`, **Sync to File** On.
3. Add another **Text DAT** named `control_exec` and point its `file` parameter to `td/project1/control/control_exec.py`, **Sync to File** On. In the `controlcook` Script CHOP **Callbacks DAT** field, set it to `control_exec`.
4. Inside `/project1/control`, add a **Table DAT** named `lights` (columns will be set at runtime: `id, locationPercent, intensity`).
5. `controlcook` → `null1` **Null CHOP** to expose the `state` channel.
6. Add a **Noise CHOP** named `idlenoise` (or use `absTime.seconds` in a Math CHOP) and reference it in `control_exec.py` if you want real `ofNoise(t+id*6.66)`-style noise. The provided `light_logic.py` has a deterministic sine fallback, but in TD a Noise CHOP is closer to OF behavior.
7. IDLE needs a driver: in the `/project1/tracking` COMP, `targetscook` outputs the `bIsIdle` channel (see tracking step 8's Null). Bind that channel into `control` — the simplest is a **Math CHOP** `bidle` inside `/project1/control` whose input TOP/DAT is empty and whose reference expression reads `op('../tracking/null1')['bIsIdle']`, then write it to `controlcook`'s `Bisidle` parameter via an **Expression** bind (`op('../tracking/null1')['bIsIdle']`). With `Manual Override` Off, `control_exec.py` uses the automatic state machine driven by this `Bisidle` (and the all-quiet check) to reach IDLE/QUIET.
8. Externalize `/project1/control` to `td/project1/control.tox` and ensure `light_logic.py`, `control_exec.py`, and any generated Python DATs are saved as external files in `td/project1/control/`.

### Parameter defaults

- Manual Override: `Off` — when Off, the automatic state machine (bIsIdle / all-quiet) drives `state`; when On, the `Manual State` slider takes over.
- Manual State: `0` (NORMAL)
- Is Idle: `Off` (bind `../tracking/null1`'s `bIsIdle` channel here so IDLE has a driver)
- Light Max Distance (per light): `300` pixels
- Idle Highlight Min: `2` s
- Idle Highlight Max: `10` s

## trackUI COMP

Inside `/project1/trackUI` (a Base COMP), build this performable track editor:

1. Add a **Custom Parameter** page named `Edit`:
   - Toggle `Edit` (default Off). When Off, drag handles are locked.
2. Add a **Select TOP** named `background`:
   - `TOP` → `../tracking/debug`
3. Add a **Table DAT** named `tracks`:
   - `File` → `data/tracks.tsv` (relative to the `.toe`, so this resolves to `td/data/tracks.tsv`)
   - `Sync to File` → **On** (or write via script)
   - Columns: `id, sx, sy, ex, ey, ip`
4. Inside `/project1/trackUI`, add a **Text DAT** named `ui_logic` and point its `File` to `td/project1/trackUI/ui_logic.py`, **Sync to File** On.
5. Add another **Text DAT** named `ui_exec` and point its `File` to `td/project1/trackUI/ui_exec.py`, **Sync to File** On.
6. Add a **Script CHOP** named `panelcook`:
   - Parameter: **Callbacks DAT** → `ui_exec`
   - Parameter: **Cook Type** → `Python`
   - Note: a Panel CHOP has no Callbacks DAT parameter. Wire the **Panel CHOP** (built in step 7) into `panelcook`'s input; `ui_exec.py` runs its drag/debounce logic on this Script CHOP.
   - This CHOP drives the debounced TSV write and reads drag-handle position channels from its Panel CHOP input.
7. Create the 8 light track endpoints as Panel CHOP drag channels. For each light `0..7`:
   - Make two **Container COMPs** (or small Button/Panel components) as handles:
     - `start0` ... `start7` (start handles)
     - `end0` ... `end7` (end handles)
   - Each handle must output its `x`/`y` position as a channel to `panelcook`, named `s<N>x`, `s<N>y` for start and `e<N>x`, `e<N>y` for end. TouchDesigner Panel CHOPs output channels named after the panel components; use the handle COMP `name` field to match these channel names.
8. For each light, draw a connecting line between `startN` and `endN`:
   - Option A: an **Add SOP** with two points → **Geometry COMP** → **Line MAT**.
   - Option B: a **Line TOP** composite between the two handle panel positions.
9. Add an **IP** parameter page or a small **Table DAT** named `ip` so the operator can edit node IP addresses. On change, write the new value to the `ip` cell in `tracks` and trigger a TSV save.
10. On init / first cook:
    - `ui_exec.py` calls `ui_logic.load_tracks()` from `td/data/tracks.tsv` and sets `tracks` DAT text.
    - If `tracks.tsv` is empty, it falls back to 8 default tracks with IPs `192.168.0.100..107`.
11. On drag / drop:
    - `panelcook` reads the handle position channels.
    - `ui_exec.py` updates the matching track row in the `tracks` DAT immediately.
    - A `Debouncer` with a 0.5 s delay writes to `td/data/tracks.tsv` only after the user stops dragging.
12. When the `Edit` toggle is Off, `ui_exec.py` ignores panel input; handles are not draggable.
13. Externalize `/project1/trackUI` to `td/project1/trackUI.tox` and ensure `ui_logic.py` and `ui_exec.py` are saved as external files in `td/project1/trackUI/`.

### Parameter defaults

- `Edit`: Off
- Debounce write: 0.5 s
- Track default start: `[100, 100 + i * 80]`
- Track default end: `[400, 100 + i * 80]`
- Default IPs: `192.168.0.100` .. `192.168.0.107`

## network COMP

Inside `/project1/network` (a Base COMP), build the OSC I/O: outbound position/intensity to the nodes, mirrors to Max + Unreal, and inbound node status.

1. Inside `/project1/network`, add a **Text DAT** named `net_logic` and point its `File` to `td/project1/network/net_logic.py`, **Sync to File** On.
2. Add another **Text DAT** named `net_exec` and point its `File` to `td/project1/network/net_exec.py`, **Sync to File** On.
3. Add a **Script CHOP** named `sendcook`:
   - Parameter: **Callbacks DAT** → `net_exec`
   - Parameter: **Cook Type** → `Python`
   - Note: `sendcook` reads the lights and tracks Table DATs directly by path (`../control/lights`, `../trackUI/tracks`) inside `net_exec.py` — do **not** wire DATs into the CHOP inputs (CHOP inlets accept CHOP family only).
4. Add an **OSC Out DAT** named `oscOut`:
   - **Network** → `UDP`
   - `Host`/`Network` parameters are set per-light by `net_exec.py` from `tracks` IPs; per-node send port is `Nodeport` (default `9999`).
   - In `net_exec.py`, the unicast block sets `oscOut.par.address = ip` (host parameter is `address`, not `hostname`) then calls `oscOut.sendOSC(address, args)`.
5. Add a second **OSC Out DAT** named `oscOutBcast` for the mirrors + `/ping`:
   - `Host` → `255.255.255.255`, `Port` → set per-target by `net_exec.py`.
   - `net_exec.py` `_mirror()` re-sends each outgoing `/light/*` message to the Max and Unreal listen IP/ports when `mirrorMax`/`mirrorUnreal` are on. The `/ping` heartbeat (1s) also goes out this DAT.
6. `sendcook` → a **Null CHOP** named `null1` to expose the `sent` channel (debug).
7. Add an **OSC In DAT** named `oscIn`:
   - **Network** → `UDP`
   - **Port** → `Listenport` (default `8899`)
   - **Callbacks** → the sibling Text DAT `net_exec.py` (the DAT's `onReceiveOSC` callback).
   - Node reports `/light/<n>/minTrigger`, `/light/<n>/maxTrigger`, `/light/<n>/maxPos <int>` are parsed by `net_logic.parse_node_status()` and logged.
8. Add a **Table DAT** named `nodeStatus` — columns are set at runtime by `net_exec.py` (`id, status, value`); this is the inbound liveness/limit-status output.
9. Inside `/project1/network`, add the **Custom Parameters** page (declared in `onSetupParameters`): `Sendrate`, `Nodeport`, `Mirrormax`/`Mirrormaxip`/`Mirrormaxport`, `Mirrorunreal`/`Mirrorunrealip`/`Mirrorunrealport`. (The listen port is not a custom param — set `oscIn`'s Port directly on the DAT.)

Manual node controls: the same page also exposes `Light`, `Moveamount`, and pulse params `Identify`, `Calibrate`, `Zero`, `Stop`, `Move`. Select a light (`Light`), optionally set `Moveamount` for `Move`, and pulse one — `net_exec.onPulse` sends `/light/<n>/identify|calibrate|zero|stop` (or `/light/<n>/move <steps>`) to that node's IP via `oscOut`.
10. Optional 30 Hz pacing: rather than relying only on per-cook `should_send()`, you can drive `sendcook` with a **Timer CHOP** at `Sendrate` Hz; the `LightThrottle` still caps bursts regardless.
11. Externalize `/project1/network` to `td/project1/network.tox` and ensure `net_logic.py` and `net_exec.py` are saved as external files in `td/project1/network/`.

### Parameter defaults

- Send Rate: `30` Hz (ceiling)
- Node Port: `9999`
- Mirror Max: Off — IP `127.0.0.1`, port `9999`
- Mirror Unreal: Off — IP `127.0.0.1`, port `9998`

### OSC contract

| Direction | Address | Args |
|-----------|---------|------|
| TD→node | `/light/<n>/position` | float 0–1 |
| TD→node | `/light/<n>/intensity` | float 0–1 |
| TD→node | `/light/<n>/identify|calibrate|zero|stop` | — |
| TD→node | `/light/<n>/move` | int steps |
| TD→all | `/ping` | int (1s heartbeat) |
| node→TD | `/light/<n>/minTrigger|maxTrigger` | — |
| node→TD | `/light/<n>/maxPos` | int |
| TD→Max/UE | same `/light/*` messages | mirrored stream |

## depthIn COMP

`/project1/depthIn` turns camera-agnostic depth sources into a merged, calibrated point cloud and renders a top-down overhead TOP for `tracking`. Build it in this exact order.

> **Build requirement:** the merge/clip path uses TOPs that read POPs (`Merge TOP` + `Ortho Camera COMP` + `Render TOP`). Point clouds and POP TOPs need TouchDesigner **2023.10k or newer** (2025 builds also fine). Older builds won't show the `Merge`/`Render` TOP options for point clouds.

### Per-camera sub-COMP (`cam1`, `cam2`, ...)

One sub-COMP per camera in `td/data/cameras.tsv`. Each is identical; you only swap the input TOP.

1. Add a **Base COMP** named `cam1` (and `cam2`, ... one per row in the TSV).
2. Inside `/project1/depthIn/cam1` add the **camera-agnostic input TOP** (swap point). This is the only node you change per camera:
   - **No hardware yet (use now):** a **Test Pattern TOP** named `input` (e.g. *Fbm Noise* / *Ramp* / *Rainbow*).
   - **Kinect:** a **Kinect TOP** named `input` (output its depth point cloud).
   - **Orbbec:** an **Orbbec TOP** named `input` (depth point cloud output).
   - **Any other depth TOP** that emits a point cloud — name it `input`.
3. `input` → **TOP to POP** (`topTo`): converts the depth TOP into a point-cloud POP. Keep the default point budget; scale up only if the scene needs it.
4. `topTo` → **Transform POP** named `calib`. Bind each param on this POP to the matching `cam1` row in `td/data/cameras.tsv`:
   - `tx`, `ty`, `tz` ← TSV `tx,ty,tz`
   - `rx`, `ry`, `rz` ← TSV `rx,ry,rz`
   - `scale` ← TSV `scale`
   - The **`enabled`** toggle is the per-cam master. When a camera row is disabled, either disable its `calib` POP or drop the `input` TOP in the merge so its cloud isn't included.
   - Bind values via the **Expression** parameter type or a small **Execute DAT** that re-reads the TSV each frame (see `depth_logic.parse_cameras` below). `scale` maps to Transform POP's **Scale** (or set `sx/sy/sz` all to `scale`).
5. `calib` → **Null POP** named `outcloudN` → **Out POP** named `out1` (the sub-COMP's first output) so the cloud leaves the COMP. (Set the sub-COMP **Output** count to 1 and route `out1` to the first output.)

Repeat for each camera row.

### Merge + clip + render

6. Inside `/project1/depthIn`, add a **Merge POP** named `merge1` and wire each camera sub-COMP's output (`../cam1/outcloudN`, `../cam2/outcloudN`, ...) into it in TSV order. Only enabled cams get wired in (ids from `depth_logic.enabled_cameras`).
7. `merge1` → **SOP to CHOP** only if you need the raw cloud as CHOP data for debug; otherwise skip and go straight to the height clip.
8. Add a **height-band clip**: `merge1` → a **Delete POP** whose **Delete Range** (Y-range) keeps only points in `[clipMin, clipMax]` (assuming Y-up, where `y` = height above floor). The two per-point clip values `clipMin`/`clipMax` are **Custom Parameters** on `/project1/depthIn`; bind them into the Delete POP's range via an expression. (Alternatively a **Script POP** that drops points with `y < clipMin` or `y > clipMax`.) This keeps only the viewer band — points below the rails / above head height are cut.
   - `clipMin` default: `0.0` (floor).
   - `clipMax` default: `2.0` (m, ~head height; tune per gallery).
9. Add an **Ortho Camera COMP** named `camOverhead`:
   - **Projection** → **Orthographic**.
   - **Position** → a large negative-`y` height with `rx = -90` (looking straight down), e.g. `ry` aligned so `+x` = path direction, `+z` = width.
   - **Ortho Width** sized to the tracked floor area so the top-down view matches `tracking`'s pixel grid.
   - Set **Near/Far** to bracket the clip band.
10. A **Render TOP** renders geometry, not POP data directly — so put the clipped cloud inside a **Geometry COMP**: add a **Geometry COMP** named `geoCloud`, drop the clipped POP (from step 8 → step 9) into it as its input, and set the Geometry COMP's **POP** parameter to that POP. Then add the **Render TOP** named `renderO`: **Camera** → `camOverhead`, render the `geoCloud` geometry through the ortho camera.
11. `renderO` → **Null TOP** named `outOverhead`. This is the COMP's output. Wire `outOverhead` → `../tracking/inOverhead`.
12. For debug: add a **Null POP** named `outCloud` fed from the merged/clipped cloud (before render) so you can inspect the raw points in the POP viewer.
13. Externalize `/project1/depthIn` to `td/project1/depthIn.tox`; add a **Text DAT** `depth_logic` pointing at `td/project1/depthIn/depth_logic.py` (Sync to File On) if you use the parser from an Execute DAT.

### Python helpers

`td/project1/depthIn/depth_logic.py` (tested in `td/tests/test_depthin.py`) exposes:
- `parse_cameras(tsv_text)` → dict keyed by camera id of `{enabled, tx, ty, tz, rx, ry, rz, scale}`. Skips blank/`#` lines, short/bad rows, malformed numbers.
- `enabled_cameras(cams)` → the ids of enabled rows, the ones actually merged.
- `in_height_band(y, clipMin, clipMax)` → inclusive height-band predicate; `None` bound = unclipped side.

`td/project1/depthIn/cam_exec.py` (used as the **Script CHOP callbacks** / enable driver in TD) exposes `load_cameras(tsv_path)` → same dict as `parse_cameras`, or `{}` if the TSV path is unreadable.

Use these from a **Script CHOP** / **Execute DAT** (`cam_exec`) to bind the Transform POP params / enable toggles and read `clipMin`/`clipMax`; the geometry/clip math stays in TD's Transform/Merge/Ortho — do not reimplement it here.

### Parameter defaults

- `clipMin`: `0.0`, `clipMax`: `2.0` (m)
- Per-cam Transform `scale`: `1.0`
- Ortho Width / height: match `tracking` floor grid; `rx` = `-90` for top-down

### Verify without hardware

1. Use **Test Pattern** tops as the `input` on all cams (step 2 above) so every sub-COMP emits a cloud.
2. Confirm `/project1/depthIn/renderO` shows a filled overhead image and `outOverhead` is non-black.
3. Confirm `outCloud` (POP viewer) shows the merged points from all active cams.
4. `tracking` should now receive `inOverhead` and, after its own threshold/blob path, emit target rows.
5. With one cam in the TSV set `enabled=0`, the merge must drop it (no cloud contribution) — validates the per-cam enable wiring.

## Integration checklist

Cross-COMP wiring — do these once when the `.toe` is first assembled. Each step is
an operator-to-operator connection at the `/theWoods` root (or the path noted).

1. `depthIn.outOverhead` → `tracking.inOverhead`. The overhead TOP (merged, clipped,
   ortho-rendered point cloud) is `tracking`'s only input.
2. `tracking.targets` (Table DAT, `label, x, y, influence, quiet, dying`) → read by
   `control`'s `control_exec.py` via `op("../tracking/targets")` — no wire needed.
3. `trackUI.tracks` (Table DAT) read by path — no wires needed (Table DATs can't feed
   Script CHOP inputs):
   - `control`'s `control_exec.py` via `op("../trackUI/tracks")`.
   - `network`'s `net_exec.py` via `op("../trackUI/tracks")`.
4. `control.lights` (Table DAT, `id, locationPercent, intensity`) → read by
   `network`'s `net_exec.py` via `op("../control/lights")` — no wire needed.
5. `network.oscIn` Port = `8899` (the UDP port nodes report status to — firmware defaultReportPort). Set on the DAT
   directly; it is not a custom parameter.

### End-to-end verification (stub camera, no hardware)

1. **Stub camera:** in `depthIn`, put a **Test Pattern TOP** as the `input` on every
   `camN` sub-COMP (Fbm Noise / Ramp / Rainbow) so each emits a cloud. `outOverhead`
   renders non-black.
2. **Tracking:** confirm `tracking` emits rows in `targets` (threshold → Blob Track →
   `targetscook`). Blobs on the test pattern should appear as target rows.
3. **Control:** confirm `control.lights` populates with `locationPercent`/`intensity`
   per light from the `tracks` + `targets` inputs.
4. **Network (out):** with `sendcook` cooking, run a python-osc listener on the node
   port and confirm `/light/<n>/position|intensity` messages arrive:

   ```bash
   uv run --with python-osc python -c \
     "from pythonosc.dispatcher import Dispatcher; from pythonosc.osc_server import BlockingOSCUDPServer
d=Dispatcher(); d.map('*', lambda a,*args: print(a, args)); BlockingOSCUDPServer(('127.0.0.1', 9999), d).serve_forever()"
   ```

   (Run inside `td/` so `uv` resolves; the listener prints every OSC message. Point an
   `oscOut` unicast at `127.0.0.1:9999` if tracks lack node IPs.)

5. **Network (in):** send a fake node status to `network.oscIn`:

   ```bash
   uv run --with python-osc python -c \
     "from pythonosc.udp_client import SimpleUDPClient; c=SimpleUDPClient('127.0.0.1', 8899); c.send_message('/light/0/maxTrigger', [])"
   ```

   Confirm `network.nodeStatus` gains a `(id, status, value)` row.

## Open

Open `td/theWoods.toe` in TouchDesigner. Externalized COMPs restore from `td/project1/`.
