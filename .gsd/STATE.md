# STATE.md — Project Memory

> Last updated: 2026-01-24T17:30:00+01:00

## Current Position

- **Phase:** Phase 6 — Améliorations UI
- **Milestone:** v2.2.0 "Cartographie Unifiée"
- **Status:** IN PROGRESS

---

## Final Project Status

The "Cartographie Unifiée" refactor is complete.

- **Frontend**: Unified specific mapped UI (Cartographie). Legacy files removed.
- **Backend**: Unified `cartographie.py`. Legacy modules removed.
- **Features**:
  - Polygon Drawing (Leaflet.Draw)
  - Vector WFS Fetching
  - Raster PVA/Mosaic Downloading
  - Unified Folder Export
  - Auto-generated QGIS Project (.qgz)

---

## Next Steps

1. **Release v2.2.0**:
   - Update README/CHANGELOG (user action pending).
   - Bump Version in `version.py`.
   - Build EXE.

2. **Future Milestones**:
   - Add new layers (ARIA, etc.)
   - Report PDF generation.
