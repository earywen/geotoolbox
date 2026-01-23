"""
Cartographie Module — Unified Geospatial Data Extraction

This module combines the functionality of GéoToolbox (vector data) and 
OrthoHisto (raster/aerial imagery) into a single, unified workflow.

Features:
- Vector data extraction (BSS, BDLisa, SSP) via WFS
- Historical aerial photographs (PVA) download
- IGN mosaic imagery download
- Unified export with GeoJSON, Excel, and QGIS project generation
- Site boundary polygon export

Author: Laurent BRIGAUD
Version: 2.2.0
"""

import os
import sys
import math
import time
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Protocol
from concurrent.futures import ThreadPoolExecutor, as_completed

from modules import core
from modules.cartographie_core import (
    LAYERS_CONFIG,
    ExportOptions,
    RASTER_CONFIG,
    fetch_features,
    generate_excel_for_layer,
    calculate_geometrics,
    get_local_slope_vector,
    get_elevation_ign_only,
    IGN_MOSAICS,
    download_wms,
    process_all_pva,
    ensure_folder,
)


# ==========================================
# 1. META-DONNÉES
# ==========================================
TOOL_INFO: Dict[str, str] = {
    "id": "cartographie",
    "name": "Cartographie",
    "icon": "🗺️",
    "description": "Données géographiques et photos aériennes"
}


# ==========================================
# 2. PROGRESS REPORTER
# ==========================================
class ProgressReporter(Protocol):
    def update(self, percent: int, message: str) -> None: ...


class CoreEventReporter:
    """Wrapper that dispatches events to the core system."""
    def update(self, percent: int, message: str) -> None:
        core.dispatch_event('loader_update', {'percent': percent, 'message': message})


# ==========================================
# 3. LOGIQUE PREVIEW
# ==========================================
def run_preview_logic(
    bbox: Dict[str, float], 
    layers_list: List[str], 
    reporter: Optional[ProgressReporter] = None
) -> List[Dict[str, Any]]:
    """
    Executes preview logic for selected vector layers within a bounding box.
    Fetches features but does not perform heavy geometric calculations.
    """
    results: List[Dict[str, Any]] = []
    logging.info(f"[Cartographie] Preview: {layers_list}")
    
    if reporter is None:
        reporter = CoreEventReporter()

    for index, layer_key in enumerate(layers_list):
        config = LAYERS_CONFIG.get(layer_key)
        if not config:
            continue

        pct = int((index / len(layers_list)) * 100)
        msg = f"Chargement {config['label']}..."
        reporter.update(pct, msg)

        rows = fetch_features(layer_key, bbox, mode='preview')
        preview_items: List[Dict[str, Any]] = []
        name_k = config["name_field"].lower()

        for r in rows:
            # Basic Latitude Filter
            if r.get('LATITUDE_APPROX', 0) > 35:
                raw_nom = r.get(name_k)
                if not raw_nom or str(raw_nom).strip() == "" or raw_nom == "None":
                    raw_nom = r.get('bss_id') or r.get('code_bss') or r.get('id') or "Sans nom"

                preview_items.append({
                    "nom": str(raw_nom),
                    "color": config["color"],
                    "geometry": r.get('geometry'),
                    "details": r.get('niveau_eau_scrappe')
                })

        results.append({
            "layer": config['label'],
            "count": len(rows),
            "items": preview_items
        })

    # Finalize
    reporter.update(100, 'Affichage...')
    core.dispatch_event('loader_hide', {})

    return results


# ==========================================
# 4. LOGIQUE EXPORT UNIFIÉ
# ==========================================
def _prepare_export_directory(folder_name: Optional[str], base_path_ui: Optional[str]) -> str:
    """Prepares the export directory and returns its path."""
    base_path: str = ""

    if base_path_ui and os.path.isdir(base_path_ui):
        base_path = base_path_ui
    elif getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    folder = folder_name.strip() if folder_name else f"Export_{datetime.now().strftime('%H%M%S')}"
    path = os.path.join(base_path, folder)
    os.makedirs(path, exist_ok=True)
    return path


