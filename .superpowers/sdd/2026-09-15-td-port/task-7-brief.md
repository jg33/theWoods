### Task 7: Firmware — OSC in `forestLight_wifi_v2`

**Files:**
- Modify: `forestLight_wifi_v2/forestLight_wifi_v2.ino`

**Interfaces:**
- Consumes: OSC per spec address map on UDP 9999 (or firmware's existing port — match spec).
- Produces: OSC status replies to TD listen port.

- [ ] **Step 1: Uncomment CNMAT OSC, map addresses**

Replace plain-text parser: `/light/<n>/position` → stepper move to `arg * maxPos`; `/intensity` → LED PWM; `/identify`, `/calibrate`, `/zero`, `/stop`, `/move` map to existing command handlers. Send `/light/<n>/minTrigger|maxTrigger` on limit hits, `/maxPos` after calibrate.

- [ ] **Step 2: Bench test**

Flash one node; send OSC from TD `network` or a python-osc script; verify move/intensity/limit replies.

- [ ] **Step 3: Commit**

`git commit -m "feat(firmware): OSC command interface in forestLight_wifi_v2"`

---

