import os
import tempfile
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


def test_onCook_flushes_pending_debounce_even_when_edit_off():
    """F2: a debounced write still fires when Edit toggles off mid-drag."""
    import project1.trackUI.ui_exec as ui_exec

    state = {}
    saved_to = []

    class _MockScriptOp:
        inputs = []

        class par:
            class Edit:
                pass

            Edit = Edit()

        def __init__(self):
            self.par = _FakePar(False)

        def fetch(self, key, default=None):
            return state.get(key, default)

        def store(self, key, value):
            state[key] = value

    class _FakePar:
        def __init__(self, edit):
            self.Edit = edit

    class _FakeBool:
        def __init__(self, v):
            self.v = v

        def __bool__(self):
            return self.v

    scriptOp = _MockScriptOp()
    scriptOp.par.Edit = _FakeBool(False)  # Edit is OFF

    # Arrange: a pending debounce already scheduled (as if a drag just ended).
    tracks = ui_logic.make_default_tracks()
    debouncer = ui_logic.Debouncer(delay=0.5)
    base = 1000.0
    debouncer.ping(now=base)
    scriptOp.store("tracks", tracks)
    scriptOp.store("debouncer", debouncer)

    # Stub the TSV write to observe it without touching disk.
    ui_exec._write_tracks_tsv = lambda *a, **k: saved_to.append(True)

    # Cook when the debounce delay has elapsed, with Edit still OFF.
    scriptOp.par.Edit = _FakeBool(False)
    ui_exec.onCook(scriptOp)

    assert saved_to, "pending TSV write must flush even when Edit is off"


class _State:
    def __init__(self, tracks, debouncer):
        self.tracks = tracks
        self.debouncer = debouncer

    def __getitem__(self, key):
        return {"tracks": self.tracks, "debouncer": self.debouncer}[key]


class _MockScriptOp:
    def __init__(self, tracks, debouncer, edit):
        self.state = _State(tracks, debouncer)
        self.inputs = []
        self.par = type("P", (), {"Edit": edit})()
        self.dat_text = None

    def fetch(self, key, _default=None):
        return self.state[key]

    def store(self, key, value):
        self.state[key] = value


def test_pending_write_flushes_when_edit_off(monkeypatch):
    import time

    import project1.trackUI.ui_exec as ui_exec

    tracks = ui_logic.make_default_tracks()
    # A debouncer with a pending write whose delay has already elapsed.
    d = ui_logic.Debouncer()
    d.ping(now=time.monotonic())
    d._pending_time = d._pending_time - 5.0  # 5s in the past → already due

    scriptop = _MockScriptOp(tracks, d, edit=False)

    written = []
    fake_logic = type("FakeLogic", (), {
        "load_tracks": staticmethod(lambda *a, **k: tracks),
        "tracks_to_dat_text": staticmethod(lambda t: "dat"),
        "save_tracks": staticmethod(lambda path, t: written.append((path, t))),
        "Debouncer": ui_logic.Debouncer,
    })
    monkeypatch.setattr(ui_exec, "ui_logic", fake_logic)
    monkeypatch.setattr(ui_exec, "op", lambda name: type("D", (), {"text": None})())

    # Edit is off, but the pending debounced write must still flush.
    ui_exec.onCook(scriptop)
    assert len(written) == 1
    # And the debouncer was reset so the write isn't re-fired.
    assert scriptop.fetch("debouncer") is not d


def test_edit_off_blocks_panel_input(monkeypatch):
    import project1.trackUI.ui_exec as ui_exec

    tracks = ui_logic.make_default_tracks()
    d = ui_logic.Debouncer()  # no pending write
    scriptop = _MockScriptOp(tracks, d, edit=False)

    fake_logic = type("FakeLogic", (), {
        "load_tracks": staticmethod(lambda *a, **k: tracks),
        "tracks_to_dat_text": staticmethod(lambda t: "dat"),
        "save_tracks": staticmethod(lambda path, t: None),
        "Debouncer": ui_logic.Debouncer,
    })
    monkeypatch.setattr(ui_exec, "ui_logic", fake_logic)
    monkeypatch.setattr(ui_exec, "op", lambda name: type("D", (), {"text": None})())

    # Edit off with no pending write: onCook is a no-op (no panel input processed).
    ui_exec.onCook(scriptop)
    assert tracks == ui_logic.make_default_tracks()
