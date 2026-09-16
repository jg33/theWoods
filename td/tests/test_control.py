
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


def test_max_distance_indexed_by_track_id():
    """Per-light MaxDistance must follow track/light id, not loop index."""
    from project1.control import control_exec

    # Patch TD globals so onCook can run outside TouchDesigner.
    control_exec.light_logic = light_logic
    control_exec.me = type("me", (), {"time": type("time", (), {"rate": 60})()})()
    control_exec.op = None

    tracks_dat = _MockDat([
        ["id", "sx", "sy", "ex", "ey", "ip"],
        ["0", "0", "0", "100", "0", "192.168.0.100"],
        ["3", "100", "0", "100", "100", "192.168.0.103"],
        ["7", "200", "0", "200", "100", "192.168.0.107"],
    ])

    class _MockPar:
        Manualoverride = False
        Manualstate = 0.0
        Bisidle = False
        Idlehighlightmin = 2.0
        Idlehighlightmax = 10.0
        Maxdistance0 = 100.0
        Maxdistance3 = 200.0
        Maxdistance7 = 300.0

        def __getattr__(self, name):
            if name.startswith("Maxdistance"):
                return 300.0
            raise AttributeError(name)

    class _MockScriptOp:
        def __init__(self):
            self._stored = {}
            self.par = _MockPar()
            self.time = type("time", (), {"seconds": 0.0})()
            self.rate = 60
            self.numSamples = 1

        def fetch(self, key, default):
            return self._stored.get(key, default)

        def store(self, key, value):
            self._stored[key] = value

        def clear(self):
            pass

        def appendChan(self, name):
            return [0.0]

    # Patch TD op() so onCook resolves targets/tracks by corrected cross-COMP path.
    control_exec.op = lambda name: {"../../trackUI/tracks": tracks_dat}.get(name)

    scriptOp = _MockScriptOp()
    control_exec.onCook(scriptOp)

    lights = scriptOp.fetch("lights", [])
    assert len(lights) == 3
    by_id = {l["id"]: l for l in lights}
    assert by_id[0]["maxDistance"] == 100.0
    assert by_id[3]["maxDistance"] == 200.0
    assert by_id[7]["maxDistance"] == 300.0

    # Change the parameters and re-cook to verify the update path as well.
    scriptOp.par.Maxdistance0 = 111.0
    scriptOp.par.Maxdistance3 = 222.0
    scriptOp.par.Maxdistance7 = 333.0
    control_exec.onCook(scriptOp)

    lights = scriptOp.fetch("lights", [])
    by_id = {l["id"]: l for l in lights}
    assert by_id[0]["maxDistance"] == 111.0
    assert by_id[3]["maxDistance"] == 222.0
    assert by_id[7]["maxDistance"] == 333.0


def _mock_dat(rows):
    return _MockDat(rows)


def test_manual_override_gate_reaches_automatic_idle():
    """Regression (finding 2): with Manualoverride Off, woods_state must be
    fed None so the automatic state machine (bIsIdle / all-quiet) is reachable —
    Manualstate alone must NOT permanently force the manual override."""
    from project1.control import control_exec

    control_exec.light_logic = light_logic
    control_exec.me = type("me", (), {"time": type("time", (), {"rate": 60})()})()
    control_exec.op = lambda name: {
        "../../tracking/targets": _mock_dat([["label", "x", "y", "influence", "quiet", "dying"]]),
        "../../trackUI/tracks": _mock_dat([["id", "sx", "sy", "ex", "ey", "ip"]]),
    }.get(name)

    class _MockPar:
        Manualoverride = False
        Manualstate = 3.0  # would force NIGHT if the override ignored the gate
        Bisidle = True
        Idlehighlightmin = 2.0
        Idlehighlightmax = 10.0

        def __getattr__(self, name):
            if name.startswith("Maxdistance"):
                return 300.0
            raise AttributeError(name)

    class _MockScriptOp:
        def __init__(self):
            self._stored = {}
            self.chans = []
            self.par = _MockPar()
            self.time = type("time", (), {"seconds": 0.0})()
            self.rate = 60
            self.numSamples = 1

        def fetch(self, key, default):
            return self._stored.get(key, default)

        def store(self, key, value):
            self._stored[key] = value

        def clear(self):
            self.chans = []

        def appendChan(self, name):
            c = [0.0]
            self.chans.append((name, c))
            return c

    scriptOp = _MockScriptOp()
    control_exec.onCook(scriptOp)
    # With Manualoverride Off + Bisidle True, the automatic machine yields IDLE
    # (1), never the manual NIGHT (3) that Manualstate alone would force.
    states = [c[0] for n, c in scriptOp.chans if n == "state"]
    assert states == [1]
