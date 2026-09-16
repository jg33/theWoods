# The Woods — TouchDesigner Port Design

Date: 2026-09-15
Status: Draft (awaiting review)

## Goal

Port the "brains" of The Woods from `forestControl` (openFrameworks) to TouchDesigner,
and lay groundwork for an Unreal Engine previz that sniffs the real control bus.

Motivation: TD's live-tunable parameters, native camera/depth TOPs, POPs, Blob Track
CHOP, and performable panels make the system far easier to iterate on than the OF app.

## Architecture

Five COMPs + firmware workstream. Data flows left to right; TSV files are the
source of truth for persistent layout.

```
depth cams ──> depthIn (POPs: merge, clip, ortho render) ──> overhead TOP
         ──> tracking (threshold, Blob Track, Target logic) ──> targets DAT
trackUI (drag endpoints over feed) ──> tracks.tsv ──> tracks DAT
         ──> control (WoodsState, Light logic) ──> lights DAT
         ──> network ──> OSC unicast to nodes
                     ──> OSC mirror to Max + Unreal
         <── node status (OSC) back
```

## COMPs

### 1. `depthIn` — acquisition → overhead TOP

Camera-agnostic. One sub-COMP per camera (`cam1`, `cam2`, ...) — each is a swap
point containing the camera's native TOP (Kinect/Azure/Orbbec/RealSense) or an
SDK bridge.

Pipeline per camera: depth source → TOP to POP → Transform POP (per-cam
calibration: `tx ty tz rx ry rz scale`) → Merge POP (all cams) → clip to height
band above stick height (only viewers blob, not floor/sticks) → ortho top-down
render → overhead TOP.

- Params: per-cam transform + enable, `clipMin/clipMax`, render resolution.
- Persisted calibration: `cameras.tsv` (id, enabled, tx..rz, scale).
- Outs: `outOverhead` TOP (primary), `outCloud` POP (debug/3D preview).

Requires TD build with POP family (2023.10k+/2025). If unavailable, same pipeline
as TOP position textures + GLSL — uglier but equivalent.

### 2. `tracking` — overhead TOP → Target table

Ports `CvManager` + `Target`.

- In: `inOverhead` TOP.
- Threshold TOP (params: `threshold`, `dilate`, `blur` — mirrors dilate-5/blur-10)
  → Blob Track CHOP (labeled blobs w/ persistence; replaces ContourFinder's
  1000ms persistence / 100px max jump — set as CHOP params).
- Script CHOP ports `Target` logic per label per frame:
  - `current.lerp(measured, 0.05)`
  - `influence`: +0.01/frame alive, −0.001/frame dying → `bReadyToDie` at ≤0
  - `quietTimer`: resets on move > `quietMoveThreshold` (20px); `bIsQuiet` after
    `quietTimeThreshold` (300 frames)
  - `bIsIdle` global: no blobs for `IDLE_TIMEOUT` frames (500)
- All constants exposed as COMP params.
- Outs: `targets` Table DAT (`label, x, y, influence, quiet, dying`),
  `bIsIdle` flag, `debug` TOP (thresholded feed + blob overlays for UI).

### 3. `trackUI` — performable track editor

- Panel COMP: background = `tracking` debug TOP (or `depthIn` overhead),
  overlay = two drag handles (start/end) per light track + connecting line.
- Track data: `id, sx, sy, ex, ey, ip` per row. Length/orientation derived on
  read — not stored.
- Node IPs edited in a table page of the same panel.
- Persistence: Table DAT with file sync → `tracks.tsv`. Write on change
  (debounced) + explicit save. Loaded on init. Same coordinate space as
  overhead TOP.
- "Edit" mode toggle so performers can't drag tracks mid-show.
- Out: `tracks` Table DAT (live mirror) → `control`, `network`.

### 4. `control` — the brain

Ports `Light` + `WoodsState`.

- In: `targets` DAT, `tracks` DAT.
- Script CHOP/DAT per frame per light (from `Light::update`):
  - nearest living target within `maxDistance` (per-light param → column in
    tracks.tsv or param page; replaces hardcoded GUI sliders)
  - `distInfluence = (maxD − dist)/maxD`, clamp 0–1, <0.1 → 0, × `target.influence`
  - `moveTarget.lerp(targetPos, distInfluence)`
  - `current.lerp(moveTarget, 0.001)`; `locationPercent = distFromStart/totalDist`
  - `targetIntensity = (maxD − nearDist)/maxD × influence`;
    `intensity.lerp(target, 0.01)`
