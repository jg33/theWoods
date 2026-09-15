# Task 1: TD project skeleton + Embody externalization

## Status: DONE

## Files created

- `td/externalizations.tsv` — Embody ledger header row.
- `td/data/tracks.tsv` — empty table with headers `id`, `sx`, `sy`, `ex`, `ey`, `ip`.
- `td/data/cameras.tsv` — empty table with headers `id`, `enabled`, `tx`, `ty`, `tz`, `rx`, `ry`, `rz`, `scale`.
- `td/project1/` — directory for externalized COMPs.
- `td/README.md` — project layout, manual TD setup steps, open instructions.

## What was not done

- `td/theWoods.toe` and the five `.tox` files require TouchDesigner GUI operations; the brief explicitly cannot run TD. README contains the numbered steps.

## Verification

- `ls -la td/ td/data/ td/project1/` confirms directories and TSVs.
- `cat td/data/tracks.tsv` and `cameras.tsv` confirm headers.
- `cat td/externalizations.tsv` confirms ledger header.

## Commit

```bash
git add td/
git -c user.name="Jesse Garrison" -c user.email="jesse@nightlight.io" commit -m "feat(td): project skeleton with externalized COMPs"
```

## Concerns

- `theWoods.toe` does not exist yet and cannot be created from the command line; user must follow the README steps.
- `externalizations.tsv` is a header-only stub; Embody will populate rows once the COMPs are externalized in TD. The brief’s Step 3 says to add rows to `td/externalizations.tsv`; since the workflow is managed by Embody, a template header was written and the README instructs Embody to fill it.
