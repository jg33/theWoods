"""Glue-level regression test for `net_exec.onCook`: the light-rate throttle
must gate ONCE per light, so both the position and intensity messages are
sent on a change (not just the first, which would consume the send slot); and
the OSC Out DAT's address/port are set for each unicast send.
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
    def __init__(self):
        self._stored = {}
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
    dats = {
        "../oscOut": osc_out,
        "../oscOutBcast": osc_out_bcast,
        "../../control/lights": _MockDat(lights_rows),
        "../../trackUI/tracks": _MockDat(tracks_rows),
    }
    monkeypatch.setattr(net_exec, "net_logic", net_logic, raising=False)
    monkeypatch.setattr(net_exec, "op", lambda name: dats[name], raising=False)

    scriptOp = _MockScriptOp()
    net_exec.onCook(scriptOp)
    return osc_out


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


def test_unicast_sets_address_and_port(monkeypatch):
    """Regression: the OSC Out DAT is pointed at the node's IP and Nodeport
    before each send (uses .par.address, not .par.hostname)."""
    osc_out = _run_onCook(
        monkeypatch,
        [
            ["id", "locationPercent", "intensity"],
            ["7", "0.2", "0.8"],
        ],
        [
            ["id", "sx", "sy", "ex", "ey", "ip"],
            ["7", "0", "0", "50", "0", "192.168.0.107"],
        ],
    )
    assert osc_out.par.address == "192.168.0.107"
    assert osc_out.par.port == 9999
    assert len(osc_out.sent) == 2


def test_onPulse_sends_control_message(monkeypatch):
    """Regression (finding 4): pulsing Identify/Zero/etc from the network COMP
    parameter page sends the matching /light/<n>/<control> message to the
    selected node's IP via oscOut."""
    import project1.network.net_exec as net_exec

    osc_out = _MockOscOut()
    dats = {
        "../oscOut": osc_out,
        "../../trackUI/tracks": _MockDat([
            ["id", "sx", "sy", "ex", "ey", "ip"],
            ["2", "0", "0", "50", "0", "192.168.0.102"],
        ]),
    }
    monkeypatch.setattr(net_exec, "net_logic", net_logic, raising=False)
    monkeypatch.setattr(net_exec, "op", lambda name: dats[name], raising=False)

    class _Par:
        Light = 2
        Nodeport = 9999
        Moveamount = 10

    scriptOp = types.SimpleNamespace(par=_Par())
    par = types.SimpleNamespace(name="Zero", owner=scriptOp)
    net_exec.onPulse(par)
    assert osc_out.sent == [("/light/2/zero", [])]
    assert osc_out.par.address == "192.168.0.102"
    assert osc_out.par.port == 9999

    osc_out.sent[:] = []
    net_exec.onPulse(types.SimpleNamespace(name="Move", owner=scriptOp))
    assert osc_out.sent == [("/light/2/move", [10])]
