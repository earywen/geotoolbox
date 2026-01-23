---
phase: 2
plan: 2
wave: 1
---

# Plan 2.2: Créer le module JavaScript cartographie.js

## Objective

Créer un fichier JS unifié reprenant la structure de GeotoolboxManager mais intégrant la logique OrthoHisto pour un workflow unifié.

## Context

- `assets/js/geotoolbox.js` — Référence principale (452 lignes, classe ES6)
- `assets/js/orthohisto.js` — Logique à fusionner
- `modules/cartographie.py` — API backend à appeler

## Tasks

<task type="auto">
  <name>Créer CartographieManager class</name>
  <files>assets/js/cartographie.js</files>
  <action>
    Créer une classe ES6 inspirée de GeotoolboxManager :
    
    ```javascript
    class CartographieManager {
        constructor() {
            this.map = null;
            this.currentBounds = null;
            this.siteMarker = null;
            this.siteCircle = null;
            this.selectedLat = 0;
            this.selectedLon = 0;
            this.emprisePolygon = null;  // Pour Phase 3
        }
        
        init() { /* Init carte Leaflet */ }
        updateSiteSelection(latlng) { /* Maj point sélectionné */ }
        updateRadius() { /* Maj cercle visuel */ }
        
        // Export unifié
        async runPreview() { /* Appel API preview */ }
        async runExport() { /* Appel API export unifié */ }
        
        // Helpers
        getExportOptions() { /* Récupère les options depuis le DOM */ }
        showLogs(messages) { /* Affiche dans la zone de logs */ }
    }
    ```
    
    Points clés :
    1. Reprendre la logique de carte de geotoolbox.js
    2. Ajouter les options d'export (vecteurs, rasters, QGIS)
    3. Appeler `window.pywebview.api.run_carto_preview()` et `run_carto_export()`
    4. Gérer la progression avec le loader existant
    
    Fonctions à exposer sur window:
    - `window.Cartographie`
    - `window.init_cartographie()`
    - `window.carto_updateRadius()`
    - `window.carto_runPreview()`
    - `window.carto_runExport()`
    - `window.carto_browseFolder()`
  </action>
  <verify>Test-Path "assets/js/cartographie.js"</verify>
  <done>Le fichier JS existe avec la classe CartographieManager</done>
</task>

## Success Criteria

- [ ] `cartographie.js` existe dans `assets/js/`
- [ ] La classe CartographieManager est définie
- [ ] Les fonctions window.* sont exposées
- [ ] Synthax JS valide (pas d'erreurs console)
