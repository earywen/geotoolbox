/**
 * BURGEAPLY JS CORE
 * Refactored for ES6+ and Modularity
 */

// Global Namespace
window.Burgeaply = {
    state: {
        viewport: null, // { center: {lat, lng}, zoom: int }
        selection: null // { lat: float, lng: float }
    },

    // Core Methods
    updateState(viewport, selection) {
        if (viewport) this.state.viewport = viewport;
        if (selection) this.state.selection = selection;
    },

    getState() {
        return this.state;
    }
};

// Legacy Global Accessors (for compatibility with Geotoolbox.js)
window.SHARED_STATE = window.Burgeaply.state;
window.updateSharedState = (v, s) => window.Burgeaply.updateState(v, s);
window.getSharedState = () => window.Burgeaply.getState();

/**
 * Smart Pan Helper
 */
function smartPanTo(map, latlng, zoom) {
    // Centre la carte en tenant compte de la sidebar (approx 400px)
    map.setView(latlng, zoom || map.getZoom(), { animate: false });
    map.panBy([-250, 0], { animate: true, duration: 0.5 });
}
window.smartPanTo = smartPanTo; // Expose for modules

/**
 * PYWEBVIEW ENTRY POINT
 */
window.addEventListener('pywebviewready', function () {
    console.log("[Core] PyWebView Ready");

    // Initial Load of Views from Python API
    if (window.pywebview && window.pywebview.api) {
        window.pywebview.api.get_initial_content()
            .then(data => {
                if (data.error) {
                    throw new Error(data.error);
                }

                if (data.menu_html) {
                    const dock = document.getElementById('dock-menu-placeholder');
                    if (dock) dock.innerHTML = data.menu_html;
                }
                if (data.views_html) {
                    const content = document.getElementById('content-area-placeholder');
                    if (content) content.innerHTML = data.views_html;
                }
                if (data.version) {
                    const vList = ['app-version', 'dock-footer-version'];
                    vList.forEach(id => {
                        const el = document.getElementById(id);
                        if (el) el.innerText = 'v' + data.version;
                    });
                    document.title = 'BURGEAPLY v' + data.version;
                }

                startSplash();

                // Check Updates safely
                setTimeout(() => window.pywebview.api.check_updates_ui(), 1000);
            })
            .catch(err => {
                console.error("Critical Error loading UI:", err);
                showToast('error', "Erreur chargement interface: " + err, 10000);
            });

        // EVENT DRIVEN ARCHITECTURE LISTENERS
        window.addEventListener('loader_update', (e) => {
            if (e.detail) {
                window.updateLoader(e.detail.percent, e.detail.message);
            }
        });

        window.addEventListener('loader_hide', () => {
            window.hideLoader();
        });

    } else {
        console.error("PyWebView API not found. Are we running in the browser?");
    }
});

function startSplash() {
    let p = 0;
    const bar = document.getElementById('splash-bar');

    const interval = setInterval(() => {
        p += 4;
        if (bar) bar.style.width = p + '%';

        if (p >= 100) {
            clearInterval(interval);
            const splash = document.getElementById('splash-screen');
            if (splash) {
                splash.style.opacity = '0';
                setTimeout(() => {
                    splash.style.display = 'none';
                    const app = document.getElementById('app');
                    if (app) app.style.opacity = '1';

                    // Trigger map resize if hidden to avoid gray tiles
                    window.dispatchEvent(new Event('resize'));
                }, 600);
            }
        }
    }, 30);
}

/**
 * UI UTILITIES
 */

// Toast Notification System
window.showToast = function (type, message, duration = 4000) {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;

    // Icons
    let icon = '';
    if (type === 'success') icon = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>';
    if (type === 'error') icon = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>';

    toast.innerHTML = `
        <div style="display:flex; align-items:center; gap:10px;">${icon} <span>${message}</span></div>
        <div style="position:absolute; bottom:0; left:0; height:3px; background:rgba(255,255,255,0.3); width:100%; animation: timeBar ${duration}ms linear forwards;"></div>
    `;

    // Dynamic Style for animation
    const style = document.createElement('style');
    style.innerHTML = `@keyframes timeBar { from { width: 100%; } to { width: 0%; } }`;
    toast.appendChild(style);

    container.appendChild(toast);

    // Auto remove
    setTimeout(() => {
        toast.style.animation = 'fadeOut 0.5s forwards';
        setTimeout(() => toast.remove(), 500);
    }, duration);
};

