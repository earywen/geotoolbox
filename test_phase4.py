
import os
import sys
import logging
import shutil

# Setup paths
base_path = os.path.dirname(os.path.abspath("."))
sys.path.append(base_path)

from modules.cartographie import run_export_logic
from modules.cartographie_core import LAYERS_CONFIG

# Configure logging
logging.basicConfig(level=logging.INFO)

class MockReporter:
    def update(self, pct, msg):
        print(f"[PROGRESS] {pct}% - {msg}")

def run_test():
    print("=== STARTING PHASE 4 EXPORT TEST ===")
    
    # Fake BBOX (Centre of Paris approx)
    bbox = {
        'min_lat': 48.85, 'max_lat': 48.86,
        'min_lon': 2.34, 'max_lon': 2.35
    }
    
    # Fake Site Polygon (GeoJSON geometry)
    emprise = {
        "type": "Polygon",
        "coordinates": [[
            [2.34, 48.85], [2.35, 48.85], [2.35, 48.86], [2.34, 48.86], [2.34, 48.85]
        ]]
    }
    
    base_ui = os.path.join(os.getcwd(), "test_export_output")
    if os.path.exists(base_ui):
        shutil.rmtree(base_ui)
    os.makedirs(base_ui)
    
    options = {
        'include_vectors': True,
        'include_rasters': False, # Skip heavy downloads for quick test
        'include_emprise': True,
        'generate_qgis': True
    }
    
    # We only test a subset of layers to be fast
    # BSS is usually reliable for testing if WFS is up, or we can mock it
    # For this test, we accept if it tries and maybe fails wfs, but checking folder structure is key
    layers = ["BSS"] 
    
    result = run_export_logic(
        bbox=bbox,
        layers_list=layers,
        folder_name="Test_Export_Phase4",
        base_path_ui=base_ui,
        options=options,
        reporter=MockReporter(),
        emprise_geojson=emprise
    )
    
    print("\n=== VERIFICATION RESULTS ===")
    root = result['folder']
    print(f"Export Root: {root}")
    
    expected_structure = [
        "vecteurs/emprise_site.geojson",
        "vecteurs/BSS.geojson",
        "rapport/BSS.xlsx",
        "etude_geotoolbox.qgz"
    ]
    
    all_good = True
    for p in expected_structure:
        full_p = os.path.join(root, p)
        exists = os.path.exists(full_p)
        status = "✅" if exists else "❌"
        if not exists: all_good = False
        print(f"{status} {p}")
        
    if all_good:
        print("\nSUCCESS: Export structure is valid.")
    else:
        print("\nFAILURE: Missing expected files.")

if __name__ == "__main__":
    run_test()
