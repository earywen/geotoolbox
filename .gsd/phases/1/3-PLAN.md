---
phase: 1
plan: 3
wave: 2
---

# Plan 1.3: Migrer la logique raster (OrthoHisto)

## Objective

Migrer le code de téléchargement d'images (PVA, mosaïques WMS) depuis `orthohisto.py` et `pva_processor.py` vers `cartographie_core/raster_*`.

## Context

- `modules/orthohisto.py` — Source: logique WMS/WFS PVA
- `modules/pva_processor.py` — Source: traitement images (crop, rotation, georef)
- `modules/cartographie_core/raster_fetcher.py` — Destination fetcher
- `modules/cartographie_core/raster_processor.py` — Destination processor

## Tasks

<task type="auto">
  <name>Migrer le code de téléchargement raster</name>
  <files>modules/cartographie_core/raster_fetcher.py</files>
  <action>
    Depuis `orthohisto.py`, copier vers `raster_fetcher.py`:
    
    1. Constantes:
       - `IGN_MOSAICS` (liste des mosaïques)
       - `MIN_IMAGE_SIZE` (seuil image vide)
    
    2. Fonctions:
       - `ensure_folder()` — Création dossier
       - `download_wms()` — Téléchargement mosaïques WMS
       - `download_file_stream()` — Téléchargement fichiers chunked
       - `download_pva_tif()` — Téléchargement PVA individuel
       - `_fallback_basic_georef()` — Géoréférencement basique
       - `process_all_pva()` — Orchestration téléchargement PVA
    
    3. Adapter les imports:
       - `from modules import core` → OK (inchangé)
       - Imports qgis_export → OK (inchangé)
       - Imports pva_processor → `from .raster_processor import ...`
    
    NE PAS supprimer orthohisto.py !
  </action>
  <verify>python -c "from modules.cartographie_core.raster_fetcher import download_wms, process_all_pva; print('OK')"</verify>
  <done>Les fonctions de téléchargement sont importables depuis raster_fetcher</done>
</task>

<task type="auto">
  <name>Migrer le processeur d'images PVA</name>
  <files>modules/cartographie_core/raster_processor.py</files>
  <action>
    Depuis `pva_processor.py`, copier TOUT le contenu vers `raster_processor.py`:
    
    1. Fonctions de crop:
       - `detect_photo_region()`
       - `crop_to_photo()`
    
    2. Fonctions de rotation:
       - `rotate_image()`
       - `normalize_orientation()`
    
    3. Fonctions de matching:
       - `find_keypoints()`
       - `match_images()`
       - `align_to_reference()`
    
    4. Pipeline complet:
       - `process_pva_image()`
       - `create_georeferenced_pva()`
    
    Les imports restent identiques (cv2, numpy, PIL).
    
    NE PAS supprimer pva_processor.py !
  </action>
  <verify>python -c "from modules.cartographie_core.raster_processor import create_georeferenced_pva; print('OK')"</verify>
  <done>Le processeur d'images est importable depuis raster_processor</done>
</task>

<task type="auto">
  <name>Mettre à jour __init__.py avec exports raster</name>
  <files>modules/cartographie_core/__init__.py</files>
  <action>
    Ajouter les exports raster à __init__.py:
    
    ```python
    # Raster exports
    from .raster_fetcher import (
        download_wms,
        process_all_pva,
        IGN_MOSAICS
    )
    from .raster_processor import (
        create_georeferenced_pva,
        process_pva_image
    )
    ```
    
    Gérer l'ImportError pour OpenCV optionnel:
    ```python
    try:
        from .raster_processor import create_georeferenced_pva
    except ImportError:
        create_georeferenced_pva = None  # OpenCV not available
    ```
  </action>
  <verify>python -c "from modules.cartographie_core import process_all_pva, IGN_MOSAICS; print(len(IGN_MOSAICS), 'mosaics')"</verify>
  <done>Les imports raster fonctionnent (avec fallback si OpenCV absent)</done>
</task>

## Success Criteria

- [ ] `raster_fetcher.py` contient toute la logique de téléchargement
- [ ] `raster_processor.py` contient le traitement d'images
- [ ] Les imports fonctionnent (avec gestion OpenCV optionnel)
- [ ] Les anciens fichiers (`orthohisto.py`, `pva_processor.py`) sont intacts
