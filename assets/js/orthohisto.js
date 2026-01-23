// --- ORTHOHISTO LOGIC ---
var oMap, oMarker, oSquare, oSelectedLat = 0, oSelectedLon = 0;

window.init_orthohisto = function () {
    console.log("Init Orthohisto called");
    if (oMap) {
        ortho_syncFromState_internal();
        setTimeout(() => oMap.invalidateSize(), 200);
        return;
    }
    // Safety check
    if (!document.getElementById('orthoMap')) return;

    oMap = L.map('orthoMap', { zoomControl: false }).setView([46.6, 1.8], 6);
    L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png').addTo(oMap);
    L.control.zoom({ position: 'topright' }).addTo(oMap);
    L.Control.geocoder({ geocoder: L.Control.Geocoder.photon({ geocodingQueryParams: { lang: 'fr' } }), defaultMarkGeocode: false })
        .on('markgeocode', function (e) { orthoUpdateSelection(e.geocode.center); oMap.setView(e.geocode.center, 15); }).addTo(oMap);
    oMap.on('click', function (e) { orthoUpdateSelection(e.latlng); });

    // SYNC WRITE
    oMap.on('moveend', function () {
        updateSharedState({ center: oMap.getCenter(), zoom: oMap.getZoom() }, null);
    });

    // Initial Sync
    ortho_syncFromState_internal();
    setTimeout(() => oMap.invalidateSize(), 200);
}

function ortho_syncFromState_internal() {
    var state = getSharedState();
    if (state.viewport && oMap) {
        oMap.setView(state.viewport.center, state.viewport.zoom, { animate: false });
    }
    if (state.selection) {
        orthoUpdateSelection(state.selection, true);
    }
}

function orthoUpdateSelection(l, skipWrite) {
    if (!skipWrite) {
        updateSharedState(null, { lat: l.lat, lng: l.lng });
        smartPanTo(oMap, l);
    }

    oSelectedLat = l.lat; oSelectedLon = l.lng;
    document.getElementById('orthoCoords').value = oSelectedLat.toFixed(5) + ", " + oSelectedLon.toFixed(5);
    if (oMarker) oMap.removeLayer(oMarker); oMarker = L.marker(l).addTo(oMap);
    orthoUpdateVisuals();
}

function orthoUpdateVisuals() {
    if (!oSelectedLat) return;
    if (oSquare) oMap.removeLayer(oSquare);
    var r = parseInt(document.getElementById('orthoRadiusInput').value);
    var d = r / 111000;
    var b = [[oSelectedLat - d, oSelectedLon - d], [oSelectedLat + d, oSelectedLon + d]];
    oSquare = L.rectangle(b, { color: "#10b981", weight: 2, fillOpacity: 0.1 }).addTo(oMap);
}

window.orthoUpdateRadius = function () {
    document.getElementById('orthoRadiusDisplay').innerText = document.getElementById('orthoRadiusInput').value + " m";
    orthoUpdateVisuals();
}

window.orthoBrowseFolder = function () { pywebview.api.select_directory().then(p => { if (p) document.getElementById('orthoTargetPath').value = p; }); }

window.startFullExtraction = function () {
    if (!oSelectedLat) return showToast("error", "Sélectionnez d'abord une zone sur la carte (clic).");
    var r = document.getElementById('orthoRadiusInput').value;
    var p = document.getElementById('orthoTargetPath').value;
    var l = document.getElementById('orthoLogs');

    showLoader("Extraction Globale");
    l.innerHTML = "Démarrage de l'analyse...<br>";

    pywebview.api.run_full_process(oSelectedLat, oSelectedLon, r, p).then(res => {
        hideLoader();
        if (res.folder) {
            l.innerHTML = "<b>TERMINÉ !</b><br>";
            l.innerHTML += "Dossier : " + res.folder + "<br>----------------<br>";
            res.summary.forEach(i => {
                let col = "#fb923c";
                if (i.status.includes("OK") || i.status.includes("Mission")) col = "#4ade80";
                if (i.status.includes("404")) col = "#f87171";
                l.innerHTML += `<span style='color:${col}'>[${i.annee}] ${i.status}</span><br>`;
            });

            // Add Open Folder Button
            l.innerHTML += `
                <div style="margin-top: 20px; text-align: center;">
                    <button onclick="window.pywebview.api.open_file('${res.folder.replace(/\\/g, '\\\\')}')"
                        style="padding: 8px 15px; border-radius: 8px; border: 1px solid #10b981; background: rgba(16, 185, 129, 0.2); color: white; cursor: pointer; font-weight: bold; font-size: 12px;">
                        📂 Ouvrir le dossier Export
                    </button>
                </div>
            `;

            showToast("success", "Extraction terminée ! (" + res.summary.length + " fichiers)", 6000);
        }
    }).catch(err => {
        hideLoader();
        l.innerHTML += "<span style='color:red'>Erreur critique : " + err + "</span>";
    });
}
