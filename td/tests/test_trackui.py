import os
import tempfile

from project1.trackUI import ui_logic


def test_make_default_tracks_has_eight_lights():
    tracks = ui_logic.make_default_tracks()
    assert len(tracks) == 8
    assert tracks[0]["id"] == 0
    assert tracks[7]["id"] == 7
    assert tracks[0]["ip"] == "192.168.0.100"


def test_track_to_row_and_back():
    track = {"id": 0, "start": [1.0, 2.0], "end": [3.0, 4.0], "ip": "10.0.0.1"}
    row = ui_logic.track_to_row(track)
    assert row == {
        "id": "0",
        "sx": "1.0",
        "sy": "2.0",
        "ex": "3.0",
        "ey": "4.0",
        "ip": "10.0.0.1",
    }
    assert ui_logic.row_to_track(row) == track


def test_save_and_load_tracks_round_trip():
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "tracks.tsv")
        tracks = ui_logic.make_default_tracks()
        tracks[2]["start"] = [11.0, 22.0]
        tracks[2]["end"] = [33.0, 44.0]
        tracks[2]["ip"] = "192.168.0.222"
        ui_logic.save_tracks(path, tracks)
        loaded = ui_logic.load_tracks(path)
        assert loaded[2] == tracks[2]


def test_load_tracks_fills_defaults_for_missing_rows():
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "tracks.tsv")
        with open(path, "w", encoding="utf-8") as f:
            f.write("id\tsx\tsy\tex\tey\tip\n0\t1\t2\t3\t4\t192.168.0.100\n")
        loaded = ui_logic.load_tracks(path)
        assert loaded[0] == {"id": 0, "start": [1.0, 2.0], "end": [3.0, 4.0], "ip": "192.168.0.100"}
        assert loaded[1] == ui_logic.make_default_tracks()[1]


def test_debouncer_requires_delay_after_last_ping():
    d = ui_logic.Debouncer(delay=0.5)
    base = 1000.0
    assert d.ping(now=base) is False
    assert d.check(now=base + 0.3) is False
    assert d.check(now=base + 0.5001) is True
    assert d.check(now=base + 0.6) is False


def test_debouncer_flushes_pending_write_once_even_with_no_further_pings():
    # Regression: a pending debounced write must still flush when the Edit flag
    # toggles off (ui_exec runs `debouncer.check()` before the Edit guard), i.e.
    # the flush is driven purely by the debouncer and never needs another event.
    d = ui_logic.Debouncer(delay=0.5)
    base = 1000.0
    d.ping(now=base)
    # edit just turned off, no more drag events — check() fires exactly once.
    assert d.check(now=base + 0.6) is True
    # follow-up cooks (edit still off) must not re-write.
    assert d.check(now=base + 0.7) is False
    assert d.check(now=base + 1.0) is False


def test_debouncer_resets_on_new_ping():
    d = ui_logic.Debouncer(delay=0.5)
    base = 1000.0
    d.ping(now=base)
    assert d.check(now=base + 0.49) is False
    d.ping(now=base + 0.49)
    assert d.check(now=base + 0.99) is False
    assert d.check(now=base + 1.0) is True


def test_pending_write_flushes_then_stays_flushed_without_edit_gate():
    # Regression: ui_exec runs debouncer.check() every cook, before the Edit guard,
    # so a pending write flushes even when Edit toggles off. After that single flush
    # the debouncer must not re-fire on later cooks until a new ping, or the edit-off
    # path would write the TSV every frame. The Debouncer is not edit-aware: flushing
    # depends only on elapsed time.
    d = ui_logic.Debouncer(delay=0.5)
    base = 1000.0
    d.ping(now=base)
    assert d.check(now=base + 0.5001) is True          # the late flush (edit off)
    for t in (base + 0.6, base + 0.7, base + 2.0):     # subsequent cooks stay idle
        assert d.check(now=t) is False
    d.ping(now=base + 2.0)                              # a new drag re-arms it
    assert d.check(now=base + 2.5001) is True


def test_tracks_to_dat_text_and_back():
    tracks = ui_logic.make_default_tracks()
    text = ui_logic.tracks_to_dat_text(tracks)
    assert text.startswith("id\tsx\tsy\tex\tey\tip\n")
    parsed = ui_logic.dat_text_to_tracks(text)
    assert parsed == tracks


def test_dat_text_to_tracks_ignores_extra_columns():
    text = "id\tsx\tsy\tex\tey\tip\n0\t1\t2\t3\t4\t192.168.0.100\n"
    parsed = ui_logic.dat_text_to_tracks(text)
    assert parsed[0] == {"id": 0, "start": [1.0, 2.0], "end": [3.0, 4.0], "ip": "192.168.0.100"}
