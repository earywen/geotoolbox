# STATE.md — Project Memory

> Last updated: 2026-01-25

## Current Position

- **Phase:** Phase 7 — Debugging Missing Layers
- **Milestone:** v2.2.1 "Hotfix WFS Layers"
- **Status:** COMPLETED
- **Hotfix:** Resolved missing `diskcache` dependency (2026-01-26).
- **Optimization:** Removed BDLISA, parallelized preview fetching (12x), reduced WFS timeouts, disabled BSS scrap in preview.
- **Modernization:** Migrated ZNIEFF/NATURA to standard OWSLib (no more Legacy mode).
- **Fix:** Switched `carmen_wfs_url` to HTTPS, fixing ZNIEFF/Natura layers.
- **Dependency:** Installed `pyproj` to fix WFS warnings.
- **Performance:** Fixed CacheManager race condition (5s gain).
- **Feature:** Added interactive layer toggling (check/uncheck) on preview map.
- **Fix:** Forced WFS 2.0.0 for IGN layers (Parcelle/Eau) to resolve empty results.
- **Fix:** Resolved API argument mismatch in `run_carto_export` (added `radius_geojson`).
- **Fix:** Fixed export crash (GeoFeature immutability) & increased Carmen timeout (60s).
- **Fix:** Updated async scraping (BSS/SSP) to handle dictionary data structures correctly.
- **Feature:** Added hover tooltips for preview objects (showing Name + Details).

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
