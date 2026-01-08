import pandas as pd
import xlsxwriter
import logging
import os

logger = logging.getLogger(__name__)

def generate_excel_for_layer(rows, layer_key, folder_path, config):
    try:
        if not rows: 
            logger.warning(f"[Export] No rows for layer {layer_key}")
            return None
        
        fname = f"{layer_key}.xlsx"
        full_path = os.path.join(folder_path, fname)
        logger.info(f"[Export] Generating {full_path} with {len(rows)} rows")
        
        df = pd.DataFrame(rows)
        
        rename_map = {
            "code_metier": "Référence",
            "code_ssp": "Référence",
            "nom_etablissement": "Etablissement / Adresse",
            "etat_activite": "Etat d'occupation du site",
            "etat": "Etat d'occupation du site",
            "activite_principale": "Activité",
            "fiche_risque": "Fiche GéoRisques",
            "adresse": "Adresse",
            "code_postal": "Code Postal",
            "nom_commune": "Commune",
            "geo_dist_dir": "Distance / Position",
            "hydro_context": "Amont / Aval (Topo)",
            # --- NOUVEAUX CHAMPS IGN ---
            "numero": "Numéro Parcelle",
            "section": "Section",
            "nom_officiel": "Commune (Admin)",
            "usage_1": "Usage Bâtiment",
            "hauteur": "Hauteur (m)",
            "nature": "Nature",
            "toponyme": "Toponyme",
            "code_insee": "INSEE",
            "population": "Population",
            # --- BSS-specific renames ---
            "code_bss": "Code BSS",
            "commune_actuelle": "Commune",
            "nature_pe": "Nature de l'ouvrage",
            "liste_masse_eau": "Nappe captée",
            "lien_infoterre": "Fiche Infoterre",
            "niveau_eau_scrappe": "Niveau d'eau mesurée dans l'ouvrage"
        }
        df.rename(columns=rename_map, inplace=True)

        cols_to_exclude = [
            # General exclusions
            'nom_inventaire', 'code_inventaire', 'code_departement', 'nom_departement', 
            'code_region', 'nom_region', 'nature_localisation', 'x_wgs84', 'y_wgs84', 
            'code_siret', 'geometry', 'LATITUDE_APPROX', 'LONGITUDE_APPROX', 'boundedBy', 'id',
            'activite', 'type_activite', 'position_relative',
            # BSS-specific exclusions
            'gid', 'type_point_eau', 'code_bassin_dce', 'code_bassin_administratif',
            'bassin_administratif', 'region', 'num_departement', 'departement',
            'code_insee_actuel', 'prof_invest', 'nature_pe_code', 'mode_gisement_code',
            'mode_gisement', 'carac_aquifere_code', 'carac_aquifere', 'liste_bdlisa',
            'date_maj', 'nb_mesures_piezo', 'nb_mesures_qualito', 'coordonneescommune',
            'longitude', 'latitude', 'lien_bsseau', 'lien_ades', 'bss_id', 'bss_id_txt',
            'prof_invest_class', 'rattachement_class',
            'prec_bss', 'altitude', 'etat_pe_code', 'etat_pe',
            'date_maj_qualito', 'date_min_qualito', 'date_max_qualito',
            'libelle', 'bassin_dce'
        ]
        df = df.drop(columns=[c for c in cols_to_exclude if c in df.columns], errors='ignore')
        
        priority_cols = [
            # BSS priorités
            "Code BSS", "Adresse", "Commune", "Nature de l'ouvrage", "Nappe captée",
            "Niveau d'eau mesurée dans l'ouvrage", "Fiche Infoterre",
            "Distance / Position", "Amont / Aval (Topo)",
            # Autres couches
            "Référence", "Etablissement / Adresse", "Code Postal",
            "Etat d'occupation du site", "Activité",
            # IGN Priorités
            "Numéro Parcelle", "Section", "Commune (Admin)", "Usage Bâtiment", "Hauteur (m)", "Toponyme"
        ]
        existing_priority = [c for c in priority_cols if c in df.columns]
        other_cols = [c for c in df.columns if c not in existing_priority]
        df = df[existing_priority + other_cols]

        writer = pd.ExcelWriter(full_path, engine='xlsxwriter')
        df.to_excel(writer, index=False, sheet_name='Données')
        
        workbook = writer.book
        worksheet = writer.sheets['Données']
        
        header_fmt = workbook.add_format({'bold': True, 'fg_color': '#005b9e', 'font_color': 'white', 'border': 1, 'text_wrap': True, 'valign': 'vcenter', 'align': 'center'})
        body_fmt = workbook.add_format({'border': 1, 'text_wrap': True, 'valign': 'vcenter', 'align': 'center'})
        center_fmt = workbook.add_format({'border': 1, 'text_wrap': True, 'valign': 'vcenter', 'align': 'center'})
        link_fmt = workbook.add_format({'color': 'blue', 'underline': 1, 'border': 1, 'valign': 'vcenter', 'align': 'center'})
        
        warning_fmt = workbook.add_format({
            'border': 1, 'text_wrap': True, 'valign': 'vcenter', 'align': 'center',
            'bg_color': '#fff9c4', 
            'font_color': '#b45309' 
        })

        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_fmt)
            width = 20
            if "Etablissement" in str(value) or "Activité" in str(value) or "Adresse" in str(value): 
                width = 40
            if "Distance" in str(value): width = 30
            if "Amont" in str(value): width = 30
            worksheet.set_column(col_num, col_num, width)

        for row_num in range(len(df)):
            for col_num in range(len(df.columns)):
                col_name = df.columns[col_num]
                val = df.iloc[row_num, col_num]
                
                if col_name == "Fiche GéoRisques" and pd.notnull(val) and str(val).startswith('http'):
                    worksheet.write_url(row_num + 1, col_num, val, link_fmt, string="Voir la fiche")
                elif col_name == "Fiche Infoterre" and pd.notnull(val) and str(val).startswith('http'):
                    worksheet.write_url(row_num + 1, col_num, val, link_fmt, string="Voir Infoterre")
                elif col_name in ["Référence", "Etat d'occupation du site", "Code Postal"]:
                    worksheet.write(row_num + 1, col_num, str(val) if pd.notnull(val) else "", center_fmt)
                
                elif col_name == "Amont / Aval (Topo)":
                        worksheet.write(row_num + 1, col_num, str(val) if pd.notnull(val) else "", warning_fmt)
                
                else:
                    worksheet.write(row_num + 1, col_num, str(val) if pd.notnull(val) else "", body_fmt)
        
        writer.close()
        logger.info(f"[Export] SUCCESS - Created {full_path}")
        return fname

    except Exception as e:
        logger.error(f"[Export] Erreur Excel: {e}")
        return None
