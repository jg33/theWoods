
from project1.control import light_logic


def test_dist_influence_ramp():
    # At distance 0 with full target influence, di should be 1.0
    assert light_logic.dist_influence(0, 300, 1.0) == 1.0
    # At distance 300, di is 0
    assert light_logic.dist_influence(300, 300, 1.0) == 0.0
    # Halfway with half influence: 0.5 * 0.5 = 0.25
    assert light_logic.dist_influence(150, 300, 0.5) == 0.25
    # Below 0.1 threshold should zero out: (300-290)/300 = 0.033
    assert light_logic.dist_influence(290, 300, 1.0) == 0.0


def test_track_percent():
    assert light_logic.track_percent([0, 0], [0, 0], [100, 0]) == 0.0
    assert light_logic.track_percent([100, 0], [0, 0], [100, 0]) == 1.0
    assert light_logic.track_percent([50, 0], [0, 0], [100, 0]) == 0.5
    # Off-axis point projects to the midpoint distance along the actual track.
    assert light_logic.track_percent(light_logic._closest_point_on_segment([50, 50], [0, 0], [100, 0]), [0, 0], [100, 0]) == 0.5


def test_make_light_initial():
    l = light_logic.make_light(0, [0, 0], [100, 0])
    assert l["current"] == [50.0, 0.0]
    assert l["move_target"] == [50.0, 0.0]
    assert l["intensity"] == 0.0
    assert l["id"] == 0


def test_update_light_intensity_rises_as_target_approaches():
    l = light_logic.make_light(0, [0, 0], [100, 0], max_distance=500)
    target = {"current": [1000, 0], "influence": 1.0, "quiet": False, "dying": False}
    # Far away light is not affected yet
    for _ in range(100):
        l = light_logic.update_light(l, [target], light_logic.woods_state(False, []))
    # Because the lerp is slow, far target still produces a tiny influence.
    assert l["intensity"] < 0.05

    # Bring the target closer
    target["current"] = [10, 0]
    for _ in range(300):
        l = light_logic.update_light(l, [target], light_logic.woods_state(False, []))
    assert l["intensity"] > 0.5


def test_update_light_location_0_at_start_1_at_end():
    l = light_logic.make_light(0, [0, 0], [100, 0])
    target = {"current": [0, 0], "influence": 1.0, "quiet": False, "dying": False}
    for _ in range(5000):
        l = light_logic.update_light(l, [target], light_logic.woods_state(False, []))
    assert l["locationPercent"] < 0.01
    assert l["current"][0] < 1.0

    target["current"] = [100, 0]
    for _ in range(15000):
        l = light_logic.update_light(l, [target], light_logic.woods_state(False, []))
    assert l["locationPercent"] > 0.95
    assert l["current"][0] > 95.0


def test_update_light_no_targets_decays():
    l = light_logic.make_light(0, [0, 0], [100, 0])
    l["intensity"] = 1.0
    for _ in range(500):
        l = light_logic.update_light(l, [], light_logic.woods_state(False, []))
    assert l["intensity"] < 0.01


def test_closest_point_on_segment():
    assert light_logic._closest_point_on_segment([50, 10], [0, 0], [100, 0]) == [50.0, 0.0]
    assert light_logic._closest_point_on_segment([-10, 0], [0, 0], [100, 0]) == [0.0, 0.0]
    assert light_logic._closest_point_on_segment([110, 0], [0, 0], [100, 0]) == [100.0, 0.0]


def test_woods_state_precedence():
    assert light_logic.woods_state(False, []) == 0  # NORMAL
    assert light_logic.woods_state(True, []) == 1   # IDLE
    quiet_target = {"quiet": True}
    assert light_logic.woods_state(False, [quiet_target]) == 2  # QUIET
    # Manual NIGHT/DARK overrides everything
    assert light_logic.woods_state(True, [quiet_target], 3) == 3
    assert light_logic.woods_state(True, [quiet_target], 4) == 4


def test_update_light_idle_noise_does_not_crash():
    l = light_logic.make_light(0, [0, 0], [100, 0])
    for i in range(60):
        l = light_logic.update_light(l, [], 1, t=i / 60.0, elapsed=i / 60.0)
    assert 0.0 <= l["intensity"] <= 1.0


def test_update_light_quiet_noise_does_not_crash():
    l = light_logic.make_light(0, [0, 0], [100, 0])
    for i in range(60):
        l = light_logic.update_light(l, [], 2, t=i / 60.0, elapsed=i / 60.0)
    assert 0.0 <= l["intensity"] <= 1.0


class _MockCell:
    def __init__(self, value):
        self.value = value

    def __int__(self):
        return int(self.value)

    def __float__(self):
        return float(self.value)

    def __str__(self):
        return str(self.value)


class _MockDat:
    def __init__(self, rows):
        # rows: list of lists of string values; row 0 is header
        self._rows = rows
        self.numRows = len(rows)

    def __getitem__(self, key):
        row, col = key
        if 0 <= row < self.numRows and 0 <= col < len(self._rows[row]):
            return _MockCell(self._rows[row][col])
        raise IndexError(key)


def test_parse_targets():
    from project1.control import control_exec

    dat = _MockDat([
        ["label", "x", "y", "influence", "quiet", "dying"],
        ["1", "100.0", "200.0", "0.8", "1", "0"],
        ["2", "10.0", "20.0", "0.5", "0", "1"],
    ])
    targets = control_exec._parse_targets(dat)
    assert len(targets) == 2
    assert targets[0]["current"] == [100.0, 200.0]
    assert targets[0]["influence"] == 0.8
    assert targets[0]["quiet"] is True
    assert targets[0]["dying"] is False
    assert targets[1]["quiet"] is False
    assert targets[1]["dying"] is True


def test_parse_targets_missing_rows_returns_empty():
    from project1.control import control_exec

    dat = _MockDat([["label", "x", "y", "influence", "quiet", "dying"]])
    assert control_exec._parse_targets(dat) == []
    assert control_exec._parse_targets(None) == []


def test_parse_tracks():
    from project1.control import control_exec

    dat = _MockDat([
        ["id", "sx", "sy", "ex", "ey", "ip"],
        ["0", "0", "0", "100", "0", "192.168.0.100"],
        ["1", "100", "0", "100", "100", "192.168.0.101"],
    ])
    tracks = control_exec._parse_tracks(dat)
    assert len(tracks) == 2
    assert tracks[0] == {"id": 0, "start": [0.0, 0.0], "end": [100.0, 0.0], "ip": "192.168.0.100"}
    assert tracks[1] == {"id": 1, "start": [100.0, 0.0], "end": [100.0, 100.0], "ip": "192.168.0.101"}


def test_update_idle_highlight_picks_one():
    from project1.control import control_exec

    l1 = light_logic.make_light(0, [0, 0], [100, 0])
    l2 = light_logic.make_light(1, [0, 0], [100, 0])
    became = control_exec._update_idle_highlight(l1, 0.0, 2.0, 10.0, False)
    assert became is True
    assert l1["bIsIdleHighlight"] is True
    assert l1["endHighlightTime"] > 0.0

    # No second pick if one is already active
    became = control_exec._update_idle_highlight(l2, 0.0, 2.0, 10.0, True)
    assert became is False
