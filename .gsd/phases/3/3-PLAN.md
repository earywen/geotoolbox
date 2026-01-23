---
phase: 3
plan: 3
wave: 3
---

# Plan 3.3: Connecter le polygone à l'export

## Objective

Modifier la logique d'export pour utiliser le polygone dessiné comme emprise du site au lieu du simple cercle.

## Context

- `assets/js/cartographie.js` — Méthode runExport()
- `modules/cartographie.py` — run_export_logic() accepte emprise_geojson

## Tasks

<task type="auto">
  <name>Modifier runExport() pour utiliser l'emprise polygone</name>
  <files>assets/js/cartographie.js</files>
  <action>
    Modifier la méthode `runExport()` dans CartographieManager :
    
    1. Modifier la construction de `emprise` pour prioriser le polygone dessiné :
    
    ```javascript
    // Build emprise GeoJSON - prioritize drawn polygon over circle
    let emprise = null;
    if (options.include_emprise) {
        if (this.emprisePolygon) {
            // Use drawn polygon
            emprise = this.emprisePolygon;
            this.addLog('info', 'Utilisation du polygone dessiné comme emprise');
        } else if (this.siteCircle) {
            // Fallback to circle bounds
            const b = this.siteCircle.getBounds();
            emprise = {
                type: "Polygon",
                coordinates: [[
                    [b.getWest(), b.getSouth()],
                    [b.getEast(), b.getSouth()],
                    [b.getEast(), b.getNorth()],
                    [b.getWest(), b.getNorth()],
                    [b.getWest(), b.getSouth()]
                ]]
            };
            this.addLog('info', 'Utilisation du cercle comme emprise');
        }
    }
    ```
    
    2. Modifier getCurrentBbox() pour utiliser les bounds du polygone si disponible :
    
    ```javascript
    getCurrentBbox() {
        // Priority: drawn polygon > circle > map bounds
        if (this.emprisePolygon && this.drawnItems) {
            const b = this.drawnItems.getBounds();
            return {
                min_lat: b.getSouth(),
                min_lon: b.getWest(),
                max_lat: b.getNorth(),
                max_lon: b.getEast()
            };
        }
        if (this.siteCircle) {
            const cb = this.siteCircle.getBounds();
            return {
                min_lat: cb.getSouth(),
                min_lon: cb.getWest(),
                max_lat: cb.getNorth(),
                max_lon: cb.getEast()
            };
        }
        return this.currentBounds;
    }
    ```
  </action>
  <verify>Select-String -Path "assets/js/cartographie.js" -Pattern "emprisePolygon"</verify>
  <done>L'export utilise le polygone dessiné quand disponible</done>
</task>

<task type="auto">
  <name>Améliorer l'affichage de l'emprise info</name>
  <files>assets/js/cartographie.js</files>
  <action>
    Améliorer updateEmpriseInfo() pour afficher plus de détails :
    
    ```javascript
    updateEmpriseInfo() {
        const infoEl = document.getElementById('empriseInfo');
        const detailsEl = document.getElementById('empriseDetails');
        
        if (this.emprisePolygon && infoEl && this.drawnItems) {
            infoEl.classList.add('visible');
            
            // Calculate area
            const coords = this.emprisePolygon.coordinates[0];
            const bounds = this.drawnItems.getBounds();
            const latRange = bounds.getNorth() - bounds.getSouth();
            const lonRange = bounds.getEast() - bounds.getWest();
            
            // Approximate area in m² (rough calculation)
            const latM = latRange * 111111;
            const lonM = lonRange * 111111 * Math.cos(bounds.getCenter().lat * Math.PI / 180);
            const areaM2 = latM * lonM;
            
            let areaStr = '';
            if (areaM2 > 10000) {
                areaStr = `~${(areaM2 / 10000).toFixed(1)} ha`;
            } else {
                areaStr = `~${Math.round(areaM2)} m²`;
            }
            
            detailsEl.innerHTML = `${coords.length - 1} points • ${areaStr}`;
            this.addLog('success', `Emprise définie: ${areaStr}`);
        } else if (infoEl) {
            infoEl.classList.remove('visible');
        }
    }
    ```
  </action>
  <verify>Select-String -Path "assets/js/cartographie.js" -Pattern "areaM2"</verify>
  <done>L'info emprise affiche le nombre de points et la surface approximative</done>
</task>

## Success Criteria

- [ ] L'export utilise le polygone dessiné quand disponible
- [ ] L'info emprise affiche la surface approximative
- [ ] Le fichier emprise_site.geojson contient le vrai polygone (pas un rectangle)
