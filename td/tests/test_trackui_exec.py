import types

from project1.trackUI import ui_logic


class _MockCell:
    def __init__(self, value):
        self.value = value

    def __int__(self):
        return int(self.value)

    def __float__(self):
        return float(self.value)

    def __str__(self):
        return str(self.value)


class _MockChannel:
    def __init__(self, name, samples):
        self.name = name
        self.numSamples = len(samples)
        self._samples = list(samples)

    def __getitem__(self, i):
        return _MockCell(self._samples[i])


class _MockChop:
    def __init__(self, channels):
        self._channels = {c.name: c for c in channels}

    def chans(self):
        return list(self._channels.values())

    def __getitem__(self, name):
        return self._channels[name]


class _MockTracksDat:
    def __init__(self):
        self.text = None


class _MockScriptOp:
    def __init__(self, tracks, debouncer, edit):
        self._state = {"tracks": tracks, "debouncer": debouncer}
        self.inputs = []
        self.par = types.SimpleNamespace(Edit=edit)

    def fetch(self, key, default=None):
        return self._state.get(key, default)

    def store(self, key, value):
        self._state[key] = value


def _stub_td(monkeypatch, saved_to):
    """Inject TD globals (op, project) and a fake ui_logic so onCook runs headless."""
    import project1.trackUI.ui_exec as ui_exec

    def fake_op(name):
        return _MockTracksDat()

    project = types.SimpleNamespace(folder="td")
    tracks = ui_logic.make_default_tracks()
    fake_logic = types.SimpleNamespace(
        load_tracks=lambda *a, **k: tracks,
        tracks_to_dat_text=lambda t: "",
        save_tracks=lambda path, t: saved_to.append(path),
        Debouncer=ui_logic.Debouncer,
    )
    # ui_exec.py references `op` and `project` as TD-builtin globals; provide them
    # (raising=False because neither exists as a module attribute when imported).
    monkeypatch.setattr(ui_exec, "op", fake_op, raising=False)
    monkeypatch.setattr(ui_exec, "project", project, raising=False)
    monkeypatch.setattr(ui_exec, "ui_logic", fake_logic)
    return ui_exec


def test_apply_panel_input_updates_start_and_end():
    tracks = ui_logic.make_default_tracks()
    panel = _MockChop([
        _MockChannel("s0x", [12.0]),
        _MockChannel("s0y", [34.0]),
        _MockChannel("e0x", [56.0]),
        _MockChannel("e0y", [78.0]),
    ])

    import project1.trackUI.ui_exec as ui_exec
    changed = ui_exec._apply_panel_input(tracks, panel)

    assert changed is True
    assert tracks[0]["start"] == [12.0, 34.0]
    assert tracks[0]["end"] == [56.0, 78.0]

    # Calling again with the same values reports no change.
    changed = ui_exec._apply_panel_input(tracks, panel)
    assert changed is False


def test_pending_debounce_flushes_when_edit_off(monkeypatch):
    """F2: a debounced write scheduled before Edit toggled off must still fire."""
    import time

    saved_to = []
    ui_exec = _stub_td(monkeypatch, saved_to)

    tracks = ui_logic.make_default_tracks()
    d = ui_logic.Debouncer()
    d.ping(now=time.monotonic())
    d._pending_time -= 5.0  # 5s in the past -> already past the delay

    # Edit is OFF, but a write is pending from a drag that just ended.
    scriptop = _MockScriptOp(tracks, d, edit=False)
    ui_exec.onCook(scriptop)

    assert len(saved_to) == 1, "pending TSV write must flush even when Edit is off"
    # Debouncer was reset so the write isn't re-fired every subsequent cook.
    assert scriptop.fetch("debouncer") is not d


def test_edit_off_blocks_panel_input(monkeypatch):
    """Edit off -> onCook ignores panel drag input."""
    saved_to = []
    ui_exec = _stub_td(monkeypatch, saved_to)

    tracks = ui_logic.make_default_tracks()
    d = ui_logic.Debouncer()  # no pending write
    scriptop = _MockScriptOp(tracks, d, edit=False)
    ui_exec.onCook(scriptop)

    assert tracks == ui_logic.make_default_tracks()
    assert saved_to == [], "no write when nothing is pending"
