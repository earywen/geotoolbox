import pandas as pd
import xlsxwriter
from io import BytesIO
from datetime import datetime
import logging
from typing import List, Dict, Optional, Any, Union
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


# --- Base Processor ---
class BaseLabProcessor:
    """Base class for Lab Report Processing."""
    def __init__(self, raw_path: str, ref_path: str):
        self.raw_path = raw_path
        self.ref_path = ref_path
        self.samples = []
        self.config = self._get_config()

    def _get_config(self) -> Dict[str, Any]:
        """Override in subclasses."""
        return {}

    def process(self) -> BytesIO:
        """Template Method."""
        df_raw = self._parse_raw()
        df_ref = self._parse_ref()
        df_merged = self._merge_data(df_raw, df_ref)
        return self._generate_excel(df_merged, df_ref)

    def _parse_raw(self) -> pd.DataFrame:
        raise NotImplementedError

    def _parse_ref(self) -> pd.DataFrame:
        raise NotImplementedError

    def get_filename(self) -> str:
        return f"Rapport_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"


    def _merge_data(self, df_raw: pd.DataFrame, df_ref: pd.DataFrame) -> pd.DataFrame:
        raise NotImplementedError
        
    def _generate_excel(self, df_merged: pd.DataFrame, df_ref_orig: pd.DataFrame) -> BytesIO:
        # Debug logging (commented out for production)
        # logger.debug(f"Generating Excel for {self.__class__.__name__}, rows: {len(df_merged)}")
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet("Rapport")
        
        # Formats
        fmt_header_gray = workbook.add_format({'bold': True, 'bg_color': '#D9D9D9', 'border': 1, 'align': 'center', 'valign': 'vcenter', 'text_wrap': True})
        fmt_header_green = workbook.add_format({'bold': True, 'bg_color': '#C6EFCE', 'border': 1, 'align': 'center', 'valign': 'vcenter', 'text_wrap': True})
        fmt_header_orange = workbook.add_format({'bold': True, 'bg_color': '#FBCA98', 'border': 1, 'align': 'center', 'valign': 'vcenter', 'text_wrap': True})
        
        # New Colors
        fmt_header_white = workbook.add_format({'bold': True, 'bg_color': '#FFFFFF', 'border': 1, 'align': 'center', 'valign': 'vcenter', 'text_wrap': True})
        fmt_header_pink = workbook.add_format({'bold': True, 'bg_color': '#FFCCFF', 'border': 1, 'align': 'center', 'valign': 'vcenter', 'text_wrap': True})
        fmt_header_cyan = workbook.add_format({'bold': True, 'bg_color': '#CCFFFF', 'border': 1, 'align': 'center', 'valign': 'vcenter', 'text_wrap': True})
        fmt_header_yellow = workbook.add_format({'bold': True, 'bg_color': '#FFFF99', 'border': 1, 'align': 'center', 'valign': 'vcenter', 'text_wrap': True})
        fmt_header_red = workbook.add_format({'bold': True, 'bg_color': '#FF99CC', 'border': 1, 'align': 'center', 'valign': 'vcenter', 'text_wrap': True}) # Salmonish red

        fmt_param = workbook.add_format({'border': 1, 'align': 'left'})
        fmt_center = workbook.add_format({'border': 1, 'align': 'center'})
        # Changed to Blue to match User Request
        fmt_family = workbook.add_format({'bold': True, 'bg_color': '#0070C0', 'font_color': 'white', 'border': 1})
        # print("[DEBUG] Workbook created & Formats defined")
        
        # --- Headers ---
        current_row = 0
        
        # Col 0: Paramètre
        worksheet.write(current_row, 0, "Paramètre", fmt_header_gray)
        worksheet.set_column(0, 0, 30)
        
        # Col 1: Unité
        worksheet.write(current_row, 1, "Unité", fmt_header_gray)
        worksheet.set_column(1, 1, 10)
        
        # Regulatory Headers
        reg_headers = self.config.get('reg_headers', [])
        col_offset = 2
        
        for idx, (title, color) in enumerate(reg_headers):
            fmt = fmt_header_orange # Default
            if color == 'green': fmt = fmt_header_green
            elif color == 'white': fmt = fmt_header_white
            elif color == 'pink': fmt = fmt_header_pink
            elif color == 'cyan': fmt = fmt_header_cyan
            elif color == 'yellow': fmt = fmt_header_yellow
            elif color == 'red': fmt = fmt_header_red
            worksheet.write(current_row, col_offset + idx, title, fmt)
            worksheet.set_column(col_offset + idx, col_offset + idx, 15)
            
        col_offset += len(reg_headers)
        
        # Sample Headers
        for idx, s in enumerate(self.samples):
            # Write Name
            worksheet.write(current_row, col_offset + idx, s.get('name', f"Ech {idx+1}"), fmt_header_gray)
            # Write Date in Row+1
            worksheet.write(current_row + 1, col_offset + idx, s.get('date', '-'), fmt_header_gray)
            # Write Location in Row+2
            worksheet.write(current_row + 2, col_offset + idx, "Localisation", fmt_header_gray)
            worksheet.set_column(col_offset + idx, col_offset + idx, 12)
            
        # Extra Rows Labels
        worksheet.write(current_row + 1, 0, "", fmt_header_gray) # Empty row under Param
        worksheet.write(current_row + 2, 0, "", fmt_header_gray) # Empty row under Param
        worksheet.write(current_row + 1, col_offset-1, "Date de prélèvement", fmt_header_gray) # Just aligned right?
        worksheet.write(current_row + 2, col_offset-1, "Localisation", fmt_header_gray)
        
        current_row += 3 # Start Data
        # print(f"[DEBUG] Headers Written. Current Row: {current_row}")
        
        # --- Data Loop ---
        # print("[DEBUG] Accessing Config for Loop")
        c_name_idx = str(self.config['ref_col_name'])
        c_unit = str(self.config['ref_col_unit'])
        reg_cols_idx = self.config['reg_cols']
        # print(f"[DEBUG] Config Loaded. NameIdx: {c_name_idx}")
        
        pending_family_header = None
        
        # Determine Color Map for Limits
        # print("[DEBUG] Building Color Map")
        col_color_map = {}
        for i, (title, color) in enumerate(reg_headers):
            key_col = f"{reg_cols_idx[i]}_REF"
            col_color_map[key_col] = color
            # print(f"[DEBUG] Color Map: {key_col} -> {color}")
            
        # print("[DEBUG] Starting Iterrows")
        for i, (idx, row) in enumerate(df_merged.iterrows()):
            # merged columns have suffixes _REF, _RAW (or handled by subclass)
            
            # Fix: Check for _REF suffix for Name column too
            p_name = row.get(f"{c_name_idx}_REF") 
            if pd.isna(p_name):
                 p_name = row.get(c_name_idx)

            p_unit = row.get(f"{c_unit}_REF")
            if pd.isna(p_unit): p_unit = row.get(c_unit) # Fallback if no suffix
            
            # Fallback: If Name is missing, checking if it's a Header row (Title is in Family Column 4)
            c_family_idx = str(self.config.get('ref_col_family', 4))
            
            if pd.isna(p_name):
                 # Try grabbing content from Family Column
                 possible_title = row.get(f"{c_family_idx}_REF")
                 if pd.isna(possible_title): possible_title = row.get(c_family_idx)
                 
                 # if we have a title, and NO unit, assume it's a Family Header
                 if pd.notna(possible_title) and pd.isna(p_unit):
                      p_name = possible_title

            # if i < 10:
            #      print(f"[DEBUG] Row {i} | Key: {row.get('_key')} | Name: {p_name} | Unit: {p_unit}")

            if pd.isna(p_name): continue
            
            # 1. Family Header Check
            if pd.isna(p_unit) or str(p_unit).strip() == "":
                pending_family_header = str(p_name)
                continue
                
            # 2. Data Check
            has_data = False
            
            # DEBUG ROW 1580 (REMOVED)
            
            raw_unit = row.get(f"{c_unit}_RAW")
            conversion_factor = self._get_conversion_factor(str(raw_unit) if pd.notna(raw_unit) else "", str(p_unit))
            
            sample_values = []
            for s in self.samples:
                # Subclass ensures Sample Columns are accessible
                raw_idx = s['idx']
                col_key = f"{raw_idx}_RAW"
                
                raw_val = row.get(col_key)
                if pd.isna(raw_val):
                     # Fix: Ensure raw_idx is string for fallback lookup
                     raw_val = row.get(str(raw_idx)) 

                if pd.notna(raw_val) and str(raw_val).strip() != "":
                    has_data = True
                    sample_values.append(str(raw_val))
                else:
                    sample_values.append("-")
            
            if not has_data: continue
            
            # Write Family Header if pending
            # 1b. FIX: Suppress Duplicate Header for Virtual Rows
            # If we are about to write a Virtual Row and a header is pending (likely duplicate), kill it.
            row_key = str(row.get('_key', ''))
            if row_key in ['13906', '13739']: 
                 pending_family_header = None

            if pending_family_header:
                 total_cols = col_offset + len(self.samples)
                 worksheet.merge_range(current_row, 0, current_row, total_cols - 1, pending_family_header, fmt_family)

                 current_row += 1
                 pending_family_header = None
                 
            # Write Row
            worksheet.write(current_row, 0, str(p_name), fmt_param)
            worksheet.write(current_row, 1, str(p_unit), fmt_center)
            
            # Limits
            parsed_limits = {}
            for i, src_col in enumerate(reg_cols_idx):
                col_key = f"{src_col}_REF"
                val = row.get(col_key)
                if pd.isna(val): val = row.get(str(src_col)) # Fallback
                
                # DEBUG REG (ONCE)
                if i < 5 and idx == 0: # First Reg Col for first 5 rows
                     pass  # Debug logging disabled

                if pd.isna(val) or str(val).strip() in ["nan", ""]: 
                    val = "-"
                
                val_str = str(val)
                # Write Limit
                written = False
                if not any(c in val_str for c in ['<', '>', 'e', 'E', 'Entre', 'entre']):
                    try:
                         f_val = float(val_str.replace(',', '.').strip())
                         worksheet.write_number(current_row, 2 + i, f_val, fmt_center)
                         written = True
                    except: pass
                if not written:
                    worksheet.write(current_row, 2 + i, val_str, fmt_center)
                    
                limit_float = self._parse_limit_value(val_str)
                if limit_float is not None:
                    parsed_limits[col_key] = limit_float # Use Key for mapping back to default color? 
                    # Actually parsing logic uses column index to find color.
                    # We stored col_key -> limit. 
                    
            # Values
            for i, val_str in enumerate(sample_values):
                cell_fmt = fmt_center
                s_val = self._parse_sample_value(val_str)
                
                if s_val is not None:
                    s_val = s_val * conversion_factor
                    
                    # Check formatting mode
                    formatting_mode = self.config.get('formatting_mode', 'eaux')
                    
                    if formatting_mode == 'sols':
                        # Sols-specific Conditional Formatting (ISDI/ISDI+/ISDND/ISDD)
                        limit_isdd = parsed_limits.get('16_REF')
                        limit_isdnd = parsed_limits.get('14_REF')
                        limit_isdi_plus = parsed_limits.get('13_REF')
                        limit_isdi = parsed_limits.get('11_REF')
                        limit_hcsp_dep = parsed_limits.get('10_REF')
                        
                        if limit_isdd is not None and s_val >= limit_isdd:
                            cell_fmt = workbook.add_format({'border': 1, 'align': 'center', 'bg_color': '#FFFFFF', 'font_color': 'red'})
                        elif limit_isdnd is not None and s_val >= limit_isdnd:
                            cell_fmt = workbook.add_format({'border': 1, 'align': 'center', 'bg_color': '#FF99CC'})
                        elif limit_isdi_plus is not None and s_val >= limit_isdi_plus:
                            cell_fmt = workbook.add_format({'border': 1, 'align': 'center', 'bg_color': '#FFFF99'})
                        elif limit_isdi is not None and s_val >= limit_isdi:
                            cell_fmt = workbook.add_format({'border': 1, 'align': 'center', 'bg_color': '#CCFFFF'})
                        elif limit_hcsp_dep is not None and s_val >= limit_hcsp_dep:
                            cell_fmt = workbook.add_format({'border': 1, 'align': 'center', 'bg_color': '#FFCCFF', 'font_color': 'red'})
                    else:
                        # Eaux Souterraines Conditional Formatting (green/yellow/orange)
                        matched_color = None
                        for limit_col, limit_val in parsed_limits.items():
                            if s_val >= limit_val:
                                color = col_color_map.get(limit_col, 'green')
                                if color == 'orange': matched_color = 'orange'
                                elif color == 'yellow' and matched_color != 'orange': matched_color = 'yellow'
                                elif color == 'green' and matched_color is None: matched_color = 'green'
                                
                        if matched_color == 'orange':
                             cell_fmt = workbook.add_format({'border': 1, 'align': 'center', 'bg_color': '#FBCA98'}) 
                        elif matched_color == 'yellow':
                             cell_fmt = workbook.add_format({'border': 1, 'align': 'center', 'bg_color': '#FFE699'})
                        elif matched_color == 'green':
                             cell_fmt = workbook.add_format({'border': 1, 'align': 'center', 'bg_color': '#C6EFCE'})
                
                # Write Value
                written_number = False
                if not any(c in val_str for c in ['<', '>', 'e', 'E']) and val_str != "-":
                    try:
                        f_v = float(val_str.replace(',', '.'))
                        c_v = f_v * conversion_factor
                        worksheet.write_number(current_row, col_offset + i, c_v, cell_fmt)
                        written_number = True
                    except: pass
                elif val_str.startswith('<') and conversion_factor != 1.0:
                    try:
                        num = float(val_str[1:].replace(',', '.'))
                        new = num * conversion_factor
                        s_new = f"<{new}".replace('.', ',')
                        worksheet.write(current_row, col_offset + i, s_new, cell_fmt)
                        written_number = True
                    except: pass
                    
                if not written_number:
                    worksheet.write(current_row, col_offset + i, val_str, cell_fmt)
            
            current_row += 1
            
        # --- Legend (Hardcoded based on Model File) ---
        current_row += 2
        
        # Check formatting mode for legend
        formatting_mode = self.config.get('formatting_mode', 'eaux')
        
        if formatting_mode == 'sols':
            # Sols-specific Legend
            fmt_legend_text = workbook.add_format({'text_wrap': True, 'valign': 'top', 'font_size': 9})
            
            legend_notes = [
                "LQ : Limite de quantification du laboratoire / n.d. : Non détecté",
                "(1) Valeurs en gras : source = Teneurs totales en éléments traces métalliques dans les sols, Denis BAIZE, INRA. En italique : source = ATSDR",
                "(2) Valeurs limites indicatives issues des textes européens, des arrêtés ministériel et des critères communément appliqués par les centres de stockage",
                "",
                "(3) [Pour l'acceptation en ISDI], une valeur limite plus élevée peut être admise, à condition que la valeur limite de 500 mg/kg de matière sèche soit respectée pour le carbone organique total sur éluat.",
                "(4) Valeur limite des ISDI : valeur non règlementaire mais parfois appliquée par les gestionnaires d'ISDI",
                "(5) Si le déchet ne respecte pas au moins une des valeurs fixées pour le chlorure, le sulfate ou la fraction soluble, le déchet peut être encore jugé conforme aux critères d'admission [en ISDI].",
            ]
            
            for note in legend_notes:
                if note:
                    worksheet.merge_range(current_row, 0, current_row, 8, note, fmt_legend_text)
                current_row += 1
            
            current_row += 1
            
            color_legend = [
                ("#FFFFFF", "black", "Concentration supérieure au bruit de fond et inférieure aux valeurs limites des ISDI"),
                ("#FFCCFF", "black", "Concentration supérieure au seuil de vigilance du HCSP"),
                ("#FFCCFF", "red", "Concentration supérieure au seuil de dépistage du HCSP"),
                ("#CCFFFF", "black", "Concentration supérieure aux valeurs limites des ISDI et inférieure aux valeurs limites des ISDI+"),
                ("#FFFF99", "black", "Concentration supérieure aux valeurs limites des ISDI+ et inférieure aux valeurs limites des ISDND"),
                ("#FF99CC", "black", "Concentration supérieure aux valeurs limites des ISDND et inférieure aux valeurs limites des ISDD"),
                ("#FFFFFF", "red", "Concentration supérieure aux valeurs limites des ISDI, des ISDI+, des ISDND, des ISDD"),
            ]
            
            for bg_color, font_color, description in color_legend:
                fmt_color = workbook.add_format({
                    'bg_color': bg_color, 
                    'border': 1, 
                    'text_wrap': True, 
                    'valign': 'vcenter',
                    'font_color': font_color
                })
                worksheet.merge_range(current_row, 0, current_row, 8, description, fmt_color)
                current_row += 1
        else:
            # Eaux Legend (from original dynamic extraction - simplified)
            worksheet.write(current_row, 0, "Légende :", fmt_header_gray)
            current_row += 1

        workbook.close()
        output.seek(0)
        return output

    def _get_conversion_factor(self, raw_unit: str, ref_unit: str) -> float:
        if not raw_unit or not ref_unit: return 1.0
        u1 = str(raw_unit).lower().strip().replace("ug", "µg")
        u2 = str(ref_unit).lower().strip().replace("ug", "µg")
        if u1 == u2: return 1.0
        if "µg" in u1 and "mg" in u2: return 0.001
        if "mg" in u1 and "µg" in u2: return 1000.0
        return 1.0

    def _parse_limit_value(self, txt: str) -> Optional[float]:
        if not txt or txt == "-": return None
        txt = txt.strip().lower()
        if "entre" in txt:
             try: return float(txt.split()[-1].replace(',', '.'))
             except: return None
        if "(" in txt: txt = txt.split("(")[0].strip()
        txt = txt.replace("<", "").replace(">", "").strip()
        try: return float(txt.replace(",", "."))
        except: return None

    def _parse_sample_value(self, txt: str) -> Optional[float]:
        if not txt or txt == "-": return None
        txt = txt.strip().lower()
        if "<" in txt: return 0.0
        try: return float(txt.replace(",", "."))
        except: return None


