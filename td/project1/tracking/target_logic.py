def update_target(t, measured_x, measured_y, seen):
    # t: dict(current=[x,y], influence, quiet_timer, dying)
    # returns updated t
    if seen:
        # Snapshot previous BEFORE the lerp (mirrors OF Target::update():
        # previous = current; current.interpolate(target, 0.05)). The quiet
        # "moved" quantity is the ACTUAL frame movement (the ~5% step), not the
        # ~95% residual between measured and post-lerp current.
        prev_x, prev_y = t["current"]
        t["current"][0] += (measured_x - t["current"][0]) * 0.05
        t["current"][1] += (measured_y - t["current"][1]) * 0.05
        t["influence"] = min(1.0, t["influence"] + 0.01)
        t["dying"] = False
        moved = ((prev_x - t["current"][0]) ** 2 + (prev_y - t["current"][1]) ** 2) ** 0.5
        t["quiet_timer"] = 0 if moved > 20 else t["quiet_timer"] + 1
    else:
        t["influence"] -= 0.001
        t["dying"] = True
    # ponytail: OF latches bIsQuiet until a move breaks it; we recompute each
    # frame from quiet_timer, so a quiet target can exit QUIET on one big move.
    # That matches OF's timer-reset behavior closely enough; latch explicitly
    # only if QUIET flapping shows up in the gallery.
    t["quiet"] = t["quiet_timer"] > 300
    t["ready_to_die"] = t["influence"] <= 0
    t["influence"] = max(0.0, t["influence"])
    return t
