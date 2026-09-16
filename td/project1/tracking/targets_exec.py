# me - this DAT
# scriptOp - the Script CHOP operator which is cooking

import zlib

IDLE_TIMEOUT = 500

# Import target logic from the parallel 'target_logic' textDAT inside this COMP.
# In TouchDesigner: mod finds sibling DATs by name when the script lives in a COMP.
if "target_logic" not in globals():
    try:
        target_logic = mod("target_logic")
    except Exception:
        target_logic = None


def onSetupParameters(scriptOp):
    return


def onPulse(par):
    return


def _get_targets(scriptOp):
    # Persistent state stored on the Script CHOP node.
    targets = scriptOp.fetch("targets", {})
    idle_timer = scriptOp.fetch("idleTimer", 0)
    return targets, idle_timer


def _set_targets(scriptOp, targets, idle_timer):
    scriptOp.store("targets", targets)
    scriptOp.store("idleTimer", idle_timer)


def _parse_blob_tracks(inp, targets, target_logic_mod):
    # Real Blob Track CHOP emits single-sample channels named per track:
    #   blob1:tx, blob1:ty, blob1:w, blob1:h, blob1:age, ...
    # Each prefix (e.g. 'blob1') is one tracked blob. Return seen label ids and
    # updated targets; logs an error if no tx/ty pairs found.
    seen_labels = set()
    if inp is None or target_logic_mod is None:
        return seen_labels, targets

    chan_names = [c.name for c in inp.chans()]
    tx_names = [n for n in chan_names if n.endswith(":tx")]
    prefixes = sorted(set(n[:-3] for n in tx_names))

    if not prefixes:
        # No recognizable blob channels — this should be noisy, not silent.
        return None, targets

    for prefix in prefixes:
        tx_name = prefix + ":tx"
        ty_name = prefix + ":ty"
        if ty_name not in chan_names:
            continue

        tx_chan = inp[tx_name]
        ty_chan = inp[ty_name]
        # Per-track channels are single-sample in the real Blob Track CHOP.
        if tx_chan.numSamples < 1 or ty_chan.numSamples < 1:
            continue

        # Derive a stable integer label from the prefix. Blob Track prefixes
        # are typically 'blob1', 'blob2', ... but we fall back to a hash if the
        # numeric suffix is missing.
        suffix = prefix[len("blob"):] if prefix.startswith("blob") else ""
        try:
            label = int(suffix)
        except ValueError:
            label = zlib.crc32(prefix.encode()) & 0x7FFFFFFF

        x = float(tx_chan[0])
        y = float(ty_chan[0])
        seen_labels.add(label)

        if label not in targets:
            targets[label] = {
                "current": [x, y],
                "influence": 0.0001,
                "quiet_timer": 0,
                "dying": False,
            }

        targets[label] = target_logic_mod.update_target(targets[label], x, y, True)

    return seen_labels, targets


def onCook(scriptOp):
    targets, idle_timer = _get_targets(scriptOp)

    inputs = scriptOp.inputs
    inp = inputs[0] if inputs else None
    seen_labels, targets = _parse_blob_tracks(inp, targets, target_logic)

    # Update unseen targets; collect labels ready to die.
    # Guard: parse failure (seen_labels is None) must not crash the loop; the
    # error channel path below will surface the failure.
    to_remove = []
    for label, t in targets.items():
        if seen_labels is None or label not in seen_labels:
            t = target_logic.update_target(t, t["current"][0], t["current"][1], False)
            targets[label] = t
        if t.get("ready_to_die"):
            to_remove.append(label)

    for label in to_remove:
        del targets[label]

    # Idle logic
    # ponytail: parse failure resets idle_timer (error != idle); if we want a
    # miswired input to eventually trigger idle, gate this on `seen_labels is not None`.
    if seen_labels is not None and len(seen_labels) == 0:
        idle_timer += 1
    else:
        idle_timer = 0

    bIsIdle = 1 if idle_timer > IDLE_TIMEOUT else 0
    _set_targets(scriptOp, targets, idle_timer)

    # Build output
    scriptOp.clear()
    scriptOp.rate = me.time.rate if hasattr(me, "time") else 60
    scriptOp.numSamples = 1
    scriptOp.appendChan("bIsIdle")[0] = bIsIdle
    # Loud failure path: if the input had no recognizable blob channels,
    # emit an error channel and log it so the operator does not die silently.
    if seen_labels is None:
        scriptOp.appendChan("error")[0] = 1
        if hasattr(ui, "status"):
            ui.status = "targets_exec: no blob:tx/blob:ty channels found"
    else:
        scriptOp.appendChan("error")[0] = 0

    # Update targets Table DAT: label, x, y, influence, quiet, dying
    targets_dat = op("../targets") if op else None
    if targets_dat is not None:
        targets_dat.setSize(1 + len(targets), 6)
        targets_dat[0, 0] = "label"
        targets_dat[0, 1] = "x"
        targets_dat[0, 2] = "y"
        targets_dat[0, 3] = "influence"
        targets_dat[0, 4] = "quiet"
        targets_dat[0, 5] = "dying"
        for row, (label, t) in enumerate(sorted(targets.items()), start=1):
            targets_dat[row, 0] = str(label)
            targets_dat[row, 1] = f"{t['current'][0]:.4f}"
            targets_dat[row, 2] = f"{t['current'][1]:.4f}"
            targets_dat[row, 3] = f"{t['influence']:.4f}"
            targets_dat[row, 4] = "1" if t["quiet"] else "0"
            targets_dat[row, 5] = "1" if t["dying"] else "0"
    return
