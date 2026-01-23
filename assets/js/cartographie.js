/**
 * CARTOGRAPHIE MODULE
 * Unified geospatial data extraction (vectors + rasters)
 * 
 * Combines functionality from geotoolbox.js and orthohisto.js
 */

class CartographieManager {
    constructor() {
        this.map = null;
        this.currentBounds = null;
        this.geoJsonLayer = null;
        this.currentPreviewData = null;
        this.siteMarker = null;
        this.siteCircle = null;
        this.selectedLat = 0;
        this.selectedLon = 0;
        this.emprisePolygon = null;  // Polygon drawing
        this.drawControl = null;
        this.drawnItems = null;
        this.currentMode = 'circle';  // 'circle' or 'polygon'
    }

    init() {
        console.log("[Cartographie] Init called");

        // Prevent double init
        if (this.map) {
            setTimeout(() => this.map.invalidateSize(), 100);
            return;
        }

        const mapEl = document.getElementById('cartoMap');
        if (!mapEl) {
            console.error("[Cartographie] Map container #cartoMap not found");
            return;
        }

        // Initialize Leaflet Map
        this.map = L.map('cartoMap', {
            zoomControl: false,
            zoomSnap: 0
        }).setView([46.603354, 1.888334], 6);

        // Base layer - Light theme
        L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
            attribution: '&copy; CARTO',
            maxZoom: 20
        }).addTo(this.map);

        // Zoom control top-right
        L.control.zoom({ position: 'topright' }).addTo(this.map);

        // Geocoder Control
        if (L.Control.geocoder) {
            L.Control.geocoder({
                defaultMarkGeocode: false,
                position: 'topright',
                placeholder: 'Rechercher une adresse...'
            })
                .on('markgeocode', (e) => this.updateSiteSelection(e.geocode.center))
                .addTo(this.map);
        }

        // Event Listeners
        this.map.on('click', (e) => this.updateSiteSelection(e.latlng));
        this.map.on('moveend', () => this.updateBounds());

        console.log("[Cartographie] Map initialized");
    }

    updateBounds() {
        const b = this.map.getBounds();
        this.currentBounds = {
            min_lat: b.getSouth(),
            min_lon: b.getWest(),
            max_lat: b.getNorth(),
            max_lon: b.getEast()
        };
    }

    updateSiteSelection(latlng) {
        this.selectedLat = latlng.lat;
        this.selectedLon = latlng.lng;

        // Update coords display
        const coordsInput = document.getElementById('cartoCoords');
        if (coordsInput) {
            coordsInput.value = `${this.selectedLat.toFixed(5)}, ${this.selectedLon.toFixed(5)}`;
        }

        // Update marker
        if (this.siteMarker) this.map.removeLayer(this.siteMarker);
        this.siteMarker = L.marker(latlng).addTo(this.map);

        // Update radius circle
        this.updateRadiusVisuals();

        // Smart pan
        if (window.smartPanTo) {
            window.smartPanTo(this.map, latlng);
        } else {
            this.map.panTo(latlng);
        }

        this.addLog('info', `Point sélectionné: ${this.selectedLat.toFixed(4)}, ${this.selectedLon.toFixed(4)}`);
    }

    updateRadius() {
        const radInput = document.getElementById('cartoRadius');
        const radDisplay = document.getElementById('cartoRadiusDisplay');

        if (radInput && radDisplay) {
            radDisplay.innerText = radInput.value + " m";
            this.updateRadiusVisuals();
        }
    }

    updateRadiusVisuals() {
        if (!this.selectedLat || !this.map) return;

        if (this.siteCircle) this.map.removeLayer(this.siteCircle);

        const radInput = document.getElementById('cartoRadius');
        const radius = radInput ? parseInt(radInput.value) : 500;

        this.siteCircle = L.circle(
            [this.selectedLat, this.selectedLon],
            {
                radius: radius,
                color: '#38bdf8',
                weight: 2,
                fillOpacity: 0.1
            }
        ).addTo(this.map);
    }

    // Get export options from DOM
    getExportOptions() {
        return {
            include_vectors: true,  // Always true for now
            include_rasters: document.getElementById('includePVA')?.checked ||
                document.getElementById('includeMosaics')?.checked,
            include_pva: document.getElementById('includePVA')?.checked ?? true,
            include_mosaics: document.getElementById('includeMosaics')?.checked ?? true,
            generate_qgis: document.getElementById('exportQGIS')?.checked ?? false,
            include_emprise: document.getElementById('exportEmprise')?.checked ?? true
        };
    }

    // Get selected vector layers
    getSelectedLayers() {
        const inputs = document.querySelectorAll('#carto-layers-list input:checked');
        return Array.from(inputs).map(i => i.value);
    }

    // Get current bbox (from polygon, circle, or map bounds)
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

    // Logging
    addLog(type, message) {
        const logsEl = document.getElementById('cartoLogs');
        if (!logsEl) return;

        const item = document.createElement('div');
        item.className = `log-item log-${type}`;
        item.textContent = message;

        // Prepend to show newest first
        logsEl.insertBefore(item, logsEl.firstChild);

        // Limit to 20 entries
        while (logsEl.children.length > 20) {
            logsEl.removeChild(logsEl.lastChild);
        }
    }

    clearLogs() {
        const logsEl = document.getElementById('cartoLogs');
        if (logsEl) logsEl.innerHTML = '';
    }

    // === PREVIEW ===
    async runPreview() {
        const bbox = this.getCurrentBbox();
        const layers = this.getSelectedLayers();

        if (!layers.length) {
            if (window.showToast) window.showToast('error', "Sélectionnez au moins une couche");
            return;
        }

        if (!bbox || !bbox.min_lat) {
            if (window.showToast) window.showToast('error', "Cliquez sur la carte pour définir un point");
            return;
        }

        this.addLog('info', 'Lancement aperçu...');
        if (window.showLoader) window.showLoader("Chargement des données...");

        try {
            const res = await window.pywebview.api.run_carto_preview(bbox, layers);
            if (window.hideLoader) window.hideLoader();

            this.currentPreviewData = res;
            this.renderPreview(res);

            // Log results
            let totalCount = 0;
            res.forEach(layer => {
                if (layer.count) {
                    this.addLog('success', `${layer.layer}: ${layer.count} éléments`);
                    totalCount += layer.count;
                }
            });
            this.addLog('success', `Total: ${totalCount} éléments`);

            if (window.showToast) window.showToast('success', `Aperçu: ${totalCount} éléments`);
        } catch (err) {
            if (window.hideLoader) window.hideLoader();
            console.error("[Cartographie] Preview error:", err);
            this.addLog('error', `Erreur: ${err}`);
            if (window.showToast) window.showToast('error', "Erreur Preview: " + err);
        }
    }

    renderPreview(res) {
        if (!this.map) return;
        if (this.geoJsonLayer) this.map.removeLayer(this.geoJsonLayer);

        this.geoJsonLayer = L.layerGroup().addTo(this.map);

        res.forEach(g => {
            if (!g.items) return;
            g.items.forEach(i => {
                if (i.geometry) {
                    L.geoJSON(i.geometry, {
                        pointToLayer: (f, l) => L.circleMarker(l, {
                            radius: 6,
                            fillColor: i.color,
                            color: "#fff",
                            weight: 1,
                            fillOpacity: 0.8
                        }),
                        style: {
                            color: i.color,
                            weight: 2,
                            opacity: 0.8
                        },
                        onEachFeature: (f, l) => l.bindPopup(`<b>${g.layer}</b><br>${i.nom}`)
                    }).addTo(this.geoJsonLayer);
                }
            });
        });
    }

    // === EXPORT ===
    async runExport() {
        const bbox = this.getCurrentBbox();
        const layers = this.getSelectedLayers();
        const options = this.getExportOptions();

        // Validate
        if (!layers.length && !options.include_rasters) {
            if (window.showToast) window.showToast('error', "Sélectionnez des données à exporter");
            return;
        }

        if (!bbox || !bbox.min_lat) {
            if (window.showToast) window.showToast('error', "Définissez une zone sur la carte");
            return;
        }

        const folderInput = document.getElementById('cartoTargetPath');
        const folder = folderInput ? folderInput.value : null;

        if (!folder) {
            if (window.showToast) window.showToast('error', "Sélectionnez un dossier d'export");
            return;
        }

        this.clearLogs();
        this.addLog('info', 'Démarrage export...');
        if (window.showLoader) window.showLoader("Export en cours...");

        try {
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

            const res = await window.pywebview.api.run_carto_export(
                bbox, layers, null, folder, options, emprise
            );

            if (window.hideLoader) window.hideLoader();

            // Log results
            if (res.summary) {
                res.summary.forEach(s => {
                    if (s.status === 'success') {
                        this.addLog('success', `✓ ${s.layer}`);
                    } else if (s.status === 'error') {
                        this.addLog('error', `✗ ${s.layer}: ${s.error}`);
                    }
                });
            }

            this.addLog('success', `Export terminé: ${res.folder}`);

            if (window.showToast) {
                const vCount = res.vector_count || 0;
                const rCount = res.raster_count || 0;
                window.showToast('success', `Export: ${vCount} vecteurs, ${rCount} rasters`);
            }

        } catch (err) {
            if (window.hideLoader) window.hideLoader();
            console.error("[Cartographie] Export error:", err);
            this.addLog('error', `Erreur: ${err}`);
            if (window.showToast) window.showToast('error', "Erreur Export: " + err);
        }
    }

    // === FOLDER BROWSE ===
    async browseFolder() {
        if (!window.pywebview || !window.pywebview.api) {
            console.error("[Cartographie] pywebview API not available");
            return;
        }

        try {
            const path = await window.pywebview.api.browse_folder();
            if (path) {
                const input = document.getElementById('cartoTargetPath');
                if (input) input.value = path;
                this.addLog('info', `Dossier: ${path}`);
            }
        } catch (err) {
            console.error("[Cartographie] Browse folder error:", err);
        }
    }

    // === DRAWING CONTROLS ===
    initDrawControls() {
        if (!L.Control.Draw) {
            console.warn('[Cartographie] Leaflet.Draw not loaded');
            return;
        }

        // Feature group for drawn shapes
        this.drawnItems = new L.FeatureGroup();
        this.map.addLayer(this.drawnItems);

        // Draw control - polygon and rectangle
        this.drawControl = new L.Control.Draw({
            position: 'topright',
            draw: {
                polyline: false,
                rectangle: {
                    shapeOptions: { color: '#22c55e', weight: 2 }
                },
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
            this.addLog('success', 'Emprise dessinée');
        });

        // Event: shape edited
        this.map.on(L.Draw.Event.EDITED, (e) => {
            const layers = e.layers;
            layers.eachLayer((layer) => {
                this.emprisePolygon = layer.toGeoJSON().geometry;
            });
            this.updateEmpriseInfo();
        });

        // Event: shape deleted
        this.map.on(L.Draw.Event.DELETED, () => {
            this.emprisePolygon = null;
            this.updateEmpriseInfo();
        });
    }

    setMode(mode) {
        this.currentMode = mode;

        // Update UI buttons
        document.getElementById('modeCircle')?.classList.toggle('active', mode === 'circle');
        document.getElementById('modePolygon')?.classList.toggle('active', mode === 'polygon');

        // Show/hide controls
        if (mode === 'polygon') {
            if (!this.drawControl) this.initDrawControls();
            if (this.drawControl) this.map.addControl(this.drawControl);
            document.getElementById('radiusContainer')?.classList.add('hidden');
            // Hide circle if exists
            if (this.siteCircle) {
                this.map.removeLayer(this.siteCircle);
                this.siteCircle = null;
            }
            this.addLog('info', 'Mode polygone activé - dessinez sur la carte');
        } else {
            if (this.drawControl) this.map.removeControl(this.drawControl);
            document.getElementById('radiusContainer')?.classList.remove('hidden');
            // Clear drawn polygon
            if (this.drawnItems) this.drawnItems.clearLayers();
            this.emprisePolygon = null;
            this.updateEmpriseInfo();
            // Restore circle if we have a point
            if (this.selectedLat) this.updateRadiusVisuals();
            this.addLog('info', 'Mode cercle activé');
        }
    }

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

            // Approximate area in m²
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
        } else if (infoEl) {
            infoEl.classList.remove('visible');
        }
    }

    clearEmprise() {
        if (this.drawnItems) this.drawnItems.clearLayers();
        this.emprisePolygon = null;
        this.updateEmpriseInfo();
        this.addLog('info', 'Emprise effacée');
    }
}

// === BOOTSTRAP ===
window.Cartographie = new CartographieManager();

// === GLOBAL BINDINGS FOR HTML ONCLICK ===
window.init_cartographie = () => window.Cartographie.init();
window.carto_updateRadius = () => window.Cartographie.updateRadius();
window.carto_runPreview = () => window.Cartographie.runPreview();
window.carto_runExport = () => window.Cartographie.runExport();
window.carto_browseFolder = () => window.Cartographie.browseFolder();
window.carto_setMode = (m) => window.Cartographie.setMode(m);
window.carto_clearEmprise = () => window.Cartographie.clearEmprise();

console.log("[Cartographie] Module loaded");
