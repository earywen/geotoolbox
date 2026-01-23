---
phase: 1
plan: 4
wave: 3
---

# Plan 1.4: Créer l'orchestrateur cartographie.py

## Objective

Implémenter la logique d'orchestration dans `cartographie.py` qui combine les exports vectoriels et raster en un seul workflow unifié.

## Context

- `modules/cartographie.py` — Fichier créé en Plan 1.1
- `modules/cartographie_core/` — Modules migrés en Plans 1.2 et 1.3
- `modules/geotoolbox.py` — Référence pour la logique preview/export
- `modules/orthohisto.py` — Référence pour la logique full_process

## Tasks

<task type="auto">
  <name>Implémenter les fonctions principales</name>
  <files>modules/cartographie.py</files>
  <action>
    Créer les fonctions suivantes en s'inspirant de geotoolbox.py et orthohisto.py:
    
    1. `TOOL_INFO` — Métadonnées UI:
       ```python
       TOOL_INFO = {
           "id": "cartographie",
           "name": "Cartographie",
           "icon": "🗺️",
           "description": "Données géographiques et photos aériennes"
       }
       ```
    
    2. `run_preview_logic(bbox, layers_list, reporter)`:
       - Déléguer à `cartographie_core.vector_fetcher.fetch_features()`
       - Retourner les résultats pour affichage carte
    
    3. `run_export_logic(bbox, layers_list, folder_name, base_path_ui, options)`:
       - Créer le dossier d'export
       - Si options.include_vectors: exporter les couches vectorielles
       - Si options.include_rasters: exporter les photos aériennes
       - Si options.include_emprise: exporter le polygone d'emprise
       - Retourner le résumé d'export
    
    4. `run_full_cartographie(lat, lon, radius, bbox, layers, folder, options)`:
       - Orchestrer le workflow complet
       - Appeler run_export_logic pour les vecteurs
       - Appeler process_all_pva pour les rasters
       - Générer le projet QGIS si demandé
    
    5. `get_ui_content()`:
       - Charger le template (placeholder pour Phase 2)
       - `return core.load_template("cartographie.html")`
    
    IMPORTANT: Utiliser les imports depuis cartographie_core/, PAS depuis geotoolbox_core/ !
  </action>
  <verify>python -c "from modules.cartographie import run_preview_logic, run_export_logic, TOOL_INFO; print(TOOL_INFO['name'])"</verify>
  <done>Les fonctions principales sont définies et importables</done>
</task>

<task type="auto">
  <name>Créer les options de configuration</name>
  <files>modules/cartographie_core/config.py</files>
  <action>
    Définir les dataclasses/TypedDict pour les options d'export:
    
    ```python
    from typing import TypedDict, Optional, List
    from dataclasses import dataclass
    
    @dataclass
    class ExportOptions:
        include_vectors: bool = True
        include_rasters: bool = True
        include_emprise: bool = True
        generate_qgis: bool = False
        vector_layers: Optional[List[str]] = None  # None = toutes
        raster_sources: Optional[List[str]] = None  # None = toutes
    
    # Re-export depuis models.py pour accès centralisé
    from .models import LAYERS_CONFIG, RASTER_CONFIG
    ```
    
    Créer aussi `RASTER_CONFIG` pour les sources raster:
    ```python
    RASTER_CONFIG = {
        "pva": {"label": "Photos Aériennes (PVA)", "enabled": True},
        "mosaics": {"label": "Mosaïques IGN", "enabled": True}
    }
    ```
  </action>
  <verify>python -c "from modules.cartographie_core.config import ExportOptions; print(ExportOptions())"</verify>
  <done>Les options d'export sont définies et utilisables</done>
</task>

## Success Criteria

- [ ] `cartographie.py` expose les fonctions `run_preview_logic`, `run_export_logic`
- [ ] `ExportOptions` permet de configurer ce qui est exporté
- [ ] Le module s'importe sans erreur
- [ ] TOOL_INFO est correctement défini
