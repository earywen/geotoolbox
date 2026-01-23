"""
Auto-detection of laboratory provider from file structure.

Analyzes Excel file headers to identify if the file comes from
AGROLAB, EUROFINS, or other supported providers.
"""

import logging
from typing import Optional, Dict, List
import pandas as pd

logger = logging.getLogger(__name__)

# Signature patterns for each provider
# These are column names that uniquely identify a provider's file format
PROVIDER_SIGNATURES: Dict[str, List[str]] = {
    "agrolab": [
        "Code Echantillon",
        "Code Échantillon",
        "Date d'échantillonnage",
        "Lithologie",
    ],
    "eurofins": [
        "N° Echantillon",
        "N° Échantillon",
        "Nom d'échantillon",
        "Sample Name",
    ],
}


def detect_provider(file_path: str) -> Optional[str]:
    """
    Analyze an Excel file to determine which laboratory provider created it.
    
    Args:
        file_path: Path to the Excel file to analyze
        
    Returns:
        Provider ID string ('agrolab', 'eurofins') or None if detection failed
    """
    try:
        # Read only the first 10 rows for speed
        df = pd.read_excel(file_path, nrows=10, header=None)
        
        # Flatten all cell values into a searchable string
        all_text = ' '.join(
            str(cell).lower() 
            for row in df.values 
            for cell in row 
            if pd.notna(cell)
        )
        
        # Score each provider by how many signature patterns match
        scores: Dict[str, int] = {}
        
        for provider_id, signatures in PROVIDER_SIGNATURES.items():
            score = sum(1 for sig in signatures if sig.lower() in all_text)
            scores[provider_id] = score
            logger.debug(f"Provider {provider_id}: score {score}")
        
        # Find the provider with the highest score (minimum 1 match required)
        best_provider = max(scores, key=scores.get)
        best_score = scores[best_provider]
        
        if best_score > 0:
            logger.info(f"Auto-detected provider: {best_provider} (score: {best_score})")
            return best_provider
        else:
            logger.warning("Could not auto-detect provider, no signature matched")
            return None
            
    except Exception as e:
        logger.error(f"Error during provider detection: {e}")
        return None


def preview_file(file_path: str) -> Dict:
    """
    Generate a quick preview/summary of a laboratory file.
    
    Args:
        file_path: Path to the Excel file
        
    Returns:
        Dict with keys: 'samples', 'parameters', 'provider_guess'
    """
    try:
        # Read full file for accurate counts
        df = pd.read_excel(file_path, header=None)
        
        # Guess provider
        provider_guess = detect_provider(file_path)
        
        # AGROLAB format:
        # - Row 2 contains sample names (filtering out headers like "Nom d'échantillon", "Résultat")
        # - Column 0 from row 5 onwards contains parameter names
        
        # Count samples from row 2
        exclude_keywords = ["nom d'échantillon", "résultat", "nan", "none"]
        row2_values = df.iloc[2].dropna().tolist() if len(df) > 2 else []
        samples = [
            str(x) for x in row2_values 
            if str(x).lower() not in exclude_keywords 
            and "résultat" not in str(x).lower()
        ]
        
        # Count parameters: rows where Unit column (col 5) is not empty
        # This indicates the parameter was actually analyzed
        if len(df) > 5 and len(df.columns) > 5:
            unit_col = df.iloc[5:, 5]  # Column 5 = "Unité"
            params = unit_col.dropna().count()
        else:
            params = 0
        
        return {
            "samples": int(len(samples)),
            "parameters": int(params),
            "provider_guess": provider_guess or "inconnu"
        }
        
    except Exception as e:
        logger.error(f"Error during file preview: {e}")
        return {
            "samples": 0,
            "parameters": 0,
            "provider_guess": "erreur"
        }
