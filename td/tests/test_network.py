import pytest

from project1.network import net_logic


# --- node_messages ---------------------------------------------------------

def test_node_messages_match_spec_addresses():
    msgs = net_logic.node_messages(3, 0.42, 0.77)
    addrs = [a for a, _ in msgs]
    assert addrs == ["/light/3/position", "/light/3/intensity"]
    assert msgs[0][1] == [0.42]
    assert msgs[1][1] == [0.77]


def test_node_messages_clamp_to_01():
    msgs = net_logic.node_messages(0, -0.5, 1.5)
    assert msgs[0][1] == [0.0]
    assert msgs[1][1] == [1.0]


def test_node_messages_int_light_id():
    msgs = net_logic.node_messages(12, 0.5, 0.5)
    assert msgs[0][0] == "/light/12/position"


# --- control_message -------------------------------------------------------

@pytest.mark.parametrize("control", ["identify", "calibrate", "zero", "stop"])
def test_control_message_no_args(control):
    addr, args = net_logic.control_message(5, control)
    assert addr == "/light/5/%s" % control
    assert args == []


def test_control_message_move_takes_int_steps():
    addr, args = net_logic.control_message(5, "move", steps=-120)
    assert addr == "/light/5/move"
    assert args == [-120]


# --- ping_message ----------------------------------------------------------

def test_ping_message_format():
    addr, args = net_logic.ping_message(7)
    assert addr == "/ping"
    assert args == [7]


# --- parse_node_status ------------------------------------------------------

def test_parse_min_trigger():
    row = net_logic.parse_node_status("/light/2/minTrigger", [])
    assert row == {"id": 2, "status": "minTrigger", "value": 1}


def test_parse_max_trigger():
    row = net_logic.parse_node_status("/light/2/maxTrigger", [])
    assert row == {"id": 2, "status": "maxTrigger", "value": 1}


def test_parse_max_pos_carries_int():
    row = net_logic.parse_node_status("/light/4/maxPos", [2048])
    assert row == {"id": 4, "status": "maxPos", "value": 2048}


def test_parse_max_pos_missing_arg_defaults_zero():
    row = net_logic.parse_node_status("/light/4/maxPos", [])
    assert row["value"] == 0


def test_parse_ignores_non_status_addresses():
    assert net_logic.parse_node_status("/ping", [1]) is None
    assert net_logic.parse_node_status("/light/1/position", [0.5]) is None
    assert net_logic.parse_node_status("/bogus", []) is None


# --- LightThrottle ----------------------------------------------------------

def test_throttle_sends_on_change_immediately():
    t = net_logic.LightThrottle(rate_hz=30, clock=lambda: 100.0)
    assert t.should_send(1, 0.1, 0.2) is True
    # different values -> immediate
    assert t.should_send(1, 0.1, 0.3) is True
    assert t.should_send(1, 0.5, 0.3) is True


def test_throttle_rate_limits_unchanged_values():
    t = net_logic.LightThrottle(rate_hz=30, clock=lambda: 100.0)
    assert t.should_send(1, 0.1, 0.2) is True
    # same values, well before 1/30s boundary
    assert t.should_send(1, 0.1, 0.2, now=100.0 + 0.01) is False


def test_throttle_refreshes_at_rate_boundary():
    t = net_logic.LightThrottle(rate_hz=30, clock=lambda: 100.0)
    assert t.should_send(1, 0.1, 0.2) is True
    # unchanged but past 1/30s (~0.0333s)
    assert t.should_send(1, 0.1, 0.2, now=100.0 + 0.034) is True


def test_throttle_per_light_independence():
    t = net_logic.LightThrottle(rate_hz=30, clock=lambda: 100.0)
    assert t.should_send(1, 0.1, 0.2) is True
    assert t.should_send(2, 0.1, 0.2) is True
    assert t.should_send(1, 0.1, 0.2, now=100.0 + 0.01) is False
    assert t.should_send(2, 0.1, 0.2, now=100.0 + 0.01) is False


def test_throttle_small_change_counts_as_change():
    t = net_logic.LightThrottle(rate_hz=30, clock=lambda: 100.0)
    assert t.should_send(1, 0.1, 0.2) is True
    # 6-decimal rounding: tiny jitter below that counts as unchanged
    assert t.should_send(1, 0.1000001, 0.2, now=100.0 + 0.001) is False