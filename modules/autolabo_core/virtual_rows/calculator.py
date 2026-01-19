"""
Virtual rows calculator for laboratory reports.

This module handles calculation of virtual summary rows (e.g., PCB sum, HAP sum)
based on component parameters.
"""

import logging
from typing import List, Dict, Any, Tuple
import pandas as pd

from ..config.models import VirtualRowConfig, ColumnMapping

logger = logging.getLogger(__name__)


class VirtualRowsCalculator:
    """
    Calculates virtual summary rows for laboratory reports.

    Virtual rows are calculated sums of component parameters,
    such as "Somme 7 PCB" or "HAP (EPA) - somme".
    """

    def __init__(
        self,
        virtual_configs: List[VirtualRowConfig],
        columns: ColumnMapping,
        samples: List[Dict[str, Any]]
    ):
        """
        Initialize the calculator.

        Args:
            virtual_configs: List of virtual row configurations
            columns: Column mapping configuration
            samples: List of detected samples
        """
        self.virtual_configs = virtual_configs
        self.columns = columns
        self.samples = samples

    def add_virtual_rows(self, merged: pd.DataFrame) -> pd.DataFrame:
        """
        Add virtual summary rows to the merged DataFrame.

        Args:
            merged: Merged DataFrame with raw and reference data

        Returns:
            DataFrame with virtual rows added and sorted
        """
        if not self.virtual_configs:
            return merged

        logger.debug(f"Adding {len(self.virtual_configs)} virtual rows...")

        rows_to_add = []

        for v_cfg in self.virtual_configs:
            new_row = self._create_virtual_row(merged, v_cfg)
            rows_to_add.append(new_row)

        if rows_to_add:
            merged = self._insert_virtual_rows(merged, rows_to_add)

        return merged

    def _create_virtual_row(
        self,
        merged: pd.DataFrame,
        v_cfg: VirtualRowConfig
    ) -> Dict[str, Any]:
        """Create a single virtual row with calculated sums."""
        cols = self.columns

        new_row = {
            '_key': v_cfg.key,
            'is_eluate': False,
            f"{cols.name}_REF": v_cfg.name,
            f"{cols.unit}_REF": v_cfg.unit,
            str(cols.name): v_cfg.name,
            str(cols.unit): v_cfg.unit,
        }

        # Add regulatory limits
        for col_idx, limit_val in v_cfg.ref_limits.items():
            new_row[f"{col_idx}_REF"] = limit_val

        # Calculate sums for each sample column
        df_comps = merged[merged['_key'].astype(str).isin(v_cfg.components)]

        for s in self.samples:
            r_col = f"{s['idx']}_RAW" if f"{s['idx']}_RAW" in merged.columns else str(s['idx'])
            if r_col not in merged.columns:
                continue

            values = df_comps[r_col].values
            total_sum, all_lower, has_data = self._calculate_sum(values)

            if not has_data:
                new_row[r_col] = "-"
            elif all_lower:
                new_row[r_col] = "n.d."
            else:
                new_row[r_col] = f"{total_sum:.3f}"

        # Find insertion point
        idx_anchor = self._find_insertion_index(merged, v_cfg)
        new_row['_temp_sort_index'] = idx_anchor + 0.1 if idx_anchor is not None else len(merged) + 100

        return new_row

    def _calculate_sum(self, values) -> Tuple[float, bool, bool]:
        """
        Calculate sum from values array.

        Returns:
            (total_sum, all_lower_than_LOQ, has_data)
        """
        total_sum = 0.0
        all_lower = True
        has_data = False

        for val in values:
            num, is_lower = self._parse_value_for_sum(val)
            if pd.notna(val) and str(val).strip() not in ['-', '']:
                has_data = True
            if not is_lower:
                all_lower = False
                total_sum += num

        return total_sum, all_lower, has_data

    def _parse_value_for_sum(self, v) -> Tuple[float, bool]:
        """
        Parse a value for sum calculation.

        Returns:
            (numeric_value, is_lower_than_LOQ)
        """
        if pd.isna(v) or str(v).strip() in ['-', '', 'nan', 'NAN']:
            return 0.0, True

        s = str(v).replace(',', '.').strip()
        is_lower = s.startswith('<')

        try:
            num = float(s.replace('<', '').strip())
        except ValueError:
            num = 0.0

        return num, is_lower

    def _find_insertion_index(
        self,
        merged: pd.DataFrame,
        v_cfg: VirtualRowConfig
    ) -> int:
        """Find the index where the virtual row should be inserted."""
        anchor_candidates = [str(c) for c in reversed(v_cfg.components)]
        if v_cfg.insert_after:
            anchor_candidates = [v_cfg.insert_after]

        for candidate in anchor_candidates:
            matches = merged.index[merged['_key'].astype(str) == candidate].tolist()
            if matches:
                return matches[0]

        return None

    def _insert_virtual_rows(
        self,
        merged: pd.DataFrame,
        rows_to_add: List[Dict[str, Any]]
    ) -> pd.DataFrame:
        """Insert virtual rows into the DataFrame and sort."""
        if '_temp_sort_index' not in merged.columns:
            merged['_temp_sort_index'] = merged.index

        df_virtual = pd.DataFrame(rows_to_add)
        merged = pd.concat([merged, df_virtual], ignore_index=False)
        merged.sort_values(by='_temp_sort_index', inplace=True)
        merged.reset_index(drop=True, inplace=True)
        merged.drop(columns=['_temp_sort_index'], inplace=True, errors='ignore')

        return merged
