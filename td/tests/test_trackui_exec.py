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
