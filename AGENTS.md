# AGENTS.md — theWoods

Control software for **"The Woods"**, an interactive light installation by Jesse Garrison.
Computer-vision tracked targets drive motorized lights over OSC/serial to Arduino/ESP8266 nodes.

## The piece

Gallery installation for small groups: a knee-high forest of sticks (gathered near the
artist's childhood home in SW Ohio) planted in the floor with a winding path. Motorized
sliders with LEDs on the carriages are embedded in the forest. An IR camera (PS3 Eye)
tracks viewers; lights follow them, dimming/brightening with proximity. Because the
sticks sit closer to the lights than the viewers do, the cast shadows loom large on
walls and ceiling — the viewer towers over the physical trees but is dwarfed by the
shadow world. A composer is building a reactive ambient soundscape (winter forest,
wind, spoken text "carried on the wind") driven by light movement — likely routed via
the Max patches.

Design intent that matters for the code: the lights should feel like they're *guiding*
viewers along the path, not chasing them mechanically — smoothing, influence ramp
up/down, dying state on `Target`, and the `WoodsState` modes (IDLE/QUIET/NIGHT/DARK)
exist to keep the behavior atmospheric rather than literal.

## Repo layout

| Path | What it is |
|------|-----------|
| `td/` | **Current** TouchDesigner control app — the port of forestControl's brains; see `td/README.md`. |
| `forestControl/` | openFrameworks app — CV tracking, light logic, OSC I/O. The legacy live version (kept until `td/` is proven in gallery). |
| `src/` | Older copy of the same app at repo root (pre-PS3Eye, no EtcLight/modes). Mostly superseded by `forestControl/src`. |
| `max/` | Max/MSP patches: `forestCtrl_v*.maxpat` (master control, latest = v5), `oscLightRouter_v*.maxpat` (OSC→node routing), `asciiProc.js`, serial/arduino comm patches. |
| `forestLight/` | Arduino firmware — serial-controlled stepper + dimmable light (AccelStepper). |
| `forestLight_wifi/`, `forestLight_wifi_v2/` | ESP8266 firmware — same idea over WiFi/UDP. **v2 is newest**; it speaks OSC (see `docs/superpowers/specs/2026-09-15-td-port-design.md`). |
| `forestLight_multiLight/` | Firmware variant driving multiple lights; `retired.ino` kept for reference. |
| `build/` | SketchUp (`.skp`) mechanical/hardware models: rails, eye housing, mini house, USB panel. |
| `woodsMechanicsDiagram.fzz` | Fritzing wiring diagram. |
| `b_side/`, `publicity/` | Artwork, posters, design files. |
| `bin/` | Built app + `data/` (runtime XML settings live here). |

## Stack

- **TouchDesigner** (the port — see `td/README.md` for build steps, requires 2023.10k+/2025 for POPs).
- **openFrameworks 0.9.8** (OS X, Xcode project + OF Makefiles). `OF_ROOT` expected at `../../..` relative to project.
- Addons (`addons.make`): `ofxCv`, `ofxGui`, `ofxOsc` — plus `ofxXmlSettings`, `ofxPS3EyeGrabber`, `ofxSyphon` in `forestControl`.
- **Max/MSP** patches for show control and OSC routing.
- **Arduino / ESP8266** firmware (AccelStepper, ESP8266WiFi, CNMAT OSC lib).

## Architecture (the port)

```
depth cams → depthIn (merge/clip/ortho) → overhead TOP
           → tracking (threshold + Blob Track + Target logic) → targets DAT
trackUI (drag endpoints) → tracks.tsv → tracks DAT
           → control (WoodsState, Light logic) → lights DAT
           → network → OSC unicast to nodes / mirror to Max + Unreal
           <─ node status (OSC) back
```

The legacy OF data flow (kept for reference):

```
camera → CvManager (ofxCv bg-subtract + ContourFinder, labeled blobs)
       → Target[] (smoothed positions, influence ramp-up/down, dying state)
       → Light[]  (each has a start→end track; moves toward nearest target,
                   intensity ∝ proximity; reports via OSC)
       → OscHandler → Max router → wifi/serial nodes (stepper + LED)
```

### OSC protocol

The **wire protocol** (addresses, arg types, ports) for the TD port is documented in
`docs/superpowers/specs/2026-09-15-td-port-design.md` — the OSC contract section is
the authoritative reference for `td/network` COMP and the `forestLight_wifi_v2` firmware.

Legacy (OF `OscHandler.hpp`) values, superseded by the TD port:

- App listens on **8888**, sends to **9999**.
- Outgoing: `/<id>/intensity <float>`, `/<id>/location <float>` (0–1 along track), `/ping`.
- Incoming: `/light/<n>/minTrigger`, `/light/<n>/maxTrigger` (limit-switch hits from nodes).
- Max patches translate these into per-node commands; node IPs are hardcoded `192.168.0.10x` (SSID "The Woods").

### Node firmware command set (v2, OSC over UDP)

`/light/<n>/position` float · `/light/<n>/intensity` float · `/light/<n>/identify|calibrate|zero|stop` · `/light/<n>/move` int. Nodes report `/light/<n>/minTrigger|maxTrigger` and `/light/<n>/maxPos` back. See the design spec for the full map.

## Conventions & gotchas

- **`td/` is the new canonical control app.** It is the port of `forestControl`'s brains to TouchDesigner. `forestControl/` remains until `td/` is proven live in the gallery — check which you're editing. The wire protocol for `td/` and the nodes is the design spec's OSC contract.
- `forestControl/` is canonical within OF-land. `src/` at root is an older snapshot — check which you're editing. The Xcode project `forestControl.xcodeproj` builds `forestControl/src`.
- Light/target counts are 8 (`#define NUM_LIGHTS 8` / `NUM_TARGETS 8` in `forestControl/src/CvManager.hpp`; matched by TD `tracks.tsv` / `cameras.tsv`).
- Per-light max-distance GUI sliders are hardcoded per-index in `ofApp::update()` — adding a light means adding a slider block.
- Persisted layout (OF): `lightSettings.xml` (light track endpoints, `s`/`l` keys), `settings.xml` (CV gui params). Loaded from `bin/data`. In the TD port, layout is `td/data/tracks.tsv` + `td/data/cameras.tsv`.
- `WoodsState` enum (NORMAL/IDLE/QUIET/NIGHT/DARK) in `forestControl/src/ofApp.h` — "quiet mode" was the last feature added.
- `EtcLight` = non-motorized DMX-ish light that only reports intensity over OSC.
- Known rough edges (from code comments): possible mem-leak note on `Target` reassignment, OSC receive in `OscHandler` was mid-refactor to `ofSendMessage`.
- The TD port has real tests (`td/tests/`, pytest). The OF app has none. Verify the port with `uv run --with pytest pytest td/tests/ -v`.

## Building

- TouchDesigner: open `td/theWoods.toe` (externalized COMPs in `td/project1/`). Requires TD 2023.10k+ / 2025 for POPs. See `td/README.md`.
- openFrameworks: open `forestControl.xcodeproj` (or `make` in `forestControl/` with `OF_ROOT` set). Requires OF 0.9.8 + the addons above.
- Firmware: Arduino IDE / PlatformIO; ESP8266 variants need the ESP8266 board package + CNMAT OSC library.
- Max: patches run standalone; `forestCtrl_v5.maxpat` is the current show patch.