# --- Eaux Processor ---
class EauxProcessor(BaseLabProcessor):
    def _get_config(self) -> Dict[str, Any]:
        return {
            "ref_data_start_row": 30, 
            "ref_col_name": 1,
            "ref_col_unit": 2,
            "reg_cols": [3, 4],
            "reg_headers": [("Limite de Qualité (Eaux Brutes)", "orange"), ("Référence de Qualité (Eaux brutes)", "green")],
            "legend_start_row": 500, # Approximate, Eaux logic handles this differently?
            # Actually Eaux doesn't have a Legend defined in previous code?
            # Let's keep it safe.
            "legend_end_row": 600
        }

    def _parse_ref(self) -> pd.DataFrame:
        try:
            df = pd.read_excel(self.ref_path, header=None)
        except Exception as e:
            raise ValueError(f"Erreur REF: {e}")
        df.columns = [str(c) for c in df.columns]
        return df

    def _parse_raw(self) -> pd.DataFrame:
        df = pd.read_excel(self.raw_path, header=None)
        df.columns = [str(c) for c in df.columns]
        
        # Eaux Logic: Search keywords
        date_row_idx = -1
        for i in range(min(30, len(df))):
            row_str = " ".join(df.iloc[i].astype(str).values)
            if "Date" in row_str and "chantillon" in row_str:
                date_row_idx = i
                break
        if date_row_idx == -1: date_row_idx = 0
        
        name_row_idx = date_row_idx + 2
        
        self.samples = []
        date_vals = df.iloc[date_row_idx]
        name_vals = df.iloc[name_row_idx]
        
        for col_idx in range(len(date_vals)):
            n_val = str(name_vals.iloc[col_idx] if col_idx < len(name_vals) else "").strip()
            if n_val.lower() not in ['nan', 'résultat', 'resultat', 'lithologie', 'paramètre', 'unité'] and len(n_val) > 1:
                d_val = str(date_vals.iloc[col_idx] if col_idx < len(date_vals) else "").strip()
                fmt_date = d_val
                if len(d_val) == 8 and d_val.isdigit():
                    fmt_date = f"{d_val[6:8]}/{d_val[4:6]}/{d_val[0:4]}"
                
                self.samples.append({
                    "idx": col_idx,
                    "name": n_val,
                    "date": fmt_date
                })
        return df

    def _merge_data(self, df_raw: pd.DataFrame, df_ref: pd.DataFrame) -> pd.DataFrame:
        c_ref_name = str(self.config['ref_col_name'])
        if c_ref_name in df_ref.columns:
            df_ref["_key"] = df_ref[c_ref_name].astype(str).str.strip().str.lower()
        else:
            df_ref["_key"] = ""
        
        df_raw["_key"] = df_raw["0"].astype(str).str.strip().str.lower()
        
        return pd.merge(df_ref, df_raw, left_on="_key", right_on="_key", how="left", suffixes=("_REF", "_RAW"))


