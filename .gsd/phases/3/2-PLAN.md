---
phase: 3
plan: 2
wave: 2
---

# Plan 3.2: Implémenter le dessin de polygone dans CartographieManager

## Objective

Ajouter la logique de dessin de polygone dans CartographieManager avec :
- Toggle entre mode cercle et mode polygone
- Contrôles Leaflet.Draw configurés
- Extraction du GeoJSON pour l'export

## Context

- `assets/js/cartographie.js` — Classe CartographieManager
- `assets/templates/cartographie.html` — Section Zone d'étude
- Leaflet.Draw API: https://leaflet.github.io/Leaflet.draw/docs/leaflet-draw-latest.html

## Tasks

<task type="auto">
  <name>Ajouter le toggle Mode Cercle/Polygone dans le template</name>
  <files>assets/templates/cartographie.html</files>
  <action>
    Modifier la Section 1 (Zone d'étude) pour ajouter un sélecteur de mode :
    
    Dans la div carto-card de la section 1, ajouter AVANT le slider rayon :
    
    ```html
    <!-- Mode Selection -->
    <div style="display: flex; gap: 10px; margin-bottom: 15px;">
        <button id="modeCircle" class="btn-mode active" onclick="carto_setMode('circle')">
            ⭕ Cercle
        </button>
        <button id="modePolygon" class="btn-mode" onclick="carto_setMode('polygon')">
            📐 Polygone
        </button>
    </div>
    
    <!-- Emprise Info (shown when polygon is drawn) -->
    <div id="empriseInfo" class="emprise-info">
        <strong>📐 Emprise définie</strong>
        <div id="empriseDetails">-</div>
        <button class="btn-mini" onclick="carto_clearEmprise()">✕ Effacer</button>
    </div>
    ```
    
    Ajouter les styles pour btn-mode dans la section <style> :
    ```css
    .btn-mode {
        flex: 1;
        padding: 8px;
        border: 1px solid rgba(255,255,255,0.2);
        background: rgba(30, 41, 59, 0.6);
        color: var(--text);
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.2s;
    }
    .btn-mode:hover { background: rgba(30, 41, 59, 0.9); }
    .btn-mode.active { 
        background: var(--accent); 
        border-color: var(--accent);
    }
    .btn-mini {
        margin-top: 8px;
        padding: 4px 10px;
        font-size: 11px;
        background: rgba(239, 68, 68, 0.2);
        border: 1px solid rgba(239, 68, 68, 0.4);
        color: #ef4444;
        border-radius: 4px;
        cursor: pointer;
    }
    ```
  </action>
  <verify>Select-String -Path "assets/templates/cartographie.html" -Pattern "modePolygon"</verify>
  <done>Les boutons de mode et l'info emprise sont présents</done>
</task>

<task type="auto">
  <name>Implémenter la logique de dessin dans CartographieManager</name>
  <files>assets/js/cartographie.js</files>
  <action>
    Ajouter les méthodes suivantes à la classe CartographieManager :
    
    1. Dans le constructor, ajouter :
       ```javascript
       this.drawControl = null;
       this.drawnItems = null;
       this.currentMode = 'circle';  // 'circle' or 'polygon'
       ```
    
    2. Ajouter la méthode initDrawControls() :
       ```javascript
       initDrawControls() {
           // Feature group for drawn shapes
           this.drawnItems = new L.FeatureGroup();
           this.map.addLayer(this.drawnItems);
           
           // Draw control - polygon only
           this.drawControl = new L.Control.Draw({
               position: 'topright',
               draw: {
                   polyline: false,
                   rectangle: true,
                   circle: false,
                   circlemarker: false,
                   marker: false,
                   polygon: {
                       allowIntersection: false,
                       showArea: true,
                       shapeOptions: { color: '#22c55e', weight: 2 }
                   }
               },
               edit: { featureGroup: this.drawnItems }
           });
           
           // Event: shape created
           this.map.on(L.Draw.Event.CREATED, (e) => {
               this.drawnItems.clearLayers();
               this.drawnItems.addLayer(e.layer);
               this.emprisePolygon = e.layer.toGeoJSON().geometry;
               this.updateEmpriseInfo();
           });
           
           // Event: shape deleted
           this.map.on(L.Draw.Event.DELETED, () => {
               this.emprisePolygon = null;
               this.updateEmpriseInfo();
           });
       }
       ```
    
    3. Ajouter setMode(mode) :
       ```javascript
       setMode(mode) {
           this.currentMode = mode;
           
           // Update UI buttons
           document.getElementById('modeCircle')?.classList.toggle('active', mode === 'circle');
           document.getElementById('modePolygon')?.classList.toggle('active', mode === 'polygon');
           
           // Show/hide controls
           if (mode === 'polygon') {
               if (!this.drawControl) this.initDrawControls();
               this.map.addControl(this.drawControl);
               // Hide radius slider
               document.getElementById('radiusContainer')?.classList.add('hidden');
           } else {
               if (this.drawControl) this.map.removeControl(this.drawControl);
               document.getElementById('radiusContainer')?.classList.remove('hidden');
           }
       }
       ```
    
    4. Ajouter updateEmpriseInfo() et clearEmprise() :
       ```javascript
       updateEmpriseInfo() {
           const infoEl = document.getElementById('empriseInfo');
           const detailsEl = document.getElementById('empriseDetails');
           
           if (this.emprisePolygon && infoEl) {
               infoEl.classList.add('visible');
               const coords = this.emprisePolygon.coordinates[0];
               detailsEl.textContent = `${coords.length - 1} points`;
           } else if (infoEl) {
               infoEl.classList.remove('visible');
           }
       }
       
       clearEmprise() {
           this.drawnItems?.clearLayers();
           this.emprisePolygon = null;
           this.updateEmpriseInfo();
       }
       ```
    
    5. Exposer sur window :
       ```javascript
       window.carto_setMode = (m) => window.Cartographie.setMode(m);
       window.carto_clearEmprise = () => window.Cartographie.clearEmprise();
       ```
  </action>
  <verify>Select-String -Path "assets/js/cartographie.js" -Pattern "initDrawControls"</verify>
  <done>Les méthodes de dessin sont implémentées et les bindings window.* existent</done>
</task>

## Success Criteria

- [ ] Toggle cercle/polygone fonctionne
- [ ] Les contrôles Leaflet.Draw apparaissent en mode polygone
- [ ] Le polygone dessiné est capturé dans `this.emprisePolygon`
- [ ] L'info emprise s'affiche avec le nombre de points
