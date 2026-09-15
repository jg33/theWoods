from project1.tracking.target_logic import update_target


def test_influence_ramps_up():
    t = dict(current=[0.0, 0.0], influence=0.0001, quiet_timer=0, dying=False)
    for _ in range(100):
        t = update_target(t, 100.0, 100.0, True)
    assert t["influence"] == 1.0


def test_dying_drains_influence():
    t = dict(current=[0.0, 0.0], influence=0.005, quiet_timer=0, dying=False)
    for _ in range(10):
        t = update_target(t, 0.0, 0.0, False)
    assert t["ready_to_die"]


def test_quiet_after_threshold():
    t = dict(current=[0.0, 0.0], influence=1.0, quiet_timer=0, dying=False)
    for _ in range(301):
        t = update_target(t, 0.0, 0.0, True)
    assert t["quiet"]


def test_moving_resets_quiet_timer():
    t = dict(current=[0.0, 0.0], influence=1.0, quiet_timer=299, dying=False)
    t = update_target(t, 100.0, 100.0, True)
    assert not t["quiet"]
    assert t["quiet_timer"] == 0


def test_dying_then_seen_revives():
    t = dict(current=[0.0, 0.0], influence=0.5, quiet_timer=0, dying=False)
    t = update_target(t, 0.0, 0.0, False)
    assert t["dying"]
    t = update_target(t, 10.0, 10.0, True)
    assert not t["dying"]
