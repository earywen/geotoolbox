"""
Generic Lab Processor using configuration-driven architecture.

This processor uses MatrixConfig from YAML files instead of hardcoded values,
enabling support for multiple laboratory providers (AGROLAB, EUROFINS, etc.).
"""

import logging
from io import BytesIO
from typing import List, Dict, Optional, Any

import pandas as pd
import xlsxwriter

from ..config.models import MatrixConfig, ProviderMeta, RegulatoryHeader

logger = logging.getLogger(__name__)


class GenericLabProcessor:
    """
    Configuration-driven laboratory report processor.
    
    Uses MatrixConfig for all parsing rules, column mappings, and formatting options.
    This eliminates the need for subclasses per matrix type.
    
    Usage:
        config = registry.load_matrix("agrolab", "sols")
        provider = registry.load_provider("agrolab")
        processor = GenericLabProcessor(raw_path, ref_path, config, provider)
        excel_io = processor.process()
    """
    
    def __init__(
        self, 
        raw_path: str, 
        ref_path: str, 
        config: MatrixConfig,
        provider: Optional[ProviderMeta] = None
    ):
        """
        Initialize the processor with paths and configuration.
        
        Args:
            raw_path: Path to the raw laboratory file
            ref_path: Path to the reference file with regulatory limits
            config: MatrixConfig loaded from YAML
            provider: Optional ProviderMeta for lab-specific behavior
        """
        self.raw_path = raw_path
        self.ref_path = ref_path
        self.config = config
        self.provider = provider
        self.samples: List[Dict[str, Any]] = []
        
        logger.info(f"Initialized processor for matrix: {config.matrix}")
        if provider:
            logger.info(f"Provider: {provider.name} (key_type: {provider.key_type})")
    
    def process(self) -> BytesIO:
        """
        Main processing method (Template Method pattern).
        
        Returns:
            BytesIO containing the Excel file
        """
        logger.info("Starting processing...")
        
        df_raw = self._parse_raw()
        logger.debug(f"Raw data parsed: {len(df_raw)} rows")
        
        df_ref = self._parse_ref()
        logger.debug(f"Reference data parsed: {len(df_ref)} rows")
        
        df_merged = self._merge_data(df_raw, df_ref)
        logger.debug(f"Merged data: {len(df_merged)} rows")
        
        excel_output = self._generate_excel(df_merged, df_ref)
        logger.info("Processing complete")
        
        return excel_output
    
    def _parse_raw(self) -> pd.DataFrame:
        """Parse the raw laboratory file and detect samples."""
        logger.debug(f"Parsing raw file: {self.raw_path}")
        
        df = pd.read_excel(self.raw_path, header=None)
        df.columns = [str(c) for c in df.columns]
        
        # Add eluate section detection for Sols
        if self.config.formatting_mode == "sols":
            df = self._add_section_column(df)
        
        # Detect samples
        self._detect_samples(df)
        
        return df
    
    def _detect_samples(self, df: pd.DataFrame) -> None:
        """Detect sample columns from the raw data."""
        parsing = self.config.parsing
        
        date_row_idx = parsing.date_row
        name_row_idx = parsing.name_row
        
        # For Eaux, search for "Date" keyword
        if self.config.matrix == "eaux":
            for i in range(min(30, len(df))):
                row_str = " ".join(df.iloc[i].astype(str).values)
                if "Date" in row_str and "chantillon" in row_str:
                    date_row_idx = i
                    name_row_idx = i + 2
                    break
        
        self.samples = []
        date_vals = df.iloc[date_row_idx] if date_row_idx < len(df) else pd.Series()
        name_vals = df.iloc[name_row_idx] if name_row_idx < len(df) else pd.Series()
        
        exclude_keywords = [kw.lower() for kw in parsing.sample_exclude_keywords]
        
        for col_idx in range(len(date_vals)):
            n_val = str(name_vals.iloc[col_idx] if col_idx < len(name_vals) else "").strip()
            
            if n_val.lower() in exclude_keywords or len(n_val) <= 1:
                continue
            
            d_val = str(date_vals.iloc[col_idx] if col_idx < len(date_vals) else "").strip()
            fmt_date = d_val
            
            # Format date if it's YYYYMMDD
            if len(d_val) == 8 and d_val.isdigit():
                fmt_date = f"{d_val[6:8]}/{d_val[4:6]}/{d_val[0:4]}"
            
            self.samples.append({
                "idx": col_idx,
                "name": n_val,
                "date": fmt_date
            })
        
        logger.debug(f"Detected {len(self.samples)} samples")
    
    def _add_section_column(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add 'is_eluate' column based on 'ANALYSES SUR ELUAT' marker."""
        df["is_eluate"] = False
        eluate_found = False
        
        for idx in df.index:
            row_vals = [str(x).upper() for x in df.loc[idx].values]
            row_str = "".join(row_vals).replace(" ", "")
            
            if "ANALYSESSURELUAT" in row_str or "ANALYSESURELUAT" in row_str:
                eluate_found = True
            
            if eluate_found:
                df.at[idx, "is_eluate"] = True
        
        return df
    
    def _parse_ref(self) -> pd.DataFrame:
        """Parse the reference file with regulatory limits."""
        logger.debug(f"Parsing reference file: {self.ref_path}")
        
        try:
            df = pd.read_excel(self.ref_path, header=None)
            df.columns = [str(c) for c in df.columns]
            
            # Add eluate section for Sols
            if self.config.formatting_mode == "sols":
                df = self._add_section_column(df)
            
            return df
            
        except Exception as e:
            logger.error(f"Error parsing reference file: {e}")
            raise ValueError(f"Erreur REF: {e}")
    
    def _merge_data(self, df_raw: pd.DataFrame, df_ref: pd.DataFrame) -> pd.DataFrame:
        """Merge raw and reference DataFrames based on parameter keys."""
        logger.debug("Merging data...")
        
        cols = self.config.columns
        
        # Get column indices as strings
        c_ref_code = str(cols.code)
        
        # Use raw_code_col if specified, otherwise fall back to code column
        if cols.raw_code_col is not None:
            c_raw_code = str(cols.raw_code_col)
        else:
            c_raw_code = str(cols.code)
        
        # Create keys
        if c_ref_code in df_ref.columns:
            df_ref["_key"] = (
                df_ref[c_ref_code]
                .astype(str)
                .str.replace(r'\.0$', '', regex=True)
                .str.strip()
                .str.lower()
            )
            df_ref.loc[df_ref["_key"].isin(['nan', 'none', '']), "_key"] = pd.NA
        else:
            df_ref["_key"] = pd.NA
        
        if c_raw_code in df_raw.columns:
            df_raw["_key"] = (
                df_raw[c_raw_code]
                .astype(str)
                .str.replace(r'\.0$', '', regex=True)
                .str.strip()
                .str.lower()
            )
            df_raw.loc[df_raw["_key"].isin(['nan', 'none', '']), "_key"] = pd.NA
        else:
            df_raw["_key"] = pd.NA
        
        # Apply key aliases
        if self.config.key_aliases:
            df_raw['_key'] = df_raw['_key'].astype(str).replace(self.config.key_aliases)
        
        # Drop rows without keys
        df_raw = df_raw.dropna(subset=['_key'])
        
        # Merge
        if self.config.formatting_mode == "sols" and "is_eluate" in df_raw.columns:
            # Merge on both key and is_eluate for Sols
            df_raw = df_raw.drop_duplicates(subset=['_key', 'is_eluate'])
            merged = pd.merge(
                df_ref, df_raw,
                left_on=["_key", "is_eluate"],
                right_on=["_key", "is_eluate"],
                how="left",
                suffixes=("_REF", "_RAW")
            )
        else:
            merged = pd.merge(
                df_ref, df_raw,
                left_on="_key",
                right_on="_key",
                how="left",
                suffixes=("_REF", "_RAW")
            )
        
        logger.debug(f"Merged {len(merged)} rows")
        
        # Add virtual rows for Sols
        if self.config.virtual_rows:
            merged = self._add_virtual_rows(merged)
        
        return merged
    
    def _add_virtual_rows(self, merged: pd.DataFrame) -> pd.DataFrame:
        """Add virtual summary rows (e.g., PCB sum, HAP sum)."""
        logger.debug(f"Adding {len(self.config.virtual_rows)} virtual rows...")
        
        rows_to_add = []
        cols = self.config.columns
        
        for v_cfg in self.config.virtual_rows:
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
                
                if not has_data:
                    new_row[r_col] = "-"
                elif all_lower:
                    new_row[r_col] = "n.d."
                else:
                    new_row[r_col] = f"{total_sum:.3f}"
            
            # Find insertion point
            anchor_candidates = [str(c) for c in reversed(v_cfg.components)]
            if v_cfg.insert_after:
                anchor_candidates = [v_cfg.insert_after]
            
            idx_anchor = None
            for candidate in anchor_candidates:
                matches = merged.index[merged['_key'].astype(str) == candidate].tolist()
                if matches:
                    idx_anchor = matches[0]
                    break
            
            new_row['_temp_sort_index'] = idx_anchor + 0.1 if idx_anchor else len(merged) + 100
            rows_to_add.append(new_row)
        
        if rows_to_add:
            if '_temp_sort_index' not in merged.columns:
                merged['_temp_sort_index'] = merged.index
            
            df_virtual = pd.DataFrame(rows_to_add)
            merged = pd.concat([merged, df_virtual], ignore_index=False)
            merged.sort_values(by='_temp_sort_index', inplace=True)
            merged.reset_index(drop=True, inplace=True)
            merged.drop(columns=['_temp_sort_index'], inplace=True, errors='ignore')
        
        return merged
    
    def _parse_value_for_sum(self, v) -> tuple:
        """Parse a value for sum calculation. Returns (numeric_value, is_lower_than_LOQ)."""
        if pd.isna(v) or str(v).strip() in ['-', '', 'nan', 'NAN']:
            return 0.0, True
        
        s = str(v).replace(',', '.').strip()
        is_lower = s.startswith('<')
        
        try:
            num = float(s.replace('<', '').strip())
        except ValueError:
            num = 0.0
        
        return num, is_lower
    
    def _generate_excel(self, df_merged: pd.DataFrame, df_ref: pd.DataFrame) -> BytesIO:
        """Generate the Excel report with formatting."""
        logger.info("Generating Excel report...")
        
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet("Rapport")
        
        # Create all formats upfront (performance optimization)
        formats = self._create_formats(workbook)
        
        # Write headers
        current_row = self._write_headers(worksheet, formats)
        
        # Write data
        current_row = self._write_data_rows(worksheet, df_merged, formats, current_row)
        
        # Write legend
        self._write_legend(worksheet, workbook, current_row + 2)
        
        workbook.close()
        output.seek(0)
        
        logger.info("Excel report generated successfully")
        return output
    
    def _create_formats(self, workbook) -> Dict[str, Any]:
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
    
    def _write_headers(self, worksheet, formats: Dict) -> int:
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
    
    def _write_data_rows(self, worksheet, df_merged: pd.DataFrame, formats: Dict, start_row: int) -> int:
        """Write data rows with conditional formatting. Returns the last row written.
        
        Performance: Uses to_dict('records') instead of iterrows() for ~10-100x faster iteration.
        """
        cols = self.config.columns
        reg_cols = self.config.regulatory_cols
        reg_headers = self.config.regulatory_headers
        
        c_name_idx = str(cols.name)
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
    
    def _write_legend(self, worksheet, workbook, start_row: int) -> None:
        """Write the legend based on config."""
        legend = self.config.legend
        current_row = start_row
        
        fmt_legend_text = workbook.add_format({
            'text_wrap': True, 'valign': 'top', 'font_size': 9
        })
        
        # Write notes
        for note in legend.notes:
            if note:
                worksheet.merge_range(current_row, 0, current_row, 8, note, fmt_legend_text)
            current_row += 1
        
        current_row += 1
        
        # Write color legend items
        for item in legend.color_items:
            fmt_color = workbook.add_format({
                'bg_color': item.bg_color,
                'border': 1,
                'text_wrap': True,
                'valign': 'vcenter',
                'font_color': item.font_color
            })
            worksheet.merge_range(current_row, 0, current_row, 8, item.description, fmt_color)
            current_row += 1
    
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
