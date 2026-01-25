# STATE.md — Project Memory

> Last updated: 2026-01-25

## Current Position

- **Phase:** Phase 7 — Debugging Missing Layers
- **Milestone:** v2.2.1 "Hotfix WFS Layers"
- **Status:** COMPLETED

---

## Accomplishments

- **Debug**: Fixed missing ZNIEFF/NATURA/PPRI layers export.
  - Implemented WFS 1.1.0 support for INPN.
  - Patched GML Parser for `featureMembers`.
  - Corrected Layer Names and Configs.
  - Added Regression Test `tests/test_vector_fetcher_layers.py`.

- **Deploy**: 
  - Changes pushed to `dev-2`.

---

## Next Steps

1. **Release v2.2.1**:
   - Merge `dev-2` to `main` (pending approval).
   - Build new EXE for production.
