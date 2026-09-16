import math


DEFAULT_MAX_DISTANCE = 300.0


def dist_influence(dist, max_dist, target_influence):
    """Per-light influence of a target based on distance."""
    di = (max_dist - dist) / max_dist
    di = max(0.0, min(1.0, di))
    if di < 0.1:
        di = 0.0
    return di * target_influence


def track_percent(current, start, end):
    """Return 0..1 position of `current` along the start->end track."""
    total = math.dist(start, end)
    return math.dist(start, current) / total if total else 0.0


def _closest_point_on_segment(p, a, b):
    """Project point p onto the line segment a->b."""
    ax, ay = a
    bx, by = b
    px, py = p
    dx = bx - ax
    dy = by - ay
    if dx == 0 and dy == 0:
        return [float(ax), float(ay)]
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return [ax + t * dx, ay + t * dy]


def _default_noise(t):
    """Deterministic 1D pseudo-Perlin fallback used when no Noise CHOP is wired."""
    # Sum of octaved sines gives smooth, bounded 0..1 noise without extra deps.
    n = 0.0
    for i, freq in enumerate((1.0, 2.0, 4.0, 8.0)):
        n += math.sin(t * freq + i * 1.3) / freq
    n = n / (1.0 + 0.5 + 0.25 + 0.125)
    return max(0.0, min(1.0, (n + 1.0) * 0.5))


def _idle_noise(t, id_, noise_func=None):
    if noise_func is not None:
        n = noise_func(t + id_ * 6.66)
    else:
        n = _default_noise(t + id_ * 6.66)
    return n * n


def make_light(id_, start, end, max_distance=DEFAULT_MAX_DISTANCE):
    """Create a fresh light state dict matching the OF Light constructor."""
    start = [float(start[0]), float(start[1])]
    end = [float(end[0]), float(end[1])]
    mid = [(start[0] + end[0]) * 0.5, (start[1] + end[1]) * 0.5]
    return {
        "id": id_,
        "start": start,
        "end": end,
        "current": mid[:],
        "move_target": mid[:],
        "intensity": 0.0,
        "target_intensity": 0.0,
        "locationPercent": 0.0,
        "bIsIdleHighlight": False,
        "endHighlightTime": 0.0,
        "maxDistance": float(max_distance),
    }


def woods_state(b_is_idle, targets, manual_state=None):
    """
    Compute the WoodsState index.
    0=NORMAL, 1=IDLE, 2=QUIET, 3=NIGHT, 4=DARK.
    Precedence: manual NIGHT/DARK > IDLE > QUIET > NORMAL.
    """
    if manual_state is not None:
        return int(manual_state)
    if b_is_idle:
        return 1
    if targets and all(t.get("quiet", False) for t in targets):
        return 2
    return 0


def update_light(l, targets, state, t=0.0, elapsed=0.0, noise_func=None):
    """
    Update one light for one frame.
    `targets` is a list of dicts with keys: current [x,y], influence, quiet, dying.
    `state` is the WoodsState index.
    `t` is a continuous time value (seconds) for noise.
    `elapsed` is the current frame time for highlight timeouts.
    """
    max_dist = l.get("maxDistance", DEFAULT_MAX_DISTANCE)

    if state == 0:  # NORMAL
        target_intensity = 0.0

        for target in targets:
            dist = math.dist(l["current"], target["current"])
            if dist < max_dist:
                di = dist_influence(dist, max_dist, target["influence"])
                track_target = _closest_point_on_segment(
                    target["current"], l["start"], l["end"]
                )
                l["move_target"][0] += (track_target[0] - l["move_target"][0]) * di
                l["move_target"][1] += (track_target[1] - l["move_target"][1]) * di

        if targets:
            nearest = min(targets, key=lambda t: math.dist(l["current"], t["current"]))
            nd = math.dist(l["current"], nearest["current"])
            if nd < max_dist:
                target_intensity = (
                    (max_dist - nd) / max_dist * nearest["influence"]
                )
                target_intensity = max(0.0, min(1.0, target_intensity))

        l["intensity"] += (target_intensity - l["intensity"]) * 0.01
        l["current"][0] += (l["move_target"][0] - l["current"][0]) * 0.001
        l["current"][1] += (l["move_target"][1] - l["current"][1]) * 0.001

    elif state == 1:  # IDLE
        if l["bIsIdleHighlight"]:
            if elapsed > l["endHighlightTime"]:
                l["bIsIdleHighlight"] = False
                l["target_intensity"] = 0.005
            else:
                l["target_intensity"] = _idle_noise(t, l["id"], noise_func) * 0.5
        else:
            l["target_intensity"] = 0.005
        l["intensity"] += (l["target_intensity"] - l["intensity"]) * 0.01

    elif state == 2:  # QUIET
        if elapsed > l["endHighlightTime"]:
            l["bIsIdleHighlight"] = False
        l["target_intensity"] = _idle_noise(t, l["id"], noise_func) * 0.5
        l["intensity"] += (l["target_intensity"] - l["intensity"]) * 0.01

    # NIGHT (3) and DARK (4) are parameter-page placeholders: leave intensity untouched.

    l["locationPercent"] = track_percent(l["current"], l["start"], l["end"])
    return l