# --- Sols Processor ---
class SolsProcessor(BaseLabProcessor):
    def _get_config(self) -> Dict[str, Any]:
        return {
            "ref_data_start_row": 13, # Correct Start
            "ref_col_code": 0, 
            "ref_col_name": 1, 
            "ref_col_unit": 5, # Correct Unit Col
            "ref_col_family": 4, # NEW: Headers are here!
            "reg_cols": [6, 10, 11, 13, 14, 16],
            "formatting_mode": "sols",  # Flag for sols-specific conditional formatting
            "reg_headers": [
                ("Bruit de fond (1)", "white"),
                ("HCSP (seuil de vigilance / dépistage)", "pink"),
                ("Valeurs limite des ISDI", "white"),
                ("Valeurs limites des ISDI + (ISDI aménagées) (2)", "cyan"),
                ("Valeurs limites des ISDND (2)", "yellow"),
                ("Valeurs limites des ISDD (2)", "red")
            ],
            "legend_start_row": 652,
            "legend_end_row": 667,
            "legend_key_col": 3,
            "legend_val_col": 4,
            # Virtual Rows for Sums (Since keys 13906/13739 are missing in Ref)
            "virtual_rows": {
                "13906": {
                    "name": "Somme 7 PCB (Ballschmiter)", 
                    "unit": "mg/kg M.S.",
                    # Union of Keys (Standard + Agrolab Long Codes) to ensure match
                    "components": ["1594", "1489", "1490", "10120", "1491", "1492", "1493",
                                   "13899", "13900", "13901", "13902", "13903", "13904", "13905"],
                    # Regulatory limits from Ref Row 258 (Cols 6, 10, 11, 13, 14, 16)
                    "ref_limits": {6: "LQ", 10: "-", 11: "1", 13: "1", 14: "50", 16: "50"}
                },
                "13739": {
                    "name": "HAP (EPA) - somme", 
                    "unit": "mg/kg M.S.",
                    # ORDER MATTERS for Anchoring! Last item is checked first.
                    "components": [
                        "1515", "11191", "1516", "13743", "1517", "13734", "1518", "13748",
                        "1519", "13735", "1520", "13742", "1521", "13745", "1522", "13738",
                        "1523", "13736", "1636", "1524", "13729", "11140", "13732", "1638",
                        "11142", "13737", "1639", "1527", "13744", "1623", "1528", "13741",
                        "1529", "13740", "1624", "1530", "13749", "1625"
                    ],
                    # Regulatory limits from Ref Row 128
                    "ref_limits": {6: "LQ", 10: "-", 11: "50", 13: "50", 14: "500", 16: "1000"}
                },
                "99901": {
                    "name": "Somme des BTEX",
                    "unit": "mg/kg M.S.",
                    "components": ["1619", "806", "1512", "1513", "1628"],
                    # Regulatory limits from Ref Row 153
                    "ref_limits": {6: "LQ", 10: "-", 11: "6", 13: "6", 14: "30", 16: "200"}
                },
                "99902": {
                    "name": "Somme des COHV",
                    "unit": "mg/kg M.S.",
                    "components": [
                        "1679", "1523", "1531", "1522", "4401", "1484", "11243", "892", "2164", 
                        "4402", "1458", "1622", "1469", "1485", "19148", "458", "745", "1612", "19799"
                    ],
                    # Regulatory limits from Ref Row 200
                    "ref_limits": {6: "LQ", 10: "-", 11: "2", 13: "2", 14: "10", 16: "100"}
                }
            },
            "key_aliases": {
                # Map Raw Key -> Ref Key
                "50521": "43425", # >C6-C8
                "46226": "43426"  # >C8-C10
            }
        }
    
    def _add_section_column(self, df: pd.DataFrame) -> pd.DataFrame:
        """Adds 'is_eluate' column based on 'ANALYSES SUR ELUAT'."""
        df["is_eluate"] = False
        eluate_found = False
        for idx in df.index:
            # Check row string robustly (ignore spaces)
            row_vals = [str(x).upper() for x in df.loc[idx].values]
            row_str = "".join(row_vals).replace(" ", "")
            if "ANALYSESSURELUAT" in row_str or "ANALYSESURELUAT" in row_str:
                eluate_found = True
            
            if eluate_found:
                 df.at[idx, "is_eluate"] = True
        return df

    def _parse_ref(self) -> pd.DataFrame:
        try:
            df = pd.read_excel(self.ref_path, header=None)
        except Exception as e:
            raise ValueError(f"Erreur REF: {e}")
        # Force string columns for consistent merging/access
        df.columns = df.columns.astype(str)
        return self._add_section_column(df)

    def _parse_raw(self) -> pd.DataFrame:
        df = pd.read_excel(self.raw_path, header=None)
        # Force string columns
        df.columns = df.columns.astype(str)
        
        # 1. Section Detection
        df = self._add_section_column(df)
        
        # 2. Sample Detection
        # Sols logic: Date at Row 0?
        date_row_idx = 0
        name_row_idx = 2
        
        self.samples = []
        date_vals = df.iloc[date_row_idx]
        name_vals = df.iloc[name_row_idx]
        
        for col_idx in range(len(date_vals)):
            n_val = str(name_vals.iloc[col_idx] if col_idx < len(name_vals) else "").strip()
            
            # Exclude Metadata columns
            if n_val.lower() in ["nom d'échantillon", "unité", "unit", "unite"]:
                continue
                
            if n_val.lower() not in ['nan', 'résultat', 'resultat', 'lithologie'] and len(n_val) > 1:
                d_val = str(date_vals.iloc[col_idx] if col_idx < len(date_vals) else "").strip()
                fmt_date = d_val
                if len(d_val) == 8 and d_val.isdigit():
                    fmt_date = f"{d_val[6:8]}/{d_val[4:6]}/{d_val[0:4]}"
                
                self.samples.append({
                    "idx": col_idx,
                    "name": n_val,
                    "date": fmt_date
                })
        return df

    def _merge_data(self, df_raw: pd.DataFrame, df_ref: pd.DataFrame) -> pd.DataFrame:
        # print("\n[DEBUG] --- MERGING DATA ---")
        
        # DEBUG: DUMP REF TO SEE HEADERS (Removed)
        c_ref_code = str(self.config.get('ref_col_code', 0))
        c_raw_code = str(self.config.get('raw_col_code', 2))
        
        # Process Ref Keys
        if c_ref_code in df_ref.columns:
             df_ref["_key"] = df_ref[c_ref_code].astype(str).str.replace(r'\.0$', '', regex=True).str.strip().str.lower()
             # Fix: Treat 'nan' as actual NaN to avoid matching empty keys
             df_ref.loc[df_ref["_key"].isin(['nan', 'none', '']), "_key"] = pd.NA
        else:
             df_ref["_key"] = pd.NA
             
        if c_raw_code in df_raw.columns:
             df_raw["_key"] = df_raw[c_raw_code].astype(str).str.replace(r'\.0$', '', regex=True).str.strip().str.lower()
             # Fix: Treat 'nan' as actual NaN
             df_raw.loc[df_raw["_key"].isin(['nan', 'none', '']), "_key"] = pd.NA
        else:
             df_raw["_key"] = pd.NA
             
        # Debug
        # print(f"[DEBUG] Ref Keys Valid: {df_ref['_key'].nunique()}")
        # print(f"[DEBUG] Raw Keys Valid (Before Drop): {df_raw['_key'].nunique()}")
        
        # 1. Drop Raw rows with no key (prevents Empty <-> Empty match)
        df_raw = df_raw.dropna(subset=['_key'])
        
        # FILTER: Keep only valid result rows (Heuristic based on Col '6')
        # Prevents merging Metadata/Date rows sharing the same Code.
        def is_valid_result_row(x):
            s = str(x).strip()
            if s == "" or s.lower() in ["nan", "none"]: return True # Keep empty, might be ND
            # If contains letters and not < (e.g. "SOLS", "BGP"), it's garbage
            if any(c.isalpha() for c in s) and "<" not in s: 
                return False
            # Check for large integers (Dates 2025..., IDs)
            try:
                # Remove < or > or ,
                clean = s.replace("<", "").replace(">", "").replace(",", ".").replace(" ", "")
                if clean == "": return True
                f = float(clean)
                if f > 200000: return False # Date or ID
                return True
            except:
                return True # Allow weird strings if unsure, but letters caught above

        if "6" in df_raw.columns:
             before_len = len(df_raw)
             df_raw = df_raw[df_raw["6"].apply(is_valid_result_row)]
             # print(f"[DEBUG] Garbage Filter: Dropped {before_len - len(df_raw)} rows (Metadata/Dates)")

        # 2. Drop Duplicates in Raw (Safety net)
        df_raw = df_raw.drop_duplicates(subset=['_key', 'is_eluate'])
        
        # --- KEY ALIASING ---
        aliases = self.config.get('key_aliases', {})
        if aliases:
             # Cast raw keys to str for safe mapping
             df_raw['_key'] = df_raw['_key'].astype(str).replace(aliases)

        # print(f"[DEBUG] Raw Keys Valid (After Drop): {len(df_raw)}")
        
        # 3. Check REF Duplicates
        ref_dups = df_ref[df_ref.duplicated(subset=['_key', 'is_eluate'], keep=False)]
        # Debug: ref_dups count (disabled for production)
             
        # 4. Check specific keys (disabled for production)

        # Perform Merge (Rows with NaN keys will not be merged)

        # Perform Merge (Rows with NaN keys will not be merged)
        
        # Check Eluate Flags
        n_ref_eluate = len(df_ref[df_ref['is_eluate']])
        n_raw_eluate = len(df_raw[df_raw['is_eluate']])
        # print(f"[DEBUG] Ref Eluate Rows: {n_ref_eluate}")
        # print(f"[DEBUG] Raw Eluate Rows: {n_raw_eluate}")

        # Merge
        merged = pd.merge(df_ref, df_raw, left_on=["_key", "is_eluate"], right_on=["_key", "is_eluate"], how="left", suffixes=("_REF", "_RAW"))
        # print(f"[DEBUG] Merged Matrix Size: {len(merged)}")
        
        # Verify Matches
        matched = merged[merged[f"0_RAW"].notna()]
        # print(f"[DEBUG] Rows with Data Match (based on Col 0 name): {len(matched)}")

        virtual_rows = self.config.get('virtual_rows', {})
        if virtual_rows:
            # print(f"[DEBUG] Injecting {len(virtual_rows)} Virtual Rows...")
            rows_to_add = []
            
            # Helper to parse value
            def parse_val(v):
                if pd.isna(v) or str(v).strip() in ['-', '', 'nan', 'NAN']: return 0.0, True # Is Empty/Zero
                s = str(v).replace(',', '.').strip()
                is_lower = s.startswith('<')
                try:
                    num = float(s.replace('<', '').strip())
                except:
                    num = 0.0
                return num, is_lower

            # Iterate Virtual Definitions
            for v_key, v_cfg in virtual_rows.items():
                # print(f"  -> Processing Virtual Key {v_key} ({v_cfg['name']})")
                
                # Check if it already exists? If distinct key, likely no.
                
                # Create Base Row
                new_row = {
                    '_key': v_key,
                    'is_eluate': False, # Usually sums are on solid
                    # Populate Ref Columns for Display
                    f"{str(self.config.get('ref_col_name', 1))}_REF": v_cfg['name'],
                    f"{str(self.config.get('ref_col_unit', 5))}_REF": v_cfg['unit'],
                     # Ensure fallback non-suffixed columns exist too if code looks there
                    str(self.config.get('ref_col_name', 1)): v_cfg['name'],
                    str(self.config.get('ref_col_unit', 5)): v_cfg['unit']
                }
                
                # --- INJECT REGULATORY LIMITS from ref_limits config ---
                ref_limits = v_cfg.get('ref_limits', {})
                for col_idx, limit_val in ref_limits.items():
                    new_row[f"{col_idx}_REF"] = limit_val
                
                # Compute Values for each Sample
                components = v_cfg['components']
                # Find matching component rows
                df_comps = merged[merged['_key'].astype(str).isin(components)]
                
                # Identify columns to process: All columns from df_raw (samples)
                # They might be suffixed with _RAW in merged if they collided with Ref
                sample_cols = [c for c in df_raw.columns if c not in ['_key', 'is_eluate']]
                
                for s_col in sample_cols:
                    # Determine name in merged
                    r_col = f"{s_col}_RAW" if f"{s_col}_RAW" in merged.columns else s_col
                    if r_col not in merged.columns: continue

                    # Calculate Sum for this column
                    total_sum = 0.0
                    sum_limits = 0.0
                    all_lower = True
                    has_data = False
                    
                    values = df_comps[r_col].values
                    
                    total_sum = 0.0
                    all_lower = True
                    has_data = False
                    
                    sum_limits = 0.0

                    for val in values:
                        num, is_lower = parse_val(val)
                        if pd.notna(val) and str(val).strip() not in ['-', '']:
                             has_data = True
                        
                        if not is_lower:
                            all_lower = False
                            total_sum += num
                        else:
                            # Lower bound: treat as 0 for sum
                            sum_limits += num 
                            pass 
                    
                    if not has_data:
                         new_row[r_col] = "-"
                    elif all_lower:
                         # User Request: If all components are < LOQ, display "n.d." instead of sum of LOQs
                         new_row[r_col] = "n.d."
                    else:
                         # Mix detected and undetectd (0)
                         new_row[r_col] = f"{total_sum:.3f}" # Detected Sum
                
                if 'insert_after' in v_cfg:
                     anchor_candidates = [str(v_cfg['insert_after'])]
                else:
                     # Default: After the last component
                     anchor_candidates = [str(c) for c in reversed(components)]
                     
                     if v_key == '13739': # HAP DEBUG
                          # print(f"\n[DEBUG] MATCHING HAP ANCHOR...")
                          # print(f"[DEBUG] Candidates (Reversed): {anchor_candidates[:10]}...")
                          # Find Indeno/Benzo keys in merged
                          for idx, r in merged.iterrows():
                               name = str(r.get('1_REF', '')) # Name Ref
                               k = str(r['_key'])
                               if 'Indeno' in name or 'Indéno' in name or 'Benzo' in name:
                                    pass  # Debug logging disabled

                
                idx_anchor = None
                for candidate in anchor_candidates:
                     matches = merged.index[merged['_key'].astype(str) == candidate].tolist()
                     if matches:
                          idx_anchor = matches[0]
                          break
                
                if idx_anchor is not None:
                     new_row['_temp_sort_index'] = idx_anchor + 0.1
                else:
                     new_row['_temp_sort_index'] = len(merged) + 100 # End fallback

                rows_to_add.append(new_row)
            
            if rows_to_add:
                # Assign default sort index to current rows
                if '_temp_sort_index' not in merged.columns:
                     merged['_temp_sort_index'] = merged.index

                df_virtual = pd.DataFrame(rows_to_add)
                merged = pd.concat([merged, df_virtual], ignore_index=False)
                
                # Sort and Clean
                merged.sort_values(by='_temp_sort_index', inplace=True)
                merged.reset_index(drop=True, inplace=True)
                merged.drop(columns=['_temp_sort_index'], inplace=True, errors='ignore')
            
        return merged


