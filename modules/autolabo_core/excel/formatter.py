"""
Excel formatting module for laboratory reports.

This module handles all Excel formatting logic including:
- Format creation (colors, borders, fonts)
- Header writing
- Data row writing with conditional formatting
- Value parsing and unit conversion
"""

import logging
from typing import Dict, Any, List, Optional
import pandas as pd

from ..config.models import MatrixConfig

logger = logging.getLogger(__name__)


class ExcelFormatter:
    """
    Handles Excel formatting for laboratory reports.

    This class provides all formatting logic including conditional
    formatting based on regulatory limits for both Eaux and Sols matrices.
    """

    def __init__(self, config: MatrixConfig, samples: List[Dict[str, Any]]):
        """
        Initialize the formatter.

        Args:
            config: Matrix configuration with formatting rules
            samples: List of detected samples (name, date, idx)
        """
        self.config = config
        self.samples = samples

    def create_formats(self, workbook) -> Dict[str, Any]:
        """Create all Excel formats upfront."""
        return {
            'header_gray': workbook.add_format({
                'bold': True, 'bg_color': '#D9D9D9', 'border': 1,
                'align': 'center', 'valign': 'vcenter', 'text_wrap': True
            }),
            'header_green': workbook.add_format({
                'bold': True, 'bg_color': '#C6EFCE', 'border': 1,
                'align': 'center', 'valign': 'vcenter', 'text_wrap': True
            }),
            'header_orange': workbook.add_format({
                'bold': True, 'bg_color': '#FBCA98', 'border': 1,
                'align': 'center', 'valign': 'vcenter', 'text_wrap': True
            }),
            'header_white': workbook.add_format({
                'bold': True, 'bg_color': '#FFFFFF', 'border': 1,
                'align': 'center', 'valign': 'vcenter', 'text_wrap': True
            }),
            'header_pink': workbook.add_format({
                'bold': True, 'bg_color': '#FFCCFF', 'border': 1,
                'align': 'center', 'valign': 'vcenter', 'text_wrap': True
            }),
            'header_cyan': workbook.add_format({
                'bold': True, 'bg_color': '#CCFFFF', 'border': 1,
                'align': 'center', 'valign': 'vcenter', 'text_wrap': True
            }),
            'header_yellow': workbook.add_format({
                'bold': True, 'bg_color': '#FFFF99', 'border': 1,
                'align': 'center', 'valign': 'vcenter', 'text_wrap': True
            }),
            'header_red': workbook.add_format({
                'bold': True, 'bg_color': '#FF99CC', 'border': 1,
                'align': 'center', 'valign': 'vcenter', 'text_wrap': True
            }),
            'param': workbook.add_format({'border': 1, 'align': 'left'}),
            'center': workbook.add_format({'border': 1, 'align': 'center'}),
            'family': workbook.add_format({
                'bold': True, 'bg_color': '#0070C0', 'font_color': 'white', 'border': 1
            }),
            # Conditional formatting colors
            'cond_green': workbook.add_format({
                'border': 1, 'align': 'center', 'bg_color': '#C6EFCE'
            }),
            'cond_yellow': workbook.add_format({
                'border': 1, 'align': 'center', 'bg_color': '#FFFF99'
            }),
            'cond_orange': workbook.add_format({
                'border': 1, 'align': 'center', 'bg_color': '#FBCA98'
            }),
            # Sols-specific
            'cond_isdd_exceeded': workbook.add_format({
                'border': 1, 'align': 'center', 'bg_color': '#FFFFFF', 'font_color': 'red'
            }),
            'cond_isdnd': workbook.add_format({
                'border': 1, 'align': 'center', 'bg_color': '#FF99CC'
            }),
            'cond_isdi_plus': workbook.add_format({
                'border': 1, 'align': 'center', 'bg_color': '#FFFF99'
            }),
            'cond_isdi': workbook.add_format({
                'border': 1, 'align': 'center', 'bg_color': '#CCFFFF'
            }),
            'cond_hcsp': workbook.add_format({
                'border': 1, 'align': 'center', 'bg_color': '#FFCCFF', 'font_color': 'red'
            }),
        }

    def write_headers(self, worksheet, formats: Dict) -> int:
        """Write header rows. Returns the starting row for data."""
        current_row = 0

        # Column 0: Paramètre
        worksheet.write(current_row, 0, "Paramètre", formats['header_gray'])
        worksheet.set_column(0, 0, 30)

        # Column 1: Unité
        worksheet.write(current_row, 1, "Unité", formats['header_gray'])
        worksheet.set_column(1, 1, 10)

        # Regulatory headers
        col_offset = 2
        color_map = {
            'green': 'header_green',
            'orange': 'header_orange',
            'white': 'header_white',
            'pink': 'header_pink',
            'cyan': 'header_cyan',
            'yellow': 'header_yellow',
            'red': 'header_red',
        }

        for header in self.config.regulatory_headers:
            fmt_key = color_map.get(header.color, 'header_orange')
            worksheet.write(current_row, col_offset, header.title, formats[fmt_key])
            worksheet.set_column(col_offset, col_offset, 15)
            col_offset += 1

        # Sample headers
        for idx, s in enumerate(self.samples):
            worksheet.write(current_row, col_offset + idx, s.get('name', f"Ech {idx+1}"), formats['header_gray'])
            worksheet.write(current_row + 1, col_offset + idx, s.get('date', '-'), formats['header_gray'])
            worksheet.write(current_row + 2, col_offset + idx, "Localisation", formats['header_gray'])
            worksheet.set_column(col_offset + idx, col_offset + idx, 12)

        # Labels for date/location rows
        worksheet.write(current_row + 1, 0, "", formats['header_gray'])
        worksheet.write(current_row + 2, 0, "", formats['header_gray'])
        worksheet.write(current_row + 1, col_offset - 1, "Date de prélèvement", formats['header_gray'])
        worksheet.write(current_row + 2, col_offset - 1, "Localisation", formats['header_gray'])

        return current_row + 3  # Data starts after header rows

    def write_data_rows(self, worksheet, df_merged: pd.DataFrame, formats: Dict, start_row: int) -> int:
        """Write data rows with conditional formatting. Returns the last row written.

        Performance: Uses to_dict('records') instead of iterrows() for ~10-100x faster iteration.
        """
        cols = self.config.columns
        reg_cols = self.config.regulatory_cols
        reg_headers = self.config.regulatory_headers

        c_name_idx = str(cols.name)
        c_raw_name_idx = str(cols.raw_name_col) if cols.raw_name_col is not None else c_name_idx
        c_unit_idx = str(cols.unit)
        c_family_idx = str(cols.family) if cols.family else None

        current_row = start_row
        pending_family_header = None

        # Build color map for limits
        col_color_map = {}
        for i, header in enumerate(reg_headers):
            col_color_map[f"{reg_cols[i]}_REF"] = header.color

        # Convert to list of dicts for faster iteration (vs iterrows)
        records = df_merged.to_dict('records')

        for row in records:
            # Get parameter name
            p_name = row.get(f"{c_name_idx}_REF")
            if pd.isna(p_name):
                # Try raw col (likely suffixed) using specific raw col index if defined
                p_name = row.get(f"{c_raw_name_idx}_RAW")
                if pd.isna(p_name):
                    p_name = row.get(c_raw_name_idx)

            # Get unit
            p_unit = row.get(f"{c_unit_idx}_REF")
            if pd.isna(p_unit):
                p_unit = row.get(f"{c_unit_idx}_RAW")
                if pd.isna(p_unit):
                    p_unit = row.get(c_unit_idx)

            # Check for family header
            if c_family_idx and pd.isna(p_name):
                possible_title = row.get(f"{c_family_idx}_REF")
                if pd.isna(possible_title):
                    possible_title = row.get(c_family_idx)
                if pd.notna(possible_title) and pd.isna(p_unit):
                    p_name = possible_title

            if pd.isna(p_name):
                continue

            # Family header check - must have no unit AND be a valid non-numeric name
            # Skip rows with numeric-only names (e.g., "0", "1", "2") as these are likely 
            # parameters with short names, not section headers
            if pd.isna(p_unit) or str(p_unit).strip() == "":
                name_str = str(p_name).strip()
                # Only treat as family header if:
                # 1. Name is not purely numeric
                # 2. Name is longer than 2 characters (real family names are descriptive)
                is_numeric_only = name_str.replace('.', '').replace('-', '').replace(',', '').isdigit()
                if not is_numeric_only and len(name_str) > 2:
                    pending_family_header = name_str
                continue

            # Check if row has data
            has_data = False
            sample_values = []

            for s in self.samples:
                raw_idx = s['idx']
                col_key = f"{raw_idx}_RAW"
                raw_val = row.get(col_key)
                if pd.isna(raw_val):
                    raw_val = row.get(str(raw_idx))

                if pd.notna(raw_val) and str(raw_val).strip() != "":
                    has_data = True
                    sample_values.append(str(raw_val))
                else:
                    sample_values.append("-")

            if not has_data:
                continue

            # Suppress duplicate headers for virtual rows
            row_key = str(row.get('_key', ''))
            if row_key in ['13906', '13739']:
                pending_family_header = None

            # Write family header if pending
            if pending_family_header:
                total_cols = 2 + len(reg_cols) + len(self.samples)
                worksheet.merge_range(
                    current_row, 0, current_row, total_cols - 1,
                    pending_family_header, formats['family']
                )
                current_row += 1
                pending_family_header = None

            # Write parameter name and unit
            worksheet.write(current_row, 0, str(p_name), formats['param'])
            worksheet.write(current_row, 1, str(p_unit), formats['center'])

            # Write regulatory limits
            parsed_limits = {}
            for i, src_col in enumerate(reg_cols):
                col_key = f"{src_col}_REF"
                val = row.get(col_key)
                if pd.isna(val):
                    val = row.get(str(src_col))

                if pd.isna(val) or str(val).strip() in ["nan", ""]:
                    val = "-"

                val_str = str(val)
                self._write_cell_value(worksheet, current_row, 2 + i, val_str, formats['center'])

                limit_float = self._parse_limit_value(val_str)
                if limit_float is not None:
                    parsed_limits[col_key] = limit_float

            # Write sample values with conditional formatting
            col_offset = 2 + len(reg_cols)
            raw_unit = row.get(f"{c_unit_idx}_RAW")
            conversion_factor = self._get_conversion_factor(
                str(raw_unit) if pd.notna(raw_unit) else "", str(p_unit)
            )

            for i, val_str in enumerate(sample_values):
                cell_fmt = self._get_conditional_format(
                    val_str, parsed_limits, col_color_map, conversion_factor, formats
                )

                # Apply conversion and write
                self._write_sample_value(
                    worksheet, current_row, col_offset + i,
                    val_str, conversion_factor, cell_fmt
                )

            current_row += 1

        return current_row

    def _write_cell_value(self, worksheet, row: int, col: int, val_str: str, fmt) -> None:
        """Write a cell value, attempting to write as number if possible."""
        if not any(c in val_str for c in ['<', '>', 'e', 'E', 'Entre', 'entre']) and val_str != "-":
            try:
                f_val = float(val_str.replace(',', '.').strip())
                worksheet.write_number(row, col, f_val, fmt)
                return
            except ValueError:
                pass
        worksheet.write(row, col, val_str, fmt)

    def _write_sample_value(self, worksheet, row: int, col: int, val_str: str,
                            conversion_factor: float, fmt) -> None:
        """Write a sample value with optional unit conversion."""
        if val_str == "-":
            worksheet.write(row, col, val_str, fmt)
            return

        if not any(c in val_str for c in ['<', '>', 'e', 'E']):
            try:
                f_v = float(val_str.replace(',', '.'))
                c_v = f_v * conversion_factor
                worksheet.write_number(row, col, c_v, fmt)
                return
            except ValueError:
                pass

        if val_str.startswith('<') and conversion_factor != 1.0:
            try:
                num = float(val_str[1:].replace(',', '.'))
                new = num * conversion_factor
                s_new = f"<{new}".replace('.', ',')
                worksheet.write(row, col, s_new, fmt)
                return
            except ValueError:
                pass

        worksheet.write(row, col, val_str, fmt)

    def _get_conditional_format(self, val_str: str, parsed_limits: Dict,
                                 col_color_map: Dict, conversion_factor: float,
                                 formats: Dict) -> Any:
        """Get the appropriate format based on value vs limits."""
        s_val = self._parse_sample_value(val_str)
        if s_val is None:
            return formats['center']

        s_val = s_val * conversion_factor

        if self.config.formatting_mode == "sols":
            return self._get_sols_format(s_val, parsed_limits, formats)
        else:
            return self._get_eaux_format(s_val, parsed_limits, col_color_map, formats)

    def _get_sols_format(self, s_val: float, parsed_limits: Dict, formats: Dict) -> Any:
        """Get format for Sols based on ISDI/ISDI+/ISDND/ISDD thresholds."""
        # Regulatory column indices for Sols
        limit_isdd = parsed_limits.get('16_REF')
        limit_isdnd = parsed_limits.get('14_REF')
        limit_isdi_plus = parsed_limits.get('13_REF')
        limit_isdi = parsed_limits.get('11_REF')
        limit_hcsp_dep = parsed_limits.get('10_REF')

        if limit_isdd is not None and s_val >= limit_isdd:
            return formats['cond_isdd_exceeded']
        elif limit_isdnd is not None and s_val >= limit_isdnd:
            return formats['cond_isdnd']
        elif limit_isdi_plus is not None and s_val >= limit_isdi_plus:
            return formats['cond_isdi_plus']
        elif limit_isdi is not None and s_val >= limit_isdi:
            return formats['cond_isdi']
        elif limit_hcsp_dep is not None and s_val >= limit_hcsp_dep:
            return formats['cond_hcsp']

        return formats['center']

    def _get_eaux_format(self, s_val: float, parsed_limits: Dict,
                         col_color_map: Dict, formats: Dict) -> Any:
        """Get format for Eaux based on thresholds."""
        matched_color = None

        for limit_col, limit_val in parsed_limits.items():
            if s_val >= limit_val:
                color = col_color_map.get(limit_col, 'green')
                if color == 'orange':
                    matched_color = 'orange'
                elif color == 'yellow' and matched_color != 'orange':
                    matched_color = 'yellow'
                elif color == 'green' and matched_color is None:
                    matched_color = 'green'

        if matched_color == 'orange':
            return formats['cond_orange']
        elif matched_color == 'yellow':
            return formats['cond_yellow']
        elif matched_color == 'green':
            return formats['cond_green']

        return formats['center']

    def _get_conversion_factor(self, raw_unit: str, ref_unit: str) -> float:
        """Calculate unit conversion factor."""
        if not raw_unit or not ref_unit:
            return 1.0

        u1 = str(raw_unit).lower().strip().replace("ug", "µg")
        u2 = str(ref_unit).lower().strip().replace("ug", "µg")

        if u1 == u2:
            return 1.0
        if "µg" in u1 and "mg" in u2:
            return 0.001
        if "mg" in u1 and "µg" in u2:
            return 1000.0

        return 1.0

    def _parse_limit_value(self, txt: str) -> Optional[float]:
        """Parse a limit value string to float."""
        if not txt or txt == "-":
            return None

        txt = txt.strip().lower()

        if "entre" in txt:
            try:
                return float(txt.split()[-1].replace(',', '.'))
            except ValueError:
                return None

        if "(" in txt:
            txt = txt.split("(")[0].strip()

        txt = txt.replace("<", "").replace(">", "").strip()

        try:
            return float(txt.replace(",", "."))
        except ValueError:
            return None

    def _parse_sample_value(self, txt: str) -> Optional[float]:
        """Parse a sample value string to float."""
        if not txt or txt == "-":
            return None

        txt = txt.strip().lower()

        if "<" in txt:
            return 0.0

        try:
            return float(txt.replace(",", "."))
        except ValueError:
            return None
