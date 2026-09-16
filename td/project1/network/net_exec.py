# me - this DAT (for the Script CHOP / DAT this is attached to)
# scriptOp - the operator which is cooking / receiving OSC

# Import net logic from the sibling `net_logic` textDAT inside this COMP.
# In TouchDesigner: mod finds sibling DATs by name when the script lives in a COMP.
if "net_logic" not in globals():
    try:
        net_logic = mod("net_logic")
    except Exception:
        net_logic = None


def onSetupParameters(scriptOp):
    # Outbound routing + mirrors. (Listen port is set directly on the oscIn DAT,
    # not here.)
    scriptOp.appendParInt("Sendrate", label="Send Rate (Hz)", defaultValue=30)
    scriptOp.appendParInt("Nodeport", label="Node Port", defaultValue=9999)
    scriptOp.appendParToggle("Mirrormax", label="Mirror Max")
    scriptOp.appendParStr("Mirrormaxip", label="Max IP", defaultValue="127.0.0.1")
    scriptOp.appendParInt("Mirrormaxport", label="Max Port", defaultValue=9999)
    scriptOp.appendParToggle("Mirrorunreal", label="Mirror Unreal")
    scriptOp.appendParStr("Mirrorunrealip", label="Unreal IP", defaultValue="127.0.0.1")
    scriptOp.appendParInt("Mirrorunrealport", label="Unreal Port", defaultValue=9998)
    return


def onPulse(par):
    return


# --------------------------------------------------------------------------
# Outbound: Script CHOP (`sendcook`). Reads the lights DAT
# (`id, locationPercent, intensity`) from `../control/lights` and the tracks
# DAT (node IPs) from `../trackUI/tracks` directly — Table DATs cannot be wired
# into Script CHOP inputs (CHOP inlets accept CHOP family only), so we look
# them up with op() instead of reading scriptOp.inputs.
# Sends `/light/<n>/position|intensity` unicast to each node's IP (from tracks),
# rate-limited <=30Hz per light, plus mirrors to Max/Unreal listen ports.
# --------------------------------------------------------------------------


def _get_throttle(scriptOp):
    t = scriptOp.fetch("throttle", None)
    if t is None:
        rate = float(getattr(scriptOp.par, "Sendrate", 30))
        t = net_logic.LightThrottle(rate_hz=max(1.0, rate))
        scriptOp.store("throttle", t)
    return t


def _parse_lights(lights_dat):
    rows = []
    if lights_dat is None:
        return rows
    nrows = lights_dat.numRows
    if nrows < 2:
        return rows
    for row in range(1, nrows):
        try:
            rows.append({
                "id": int(lights_dat[row, 0]),
                "locationPercent": float(lights_dat[row, 1]),
                "intensity": float(lights_dat[row, 2]),
            })
        except (ValueError, IndexError):
            try:
                debug("net: skipping malformed lights row %d" % row)
            except NameError:
                pass
            continue
    return rows


def _tracks_by_id(tracks_dat):
    by_id = {}
    if tracks_dat is None:
        return by_id
    nrows = tracks_dat.numRows
    if nrows < 2:
        return by_id
    for row in range(1, nrows):
        try:
            by_id[int(tracks_dat[row, 0])] = str(tracks_dat[row, 5])
        except (ValueError, IndexError):
            # Drop malformed light row but log it so bad data isn't silent.
            try:
                debug("Dropping malformed light row %d" % row)
            except Exception:
                pass
            continue
    return by_id