- WoodsState machine (Script DAT): NORMAL / IDLE / QUIET / NIGHT / DARK.
  - IDLE: `bIsIdle` → low base intensity + per-light noise pulse + timed
    highlight (`ofNoise(t + id*6.66)` → Noise CHOP)
  - QUIET: all targets quiet → global noise-driven intensity
  - NIGHT/DARK: previously placeholders — now implementable as param pages
- Params page: all lerp rates, thresholds, timeouts, maxDistance default.
- Out: `lights` Table DAT (`id, locationPercent, intensity`) per frame.

### 5. `network` — OSC I/O

- In: `lights` DAT, `tracks` DAT (node IPs), `nodeStatus` handling.
- Out per light (on change or ≤30Hz rate limit):
  `/light/<id>/position <float 0–1>`, `/light/<id>/intensity <float 0–1>`
  via OSC DAT, unicast to each node IP.
- Mirror: identical OSC messages to Max listen port and Unreal listen port
  (param-gated: `mirrorMax`, `mirrorUnreal` toggles + IP/port). Max becomes a
  pure listener for the composer's soundscape; Unreal sniffs the same bus.
- In: OSC listen port — `/light/<n>/minTrigger`, `/light/<n>/maxTrigger`,
  node status reports → `nodeStatus` DAT → `control` (limit hits clamp
  locationPercent).
- `/ping` heartbeat → node liveness shown in `trackUI`.

## OSC address map (contract for firmware + Max + UE)

| Direction | Address | Args | Meaning |
|-----------|---------|------|---------|
| TD→node | `/light/<n>/position` | float 0–1 | target position along track |
| TD→node | `/light/<n>/intensity` | float 0–1 | LED intensity |
| TD→node | `/light/<n>/identify` | — | flash/identify (was `x`) |
| TD→node | `/light/<n>/calibrate` | — | run calibration (was `c`) |
| TD→node | `/light/<n>/zero` | — | zero position (was `r`) |
| TD→node | `/light/<n>/stop` | — | stop (was `z`) |
| TD→node | `/light/<n>/move` | int steps | relative move (was `-n`/`=n`) |
| node→TD | `/light/<n>/minTrigger` | — | min limit switch hit |
| node→TD | `/light/<n>/maxTrigger` | — | max limit switch hit |
| node→TD | `/light/<n>/maxPos` | int | report calibrated max position |
| TD→all | `/ping` | int | heartbeat (1s) |
| TD→Max/UE | same `/light/*` messages | | mirrored stream |

## Firmware workstream (forestLight_wifi_v2)

Uncomment + adapt CNMAT OSC code: parse the address map above, drive
AccelStepper + LED as today, send OSC status replies. Plain-text parser removed.
Per-node config (id, IP) stays as-is.

## Unreal previz groundwork

Deliverables in this project (UE project itself is a separate spec):
1. `network` mirror output (OSC) — done above.
2. `tracks.tsv` readable by UE (track endpoints, node ids).
3. This document's OSC address map = the message spec.

UE side (later): OSC listener → `/light/<n>/position` moves a virtual carriage
actor along a track spline; `/intensity` drives light intensity. `tracks.tsv`
spawns track geometry.

## Files

- `td/` — new .toe project + externalized COMPs (Embody for git-diffable .tox)
- `td/data/tracks.tsv`, `td/data/cameras.tsv`
- firmware: `forestLight_wifi_v2/` modified in place

## Not doing (YAGNI)

- No POP-space clustering — image-space blob track is proven and debuggable.
- No multicast — unicast + explicit mirrors; revisit if listener count grows.
- No Max routing — Max only listens.
- No changes to `src/` (old OF snapshot) or Max patches.
- `forestControl` remains until TD version is proven in the gallery.

## Open questions

- TD version on the show machine (POP support)?
- Frame-rate assumptions: OF constants are per-frame at 60fps; TD Script CHOPs
  should use time-based deltas or pin the cook rate. Decision: pin to 60fps
  and keep per-frame constants identical to OF for now.
