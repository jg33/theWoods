# SDD ledger — plan: docs/superpowers/plans/2026-09-15-td-port.md
Pre-flight scan: interfaces consistent (targets/tracks/lights DAT schemas, OSC map). Ruling: T1/T4/T6 contain TD-GUI steps subagents cannot perform — implementers produce code + precise build instructions; user does TD assembly. Cost if wrong: tasks report DONE but need manual TD steps.
Task 1: complete (commits 29165cf..e79705d, review clean)
Task 1: minor (deferred): README conflates project1/ fs dir vs network path — clarify when .toe built; verify externalizations.tsv header against Embody schema on first run.
Task 2: fix round 1/5 (Important: Blob Track channel layout + silent fail — addressed; minors: pycache, dead branch; commits 7b5195d..fc141fa)
Task 2: fix round 2/5 (Important: None-iteration crash in error path — addressed w/ regression test; minors: crc32 label, ponytail comment; commits fc141fa..4c3a14a)
Task 2: complete (commits e79705d..4c3a14a, review clean)
Task 2: minor (deferred): regression test re-implements onCook loop inline — may drift; extract testable helper if onCook grows.
Task 3: Ruling: reviewer-tier subagents failed 6x on provider TTFB timeout — dispatched @explore for the task review instead of @reviewer. Cost if wrong: review done by a cheaper tier, may miss subtle issues; re-review at final whole-branch gate with most capable model.
Task 3: fix round 1/5 (Important: per-light params indexed by track id w/ non-contiguous test — addressed; minors: redundant mid, elapsed comment; commits 92eaac2..49bafbb)
Task 3: complete (commits 4c3a14a..49bafbb, review clean)
Task 4: fix round 1/5 (F1 TSV path, F2 debounce-before-edit-guard, F4 dead code, F6 vacuous guard — all addressed; commits 0cd918a..7da498b)
Task 4: Ruling: subagent dispatches failed 8x consecutively (provider cancels) — applied the 4 mechanically-specified fixes in controller session, then scoped re-review via @reviewer (dispatch had recovered). Cost if wrong: fixes went unreviewed by implementer-fresh-eyes, but re-review verified all four + no new breakage.
Task 4: minor (deferred): test_trackui_exec.py uses bare assignment stub instead of monkeypatch (test pollution risk); 4 near-duplicate regression tests.
Task 4: complete (commits 5f00e0b..7da498b, review clean)
Task 5: fix round 1/5 (3 Critical TD-API breaks: onReceiveOSC arity, par.address, DAT lookups; Important: per-light throttle, unicast port, ping seq; minors: status keying, dead param, drop logging — all 9 ADDRESSED; commits ed2cc77..41c32e8)
Task 5: minor (deferred): `op(...) if op` NameError outside TD (cosmetic); _tracks_by_id log says "light" not "track".
Task 5: complete (commits 7da498b..41c32e8, review clean)
Task 5: Ruling: multiple dispatches cancelled mid-run but completed work anyway — controller verified each partial result on disk before proceeding, committed orphaned work with attribution. Cost if wrong: commit boundaries blur, but diffs were reviewed as a whole.
Task 6: fix round 1/5 (Important: Delete POP clip naming, Geo COMP render path in README; minors: Out POP/output count, docstring, indented comments, dup-id note — all ADDRESSED; commits 3ef3efc..17dd7c5)
Task 6: minor (deferred): README doesn't show how cam_exec resolves cameras.tsv path inside TD.
Task 6: complete (commits 41c32e8..17dd7c5, review clean)
Task 7: complete (commit 0418a22). Firmware forestLight_wifi_v2: plain-text UDP -> CNMAT OSC, matching network COMP map (listen 9999, report 8899). Hardware logic preserved verbatim; only wire protocol changed. NODE_ID define added per-node. Not compiled (no toolchain); verified by reading. Bench test Step 2 deferred — no hardware.
