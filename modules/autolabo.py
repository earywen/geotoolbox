from datetime import datetime
import logging
from typing import List, Dict, Any
import os
from . import core

# ==========================================
# META-DONNÉES UI
# ==========================================
TOOL_INFO = {
    "id": "autolabo",
    "name": "AutoLabo",
    "icon": "🧪",
    "description": "Traitement de rapports laboratoires"
}


def preview_file(file_path: str) -> Dict[str, Any]:
    """
    Generate a quick preview/summary of a laboratory file.
    
    Args:
        file_path: Path to the Excel file
        
    Returns:
        Dict with 'samples', 'parameters', 'provider_guess'
    """
    from .autolabo_core.detector import preview_file as _preview
    return _preview(file_path)


def analyze_preview(file_path: str, model_id: str = "es", provider_id: str = "auto") -> Dict[str, Any]:
    """
    Detailed dry-run analysis for Preview UI.
    
    Args:
        file_path: Path to the raw laboratory file
        model_id: Matrix identifier ("es" for eaux, "sols" for sols)
        provider_id: Laboratory provider ID (agrolab, eurofins, or 'auto')
        
    Returns:
        Dict with 'success', 'data' (list of rows) or 'error'
    """
    from .autolabo_core.config.registry import ProviderRegistry
    from .autolabo_core.processors.generic import GenericLabProcessor
    from .autolabo_core.detector import detect_provider
    import logging

    try:
        base = core.get_base_path()
        matrix_map = {"es": "eaux", "sols": "sols"}
        matrix = matrix_map.get(model_id, "eaux")

        # Define reference paths
        ref_paths = {
            "eaux": os.path.join(base, "ressources", "Eaux souterraines", 
                                 "Eaux souterraines familles et paramètres et valeurs réglementaires.xlsx"),
            "sols": os.path.join(base, "ressources", "Sols", 
                                 "Sols - familles et paramètres et valeurs réglementaires.xlsx")
        }
        ref_path = ref_paths.get(matrix)
        if not ref_path or not os.path.exists(ref_path):
            return {"success": False, "error": "Fichier référentiel introuvable"}

        # Provider detection
        current_provider_id = provider_id
        if provider_id == "auto":
            detected = detect_provider(file_path)
            current_provider_id = detected if detected else "agrolab"

        # Load config
        registry = ProviderRegistry()
        provider = registry.load_provider(current_provider_id)
        config = registry.load_matrix(current_provider_id, matrix)

        # Run Preview Analysis
        processor = GenericLabProcessor(file_path, ref_path, config, provider)
        data = processor.preview_analysis()
        
        return {
            "success": True, 
            "data": data, 
            "provider": getattr(provider, "name", current_provider_id)
        }

    except Exception as e:
        logging.error(f"Preview Error: {e}")
        return {"success": False, "error": str(e)}


# --- Entry Point ---
def process_and_export(file_paths: List[str], model_id: str = "es", target_path: str = "", provider_id: str = "agrolab", options: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    API Entry Point for laboratory report processing.

    Supports batch processing: processes all files and returns results for each.

    Args:
        file_paths: List of raw laboratory file paths
        model_id: Matrix identifier ("es" for eaux, "sols" for sols, "sup" for surface)
        target_path: Optional target directory for output
        provider_id: Laboratory provider ID (agrolab, eurofins, or 'auto' for auto-detection)

    Returns:
        Dict with 'success', 'reports' (list of successful outputs), 'errors' (list of failures)
    """
    from .autolabo_core.config.registry import ProviderRegistry
    from .autolabo_core.processors.generic import GenericLabProcessor
    from .autolabo_core.detector import detect_provider

    if not file_paths:
        return {"success": False, "error": "No file", "reports": [], "errors": []}

    base = core.get_base_path()
    
    # Map model_id to matrix name
    matrix_map = {
        "es": "eaux",
        "sols": "sols",
        "sup": "sup"
    }
    matrix = matrix_map.get(model_id, "eaux")

    if matrix == "sup":
        return {"success": False, "error": "Eaux de Surface not impl.", "reports": [], "errors": []}

    # Reference file paths
    ref_paths = {
        "eaux": os.path.join(base, "ressources", "Eaux souterraines",
                             "Eaux souterraines familles et paramètres et valeurs réglementaires.xlsx"),
        "sols": os.path.join(base, "ressources", "Sols",
                             "Sols - familles et paramètres et valeurs réglementaires.xlsx")
    }

    ref_path = ref_paths.get(matrix)
    if not ref_path or not os.path.exists(ref_path):
        return {"success": False, "error": f"Ref not found: {ref_path}", "reports": [], "errors": []}

    # Load registry once
    registry = ProviderRegistry()
    
    # Batch processing results
    reports = []
    errors = []
    out_dir = target_path if target_path and os.path.isdir(target_path) else core.get_user_dir()
    matrix_label = "Sols" if matrix == "sols" else "Eaux"
    
    for i, raw_path in enumerate(file_paths):
        file_name = os.path.basename(raw_path)
        
        # Calculate progress: Start at 10%, end at 90% (final 10% for return)
        progress = 10 + int((i / len(file_paths)) * 80)
        core.dispatch_event('loader_update', {'percent': progress, 'message': f"Traitement {i+1}/{len(file_paths)}: {file_name}"})
        
        # Original granular step event for the sidebar log
        core.dispatch_event('autolabo_step', {'step': f'📂 Fichier {i+1}/{len(file_paths)}: {file_name}'})
        
        try:
            # Auto-detect provider if requested (per-file)
            current_provider_id = provider_id
            if provider_id == "auto":
                detected = detect_provider(raw_path)
                if detected:
                    current_provider_id = detected
                    logging.info(f"Auto-detected provider for {file_name}: {current_provider_id}")
                else:
                    current_provider_id = "agrolab"
                    logging.warning(f"Auto-detection failed for {file_name}, defaulting to AGROLAB")

            # Load config
            provider = registry.load_provider(current_provider_id)
            config = registry.load_matrix(current_provider_id, matrix)
            
            # Process
            processor = GenericLabProcessor(raw_path, ref_path, config, provider)
            
            # Apply options (like active headers from preview)
            if options and "active_headers" in options:
                # Provide a list of INDICES (integers)
                indices = options["active_headers"]
                if indices is not None:
                    processor.set_active_regulatory_headers(indices)

            excel_io = processor.process()
            
            # Save output with unique timestamp per file
            out_name = f"Rapport_{matrix_label}_{i+1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            out_path = os.path.join(out_dir, out_name)
            
            with open(out_path, "wb") as f:
                f.write(excel_io.getvalue())
            
            reports.append({"file": file_name, "output_path": out_path})
            logging.info(f"Report saved: {out_path}")
            
        except Exception as e:
            logging.error(f"Error processing {file_name}: {e}", exc_info=True)
            errors.append({"file": file_name, "error": str(e)})

    # Summary
    success = len(reports) > 0
    if len(file_paths) == 1 and reports:
        # Single file: backward compatible response
        return {"success": True, "output_path": reports[0]["output_path"], "reports": reports, "errors": errors}
    
    return {
        "success": success,
        "reports": reports,
        "errors": errors,
        "summary": f"{len(reports)}/{len(file_paths)} fichiers traités"
    }

# ==========================================
# UI LOADER
# ==========================================
def get_ui_content() -> str:
    """Returns the HTML fragment for the AutoLabo module."""
    return core.load_template("autolabo.html")

if __name__ == "__main__":
    pass
