# Task 5 Report — `network` COMP (OSC to nodes + Max/UE mirrors + inbound status)

Date: 2026-09-16

## Status: DONE

## Summary

Built the `network` COMP for the TD port: outbound OSC position/intensity
unicast to each node IP, identical message mirrors to Max + Unreal listen ports,
a 1s `/ping` heartbeat, and inbound node status parsing into a `nodeStatus` DAT.

## Files

- `td/project1/network/net_logic.py` — TD-free logic (builds messages, rate-limits,
  parses inbound status). No TD imports; importable by tests.
- `td/project1/network/net_exec.py` — thin TouchDesigner glue (Script CHOP/DAT callbacks).
- `td/tests/test_network.py` — 19 unit tests.
- `td/README.md` — appended `## network COMP` build instructions (numbered) with the
  OSC contract table.

## What was built

### Step 1 — OSC out
`net_logic.node_messages(id, location, intensity)` produces the spec addresses
`/light/<n>/position <float 0-1>` and `/light/<n>/intensity <float 0-1>`, clamped
to 0–1. `net_exec.onCook` (a Script CHOP, `sendcook`) reads the `lights` DAT
(input 0) and `tracks` DAT (input 1) for per-node IPs, then sends **unicast** to
each node's IP by setting `oscOut.par.hostname = ip` + `sendOSC`. Sending is
gated by `LightThrottle`: **send on value change immediately, else at most 30Hz
(refresh at the rate boundary)** — exactly the "send on change or max 30Hz" rule.
Control messages `/light/<n>/identify|calibrate|zero|stop|move` are built by
`net_logic.control_message`.

### Step 2 — OSC in + ping
`net_exec.onReceiveOSC` parses inbound node status via
`net_logic.parse_node_status`, which maps `/light/<n>/minTrigger|maxTrigger`
(limit-switch hits, value 1) and `/light/<n>/maxPos <int>` (calibrated max
position) into `{id, status, value}` rows; `ping` and outgoing addresses are
ignored (return `None`). Reports accumulate in `nodeStatus` Table DAT
(`id, status, value`). The `/ping <int>` heartbeat is sent every 1s (wall-clock
self-paced in `onCook`), broadcast via `oscOutBcast` or unicast per node when no
bcast DAT is wired — `net_logic.ping_message` produces it.

### Step 3 — mirrors
`net_exec._mirror` re-sends **every** outgoing `/light/*` message verbatim to the
Max and Unreal listen IPs/ports when the `mirrorMax` / `mirrorUnreal` toggles are
on (each with IP + port par). Max becomes a pure listener for the composer's
soundscape; Unreal sniffs the same bus.

### Parameters (`onSetupParameters`)
`Listenport` (8899), `Sendrate` (30 Hz ceiling), `Nodeport` (9999),
`Mirrormax`(+ip+port), `Mirrorunreal`(+ip+port).

## Notes on an artifact found during execution

A partially-built `net_logic.py` already existed and exposed a *different* API
(`parse_incoming`/`light_messages`/`RateLimiter`) than the on-disk unit tests
and glue (`parse_node_status`/`node_messages`/`LightThrottle`). I made the
`net_logic.py` and `net_exec.py` consistent with the passing test contract
(added `__pycache__` was stale from an earlier build). All 57 tests pass.

## Verification

```
uv run --with pytest pytest td/tests/  => 57 passed
```

- `test_network.py`: 19 passed (message addresses/clamping, control variants,
  ping format, status parsing incl. `None`/missing-arg fallbacks, throttle
  send-on-change / rate-limit / boundary-refresh / per-light independence).

## Commit

- `ed2cc77` feat(td): network COMP — OSC to nodes + Max/UE mirrors
  (signed as Jesse Garrison <jesse@nightlight.io>)

Could not run TouchDesigner / the real test-listener end-to-end check (Step 3 of
the brief) in this environment; the message contract is exercised headless by
the unit tests instead.

---

## Fix Report (task 5 follow-up: throttle gating dropped the intensity message)

### Status

Done. Fixed a per-frame OSC drop bug; added a regression test; suite green.

### Bug

In `net_exec.onCook`, the `LightThrottle.should_send()` gate was checked **inside**
the per-address loop but keyed **per light id**. Since `node_messages()` yields two
addresses for one light (`/light/<n>/position` and `/light/<n>/intensity`), the
position message consumed the "send on change" slot and the immediately-following
intensity message hit the rate-limit → **intensity was dropped on nearly every
cook**, only (re)sending when the per-light value crossed a change again.

### Fix

- `td/project1/network/net_exec.py` — hoist the `should_send()` decision to **once per
  light**, then emit both position and intensity within that slot.
- `td/tests/test_network_exec.py` — new glue regression test
  `test_single_cook_sends_both_position_and_intensity`: stubs `net_logic`, `op`,
  `lights`/`tracks` DATs and a fake OSC Out, asserts a single cook sends both
  `/light/3/position` and `/light/3/intensity`.

### Test summary

`uv run --with pytest pytest td/tests/ -q` → **58 passed** (57 prior + 1 regression).

### Commit

- `fix(td): network throttle gates per light so intensity isn't dropped on every cook`
