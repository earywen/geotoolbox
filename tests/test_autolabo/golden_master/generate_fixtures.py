import sys
import os
import pandas as pd
import json
import hashlib
from datetime import datetime
from freezegun import freeze_time

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../../../"))
sys.path.insert(0, project_root)

from modules.autolabo import process_and_export

# Configuration
FIXTURES_DIR = os.path.join(current_dir, "fixtures")
HASHES_FILE = os.path.join(current_dir, "golden_master_hashes.json")

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def generate_agrolab_eaux_sample(path):
    """Generates a sample Agrolab Eaux Excel file."""
    # Agrolab Config:
    # Date row search "Date". Name row + 2.
    # Raw Code Col: 2.
    # We use param code "180" (pH).
    
    # Structure:
    # Row 0: "Date d'échantillonnage" | | | "20230101"
    # Row 1: empty
    # Row 2: "Paramètre" | | | "PZ1" (Sample)
    # Row 3: Headers
    # Row 4: Data
    
    data = [
        ["Date d'échantillonnage", "", "", "20230101"],
        ["", "", "", ""],
        ["Paramètre", "", "", "PZ1"],
        ["Header1", "Header2", "Code", "Header3"],
        ["pH", "", 180, 7.5] 
    ]
    
    df = pd.DataFrame(data)
    # Write without header to get exact layout
    df.to_excel(path, header=False, index=False)
    print(f"Generated {path}")

def generate_eurofins_eaux_sample(path):
    """Generates a sample Eurofins Eaux Excel file (Legacy format)."""
    # Legacy Eaux:
    # Search "Date" and "chantillon".
    # Date row idx. Name row idx = date + 2.
    
    data = [
        ["Date d'échantillonnage", "01/01/2023"],
        ["", ""],
        ["Nom d'échantillon", "PZ_Euro"],
        ["Paramètre", "Résultat"],
        ["pH", 7.2]
    ]
    
    df = pd.DataFrame(data)
    df.to_excel(path, header=False, index=False)
    print(f"Generated {path}")

def generate_agrolab_sols_sample(path):
    """Generates a sample Agrolab Sols Excel file."""
    # Agrolab Sols Config:
    # Date row: 0, Name row: 2. Data start: 13.
    # Raw Keys in Col 2.
    
    # We need enough rows to reach Data Start Row 13
    # Row 0: Date
    # Row 2: Names
    # Row 13: Data
    
    data = [[""] * 5 for _ in range(15)] # Init empty grid
    
    # Dates (Row 0)
    data[0][0] = "Date" 
    data[0][3] = "20230101" # Sample 1
    
    # Names (Row 2) - Config excludes "Nom d'échantillon"
    data[2][0] = "Nom d'échantillon"
    data[2][3] = "Sondage_Agro"
    
    # Data (Row 13)
    # Col 2 must contain the Code. Ref uses internal code.
    # Let's use a known Code from Ref or Virtual Row?
    # Virtual Row 13906 (PCB) uses component 1594.
    # Let's use Code 1594 (PCB 28)
    data[13][2] = 1594
    data[13][3] = 0.05
    
    df = pd.DataFrame(data)
    df.to_excel(path, header=False, index=False)
    print(f"Generated {path}")


def calculate_file_hash(path):
    """Calculates SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(path, "rb") as f:
        # Read and update hash string value in blocks of 4K
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def main():
    ensure_dir(FIXTURES_DIR)
    
    fixtures = {
        "agrolab_eaux": os.path.join(FIXTURES_DIR, "agrolab_eaux_sample.xlsx"),
        "eurofins_eaux": os.path.join(FIXTURES_DIR, "eurofins_eaux_sample.xlsx"),
        "agrolab_sols": os.path.join(FIXTURES_DIR, "agrolab_sols_sample.xlsx")
    }
    
    generate_agrolab_eaux_sample(fixtures["agrolab_eaux"])
    generate_eurofins_eaux_sample(fixtures["eurofins_eaux"])
    generate_agrolab_sols_sample(fixtures["agrolab_sols"])
    
    hashes = {}
    
    # Use freeze_time to ensure strict binary reproducibility for xlsxwriter
    with freeze_time("2023-01-01 12:00:00"):
        for key, path in fixtures.items():
            print(f"Processing {key}...")
            provider = key.split("_")[0]
            # Infer matrix from key name
            matrix = "eaux" if "eaux" in key else "sols"
            
            # Output to fixtures dir
            # Note: process_and_export uses 'model_id' arg for matrix (historical naming)
            result = process_and_export([path], model_id=matrix, target_path=FIXTURES_DIR, provider_id=provider)
            
            if result["success"]:
                out_path = result["output_path"]
                print(f"Success: {out_path}")
                
                baseline_name = f"{key}_baseline.xlsx"
                baseline_path = os.path.join(FIXTURES_DIR, baseline_name)
                
                if os.path.exists(baseline_path):
                    os.remove(baseline_path)
                os.rename(out_path, baseline_path)
                print(f"Renamed to {baseline_path}")
                
                file_hash = calculate_file_hash(baseline_path)
                hashes[key] = file_hash
                print(f"Hash: {file_hash}")
            else:
                print(f"Error processing {key}: {result.get('error')}")

    # Write hashes
    with open(HASHES_FILE, "w") as f:
        json.dump(hashes, f, indent=4)
    print(f"Hashes saved to {HASHES_FILE}")

if __name__ == "__main__":
    main()
