# me - this DAT
# scriptOp - the Script CHOP/Script DAT/Panel CHOP operator being cooked

import os

# Import ui logic from the sibling `ui_logic` textDAT inside this COMP.
# In TouchDesigner: mod finds sibling DATs by name when the script lives in a COMP.
if "ui_logic" not in globals():
    try:
        ui_logic = mod("ui_logic")
    except Exception:
        ui_logic = None


_TRACKS_PATH = "../data/tracks.tsv"
_NUM_LIGHTS = 8


def onSetupParameters(scriptOp):
    # Toggle: when off, handles are locked / not draggable.
    scriptOp.appendParToggle("Edit", label="Edit Tracks")
    return


def _get_state(scriptOp):
    tracks = scriptOp.fetch("tracks", None)
    debouncer = scriptOp.fetch("debouncer", None)
    return tracks, debouncer


def _set_state(scriptOp, tracks, debouncer):
    scriptOp.store("tracks", tracks)
    scriptOp.store("debouncer", debouncer)


def _ensure_state(scriptOp):
    tracks, debouncer = _get_state(scriptOp)
    if tracks is None:
        tracks = ui_logic.load_tracks(_resolve_path(scriptOp), num_lights=_NUM_LIGHTS)
        _write_tracks_dat(scriptOp, tracks)
    if debouncer is None:
        debouncer = ui_logic.Debouncer()
    _set_state(scriptOp, tracks, debouncer)
    return tracks, debouncer


def _resolve_path(scriptOp):
    # If a scriptOp gives us a file par path, prefer it; otherwise the default sibling path.
    if os.path.isabs(_TRACKS_PATH):
        return _TRACKS_PATH
    return os.path.join(project.folder, _TRACKS_PATH)


def _write_tracks_dat(scriptOp, tracks):
    dat = op("../tracks") if op else None
    if dat is None:
        return
    text = ui_logic.tracks_to_dat_text(tracks)
    dat.text = text


def _write_tracks_tsv(scriptOp, tracks):
    path = _resolve_path(scriptOp)
    ui_logic.save_tracks(path, tracks)


def onCook(scriptOp):
    if ui_logic is None:
        return

    _ensure_state(scriptOp)

    # Panel CHOP cooks every frame; we use it to run the debouncer check.
    tracks, debouncer = _get_state(scriptOp)

    # If edit is off, ignore drag input entirely (the handles can still render but don't move).
    if not bool(scriptOp.par.Edit):
        return

    # TD Panel CHOP gives us u/v or x/y channels for each panel drag handle.
    # We expect one panel with 16 channels: s0_x, s0_y, e0_x, e0_y, ... e7_y.
    inp = scriptOp.inputs[0] if scriptOp.inputs else None
    if inp is not None:
        handle_changed = _apply_panel_input(tracks, inp)
        if handle_changed:
            debouncer.ping()
            _set_state(scriptOp, tracks, debouncer)
            _write_tracks_dat(scriptOp, tracks)

    # Debounced write to TSV after drag ends (0.5s after last change).
    if debouncer.check():
        _write_tracks_tsv(scriptOp, tracks)
        _set_state(scriptOp, tracks, ui_logic.Debouncer())

    return


def _apply_panel_input(tracks, panel_chop):
    """Read panel chop channels and update matching track endpoints."""
    changed = False
    chan_names = [c.name for c in panel_chop.chans()]

    for light_id in range(_NUM_LIGHTS):
        sx_name = f"s{light_id}x"
        sy_name = f"s{light_id}y"
        ex_name = f"e{light_id}x"
        ey_name = f"e{light_id}y"

        if sx_name in chan_names and sy_name in chan_names:
            sx = float(panel_chop[sx_name][0])
            sy = float(panel_chop[sy_name][0])
            track = next((t for t in tracks if t["id"] == light_id), None)
            if track is not None and track["start"] != [sx, sy]:
                track["start"] = [sx, sy]
                changed = True

        if ex_name in chan_names and ey_name in chan_names:
            ex = float(panel_chop[ex_name][0])
            ey = float(panel_chop[ey_name][0])
            track = next((t for t in tracks if t["id"] == light_id), None)
            if track is not None and track["end"] != [ex, ey]:
                track["end"] = [ex, ey]
                changed = True

    return changed
