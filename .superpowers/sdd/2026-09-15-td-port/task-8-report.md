# Task 8 Report — Integration + docs

## Status
Done (with reality-constraint deferrals). Cannot run TouchDesigner in this
environment, so the "wire COMPs in the .toe / run the full chain live" step is
deferred; the exact cross-COMP wiring + stub-camera + listener verification
sequence is captured as an **Integration checklist** in `td/README.md` for the
user to perform in TD. Everything verifiable here (tests + doc coherence) is
verified.

## What changed

- **AGENTS.md** (new file in the worktree — see note below):
  - Repo layout table: added `td/` row — "**Current** TouchDesigner control app —
    the port of forestControl's brains; see `td/README.md`".
  - Conventions & gotchas: `td/` is the new canonical control app; `forestControl/`
    remains (kept) until `td/` is proven live in the gallery.
  - OSC protocol: the design spec
    `docs/superpowers/specs/2026-09-15-td-port-design.md` is referenced as the
    authoritative wire-protocol doc (addresses/args/ports); the legacy OF
    `OscHandler.hpp` values are marked superseded; the firmware command-set line is
    updated to the OSC map (`forestLight_wifi_v2` now speaks OSC, per Task 7).
  - Stack, Architecture, and Building sections extended with the TD port; noted the
    port has real pytest tests (`td/tests/`).
- **td/README.md**: added `## Integration checklist` before the `## Open` section —
  exact cross-COMP wiring (`depthIn.outOverhead → tracking.inOverhead`; `tracking.targets`
  → `control` in0; `trackUI.tracks` → `control` in1 and read by `network`; `control.lights`
  read by `network`; `network.oscIn` listen port `8899`) plus an end-to-end verification
  sequence (Test Pattern stub cams → `outOverhead` non-black → `targets` rows →
  `lights` DAT populates → OSC out to a `python-osc` listener → fake inbound status into
  `nodeStatus`). README per-COMP sections re-read for coherence; port numbers cross-checked
  against the design spec and `net_exec.py` (`Nodeport` 9999, `oscIn` 8899, ping 1s) —
  consistent, no changes needed to existing sections.

## Note on AGENTS.md repo state
`AGENTS.md` is **untracked** in the main repo (only lives in `master`'s working tree) and
does **not** exist in the worktree — git worktrees don't share untracked files. Created it
in the worktree from `master`'s version + the Task 8 deltas and committed it on this branch.
The integrator must carry it into the merged tree. Same caution applies to
`docs/superpowers/` (also untracked, outside the worktree) — the design-spec path that
AGENTS.md references must exist in the merged tree.

## Verification
- `uv run --with pytest pytest td/tests/ -v` → **70 passed** in ~0.08s. No failures.
- README port/address facts cross-checked against the design-spec OSC map and
  `td/project1/network/net_exec.py` (`Nodeport` default 9999, `oscIn` listen 8899,
  ping interval 1s) — matches.

## Commits
- `6d3c85b` — `chore: TD port integration + docs` (2 files, +183/-0:
  AGENTS.md +102, td/README.md +81). Author/committer Jesse Garrison <jesse@nightlight.io>.

## Deferred (cannot be done here — needs live TD + hardware)
- Wire the five COMPs in the .toe and run the full chain live.
- Stub-camera end-to-end run (TD GUI step).
- OSC reaching a real test listener in-TD (the `python-osc` command is provided in the
  README checklist; python-osc itself was not run here since TD isn't running).
- Per task-8 self-review: POP clustering, multicast, Max routing, UE project itself.
