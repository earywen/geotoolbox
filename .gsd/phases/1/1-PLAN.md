---
phase: 1
plan: 1
wave: 1
---

# Plan 1.1: Créer la structure cartographie_core/

## Objective

Créer le squelette du nouveau module `cartographie_core/` avec tous les fichiers vides nécessaires. Cela établit l'architecture cible avant la migration du code.

## Context

- `.gsd/SPEC.md` — Architecture cible définie
- `.gsd/ARCHITECTURE.md` — Structure actuelle documentée
- `modules/geotoolbox_core/` — Structure à répliquer
- `modules/orthohisto.py` — Logique à migrer

## Tasks

<task type="auto">
  <name>Créer le module cartographie.py</name>
  <files>modules/cartographie.py</files>
  <action>
    Créer le fichier orchestrateur principal avec:
    - Imports minimaux (os, logging, typing)
    - TOOL_INFO dict pour les métadonnées UI
    - Fonction get_ui_content() placeholder
    - Docstring expliquant le rôle du module
    
    Ne PAS encore implémenter la logique — juste le squelette.
  </action>
  <verify>python -c "from modules import cartographie; print(cartographie.TOOL_INFO)"</verify>
  <done>Le module s'importe sans erreur et TOOL_INFO est accessible</done>
</task>

<task type="auto">
  <name>Créer l'arborescence cartographie_core/</name>
  <files>
    modules/cartographie_core/__init__.py
    modules/cartographie_core/config.py
    modules/cartographie_core/vector_fetcher.py
    modules/cartographie_core/vector_export.py
    modules/cartographie_core/raster_fetcher.py
    modules/cartographie_core/raster_processor.py
    modules/cartographie_core/maths.py
    modules/cartographie_core/models.py
    modules/cartographie_core/parsers.py
  </files>
  <action>
    Créer chaque fichier avec:
    - Docstring décrivant son rôle futur
    - Imports de base (typing, logging)
    - Commentaire "# TODO: Migrer depuis [source]"
    
    __init__.py doit exposer les imports principaux (vides pour l'instant).
    
    NE PAS copier de code existant — juste créer les fichiers vides structurés.
  </action>
  <verify>python -c "from modules import cartographie_core; print('OK')"</verify>
  <done>Tous les fichiers existent et le package s'importe sans erreur</done>
</task>

## Success Criteria

- [ ] `modules/cartographie.py` existe et s'importe
- [ ] `modules/cartographie_core/` contient 9 fichiers Python
- [ ] Aucune erreur d'import
- [ ] Structure prête pour la migration du code
