import csv
import io
import os
import time

NUM_LIGHTS = 8
HANDLE_THRESHOLD = 50.0
DEBOUNCE_SECONDS = 0.5


def handle_id(light_id, is_start):
    """Return a stable string handle id."""
    suffix = "s" if is_start else "e"
    return f"{suffix}{light_id}"


def parse_handle_id(handle_id):
    """Parse a handle id back into (light_id, is_start)."""
    if not handle_id or len(handle_id) < 2:
        return None
    suffix = handle_id[0]
    if suffix not in ("s", "e"):
        return None
    try:
        light_id = int(handle_id[1:])
    except ValueError:
        return None
    return (light_id, suffix == "s")


def _default_ip(light_id):
    return f"192.168.0.{100 + light_id}"


def make_default_tracks(num_lights=NUM_LIGHTS):
    """Return a list of default track dicts for `num_lights`."""
    tracks = []
    for i in range(num_lights):
        y = 100.0 + i * 80.0
        tracks.append({
            "id": i,
            "start": [100.0, y],
            "end": [400.0, y],
            "ip": _default_ip(i),
        })
    return tracks


def track_to_row(track):
    """Convert a track dict to a `tracks.tsv` row dict."""
    return {
        "id": str(track["id"]),
        "sx": str(float(track["start"][0])),
        "sy": str(float(track["start"][1])),
        "ex": str(float(track["end"][0])),
        "ey": str(float(track["end"][1])),
        "ip": str(track["ip"]),
    }


def row_to_track(row):
    """Parse a `tracks.tsv` row dict into a track dict."""
    return {
        "id": int(row["id"]),
        "start": [float(row["sx"]), float(row["sy"])],
        "end": [float(row["ex"]), float(row["ey"])],
        "ip": row["ip"],
    }


def load_tracks(path, num_lights=NUM_LIGHTS):
    """Load tracks from a TSV file, filling defaults for missing rows."""
    tracks = make_default_tracks(num_lights)
    if not os.path.exists(path):
        return tracks
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        rows = list(reader)
    if not rows:
        return tracks
    by_id = {}
    for row in rows:
        try:
            track = row_to_track(row)
            by_id[track["id"]] = track
        except (ValueError, KeyError):
            continue
    for i in range(num_lights):
        if i in by_id:
            tracks[i] = by_id[i]
    return tracks


def save_tracks(path, tracks):
    """Write tracks to a TSV file, creating parent directories if needed."""
    rows = [track_to_row(t) for t in sorted(tracks, key=lambda t: t["id"])]
    _mkdir_for(path)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "sx", "sy", "ex", "ey", "ip"], delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _mkdir_for(path):
    dir_ = os.path.dirname(path)
    if dir_:
        os.makedirs(dir_, exist_ok=True)


def find_nearest_handle(x, y, tracks, threshold=HANDLE_THRESHOLD):
    """Return the handle id of the nearest start/end to (x, y) within threshold."""
    best = None
    best_dist = float("inf")
    for track in tracks:
        light_id = track["id"]
        for is_start, point in ((True, track["start"]), (False, track["end"])):
            dist = ((point[0] - x) ** 2 + (point[1] - y) ** 2) ** 0.5
            if dist < best_dist:
                best_dist = dist
                best = handle_id(light_id, is_start)
    if best is not None and best_dist <= threshold:
        return best
    return None


def update_track_from_handle(tracks, handle_id, x, y):
    """Move the handle's endpoint to (x, y). Mutates the matching track."""
    parsed = parse_handle_id(handle_id)
    if parsed is None:
        return None
    light_id, is_start = parsed
    for track in tracks:
        if track["id"] == light_id:
            if is_start:
                track["start"] = [float(x), float(y)]
            else:
                track["end"] = [float(x), float(y)]
            return track
    return None


class Debouncer:
    """Simple falling-edge debounce: call write only 0.5s after the last event."""

    def __init__(self, delay=DEBOUNCE_SECONDS):
        self.delay = delay
        self._pending_time = None

    def ping(self, now=None):
        """Call on every user event (drag/drop/edit). Returns True if a write should happen."""
        if now is None:
            now = time.monotonic()
        self._pending_time = now
        return False

    def check(self, now=None):
        """Call on each frame/cook. Returns True once when delay has elapsed since last ping."""
        if now is None:
            now = time.monotonic()
        if self._pending_time is None:
            return False
        if now - self._pending_time > self.delay:
            self._pending_time = None
            return True
        return False

    def reset(self):
        self._pending_time = None


def tracks_to_dat_text(tracks):
    """Render tracks as a tab-separated string for a Table DAT."""
    out = io.StringIO()
    writer = csv.DictWriter(
        out,
        fieldnames=["id", "sx", "sy", "ex", "ey", "ip"],
        delimiter="\t",
        lineterminator="\n",
    )
    writer.writeheader()
    for track in sorted(tracks, key=lambda t: t["id"]):
        writer.writerow(track_to_row(track))
    return out.getvalue()


def dat_text_to_tracks(text, num_lights=NUM_LIGHTS):
    """Parse Table DAT text (tab-separated) into a list of track dicts."""
    tracks = make_default_tracks(num_lights)
    rows = list(csv.DictReader(io.StringIO(text), delimiter="\t"))
    by_id = {}
    for row in rows:
        try:
            track = row_to_track(row)
            by_id[track["id"]] = track
        except (ValueError, KeyError):
            continue
    for i in range(num_lights):
        if i in by_id:
            tracks[i] = by_id[i]
    return tracks