// View Switcher
window.switchView = function (viewId, menuEl) {
    document.querySelectorAll('.dock-item').forEach(el => el.classList.remove('active'));
    if (menuEl) menuEl.classList.add('active');

    document.querySelectorAll('.view-section').forEach(el => el.classList.remove('active'));
    const target = document.getElementById('view-' + viewId);
    if (target) {
        target.classList.add('active');
        // Force Leaflet/Map resize
        setTimeout(() => window.dispatchEvent(new Event('resize')), 100);
    }

    // Execute legacy init function if exists
    const initFn = window['init_' + viewId];
    if (typeof initFn === 'function') {
        try { initFn(); } catch (e) { console.warn(`Error init ${viewId}`, e); }
    }
};

// Directory Browser
window.browseFolder = function () {
    if (window.pywebview && window.pywebview.api) {
        window.pywebview.api.select_directory().then(p => {
            if (p) {
                const input = document.getElementById('targetPath');
                if (input) input.value = p;
            }
        });
    }
};

/**
 * LOADING OVERLAY METHODS (Called by Python)
 */
window.showLoader = function (title) {
    const overlay = document.getElementById('processing-overlay');
    if (overlay) overlay.classList.add('active');

    const t = document.getElementById('proc-title');
    if (t) t.innerText = title;

    window.updateLoader(0, "Initialisation...");
};

window.hideLoader = function () {
    setTimeout(() => {
        const overlay = document.getElementById('processing-overlay');
        if (overlay) overlay.classList.remove('active');
    }, 500);
};

window.updateLoader = function (percent, message) {
    const bar = document.getElementById('proc-bar');
    const txt = document.getElementById('proc-percent');
    const desc = document.getElementById('proc-desc');

    if (bar) bar.style.width = percent + '%';
    if (txt) txt.innerText = Math.round(percent) + '%';
    // message is already a string (Python sends JSON string which pywebview auto-deserializes for evaluate_js arguments? 
    // No, evaluate_js executes string code. We pass json.dumps(msg) in python -> which is a JS string literal.
    // So 'message' here is a string.
    if (message && desc) desc.innerText = message;
};

/**
 * AUTOLABO MODULE LOGIC
 */
let autoLaboFiles = [];

window.init_autolabo = function () {
    const dropzone = document.getElementById('autolabo-dropzone');
    if (!dropzone) return;

    // Guard: Prevent re-initializing listeners on repeated calls
    if (dropzone.dataset.initialized) {
        renderFileList();
        return;
    }
    dropzone.dataset.initialized = 'true';

    // Prevent default drag behaviors
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, preventDefaults, false);
        document.body.addEventListener(eventName, preventDefaults, false);
    });

    // Highlight drop area
    ['dragenter', 'dragover'].forEach(eventName => {
        dropzone.addEventListener(eventName, highlight, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, unhighlight, false);
    });

    // Handle dropped files
    dropzone.addEventListener('drop', handleDrop, false);

    // Click to browse (uses Python Native Dialog for full paths)
    dropzone.addEventListener('click', () => {
        if (window.pywebview && window.pywebview.api) {
            window.pywebview.api.select_files().then(files => {
                if (files && files.length > 0) {
                    addFiles(files);
                }
            });
        }
    });

    renderFileList();
}

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

function highlight(e) {
    const dz = document.getElementById('autolabo-dropzone');
    if (dz) dz.classList.add('drag-active');
}

function unhighlight(e) {
    const dz = document.getElementById('autolabo-dropzone');
    if (dz) dz.classList.remove('drag-active');
}

function handleDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;

    let paths = [];
    let hasPath = false;
    for (let i = 0; i < files.length; i++) {
        if (files[i].path) {
            paths.push(files[i].path);
            hasPath = true;
        }
    }

    if (hasPath) {
        addFiles(paths);
    } else {
        window.showToast('error', "Navigateur: Chemin introuvable (sécurité). Utilisez 'Parcourir'.");
    }
}

function addFiles(newFiles) {
    if (!newFiles || !Array.isArray(newFiles)) return;
    newFiles.forEach(path => {
        if (!autoLaboFiles.includes(path)) {
            autoLaboFiles.push(path);
        }
    });
    renderFileList();
}

window.removeFile = function (index) {
    autoLaboFiles.splice(index, 1);
    renderFileList();
}

function renderFileList() {
    const list = document.getElementById('file-list');
    const count = document.getElementById('file-count'); // Unused in new TPL?
    const btn = document.getElementById('btn-process-autolabo');

    if (!list) return;

    if (btn) btn.disabled = autoLaboFiles.length === 0;

    if (autoLaboFiles.length === 0) {
        list.innerHTML = `<div style="text-align: center; padding: 20px; opacity: 0.5;">Aucun fichier</div>`;
        return;
    }

    list.innerHTML = '';
    autoLaboFiles.forEach((file, index) => {
        const name = file.replace(/^.*[\\\/]/, '');
        const div = document.createElement('div');
        div.className = 'file-item';
        div.innerHTML = `
            <div class="name">${name}</div>
            <div class="remove" onclick="removeFile(${index})">✖</div>
        `;
        list.appendChild(div);
    });
}

