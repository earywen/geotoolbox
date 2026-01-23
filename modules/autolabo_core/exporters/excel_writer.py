"""
Excel Writer for AutoLabo reports.

Handles all worksheet writing operations: headers, data rows, and legend.
Uses ExcelFormatter for all format-related decisions.
"""

import logging
from typing import List, Dict, Any, Optional

import pandas as pd

from ..config.models import MatrixConfig
from .formatter import ExcelFormatter

logger = logging.getLogger(__name__)


class ExcelWriter:
    """
    Writes formatted data to Excel worksheets.

    Separates the concerns of what to write from how to format it.
    Uses ExcelFormatter for all formatting decisions.

    Usage:
        formatter = ExcelFormatter(workbook)
        writer = ExcelWriter(worksheet, formatter, config, samples)
        current_row = writer.write_headers()
        current_row = writer.write_data_rows(df_merged, current_row)
        writer.write_legend(current_row + 2)
    """

    def __init__(
        self,
        worksheet,
        formatter: ExcelFormatter,
        config: MatrixConfig,
        samples: List[Dict[str, Any]]
    ):
        """
        Initialize the Excel writer.

        Args:
            worksheet: xlsxwriter worksheet object
            formatter: ExcelFormatter instance
            config: MatrixConfig with regulatory headers and legend
            samples: List of sample dicts with idx, name, date
        """
        self.worksheet = worksheet
        self.formatter = formatter
        self.config = config
        self.samples = samples

        # Build color map for regulatory columns
        self._col_color_map = {}
        for i, header in enumerate(config.regulatory_headers):
            col_key = f"{config.regulatory_cols[i]}_REF"
            self._col_color_map[col_key] = header.color

    def write_headers(self) -> int:
        """
        Write header rows to the worksheet.

        Returns:
            Row number where data should start
        """
        ws = self.worksheet
        fmt = self.formatter
        current_row = 0

        # Column 0: Paramètre
        ws.write(current_row, 0, "Paramètre", fmt.get_header_format('gray'))
        ws.set_column(0, 0, 30)

        # Column 1: Unité
        ws.write(current_row, 1, "Unité", fmt.get_header_format('gray'))
        ws.set_column(1, 1, 10)

        # Regulatory headers
        col_offset = 2
        for header in self.config.regulatory_headers:
            ws.write(current_row, col_offset, header.title, fmt.get_header_format(header.color))
            ws.set_column(col_offset, col_offset, 15)
            col_offset += 1

        # Sample headers
        for idx, s in enumerate(self.samples):
            ws.write(current_row, col_offset + idx, s.get('name', f"Ech {idx+1}"), fmt.get_header_format('gray'))
            ws.write(current_row + 1, col_offset + idx, s.get('date', '-'), fmt.get_header_format('gray'))
            ws.write(current_row + 2, col_offset + idx, "Localisation", fmt.get_header_format('gray'))
            ws.set_column(col_offset + idx, col_offset + idx, 12)

        # Labels for date/location rows
        ws.write(current_row + 1, 0, "", fmt.get_header_format('gray'))
        ws.write(current_row + 2, 0, "", fmt.get_header_format('gray'))

        last_reg_col = col_offset - 1
        ws.write(current_row + 1, last_reg_col, "Date de prélèvement", fmt.get_header_format('gray'))
        ws.write(current_row + 2, last_reg_col, "Localisation", fmt.get_header_format('gray'))

        logger.debug(f"Headers written, data starts at row {current_row + 3}")
        return current_row + 3

    def write_data_rows(self, df_merged: pd.DataFrame, start_row: int) -> int:
        """
        Write all data rows with conditional formatting.

        Args:
            df_merged: Merged DataFrame with all data
            start_row: Row to start writing data

        Returns:
            Last row written
        """
        ws = self.worksheet
        fmt = self.formatter
        cols = self.config.columns
        reg_cols = self.config.regulatory_cols

        c_name_idx = str(cols.name)
        c_unit_idx = str(cols.unit)
        c_family_idx = str(cols.family) if cols.family else None

        current_row = start_row
        pending_family_header = None

        for idx, row in df_merged.iterrows():
            # Get parameter name
            p_name = row.get(f"{c_name_idx}_REF")
            if pd.isna(p_name):
                p_name = row.get(c_name_idx)

            # Get unit
            p_unit = row.get(f"{c_unit_idx}_REF")
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

            # Family header check
            if pd.isna(p_unit) or str(p_unit).strip() == "":
                pending_family_header = str(p_name)
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

            # Skip duplicate headers for virtual rows
            row_key = str(row.get('_key', ''))
            if row_key in ['13906', '13739']:
                pending_family_header = None

            # Write family header if pending
            if pending_family_header:
                total_cols = 2 + len(reg_cols) + len(self.samples)
                ws.merge_range(
                    current_row, 0, current_row, total_cols - 1,
                    pending_family_header, fmt.get_format('family')
                )
                current_row += 1
                pending_family_header = None

            # Write parameter name and unit
            ws.write(current_row, 0, str(p_name), fmt.get_format('param'))
            ws.write(current_row, 1, str(p_unit), fmt.get_format('center'))

            # Write regulatory limits and collect parsed values
            parsed_limits = {}
            for i, src_col in enumerate(reg_cols):
                col_key = f"{src_col}_REF"
                val = row.get(col_key)
                if pd.isna(val):
                    val = row.get(str(src_col))

                if pd.isna(val) or str(val).strip() in ["nan", ""]:
                    val = "-"

                val_str = str(val)
                self._write_cell_value(current_row, 2 + i, val_str, fmt.get_format('center'))

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
                s_val = self._parse_sample_value(val_str)
                if s_val is not None:
                    s_val = s_val * conversion_factor

                # Get conditional format
                if self.config.formatting_mode == "sols":
                    cell_fmt = fmt.get_conditional_format_sols(s_val, parsed_limits)
                else:
                    cell_fmt = fmt.get_conditional_format_eaux(s_val, parsed_limits, self._col_color_map)

                self._write_sample_value(current_row, col_offset + i, val_str, conversion_factor, cell_fmt)

            current_row += 1

        logger.debug(f"Data rows written, ending at row {current_row}")
        return current_row

    def write_legend(self, start_row: int) -> int:
        """
        Write the legend section.

        Args:
            start_row: Row to start writing legend

        Returns:
            Last row written
        """
        ws = self.worksheet
        fmt = self.formatter
        legend = self.config.legend
        current_row = start_row

        # Write notes
        for note in legend.notes:
            if note:
                ws.merge_range(current_row, 0, current_row, 8, note, fmt.get_format('legend_text'))
            current_row += 1

        current_row += 1

        # Write color legend items
        for item in legend.color_items:
            item_fmt = fmt.create_legend_format(item.bg_color, item.font_color)
            ws.merge_range(current_row, 0, current_row, 8, item.description, item_fmt)
            current_row += 1

        logger.debug(f"Legend written, ending at row {current_row}")
        return current_row

    def _write_cell_value(self, row: int, col: int, val_str: str, cell_fmt) -> None:
        """Write a cell, attempting numeric format when possible."""
        if not any(c in val_str for c in ['<', '>', 'e', 'E', 'Entre', 'entre']) and val_str != "-":
            try:
                f_val = float(val_str.replace(',', '.').strip())
                self.worksheet.write_number(row, col, f_val, cell_fmt)
                return
            except ValueError:
                pass
        self.worksheet.write(row, col, val_str, cell_fmt)

    def _write_sample_value(self, row: int, col: int, val_str: str,
                            conversion_factor: float, cell_fmt) -> None:
        """Write a sample value with optional unit conversion."""
        if val_str == "-":
            self.worksheet.write(row, col, val_str, cell_fmt)
            return

        if not any(c in val_str for c in ['<', '>', 'e', 'E']):
            try:
                f_v = float(val_str.replace(',', '.'))
                c_v = f_v * conversion_factor
                self.worksheet.write_number(row, col, c_v, cell_fmt)
                return
            except ValueError:
                pass

        if val_str.startswith('<') and conversion_factor != 1.0:
            try:
                num = float(val_str[1:].replace(',', '.'))
                new = num * conversion_factor
                s_new = f"<{new}".replace('.', ',')
                self.worksheet.write(row, col, s_new, cell_fmt)
                return
            except ValueError:
                pass

        self.worksheet.write(row, col, val_str, cell_fmt)

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
