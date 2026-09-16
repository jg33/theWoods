"""Pure-Python helpers for the depthIn COMP.

Only the logic that must run outside TD lives here. Transform/Merge POPs do the
geometry and clip math natively in TD — do not reimplement that here, beyond the
tiny `in_height_band` predicate used to sanity-check the height clip band.
"""


def parse_cameras(tsv_text):
    """Parse cameras.tsv into a dict keyed by camera id.

    Schema: id, enabled, tx, ty, tz, rx, ry, rz, scale.
    Blank lines and comments (#..., incl. leading whitespace) are ignored. Rows
    shorter than the header are skipped. `enabled` is truthy for 1/true/yes/on.
    Returns {} if there is only a header.
    """
    lines = [
        l for l in tsv_text.splitlines()
        if l.strip() and not l.strip().startswith("#")
    ]
    if not lines:
        return {}
    header = [h.strip() for h in lines[0].split("\t")]
    cams = {}
    for line in lines[1:]:
        parts = [p.strip() for p in line.split("\t")]
        if len(parts) != len(header):
            continue
        row = dict(zip(header, parts))
        try:
            # Duplicate id rows: last wins (deliberate — later rows override earlier).
            cams[row["id"]] = {
                "enabled": row["enabled"].lower() in ("1", "true", "yes", "on"),
                "tx": float(row["tx"]),
                "ty": float(row["ty"]),
                "tz": float(row["tz"]),
                "rx": float(row["rx"]),
                "ry": float(row["ry"]),
                "rz": float(row["rz"]),
                "scale": float(row["scale"]),
            }
        except (KeyError, ValueError):
            # Malformed row: skip rather than crash the whole merge.
            continue
    return cams


def enabled_cameras(cams):
    """Return the ids of enabled cameras (the ones wired into the merge)."""
    return [cid for cid, c in cams.items() if c["enabled"]]


def in_height_band(y, clip_min, clip_max):
    """True if point height `y` is inside [clip_min, clip_max]; band edges inclusive.

    Either bound being None means that side is unconfigured -> no clipping.
    """
    if clip_min is not None and y < clip_min:
        return False
    if clip_max is not None and y > clip_max:
        return False
    return True
