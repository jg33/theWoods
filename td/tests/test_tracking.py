from project1.tracking import target_logic
from project1.tracking.targets_exec import _parse_blob_tracks


def test_influence_ramps_up():
    t = dict(current=[0.0, 0.0], influence=0.0001, quiet_timer=0, dying=False)
    for _ in range(100):
        t = target_logic.update_target(t, 100.0, 100.0, True)
    assert t["influence"] == 1.0


def test_dying_drains_influence():
    t = dict(current=[0.0, 0.0], influence=0.005, quiet_timer=0, dying=False)
    for _ in range(10):
        t = target_logic.update_target(t, 0.0, 0.0, False)
    assert t["ready_to_die"]


def test_quiet_after_threshold():
    t = dict(current=[0.0, 0.0], influence=1.0, quiet_timer=0, dying=False)
    for _ in range(301):
        t = target_logic.update_target(t, 0.0, 0.0, True)
    assert t["quiet"]


def test_moving_resets_quiet_timer():
    t = dict(current=[0.0, 0.0], influence=1.0, quiet_timer=299, dying=False)
    t = target_logic.update_target(t, 100.0, 100.0, True)
    assert not t["quiet"]
    assert t["quiet_timer"] == 0


def test_dying_then_seen_revives():
    t = dict(current=[0.0, 0.0], influence=0.5, quiet_timer=0, dying=False)
    t = target_logic.update_target(t, 0.0, 0.0, False)
    assert t["dying"]
    t = target_logic.update_target(t, 10.0, 10.0, True)
    assert not t["dying"]


class _Channel:
    def __init__(self, name, samples):
        self.name = name
        self.numSamples = len(samples)
        self._samples = list(samples)

    def __getitem__(self, i):
        return self._samples[i]


class _Chop:
    def __init__(self, channels):
        self._channels = {c.name: c for c in channels}

    def chans(self):
        return list(self._channels.values())

    def __getitem__(self, name):
        return self._channels[name]


def test_parse_blob_tracks_per_prefix_channels():
    inp = _Chop(
        [
            _Channel("blob1:tx", [0.5]),
            _Channel("blob1:ty", [0.6]),
            _Channel("blob1:w", [10.0]),
            _Channel("blob1:h", [12.0]),
            _Channel("blob1:age", [2.0]),
            _Channel("blob2:tx", [0.7]),
            _Channel("blob2:ty", [0.8]),
        ]
    )
    targets = {}
    seen, targets = _parse_blob_tracks(inp, targets, target_logic)
    assert seen == {1, 2}
    assert set(targets.keys()) == {1, 2}
    assert targets[1]["current"] == [0.5, 0.6]
    assert targets[2]["current"] == [0.7, 0.8]


def test_parse_blob_tracks_empty_returns_none():
    inp = _Chop([_Channel("something", [1.0])])
    targets = {}
    seen, targets = _parse_blob_tracks(inp, targets, target_logic)
    assert seen is None


def test_parse_blob_tracks_missing_ty_skipped():
    inp = _Chop([_Channel("blob1:tx", [0.5])])
    targets = {}
    seen, targets = _parse_blob_tracks(inp, targets, target_logic)
    assert seen == set()


def test_parse_blob_tracks_non_blob_prefix_uses_crc32():
    inp = _Chop([_Channel("foo:tx", [0.5]), _Channel("foo:ty", [0.6])])
    targets = {}
    seen, targets = _parse_blob_tracks(inp, targets, target_logic)
    assert len(seen) == 1
    label = next(iter(seen))
    assert label == __import__("zlib").crc32(b"foo") & 0x7FFFFFFF


def test_parse_failure_with_existing_targets_no_crash_and_error_channel():
    inp = _Chop([_Channel("something", [1.0])])
    targets = {1: dict(current=[0.5, 0.5], influence=1.0, quiet_timer=0, dying=False)}
    seen, targets = _parse_blob_tracks(inp, targets, target_logic)
    assert seen is None
    # simulate onCook update-unseen loop
    to_remove = []
    for label, t in targets.items():
        if seen is None or label not in seen:
            t = target_logic.update_target(t, t["current"][0], t["current"][1], False)
            targets[label] = t
        if t.get("ready_to_die"):
            to_remove.append(label)
    assert not to_remove
    assert targets[1]["dying"]
    # error channel condition from onCook
    assert seen is None
