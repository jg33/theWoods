def update_target(t, measured_x, measured_y, seen):
    # t: dict(current=[x,y], influence, quiet_timer, dying)
    # returns updated t
    if seen:
        t["current"][0] += (measured_x - t["current"][0]) * 0.05
        t["current"][1] += (measured_y - t["current"][1]) * 0.05
        t["influence"] = min(1.0, t["influence"] + 0.01)
        t["dying"] = False
        moved = abs(measured_x - t["current"][0]) + abs(measured_y - t["current"][1])
        t["quiet_timer"] = 0 if moved > 20 else t["quiet_timer"] + 1
    else:
        t["influence"] -= 0.001
        t["dying"] = True
    t["quiet"] = t["quiet_timer"] > 300
    t["ready_to_die"] = t["influence"] <= 0
    t["influence"] = max(0.0, t["influence"])
    return t