def _perform_global_analysis(bbox: Dict[str, float], reporter: Optional[ProgressReporter] = None) -> tuple:
    """Performs global analysis (slope, elevation) for the bbox center."""
    if reporter: reporter.update(5, 'Analyse du relief (Pente locale)...')

    try:
        c_lat = (float(bbox['min_lat']) + float(bbox['max_lat'])) / 2.0
        c_lon = (float(bbox['min_lon']) + float(bbox['max_lon'])) / 2.0
    except (KeyError, ValueError, TypeError):
        c_lat, c_lon = 0.0, 0.0

    slope_azimut, _ = get_local_slope_vector(c_lat, c_lon)

    if reporter: reporter.update(10, 'Récupération Altitude de référence...')
    z_center, src_center = get_elevation_ign_only(c_lat, c_lon)

    if z_center:
        logging.info(f"Centre Z={z_center}m ({src_center})")
    
    return slope_azimut, z_center


def _export_emprise(emprise_geojson: Dict[str, Any], folder_path: str) -> Optional[str]:
    """Exports the site boundary polygon to GeoJSON."""
    if not emprise_geojson:
        return None
    
    try:
        import json
        emprise_path = os.path.join(folder_path, "emprise_site.geojson")
        
        geojson_feature = {
            "type": "FeatureCollection",
            "features": [{
                "type": "Feature",
                "properties": {
                    "name": "Emprise du site",
                    "created": datetime.now().isoformat()
                },
                "geometry": emprise_geojson
            }]
        }
        
        with open(emprise_path, 'w', encoding='utf-8') as f:
            json.dump(geojson_feature, f, ensure_ascii=False, indent=2)
        
        logging.info(f"[Cartographie] Emprise exportée: {emprise_path}")
        return emprise_path
        
    except Exception as e:
        logging.error(f"[Cartographie] Erreur export emprise: {e}")
        return None


