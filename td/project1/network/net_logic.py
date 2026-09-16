"""TD-free logic for the `network` COMP: build OSC messages, rate-limit,
throttle per light, and parse inbound node status.

No TouchDesigner imports here — importable by both `net_exec.py` (glue) and
the unit tests, mirroring the tracking/control/trackUI pattern.
"""

import re
import time

RATE_LIMIT_HZ = 30.0
PING_INTERVAL = 1.0

# Inbound node status addresses (spec table: node->TD).
_STATUS_RE = re.compile(r"^/light/(\d+)/(minTrigger|maxTrigger|maxPos)$")


def clamp01(v):
    """Clamp a value to the 0..1 OSC domain."""
    return max(0.0, min(1.0, float(v)))


def node_messages(light_id, location, intensity):
    """Build the per-node TD->node OSC messages for one light.

    Returns a list of ``(address, [args])`` pairs matching the spec table:
    ``/light/<n>/position <float 0-1>`` and ``/light/<n>/intensity <float 0-1>``.
    The same messages are re-sent verbatim to Max/Unreal mirrors.
    """
    return [
        ("/light/%d/position" % light_id, [round(clamp01(location), 6)]),
        ("/light/%d/intensity" % light_id, [round(clamp01(intensity), 6)]),
    ]


def control_message(light_id, control, steps=0):
    """Build a control message: identify|calibrate|zero|stop (no args) or move <int>."""
    if control == "move":
        return ("/light/%d/move" % light_id, [int(steps)])
    return ("/light/%d/%s" % (light_id, control), [])


def ping_message(sequence=0):
    """Heartbeat broadcast to all nodes, spec: ``/ping <int>`` every 1s."""
    return ("/ping", [int(sequence)])


def parse_node_status(address, args=None):
    """Parse an inbound node->TD OSC message.

    Returns a row dict for the ``nodeStatus`` DAT (``id, status, value``), or
    ``None`` when the address is not a status message (e.g. ``/ping``).
    ``minTrigger``/``maxTrigger`` are limit-switch hits (value 1); ``maxPos``
    carries the reported calibrated max position int.
    """
    m = _STATUS_RE.match(address) if address else None
    if not m:
        return None
    light_id = int(m.group(1))
    status = m.group(2)
    if status == "maxPos":
        value = int(args[0]) if args else 0
    else:
        value = 1
    return {"id": light_id, "status": status, "value": value}


class LightThrottle:
    """Per-light rate limiter: send on change immediately, else at most ``rate_hz``.

    "send on change or max 30Hz" (spec Task 5 step 1). A value change flushes
    at once; unchanged values are still refreshed at the rate boundary so a
    stuck light never goes silent.
    """

    def __init__(self, rate_hz=RATE_LIMIT_HZ, clock=time.monotonic):
        self.rate_hz = rate_hz
        self.clock = clock
        self._last = {}
        self._next = {}

    def should_send(self, light_id, location, intensity, now=None):
        if now is None:
            now = self.clock()
        value = (round(clamp01(location), 6), round(clamp01(intensity), 6))
        changed = value != self._last.get(light_id)
        due = now >= self._next.get(light_id, 0.0)
        if changed or due:
            self._last[light_id] = value
            self._next[light_id] = now + (1.0 / self.rate_hz)
            return True
        return False
