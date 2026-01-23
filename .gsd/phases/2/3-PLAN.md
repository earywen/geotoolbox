---
phase: 2
plan: 3
wave: 2
---

# Plan 2.3: Intégrer Cartographie dans l'application

## Objective

Modifier les fichiers existants pour intégrer le nouveau module Cartographie :
- Ajouter dans le dock flottant
- Connecter à l'API Python
- Charger le script JS

## Context

- `assets/index.html` — Page principale avec dock
- `app.py` — API Python BurgeaplyApi
- `assets/js/app.js` — Bootstrap application
- `modules/cartographie.py` — Backend créé en Phase 1

## Tasks

<task type="auto">
  <name>Mettre à jour le dock dans index.html</name>
  <files>assets/index.html</files>
  <action>
    1. Ajouter l'item Cartographie dans le dock flottant (remplacer ou compléter GéoToolbox/OrthoHisto)
    
    2. Chercher la section du dock et ajouter :
       ```html
       <div class="dock-item" onclick="loadTool('cartographie')">
         <span class="dock-icon">🗺️</span>
         <span class="dock-label">Cartographie</span>
       </div>
       ```
    
    3. Ajouter le script cartographie.js :
       ```html
       <script src="js/cartographie.js"></script>
       ```
       
    Note: Garder les anciens items dock pour l'instant (rétrocompatibilité)
  </action>
  <verify>Select-String -Path "assets/index.html" -Pattern "cartographie"</verify>
  <done>Le dock contient l'item Cartographie et le script est chargé</done>
</task>

<task type="auto">
  <name>Ajouter les routes API dans app.py</name>
  <files>app.py</files>
  <action>
    Ajouter les méthodes API pour le module Cartographie dans BurgeaplyApi :
    
    1. Importer le module :
       ```python
       from modules import cartographie
       ```
    
    2. Ajouter les méthodes :
       ```python
       def run_carto_preview(self, bbox, layers):
           """Preview pour le module Cartographie."""
           return cartographie.run_preview_logic(bbox, layers)
       
       def run_carto_export(self, bbox, layers, folder_name, base_path, options, emprise=None):
           """Export unifié Cartographie."""
           return cartographie.run_export_logic(
               bbox, layers, folder_name, base_path, options,
               emprise_geojson=emprise
           )
       ```
    
    3. Mettre à jour get_ui pour Cartographie :
       ```python
       elif tool_id == 'cartographie':
           return cartographie.get_ui_content()
       ```
  </action>
  <verify>Select-String -Path "app.py" -Pattern "run_carto_"</verify>
  <done>Les méthodes run_carto_preview et run_carto_export existent dans app.py</done>
</task>

<task type="auto">
  <name>Configurer l'initialisation dans app.js</name>
  <files>assets/js/app.js</files>
  <action>
    Ajouter le hook d'initialisation pour le module Cartographie :
    
    Chercher la section qui gère le chargement des modules (loadTool ou similar) et ajouter :
    ```javascript
    if (toolId === 'cartographie') {
        // Import dynamique ou appel init
        if (window.Cartographie) {
            window.Cartographie.init();
        } else if (window.init_cartographie) {
            window.init_cartographie();
        }
    }
    ```
  </action>
  <verify>Select-String -Path "assets/js/app.js" -Pattern "cartographie"</verify>
  <done>L'initialisation du module Cartographie est configurée</done>
</task>

## Success Criteria

- [ ] Index.html charge cartographie.js
- [ ] Le dock contient l'item Cartographie
- [ ] app.py expose run_carto_preview et run_carto_export
- [ ] L'init est appelée au chargement du module
