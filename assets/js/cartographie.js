/**
 * CARTOGRAPHIE MODULE
 * Unified geospatial data extraction (vectors + rasters)
 * 
 * Logic:
 * 1. User draws site polygon (Leaflet.Draw)
 * 2. System calculates center and defines search radius
 * 3. Exports based on search radius, but includes site polygon as 'emprise'
 */

class CartographieManager {
    constructor() {
        this.map = null;
        this.currentBounds = null;
        this.geoJsonLayer = null;

        // Site Definition
        this.siteMarker = null;     // Center of search
        this.siteCircle = null;     // Search Radius
        this.emprisePolygon = null; // Actual site boundary (GeoJSON geometry)
        this.drawnItems = null;     // Leaflet LayerGroup for drawn items
        this.drawControl = null;    // Leaflet.Draw control

        this.selectedLat = 0;
        this.selectedLon = 0;
    }

    init() {
        console.log("[Cartographie] Init called");

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

        // Base layers
        const lightLayer = L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
            attribution: '&copy; CARTO',
            maxZoom: 20
        });
        const osmLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        });

        const googleSatLayer = L.tileLayer('http://{s}.google.com/vt/lyrs=s&x={x}&y={y}&z={z}', {
            maxZoom: 20,
            subdomains: ['mt0', 'mt1', 'mt2', 'mt3']
        });

        const brgmGeology = L.tileLayer.wms('http://geoservices.brgm.fr/geologie', {
            layers: 'GEOLOGIE',
            format: 'image/png',
            transparent: true,
            opacity: 0.65,
            attribution: '&copy; BRGM'
        });

        // Layer Control
        const baseMaps = {
            "Plan (OSM)": osmLayer,
            "Satellite (Google)": googleSatLayer
        };

        const overlayMaps = {
            "Carte Géologique 1/50k": brgmGeology
        };

        if (this.currentLayerControl) {
            this.map.removeControl(this.currentLayerControl);
        }

        this.currentLayerControl = L.control.layers(baseMaps, overlayMaps, { position: 'bottomright' }).addTo(this.map);

        // Default View
        osmLayer.addTo(this.map);

        L.control.zoom({ position: 'topright' }).addTo(this.map);

        // Geocoder Control
        if (L.Control.geocoder) {
            L.Control.geocoder({
                defaultMarkGeocode: false,
                position: 'topright',
                placeholder: 'Rechercher une adresse...'
            })
                .on('markgeocode', (e) => {
                    this.map.panTo(e.geocode.center);
                    this.map.setZoom(16); // Zoom closer to help drawing
                })
                .addTo(this.map);
        }

        this.initDrawControls();

        // Load Layers from Backend
        this.loadLayers();

        // Init Slider Background
        const radInput = document.getElementById('cartoRadius');
        if (radInput) this.updateSliderBackground(radInput);

        // Init Icons
        if (window.lucide) window.lucide.createIcons();

        console.log("[Cartographie] Map initialized");
    }

    async loadLayers() {
        const container = document.getElementById('carto-layers-list');
        if (!container) return;

        // 1. Show Skeleton
        container.innerHTML = `
            <div class="skeleton" style="height: 30px; margin-bottom: 8px;"></div>
            <div class="skeleton" style="height: 30px; margin-bottom: 8px;"></div>
            <div class="skeleton" style="height: 30px; margin-bottom: 8px;"></div>
            <div class="skeleton" style="height: 30px; margin-bottom: 8px;"></div>
        `;

        try {
            // Simulate network delay for effect (can be removed)
            await new Promise(r => setTimeout(r, 600));

            const config = await window.pywebview.api.get_carto_config();
            if (!config) throw new Error("Empty config");

            container.innerHTML = ''; // Clear skeleton

            Object.entries(config).forEach(([key, conf]) => {
                const color = conf.color || "#cbd5e1";
                const label = conf.label || key;
                const checked = true; // Default to checked

                // Create Checkbox Wrapper
                const div = document.createElement('div');
                div.className = 'carto-checkbox-wrapper';
                // Add fade-in animation
                div.style.animation = "fadeIn 0.3s ease-out forwards";
                div.innerHTML = `
                    <input type="checkbox" id="chk_${key}" value="${key}" ${checked ? 'checked' : ''}>
                    <label for="chk_${key}" style="color:${color}">${label}</label>
                `;

                // Event Listener for Toggling
                const chk = div.querySelector('input');
                chk.addEventListener('change', () => {
                    if (this.currentPreviewData) {
                        this.renderPreview(this.currentPreviewData);
                    }
                });

                container.appendChild(div);
            });
            console.log("[Cartographie] Layers loaded dynamically");

        } catch (e) {
            console.error("[Cartographie] Failed to load layer config:", e);
            container.innerHTML = `<div style="color: #ef4444; font-size:11px; padding: 10px; border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 8px; background: rgba(239, 68, 68, 0.1);">
                ⚠️ Erreur chargement couches<br>
                <span style="opacity: 0.7; font-size: 9px;">${e.message || e}</span>
            </div>`;
            if (window.showToast) window.showToast('error', "Impossible de charger les couches");
        }
    }

    initDrawControls() {
        if (!L.Control.Draw) return;

        // French Localization
        L.drawLocal = {
            draw: {
                toolbar: {
                    actions: {
                        title: 'Annuler le dessin',
                        text: 'Annuler'
                    },
                    finish: {
                        title: 'Terminer le dessin',
                        text: 'Terminer'
                    },
                    undo: {
                        title: 'Supprimer le dernier point',
                        text: 'Supprimer dernier point'
                    },
                    buttons: {
                        polygon: 'Dessiner un polygone (Emprise)',
                        rectangle: 'Dessiner un rectangle',
                        marker: 'Placer un marqueur',
                        circle: 'Dessiner un cercle',
                        circlemarker: 'Dessiner un marqueur circulaire',
                        polyline: 'Dessiner une polyligne'
                    }
                },
                handlers: {
                    circle: {
                        tooltip: {
                            start: 'Cliquez et glissez pour dessiner le cercle.'
                        },
                        radius: 'Rayon'
                    },
                    circlemarker: {
                        tooltip: {
                            start: 'Cliquez sur la carte pour placer le marqueur.'
                        }
                    },
                    marker: {
                        tooltip: {
                            start: 'Cliquez sur la carte pour placer le marqueur.'
                        }
                    },
                    polygon: {
                        tooltip: {
                            start: 'Cliquez pour commencer à dessiner.',
                            cont: 'Cliquez pour continuer à dessiner.',
                            end: 'Cliquez sur le premier point pour fermer ce polygone.'
                        }
                    },
                    polyline: {
                        error: '<strong>Erreur:</strong> les arêtes ne doivent pas se croiser!',
                        tooltip: {
                            start: 'Cliquez pour commencer à dessiner.',
                            cont: 'Cliquez pour continuer à dessiner.',
                            end: 'Cliquez sur le dernier point pour terminer la ligne.'
                        }
                    },
                    rectangle: {
                        tooltip: {
                            start: 'Cliquez et glissez pour dessiner un rectangle.'
                        }
                    },
                    simpleshape: {
                        tooltip: {
                            end: 'Relâchez la souris pour terminer le dessin.'
                        }
                    }
                }
            },
            edit: {
                toolbar: {
                    actions: {
                        save: {
                            title: 'Sauvegarder les modifications',
                            text: 'Sauvegarder'
                        },
                        cancel: {
                            title: 'Annuler toutes les modifications',
                            text: 'Annuler'
                        },
                        clearAll: {
                            title: 'Tout effacer',
                            text: 'Tout effacer'
                        }
                    },
                    buttons: {
                        edit: 'Modifier les calques',
                        editDisabled: 'Aucun calque à modifier',
                        remove: 'Supprimer des calques',
                        removeDisabled: 'Aucun calque à supprimer'
                    }
                },
                handlers: {
                    edit: {
                        tooltip: {
                            text: 'Glissez les poignées ou le marqueur pour modifier les objets.',
                            subtext: 'Cliquez sur Annuler pour revenir en arrière.'
                        }
                    },
                    remove: {
                        tooltip: {
                            text: 'Cliquez sur un objet pour le supprimer.'
                        }
                    }
                }
            }
        };

        // Feature group for drawn shapes
        this.drawnItems = new L.FeatureGroup();
        this.map.addLayer(this.drawnItems);

        // Draw configuration
        this.drawControl = new L.Control.Draw({
            position: 'topright',
            draw: {
                polyline: false,
                circle: false,
                circlemarker: false,
                marker: false,
                rectangle: {
                    shapeOptions: { color: '#22c55e', weight: 2 }
                },
                polygon: {
                    allowIntersection: false,
                    showArea: true,
                    shapeOptions: { color: '#22c55e', weight: 2 }
                }
            },
            edit: {
                featureGroup: this.drawnItems,
                remove: true
            }
        });

        this.map.addControl(this.drawControl);

        // EVENT: Shape Created
        this.map.on(L.Draw.Event.CREATED, (e) => {
            // Clear previous drawings
            this.drawnItems.clearLayers();

            // Add new layer
            const layer = e.layer;
            this.drawnItems.addLayer(layer);

            // Update Site Logic
            this.updateSiteFromLayer(layer);

            this.addLog('success', 'Emprise définie');
        });

        // EVENT: Shape Deleted
        this.map.on(L.Draw.Event.DELETED, () => {
            this.clearSite();
        });

        // EVENT: Shape Edited
        this.map.on(L.Draw.Event.EDITED, (e) => {
            e.layers.eachLayer(layer => {
                this.updateSiteFromLayer(layer);
            });
        });

        // FORCE ICONS (Fix for invisible sprites)
        setTimeout(() => this.fixDrawIcons(), 500);
    }

    fixDrawIcons() {
        // Icons map
        const icons = {
            'leaflet-draw-draw-polygon': `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#334155" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2L2 22h20L12 2z"/></svg>`,
            'leaflet-draw-draw-rectangle': `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#334155" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/></svg>`,
            'leaflet-draw-draw-marker': `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#334155" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>`,
            'leaflet-draw-edit-edit': `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#334155" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>`,
            'leaflet-draw-edit-remove': `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#ef4444" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><line x1="10" y1="11" x2="10" y2="17"/><line x1="14" y1="11" x2="14" y2="17"/></svg>`
        };

        for (const [cls, svg] of Object.entries(icons)) {
            const els = document.getElementsByClassName(cls);
            for (let el of els) {
                el.innerHTML = svg;
                el.style.backgroundImage = 'none'; // Ensure generic CSS doesn't override
            }
        }
    }

    updateSiteFromLayer(layer) {
        // 1. Save Polygon GeoJSON
        this.emprisePolygon = layer.toGeoJSON().geometry;

        // 2. Calculate Centroid
        const center = layer.getBounds().getCenter();
        this.selectedLat = center.lat;
        this.selectedLon = center.lng;

        // 3. Update Visuals (Center Marker + Search Radius)
        this.updateVisuals();

        // 4. Update UI Infos
        this.updateUIInfos();

        // 5. Pulse Export Button to guide user
        // 5. Pulse/Highlight Export Button
        const exportBtn = document.querySelector('.btn-shimmer');
        if (exportBtn) {
            // Optional: We could boost the shimmer speed or add a glow here
            // For now, let's just trigger a small 'pop' animation via CSS class if needed
            exportBtn.style.transform = "scale(1.05)";
            setTimeout(() => exportBtn.style.transform = "", 200);
        }
    }

    updateVisuals() {
        if (!this.selectedLat || !this.map) return;

        const center = [this.selectedLat, this.selectedLon];

        // Marker (Center)
        if (this.siteMarker) this.map.removeLayer(this.siteMarker);
        this.siteMarker = L.marker(center, { interactive: false }).addTo(this.map);

        // Search Circle
        const radInput = document.getElementById('cartoRadius');
        const radius = radInput ? parseInt(radInput.value) : 500;

        if (this.siteCircle) this.map.removeLayer(this.siteCircle);
        this.siteCircle = L.circle(center, {
            radius: radius,
            color: '#38bdf8',
            weight: 1,
            dashArray: '5, 5',
            fillColor: '#38bdf8',
            fillOpacity: 0.1
        }).addTo(this.map);
    }

    updateRadius() {
        const radInput = document.getElementById('cartoRadius');
        const radDisplay = document.getElementById('cartoRadiusDisplay');

        if (radInput && radDisplay) {
            radDisplay.innerText = radInput.value + " m";
            this.updateSliderBackground(radInput); // Update visual fill
            this.updateVisuals(); // Re-draw circle with new radius
        }
    }

    updateSliderBackground(elm) {
        if (!elm) return;
        const min = elm.min ? parseFloat(elm.min) : 0;
        const max = elm.max ? parseFloat(elm.max) : 100;
        const val = parseFloat(elm.value);

        const percentage = ((val - min) / (max - min)) * 100;

        // CSS Variable integration for colors
        // Left part (filled): var(--accent) #38bdf8
        // Right part (empty): rgba(15, 23, 42, 0.8) (from CSS)

        elm.style.background = `linear-gradient(to right, #38bdf8 0%, #38bdf8 ${percentage}%, rgba(15, 23, 42, 0.8) ${percentage}%, rgba(15, 23, 42, 0.8) 100%)`;
    }

    updateUIInfos() {

        // Emprise Info
        const infoEl = document.getElementById('empriseInfo');
        const detailsEl = document.getElementById('empriseDetails');

        if (this.emprisePolygon && infoEl && this.drawnItems) {
            infoEl.classList.add('visible');

            // Calculate Area
            const bounds = this.drawnItems.getBounds();
            const latRange = bounds.getNorth() - bounds.getSouth();
            const lonRange = bounds.getEast() - bounds.getWest();

            // Approximation (flat earth)
            const latM = latRange * 111111;
            const lonM = lonRange * 111111 * Math.cos(bounds.getCenter().lat * Math.PI / 180);
            const areaM2 = latM * lonM;

            let areaStr = areaM2 > 10000
                ? `~${(areaM2 / 10000).toFixed(1)} ha`
                : `~${Math.round(areaM2)} m²`;

            detailsEl.innerHTML = `${areaStr} • Centre auto-calculé`;
        } else if (infoEl) {
            infoEl.classList.remove('visible');
        }
    }

    clearSite() {
        if (this.drawnItems) this.drawnItems.clearLayers();
        if (this.siteMarker) this.map.removeLayer(this.siteMarker);
        if (this.siteCircle) this.map.removeLayer(this.siteCircle);

        this.emprisePolygon = null;
        this.siteMarker = null;
        this.siteCircle = null;
        this.selectedLat = 0;

        // Reset UI

        this.updateUIInfos();
        this.addLog('info', 'Emprise effacée');
    }

    // === DATA & EXPORT ===

    // Get current bbox (ALWAYS from Search Circle)
    getCurrentBbox() {
        if (!this.siteCircle) return null;

        const cb = this.siteCircle.getBounds();
        return {
            min_lat: cb.getSouth(),
            min_lon: cb.getWest(),
            max_lat: cb.getNorth(),
            max_lon: cb.getEast()
        };
    }

    getSelectedLayers() {
        const inputs = document.querySelectorAll('#carto-layers-list input:checked');
        return Array.from(inputs).map(i => i.value);
    }

    getExportOptions() {
        return {
            include_vectors: true,
            include_rasters: document.getElementById('includePVA')?.checked ||
                document.getElementById('includeMosaics')?.checked,
            include_pva: document.getElementById('includePVA')?.checked ?? true,
            include_mosaics: document.getElementById('includeMosaics')?.checked ?? true,

            include_emprise: true // Always include site boundary
        };
    }

    // Logging
    addLog(type, message) {
        const logsEl = document.getElementById('cartoLogs');
        if (!logsEl) return;
        const item = document.createElement('div');
        item.className = `log-item log-${type}`;
        item.textContent = message;
        logsEl.insertBefore(item, logsEl.firstChild);
        while (logsEl.children.length > 20) logsEl.removeChild(logsEl.lastChild);
    }

    clearLogs() {
        document.getElementById('cartoLogs').innerHTML = '';
    }

    // === ACTIONS ===

    async runPreview() {
        const bbox = this.getCurrentBbox();
        const layers = this.getSelectedLayers();

        if (!bbox) {
            if (window.showToast) window.showToast('error', "Veuillez dessiner un polygone d'abord");
            return;
        }

        if (!layers.length) {
            if (window.showToast) window.showToast('error', "Sélectionnez au moins une couche");
            return;
        }

        this.addLog('info', 'Lancement aperçu (dans rayon de recherche)...');
        if (window.showLoader) window.showLoader("Chargement...");

        try {
            const res = await window.pywebview.api.run_carto_preview(bbox, layers);
            if (window.hideLoader) window.hideLoader();

            this.currentPreviewData = res;
            this.renderPreview(res);
            this.addLog('success', 'Aperçu terminé');
        } catch (err) {
            if (window.hideLoader) window.hideLoader();
            console.error(err);
            this.addLog('error', `Erreur: ${err}`);
        }
    }

    renderPreview(res) {
        if (!this.map) return;
        if (this.geoJsonLayer) this.map.removeLayer(this.geoJsonLayer);

        // Use MarkerClusterGroup (if available) or fallback to LayerGroup
        if (L.markerClusterGroup) {
            this.geoJsonLayer = L.markerClusterGroup({
                chunkedLoading: true, // Optim: Process in chunks to avoid UI freeze
                maxClusterRadius: 50
            });
        } else {
            this.geoJsonLayer = L.layerGroup();
        }

        this.geoJsonLayer.addTo(this.map);

        res.forEach(g => {
            if (!g.items) return;

            // CHECKBOX CHECK: Only render if the corresponding checkbox is checked
            // Fallback: If 'key' is missing (old backend), assume visible or check label? 
            // Better to rely on key. g.key was added in backend.
            let isVisible = true;
            if (g.key) {
                const chk = document.getElementById(`chk_${g.key}`);
                if (chk && !chk.checked) isVisible = false;
            }

            if (!isVisible) return;

            // Optimization: Filter out invalid geometries beforehand
            const validItems = g.items.filter(i => i.geometry);

            validItems.forEach(i => {
                // Create layer from GeoJSON
                L.geoJSON(i.geometry, {
                    pointToLayer: (f, l) => L.circleMarker(l, {
                        radius: 6, // Slightly larger for better hover target
                        fillColor: i.color,
                        color: "#fff",
                        weight: 1.5,
                        fillOpacity: 0.9
                    }),
                    style: { color: i.color, weight: 2, opacity: 0.8 },
                    onEachFeature: (feature, layer) => {
                        const popupContent = `<div style="font-size:12px"><b>${g.layer}</b><br>${i.nom}${i.details ? '<br><i>' + i.details + '</i>' : ''}</div>`;
                        const tooltipContent = `<div style="font-weight:600; font-size:11px; color:${i.color}">${i.nom}</div>${i.details ? '<div style="font-size:10px; opacity:0.8">' + i.details + '</div>' : ''}`;

                        layer.bindPopup(popupContent);
                        layer.bindTooltip(tooltipContent, {
                            direction: 'top',
                            sticky: true,
                            className: 'carto-tooltip',
                            opacity: 0.95
                        });
                    }
                })
                    .addTo(this.geoJsonLayer);
            });
        });
    }

    async runExport() {
        const bbox = this.getCurrentBbox(); // Search Radius BBOX
        const layers = this.getSelectedLayers();
        const options = this.getExportOptions();

        if (!bbox) {
            if (window.showToast) window.showToast('error', "Veuillez dessiner l'emprise du site");
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
            // Emprise is explicitly the drawn polygon
            let emprise = this.emprisePolygon;

            // Fallback to circle if for some reason polygon is missing but circle exists (edge case)
            if (!emprise && this.siteCircle) {
                const b = this.siteCircle.getBounds();
                emprise = {
                    type: "Polygon",
                    coordinates: [[
                        [b.getWest(), b.getSouth()], [b.getEast(), b.getSouth()],
                        [b.getEast(), b.getNorth()], [b.getWest(), b.getNorth()],
                        [b.getWest(), b.getSouth()]
                    ]]
                };
            }

            // Generate Radius Polygon (Circle)
            let radiusGeoJSON = null;
            if (this.siteCircle) {
                radiusGeoJSON = this.getCirclePolygon(this.siteCircle);
            }

            const res = await window.pywebview.api.run_carto_export(
                bbox, layers, null, folder, options, emprise, radiusGeoJSON
            );

            if (window.hideLoader) window.hideLoader();

            if (res.summary) {
                res.summary.forEach(s => {
                    this.addLog(s.status === 'success' ? 'success' : 'error',
                        `${s.status === 'success' ? '✓' : '✗'} ${s.layer} ${s.error || ''}`);
                });
            }
            this.addLog('success', `Export terminé: ${res.folder}`);
            if (window.showToast) window.showToast('success', "Export terminé !");

        } catch (err) {
            if (window.hideLoader) window.hideLoader();
            this.addLog('error', `Erreur: ${err}`);
        }
    }

    getCirclePolygon(circle) {
        const center = circle.getLatLng();
        const radius = circle.getRadius(); // meters
        const sides = 64;
        const lat = center.lat;
        const lng = center.lng;

        const points = [];
        for (let i = 0; i < sides; i++) {
            const angle = (i * 360 / sides) * (Math.PI / 180);
            // Simple flat earth approximation is sufficient for local visualization
            const dLat = (radius * Math.cos(angle)) / 111111;
            const dLng = (radius * Math.sin(angle)) / (111111 * Math.cos(lat * Math.PI / 180));
            points.push([lng + dLng, lat + dLat]);
        }
        // Close ring
        points.push(points[0]);

        return {
            type: "Polygon",
            coordinates: [points]
        };
    }

    async browseFolder() {
        try {
            const path = await window.pywebview.api.browse_folder();
            if (path) {
                document.getElementById('cartoTargetPath').value = path;
                this.addLog('info', `Dossier: ${path}`);
            }
        } catch (e) {
            console.error(e);
        }
    }
}

// === BOOTSTRAP ===
window.Cartographie = new CartographieManager();

// === GLOBAL BINDINGS ===
window.init_cartographie = () => window.Cartographie.init();
window.carto_updateRadius = () => window.Cartographie.updateRadius();
window.carto_runPreview = () => window.Cartographie.runPreview();
window.carto_runExport = () => window.Cartographie.runExport();
window.carto_browseFolder = () => window.Cartographie.browseFolder();
window.carto_clearEmprise = () => window.Cartographie.clearSite();

console.log("[Cartographie] Module loaded (Refactored)");
