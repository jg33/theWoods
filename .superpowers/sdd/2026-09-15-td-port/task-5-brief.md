### Task 5: `network` — OSC out + mirrors + inbound status

**Files:**
- Modify: `td/project1/network.tox`
- Create: `td/project1/network/net_exec.py`

**Interfaces:**
- Consumes: `lights` DAT (Task 3), `tracks` DAT (IPs).
- Produces: OSC to nodes `/light/<n>/position|intensity`; mirrors to Max/UE ports; `nodeStatus` DAT from inbound OSC.

- [ ] **Step 1: OSC out**

OSC Out DAT per node (or one DAT, per-row address). `net_exec.py`: on `lights` DAT change (or 30Hz timer), send `/light/<id>/position <locationPercent>` and `/light/<id>/intensity <intensity>` to that light's IP from `tracks` DAT. Params: `mirrorMax` (toggle+IP+port), `mirrorUnreal` — same messages re-sent.

- [ ] **Step 2: OSC in + ping**

OSC In DAT on listen port → parse `/light/<n>/minTrigger|maxTrigger|maxPos` → `nodeStatus` DAT. `/ping` every 1s (Timer CHOP → OSC out broadcast/unicast per node).

- [ ] **Step 3: Verify against a test listener**

`uv run python -c` osc4py3/python-osc listener script printing received messages; confirm format matches spec table. Commit `feat(td): network COMP — OSC to nodes + Max/UE mirrors`.

---

