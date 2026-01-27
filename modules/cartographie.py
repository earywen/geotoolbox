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
    LAYER_CATEGORIES,
    PRESET_PROFILES,
    ExportOptions,
    RASTER_CONFIG,
    fetch_features,
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

    # Parallel Execution
    with ThreadPoolExecutor(max_workers=12) as executor:
        future_to_layer = {
            executor.submit(fetch_features, layer_key, bbox, mode='preview'): layer_key 
            for layer_key in layers_list 
            if LAYERS_CONFIG.get(layer_key)
        }

        completed_count = 0
        total_count = len(future_to_layer)

        for future in as_completed(future_to_layer):
            layer_key = future_to_layer[future]
            config = LAYERS_CONFIG[layer_key]
            
            completed_count += 1
            pct = int((completed_count / total_count) * 100)
            reporter.update(pct, f"Chargement {config['label']}...")

            try:
                rows = future.result()
            except Exception as e:
                logging.error(f"Preview Error {layer_key}: {e}")
                rows = []

            preview_items: List[Dict[str, Any]] = []
            name_k = config["name_field"].lower()

            for r in rows:
                if isinstance(r, dict):
                    props = r.get('properties', {})
                else:
                    props = r.properties
                lat = props.get('LATITUDE_APPROX', 0)
                if isinstance(lat, (int, float)) and lat > 35: pass
                elif 'LATITUDE_APPROX' not in props: pass
                else: continue
                
                raw_nom = props.get(name_k)
                if not raw_nom or str(raw_nom).strip() == "" or raw_nom == "None":
                    raw_nom = props.get('bss_id') or props.get('code_bss') or r.id or "Sans nom"

                preview_items.append({
                    "nom": str(raw_nom),
                    "color": config["color"],
                    "geometry": r.geometry,
                    "details": props.get('niveau_eau_scrappe')
                })

            results.append({
                "key": layer_key,
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
    emprise_geojson: Optional[Dict[str, Any]] = None,
    radius_geojson: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Executes the full export logic for vectors and rasters.
    
    Args:
        bbox: Bounding box for data extraction
        layers_list: Vector layers to export
        folder_name: Export folder name
        base_path_ui: Base path from UI
        options: Export options
        reporter: Progress reporter
        emprise_geojson: Optional site boundary polygon
        radius_geojson: Optional search radius polygon
        
    Returns:
        Export summary with folder path and results
    """
    opts = ExportOptions()
    if options:
        opts.include_vectors = options.get('include_vectors', True)
        opts.include_rasters = options.get('include_rasters', True)
        opts.include_emprise = options.get('include_emprise', True)


    path = _prepare_export_directory(folder_name, base_path_ui)
    summary: List[Dict[str, Any]] = []
    geojson_paths: List[str] = []

    if reporter is None:
        reporter = CoreEventReporter()

    # --- ÉTAPE 0 : EXPORT EMPRISE & RAYON ---
    vector_files_for_qgis = []
    vecteurs_dir = os.path.join(path, "vecteurs")
    os.makedirs(vecteurs_dir, exist_ok=True)
    
    if opts.include_emprise and emprise_geojson:
        # Manually save export
        final_emp_path = _export_emprise(emprise_geojson, vecteurs_dir) 
        
        if final_emp_path:
            # Generate Style for Emprise (Contour Rouge Épais, Fond Transparent)
            try:
                from modules.qgis_export.style_generator import generate_qml_polygon
                emp_qml = final_emp_path.replace('.geojson', '.qml')
                generate_qml_polygon(emp_qml, color='#ef4444', outline_color='#ef4444', outline_width=0.8, opacity=0, fill_style='no')
            except ImportError as e:
                logging.error(f"Could not gen emprise style: {e}")
                
            summary.append({"status": "success", "layer": "Emprise du site", "type": "emprise"})
            vector_files_for_qgis.append(final_emp_path)

    # Export Radius if available
    if radius_geojson:
        try:
            import json
            radius_path = os.path.join(vecteurs_dir, "rayon_recherche.geojson")
            
            geojson_feature = {
                "type": "FeatureCollection",
                "features": [{
                    "type": "Feature",
                    "properties": {
                        "name": "Rayon de recherche",
                        "created": datetime.now().isoformat()
                    },
                    "geometry": radius_geojson
                }]
            }
            
            with open(radius_path, 'w', encoding='utf-8') as f:
                json.dump(geojson_feature, f, ensure_ascii=False, indent=2)

            # Style for Radius (Dashed Blue Line, Transparent Fill)
            try:
                from modules.qgis_export.style_generator import generate_qml_polygon
                radius_qml = radius_path.replace('.geojson', '.qml')
                # We need to support 'dashed' line style in style_generator if possible, 
                # but for now we'll use a standard solid blue line of different shade
                generate_qml_polygon(radius_qml, color='#0ea5e9', outline_color='#0ea5e9', outline_width=0.6, opacity=0.1, fill_style='solid')
            except ImportError:
                pass

            summary.append({"status": "success", "layer": "Rayon de recherche", "type": "vector"})
            vector_files_for_qgis.append(radius_path)
            logging.info(f"[Cartographie] Rayon exporté: {radius_path}")

        except Exception as e:
            logging.error(f"Error exporting radius: {e}")

    # --- ÉTAPE 1 : ANALYSE GLOBALE (0-10%) ---
    if opts.include_vectors and layers_list:
        logging.info("--- DÉBUT ANALYSE GLOBALE ---")
        try:
            slope_azimut, z_center = _perform_global_analysis(bbox, reporter)
        except Exception as e:
            logging.error(f"Global analysis failed: {e}")
            slope_azimut, z_center = 0, 0

        # --- ÉTAPE 2 : BOUCLE SUR LES COUCHES VECTORIELLES (10-50%) ---
        total_layers = len(layers_list)
        
        # Prepare subfolders
        vecteurs_dir = os.path.join(path, "vecteurs")
        rapport_dir = os.path.join(path, "rapport")
        os.makedirs(vecteurs_dir, exist_ok=True)
        os.makedirs(rapport_dir, exist_ok=True)

        layers_data = {}
        for i, layer_key in enumerate(layers_list):
            config = LAYERS_CONFIG.get(layer_key)
            if not config:
                continue

            progress_start = 10 + int((i / total_layers) * 40)
            msg = f"Traitement {config['label']}..."
            reporter.update(progress_start, msg)

            try:
                rows = fetch_features(layer_key, bbox, mode='export')
                # Compatibilité: Convertir les objets GeoFeature en dicts plats pour maths.py et pandas
                rows = [r.to_ui_dict() if hasattr(r, 'to_ui_dict') else r for r in rows]

                # Optimization: Only calculate topography (Amont/Aval) for specific point layers
                # This avoids hitting IGN API rate limits for massive polygon layers where it's less relevant
                LAYERS_WITH_TOPO = ["BSS", "SSP", "SIS", "ICPE", "SUP", "QUALITO", "PIEZO"]
                
                # Use z_center only if layer needs it, otherwise None (skips IGN API)
                effective_z = z_center if layer_key in LAYERS_WITH_TOPO else None

                if rows and layer_key != "PARCELLE":
                    rows = calculate_geometrics(rows, bbox, slope_azimut, effective_z)

                # Prepare Excel data (accumulate for single file)
                from modules.cartographie_core.vector_export import prepare_layer_export_data
                df_export = prepare_layer_export_data(rows, layer_key, config)
                if df_export is not None:
                    # Accumulate for unified export
                    # Note: layers_data needs to be passed in or initialized before loop.
                    # Since this function scope is complex, we'll initialize it if missing?
                    # No, better refactor: we can't easily change function signature here without broader impact.
                    # But we can assume layers_data dict exists in local scope if we init it before.
                    # Let's check where to init. But wait, we are editing lines 356-435 which is INSIDE the loop.
                    # We need to ensure `layers_data` variable is available. 
                    # Actually, let's step back. We are viewing lines 340-450.
                    # The loop starts at 341. We can't inject `layers_data = {}` before the loop with this ReplaceBlock easily unless we include the line before.
                    pass

                # GeoJSON export (always if rows exist, useful for QGIS even if QGIS opt is False)
                geojson_path = None
                if rows:
                    from modules.qgis_export import export_geojson

                    try:
                        geojson_path = os.path.join(vecteurs_dir, f"{layer_key}.geojson")
                        export_geojson(rows, geojson_path, layer_key)
                        
                        # Generate QML Style based on specific requirements
                        qml_path = os.path.join(vecteurs_dir, f"{layer_key}.qml")
                        
                        from modules.qgis_export.style_generator import (
                            generate_qml_point, 
                            generate_qml_polygon, 
                            generate_qml_line
                        )
                        
                        # Dynamic Style Loading
                        from modules.cartographie_core.config import load_styles
                        styles_cache = load_styles()
                        
                        defaults = styles_cache.get('default', {})
                        layer_styles = styles_cache.get('layers', {})
                        spec_style = layer_styles.get(layer_key, {})
                        
                        # Determine type: Config Style > Layer Config > Default Point
                        ltype = spec_style.get('type') or config.get('type', 'point')
                        
                        # Merge: Default(Type) + Specific
                        final_style = defaults.get(ltype, {}).copy()
                        final_style.update(spec_style)
                        
                        # Clean arguments (remove 'type' if present)
                        final_style.pop('type', None)
                        
                        # Generate based on type
                        if ltype == 'point':
                            generate_qml_point(qml_path, **final_style)
                        elif ltype == 'polygon':
                            generate_qml_polygon(qml_path, **final_style)
                        elif ltype == 'line':
                            generate_qml_line(qml_path, **final_style)
                        else:
                            # Safe fallback
                            generate_qml_point(qml_path, color='#888888')

                        
                        vector_files_for_qgis.append(geojson_path)
                    except ImportError:
                        # Fallback if module structure differs
                        pass
                
                if df_export is not None:
                     layers_data[layer_key] = df_export
                     summary.append({
                        "status": "success", 
                        "layer": config['label'], 
                        "count": len(rows), 
                        "geojson": geojson_path,
                        "type": "vector"
                    })
                        
            except Exception as e:
                logging.exception(f"Error exporting layer {layer_key}: {e}")
                summary.append({"status": "error", "layer": config.get('label', layer_key), "error": str(e)})

    # --- UNIFIED EXCEL EXPORT ---
    if layers_data:
        from modules.cartographie_core.vector_export import generate_unified_excel
        excel_path = generate_unified_excel(layers_data, rapport_dir)
        if excel_path:
             logging.info(f"Unified Excel created: {excel_path}")

    # --- ÉTAPE 3 : EXPORT RASTERS (50-100%) si demandé ---
    raster_files_for_qgis = []
    
    if opts.include_rasters:
        reporter.update(50, "Préparation téléchargement images aériennes...")
        
        # Calculate center for PVA search
        try:
            c_lat = (float(bbox['min_lat']) + float(bbox['max_lat'])) / 2.0
            c_lon = (float(bbox['min_lon']) + float(bbox['max_lon'])) / 2.0
            lat_range = float(bbox['max_lat']) - float(bbox['min_lat'])
            lon_range = float(bbox['max_lon']) - float(bbox['min_lon'])
        except:
             c_lat, c_lon = 0, 0
             lat_range, lon_range = 0.01, 0.01

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
        
        try:
            pva_results = process_all_pva(c_lat, c_lon, ortho_dir, radius_m, 
                                           callback=pva_callback, current_prog=0, progress_range=90)
            
            for res in pva_results:
                if "OK" in res.get('status', ''):
                    summary.append({
                        "status": "success",
                        "layer": f"PVA {res['annee']}",
                        "type": "raster"
                    })
                    # Add to QGIS if valid
                    if os.path.exists(res.get('filename', '')):
                        raster_files_for_qgis.append(res['filename'])
        except Exception as e:
             logging.exception(f"PVA Error: {e}")
        
        # Download mosaics (90-100%)
        reporter.update(90, "Téléchargement mosaïques géoréférencées...")
        
        wms_bbox = f"{c_lat - lat_range/2},{c_lon - lon_range/2},{c_lat + lat_range/2},{c_lon + lon_range/2}"
        bbox_dict = {
            'min_lat': c_lat - lat_range/2,
            'max_lat': c_lat + lat_range/2,
            'min_lon': c_lon - lon_range/2,
            'max_lon': c_lon + lon_range/2
        }
        
        for label, layer in IGN_MOSAICS:  # Try all available mosaics
            fname = os.path.join(ortho_dir, f"{label}_Mosaic.png")
            # Worldfile is implicitly created by download_wms
            result = download_wms(layer, fname, wms_bbox, bbox_dict)
            if result == "OK":
                summary.append({
                    "status": "success",
                    "layer": f"Mosaïque {label}",
                    "type": "raster"
                })
                raster_files_for_qgis.append(fname)
                

    time.sleep(0.5)

    return {
        "folder": path, 
        "summary": summary,
        "vector_count": len([s for s in summary if s.get('type') == 'vector']),
        "raster_count": len([s for s in summary if s.get('type') == 'raster']),
        "has_emprise": any(s.get('type') == 'emprise' for s in summary)
    }


# ==========================================
# 5. API FUNCTIONS FOR UI
# ==========================================
def get_carto_categories_config() -> Dict[str, Any]:
    """
    Returns the categorized layer configuration for the UI.
    
    Structure:
    {
        "categories": { category_key: { label, icon, description, layers: {...} } },
        "profiles": { profile_key: { label, description, layers: [...] } },
        "flatLayers": { layer_key: {...} }  // For backward compatibility
    }
    """
    return {
        "categories": LAYER_CATEGORIES,
        "profiles": PRESET_PROFILES,
        "flatLayers": LAYERS_CONFIG
    }


# ==========================================
# 6. UI LOADER
# ==========================================
def get_ui_content() -> str:
    """Returns the HTML fragment for the Cartographie module."""
    try:
        html = core.load_template("cartographie.html")
        return html 
    except FileNotFoundError:
        return "<div class='placeholder'>Erreur: Template cartographie.html introuvable</div>"

