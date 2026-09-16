"""Glue-level regression test for `net_exec.onCook`: the light-rate throttle
must gate ONCE per light, so both the position and intensity messages are
sent on a change (not just the first, which would consume the send slot).
"""

import types

from project1.network import net_logic


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
        self._rows = rows
        self.numRows = len(rows)

    def __getitem__(self, key):
        row, col = key
        if 0 <= row < self.numRows and 0 <= col < len(self._rows[row]):
            return _MockCell(self._rows[row][col])
        raise IndexError(key)


class _MockOscOut:
    def __init__(self):
        self.par = types.SimpleNamespace(address="", port=0)
        self.sent = []

    def sendOSC(self, address, args):
        self.sent.append((address, list(args)))


class _MockScriptOp:
    def __init__(self, lights_dat, tracks_dat, sent_op):
        self._stored = {}
        self.inputs = [lights_dat, tracks_dat]
        self.par = types.SimpleNamespace(
            Sendrate=30,
            Nodeport=9999,
            Mirrormax=False,
            Mirrormaxip="127.0.0.1",
            Mirrormaxport=9999,
            Mirrorunreal=False,
            Mirrorunrealip="127.0.0.1",
            Mirrorunrealport=9998,
        )
        self.time = types.SimpleNamespace(seconds=0.0)
        self.sent_op = sent_op
        self.numSamples = 0

    def fetch(self, key, default=None):
        return self._stored.get(key, default)

    def store(self, key, value):
        self._stored[key] = value

    def appendChan(self, name):
        return [0.0]


def _run_onCook(monkeypatch, lights_rows, tracks_rows):
    import project1.network.net_exec as net_exec

    osc_out = _MockOscOut()
    osc_out_bcast = _MockOscOut()

    def fake_op(name):
        if name == "../oscOut":
            return osc_out
        if name == "../oscOutBcast":
            return osc_out_bcast
        if name == "../control/lights":
            return _MockDat(lights_rows)
        if name == "../trackUI/tracks":
            return _MockDat(tracks_rows)
        return None

    monkeypatch.setattr(net_exec, "net_logic", net_logic, raising=False)
    monkeypatch.setattr(net_exec, "op", fake_op, raising=False)

    scriptOp = _MockScriptOp(osc_out, osc_out_bcast)
    net_exec.onCook(scriptOp)
    return osc_out


class _MockScriptOp:
    def __init__(self, sent_op, bcast_op):
        self._stored = {}
        self.inputs = []
        self.par = types.SimpleNamespace(
            Sendrate=30,
            Nodeport=9999,
            Mirrormax=False,
            Mirrormaxip="127.0.0.1",
            Mirrormaxport=9999,
            Mirrorunreal=False,
            Mirrorunrealip="127.0.0.1",
            Mirrorunrealport=9998,
        )
        self.time = types.SimpleNamespace(seconds=0.0)
        self.sent_op = sent_op
        self.numSamples = 0

    def fetch(self, key, default=None):
        return self._stored.get(key, default)

    def store(self, key, value):
        self._stored[key] = value

    def appendChan(self, name):
        return [0.0]


def test_single_cook_sends_both_position_and_intensity(monkeypatch):
    """Regression: the throttle gates per light once, so a change emits BOTH
    /light/<n>/position and /light/<n>/intensity in the same cook."""
    osc_out = _run_onCook(
        monkeypatch,
        [
            ["id", "locationPercent", "intensity"],
            ["3", "0.5", "0.25"],
        ],
        [
            ["id", "sx", "sy", "ex", "ey", "ip"],
            ["3", "0", "0", "100", "0", "192.168.0.103"],
        ],
    )
    addrs = [a for a, _ in osc_out.sent]
    assert addrs == ["/light/3/position", "/light/3/intensity"]
    assert osc_out.sent[0] == ("/light/3/position", [0.5])
    assert osc_out.sent[1] == ("/light/3/intensity", [0.25])


def test_send_sets_unicast_address_and_port(monkeypatch):
    """Regression (finding 5): the unicast OSC Out DAT must have both the node
    address and the Nodeport set before each send — the port was never applied
    before."""
    osc_out = _run_onCook(
        monkeypatch,
        [
            ["id", "locationPercent", "intensity"],
            ["3", "0.5", "0.25"],
        ],
        [
            ["id", "sx", "sy", "ex", "ey", "ip"],
            ["3", "0", "0", "100", "0", "192.168.0.103"],
        ],
    )
    assert osc_out.par.address == "192.168.0.103"
    assert osc_out.par.port == 9999
