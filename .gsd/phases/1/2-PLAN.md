---
phase: 1
plan: 2
wave: 1
---

# Plan 1.2: Migrer la logique vectorielle (GéoToolbox)

## Objective

Migrer le code de `geotoolbox_core/` vers `cartographie_core/vector_*` en préservant toute la logique existante. Les anciens fichiers restent en place pour l'instant (rétrocompatibilité).

## Context

- `modules/geotoolbox_core/fetcher.py` — Source: requêtes WFS
- `modules/geotoolbox_core/exporter.py` — Source: export Excel/GeoJSON
- `modules/geotoolbox_core/maths.py` — Source: calculs géométriques
- `modules/geotoolbox_core/models.py` — Source: config couches
- `modules/geotoolbox_core/parsers.py` — Source: parsing XML/JSON
- `modules/cartographie_core/` — Destination

## Tasks

<task type="auto">
  <name>Migrer le code vectoriel</name>
  <files>
    modules/cartographie_core/vector_fetcher.py
    modules/cartographie_core/vector_export.py
    modules/cartographie_core/maths.py
    modules/cartographie_core/models.py
    modules/cartographie_core/parsers.py
    modules/cartographie_core/config.py
  </files>
  <action>
    Pour chaque fichier source dans geotoolbox_core/:
    
    1. `fetcher.py` → `vector_fetcher.py`
       - Copier tout le contenu
       - Adapter les imports (from modules.cartographie_core.xxx)
       
    2. `exporter.py` → `vector_export.py`
       - Copier tout le contenu
       - Adapter les imports
       
    3. `maths.py` → `maths.py` (même nom)
       - Copier tout le contenu
       - Ce fichier est partagé vecteurs + rasters
       
    4. `models.py` → `models.py`
       - Copier LAYERS_CONFIG et autres modèles
       
    5. `parsers.py` → `parsers.py`
       - Copier tout le contenu
       
    6. Dans `config.py`:
       - Créer un point d'entrée unifié pour la config
       - Importer et réexporter LAYERS_CONFIG de models.py
       
    NE PAS supprimer les anciens fichiers geotoolbox_core/ !
  </action>
  <verify>python -c "from modules.cartographie_core.vector_fetcher import fetch_features; print('OK')"</verify>
  <done>Les fonctions clés (fetch_features, generate_excel_for_layer, calculate_geometrics) sont importables depuis cartographie_core/</done>
</task>

<task type="auto">
  <name>Mettre à jour __init__.py avec les exports</name>
  <files>modules/cartographie_core/__init__.py</files>
  <action>
    Dans __init__.py, exposer les fonctions principales:
    
    ```python
    from .vector_fetcher import fetch_features
    from .vector_export import generate_excel_for_layer
    from .maths import calculate_geometrics, get_local_slope_vector, get_elevation_ign_only
    from .models import LAYERS_CONFIG
    from .parsers import parse_wfs_response
    ```
    
    Cela permet un import propre: `from modules.cartographie_core import fetch_features`
  </action>
  <verify>python -c "from modules.cartographie_core import fetch_features, LAYERS_CONFIG; print(len(LAYERS_CONFIG), 'layers')"</verify>
  <done>Les imports principaux fonctionnent depuis le package</done>
</task>

## Success Criteria

- [ ] `vector_fetcher.py` contient `fetch_features()`
- [ ] `vector_export.py` contient `generate_excel_for_layer()`
- [ ] `maths.py` contient les fonctions géométriques
- [ ] Les imports fonctionnent sans erreur
- [ ] Les anciens fichiers `geotoolbox_core/` sont intacts
