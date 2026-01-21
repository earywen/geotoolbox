"""
Rule Manager for AutoLabo.

Handles loading, saving, and applying user-defined persistent overrides 
for regulatory thresholds. Rules are stored in %APPDATA%/Geotoolbox/custom_rules.json.
"""

import os
import json
import logging
import pandas as pd
from typing import Dict, Any, Optional

from modules import core

logger = logging.getLogger(__name__)

RULES_FILENAME = "custom_rules.json"

class RuleManager:
    """Manages persistent rules overriding Excel reference values."""
    
    def __init__(self):
        self._rules: Dict[str, Dict[str, Dict[str, float]]] = {}
        self._normalized_rules: Dict[str, Dict[str, Dict[str, float]]] = {}  # Pre-normalized cache
        self._loaded = False
        
    def _get_rules_path(self) -> str:
        """Get path to the persistent rules file."""
        return os.path.join(core.get_app_data_dir(), RULES_FILENAME)
        
    def load_rules(self) -> None:
        """Load rules from JSON file."""
        path = self._get_rules_path()
        if not os.path.exists(path):
            self._rules = {"eaux": {}, "sols": {}}
            self._loaded = True
            return
            
        try:
            with open(path, "r", encoding="utf-8") as f:
                self._rules = json.load(f)
            # Build pre-normalized cache for faster lookups
            self._build_normalized_cache()
            logger.info(f"Loaded custom rules from {path}")
        except Exception as e:
            logger.error(f"Failed to load custom rules: {e}")
            self._rules = {"eaux": {}, "sols": {}}
            self._normalized_rules = {"eaux": {}, "sols": {}}
        
        self._loaded = True
    
    def _build_normalized_cache(self) -> None:
        """Build pre-normalized rules cache for faster key lookups."""
        self._normalized_rules = {}
        for matrix, params in self._rules.items():
            self._normalized_rules[matrix] = {
                str(k).strip().lower(): v for k, v in params.items()
            }
        
    def save_rules(self) -> bool:
        """Save current rules to JSON file."""
        path = self._get_rules_path()
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self._rules, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved custom rules to {path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save custom rules: {e}")
            return False
            
    def get_rules(self, matrix: str) -> Dict[str, Dict[str, float]]:
        """Get all rules for a specific matrix (eaux/sols)."""
        if not self._loaded:
            self.load_rules()
        return self._rules.get(matrix, {})
        
    def set_rule(self, matrix: str, parameter: str, column: str, value: float) -> bool:
        """
        Set a specific override rule.
        
        Args:
            matrix: 'eaux' or 'sols'
            parameter: Parameter name (key)
            column: Column name to override (e.g., 'V_REF', 'V_IMPACT')
            value: New threshold value
        """
        if not self._loaded:
            self.load_rules()
            
        if matrix not in self._rules:
            self._rules[matrix] = {}
            
        if parameter not in self._rules[matrix]:
            self._rules[matrix][parameter] = {}
            
        self._rules[matrix][parameter][column] = float(value)
        return self.save_rules()
        
    def delete_rule(self, matrix: str, parameter: str) -> bool:
        """Delete all overrides for a parameter."""
        if not self._loaded:
            self.load_rules()
            
        if matrix in self._rules and parameter in self._rules[matrix]:
            del self._rules[matrix][parameter]
            return self.save_rules()
        return False

    def apply_overrides(self, df_ref: pd.DataFrame, matrix: str, key_col: str = "_key") -> pd.DataFrame:
        """
        Apply overrides to the reference DataFrame.
        
        Modifies df_ref in-place by updating values where overrides exist.
        """
        if not self._loaded:
            self.load_rules()
            
        matrix_rules = self._rules.get(matrix, {})
        if not matrix_rules:
            return df_ref
            
        overrides_count = 0
        
        # Ensure key column exists and is normalized for matching
        if key_col not in df_ref.columns:
            logger.warning(f"Key column {key_col} not found in reference DataFrame")
            return df_ref
            
        # Create a lookup map: normalized_key -> index
        # This assumes keys are unique in reference file
        key_map = {
            str(k).strip().lower(): idx 
            for idx, k in df_ref[key_col].items() 
            if pd.notna(k)
        }
        
        # Use pre-normalized rules cache for faster lookups
        normalized_rules = self._normalized_rules.get(matrix, {})
        
        for normalized_key, overrides in normalized_rules.items():
            if normalized_key not in key_map:
                continue
                
            idx = key_map[normalized_key]
            
            for col, val in overrides.items():
                if col in df_ref.columns:
                    original = df_ref.at[idx, col]
                    if original != val:
                        df_ref.at[idx, col] = val
                        logger.debug(f"Applied override: {param_key} [{col}] {original} -> {val}")
                        overrides_count += 1
                        
        if overrides_count > 0:
            logger.info(f"⚡ Applied {overrides_count} custom rule override(s)")
            
        return df_ref