def run_export_logic(
    bbox: Dict[str, float],
    layers_list: List[str],
    folder_name: Optional[str],
    base_path_ui: Optional[str],
    options: Optional[Dict[str, Any]] = None,
    reporter: Optional[ProgressReporter] = None,
    emprise_geojson: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Executes the full export logic for vectors and rasters.
    
    Args:
        bbox: Bounding box for data extraction
        layers_list: Vector layers to export
        folder_name: Export folder name
        base_path_ui: Base path from UI
        options: Export options (include_vectors, include_rasters, export_qgis, etc.)
        reporter: Progress reporter
        emprise_geojson: Optional site boundary polygon as GeoJSON geometry
        
    Returns:
        Export summary with folder path and results
    """
    opts = ExportOptions()
    if options:
        opts.include_vectors = options.get('include_vectors', True)
        opts.include_rasters = options.get('include_rasters', True)
        opts.include_emprise = options.get('include_emprise', True)
        opts.generate_qgis = options.get('generate_qgis', False)

    path = _prepare_export_directory(folder_name, base_path_ui)
    summary: List[Dict[str, Any]] = []
    geojson_paths: List[str] = []

    if reporter is None:
        reporter = CoreEventReporter()

    # --- ÉTAPE 0 : EXPORT EMPRISE (si fournie) ---
    if opts.include_emprise and emprise_geojson:
        emprise_path = _export_emprise(emprise_geojson, path)
        if emprise_path:
            summary.append({"status": "success", "layer": "Emprise du site", "type": "emprise"})
            geojson_paths.append(emprise_path)

    # --- ÉTAPE 1 : ANALYSE GLOBALE (0-10%) ---
    if opts.include_vectors and layers_list:
        logging.info("--- DÉBUT ANALYSE GLOBALE ---")
        slope_azimut, z_center = _perform_global_analysis(bbox, reporter)

        # --- ÉTAPE 2 : BOUCLE SUR LES COUCHES VECTORIELLES (10-50%) ---
        total_layers = len(layers_list)

        for i, layer_key in enumerate(layers_list):
            config = LAYERS_CONFIG.get(layer_key)
            if not config:
                continue

            progress_start = 10 + int((i / total_layers) * 40)
            msg = f"Traitement {config['label']}..."
            reporter.update(progress_start, msg)

            try:
                rows = fetch_features(layer_key, bbox, mode='export')

                if rows and layer_key != "PARCELLE":
                    rows = calculate_geometrics(rows, bbox, slope_azimut, z_center)

                # Excel export
                fname = generate_excel_for_layer(rows, layer_key, path, config)
                
                # GeoJSON export (for QGIS)
                geojson_path = None
                if opts.generate_qgis and rows:
                    from modules.qgis_export import export_geojson
                    vecteurs_dir = os.path.join(path, "vecteurs")
                    os.makedirs(vecteurs_dir, exist_ok=True)
                    geojson_path = os.path.join(vecteurs_dir, f"{layer_key}.geojson")
                    export_geojson(rows, geojson_path, layer_key)
                
                if fname:
                    summary.append({
                        "status": "success", 
                        "layer": config['label'], 
                        "count": len(rows), 
                        "filename": fname,
                        "geojson": geojson_path,
                        "type": "vector"
                    })
                    if geojson_path:
                        geojson_paths.append(geojson_path)
                        
            except Exception as e:
                logging.error(f"Error exporting layer {layer_key}: {e}")
                summary.append({"status": "error", "layer": config.get('label', layer_key), "error": str(e)})

    # --- ÉTAPE 3 : EXPORT RASTERS (50-100%) si demandé ---
    if opts.include_rasters:
        reporter.update(50, "Préparation téléchargement images aériennes...")
        
        # Calculate center for PVA search
        c_lat = (float(bbox['min_lat']) + float(bbox['max_lat'])) / 2.0
        c_lon = (float(bbox['min_lon']) + float(bbox['max_lon'])) / 2.0
        
        # Estimate radius from bbox
        lat_range = float(bbox['max_lat']) - float(bbox['min_lat'])
        lon_range = float(bbox['max_lon']) - float(bbox['min_lon'])
        radius_m = int(max(lat_range, lon_range) * 111111 / 2)  # Convert to meters
        radius_m = max(radius_m, 500)  # Minimum 500m
        
        # Create orthophotos subfolder
        ortho_dir = os.path.join(path, "orthophotos")
        os.makedirs(ortho_dir, exist_ok=True)
        
        # Download PVA
        def pva_callback(pct, msg):
            # Scale 0-90% of PVA to 50-90% of overall
            scaled_pct = 50 + (pct * 0.4)
            reporter.update(int(scaled_pct), msg)
        
        pva_results = process_all_pva(c_lat, c_lon, ortho_dir, radius_m, 
                                       callback=pva_callback, current_prog=0, progress_range=90)
        
        for res in pva_results:
            if "OK" in res.get('status', ''):
                summary.append({
                    "status": "success",
                    "layer": f"PVA {res['annee']}",
                    "type": "raster"
                })
        
        # Download mosaics (90-100%)
        reporter.update(90, "Téléchargement mosaïques géoréférencées...")
        
        wms_bbox = f"{c_lat - lat_range/2},{c_lon - lon_range/2},{c_lat + lat_range/2},{c_lon + lon_range/2}"
        bbox_dict = {
            'min_lat': c_lat - lat_range/2,
            'max_lat': c_lat + lat_range/2,
            'min_lon': c_lon - lon_range/2,
            'max_lon': c_lon + lon_range/2
        }
        
        for label, layer in IGN_MOSAICS[-3:]:  # Only most recent mosaics
            fname = os.path.join(ortho_dir, f"{label}_Mosaic.png")
            result = download_wms(layer, fname, wms_bbox, bbox_dict)
            if result == "OK":
                summary.append({
                    "status": "success",
                    "layer": f"Mosaïque {label}",
                    "type": "raster"
                })

    reporter.update(100, 'Export terminé !')
    time.sleep(0.5)

    return {
        "folder": path, 
        "summary": summary,
        "vector_count": len([s for s in summary if s.get('type') == 'vector']),
        "raster_count": len([s for s in summary if s.get('type') == 'raster']),
        "has_emprise": any(s.get('type') == 'emprise' for s in summary)
    }


# ==========================================
# 5. UI LOADER
# ==========================================
def get_ui_content() -> str:
    """Returns the HTML fragment for the Cartographie module."""
    try:
        return core.load_template("cartographie.html")
    except FileNotFoundError:
        # Fallback until template is created in Phase 2
        return "<div class='placeholder'>Module Cartographie en construction</div>"
