# Architecture Documentation

> **Status**: Updated for v2.2.0 "Cartographie Unifiée"
> **Date**: 2026-01-24

## 1. High-Level Overview

**Burgeaply** is a hybrid Python/Web desktop application that orchestrates geospatial data extraction and processing.

### Core Stack
- **Frontend**: HTML5/CSS3/native JS (running in Edge WebView2 via PyWebView)
- **Backend**: Python 3.13 (PyWebView Bridge API)
- **Mapping Engine**: Leaflet.js (Frontend) + Leaflet.Draw
- **Geodata Processing**: Python (Shapely, Fiona, Requests)
- **Map Service**: IGN Geoportail (WFS/WMS) & BRGM (WFS)

---

## 2. Directory Structure (Updated)

```
geotoolbox/
├── app.py                      # Main entry point (PyWebView Bridge)
├── modules/
│   ├── core.py                 # Core utilities (Config, Logging, Network)
│   ├── cartographie.py         # [NEW] Unified Orchestrator (Vectors + Rasters)
│   ├── cartographie_core/      # [NEW] Business Logic
│   │   ├── config.py           # Layer definitions
│   │   ├── vector_fetcher.py   # WFS logic (ex-Geotoolbox)
│   │   ├── raster_fetcher.py   # WMS/PVA logic (ex-Orthohisto)
│   │   ├── vector_export.py    # Excel/GeoJSON exporters
│   │   ├── models.py           # Data models
│   │   └── maths.py            # Geometric calculations
│   ├── autolabo.py             # Lab data processing module
│   ├── qgis_export/            # QGIS Project Generation
│   └── updater.py              # Update mechanism
├── assets/
│   ├── index.html              # Main UI Shell
│   ├── js/
│   │   ├── app.js              # Core UI logic
│   │   └── cartographie.js     # [NEW] Unified Map Component
│   └── templates/              # HTML fragments
└── .gsd/                       # Project Memory (Spec, State, Roadmap)
```

---

## 3. Key Data Flows

### A. Data Extraction (Unified)
1. User defines **Emprise** (Polygon) in UI (Leaflet.Draw).
2. `cartographie.js` sends Geometry + Layer Selection to `run_carto_export`.
3. `cartographie.py` orchestrates:
   - **Vector Data**: Fetched via WFS (BRGM, IGN) -> `vector_fetcher.py`
   - **Raster Data**: Fetched via WMS/API (PVA, Mosaics) -> `raster_fetcher.py`
   - **Geometrics**: Distance/Slope relative to center.
4. **Export**:
   - Organized into `vecteurs/`, `orthophotos/`, `rapport/`.
   - QGIS Project (`.qgz`) generated via `qgis_export/`.

### B. QGIS Integration
- The application acts as a "Pre-processor" for QGIS.
- It generates a `.qgz` file that references the downloaded local files using relative paths.
- **Layers Supported**:
  - Vector: GeoJSON (Points, Polygons) with custom styling.
  - Basic: Basemaps (XYZ Tiles).
  - Raster: Standard Images (PNG/JPG + Worldfile).

---

## 4. Configuration

- **Global Config**: `modules/core.py` handles `config.json` loading.
- **Layer Config**: `cartographie_core/config.py` defines all available layers (Color, WFS URL, Fields).
- **Secrets**: API Keys (if any) are managed in environment variables or `config.json` (git-ignored in production).

## 5. Deployment

- Built with **PyInstaller**.
- `version.py` tracks build version.
- `updater.py` checks for new versions on GitHub Releases.
