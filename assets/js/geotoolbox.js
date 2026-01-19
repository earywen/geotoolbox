/**
 * GEOTOOLBOX LOGIC
 * Refactored to ES6 Class Structure
 */

class GeotoolboxManager {
    constructor() {
        this.map = null;
        this.currentBounds = null;
        this.geoJsonLayer = null;
        this.currentPreviewData = null;
        this.siteMarker = null;
        this.siteCircle = null;
        this.selectedLat = 0;
        this.selectedLon = 0;

        this.EXPORT_FORMATS = {
            'format_land': { w: 1587, h: 1123 },
            'format_port': { w: 1123, h: 1587 }
        };
    }

    init() {
        console.log("[Geotoolbox] Init called");

        // Prevent double init
        if (this.map) {
            setTimeout(() => this.map.invalidateSize(), 100);
            this.syncFromState();
            return;
        }

        const mapEl = document.getElementById('map');
        if (!mapEl) {
            console.error("[Geotoolbox] Map container not found");
            return;
        }

        // Initialize Leaflet Map
        this.map = L.map('map', { zoomControl: false, zoomSnap: 0 }).setView([46.603354, 1.888334], 6);

        L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
            attribution: '&copy; CARTO',
            maxZoom: 20
        }).addTo(this.map);

        L.control.zoom({ position: 'topright' }).addTo(this.map);

        // Geocoder Control
        L.Control.geocoder({ defaultMarkGeocode: false, position: 'topright' })
            .on('markgeocode', (e) => this.updateSiteSelection(e.geocode.center))
            .addTo(this.map);

        // Event Listeners
        this.map.on('click', (e) => this.updateSiteSelection(e.latlng));
        this.map.on('moveend', () => {
            const b = this.map.getBounds();
            this.currentBounds = {
                min_lat: b.getSouth(), min_lon: b.getWest(),
                max_lat: b.getNorth(), max_lon: b.getEast()
            };
            this.storeViewport();
        });

        this.syncFromState();
    }

    syncFromState() {
        // Sync logic with shared state
        if (window.Burgeaply && window.Burgeaply.getState) {
            const state = window.Burgeaply.getState();
            if (state && state.viewport && this.map) {
                // Restore logic could go here if implemented
            }
        }
    }

    storeViewport() {
        if (this.map && window.Burgeaply && window.Burgeaply.updateState) {
            window.Burgeaply.updateState({ center: this.map.getCenter(), zoom: this.map.getZoom() }, null);
        }
    }

    updateSiteSelection(latlng) {
        this.selectedLat = latlng.lat;
        this.selectedLon = latlng.lng;

        const coordsInput = document.getElementById('siteCoords');
        if (coordsInput) coordsInput.value = this.selectedLat.toFixed(5) + ", " + this.selectedLon.toFixed(5);

        if (this.siteMarker) this.map.removeLayer(this.siteMarker);
        this.siteMarker = L.marker(latlng).addTo(this.map);

        this.updateRadiusVisuals();

        // Use global helper now exposed on window
        if (window.smartPanTo) window.smartPanTo(this.map, latlng);
    }

    updateRadius() {
        const radInput = document.getElementById('radiusInput');
        const radDisplay = document.getElementById('radiusDisplay');
        if (radInput && radDisplay) {
            radDisplay.innerText = radInput.value + " m";
            this.updateRadiusVisuals();
        }
    }

    updateRadiusVisuals() {
        if (!this.selectedLat || !this.map) return;

        if (this.siteCircle) this.map.removeLayer(this.siteCircle);

        const radInput = document.getElementById('radiusInput');
        const r = radInput ? parseInt(radInput.value) : 100;

        this.siteCircle = L.circle(
            [this.selectedLat, this.selectedLon],
            { radius: r, color: '#38bdf8', weight: 2 }
        ).addTo(this.map);
    }

    // --- GABARIT & EXPORT LOGIC ---
    toggleGabarit() {
        const chk = document.getElementById('showGabarit');
        const overlay = document.getElementById('gabarit-overlay');
        const show = chk ? chk.checked : false;

        if (overlay) overlay.style.display = show ? 'flex' : 'none';
        if (show) this.updateGabarit();
    }

    updateGabarit() {
        const fmtInput = document.getElementById('exportFormat');
        const dim = this.EXPORT_FORMATS[fmtInput ? fmtInput.value : 'format_land'];

        const frame = document.getElementById('gabarit-frame');
        const container = document.getElementById('map-container-absolute');

        if (!frame || !container) return;

        const containerH = container.offsetHeight;
        const containerW = container.offsetWidth;
        const SIDEBAR_OFFSET = 500;

        let availableW = containerW - SIDEBAR_OFFSET;
        if (availableW < 100 || containerW < 900) availableW = containerW;

        const ratio = dim.w / dim.h;
        let targetH = containerH * 0.75;
        let targetW = targetH * ratio;

        if (targetW > availableW * 0.9) { targetW = availableW * 0.9; targetH = targetW / ratio; }
        if (targetH > containerH * 0.9) { targetH = containerH * 0.9; targetW = targetH * ratio; }

        frame.style.width = targetW + 'px';
        frame.style.height = targetH + 'px';

        const leftPos = (containerW < 900) ? (containerW - targetW) / 2 : SIDEBAR_OFFSET + ((availableW - targetW) / 2);
        frame.style.left = leftPos + 'px';
        frame.style.top = ((containerH - targetH) / 2) + 'px';
        frame.style.margin = "0";
    }

    getGabaritBounds() {
        const frame = document.getElementById('gabarit-frame');
        const mapEl = document.getElementById('map');
        if (!frame || !mapEl || !this.map) return this.map.getBounds();

        const rect = frame.getBoundingClientRect();
        const mapRect = mapEl.getBoundingClientRect();

        const tl = this.map.containerPointToLatLng([rect.left - mapRect.left + 2, rect.top - mapRect.top + 2]);
        const br = this.map.containerPointToLatLng([rect.right - mapRect.left - 2, rect.bottom - mapRect.top - 2]);

        return L.latLngBounds(tl, br);
    }

    // --- PROCESS EXECUTION ---
    async runProcess(mode) {
        let b = this.currentBounds;

        // If circle exists, prioritize its bounds
        if (this.siteCircle) {
            const cb = this.siteCircle.getBounds();
            b = {
                min_lat: cb.getSouth(), min_lon: cb.getWest(),
                max_lat: cb.getNorth(), max_lon: cb.getEast()
            };
        }

        const inputs = document.querySelectorAll('#layers-list input:checked');
        const l = Array.from(inputs).map(i => i.value);

        if (!l.length) {
            if (window.showToast) window.showToast('error', "Sélectionnez une couche");
            return;
        }

        if (mode === 'preview') {
            if (window.showLoader) window.showLoader("Chargement...");

            try {
                const res = await window.pywebview.api.run_preview(b, l);
                if (window.hideLoader) window.hideLoader();

                this.currentPreviewData = res;
                this.renderPreview(res);
                if (window.showToast) window.showToast('success', "Aperçu OK");
            } catch (err) {
                if (window.hideLoader) window.hideLoader();
                console.error(err);
                if (window.showToast) window.showToast('error', "Erreur Preview: " + err);
            }
        } else {
            const folderInput = document.getElementById('targetPath');
            const folder = folderInput ? folderInput.value : null;

            if (!folder) {
                if (window.showToast) window.showToast('error', "Dossier manquant");
                return;
            }

            if (window.showLoader) window.showLoader("Export Data...");

            try {
                const res = await window.pywebview.api.run_export(b, l, null, folder);
                if (window.hideLoader) window.hideLoader();
                if (window.showToast) window.showToast('success', "Export Terminé");

                const log = document.getElementById('status-log');
                if (log && res.summary) {
                    log.style.display = 'block';

                    // Results List
                    let html = res.summary.map(s =>
                        `<div class="res-item"><span style="color:var(--accent)">${s.layer}</span>: ${s.count}</div>`
                    ).join('');

                    // Open Folder Button
                    // We use open_file(folder) because os.startfile(folder) opens it (enters directory)
                    // whereas open_folder(folder) calls explorer /select which just highlights it.
                    if (res.folder) {
                        html += `
                        <div style="margin-top: 15px; text-align: center;">
                            <button onclick="window.pywebview.api.open_file('${res.folder.replace(/\\/g, '\\\\')}')" 
                                class="btn-secondary" style="font-size: 11px; padding: 6px 12px; width: auto;">
                                📂 Ouvrir le dossier Export
                            </button>
                        </div>
                        `;
                    }

                    log.innerHTML = html;
                }
            } catch (err) {
                if (window.hideLoader) window.hideLoader();
                console.error(err);
                if (window.showToast) window.showToast('error', "Erreur Export: " + err);
            }
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
                            radius: 6, fillColor: i.color,
                            color: "#fff", weight: 1, fillOpacity: 0.8
                        }),
                        style: { color: i.color, weight: 2, opacity: 0.8 },
                        onEachFeature: (f, l) => l.bindPopup(`<b>${g.layer}</b><br>${i.nom}`)
                    }).addTo(this.geoJsonLayer);
                }
            });
        });
    }

    // --- SHADOW EXPORT V2 ---
    async exportMapImage() {
        const folderInput = document.getElementById('targetPath');
        const folder = folderInput ? folderInput.value : null;

        if (!folder) {
            if (window.showToast) window.showToast('error', "Sélectionnez un dossier d'export !");
            return;
        }

        // Logic: Use current preview data OR auto-fetch
        if (!this.currentPreviewData) {
            // Auto-fetch required logic duplicating runProcess roughly
            // For brevity, let's just trigger runProcess(preview) first then export
            // BUT for user experience, let's implement the fetch here
            let b = this.currentBounds;
            if (this.siteCircle) {
                const cb = this.siteCircle.getBounds();
                b = { min_lat: cb.getSouth(), min_lon: cb.getWest(), max_lat: cb.getNorth(), max_lon: cb.getEast() };
            }
            const inputs = document.querySelectorAll('#layers-list input:checked');
            const l = Array.from(inputs).map(i => i.value);

            if (!l.length) { if (window.showToast) window.showToast('error', "Aucune couche sélectionnée"); return; }

            if (window.showLoader) window.showLoader("Récupération des données...");

            try {
                const res = await window.pywebview.api.run_preview(b, l);
                this.currentPreviewData = res;
                this.renderPreview(res);
                this._performShadowExport(res, folder);
            } catch (e) {
                if (window.hideLoader) window.hideLoader();
                if (window.showToast) window.showToast('error', "Erreur récupération: " + e);
            }
        } else {
            this._performShadowExport(this.currentPreviewData, folder);
        }
    }

    _performShadowExport(data, folder) {
        const chk = document.getElementById('showGabarit');
        const showGabarit = chk ? chk.checked : false;
        const exportBounds = showGabarit ? this.getGabaritBounds() : this.map.getBounds();

        const fmtInput = document.getElementById('exportFormat');
        const dim = this.EXPORT_FORMATS[fmtInput ? fmtInput.value : 'format_land'];

        if (window.showLoader) window.showLoader("Génération Carte HD...");

        const shadow = document.getElementById('shadow-export-container');
        if (!shadow) return;

        shadow.innerHTML = "";
        shadow.style.width = dim.w + 'px';
        shadow.style.height = dim.h + 'px';
        shadow.style.visibility = 'visible';

        const shadowMap = L.map(shadow, {
            zoomControl: false, attributionControl: false, preferCanvas: true,
            fadeAnimation: false, zoomAnimation: false
        });

        const padding = L.point(50, 50);
        shadowMap.setView(exportBounds.getCenter(), shadowMap.getBoundsZoom(exportBounds, false, padding), { animate: false });

        L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', { maxZoom: 20 }).addTo(shadowMap);

        // Map Layers
        if (this.selectedLat) {
            L.marker([this.selectedLat, this.selectedLon]).addTo(shadowMap);
            const radInput = document.getElementById('radiusInput');
            const r = radInput ? parseInt(radInput.value) : 100;
            L.circle([this.selectedLat, this.selectedLon], {
                radius: r, color: '#38bdf8', weight: 2, fill: false, dashArray: "10, 10"
            }).addTo(shadowMap);
        }

        if (data) {
            const shadowDataLayer = L.layerGroup().addTo(shadowMap);
            data.forEach(g => {
                if (!g.items) return;
                g.items.forEach(i => {
                    if (i.geometry) L.geoJSON(i.geometry, {
                        pointToLayer: (f, l) => L.circleMarker(l, { radius: 6, fillColor: i.color, color: "#fff", weight: 1, fillOpacity: 0.8 }),
                        style: { color: i.color, weight: 2, opacity: 0.8 }
                    }).addTo(shadowDataLayer);
                });
            });
        }

        // Decoration
        this._addMapDecorations(shadow);

        L.control.scale({ imperial: false, position: 'bottomleft' }).addTo(shadowMap);

        // Render
        setTimeout(() => {
            html2canvas(shadow, { useCORS: true, allowTaint: true, width: dim.w, height: dim.h, scale: 2, logging: false }).then(canvas => {
                const dataUrl = canvas.toDataURL("image/jpeg", 0.9);
                window.pywebview.api.run_save_map(dataUrl, folder).then(path => {
                    shadowMap.remove();
                    shadow.innerHTML = ""; shadow.style.visibility = 'hidden';
                    if (window.hideLoader) window.hideLoader();
                    if (path && window.showToast) window.showToast('success', "Carte sauvegardée !");
                });
            }).catch(e => {
                shadowMap.remove(); shadow.style.visibility = 'hidden';
                if (window.hideLoader) window.hideLoader();
                if (window.showToast) window.showToast('error', "Err: " + e);
            });
        }, 1500);
    }

    _addMapDecorations(container) {
        // North Arrow
        const northDiv = document.createElement('div');
        northDiv.className = 'map-overlay-north';
        northDiv.innerHTML = '<svg viewBox="0 0 100 100"><circle cx="50" cy="50" r="45" fill="white" stroke="black" stroke-width="2"/><path d="M50 10 L65 50 L50 90 L35 50 Z" fill="black"/><text x="50" y="28" font-family="Arial" font-size="20" fill="white" text-anchor="middle" font-weight="bold">N</text></svg>';
        container.appendChild(northDiv);

        // Legend
        const legendDiv = document.createElement('div');
        legendDiv.className = 'map-overlay-legend';

        let html = "<b>Légende</b><br><br>";
        document.querySelectorAll('.checkbox-wrapper input:checked').forEach(cb => {
            const lbl = document.querySelector('label[for="' + cb.id + '"]');
            const color = lbl ? lbl.style.color : '#000';
            const txt = lbl ? lbl.innerText : cb.value;
            let sym = `<div style="background:${color}; width:20px; height:20px; margin-right:10px; border:1px solid #94a3b8;"></div>`;
            if (cb.value === 'EAU') sym = `<div style="background:${color}; width:25px; height:4px; margin-right:10px;"></div>`;
            if (cb.value === 'SSP' || cb.value === 'BSS') sym = `<div style="background:${color}; width:16px; height:16px; border-radius:50%; margin-right:15px; border:1px solid #333;"></div>`;
            html += `<div class="legend-item">${sym}<div>${txt}</div></div>`;
        });
        legendDiv.innerHTML = html;
        container.appendChild(legendDiv);
    }
}

// === BOOTSTRAP ===
window.Geotoolbox = new GeotoolboxManager();

// === LEGACY BINDINGS FOR HTML ONCLICK ===
// These should ideally be replaced by event listeners in the class, but HTML still calls them
window.init_geotoolbox = () => window.Geotoolbox.init();
window.updateRadius = () => window.Geotoolbox.updateRadius();
window.toggleGabarit = () => window.Geotoolbox.toggleGabarit();
window.updateGabarit = () => window.Geotoolbox.updateGabarit();
window.runProcess = (mode) => window.Geotoolbox.runProcess(mode);
window.geo_exportMap = () => window.Geotoolbox.exportMapImage();

// Ensure global helper is available just in case app.js didn't load it yet (though it should have)
window.gt_browseFolder = () => window.browseFolder();
