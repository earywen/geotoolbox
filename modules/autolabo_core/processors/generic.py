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

from ..config.models import MatrixConfig, ProviderMeta
from .base import BaseProcessor

logger = logging.getLogger(__name__)


class GenericLabProcessor(BaseProcessor):
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
        Initialize the processor.

        Args:
            raw_path: Path to the raw laboratory file
            ref_path: Path to the reference file with regulatory limits
            config: MatrixConfig loaded from YAML
            provider: Optional ProviderMeta for lab-specific behavior
        """
        super().__init__(raw_path, ref_path, config)
        self.provider = provider

        # State
        self.samples: List[Dict[str, Any]] = []
        self.active_reg_headers_indices: Optional[List[int]] = None

        logger.info(f"Initialized processor for matrix: {config.matrix}")
        if provider:
            logger.info(f"Provider: {provider.name} (key_type: {provider.key_type})")

    def set_active_regulatory_headers(self, indices: List[int]) -> None:
        """
        Set the list of active regulatory header indices for export.
        
        Args:
            indices: List of indices corresponding to config.regulatory_headers
        """
        self.active_reg_headers_indices = indices

    def process(self) -> BytesIO:
        """
        Main processing method (Template Method pattern).

        Returns:
            BytesIO containing the Excel file
        """
        from modules import core
        
        logger.info("Starting processing...")
        core.dispatch_event('autolabo_step', {'step': '📖 Lecture du fichier laboratoire...'})

        df_raw = self._parse_raw()
        logger.debug(f"Raw data parsed: {len(df_raw)} rows")
        core.dispatch_event('autolabo_step', {'step': f'✅ {len(df_raw)} lignes lues'})

        core.dispatch_event('autolabo_step', {'step': '📚 Chargement du référentiel...'})
        df_ref = self._parse_ref()
        logger.debug(f"Reference data parsed: {len(df_ref)} rows")

        core.dispatch_event('autolabo_step', {'step': '🔄 Comparaison des valeurs...'})
        df_merged = self._merge_data(df_raw, df_ref)
        logger.debug(f"Merged data: {len(df_merged)} rows")

        core.dispatch_event('autolabo_step', {'step': '📊 Génération du rapport Excel...'})
        excel_output = self._generate_excel(df_merged, df_ref)
        
        core.dispatch_event('autolabo_step', {'step': '✅ Traitement terminé !'})
        logger.info("Processing complete")

        return excel_output

    def preview_analysis(self) -> List[Dict[str, Any]]:
        """
        Run a dry-run analysis merged with reference data.
        Returns a list of records for UI preview.
        """
        try:
            df_raw = self._parse_raw()
            df_ref = self._parse_ref()
            df_merged = self._merge_data(df_raw, df_ref)
            
            # Prepare serializable result
            preview_rows = []
            
            # Get regulatory columns metadata
            reg_headers = []
            for idx, rh in enumerate(self.config.regulatory_headers):
                reg_headers.append({
                    "id": idx,
                    "title": rh.title,
                    "color": rh.color,
                    "col_idx": rh.column
                })
            
            # Identify relevant columns
            cols = self.config.columns
            c_code = str(cols.code)
            c_name = str(cols.name)
            
            # Suffixes used in merge
            s_ref = "_REF"
            s_raw = "_RAW"
            
            # Determine Raw Code Column (same logic as _merge_data)
            if cols.raw_code_col is not None:
                c_raw_code = str(cols.raw_code_col)
            else:
                c_raw_code = str(cols.code)
            
            # Determine Raw Unit Column
            c_raw_unit = str(cols.unit)

            logger.info(f"PREVIEW DEBUG: Merged Shape: {df_merged.shape}")
            if df_merged.empty:
                 logger.warning("PREVIEW DEBUG: Merged DataFrame is empty!")
            else:
                 logger.info(f"PREVIEW DEBUG: Columns: {df_merged.columns.tolist()}")
                 logger.info(f"PREVIEW DEBUG: Head(1): {df_merged.iloc[0].to_dict()}")

            # Helper to clean value (NaN -> None)
            def clean(val):
                if pd.isna(val) or val == "": return None
                return str(val)

            for _, row in df_merged.iterrows():
                # Determine status: Matched if RAW code column AND RAW unit column are present
                # Note: merge suffixes result in {code}_RAW and {unit}_RAW
                
                # Check code presence
                has_code = pd.notna(row.get(f"{c_raw_code}{s_raw}"))
                
                # Check unit presence (if unit column exists in raw)
                # Some parameters might have empty unit but be valid? user says no.
                # "paramètre ... n'a rien dans sa colonne 'unité', ça veut donc dire qu'il n'a pas été analysé"
                
                unit_val = row.get(f"{c_raw_unit}{s_raw}")
                # check if column existed and value is not NA (and not empty string strictly speaking, but pandas usually handles "" as object)
                # We should be safe with pd.notna if read_excel handled it? 
                # read_excel might treat empty cell as NaN.
                
                has_unit = pd.notna(unit_val) and str(unit_val).strip() != ""
                
                is_matched = has_code and has_unit
                
                # Extract limits from ALL regulatory headers
                reg_values = {}
                for idx, rh in enumerate(self.config.regulatory_headers):
                    c_idx = str(rh.column)
                    # Try plain, then suffixed _REF (ref columns might have suffix if collision)
                    # Typically ref columns are indices "12", "13"
                    val = row.get(c_idx)
                    if pd.isna(val) or val == "":
                         val = row.get(f"{c_idx}{s_ref}")
                    
                    reg_values[idx] = clean(val)

                item = {
                    "raw_name": clean(row.get(f"{c_code}{s_raw}")) or clean(row.get("_key")),
                    "ref_name": clean(row.get(f"{c_name}{s_ref}")) if c_name else clean(row.get(f"{c_code}{s_ref}")),
                    "matched": is_matched,
                    "regulatory_values": reg_values,
                    "samples": []
                }
                
                # Add sample values
                for s in self.samples:
                    # Sample cols are usually from Raw, so likely have _RAW suffix if name conflict
                    # But sample indices (integers) in Raw shouldn't conflict with string Ref cols.
                    # Unless Ref has '1', '2' cols? Unlikely.
                    # Let's check _merge_data logic.
                    # df_raw has cols "0", "1"... 
                    # df_ref has cols "0", "1"... 
                    # So YES, sample columns get SUFFIXED! "_RAW"
                    
                    s_idx = str(s['idx'])
                    val_col = f"{s_idx}{s_raw}" # e.g. "4_RAW"
                    
                    # Fallback if no conflict (unlikely given standardized headers logic but possible)
                    if val_col not in df_merged.columns and s_idx in df_merged.columns:
                        val_col = s_idx
                        
                    val = row.get(val_col)
                    item["samples"].append({
                        "name": s['name'],
                        "value": clean(val)
                    })
                
                preview_rows.append(item)
                
            return {
                "rows": preview_rows,
                "regulatory_headers": reg_headers
            }
            
        except Exception as e:
            logger.error(f"Preview analysis failed: {e}", exc_info=True)
            raise

    def validate(self, df: pd.DataFrame) -> bool:
        """
        Validate the structure of the input data.

        Checks if required columns/rows are present based on config.
        """
        # Simple validation for now
        if df.empty:
            return False

        # Check if Date/Name rows are reachable
        rows = len(df)
        if self.config.parsing:
             if self.config.parsing.date_row >= rows:
                 logger.warning("Date row index out of bounds")
                 return False

        return True

    def _parse_raw(self) -> pd.DataFrame:
        """Parse the raw laboratory file and detect samples."""
        logger.debug(f"Parsing raw file: {self.raw_path}")

        try:
            df = pd.read_excel(self.raw_path, header=None)
        except FileNotFoundError:
            logger.error(f"❌ Raw file not found: {self.raw_path}")
            raise
        except Exception as e:
            logger.error(f"❌ Error reading raw file {self.raw_path}: {e}")
            raise

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
        except FileNotFoundError:
            logger.error(f"❌ Reference file not found: {self.ref_path}")
            raise
        except Exception as e:
            logger.error(f"❌ Error reading reference file {self.ref_path}: {e}")
            raise

        df.columns = [str(c) for c in df.columns]

        # Add eluate section for Sols
        if self.config.formatting_mode == "sols":
            df = self._add_section_column(df)

        # Apply User Custom Rules (Epic 14)
        try:
            from ..rules import RuleManager
            rule_manager = RuleManager()
            
            # Use raw_code_col or code as the key column
            cols = self.config.columns
            key_col_ref = str(cols.code) # Default to code dict key
            
            # But apply_overrides processes the dataframe which has generic columns "0", "1", etc.
            # Wait, df is read with header=None, so columns are "0", "1", etc.
            # We need to target the column index that corresponds to the key.
            # The config object stores column INDICES. 
            
            # The generic generic.py code assumes config.columns attributes are column INDICES (integers)
            # or names if header was present. 
            # Let's verify how config is loaded. 
            # In yaml: code: 0, unit: 5. 
            # So df.columns are '0', '1'... NO. pd.read_excel(header=None) makes columns Integers 0, 1...
            # BUT line 209: df.columns = [str(c) for c in df.columns] -> Converts to "0", "1".
            
            # So if yaml says code: 0, we look for column "0".
            
            key_col_idx = str(self.config.columns.code)
            
            # To be safe, we also need to know which matrix we are in.
            # GenericLabProcessor doesn't explicitly know "eaux" or "sols", but it has config.
            # We can infer it or pass it. 
            
            # Let's add a matrix_id to GenericLabProcessor or infer from formatting_mode
            matrix_id = "sols" if self.config.formatting_mode == "sols" else "eaux"
            
            df = rule_manager.apply_overrides(df, matrix_id, key_col=key_col_idx)
            
        except Exception as e:
            logger.warning(f"Failed to apply custom rules: {e}")

        return df


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
                how="right",
                suffixes=("_REF", "_RAW")
            )
        else:
            merged = pd.merge(
                df_ref, df_raw,
                left_on="_key",
                right_on="_key",
                how="right",
                suffixes=("_REF", "_RAW")
            )

        logger.debug(f"Merged {len(merged)} rows")

        # Smart Unit Conversion: normalize raw values to reference units
        merged = self._normalize_units(merged)

        # Add virtual rows for Sols
        if self.config.virtual_rows:
            from ..virtual_rows.calculator import VirtualRowsCalculator
            calculator = VirtualRowsCalculator(
                self.config.virtual_rows,
                self.config.columns,
                self.samples
            )
            merged = calculator.add_virtual_rows(merged)

        return merged

    def _normalize_units(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize sample values to match reference units.
        
        Automatically converts values when raw and reference units differ
        (e.g., mg/L → µg/L, ng/kg → µg/kg).
        """
        from ..units import normalize_to_reference
        
        cols = self.config.columns
        unit_col_ref = str(cols.unit) + "_REF" if str(cols.unit) + "_REF" in df.columns else str(cols.unit)
        unit_col_raw = str(cols.unit) + "_RAW" if str(cols.unit) + "_RAW" in df.columns else None
        
        if not unit_col_raw or unit_col_raw not in df.columns:
            logger.debug("No raw unit column found, skipping unit normalization")
            return df
        
        conversions_made = 0
        
        for sample in self.samples:
            sample_col = sample["idx"]
            
            for idx in df.index:
                try:
                    raw_unit = str(df.at[idx, unit_col_raw]) if pd.notna(df.at[idx, unit_col_raw]) else ""
                    ref_unit = str(df.at[idx, unit_col_ref]) if pd.notna(df.at[idx, unit_col_ref]) else ""
                    
                    if not raw_unit or not ref_unit or raw_unit.lower() == ref_unit.lower():
                        continue
                    
                    raw_value = df.at[idx, sample_col]
                    if pd.isna(raw_value) or not isinstance(raw_value, (int, float)):
                        continue
                    
                    converted, was_converted = normalize_to_reference(float(raw_value), raw_unit, ref_unit)
                    
                    if was_converted:
                        df.at[idx, sample_col] = converted
                        conversions_made += 1
                        
                except Exception as e:
                    logger.debug(f"Unit conversion skipped for row {idx}: {e}")
                    continue
        
        if conversions_made > 0:
            logger.info(f"⚡ Smart Units: {conversions_made} value(s) converted")
            from modules import core
            core.dispatch_event('autolabo_step', {'step': f'⚡ {conversions_made} conversion(s) d\'unité effectuée(s)'})
        
        return df


    def _filter_config(self, indices: List[int]) -> MatrixConfig:
        """
        Create a new MatrixConfig with only the selected regulatory headers.
        Also filters the legend items to match.
        """
        # Filter headers
        selected_headers = [
            h for i, h in enumerate(self.config.regulatory_headers) 
            if i in indices
        ]
        
        # Filter regulatory_cols (indices in ref match header structure usually?)
        # config.regulatory_cols is list of INTs.
        # But regulatory_headers is list of objects.
        # We need to filter regulatory_headers.
        
        # Also filter Legend Items
        # Rule: Keep legend item if its bg_color matches any of selected headers color
        active_colors = {h.color.lower() for h in selected_headers}
        
        filtered_legend_items = [
            item for item in self.config.legend.color_items 
            if item.bg_color.lower() in active_colors
        ]
        
        # Filter regulatory_cols to match selected headers
        # Use header.column attribute
        selected_cols = [h.column for h in selected_headers]
        
        # Create copy of config
        # Use simple creation or model_copy
        # Just create dict and pass to model_copy
        
        new_legend = self.config.legend.copy(update={"color_items": filtered_legend_items})
        
        logger.info("Creating filtered config copy...")
        filtered_config = self.config.copy(update={
            "regulatory_headers": selected_headers,
            "regulatory_cols": selected_cols,
            "legend": new_legend
        })
        return filtered_config

    def _generate_excel(self, df_merged: pd.DataFrame, df_ref: pd.DataFrame) -> BytesIO:
        """Generate the Excel report with formatting."""
        from ..excel.writer import ExcelWriter
        from ..excel.formatter import ExcelFormatter
        from ..excel.legend import LegendWriter

        # Apply filtering if active headers are set
        export_config = self.config
        if self.active_reg_headers_indices is not None:
            logger.info(f"Using active regulatory headers: {self.active_reg_headers_indices}")
            try:
                export_config = self._filter_config(self.active_reg_headers_indices)
                logger.info("Config filtered successfully")
            except Exception as e:
                logger.error(f"Failed to filter config: {e}")
                # Fallback to full config if filtering fails, or re-raise?
                # For now let's just log and re-raise to see the error
                raise e

        # Initialize components with EXPORT config
        logger.info("Initializing ExcelWriter...")
        ExcelWriter(export_config, self.samples)
        logger.info("Initializing ExcelFormatter...")
        formatter = ExcelFormatter(export_config, self.samples)
        logger.info("Initializing LegendWriter...")
        legend_writer = LegendWriter(export_config.legend)

        # Generate using new architecture
        logger.info("Generating Excel report...")

        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet("Rapport")

        formats = formatter.create_formats(workbook)
        current_row = formatter.write_headers(worksheet, formats)
        current_row = formatter.write_data_rows(worksheet, df_merged, formats, current_row)
        legend_writer.write_legend(worksheet, workbook, current_row + 2)

        workbook.close()
        output.seek(0)

        logger.info("Excel report generated successfully")
        return output