# --- Main Factory ---
def process_and_export(file_paths: List[str], model_id: str = "es", target_path: str = "", provider_id: str = "agrolab") -> Dict[str, Any]:
    """
    API Entry Point for laboratory report processing.
    
    Uses the new config-driven GenericLabProcessor when possible,
    with fallback to legacy processors if needed.
    
    Args:
        file_paths: List of raw laboratory file paths
        model_id: Matrix identifier ("es" for eaux, "sols" for sols, "sup" for surface)
        target_path: Optional target directory for output
        provider_id: Laboratory provider ID (agrolab, eurofins, etc.)
        
    Returns:
        Dict with 'success' and 'output_path' or 'error'
    """
    try:
        if not file_paths:
            return {"success": False, "error": "No file"}
        
        raw_path = file_paths[0]
        base = core.get_base_path()
        
        # Map model_id to matrix name
        matrix_map = {
            "es": "eaux",
            "sols": "sols",
            "sup": "sup"
        }
        matrix = matrix_map.get(model_id, "eaux")
        
        if matrix == "sup":
            return {"success": False, "error": "Eaux de Surface not impl."}
        
        # Reference file paths
        ref_paths = {
            "eaux": os.path.join(base, "ressources", "Eaux souterraines", 
                                 "Eaux souterraines familles et paramètres et valeurs réglementaires.xlsx"),
            "sols": os.path.join(base, "ressources", "Sols", 
                                 "Sols - familles et paramètres et valeurs réglementaires.xlsx")
        }
        
        ref_path = ref_paths.get(matrix)
        if not ref_path or not os.path.exists(ref_path):
            return {"success": False, "error": f"Ref not found: {ref_path}"}
        
        # Try new config-driven processor first
        try:
            from .autolabo_core.config.registry import ProviderRegistry
            from .autolabo_core.processors.base import GenericLabProcessor
            
            registry = ProviderRegistry()
            provider = registry.load_provider(provider_id)
            config = registry.load_matrix(provider_id, matrix)
            
            processor = GenericLabProcessor(raw_path, ref_path, config, provider)
            logging.info(f"Using GenericLabProcessor for {provider.name}/{matrix}")
            
        except Exception as e:
            # Fallback to legacy processors
            logging.warning(f"Falling back to legacy processor: {e}")
            
            if matrix == "sols":
                processor = SolsProcessor(raw_path, ref_path)
            else:
                processor = EauxProcessor(raw_path, ref_path)
        
        # Process
        try:
            excel_io = processor.process()
            logging.info("Processing completed successfully")
        except Exception as e:
            logging.error(f"Processing error: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
        
        # Save output
        matrix_label = "Sols" if matrix == "sols" else "Eaux"
        out_name = f"Rapport_{matrix_label}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        out_dir = target_path if target_path and os.path.isdir(target_path) else core.get_user_dir()
        out_path = os.path.join(out_dir, out_name)
        
        with open(out_path, "wb") as f:
            f.write(excel_io.getvalue())
        
        logging.info(f"Report saved: {out_path}")
        return {"success": True, "output_path": out_path}

    except Exception as e:
        logging.error(f"AutoLabo Error: {e}", exc_info=True)
        return {"success": False, "error": str(e)}

# ==========================================
# UI LOADER
# ==========================================
def get_ui_content() -> str:
    """Returns the HTML fragment for the AutoLabo module."""
    return core.load_template("autolabo.html")

# Remove old LabReportProcessor to avoid confusion
if __name__ == "__main__":
    pass