// AutoLabo Folder Browser
window.autoLaboBrowseFolder = function () {
    if (window.pywebview && window.pywebview.api) {
        window.pywebview.api.select_directory().then(p => {
            if (p) {
                const input = document.getElementById('autolabo-target-path');
                if (input) input.value = p;
            }
        });
    }
};

window.runAutoLabo = function () {
    if (autoLaboFiles.length === 0) return;

    const logsBox = document.getElementById('autolabo-logs');
    const addLog = (msg) => {
        if (!logsBox) return;
        const time = new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
        logsBox.innerHTML += `<div>[${time}] ${msg}</div>`;
        logsBox.scrollTop = logsBox.scrollHeight;
    };

    // Clear and start
    if (logsBox) logsBox.innerHTML = '';
    addLog('🚀 Démarrage du traitement...');
    addLog(`📂 ${autoLaboFiles.length} fichier(s) à traiter`);

    // Get target path
    const targetPathInput = document.getElementById('autolabo-target-path');
    const targetPath = targetPathInput ? targetPathInput.value : '';
    if (targetPath) {
        addLog(`📁 Dossier cible: ${targetPath}`);
    }

    window.showLoader("Traitement de " + autoLaboFiles.length + " fichier(s)...");

    // Get provider
    const providerSelect = document.getElementById('provider-select');
    const providerId = providerSelect ? providerSelect.value : 'agrolab';
    const providerName = providerSelect ? providerSelect.options[providerSelect.selectedIndex].text : 'AGROLAB';
    addLog(`🧪 Laboratoire: ${providerName}`);

    // Get matrix
    const modelSelect = document.getElementById('matrix-select');
    const modelId = modelSelect ? modelSelect.value : 'es';
    addLog(`📋 Matrice: ${modelId === 'es' ? 'Eaux Souterraines' : modelId === 'sols' ? 'Sols' : 'Eaux de Surface'}`);

    window.pywebview.api.run_autolabo_process(autoLaboFiles, modelId, targetPath, providerId)
        .then(res => {
            window.hideLoader();
            if (res.success) {
                addLog('✅ Rapport généré avec succès !');
                if (res.output_path) {
                    addLog(`📁 Fichier: ${res.output_path.split(/[\\/]/).pop()}`);

                    // Add action buttons
                    if (logsBox) {
                        const btnContainer = document.createElement('div');
                        btnContainer.style.cssText = 'display: flex; gap: 8px; margin-top: 10px;';
                        btnContainer.innerHTML = `
                            <button onclick="openAutoLaboFile('${res.output_path.replace(/\\/g, '\\\\')}')" 
                                style="flex: 1; padding: 8px; border-radius: 8px; border: none; background: linear-gradient(135deg, #0ea5e9 0%, #2563eb 100%); color: white; cursor: pointer; font-size: 11px; font-weight: 600;">
                                📄 Ouvrir le fichier
                            </button>
                            <button onclick="openAutoLaboFolder('${res.output_path.replace(/\\/g, '\\\\')}')" 
                                style="flex: 1; padding: 8px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.2); background: rgba(255,255,255,0.05); color: white; cursor: pointer; font-size: 11px;">
                                📂 Ouvrir le dossier
                            </button>
                        `;
                        logsBox.appendChild(btnContainer);
                        logsBox.scrollTop = logsBox.scrollHeight;
                    }
                }
                window.showToast('success', "Rapport généré !");
                autoLaboFiles = [];
                renderFileList();
            } else {
                addLog(`❌ Erreur: ${res.error}`);
                window.showToast('error', "Erreur: " + res.error);
            }
        })
        .catch(err => {
            window.hideLoader();
            addLog(`❌ Erreur Backend: ${err}`);
            window.showToast('error', "Erreur Backend: " + err);
        });
};

// AutoLabo: Open generated file
window.openAutoLaboFile = function (filePath) {
    if (window.pywebview && window.pywebview.api) {
        window.pywebview.api.open_file(filePath);
    }
};

// AutoLabo: Open containing folder
window.openAutoLaboFolder = function (filePath) {
    if (window.pywebview && window.pywebview.api) {
        window.pywebview.api.open_folder(filePath);
    }
};
