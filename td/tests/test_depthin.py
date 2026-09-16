from project1.depthIn import depth_logic

HEADER = "id\tenabled\ttx\tty\ttz\trx\try\trz\tscale\n"

# Sample row: cam1 enabled, full transforms in meters/degrees, scale 1.0.
ROW = "cam1\t1\t-0.5\t0.0\t1.8\t0\t0\t180\t1.0\n"


def _sample_text():
    return HEADER + ROW + "cam2\t0\t0.5\t0.0\t1.8\t0\t0\t0\t1.0\n"


def test_parse_cameras_skips_header_and_returns_numeric_params():
    cams = depth_logic.parse_cameras(_sample_text())
    assert set(cams.keys()) == {"cam1", "cam2"}
    p = cams["cam1"]
    assert p["tx"] == -0.5
    assert p["ty"] == 0.0
    assert p["tz"] == 1.8
    assert p["rx"] == 0
    assert p["ry"] == 0
    assert p["rz"] == 180
    assert p["scale"] == 1.0


def test_parse_cameras_enabled_flag():
    cams = depth_logic.parse_cameras(_sample_text())
    assert cams["cam1"]["enabled"] is True
    assert cams["cam2"]["enabled"] is False


def test_parse_cameras_skips_short_or_malformed_rows():
    text = HEADER + "junk\nshort\tline\n" + ROW
    cams = depth_logic.parse_cameras(text)
    assert set(cams.keys()) == {"cam1"}


def test_parse_cameras_comment_and_blank():
    cams = depth_logic.parse_cameras("# comment\n\n" + HEADER)
    assert cams == {}


def test_parse_cameras_skips_indented_comment_row():
    # Leading-whitespace comment lines must be stripped before the # check.
    cams = depth_logic.parse_cameras(HEADER + "\t# indented comment\n" + ROW)
    assert set(cams.keys()) == {"cam1"}


def test_parse_cameras_tolerates_true_string_enabled():
    cams = depth_logic.parse_cameras(HEADER + "a\ttrue\t0\t0\t1\t0\t0\t0\t1\n")
    assert cams["a"]["enabled"] is True


def test_enabled_cameras_returns_only_enabled_ids():
    cams = depth_logic.parse_cameras(_sample_text())
    assert depth_logic.enabled_cameras(cams) == ["cam1"]


def test_height_band_keeps_in_band_and_rejects_outside():
    assert depth_logic.in_height_band(0.0, -1.0, 1.0)
    assert depth_logic.in_height_band(2.0, -1.0, 1.0) is False
    assert depth_logic.in_height_band(-2.0, -1.0, 1.0) is False
    # band edges are inclusive
    assert depth_logic.in_height_band(-1.0, -1.0, 1.0)
    assert depth_logic.in_height_band(1.0, -1.0, 1.0)


def test_height_band_unconfigured_clip_is_noop():
    assert depth_logic.in_height_band(0.0, None, None)
    assert depth_logic.in_height_band(1e9, None, None)
    assert depth_logic.in_height_band(-1e9, None, None)


def test_load_cameras_from_path(tmp_path):
    import project1.depthIn.cam_exec as ce

    p = tmp_path / "cameras.tsv"
    p.write_text(HEADER + "cam1\t1\t0\t0\t1\t0\t0\t0\t1\n")
    cams = ce.load_cameras(str(p))
    assert cams["cam1"]["enabled"] is True


def test_load_cameras_missing_path_returns_empty(tmp_path):
    import project1.depthIn.cam_exec as ce

    assert ce.load_cameras(str(tmp_path / "nope.tsv")) == {}
