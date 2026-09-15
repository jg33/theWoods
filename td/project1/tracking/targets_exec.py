# me - this DAT
# scriptOp - the Script CHOP operator which is cooking

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


def onCook(scriptOp):
    targets, idle_timer = _get_targets(scriptOp)

    # Blob Track CHOP input channels: blobid, tx, ty (one sample per blob).
    inputs = scriptOp.inputs
    seen_labels = set()
    if inputs and target_logic is not None:
        inp = inputs[0]
        chan_names = [c.name for c in inp.chans()]
        blobid = inp["blobid"] if "blobid" in chan_names else None
        tx = inp["tx"] if "tx" in chan_names else None
        ty = inp["ty"] if "ty" in chan_names else None

        if blobid is not None and tx is not None and ty is not None:
            for i in range(inp.numSamples):
                label = int(blobid[i])
                x = float(tx[i])
                y = float(ty[i])
                seen_labels.add(label)

                if label not in targets:
                    targets[label] = {
                        "current": [x, y],
                        "influence": 0.0001,
                        "quiet_timer": 0,
                        "dying": False,
                    }

                targets[label] = target_logic.update_target(
                    targets[label], x, y, True
                )

    # Update unseen targets; collect labels ready to die.
    to_remove = []
    for label, t in targets.items():
        if label not in seen_labels:
            t = target_logic.update_target(t, t["current"][0], t["current"][1], False)
            targets[label] = t
        if t.get("ready_to_die"):
            to_remove.append(label)

    for label in to_remove:
        del targets[label]

    # Idle logic
    if len(seen_labels) == 0:
        idle_timer += 1
    else:
        if idle_timer > IDLE_TIMEOUT:
            pass  # leaving idle
        idle_timer = 0

    bIsIdle = 1 if idle_timer > IDLE_TIMEOUT else 0
    _set_targets(scriptOp, targets, idle_timer)

    # Build output
    scriptOp.clear()
    scriptOp.rate = me.time.rate if hasattr(me, "time") else 60
    scriptOp.numSamples = 1
    scriptOp.appendChan("bIsIdle")[0] = bIsIdle

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
