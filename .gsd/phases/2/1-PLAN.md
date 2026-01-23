---
phase: 2
plan: 1
wave: 1
---

# Plan 2.1: Créer le template cartographie.html

## Objective

Créer un template HTML unifié fusionnant geotoolbox.html et orthohisto.html avec :
- Une sidebar commune
- Sélection de la zone (point + rayon OU polygone)
- Sélection des couches vectorielles
- Options d'export (vecteurs, rasters, emprise)

## Context

- `assets/templates/geotoolbox.html` — Template référence (228 lignes)
- `assets/templates/orthohisto.html` — Template à fusionner (88 lignes)
- `.gsd/SPEC.md` — Spécification fonctionnelle

## Tasks

<task type="auto">
  <name>Créer le template unifié cartographie.html</name>
  <files>assets/templates/cartographie.html</files>
  <action>
    Créer un nouveau template fusionnant les deux existants :
    
    1. STRUCTURE DE BASE (reprendre geotoolbox.html)
       ```html
       <style>/* Styles du module */</style>
       <div id="cartographie-container">
         <div id="map-container">...</div>
         <div id="carto-sidebar" class="glass-panel">...</div>
       </div>
       ```
    
    2. SIDEBAR SECTIONS :
       - **Section 1: Zone d'étude**
         - Affichage coordonnées (comme geotoolbox)
         - Slider rayon (comme orthohisto)
         - Note: "Polygone disponible via Phase 3"
       
       - **Section 2: Données vectorielles**
         - Checkboxes générées dynamiquement ({{CHECKBOXES}})
         - Reprendre le style de geotoolbox
       
       - **Section 3: Photos aériennes**
         - Checkbox "Inclure photos historiques (PVA)"
         - Checkbox "Inclure mosaïques IGN récentes"
       
       - **Section 4: Export**
         - Input dossier cible
         - Checkbox "Générer projet QGIS"
         - Boutons Aperçu + Export
         - Zone de logs (comme orthohisto)
    
    3. IDs à utiliser :
       - `#carto-sidebar`, `#cartoMap`
       - `#cartoCoords`, `#cartoRadius`
       - `#cartoTargetPath`, `#cartoLogs`
       - `#includeVectors`, `#includeRasters`, `#includeQgis`
    
    NE PAS copier les styles en double - factoriser dans la section <style>.
  </action>
  <verify>Test-Path "assets/templates/cartographie.html"</verify>
  <done>Le template existe et contient les 4 sections</done>
</task>

## Success Criteria

- [ ] `cartographie.html` existe dans `assets/templates/`
- [ ] Les 4 sections sont présentes (Zone, Vecteurs, Rasters, Export)
- [ ] Les IDs sont cohérents et documentés
- [ ] Le template est syntaxiquement correct (pas de tags non fermés)
