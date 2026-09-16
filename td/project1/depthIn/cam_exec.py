"""Per-camera enable glue for the `depthIn` COMP (Script CHOP / callbacks).

Reads `cameras.tsv` and reports which sub-COMPs are enabled so the merge build
can toggle each `camN` output. The Transform/Merge/Render math is all native
TD; here we only resolve the TSV row into the per-cam params a Transform POP's
custom parameter binds to (via the `depth_logic` helpers). In TD this script
CHOP drives the `enabled` toggles on each `camN` sub-COMP and reads the
`clipMin`/`clipMax` params for the band clip.

In TouchDesigner, `depth_logic` is a sibling Text DAT (like `targets_exec` uses
`mod("target_logic")`); `load_cameras` takes the resolved path to `cameras.tsv`.
"""

try:
    import depth_logic  # TD: sibling Text DAT
except ImportError:
    from . import depth_logic  # pytest: package path


def load_cameras(tsv_path):
    """Return per-camera param dicts from a cameras.tsv path, or {} if unreadable."""
    try:
        with open(tsv_path, "r", encoding="utf-8") as f:
            return depth_logic.parse_cameras(f.read())
    except OSError:
        return {}