def onCook(scriptOp):
    if net_logic is None:
        scriptOp.numSamples = 0
        return

    # Script CHOP inlets accept only CHOP-family inputs, so the lights/tracks
    # Table DATs are referenced directly rather than wired in as inputs.
    lights_dat = op("../control/lights") if op else None
    tracks_dat = op("../trackUI/tracks") if op else None
    lights = _parse_lights(lights_dat)
    ip_by_id = _tracks_by_id(tracks_dat)

    osc_out = op("../oscOut") if op else None
    osc_out_bcast = op("../oscOutBcast") if op else None

    throttle = _get_throttle(scriptOp)
    for light in lights:
        lid = light["id"]
        ip = ip_by_id.get(lid)
        if not ip:
            continue
        # Decide send-or-skip ONCE per light, then emit both the position and
        # intensity messages (the throttle is keyed per-light — checking it per
        # address would let the first message consume the slot and drop the second).
        if not throttle.should_send(lid, light["locationPercent"], light["intensity"]):
            continue
        for address, args in net_logic.node_messages(lid, light["locationPercent"], light["intensity"]):
            if osc_out is not None:
                # Unicast to this node: point the OSC Out DAT at its IP.
                osc_out.par.address = ip
                osc_out.par.port = int(getattr(scriptOp.par, "Nodeport", 9999))
                osc_out.sendOSC(address, args)
            _mirror(scriptOp, osc_out_bcast, address, args)

    # 1s /ping heartbeat -> broadcast, or unicast per node when no bcast DAT.
    now = scriptOp.time.seconds if hasattr(scriptOp, "time") else 0.0
    last_ping = scriptOp.fetch("last_ping", 0.0)
    if now - last_ping >= net_logic.PING_INTERVAL:
        scriptOp.store("last_ping", now)
        seq = scriptOp.fetch("ping_seq", 0) + 1
        scriptOp.store("ping_seq", seq)
        address, args = net_logic.ping_message(seq)
        if osc_out_bcast is not None:
            osc_out_bcast.par.address = "255.255.255.255"
            osc_out_bcast.par.port = int(getattr(scriptOp.par, "Nodeport", 9999))
            osc_out_bcast.sendOSC(address, args)
        elif osc_out is not None:
            for ip in ip_by_id.values():
                osc_out.par.address = ip
                osc_out.par.port = int(getattr(scriptOp.par, "Nodeport", 9999))
                osc_out.sendOSC(address, args)

    scriptOp.numSamples = 1
    scriptOp.appendChan("sent")[0] = 1.0
    return


def _mirror(scriptOp, osc_out_bcast, address, args):
    """Re-send the same OSC message to Max and Unreal listen ports when enabled."""
    if osc_out_bcast is None:
        return
    targets = []
    if bool(scriptOp.par.Mirrormax):
        targets.append((str(scriptOp.par.Mirrormaxip), int(scriptOp.par.Mirrormaxport)))
    if bool(scriptOp.par.Mirrorunreal):
        targets.append((str(scriptOp.par.Mirrorunrealip), int(scriptOp.par.Mirrorunrealport)))
    for host, port in targets:
        osc_out_bcast.par.address = host
        osc_out_bcast.par.port = port
        osc_out_bcast.sendOSC(address, args)


# --------------------------------------------------------------------------
# Inbound: OSC In DAT (`oscIn`). Parses node status reports into `nodeStatus`.
# --------------------------------------------------------------------------


def onReceiveOSC(dat, rowIndex, message, bytes, timeStamp, address, args, peer):
    if net_logic is None:
        return
    status = net_logic.parse_node_status(address, args)
    if status is None:
        return
    log = dat.fetch("status_log", None)
    if log is None:
        log = {}
    # Key by (id, status) so a later report for the same status overwrites its
    # row but distinct statuses for one node are kept alongside each other.
    log[(status["id"], status["status"])] = status
    dat.store("status_log", log)
    _write_node_status(dat, log)


def _write_node_status(dat, log):
    node_status_dat = op("../nodeStatus") if op else None
    if node_status_dat is None:
        return
    rows = [log[k] for k in sorted(log)]
    node_status_dat.setSize(1 + len(rows), 3)
    node_status_dat[0, 0] = "id"
    node_status_dat[0, 1] = "status"
    node_status_dat[0, 2] = "value"
    for i, r in enumerate(rows, start=1):
        node_status_dat[i, 0] = str(r["id"])
        node_status_dat[i, 1] = str(r["status"])
        node_status_dat[i, 2] = str(r["value"])
