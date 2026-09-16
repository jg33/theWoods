# me - this DAT
# scriptOp - the Script CHOP/Script DAT operator which is cooking

import random

# Import light logic from the sibling `light_logic` textDAT inside this COMP.
# In TouchDesigner: mod finds sibling DATs by name when the script lives in a COMP.
if "light_logic" not in globals():
    try:
        light_logic = mod("light_logic")
    except Exception:
        light_logic = None


def onSetupParameters(scriptOp):
    # Global state controls
    scriptOp.appendParToggle("Manualoverride", label="Manual Override")
    scriptOp.appendParFloat("Manualstate", label="Manual State")
    scriptOp.appendParToggle("Bisidle", label="Is Idle")

    # Per-light Max Distance parameters (mirrors the OF GUI sliders).
    for i in range(8):
        page = scriptOp.appendParPage(f"Light{i}")
        page.appendFloat(f"Maxdistance{i}", label="Max Distance", defaultValue=300.0)

    # Idle highlight timing
    scriptOp.appendParFloat("Idlehighlightmin", label="Idle Highlight Min", defaultValue=2.0)
    scriptOp.appendParFloat("Idlehighlightmax", label="Idle Highlight Max", defaultValue=10.0)
    return


def onPulse(par):
    return


def _parse_targets(targets_dat):
    targets = []
    if targets_dat is None:
        return targets
    nrows = targets_dat.numRows
    if nrows < 2:
        return targets
    for row in range(1, nrows):
        try:
            x = float(targets_dat[row, 1])
            y = float(targets_dat[row, 2])
            influence = float(targets_dat[row, 3])
            quiet = int(targets_dat[row, 4]) == 1
            dying = int(targets_dat[row, 5]) == 1
            targets.append({
                "current": [x, y],
                "influence": influence,
                "quiet": quiet,
                "dying": dying,
            })
        except (ValueError, IndexError):
            continue
    return targets


def _parse_tracks(tracks_dat):
    tracks = []
    if tracks_dat is None:
        return tracks
    nrows = tracks_dat.numRows
    if nrows < 2:
        return tracks
    for row in range(1, nrows):
        try:
            id_ = int(tracks_dat[row, 0])
            sx = float(tracks_dat[row, 1])
            sy = float(tracks_dat[row, 2])
            ex = float(tracks_dat[row, 3])
            ey = float(tracks_dat[row, 4])
            ip = str(tracks_dat[row, 5])
            tracks.append({"id": id_, "start": [sx, sy], "end": [ex, ey], "ip": ip})
        except (ValueError, IndexError):
            continue
    return tracks


def _get_lights(scriptOp):
    return scriptOp.fetch("lights", [])


def _set_lights(scriptOp, lights):
    scriptOp.store("lights", lights)


def _update_idle_highlight(l, elapsed, min_time, max_time, lights_in_idle):
    # If no light is currently highlighted in IDLE, pick one.
    if l["bIsIdleHighlight"]:
        if elapsed > l["endHighlightTime"]:
            l["bIsIdleHighlight"] = False
    elif not lights_in_idle:
        # Only the first eligible light in the loop will win this call.
        l["bIsIdleHighlight"] = True
        l["endHighlightTime"] = elapsed + random.uniform(min_time, max_time)
        return True
    return l["bIsIdleHighlight"]


def onCook(scriptOp):
    # Light logic module is required.
    if light_logic is None:
        scriptOp.clear()
        return

    # Script CHOP inlets accept only CHOP-family inputs, so the targets/tracks
    # Table DATs are referenced by path instead of being wired in as inputs.
    targets_dat = op("../tracking/targets") if op else None
    tracks_dat = op("../trackUI/tracks") if op else None

    targets = _parse_targets(targets_dat)
    tracks = _parse_tracks(tracks_dat)

    # State machine
    manual_override = bool(scriptOp.par.Manualoverride) if hasattr(scriptOp.par, "Manualoverride") else False
    manual_state = float(scriptOp.par.Manualstate) if hasattr(scriptOp.par, "Manualstate") else None
    b_is_idle = bool(scriptOp.par.Bisidle) if hasattr(scriptOp.par, "Bisidle") else False
    state = light_logic.woods_state(b_is_idle, targets, manual_state if manual_override else None)

    # Fetch or initialize light state
    lights = _get_lights(scriptOp)
    if not lights:
        for tr in tracks:
            max_d = getattr(
                scriptOp.par,
                f"Maxdistance{tr['id']}",
                light_logic.DEFAULT_MAX_DISTANCE,
            )
            lights.append(light_logic.make_light(tr["id"], tr["start"], tr["end"], max_d))

    # Ensure lights and tracks stay in sync (new tracks or new light count)
    if len(lights) != len(tracks):
        lights = []
        for tr in tracks:
            max_d = getattr(
                scriptOp.par,
                f"Maxdistance{tr['id']}",
                light_logic.DEFAULT_MAX_DISTANCE,
            )
            lights.append(light_logic.make_light(tr["id"], tr["start"], tr["end"], max_d))

    # Update per-light maxDistance from parameters, keyed by light id so
    # non-contiguous track IDs still map to the right parameter.
    id_to_track = {tr["id"]: tr for tr in tracks}
    for l in lights:
        track = id_to_track.get(l["id"])
        if track is not None:
            par = getattr(scriptOp.par, f"Maxdistance{l['id']}", None)
            if par is not None:
                l["maxDistance"] = float(par)

    # t = absolute time (seconds) for the noise function; elapsed = same here because
    # we use wall-clock time for both noise phase and highlight timeout comparison.
    t = scriptOp.time.seconds if hasattr(scriptOp, "time") else 0.0
    elapsed = scriptOp.time.seconds if hasattr(scriptOp, "time") else 0.0
    min_time = float(scriptOp.par.Idlehighlightmin) if hasattr(scriptOp.par, "Idlehighlightmin") else 2.0
    max_time = float(scriptOp.par.Idlehighlightmax) if hasattr(scriptOp.par, "Idlehighlightmax") else 10.0

    # IDLE: make sure at least one light is highlighted
    if state == 1:
        lights_in_idle = any(l["bIsIdleHighlight"] for l in lights)
        for l in lights:
            became = _update_idle_highlight(l, elapsed, min_time, max_time, lights_in_idle)
            if became:
                lights_in_idle = True

    # Update all lights
    for l in lights:
        l = light_logic.update_light(l, targets, state, t=t, elapsed=elapsed)

    _set_lights(scriptOp, lights)

    # Build output channels
    scriptOp.clear()
    scriptOp.rate = me.time.rate if hasattr(me, "time") else 60
    scriptOp.numSamples = 1
    scriptOp.appendChan("state")[0] = state

    # Build lights Table DAT
    lights_dat = op("../lights") if op else None
    if lights_dat is not None:
        lights_dat.setSize(1 + len(lights), 3)
        lights_dat[0, 0] = "id"
        lights_dat[0, 1] = "locationPercent"
        lights_dat[0, 2] = "intensity"
        for row, l in enumerate(lights, start=1):
            lights_dat[row, 0] = str(l["id"])
            lights_dat[row, 1] = f"{l['locationPercent']:.6f}"
            lights_dat[row, 2] = f"{l['intensity']:.6f}"

    return
